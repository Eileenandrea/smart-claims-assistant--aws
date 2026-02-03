
#!/bin/bash
set -e

# Variables
STACK_NAME="AiClaimsAssistantStack"
LAMBDA_DIR="lambda"
ZIP_FILE="lambda.zip"

echo "=== Packaging Lambda Function ==="
cd $LAMBDA_DIR
zip -r ../$ZIP_FILE .
cd ..

echo "=== Installing CDK Dependencies ==="
pip install -r requirements.txt

echo "=== Synthesizing CDK Stack ==="
cdk synth

echo "=== Deploying CDK Stack ==="
cdk deploy $STACK_NAME --require-approval never

echo "=== Deployment Complete ==="
echo "Lambda packaged as $ZIP_FILE and stack deployed successfully!"
