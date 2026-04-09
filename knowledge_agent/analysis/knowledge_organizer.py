import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from ..knowledge.knowledge_store import KnowledgeStore
from ..knowledge.catalog_manager import CatalogManager
from ..knowledge.models import KnowledgeItem
from ..agent.qa_agent import create_llm
from .similarity_analyzer import SimilarityAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class MergeSuggestion:
    primary_id: str
    primary_question: str
    duplicate_ids: List[str]
    duplicate_questions: List[str]
    merged_question: str
    merged_answer: str
    similarity_scores: List[float]


@dataclass
class CatalogSplitSuggestion:
    catalog_id: str
    catalog_name: str
    current_count: int
    suggested_sub_catalogs: List[Dict[str, Any]]


class KnowledgeOrganizer:
    def __init__(
        self,
        knowledge_store: KnowledgeStore = None,
        catalog_manager: CatalogManager = None
    ):
        self.knowledge_store = knowledge_store or KnowledgeStore()
        self.catalog_manager = catalog_manager or CatalogManager()
        self.similarity_analyzer = SimilarityAnalyzer(
            knowledge_store=self.knowledge_store,
            catalog_manager=self.catalog_manager
        )
        self.llm = create_llm(streaming=False)
    
    def find_merge_candidates(
        self,
        similarity_threshold: float = 0.90
    ) -> List[MergeSuggestion]:
        duplicates = self.similarity_analyzer.find_duplicates(threshold=similarity_threshold)
        
        merge_suggestions = []
        processed_ids = set()
        
        for dup_group in duplicates:
            primary_id = dup_group["primary_id"]
            
            if primary_id in processed_ids:
                continue
            
            primary_item = self.knowledge_store.get_knowledge(primary_id)
            if not primary_item:
                continue
            
            duplicate_ids = []
            duplicate_questions = []
            similarity_scores = []
            
            for dup in dup_group["duplicates"]:
                dup_id = dup["id"]
                if dup_id not in processed_ids:
                    duplicate_ids.append(dup_id)
                    duplicate_questions.append(dup["question"])
                    similarity_scores.append(dup["similarity"])
                    processed_ids.add(dup_id)
            
            if duplicate_ids:
                processed_ids.add(primary_id)
                merge_suggestions.append(MergeSuggestion(
                    primary_id=primary_id,
                    primary_question=primary_item.question,
                    duplicate_ids=duplicate_ids,
                    duplicate_questions=duplicate_questions,
                    merged_question=primary_item.question,
                    merged_answer=primary_item.answer,
                    similarity_scores=similarity_scores
                ))
        
        return merge_suggestions
    
    def generate_merged_content(
        self,
        primary_id: str,
        duplicate_ids: List[str]
    ) -> Tuple[str, str]:
        primary_item = self.knowledge_store.get_knowledge(primary_id)
        if not primary_item:
            return "", ""
        
        all_items = [primary_item]
        for dup_id in duplicate_ids:
            dup_item = self.knowledge_store.get_knowledge(dup_id)
            if dup_item:
                all_items.append(dup_item)
        
        if len(all_items) == 1:
            return primary_item.question, primary_item.answer
        
        combined_text = "\n\n".join([
            f"【条目{i+1}】\n问题: {item.question}\n答案: {item.answer}"
            for i, item in enumerate(all_items)
        ])
        
        from langchain_core.messages import HumanMessage
        
        prompt = f"""请将以下{len(all_items)}个相似的知识条目合并为一个更完整的条目。

{combined_text}

请输出合并后的内容，格式如下：
## 问题
[合并后的问题，保留最完整的表述]

## 答案
[合并后的答案，整合所有相关信息，去除重复内容]"""

        try:
            result = self.llm.invoke([HumanMessage(content=prompt)])
            content = result.content
            
            question = ""
            answer = ""
            
            lines = content.split('\n')
            current_section = None
            current_content = []
            
            for line in lines:
                if '## 问题' in line or '##问题' in line:
                    if current_section == 'answer' and current_content:
                        answer = '\n'.join(current_content).strip()
                    current_section = 'question'
                    current_content = []
                elif '## 答案' in line or '##答案' in line:
                    if current_section == 'question' and current_content:
                        question = '\n'.join(current_content).strip()
                    current_section = 'answer'
                    current_content = []
                elif current_section:
                    current_content.append(line)
            
            if current_section == 'answer' and current_content:
                answer = '\n'.join(current_content).strip()
            
            if not question:
                question = primary_item.question
            if not answer:
                answer = primary_item.answer
            
            return question, answer
            
        except Exception as e:
            logger.error(f"生成合并内容失败: {e}")
            return primary_item.question, primary_item.answer
    
    def merge_knowledge(
        self,
        primary_id: str,
        duplicate_ids: List[str],
        merged_question: str = None,
        merged_answer: str = None
    ) -> Optional[KnowledgeItem]:
        if merged_question is None or merged_answer is None:
            merged_question, merged_answer = self.generate_merged_content(primary_id, duplicate_ids)
        
        primary_item = self.knowledge_store.get_knowledge(primary_id)
        if not primary_item:
            return None
        
        all_keywords = list(primary_item.keywords)
        all_sources = list(primary_item.sources)
        
        for dup_id in duplicate_ids:
            dup_item = self.knowledge_store.get_knowledge(dup_id)
            if dup_item:
                all_keywords.extend(dup_item.keywords)
                all_sources.extend(dup_item.sources)
        
        all_keywords = list(set(all_keywords))
        all_sources = list(set(all_sources))
        
        updated_item = self.knowledge_store.update_knowledge(
            knowledge_id=primary_id,
            question=merged_question,
            answer=merged_answer,
            keywords=all_keywords,
            sources=all_sources
        )
        
        for dup_id in duplicate_ids:
            dup_item = self.knowledge_store.get_knowledge(dup_id)
            if dup_item and dup_item.catalog_id:
                self.catalog_manager.remove_knowledge_from_catalog(dup_item.catalog_id, dup_id)
            self.knowledge_store.delete_knowledge(dup_id)
            logger.info(f"已删除重复知识: {dup_id}")
        
        logger.info(f"知识合并完成: 主条目 {primary_id}, 合并了 {len(duplicate_ids)} 条重复")
        return updated_item
    
    def analyze_catalog_for_split(
        self,
        catalog_id: str,
        max_items: int = 20
    ) -> Optional[CatalogSplitSuggestion]:
        catalog = self.catalog_manager.get_catalog(catalog_id)
        if not catalog:
            return None
        
        items = self.knowledge_store.get_knowledge_by_catalog(catalog_id)
        if len(items) <= max_items:
            return None
        
        item_texts = [
            f"- {item.question}: {item.answer[:100]}..."
            for item in items[:50]
        ]
        
        from langchain_core.messages import HumanMessage
        
        prompt = f"""请分析以下{len(items)}条知识，建议如何将它们拆分为子目录。

知识条目：
{chr(10).join(item_texts)}

请输出建议的子目录，格式为JSON数组：
[
  {{"name": "子目录名称", "keywords": ["关键词1", "关键词2"], "description": "描述"}},
  ...
]"""

        try:
            result = self.llm.invoke([HumanMessage(content=prompt)])
            content = result.content
            
            import json
            import re
            
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                sub_catalogs = json.loads(json_match.group())
            else:
                sub_catalogs = []
            
            return CatalogSplitSuggestion(
                catalog_id=catalog_id,
                catalog_name=catalog.name,
                current_count=len(items),
                suggested_sub_catalogs=sub_catalogs
            )
            
        except Exception as e:
            logger.error(f"分析目录拆分失败: {e}")
            return None
    
    def split_catalog(
        self,
        catalog_id: str,
        sub_catalog_configs: List[Dict[str, Any]]
    ) -> List[str]:
        catalog = self.catalog_manager.get_catalog(catalog_id)
        if not catalog:
            return []
        
        items = self.knowledge_store.get_knowledge_by_catalog(catalog_id)
        new_catalog_ids = []
        
        for config in sub_catalog_configs:
            new_catalog = self.catalog_manager.create_catalog(
                name=config["name"],
                keywords=config.get("keywords", []),
                parent_id=catalog_id
            )
            new_catalog_ids.append(new_catalog.id)
            
            keywords = config.get("keywords", [])
            for item in items:
                item_keywords = set(item.keywords)
                config_keywords = set(keywords)
                
                if item_keywords & config_keywords:
                    self.knowledge_store.update_knowledge(
                        knowledge_id=item.id,
                        catalog_id=new_catalog.id
                    )
                    self.catalog_manager.add_knowledge_to_catalog(new_catalog.id, item.id)
        
        logger.info(f"目录拆分完成: {catalog.name} -> {len(new_catalog_ids)} 个子目录")
        return new_catalog_ids
    
    def auto_organize(
        self,
        merge_threshold: float = 0.90,
        max_items_per_catalog: int = 20
    ) -> Dict[str, Any]:
        merge_suggestions = self.find_merge_candidates(merge_threshold)
        merged_count = 0
        
        for suggestion in merge_suggestions[:10]:
            try:
                self.merge_knowledge(
                    primary_id=suggestion.primary_id,
                    duplicate_ids=suggestion.duplicate_ids
                )
                merged_count += 1
            except Exception as e:
                logger.error(f"合并知识失败: {e}")
        
        reorganization_suggestions = self.similarity_analyzer.suggest_catalog_reorganization(
            max_items_per_catalog
        )
        
        split_results = []
        for suggestion in reorganization_suggestions[:5]:
            split_suggestion = self.analyze_catalog_for_split(
                suggestion["catalog_id"],
                max_items_per_catalog
            )
            if split_suggestion:
                split_results.append({
                    "catalog_id": split_suggestion.catalog_id,
                    "catalog_name": split_suggestion.catalog_name,
                    "current_count": split_suggestion.current_count,
                    "suggested_sub_catalogs": split_suggestion.suggested_sub_catalogs
                })
        
        return {
            "merged_knowledge_count": merged_count,
            "merge_suggestions_total": len(merge_suggestions),
            "split_suggestions": split_results,
            "organized_at": datetime.now().isoformat()
        }
    
    def get_organization_summary(self) -> Dict[str, Any]:
        all_knowledge = self.knowledge_store.get_all_knowledge()
        all_catalogs = self.catalog_manager.get_all_catalogs()
        
        catalog_distribution = self.similarity_analyzer.analyze_catalog_distribution()
        duplicates = self.similarity_analyzer.find_duplicates(threshold=0.90)
        
        uncategorized_count = sum(
            1 for item in all_knowledge if not item.catalog_id
        )
        
        return {
            "total_knowledge": len(all_knowledge),
            "total_catalogs": len(all_catalogs),
            "uncategorized_count": uncategorized_count,
            "duplicate_groups_count": len(duplicates),
            "catalog_distribution": catalog_distribution,
            "needs_organization": len(duplicates) > 0 or uncategorized_count > 0
        }
