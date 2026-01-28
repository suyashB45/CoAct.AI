
import httpx
import os
from dotenv import load_dotenv

load_dotenv('inter-ai-backend/.env')

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
key = os.getenv("AZURE_OPENAI_API_KEY")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4.1-mini")
version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={version}"

headers = {
    "api-key": key,
    "Content-Type": "application/json"
}

payload = {
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10
}

print(f"Testing RAW POST to {url}", flush=True)

try:
    with httpx.Client(trust_env=False, verify=False, timeout=3.0) as client:
        print("Sending request...", flush=True)
        r = client.post(url, headers=headers, json=payload)
        print(f"Response Code: {r.status_code}", flush=True)
        print(f"Response Text: {r.text}", flush=True)
except Exception as e:
    print(f"Exception: {e}", flush=True)
