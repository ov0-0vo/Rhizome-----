print("Step 1: Starting test...")

import os
os.environ["HF_HUB_OFFLINE"] = "1"

import sys
sys.path.insert(0, '.')

print("Step 2: Importing config...")
from knowledge_agent.config import config

print("Step 3: Config loaded")
print(f"  embedding_provider: {config.embedding_provider}")
print(f"  embedding_model: {config.embedding_model}")

print("Step 4: Importing HuggingFaceEmbeddings...")
from langchain_community.embeddings import HuggingFaceEmbeddings

print("Step 5: Creating embeddings...")
embeddings = HuggingFaceEmbeddings(
    model_name=config.embedding_model,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
    cache_folder=os.path.expanduser("~/.cache/huggingface/hub")
)

print("Step 6: Testing embeddings...")
test_text = "这是一个测试"
result = embeddings.embed_query(test_text)
print(f"Embedding dimension: {len(result)}")
print(f"First 5 values: {result[:5]}")

print("\nEmbedding test passed!")
