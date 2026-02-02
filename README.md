# Smart Claims Assistant (AWS)

**Overview** ✅

This repository contains an AWS Serverless application (SAM) for the Smart Claims Assistant. It includes Lambda functions, a Step Functions state machine, and helper scripts to build, run locally, and deploy to AWS.

---

## Prerequisites 🔧

Install the tools below (Windows):

- **Git** — clone the repo: https://git-scm.com/
- **Python 3.9+** — https://www.python.org/downloads/
  - Verify: `python --version`
- **AWS CLI v2** — https://docs.aws.amazon.com/cli/
  - Quick install (Windows): `winget install --id Amazon.AWSCLI`
  - Verify: `aws --version`
- **AWS SAM CLI** — https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html
  - Install via Chocolatey: `choco install -y aws-sam-cli` or follow AWS docs
  - Verify: `sam --version`
- **Docker Desktop** — required for `sam local` and container builds: https://www.docker.com/
  - Make sure Docker is running before using SAM local
- (Optional) **Node.js / npm** — some SAM features may use node-based tooling: https://nodejs.org/

> Note: On Windows it's recommended to use **Git Bash** or **WSL** when running the provided shell scripts in `scripts/`.

---

## Local Development — Setup (Quick) ⚡

1. Clone the repository

```bash
git clone <repo-url>
cd smart-claims-assistant--aws
```

2. Create and activate a Python virtual environment

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

CMD:

```bat
python -m venv .venv
.\.venv\Scripts\activate.bat
```

Git Bash / WSL:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

3. Install Python dependencies

```bash
pip install -r requirements.txt
```

4. Verify environment

```bash
python -c "import aws_lambda_powertools; print('powertools ok')"
```

---

## Run Locally 🔁

- Start local API (if defined in `template.yaml`):

```bash
sam local start-api -t template.yaml
```

- Invoke a function directly (use a logical name from `template.yaml`, or check `template.yaml` for the function name):

```bash
sam local invoke <FunctionLogicalId> -e events/api_event.json
```

- Use provided helper script (preferred for convenience):

```bash
# From Git Bash or WSL
bash scripts/local.sh
```

> Tip: If an invocation needs Docker, ensure Docker Desktop is running.

---

## Deploy to AWS ☁️

1. Configure AWS credentials and default region

```bash
aws configure
```

2. Create (or choose) an S3 bucket for SAM artifacts (optional — SAM can create one during guided deploy)

```bash
aws s3 mb s3://<your-deploy-bucket> --region us-east-1
```

3. Build and deploy with SAM (guided)

```bash
sam build
sam deploy --guided --stack-name smart-claims-assistant
```

During `sam deploy --guided`, you'll be asked for the S3 bucket name, AWS region, stack name, and whether to save the configuration to `samconfig.toml` (recommended).

4. Or use the included script (runs `sam build` and `sam deploy`):

```bash
bash scripts/deploy.sh
```

> After deploy, SAM/CloudFormation outputs will show service endpoints and ARNs. Use the `Outputs` to find the API endpoint and Step Function ARN.

---

## Step Functions

The state machine definition is in `statemachine/claims_flow.asl.json`. The SAM deployment will create the state machine defined in `template.yaml`.

- To execute the state machine from the AWS Console or CLI, use the ARN printed in the CloudFormation outputs.

---

## Useful Commands & Scripts 🔍

- `bash scripts/build.sh` — run a full `sam build`
- `bash scripts/deploy.sh` — build and deploy to AWS
- `bash scripts/local.sh` — run locally via SAM
- `events/api_event.json` — example event for local `sam local invoke`

---

## Troubleshooting ⚠️

- Docker errors: ensure Docker Desktop is running and that your user has permissions to run Docker.
- Permission/AccessDenied during deploy: ensure IAM user has rights for CloudFormation, S3, Lambda, IAM, Step Functions, API Gateway, and related services.
- If `sam` commands fail on Windows, try Git Bash or WSL to run the included scripts.

---

## Contributing & Support 🤝

- Open an issue or PR if you need help or want to add features.
- Contact the repository owner for access or deployment questions.

---

**Happy hacking!** ✨