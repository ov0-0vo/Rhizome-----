from knowledge_agent.agent.qa_agent import QAAgent
from knowledge_agent.knowledge.catalog_manager import CatalogManager
from knowledge_agent.knowledge.knowledge_store import KnowledgeStore


class AppState:
    qa_agent: QAAgent = None
    catalog_manager: CatalogManager = None
    knowledge_store: KnowledgeStore = None


state = AppState()


def get_state():
    if state.qa_agent is None:
        state.qa_agent = QAAgent()
        state.catalog_manager = CatalogManager()
        state.knowledge_store = KnowledgeStore()
    return state
