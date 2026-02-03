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
        # Validate event structure
        if 'Records' not in event or len(event['Records']) == 0:
            raise ValueError("Invalid event: Missing S3 record information")

        s3_record = event['Records'][0]['s3']
        file_name = s3_record['object']['key']

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
            prompt = f"Summarize this insurance claim for elderly users:\n{document_text}"
            bedrock_response = bedrock_client.invoke_model(
                modelId="anthropic.claude-v2",
                body=json.dumps({"input": prompt})
            )
            response_body = json.loads(bedrock_response['body'].read())
            ai_summary = response_body.get('completion', 'No summary generated.')
        except (BotoCoreError, ClientError, json.JSONDecodeError) as e:
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
