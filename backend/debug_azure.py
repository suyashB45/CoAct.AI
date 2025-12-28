import os
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load env variables
load_dotenv()

print("--- DIAGNOSTIC START ---")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://coact-mfxe5pof-swedencentral.cognitiveservices.azure.com/")
api_key = os.getenv("AZURE_OPENAI_API_KEY", "jMkOm3ie4EVMVE6318aGUlo6wVQbBD9AaTLZeIf0wVCspOgqqDF0JQQJ99BIACfhMk5XJ3w3AAAAACOGmi3r")
api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

print(f"Connecting to: {endpoint}")

client = AzureOpenAI(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=endpoint
)

try:
    # In Azure OpenAI SDK, .list() often returns the DEPLOYMENTS available
    models = client.models.list()
    
    print("\n✅ CONNECTION SUCCESSFUL!")
    print("\nHere are your available Deployment Names. COPY ONE OF THESE:")
    print("-" * 50)
    
    found_embedding = False
    for model in models:
        # Check if 'embed' or 'ada' is in the name to hint strictly at embedding models
        is_embedding = "embed" in model.id.lower() or "ada" in model.id.lower()
        label = "  <-- USE THIS FOR EMBEDDINGS?" if is_embedding else ""
        
        if is_embedding: found_embedding = True
        
        print(f"Deployment Name:  '{model.id}'{label}")

    print("-" * 50)
    
    if not found_embedding:
        print("\n⚠️ CRITICAL: No obvious embedding deployment found.")
        print("Please go to Azure Portal > OpenAI > Model Deployments and create a deployment for 'text-embedding-ada-002'.")

except Exception as e:
    print(f"\n❌ CONNECTION FAILED: {e}")