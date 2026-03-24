from knowledge_agent.agent.qa_agent import QAAgent
from knowledge_agent.knowledge.catalog_manager import CatalogManager
from knowledge_agent.knowledge.knowledge_store import KnowledgeStore
from knowledge_agent.review import ReviewManager


class AppState:
    qa_agent: QAAgent = None
    catalog_manager: CatalogManager = None
    knowledge_store: KnowledgeStore = None
    review_manager: ReviewManager = None


state = AppState()


def get_state():
    if state.qa_agent is None:
        state.catalog_manager = CatalogManager()
        state.knowledge_store = KnowledgeStore()
        state.qa_agent = QAAgent(
            catalog_manager=state.catalog_manager,
            knowledge_store=state.knowledge_store
        )
    return state


def get_review_manager():
    if state.review_manager is None:
        get_state()
        state.review_manager = ReviewManager(
            knowledge_store=state.knowledge_store,
            catalog_manager=state.catalog_manager,
            qa_agent=state.qa_agent
        )
    return state.review_manager
