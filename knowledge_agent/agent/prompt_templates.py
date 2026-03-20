from langchain_core.prompts import PromptTemplate

QA_SYSTEM_PROMPT = """你是一个知识体系助手，帮助用户建立和管理个人知识体系。

你的职责：
1. 回答用户的问题，提供准确、有用的信息
2. 在回答过程中，识别问题所属的知识领域
3. 提取问题中的关键概念和关键词
4. 建议如何将新知识整合到知识体系中

请用清晰、易懂的方式回答问题。"""

QUESTION_ANALYSIS_PROMPT = PromptTemplate(
    template="""分析以下问题，提取关键信息：

问题：{question}

请返回以下格式的JSON：
{{
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "domain": "知识领域（如：编程、物理、历史等）",
    "concepts": ["核心概念1", "核心概念2"],
    "suggested_category": "建议的知识分类"
}}

只返回JSON，不要其他内容。""",
    input_variables=["question"]
)

KNOWLEDGE_SUMMARIZATION_PROMPT = PromptTemplate(
    template="""基于以下对话历史和新的问答，生成知识摘要：

问题：{question}
回答：{answer}

请返回以下格式的JSON：
{{
    "summary": "知识摘要（50字以内）",
    "keywords": ["关键词1", "关键词2"],
    "related_topics": ["相关主题1", "相关主题2"]
}}

只返回JSON，不要其他内容。""",
    input_variables=["question", "answer"]
)

CATALOG_MATCHING_PROMPT = PromptTemplate(
    template="""判断以下问题应该属于哪个知识目录：

问题：{question}

已有目录：
{catalogs}

请返回以下格式的JSON：
{{
    "matched_catalog_id": "匹配的目录ID，如果没有匹配则为null",
    "new_category_suggestion": "如果需要新目录，建议的目录名称",
    "reason": "匹配原因"
}}

只返回JSON，不要其他内容。""",
    input_variables=["question", "catalogs"]
)

ANSWER_WITH_CONTEXT_PROMPT = PromptTemplate(
    template=""""基于以下相关知识回答用户问题。

相关知识：
{context}

用户问题：{question}

请根据相关知识回答问题。如果相关知识不能完全回答问题，请基于你的知识回答，但要说明这一点。""",
    input_variables=["context", "question"]
)
