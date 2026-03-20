# Rhizome（灵犀树）- UV 环境配置指南

## 环境已配置完成

- **Python 版本**: 3.11.15
- **虚拟环境**: `.venv`
- **Node.js**: 18+ (前端需要)

## 快速启动

### 方式一：使用 start.bat（推荐）
```powershell
.\start.bat
```

该脚本会自动启动：
- 后端服务 (FastAPI on port 8000)
- 前端服务 (Vue 3 on port 3000)

### 方式二：手动启动

**启动后端：**
```powershell
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**启动前端（新终端）：**
```powershell
cd frontend
npm install  # 首次运行
npm run dev
```

## 访问地址

- **前端界面**: http://localhost:3000
- **API 文档**: http://localhost:8000/docs

## 常用命令

### 后端 (uv)

| 命令 | 说明 |
|------|------|
| `uv sync` | 同步依赖到虚拟环境 |
| `uv add <package>` | 添加依赖 |
| `uv remove <package>` | 移除依赖 |
| `uv lock` | 锁定依赖版本 |
| `uv run <command>` | 在虚拟环境中运行命令 |
| `uv python list` | 查看可用 Python 版本 |

### 前端 (npm)

| 命令 | 说明 |
|------|------|
| `npm install` | 安装前端依赖 |
| `npm run dev` | 启动开发服务器 |
| `npm run build` | 构建生产版本 |
| `npm run preview` | 预览生产版本 |

## 激活虚拟环境

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows CMD
.venv\Scripts\activate.bat
```

## 环境变量配置

编辑 `.env` 文件并填入你的 API Key：

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-3.5-turbo

# 嵌入模型配置（可选，默认使用本地 HuggingFace 模型）
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
```

## 项目结构

```
rhizome/
├── backend/           # FastAPI 后端
├── frontend/          # Vue 3 前端
├── knowledge_agent/   # 核心业务逻辑
├── data/              # 数据目录（自动创建）
├── .env               # 环境变量
├── start.bat          # 启动脚本
└── pyproject.toml     # Python 依赖配置
```

## 注意事项

1. **中文路径问题**: 由于项目路径可能包含中文字符，建议使用 `start.bat` 脚本启动项目
2. **首次运行**: 首次运行时会自动下载 HuggingFace 嵌入模型到本地缓存 (`~/.cache/huggingface/hub`)
3. **离线使用**: 模型下载完成后，后续使用无需网络连接
