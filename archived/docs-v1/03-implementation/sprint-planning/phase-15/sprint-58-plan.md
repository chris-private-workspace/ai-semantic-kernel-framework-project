# Sprint 58: AG-UI Core Infrastructure

## Sprint 概述

**Sprint 目標**: 建立 AG-UI 協議的核心基礎設施，包含 SSE 端點、事件橋接器、線程管理和事件類型定義

**Story Points**: 30 點
**預估工期**: 1 週

## User Stories

### S58-1: AG-UI SSE Endpoint (10 pts)

**As a** 前端開發者
**I want** 符合 AG-UI 協議的 SSE 端點
**So that** 前端能以標準化方式接收 Agent 事件串流

**Acceptance Criteria**:
- [ ] `POST /api/v1/ag-ui` 端點實現
- [ ] 正確解析 `RunAgentInput` 請求格式
- [ ] 返回 `text/event-stream` SSE 響應
- [ ] 支持 CORS 跨域請求
- [ ] 實現正確的 SSE 格式 (`data: {...}\n\n`)
- [ ] 單元測試覆蓋率 > 90%

**Technical Tasks**:
```
backend/src/api/v1/ag_ui/
├── __init__.py
├── routes.py           # 主端點路由
├── schemas.py          # Pydantic 模型
└── dependencies.py     # 依賴注入
```

**Implementation Details**:
```python
# routes.py
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from src.integrations.ag_ui import HybridEventBridge

router = APIRouter(prefix="/ag-ui", tags=["AG-UI"])

@router.post("/")
async def ag_ui_endpoint(
    request: Request,
    event_bridge: HybridEventBridge = Depends(get_event_bridge),
) -> StreamingResponse:
    """AG-UI Protocol Endpoint"""
    body = await request.json()
    run_input = RunAgentInput.model_validate(body)

    return StreamingResponse(
        event_bridge.stream_events(run_input),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
```

**API Specification**:
```yaml
/api/v1/ag-ui:
  post:
    summary: AG-UI Protocol Endpoint
    requestBody:
      content:
        application/json:
          schema:
            type: object
            required:
              - threadId
              - runId
              - messages
            properties:
              threadId:
                type: string
              runId:
                type: string
              messages:
                type: array
                items:
                  type: object
                  properties:
                    role:
                      type: string
                    content:
                      type: string
              tools:
                type: array
              state:
                type: object
              forwardedProps:
                type: object
    responses:
      200:
        description: SSE Event Stream
        content:
          text/event-stream:
            schema:
              type: string
```

---

### S58-2: HybridEventBridge (10 pts)

**As a** 後端開發者
**I want** 將 Hybrid 內部事件轉換為 AG-UI 標準事件
**So that** 現有系統能無縫整合 AG-UI 協議

**Acceptance Criteria**:
- [ ] 支持所有 AG-UI 事件類型轉換
- [ ] 正確處理 RunStarted/RunFinished 生命週期
- [ ] 文字訊息事件串流 (Start/Content/End)
- [ ] 工具調用事件串流 (Start/Args/End)
- [ ] 錯誤處理和異常事件
- [ ] 單元測試覆蓋率 > 90%

**Technical Tasks**:
```
backend/src/integrations/ag_ui/
├── __init__.py
├── bridge.py           # HybridEventBridge 主類別
├── converters.py       # 事件轉換邏輯
└── types.py            # AG-UI 類型定義
```

**Implementation Details**:
```python
# bridge.py
from typing import AsyncGenerator
from src.integrations.hybrid import HybridOrchestratorV2

class HybridEventBridge:
    """將 Hybrid 事件轉換為 AG-UI 事件"""

    def __init__(
        self,
        orchestrator: HybridOrchestratorV2,
        converters: EventConverters,
    ):
        self.orchestrator = orchestrator
        self.converters = converters

    async def stream_events(
        self,
        run_input: RunAgentInput,
    ) -> AsyncGenerator[str, None]:
        """串流 AG-UI 事件"""
        # 1. 發送 RUN_STARTED
        yield self._format_sse(
            self.converters.to_run_started(run_input)
        )

        # 2. 執行並轉換事件
        async for hybrid_event in self.orchestrator.execute_stream(
            messages=run_input.messages,
            tools=run_input.tools,
            context=run_input.state,
        ):
            ag_ui_event = self.converters.convert(hybrid_event)
            if ag_ui_event:
                yield self._format_sse(ag_ui_event)

        # 3. 發送 RUN_FINISHED
        yield self._format_sse(
            self.converters.to_run_finished(run_input)
        )

    def _format_sse(self, event: BaseAGUIEvent) -> str:
        """格式化為 SSE 字串"""
        return f"data: {event.model_dump_json()}\n\n"
```

**Event Mapping**:
| Hybrid Event | AG-UI Event |
|--------------|-------------|
| `execution_started` | `RunStartedEvent` |
| `execution_completed` | `RunFinishedEvent` |
| `message_start` | `TextMessageStartEvent` |
| `message_chunk` | `TextMessageContentEvent` |
| `message_end` | `TextMessageEndEvent` |
| `tool_call_start` | `ToolCallStartEvent` |
| `tool_call_args` | `ToolCallArgsEvent` |
| `tool_call_end` | `ToolCallEndEvent` |

---

### S58-3: Thread Manager (5 pts)

**As a** 系統管理員
**I want** 管理 AG-UI Thread (對話線程)
**So that** 對話狀態能被正確追蹤和持久化

**Acceptance Criteria**:
- [ ] Thread 創建和獲取
- [ ] Thread 持久化 (Redis + PostgreSQL)
- [ ] Thread 狀態追蹤
- [ ] 多 Run 在同一 Thread 中執行
- [ ] `GET /api/v1/ag-ui/threads/{thread_id}` 端點
- [ ] `DELETE /api/v1/ag-ui/threads/{thread_id}` 端點

**Technical Tasks**:
```
backend/src/integrations/ag_ui/thread/
├── __init__.py
├── manager.py      # ThreadManager 主類別
├── models.py       # Thread 資料模型
└── storage.py      # 存儲後端
```

**Implementation Details**:
```python
# models.py
@dataclass
class AGUIThread:
    """AG-UI Thread (對話線程)"""
    thread_id: str
    created_at: datetime
    updated_at: datetime
    messages: List[AGUIMessage]
    state: Dict[str, Any]
    metadata: Dict[str, Any]

# manager.py
class ThreadManager:
    """Thread 管理器"""

    def __init__(
        self,
        cache: RedisCache,
        repository: ThreadRepository,
    ):
        self.cache = cache
        self.repository = repository

    async def get_or_create(
        self,
        thread_id: str | None,
    ) -> AGUIThread:
        """獲取或創建 Thread"""
        if thread_id:
            # 先查 Redis 緩存
            thread = await self.cache.get(f"thread:{thread_id}")
            if thread:
                return thread
            # 再查資料庫
            return await self.repository.get_by_id(thread_id)
        return await self._create_thread()

    async def append_messages(
        self,
        thread_id: str,
        messages: List[AGUIMessage],
    ) -> None:
        """追加訊息到 Thread"""
        thread = await self.get_or_create(thread_id)
        thread.messages.extend(messages)
        thread.updated_at = datetime.utcnow()
        await self._save(thread)

    async def _save(self, thread: AGUIThread) -> None:
        """保存 Thread (Write-Through)"""
        await self.cache.set(
            f"thread:{thread.thread_id}",
            thread,
            ttl=7200  # 2 hours
        )
        await self.repository.save(thread)
```

---

### S58-4: AG-UI Event Types (5 pts)

**As a** 開發者
**I want** 完整的 AG-UI 事件類型定義
**So that** 事件能被正確序列化和驗證

**Acceptance Criteria**:
- [ ] 所有 AG-UI 事件類型枚舉
- [ ] 每種事件的 Pydantic 模型
- [ ] JSON 序列化支持
- [ ] 類型驗證
- [ ] 單元測試覆蓋率 > 90%

**Technical Tasks**:
```
backend/src/integrations/ag_ui/
├── events/
│   ├── __init__.py
│   ├── base.py         # BaseAGUIEvent
│   ├── lifecycle.py    # RunStarted, RunFinished
│   ├── message.py      # TextMessage 事件
│   ├── tool.py         # ToolCall 事件
│   └── state.py        # State 事件
```

**Implementation Details**:
```python
# events/base.py
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal

class AGUIEventType(str, Enum):
    # 生命週期事件
    RUN_STARTED = "RUN_STARTED"
    RUN_FINISHED = "RUN_FINISHED"

    # 文字訊息事件
    TEXT_MESSAGE_START = "TEXT_MESSAGE_START"
    TEXT_MESSAGE_CONTENT = "TEXT_MESSAGE_CONTENT"
    TEXT_MESSAGE_END = "TEXT_MESSAGE_END"

    # 工具調用事件
    TOOL_CALL_START = "TOOL_CALL_START"
    TOOL_CALL_ARGS = "TOOL_CALL_ARGS"
    TOOL_CALL_END = "TOOL_CALL_END"

    # 狀態事件
    STATE_SNAPSHOT = "STATE_SNAPSHOT"
    STATE_DELTA = "STATE_DELTA"

    # 自定義事件
    CUSTOM = "CUSTOM"

class BaseAGUIEvent(BaseModel):
    """AG-UI 事件基類"""
    type: AGUIEventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# events/message.py
class TextMessageStartEvent(BaseAGUIEvent):
    """文字訊息開始事件"""
    type: Literal[AGUIEventType.TEXT_MESSAGE_START] = AGUIEventType.TEXT_MESSAGE_START
    message_id: str
    role: str = "assistant"

class TextMessageContentEvent(BaseAGUIEvent):
    """文字內容事件 (串流增量)"""
    type: Literal[AGUIEventType.TEXT_MESSAGE_CONTENT] = AGUIEventType.TEXT_MESSAGE_CONTENT
    message_id: str
    delta: str

class TextMessageEndEvent(BaseAGUIEvent):
    """文字訊息結束事件"""
    type: Literal[AGUIEventType.TEXT_MESSAGE_END] = AGUIEventType.TEXT_MESSAGE_END
    message_id: str

# events/tool.py
class ToolCallStartEvent(BaseAGUIEvent):
    """工具調用開始事件"""
    type: Literal[AGUIEventType.TOOL_CALL_START] = AGUIEventType.TOOL_CALL_START
    tool_call_id: str
    tool_call_name: str
    parent_message_id: str | None = None

class ToolCallArgsEvent(BaseAGUIEvent):
    """工具參數事件 (串流增量)"""
    type: Literal[AGUIEventType.TOOL_CALL_ARGS] = AGUIEventType.TOOL_CALL_ARGS
    tool_call_id: str
    delta: str

class ToolCallEndEvent(BaseAGUIEvent):
    """工具調用結束事件"""
    type: Literal[AGUIEventType.TOOL_CALL_END] = AGUIEventType.TOOL_CALL_END
    tool_call_id: str
    result: Any | None = None
```

---

## Dependencies

| 依賴項 | 來源 | 狀態 |
|--------|------|------|
| HybridOrchestratorV2 | Sprint 54 | 📋 待完成 |
| Unified Tool Executor | Sprint 54 | 📋 待完成 |
| Redis Cache | Phase 11 | ✅ 已完成 |
| PostgreSQL | Phase 1 | ✅ 已完成 |

## Definition of Done

- [ ] 所有 User Stories 完成
- [ ] 單元測試覆蓋率 > 85%
- [ ] SSE 端點可正常串流事件
- [ ] Thread 可正確持久化
- [ ] API 文檔更新
- [ ] Code Review 完成
