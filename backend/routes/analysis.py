from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
import asyncio

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

logger = logging.getLogger(__name__)

similarity_analyzer = None
knowledge_organizer = None


def get_similarity_analyzer():
    global similarity_analyzer
    if similarity_analyzer is None:
        from ..dependencies import get_state
        state = get_state()
        from knowledge_agent.analysis import SimilarityAnalyzer
        similarity_analyzer = SimilarityAnalyzer(
            knowledge_store=state.knowledge_store,
            catalog_manager=state.catalog_manager
        )
    return similarity_analyzer


def get_knowledge_organizer():
    global knowledge_organizer
    if knowledge_organizer is None:
        from ..dependencies import get_state
        state = get_state()
        from knowledge_agent.analysis import KnowledgeOrganizer
        knowledge_organizer = KnowledgeOrganizer(
            knowledge_store=state.knowledge_store,
            catalog_manager=state.catalog_manager
        )
    return knowledge_organizer


class DistributionStats(BaseModel):
    total_knowledge: int
    total_pairs: int
    mean_similarity: float
    median_similarity: float
    std_similarity: float
    min_similarity: float
    max_similarity: float
    high_similarity_count: int
    high_similarity_threshold: float
    distribution_bins: List[Dict[str, Any]]


class SimilarPair(BaseModel):
    id1: str
    id2: str
    question1: str
    question2: str
    similarity: float
    catalog_id1: str
    catalog_id2: str


class DuplicateGroup(BaseModel):
    primary_id: str
    primary_question: str
    duplicates: List[Dict[str, Any]]


class CatalogDistribution(BaseModel):
    catalog_id: str
    catalog_name: str
    knowledge_count: int


class ReorganizationSuggestion(BaseModel):
    catalog_id: str
    catalog_name: str
    current_count: int
    suggested_action: str
    reason: str


class MergeSuggestion(BaseModel):
    primary_id: str
    primary_question: str
    duplicate_ids: List[str]
    duplicate_questions: List[str]
    merged_question: str
    merged_answer: str
    similarity_scores: List[float]


class MergeRequest(BaseModel):
    primary_id: str
    duplicate_ids: List[str]
    merged_question: str = None
    merged_answer: str = None


class SplitCatalogRequest(BaseModel):
    catalog_id: str
    sub_catalog_configs: List[Dict[str, Any]]


class AutoOrganizeRequest(BaseModel):
    merge_threshold: float = 0.90
    max_items_per_catalog: int = 20


@router.get("/distribution", response_model=DistributionStats)
async def get_distribution(
    threshold: float = Query(0.85, description="高相似度阈值")
):
    analyzer = get_similarity_analyzer()
    try:
        stats = await asyncio.to_thread(analyzer.analyze_distribution, high_similarity_threshold=threshold)
        return DistributionStats(**stats.__dict__)
    except Exception as e:
        logger.error(f"分析分布失败: {e}")
        raise HTTPException(status_code=500, detail=f"分析分布失败: {str(e)}")


@router.get("/distribution/chart")
async def get_distribution_chart():
    analyzer = get_similarity_analyzer()
    try:
        return await asyncio.to_thread(analyzer.get_distribution_chart_data)
    except Exception as e:
        logger.error(f"获取分布图表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取分布图表失败: {str(e)}")


@router.get("/similar-pairs", response_model=List[SimilarPair])
async def get_similar_pairs(
    threshold: float = Query(0.85, description="相似度阈值"),
    limit: int = Query(50, description="返回数量限制")
):
    analyzer = get_similarity_analyzer()
    try:
        pairs = await asyncio.to_thread(analyzer.find_similar_pairs, threshold=threshold, limit=limit)
        return [SimilarPair(**p.__dict__) for p in pairs]
    except Exception as e:
        logger.error(f"查找相似对失败: {e}")
        raise HTTPException(status_code=500, detail=f"查找相似对失败: {str(e)}")


@router.get("/duplicates", response_model=List[DuplicateGroup])
async def get_duplicates(
    threshold: float = Query(0.90, description="重复检测阈值")
):
    analyzer = get_similarity_analyzer()
    try:
        duplicates = await asyncio.to_thread(analyzer.find_duplicates, threshold=threshold)
        return [DuplicateGroup(**d) for d in duplicates]
    except Exception as e:
        logger.error(f"查找重复项失败: {e}")
        raise HTTPException(status_code=500, detail=f"查找重复项失败: {str(e)}")


@router.get("/catalog-distribution", response_model=List[CatalogDistribution])
async def get_catalog_distribution():
    analyzer = get_similarity_analyzer()
    try:
        return await asyncio.to_thread(analyzer.analyze_catalog_distribution)
    except Exception as e:
        logger.error(f"获取目录分布失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取目录分布失败: {str(e)}")


@router.get("/reorganization-suggestions", response_model=List[ReorganizationSuggestion])
async def get_reorganization_suggestions(
    max_items: int = Query(20, description="每个目录最大知识条目数")
):
    analyzer = get_similarity_analyzer()
    try:
        return await asyncio.to_thread(analyzer.suggest_catalog_reorganization, max_items_per_catalog=max_items)
    except Exception as e:
        logger.error(f"获取重组建议失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取重组建议失败: {str(e)}")


@router.get("/merge-suggestions", response_model=List[MergeSuggestion])
async def get_merge_suggestions(
    threshold: float = Query(0.90, description="相似度阈值")
):
    organizer = get_knowledge_organizer()
    try:
        suggestions = await asyncio.to_thread(organizer.find_merge_candidates, similarity_threshold=threshold)
        return [MergeSuggestion(**s.__dict__) for s in suggestions]
    except Exception as e:
        logger.error(f"获取合并建议失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取合并建议失败: {str(e)}")


@router.post("/merge")
async def merge_knowledge(request: MergeRequest):
    organizer = get_knowledge_organizer()
    try:
        result = await asyncio.to_thread(
            organizer.merge_knowledge,
            primary_id=request.primary_id,
            duplicate_ids=request.duplicate_ids,
            merged_question=request.merged_question,
            merged_answer=request.merged_answer
        )
        if result:
            return {"message": "合并成功", "knowledge_id": result.id}
        return {"message": "合并失败"}
    except Exception as e:
        logger.error(f"合并知识失败: {e}")
        raise HTTPException(status_code=500, detail=f"合并知识失败: {str(e)}")


@router.post("/generate-merged-content")
async def generate_merged_content(request: MergeRequest):
    organizer = get_knowledge_organizer()
    try:
        question, answer = await asyncio.to_thread(
            organizer.generate_merged_content,
            primary_id=request.primary_id,
            duplicate_ids=request.duplicate_ids
        )
        return {"question": question, "answer": answer}
    except Exception as e:
        logger.error(f"生成合并内容失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成合并内容失败: {str(e)}")


@router.get("/catalog-split-suggestion/{catalog_id}")
async def get_catalog_split_suggestion(
    catalog_id: str,
    max_items: int = Query(20, description="每个目录最大知识条目数")
):
    organizer = get_knowledge_organizer()
    try:
        suggestion = await asyncio.to_thread(organizer.analyze_catalog_for_split, catalog_id, max_items)
        if suggestion:
            return {
                "catalog_id": suggestion.catalog_id,
                "catalog_name": suggestion.catalog_name,
                "current_count": suggestion.current_count,
                "suggested_sub_catalogs": suggestion.suggested_sub_catalogs
            }
        return {"message": "该目录无需拆分"}
    except Exception as e:
        logger.error(f"获取目录拆分建议失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取目录拆分建议失败: {str(e)}")


@router.post("/split-catalog")
async def split_catalog(request: SplitCatalogRequest):
    organizer = get_knowledge_organizer()
    try:
        new_catalog_ids = await asyncio.to_thread(
            organizer.split_catalog,
            catalog_id=request.catalog_id,
            sub_catalog_configs=request.sub_catalog_configs
        )
        return {"message": "拆分成功", "new_catalog_ids": new_catalog_ids}
    except Exception as e:
        logger.error(f"拆分目录失败: {e}")
        raise HTTPException(status_code=500, detail=f"拆分目录失败: {str(e)}")


@router.post("/auto-organize")
async def auto_organize(request: AutoOrganizeRequest = AutoOrganizeRequest()):
    organizer = get_knowledge_organizer()
    try:
        result = await asyncio.to_thread(
            organizer.auto_organize,
            merge_threshold=request.merge_threshold,
            max_items_per_catalog=request.max_items_per_catalog
        )
        return result
    except Exception as e:
        logger.error(f"自动整理失败: {e}")
        raise HTTPException(status_code=500, detail=f"自动整理失败: {str(e)}")


@router.get("/organization-summary")
async def get_organization_summary():
    organizer = get_knowledge_organizer()
    try:
        return await asyncio.to_thread(organizer.get_organization_summary)
    except Exception as e:
        logger.error(f"获取组织摘要失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取组织摘要失败: {str(e)}")


@router.post("/refresh-cache")
async def refresh_cache():
    global similarity_analyzer, knowledge_organizer
    similarity_analyzer = None
    knowledge_organizer = None
    return {"message": "Cache refreshed"}


@router.get("/knowledge-space")
async def get_knowledge_space():
    analyzer = get_similarity_analyzer()
    try:
        return await asyncio.to_thread(analyzer.get_knowledge_space_coordinates)
    except Exception as e:
        logger.error(f"获取知识空间失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取知识空间失败: {str(e)}")


@router.get("/similarity-heatmap")
async def get_similarity_heatmap(
    max_items: int = Query(50, description="最大显示条目数"),
    cluster_by_catalog: bool = Query(True, description="按目录聚类")
):
    analyzer = get_similarity_analyzer()
    try:
        return await asyncio.to_thread(
            analyzer.get_similarity_heatmap_data,
            max_items=max_items,
            cluster_by_catalog=cluster_by_catalog
        )
    except Exception as e:
        logger.error(f"获取相似度热力图失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取相似度热力图失败: {str(e)}")


@router.get("/similarity-network")
async def get_similarity_network(
    threshold: float = Query(0.7, description="相似度阈值"),
    max_nodes: int = Query(100, description="最大节点数")
):
    analyzer = get_similarity_analyzer()
    try:
        return await asyncio.to_thread(
            analyzer.get_similarity_network,
            threshold=threshold,
            max_nodes=max_nodes
        )
    except Exception as e:
        logger.error(f"获取相似度网络失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取相似度网络失败: {str(e)}")


@router.get("/knowledge-clusters")
async def get_knowledge_clusters(
    n_clusters: int = Query(None, description="聚类数量")
):
    analyzer = get_similarity_analyzer()
    try:
        return await asyncio.to_thread(analyzer.get_knowledge_clusters, n_clusters=n_clusters)
    except Exception as e:
        logger.error(f"获取知识聚类失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取知识聚类失败: {str(e)}")


@router.post("/sync-catalog-counts")
async def sync_catalog_counts():
    from ..dependencies import get_state
    state = get_state()
    
    all_knowledge = state.knowledge_store.get_all_knowledge()
    stats = state.catalog_manager.sync_knowledge_items(all_knowledge)
    
    global similarity_analyzer, knowledge_organizer
    similarity_analyzer = None
    knowledge_organizer = None
    
    return {
        "message": "目录计数同步完成",
        **stats
    }
