import requests
import os


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

def process_file(file_path):
    # Check if the given path is a directory
    if os.path.isdir(file_path):
        print(f"{file_path} is a directory. Listing contents:")
        directories = os.listdir(file_path)
        for item in directories:
            if os.path.isfile(item):
                with open(file_path, 'r') as file:
                    content = file.read()
                    print("Content of the file:", content)
                print(f"File: {item}")
            print(item)
    elif os.path.isfile(file_path):
        # Process the file if it's a file
        with open(file_path, 'r') as file:
            content = file.read()
            print("Content of the file:", content)

        # Add your processing logic here
        # For example, appending data to the file:
        with open(file_path, 'a') as file:
            file.write("\nProcessed by Python script")
    else:
        print(f"Path {file_path} is neither a file nor a directory.")

if __name__ == "__main__":
    artifact_path = 'test-report/sample-artifact.xml'  # Path where the artifact was downloaded
    if os.path.exists(artifact_path):
        process_file(artifact_path)
    else:
        print(f"Artifact not found at {artifact_path}")