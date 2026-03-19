import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import OllamaEmbeddings
from langchain.schema import Document

from knowledge_agent.config import config


def create_embeddings():
    provider = config.provider.lower()
    
    if provider == "ollama":
        return OllamaEmbeddings(
            model=config.embedding_model,
            base_url=config.embedding_api_base if config.embedding_api_base else "http://localhost:11434"
        )
    elif provider == "azure":
        return OpenAIEmbeddings(
            model=config.embedding_model,
            openai_api_key=config.openai_api_key,
            api_base=config.embedding_api_base if config.embedding_api_base else f"{config.openai_api_base}/openai",
            api_version="2024-02-01",
            deployment=config.embedding_model
        )
    else:
        return OpenAIEmbeddings(
            model=config.embedding_model,
            openai_api_key=config.openai_api_key,
            base_url=config.embedding_api_base if config.embedding_api_base else None
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
