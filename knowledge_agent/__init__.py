from knowledge_agent.knowledge.catalog_manager import CatalogManager
from knowledge_agent.knowledge.knowledge_store import KnowledgeStore
from knowledge_agent.config import config

__all__ = ["QAAgent", "CatalogManager", "KnowledgeStore", "config"]


def __getattr__(name):
    """Lazy import QAAgent to avoid initialization during package import."""
    if name == "QAAgent":
        from knowledge_agent.agent.qa_agent import QAAgent
        return QAAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
