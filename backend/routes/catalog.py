from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class CatalogNode(BaseModel):
    id: str
    name: str
    keywords: List[str]
    knowledge_count: int
    children: List["CatalogNode"]


class CatalogInfo(BaseModel):
    id: str
    name: str
    keywords: List[str]
    parent_id: Optional[str] = None


class CreateCatalogRequest(BaseModel):
    name: str
    keywords: List[str] = []
    parent_id: Optional[str] = None


class UpdateCatalogRequest(BaseModel):
    name: str
    keywords: List[str] = []


CatalogNode.model_rebuild()


@router.get("/tree", response_model=Optional[CatalogNode])
async def get_catalog_tree():
    from ..dependencies import get_state
    current_state = get_state()
    tree = current_state.catalog_manager.get_catalog_tree()
    if not tree:
        return None

    def convert_node(node: dict) -> CatalogNode:
        return CatalogNode(
            id=node["id"],
            name=node["name"],
            keywords=node.get("keywords", []),
            knowledge_count=node.get("knowledge_count", 0),
            children=[convert_node(child) for child in node.get("children", [])]
        )

    return convert_node(tree)


@router.get("", response_model=List[CatalogInfo])
async def get_all_catalogs():
    from ..dependencies import get_state
    current_state = get_state()
    catalogs = current_state.catalog_manager.get_all_catalogs()
    return [
        CatalogInfo(
            id=c.id,
            name=c.name,
            keywords=c.keywords,
            parent_id=c.parent_id
        )
        for c in catalogs
    ]


@router.post("", response_model=CatalogInfo)
async def create_catalog(request: CreateCatalogRequest):
    from ..dependencies import get_state
    current_state = get_state()
    catalog = current_state.catalog_manager.create_catalog(
        name=request.name,
        keywords=request.keywords,
        parent_id=request.parent_id
    )
    return CatalogInfo(
        id=catalog.id,
        name=catalog.name,
        keywords=catalog.keywords,
        parent_id=catalog.parent_id
    )


@router.put("/{catalog_id}", response_model=CatalogInfo)
async def update_catalog(catalog_id: str, request: UpdateCatalogRequest):
    from ..dependencies import get_state
    current_state = get_state()
    catalog = current_state.catalog_manager.update_catalog(
        catalog_id=catalog_id,
        name=request.name,
        keywords=request.keywords
    )
    if not catalog:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Catalog not found")
    return CatalogInfo(
        id=catalog.id,
        name=catalog.name,
        keywords=catalog.keywords,
        parent_id=catalog.parent_id
    )


@router.delete("/{catalog_id}")
async def delete_catalog(catalog_id: str):
    from ..dependencies import get_state
    current_state = get_state()
    current_state.catalog_manager.delete_catalog(catalog_id)
    return {"message": "Catalog deleted successfully"}
