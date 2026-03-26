import uuid
from typing import Dict, List, Optional, AsyncIterator, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from ..agent.qa_agent import create_llm
from ..knowledge.knowledge_store import KnowledgeStore
from ..knowledge.catalog_manager import CatalogManager


@dataclass
class ReflectionMessage:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ReflectionSession:
    id: str
    topic: str
    messages: List[ReflectionMessage] = field(default_factory=list)
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

SUMMARY_PROMPT = """请根据以下对话历史，总结用户对知识的理解，生成一条完整的知识条目。

对话主题：{topic}

对话历史：
{conversation}

请生成：
1. 一个简洁的问题/标题（作为知识条目的question字段）
2. 完整的答案/解释（作为知识条目的answer字段）

请以JSON格式返回：
{{
    "question": "问题标题",
    "answer": "完整的答案内容"
}}"""


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
        
        session.messages.append(ReflectionMessage(
            role="user",
            content=user_message
        ))
        
        langchain_messages = [
            SystemMessage(content=REFLECTION_SYSTEM_PROMPT)
        ]
        
        for msg in session.messages[:-1]:
            if msg.role == "user":
                langchain_messages.append(HumanMessage(content=msg.content))
            else:
                langchain_messages.append(AIMessage(content=msg.content))
        
        langchain_messages.append(HumanMessage(content=user_message))
        
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
        
        session.messages.append(ReflectionMessage(
            role="assistant",
            content=full_response
        ))
        session.updated_at = datetime.now()
        
        yield ("session_id", session_id)
    
    def summarize_and_archive(
        self,
        session_id: str,
        catalog_id: str = None
    ) -> dict:
        session = self.get_session(session_id)
        if not session or not session.messages:
            return None
        
        conversation_text = "\n".join([
            f"{'用户' if msg.role == 'user' else '助手'}: {msg.content}"
            for msg in session.messages
        ])
        
        prompt = ChatPromptTemplate.from_template(SUMMARY_PROMPT)
        chain = prompt | self.llm_non_streaming
        
        result = chain.invoke({
            "topic": session.topic,
            "conversation": conversation_text
        })
        
        import json
        try:
            summary = json.loads(result.content)
        except:
            summary = {
                "question": session.topic,
                "answer": result.content
            }
        
        item = self.knowledge_store.add_knowledge(
            question=summary.get("question", session.topic),
            answer=summary.get("answer", ""),
            catalog_id=catalog_id
        )
        
        self.delete_session(session_id)
        
        return {
            "knowledge_id": item.id,
            "question": item.question,
            "answer": item.answer
        }
    
    def get_session_messages(self, session_id: str) -> List[dict]:
        session = self.get_session(session_id)
        if not session:
            return []
        
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in session.messages
        ]