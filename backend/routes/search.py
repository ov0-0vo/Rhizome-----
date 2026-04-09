from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import os

router = APIRouter(prefix="/api/search", tags=["search"])

logger = logging.getLogger(__name__)

search_manager = None


def get_search_manager():
    global search_manager
    if search_manager is None:
        from knowledge_agent.tools import WebSearchManager
        search_manager = WebSearchManager()
    return search_manager


class SearchRequest(BaseModel):
    query: str
    max_results: int = 5


class SearchResult(BaseModel):
    title: str
    url: str
    content: str
    score: float


class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    total: int


class SearchStatus(BaseModel):
    enabled: bool
    provider: Optional[str]
    api_key_configured: bool


class EnableSearchRequest(BaseModel):
    api_key: str = None


@router.get("/status", response_model=SearchStatus)
async def get_search_status():
    manager = get_search_manager()
    status = manager.get_status()
    return SearchStatus(**status)


@router.post("/enable")
async def enable_search(request: EnableSearchRequest):
    manager = get_search_manager()
    
    api_key = request.api_key or os.getenv("TAVILY_API_KEY", "")
    
    if not api_key:
        raise HTTPException(status_code=400, detail="需要提供 Tavily API Key")
    
    success = manager.enable(api_key)
    
    if success:
        return {"message": "搜索功能已启用", "enabled": True}
    else:
        raise HTTPException(status_code=500, detail="启用搜索功能失败")


@router.post("/disable")
async def disable_search():
    manager = get_search_manager()
    manager.disable()
    return {"message": "搜索功能已禁用", "enabled": False}


@router.post("", response_model=SearchResponse)
async def search(request: SearchRequest):
    manager = get_search_manager()
    
    if not manager.is_enabled():
        raise HTTPException(status_code=400, detail="搜索功能未启用，请先配置 Tavily API Key")
    
    results = manager.search(request.query, request.max_results)
    
    return SearchResponse(
        results=[SearchResult(**r.__dict__) for r in results],
        query=request.query,
        total=len(results)
    )


@router.post("/search-and-format")
async def search_and_format(request: SearchRequest):
    manager = get_search_manager()
    
    if not manager.is_enabled():
        raise HTTPException(status_code=400, detail="搜索功能未启用，请先配置 Tavily API Key")
    
    formatted_result = manager.search_and_format(request.query, request.max_results)
    
    return {
        "query": request.query,
        "formatted_result": formatted_result
    }
