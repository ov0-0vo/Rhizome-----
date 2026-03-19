# Rhizome（灵犀树）- UV 环境配置指南

## 环境已配置完成

- **Python版本**: 3.11.15
- **虚拟环境**: `.venv`
- **已安装依赖**: 145 个包

## 运行项目

### 方式一：使用 run.bat（推荐，解决中文路径编码问题）
```powershell
.\run.bat -m knowledge_agent.ui.gradio_app
```

### 方式二：使用 uv run
```powershell
uv run python -m knowledge_agent.ui.gradio_app
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `uv sync` | 同步依赖到虚拟环境 |
| `uv add <package>` | 添加依赖 |
| `uv remove <package>` | 移除依赖 |
| `uv lock` | 锁定依赖版本 |
| `uv run <command>` | 在虚拟环境中运行命令 |
| `uv python list` | 查看可用 Python 版本 |

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
EMBEDDING_MODEL=text-embedding-ada-002
```

## 注意事项

由于项目路径包含中文字符，建议使用 `run.bat` 脚本运行项目，该脚本会自动设置 UTF-8 编码。
