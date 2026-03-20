from typing import List, Optional, Dict, Any
import json
from .models import KnowledgeCatalog
from ..storage.json_storage import CatalogStorage
from ..config import config


class CatalogManager:
    def __init__(self):
        self.storage = CatalogStorage(config.catalog_file)

    def get_all_catalogs(self) -> List[KnowledgeCatalog]:
        return self.storage.get_all_catalogs()

    def get_catalog(self, catalog_id: str) -> Optional[KnowledgeCatalog]:
        return self.storage.get_catalog(catalog_id)

    def get_root_catalog(self) -> Optional[KnowledgeCatalog]:
        root_id = self.storage.get_root_id()
        if root_id:
            return self.storage.get_catalog(root_id)
        return None

    def create_catalog(
        self,
        name: str,
        keywords: List[str] = None,
        parent_id: Optional[str] = None
    ) -> KnowledgeCatalog:
        catalog = KnowledgeCatalog(
            name=name,
            keywords=keywords or [],
            parent_id=parent_id
        )
        return self.storage.add_catalog(catalog)

    def update_catalog(
        self,
        catalog_id: str,
        name: str = None,
        keywords: List[str] = None
    ) -> Optional[KnowledgeCatalog]:
        catalog = self.storage.get_catalog(catalog_id)
        if catalog:
            catalog.update(name=name, keywords=keywords)
            self.storage.update_catalog(catalog)
        return catalog

    def delete_catalog(self, catalog_id: str):
        self.storage.delete_catalog(catalog_id)

    def add_knowledge_to_catalog(self, catalog_id: str, knowledge_id: str):
        catalog = self.storage.get_catalog(catalog_id)
        if catalog and knowledge_id not in catalog.knowledge_items:
            catalog.knowledge_items.append(knowledge_id)
            self.storage.update_catalog(catalog)

    def remove_knowledge_from_catalog(self, catalog_id: str, knowledge_id: str):
        catalog = self.storage.get_catalog(catalog_id)
        if catalog and knowledge_id in catalog.knowledge_items:
            catalog.knowledge_items.remove(knowledge_id)
            self.storage.update_catalog(catalog)

    def match_catalog_by_keywords(self, keywords: List[str]) -> Optional[KnowledgeCatalog]:
        catalogs = self.get_all_catalogs()
        
        best_match = None
        best_score = 0
        
        for catalog in catalogs:
            score = 0
            for kw in keywords:
                if kw.lower() in [k.lower() for k in catalog.keywords]:
                    score += 1
                if kw.lower() in catalog.name.lower():
                    score += 2
            
            if score > best_score:
                best_score = score
                best_match = catalog
        
        return best_match if best_score > 0 else None

    def get_catalog_tree(self, catalog_id: str = None) -> Dict[str, Any]:
        if catalog_id is not None:
            catalog = self.get_catalog(catalog_id)
            if catalog:
                return self._build_tree(catalog)
            return {}
        
        all_catalogs = self.get_all_catalogs()
        root_catalogs = [c for c in all_catalogs if c.parent_id is None]
        
        if not root_catalogs:
            return {}
        
        if len(root_catalogs) == 1:
            return self._build_tree(root_catalogs[0])
        
        return {
            "id": "root",
            "name": "知识库",
            "keywords": [],
            "knowledge_count": 0,
            "children": [self._build_tree(c) for c in root_catalogs]
        }

    def _build_tree(self, catalog: KnowledgeCatalog) -> Dict[str, Any]:
        tree = {
            "id": catalog.id,
            "name": catalog.name,
            "keywords": catalog.keywords,
            "knowledge_count": len(catalog.knowledge_items),
            "children": []
        }
        
        for child_id in catalog.children:
            child = self.get_catalog(child_id)
            if child:
                tree["children"].append(self._build_tree(child))
        
        return tree

    def get_all_descendant_ids(self, catalog_id: str) -> List[str]:
        catalog = self.get_catalog(catalog_id)
        if not catalog:
            return []
        
        descendants = [catalog_id]
        for child_id in catalog.children:
            descendants.extend(self.get_all_descendant_ids(child_id))
        
        return descendants

    def get_catalogs_summary(self) -> List[Dict[str, Any]]:
        catalogs = self.get_all_catalogs()
        return [
            {
                "id": c.id,
                "name": c.name,
                "keywords": c.keywords,
                "knowledge_count": len(c.knowledge_items),
                "parent_id": c.parent_id
            }
            for c in catalogs
        ]
