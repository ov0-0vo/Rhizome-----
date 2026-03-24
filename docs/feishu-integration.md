# 飞书机器人集成文档

## 概述

本文档记录了 Rhizome 项目集成飞书机器人过程中遇到的问题及解决方案。飞书机器人使用长连接模式（WebSocket）接收消息事件，无需公网服务器。

## 功能特性

| 功能 | 说明 |
|------|------|
| 流式回复 | 答案逐步显示，每 0.5 秒更新一次 |
| 消息去重 | 使用 LRU 缓存防止重复处理消息 |
| 跟随气泡 | 显示"正在处理"提示（需 SDK 支持） |
| 自动保存 | 对话内容自动保存到知识库 |

## 架构设计

```
┌─────────────────┐     WebSocket      ┌─────────────────┐
│   飞书开放平台    │ ◄──────────────► │  FastAPI 后端    │
│  (事件推送)      │                    │  (长连接客户端)   │
└─────────────────┘                    └─────────────────┘
                                              │
                                              ▼
                                       ┌─────────────────┐
                                       │   QA Agent      │
                                       │  (知识问答)      │
                                       └─────────────────┘
```

## 模块结构

```
knowledge_agent/feishu/
├── __init__.py          # 模块导出
├── config.py            # 配置管理
├── client.py            # API 客户端（发送消息、编辑消息）
├── message.py           # 消息处理器（流式回复、去重）
└── longpoll.py          # 长连接客户端
```

## 流式回复实现

### 流程图

```
用户发送消息
    ↓
机器人回复"🤔 正在思考中..."卡片
    ↓
添加跟随气泡"正在处理您的问题..."（SDK 版本依赖）
    ↓
调用 QA Agent 流式生成答案
    ↓
每 0.5 秒更新一次卡片内容（带"⏳ 正在生成..."提示）
    ↓
流式结束后更新最终内容（移除生成提示）
    ↓
后台线程保存知识到知识库
```

### 核心代码

#### message.py - 流式回复处理

```python
def _handle_question_stream(self, message_id: str, question: str) -> None:
    # 1. 发送"正在思考中..."卡片
    processing_card = {
        "config": {"wide_screen_mode": True},
        "elements": [{"tag": "markdown", "content": "🤔 **正在思考中...**"}]
    }
    reply_msg_id = self.client.reply_card_with_id(message_id, processing_card)

    # 2. 添加跟随气泡（SDK 版本依赖）
    if reply_msg_id:
        self.client.push_follow_up(reply_msg_id, "正在处理您的问题...")

    # 3. 获取流式迭代器
    stream_iter, metadata = self.qa_agent.chat_with_stream(question)
    keywords = metadata.get("analysis", {}).get("keywords", [])

    # 4. 节流更新卡片
    accumulated_content = ""
    last_update_time = 0

    for chunk in stream_iter:
        accumulated_content += chunk
        now = time.time()

        if (now - last_update_time) >= 0.5:  # 每 0.5 秒更新一次
            self._update_streaming_card(reply_msg_id, question, accumulated_content, keywords)
            last_update_time = now

    # 5. 更新最终内容
    self._update_streaming_card(reply_msg_id, question, accumulated_content, keywords, is_final=True)
```

#### client.py - 消息编辑

```python
def edit_card(self, message_id: str, card: Dict[str, Any]) -> bool:
    try:
        from lark_oapi.api.im.v1 import PatchMessageRequest, PatchMessageRequestBody

        request = PatchMessageRequest.builder() \
            .message_id(message_id) \
            .request_body(PatchMessageRequestBody.builder()
                .content(json.dumps(card))
                .build()) \
            .build()

        response = self.client.im.v1.message.patch(request)
        return response.success()
    except ImportError:
        logger.warning("PatchMessageRequest not available in current lark-oapi version")
        return True
```

### 节流控制

| 参数 | 值 | 说明 |
|------|-----|------|
| `UPDATE_THROTTLE_INTERVAL` | 0.5 秒 | 更新间隔，避免 API 频率限制 |

## 消息去重实现

### 问题背景

飞书 WebSocket 客户端可能会发送重复的消息事件，导致机器人重复处理同一条消息。

### 解决方案

使用 `OrderedDict` 实现 LRU 缓存：

```python
from collections import OrderedDict

MAX_PROCESSED_MESSAGES = 1000    # 最大缓存数量
MESSAGE_EXPIRE_SECONDS = 3600    # 过期时间（1小时）

class FeishuMessageHandler:
    def __init__(self, qa_agent=None):
        self.processed_message_ids = OrderedDict()

    def handle_message(self, event) -> None:
        message_id = message.message_id

        # 消息去重检查
        if message_id in self.processed_message_ids:
            logger.info(f"Duplicate message detected: {message_id}, skipping")
            return

        # 清理过期消息
        self._cleanup_expired_messages()

        # LRU 淘汰
        if len(self.processed_message_ids) >= MAX_PROCESSED_MESSAGES:
            self.processed_message_ids.popitem(last=False)

        # 记录消息 ID 和时间戳
        self.processed_message_ids[message_id] = time.time()

    def _cleanup_expired_messages(self) -> None:
        current_time = time.time()
        expired_ids = [
            msg_id for msg_id, timestamp in self.processed_message_ids.items()
            if current_time - timestamp > MESSAGE_EXPIRE_SECONDS
        ]
        for msg_id in expired_ids:
            del self.processed_message_ids[msg_id]
```

### 为什么是 1 小时？

| 场景 | 说明 |
|------|------|
| 正常情况 | 飞书重复推送通常在几秒内发生 |
| 异常情况 | 网络延迟可能导致延迟推送，但极少超过 1 小时 |
| 结论 | 1 小时足够覆盖所有重复推送场景 |

## 遇到的问题与解决方案

### 问题 1: EventDispatcher 导入错误

**错误信息:**
```
AttributeError: module 'lark_oapi' has no attribute 'EventDispatcher'
```

**原因:**
`lark_oapi` SDK 的 API 结构与预期不同，`EventDispatcher` 不是顶层属性。

**解决方案:**
使用 `lark.EventDispatcherHandler.builder()` 创建事件处理器：

```python
import lark_oapi as lark

event_handler = lark.EventDispatcherHandler.builder("", "") \
    .register_p2_im_message_receive_v1(on_message) \
    .build()
```

---

### 问题 2: Event 类不存在

**错误信息:**
```
ImportError: cannot import name 'Event' from 'lark_oapi.ws'
```

**原因:**
`lark_oapi.ws` 模块没有导出 `Event` 类，事件数据直接通过回调函数参数传递。

**解决方案:**
直接使用 `lark.ws.Client` 并在回调函数中处理事件：

```python
def on_message(data: lark.im.v1.P2ImMessageReceiveV1) -> None:
    message = data.event.message
    # 处理消息...

ws_client = lark.ws.Client(
    app_id,
    app_secret,
    event_handler=event_handler
)
ws_client.start()
```

---

### 问题 3: 事件循环冲突

**错误信息:**
```
RuntimeError: This event loop is already running
```

**原因:**
`lark_oapi.ws.client` 模块在导入时会缓存当前事件循环。当在 FastAPI 的异步环境中导入该模块时，它会缓存 FastAPI 的事件循环，导致后续在新线程中运行时无法创建新的事件循环。

**解决方案:**

1. **延迟导入 `lark_oapi` 模块**
   
   将 `import lark_oapi` 从文件顶部移到方法内部：

   ```python
   # 错误做法 - 顶层导入
   import lark_oapi as lark
   
   class FeishuClient:
       def method(self):
           client = lark.Client.builder()...
   
   # 正确做法 - 延迟导入
   class FeishuClient:
       @property
       def client(self):
           import lark_oapi as lark  # 在方法内部导入
           return lark.Client.builder()...
   ```

2. **在独立线程中运行 WebSocket 客户端**

   ```python
   import threading
   import asyncio
   
   class FeishuLongPollClient:
       def connect(self):
           self._thread = threading.Thread(target=self._run_in_new_loop, daemon=True)
           self._thread.start()
       
       def _run_in_new_loop(self):
           new_loop = asyncio.new_event_loop()
           asyncio.set_event_loop(new_loop)
           
           import lark_oapi as lark
           
           try:
               self._ws_client = lark.ws.Client(...)
               self._ws_client.start()
           finally:
               new_loop.close()
   ```

---

### 问题 4: 卡片格式错误

**错误信息:**
```
code=230099, msg=Failed to create card content, ext=ErrCode: 11310; 
ErrMsg: unsupported type of block; ErrorValue: divider
```

**原因:**
飞书消息卡片不支持 `divider` 类型的 block 元素。

**解决方案:**
使用 `markdown` 标签，通过 `\n\n` 分隔内容：

```python
# 错误做法
return {
    "elements": [
        {"tag": "div", "text": {"tag": "lark_md", "content": "**问题:**\n..."}},
        {"tag": "divider"},  # 不支持！
        {"tag": "div", "text": {"tag": "lark_md", "content": "**回答:**\n..."}}
    ]
}

# 正确做法
return {
    "config": {"wide_screen_mode": True},
    "elements": [
        {
            "tag": "markdown",
            "content": "**问题:**\n...\n\n**回答:**\n..."
        }
    ]
}
```

---

### 问题 5: PatchMessageRequestBody 无 msg_type 属性

**错误信息:**
```
AttributeError: 'PatchMessageRequestBodyBuilder' object has no attribute 'msg_type'
```

**原因:**
当前版本的 lark-oapi SDK 中，`PatchMessageRequestBodyBuilder` 类没有 `msg_type` 方法。

**解决方案:**
移除不必要的 `msg_type` 调用：

```python
# 错误做法
request = PatchMessageRequest.builder() \
    .message_id(message_id) \
    .request_body(PatchMessageRequestBody.builder()
        .msg_type("interactive")  # 不支持！
        .content(json.dumps(card))
        .build()) \
    .build()

# 正确做法
request = PatchMessageRequest.builder() \
    .message_id(message_id) \
    .request_body(PatchMessageRequestBody.builder()
        .content(json.dumps(card))
        .build()) \
    .build()
```

---

## 环境配置

### .env 文件

```env
FEISHU_APP_ID=cli_xxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxx
```

### 飞书开放平台配置

1. 创建企业自建应用
2. 在「事件订阅」中选择「使用长连接接收事件」
3. 添加事件订阅：`im.message.receive_v1`
4. 配置应用权限：
   - `im:message` - 获取与发送消息
   - `im:message:send_as_bot` - 以应用身份发消息

---

## 最佳实践

1. **延迟导入 SDK** - 避免事件循环冲突
2. **使用守护线程** - WebSocket 客户端在独立线程运行
3. **实现重连机制** - 连接断开后自动重连
4. **简化卡片格式** - 使用 markdown 标签避免兼容性问题
5. **3 秒响应限制** - 长连接模式要求 3 秒内处理完成
6. **消息去重** - 使用 LRU 缓存防止重复处理
7. **节流控制** - 流式更新间隔 ≥ 0.5 秒

---

## 参考文档

- [飞书开放平台 - Python SDK](https://open.feishu.cn/document/server-side-sdk/python--sdk/invoke-server-api)
- [飞书开放平台 - 处理事件](https://open.feishu.cn/document/server-side-sdk/python--sdk/handle-events)
- [飞书开放平台 - 长连接模式](https://open.feishu.cn/document/client-docs/bot-v3/events/long-connection)
