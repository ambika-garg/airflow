from __future__ import annotations
import json
import os
from azure.storage.blob import BlobServiceClient

def preprocess_blob_data(report_group_by_testcases, blob_data):
    """
    Preprocess the blob data to extract the required information.

    :param blob_data: The data read from the blob.
    :return: Preprocessed data.
    """
    test_run = json.loads(blob_data)
    for index, item in enumerate(test_run):
        testname = item["name"]
        if testname not in report_group_by_testcases:
            report_group_by_testcases[testname] = {
                "last_runs": [
                    {
                        "timestamp": item["timestamp"],
                        "type": "failure" if item["failure"] else "success" # Improve it, need to consider all the test cases like failure, success, skipped, cancelled, etc.
                    }
                ]
            }
        else:
            report_group_by_testcases[testname]["last_runs"].append({
                "timestamp": item["timestamp"],
                "type": "failure" if item["failure"] else "success"
            })


def upload_blob(connection_string: str, container_name: str, blob_name: str, file_path: str) -> None:
    """
    Uploads a file to Azure Blob Storage.

    :param connection_string: The connection string to the Azure Storage account.
    :param container_name: The name of the container where the blob will be uploaded.
    :param blob_name: The name of the blob in the container.
    :param file_path: The path to the local file to be uploaded.
    :raises ResourceExistsError: If the blob already exists and the upload is not allowed to overwrite.
    """
    try:
        # Create a BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)

        # Create a ContainerClient
        container_client = blob_service_client.get_container_client(container_name)

        # Create a BlobClient
        blob_client = container_client.get_blob_client(blob_name)

        # Upload the file
        with open(file_path, "rb") as data:
            blob_client.upload_blob(
                data, overwrite=True
            )  # Set overwrite=True to replace if blob already exists

        print(f"File '{file_path}' uploaded to blob '{blob_name}' in container '{container_name}'.")

    except Exception as e:
        print(f"An error occurred: {e}")

def consolidate_runs(connection_string, container_name, k=10):
    """
    List all blobs in the specified Azure Blob Storage container.

    :param connection_string: Connection string to the Azure Blob Storage account.
    :param container_name: The name of the container in which blobs are listed.
    :return: List of blob names.
    """
    # Create a BlobServiceClient object using the connection string
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    
    # Get the container client
    container_client = blob_service_client.get_container_client(container_name)
    
    report_group_by_testcases = {}
    try:
        blob_count = 0
        blob_list = container_client.list_blobs()
        if blob_list is not None:
            print("blob_list", blob_list)
        else:
            print("No blobs found or container doesn't exist.")
        # blob_list.sort(reverse=True)

        # for blob in blob_list:
        #     if blob_count > k:
        #         break
        #     blob_client = container_client.get_blob_client(blob)
        #     blob_data = blob_client.download_blob().readall()
        #     blob_count += 1
            
        #     # Preprocess the blob data
        #     preprocess_blob_data(report_group_by_testcases, blob_data)
        
        # # Convert the dictionary to a list
        # report_group_by_testcases_list = [{"name": key, **value} for key, value in report_group_by_testcases.items()]
        
        # # Write it to json file
        # with open("consolidate-blob/report.json", "w") as json_file:
        #     json.dump(report_group_by_testcases_list, json_file, indent=4)
        
        # # Upload blob
        # upload_blob(connection_string, "consolidate-blob", "gold-report.json", "consolidate-blob/report.json")
        
    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
if __name__ == "__main__":
    
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = "airflow-system-dashboard-output"
    
    blobs = consolidate_runs(connection_string, container_name, k=10)
    print("Blobs in container:")
    for blob in blobs:
        print(blob)



