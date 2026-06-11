# Sprint 135: AG-UI Bridge 遷移 + 即時串流

## Sprint 目標

1. MediatorEventBridge — 適配 OrchestratorMediator 事件到 AG-UI 事件格式
2. AG-UI `/run` endpoint 改用 MediatorEventBridge
3. 中間事件串流（thinking tokens、tool-call progress）
4. Session-aware SSE 通道（用戶斷開重連不丟事件）
5. MemoryManager 接入 ContextHandler（自動記憶注入）

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 39 — E2E Assembly D |
| **Sprint** | 135 |
| **Story Points** | 12 點 |
| **狀態** | 📋 計劃中 |

## Sprint 概述

Sprint 135 是 Phase 39 的第二個 Sprint，專注於將 AG-UI SSE 串流從舊的 HybridOrchestratorV2 遷移到新的 OrchestratorMediator。包含 MediatorEventBridge 適配層（將 Mediator 內部事件轉換為 AG-UI Protocol 標準事件格式）、AG-UI `/run` endpoint 重新接線到新 Bridge（新舊 Bridge 並存，feature flag 切換）、中間事件串流支援（thinking tokens 即時推送、tool-call progress 進度回報）、Session-aware SSE 通道（支援用戶斷線重連且不丟失事件）、以及 MemoryManager 接入 ContextHandler 實現自動記憶注入（對話歷史和知識自動載入上下文）。

## User Stories

### S135-1: MediatorEventBridge (3 SP)

**作為** 後端開發者
**我希望** 有一個事件橋接層將 Mediator 事件轉換為 AG-UI 事件格式
**以便** 新的 OrchestratorMediator 能無縫接入現有的 AG-UI SSE 串流

**技術規格**:
- 新增 `backend/src/integrations/ag_ui/mediator_bridge.py`
  - `MediatorEventBridge` class: 將 OrchestratorMediator 的內部事件（from `backend/src/integrations/hybrid/orchestrator/events.py`）轉換為 AG-UI 事件格式
  - 事件映射規則:
    - `MediatorEvent.ROUTING_COMPLETE` → `AGUIEvent.RunStarted`
    - `MediatorEvent.EXECUTION_STARTED` → `AGUIEvent.StepStarted`
    - `MediatorEvent.AGENT_MESSAGE` → `AGUIEvent.TextMessageContent`
    - `MediatorEvent.TOOL_CALL` → `AGUIEvent.ToolCallStart`
    - `MediatorEvent.TOOL_RESULT` → `AGUIEvent.ToolCallEnd`
    - `MediatorEvent.EXECUTION_COMPLETE` → `AGUIEvent.RunFinished`
    - `MediatorEvent.ERROR` → `AGUIEvent.RunError`
  - `async def stream_events()` — 產生 AG-UI 格式的 SSE 事件串流
  - `subscribe(mediator)` — 訂閱 OrchestratorMediator 的事件匯流排
- 修改 `backend/src/integrations/ag_ui/__init__.py`
  - 匯出 `MediatorEventBridge`
- 新增 `backend/tests/unit/integrations/ag_ui/test_mediator_bridge.py`
  - 測試每個事件映射轉換
  - 測試 SSE 串流格式正確
  - 測試訂閱/取消訂閱

### S135-2: AG-UI /run endpoint 改用新 Bridge (2 SP)

**作為** 前端開發者
**我希望** AG-UI `/run` endpoint 使用新的 MediatorEventBridge
**以便** 前端能接收來自 OrchestratorMediator 的即時事件串流

**技術規格**:
- 修改 `backend/src/api/v1/ag_ui/routes.py`
  - 新增 `/api/v1/ag-ui/run-v2` endpoint（新 Bridge 入口）
  - 使用 `MediatorEventBridge` + `OrchestratorBootstrap.build()` 建立管線
  - Feature flag `USE_MEDIATOR_BRIDGE=true/false` 控制新舊切換
  - 舊 `/api/v1/ag-ui/run` 保持不變（向後相容）
- 修改 `backend/src/api/v1/ag_ui/dependencies.py`
  - 新增 `get_mediator_bridge()` 依賴注入
  - 新增 `get_orchestrator()` 依賴注入（from Bootstrap）
- 修改 `backend/src/integrations/ag_ui/bridge.py`
  - 新增 `create_mediator_bridge()` 工廠方法
  - 保留原有 `create_bridge()` 不變
- 新增 `backend/tests/unit/api/v1/ag_ui/test_run_v2.py`
  - 測試 `/run-v2` endpoint 回傳 SSE 串流
  - 測試 feature flag 切換邏輯

### S135-3: 中間事件串流 (3 SP)

**作為** 前端使用者
**我希望** 在等待 AI 回應時能看到即時進度
**以便** 了解系統正在做什麼（思考中、調用工具中、等待審批中）

**技術規格**:
- 修改 `backend/src/integrations/ag_ui/mediator_bridge.py`
  - 新增中間事件映射:
    - `MediatorEvent.THINKING_TOKEN` → AG-UI `TextMessageContent` (streaming delta)
    - `MediatorEvent.TOOL_CALL_PROGRESS` → AG-UI `ToolCallStart` + progress metadata
    - `MediatorEvent.APPROVAL_PENDING` → AG-UI custom event `ApprovalRequired`
    - `MediatorEvent.STEP_PROGRESS` → AG-UI `StepProgress` with percentage
  - `format_thinking_delta()` — 格式化 thinking token 為 SSE delta
  - `format_tool_progress()` — 格式化工具調用進度
- 修改 `backend/src/integrations/hybrid/orchestrator/events.py`
  - 新增事件類型: `THINKING_TOKEN`, `TOOL_CALL_PROGRESS`, `APPROVAL_PENDING`, `STEP_PROGRESS`
  - 新增 `MediatorEventData` typed dict 包含 progress metadata
- 新增 `backend/src/integrations/ag_ui/events/progress.py`（若不存在則修改）
  - AG-UI progress event models（ToolCallProgress, ThinkingDelta, ApprovalRequired）
- 新增 `backend/tests/unit/integrations/ag_ui/test_intermediate_events.py`
  - 測試 thinking token 串流格式
  - 測試 tool-call progress 事件
  - 測試 approval pending 事件

### S135-4: Session-aware SSE (2 SP)

**作為** 前端使用者
**我希望** 斷線重連後能接續收到之前錯過的事件
**以便** 不會因為網路中斷而丟失 AI 的回應

**技術規格**:
- 新增 `backend/src/integrations/ag_ui/sse_buffer.py`
  - `SSEEventBuffer` class: 在 Redis 中暫存近期事件（TTL 5 分鐘）
  - `buffer_event(session_id, event)` — 儲存事件到 Redis list
  - `replay_from(session_id, last_event_id)` — 從指定 event_id 重播事件
  - `cleanup(session_id)` — 清理過期事件
  - 每個事件附加遞增 `event_id` 供重連定位
- 修改 `backend/src/api/v1/ag_ui/routes.py`
  - `/run-v2` endpoint 支援 `Last-Event-ID` header
  - 若有 `Last-Event-ID`，先 replay 缺失事件再接續即時串流
- 修改 `backend/src/integrations/ag_ui/mediator_bridge.py`
  - 整合 `SSEEventBuffer`: 每個事件同時推送和暫存
- 新增 `backend/tests/unit/integrations/ag_ui/test_sse_buffer.py`
  - 測試事件暫存與重播
  - 測試 TTL 過期清理
  - 測試斷線重連場景

### S135-5: MemoryManager 接入 ContextHandler (2 SP)

**作為** Orchestrator 系統
**我希望** MemoryManager 自動接入 ContextHandler
**以便** 每次對話時自動載入相關記憶和知識到上下文

**技術規格**:
- 修改 `backend/src/integrations/hybrid/orchestrator/handlers/context.py`
  - `ContextHandler.__init__()` 接受 `memory_manager` 參數
  - `handle()` 方法串接:
    - 調用 `MemoryManager.retrieve()` (from `backend/src/integrations/hybrid/orchestrator/memory_manager.py`) 獲取相關記憶
    - 將記憶注入到 context（對話歷史、知識片段、用戶偏好）
    - 控制上下文長度不超過 token limit
- 修改 `backend/src/integrations/hybrid/orchestrator/bootstrap.py`
  - `_wire_context_handler()` 實作:
    - 建立 `MemoryManager` 實例
    - 將 MemoryManager 注入 ContextHandler
- 修改 `backend/src/integrations/hybrid/orchestrator/memory_manager.py`
  - 新增 `retrieve(session_id, query)` 方法（若不存在）
  - 回傳 `MemoryContext` typed dict（conversation_history, knowledge_fragments, user_preferences）
- 新增 `backend/tests/unit/integrations/hybrid/orchestrator/test_memory_context_wiring.py`
  - 測試 MemoryManager → ContextHandler 注入
  - 測試記憶自動載入
  - 測試上下文長度控制

## 檔案變更清單

### 新增檔案
| 檔案路徑 | 用途 |
|----------|------|
| `backend/src/integrations/ag_ui/mediator_bridge.py` | MediatorEventBridge 事件橋接層 |
| `backend/src/integrations/ag_ui/sse_buffer.py` | Session-aware SSE 事件暫存 |
| `backend/tests/unit/integrations/ag_ui/test_mediator_bridge.py` | 事件橋接測試 |
| `backend/tests/unit/integrations/ag_ui/test_intermediate_events.py` | 中間事件串流測試 |
| `backend/tests/unit/integrations/ag_ui/test_sse_buffer.py` | SSE 暫存與重連測試 |
| `backend/tests/unit/api/v1/ag_ui/test_run_v2.py` | /run-v2 endpoint 測試 |
| `backend/tests/unit/integrations/hybrid/orchestrator/test_memory_context_wiring.py` | Memory → Context 接線測試 |

### 修改檔案
| 檔案路徑 | 修改內容 |
|----------|---------|
| `backend/src/api/v1/ag_ui/routes.py` | 新增 `/run-v2` endpoint + Last-Event-ID 支援 |
| `backend/src/api/v1/ag_ui/dependencies.py` | 新增 get_mediator_bridge() + get_orchestrator() |
| `backend/src/integrations/ag_ui/__init__.py` | 匯出 MediatorEventBridge |
| `backend/src/integrations/ag_ui/bridge.py` | 新增 create_mediator_bridge() 工廠方法 |
| `backend/src/integrations/ag_ui/events/progress.py` | 新增/修改 progress event models |
| `backend/src/integrations/hybrid/orchestrator/events.py` | 新增 THINKING_TOKEN / TOOL_CALL_PROGRESS / APPROVAL_PENDING / STEP_PROGRESS 事件類型 |
| `backend/src/integrations/hybrid/orchestrator/handlers/context.py` | 接受 MemoryManager 注入 + 自動記憶載入 |
| `backend/src/integrations/hybrid/orchestrator/bootstrap.py` | _wire_context_handler() 接入 MemoryManager |
| `backend/src/integrations/hybrid/orchestrator/memory_manager.py` | 新增 retrieve() 方法 + MemoryContext 型別 |
| `backend/src/integrations/ag_ui/mediator_bridge.py` | 整合 SSEEventBuffer |

## 驗收標準

- [ ] MediatorEventBridge 能將所有 Mediator 事件正確轉換為 AG-UI 格式
- [ ] `/api/v1/ag-ui/run-v2` endpoint 回傳 AG-UI 標準 SSE 串流
- [ ] Feature flag 可切換新舊 Bridge，舊 `/run` endpoint 不受影響
- [ ] Thinking tokens 能即時串流到前端
- [ ] Tool-call progress 能顯示工具調用進度
- [ ] 用戶斷線後重連能透過 `Last-Event-ID` 重播缺失事件
- [ ] SSE 事件暫存 TTL 5 分鐘後自動清理
- [ ] MemoryManager 在每次對話時自動載入相關記憶到上下文
- [ ] 上下文長度控制在 token limit 內
- [ ] 所有新增程式碼通過 black / isort / flake8 / mypy 檢查
- [ ] 單元測試覆蓋率 >= 80%

## 相關連結

- [Phase 39 計劃](./README.md)
- [Sprint 134 Plan](./sprint-134-plan.md)
- [Sprint 136 Plan](./sprint-136-plan.md)
- [AG-UI Bridge](../../../../backend/src/integrations/ag_ui/bridge.py)
- [OrchestratorMediator Events](../../../../backend/src/integrations/hybrid/orchestrator/events.py)
- [AG-UI API Reference](../../../../docs/api/ag-ui-api-reference.md)

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 12
