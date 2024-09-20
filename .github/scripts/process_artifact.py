from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET

from azure.storage.blob import BlobServiceClient

XML_ARTIFACT_PATH = "pytest-report/pytest-report.xml"
JSON_OUTPUT_PATH = "pytest-report/processed-report.json"


def parse_xml_to_json(xml_content):
    # Parse XML content
    root = ET.fromstring(xml_content)
    
    # Helper function to convert XML elements to dictionary
    def elem_to_dict(elem):
        # Convert attributes to dictionary
        data = elem.attrib.copy()
        # Add children if they exist
        if elem.text and elem.text.strip():
            data['text'] = elem.text.strip()
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
    if 'testsuite' in data:
        testsuite = data['testsuite']        
        timestamp = testsuite.get('timestamp', None)
        if 'testcase' in testsuite:
            for testcase in testsuite['testcase']:
                testcaseobj = {}
                testcaseobj['name'] = testcase.get('name', None)
                testcaseobj['time'] = testcase.get('time', None)
                testcaseobj['classname'] = testcase.get('classname', None)
                testcaseobj['failure'] = testcase.get('failure', None)
                testcaseobj['timestamp'] = timestamp
                
                testcases.append(testcaseobj)

    return testcases, timestamp


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


def process_file(file_path):
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
    output_container_name = "airflow-system-dashboard-output"

    if os.path.exists(XML_ARTIFACT_PATH):
        blob_name, json_data = process_file(XML_ARTIFACT_PATH)

        save_json(json_data, JSON_OUTPUT_PATH)

        upload_blob(
            connection_string=connection_string,
            container_name=output_container_name,
            blob_name=blob_name,
            file_path=JSON_OUTPUT_PATH,
        )
    else:
        print(f"Artifact not found at {XML_ARTIFACT_PATH}")
