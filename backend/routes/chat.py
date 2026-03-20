from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import json
import asyncio

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


class HistoryItem(BaseModel):
    id: str
    question: str
    answer: str
    catalog_name: Optional[str] = None
    created_at: str


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


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    from ..dependencies import get_state
    current_state = get_state()

    async def event_generator():
        try:
            stream_iter, metadata = current_state.qa_agent.chat_with_stream(request.message)

            catalog_name = None
            if metadata.get("catalog_id"):
                catalog = current_state.catalog_manager.get_catalog(metadata["catalog_id"])
                if catalog:
                    catalog_name = catalog.name

            for chunk in stream_iter:
                data = {
                    "type": "chunk",
                    "content": chunk
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

            final_data = {
                "type": "done",
                "metadata": {
                    "catalog_id": metadata.get("catalog_id"),
                    "catalog_name": catalog_name,
                    "is_new": metadata.get("is_new", True)
                }
            }
            yield f"data: {json.dumps(final_data, ensure_ascii=False)}\n\n"

        except Exception as e:
            error_data = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/history", response_model=List[HistoryItem])
async def get_history(limit: int = 20):
    from ..dependencies import get_state
    current_state = get_state()

    all_knowledge = current_state.qa_agent.get_all_knowledge()
    recent = sorted(all_knowledge, key=lambda x: x.created_at, reverse=True)[:limit]

    history = []
    for item in recent:
        catalog_name = None
        if item.catalog_id:
            catalog = current_state.catalog_manager.get_catalog(item.catalog_id)
            if catalog:
                catalog_name = catalog.name

        history.append(HistoryItem(
            id=item.id,
            question=item.question,
            answer=item.answer,
            catalog_name=catalog_name,
            created_at=item.created_at
        ))

    return history
