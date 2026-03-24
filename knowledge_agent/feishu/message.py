import json
import logging
import time
import threading
from typing import Optional
from collections import OrderedDict

from .config import feishu_config
from .client import FeishuClient

logger = logging.getLogger(__name__)

UPDATE_THROTTLE_INTERVAL = 0.5
MAX_PROCESSED_MESSAGES = 1000
MESSAGE_EXPIRE_SECONDS = 3600


class FeishuMessageHandler:
    def __init__(self, qa_agent=None):
        self.client = FeishuClient()
        self.qa_agent = qa_agent
        self.processed_message_ids = OrderedDict()

    def handle_message(self, event) -> None:
        try:
            message = event.event.message
            message_id = message.message_id
            message_type = message.message_type
            content = message.content

            if message_id in self.processed_message_ids:
                logger.info(f"Duplicate message detected: {message_id}, skipping")
                return

            self._cleanup_expired_messages()
            
            if len(self.processed_message_ids) >= MAX_PROCESSED_MESSAGES:
                self.processed_message_ids.popitem(last=False)
            
            self.processed_message_ids[message_id] = time.time()

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
                self._handle_question_stream(message_id, text)

        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)

    def _cleanup_expired_messages(self) -> None:
        current_time = time.time()
        expired_ids = [
            msg_id for msg_id, timestamp in self.processed_message_ids.items()
            if current_time - timestamp > MESSAGE_EXPIRE_SECONDS
        ]
        for msg_id in expired_ids:
            del self.processed_message_ids[msg_id]

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

    def _handle_question_stream(self, message_id: str, question: str) -> None:
        if not self.qa_agent:
            self.client.reply_text(message_id, "知识库未初始化")
            return

        processing_card = {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "markdown",
                    "content": "🤔 **正在思考中...**"
                }
            ]
        }

        reply_msg_id = self.client.reply_card_with_id(message_id, processing_card)

        if reply_msg_id:
            self.client.push_follow_up(reply_msg_id, "正在处理您的问题...")

        try:
            stream_iter, metadata = self.qa_agent.chat_with_stream(question)
            keywords = metadata.get("analysis", {}).get("keywords", [])

            accumulated_content = ""
            last_update_time = 0

            for chunk in stream_iter:
                accumulated_content += chunk
                now = time.time()

                if (now - last_update_time) >= UPDATE_THROTTLE_INTERVAL:
                    self._update_streaming_card(reply_msg_id, question, accumulated_content, keywords)
                    last_update_time = now

            self._update_streaming_card(reply_msg_id, question, accumulated_content, keywords, is_final=True)

        except Exception as e:
            logger.error(f"Error processing question: {e}", exc_info=True)
            error_card = self.client.create_error_card(str(e))
            if reply_msg_id:
                self.client.edit_card(reply_msg_id, error_card)
            else:
                self.client.reply_card(message_id, error_card)

    def _update_streaming_card(
        self,
        message_id: Optional[str],
        question: str,
        answer: str,
        keywords: list,
        is_final: bool = False
    ) -> None:
        if not message_id:
            return

        content = f"**问题:**\n{question}\n\n**回答:**\n{answer}"

        if keywords:
            keywords_text = " ".join([f"`{kw}`" for kw in keywords[:5]])
            content += f"\n\n**关键词:** {keywords_text}"

        if not is_final:
            content += "\n\n⏳ *正在生成...*"

        card = {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "markdown",
                    "content": content
                }
            ]
        }

        self.client.edit_card(message_id, card)

    def _handle_question(self, message_id: str, question: str) -> None:
        if not self.qa_agent:
            self.client.reply_text(message_id, "知识库未初始化")
            return

        processing_card = {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "markdown",
                    "content": "🤔 **正在思考中...**"
                }
            ]
        }

        reply_msg_id = self.client.reply_card_with_id(message_id, processing_card)

        if reply_msg_id:
            self.client.push_follow_up(reply_msg_id, "正在处理您的问题...")

        try:
            result = self.qa_agent.chat(question)
            answer = result.get("answer", "")
            keywords = result.get("analysis", {}).get("keywords", [])

            card = self.client.create_answer_card(
                question=question,
                answer=answer,
                keywords=keywords
            )

            if reply_msg_id:
                self.client.edit_card(reply_msg_id, card)
            else:
                self.client.reply_card(message_id, card)

        except Exception as e:
            logger.error(f"Error processing question: {e}", exc_info=True)
            error_card = self.client.create_error_card(str(e))
            if reply_msg_id:
                self.client.edit_card(reply_msg_id, error_card)
            else:
                self.client.reply_card(message_id, error_card)
