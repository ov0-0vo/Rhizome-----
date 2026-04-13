from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import asyncio

router = APIRouter(prefix="/api/discovery", tags=["discovery"])

logger = logging.getLogger(__name__)

discovery_manager = None


def get_discovery_manager():
    global discovery_manager
    if discovery_manager is None:
        from ..dependencies import get_state
        state = get_state()
        from knowledge_agent.discovery import DailyDiscoveryManager
        discovery_manager = DailyDiscoveryManager(
            catalog_manager=state.catalog_manager,
            knowledge_store=state.knowledge_store
        )
    return discovery_manager


class HotspotItem(BaseModel):
    title: str
    summary: str
    source: str
    url: str
    relevance: float
    category: str
    fetched_at: str


class NextTopic(BaseModel):
    topic: str
    reason: str
    priority: str
    type: str


class ExpandDirection(BaseModel):
    direction: str
    description: str
    related_topics: List[str]
    type: str


class DeepDiveArea(BaseModel):
    area: str
    current_level: str
    suggested_depth: str
    type: str


class LearningRecommendations(BaseModel):
    next_topics: List[NextTopic]
    expand_directions: List[ExpandDirection]
    deep_dive_areas: List[DeepDiveArea]
    generated_at: str


class KnowledgeGap(BaseModel):
    domain: str
    current_count: int
    suggested_min: int
    gap_type: str


class KnowledgeGapsAnalysis(BaseModel):
    total_domains: int
    total_knowledge: int
    domain_distribution: Dict[str, int]
    identified_gaps: List[KnowledgeGap]


class DiscoverySummary(BaseModel):
    knowledge_summary: Dict[str, Any]
    knowledge_gaps: KnowledgeGapsAnalysis
    search_enabled: bool
    generated_at: str


@router.get("/hotspots", response_model=List[HotspotItem])
async def get_daily_hotspots(
    max_items: int = Query(10, description="最大返回数量")
):
    manager = get_discovery_manager()
    try:
        hotspots = await asyncio.to_thread(manager.get_daily_hotspots, max_items=max_items)
        return [HotspotItem(**h) for h in hotspots]
    except Exception as e:
        logger.error(f"获取每日热点失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取每日热点失败: {str(e)}")


@router.get("/recommendations", response_model=LearningRecommendations)
async def get_learning_recommendations():
    manager = get_discovery_manager()
    try:
        recommendations = await asyncio.to_thread(manager.get_learning_recommendations)
        return LearningRecommendations(**recommendations)
    except Exception as e:
        logger.error(f"获取学习推荐失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取学习推荐失败: {str(e)}")


@router.get("/gaps", response_model=KnowledgeGapsAnalysis)
async def analyze_knowledge_gaps():
    manager = get_discovery_manager()
    try:
        gaps = await asyncio.to_thread(manager.analyze_knowledge_gaps)
        return KnowledgeGapsAnalysis(**gaps)
    except Exception as e:
        logger.error(f"分析知识盲区失败: {e}")
        raise HTTPException(status_code=500, detail=f"分析知识盲区失败: {str(e)}")


@router.get("/summary", response_model=DiscoverySummary)
async def get_discovery_summary():
    manager = get_discovery_manager()
    try:
        summary = await asyncio.to_thread(manager.get_discovery_summary)
        return DiscoverySummary(**summary)
    except Exception as e:
        logger.error(f"获取发现摘要失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取发现摘要失败: {str(e)}")


@router.post("/refresh-cache")
async def refresh_discovery_cache():
    global discovery_manager
    discovery_manager = None
    return {"message": "Discovery cache refreshed"}
