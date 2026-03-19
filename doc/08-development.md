# 8. 开发指南

## 8.1 项目结构

```
rhizome/
├── knowledge_agent/          # 主包
│   ├── __init__.py
│   ├── config.py            # 配置
│   ├── agent/               # Agent 模块
│   │   ├── __init__.py
│   │   ├── qa_agent.py
│   │   └── prompt_templates.py
│   ├── knowledge/           # 知识管理模块
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── catalog_manager.py
│   │   └── knowledge_store.py
│   ├── storage/             # 存储模块
│   │   ├── __init__.py
│   │   ├── json_storage.py
│   │   └── vector_store.py
│   └── ui/                  # UI 模块
│       ├── __init__.py
│       └── gradio_app.py
├── data/                    # 数据目录
├── doc/                     # 技术文档
├── tests/                   # 测试
├── pyproject.toml           # 项目配置
├── .env.example            # 环境变量示例
└── README.md
```

## 8.2 开发环境设置

### 8.2.1 安装 uv

```powershell
winget install astral-sh.uv
```

### 8.2.2 初始化开发环境

```powershell
# 创建虚拟环境
uv venv --prompt Rhizome --python 3.11

# 安装依赖（包括开发依赖)
uv sync --all-extras

# 激活虚拟环境
.venv\Scripts\Activate.ps1
```

### 8.2.3 安装开发依赖

```bash
uv add --dev pytest black ruff
```

## 8.3 代码规范

### 8.3.1 Python 版本

- 最低支持：Python 3.10
- 推荐：Python 3.11

### 8.3.2 代码格式化

使用 Black 进行格式化：

```bash
# 格式化所有代码
uv run black knowledge_agent/

# 检查格式
uv run black --check knowledge_agent/
```

### 8.3.3 代码检查

使用 Ruff 进行检查：

```bash
# 检查代码
uv run ruff check knowledge_agent/

# 自动修复
uv run ruff check --fix knowledge_agent/
```

### 8.3.4 导入排序

```bash
# 排序导入
uv run ruff check --select I knowledge_agent/
```

## 8.4 测试

### 8.4.1 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_qa_agent.py

# 带详细输出
uv run pytest -v
```

### 8.4.2 测试覆盖

```bash
# 生成覆盖率报告
uv run pytest --cov=knowledge_agent --cov-report=html
```

## 8.5 添加新功能

### 8.5.1 添加新的 LLM 供应商

在 `knowledge_agent/agent/qa_agent.py` 中修改 `create_llm()` 函数：

```python
def create_llm():
    provider = config.provider.lower()

    if provider == "openai":
        return ChatOpenAI(...)
    elif provider == "anthropic":
        return ChatAnthropic(...)
    elif provider == "ollama":
        return ChatOllama(...)
    elif provider == "azure":
        return ChatOpenAI(...)
    elif provider == "your_new_provider":  # 新增
        return ChatYourProvider(...)  # 实现新供应商
    else:
        raise ValueError(f"Unknown provider: {provider}")
```

### 8.5.2 添加新的存储后端

创建新的存储类，实现相同的接口：

```python
# knowledge_agent/storage/postgres_storage.py
class PostgresStorage:
    def __init__(self, connection_string: str):
        self.conn = connect(connection_string)

    def get_all_catalogs(self) -> List[KnowledgeCatalog]:
        # 实现...
```

然后在 `catalog_manager.py` 中替换：

```python
from knowledge_agent.storage.postgres_storage import PostgresStorage

class CatalogManager:
    def __init__(self):
        self.storage = PostgresStorage(connection_string)
```

### 8.5.3 添加新的 UI 界面

参考 `gradio_app.py` 创建新的 UI：

```python
# knowledge_agent/ui/streamlit_app.py
import streamlit as st

def create_streamlit_app():
    st.title("Rhizome Knowledge Agent")
    # 实现...
```

## 8.6 调试技巧

### 8.6.1 启用详细日志

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

### 8.6.2 检查配置

```python
from knowledge_agent.config import config

print(f"Provider: {config.provider}")
print(f"Model: {config.openai_model}")
print(f"API Key: {config.openai_api_key[:10]}...")
```

### 8.6.3 测试 LLM 连接

```python
from knowledge_agent.agent.qa_agent import create_llm

llm = create_llm()
response = llm.invoke("Say hello!")
print(response)
```

## 8.7 贡献指南

### 8.7.1 分支管理

- `main`：稳定版本
- `develop`：开发版本
- `feature/*`：新功能
- `fix/*`：修复

### 8.7.2 提交流程

1. Fork 仓库
2. 创建功能分支：`git checkout -b feature/new-feature`
3. 编写代码和测试
4. 确保代码通过检查：`uv run ruff check && uv run black --check`
5. 提交：`git commit -m "feat: add new feature"`
6. 推送：`git push origin feature/new-feature`
7. 创建 Pull Request

### 8.7.3 提交信息规范

```
feat: 新功能
fix: 修复问题
docs: 文档更新
style: 代码格式（不影响功能）
refactor: 重构
test: 测试
chore: 构建/工具
```

## 8.8 依赖管理

### 8.8.1 添加依赖

```bash
# 添加运行时依赖
uv add package-name

# 添加开发依赖
uv add --dev package-name
```

### 8.8.2 更新依赖

```bash
# 更新所有依赖
uv lock --refresh

# 同步更新
uv sync
```

### 8.8.3 移除依赖

```bash
uv remove package-name
```
