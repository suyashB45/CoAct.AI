
import os
import httpx
from openai import AzureOpenAI
from dotenv import load_dotenv

# Redefine everything locally to be absolutely sure
load_dotenv('inter-ai-backend/.env')

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
key = os.getenv("AZURE_OPENAI_API_KEY")
version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4.1-mini")

print(f"Testing Azure OpenAI Full Integration", flush=True)
print(f"Endpoint: {endpoint}", flush=True)
print(f"Deployment: {deployment}", flush=True)

# Create Client exactly as in cli_report
http_client = httpx.Client(trust_env=False, verify=False, timeout=10.0)

client = AzureOpenAI(
    api_key=key,
    api_version=version,
    azure_endpoint=endpoint,
    http_client=http_client
)

print("Client created. Sending request...", flush=True)

try:
    response = client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=10
    )
    print("Success!", flush=True)
    print(response.choices[0].message.content, flush=True)
except Exception as e:
    print(f"FAILED: {e}", flush=True)
