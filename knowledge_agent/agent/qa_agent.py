import json
from typing import List, Dict, Any, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama
from langchain.chains import LLMChain
from langchain.schema import HumanMessage

from .prompt_templates import (
    QUESTION_ANALYSIS_PROMPT,
    KNOWLEDGE_SUMMARIZATION_PROMPT,
    CATALOG_MATCHING_PROMPT,
    ANSWER_WITH_CONTEXT_PROMPT,
    QA_SYSTEM_PROMPT
)
from ..knowledge.catalog_manager import CatalogManager
from ..knowledge.knowledge_store import KnowledgeStore
from ..knowledge.models import KnowledgeItem
from ..config import config


def create_llm():
    provider = config.provider.lower()
    
    if provider == "openai":
        return ChatOpenAI(
            model=config.openai_model,
            api_key=config.openai_api_key,
            base_url=config.openai_api_base if config.openai_api_base else None,
            max_tokens=config.max_tokens,
            temperature=config.temperature
        )
    elif provider == "anthropic":
        return ChatAnthropic(
            model=config.openai_model,
            api_key=config.openai_api_key,
            max_tokens_to_sample=config.max_tokens
        )
    elif provider == "ollama":
        return ChatOllama(
            model=config.openai_model,
            base_url=config.openai_api_base if config.openai_api_base else "http://localhost:11434"
        )
    elif provider == "azure":
        return ChatOpenAI(
            model=config.openai_model,
            api_key=config.openai_api_key,
            base_url=config.openai_api_base,
            api_version="2024-02-01",
            max_tokens=config.max_tokens,
            temperature=config.temperature
        )
    else:
        return ChatOpenAI(
            model=config.openai_model,
            api_key=config.openai_api_key,
            base_url=config.openai_api_base if config.openai_api_base else None,
            max_tokens=config.max_tokens,
            temperature=config.temperature
        )


class QAAgent:
    def __init__(self):
        self.llm = create_llm()
        self.catalog_manager = CatalogManager()
        self.knowledge_store = KnowledgeStore()

    def analyze_question(self, question: str) -> Dict[str, Any]:
        chain = LLMChain(llm=self.llm, prompt=QUESTION_ANALYSIS_PROMPT)
        try:
            result = chain.run(question=question).strip()
            return json.loads(result)
        except:
            return {
                "keywords": [],
                "domain": "unknown",
                "concepts": [],
                "suggested_category": None
            }

    def match_catalog(self, question: str) -> Tuple[Optional[str], Optional[str]]:
        catalogs = self.catalog_manager.get_catalogs_summary()
        
        if not catalogs:
            return None, None
        
        catalogs_text = "\n".join([
            f"- ID: {c['id']}, 名称: {c['name']}, 关键词: {', '.join(c['keywords'])}"
            for c in catalogs
        ])
        
        chain = LLMChain(llm=self.llm, prompt=CATALOG_MATCHING_PROMPT)
        try:
            result = chain.run(question=question, catalogs=catalogs_text).strip()
            match_result = json.loads(result)
            
            if match_result.get("matched_catalog_id"):
                return match_result["matched_catalog_id"], match_result.get("reason")
            
            if match_result.get("new_category_suggestion"):
                new_catalog = self.catalog_manager.create_catalog(
                    name=match_result["new_category_suggestion"],
                    keywords=match_result.get("keywords", [])
                )
                return new_catalog.id, "新创建的目录"
            
        except:
            pass
        
        matched = self.catalog_manager.match_catalog_by_keywords(
            self.analyze_question(question).get("keywords", [])
        )
        if matched:
            return matched.id, "关键词匹配"
        
        return None, None

    def retrieve_knowledge(
        self,
        question: str,
        catalog_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if catalog_id:
            all_catalog_ids = self.catalog_manager.get_all_descendant_ids(catalog_id)
            return self.knowledge_store.search_by_catalog_tree(question, all_catalog_ids)
        
        return self.knowledge_store.search(question, n_results=config.top_k)

    def generate_answer(
        self,
        question: str,
        context_knowledge: List[Dict[str, Any]] = None
    ) -> str:
        if context_knowledge:
            context = "\n\n".join([
                f"【相关知识 {i+1}】\n问题: {k['question']}\n答案: {k['answer']}"
                for i, k in enumerate(context_knowledge)
            ])
            
            chain = LLMChain(llm=self.llm, prompt=ANSWER_WITH_CONTEXT_PROMPT)
            answer = chain.run(context=context, question=question)
        else:
            messages = [
                {"role": "system", "content": QA_SYSTEM_PROMPT},
                {"role": "user", "content": question}
            ]
            response = self.llm(messages)
            answer = response.content
        
        return answer.strip()

    def extract_knowledge_metadata(
        self,
        question: str,
        answer: str
    ) -> Dict[str, Any]:
        chain = LLMChain(llm=self.llm, prompt=KNOWLEDGE_SUMMARIZATION_PROMPT)
        try:
            result = chain.run(question=question, answer=answer).strip()
            return json.loads(result)
        except:
            return {
                "summary": answer[:100],
                "keywords": [],
                "related_topics": []
            }

    def chat(self, question: str) -> Dict[str, Any]:
        similar = self.knowledge_store.find_similar_question(question)
        if similar:
            return {
                "answer": similar.answer,
                "source": "existing_knowledge",
                "knowledge_id": similar.id,
                "catalog_id": similar.catalog_id,
                "is_new": False
            }
        
        analysis = self.analyze_question(question)
        
        catalog_id, match_reason = self.match_catalog(question)
        
        context_knowledge = self.retrieve_knowledge(question, catalog_id)
        
        answer = self.generate_answer(question, context_knowledge)
        
        knowledge_metadata = self.extract_knowledge_metadata(question, answer)
        
        keywords = list(set(analysis.get("keywords", []) + knowledge_metadata.get("keywords", [])))
        
        knowledge_item = self.knowledge_store.add_knowledge(
            question=question,
            answer=answer,
            catalog_id=catalog_id,
            keywords=keywords
        )
        
        if catalog_id:
            self.catalog_manager.add_knowledge_to_catalog(catalog_id, knowledge_item.id)
        
        return {
            "answer": answer,
            "source": "generated",
            "knowledge_id": knowledge_item.id,
            "catalog_id": catalog_id,
            "match_reason": match_reason,
            "analysis": analysis,
            "metadata": knowledge_metadata,
            "is_new": True
        }

    def get_knowledge_tree(self) -> Dict[str, Any]:
        return self.catalog_manager.get_catalog_tree()

    def get_statistics(self) -> Dict[str, Any]:
        return self.knowledge_store.get_statistics()

    def get_all_knowledge(self) -> List[KnowledgeItem]:
        return self.knowledge_store.get_all_knowledge()

    def search_knowledge(self, query: str) -> List[Dict[str, Any]]:
        return self.knowledge_store.search(query)

    def update_knowledge(
        self,
        knowledge_id: str,
        answer: str
    ) -> Optional[KnowledgeItem]:
        return self.knowledge_store.update_knowledge(knowledge_id, answer=answer)

    def delete_knowledge(self, knowledge_id: str):
        item = self.knowledge_store.get_knowledge(knowledge_id)
        if item and item.catalog_id:
            self.catalog_manager.remove_knowledge_from_catalog(
                item.catalog_id, knowledge_id
            )
        self.knowledge_store.delete_knowledge(knowledge_id)
