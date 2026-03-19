from typing import List, Dict, Any, Optional
import json

from .models import KnowledgeItem
from ..storage.json_storage import KnowledgeStorage
from ..storage.vector_store import VectorStoreManager
from ..config import config


class KnowledgeStore:
    def __init__(self):
        self.json_storage = KnowledgeStorage(config.catalog_file.replace("catalog.json", "knowledge.json"))
        self.vector_store = VectorStoreManager()

    def add_knowledge(
        self,
        question: str,
        answer: str,
        catalog_id: str = None,
        keywords: List[str] = None,
        sources: List[str] = None
    ) -> KnowledgeItem:
        item = KnowledgeItem(
            question=question,
            answer=answer,
            catalog_id=catalog_id,
            keywords=keywords or [],
            sources=sources or []
        )
        
        self.json_storage.add_item(item)
        self.vector_store.add_knowledge(item.id, question, answer, catalog_id)
        
        return item

    def get_knowledge(self, knowledge_id: str) -> Optional[KnowledgeItem]:
        return self.json_storage.get_item(knowledge_id)

    def get_all_knowledge(self) -> List[KnowledgeItem]:
        return self.json_storage.get_all_items()

    def get_knowledge_by_catalog(self, catalog_id: str) -> List[KnowledgeItem]:
        return self.json_storage.get_items_by_catalog(catalog_id)

    def update_knowledge(
        self,
        knowledge_id: str,
        answer: str = None,
        keywords: List[str] = None,
        sources: List[str] = None,
        catalog_id: str = None
    ) -> Optional[KnowledgeItem]:
        item = self.json_storage.get_item(knowledge_id)
        if item:
            item.update(answer=answer, keywords=keywords, sources=sources)
            if catalog_id is not None:
                item.catalog_id = catalog_id
            self.json_storage.update_item(item)
            self.vector_store.update_knowledge(
                item.id, item.question, item.answer, item.catalog_id
            )
        return item

    def delete_knowledge(self, knowledge_id: str):
        self.json_storage.delete_item(knowledge_id)
        self.vector_store.delete_knowledge(knowledge_id)

    def search(
        self,
        query: str,
        n_results: int = 5,
        catalog_id: str = None
    ) -> List[Dict[str, Any]]:
        vector_results = self.vector_store.search(query, n_results, catalog_id)
        
        results = []
        for vr in vector_results:
            item = self.json_storage.get_item(vr["id"])
            if item:
                results.append({
                    "id": item.id,
                    "question": item.question,
                    "answer": item.answer,
                    "keywords": item.keywords,
                    "catalog_id": item.catalog_id,
                    "similarity": 1 - vr["distance"],
                    "created_at": item.created_at
                })
        
        return results

    def search_by_catalog_tree(
        self,
        query: str,
        catalog_ids: List[str],
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        vector_results = self.vector_store.search_by_catalog_tree(query, catalog_ids, n_results)
        
        results = []
        for vr in vector_results:
            item = self.json_storage.get_item(vr["id"])
            if item:
                results.append({
                    "id": item.id,
                    "question": item.question,
                    "answer": item.answer,
                    "keywords": item.keywords,
                    "catalog_id": item.catalog_id,
                    "similarity": 1 - vr["distance"],
                    "created_at": item.created_at
                })
        
        return results

    def find_similar_question(self, question: str) -> Optional[KnowledgeItem]:
        items = self.json_storage.search_by_question(question)
        if items:
            return items[0]
        
        vector_results = self.vector_store.search(question, n_results=1)
        if vector_results:
            return self.json_storage.get_item(vector_results[0]["id"])
        
        return None

    def get_statistics(self) -> Dict[str, Any]:
        all_items = self.json_storage.get_all_items()
        return {
            "total_knowledge": len(all_items),
            "catalogs_count": len(set(item.catalog_id for item in all_items if item.catalog_id)),
            "latest_knowledge": [
                {
                    "id": item.id,
                    "question": item.question[:50] + "..." if len(item.question) > 50 else item.question,
                    "created_at": item.created_at
                }
                for item in sorted(all_items, key=lambda x: x.created_at, reverse=True)[:5]
            ]
        }
