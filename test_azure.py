
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

# Explicitly load the backend .env file
load_dotenv('inter-ai-backend/.env')

print(f"Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
print(f"Key: {os.getenv('AZURE_OPENAI_API_KEY')[:5]}...")
print(f"Version: {os.getenv('AZURE_OPENAI_API_VERSION')}")
print(f"Deployment: {os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')}")

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
    azure_endpoint="https://coact-mfxe5pof-swedencentral.openai.azure.com/"
)

try:
    print("Attempting to call Azure OpenAI...")
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4.1-mini"),
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=10
    )
    print("Success!")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"FAILED: {e}")
