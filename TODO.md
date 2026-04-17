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

### 4. 性能优化（v0.4.0）
- [x] LLM 实例复用（减少 66% 连接开销）
- [x] JSON 存储内存缓存（Write-Through 策略）
- [x] N+1 查询模式修复（ChromaDB $or 过滤器）
- [x] 同步调用 async 包装（asyncio.to_thread）
- [x] 前端视图懒加载（defineAsyncComponent）
- [x] 力导向图收敛检测
- [x] XSS 防护（DOMPurify）

### 5. Bug 修复（v0.4.0）
- [x] reflection_manager 方法调用修复
- [x] 相似度计算公式修复
- [x] 裸 except 替换为具体异常
- [x] 目录计数同步机制
- [x] 异步调用错误处理

### 6. 新功能（v0.4.0）
- [x] 每日发现模块（热点/推荐/盲区）
- [x] 知识库导入功能（.md/.txt 文件导入）

---

## 🔲 待完成

### P0 - 严重问题

- [x] **API Key 明文暴露** — `GET /api/config` 将所有 API Key 以明文返回前端，应脱敏显示仅返回后4位 ✅ 已修复
- [x] **习题答案安全漏洞** — 习题生成接口返回 correct_answer 给前端，用户可通过开发者工具查看答案，应在服务端存储答案 ✅ 已修复
- [x] **SSE 流解析跨 chunk 边界问题** — sendStreamPost 未处理 TCP chunk 分割，可能导致 JSON 解析失败 ✅ 已修复
- [x] **sendStreamPost 缺少 onDone 回调** — 流正常结束时 loading 状态不会重置 ✅ 已修复
- [x] **knowledge.py 统计接口裸 except** — `except: pass` 吞掉日期解析异常，导致统计不准确 ✅ 已修复
- [x] **JSON 与向量存储双写非原子性** — 写入 JSON 成功但向量存储失败会导致数据不一致 ✅ 已修复
- [x] **全量加载无分页** — `GET /api/knowledge` 等接口返回全部数据，缺少 offset/limit 分页参数 ✅ 已修复

### P1 - 中等问题

- [x] **分析/统计接口无缓存** — 相似度分析 O(n²) 每次重新计算，应添加 TTL 缓存 ✅ 已修复
- [x] **Canvas 未处理 DPR** — 高 DPI 屏幕 Canvas 模糊，需乘以 devicePixelRatio ✅ 已修复
- [x] **目录删除不处理孤儿知识** — 删除目录后知识条目的 catalog_id 仍指向已删除目录 ✅ 已修复
- [x] **qa_agent._background_store 仍使用 print()** — 应替换为 logger ✅ 已修复
- [ ] **knowledge_store.add_knowledge 不更新目录引用** — 新增知识不自动添加到目录的 knowledge_items
- [ ] **图谱接口全量加载无限制** — 大量知识时节点和边过多，前端卡顿
- [ ] **配置更新无验证** — 可写入无效配置导致服务崩溃
- [ ] **write_env_file 不保留未知键和注释** — 用户手动添加的配置会被丢弃
- [ ] **前端无全局错误处理** — axios 无响应拦截器，各组件需单独处理错误
- [ ] **前端多处使用 alert()** — 应实现统一的 Toast/Notification 组件
- [x] **DiscoveryView.loadSummary 未使用结果** — summary 数据被 console.log 丢弃 ✅ 已修复
- [x] **JSON 存储无文件锁** — 多线程并发读写可能导致数据损坏 ✅ 已修复
- [ ] **搜索结果无分页** — 前端固定 limit=5，无法浏览更多结果
- [ ] **ChatView 历史记录逻辑错误** — 加载的是知识库问答对而非对话历史

### P2 - 低优先级

- [ ] **GraphView 无触摸支持** — 移动端无法拖拽缩放图谱
- [ ] **GraphView 样式硬编码** — 未使用 CSS 变量，深色模式显示异常
- [ ] **AnalysisView 组件过大** — 超过 1800 行，应拆分子组件
- [ ] **中文分词过于简单** — 正则提取产生无意义片段，应引入 jieba
- [ ] **配置更新需重启服务** — 应实现配置热重载机制
- [ ] **无请求限流** — LLM 调用无频率限制，可能被滥用
- [x] **健康检查不检测依赖** — 不检查 ChromaDB/LLM 连接状态 ✅ 已修复
- [x] **VectorStoreManager 异常捕获范围过窄** — 仅捕获 ValueError/KeyError/TypeError ✅ 已修复
- [ ] **前端无请求取消机制** — 组件卸载时未取消进行中的请求
- [ ] **StatsView/DiscoveryView 错误无用户反馈** — 加载失败时无错误提示
- [ ] **ConfigView 无表单验证** — 保存前不验证必填字段和格式
- [ ] **反思会话无持久化** — 服务重启后会话丢失

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

#### 导入相关
- `POST /api/import/file` - 文件上传导入
- `POST /api/import/text` - 文本内容导入
