from __future__ import annotations
import os
from azure.storage.blob import BlobServiceClient

def list_blobs(connection_string, container_name):
    """
    List all blobs in the specified Azure Blob Storage container.

    :param connection_string: Connection string to the Azure Blob Storage account.
    :param container_name: The name of the container in which to list blobs.
    :return: List of blob names.
    """
    # Create a BlobServiceClient object using the connection string
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    
    # Get the container client
    container_client = blob_service_client.get_container_client(container_name)
    
    # List blobs in the container
    blob_names = []
    try:
        blob_list = container_client.list_blobs()
        for blob in blob_list:
            blob_names.append(blob.name)
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return blob_names

# Example usage
if __name__ == "__main__":
    
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = "airflow-system-dashboard-input"
    
    blobs = list_blobs(connection_string, container_name)
    print("Blobs in container:")
    for blob in blobs:
        print(blob)
