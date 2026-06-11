# Sprint 145: Orchestrator SSE 串流端點

## Sprint 目標

1. 新增 `POST /orchestrator/chat/stream` SSE 端點，Pipeline 每步即時推送事件
2. 前端 UnifiedChat 改用 SSE 接收（取代同步 POST + typewriter 假串流）
3. MediatorEventBridge 連接 AG-UI 協議事件，統一事件格式

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 42 — E2E Pipeline Deep Integration |
| **Sprint** | 145 |
| **Story Points** | 12 點 |
| **狀態** | 📋 計劃中 |

## User Stories

### S145-1: 後端 SSE 端點 (5 SP)

**作為** 前端應用
**我希望** 透過 SSE 即時接收 Pipeline 每個步驟的事件
**以便** 能即時顯示路由結果、工具調用進度、Agent 思考狀態，而非等待同步回應

**技術規格**:

**改動 1: `backend/src/api/v1/orchestration.py` — 新增 SSE 端點**
- 新增 `POST /orchestrator/chat/stream` 路由
- 使用 FastAPI `StreamingResponse` + `text/event-stream` content type
- 接收 `PipelineRequest`（與同步端點相同格式）
- 回傳 SSE event stream：
  ```
  event: PIPELINE_START
  data: {"session_id": "...", "timestamp": "..."}

  event: ROUTING_COMPLETE
  data: {"intent": "...", "risk_level": "...", "mode": "...", "confidence": 0.95}

  event: AGENT_THINKING
  data: {"agent_id": "...", "status": "thinking"}

  event: TOOL_CALL_START
  data: {"tool_name": "create_task", "params": {...}}

  event: TOOL_CALL_END
  data: {"tool_name": "create_task", "result": {...}, "duration_ms": 150}

  event: TEXT_DELTA
  data: {"delta": "部分回應文字..."}

  event: TASK_DISPATCHED
  data: {"task_id": "...", "mode": "WORKFLOW", "description": "..."}

  event: PIPELINE_COMPLETE
  data: {"content": "完整回應", "metadata": {...}, "processing_time_ms": 1200}
  ```
- 保留原有 `POST /orchestrator/chat` 同步端點作為 fallback

**改動 2: `backend/src/integrations/orchestration/mediator.py` — 事件發射機制**
- 為 Mediator Pipeline 加入 `EventEmitter` 機制
- 每個 Handler 執行前後發射對應事件
- 使用 `asyncio.Queue` 作為事件通道：
  ```python
  class PipelineEventEmitter:
      def __init__(self):
          self.queue: asyncio.Queue[SSEEvent] = asyncio.Queue()

      async def emit(self, event_type: str, data: dict):
          await self.queue.put(SSEEvent(event_type=event_type, data=data))

      async def stream(self) -> AsyncGenerator[str, None]:
          while True:
              event = await self.queue.get()
              yield f"event: {event.event_type}\ndata: {json.dumps(event.data)}\n\n"
              if event.event_type == "PIPELINE_COMPLETE":
                  break
  ```
- Mediator 的 `process()` 方法接受 optional `event_emitter` 參數

**改動 3: `backend/src/integrations/orchestration/models.py` — SSE 事件模型**
- 新增 `SSEEvent` dataclass：`event_type: str, data: dict, timestamp: datetime`
- 新增 `SSEEventType` enum：定義所有事件類型常量
- 事件格式對齊 AG-UI 協議命名慣例

### S145-2: 前端 SSE 接收 (4 SP)

**作為** Chat 使用者
**我希望** 在 Chat 中即時看到 Pipeline 處理進度
**以便** 了解系統正在做什麼（路由中、工具調用中、Agent 思考中），不再是空白等待

**技術規格**:

**改動 1: `frontend/src/hooks/useSSEChat.ts` — 新增 SSE Chat Hook**
- 使用 `fetch` + `ReadableStream` 接收 SSE 事件（非 EventSource，因需 POST）
- 解析 SSE 格式：`event: TYPE\ndata: JSON\n\n`
- 事件分發到對應 handler：
  ```typescript
  const eventHandlers: Record<string, (data: any) => void> = {
    PIPELINE_START: (data) => setStatus('processing'),
    ROUTING_COMPLETE: (data) => updateIntentStatus(data),
    AGENT_THINKING: (data) => setAgentStatus('thinking'),
    TOOL_CALL_START: (data) => addToolCall(data),
    TOOL_CALL_END: (data) => updateToolCall(data),
    TEXT_DELTA: (data) => appendTextDelta(data.delta),
    TASK_DISPATCHED: (data) => addTask(data),
    PIPELINE_COMPLETE: (data) => finalizeResponse(data),
  };
  ```
- 支援連線中斷重試（最多 3 次）

**改動 2: `frontend/src/pages/UnifiedChat.tsx` — 切換到 SSE**
- `handleSend()` 改用 `useSSEChat` hook（取代同步 POST）
- 移除 typewriter 假串流，改用 TEXT_DELTA 真實串流
- ROUTING_COMPLETE 事件即時更新 IntentStatusChip
- TOOL_CALL_START/END 事件即時更新 ToolCallTracker
- TASK_DISPATCHED 事件填充 TaskProgressCard
- 保留同步 POST fallback（SSE 連線失敗時降級）

**改動 3: `frontend/src/api/endpoints/orchestrator.ts` — SSE API 函數**
- 新增 `streamMessage(request: PipelineRequest): ReadableStream` 函數
- 處理 SSE 格式解析
- 錯誤處理：網路斷線、timeout、server error

### S145-3: MediatorEventBridge 連接 AG-UI (3 SP)

**作為** 系統架構
**我希望** Pipeline 事件能映射到 AG-UI 協議事件格式
**以便** 現有 AG-UI 前端組件可以重用，事件格式統一

**技術規格**:

**改動 1: `backend/src/integrations/ag_ui/mediator_bridge.py` — 事件映射**
- 連接 `PipelineEventEmitter` 到 `MediatorEventBridge`
- 定義映射規則：
  | Pipeline Event | AG-UI Event |
  |---|---|
  | ROUTING_COMPLETE | `RunStarted` |
  | AGENT_THINKING | `AgentStateMessage` |
  | TEXT_DELTA | `TextMessageContent` |
  | TOOL_CALL_START | `ToolCallStart` |
  | TOOL_CALL_END | `ToolCallEnd` |
  | PIPELINE_COMPLETE | `RunFinished` |
- 確保 AG-UI 事件 ID 和 thread_id 正確生成

**改動 2: `backend/src/api/v1/ag_ui/routes.py` — 使用新 bridge**
- AG-UI SSE 端點改用 MediatorEventBridge（取代舊的直接呼叫）
- 統一事件來源為 Pipeline

**改動 3: 整合測試**
- 測試 Pipeline 事件 → AG-UI 事件映射正確性
- 測試 SSE 端點回傳正確格式
- 測試連線中斷 + 重連場景

## 驗收標準

- [ ] `POST /orchestrator/chat/stream` 回傳 SSE event stream
- [ ] 至少包含 PIPELINE_START、ROUTING_COMPLETE、TEXT_DELTA、PIPELINE_COMPLETE 四種事件
- [ ] 前端 UnifiedChat 使用 SSE 接收即時事件
- [ ] TEXT_DELTA 事件驅動真實逐 token 串流（非 typewriter 模擬）
- [ ] IntentStatusChip 在 ROUTING_COMPLETE 時即時更新
- [ ] ToolCallTracker 在 TOOL_CALL_START/END 時即時更新
- [ ] 同步 POST fallback 仍可用
- [ ] MediatorEventBridge 正確映射 Pipeline → AG-UI 事件
- [ ] SSE 連線中斷後自動重試（最多 3 次）
- [ ] TypeScript 零錯誤、npm run build 通過
- [ ] `black . && isort . && flake8 .` 通過

## 相關連結

- [Phase 42 計劃](./README.md)
- [Sprint 144 Plan](./sprint-144-plan.md)
- [Sprint 146 Plan](./sprint-146-plan.md)

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 12
