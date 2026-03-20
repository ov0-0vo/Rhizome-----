# Rhizome（灵犀树）

基于 LangChain 的知识体系智能体，帮助用户通过对话方式建立和管理个人知识体系。

## 特性

- **智能问答** - 自然语言提问，AI 理解并准确回答
- **知识目录管理** - 自动将知识分类到结构化目录
- **智能检索优化** - 目录索引 + 向量检索，只查看相关知识
- **多模型支持** - OpenAI、Anthropic、Ollama、Azure OpenAI
- **本地嵌入模型** - 支持 HuggingFace 本地模型，离线可用
- **前后端分离** - FastAPI 后端 + Vue 3 前端

## 技术栈

### 后端
- **框架**: FastAPI
- **LLM 框架**: LangChain
- **向量存储**: Chroma
- **嵌入模型**: HuggingFace (本地缓存优化)

### 前端
- **框架**: Vue 3
- **构建工具**: Vite
- **HTTP 客户端**: Axios

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
│   └── routes/            # API 路由
│       ├── chat.py        # 对话接口
│       ├── knowledge.py   # 知识管理接口
│       └── catalog.py     # 目录管理接口
├── frontend/              # Vue 3 前端
│   ├── src/
│   │   ├── views/        # 页面组件
│   │   ├── components/   # 通用组件
│   │   ├── api.js        # API 封装
│   │   └── App.vue       # 根组件
│   └── package.json
├── knowledge_agent/       # 核心业务逻辑
│   ├── agent/            # Agent 模块
│   ├── knowledge/        # 知识管理
│   └── storage/          # 存储层
└── data/                 # 数据目录（自动创建）
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

### 知识管理
- `GET /api/knowledge` - 获取所有知识
- `GET /api/knowledge/statistics` - 获取统计数据
- `GET /api/knowledge/search` - 搜索知识
- `DELETE /api/knowledge/{id}` - 删除知识

### 目录管理
- `GET /api/catalog/tree` - 获取目录树
- `GET /api/catalog` - 获取所有目录
- `POST /api/catalog` - 创建目录
- `DELETE /api/catalog/{id}` - 删除目录

## 许可证

MIT
