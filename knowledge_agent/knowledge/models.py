import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path


class KnowledgeCatalog:
    def __init__(
        self,
        id: str = None,
        name: str = "",
        keywords: List[str] = None,
        parent_id: Optional[str] = None,
        children: List[str] = None,
        knowledge_items: List[str] = None,
        created_at: str = None,
        updated_at: str = None
    ):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.keywords = keywords or []
        self.parent_id = parent_id
        self.children = children or []
        self.knowledge_items = knowledge_items or []
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "keywords": self.keywords,
            "parent_id": self.parent_id,
            "children": self.children,
            "knowledge_items": self.knowledge_items,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeCatalog":
        return cls(**data)

    def update(self, name: str = None, keywords: List[str] = None):
        if name is not None:
            self.name = name
        if keywords is not None:
            self.keywords = keywords
        self.updated_at = datetime.now().isoformat()


class KnowledgeItem:
    def __init__(
        self,
        id: str = None,
        catalog_id: str = "",
        question: str = "",
        answer: str = "",
        keywords: List[str] = None,
        sources: List[str] = None,
        confidence: float = 1.0,
        created_at: str = None,
        updated_at: str = None
    ):
        self.id = id or str(uuid.uuid4())
        self.catalog_id = catalog_id
        self.question = question
        self.answer = answer
        self.keywords = keywords or []
        self.sources = sources or []
        self.confidence = confidence
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "catalog_id": self.catalog_id,
            "question": self.question,
            "answer": self.answer,
            "keywords": self.keywords,
            "sources": self.sources,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeItem":
        return cls(**data)

    def update(self, answer: str = None, keywords: List[str] = None, sources: List[str] = None):
        if answer is not None:
            self.answer = answer
        if keywords is not None:
            self.keywords = keywords
        if sources is not None:
            self.sources = sources
        self.updated_at = datetime.now().isoformat()
