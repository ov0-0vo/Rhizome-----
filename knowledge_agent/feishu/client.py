import json
import logging
from typing import Dict, Any, List, Optional

from .config import feishu_config

logger = logging.getLogger(__name__)


class FeishuClient:
    def __init__(self):
        self.config = feishu_config
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            import lark_oapi as lark
            self._client = lark.Client.builder() \
                .app_id(self.config.app_id) \
                .app_secret(self.config.app_secret) \
                .log_level(lark.LogLevel.ERROR) \
                .build()
        return self._client
    
    def reply_text(self, message_id: str, text: str) -> bool:
        from lark_oapi.api.im.v1 import ReplyMessageRequest, ReplyMessageRequestBody
        
        request = ReplyMessageRequest.builder() \
            .message_id(message_id) \
            .request_body(ReplyMessageRequestBody.builder()
                .msg_type("text")
                .content(json.dumps({"text": text}))
                .build()) \
            .build()
        
        response = self.client.im.v1.message.reply(request)
        
        if not response.success():
            logger.error(f"Reply message failed: code={response.code}, msg={response.msg}")
            return False
        
        return True

    def reply_text_with_id(self, message_id: str, text: str) -> Optional[str]:
        from lark_oapi.api.im.v1 import ReplyMessageRequest, ReplyMessageRequestBody
        
        request = ReplyMessageRequest.builder() \
            .message_id(message_id) \
            .request_body(ReplyMessageRequestBody.builder()
                .msg_type("text")
                .content(json.dumps({"text": text}))
                .build()) \
            .build()
        
        response = self.client.im.v1.message.reply(request)
        
        if not response.success():
            logger.error(f"Reply message failed: code={response.code}, msg={response.msg}")
            return None
        
        return response.data.message_id
    
    def reply_card(self, message_id: str, card: Dict[str, Any]) -> bool:
        from lark_oapi.api.im.v1 import ReplyMessageRequest, ReplyMessageRequestBody
        
        request = ReplyMessageRequest.builder() \
            .message_id(message_id) \
            .request_body(ReplyMessageRequestBody.builder()
                .msg_type("interactive")
                .content(json.dumps(card))
                .build()) \
            .build()
        
        response = self.client.im.v1.message.reply(request)
        
        if not response.success():
            logger.error(f"Reply card failed: code={response.code}, msg={response.msg}")
            return False
        
        return True

    def reply_card_with_id(self, message_id: str, card: Dict[str, Any]) -> Optional[str]:
        from lark_oapi.api.im.v1 import ReplyMessageRequest, ReplyMessageRequestBody
        
        request = ReplyMessageRequest.builder() \
            .message_id(message_id) \
            .request_body(ReplyMessageRequestBody.builder()
                .msg_type("interactive")
                .content(json.dumps(card))
                .build()) \
            .build()
        
        response = self.client.im.v1.message.reply(request)
        
        if not response.success():
            logger.error(f"Reply card failed: code={response.code}, msg={response.msg}")
            return None
        
        return response.data.message_id
    
    def send_text(self, receive_id: str, text: str, receive_id_type: str = "chat_id") -> bool:
        from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody
        
        request = CreateMessageRequest.builder() \
            .receive_id_type(receive_id_type) \
            .request_body(CreateMessageRequestBody.builder()
                .receive_id(receive_id)
                .msg_type("text")
                .content(json.dumps({"text": text}))
                .build()) \
            .build()
        
        response = self.client.im.v1.message.create(request)
        
        if not response.success():
            logger.error(f"Send message failed: code={response.code}, msg={response.msg}")
            return False
        
        return True
    
    def create_answer_card(
        self,
        question: str,
        answer: str,
        keywords: List[str] = None,
        similarity: float = None
    ) -> Dict[str, Any]:
        content = f"**问题:**\n{question}\n\n**回答:**\n{answer}"
        
        if keywords:
            keywords_text = " ".join([f"`{kw}`" for kw in keywords[:5]])
            content += f"\n\n**关键词:** {keywords_text}"
        
        if similarity is not None:
            content += f"\n\n**相似度:** {similarity:.1%}"
        
        return {
            "config": {
                "wide_screen_mode": True
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": content
                }
            ]
        }
    
    def create_help_card(self) -> Dict[str, Any]:
        help_text = """**Rhizome 知识机器人帮助**

可用命令:
- `/help` - 显示帮助信息
- `/stats` - 查看知识库统计
- `/search <关键词>` - 搜索知识

直接发送问题，机器人会智能回答并保存知识。"""
        
        return {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "markdown",
                    "content": help_text
                }
            ]
        }
    
    def create_stats_card(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        stats_text = f"""**知识库统计**

- 总知识条目: {stats.get('total_knowledge', 0)}
- 目录数量: {stats.get('catalogs_count', 0)}"""
        
        return {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "markdown",
                    "content": stats_text
                }
            ]
        }
    
    def create_error_card(self, error_msg: str) -> Dict[str, Any]:
        return {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "markdown",
                    "content": f"❌ **错误:**\n{error_msg}"
                }
            ]
        }

    def push_follow_up(self, message_id: str, content: str = "机器人正在处理中...") -> bool:
        try:
            from lark_oapi.api.im.v1 import PushFollowUpRequest, PushFollowUpRequestBody, FollowUp
            
            follow_up = FollowUp.builder().content(content).build()

            request = PushFollowUpRequest.builder() \
                .message_id(message_id) \
                .request_body(PushFollowUpRequestBody.builder()
                    .follow_ups([follow_up])
                    .build()) \
                .build()

            response = self.client.im.v1.message.push_follow_up(request)

            if not response.success():
                logger.error(f"Push follow up failed: code={response.code}, msg={response.msg}")
                return False

            return True
        except ImportError:
            logger.warning("PushFollowUpRequest not available in current lark-oapi version, skipping follow up")
            return True

    def edit_card(self, message_id: str, card: Dict[str, Any]) -> bool:
        try:
            from lark_oapi.api.im.v1 import PatchMessageRequest, PatchMessageRequestBody

            request = PatchMessageRequest.builder() \
                .message_id(message_id) \
                .request_body(PatchMessageRequestBody.builder()
                    .content(json.dumps(card))
                    .build()) \
                .build()

            response = self.client.im.v1.message.patch(request)

            if not response.success():
                logger.error(f"Edit message failed: code={response.code}, msg={response.msg}")
                return False

            return True
        except ImportError:
            logger.warning("PatchMessageRequest not available in current lark-oapi version, skipping message edit")
            return True
