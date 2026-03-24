# Rhizome（灵犀树）技术文档

## 目录

1. [项目概述](01-overview.md)
2. [系统架构](02-architecture.md)
3. [核心模块详解](03-modules.md)
4. [数据模型](04-data-models.md)
5. [API 参考](05-api-reference.md)
6. [配置指南](06-configuration.md)
7. [部署指南](07-deployment.md)
8. [开发指南](08-development.md)
9. [HuggingFace 模型缓存优化](09-huggingface-cache.md)

## 快速链接

- [README](../README.md) - 项目简介
- [SPEC](../SPEC.md) - 项目规格说明
- [UV_SETUP](../UV_SETUP.md) - 环境配置指南
- [飞书集成文档](../docs/feishu-integration.md) - 飞书机器人集成指南

## 版本历史

### v0.3.0 (当前)

**新增功能：**
- 飞书机器人集成
  - 长连接模式接收消息
  - 流式回复功能
  - 消息去重机制（LRU 缓存）
  - 跟随气泡提示（SDK 版本依赖）
- 飞书命令支持：`/help`、`/stats`、`/search`

**技术改进：**
- 飞书模块独立封装
- 消息 ID LRU 缓存管理
- 流式回复节流控制（0.5 秒）
- SDK 兼容性处理

### v0.2.0

**新增功能：**
- 流式输出支持（SSE）
- 对话历史记录
- Markdown 渲染
- 扩展统计功能
- 知识详情查看
- 知识创建和更新接口

**技术改进：**
- 依赖注入模式
- 后端异步处理
- 前端组件优化
- Vue 3 前端替代 Gradio
- FastAPI 后端 API
- 前后端分离架构

### v0.1.0

**基础功能：**
- 基础对话功能
- 知识目录管理
- 向量检索
- 多模型支持
- Gradio Web 界面
