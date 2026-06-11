# Sprint 47: Integration & Polish

> **Phase 11**: Agent-Session Integration
> **Sprint 目標**: 整合測試、錯誤處理優化、文檔完善

---

## Sprint 概述

| 屬性 | 值 |
|------|-----|
| Sprint 編號 | 47 |
| 計劃點數 | 25 Story Points |
| 預計工期 | 4 工作日 |
| 前置條件 | Sprint 45, 46 完成 |

### Sprint 目標

1. 端到端整合測試
2. 錯誤處理與恢復機制完善
3. 效能優化與監控
4. API 文檔與使用指南

---

## User Stories

### S47-1: 端到端整合測試 (8 pts)

**As a** QA 工程師
**I want** 完整的端到端測試
**So that** 確保 Session-Agent 整合功能正確

**驗收標準**:
- [ ] 完整對話流程測試
- [ ] 工具調用流程測試
- [ ] 審批流程測試
- [ ] 錯誤恢復測試
- [ ] 並發測試

**技術設計**:

```python
# tests/e2e/test_session_agent_integration.py

import pytest
from httpx import AsyncClient
import asyncio

class TestSessionAgentE2E:
    """Session-Agent 端到端測試"""

    @pytest.fixture
    async def test_agent(self, db_session):
        """創建測試 Agent"""
        agent = Agent(
            name="Test Agent",
            system_prompt="You are a helpful assistant.",
            tool_ids=["mcp_calculator", "mcp_weather"]
        )
        db_session.add(agent)
        await db_session.commit()
        return agent

    @pytest.fixture
    async def test_session(self, client, test_agent):
        """創建測試 Session"""
        response = await client.post("/api/v1/sessions", json={
            "agent_id": str(test_agent.id),
            "title": "E2E Test Session"
        })
        session = response.json()

        # Activate session
        await client.post(f"/api/v1/sessions/{session['id']}/activate")
        return session

    @pytest.mark.e2e
    async def test_complete_conversation_flow(
        self,
        client: AsyncClient,
        test_session
    ):
        """測試完整對話流程"""
        session_id = test_session["id"]

        # 第一輪對話
        response1 = await client.post(
            f"/api/v1/sessions/{session_id}/chat",
            json={"content": "Hello, who are you?", "stream": False}
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["content"]
        assert "assistant" in data1["content"].lower() or "helpful" in data1["content"].lower()

        # 第二輪對話 (保持上下文)
        response2 = await client.post(
            f"/api/v1/sessions/{session_id}/chat",
            json={"content": "What did I just ask you?", "stream": False}
        )
        assert response2.status_code == 200
        data2 = response2.json()
        # 應該記得之前的問題
        assert "hello" in data2["content"].lower() or "who" in data2["content"].lower()

        # 驗證訊息歷史
        history = await client.get(f"/api/v1/sessions/{session_id}/messages")
        assert history.status_code == 200
        messages = history.json()["data"]
        assert len(messages) >= 4  # 2 user + 2 assistant

    @pytest.mark.e2e
    async def test_tool_calling_flow(
        self,
        client: AsyncClient,
        test_session
    ):
        """測試工具調用流程"""
        session_id = test_session["id"]

        # 觸發工具調用
        response = await client.post(
            f"/api/v1/sessions/{session_id}/chat",
            json={"content": "What is 15 + 27?", "stream": False}
        )
        assert response.status_code == 200
        data = response.json()

        # 驗證結果 (假設 calculator 工具返回正確答案)
        assert "42" in data["content"]

    @pytest.mark.e2e
    async def test_tool_approval_flow(
        self,
        client: AsyncClient,
        test_session_with_sensitive_tools
    ):
        """測試工具審批流程"""
        session_id = test_session_with_sensitive_tools["id"]

        # 使用 WebSocket 進行對話
        async with client.websocket_connect(f"/api/v1/sessions/{session_id}/ws") as ws:
            # 接收連接確認
            connect_msg = await ws.receive_json()
            assert connect_msg["type"] == "connected"

            # 發送觸發敏感工具的訊息
            await ws.send_json({
                "type": "message",
                "content": "Delete the file /tmp/test.txt"
            })

            # 收集事件直到收到審批請求
            events = []
            approval_event = None
            while True:
                event = await asyncio.wait_for(ws.receive_json(), timeout=30)
                events.append(event)

                if event.get("payload", {}).get("type") == "approval_required":
                    approval_event = event
                    break
                if event.get("payload", {}).get("type") == "done":
                    break

            assert approval_event is not None
            approval_id = approval_event["payload"]["data"]["approval_id"]

            # 發送審批拒絕
            await ws.send_json({
                "type": "approval",
                "approval_id": approval_id,
                "approved": False,
                "feedback": "Not authorized for file deletion"
            })

            # 驗證收到拒絕確認
            rejection_event = await ws.receive_json()
            assert rejection_event["payload"]["data"]["status"] == "rejected"

    @pytest.mark.e2e
    async def test_streaming_response(
        self,
        client: AsyncClient,
        test_session
    ):
        """測試串流回應"""
        session_id = test_session["id"]

        chunks = []
        async with client.stream(
            "POST",
            f"/api/v1/sessions/{session_id}/chat",
            json={"content": "Tell me a short story", "stream": True}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    chunks.append(line[5:].strip())

        # 驗證收到多個 chunks
        assert len(chunks) > 1

        # 驗證最後一個是 done 事件
        import json
        last_event = json.loads(chunks[-1])
        assert last_event.get("type") == "done"

    @pytest.mark.e2e
    async def test_concurrent_sessions(
        self,
        client: AsyncClient,
        test_agent
    ):
        """測試並發 Session"""
        # 創建 5 個 Session
        sessions = []
        for i in range(5):
            response = await client.post("/api/v1/sessions", json={
                "agent_id": str(test_agent.id),
                "title": f"Concurrent Test {i}"
            })
            session = response.json()
            await client.post(f"/api/v1/sessions/{session['id']}/activate")
            sessions.append(session)

        # 並發發送訊息
        async def send_message(session_id: str, content: str):
            return await client.post(
                f"/api/v1/sessions/{session_id}/chat",
                json={"content": content, "stream": False}
            )

        tasks = [
            send_message(s["id"], f"Hello from session {i}")
            for i, s in enumerate(sessions)
        ]

        responses = await asyncio.gather(*tasks)

        # 驗證所有回應成功
        for response in responses:
            assert response.status_code == 200
            assert response.json()["content"]
```

**依賴**:
- pytest-asyncio
- httpx AsyncClient
- 完整的 Session-Agent 整合

---

### S47-2: 錯誤處理與恢復 (7 pts)

**As a** 系統開發者
**I want** 完善的錯誤處理機制
**So that** 系統可優雅處理各種錯誤情況

**驗收標準**:
- [ ] LLM 調用錯誤處理
- [ ] 工具執行錯誤處理
- [ ] WebSocket 斷線恢復
- [ ] Session 狀態恢復
- [ ] 錯誤日誌記錄

**技術設計**:

```python
# backend/src/domain/sessions/error_handler.py

from typing import Optional, Dict, Any
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SessionErrorCode(Enum):
    """Session 錯誤碼"""
    # Session 相關
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SESSION_NOT_ACTIVE = "SESSION_NOT_ACTIVE"
    SESSION_EXPIRED = "SESSION_EXPIRED"

    # Agent 相關
    AGENT_NOT_FOUND = "AGENT_NOT_FOUND"
    AGENT_CONFIG_ERROR = "AGENT_CONFIG_ERROR"

    # LLM 相關
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_RATE_LIMIT = "LLM_RATE_LIMIT"
    LLM_API_ERROR = "LLM_API_ERROR"
    LLM_CONTENT_FILTER = "LLM_CONTENT_FILTER"

    # 工具相關
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    TOOL_EXECUTION_ERROR = "TOOL_EXECUTION_ERROR"
    TOOL_TIMEOUT = "TOOL_TIMEOUT"
    TOOL_PERMISSION_DENIED = "TOOL_PERMISSION_DENIED"

    # 系統相關
    INTERNAL_ERROR = "INTERNAL_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"


class SessionError(Exception):
    """Session 錯誤基類"""

    def __init__(
        self,
        code: SessionErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.recoverable = recoverable
        self.timestamp = datetime.utcnow()
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.code.value,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
            "timestamp": self.timestamp.isoformat()
        }

    def to_event(self) -> ExecutionEvent:
        return ExecutionEvent(
            type=ExecutionEventType.ERROR,
            data=self.to_dict()
        )


class SessionErrorHandler:
    """Session 錯誤處理器"""

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    async def handle_llm_error(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> SessionError:
        """處理 LLM 錯誤"""
        error_str = str(error).lower()

        if "timeout" in error_str:
            return SessionError(
                code=SessionErrorCode.LLM_TIMEOUT,
                message="LLM 回應超時，請稍後重試",
                details={"original_error": str(error)},
                recoverable=True
            )
        elif "rate" in error_str and "limit" in error_str:
            return SessionError(
                code=SessionErrorCode.LLM_RATE_LIMIT,
                message="API 請求過於頻繁，請稍後重試",
                details={"original_error": str(error)},
                recoverable=True
            )
        elif "content_filter" in error_str:
            return SessionError(
                code=SessionErrorCode.LLM_CONTENT_FILTER,
                message="訊息內容被安全過濾器攔截",
                details={"original_error": str(error)},
                recoverable=False
            )
        else:
            return SessionError(
                code=SessionErrorCode.LLM_API_ERROR,
                message="LLM 服務暫時不可用",
                details={"original_error": str(error)},
                recoverable=True
            )

    async def handle_tool_error(
        self,
        error: Exception,
        tool_name: str,
        context: Dict[str, Any]
    ) -> SessionError:
        """處理工具執行錯誤"""
        error_str = str(error).lower()

        if "timeout" in error_str:
            return SessionError(
                code=SessionErrorCode.TOOL_TIMEOUT,
                message=f"工具 {tool_name} 執行超時",
                details={"tool_name": tool_name, "original_error": str(error)},
                recoverable=True
            )
        elif "permission" in error_str or "denied" in error_str:
            return SessionError(
                code=SessionErrorCode.TOOL_PERMISSION_DENIED,
                message=f"無權限執行工具 {tool_name}",
                details={"tool_name": tool_name, "original_error": str(error)},
                recoverable=False
            )
        else:
            return SessionError(
                code=SessionErrorCode.TOOL_EXECUTION_ERROR,
                message=f"工具 {tool_name} 執行失敗",
                details={"tool_name": tool_name, "original_error": str(error)},
                recoverable=True
            )

    async def with_retry(
        self,
        operation,
        error_handler,
        context: Dict[str, Any]
    ):
        """帶重試的操作執行"""
        last_error = None

        for attempt in range(self._max_retries):
            try:
                return await operation()
            except Exception as e:
                last_error = e
                session_error = await error_handler(e, context)

                if not session_error.recoverable:
                    raise session_error

                if attempt < self._max_retries - 1:
                    logger.warning(
                        f"Operation failed (attempt {attempt + 1}), retrying...",
                        extra={"error": str(e), "context": context}
                    )
                    await asyncio.sleep(self._retry_delay * (attempt + 1))

        # 所有重試失敗
        raise await error_handler(last_error, context)


class SessionRecoveryManager:
    """Session 恢復管理器"""

    def __init__(
        self,
        session_service: SessionService,
        cache: RedisCache
    ):
        self._sessions = session_service
        self._cache = cache

    async def save_checkpoint(
        self,
        session_id: str,
        state: Dict[str, Any]
    ):
        """保存 Session 檢查點"""
        await self._cache.set(
            f"session_checkpoint:{session_id}",
            {
                "state": state,
                "timestamp": datetime.utcnow().isoformat()
            },
            ttl=3600  # 1 小時
        )

    async def restore_from_checkpoint(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """從檢查點恢復"""
        checkpoint = await self._cache.get(f"session_checkpoint:{session_id}")
        if checkpoint:
            return checkpoint["state"]
        return None

    async def handle_websocket_reconnect(
        self,
        session_id: str,
        last_event_id: Optional[str] = None
    ) -> List[ExecutionEvent]:
        """處理 WebSocket 重連"""
        # 獲取斷線後的事件
        events = []

        # 檢查是否有進行中的操作
        pending_state = await self.restore_from_checkpoint(session_id)
        if pending_state:
            events.append(ExecutionEvent(
                type=ExecutionEventType.CONTENT,
                data={"status": "reconnected", "pending_state": pending_state}
            ))

        return events
```

**依賴**:
- logging module
- RedisCache

---

### S47-3: 效能優化與監控 (5 pts)

**As a** 運維工程師
**I want** 效能監控指標
**So that** 可追蹤系統健康狀況

**驗收標準**:
- [ ] 回應時間監控
- [ ] Token 使用量追蹤
- [ ] 並發連接數監控
- [ ] 錯誤率統計
- [ ] Prometheus 指標暴露

**技術設計**:

```python
# backend/src/domain/sessions/metrics.py

from prometheus_client import Counter, Histogram, Gauge
from functools import wraps
import time

# Counters
session_messages_total = Counter(
    'session_messages_total',
    'Total session messages processed',
    ['session_id', 'message_type', 'status']
)

session_tool_calls_total = Counter(
    'session_tool_calls_total',
    'Total tool calls executed',
    ['tool_name', 'status']
)

session_errors_total = Counter(
    'session_errors_total',
    'Total session errors',
    ['error_code']
)

# Histograms
session_response_time = Histogram(
    'session_response_time_seconds',
    'Session response time in seconds',
    ['operation'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

session_token_usage = Histogram(
    'session_token_usage',
    'Token usage per request',
    ['type'],  # input, output, total
    buckets=[100, 500, 1000, 2000, 4000, 8000]
)

# Gauges
active_sessions = Gauge(
    'active_sessions',
    'Number of active sessions'
)

active_websocket_connections = Gauge(
    'active_websocket_connections',
    'Number of active WebSocket connections'
)


class MetricsCollector:
    """指標收集器"""

    @staticmethod
    def track_message(session_id: str, message_type: str, status: str):
        """追蹤訊息"""
        session_messages_total.labels(
            session_id=session_id,
            message_type=message_type,
            status=status
        ).inc()

    @staticmethod
    def track_tool_call(tool_name: str, status: str):
        """追蹤工具調用"""
        session_tool_calls_total.labels(
            tool_name=tool_name,
            status=status
        ).inc()

    @staticmethod
    def track_error(error_code: str):
        """追蹤錯誤"""
        session_errors_total.labels(error_code=error_code).inc()

    @staticmethod
    def track_response_time(operation: str, duration: float):
        """追蹤回應時間"""
        session_response_time.labels(operation=operation).observe(duration)

    @staticmethod
    def track_tokens(input_tokens: int, output_tokens: int):
        """追蹤 Token 使用量"""
        session_token_usage.labels(type="input").observe(input_tokens)
        session_token_usage.labels(type="output").observe(output_tokens)
        session_token_usage.labels(type="total").observe(input_tokens + output_tokens)

    @staticmethod
    def set_active_sessions(count: int):
        """設定活躍 Session 數"""
        active_sessions.set(count)

    @staticmethod
    def set_active_connections(count: int):
        """設定活躍連接數"""
        active_websocket_connections.set(count)


def track_time(operation: str):
    """追蹤執行時間的裝飾器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                MetricsCollector.track_response_time(operation, duration)
        return wrapper
    return decorator
```

**依賴**:
- prometheus_client

---

### S47-4: API 文檔與使用指南 (5 pts)

**As a** API 使用者
**I want** 完整的 API 文檔
**So that** 可正確使用 Session-Agent 功能

**驗收標準**:
- [ ] OpenAPI 規格更新
- [ ] WebSocket 協議文檔
- [ ] 使用範例
- [ ] 錯誤碼說明
- [ ] 最佳實踐指南

**文檔結構**:

```markdown
# Session-Agent Integration API 文檔

## 概述

Session-Agent Integration 提供基於 Session 的 Agent 對話能力，
支援 REST API 和 WebSocket 兩種通訊方式。

## API 端點

### REST API

#### POST /api/v1/sessions/{session_id}/chat
發送訊息並獲取 Agent 回應。

**請求**:
```json
{
  "content": "Hello, how are you?",
  "attachments": [],
  "stream": true
}
```

**回應 (stream=false)**:
```json
{
  "message_id": "uuid",
  "content": "I'm doing well, thank you!",
  "tool_calls": null
}
```

**回應 (stream=true)**:
```
event: content
data: {"data": "I'm"}

event: content
data: {"data": " doing"}

event: content
data: {"data": " well"}

event: done
data: {"content": "I'm doing well, thank you!"}
```

### WebSocket API

#### WS /api/v1/sessions/{session_id}/ws

**連接流程**:
1. 建立 WebSocket 連接
2. 接收 `connected` 確認
3. 發送訊息
4. 接收串流回應

**訊息類型**:

| 類型 | 方向 | 說明 |
|------|------|------|
| message | Client→Server | 用戶訊息 |
| approval | Client→Server | 工具審批 |
| heartbeat | Bidirectional | 心跳 |
| connected | Server→Client | 連接確認 |
| execution_event | Server→Client | 執行事件 |

## 錯誤碼

| 錯誤碼 | 說明 | 可恢復 |
|--------|------|--------|
| SESSION_NOT_FOUND | Session 不存在 | 否 |
| SESSION_NOT_ACTIVE | Session 未啟動 | 是 |
| LLM_TIMEOUT | LLM 回應超時 | 是 |
| LLM_RATE_LIMIT | API 頻率限制 | 是 |
| TOOL_EXECUTION_ERROR | 工具執行錯誤 | 是 |

## 最佳實踐

1. **使用串流**: 對於長回應，使用 stream=true 提供更好的用戶體驗
2. **心跳保活**: WebSocket 連接建議每 30 秒發送心跳
3. **錯誤重試**: 對於可恢復錯誤，建議使用指數退避重試
4. **Session 管理**: 不使用時及時結束 Session 釋放資源
```

**依賴**:
- OpenAPI 3.0
- Markdown 文檔

---

## 測試計劃總覽

### 測試類型分佈

| 類型 | 數量 | 覆蓋率目標 |
|------|------|-----------|
| 單元測試 | ~50 | 85% |
| 整合測試 | ~20 | 80% |
| E2E 測試 | ~15 | 關鍵路徑 |
| 效能測試 | ~5 | 基準確立 |

### 測試執行

```bash
# 單元測試
pytest tests/unit/domain/sessions/ -v --cov

# 整合測試
pytest tests/integration/ -v

# E2E 測試
pytest tests/e2e/ -v --e2e

# 效能測試
pytest tests/performance/ -v --benchmark
```

---

## 完成標準

- [ ] 所有 Story 完成並通過驗收
- [ ] E2E 測試全部通過
- [ ] 錯誤處理覆蓋所有已知情況
- [ ] 效能指標滿足要求
- [ ] API 文檔完整準確
- [ ] Phase 11 整體驗收通過

---

## Phase 11 總結

### 交付物清單

| 組件 | Sprint | 狀態 |
|------|--------|------|
| AgentExecutor | 45 | - |
| StreamingLLMHandler | 45 | - |
| ToolCallHandler | 45 | - |
| ExecutionEvent | 45 | - |
| SessionAgentBridge | 46 | - |
| WebSocket Handler | 46 | - |
| REST Chat API | 46 | - |
| ToolApprovalManager | 46 | - |
| E2E Tests | 47 | - |
| Error Handling | 47 | - |
| Metrics | 47 | - |
| Documentation | 47 | - |

### 效能指標

| 指標 | 目標值 |
|------|--------|
| 首 Token 延遲 | < 2秒 |
| 串流回應延遲 | < 100ms/chunk |
| WebSocket 延遲 | < 50ms |
| 並發 Session | > 100 |
| 測試覆蓋率 | > 85% |

---

**創建日期**: 2025-12-23
**預計完成**: Sprint 47 結束 (Phase 11 完成)
