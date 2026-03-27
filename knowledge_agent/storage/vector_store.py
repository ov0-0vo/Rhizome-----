import os
import logging

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

_HF_CACHE_FOLDER = os.path.expanduser("~/.cache/huggingface/hub")
_DEFAULT_MODEL = "BAAI/bge-small-zh-v1.5"


def _check_model_cached(model_name: str, cache_folder: str) -> bool:
    model_cache_path = os.path.join(
        cache_folder, 
        f"models--{model_name.replace('/', '--')}"
    )
    return os.path.exists(model_cache_path)


def _get_embedding_model_name():
    try:
        from dotenv import load_dotenv
        load_dotenv()
        return os.getenv("EMBEDDING_MODEL", _DEFAULT_MODEL)
    except:
        return _DEFAULT_MODEL


_EMBEDDING_MODEL_NAME = _get_embedding_model_name()

if _check_model_cached(_EMBEDDING_MODEL_NAME, _HF_CACHE_FOLDER):
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_DATASETS_OFFLINE"] = "1"
else:
    os.environ["HF_HUB_OFFLINE"] = "0"
    os.environ["TRANSFORMERS_OFFLINE"] = "0"
    os.environ["HF_DATASETS_OFFLINE"] = "0"

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.documents import Document
from knowledge_agent.config import config

logger = logging.getLogger(__name__)

_HF_EMBEDDINGS_CLASS = None


def _init_hf_offline_mode():
    cache_folder = os.path.expanduser("~/.cache/huggingface/hub")
    
    if _check_model_cached(config.embedding_model, cache_folder):
        logger.info(f"使用本地缓存的嵌入模型: {config.embedding_model}")
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_DATASETS_OFFLINE"] = "1"
    else:
        logger.info(f"本地未找到模型，正在下载: {config.embedding_model}")
        os.environ["HF_HUB_OFFLINE"] = "0"
        os.environ["TRANSFORMERS_OFFLINE"] = "0"
        os.environ["HF_DATASETS_OFFLINE"] = "0"


def _get_hf_embeddings_class():
    global _HF_EMBEDDINGS_CLASS
    if _HF_EMBEDDINGS_CLASS is None:
        _init_hf_offline_mode()
        from langchain_community.embeddings import HuggingFaceEmbeddings
        _HF_EMBEDDINGS_CLASS = HuggingFaceEmbeddings
    return _HF_EMBEDDINGS_CLASS


def create_embeddings():
    embedding_provider = config.embedding_provider.lower()
    
    if embedding_provider == "local":
        HuggingFaceEmbeddings = _get_hf_embeddings_class()
        cache_folder = os.path.expanduser("~/.cache/huggingface/hub")
        
        return HuggingFaceEmbeddings(
            model_name=config.embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
            cache_folder=cache_folder
        )
    elif embedding_provider == "openai":
        return OpenAIEmbeddings(
            model=config.embedding_model,
            openai_api_key=config.embedding_api_key or config.openai_api_key,
            base_url=config.embedding_api_base if config.embedding_api_base else None
        )
    elif embedding_provider == "ollama":
        return OllamaEmbeddings(
            model=config.embedding_model,
            base_url=config.embedding_api_base if config.embedding_api_base else "http://localhost:11434"
        )
    elif embedding_provider == "azure":
        return OpenAIEmbeddings(
            model=config.embedding_model,
            openai_api_key=config.embedding_api_key or config.openai_api_key,
            azure_endpoint=config.embedding_api_base if config.embedding_api_base else config.openai_api_base,
            api_version="2024-02-01",
            azure_deployment=config.embedding_model
        )
    else:
        HuggingFaceEmbeddings = _get_hf_embeddings_class()
        cache_folder = os.path.expanduser("~/.cache/huggingface/hub")
        
        return HuggingFaceEmbeddings(
            model_name=config.embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
            cache_folder=cache_folder
        )


class VectorStoreManager:
    def __init__(self, persist_directory: str = None):
        self.persist_directory = persist_directory or config.vector_store_dir
        self.embeddings = create_embeddings()
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        try:
            return self.client.get_collection(name="knowledge")
        except:
            return self.client.create_collection(
                name="knowledge",
                metadata={"hnsw:space": "cosine"}
            )

    def add_knowledge(self, knowledge_id: str, question: str, answer: str, catalog_id: str = None):
        doc = f"问题: {question}\n答案: {answer}"
        self.collection.add(
            documents=[doc],
            ids=[knowledge_id],
            metadatas=[{"catalog_id": catalog_id or "unknown", "question": question}]
        )

        

    def update_knowledge(self, knowledge_id: str, question: str, answer: str, catalog_id: str = None):
        doc = f"问题: {question}\n答案: {answer}"
        try:
            self.collection.update(
                ids=[knowledge_id],
                documents=[doc],
                metadatas=[{"catalog_id": catalog_id or "unknown", "question": question}]
            )
        except Exception:
            self.add_knowledge(knowledge_id, question, answer, catalog_id)

    def delete_knowledge(self, knowledge_id: str):
        try:
            self.collection.delete(ids=[knowledge_id])
        except:
            pass

    def search(
        self,
        query: str,
        n_results: int = 5,
        catalog_id: str = None
    ) -> List[Dict[str, Any]]:
        where_filter = {"catalog_id": catalog_id} if catalog_id else None
        
        try:
            if where_filter:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where_filter
                )
            else:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n_results
                )
        except:
            return []

        parsed_results = []
        if results.get("documents") and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                parsed_results.append({
                    "id": results["ids"][0][i],
                    "document": doc,
                    "distance": results["distances"][0][i] if "distances" in results else 0,
                    "metadata": results["metadatas"][0][i] if "metadatas" in results else {}
                })
        
        return parsed_results

    def search_by_catalog_tree(
        self,
        query: str,
        catalog_ids: List[str],
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        if not catalog_ids:
            return self.search(query, n_results)
        
        results = []
        for cat_id in catalog_ids:
            cat_results = self.search(query, n_results, catalog_id=cat_id)
            results.extend(cat_results)
        
        results.sort(key=lambda x: x["distance"])
        return results[:n_results]

    def get_all_ids(self) -> List[str]:
        try:
            return self.collection.get()["ids"]
        except:
            return []
