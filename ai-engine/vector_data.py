import json
import faiss
import numpy as np
from openai import AzureOpenAI
import os
from dotenv import load_dotenv
load_dotenv()

# -------------------
# 1. Setup
# -------------------
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = "2024-12-01-preview"

if not endpoint or not api_key:
    raise ValueError("Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY environment variables.")

if not endpoint or not api_key:
    raise ValueError("Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY environment variables.")

# AzureOpenAI format (2024+)
client = AzureOpenAI(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=endpoint
)

DATA_FILE = "framework_questions.json"
INDEX_FILE = "framework_faiss.index"

# -------------------
# 2. Load GROW dataset
# -------------------
with open(DATA_FILE, "r") as f:
    data = json.load(f)

# -------------------
# 3. Generate embeddings and build FAISS index
# -------------------
print("Generating embeddings...")

dim = 1536  # embedding dimension for text-embedding-ada-002
index = faiss.IndexFlatL2(dim)

# Store metadata separately
questions = []
stages = []
frameworks = []

embeddings = []

for item in data:
    q = item["question"]
    
    # Get embedding
    emb = client.embeddings.create(
        model="text-embedding-ada-002",
        input=q
    ).data[0].embedding

    embeddings.append(emb)
    questions.append(q)
    stages.append(item["stage"])
    frameworks.append(item["framework"])
emb_matrix = np.array(embeddings).astype("float32")
print("Embedding matrix shape:", emb_matrix.shape)
print("FAISS index dimension:", dim)
if emb_matrix.shape[1] != dim:
    raise ValueError(f"Embedding dimension mismatch: got {emb_matrix.shape[1]}, expected {dim}")
index.add(emb_matrix)

# Save index + metadata
faiss.write_index(index, INDEX_FILE)

meta = {"questions": questions, "stages": stages, "frameworks": frameworks}
with open("framework_meta.json", "w") as f:
    json.dump(meta, f)

print(f"✅ FAISS index built with {len(questions)} questions")
print(f"Index saved to {INDEX_FILE} and metadata to framework_meta.json")