# Rhizome（灵犀树）

基于 LangChain 的知识体系智能体，帮助用户通过对话方式建立和管理个人知识体系。

## 特性

- **智能问答** - 自然语言提问，AI 理解并准确回答
- **流式输出** - 实时显示 AI 回答，提升用户体验
- **知识目录管理** - 自动将知识分类到结构化目录
- **智能检索优化** - 目录索引 + 向量检索，只查看相关知识
- **知识图谱可视化** - 图形化展示知识关联，支持关键词网络
- **Markdown 渲染** - 知识详情支持 Markdown 格式展示
- **多模型支持** - OpenAI、Anthropic、Ollama、Azure OpenAI
- **本地嵌入模型** - 支持 HuggingFace 本地模型，离线可用
- **前后端分离** - FastAPI 后端 + Vue 3 前端

## 技术栈

### 后端
- **框架**: FastAPI
- **LLM 框架**: LangChain
- **向量存储**: Chroma
- **嵌入模型**: HuggingFace (本地缓存优化)
- **实时通信**: Server-Sent Events (SSE)

### 前端
- **框架**: Vue 3
- **构建工具**: Vite
- **HTTP 客户端**: Axios
- **Markdown 渲染**: marked

## 环境要求

- Python 3.10+
- Node.js 18+
- uv 包管理器

## 快速开始

### 1. 安装 uv

```powershell
winget install astral-sh.uv
```

### 2. 安装后端依赖

```powershell
uv sync
```

### 3. 安装前端依赖

```powershell
cd frontend
npm install
```

### 4. 配置环境变量

复制 `.env.example` 为 `.env` 并填入你的 API Key：

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-3.5-turbo

# 嵌入模型配置（可选，默认使用本地 HuggingFace 模型）
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
```

**提示**：首次使用 HuggingFace 模型时会自动下载到本地缓存 (`~/.cache/huggingface/hub`)，后续使用离线模式，无需网络连接。

### 5. 启动项目

**方式一：使用启动脚本（Windows）**
```powershell
.\start.bat
```

**方式二：手动启动**

启动后端：
```powershell
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

启动前端：
```powershell
cd frontend
npm run dev
```

### 6. 访问应用

- 前端界面: http://localhost:3000
- API 文档: http://localhost:8000/docs

## 项目结构

```
rhizome/
├── backend/                # FastAPI 后端
│   ├── main.py            # 应用入口
│   ├── dependencies.py    # 依赖注入
│   └── routes/            # API 路由
│       ├── chat.py        # 对话接口（支持 SSE 流式）
│       ├── knowledge.py   # 知识管理接口
│       ├── catalog.py     # 目录管理接口
│       └── graph.py       # 知识图谱接口
├── frontend/              # Vue 3 前端
│   ├── src/
│   │   ├── views/        # 页面组件
│   │   │   ├── ChatView.vue    # 对话页面
│   │   │   ├── CatalogView.vue # 知识目录页面
│   │   │   ├── SearchView.vue  # 搜索页面
│   │   │   ├── StatsView.vue   # 统计页面
│   │   │   └── GraphView.vue   # 知识图谱页面
│   │   ├── components/   # 通用组件
│   │   │   └── TreeNode.vue    # 目录树节点
│   │   ├── api.js        # API 封装
│   │   ├── App.vue       # 根组件
│   │   └── style.css     # 全局样式
│   └── package.json
├── knowledge_agent/       # 核心业务逻辑
│   ├── agent/            # Agent 模块
│   │   ├── qa_agent.py   # QA Agent（支持流式）
│   │   └── prompt_templates.py
│   ├── knowledge/        # 知识管理
│   │   ├── catalog_manager.py
│   │   ├── knowledge_store.py
│   │   └── models.py
│   ├── storage/          # 存储层
│   │   ├── json_storage.py
│   │   └── vector_store.py
│   └── config.py         # 配置管理
├── data/                 # 数据目录（自动创建）
│   ├── catalog.json      # 知识目录
│   ├── knowledge.json    # 知识条目
│   └── vector_store/     # 向量存储
├── doc/                  # 技术文档
├── tests/                # 测试文件
└── scripts/              # 工具脚本
```

## 支持的 LLM 供应商

| 供应商 | LLM_PROVIDER | 说明 |
|--------|--------------|------|
| OpenAI | `openai` | 默认值，使用 OpenAI 官方 API |
| Anthropic | `anthropic` | Claude 系列模型 |
| Ollama | `ollama` | 本地开源模型 |
| Azure | `azure` | Azure OpenAI Service |

## 支持的嵌入模型

| 类型 | EMBEDDING_PROVIDER | 模型示例 | 说明 |
|------|-------------------|----------|------|
| 本地模型 | `local` | BAAI/bge-small-zh-v1.5 | HuggingFace 本地模型，离线可用 |
| OpenAI | `openai` | text-embedding-ada-002 | OpenAI 嵌入 API |
| Ollama | `ollama` | nomic-embed-text | 本地 Ollama 嵌入模型 |
| Azure | `azure` | text-embedding-ada-002 | Azure OpenAI 嵌入服务 |

**本地模型优化**：
- 首次运行时自动下载模型到本地缓存
- 后续使用离线模式，无需网络连接
- 缓存位置：`~/.cache/huggingface/hub`

## API 接口

### 对话
- `POST /api/chat` - 发送消息并获取回复
- `POST /api/chat/stream` - 流式对话（SSE）
- `GET /api/chat/history` - 获取对话历史

### 知识管理
- `GET /api/knowledge` - 获取所有知识
- `GET /api/knowledge/statistics` - 获取统计数据（扩展版）
- `GET /api/knowledge/search` - 搜索知识
- `GET /api/knowledge/catalog/{catalog_id}` - 获取目录下的知识
- `DELETE /api/knowledge/{id}` - 删除知识

### 目录管理
- `GET /api/catalog/tree` - 获取目录树
- `GET /api/catalog` - 获取所有目录
- `POST /api/catalog` - 创建目录
- `DELETE /api/catalog/{id}` - 删除目录

### 知识图谱
- `GET /api/graph` - 获取完整知识图谱
- `GET /api/graph/keywords` - 获取关键词网络图谱
- `GET /api/graph/catalog/{catalog_id}` - 获取指定目录的知识图谱

## 前端功能

### 对话页面
- 流式输出 AI 回答
- 对话历史记录
- 自动滚动到最新消息

### 知识目录页面
- 树形结构展示知识目录
- 点击目录查看知识列表
- 知识详情弹窗（Markdown 渲染）

### 搜索页面
- 关键词搜索知识
- 相似度排序
- 知识详情弹窗（Markdown 渲染）

### 统计页面
- 总知识条目、目录数
- 今日/本周新增统计
- 最近添加的知识列表
- 目录分布可视化
- 热门关键词云

### 知识图谱页面
- 完整图谱 / 关键词网络视图切换
- Canvas 高性能渲染
- 节点拖拽和缩放交互
- 点击节点查看详情
- 力导向自动布局

## 许可证

MIT
