import logging
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from langchain_core.messages import HumanMessage

from ..agent.qa_agent import create_llm
from ..knowledge.catalog_manager import CatalogManager
from ..knowledge.knowledge_store import KnowledgeStore
from ..tools.search_tool import WebSearchManager

logger = logging.getLogger(__name__)


HOTSPOT_SEARCH_PROMPT = """你是一个知识热点分析助手。根据用户的知识领域，生成用于搜索最新热点和趋势的搜索关键词。

用户的知识领域：
{knowledge_domains}

请生成3-5个搜索关键词，用于搜索与这些领域相关的最新热点、技术动态、行业新闻。
要求：
1. 关键词应该聚焦于"最新"、"2024"、"趋势"、"突破"等时效性词汇
2. 每个关键词应该具体且有针对性
3. 返回JSON格式：{{"keywords": ["关键词1", "关键词2", ...]}}
"""

LEARNING_RECOMMENDATION_PROMPT = """你是一个学习规划助手。根据用户已有的知识体系和知识盲区，推荐下一步学习方向。

用户已有知识概览：
{knowledge_overview}

用户的知识盲区分析：
{knowledge_gaps}

请分析用户的知识体系，并推荐：
1. 下一步应该学习的具体知识点（3-5个）
2. 需要拓展的知识方向（2-3个）
3. 建议深入学习的领域（1-2个）

返回JSON格式：
{{
    "next_topics": [
        {{"topic": "知识点名称", "reason": "推荐理由", "priority": "high/medium/low"}},
        ...
    ],
    "expand_directions": [
        {{"direction": "拓展方向", "description": "详细描述", "related_topics": ["相关知识点"]}},
        ...
    ],
    "deep_dive_areas": [
        {{"area": "深入领域", "current_level": "当前水平", "suggested_depth": "建议深度"}},
        ...
    ]
}}
"""

KNOWLEDGE_SUMMARY_PROMPT = """请总结用户的知识体系，提取主要的知识领域和关键词。

知识目录结构：
{catalog_structure}

最近学习的知识条目：
{recent_knowledge}

请返回JSON格式：
{{
    "main_domains": ["领域1", "领域2", ...],
    "keywords": ["关键词1", "关键词2", ...],
    "knowledge_level": "beginner/intermediate/advanced",
    "focus_areas": ["重点领域1", "重点领域2", ...]
}}
"""


@dataclass
class HotspotItem:
    title: str
    summary: str
    source: str
    url: str
    relevance: float
    category: str


@dataclass
class LearningRecommendation:
    topic: str
    reason: str
    priority: str
    type: str


@dataclass
class ExpandDirection:
    direction: str
    description: str
    related_topics: List[str]


class DailyDiscoveryManager:
    def __init__(
        self,
        catalog_manager: CatalogManager = None,
        knowledge_store: KnowledgeStore = None
    ):
        self.catalog_manager = catalog_manager or CatalogManager()
        self.knowledge_store = knowledge_store or KnowledgeStore()
        self.llm = create_llm(streaming=False)
        self.web_search = WebSearchManager()
    
    def _get_knowledge_summary(self) -> Dict[str, Any]:
        catalogs = self.catalog_manager.get_all_catalogs()
        all_knowledge = self.knowledge_store.get_all_knowledge()
        
        catalog_structure = []
        for catalog in catalogs[:10]:
            catalog_structure.append({
                "name": catalog.name,
                "keywords": catalog.keywords[:5],
                "knowledge_count": len(catalog.knowledge_items)
            })
        
        recent_knowledge = []
        sorted_knowledge = sorted(all_knowledge, key=lambda x: x.created_at, reverse=True)[:10]
        for item in sorted_knowledge:
            recent_knowledge.append({
                "question": item.question[:100],
                "keywords": item.keywords[:3]
            })
        
        try:
            prompt = KNOWLEDGE_SUMMARY_PROMPT.format(
                catalog_structure=json.dumps(catalog_structure, ensure_ascii=False, indent=2),
                recent_knowledge=json.dumps(recent_knowledge, ensure_ascii=False, indent=2)
            )
            
            result = self.llm.invoke([HumanMessage(content=prompt)])
            content = result.content.strip()
            
            json_match = json.dumps({})
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json.loads(json_match.group())
            return {}
        except Exception as e:
            logger.error(f"生成知识摘要失败: {e}")
            return {
                "main_domains": [c["name"] for c in catalog_structure[:5]],
                "keywords": [],
                "knowledge_level": "intermediate",
                "focus_areas": []
            }
    
    def _generate_search_keywords(self, knowledge_domains: List[str]) -> List[str]:
        if not knowledge_domains:
            return ["科技新闻", "技术趋势", "行业动态"]
        
        try:
            prompt = HOTSPOT_SEARCH_PROMPT.format(
                knowledge_domains="\n".join([f"- {d}" for d in knowledge_domains])
            )
            
            result = self.llm.invoke([HumanMessage(content=prompt)])
            content = result.content.strip()
            
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("keywords", knowledge_domains[:3])
            return knowledge_domains[:3]
        except Exception as e:
            logger.error(f"生成搜索关键词失败: {e}")
            return knowledge_domains[:3]
    
    def get_daily_hotspots(self, max_items: int = 10) -> List[Dict[str, Any]]:
        if not self.web_search.is_enabled():
            logger.warning("网络搜索未启用")
            return self._get_mock_hotspots()
        
        knowledge_summary = self._get_knowledge_summary()
        domains = knowledge_summary.get("main_domains", [])
        
        search_keywords = self._generate_search_keywords(domains)
        
        hotspots = []
        for keyword in search_keywords[:3]:
            try:
                results = self.web_search.search(f"{keyword} 最新 动态 2024", max_results=3)
                for result in results:
                    hotspots.append({
                        "title": result.title,
                        "summary": result.content[:300] if len(result.content) > 300 else result.content,
                        "source": result.url,
                        "url": result.url,
                        "relevance": result.score,
                        "category": keyword,
                        "fetched_at": datetime.now().isoformat()
                    })
            except Exception as e:
                logger.error(f"搜索热点失败 [{keyword}]: {e}")
        
        hotspots.sort(key=lambda x: x["relevance"], reverse=True)
        return hotspots[:max_items]
    
    def _get_mock_hotspots(self) -> List[Dict[str, Any]]:
        return [
            {
                "title": "网络搜索未启用",
                "summary": "请配置 TAVILY_API_KEY 以启用网络搜索功能，获取与您知识领域相关的最新热点内容。",
                "source": "",
                "url": "",
                "relevance": 0.5,
                "category": "系统提示",
                "fetched_at": datetime.now().isoformat()
            }
        ]
    
    def analyze_knowledge_gaps(self) -> Dict[str, Any]:
        catalogs = self.catalog_manager.get_all_catalogs()
        all_knowledge = self.knowledge_store.get_all_knowledge()
        
        domain_knowledge_count = {}
        for item in all_knowledge:
            if item.catalog_id:
                catalog = self.catalog_manager.get_catalog(item.catalog_id)
                if catalog:
                    domain = catalog.name
                    domain_knowledge_count[domain] = domain_knowledge_count.get(domain, 0) + 1
        
        gaps = []
        for catalog in catalogs:
            count = len(catalog.knowledge_items)
            if count < 3:
                gaps.append({
                    "domain": catalog.name,
                    "current_count": count,
                    "suggested_min": 5,
                    "gap_type": "knowledge_sparse"
                })
        
        return {
            "total_domains": len(catalogs),
            "total_knowledge": len(all_knowledge),
            "domain_distribution": domain_knowledge_count,
            "identified_gaps": gaps
        }
    
    def get_learning_recommendations(self) -> Dict[str, Any]:
        knowledge_summary = self._get_knowledge_summary()
        gaps = self.analyze_knowledge_gaps()
        
        overview_text = json.dumps({
            "domains": knowledge_summary.get("main_domains", []),
            "level": knowledge_summary.get("knowledge_level", "intermediate"),
            "focus": knowledge_summary.get("focus_areas", [])
        }, ensure_ascii=False, indent=2)
        
        gaps_text = json.dumps(gaps.get("identified_gaps", []), ensure_ascii=False, indent=2)
        
        try:
            prompt = LEARNING_RECOMMENDATION_PROMPT.format(
                knowledge_overview=overview_text,
                knowledge_gaps=gaps_text
            )
            
            result = self.llm.invoke([HumanMessage(content=prompt)])
            content = result.content.strip()
            
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                recommendations = json.loads(json_match.group())
                
                for topic in recommendations.get("next_topics", []):
                    topic["type"] = "next_topic"
                for direction in recommendations.get("expand_directions", []):
                    direction["type"] = "expand_direction"
                for area in recommendations.get("deep_dive_areas", []):
                    area["type"] = "deep_dive"
                
                return {
                    "next_topics": recommendations.get("next_topics", []),
                    "expand_directions": recommendations.get("expand_directions", []),
                    "deep_dive_areas": recommendations.get("deep_dive_areas", []),
                    "generated_at": datetime.now().isoformat()
                }
            
            return self._get_default_recommendations()
        except Exception as e:
            logger.error(f"生成学习推荐失败: {e}")
            return self._get_default_recommendations()
    
    def _get_default_recommendations(self) -> Dict[str, Any]:
        return {
            "next_topics": [
                {"topic": "继续探索您感兴趣的领域", "reason": "保持学习动力", "priority": "high", "type": "next_topic"}
            ],
            "expand_directions": [
                {"direction": "跨领域学习", "description": "尝试将不同领域的知识联系起来", "related_topics": [], "type": "expand_direction"}
            ],
            "deep_dive_areas": [
                {"area": "核心知识领域", "current_level": "待评估", "suggested_depth": "深入学习", "type": "deep_dive"}
            ],
            "generated_at": datetime.now().isoformat()
        }
    
    def get_discovery_summary(self) -> Dict[str, Any]:
        knowledge_summary = self._get_knowledge_summary()
        gaps = self.analyze_knowledge_gaps()
        
        return {
            "knowledge_summary": knowledge_summary,
            "knowledge_gaps": gaps,
            "search_enabled": self.web_search.is_enabled(),
            "generated_at": datetime.now().isoformat()
        }
