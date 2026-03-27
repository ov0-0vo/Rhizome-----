from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import json
import logging

router = APIRouter(prefix="/api/reflection", tags=["reflection"])

logger = logging.getLogger(__name__)

reflection_manager = None


def get_reflection_manager():
    global reflection_manager
    if reflection_manager is None:
        from ..dependencies import get_state
        state = get_state()
        from knowledge_agent.reflection import ReflectionManager
        reflection_manager = ReflectionManager(
            knowledge_store=state.knowledge_store,
            catalog_manager=state.catalog_manager
        )
    return reflection_manager


class CreateSessionRequest(BaseModel):
    topic: str = ""


class ChatRequest(BaseModel):
    session_id: str
    message: str
    topic: str = ""


class ArchiveRequest(BaseModel):
    session_id: str
    catalog_id: Optional[str] = None


class Message(BaseModel):
    role: str
    content: str
    timestamp: str


class SessionInfo(BaseModel):
    id: str
    topic: str
    messages: List[Message]
    created_at: str
    updated_at: str


class ArchiveResult(BaseModel):
    knowledge_id: str
    question: str
    answer: str
    catalog_id: Optional[str] = None
    catalog_name: Optional[str] = None


@router.post("/session", response_model=SessionInfo)
async def create_session(request: CreateSessionRequest):
    manager = get_reflection_manager()
    session = manager.create_session(request.topic)
    
    return SessionInfo(
        id=session.id,
        topic=session.topic,
        messages=[],
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat()
    )


@router.get("/session/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    manager = get_reflection_manager()
    session = manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = manager.get_session_messages(session_id)
    
    return SessionInfo(
        id=session.id,
        topic=session.topic,
        messages=[Message(**msg) for msg in messages],
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat()
    )


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    manager = get_reflection_manager()
    manager.delete_session(session_id)
    return {"message": "Session deleted"}


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    manager = get_reflection_manager()
    
    async def generate():
        logger.info(f"Starting stream for session {request.session_id}")
        try:
            async for key, value in manager.chat_stream(
                session_id=request.session_id,
                user_message=request.message,
                topic=request.topic
            ):
                data = f"data: {json.dumps({key: value}, ensure_ascii=False)}\n\n"
                logger.debug(f"Yielding: {key} = {value[:50] if isinstance(value, str) else value}")
                yield data
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/archive/stream")
async def archive_stream(request: ArchiveRequest):
    manager = get_reflection_manager()
    
    async def generate():
        logger.info(f"Starting archive stream for session {request.session_id}")
        try:
            async for key, value in manager.summarize_stream(
                session_id=request.session_id
            ):
                data = f"data: {json.dumps({key: value}, ensure_ascii=False)}\n\n"
                logger.debug(f"Archive yielding: {key}")
                yield data
        except Exception as e:
            logger.error(f"Archive stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/archive", response_model=ArchiveResult)
async def archive_session(request: ArchiveRequest):
    manager = get_reflection_manager()
    
    result = manager.summarize_and_archive(
        session_id=request.session_id,
        catalog_id=request.catalog_id
    )
    
    if not result:
        raise HTTPException(status_code=400, detail="Cannot archive empty session")
    
    catalog_name = None
    if result.get("catalog_id"):
        from ..dependencies import get_state
        state = get_state()
        catalog = state.catalog_manager.get_catalog(result["catalog_id"])
        if catalog:
            catalog_name = catalog.name
    
    return ArchiveResult(
        knowledge_id=result["knowledge_id"],
        question=result["question"],
        answer=result["answer"],
        catalog_id=result.get("catalog_id"),
        catalog_name=catalog_name
    )
