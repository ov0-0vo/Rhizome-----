from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    source: str
    knowledge_id: Optional[str] = None
    catalog_id: Optional[str] = None
    is_new: bool
    catalog_name: Optional[str] = None


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    from ..dependencies import get_state
    current_state = get_state()
    result = current_state.qa_agent.chat(request.message)

    catalog_name = None
    if result.get("catalog_id"):
        catalog = current_state.catalog_manager.get_catalog(result["catalog_id"])
        if catalog:
            catalog_name = catalog.name

    return ChatResponse(
        answer=result["answer"],
        source=result["source"],
        knowledge_id=result.get("knowledge_id"),
        catalog_id=result.get("catalog_id"),
        is_new=result["is_new"],
        catalog_name=catalog_name
    )
