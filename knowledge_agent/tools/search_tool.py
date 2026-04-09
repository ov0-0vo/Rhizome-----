import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from langchain_core.tools import Tool
from langchain_tavily import TavilySearch

from ..config import config

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    score: float


class TavilySearchTool:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY", "")
        self._tool = None
        
        if self.api_key:
            self._init_tool()
    
    def _init_tool(self):
        try:
            self._tool = TavilySearch(
                max_results=5,
                topic="general",
                include_answer=True,
                include_raw_content=False,
                include_images=False,
                search_depth="basic"
            )
            logger.info("Tavily 搜索工具初始化成功")
        except Exception as e:
            logger.error(f"Tavily 搜索工具初始化失败: {e}")
            self._tool = None
    
    def is_available(self) -> bool:
        return self._tool is not None
    
    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        if not self.is_available():
            logger.warning("Tavily 搜索工具不可用")
            return []
        
        try:
            results = self._tool.invoke({"query": query})
            
            search_results = []
            
            if isinstance(results, dict):
                if "results" in results:
                    for item in results["results"][:max_results]:
                        search_results.append(SearchResult(
                            title=item.get("title", ""),
                            url=item.get("url", ""),
                            content=item.get("content", ""),
                            score=item.get("score", 0.0)
                        ))
                
                if "answer" in results and results["answer"]:
                    search_results.insert(0, SearchResult(
                        title="AI 摘要",
                        url="",
                        content=results["answer"],
                        score=1.0
                    ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    def get_langchain_tool(self) -> Optional[Tool]:
        if not self.is_available():
            return None
        
        return Tool(
            name="web_search",
            description="使用 Tavily 搜索引擎在互联网上搜索信息。当需要查找最新信息、新闻、事实或本地知识库中没有的内容时使用。",
            func=self._search_wrapper
        )
    
    def _search_wrapper(self, query: str) -> str:
        results = self.search(query)
        
        if not results:
            return "未找到相关搜索结果"
        
        output = []
        for i, result in enumerate(results, 1):
            if result.url:
                output.append(f"【{i}】{result.title}\n来源: {result.url}\n{result.content}")
            else:
                output.append(f"【{i}】{result.title}\n{result.content}")
        
        return "\n\n".join(output)


class WebSearchManager:
    def __init__(self):
        self.tavily_tool = TavilySearchTool()
        self._enabled = self.tavily_tool.is_available()
    
    def is_enabled(self) -> bool:
        return self._enabled
    
    def enable(self, api_key: str):
        self.tavily_tool = TavilySearchTool(api_key=api_key)
        self._enabled = self.tavily_tool.is_available()
        return self._enabled
    
    def disable(self):
        self._enabled = False
    
    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        if not self._enabled:
            return []
        return self.tavily_tool.search(query, max_results)
    
    def search_and_format(self, query: str, max_results: int = 5) -> str:
        results = self.search(query, max_results)
        
        if not results:
            return ""
        
        output = ["以下是来自互联网的搜索结果：\n"]
        for i, result in enumerate(results, 1):
            if result.url:
                output.append(f"**{i}. {result.title}**\n来源: {result.url}\n{result.content}\n")
            else:
                output.append(f"**{i}. {result.title}**\n{result.content}\n")
        
        return "\n".join(output)
    
    def get_tools(self) -> List[Tool]:
        if not self._enabled:
            return []
        
        tool = self.tavily_tool.get_langchain_tool()
        return [tool] if tool else []
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "enabled": self._enabled,
            "provider": "tavily" if self._enabled else None,
            "api_key_configured": bool(os.getenv("TAVILY_API_KEY"))
        }
