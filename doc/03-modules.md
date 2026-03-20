# 3. 核心模块详解

## 3.1 配置模块 (config.py)

配置模块负责管理所有运行时配置，支持环境变量和配置文件两种方式。

### 3.1.1 配置项

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|----------|--------|------|
| provider | `LLM_PROVIDER` | `openai` | LLM 供应商 |
| openai_api_key | `OPENAI_API_KEY` | `""` | API 密钥 |
| openai_api_base | `OPENAI_API_BASE` | `""` | API 基础 URL |
| openai_model | `OPENAI_MODEL` | `gpt-3.5-turbo` | 模型名称 |
| embedding_provider | `EMBEDDING_PROVIDER` | `local` | 嵌入模型供应商 |
| embedding_model | `EMBEDDING_MODEL` | `BAAI/bge-small-zh-v1.5` | 嵌入模型名称 |
| embedding_api_key | `EMBEDDING_API_KEY` | `""` | 嵌入 API 密钥 |
| embedding_api_base | `EMBEDDING_API_BASE` | `""` | 嵌入 API URL |
| max_tokens | - | `2000` | 最大 token 数 |
| temperature | - | `0.7` | 生成温度 |
| top_k | - | `5` | 检索返回数量 |

### 3.1.2 使用示例

```python
from knowledge_agent.config import config

# 访问配置
print(config.openai_model)  # gpt-3.5-turbo
print(config.provider)       # openai
```

## 3.2 Agent 模块 (agent/)

### 3.2.1 QAAgent 类

`QAAgent` 是系统的核心 orchestrator，整合所有功能模块。

#### 初始化

```python
from knowledge_agent.agent.qa_agent import QAAgent

agent = QAAgent()
```

初始化时会自动：

1. 根据配置创建 LLM 实例
2. 初始化 `CatalogManager`
3. 初始化 `KnowledgeStore`

#### 核心方法

**chat(question: str) -> Dict[str, Any]**

处理用户提问的主入口：

```python
result = agent.chat("什么是机器学习？")
print(result["answer"])           # AI 生成的回答
print(result["catalog_id"])      # 所属知识目录 ID
print(result["is_new"])           # 是否是新知识
```

**analyze_question(question: str) -> Dict[str, Any]**

分析问题，提取关键信息：

```python
analysis = agent.analyze_question("Python 中的列表和元组有什么区别？")
# 返回: {"keywords": [...], "domain": "编程", "concepts": [...], "suggested_category": "..."}
```

**match_catalog(question: str) -> Tuple[str, str]**

将问题匹配到知识目录：

```python
catalog_id, reason = agent.match_catalog("什么是深度学习？")
# 返回: (目录ID, 匹配原因)
```

**retrieve_knowledge(question: str, catalog_id: str = None) -> List[Dict]**

检索相关知识：

```python
# 在指定目录下检索
results = agent.retrieve_knowledge("神经网络", catalog_id="xxx")

# 全局检索
results = agent.retrieve_knowledge("神经网络")
```

**generate_answer(question: str, context_knowledge: List = None) -> str**

生成回答：

```python
answer = agent.generate_answer(
    question="什么是过拟合？",
    context_knowledge=[{"question": "...", "answer": "..."}]
)
```

### 3.2.2 提示词模板 (prompt_templates.py)

系统使用多个提示词模板：

| 模板 | 用途 |
|------|------|
| `QA_SYSTEM_PROMPT` | AI 角色设定 |
| `QUESTION_ANALYSIS_PROMPT` | 问题分析 |
| `KNOWLEDGE_SUMMARIZATION_PROMPT` | 知识摘要提取 |
| `CATALOG_MATCHING_PROMPT` | 目录匹配 |
| `ANSWER_WITH_CONTEXT_PROMPT` | 带上下文的回答生成 |

## 3.3 知识管理模块 (knowledge/)

### 3.3.1 CatalogManager 类

管理知识目录的创建、查询和更新。

#### 主要方法

**create_catalog(name: str, keywords: List[str], parent_id: str = None) -> KnowledgeCatalog**

创建新目录：

```python
catalog = catalog_manager.create_catalog(
    name="机器学习",
    keywords=["ML", "监督学习", "神经网络"],
    parent_id=None  # 根目录
)
```

**match_catalog_by_keywords(keywords: List[str]) -> KnowledgeCatalog**

通过关键词匹配目录：

```python
matched = catalog_manager.match_catalog_by_keywords(["Python", "编程"])
```

**get_catalog_tree(catalog_id: str = None) -> Dict[str, Any]**

获取目录树结构：

```python
tree = catalog_manager.get_catalog_tree()
# 返回树形结构数据
```

**get_all_descendant_ids(catalog_id: str) -> List[str]**

获取目录及其所有子目录 ID：

```python
all_ids = catalog_manager.get_all_descendant_ids("根目录ID")
```

### 3.3.2 KnowledgeStore 类

管理知识条目的存储和检索。

#### 主要方法

**add_knowledge(question, answer, catalog_id, keywords, sources) -> KnowledgeItem**

添加新知识：

```python
item = knowledge_store.add_knowledge(
    question="什么是梯度下降？",
    answer="梯度下降是一种优化算法...",
    catalog_id="ml-001",
    keywords=["优化", "梯度", "收敛"]
)
```

**search(query, n_results, catalog_id) -> List[Dict]**

搜索知识：

```python
results = knowledge_store.search(
    query="优化算法有哪些",
    n_results=5,
    catalog_id=None  # 可指定目录
)
```

**search_by_catalog_tree(query, catalog_ids, n_results) -> List[Dict]**

在目录树中搜索：

```python
results = knowledge_store.search_by_catalog_tree(
    query="神经网络",
    catalog_ids=["父目录ID", "子目录ID"]
)
```

**find_similar_question(question) -> KnowledgeItem**

查找相似问题：

```python
existing = knowledge_store.find_similar_question("什么是机器学习")
if existing:
    print(f"找到相似问题: {existing.question}")
```

## 3.4 存储模块 (storage/)

### 3.4.1 JSON Storage

基于 JSON 文件的轻量级存储。

**CatalogStorage** - 知识目录存储：

```python
from knowledge_agent.storage.json_storage import CatalogStorage

storage = CatalogStorage("data/catalog.json")
catalogs = storage.get_all_catalogs()
storage.add_catalog(catalog)
storage.update_catalog(catalog)
storage.delete_catalog(catalog_id)
```

**KnowledgeStorage** - 知识条目存储：

```python
from knowledge_agent.storage.json_storage import KnowledgeStorage

storage = KnowledgeStorage("data/knowledge.json")
items = storage.get_all_items()
items = storage.get_items_by_catalog(catalog_id)
storage.add_item(item)
storage.update_item(item)
```

### 3.4.2 Vector Store

基于 Chroma 的向量存储，支持 HuggingFace 本地嵌入模型。

```python
from knowledge_agent.storage.vector_store import VectorStoreManager

vector_store = VectorStoreManager(persist_directory="data/vector_store")

# 添加知识
vector_store.add_knowledge(
    knowledge_id="uuid",
    question="什么是过拟合？",
    answer="过拟合是...",
    catalog_id="ml-001"
)

# 检索
results = vector_store.search(
    query="过拟合",
    n_results=5,
    catalog_id="ml-001"
)
```

**嵌入模型优化**：

- **本地缓存**：HuggingFace 模型自动下载到 `~/.cache/huggingface/hub`
- **离线模式**：设置 `HF_HUB_OFFLINE=1`，避免每次初始化都检查远程
- **智能降级**：如本地无模型，自动尝试远程下载（首次运行时）

## 3.5 UI 模块 (ui/)

### 3.5.1 Gradio 应用

基于 Gradio 的 Web 用户界面：

```python
from knowledge_agent.ui.gradio_app import create_app

app = create_app()
app.launch(server_name="0.0.0.0", server_port=7860)
```

#### 界面功能

| Tab | 功能 |
|-----|------|
| 💬 对话 | 与 Agent 对话，查看回答 |
| 📚 知识目录 | 查看知识体系树状结构 |
| 📊 知识统计 | 查看知识库统计信息 |
| 🔍 知识搜索 | 搜索已有知识 |
