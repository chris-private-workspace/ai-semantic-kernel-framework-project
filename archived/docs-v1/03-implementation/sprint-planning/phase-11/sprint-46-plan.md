# Sprint 46: Session-Agent Bridge

> **Phase 11**: Agent-Session Integration
> **Sprint 目標**: 建立 Session 與 Agent 的橋接層，實現完整對話流程

---

## Sprint 概述

| 屬性 | 值 |
|------|-----|
| Sprint 編號 | 46 |
| 計劃點數 | 30 Story Points |
| 預計工期 | 5 工作日 |
| 前置條件 | Sprint 45 完成 |

### Sprint 目標

1. 建立 SessionAgentBridge 橋接層
2. 實現訊息處理流程
3. 整合 WebSocket 串流回應
4. 工具調用審批流程

---

## User Stories

### S46-1: SessionAgentBridge 核心 (10 pts)

**As a** 系統開發者
**I want** Session 與 Agent 的橋接層
**So that** Session API 可調用 Agent 執行

**驗收標準**:
- [ ] SessionAgentBridge 類別實現
- [ ] process_message() 方法
- [ ] 訊息存儲整合
- [ ] 對話歷史載入
- [ ] Agent 回應存儲

**技術設計**:

```python
# backend/src/domain/sessions/bridge.py

from typing import AsyncIterator, List, Optional
from uuid import UUID

class SessionAgentBridge:
    """Session-Agent 橋接層"""

    def __init__(
        self,
        session_service: SessionService,
        agent_executor: AgentExecutor,
        agent_repository: AgentRepository
    ):
        self._sessions = session_service
        self._executor = agent_executor
        self._agents = agent_repository

    async def process_message(
        self,
        session_id: UUID,
        content: str,
        attachments: Optional[List[Attachment]] = None,
        stream: bool = True
    ) -> AsyncIterator[ExecutionEvent]:
        """
        處理用戶訊息並生成回應

        流程:
        1. 驗證 Session 狀態
        2. 存儲用戶訊息
        3. 獲取對話歷史
        4. 調用 Agent 生成回應
        5. 存儲 Assistant 訊息
        6. 串流/返回回應

        Args:
            session_id: Session ID
            content: 用戶訊息內容
            attachments: 附件列表
            stream: 是否串流回應

        Yields:
            ExecutionEvent: 執行事件
        """
        # 1. 獲取 Session
        session = await self._sessions.get_session(session_id)
        if session.status != SessionStatus.ACTIVE:
            yield ExecutionEvent(
                type=ExecutionEventType.ERROR,
                data={"error": "session_not_active", "status": session.status}
            )
            return

        # 2. 獲取 Agent
        agent = await self._agents.get(session.agent_id)
        if not agent:
            yield ExecutionEvent(
                type=ExecutionEventType.ERROR,
                data={"error": "agent_not_found", "agent_id": str(session.agent_id)}
            )
            return

        # 3. 存儲用戶訊息
        user_message = Message(
            session_id=session_id,
            role=MessageRole.USER,
            content=content,
            attachments=attachments
        )
        await self._sessions.add_message(session_id, user_message)

        # 4. 獲取對話歷史
        history = await self._sessions.get_messages(session_id)

        # 5. 發送開始事件
        yield ExecutionEvent(
            type=ExecutionEventType.STARTED,
            data={"session_id": str(session_id), "agent_id": str(agent.id)}
        )

        # 6. 調用 Agent 執行
        assistant_content = ""
        tool_calls = []

        async for event in self._executor.execute(agent, history, stream=stream):
            # 累積內容
            if event.type == ExecutionEventType.CONTENT:
                assistant_content += event.data
            elif event.type == ExecutionEventType.TOOL_CALL:
                tool_calls.append(event.data)

            # 轉發事件
            yield event

        # 7. 存儲 Assistant 訊息
        if assistant_content or tool_calls:
            assistant_message = Message(
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=assistant_content,
                tool_calls=tool_calls if tool_calls else None
            )
            await self._sessions.add_message(session_id, assistant_message)

    async def handle_tool_approval(
        self,
        session_id: UUID,
        approval_id: str,
        approved: bool,
        feedback: Optional[str] = None
    ) -> AsyncIterator[ExecutionEvent]:
        """
        處理工具調用審批

        Args:
            session_id: Session ID
            approval_id: 審批請求 ID
            approved: 是否批准
            feedback: 用戶反饋

        Yields:
            ExecutionEvent: 執行事件
        """
        # 獲取待審批的工具調用
        pending_call = await self._get_pending_tool_call(session_id, approval_id)

        if approved:
            # 執行工具
            async for event in self._executor.execute_tool(pending_call):
                yield event

            # 繼續對話 (將工具結果送回 LLM)
            history = await self._sessions.get_messages(session_id)
            async for event in self._executor.continue_with_tool_result(
                session_id,
                pending_call,
                history
            ):
                yield event
        else:
            # 記錄拒絕
            yield ExecutionEvent(
                type=ExecutionEventType.TOOL_RESULT,
                data={
                    "tool_call_id": pending_call.id,
                    "status": "rejected",
                    "feedback": feedback
                }
            )
```

**依賴**:
- SessionService (Phase 10)
- AgentExecutor (Sprint 45)
- AgentRepository (Phase 3)

---

### S46-2: WebSocket 訊息處理 (8 pts)

**As a** 用戶
**I want** 透過 WebSocket 即時對話
**So that** 可獲得串流式 Agent 回應

**驗收標準**:
- [ ] WebSocket 連接管理
- [ ] 訊息接收處理
- [ ] 串流回應推送
- [ ] 心跳保活機制
- [ ] 斷線重連支援

**技術設計**:

```python
# backend/src/api/v1/sessions/websocket.py

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
import asyncio

class SessionWebSocketManager:
    """Session WebSocket 管理器"""

    def __init__(self):
        self._active_connections: Dict[str, WebSocket] = {}
        self._bridge: SessionAgentBridge = None

    def set_bridge(self, bridge: SessionAgentBridge):
        self._bridge = bridge

    async def connect(self, websocket: WebSocket, session_id: str):
        """建立 WebSocket 連接"""
        await websocket.accept()
        self._active_connections[session_id] = websocket

        # 發送連接確認
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id
        })

    def disconnect(self, session_id: str):
        """斷開連接"""
        if session_id in self._active_connections:
            del self._active_connections[session_id]

    async def handle_message(
        self,
        websocket: WebSocket,
        session_id: str,
        data: Dict
    ):
        """
        處理 WebSocket 訊息

        訊息類型:
        - message: 用戶訊息
        - approval: 工具審批
        - heartbeat: 心跳
        """
        msg_type = data.get("type")

        if msg_type == "message":
            await self._handle_user_message(websocket, session_id, data)
        elif msg_type == "approval":
            await self._handle_approval(websocket, session_id, data)
        elif msg_type == "heartbeat":
            await websocket.send_json({"type": "heartbeat_ack"})
        else:
            await websocket.send_json({
                "type": "error",
                "message": f"Unknown message type: {msg_type}"
            })

    async def _handle_user_message(
        self,
        websocket: WebSocket,
        session_id: str,
        data: Dict
    ):
        """處理用戶訊息"""
        content = data.get("content", "")
        attachments = data.get("attachments", [])

        async for event in self._bridge.process_message(
            session_id=session_id,
            content=content,
            attachments=attachments,
            stream=True
        ):
            await websocket.send_json(event.to_websocket())

    async def _handle_approval(
        self,
        websocket: WebSocket,
        session_id: str,
        data: Dict
    ):
        """處理工具審批"""
        approval_id = data.get("approval_id")
        approved = data.get("approved", False)
        feedback = data.get("feedback")

        async for event in self._bridge.handle_tool_approval(
            session_id=session_id,
            approval_id=approval_id,
            approved=approved,
            feedback=feedback
        ):
            await websocket.send_json(event.to_websocket())


# WebSocket 路由
websocket_manager = SessionWebSocketManager()

@router.websocket("/sessions/{session_id}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str
):
    """Session WebSocket 端點"""
    await websocket_manager.connect(websocket, session_id)

    try:
        # 啟動心跳任務
        heartbeat_task = asyncio.create_task(
            _send_heartbeat(websocket, interval=30)
        )

        while True:
            data = await websocket.receive_json()
            await websocket_manager.handle_message(websocket, session_id, data)

    except WebSocketDisconnect:
        websocket_manager.disconnect(session_id)
        heartbeat_task.cancel()


async def _send_heartbeat(websocket: WebSocket, interval: int):
    """定期發送心跳"""
    while True:
        await asyncio.sleep(interval)
        try:
            await websocket.send_json({"type": "heartbeat"})
        except:
            break
```

**依賴**:
- FastAPI WebSocket
- SessionAgentBridge (S46-1)

---

### S46-3: REST API 訊息端點 (7 pts)

**As a** 用戶
**I want** REST API 發送訊息
**So that** 可選擇非 WebSocket 方式對話

**驗收標準**:
- [ ] POST /sessions/{id}/chat 端點
- [ ] SSE 串流回應支援
- [ ] 同步回應支援
- [ ] 錯誤處理完善

**技術設計**:

```python
# backend/src/api/v1/sessions/chat.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()

class ChatRequest(BaseModel):
    """聊天請求"""
    content: str
    attachments: Optional[List[AttachmentCreate]] = None
    stream: bool = True

class ChatResponse(BaseModel):
    """聊天回應 (非串流)"""
    message_id: str
    content: str
    tool_calls: Optional[List[Dict]] = None

@router.post("/sessions/{session_id}/chat")
async def chat(
    session_id: str,
    request: ChatRequest,
    bridge: SessionAgentBridge = Depends(get_bridge)
):
    """
    發送訊息並獲取 Agent 回應

    支援兩種模式:
    - stream=True: 返回 SSE 串流
    - stream=False: 返回完整回應
    """
    if request.stream:
        return StreamingResponse(
            _stream_response(bridge, session_id, request),
            media_type="text/event-stream"
        )
    else:
        return await _sync_response(bridge, session_id, request)


async def _stream_response(
    bridge: SessionAgentBridge,
    session_id: str,
    request: ChatRequest
):
    """生成 SSE 串流"""
    async for event in bridge.process_message(
        session_id=session_id,
        content=request.content,
        attachments=request.attachments,
        stream=True
    ):
        yield event.to_sse()


async def _sync_response(
    bridge: SessionAgentBridge,
    session_id: str,
    request: ChatRequest
) -> ChatResponse:
    """生成同步回應"""
    content = ""
    tool_calls = []
    message_id = None

    async for event in bridge.process_message(
        session_id=session_id,
        content=request.content,
        attachments=request.attachments,
        stream=False
    ):
        if event.type == ExecutionEventType.CONTENT:
            content += event.data
        elif event.type == ExecutionEventType.TOOL_CALL:
            tool_calls.append(event.data)
        elif event.type == ExecutionEventType.DONE:
            message_id = event.data.get("message_id")

    return ChatResponse(
        message_id=message_id or str(uuid4()),
        content=content,
        tool_calls=tool_calls if tool_calls else None
    )
```

**依賴**:
- FastAPI StreamingResponse
- SessionAgentBridge (S46-1)

---

### S46-4: 工具審批流程 (5 pts)

**As a** 用戶
**I want** 審批敏感工具調用
**So that** 可控制 Agent 執行危險操作

**驗收標準**:
- [ ] 審批請求生成
- [ ] 審批狀態追蹤
- [ ] 審批超時處理
- [ ] 審批歷史記錄

**技術設計**:

```python
# backend/src/domain/sessions/approval.py

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict
from uuid import UUID, uuid4

class ApprovalStatus(Enum):
    """審批狀態"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

@dataclass
class ToolApprovalRequest:
    """工具審批請求"""
    id: str
    session_id: UUID
    tool_call: Dict
    created_at: datetime
    expires_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    feedback: Optional[str] = None

class ToolApprovalManager:
    """工具審批管理器"""

    def __init__(
        self,
        cache: RedisCache,
        default_timeout: int = 300  # 5 分鐘
    ):
        self._cache = cache
        self._default_timeout = default_timeout

    async def create_approval_request(
        self,
        session_id: UUID,
        tool_call: Dict,
        timeout: Optional[int] = None
    ) -> ToolApprovalRequest:
        """創建審批請求"""
        timeout = timeout or self._default_timeout
        now = datetime.utcnow()

        request = ToolApprovalRequest(
            id=str(uuid4()),
            session_id=session_id,
            tool_call=tool_call,
            created_at=now,
            expires_at=now + timedelta(seconds=timeout)
        )

        # 存儲到 Redis
        await self._cache.set(
            f"approval:{request.id}",
            request.__dict__,
            ttl=timeout
        )

        return request

    async def get_approval_request(
        self,
        approval_id: str
    ) -> Optional[ToolApprovalRequest]:
        """獲取審批請求"""
        data = await self._cache.get(f"approval:{approval_id}")
        if not data:
            return None
        return ToolApprovalRequest(**data)

    async def resolve_approval(
        self,
        approval_id: str,
        approved: bool,
        resolved_by: str,
        feedback: Optional[str] = None
    ) -> ToolApprovalRequest:
        """解決審批請求"""
        request = await self.get_approval_request(approval_id)
        if not request:
            raise ValueError(f"Approval request not found: {approval_id}")

        if request.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval already resolved: {request.status}")

        request.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        request.resolved_at = datetime.utcnow()
        request.resolved_by = resolved_by
        request.feedback = feedback

        # 更新 Redis
        await self._cache.set(
            f"approval:{approval_id}",
            request.__dict__,
            ttl=3600  # 保留 1 小時用於審計
        )

        return request

    async def get_pending_approvals(
        self,
        session_id: UUID
    ) -> List[ToolApprovalRequest]:
        """獲取 Session 的待審批請求"""
        pattern = f"approval:*"
        approvals = []

        async for key in self._cache.scan(pattern):
            data = await self._cache.get(key)
            if data and data.get("session_id") == str(session_id):
                request = ToolApprovalRequest(**data)
                if request.status == ApprovalStatus.PENDING:
                    approvals.append(request)

        return approvals
```

**依賴**:
- RedisCache
- Session context

---

## 技術架構

### 組件關係

```
┌─────────────────────────────────────────────────────────────┐
│                    Client (Browser/App)                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
          ▼                               ▼
┌─────────────────────┐         ┌─────────────────────┐
│  WebSocket Handler  │         │   REST Chat API     │
│  /sessions/{id}/ws  │         │  /sessions/{id}/chat│
└─────────┬───────────┘         └─────────┬───────────┘
          │                               │
          └───────────────┬───────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   SessionAgentBridge                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                 process_message()                    │    │
│  │  1. 驗證 Session 狀態                               │    │
│  │  2. 存儲用戶訊息                                    │    │
│  │  3. 調用 AgentExecutor                              │    │
│  │  4. 存儲 Assistant 訊息                             │    │
│  └─────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │SessionService │ │ AgentExecutor │ │ToolApproval   │
    │ (Phase 10)    │ │ (Sprint 45)   │ │ Manager       │
    └───────────────┘ └───────────────┘ └───────────────┘
```

### 訊息流程

```
用戶發送訊息
     │
     ▼
┌────────────────────────────┐
│ WebSocket/REST 接收訊息     │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│ SessionAgentBridge         │
│ 1. 驗證 Session            │
│ 2. 存儲用戶訊息             │
│ 3. 載入對話歷史             │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│ AgentExecutor              │
│ 1. 構建 LLM 請求           │
│ 2. 調用 Azure OpenAI       │
│ 3. 串流生成回應             │
└────────────┬───────────────┘
             │
     ┌───────┴───────┐
     │               │
     ▼               ▼
┌──────────┐   ┌──────────────┐
│ 純文字   │   │ 工具調用      │
│ 回應     │   │              │
└────┬─────┘   └──────┬───────┘
     │                │
     │         ┌──────┴───────┐
     │         │              │
     │         ▼              ▼
     │   ┌──────────┐   ┌──────────┐
     │   │ 直接執行  │   │ 需要審批  │
     │   └────┬─────┘   └────┬─────┘
     │        │              │
     │        │              ▼
     │        │         等待用戶審批
     │        │              │
     └────────┴──────────────┘
                    │
                    ▼
┌────────────────────────────┐
│ 存儲 Assistant 訊息         │
│ 串流回應給客戶端            │
└────────────────────────────┘
```

### 檔案結構

```
backend/src/
├── domain/sessions/
│   ├── bridge.py            # SessionAgentBridge (S46-1)
│   └── approval.py          # ToolApprovalManager (S46-4)
│
└── api/v1/sessions/
    ├── websocket.py         # WebSocket 處理 (S46-2)
    └── chat.py              # REST Chat API (S46-3)
```

---

## 測試計劃

### 單元測試

```python
# tests/unit/domain/sessions/test_bridge.py

class TestSessionAgentBridge:
    """SessionAgentBridge 單元測試"""

    async def test_process_message_inactive_session(self, bridge, inactive_session):
        """測試非活躍 Session"""
        events = [e async for e in bridge.process_message(
            inactive_session.id, "Hello"
        )]
        assert events[0].type == ExecutionEventType.ERROR
        assert "session_not_active" in events[0].data["error"]

    async def test_process_message_success(self, bridge, active_session):
        """測試成功處理訊息"""
        events = [e async for e in bridge.process_message(
            active_session.id, "Hello"
        )]
        assert any(e.type == ExecutionEventType.CONTENT for e in events)
        assert events[-1].type == ExecutionEventType.DONE
```

### WebSocket 測試

```python
# tests/integration/test_websocket.py

class TestSessionWebSocket:
    """Session WebSocket 整合測試"""

    async def test_websocket_connection(self, client, session):
        """測試 WebSocket 連接"""
        async with client.websocket_connect(f"/sessions/{session.id}/ws") as ws:
            data = await ws.receive_json()
            assert data["type"] == "connected"

    async def test_websocket_message(self, client, session):
        """測試 WebSocket 訊息處理"""
        async with client.websocket_connect(f"/sessions/{session.id}/ws") as ws:
            await ws.receive_json()  # connected

            await ws.send_json({
                "type": "message",
                "content": "Hello"
            })

            # 收集回應事件
            events = []
            while True:
                data = await ws.receive_json()
                events.append(data)
                if data["payload"]["type"] == "done":
                    break

            assert len(events) > 0
```

---

## 完成標準

- [ ] 所有 Story 完成並通過驗收
- [ ] 單元測試覆蓋率 > 85%
- [ ] WebSocket 整合測試通過
- [ ] SSE 串流測試通過
- [ ] 代碼審查完成

---

**創建日期**: 2025-12-23
**預計完成**: Sprint 46 結束
