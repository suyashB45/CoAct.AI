
import os
import httpx
import time
from dotenv import load_dotenv

load_dotenv('inter-ai-backend/.env')

endpoint = "https://coact-mfxe5pof-swedencentral.openai.azure.com/"
api_key = os.getenv("AZURE_OPENAI_API_KEY")

print(f"Testing httpx connection to {endpoint}...", flush=True)

# Test 1: Default
print("\n--- Test 1: Default Environment ---", flush=True)
try:
    with httpx.Client(timeout=5) as client:
        r = client.get(endpoint)
        print(f"Status: {r.status_code}", flush=True)
except Exception as e:
    print(f"Error: {e}", flush=True)

# Test 2: NO_PROXY
print("\n--- Test 2: With NO_PROXY ---", flush=True)
os.environ['NO_PROXY'] = 'azure.com,microsoft.com,windows.net,localhost,127.0.0.1'
os.environ['no_proxy'] = 'azure.com,microsoft.com,windows.net,localhost,127.0.0.1'
try:
    with httpx.Client(timeout=5, trust_env=True) as client:
        r = client.get(endpoint)
        print(f"Status: {r.status_code}", flush=True)
except Exception as e:
    print(f"Error: {e}", flush=True)

# Test 3: Explicit trust_env=False (Best way to disable proxies in httpx)
print("\n--- Test 3: trust_env=False ---", flush=True)
try:
    with httpx.Client(timeout=5, trust_env=False) as client:
        r = client.get(endpoint)
        print(f"Status: {r.status_code}", flush=True)
except Exception as e:
    print(f"Error: {e}", flush=True)

# Test 4: Verify=False
print("\n--- Test 4: Verify=False ---", flush=True)
try:
    with httpx.Client(timeout=5, verify=False) as client:
        r = client.get(endpoint)
        print(f"Status: {r.status_code}", flush=True)
except Exception as e:
    print(f"Error: {e}", flush=True)
