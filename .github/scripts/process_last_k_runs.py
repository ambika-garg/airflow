from __future__ import annotations

import os
import json
from datetime import datetime, timedelta, timezone

from azure.storage.blob import BlobServiceClient


def preprocess_blob_data(report_group_by_testcases: dict[str, dict], test_run_data: str, k: int) -> None:
    """
    Preprocess the blob data to extract the timestamp, status of test run and last run duration.

    :param report_group_by_testcases: 
        A consolidated dictionart to store the test run data.
        Expected structure:
        {
            "TestCaseName": {
                "last_runs": [
                    {
                        "timestamp": str,  # ISO format datetime string
                        "type": str  # "failure", "success", etc.
                    },
                    ...
                ],
                "last_run_duration": float,  # Duration in seconds
                "InvocationCount": int,  # Number of times the test case was invoked in a week window
                "FailureCount": int,  # Number of times the test case failed in a week window
            }
        }
        
    :param test_run_data: 
        A JSON string containing test run details. 
        Expected structure:
        [
            {
                "classname": str,       # Name of the test case
                "timestamp": str,       # ISO format datetime string
                "failure": bool,        # True if the test failed, else False
                "time": float           # Duration of the test in seconds
            },
            ...
        ]
        
    :param k: 
        The number of last runs to be considered for each test case.
    
    :return: Updates the report_group_by_testcases dict with the test run data inplace.
    """
    test_run = json.loads(test_run_data)
    for _index, item in enumerate(test_run):
        testname = item["classname"]
        if testname not in report_group_by_testcases:
            # Initialize new test case.
            report_group_by_testcases[testname] = {
                "last_runs": [
                    {
                        "timestamp": item["timestamp"],
                        "type": "failure"
                        if item["failure"]
                        else "success",  # TODO: Need to consider all the test cases like failure, success, skipped, cancelled, etc.
                    }
                ],
                "last_run_duration": item["time"],
                "InvocationCount": 1,
                "FailureCount": 1 if item["failure"] else 0,
                "SuccessCount": 0 if item["failure"] else 1,
            }
        else:
            # Update existing test case.
            if len(report_group_by_testcases[testname]["last_runs"]) < k:
                report_group_by_testcases[testname]["last_runs"].append(
                    {"timestamp": item["timestamp"], "type": "failure" if item["failure"] else "success"}
                )
            
            report_group_by_testcases[testname]["InvocationCount"] += 1
            if item["failure"]:
                report_group_by_testcases[testname]["FailureCount"] += 1
            else:
                report_group_by_testcases[testname]["SuccessCount"] += 1
            
    return


def upload_blob(connection_string: str, container_name: str, blob_name: str, data: str) -> None:
    """
    Upload a file to Azure Blob Storage.

    :param connection_string: Provide the connection string to the Azure Storage account.
    :param container_name: Specify the name of the container where the blob will be uploaded.
    :param blob_name: Specify the name of the blob in the container.
    :param file_path: Provide the path to the local file to be uploaded.
    :raises ResourceExistsError: Raise if the blob already exists and the upload is not allowed to overwrite.
    """
    try:
        # Create a BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)

        # Create a ContainerClient
        container_client = blob_service_client.get_container_client(container_name)

        # Create a BlobClient
        blob_client = container_client.get_blob_client(blob_name)

        # Upload the file
        blob_client.upload_blob(data, overwrite=True)  # Set overwrite=True to replace if blob already exists

        print(f"Data uploaded to blob '{blob_name}' in container '{container_name}'.")

    except Exception as e:
        raise ValueError(f"An error occurred while uploading the blob to Gold container {container_name}: {e}")

def fetch_all_blobs(connection_string: str, container_name: str) -> list:
    """
        Fetch all the blobs from the Azure blob storage container.
        Returns:
            List of blob names in the container and timestamp.
    """
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    
    try:
        blobs = []
        blob_list = container_client.list_blobs()
        
        for blob in blob_list:
            # Extract timestamp from the blob name
            if blob.name.startswith("pytest-report-") and blob.name.endswith(".json"):
                try:
                    timestamp_str = blob.name.split("pytest-report-")[1].replace(".json", "")
                    blob_timestamp = datetime.fromisoformat(timestamp_str)
                    blobs.append({"name": blob.name, "timestamp": blob_timestamp})
                except ValueError:
                    print(f"Skipping invalid blob: {blob.name}")
                    
        return blobs
    except Exception as e:
        raise ValueError(f"An unexpected error occured while fetching the blobs from Azure Blob storage container {container_name}: {e}")

def download_blob(connection_string: str, container_name: str, blob_name: str) -> str:
    """
    Download a blob from Azure Blob Storage.

    :param connection_string: Provide the connection string to the Azure Storage account.
    :param container_name: Specify the name of the container where the blob is stored.
    :param blob_name: Specify the name of the blob to be downloaded.
    :return: The content of the blob.
    """
    try:
        # Create a BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)

        # Create a ContainerClient
        container_client = blob_service_client.get_container_client(container_name)

        # Create a BlobClient
        blob_client = container_client.get_blob_client(blob_name)

        # Download the blob
        blob_data = blob_client.download_blob().readall()

        return blob_data

    except Exception as e:
        raise ValueError(f"An error occurred while downloading the blob {blob_name} from container {container_name}: {e}")

def consolidate_runs(connection_string: str, container_name: str, k=10) -> None:
    """
    Combine the last k runs of the test cases and consolidate them into a single report.

    :param connection_string: Connection string to the Azure Blob Storage account.
    :param container_name: The name of the container in which blobs are listed.

    :return: The consolidated report of the last k runs of the test cases.
    """
    # A test run contains the run report of the system tests present in the Microsoft Fabric Apache Airflow repository.
    # Each test run is represented as a blob in the storage container. The blob includes detailed status and results 
    # for all system tests executed during that particular run.
    
    # Fetch all blobs from azure blob storage container
    blobs = fetch_all_blobs(connection_string, container_name)
    
    # Sort the blobs by timestamp in descending order
    blobs.sort(key=lambda b: b["timestamp"], reverse=True)
    
    # Calculate one week ago
    one_week_ago = datetime.now(timezone.utc) - timedelta(weeks=1)

    # Filter blobs that are one week old
    one_week_old_blobs = [blob for blob in blobs if blob["timestamp"] >= one_week_ago]
    
    # Prepare the consolidated report
    report_group_by_testcases: dict = {}
    
    try:
        for blob in one_week_old_blobs:
            test_run_data = download_blob(connection_string, container_name, blob["name"])

            # Preprocess the blob data - this will add the test run to the list of runs for a test case
            preprocess_blob_data(report_group_by_testcases, test_run_data, k)

        # Convert the dictionary to a list
        report_group_by_testcases_list = [
            {"name": key, **value} for key, value in report_group_by_testcases.items()
        ]
        
        return report_group_by_testcases_list
    except Exception as e:
        raise ValueError(f"An error occurred: {e}")


if __name__ == "__main__":
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    silver_container_name = os.getenv("SILVER_AZURE_STORAGE_CONTAINER_NAME")
    gold_container_name = os.getenv("GOLD_AZURE_STORAGE_CONTAINER_NAME")

    if connection_string is None:
        raise ValueError("Connection string is not provided for Azure blob storage.")
    if silver_container_name is None:
        raise ValueError("Silver container name is not provided for Azure Blob Storage.")
    if gold_container_name is None:
        raise ValueError("Gold container name is not provided for Azure Blob Storage.")

    workflow_run_group_by_testcase = consolidate_runs(connection_string, silver_container_name, k=10)
    
    upload_blob(
        connection_string,
        gold_container_name,
        "gold-report.json",
        json.dumps(workflow_run_group_by_testcase),
    )
