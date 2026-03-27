from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import json
import asyncio
import logging
import time

router = APIRouter()
logger = logging.getLogger(__name__)


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
    request_start = time.time()
    logger.info(f"[PERF] ========== API /chat/stream 请求开始 ==========")
    logger.info(f"[PERF] 消息: {request.message[:100]}...")
    
    from ..dependencies import get_state
    current_state = get_state()

    async def event_generator():
        try:
            step_start = time.time()
            stream_iter, metadata = current_state.qa_agent.chat_with_stream(request.message)
            logger.info(f"[PERF] API层-获取stream迭代器耗时: {time.time() - step_start:.3f}s")

            catalog_name = None
            if metadata.get("catalog_id"):
                catalog = current_state.catalog_manager.get_catalog(metadata["catalog_id"])
                if catalog:
                    catalog_name = catalog.name

            chunk_count = 0
            for chunk in stream_iter:
                chunk_count += 1
                data = {
                    "type": "chunk",
                    "content": chunk
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

            logger.info(f"[PERF] API层-发送完成, chunks: {chunk_count}")

            final_data = {
                "type": "done",
                "metadata": {
                    "catalog_id": metadata.get("catalog_id"),
                    "catalog_name": catalog_name,
                    "is_new": metadata.get("is_new", True)
                }
            }
            yield f"data: {json.dumps(final_data, ensure_ascii=False)}\n\n"
            
            logger.info(f"[PERF] ========== API /chat/stream 总耗时: {time.time() - request_start:.3f}s ==========")

        except Exception as e:
            logger.error(f"[PERF] API错误: {e}")
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
