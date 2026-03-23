# 飞书机器人集成文档

## 概述

本文档记录了 Rhizome 项目集成飞书机器人过程中遇到的问题及解决方案。飞书机器人使用长连接模式（WebSocket）接收消息事件，无需公网服务器。

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
├── client.py            # API 客户端（发送消息）
├── message.py           # 消息处理器
└── longpoll.py          # 长连接客户端
```

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
           # 创建新的事件循环
           new_loop = asyncio.new_event_loop()
           asyncio.set_event_loop(new_loop)
           
           # 延迟导入
           import lark_oapi as lark
           
           try:
               # 运行 WebSocket 客户端
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

## 关键代码示例

### 配置 (config.py)

```python
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

@dataclass
class FeishuConfig:
    app_id: str = field(default_factory=lambda: os.getenv("FEISHU_APP_ID", ""))
    app_secret: str = field(default_factory=lambda: os.getenv("FEISHU_APP_SECRET", ""))
    
    @property
    def enabled(self) -> bool:
        return bool(self.app_id and self.app_secret)
```

### 长连接客户端 (longpoll.py)

```python
import asyncio
import threading
from typing import Optional

from .config import feishu_config
from .message import FeishuMessageHandler

class FeishuLongPollClient:
    def __init__(self, message_handler: FeishuMessageHandler = None):
        self.config = feishu_config
        self.message_handler = message_handler
        self._running = False
        self._ws_client = None
        self._thread: Optional[threading.Thread] = None
    
    def connect(self):
        if not self.config.enabled:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_in_new_loop, daemon=True)
        self._thread.start()
    
    def _run_in_new_loop(self):
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        
        import lark_oapi as lark
        
        try:
            while self._running:
                try:
                    self._start_ws_client(lark)
                except Exception as e:
                    import time
                    time.sleep(5)
        finally:
            new_loop.close()
    
    def _start_ws_client(self, lark):
        def on_message(data: lark.im.v1.P2ImMessageReceiveV1) -> None:
            self.message_handler.handle_message(data)
        
        event_handler = lark.EventDispatcherHandler.builder("", "") \
            .register_p2_im_message_receive_v1(on_message) \
            .build()
        
        self._ws_client = lark.ws.Client(
            self.config.app_id,
            self.config.app_secret,
            event_handler=event_handler
        )
        self._ws_client.start()
    
    def stop(self):
        self._running = False
```

### API 客户端 (client.py)

```python
import json
from typing import Dict, Any

class FeishuClient:
    def __init__(self):
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            import lark_oapi as lark
            self._client = lark.Client.builder() \
                .app_id(feishu_config.app_id) \
                .app_secret(feishu_config.app_secret) \
                .build()
        return self._client
    
    def reply_text(self, message_id: str, text: str) -> bool:
        from lark_oapi.api.im.v1 import ReplyMessageRequest, ReplyMessageRequestBody
        
        request = ReplyMessageRequest.builder() \
            .message_id(message_id) \
            .request_body(ReplyMessageRequestBody.builder()
                .msg_type("text")
                .content(json.dumps({"text": text}))
                .build()) \
            .build()
        
        response = self.client.im.v1.message.reply(request)
        return response.success()
    
    def reply_card(self, message_id: str, card: Dict[str, Any]) -> bool:
        from lark_oapi.api.im.v1 import ReplyMessageRequest, ReplyMessageRequestBody
        
        request = ReplyMessageRequest.builder() \
            .message_id(message_id) \
            .request_body(ReplyMessageRequestBody.builder()
                .msg_type("interactive")
                .content(json.dumps(card))
                .build()) \
            .build()
        
        response = self.client.im.v1.message.reply(request)
        return response.success()
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

---

## 参考文档

- [飞书开放平台 - Python SDK](https://open.feishu.cn/document/server-side-sdk/python--sdk/invoke-server-api)
- [飞书开放平台 - 处理事件](https://open.feishu.cn/document/server-side-sdk/python--sdk/handle-events)
- [飞书开放平台 - 长连接模式](https://open.feishu.cn/document/client-docs/bot-v3/events/long-connection)
