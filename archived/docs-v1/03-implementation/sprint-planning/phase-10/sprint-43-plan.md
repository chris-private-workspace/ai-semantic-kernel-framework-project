# Sprint 43: Real-time Communication

> **目標**: 實現 WebSocket 即時通訊，支援串流響應和事件推送

---

## Sprint 概述

| 屬性 | 值 |
|------|-----|
| Sprint 編號 | 43 |
| 總點數 | 35 Story Points |
| 預計時間 | 2 週 |
| 前置條件 | Sprint 42 完成 |
| 狀態 | 📋 計劃中 |

---

## Stories

### S43-1: WebSocket 基礎設施 (10 pts)

**描述**: 實現 WebSocket 連接管理和協議處理

**功能需求**:
1. WebSocket 連接管理
2. 連接認證
3. 心跳檢測
4. 重連處理

**技術設計**:

```python
# infrastructure/websocket/manager.py

from typing import Dict, Set, Optional
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class Connection:
    """WebSocket 連接"""
    websocket: WebSocket
    session_id: str
    user_id: str
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_ping: datetime = field(default_factory=datetime.utcnow)

    async def send(self, message: dict) -> None:
        """發送訊息"""
        await self.websocket.send_json(message)

    async def close(self, code: int = 1000, reason: str = "") -> None:
        """關閉連接"""
        await self.websocket.close(code, reason)


class ConnectionManager:
    """WebSocket 連接管理器"""

    def __init__(self, heartbeat_interval: int = 30):
        self._connections: Dict[str, Connection] = {}  # session_id -> Connection
        self._user_sessions: Dict[str, Set[str]] = {}  # user_id -> session_ids
        self._heartbeat_interval = heartbeat_interval
        self._heartbeat_task: Optional[asyncio.Task] = None

    async def connect(
        self,
        websocket: WebSocket,
        session_id: str,
        user_id: str
    ) -> Connection:
        """建立連接"""
        await websocket.accept()

        connection = Connection(
            websocket=websocket,
            session_id=session_id,
            user_id=user_id
        )

        # 關閉舊連接 (同一 session 只允許一個連接)
        if session_id in self._connections:
            old_conn = self._connections[session_id]
            await old_conn.close(code=4000, reason="Replaced by new connection")

        self._connections[session_id] = connection

        # 記錄用戶的 sessions
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = set()
        self._user_sessions[user_id].add(session_id)

        return connection

    async def disconnect(self, session_id: str) -> None:
        """斷開連接"""
        if session_id in self._connections:
            connection = self._connections[session_id]
            del self._connections[session_id]

            # 更新用戶 sessions
            user_id = connection.user_id
            if user_id in self._user_sessions:
                self._user_sessions[user_id].discard(session_id)
                if not self._user_sessions[user_id]:
                    del self._user_sessions[user_id]

    async def send_to_session(self, session_id: str, message: dict) -> bool:
        """發送訊息到指定 session"""
        if session_id in self._connections:
            try:
                await self._connections[session_id].send(message)
                return True
            except Exception:
                await self.disconnect(session_id)
                return False
        return False

    async def broadcast_to_user(self, user_id: str, message: dict) -> int:
        """廣播訊息給用戶的所有 sessions"""
        sent = 0
        session_ids = self._user_sessions.get(user_id, set()).copy()
        for session_id in session_ids:
            if await self.send_to_session(session_id, message):
                sent += 1
        return sent

    def get_connection(self, session_id: str) -> Optional[Connection]:
        """獲取連接"""
        return self._connections.get(session_id)

    def is_connected(self, session_id: str) -> bool:
        """檢查是否連接"""
        return session_id in self._connections

    async def start_heartbeat(self) -> None:
        """啟動心跳檢測"""
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def stop_heartbeat(self) -> None:
        """停止心跳檢測"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

    async def _heartbeat_loop(self) -> None:
        """心跳循環"""
        while True:
            await asyncio.sleep(self._heartbeat_interval)

            for session_id, connection in list(self._connections.items()):
                try:
                    await connection.send({"type": "ping"})
                except Exception:
                    await self.disconnect(session_id)
```

```python
# infrastructure/websocket/protocols.py

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

class MessageType(Enum):
    """WebSocket 訊息類型"""
    # 客戶端 → 服務器
    MESSAGE = "message"
    TYPING = "typing"
    TOOL_APPROVAL = "tool_approval"
    PONG = "pong"

    # 服務器 → 客戶端
    STREAM_START = "stream_start"
    STREAM_DELTA = "stream_delta"
    STREAM_END = "stream_end"
    TOOL_CALL = "tool_call"
    TOOL_APPROVAL_REQUEST = "tool_approval_request"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    PING = "ping"


@dataclass
class WSMessage:
    """WebSocket 訊息"""
    type: MessageType
    data: Dict[str, Any]
    message_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "message_id": self.message_id,
            **self.data
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WSMessage":
        msg_type = MessageType(data.pop("type"))
        msg_id = data.pop("message_id", None)
        return cls(type=msg_type, data=data, message_id=msg_id)


# 預定義訊息

def stream_start(message_id: str) -> WSMessage:
    return WSMessage(
        type=MessageType.STREAM_START,
        message_id=message_id,
        data={}
    )

def stream_delta(message_id: str, delta: str) -> WSMessage:
    return WSMessage(
        type=MessageType.STREAM_DELTA,
        message_id=message_id,
        data={"delta": delta}
    )

def stream_end(message_id: str) -> WSMessage:
    return WSMessage(
        type=MessageType.STREAM_END,
        message_id=message_id,
        data={}
    )

def tool_approval_request(
    tool_call_id: str,
    tool: str,
    arguments: dict
) -> WSMessage:
    return WSMessage(
        type=MessageType.TOOL_APPROVAL_REQUEST,
        data={
            "tool_call_id": tool_call_id,
            "tool": tool,
            "arguments": arguments
        }
    )

def error_message(error: str, code: str = "error") -> WSMessage:
    return WSMessage(
        type=MessageType.ERROR,
        data={"error": error, "code": code}
    )
```

**驗收標準**:
- [ ] WebSocket 連接建立正常
- [ ] 認證機制運作
- [ ] 心跳檢測正常
- [ ] 連接重連處理
- [ ] 測試覆蓋率 > 85%

---

### S43-2: 串流響應處理 (10 pts)

**描述**: 實現 LLM 串流響應和客戶端推送

**功能需求**:
1. LLM 串流調用
2. Token 逐個推送
3. 完成信號
4. 錯誤處理

**技術設計**:

```python
# domain/sessions/streaming.py

from typing import AsyncIterator, Optional
import uuid
from .models import Session, Message, MessageRole
from .repository import SessionRepository
from ..agents.service import AgentService
from ...infrastructure.websocket.manager import ConnectionManager
from ...infrastructure.websocket.protocols import (
    stream_start, stream_delta, stream_end, error_message
)

class StreamingHandler:
    """串流響應處理器"""

    def __init__(
        self,
        repository: SessionRepository,
        agent_service: AgentService,
        connection_manager: ConnectionManager
    ):
        self._repository = repository
        self._agent_service = agent_service
        self._connections = connection_manager

    async def handle_message(
        self,
        session: Session,
        content: str,
        attachments: list = None
    ) -> Message:
        """
        處理用戶訊息並串流響應

        Returns:
            Message: 助手回覆訊息
        """
        # 1. 保存用戶訊息
        user_message = Message(
            role=MessageRole.USER,
            content=content,
            attachments=attachments or []
        )
        await self._repository.add_message(session.id, user_message)

        # 2. 獲取對話歷史
        history = await self._repository.get_messages(session.id, limit=50)

        # 3. 發送串流開始
        assistant_message_id = str(uuid.uuid4())
        await self._connections.send_to_session(
            session.id,
            stream_start(assistant_message_id).to_dict()
        )

        # 4. 調用 Agent 並串流響應
        full_content = ""
        try:
            async for chunk in self._stream_agent_response(session, history):
                full_content += chunk
                await self._connections.send_to_session(
                    session.id,
                    stream_delta(assistant_message_id, chunk).to_dict()
                )

            # 5. 發送串流結束
            await self._connections.send_to_session(
                session.id,
                stream_end(assistant_message_id).to_dict()
            )

        except Exception as e:
            # 發送錯誤
            await self._connections.send_to_session(
                session.id,
                error_message(str(e)).to_dict()
            )
            raise

        # 6. 保存助手回覆
        assistant_message = Message(
            id=assistant_message_id,
            role=MessageRole.ASSISTANT,
            content=full_content
        )
        await self._repository.add_message(session.id, assistant_message)

        return assistant_message

    async def _stream_agent_response(
        self,
        session: Session,
        history: list
    ) -> AsyncIterator[str]:
        """串流 Agent 響應"""
        # 構建訊息
        messages = [
            {"role": m.role.value, "content": m.content}
            for m in history
        ]

        # 調用 Agent 串流 API
        async for chunk in self._agent_service.stream_completion(
            agent_id=session.agent_id,
            messages=messages,
            session_config=session.config
        ):
            yield chunk
```

```python
# api/v1/sessions/websocket.py

from fastapi import WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
import json

from ....domain.sessions.service import SessionService
from ....domain.sessions.streaming import StreamingHandler
from ....infrastructure.websocket.manager import ConnectionManager
from ....infrastructure.websocket.protocols import MessageType, WSMessage, error_message

async def session_websocket(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(...),
    service: SessionService = Depends(get_session_service),
    streaming: StreamingHandler = Depends(get_streaming_handler),
    connections: ConnectionManager = Depends(get_connection_manager)
):
    """Session WebSocket 端點"""

    # 1. 驗證 token
    user = await verify_token(token)
    if user is None:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    # 2. 驗證 Session
    session = await service.get_session(session_id)
    if session is None:
        await websocket.close(code=4004, reason="Session not found")
        return

    if session.user_id != user.id:
        await websocket.close(code=4003, reason="Access denied")
        return

    # 3. 建立連接
    connection = await connections.connect(websocket, session_id, user.id)

    # 4. 激活 Session
    await service.activate_session(session_id)

    try:
        while True:
            # 接收訊息
            data = await websocket.receive_json()
            message = WSMessage.from_dict(data)

            # 處理訊息
            await handle_ws_message(
                session_id=session_id,
                message=message,
                service=service,
                streaming=streaming,
                connections=connections
            )

    except WebSocketDisconnect:
        # 正常斷開
        await connections.disconnect(session_id)
        await service.suspend_session(session_id)

    except Exception as e:
        # 錯誤處理
        await connections.send_to_session(
            session_id,
            error_message(str(e)).to_dict()
        )
        await connections.disconnect(session_id)


async def handle_ws_message(
    session_id: str,
    message: WSMessage,
    service: SessionService,
    streaming: StreamingHandler,
    connections: ConnectionManager
):
    """處理 WebSocket 訊息"""

    session = await service.get_session(session_id)

    if message.type == MessageType.MESSAGE:
        # 用戶訊息
        content = message.data.get("content", "")
        attachments = message.data.get("attachments", [])

        await streaming.handle_message(
            session=session,
            content=content,
            attachments=attachments
        )

    elif message.type == MessageType.TYPING:
        # 打字狀態 (可選: 廣播給其他觀察者)
        pass

    elif message.type == MessageType.TOOL_APPROVAL:
        # 工具審批響應
        tool_call_id = message.data.get("tool_call_id")
        approved = message.data.get("approved", False)

        await handle_tool_approval(
            session_id=session_id,
            tool_call_id=tool_call_id,
            approved=approved,
            service=service
        )

    elif message.type == MessageType.PONG:
        # 心跳響應
        connection = connections.get_connection(session_id)
        if connection:
            connection.last_ping = datetime.utcnow()
```

**驗收標準**:
- [ ] 串流響應正常
- [ ] Token 逐個推送到客戶端
- [ ] 完成/錯誤信號正確
- [ ] 訊息正確保存
- [ ] 測試覆蓋率 > 85%

---

### S43-3: 工具調用處理 (10 pts)

**描述**: 實現在對話中的 MCP 工具調用和審批流程

**功能需求**:
1. 識別工具調用請求
2. 權限檢查
3. 需審批工具的處理
4. 工具執行和結果回報

**技術設計**:

```python
# domain/sessions/tool_handler.py

from typing import Optional, Dict, Any
import uuid
from .models import Session, Message, ToolCall, MessageRole
from .repository import SessionRepository
from ...integrations.mcp.core.client import MCPClient
from ...integrations.mcp.security.permissions import MCPPermissionManager, ApprovalRequirement
from ...infrastructure.websocket.manager import ConnectionManager
from ...infrastructure.websocket.protocols import (
    tool_approval_request, error_message, WSMessage, MessageType
)

class ToolCallHandler:
    """工具調用處理器"""

    def __init__(
        self,
        repository: SessionRepository,
        mcp_client: MCPClient,
        permission_manager: MCPPermissionManager,
        connection_manager: ConnectionManager
    ):
        self._repository = repository
        self._mcp = mcp_client
        self._permissions = permission_manager
        self._connections = connection_manager
        self._pending_approvals: Dict[str, ToolCall] = {}

    async def handle_tool_call(
        self,
        session: Session,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        處理工具調用

        Returns:
            工具結果 (如果需要審批則返回 None)
        """
        # 1. 檢查權限
        permission_result = await self._permissions.check_permission(
            tool_name=tool_name,
            user_id=session.user_id,
            arguments=arguments
        )

        if not permission_result.allowed:
            raise PermissionError(f"Tool not allowed: {permission_result.reason}")

        # 2. 創建 ToolCall 記錄
        tool_call = ToolCall(
            tool_name=tool_name,
            arguments=arguments,
            requires_approval=permission_result.approval_required != ApprovalRequirement.NONE
        )

        # 3. 需要審批?
        if tool_call.requires_approval:
            return await self._request_approval(session, tool_call)

        # 4. 直接執行
        return await self._execute_tool(session, tool_call)

    async def _request_approval(
        self,
        session: Session,
        tool_call: ToolCall
    ) -> None:
        """請求用戶審批"""
        # 保存待審批的調用
        self._pending_approvals[tool_call.id] = tool_call

        # 發送審批請求
        await self._connections.send_to_session(
            session.id,
            tool_approval_request(
                tool_call_id=tool_call.id,
                tool=tool_call.tool_name,
                arguments=tool_call.arguments
            ).to_dict()
        )

        return None  # 等待審批

    async def handle_approval_response(
        self,
        session: Session,
        tool_call_id: str,
        approved: bool,
        approved_by: str
    ) -> Optional[Dict[str, Any]]:
        """處理審批響應"""
        tool_call = self._pending_approvals.pop(tool_call_id, None)
        if tool_call is None:
            raise ValueError(f"Tool call not found: {tool_call_id}")

        if not approved:
            tool_call.status = "rejected"
            # 通知用戶
            await self._connections.send_to_session(
                session.id,
                WSMessage(
                    type=MessageType.TOOL_RESULT,
                    data={
                        "tool_call_id": tool_call_id,
                        "status": "rejected",
                        "result": None
                    }
                ).to_dict()
            )
            return None

        # 更新審批信息
        tool_call.approved_by = approved_by
        tool_call.approved_at = datetime.utcnow()

        # 執行工具
        return await self._execute_tool(session, tool_call)

    async def _execute_tool(
        self,
        session: Session,
        tool_call: ToolCall
    ) -> Dict[str, Any]:
        """執行工具"""
        tool_call.status = "executing"
        tool_call.executed_at = datetime.utcnow()

        try:
            # 解析工具名稱 (server.tool 格式)
            parts = tool_call.tool_name.split(".")
            if len(parts) == 2:
                server_name, tool_name = parts
            else:
                server_name = "default"
                tool_name = tool_call.tool_name

            # 調用 MCP 工具
            result = await self._mcp.call_tool(
                server=server_name,
                tool=tool_name,
                arguments=tool_call.arguments
            )

            tool_call.result = result.data if result.success else None
            tool_call.error = result.error
            tool_call.status = "completed" if result.success else "failed"

            # 發送結果
            await self._connections.send_to_session(
                session.id,
                WSMessage(
                    type=MessageType.TOOL_RESULT,
                    data={
                        "tool_call_id": tool_call.id,
                        "status": tool_call.status,
                        "result": tool_call.result,
                        "error": tool_call.error
                    }
                ).to_dict()
            )

            return tool_call.result

        except Exception as e:
            tool_call.status = "failed"
            tool_call.error = str(e)

            await self._connections.send_to_session(
                session.id,
                error_message(str(e), "tool_error").to_dict()
            )

            raise
```

**驗收標準**:
- [ ] 工具調用識別正確
- [ ] 權限檢查正常
- [ ] 審批流程運作
- [ ] 工具執行結果正確回報
- [ ] 測試覆蓋率 > 85%

---

### S43-4: 事件系統整合 (5 pts)

**描述**: 整合事件系統，支援即時狀態更新

**功能需求**:
1. 事件訂閱
2. 狀態變更通知
3. 外部事件推送

**技術設計**:

```python
# domain/sessions/event_handler.py

from typing import Callable, Dict, List, Any
import asyncio
from .models import Session
from ...infrastructure.websocket.manager import ConnectionManager
from ...infrastructure.websocket.protocols import WSMessage, MessageType

class SessionEventHandler:
    """Session 事件處理器"""

    def __init__(self, connection_manager: ConnectionManager):
        self._connections = connection_manager
        self._subscribers: Dict[str, List[Callable]] = {}

    async def on_agent_status_change(
        self,
        session_id: str,
        status: str,
        details: dict = None
    ):
        """Agent 狀態變更"""
        await self._connections.send_to_session(
            session_id,
            WSMessage(
                type=MessageType.AGENT_STATUS,
                data={
                    "status": status,
                    "details": details or {}
                }
            ).to_dict()
        )

    async def on_workflow_progress(
        self,
        session_id: str,
        workflow_id: str,
        progress: float,
        step: str
    ):
        """工作流進度更新"""
        await self._connections.send_to_session(
            session_id,
            WSMessage(
                type=MessageType.WORKFLOW_PROGRESS,
                data={
                    "workflow_id": workflow_id,
                    "progress": progress,
                    "step": step
                }
            ).to_dict()
        )

    async def on_external_event(
        self,
        user_id: str,
        event_type: str,
        event_data: dict
    ):
        """外部事件 (廣播給用戶所有 sessions)"""
        await self._connections.broadcast_to_user(
            user_id,
            WSMessage(
                type=MessageType.EXTERNAL_EVENT,
                data={
                    "event_type": event_type,
                    "event_data": event_data
                }
            ).to_dict()
        )
```

**驗收標準**:
- [ ] 事件訂閱正常
- [ ] 狀態更新即時推送
- [ ] 外部事件正確廣播
- [ ] 測試覆蓋率 > 85%

---

## 技術規格

### 依賴套件

```bash
pip install websockets
```

### 文件結構

```
backend/src/
├── infrastructure/websocket/
│   ├── __init__.py
│   ├── manager.py      # 連接管理
│   └── protocols.py    # 協議定義
│
├── domain/sessions/
│   ├── streaming.py    # 串流處理
│   ├── tool_handler.py # 工具調用
│   └── event_handler.py # 事件處理
│
└── api/v1/sessions/
    └── websocket.py    # WebSocket 端點
```

---

## 風險評估

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|---------|
| 連接不穩定 | 中 | 中 | 心跳 + 重連 |
| 訊息丟失 | 低 | 中 | 訊息確認機制 |
| 並發連接過多 | 中 | 高 | 連接限制 |
| 串流延遲 | 中 | 中 | 優化緩衝區 |

---

**創建日期**: 2025-12-22
**上次更新**: 2025-12-22
