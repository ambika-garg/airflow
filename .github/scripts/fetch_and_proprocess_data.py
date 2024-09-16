from __future__ import annotations
import os

connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
print(connection_string)
print("hello")
