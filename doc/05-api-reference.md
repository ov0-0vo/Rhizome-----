# 5. API 参考

## 5.1 QAAgent 类

Agent 核心类，提供所有问答和知识管理功能，支持流式输出。

### 5.1.1 初始化

```python
from knowledge_agent.agent.qa_agent import QAAgent
from knowledge_agent.knowledge.catalog_manager import CatalogManager
from knowledge_agent.knowledge.knowledge_store import KnowledgeStore

# 使用依赖注入
catalog_manager = CatalogManager()
knowledge_store = KnowledgeStore()
agent = QAAgent(
    catalog_manager=catalog_manager,
    knowledge_store=knowledge_store
)
```

### 5.1.2 chat(question: str) -> Dict[str, Any]

处理用户提问，返回回答和管理信息（非流式）。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question | str | 是 | 用户提问 |

**返回值：**

```python
{
    "answer": "回答内容...",
    "source": "generated",  # 或 "existing_knowledge"
    "knowledge_id": "uuid",
    "catalog_id": "uuid",
    "is_new": True
}
```

**示例：**

```python
result = agent.chat("什么是Python？")
print(result["answer"])
```

### 5.1.3 chat_with_stream(question: str) -> Tuple[Iterator[str], Dict[str, Any]]

流式处理用户提问，实时返回回答片段。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question | str | 是 | 用户提问 |

**返回值：**

```python
# 返回流式迭代器和元数据
stream_iter, metadata = agent.chat_with_stream("什么是机器学习？")

# 流式迭代器返回回答片段
for chunk in stream_iter:
    print(chunk, end="")

# 元数据包含目录信息
print(metadata["catalog_id"])
print(metadata["match_reason"])
```

### 5.1.4 analyze_question(question: str) -> Dict[str, Any]

分析问题，提取关键信息。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question | str | 是 | 待分析的问题 |

**返回值：**

```python
{
    "keywords": ["Python", "编程语言"],
    "domain": "编程",
    "concepts": ["解释型语言", "动态类型"],
    "suggested_category": "编程语言"
}
```

### 5.1.5 match_catalog(question: str) -> Tuple[str, str]

将问题匹配到知识目录。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question | str | 是 | 用户问题 |

**返回值：**

```python
("catalog-uuid", "关键词匹配")
```

如果没有匹配，返回 `(None, None)`。

### 5.1.6 retrieve_knowledge(question: str, catalog_id: str = None) -> List[Dict[str, Any]]

检索相关知识。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question | str | 是 | 检索查询 |
| catalog_id | str | 否 | 限定目录 ID |

**返回值：**

```python
[
    {
        "id": "item-001",
        "question": "Python 是什么？",
        "answer": "Python 是一种...",
        "similarity": 0.85
    }
]
```

### 5.1.7 generate_answer(question: str, context_knowledge: List = None) -> str

生成 AI 回答（非流式）。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question | str | 是 | 用户问题 |
| context_knowledge | List | 否 | 上下文知识 |

**返回值：**

回答文本字符串。

### 5.1.8 _generate_stream(question: str, context_knowledge: List = None) -> Iterator[str]

流式生成 AI 回答。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question | str | 是 | 用户问题 |
| context_knowledge | List | 否 | 上下文知识 |

**返回值：**

回答片段的迭代器。

### 5.1.9 get_knowledge_tree() -> Dict[str, Any]

获取知识目录树。

**返回值：**

```python
{
    "id": "root-001",
    "name": "知识体系",
    "knowledge_count": 10,
    "children": [
        {"id": "...", "name": "编程", "knowledge_count": 5, "children": [...]}
    ]
}
```

### 5.1.10 get_statistics() -> Dict[str, Any]

获取知识库统计。

**返回值：**

```python
{
    "total_knowledge": 100,
    "catalogs_count": 10,
    "today_count": 5,
    "week_count": 20,
    "month_count": 50,
    "latest_knowledge": [...],
    "catalog_distribution": [...],
    "top_keywords": [...]
}
```

### 5.1.11 search_knowledge(query: str) -> List[Dict[str, Any]]

搜索知识。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | str | 是 | 搜索关键词 |

**返回值：**

```python
[
    {
        "id": "item-001",
        "question": "...",
        "answer": "...",
        "keywords": [...],
        "similarity": 0.9,
        "created_at": "2024-01-01T00:00:00"
    }
]
```

## 5.2 CatalogManager 类

知识目录管理类。

### 5.2.1 get_all_catalogs() -> List[KnowledgeCatalog]

获取所有目录。

### 5.2.2 get_catalog(catalog_id: str) -> KnowledgeCatalog

获取指定目录。

### 5.2.3 create_catalog(name: str, keywords: List[str] = None, parent_id: str = None) -> KnowledgeCatalog

创建新目录。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | str | 是 | 目录名称 |
| keywords | List[str] | 否 | 关键词 |
| parent_id | str | 否 | 父目录 ID |

### 5.2.4 update_catalog(catalog_id: str, name: str = None, keywords: List[str] = None) -> KnowledgeCatalog

更新目录。

### 5.2.5 delete_catalog(catalog_id: str)

删除目录。

### 5.2.6 add_knowledge_to_catalog(catalog_id: str, knowledge_id: str)

将知识添加到目录。

### 5.2.7 match_catalog_by_keywords(keywords: List[str]) -> KnowledgeCatalog

通过关键词匹配目录。

### 5.2.8 get_catalog_tree(catalog_id: str = None) -> Dict[str, Any]

获取目录树。

### 5.2.9 get_all_descendant_ids(catalog_id: str) -> List[str]

获取所有后代目录 ID。

## 5.3 KnowledgeStore 类

知识存储管理类。

### 5.3.1 add_knowledge(question: str, answer: str, catalog_id: str = None, keywords: List[str] = None, sources: List[str] = None) -> KnowledgeItem

添加知识。

### 5.3.2 get_knowledge(knowledge_id: str) -> KnowledgeItem

获取知识。

### 5.3.3 get_all_knowledge() -> List[KnowledgeItem]

获取所有知识。

### 5.3.4 get_knowledge_by_catalog(catalog_id: str) -> List[KnowledgeItem]

获取目录下所有知识。

### 5.3.5 update_knowledge(knowledge_id: str, answer: str = None, keywords: List[str] = None, sources: List[str] = None, catalog_id: str = None) -> KnowledgeItem

更新知识。

### 5.3.6 delete_knowledge(knowledge_id: str)

删除知识。

### 5.3.7 search(query: str, n_results: int = 5, catalog_id: str = None) -> List[Dict[str, Any]]

搜索知识。

### 5.3.8 search_by_catalog_tree(query: str, catalog_ids: List[str], n_results: int = 5) -> List[Dict[str, Any]]

在目录树中搜索。

### 5.3.9 find_similar_question(question: str) -> KnowledgeItem

查找相似问题。

## 5.4 REST API 接口

### 5.4.1 对话接口

**POST /api/chat**

发送消息并获取回复（非流式）。

请求体：
```json
{
    "message": "什么是机器学习？"
}
```

响应：
```json
{
    "answer": "机器学习是...",
    "source": "generated",
    "knowledge_id": "uuid",
    "catalog_id": "uuid",
    "is_new": true
}
```

**POST /api/chat/stream**

流式对话（SSE）。

请求体：
```json
{
    "message": "什么是机器学习？"
}
```

响应（SSE 格式）：
```
data: {"type": "metadata", "data": {"catalog_id": "uuid", "match_reason": "..."}}

data: {"type": "chunk", "data": "机器"}

data: {"type": "chunk", "data": "学习"}

data: {"type": "done"}
```

**GET /api/chat/history**

获取对话历史。

响应：
```json
[
    {
        "id": "uuid",
        "question": "...",
        "answer": "...",
        "created_at": "2024-01-01T00:00:00"
    }
]
```

### 5.4.2 知识管理接口

**GET /api/knowledge**

获取所有知识。

**GET /api/knowledge/statistics**

获取统计数据（扩展版）。

响应：
```json
{
    "total_knowledge": 100,
    "catalogs_count": 10,
    "today_count": 5,
    "week_count": 20,
    "month_count": 50,
    "latest_knowledge": [
        {"id": "...", "question": "...", "created_at": "..."}
    ],
    "catalog_distribution": [
        {"catalog_id": "...", "catalog_name": "编程", "count": 30}
    ],
    "top_keywords": [
        {"keyword": "Python", "count": 20}
    ]
}
```

**GET /api/knowledge/search?query=xxx**

搜索知识。

**GET /api/knowledge/catalog/{catalog_id}**

获取目录下的知识。

**GET /api/knowledge/{id}**

获取单个知识详情。

**POST /api/knowledge**

创建知识。

请求体：
```json
{
    "question": "问题内容",
    "answer": "答案内容",
    "keywords": ["关键词1", "关键词2"],
    "catalog_id": "目录ID"
}
```

**PUT /api/knowledge/{id}**

更新知识。

请求体：
```json
{
    "question": "更新后的问题",
    "answer": "更新后的答案",
    "keywords": ["关键词1", "关键词2"],
    "catalog_id": "目录ID"
}
```

**DELETE /api/knowledge/{id}**

删除知识。

### 5.4.3 目录管理接口

**GET /api/catalog/tree**

获取目录树。

**GET /api/catalog**

获取所有目录。

**POST /api/catalog**

创建目录。

请求体：
```json
{
    "name": "新目录",
    "keywords": ["关键词1", "关键词2"],
    "parent_id": null
}
```

**PUT /api/catalog/{id}**

更新目录。

请求体：
```json
{
    "name": "更新后的目录名",
    "keywords": ["关键词1", "关键词2"]
}
```

**DELETE /api/catalog/{id}**

删除目录。

## 5.5 数据模型

### 5.5.1 KnowledgeCatalog

```python
class KnowledgeCatalog:
    id: str
    name: str
    keywords: List[str]
    parent_id: Optional[str]
    children: List[str]
    knowledge_items: List[str]
    created_at: str
    updated_at: str
```

### 5.5.2 KnowledgeItem

```python
class KnowledgeItem:
    id: str
    catalog_id: str
    question: str
    answer: str
    keywords: List[str]
    sources: List[str]
    confidence: float
    created_at: str
    updated_at: str
```

## 5.6 配置

### 5.6.1 Config

```python
from knowledge_agent.config import config

config.openai_api_key  # API 密钥
config.openai_model    # 模型名称
config.provider         # 供应商
config.embedding_provider  # 嵌入模型供应商
config.embedding_model     # 嵌入模型名称
```
