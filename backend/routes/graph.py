from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from collections import Counter

from ..dependencies import get_state

router = APIRouter()


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    size: int = 10
    catalog_id: Optional[str] = None


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str
    weight: float = 1.0


class KnowledgeGraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


@router.get("", response_model=KnowledgeGraph)
async def get_knowledge_graph():
    current_state = get_state()
    
    nodes = []
    edges = []
    
    catalogs = current_state.catalog_manager.get_all_catalogs()
    knowledge_items = current_state.knowledge_store.get_all_knowledge()
    
    catalog_map = {c.id: c for c in catalogs}
    
    for catalog in catalogs:
        nodes.append(GraphNode(
            id=f"catalog-{catalog.id}",
            label=catalog.name,
            type="catalog",
            size=15 + len(catalog.knowledge_items) * 2
        ))
        
        if catalog.parent_id:
            edges.append(GraphEdge(
                source=f"catalog-{catalog.parent_id}",
                target=f"catalog-{catalog.id}",
                type="parent-child"
            ))
    
    for item in knowledge_items:
        nodes.append(GraphNode(
            id=f"knowledge-{item.id}",
            label=item.question[:30] + "..." if len(item.question) > 30 else item.question,
            type="knowledge",
            size=10,
            catalog_id=item.catalog_id
        ))
        
        if item.catalog_id:
            edges.append(GraphEdge(
                source=f"catalog-{item.catalog_id}",
                target=f"knowledge-{item.id}",
                type="contains"
            ))
    
    keyword_connections = {}
    for item in knowledge_items:
        for kw in item.keywords:
            if kw not in keyword_connections:
                keyword_connections[kw] = []
            keyword_connections[kw].append(item.id)
    
    for kw, item_ids in keyword_connections.items():
        if len(item_ids) > 1:
            nodes.append(GraphNode(
                id=f"keyword-{kw}",
                label=kw,
                type="keyword",
                size=8 + len(item_ids)
            ))
            
            for item_id in item_ids:
                edges.append(GraphEdge(
                    source=f"keyword-{kw}",
                    target=f"knowledge-{item_id}",
                    type="has-keyword",
                    weight=0.5
                ))
    
    return KnowledgeGraph(nodes=nodes, edges=edges)


class KeywordNetwork(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


@router.get("/keywords", response_model=KeywordNetwork)
async def get_keyword_network(limit: int = 50):
    current_state = get_state()
    
    knowledge_items = current_state.knowledge_store.get_all_knowledge()
    
    keyword_items = {}
    for item in knowledge_items:
        for kw in item.keywords:
            if kw not in keyword_items:
                keyword_items[kw] = []
            keyword_items[kw].append(item.id)
    
    keyword_counter = Counter({k: len(v) for k, v in keyword_items.items()})
    top_keywords = keyword_counter.most_common(limit)
    
    nodes = []
    edges = []
    
    for kw, count in top_keywords:
        nodes.append({
            "id": kw,
            "label": kw,
            "size": 10 + count * 2,
            "count": count
        })
    
    keyword_list = [kw for kw, _ in top_keywords]
    for i, kw1 in enumerate(keyword_list):
        for kw2 in keyword_list[i+1:]:
            common_items = set(keyword_items[kw1]) & set(keyword_items[kw2])
            if common_items:
                edges.append({
                    "source": kw1,
                    "target": kw2,
                    "weight": len(common_items)
                })
    
    return {"nodes": nodes, "edges": edges}


@router.get("/catalog/{catalog_id}", response_model=KnowledgeGraph)
async def get_catalog_graph(catalog_id: str):
    current_state = get_state()
    
    nodes = []
    edges = []
    
    catalog = current_state.catalog_manager.get_catalog(catalog_id)
    if not catalog:
        return KnowledgeGraph(nodes=[], edges=[])
    
    nodes.append(GraphNode(
        id=f"catalog-{catalog.id}",
        label=catalog.name,
        type="catalog",
        size=20
    ))
    
    descendant_ids = current_state.catalog_manager.get_all_descendant_ids(catalog_id)
    
    for child_id in descendant_ids:
        if child_id == catalog_id:
            continue
        child = current_state.catalog_manager.get_catalog(child_id)
        if child:
            nodes.append(GraphNode(
                id=f"catalog-{child.id}",
                label=child.name,
                type="catalog",
                size=15 + len(child.knowledge_items)
            ))
            
            if child.parent_id:
                edges.append(GraphEdge(
                    source=f"catalog-{child.parent_id}",
                    target=f"catalog-{child.id}",
                    type="parent-child"
                ))
    
    for cid in descendant_ids:
        items = current_state.knowledge_store.get_knowledge_by_catalog(cid)
        for item in items:
            nodes.append(GraphNode(
                id=f"knowledge-{item.id}",
                label=item.question[:30] + "..." if len(item.question) > 30 else item.question,
                type="knowledge",
                size=10,
                catalog_id=item.catalog_id
            ))
            
            edges.append(GraphEdge(
                source=f"catalog-{item.catalog_id}",
                target=f"knowledge-{item.id}",
                type="contains"
            ))
    
    return KnowledgeGraph(nodes=nodes, edges=edges)
