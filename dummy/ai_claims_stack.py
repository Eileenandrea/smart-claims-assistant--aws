
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    aws_opensearchservice as opensearch,
    aws_connect as connect,
    aws_lex as lex,
    aws_iam as iam,
    RemovalPolicy,
)
from constructs import Construct

class AiClaimsStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # 1. S3 Bucket for Document Storage
        claims_bucket = s3.Bucket(self, "ClaimsBucket",
                                  versioned=True,
                                  removal_policy=RemovalPolicy.DESTROY)

        # 2. DynamoDB Table for Claim Metadata
        claims_table = dynamodb.Table(self, "ClaimsTable",
                                      partition_key={"name": "ClaimID", "type": dynamodb.AttributeType.STRING},
                                      billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST)

        # 3. Lambda Function for Orchestration (with Polly & Translate)
        lambda_fn = _lambda.Function(self, "ClaimsProcessor",
                                     runtime=_lambda.Runtime.PYTHON_3_9,
                                     handler="processor.handler",
                                     code=_lambda.Code.from_asset("lambda"),
                                     environment={
                                         "BUCKET_NAME": claims_bucket.bucket_name,
                                         "TABLE_NAME": claims_table.table_name,
                                         "TARGET_LANGUAGE": "es",  # Example: Spanish translation
                                         "VOICE_ID": "Joanna"      # Polly voice
                                     })

        # Grant permissions to Lambda for S3 and DynamoDB
        claims_bucket.grant_read_write(lambda_fn)
        claims_table.grant_read_write_data(lambda_fn)

        # Attach IAM policy for Textract, Bedrock, Polly, Translate
        lambda_fn.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "textract:AnalyzeDocument",
                "bedrock:InvokeModel",
                "polly:SynthesizeSpeech",
                "translate:TranslateText",
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "s3:PutObject",
                "s3:GetObject"
            ],
            resources=["*"]
        ))

        # 4. API Gateway for Integration
        api = apigw.LambdaRestApi(self, "ClaimsAPI", handler=lambda_fn)

        # 5. OpenSearch Domain for Knowledge Retrieval
        search_domain = opensearch.Domain(self, "ClaimsSearch",
                                          version=opensearch.EngineVersion.OPENSEARCH_2_11,
                                          removal_policy=RemovalPolicy.DESTROY)

        # 6. Amazon Connect Instance
        connect_instance = connect.CfnInstance(self, "ConnectInstance",
                                               identity_management_type="CONNECT_MANAGED",
                                               instance_alias="AIClaimsConnect")

        # 7. Amazon Lex Bot for Chat Interface
        lex_bot = lex.CfnBot(self, "ClaimsLexBot",
                             name="ClaimsAssistantBot",
                             role_arn="arn:aws:iam::ACCOUNT_ID:role/service-role/AmazonLexBotRole",
                             data_privacy={"childDirected": False},
                             idle_session_ttl_in_seconds=300)

        # Outputs
        self.add_output("APIEndpoint", api.url)
        self.add_output("BucketName", claims_bucket.bucket_name)
        self.add_output("OpenSearchEndpoint", search_domain.domain_endpoint)
        self.add_output("ConnectInstanceId", connect_instance.ref)
        self.add_output("LexBotName", lex_bot.name)

    def add_output(self, name, value):
        from aws_cdk import CfnOutput
        CfnOutput(self, name, value=value)
