import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class ProposalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MdDocument:
    def __init__(
        self,
        id: str = None,
        title: str = "",
        content: str = "",
        path: str = "",
        tags: List[str] = None,
        created_at: str = None,
        updated_at: str = None,
        version: int = 1,
        is_protected: bool = True
    ):
        self.id = id or str(uuid.uuid4())
        self.title = title
        self.content = content
        self.path = path
        self.tags = tags or []
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
        self.version = version
        self.is_protected = is_protected

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "path": self.path,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "is_protected": self.is_protected
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MdDocument":
        return cls(**data)

    def update(self, title: str = None, content: str = None, tags: List[str] = None):
        if title is not None:
            self.title = title
        if content is not None:
            self.content = content
        if tags is not None:
            self.tags = tags
        self.updated_at = datetime.now().isoformat()
        self.version += 1


class MdEditProposal:
    def __init__(
        self,
        id: str = None,
        document_id: str = "",
        proposed_content: str = "",
        original_content: str = "",
        description: str = "",
        status: str = ProposalStatus.PENDING,
        created_at: str = None,
        reviewed_at: str = None,
        review_comment: str = ""
    ):
        self.id = id or str(uuid.uuid4())
        self.document_id = document_id
        self.proposed_content = proposed_content
        self.original_content = original_content
        self.description = description
        self.status = status
        self.created_at = created_at or datetime.now().isoformat()
        self.reviewed_at = reviewed_at
        self.review_comment = review_comment

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "document_id": self.document_id,
            "proposed_content": self.proposed_content,
            "original_content": self.original_content,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at,
            "reviewed_at": self.reviewed_at,
            "review_comment": self.review_comment
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MdEditProposal":
        return cls(**data)

    def approve(self, comment: str = ""):
        self.status = ProposalStatus.APPROVED
        self.reviewed_at = datetime.now().isoformat()
        self.review_comment = comment

    def reject(self, comment: str = ""):
        self.status = ProposalStatus.REJECTED
        self.reviewed_at = datetime.now().isoformat()
        self.review_comment = comment
