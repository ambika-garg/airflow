import os

DATASET_ID = os.getenv("DATASET_ID", "None")
GROUP_ID = os.getenv("GROUP_ID", "None")
CLIENT_ID = os.getenv("CLIENT_ID", None)
CLIENT_SECRET = os.getenv("CLIENT_SECRET", None)
TENANT_ID = os.getenv("TENANT_ID", None)


print("DATASET_ID", DATASET_ID)
print("GROUP_ID", GROUP_ID)
print("CLIENT_ID", CLIENT_ID)
print("CLIENT_SECRET", CLIENT_SECRET)
print("TENANT_ID", TENANT_ID)