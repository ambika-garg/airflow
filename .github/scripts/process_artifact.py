from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET

from azure.storage.blob import BlobServiceClient

XML_ARTIFACT_PATH = "pytest-report/pytest-report.xml"
JSON_OUTPUT_PATH = "pytest-report/processed-report.json"

def upload_blob(connection_string: str, container_name: str, blob_name: str, file_path: str) -> None:
    """
    Upload a file to Azure Blob Storage.

    :param connection_string: Provide the connection string to the Azure Storage account.
    :param container_name: Specify the name of the container where the blob will be uploaded.
    :param blob_name: Define the name of the blob in the container.
    :param file_path: Indicate the path to the local file to be uploaded.
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
        with open(file_path, "rb") as data:
            blob_client.upload_blob(
                data, overwrite=True
            )  # Set overwrite=True to replace if blob already exists

        print(f"File '{file_path}' uploaded to blob '{blob_name}' in container '{container_name}'.")

    except Exception as e:
        raise ValueError(f"An error occurred while uploading the blob to Gold container {container_name}: {e}")


def parse_xml_to_json(xml_content):
    """
    Parses XML content and converts it to a JSON-like structure.
    Args:
        xml_content (str): A string containing XML data.
    Returns:
        tuple: A tuple containing:
            - testcases (list): A list of dictionaries, each representing a testcase with the following keys:
                - name (str): The name of the testcase.
                - time (str): The time taken for the testcase.
                - classname (str): The classname of the testcase.
                - failure (str): The failure message of the testcase, if any.
                - timestamp (str): The timestamp of the testsuite.
            - timestamp (str): The timestamp of the testsuite.
    """
    # Parse XML content
    root = ET.fromstring(xml_content)

    # Helper function to convert XML elements to dictionary
    def elem_to_dict(elem):
        # Convert attributes to dictionary
        data = elem.attrib.copy()
        # Add children if they exist
        if elem.text and elem.text.strip():
            data["text"] = elem.text.strip()
        # Add child elements
        for child in elem:
            child_data = elem_to_dict(child)
            if child.tag in data:
                # If the tag already exists, make it a list
                if isinstance(data[child.tag], list):
                    data[child.tag].append(child_data)
                else:
                    data[child.tag] = [data[child.tag], child_data]
            else:
                data[child.tag] = child_data
        return data

    # Convert the root element to dictionary
    data = elem_to_dict(root)

    # Create a testcase-wise structure
    testcases = []
    if "testsuite" in data:
        testsuite = data["testsuite"]
        timestamp = testsuite.get("timestamp", None)
        if "testcase" in testsuite:
            for testcase in testsuite["testcase"]:
                testcaseobj = {}
                testcaseobj["name"] = testcase.get("name", None)
                testcaseobj["time"] = testcase.get("time", None) # Time taken for the testcase to run
                testcaseobj["classname"] = testcase.get("classname", None)
                testcaseobj["failure"] = testcase.get("failure", None)
                testcaseobj["timestamp"] = timestamp # Timestamp of the testsuite

                testcases.append(testcaseobj)
                
                # TODO: If test is a failure, we can send a notification to the team

    return testcases, timestamp


def process_file(file_path):
    """
    Processes an XML file, converts its content to JSON, and generates a blob name based on current timestamp.

    Args:
        file_path (str): The path to the XML file to be processed.

    Returns:
        tuple: A tuple containing:
            - blob_name (str): The name of the blob to be uploaded, based on the timestamp when test was executed.
            - json_data (str): JSON list in the below format:
            [
                {
                    "name": "test_run",
                    "time": "36.376",
                    "classname": "providers.tests.system.microsoft.fabric.example_fabric_notebook_run",
                    "failure": null,
                    "timestamp": "2024-12-09T22:15:02.123111+00:00"
                },
                {
                    "name": "test_run",
                    "time": "2.525",
                    "classname": "providers.tests.system.microsoft.fabric.example_fabric_pipeline_run",
                    "failure": null,
                    "timestamp": "2024-12-09T22:15:02.123111+00:00"
                }
            ]
    """
    if os.path.isfile(file_path):
        with open(file_path) as file:
            xml_content = file.read()

    # Convert XML to JSON
    data, timestamp = parse_xml_to_json(xml_content)

    # Convert to JSON string
    json_data = json.dumps(data, indent=4)

    # Blob name
    blob_name = f"pytest-report-{timestamp}.json"
    return blob_name, json_data


def save_json(json_data, file_path):
    with open(file_path, "w") as json_file:
        json_file.write(json_data)


if __name__ == "__main__":
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    gold_container_name = os.getenv("GOLD_AZURE_STORAGE_CONTAINER_NAME")

    if not connection_string:
        raise ValueError("No connection string provided for Azure Blob Storage.")
    if gold_container_name is None:
        raise ValueError("Gold container name is not provided for Azure Blob Storage.")

    if os.path.exists(XML_ARTIFACT_PATH):
        blob_name, json_data = process_file(XML_ARTIFACT_PATH)
 
        save_json(json_data, JSON_OUTPUT_PATH)

        upload_blob(
            connection_string=connection_string,
            container_name=gold_container_name,
            blob_name=blob_name,
            file_path=JSON_OUTPUT_PATH,
        )
    else:
        print(f"Artifact not found at {XML_ARTIFACT_PATH}")
