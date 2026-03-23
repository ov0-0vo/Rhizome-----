from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging

from knowledge_agent.feishu import feishu_config

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/status")
async def feishu_status():
    return {
        "enabled": feishu_config.enabled,
        "app_id": feishu_config.app_id[:8] + "..." if feishu_config.app_id else None,
        "mode": "long_poll"
    }
