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

`QAAgent` 是系统的核心 orchestrator，整合所有功能模块，支持流式输出和依赖注入。

#### 初始化

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

初始化时会自动：

1. 创建流式和非流式两个 LLM 实例
2. 使用注入的 CatalogManager 和 KnowledgeStore
3. 初始化各种处理链

#### 核心方法

**chat(question: str) -> Dict[str, Any]**

处理用户提问的主入口（非流式）：

```python
result = agent.chat("什么是机器学习？")
print(result["answer"])           # AI 生成的回答
print(result["catalog_id"])      # 所属知识目录 ID
print(result["is_new"])           # 是否是新知识
```

**chat_with_stream(question: str) -> Tuple[Iterator[str], Dict[str, Any]]**

流式处理用户提问：

```python
stream_iter, metadata = agent.chat_with_stream("什么是机器学习？")

for chunk in stream_iter:
    print(chunk, end="", flush=True)  # 实时输出

print(metadata["catalog_id"])  # 目录 ID
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

生成回答（非流式）：

```python
answer = agent.generate_answer(
    question="什么是过拟合？",
    context_knowledge=[{"question": "...", "answer": "..."}]
)
```

**_generate_stream(question: str, context_knowledge: List = None) -> Iterator[str]**

流式生成回答：

```python
for chunk in agent._generate_stream(question, context):
    yield chunk
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

**get_knowledge_by_catalog(catalog_id: str) -> List[KnowledgeItem]**

获取目录下所有知识：

```python
items = knowledge_store.get_knowledge_by_catalog("catalog-001")
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

## 3.5 后端模块 (backend/)

### 3.5.1 FastAPI 应用

基于 FastAPI 的 RESTful API 服务：

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Rhizome API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.routes import chat, knowledge, catalog

app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge"])
app.include_router(catalog.router, prefix="/api/catalog", tags=["catalog"])
```

### 3.5.2 依赖注入

使用 FastAPI 的依赖注入管理状态：

```python
from knowledge_agent.agent.qa_agent import QAAgent
from knowledge_agent.knowledge.catalog_manager import CatalogManager
from knowledge_agent.knowledge.knowledge_store import KnowledgeStore

class AppState:
    qa_agent: QAAgent = None
    catalog_manager: CatalogManager = None
    knowledge_store: KnowledgeStore = None

state = AppState()

def get_state():
    if state.qa_agent is None:
        state.catalog_manager = CatalogManager()
        state.knowledge_store = KnowledgeStore()
        state.qa_agent = QAAgent(
            catalog_manager=state.catalog_manager,
            knowledge_store=state.knowledge_store
        )
    return state
```

### 3.5.3 SSE 流式接口

使用 Server-Sent Events 实现流式响应：

```python
from fastapi.responses import StreamingResponse
import json

@router.post("/stream")
async def chat_stream(request: ChatRequest):
    current_state = get_state()
    stream_iter, metadata = current_state.qa_agent.chat_with_stream(request.message)
    
    async def event_generator():
        for chunk in stream_iter:
            data = {"type": "chunk", "content": chunk}
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
        
        final_data = {
            "type": "done",
            "metadata": {
                "catalog_id": metadata.get("catalog_id"),
                "is_new": metadata.get("is_new", True)
            }
        }
        yield f"data: {json.dumps(final_data, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )
```

### 3.5.4 API 路由模块

**chat.py** - 对话接口：
- `POST /api/chat` - 普通对话
- `POST /api/chat/stream` - 流式对话（SSE）
- `GET /api/chat/history` - 获取对话历史

**knowledge.py** - 知识管理接口：
- `GET /api/knowledge` - 获取所有知识
- `GET /api/knowledge/statistics` - 获取统计数据
- `GET /api/knowledge/search` - 搜索知识
- `GET /api/knowledge/{id}` - 获取单个知识
- `POST /api/knowledge` - 创建知识
- `PUT /api/knowledge/{id}` - 更新知识
- `DELETE /api/knowledge/{id}` - 删除知识

**catalog.py** - 目录管理接口：
- `GET /api/catalog/tree` - 获取目录树
- `GET /api/catalog` - 获取所有目录
- `POST /api/catalog` - 创建目录
- `PUT /api/catalog/{id}` - 更新目录
- `DELETE /api/catalog/{id}` - 删除目录

**graph.py** - 知识图谱接口：
- `GET /api/graph` - 获取完整知识图谱
- `GET /api/graph/keywords` - 获取关键词网络图谱
- `GET /api/graph/catalog/{catalog_id}` - 获取指定目录的知识图谱

图谱数据模型：
```python
class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # catalog, knowledge, keyword
    size: int = 10
    catalog_id: Optional[str] = None

class GraphEdge(BaseModel):
    source: str
    target: str
    type: str  # parent-child, contains, has-keyword
    weight: float = 1.0

class KnowledgeGraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class KeywordNetwork(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
```

## 3.6 前端模块 (frontend/)

### 3.6.1 Vue 3 应用

基于 Vue 3 + Vite 的单页应用：

```javascript
// frontend/src/main.js
import { createApp } from 'vue'
import App from './App.vue'

createApp(App).mount('#app')
```

### 3.6.2 API 封装

统一的 API 调用封装：

```javascript
// frontend/src/api.js
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api'
})

export const chatApi = {
  send: (message) => api.post('/chat', { message }),
  stream: async function* (message) {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      body: JSON.stringify({ message })
    })
    // SSE 处理...
  },
  getHistory: () => api.get('/chat/history')
}

export const knowledgeApi = {
  getAll: () => api.get('/knowledge'),
  search: (query) => api.get('/knowledge/search', { params: { query } }),
  getByCatalog: (catalogId) => api.get(`/knowledge/catalog/${catalogId}`),
  getStatistics: () => api.get('/knowledge/statistics')
}
```

### 3.6.3 Markdown 渲染

使用 marked 库渲染 Markdown：

```vue
<script setup>
import { marked } from 'marked'

const formatMarkdown = (text) => {
  if (!text) return ''
  return marked(text)
}
</script>

<template>
  <div class="markdown-content" v-html="formatMarkdown(answer)"></div>
</template>
```

### 3.6.4 页面组件

| 组件 | 功能 |
|------|------|
| `ChatView.vue` | 对话页面，流式输出，历史记录 |
| `CatalogView.vue` | 知识目录树，点击查看详情 |
| `SearchView.vue` | 知识搜索，相似度排序 |
| `StatsView.vue` | 统计数据，可视化图表 |
| `GraphView.vue` | 知识图谱可视化，Canvas 绑定交互 |
| `TreeNode.vue` | 目录树节点组件，Markdown 渲染 |

### 3.6.5 知识图谱可视化

`GraphView.vue` 提供知识图谱的可视化展示：

**功能特性**：
- **多视图模式**：完整图谱 / 关键词网络
- **Canvas 渲染**：高性能图形绘制
- **交互操作**：
  - 拖拽节点
  - 缩放视图
  - 点击查看节点详情
- **力导向布局**：自动排列节点位置
- **节点类型区分**：
  - 目录节点（蓝色）
  - 知识节点（绿色）
  - 关键词节点（橙色）

**核心实现**：
```javascript
// 视图模式切换
const viewMode = ref('full')  // 'full' 或 'keywords'

// 加载图谱数据
const loadGraph = async () => {
    const url = viewMode.value === 'full' 
        ? '/api/graph' 
        : '/api/graph/keywords?limit=50'
    const response = await fetch(url)
    graphData.value = await response.json()
    initGraph()
}

// 力导向布局模拟
const simulateForces = () => {
    // 节点斥力
    // 边的引力
    // 向中心的引力
}
```

## 3.7 飞书机器人模块 (feishu/)

### 3.7.1 模块概述

飞书机器人模块实现了与飞书开放平台的集成，支持长连接模式接收消息事件，并提供流式回复功能。

```
knowledge_agent/feishu/
├── __init__.py          # 模块导出
├── config.py            # 配置管理
├── client.py            # API 客户端
├── message.py           # 消息处理器
└── longpoll.py          # 长连接客户端
```

### 3.7.2 配置管理 (config.py)

```python
@dataclass
class FeishuConfig:
    app_id: str = field(default_factory=lambda: os.getenv("FEISHU_APP_ID", ""))
    app_secret: str = field(default_factory=lambda: os.getenv("FEISHU_APP_SECRET", ""))
    
    @property
    def enabled(self) -> bool:
        return bool(self.app_id and self.app_secret)
```

### 3.7.3 API 客户端 (client.py)

`FeishuClient` 封装了飞书 API 调用：

| 方法 | 说明 |
|------|------|
| `reply_text()` | 回复文本消息 |
| `reply_text_with_id()` | 回复文本消息并返回消息 ID |
| `reply_card()` | 回复卡片消息 |
| `reply_card_with_id()` | 回复卡片消息并返回消息 ID |
| `edit_card()` | 编辑已发送的消息内容 |
| `push_follow_up()` | 添加跟随气泡（SDK 版本依赖） |

**消息编辑示例**：

```python
def edit_card(self, message_id: str, card: Dict[str, Any]) -> bool:
    from lark_oapi.api.im.v1 import PatchMessageRequest, PatchMessageRequestBody

    request = PatchMessageRequest.builder() \
        .message_id(message_id) \
        .request_body(PatchMessageRequestBody.builder()
            .content(json.dumps(card))
            .build()) \
        .build()

    response = self.client.im.v1.message.patch(request)
    return response.success()
```

### 3.7.4 消息处理器 (message.py)

`FeishuMessageHandler` 处理消息事件：

**核心功能**：

| 功能 | 说明 |
|------|------|
| 消息去重 | 使用 LRU 缓存防止重复处理 |
| 流式回复 | 答案逐步显示，每 0.5 秒更新一次 |
| 命令处理 | 支持 `/help`、`/stats`、`/search` 命令 |

**消息去重实现**：

```python
from collections import OrderedDict

MAX_PROCESSED_MESSAGES = 1000
MESSAGE_EXPIRE_SECONDS = 3600

class FeishuMessageHandler:
    def __init__(self, qa_agent=None):
        self.processed_message_ids = OrderedDict()

    def handle_message(self, event) -> None:
        message_id = message.message_id

        if message_id in self.processed_message_ids:
            return

        self._cleanup_expired_messages()

        if len(self.processed_message_ids) >= MAX_PROCESSED_MESSAGES:
            self.processed_message_ids.popitem(last=False)

        self.processed_message_ids[message_id] = time.time()
```

**流式回复流程**：

```python
def _handle_question_stream(self, message_id: str, question: str) -> None:
    # 1. 发送"正在思考中..."卡片
    reply_msg_id = self.client.reply_card_with_id(message_id, processing_card)

    # 2. 获取流式迭代器
    stream_iter, metadata = self.qa_agent.chat_with_stream(question)

    # 3. 节流更新卡片
    for chunk in stream_iter:
        accumulated_content += chunk
        if (now - last_update_time) >= 0.5:
            self._update_streaming_card(reply_msg_id, ...)
            last_update_time = now

    # 4. 更新最终内容
    self._update_streaming_card(..., is_final=True)
```

### 3.7.5 长连接客户端 (longpoll.py)

`FeishuLongPollClient` 管理 WebSocket 连接：

```python
class FeishuLongPollClient:
    def connect(self):
        self._thread = threading.Thread(target=self._run_in_new_loop, daemon=True)
        self._thread.start()

    def _run_in_new_loop(self):
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)

        import lark_oapi as lark

        try:
            self._start_ws_client(lark)
        finally:
            new_loop.close()

    def _start_ws_client(self, lark):
        def on_message(data: lark.im.v1.P2ImMessageReceiveV1) -> None:
            self.message_handler.handle_message(data)

        event_handler = lark.EventDispatcherHandler.builder("", "") \
            .register_p2_im_message_receive_v1(on_message) \
            .build()

        self._ws_client = lark.ws.Client(
            self.config.app_id,
            self.config.app_secret,
            event_handler=event_handler
        )
        self._ws_client.start()
```

### 3.7.6 配置常量

| 常量 | 值 | 说明 |
|------|-----|------|
| `UPDATE_THROTTLE_INTERVAL` | 0.5 秒 | 流式更新间隔 |
| `MAX_PROCESSED_MESSAGES` | 1000 | 最大缓存消息数 |
| `MESSAGE_EXPIRE_SECONDS` | 3600 秒 | 消息 ID 过期时间 |
