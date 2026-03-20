print("Step 1: Starting test...")

import sys
sys.path.insert(0, '.')

print("Step 2: Testing importlib_metadata...")
import importlib.metadata
print(f"importlib_metadata version: {importlib.metadata.version('importlib-metadata')}")

print("Step 3: Testing huggingface_hub...")
import huggingface_hub
print(f"huggingface_hub version: {importlib.metadata.version('huggingface-hub')}")

print("Step 4: Testing transformers...")
import transformers
print(f"transformers version: {importlib.metadata.version('transformers')}")

print("\nAll imports successful!")
