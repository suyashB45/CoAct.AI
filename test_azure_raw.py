
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv('inter-ai-backend/.env')

api_key = os.getenv("AZURE_OPENAI_API_KEY")
endpoint = "https://coact-ai-mfxe5pof-swedencentral.openai.azure.com/"
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", os.getenv("MODEL_NAME", "gpt-4.1-mini"))
api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

# Normalize endpoint
if not endpoint.endswith("/"):
    endpoint += "/"

# Construct URL
# Try both domains if checking manually, but here just use what is in env
url = f"{endpoint}openai/deployments/{deployment}/chat/completions?api-version={api_version}"

headers = {
    "Content-Type": "application/json",
    "api-key": api_key
}

data = {
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10
}

print(f"Testing URL: {url}")
print(f"API Key (first 5): {api_key[:5]}")

try:
    print("Sending request via requests (timeout=10s)...")
    response = requests.post(url, headers=headers, json=data, timeout=10)
    print(f"Status: {response.status_code}")
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
