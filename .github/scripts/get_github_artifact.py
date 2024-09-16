import requests
import os
from azure.storage.blob import BlobServiceClient


# def list_artifacts(repo_name, github_token, github_runid):
#     """
#     List all artifacts in a GitHub repository.

#     :param repo_owner: Owner of the repository.
#     :param repo_name: Name of the repository.
#     :param github_token: GitHub Personal Access Token.
#     :return: List of artifact names and IDs.
#     """
#     url = f"https://api.github.com/repos/{repo_name}/actions/runs/{github_runid}/artifacts"
#     print("URL:", url)
#     headers = {
#         "Authorization": f"Bearer {github_token}",
#         "Accept": "application/vnd.github+json"
#     }
#     response = requests.get(url, headers=headers)
    

#     if response.status_code == 200:
#         artifacts = response.json()
#         print(artifacts)
#         # .get('artifacts', [])
#         # return [(artifact['id'], artifact['name']) for artifact in artifacts]
#     else:
#         raise Exception(f"Failed to list artifacts: {response.status_code} {response.text}")

# # Example usage
# if __name__ == "__main__":
#     repo_name = os.getenv("REPO_NAME")
#     github_token = os.getenv("GITHUB_TOKEN")
#     github_runid = os.getenv("GITHUB_RUN_ID")

#     artifacts = list_artifacts(repo_name, github_token, github_runid)
    # for artifact_id, artifact_name in artifacts:
    #     print(f"Artifact ID: {artifact_id}, Name: {artifact_name}")


# import zipfile

# # Define the path to the downloaded artifact
# artifact_path = 'test-reports.zip'

# # Unzip the artifact
# with zipfile.ZipFile(artifact_path, 'r') as zip_ref:
#     zip_ref.extractall('test-reports')

# # Read and print the content of a file from the artifact
# with open('test-reports/sample-artifact.xml', 'r') as file:
#     content = file.read()
#     print("Content of sample.txt:", content)

import os

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
            blob_client.upload_blob(data, overwrite=True)  # Set overwrite=True to replace if blob already exists

        print(f"File '{file_path}' uploaded to blob '{blob_name}' in container '{container_name}'.")

    except Exception as e:
        print(f"An error occurred: {e}")



def process_file(file_path):
    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            content = file.read()
            print("Content of the file:", content)
        print(f"File: {file_path}")

def upload_blob(file_path):
    print(f"Uploading {file_path} to Azure Blob Storage")
    # Upload the file to Azure Blob Storage here

if __name__ == "__main__":
    artifact_path = 'test-report/sample-artifact.xml'  # Path where the artifact was downloaded
    connection_string = os.getenv("AZURE_BLOB_STORAGE_CONNECTION_STRING")
    container_name = "airflow-system-dashboard-output"
    
    if os.path.exists(artifact_path):
        process_file(artifact_path)
        upload_blob(connection_string=connection_string, container_name = container_name, blob_name="Blob_from_rebase_workflow.xml", file_path=artifact_path)
    else:
        print(f"Artifact not found at {artifact_path}")