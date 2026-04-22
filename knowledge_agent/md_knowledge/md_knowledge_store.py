import json
import logging
import threading
from typing import List, Dict, Any, Optional
from pathlib import Path

from .models import MdDocument, MdEditProposal, ProposalStatus

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "md_knowledge"
DOCUMENTS_FILE = DATA_DIR / "documents.json"
PROPOSALS_FILE = DATA_DIR / "proposals.json"


class MdKnowledgeStore:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.documents_file = DOCUMENTS_FILE
        self.proposals_file = PROPOSALS_FILE
        self._doc_cache: Optional[Dict[str, Any]] = None
        self._prop_cache: Optional[Dict[str, Any]] = None
        self._lock = threading.Lock()
        self._ensure_files_exist()

    def _ensure_files_exist(self):
        for file_path in [self.documents_file, self.proposals_file]:
            if not file_path.exists():
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({"items": []}, f, ensure_ascii=False, indent=2)

    def _read_docs(self) -> Dict[str, Any]:
        if self._doc_cache is not None:
            return self._doc_cache
        with self._lock:
            with open(self.documents_file, 'r', encoding='utf-8') as f:
                self._doc_cache = json.load(f)
            return self._doc_cache

    def _write_docs(self, data: Dict[str, Any]):
        with self._lock:
            with open(self.documents_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._doc_cache = data

    def _read_proposals(self) -> Dict[str, Any]:
        if self._prop_cache is not None:
            return self._prop_cache
        with self._lock:
            with open(self.proposals_file, 'r', encoding='utf-8') as f:
                self._prop_cache = json.load(f)
            return self._prop_cache

    def _write_proposals(self, data: Dict[str, Any]):
        with self._lock:
            with open(self.proposals_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._prop_cache = data

    def invalidate_cache(self):
        self._doc_cache = None
        self._prop_cache = None

    def create_document(self, title: str, content: str, path: str = "", tags: List[str] = None) -> MdDocument:
        doc = MdDocument(title=title, content=content, path=path, tags=tags or [])
        data = self._read_docs()
        data["items"].append(doc.to_dict())
        self._write_docs(data)
        return doc

    def get_document(self, doc_id: str) -> Optional[MdDocument]:
        data = self._read_docs()
        for item in data.get("items", []):
            if item["id"] == doc_id:
                return MdDocument.from_dict(item)
        return None

    def get_all_documents(self) -> List[MdDocument]:
        data = self._read_docs()
        return [MdDocument.from_dict(item) for item in data.get("items", [])]

    def update_document(self, doc_id: str, title: str = None, content: str = None, tags: List[str] = None) -> Optional[MdDocument]:
        doc = self.get_document(doc_id)
        if doc:
            doc.update(title=title, content=content, tags=tags)
            data = self._read_docs()
            for i, item in enumerate(data["items"]):
                if item["id"] == doc_id:
                    data["items"][i] = doc.to_dict()
                    break
            self._write_docs(data)
        return doc

    def delete_document(self, doc_id: str) -> bool:
        data = self._read_docs()
        original_len = len(data["items"])
        data["items"] = [item for item in data["items"] if item["id"] != doc_id]
        if len(data["items"]) < original_len:
            self._write_docs(data)
            return True
        return False

    def search_documents(self, query: str) -> List[MdDocument]:
        docs = self.get_all_documents()
        query_lower = query.lower()
        results = []
        for doc in docs:
            if (query_lower in doc.title.lower() or
                query_lower in doc.content.lower() or
                any(query_lower in tag.lower() for tag in doc.tags)):
                results.append(doc)
        return results

    def create_proposal(self, document_id: str, proposed_content: str, original_content: str, description: str = "") -> MdEditProposal:
        proposal = MdEditProposal(
            document_id=document_id,
            proposed_content=proposed_content,
            original_content=original_content,
            description=description
        )
        data = self._read_proposals()
        data["items"].append(proposal.to_dict())
        self._write_proposals(data)
        return proposal

    def get_proposal(self, proposal_id: str) -> Optional[MdEditProposal]:
        data = self._read_proposals()
        for item in data.get("items", []):
            if item["id"] == proposal_id:
                return MdEditProposal.from_dict(item)
        return None

    def get_proposals_by_document(self, document_id: str) -> List[MdEditProposal]:
        data = self._read_proposals()
        return [MdEditProposal.from_dict(item) for item in data.get("items", []) if item["document_id"] == document_id]

    def get_pending_proposals(self) -> List[MdEditProposal]:
        data = self._read_proposals()
        return [MdEditProposal.from_dict(item) for item in data.get("items", []) if item["status"] == ProposalStatus.PENDING]

    def get_all_proposals(self) -> List[MdEditProposal]:
        data = self._read_proposals()
        return [MdEditProposal.from_dict(item) for item in data.get("items", [])]

    def review_proposal(self, proposal_id: str, approve: bool, comment: str = "") -> Optional[MdEditProposal]:
        proposal = self.get_proposal(proposal_id)
        if not proposal:
            return None

        if approve:
            proposal.approve(comment)
            doc = self.get_document(proposal.document_id)
            if doc:
                doc.content = proposal.proposed_content
                doc.updated_at = proposal.reviewed_at
                doc.version += 1
                data = self._read_docs()
                for i, item in enumerate(data["items"]):
                    if item["id"] == doc.id:
                        data["items"][i] = doc.to_dict()
                        break
                self._write_docs(data)
        else:
            proposal.reject(comment)

        data = self._read_proposals()
        for i, item in enumerate(data["items"]):
            if item["id"] == proposal_id:
                data["items"][i] = proposal.to_dict()
                break
        self._write_proposals(data)

        return proposal

    def delete_proposal(self, proposal_id: str) -> bool:
        data = self._read_proposals()
        original_len = len(data["items"])
        data["items"] = [item for item in data["items"] if item["id"] != proposal_id]
        if len(data["items"]) < original_len:
            self._write_proposals(data)
            return True
        return False

    def get_statistics(self) -> Dict[str, Any]:
        docs = self.get_all_documents()
        proposals = self.get_all_proposals()
        pending = [p for p in proposals if p.status == ProposalStatus.PENDING]
        return {
            "total_documents": len(docs),
            "total_proposals": len(proposals),
            "pending_proposals": len(pending),
            "total_words": sum(len(d.content) for d in docs)
        }


md_knowledge_store = MdKnowledgeStore()
