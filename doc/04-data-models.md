# 4. 数据模型

## 4.1 知识目录 (KnowledgeCatalog)

知识目录采用树状结构，用于组织和管理知识条目。

### 4.1.1 数据结构

```python
class KnowledgeCatalog:
    id: str                    # 唯一标识符 (UUID)
    name: str                  # 目录名称
    keywords: List[str]       # 关键词列表，用于匹配
    parent_id: Optional[str]   # 父目录 ID，None 表示根目录
    children: List[str]        # 子目录 ID 列表
    knowledge_items: List[str] # 知识条目 ID 列表
    created_at: str           # 创建时间 (ISO 格式)
    updated_at: str           # 更新时间 (ISO 格式)
```

### 4.1.2 JSON 表示

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "机器学习",
  "keywords": ["ML", "监督学习", "神经网络", "深度学习"],
  "parent_id": null,
  "children": [
    "550e8400-e29b-41d4-a716-446655440001",
    "550e8400-e29b-41d4-a716-446655440002"
  ],
  "knowledge_items": [
    "item-001",
    "item-002"
  ],
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T14:20:00"
}
```

### 4.1.3 层级关系

```
根目录 (null)
└── 机器学习
    ├── 监督学习
    │   ├── 分类
    │   └── 回归
    ├── 无监督学习
    │   ├── 聚类
    │   └── 降维
    └── 深度学习
        ├── CNN
        └── RNN
```

## 4.2 知识条目 (KnowledgeItem)

知识条目是系统的基本存储单元，存储用户问题和 AI 回答。

### 4.2.1 数据结构

```python
class KnowledgeItem:
    id: str                    # 唯一标识符 (UUID)
    catalog_id: str            # 所属目录 ID
    question: str              # 用户问题
    answer: str                # AI 回答
    keywords: List[str]        # 关键词列表
    sources: List[str]         # 参考来源
    confidence: float          # 置信度 (0-1)
    created_at: str            # 创建时间
    updated_at: str            # 更新时间
```

### 4.2.2 JSON 表示

```json
{
  "id": "item-001",
  "catalog_id": "550e8400-e29b-41d4-a716-446655440001",
  "question": "什么是监督学习？",
  "answer": "监督学习是一种机器学习方法...",
  "keywords": ["监督学习", "标签", "训练集"],
  "sources": [],
  "confidence": 0.95,
  "created_at": "2024-01-15T10:35:00",
  "updated_at": "2024-01-15T10:35:00"
}
```

## 4.3 目录结构文件 (catalog.json)

存储所有知识目录的 JSON 文件。

### 4.3.1 文件结构

```json
{
  "catalogs": [
    {
      "id": "uuid-1",
      "name": "根目录",
      "keywords": [],
      "parent_id": null,
      "children": ["uuid-2", "uuid-3"],
      "knowledge_items": [],
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ],
  "root_id": "uuid-1"
}
```

## 4.4 知识数据文件 (knowledge.json)

存储所有知识条目的 JSON 文件。

### 4.4.1 文件结构

```json
{
  "items": [
    {
      "id": "item-001",
      "catalog_id": "catalog-001",
      "question": "问题内容",
      "answer": "回答内容",
      "keywords": ["关键词1", "关键词2"],
      "sources": [],
      "confidence": 0.95,
      "created_at": "2024-01-15T10:35:00",
      "updated_at": "2024-01-15T10:35:00"
    }
  ]
}
```

## 4.5 向量存储 (Chroma)

向量存储用于高效的知识检索。

### 4.5.1 Collection 结构

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 知识条目 ID |
| document | string | 问题+回答的组合文本 |
| metadata.catalog_id | string | 所属目录 ID |
| metadata.question | string | 原始问题 |

### 4.5.2 文档格式

存储时，问题和建议将合并为一个文档：

```
问题: 什么是机器学习？
答案: 机器学习是人工智能的一个分支...
```

### 4.5.3 检索流程

1. 用户提问 → 转换为向量
2. 在 Chroma 中搜索相似文档
3. 返回 top-k 个最相似的知识条目
4. 将检索结果作为上下文传给 LLM

## 4.6 配置模型

### 4.6.1 Config 数据类

```python
@dataclass
class Config:
    provider: str              # LLM 供应商
    openai_api_key: str       # API 密钥
    openai_api_base: str      # API 基础 URL
    openai_model: str         # 模型名称
    embedding_model: str       # 嵌入模型
    embedding_api_base: str    # 嵌入 API URL
    data_dir: str              # 数据目录
    catalog_file: str          # 目录文件路径
    vector_store_dir: str      # 向量存储路径
    max_tokens: int           # 最大 token 数
    temperature: float         # 生成温度
    top_k: int                # 检索返回数量
```

## 4.7 API 响应模型

### 4.7.1 chat() 返回值

```python
{
    "answer": str,              # AI 生成的回答
    "source": str,             # "existing_knowledge" | "generated"
    "knowledge_id": str,        # 知识条目 ID
    "catalog_id": str,          # 所属目录 ID
    "match_reason": str,        # 匹配原因（仅新知识）
    "analysis": {               # 问题分析结果
        "keywords": List[str],
        "domain": str,
        "concepts": List[str],
        "suggested_category": str
    },
    "metadata": {               # 知识元数据
        "summary": str,
        "keywords": List[str],
        "related_topics": List[str]
    },
    "is_new": bool              # 是否是新知识
}
```

### 4.7.2 search() 返回值

```python
[
    {
        "id": str,              # 知识条目 ID
        "question": str,        # 问题
        "answer": str,          # 回答
        "keywords": List[str],  # 关键词
        "catalog_id": str,      # 所属目录
        "similarity": float,    # 相似度分数
        "created_at": str       # 创建时间
    }
]
```

### 4.7.3 get_catalog_tree() 返回值

```python
{
    "id": str,                  # 目录 ID
    "name": str,                # 目录名称
    "keywords": List[str],      # 关键词
    "knowledge_count": int,     # 知识条目数量
    "children": [               # 子目录
        {
            "id": str,
            "name": str,
            "keywords": List[str],
            "knowledge_count": int,
            "children": []
        }
    ]
}
```
