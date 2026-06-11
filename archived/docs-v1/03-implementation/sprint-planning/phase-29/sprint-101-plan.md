# Sprint 101: Swarm 事件系統 + SSE 整合

## 概述

Sprint 101 專注於建立 Agent Swarm 的事件發送系統，並與現有的 AG-UI SSE 基礎設施整合，實現實時的 Swarm 狀態推送。

## 目標

1. 實現 SwarmEventEmitter 事件發送器
2. 定義 Swarm 相關的 CustomEvent 類型
3. 整合 HybridEventBridge
4. 實現事件節流和批量發送

## Story Points: 25 點

## 前置條件

- ✅ Sprint 100 完成 (Swarm 數據模型 + API)
- ✅ AG-UI CustomEvent 系統就緒
- ✅ HybridEventBridge 就緒

## 任務分解

### Story 101-1: 定義 Swarm 事件類型 (3h, P0)

**目標**: 定義所有 Swarm 相關的 SSE 事件類型

**交付物**:
- `backend/src/integrations/swarm/events/types.py`

**事件類型定義**:

```python
# types.py
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

# ==================== Swarm 生命週期事件 ====================

@dataclass
class SwarmCreatedPayload:
    """Swarm 創建事件 payload"""
    swarm_id: str
    session_id: str
    mode: str  # sequential, parallel, pipeline, hybrid
    workers: List[Dict[str, str]]  # [{worker_id, worker_name, worker_type, role}]
    created_at: str

@dataclass
class SwarmStatusUpdatePayload:
    """Swarm 狀態更新事件 payload (完整狀態)"""
    swarm_id: str
    session_id: str
    mode: str
    status: str
    total_workers: int
    overall_progress: int
    workers: List[Dict]  # WorkerSummary list
    metadata: Dict[str, Any]

@dataclass
class SwarmCompletedPayload:
    """Swarm 完成事件 payload"""
    swarm_id: str
    status: str  # completed, failed
    summary: Optional[str]
    total_duration_ms: int
    completed_at: str

# ==================== Worker 事件 ====================

@dataclass
class WorkerStartedPayload:
    """Worker 啟動事件 payload"""
    swarm_id: str
    worker_id: str
    worker_name: str
    worker_type: str
    role: str
    task_description: str
    started_at: str

@dataclass
class WorkerProgressPayload:
    """Worker 進度更新事件 payload"""
    swarm_id: str
    worker_id: str
    progress: int  # 0-100
    current_action: Optional[str]  # "Read Todo", "Think", "Search"...
    status: str
    updated_at: str

@dataclass
class WorkerThinkingPayload:
    """Worker 思考過程事件 payload"""
    swarm_id: str
    worker_id: str
    thinking_content: str
    token_count: Optional[int]
    timestamp: str

@dataclass
class WorkerToolCallPayload:
    """Worker 工具調用事件 payload"""
    swarm_id: str
    worker_id: str
    tool_call_id: str
    tool_name: str
    status: str  # pending, running, completed, failed
    input_args: Dict[str, Any]
    output_result: Optional[Dict[str, Any]]
    error: Optional[str]
    duration_ms: Optional[int]
    timestamp: str

@dataclass
class WorkerMessagePayload:
    """Worker 消息事件 payload"""
    swarm_id: str
    worker_id: str
    role: str  # system, user, assistant, tool
    content: str
    tool_call_id: Optional[str]
    timestamp: str

@dataclass
class WorkerCompletedPayload:
    """Worker 完成事件 payload"""
    swarm_id: str
    worker_id: str
    status: str  # completed, failed
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    duration_ms: int
    completed_at: str

# ==================== 事件名稱常量 ====================

class SwarmEventNames:
    SWARM_CREATED = "swarm_created"
    SWARM_STATUS_UPDATE = "swarm_status_update"
    SWARM_COMPLETED = "swarm_completed"

    WORKER_STARTED = "worker_started"
    WORKER_PROGRESS = "worker_progress"
    WORKER_THINKING = "worker_thinking"
    WORKER_TOOL_CALL = "worker_tool_call"
    WORKER_MESSAGE = "worker_message"
    WORKER_COMPLETED = "worker_completed"
```

**驗收標準**:
- [ ] 所有事件類型定義完成
- [ ] 類型註解完整
- [ ] 與 AG-UI CustomEvent 格式兼容
- [ ] 單元測試通過

### Story 101-2: 實現 SwarmEventEmitter (6h, P0)

**目標**: 實現事件發送器，負責將 Swarm 狀態變化轉換為 SSE 事件

**交付物**:
- `backend/src/integrations/swarm/events/__init__.py`
- `backend/src/integrations/swarm/events/emitter.py`

**核心實現**:

```python
# emitter.py
from typing import Callable, Awaitable, Optional
import asyncio
from datetime import datetime
import time

from integrations.ag_ui.events import CustomEvent
from .types import (
    SwarmEventNames,
    SwarmCreatedPayload,
    WorkerProgressPayload,
    WorkerThinkingPayload,
    WorkerToolCallPayload,
    WorkerCompletedPayload,
    SwarmCompletedPayload,
)

EventCallback = Callable[[CustomEvent], Awaitable[None]]

class SwarmEventEmitter:
    """
    Swarm 事件發送器

    功能:
    1. 將 Swarm 狀態變化轉換為 AG-UI CustomEvent
    2. 事件節流（限制頻率）
    3. 批量發送優化
    """

    def __init__(
        self,
        event_callback: EventCallback,
        throttle_interval_ms: int = 200,  # 最小事件間隔
        batch_size: int = 5,  # 批量發送閾值
    ):
        self._callback = event_callback
        self._throttle_interval = throttle_interval_ms / 1000
        self._batch_size = batch_size

        # 事件節流
        self._last_emit_time: Dict[str, float] = {}
        self._pending_events: Dict[str, CustomEvent] = {}

        # 批量發送
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._batch_task: Optional[asyncio.Task] = None

    async def start(self):
        """啟動批量發送任務"""
        self._batch_task = asyncio.create_task(self._batch_sender())

    async def stop(self):
        """停止批量發送任務"""
        if self._batch_task:
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass

    # ==================== Swarm 事件 ====================

    async def emit_swarm_created(self, swarm: 'AgentSwarmStatus'):
        """發送 Swarm 創建事件"""
        payload = SwarmCreatedPayload(
            swarm_id=swarm.swarm_id,
            session_id=swarm.session_id,
            mode=swarm.mode.value,
            workers=[
                {
                    "worker_id": w.worker_id,
                    "worker_name": w.worker_name,
                    "worker_type": w.worker_type.value,
                    "role": w.role,
                }
                for w in swarm.workers
            ],
            created_at=swarm.created_at.isoformat(),
        )

        event = CustomEvent(
            event_name=SwarmEventNames.SWARM_CREATED,
            payload=payload.__dict__,
        )
        await self._emit(event, priority=True)

    async def emit_swarm_status_update(self, swarm: 'AgentSwarmStatus'):
        """發送 Swarm 狀態更新事件（完整狀態）"""
        payload = SwarmStatusUpdatePayload(
            swarm_id=swarm.swarm_id,
            session_id=swarm.session_id,
            mode=swarm.mode.value,
            status=swarm.status.value,
            total_workers=swarm.total_workers,
            overall_progress=swarm.overall_progress,
            workers=[self._worker_to_summary(w) for w in swarm.workers],
            metadata=swarm.metadata,
        )

        event = CustomEvent(
            event_name=SwarmEventNames.SWARM_STATUS_UPDATE,
            payload=payload.__dict__,
        )
        await self._emit_throttled(event, f"swarm_status_{swarm.swarm_id}")

    async def emit_swarm_completed(self, swarm: 'AgentSwarmStatus'):
        """發送 Swarm 完成事件"""
        duration_ms = 0
        if swarm.started_at and swarm.completed_at:
            duration_ms = int(
                (swarm.completed_at - swarm.started_at).total_seconds() * 1000
            )

        payload = SwarmCompletedPayload(
            swarm_id=swarm.swarm_id,
            status=swarm.status.value,
            summary=swarm.metadata.get("summary"),
            total_duration_ms=duration_ms,
            completed_at=swarm.completed_at.isoformat() if swarm.completed_at else "",
        )

        event = CustomEvent(
            event_name=SwarmEventNames.SWARM_COMPLETED,
            payload=payload.__dict__,
        )
        await self._emit(event, priority=True)

    # ==================== Worker 事件 ====================

    async def emit_worker_started(
        self,
        swarm_id: str,
        worker: 'WorkerExecution',
    ):
        """發送 Worker 啟動事件"""
        payload = WorkerStartedPayload(
            swarm_id=swarm_id,
            worker_id=worker.worker_id,
            worker_name=worker.worker_name,
            worker_type=worker.worker_type.value,
            role=worker.role,
            task_description=worker.task_description,
            started_at=worker.started_at.isoformat() if worker.started_at else "",
        )

        event = CustomEvent(
            event_name=SwarmEventNames.WORKER_STARTED,
            payload=payload.__dict__,
        )
        await self._emit(event, priority=True)

    async def emit_worker_progress(
        self,
        swarm_id: str,
        worker: 'WorkerExecution',
    ):
        """發送 Worker 進度更新事件"""
        payload = WorkerProgressPayload(
            swarm_id=swarm_id,
            worker_id=worker.worker_id,
            progress=worker.progress,
            current_action=worker.current_action,
            status=worker.status.value,
            updated_at=datetime.utcnow().isoformat(),
        )

        event = CustomEvent(
            event_name=SwarmEventNames.WORKER_PROGRESS,
            payload=payload.__dict__,
        )
        # 進度更新使用節流
        await self._emit_throttled(
            event, f"worker_progress_{swarm_id}_{worker.worker_id}"
        )

    async def emit_worker_thinking(
        self,
        swarm_id: str,
        worker: 'WorkerExecution',
    ):
        """發送 Worker 思考過程事件"""
        if not worker.thinking_history:
            return

        latest_thinking = worker.thinking_history[-1]
        payload = WorkerThinkingPayload(
            swarm_id=swarm_id,
            worker_id=worker.worker_id,
            thinking_content=latest_thinking.content,
            token_count=latest_thinking.token_count,
            timestamp=latest_thinking.timestamp.isoformat(),
        )

        event = CustomEvent(
            event_name=SwarmEventNames.WORKER_THINKING,
            payload=payload.__dict__,
        )
        # 思考事件使用節流
        await self._emit_throttled(
            event, f"worker_thinking_{swarm_id}_{worker.worker_id}"
        )

    async def emit_worker_tool_call(
        self,
        swarm_id: str,
        worker: 'WorkerExecution',
        tool_call: 'ToolCallInfo',
    ):
        """發送 Worker 工具調用事件"""
        duration_ms = None
        if tool_call.started_at and tool_call.completed_at:
            duration_ms = int(
                (tool_call.completed_at - tool_call.started_at).total_seconds() * 1000
            )

        payload = WorkerToolCallPayload(
            swarm_id=swarm_id,
            worker_id=worker.worker_id,
            tool_call_id=tool_call.tool_call_id,
            tool_name=tool_call.tool_name,
            status=tool_call.status,
            input_args=tool_call.input_args,
            output_result=tool_call.output_result,
            error=tool_call.error,
            duration_ms=duration_ms,
            timestamp=datetime.utcnow().isoformat(),
        )

        event = CustomEvent(
            event_name=SwarmEventNames.WORKER_TOOL_CALL,
            payload=payload.__dict__,
        )
        await self._emit(event, priority=True)

    async def emit_worker_completed(
        self,
        swarm_id: str,
        worker: 'WorkerExecution',
    ):
        """發送 Worker 完成事件"""
        duration_ms = 0
        if worker.started_at and worker.completed_at:
            duration_ms = int(
                (worker.completed_at - worker.started_at).total_seconds() * 1000
            )

        payload = WorkerCompletedPayload(
            swarm_id=swarm_id,
            worker_id=worker.worker_id,
            status=worker.status.value,
            result=worker.result,
            error=worker.error,
            duration_ms=duration_ms,
            completed_at=worker.completed_at.isoformat() if worker.completed_at else "",
        )

        event = CustomEvent(
            event_name=SwarmEventNames.WORKER_COMPLETED,
            payload=payload.__dict__,
        )
        await self._emit(event, priority=True)

    # ==================== 內部方法 ====================

    async def _emit(self, event: CustomEvent, priority: bool = False):
        """發送事件"""
        if priority:
            # 優先級事件直接發送
            await self._callback(event)
        else:
            # 普通事件加入隊列
            await self._event_queue.put(event)

    async def _emit_throttled(self, event: CustomEvent, key: str):
        """節流發送事件"""
        now = time.time()
        last_time = self._last_emit_time.get(key, 0)

        if now - last_time >= self._throttle_interval:
            # 超過節流間隔，發送事件
            await self._emit(event)
            self._last_emit_time[key] = now
            # 清除待發送事件
            self._pending_events.pop(key, None)
        else:
            # 未超過間隔，存儲待發送事件
            self._pending_events[key] = event

    async def _batch_sender(self):
        """批量發送任務"""
        while True:
            try:
                events = []
                # 收集事件
                while len(events) < self._batch_size:
                    try:
                        event = await asyncio.wait_for(
                            self._event_queue.get(), timeout=0.1
                        )
                        events.append(event)
                    except asyncio.TimeoutError:
                        break

                # 發送收集的事件
                for event in events:
                    await self._callback(event)

                # 發送待發送的節流事件
                for key, event in list(self._pending_events.items()):
                    await self._callback(event)
                    del self._pending_events[key]

            except asyncio.CancelledError:
                # 發送剩餘事件
                while not self._event_queue.empty():
                    event = self._event_queue.get_nowait()
                    await self._callback(event)
                raise

    def _worker_to_summary(self, worker: 'WorkerExecution') -> Dict:
        """Worker 轉換為摘要格式"""
        return {
            "worker_id": worker.worker_id,
            "worker_name": worker.worker_name,
            "worker_type": worker.worker_type.value,
            "role": worker.role,
            "status": worker.status.value,
            "progress": worker.progress,
            "current_action": worker.current_action,
            "tool_calls_count": len(worker.tool_calls),
        }
```

**驗收標準**:
- [ ] SwarmEventEmitter 類實現完成
- [ ] 所有事件發送方法實現
- [ ] 事件節流正常工作
- [ ] 批量發送正常工作
- [ ] 單元測試通過

### Story 101-3: 整合 HybridEventBridge (5h, P0)

**目標**: 將 SwarmEventEmitter 整合到 HybridEventBridge 中

**交付物**:
- 修改 `backend/src/integrations/ag_ui/bridge.py`

**整合實現**:

```python
# 在 HybridEventBridge 中添加 Swarm 支持

class HybridEventBridge:
    def __init__(
        self,
        # ... 現有參數
        enable_swarm_events: bool = True,
    ):
        # ... 現有初始化
        self._enable_swarm_events = enable_swarm_events
        self._swarm_emitter: Optional[SwarmEventEmitter] = None

    def configure_swarm_emitter(
        self,
        throttle_interval_ms: int = 200,
        batch_size: int = 5,
    ):
        """配置 Swarm 事件發送器"""
        if self._enable_swarm_events:
            self._swarm_emitter = SwarmEventEmitter(
                event_callback=self._send_event,
                throttle_interval_ms=throttle_interval_ms,
                batch_size=batch_size,
            )

    @property
    def swarm_emitter(self) -> Optional[SwarmEventEmitter]:
        """獲取 Swarm 事件發送器"""
        return self._swarm_emitter

    async def start(self):
        """啟動 Bridge"""
        if self._swarm_emitter:
            await self._swarm_emitter.start()

    async def stop(self):
        """停止 Bridge"""
        if self._swarm_emitter:
            await self._swarm_emitter.stop()
```

**驗收標準**:
- [ ] HybridEventBridge 整合完成
- [ ] SwarmEventEmitter 正確初始化
- [ ] 生命週期管理正確
- [ ] 不影響現有功能
- [ ] 整合測試通過

### Story 101-4: 前端 SSE 事件處理 Hook (5h, P0)

**目標**: 實現前端處理 Swarm 事件的 React Hook

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/hooks/useSwarmEvents.ts`

**核心實現**:

```typescript
// useSwarmEvents.ts
import { useCallback, useEffect, useRef } from 'react';
import { AgentSwarmStatus, WorkerExecution } from '../types';

interface SwarmEventHandlers {
  onSwarmCreated?: (payload: SwarmCreatedPayload) => void;
  onSwarmStatusUpdate?: (payload: AgentSwarmStatus) => void;
  onSwarmCompleted?: (payload: SwarmCompletedPayload) => void;
  onWorkerStarted?: (payload: WorkerStartedPayload) => void;
  onWorkerProgress?: (payload: WorkerProgressPayload) => void;
  onWorkerThinking?: (payload: WorkerThinkingPayload) => void;
  onWorkerToolCall?: (payload: WorkerToolCallPayload) => void;
  onWorkerCompleted?: (payload: WorkerCompletedPayload) => void;
}

export function useSwarmEvents(
  eventSource: EventSource | null,
  handlers: SwarmEventHandlers,
) {
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers;

  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data);

      // 只處理 CUSTOM 類型的 Swarm 事件
      if (data.type !== 'CUSTOM') return;

      const { event_name, payload } = data;

      switch (event_name) {
        case 'swarm_created':
          handlersRef.current.onSwarmCreated?.(payload);
          break;
        case 'swarm_status_update':
          handlersRef.current.onSwarmStatusUpdate?.(payload);
          break;
        case 'swarm_completed':
          handlersRef.current.onSwarmCompleted?.(payload);
          break;
        case 'worker_started':
          handlersRef.current.onWorkerStarted?.(payload);
          break;
        case 'worker_progress':
          handlersRef.current.onWorkerProgress?.(payload);
          break;
        case 'worker_thinking':
          handlersRef.current.onWorkerThinking?.(payload);
          break;
        case 'worker_tool_call':
          handlersRef.current.onWorkerToolCall?.(payload);
          break;
        case 'worker_completed':
          handlersRef.current.onWorkerCompleted?.(payload);
          break;
      }
    } catch (error) {
      console.error('Failed to parse swarm event:', error);
    }
  }, []);

  useEffect(() => {
    if (!eventSource) return;

    eventSource.addEventListener('message', handleMessage);

    return () => {
      eventSource.removeEventListener('message', handleMessage);
    };
  }, [eventSource, handleMessage]);
}
```

**驗收標準**:
- [ ] useSwarmEvents Hook 實現完成
- [ ] 所有事件類型處理
- [ ] TypeScript 類型定義完整
- [ ] 錯誤處理正確
- [ ] 單元測試通過

### Story 101-5: 單元測試與整合測試 (4h, P0)

**目標**: 為事件系統編寫完整測試

**交付物**:
- `backend/tests/unit/swarm/test_event_types.py`
- `backend/tests/unit/swarm/test_emitter.py`
- `backend/tests/integration/swarm/test_bridge_integration.py`
- `frontend/src/components/unified-chat/agent-swarm/hooks/__tests__/useSwarmEvents.test.ts`

**測試案例**:

1. **事件類型測試**:
   - [ ] Payload 序列化測試
   - [ ] 類型驗證測試

2. **SwarmEventEmitter 測試**:
   - [ ] 各類事件發送測試
   - [ ] 節流功能測試
   - [ ] 批量發送測試

3. **Bridge 整合測試**:
   - [ ] 完整事件流測試
   - [ ] 生命週期測試

4. **前端 Hook 測試**:
   - [ ] 事件接收測試
   - [ ] Handler 調用測試

**驗收標準**:
- [ ] 單元測試覆蓋率 > 90%
- [ ] 所有測試通過
- [ ] 前後端事件格式一致

### Story 101-6: 性能測試與優化 (2h, P1)

**目標**: 確保事件系統性能符合要求

**交付物**:
- `backend/tests/performance/swarm/test_event_performance.py`

**性能指標**:
- 事件延遲: < 100ms
- 事件吞吐量: > 50 events/sec
- 內存使用: < 10MB (1000 events)

**驗收標準**:
- [ ] 性能測試通過
- [ ] 延遲 < 100ms
- [ ] 吞吐量 > 50 events/sec

## 技術設計

### 事件流架構

```
ClaudeCoordinator
        │
        ▼
  SwarmIntegration
        │
        ▼
  SwarmTracker ─────────────────────┐
        │                           │
        ▼                           ▼
  SwarmEventEmitter           SwarmTracker.get_swarm()
        │                           │
        │ (event_callback)          │ (API)
        ▼                           ▼
  HybridEventBridge ──────► SSE Response ◄─── REST API
        │
        │ (SSE)
        ▼
  React Frontend
        │
        ▼
  useSwarmEvents Hook
        │
        ├─► AgentSwarmPanel
        ├─► WorkerCard
        └─► WorkerDetailDrawer
```

### 事件節流策略

```
進度更新事件:
├─ 間隔 < 200ms: 存儲待發送
├─ 間隔 >= 200ms: 立即發送
└─ 批量發送週期: 每 100ms 檢查

優先級事件 (立即發送):
├─ swarm_created
├─ swarm_completed
├─ worker_started
├─ worker_completed
└─ worker_tool_call
```

## 依賴

- asyncio
- AG-UI CustomEvent

## 風險

| 風險 | 緩解措施 |
|------|---------|
| 事件堆積 | 批量發送 + 節流 |
| 內存洩漏 | 定期清理待發送事件 |
| 網路延遲 | 樂觀更新 + 確認機制 |

## 完成標準

- [ ] 所有 Story 完成
- [ ] 單元測試覆蓋率 > 90%
- [ ] 性能測試通過
- [ ] 代碼審查通過

---

**Sprint 開始**: 2026-02-06
**Sprint 結束**: 2026-02-13
**Story Points**: 25
