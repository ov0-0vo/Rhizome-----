from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class KnowledgeItem(BaseModel):
    id: str
    question: str
    answer: str
    keywords: List[str]
    catalog_id: Optional[str] = None
    created_at: str


class KnowledgeSearchResult(BaseModel):
    id: str
    question: str
    answer: str
    keywords: List[str]
    catalog_id: Optional[str] = None
    similarity: float
    created_at: str


class Statistics(BaseModel):
    total_knowledge: int
    catalogs_count: int


@router.get("", response_model=List[KnowledgeItem])
async def get_all_knowledge():
    from ..dependencies import get_state
    current_state = get_state()
    items = current_state.qa_agent.get_all_knowledge()
    return [
        KnowledgeItem(
            id=item.id,
            question=item.question,
            answer=item.answer,
            keywords=item.keywords,
            catalog_id=item.catalog_id,
            created_at=item.created_at
        )
        for item in items
    ]


@router.get("/statistics", response_model=Statistics)
async def get_statistics():
    from ..dependencies import get_state
    current_state = get_state()
    stats = current_state.qa_agent.get_statistics()
    return Statistics(
        total_knowledge=stats["total_knowledge"],
        catalogs_count=stats["catalogs_count"]
    )


@router.get("/search", response_model=List[KnowledgeSearchResult])
async def search_knowledge(query: str, limit: int = 5):
    from ..dependencies import get_state
    current_state = get_state()
    results = current_state.qa_agent.search_knowledge(query)
    return [
        KnowledgeSearchResult(
            id=r["id"],
            question=r["question"],
            answer=r["answer"],
            keywords=r["keywords"],
            catalog_id=r.get("catalog_id"),
            similarity=r["similarity"],
            created_at=r["created_at"]
        )
        for r in results[:limit]
    ]


@router.get("/catalog/{catalog_id}", response_model=List[KnowledgeItem])
async def get_knowledge_by_catalog(catalog_id: str):
    from ..dependencies import get_state
    current_state = get_state()
    items = current_state.knowledge_store.get_knowledge_by_catalog(catalog_id)
    return [
        KnowledgeItem(
            id=item.id,
            question=item.question,
            answer=item.answer,
            keywords=item.keywords,
            catalog_id=item.catalog_id,
            created_at=item.created_at
        )
        for item in items
    ]


@router.delete("/{knowledge_id}")
async def delete_knowledge(knowledge_id: str):
    from ..dependencies import get_state
    current_state = get_state()
    current_state.qa_agent.delete_knowledge(knowledge_id)
    return {"message": "Knowledge deleted successfully"}
