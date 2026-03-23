import json
import logging
from typing import Optional

from .config import feishu_config
from .client import FeishuClient

logger = logging.getLogger(__name__)


class FeishuMessageHandler:
    def __init__(self, qa_agent=None):
        self.client = FeishuClient()
        self.qa_agent = qa_agent
    
    def handle_message(self, event) -> None:
        try:
            message = event.event.message
            message_id = message.message_id
            message_type = message.message_type
            content = message.content
            
            sender = event.event.sender
            sender_id = sender.sender_id.user_id if sender.sender_id else None
            
            logger.info(f"Message from {sender_id}: type={message_type}")
            
            if message_type != "text":
                self.client.reply_text(message_id, "暂不支持非文本消息类型")
                return
            
            try:
                content_data = json.loads(content)
                text = content_data.get("text", "").strip()
            except json.JSONDecodeError:
                text = content.strip()
            
            if not text:
                return
            
            if text.startswith("/"):
                self._handle_command(message_id, text)
            else:
                self._handle_question(message_id, text)
                
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
    
    def _handle_command(self, message_id: str, command: str) -> None:
        command = command.lower().strip()
        
        if command in ["/help", "/帮助"]:
            card = self.client.create_help_card()
            self.client.reply_card(message_id, card)
        
        elif command in ["/stats", "/统计"]:
            if not self.qa_agent:
                self.client.reply_text(message_id, "知识库未初始化")
                return
            
            stats = self.qa_agent.get_statistics()
            card = self.client.create_stats_card(stats)
            self.client.reply_card(message_id, card)
        
        elif command.startswith("/search ") or command.startswith("/搜索 "):
            if not self.qa_agent:
                self.client.reply_text(message_id, "知识库未初始化")
                return
            
            keyword = command.split(" ", 1)[1].strip()
            results = self.qa_agent.search_knowledge(keyword)
            
            if not results:
                self.client.reply_text(message_id, f"未找到与「{keyword}」相关的知识")
                return
            
            top_result = results[0]
            card = self.client.create_answer_card(
                question=top_result.get("question", ""),
                answer=top_result.get("answer", ""),
                keywords=top_result.get("keywords", []),
                similarity=top_result.get("similarity")
            )
            self.client.reply_card(message_id, card)
        
        else:
            self.client.reply_text(message_id, f"未知命令: {command}\n发送 /help 查看可用命令")
    
    def _handle_question(self, message_id: str, question: str) -> None:
        if not self.qa_agent:
            self.client.reply_text(message_id, "知识库未初始化")
            return
        
        try:
            result = self.qa_agent.chat(question)
            answer = result.get("answer", "")
            keywords = result.get("analysis", {}).get("keywords", [])
            
            card = self.client.create_answer_card(
                question=question,
                answer=answer,
                keywords=keywords
            )
            self.client.reply_card(message_id, card)
        
        except Exception as e:
            logger.error(f"Error processing question: {e}", exc_info=True)
            card = self.client.create_error_card(str(e))
            self.client.reply_card(message_id, card)
