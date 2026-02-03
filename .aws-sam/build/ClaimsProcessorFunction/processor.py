import os
import json
import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Initialize AWS clients
textract_client = boto3.client('textract')
bedrock_client = boto3.client('bedrock-runtime')
dynamodb_client = boto3.client('dynamodb')
polly_client = boto3.client('polly')
translate_client = boto3.client('translate')
s3_client = boto3.client('s3')

BUCKET_NAME = os.environ.get("BUCKET_NAME")
TABLE_NAME = os.environ.get("TABLE_NAME")
TARGET_LANGUAGE = "es"
VOICE_ID = "Joanna"


def handler(event, context):
    try:
        records = None

        # Case 1: S3 trigger
        if "Records" in event:
            records = event["Records"]

        # Case 2: API Gateway trigger
        elif "body" in event and event["body"]:
            body = event["body"]
            if isinstance(body, str):
                body = json.loads(body)
            records = body.get("Records")

        if not records or len(records) == 0:
            raise ValueError("Invalid event: Missing S3 record information")

        s3_record = records[0]["s3"]
        bucket_name = s3_record["bucket"]["name"]
        file_name = s3_record["object"]["key"]
# ------------------------------------
        # Step 1: Extract text using Textract
        try:
            textract_response = textract_client.analyze_document(
                Document={'S3Object': {'Bucket': BUCKET_NAME, 'Name': file_name}},
                FeatureTypes=["FORMS", "TABLES"]
            )
            extracted_text = [block['Text'] for block in textract_response.get('Blocks', []) if block['BlockType'] == 'LINE']
            document_text = "\n".join(extracted_text) if extracted_text else "No text found"
        except (BotoCoreError, ClientError) as e:
            return error_response("Textract failed", str(e))

        # Step 2: Summarize using Bedrock
        try:
            bedrock_response = bedrock_client.invoke_model(
                modelId="anthropic.claude-3-haiku-20240307-v1:0",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 300,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Summarize this insurance claim for elderly users:\n{document_text}"
                        }
                    ]
                })
            )

            response_body = json.loads(bedrock_response["body"].read())
            ai_summary = response_body["content"][0]["text"]

        except (BotoCoreError, ClientError, KeyError, json.JSONDecodeError) as e:
            return error_response("Bedrock summarization failed", str(e))
        # Step 3: Translate summary
        try:
            translated_summary = translate_client.translate_text(
                Text=ai_summary,
                SourceLanguageCode="en",
                TargetLanguageCode=TARGET_LANGUAGE
            )['TranslatedText']
        except (BotoCoreError, ClientError) as e:
            translated_summary = "Translation failed"

        # Step 4: Convert summary to speech using Polly
        audio_file = f"{file_name}-summary.mp3"
        try:
            polly_response = polly_client.synthesize_speech(
                Text=ai_summary,
                OutputFormat="mp3",
                VoiceId=VOICE_ID
            )
            s3_client.put_object(Bucket=BUCKET_NAME, Key=audio_file, Body=polly_response['AudioStream'].read())
        except (BotoCoreError, ClientError) as e:
            audio_file = "Audio generation failed"

        # Step 5: Store metadata in DynamoDB
        try:
            dynamodb_client.put_item(
                TableName=TABLE_NAME,
                Item={
                    'ClaimID': {'S': file_name},
                    'Summary': {'S': ai_summary},
                    'TranslatedSummary': {'S': translated_summary},
                    'OriginalText': {'S': document_text},
                    'AudioFile': {'S': audio_file}
                }
            )
        except (BotoCoreError, ClientError) as e:
            return error_response("DynamoDB write failed", str(e))

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Claim processed successfully!",
                "summary": ai_summary,
                "translated_summary": translated_summary,
                "audio_file": audio_file
            })
        }

    except Exception as e:
        return error_response("Unexpected error", str(e))


def error_response(title, details):
    return {
        "statusCode": 500,
        "body": json.dumps({"error": title, "details": details})
    }
