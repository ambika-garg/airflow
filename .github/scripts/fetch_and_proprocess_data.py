from __future__ import annotations
import os

def printenv() -> None:
    for key, value in os.environ.items():
            print(f"{key}: {value}")
print("hello")
