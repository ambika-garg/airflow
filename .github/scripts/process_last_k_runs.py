from __future__ import annotations

import json
import os

from azure.storage.blob import BlobServiceClient


def preprocess_blob_data(report_group_by_testcases: dict, test_run_data) -> None:
    """
    Preprocess the blob data to extract the required information.

    :param report_group_by_testcases: The consolidated dict to store the test run data.
    :param test_run_data: Test run data to added in the consolidated dict `report group by testcases`.
    :return: None.
    """
    test_run = json.loads(test_run_data)
    for _index, item in enumerate(test_run):
        testname = item["classname"]
        if testname not in report_group_by_testcases:
            report_group_by_testcases[testname] = {
                "last_runs": [
                    {
                        "timestamp": item["timestamp"],
                        "type": "failure"
                        if item["failure"]
                        else "success",  # Improve it, need to consider all the test cases like failure, success, skipped, cancelled, etc.
                    }
                ],
                "last_run_duration": item["time"],
            }
        else:
            report_group_by_testcases[testname]["last_runs"].append(
                {"timestamp": item["timestamp"], "type": "failure" if item["failure"] else "success"}
            )
            # Overwrite the last run duration as blobs are sorted by timestamp
            report_group_by_testcases[testname]["last_run_duration"] = item["time"]


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
        print(f"An error occurred: {e}")


def consolidate_runs(connection_string: str, container_name: str, k=10) -> None:
    """
    List all blobs in the specified Azure Blob Storage container.

    :param connection_string: Connection string to the Azure Blob Storage account.
    :param container_name: The name of the container in which blobs are listed.
    :return: None
    """
    # Create a BlobServiceClient object using the connection string
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    # Get the container client
    container_client = blob_service_client.get_container_client(container_name)

    report_group_by_testcases: dict = {}
    try:
        blob_count = 0
        blob_list = container_client.list_blobs()
        if blob_list is not None:
            sorted_blobs = sorted(blob_list, key=lambda b: b.name)
            for blob in sorted_blobs:
                if blob_count > k:
                    break
                blob_client = container_client.get_blob_client(blob)  # type: ignore
                test_run_data = blob_client.download_blob().readall()
                blob_count += 1

                # Preprocess the blob data
                preprocess_blob_data(report_group_by_testcases, test_run_data)

            # Convert the dictionary to a list
            report_group_by_testcases_list = [
                {"name": key, **value} for key, value in report_group_by_testcases.items()
            ]

            upload_blob(
                connection_string,
                "consolidate-blob",
                "gold-report.json",
                json.dumps(report_group_by_testcases_list),
            )
        else:
            print("No blobs found or container doesn't exist.")
    except Exception as e:
        print(f"An error occurred: {e}")


# Example usage
if __name__ == "__main__":
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = "airflow-system-dashboard-output"

    if connection_string is None:
        raise ValueError("Connection string is not provided for Azure blob storage.")

    consolidate_runs(connection_string, container_name, k=10)
