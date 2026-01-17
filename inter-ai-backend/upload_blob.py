import os
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv()

# Get connection string from environment variable
connection_string = os.getenv(
    "AZURE_STORAGE_CONNECTION_STRING",
    "DefaultEndpointsProtocol=https;AccountName=storage1coactai;AccountKey=HsziK+BLsQkuMkInjbu34FFe62F2/8/uxEvuGgTSkI5YxLM5S8wGfdrsSftIuZFZU98G+FvGt/gg+AStUz135A==;EndpointSuffix=core.windows.net"
)

CONTAINER_NAME = "coact-ai-reports"


def upload_pdf_to_blob(pdf_path: str, blob_name: str = None, container_name: str = CONTAINER_NAME) -> str:
    """
    Upload a PDF file to Azure Blob Storage.
    
    Args:
        pdf_path: Path to the local PDF file
        blob_name: Name for the blob (defaults to filename)
        container_name: Azure container name
    
    Returns:
        URL of the uploaded blob
    """
    if not connection_string:
        raise ValueError("AZURE_STORAGE_CONNECTION_STRING not configured")
    
    # Use filename as blob name if not specified
    if blob_name is None:
        blob_name = os.path.basename(pdf_path)
    
    # Create client with connection string
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    # Ensure container exists
    container_client = blob_service_client.get_container_client(container_name)
    try:
        container_client.create_container()
        print(f"✅ Created container '{container_name}'")
    except Exception:
        pass  # Container already exists

    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

    with open(pdf_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)

    url = blob_client.url
    print(f"✅ Uploaded '{pdf_path}' to blob '{blob_name}'")
    print(f"📎 Blob URL: {url}")
    return url


if __name__ == "__main__":
    # Test upload
    container = "coact-ai-reports"
    local_pdf = "grow_report.pdf"
    
    if os.path.exists(local_pdf):
        upload_pdf_to_blob(local_pdf)
    else:
        print(f"❌ File not found: {local_pdf}")