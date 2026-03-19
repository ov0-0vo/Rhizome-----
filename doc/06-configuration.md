# 6. 配置指南

## 6.1 环境变量配置

Rhizome 支持通过环境变量进行配置。创建 `.env` 文件（可复制自 `.env.example`）。

### 6.1.1 必需配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `OPENAI_API_KEY` | API 密钥 | `sk-xxxxx` |

### 6.1.2 可选配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `LLM_PROVIDER` | `openai` | LLM 供应商 |
| `OPENAI_MODEL` | `gpt-3.5-turbo` | 模型名称 |
| `OPENAI_API_BASE` | `""` | API 基础 URL（用于代理） |
| `EMBEDDING_MODEL` | `text-embedding-ada-002` | 嵌入模型 |
| `EMBEDDING_API_BASE` | `""` | 嵌入 API URL |

## 6.2 LLM 供应商配置

### 6.2.1 OpenAI（默认）

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-3.5-turbo
```

### 6.2.2 Anthropic Claude

```env
LLM_PROVIDER=anthropic
OPENAI_API_KEY=sk-ant-your-key-here
OPENAI_MODEL=claude-3-sonnet-20240229
```

### 6.2.3 Ollama（本地模型）

```env
LLM_PROVIDER=ollama
OPENAI_API_BASE=http://localhost:11434
OPENAI_MODEL=llama2
```

### 6.2.4 Azure OpenAI

```env
LLM_PROVIDER=azure
OPENAI_API_KEY=your-azure-key
OPENAI_API_BASE=https://your-resource.openai.azure.com
OPENAI_MODEL=gpt-4
```

### 6.2.5 使用代理或第三方 API

如果你使用 OpenRouter 或其他兼容 API：

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your-api-key
OPENAI_API_BASE=https://openrouter.ai/api/v1
OPENAI_MODEL=google/gemini-pro
```

## 6.3 代码配置

### 6.3.1 配置类

```python
from knowledge_agent.config import Config

# 创建自定义配置
config = Config(
    provider="openai",
    openai_model="gpt-4",
    max_tokens=3000,
    temperature=0.5
)
```

### 6.3.2 配置优先级

配置按以下优先级生效（从高到低）：

1. 代码中直接设置的 `Config` 属性
2. 环境变量
3. 代码默认值

## 6.4 数据目录配置

### 6.4.1 默认结构

```
data/
├── catalog.json      # 知识目录
├── knowledge.json    # 知识条目
└── vector_store/     # Chroma 向量存储
```

### 6.4.2 自定义数据目录

```python
from knowledge_agent.config import Config

config = Config(
    data_dir="custom_data_path",
    catalog_file="custom_data_path/catalog.json",
    vector_store_dir="custom_data_path/vector_store"
)
```

## 6.5 模型参数配置

### 6.5.1 生成参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_tokens` | 2000 | 单次生成的最大 token 数 |
| `temperature` | 0.7 | 生成温度，控制随机性 (0-1) |

### 6.5.2 检索参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `top_k` | 5 | 检索返回的最大结果数 |

### 6.5.3 调整示例

```python
from knowledge_agent.config import Config

config = Config(
    max_tokens=4000,    # 更长的回答
    temperature=0.3,     # 更确定的回答
    top_k=10            # 更多检索结果
)
```

## 6.6 多语言配置

### 6.6.1 界面语言

当前界面支持中文。界面语言在 `gradio_app.py` 中定义。

### 6.6.2 提示词语言

系统提示词支持中英文。在 `prompt_templates.py` 中修改。

## 6.7 生产环境配置

### 6.7.1 安全建议

1. **不要提交 `.env`**：确保 `.env` 在 `.gitignore` 中
2. **使用密钥管理服务**：生产环境建议使用 AWS Secrets Manager、Azure Key Vault 等
3. **限制 API 密钥权限**：只授予必要的权限

### 6.7.2 性能优化

```env
# 使用更快的模型响应
OPENAI_MODEL=gpt-3.5-turbo

# 或使用本地模型
LLM_PROVIDER=ollama
OPENAI_MODEL=llama2
```

### 6.7.3 日志配置

当前系统无专门日志配置，可通过 Python logging 模块配置：

```python
import logging

logging.basicConfig(level=logging.INFO)
```
