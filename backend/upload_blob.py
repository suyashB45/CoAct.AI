from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv

load_dotenv()

connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

def upload_pdf_to_blob(conn_str: str, container_name: str, blob_name: str, pdf_path: str) -> str:
    # Create client with connection string
    blob_service_client = BlobServiceClient.from_connection_string(conn_str)

    # Ensure container exists
    container_client = blob_service_client.get_container_client(container_name)
    try:
        container_client.create_container()
    except Exception:
        pass

    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

    with open(pdf_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)

    url = blob_client.url
    print(f"Uploaded {pdf_path} to blob '{blob_name}' in container '{container_name}'")
    print(f"Blob URL: {url}")
    return url

if __name__ == "__main__":
    # conn_str = connection_string
    container = "coact-ai-reports"
    blob = "report.pdf"
    local_pdf = "report.pdf"

    upload_pdf_to_blob(connection_string, container, blob, local_pdf)
