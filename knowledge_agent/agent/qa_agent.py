import json
import threading
import re
import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Iterator
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama
from langchain_core.runnables import RunnableSequence
from langchain_core.messages import HumanMessage

from .prompt_templates import (
    QUESTION_ANALYSIS_PROMPT,
    KNOWLEDGE_SUMMARIZATION_PROMPT,
    CATALOG_MATCHING_PROMPT,
    ANSWER_WITH_CONTEXT_PROMPT,
    QA_SYSTEM_PROMPT,
    FAST_ANALYSIS_AND_MATCH_PROMPT
)
from ..knowledge.catalog_manager import CatalogManager
from ..knowledge.knowledge_store import KnowledgeStore
from ..knowledge.models import KnowledgeItem
from ..config import config

logger = logging.getLogger(__name__)


def create_llm(streaming: bool = True):
    provider = config.provider.lower()

    common_kwargs = {
        "model": config.openai_model,
        "api_key": config.openai_api_key,
        "base_url": config.openai_api_base if config.openai_api_base else None,
        "max_tokens": config.max_tokens,
        "temperature": config.temperature,
        "streaming": streaming
    }

    if provider == "openai":
        return ChatOpenAI(**common_kwargs)
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
            temperature=config.temperature,
            streaming=streaming
        )
    else:
        return ChatOpenAI(**common_kwargs)


def create_chain(prompt, llm) -> RunnableSequence:
    return prompt | llm


def _extract_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text.strip())
    except:
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        return {}


class QAAgent:
    def __init__(
        self,
        catalog_manager: CatalogManager = None,
        knowledge_store: KnowledgeStore = None
    ):
        self.llm = create_llm(streaming=True)
        self.llm_non_streaming = create_llm(streaming=False)
        self.catalog_manager = catalog_manager or CatalogManager()
        self.knowledge_store = knowledge_store or KnowledgeStore()
        
        self._fast_analysis_chain = create_chain(FAST_ANALYSIS_AND_MATCH_PROMPT, self.llm_non_streaming)
        self._knowledge_summarization_chain = create_chain(KNOWLEDGE_SUMMARIZATION_PROMPT, self.llm_non_streaming)
        self._answer_with_context_chain = create_chain(ANSWER_WITH_CONTEXT_PROMPT, self.llm_non_streaming)
        self._answer_with_context_chain_streaming = create_chain(ANSWER_WITH_CONTEXT_PROMPT, self.llm)
        
        self._catalogs_cache = None
        self._catalogs_cache_time = 0

    def _get_catalogs_summary_cached(self) -> List[Dict[str, Any]]:
        import time
        current_time = time.time()
        if self._catalogs_cache is None or (current_time - self._catalogs_cache_time) > 30:
            self._catalogs_cache = self.catalog_manager.get_catalogs_summary()
            self._catalogs_cache_time = current_time
        return self._catalogs_cache

    def _match_catalog_fast(self, keywords: List[str]) -> Optional[str]:
        matched = self.catalog_manager.match_catalog_by_keywords(keywords)
        return matched.id if matched else None

    def _fast_analyze_and_match(self, question: str) -> Tuple[str, List[str], str]:
        start_time = time.time()
        logger.info(f"[PERF] _fast_analyze_and_match 开始, 问题: {question[:50]}...")
        
        catalogs = self._get_catalogs_summary_cached()
        logger.info(f"[PERF] 获取目录缓存耗时: {time.time() - start_time:.3f}s")
        
        if not catalogs:
            domain = "general"
            keywords = self._extract_keywords_simple(question)
            catalog_name = self._get_catalog_name_from_domain(domain)
            new_catalog = self.catalog_manager.create_catalog(
                name=catalog_name,
                keywords=keywords
            )
            logger.info(f"[PERF] _fast_analyze_and_match 完成(首个目录), 总耗时: {time.time() - start_time:.3f}s")
            return new_catalog.id, keywords, "首个目录"

        matched_id = self._match_catalog_fast(self._extract_keywords_simple(question))
        if matched_id:
            logger.info(f"[PERF] _fast_analyze_and_match 完成(快速匹配), 总耗时: {time.time() - start_time:.3f}s")
            return matched_id, [], "关键词快速匹配"

        catalogs_text = "\n".join([
            f"- ID: {c['id']}, 名称: {c['name']}, 关键词: {', '.join(c['keywords'][:5])}"
            for c in catalogs[:10]
        ])

        try:
            llm_start = time.time()
            result = self._fast_analysis_chain.invoke(
                {"question": question, "catalogs": catalogs_text}
            ).content.strip()
            logger.info(f"[PERF] LLM 目录匹配调用耗时: {time.time() - llm_start:.3f}s")
            
            analysis = _extract_json(result)
            
            keywords = analysis.get("keywords", [])
            matched_id = analysis.get("matched_catalog_id")
            
            if matched_id:
                logger.info(f"[PERF] _fast_analyze_and_match 完成(智能匹配), 总耗时: {time.time() - start_time:.3f}s")
                return matched_id, keywords, "智能匹配"
            
            if analysis.get("new_category_suggestion"):
                new_catalog = self.catalog_manager.create_catalog(
                    name=analysis["new_category_suggestion"],
                    keywords=keywords
                )
                logger.info(f"[PERF] _fast_analyze_and_match 完成(新目录), 总耗时: {time.time() - start_time:.3f}s")
                return new_catalog.id, keywords, "新创建的目录"
                
        except Exception as e:
            logger.warning(f"[PERF] LLM 目录匹配异常: {e}")

        keywords = self._extract_keywords_simple(question)
        domain = analysis.get("domain", "general") if 'analysis' in dir() else "general"
        catalog_name = self._get_catalog_name_from_domain(domain)
        new_catalog = self.catalog_manager.create_catalog(
            name=catalog_name,
            keywords=keywords
        )
        logger.info(f"[PERF] _fast_analyze_and_match 完成(默认目录), 总耗时: {time.time() - start_time:.3f}s")
        return new_catalog.id, keywords, "默认目录"

    def _extract_keywords_simple(self, question: str) -> List[str]:
        stop_words = {'的', '是', '在', '有', '和', '了', '我', '你', '他', '她', '它', '这', '那', '什么', '怎么', '如何', '为什么', '吗', '呢', '啊', '吧'}
        words = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', question)
        keywords = [w for w in words if w not in stop_words and len(w) > 1]
        return keywords[:5]

    def _get_catalog_name_from_domain(self, domain: str) -> str:
        domain_names = {
            "programming": "编程开发",
            "technology": "科技",
            "science": "科学",
            "mathematics": "数学",
            "history": "历史",
            "literature": "文学",
            "art": "艺术",
            "music": "音乐",
            "sports": "体育",
            "health": "健康",
            "business": "商业",
            "finance": "金融",
            "psychology": "心理学",
            "philosophy": "哲学",
            "education": "教育",
            "travel": "旅行",
            "food": "美食",
            "general": "通用知识"
        }
        return domain_names.get(domain.lower(), domain)

    def retrieve_knowledge(
        self,
        question: str,
        catalog_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        start_time = time.time()
        logger.info(f"[PERF] retrieve_knowledge 开始, catalog_id: {catalog_id}")
        
        if catalog_id:
            all_catalog_ids = self.catalog_manager.get_all_descendant_ids(catalog_id)
            result = self.knowledge_store.search_by_catalog_tree(question, all_catalog_ids)
        else:
            result = self.knowledge_store.search(question, n_results=config.top_k)
        
        logger.info(f"[PERF] retrieve_knowledge 完成, 找到 {len(result)} 条, 耗时: {time.time() - start_time:.3f}s")
        return result

    def _stream_answer(self, chain, prompt_input: Dict) -> Iterator[str]:
        for chunk in chain.stream(prompt_input):
            if chunk.content:
                yield chunk.content

    def _stream_llm_response(self, llm, messages: List) -> Iterator[str]:
        for chunk in llm.stream(messages):
            if chunk.content:
                yield chunk.content

    def extract_knowledge_metadata(
        self,
        question: str,
        answer: str
    ) -> Dict[str, Any]:
        try:
            result = self._knowledge_summarization_chain.invoke(
                {"question": question, "answer": answer}
            ).content.strip()
            return _extract_json(result)
        except:
            return {
                "summary": answer[:100],
                "keywords": [],
                "related_topics": []
            }

    def chat(self, question: str) -> Dict[str, Any]:
        catalog_id, keywords, match_reason = self._fast_analyze_and_match(question)
        context_knowledge = self.retrieve_knowledge(question, catalog_id)
        answer = self.generate_answer(question, context_knowledge, stream=False)

        threading.Thread(
            target=self._background_store,
            args=(question, answer, catalog_id, match_reason, keywords),
            daemon=True
        ).start()

        return {
            "answer": answer,
            "source": "generated",
            "catalog_id": catalog_id,
            "match_reason": match_reason,
            "is_new": True
        }

    def generate_answer(
        self,
        question: str,
        context_knowledge: List[Dict[str, Any]] = None,
        stream: bool = False
    ) -> str:
        if context_knowledge:
            context = "\n\n".join([
                f"【相关知识 {i+1}】\n问题: {k['question']}\n答案: {k['answer']}"
                for i, k in enumerate(context_knowledge)
            ])

            prompt_input = {"context": context, "question": question}
            return self._answer_with_context_chain.invoke(prompt_input).content
        else:
            messages = [
                HumanMessage(content=QA_SYSTEM_PROMPT),
                HumanMessage(content=question)
            ]
            return self.llm_non_streaming.invoke(messages).content

    def chat_with_stream(self, question: str) -> Tuple[Iterator[str], Dict[str, Any]]:
        total_start = time.time()
        logger.info(f"[PERF] ========== chat_with_stream 开始 ==========")
        logger.info(f"[PERF] 问题: {question[:100]}...")
        
        step_start = time.time()
        catalog_id, keywords, match_reason = self._fast_analyze_and_match(question)
        logger.info(f"[PERF] 步骤1-目录匹配完成, 耗时: {time.time() - step_start:.3f}s, 匹配结果: {match_reason}")
        
        step_start = time.time()
        context_knowledge = self.retrieve_knowledge(question, catalog_id)
        logger.info(f"[PERF] 步骤2-知识检索完成, 耗时: {time.time() - step_start:.3f}s")

        metadata = {
            "catalog_id": catalog_id,
            "match_reason": match_reason,
            "is_new": True
        }

        def answer_stream():
            full_answer = ""
            stream_start = time.time()
            logger.info(f"[PERF] 步骤3-开始LLM流式生成答案...")
            first_chunk = True
            stream_iter = self._generate_stream(question, context_knowledge)
            for chunk in stream_iter:
                if first_chunk:
                    logger.info(f"[PERF] 首个chunk到达, 延迟: {time.time() - stream_start:.3f}s")
                    first_chunk = False
                full_answer += chunk
                yield chunk
            
            logger.info(f"[PERF] 步骤3-LLM流式生成完成, 总耗时: {time.time() - stream_start:.3f}s, 答案长度: {len(full_answer)}")
            logger.info(f"[PERF] ========== chat_with_stream 总耗时: {time.time() - total_start:.3f}s ==========")

            threading.Thread(
                target=self._background_store,
                args=(question, full_answer, catalog_id, match_reason, keywords),
                daemon=True
            ).start()

        return answer_stream(), metadata

    def _generate_stream(self, question: str, context_knowledge: List[Dict[str, Any]] = None) -> Iterator[str]:
        if context_knowledge:
            context = "\n\n".join([
                f"【相关知识 {i+1}】\n问题: {k['question']}\n答案: {k['answer']}"
                for i, k in enumerate(context_knowledge)
            ])
            prompt_input = {"context": context, "question": question}
            for chunk in self._stream_answer(self._answer_with_context_chain_streaming, prompt_input):
                yield chunk
        else:
            messages = [
                HumanMessage(content=QA_SYSTEM_PROMPT),
                HumanMessage(content=question)
            ]
            for chunk in self._stream_llm_response(self.llm, messages):
                yield chunk

    def _background_store(
        self,
        question: str,
        answer: str,
        catalog_id: Optional[str],
        match_reason: Optional[str],
        keywords: List[str]
    ):
        try:
            knowledge_metadata = self.extract_knowledge_metadata(question, answer)
            all_keywords = list(set(keywords + knowledge_metadata.get("keywords", [])))

            knowledge_item = self.knowledge_store.add_knowledge(
                question=question,
                answer=answer,
                catalog_id=catalog_id,
                keywords=all_keywords
            )

            if catalog_id:
                self.catalog_manager.add_knowledge_to_catalog(catalog_id, knowledge_item.id)
        except Exception as e:
            print(f"Background store error: {e}")

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
