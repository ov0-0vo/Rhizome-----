import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..knowledge.models import KnowledgeCatalog, KnowledgeItem


class CatalogStorage:
    def __init__(self, catalog_file: str):
        self.catalog_file = catalog_file
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        Path(self.catalog_file).parent.mkdir(parents=True, exist_ok=True)
        if not os.path.exists(self.catalog_file):
            with open(self.catalog_file, 'w', encoding='utf-8') as f:
                json.dump({"catalogs": [], "root_id": None}, f, ensure_ascii=False, indent=2)

    def _read(self) -> Dict[str, Any]:
        with open(self.catalog_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _write(self, data: Dict[str, Any]):
        with open(self.catalog_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_all_catalogs(self) -> List[KnowledgeCatalog]:
        data = self._read()
        return [KnowledgeCatalog.from_dict(c) for c in data.get("catalogs", [])]

    def get_catalog(self, catalog_id: str) -> Optional[KnowledgeCatalog]:
        data = self._read()
        for c in data.get("catalogs", []):
            if c["id"] == catalog_id:
                return KnowledgeCatalog.from_dict(c)
        return None

    def add_catalog(self, catalog: KnowledgeCatalog) -> KnowledgeCatalog:
        data = self._read()
        data["catalogs"].append(catalog.to_dict())
        
        if data.get("root_id") is None:
            data["root_id"] = catalog.id
        else:
            parent = self.get_catalog(catalog.parent_id) if catalog.parent_id else None
            if parent:
                parent_data = next((c for c in data["catalogs"] if c["id"] == parent.id), None)
                if parent_data and catalog.id not in parent_data["children"]:
                    parent_data["children"].append(catalog.id)
        
        self._write(data)
        return catalog

    def update_catalog(self, catalog: KnowledgeCatalog):
        data = self._read()
        for i, c in enumerate(data["catalogs"]):
            if c["id"] == catalog.id:
                data["catalogs"][i] = catalog.to_dict()
                break
        self._write(data)

    def delete_catalog(self, catalog_id: str):
        data = self._read()
        data["catalogs"] = [c for c in data["catalogs"] if c["id"] != catalog_id]
        
        for c in data["catalogs"]:
            if catalog_id in c["children"]:
                c["children"].remove(catalog_id)
        
        self._write(data)

    def get_root_id(self) -> Optional[str]:
        data = self._read()
        return data.get("root_id")


class KnowledgeStorage:
    def __init__(self, knowledge_file: str):
        self.knowledge_file = knowledge_file
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        Path(self.knowledge_file).parent.mkdir(parents=True, exist_ok=True)
        if not os.path.exists(self.knowledge_file):
            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                json.dump({"items": []}, f, ensure_ascii=False, indent=2)

    def _read(self) -> Dict[str, Any]:
        with open(self.knowledge_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _write(self, data: Dict[str, Any]):
        with open(self.knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_all_items(self) -> List[KnowledgeItem]:
        data = self._read()
        return [KnowledgeItem.from_dict(item) for item in data.get("items", [])]

    def get_item(self, item_id: str) -> Optional[KnowledgeItem]:
        data = self._read()
        for item in data.get("items", []):
            if item["id"] == item_id:
                return KnowledgeItem.from_dict(item)
        return None

    def get_items_by_catalog(self, catalog_id: str) -> List[KnowledgeItem]:
        data = self._read()
        return [KnowledgeItem.from_dict(item) for item in data.get("items", []) 
                if item.get("catalog_id") == catalog_id]

    def add_item(self, item: KnowledgeItem) -> KnowledgeItem:
        data = self._read()
        data["items"].append(item.to_dict())
        self._write(data)
        return item

    def update_item(self, item: KnowledgeItem):
        data = self._read()
        for i, it in enumerate(data["items"]):
            if it["id"] == item.id:
                data["items"][i] = item.to_dict()
                break
        self._write(data)

    def delete_item(self, item_id: str):
        data = self._read()
        data["items"] = [item for item in data["items"] if item["id"] != item_id]
        self._write(data)

    def search_by_question(self, question: str) -> List[KnowledgeItem]:
        data = self._read()
        results = []
        question_lower = question.lower()
        for item in data.get("items", []):
            if question_lower in item["question"].lower():
                results.append(KnowledgeItem.from_dict(item))
        return results
