import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    provider: str = os.getenv("LLM_PROVIDER", "openai")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_api_base: str = os.getenv("OPENAI_API_BASE", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "local")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
    embedding_api_key: str = os.getenv("EMBEDDING_API_KEY", "")
    embedding_api_base: str = os.getenv("EMBEDDING_API_BASE", "")
    
    data_dir: str = "data"
    catalog_file: str = "data/catalog.json"
    vector_store_dir: str = "data/vector_store"
    max_tokens: int = 2000
    temperature: float = 0.7
    top_k: int = 5


config = Config()

