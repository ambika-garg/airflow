import os

DATASET_ID = os.environ.get("DATASET_ID", "None")
GROUP_ID = os.environ.get("GROUP_ID", "None")
CLIENT_ID = os.environ.get("CLIENT_ID", None)
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", None)
TENANT_ID = os.environ.get("TENANT_ID", None)


print("DATASET_ID", DATASET_ID)
print("GROUP_ID", GROUP_ID)
print("CLIENT_ID", CLIENT_ID)
print("CLIENT_SECRET", CLIENT_SECRET)
print("TENANT_ID", TENANT_ID)