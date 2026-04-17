from typing import List, Dict, Any, Optional
import json
import logging

from .models import KnowledgeItem
from ..storage.json_storage import KnowledgeStorage
from ..storage.vector_store import VectorStoreManager
from ..config import config

logger = logging.getLogger(__name__)


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
        
        try:
            self.vector_store.add_knowledge(item.id, question, answer, catalog_id)
        except Exception as e:
            logger.error(f"向量存储写入失败，已回滚JSON记录 {item.id}: {e}")
            self.json_storage.delete_item(item.id)
            raise
        
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
        question: str = None,
        answer: str = None,
        keywords: List[str] = None,
        sources: List[str] = None,
        catalog_id: str = None
    ) -> Optional[KnowledgeItem]:
        item = self.json_storage.get_item(knowledge_id)
        if item:
            old_question = item.question
            old_answer = item.answer
            old_catalog_id = item.catalog_id
            
            if question is not None:
                item.question = question
            item.update(answer=answer, keywords=keywords, sources=sources)
            if catalog_id is not None:
                item.catalog_id = catalog_id
            self.json_storage.update_item(item)
            
            try:
                self.vector_store.update_knowledge(
                    item.id, item.question, item.answer, item.catalog_id
                )
            except Exception as e:
                logger.error(f"向量存储更新失败 {knowledge_id}: {e}")
                item.question = old_question
                item.answer = old_answer
                item.catalog_id = old_catalog_id
                self.json_storage.update_item(item)
        return item

    def delete_knowledge(self, knowledge_id: str):
        self.json_storage.delete_item(knowledge_id)
        
        try:
            self.vector_store.delete_knowledge(knowledge_id)
        except Exception as e:
            logger.error(f"向量存储删除失败 {knowledge_id}: {e}")

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
                similarity = max(0.0, 1 - vr["distance"] / 2)
                results.append({
                    "id": item.id,
                    "question": item.question,
                    "answer": item.answer,
                    "keywords": item.keywords,
                    "catalog_id": item.catalog_id,
                    "similarity": similarity,
                    "created_at": item.created_at
                })
            else:
                logger.warning(f"向量库中存在但JSON中缺失的知识条目: {vr['id']}")
        
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
                similarity = max(0.0, 1 - vr["distance"] / 2)
                results.append({
                    "id": item.id,
                    "question": item.question,
                    "answer": item.answer,
                    "keywords": item.keywords,
                    "catalog_id": item.catalog_id,
                    "similarity": similarity,
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
