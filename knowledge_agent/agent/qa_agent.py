import json
import threading
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
    QA_SYSTEM_PROMPT
)
from ..knowledge.catalog_manager import CatalogManager
from ..knowledge.knowledge_store import KnowledgeStore
from ..knowledge.models import KnowledgeItem
from ..config import config


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
        self._question_analysis_chain = create_chain(QUESTION_ANALYSIS_PROMPT, self.llm_non_streaming)
        self._catalog_matching_chain = create_chain(CATALOG_MATCHING_PROMPT, self.llm_non_streaming)
        self._knowledge_summarization_chain = create_chain(KNOWLEDGE_SUMMARIZATION_PROMPT, self.llm_non_streaming)
        self._answer_with_context_chain = create_chain(ANSWER_WITH_CONTEXT_PROMPT, self.llm_non_streaming)

    def analyze_question(self, question: str) -> Dict[str, Any]:
        try:
            result = self._question_analysis_chain.invoke({"question": question}).content.strip()
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
            analysis = self.analyze_question(question)
            domain = analysis.get("domain", "general")
            keywords = analysis.get("keywords", [])
            
            if domain and domain != "unknown":
                catalog_name = self._get_catalog_name_from_domain(domain)
            else:
                catalog_name = "通用知识"
            
            new_catalog = self.catalog_manager.create_catalog(
                name=catalog_name,
                keywords=keywords
            )
            return new_catalog.id, "首个目录"

        catalogs_text = "\n".join([
            f"- ID: {c['id']}, 名称: {c['name']}, 关键词: {', '.join(c['keywords'])}"
            for c in catalogs
        ])

        try:
            result = self._catalog_matching_chain.invoke(
                {"question": question, "catalogs": catalogs_text}
            ).content.strip()
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
        if catalog_id:
            all_catalog_ids = self.catalog_manager.get_all_descendant_ids(catalog_id)
            return self.knowledge_store.search_by_catalog_tree(question, all_catalog_ids)

        return self.knowledge_store.search(question, n_results=config.top_k)

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

    def _stream_answer(self, chain, prompt_input: Dict) -> Iterator[str]:
        for chunk in chain.stream(prompt_input):
            if chunk.content:
                yield chunk.content

    def _stream_llm_response(self, llm, messages: List) -> Iterator[str]:
        for chunk in llm.stream(messages):
            if chunk.content:
                yield chunk.content

    def _collect_stream(self, stream_iter: Iterator[str]) -> str:
        full_response = ""
        for chunk in stream_iter:
            full_response += chunk
        return full_response

    def extract_knowledge_metadata(
        self,
        question: str,
        answer: str
    ) -> Dict[str, Any]:
        try:
            result = self._knowledge_summarization_chain.invoke(
                {"question": question, "answer": answer}
            ).content.strip()
            return json.loads(result)
        except:
            return {
                "summary": answer[:100],
                "keywords": [],
                "related_topics": []
            }

    def chat(self, question: str) -> Dict[str, Any]:
        analysis = self.analyze_question(question)
        catalog_id, match_reason = self.match_catalog(question)
        context_knowledge = self.retrieve_knowledge(question, catalog_id)
        answer = self.generate_answer(question, context_knowledge, stream=False)

        threading.Thread(
            target=self._background_store,
            args=(question, answer, catalog_id, match_reason, analysis),
            daemon=True
        ).start()

        return {
            "answer": answer,
            "source": "generated",
            "catalog_id": catalog_id,
            "match_reason": match_reason,
            "analysis": analysis,
            "is_new": True
        }

    def chat_with_stream(self, question: str) -> Tuple[Iterator[str], Dict[str, Any]]:
        analysis = self.analyze_question(question)
        catalog_id, match_reason = self.match_catalog(question)
        context_knowledge = self.retrieve_knowledge(question, catalog_id)

        metadata = {
            "catalog_id": catalog_id,
            "match_reason": match_reason,
            "analysis": analysis,
            "is_new": True
        }

        def answer_stream():
            full_answer = ""
            stream_iter = self._generate_stream(question, context_knowledge)
            for chunk in stream_iter:
                full_answer += chunk
                yield chunk

            threading.Thread(
                target=self._background_store,
                args=(question, full_answer, catalog_id, match_reason, analysis),
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
            for chunk in self._stream_answer(self._answer_with_context_chain, prompt_input):
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
        analysis: Dict[str, Any]
    ):
        try:
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


# if __name__ == "__main__":
#     print("=" * 50)
#     print("QAAgent 对话功能测试")
#     print("=" * 50)
    
#     print(f"\n配置信息:")
#     print(f"  Provider: {config.provider}")
#     print(f"  Model: {config.openai_model}")
#     print(f"  API Base: {config.openai_api_base}")
    
#     print("\n正在初始化 QAAgent...")
#     try:
#         agent = QAAgent()
#         print("QAAgent 初始化成功!")
#     except Exception as e:
#         print(f"QAAgent 初始化失败: {e}")
#         exit(1)
    
#     test_questions = [
#         "你好，请介绍一下你自己",
#         "什么是 Python？",
#     ]
    
#     for i, question in enumerate(test_questions, 1):
#         print(f"\n{'='*50}")
#         print(f"测试 {i}: {question}")
#         print("-" * 50)
#         try:
#             result = agent.chat(question)
#             print(f"回答: {result['answer'][:200]}..." if len(result['answer']) > 200 else f"回答: {result['answer']}")
#             print(f"来源: {result['source']}")
#             print(f"是否新知识: {result['is_new']}")
#         except Exception as e:
#             print(f"测试失败: {e}")
    
#     print("\n" + "=" * 50)
#     print("测试完成!")
#     print("=" * 50)
