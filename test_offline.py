import os
print("Step 1: Setting HF_HUB_OFFLINE=1")
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

print("Step 2: Importing dependencies...")
import sys
sys.path.insert(0, '.')

print("Step 3: Importing HuggingFaceEmbeddings (after setting offline mode)...")
from langchain_community.embeddings import HuggingFaceEmbeddings

print("Step 4: Creating embeddings...")
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-zh-v1.5",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
    cache_folder=os.path.expanduser("~/.cache/huggingface/hub")
)

print("Step 5: Testing embeddings...")
test_text = "测试"
result = embeddings.embed_query(test_text)
print(f"Success! Embedding dimension: {len(result)}")
