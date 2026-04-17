from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging

from .dependencies import state, get_state
from knowledge_agent.feishu import feishu_config, FeishuLongPollClient, FeishuMessageHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

feishu_client: FeishuLongPollClient = None
feishu_task: asyncio.Task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global feishu_client, feishu_task
    
    if feishu_config.enabled:
        current_state = get_state()
        message_handler = FeishuMessageHandler(qa_agent=current_state.qa_agent)
        feishu_client = FeishuLongPollClient(message_handler=message_handler)
        
        feishu_task = asyncio.create_task(feishu_client.start_async())
        logger.info("Feishu long poll client started")
    
    yield
    
    if feishu_client:
        feishu_client.stop()
        if feishu_task:
            feishu_task.cancel()
        logger.info("Feishu long poll client stopped")


app = FastAPI(
    title="Rhizome API",
    description="知识体系智能体 API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from .routes import chat, knowledge, catalog, graph, feishu, review, config, reflection, analysis, search, discovery, import_

app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge"])
app.include_router(catalog.router, prefix="/api/catalog", tags=["catalog"])
app.include_router(graph.router, prefix="/api/graph", tags=["graph"])
app.include_router(feishu.router, prefix="/api/feishu", tags=["feishu"])
app.include_router(review.router, tags=["review"])
app.include_router(config.router)
app.include_router(reflection.router)
app.include_router(analysis.router)
app.include_router(search.router)
app.include_router(discovery.router)
app.include_router(import_.router, prefix="/api/import", tags=["import"])


@app.get("/")
async def root():
    return {"message": "Rhizome API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    from fastapi.responses import JSONResponse
    checks = {
        "service": "rhizome-backend",
        "status": "healthy",
        "checks": {}
    }
    
    try:
        state = get_state()
        checks["checks"]["knowledge_store"] = "ok" if state.knowledge_store else "unavailable"
        checks["checks"]["catalog_manager"] = "ok" if state.catalog_manager else "unavailable"
        checks["checks"]["qa_agent"] = "ok" if state.qa_agent else "unavailable"
        
        if state.knowledge_store:
            try:
                items = state.knowledge_store.get_all_knowledge()
                checks["checks"]["knowledge_count"] = len(items)
            except Exception as e:
                checks["checks"]["knowledge_store"] = f"error: {str(e)[:50]}"
                checks["status"] = "degraded"
        
        if state.vector_store:
            try:
                ids = state.vector_store.get_all_ids()
                checks["checks"]["vector_count"] = len(ids)
            except Exception as e:
                checks["checks"]["vector_store"] = f"error: {str(e)[:50]}"
                checks["status"] = "degraded"
    except Exception as e:
        checks["status"] = "unhealthy"
        checks["error"] = str(e)
    
    status_code = 200 if checks["status"] == "healthy" else 503 if checks["status"] == "unhealthy" else 200
    return JSONResponse(content=checks, status_code=status_code)
