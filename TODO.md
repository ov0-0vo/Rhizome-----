# TODO

## ✅ 已完成

### 1. 知识向量相似度分布
- [x] 对知识条目进行相似度分布分析
- [x] 给出分布图数据（API: `/api/analysis/distribution/chart`）
- [x] 检测高相似度知识对（API: `/api/analysis/similar-pairs`）
- [x] 检测重复知识（API: `/api/analysis/duplicates`）

### 2. 知识整理
- [x] 对知识条目进行整理，给出整理结果
- [x] 重复的知识进行合并优化（API: `/api/analysis/merge`）
- [x] 目录也进行优化，使得一个目录级别不要同时存在太多知识
- [x] 自动整理功能（API: `/api/analysis/auto-organize`）

### 3. 联网搜索
- [x] 基于 langchain 的 tool 调用
- [x] 基于 tavily 的搜索功能
- [x] 实现联网搜索（API: `/api/search`）

---

## 使用说明

### 联网搜索配置

在 `.env` 文件中添加：

```env
TAVILY_API_KEY=your_tavily_api_key
WEB_SEARCH_ENABLED=true
```

获取 Tavily API Key: https://tavily.com/

### API 端点

#### 分析相关
- `GET /api/analysis/distribution` - 获取相似度分布统计
- `GET /api/analysis/distribution/chart` - 获取分布图数据
- `GET /api/analysis/similar-pairs` - 获取相似知识对
- `GET /api/analysis/duplicates` - 获取重复知识
- `GET /api/analysis/catalog-distribution` - 获取目录分布
- `GET /api/analysis/reorganization-suggestions` - 获取重组建议

#### 整理相关
- `GET /api/analysis/merge-suggestions` - 获取合并建议
- `POST /api/analysis/merge` - 执行知识合并
- `POST /api/analysis/generate-merged-content` - 生成合并内容
- `GET /api/analysis/catalog-split-suggestion/{catalog_id}` - 获取目录拆分建议
- `POST /api/analysis/split-catalog` - 执行目录拆分
- `POST /api/analysis/auto-organize` - 自动整理
- `GET /api/analysis/organization-summary` - 获取整理摘要

#### 搜索相关
- `GET /api/search/status` - 获取搜索状态
- `POST /api/search/enable` - 启用搜索
- `POST /api/search/disable` - 禁用搜索
- `POST /api/search` - 执行搜索
