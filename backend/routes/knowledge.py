from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..dependencies import get_state

router = APIRouter()


class KnowledgeItem(BaseModel):
    id: str
    question: str
    answer: str
    keywords: List[str]
    catalog_id: Optional[str] = None
    created_at: str


class KnowledgeCreateRequest(BaseModel):
    question: str
    answer: str
    keywords: List[str] = []
    catalog_id: Optional[str] = None


class KnowledgeUpdateRequest(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    keywords: Optional[List[str]] = None
    catalog_id: Optional[str] = None


class KnowledgeSearchResult(BaseModel):
    id: str
    question: str
    answer: str
    keywords: List[str]
    catalog_id: Optional[str] = None
    similarity: float
    created_at: str


class LatestKnowledge(BaseModel):
    id: str
    question: str
    created_at: str


class CatalogDistribution(BaseModel):
    catalog_id: str
    catalog_name: str
    count: int


class Statistics(BaseModel):
    total_knowledge: int
    catalogs_count: int
    today_count: int
    week_count: int
    month_count: int
    latest_knowledge: List[LatestKnowledge]
    catalog_distribution: List[CatalogDistribution]
    top_keywords: List[Dict[str, Any]]


@router.get("", response_model=List[KnowledgeItem])
async def get_all_knowledge():
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
    current_state = get_state()
    
    all_items = current_state.qa_agent.get_all_knowledge()
    all_catalogs = current_state.catalog_manager.get_all_catalogs()
    
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)
    
    today_count = 0
    week_count = 0
    month_count = 0
    keyword_count = {}
    catalog_items = {}
    
    for item in all_items:
        try:
            created = datetime.fromisoformat(item.created_at)
            if created >= today_start:
                today_count += 1
            if created >= week_start:
                week_count += 1
            if created >= month_start:
                month_count += 1
        except:
            pass
        
        for kw in item.keywords:
            keyword_count[kw] = keyword_count.get(kw, 0) + 1
        
        if item.catalog_id:
            catalog_items[item.catalog_id] = catalog_items.get(item.catalog_id, 0) + 1
    
    top_keywords = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)[:10]
    
    catalog_distribution = []
    for catalog in all_catalogs:
        count = catalog_items.get(catalog.id, 0)
        if count > 0:
            catalog_distribution.append({
                "catalog_id": catalog.id,
                "catalog_name": catalog.name,
                "count": count
            })
    
    latest = sorted(all_items, key=lambda x: x.created_at, reverse=True)[:5]
    latest_knowledge = [
        {
            "id": item.id,
            "question": item.question[:50] + "..." if len(item.question) > 50 else item.question,
            "created_at": item.created_at
        }
        for item in latest
    ]
    
    return Statistics(
        total_knowledge=len(all_items),
        catalogs_count=len(all_catalogs),
        today_count=today_count,
        week_count=week_count,
        month_count=month_count,
        latest_knowledge=latest_knowledge,
        catalog_distribution=catalog_distribution,
        top_keywords=[{"keyword": k, "count": c} for k, c in top_keywords]
    )


@router.get("/search", response_model=List[KnowledgeSearchResult])
async def search_knowledge(query: str, limit: int = 5):
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


@router.get("/uncategorized", response_model=List[KnowledgeItem])
async def get_uncategorized_knowledge():
    current_state = get_state()
    all_items = current_state.knowledge_store.get_all_knowledge()
    uncategorized = [item for item in all_items if not item.catalog_id]
    return [
        KnowledgeItem(
            id=item.id,
            question=item.question,
            answer=item.answer,
            keywords=item.keywords,
            catalog_id=item.catalog_id,
            created_at=item.created_at
        )
        for item in uncategorized
    ]


@router.get("/uncategorized/count")
async def get_uncategorized_count():
    current_state = get_state()
    all_items = current_state.knowledge_store.get_all_knowledge()
    count = sum(1 for item in all_items if not item.catalog_id)
    return {"count": count}


@router.delete("/{knowledge_id}")
async def delete_knowledge(knowledge_id: str):
    current_state = get_state()
    current_state.qa_agent.delete_knowledge(knowledge_id)
    return {"message": "Knowledge deleted successfully"}


@router.post("", response_model=KnowledgeItem)
async def create_knowledge(request: KnowledgeCreateRequest):
    current_state = get_state()
    
    if request.catalog_id is not None:
        catalog = current_state.catalog_manager.get_catalog(request.catalog_id)
        if not catalog:
            raise HTTPException(status_code=400, detail=f"Catalog with id '{request.catalog_id}' not found")
    
    item = current_state.knowledge_store.add_knowledge(
        question=request.question,
        answer=request.answer,
        catalog_id=request.catalog_id,
        keywords=request.keywords
    )
    return KnowledgeItem(
        id=item.id,
        question=item.question,
        answer=item.answer,
        keywords=item.keywords,
        catalog_id=item.catalog_id,
        created_at=item.created_at
    )


@router.get("/{knowledge_id}", response_model=KnowledgeItem)
async def get_knowledge(knowledge_id: str):
    current_state = get_state()
    item = current_state.knowledge_store.get_knowledge(knowledge_id)
    if not item:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    return KnowledgeItem(
        id=item.id,
        question=item.question,
        answer=item.answer,
        keywords=item.keywords,
        catalog_id=item.catalog_id,
        created_at=item.created_at
    )


@router.put("/{knowledge_id}", response_model=KnowledgeItem)
async def update_knowledge(knowledge_id: str, request: KnowledgeUpdateRequest):
    current_state = get_state()
    
    if request.catalog_id is not None:
        catalog = current_state.catalog_manager.get_catalog(request.catalog_id)
        if not catalog:
            raise HTTPException(status_code=400, detail=f"Catalog with id '{request.catalog_id}' not found")
    
    item = current_state.knowledge_store.update_knowledge(
        knowledge_id=knowledge_id,
        question=request.question,
        answer=request.answer,
        keywords=request.keywords,
        catalog_id=request.catalog_id
    )
    if not item:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    return KnowledgeItem(
        id=item.id,
        question=item.question,
        answer=item.answer,
        keywords=item.keywords,
        catalog_id=item.catalog_id,
        created_at=item.created_at
    )
