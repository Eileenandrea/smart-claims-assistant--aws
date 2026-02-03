
#!/usr/bin/env python3
import aws_cdk as cdk
from ai_claims_stack import AiClaimsStack

app = cdk.App()
AiClaimsStack(app, "AiClaimsAssistantStack")
app.synth()
