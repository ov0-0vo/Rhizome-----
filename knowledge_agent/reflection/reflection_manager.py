import uuid
import json
from typing import Dict, List, Optional, AsyncIterator, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from ..agent.qa_agent import create_llm, QAAgent
from ..knowledge.knowledge_store import KnowledgeStore
from ..knowledge.catalog_manager import CatalogManager


@dataclass
class ReflectionSession:
    id: str
    topic: str
    messages: List[BaseMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


REFLECTION_SYSTEM_PROMPT = """你是一个知识理解和反思的辅导助手。你的任务是：

1. 倾听用户对某个知识点的理解和认知
2. 分析用户的理解是否正确、完整
3. 指出理解中的偏差或不足
4. 引导用户深入思考，补充遗漏的知识点
5. 用鼓励和引导的方式帮助用户建立正确的认知

注意事项：
- 保持耐心和友善的态度
- 使用具体的例子来说明概念
- 如果用户的理解基本正确，给予肯定并引导更深入的思考
- 如果理解有误，温和地指出并提供正确的解释
- 每次回复控制在200字以内，保持对话的互动性
- 不要一次性给出所有答案，而是通过提问引导用户思考"""

SUMMARY_SYSTEM_PROMPT = """你是一个知识总结助手。你的任务是根据对话历史，总结用户对知识的理解，生成一条完整的知识条目。

你需要生成：
1. 一个简洁的问题/标题（作为知识条目的question字段）
2. 完整的答案/解释（作为知识条目的answer字段）

请直接输出总结内容，格式如下：

## 问题
[简洁的问题标题]

## 答案
[完整的答案内容，要全面准确地总结对话中的知识点]"""


class ReflectionManager:
    def __init__(
        self,
        knowledge_store: KnowledgeStore = None,
        catalog_manager: CatalogManager = None
    ):
        self.sessions: Dict[str, ReflectionSession] = {}
        self.llm = create_llm(streaming=True)
        self.llm_non_streaming = create_llm(streaming=False)
        self.knowledge_store = knowledge_store or KnowledgeStore()
        self.catalog_manager = catalog_manager or CatalogManager()
    
    def create_session(self, topic: str = "") -> ReflectionSession:
        session_id = str(uuid.uuid4())
        session = ReflectionSession(
            id=session_id,
            topic=topic or "知识理解反思"
        )
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[ReflectionSession]:
        return self.sessions.get(session_id)
    
    def delete_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def _build_chat_messages(self, session: ReflectionSession, user_message: str) -> List[BaseMessage]:
        messages = [SystemMessage(content=REFLECTION_SYSTEM_PROMPT)]
        messages.extend(session.messages)
        messages.append(HumanMessage(content=user_message))
        return messages
    
    async def chat_stream(
        self,
        session_id: str,
        user_message: str,
        topic: str = ""
    ) -> AsyncIterator[Tuple[str, str]]:
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(topic)
            session_id = session.id
        
        if topic and not session.topic:
            session.topic = topic
        
        langchain_messages = self._build_chat_messages(session, user_message)
        
        print(f"[ReflectionManager] Starting LLM stream with {len(langchain_messages)} messages")
        
        full_response = ""
        chunk_count = 0
        async for chunk in self.llm.astream(langchain_messages):
            chunk_count += 1
            if chunk.content:
                full_response += chunk.content
                if chunk_count <= 3 or chunk_count % 10 == 0:
                    print(f"[ReflectionManager] Chunk {chunk_count}: {chunk.content[:50]}...")
                yield ("content", chunk.content)
        
        print(f"[ReflectionManager] Stream complete. Total chunks: {chunk_count}, Total length: {len(full_response)}")
        
        session.messages.append(HumanMessage(content=user_message))
        session.messages.append(AIMessage(content=full_response))
        session.updated_at = datetime.now()
        
        yield ("session_id", session_id)
    
    def _build_summary_messages(self, session: ReflectionSession) -> List[BaseMessage]:
        messages = [SystemMessage(content=SUMMARY_SYSTEM_PROMPT)]
        
        conversation_context = f"对话主题：{session.topic}\n\n以下是完整的对话历史：\n\n"
        for msg in session.messages:
            role = "用户" if isinstance(msg, HumanMessage) else "助手"
            conversation_context += f"**{role}**: {msg.content}\n\n"
        
        messages.append(HumanMessage(content=conversation_context))
        return messages
    
    def _parse_summary(self, summary_text: str) -> Tuple[str, str]:
        question = ""
        answer = ""
        
        lines = summary_text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            if line.strip().startswith('## 问题') or line.strip().startswith('##问题'):
                if current_section == 'answer' and current_content:
                    answer = '\n'.join(current_content).strip()
                current_section = 'question'
                current_content = []
            elif line.strip().startswith('## 答案') or line.strip().startswith('##答案'):
                if current_section == 'question' and current_content:
                    question = '\n'.join(current_content).strip()
                current_section = 'answer'
                current_content = []
            elif current_section:
                current_content.append(line)
        
        if current_section == 'answer' and current_content:
            answer = '\n'.join(current_content).strip()
        
        if not question:
            question = session.topic if 'session' in dir() else "知识总结"
        if not answer:
            answer = summary_text
        
        return question, answer
    
    async def summarize_stream(
        self,
        session_id: str
    ) -> AsyncIterator[Tuple[str, str]]:
        session = self.get_session(session_id)
        if not session or not session.messages:
            yield ("error", "没有可总结的对话内容")
            return
        
        summary_messages = self._build_summary_messages(session)
        
        print(f"[ReflectionManager] Starting summary stream with {len(summary_messages)} messages")
        
        full_summary = ""
        chunk_count = 0
        async for chunk in self.llm.astream(summary_messages):
            chunk_count += 1
            if chunk.content:
                full_summary += chunk.content
                yield ("summary", chunk.content)
        
        print(f"[ReflectionManager] Summary complete. Total length: {len(full_summary)}")
        
        question, answer = self._parse_summary(full_summary)
        
        qa_agent = QAAgent(
            catalog_manager=self.catalog_manager,
            knowledge_store=self.knowledge_store
        )
        
        analysis = qa_agent.analyze_question(question)
        knowledge_metadata = qa_agent.extract_knowledge_metadata(question, answer)
        keywords = list(set(analysis.get("keywords", []) + knowledge_metadata.get("keywords", [])))
        
        catalog_id, match_reason = qa_agent.match_catalog(question)
        
        item = self.knowledge_store.add_knowledge(
            question=question,
            answer=answer,
            catalog_id=catalog_id,
            keywords=keywords
        )
        
        if catalog_id:
            self.catalog_manager.add_knowledge_to_catalog(catalog_id, item.id)
        
        catalog_name = None
        if catalog_id:
            catalog = self.catalog_manager.get_catalog(catalog_id)
            if catalog:
                catalog_name = catalog.name
        
        self.delete_session(session_id)
        
        yield ("done", json.dumps({
            "knowledge_id": item.id,
            "question": question,
            "answer": answer,
            "catalog_id": catalog_id,
            "catalog_name": catalog_name,
            "keywords": keywords
        }, ensure_ascii=False))
    
    def summarize_and_archive(
        self,
        session_id: str,
        catalog_id: str = None
    ) -> dict:
        session = self.get_session(session_id)
        if not session or not session.messages:
            return None
        
        summary_messages = self._build_summary_messages(session)
        
        result = self.llm_non_streaming.invoke(summary_messages)
        summary_text = result.content
        
        question, answer = self._parse_summary(summary_text)
        
        qa_agent = QAAgent(
            catalog_manager=self.catalog_manager,
            knowledge_store=self.knowledge_store
        )
        
        analysis = qa_agent.analyze_question(question)
        knowledge_metadata = qa_agent.extract_knowledge_metadata(question, answer)
        keywords = list(set(analysis.get("keywords", []) + knowledge_metadata.get("keywords", [])))
        
        if catalog_id is None:
            catalog_id, match_reason = qa_agent.match_catalog(question)
        
        item = self.knowledge_store.add_knowledge(
            question=question,
            answer=answer,
            catalog_id=catalog_id,
            keywords=keywords
        )
        
        if catalog_id:
            self.catalog_manager.add_knowledge_to_catalog(catalog_id, item.id)
        
        self.delete_session(session_id)
        
        return {
            "knowledge_id": item.id,
            "question": item.question,
            "answer": item.answer,
            "catalog_id": catalog_id,
            "keywords": keywords
        }
    
    def get_session_messages(self, session_id: str) -> List[dict]:
        session = self.get_session(session_id)
        if not session:
            return []
        
        return [
            {
                "role": "user" if isinstance(msg, HumanMessage) else "assistant",
                "content": msg.content,
                "timestamp": datetime.now().isoformat()
            }
            for msg in session.messages
        ]
