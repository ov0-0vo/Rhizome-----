import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Iterator

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import Tool

from ..agent.qa_agent import QAAgent, create_llm
from ..tools.search_tool import WebSearchManager
from ..config import config

logger = logging.getLogger(__name__)

SEARCH_SYSTEM_PROMPT = """你是一个智能知识助手，可以访问本地知识库和互联网搜索。

当用户的问题涉及以下情况时，你应该使用联网搜索：
1. 最新新闻、事件或动态
2. 实时数据（如天气、股价、汇率等）
3. 本地知识库中没有的信息
4. 需要验证或补充的信息

搜索结果会作为上下文提供给你，请基于搜索结果给出准确、有帮助的回答。
如果搜索结果不足或不可用，请如实告知用户。

回答时请：
- 简洁明了，直接回答问题
- 如果使用了搜索结果，可以适当引用来源
- 保持友好和专业的语气"""


class SearchEnabledAgent:
    def __init__(
        self,
        qa_agent: QAAgent = None,
        web_search_manager: WebSearchManager = None
    ):
        self.qa_agent = qa_agent or QAAgent()
        self.web_search_manager = web_search_manager or WebSearchManager()
        self.llm = create_llm(streaming=True)
        self.llm_non_streaming = create_llm(streaming=False)
    
    def _should_search(self, question: str) -> bool:
        if not self.web_search_manager.is_enabled():
            return False
        
        search_keywords = [
            "最新", "新闻", "今天", "昨天", "最近",
            "当前", "现在", "实时", "即时",
            "天气", "股价", "汇率", "价格",
            "搜索", "查找", "网上", "互联网"
        ]
        
        question_lower = question.lower()
        for keyword in search_keywords:
            if keyword in question_lower:
                return True
        
        return False
    
    def _search_and_context(self, question: str) -> Tuple[str, List[Dict[str, Any]]]:
        if not self._should_search(question):
            return "", []
        
        logger.info(f"[SearchEnabledAgent] 执行联网搜索: {question}")
        search_start = time.time()
        
        search_results = self.web_search_manager.search(question, max_results=5)
        
        logger.info(f"[SearchEnabledAgent] 搜索完成, 耗时: {time.time() - search_start:.3f}s, 结果数: {len(search_results)}")
        
        if not search_results:
            return "", []
        
        context_parts = []
        for i, result in enumerate(search_results, 1):
            if result.url:
                context_parts.append(f"【{i}】{result.title}\n来源: {result.url}\n{result.content}")
            else:
                context_parts.append(f"【{i}】{result.title}\n{result.content}")
        
        context = "\n\n".join(context_parts)
        
        results_data = [
            {
                "title": r.title,
                "url": r.url,
                "content": r.content[:200] + "..." if len(r.content) > 200 else r.content,
                "score": r.score
            }
            for r in search_results
        ]
        
        return context, results_data
    
    def chat_with_search(
        self,
        question: str,
        use_search: bool = True
    ) -> Tuple[str, Dict[str, Any]]:
        total_start = time.time()
        logger.info(f"[SearchEnabledAgent] 开始处理问题: {question}")
        
        metadata = {
            "used_search": False,
            "search_results": [],
            "used_local_knowledge": False,
            "local_knowledge_count": 0
        }
        
        search_context = ""
        if use_search and self._should_search(question):
            search_context, search_results = self._search_and_context(question)
            if search_context:
                metadata["used_search"] = True
                metadata["search_results"] = search_results
        
        local_context = ""
        local_knowledge = self.qa_agent.retrieve_knowledge(question)
        if local_knowledge:
            metadata["used_local_knowledge"] = True
            metadata["local_knowledge_count"] = len(local_knowledge)
            
            local_context = "\n\n".join([
                f"【本地知识 {i+1}】\n问题: {k['question']}\n答案: {k['answer']}"
                for i, k in enumerate(local_knowledge)
            ])
        
        context_parts = []
        if search_context:
            context_parts.append("=== 互联网搜索结果 ===\n" + search_context)
        if local_context:
            context_parts.append("=== 本地知识库 ===\n" + local_context)
        
        if context_parts:
            full_context = "\n\n".join(context_parts)
            prompt = f"""基于以下信息回答用户的问题。

{full_context}

用户问题: {question}

请给出准确、有帮助的回答。如果使用了搜索结果，请注明来源。"""
            
            messages = [
                SystemMessage(content=SEARCH_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]
        else:
            messages = [
                SystemMessage(content=SEARCH_SYSTEM_PROMPT),
                HumanMessage(content=question)
            ]
        
        answer = self.llm_non_streaming.invoke(messages).content
        
        logger.info(f"[SearchEnabledAgent] 处理完成, 总耗时: {time.time() - total_start:.3f}s")
        
        return answer, metadata
    
    def chat_with_search_stream(
        self,
        question: str,
        use_search: bool = True
    ) -> Tuple[Iterator[str], Dict[str, Any]]:
        total_start = time.time()
        logger.info(f"[SearchEnabledAgent] 开始流式处理问题: {question}")
        
        metadata = {
            "used_search": False,
            "search_results": [],
            "used_local_knowledge": False,
            "local_knowledge_count": 0
        }
        
        search_context = ""
        if use_search and self._should_search(question):
            search_context, search_results = self._search_and_context(question)
            if search_context:
                metadata["used_search"] = True
                metadata["search_results"] = search_results
        
        local_context = ""
        local_knowledge = self.qa_agent.retrieve_knowledge(question)
        if local_knowledge:
            metadata["used_local_knowledge"] = True
            metadata["local_knowledge_count"] = len(local_knowledge)
            
            local_context = "\n\n".join([
                f"【本地知识 {i+1}】\n问题: {k['question']}\n答案: {k['answer']}"
                for i, k in enumerate(local_knowledge)
            ])
        
        context_parts = []
        if search_context:
            context_parts.append("=== 互联网搜索结果 ===\n" + search_context)
        if local_context:
            context_parts.append("=== 本地知识库 ===\n" + local_context)
        
        if context_parts:
            full_context = "\n\n".join(context_parts)
            prompt = f"""基于以下信息回答用户的问题。

{full_context}

用户问题: {question}

请给出准确、有帮助的回答。如果使用了搜索结果，请注明来源。"""
            
            messages = [
                SystemMessage(content=SEARCH_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]
        else:
            messages = [
                SystemMessage(content=SEARCH_SYSTEM_PROMPT),
                HumanMessage(content=question)
            ]
        
        def answer_stream():
            for chunk in self.llm.stream(messages):
                if chunk.content:
                    yield chunk.content
            
            logger.info(f"[SearchEnabledAgent] 流式处理完成, 总耗时: {time.time() - total_start:.3f}s")
        
        return answer_stream(), metadata
    
    def get_search_status(self) -> Dict[str, Any]:
        return self.web_search_manager.get_status()
    
    def enable_search(self, api_key: str = None) -> bool:
        if api_key:
            return self.web_search_manager.enable(api_key)
        return self.web_search_manager.is_enabled()
    
    def disable_search(self):
        self.web_search_manager.disable()
