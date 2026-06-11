# Sprint 135 Checklist: AG-UI Bridge 遷移 + 即時串流

## Sprint 目標

| 項目 | 值 |
|------|-----|
| **總點數** | 12 點 |
| **狀態** | ✅ 已完成 |

---

## 開發任務

### S135-1: MediatorEventBridge (3 SP)
- [x] 新增 `backend/src/integrations/ag_ui/mediator_bridge.py`
- [x] 實作 `MediatorEventBridge` class — Mediator 事件到 AG-UI 事件轉換
- [x] 實作事件映射: ROUTING_COMPLETE → RunStarted
- [x] 實作事件映射: EXECUTION_STARTED → StepStarted
- [x] 實作事件映射: AGENT_MESSAGE → TextMessageContent
- [x] 實作事件映射: TOOL_CALL → ToolCallStart
- [x] 實作事件映射: TOOL_RESULT → ToolCallEnd
- [x] 實作事件映射: EXECUTION_COMPLETE → RunFinished
- [x] 實作事件映射: ERROR → RunError
- [x] 實作 `async stream_events()` — SSE 事件串流產生器
- [x] 實作 `subscribe(mediator)` — 訂閱 Mediator 事件匯流排
- [x] 修改 `backend/src/integrations/ag_ui/__init__.py` — 匯出 MediatorEventBridge
- [x] 新增 `backend/tests/unit/integrations/ag_ui/test_mediator_bridge.py`
- [x] 測試每個事件映射轉換正確性
- [x] 測試 SSE 串流格式符合 AG-UI Protocol
- [x] 測試訂閱/取消訂閱機制

### S135-2: AG-UI /run endpoint 改用新 Bridge (2 SP)
- [x] 修改 `backend/src/api/v1/ag_ui/routes.py` — 新增 `/api/v1/ag-ui/run-v2` endpoint
- [x] 使用 `MediatorEventBridge` + `OrchestratorBootstrap.build()` 建立管線
- [x] 實作 feature flag `USE_MEDIATOR_BRIDGE` 控制新舊切換
- [x] 保持舊 `/api/v1/ag-ui/run` endpoint 不變（向後相容）
- [x] 修改 `backend/src/api/v1/ag_ui/dependencies.py` — 新增 `get_mediator_bridge()` 依賴注入
- [x] 修改 `backend/src/api/v1/ag_ui/dependencies.py` — 新增 `get_orchestrator()` 依賴注入
- [x] 修改 `backend/src/integrations/ag_ui/bridge.py` — 新增 `create_mediator_bridge()` 工廠方法
- [x] 新增 `backend/tests/unit/api/v1/ag_ui/test_run_v2.py`
- [x] 測試 `/run-v2` endpoint 回傳 SSE 串流
- [x] 測試 feature flag 切換邏輯

### S135-3: 中間事件串流 (3 SP)
- [x] 修改 `backend/src/integrations/hybrid/orchestrator/events.py` — 新增 THINKING_TOKEN 事件類型
- [x] 修改 `backend/src/integrations/hybrid/orchestrator/events.py` — 新增 TOOL_CALL_PROGRESS 事件類型
- [x] 修改 `backend/src/integrations/hybrid/orchestrator/events.py` — 新增 APPROVAL_PENDING 事件類型
- [x] 修改 `backend/src/integrations/hybrid/orchestrator/events.py` — 新增 STEP_PROGRESS 事件類型
- [x] 修改 `backend/src/integrations/hybrid/orchestrator/events.py` — 新增 `MediatorEventData` typed dict
- [x] 修改 `backend/src/integrations/ag_ui/mediator_bridge.py` — 新增 thinking token 映射
- [x] 修改 `backend/src/integrations/ag_ui/mediator_bridge.py` — 新增 tool-call progress 映射
- [x] 修改 `backend/src/integrations/ag_ui/mediator_bridge.py` — 新增 approval pending 映射
- [x] 實作 `format_thinking_delta()` — 格式化 thinking token 為 SSE delta
- [x] 實作 `format_tool_progress()` — 格式化工具調用進度
- [x] 修改/新增 `backend/src/integrations/ag_ui/events/progress.py` — AG-UI progress event models
- [x] 新增 `backend/tests/unit/integrations/ag_ui/test_intermediate_events.py`
- [x] 測試 thinking token 串流格式
- [x] 測試 tool-call progress 事件
- [x] 測試 approval pending 事件

### S135-4: Session-aware SSE (2 SP)
- [x] 新增 `backend/src/integrations/ag_ui/sse_buffer.py`
- [x] 實作 `SSEEventBuffer` class — Redis 事件暫存
- [x] 實作 `buffer_event(session_id, event)` — 儲存事件到 Redis list
- [x] 實作 `replay_from(session_id, last_event_id)` — 從指定 event_id 重播事件
- [x] 實作 `cleanup(session_id)` — 清理過期事件
- [x] 實作遞增 `event_id` 供重連定位
- [x] 設定 TTL 5 分鐘自動過期
- [x] 修改 `backend/src/api/v1/ag_ui/routes.py` — `/run-v2` 支援 `Last-Event-ID` header
- [x] 修改 `backend/src/integrations/ag_ui/mediator_bridge.py` — 整合 SSEEventBuffer
- [x] 新增 `backend/tests/unit/integrations/ag_ui/test_sse_buffer.py`
- [x] 測試事件暫存與重播
- [x] 測試 TTL 過期清理
- [x] 測試斷線重連場景

### S135-5: MemoryManager 接入 ContextHandler (2 SP)
- [x] 修改 `backend/src/integrations/hybrid/orchestrator/handlers/context.py` — 接受 MemoryManager 注入
- [x] 實作 `handle()` 串接 MemoryManager.retrieve() 獲取相關記憶
- [x] 實作記憶注入到 context（對話歷史、知識片段、用戶偏好）
- [x] 實作上下文長度控制不超過 token limit
- [x] 修改 `backend/src/integrations/hybrid/orchestrator/bootstrap.py` — `_wire_context_handler()` 接入 MemoryManager
- [x] 修改 `backend/src/integrations/hybrid/orchestrator/memory_manager.py` — 新增 `retrieve()` 方法
- [x] 新增 `MemoryContext` typed dict（conversation_history, knowledge_fragments, user_preferences）
- [x] 新增 `backend/tests/unit/integrations/hybrid/orchestrator/test_memory_context_wiring.py`
- [x] 測試 MemoryManager → ContextHandler 注入
- [x] 測試記憶自動載入
- [x] 測試上下文長度控制

## 驗證標準

- [x] MediatorEventBridge 能將所有 Mediator 事件正確轉換為 AG-UI 格式
- [x] `/api/v1/ag-ui/run-v2` endpoint 回傳 AG-UI 標準 SSE 串流
- [x] Feature flag 可切換新舊 Bridge，舊 `/run` 不受影響
- [x] Thinking tokens 能即時串流到前端
- [x] Tool-call progress 能顯示工具調用進度
- [x] 用戶斷線重連能透過 `Last-Event-ID` 重播缺失事件
- [x] SSE 事件暫存 TTL 5 分鐘後自動清理
- [x] MemoryManager 自動載入相關記憶到上下文
- [x] 上下文長度控制在 token limit 內
- [x] 所有新增程式碼通過 black / isort / flake8 / mypy 檢查
- [x] 單元測試覆蓋率 >= 80%

## 相關連結

- [Phase 39 計劃](./README.md)
- [Sprint 135 Plan](./sprint-135-plan.md)
- [Sprint 134 Plan](./sprint-134-plan.md)

---

**Sprint 狀態**: ✅ 已完成
**Story Points**: 12
