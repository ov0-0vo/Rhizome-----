# Rhizome（灵犀树）

基于 LangChain 的知识体系智能体，帮助用户通过对话方式建立和管理个人知识体系。

## 特性

- **智能问答** - 自然语言提问，AI 理解并准确回答
- **知识目录管理** - 自动将知识分类到结构化目录
- **智能检索优化** - 目录索引 + 向量检索，只查看相关知识
- **多模型支持** - OpenAI、Anthropic、Ollama、Azure OpenAI

## 环境要求

- Python 3.10+
- uv 包管理器

## 快速开始

### 1. 安装 uv

```powershell
winget install astral-sh.uv
```

### 2. 创建虚拟环境并安装依赖

```powershell
uv sync
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并填入你的 API Key：

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=text-embedding-ada-002
```

### 4. 运行项目

```powershell
uv run python -m knowledge_agent.ui.gradio_app
```

或使用启动脚本（解决中文路径编码问题）：

```powershell
.\run.bat -m knowledge_agent.ui.gradio_app
```

## 支持的 LLM 供应商

| 供应商 | LLM_PROVIDER | 说明 |
|--------|--------------|------|
| OpenAI | `openai` | 默认值，使用 OpenAI 官方 API |
| Anthropic | `anthropic` | Claude 系列模型 |
| Ollama | `ollama` | 本地开源模型 |
| Azure | `azure` | Azure OpenAI Service |

## 项目结构

```
knowledge_agent/
├── agent/              # Agent 核心模块
│   ├── prompt_templates.py
│   └── qa_agent.py
├── knowledge/          # 知识管理模块
│   ├── catalog_manager.py
│   ├── knowledge_store.py
│   └── models.py
├── storage/            # 存储模块
│   ├── json_storage.py
│   └── vector_store.py
└── ui/                 # 界面模块
    └── gradio_app.py
```

## 技术栈

- **LLM 框架**: LangChain
- **向量存储**: Chroma
- **前端**: Gradio
- **环境管理**: uv

## 许可证

MIT
