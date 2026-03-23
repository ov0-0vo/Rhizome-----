import asyncio
import logging
import threading
import time
from typing import Optional

from .config import feishu_config
from .message import FeishuMessageHandler

logger = logging.getLogger(__name__)


class FeishuLongPollClient:
    def __init__(self, message_handler: FeishuMessageHandler = None):
        self.config = feishu_config
        self.message_handler = message_handler
        self._running = False
        self._ws_client = None
        self._thread: Optional[threading.Thread] = None
    
    def connect(self):
        if not self.config.enabled:
            logger.warning("Feishu bot not configured, skipping long poll connection")
            return
        
        logger.info(f"Feishu config: app_id={self.config.app_id[:8] if self.config.app_id else 'None'}...")
        
        self._running = True
        
        self._thread = threading.Thread(target=self._run_in_new_loop, daemon=True)
        self._thread.start()
        logger.info("Feishu WebSocket client thread started")
    
    def _run_in_new_loop(self):
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        
        import lark_oapi as lark
        
        try:
            while self._running:
                try:
                    self._start_ws_client(lark)
                except Exception as e:
                    logger.error(f"WebSocket client error: {e}")
                    if self._running:
                        logger.info("Attempting to reconnect in 5 seconds...")
                        time.sleep(5)
        finally:
            new_loop.close()
    
    def _start_ws_client(self, lark):
        def on_message(data: lark.im.v1.P2ImMessageReceiveV1) -> None:
            try:
                logger.info("Received message event")
                self.message_handler.handle_message(data)
            except Exception as e:
                logger.error(f"Error in message handler: {e}", exc_info=True)
        
        event_handler = lark.EventDispatcherHandler.builder("", "") \
            .register_p2_im_message_receive_v1(on_message) \
            .build()
        
        self._ws_client = lark.ws.Client(
            self.config.app_id,
            self.config.app_secret,
            event_handler=event_handler,
            log_level=lark.LogLevel.INFO
        )
        
        logger.info("Starting Feishu WebSocket connection...")
        self._ws_client.start()
    
    def stop(self):
        self._running = False
        logger.info("Stopping Feishu long poll client")
    
    async def start_async(self):
        self.connect()
