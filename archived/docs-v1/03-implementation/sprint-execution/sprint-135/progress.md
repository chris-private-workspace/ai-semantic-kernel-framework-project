# Sprint 135 Progress: AG-UI Bridge 遷移 + 即時串流

## 狀態概覽

| 項目 | 狀態 |
|------|------|
| **開始日期** | 2026-03-19 |
| **預計結束** | 2026-03-19 |
| **總點數** | 12 點 |
| **完成點數** | 12 點 |
| **進度** | 100% |
| **Phase** | Phase 39 — E2E Assembly D |
| **Branch** | `feature/phase-39-e2e-d` |

## Sprint 目標

1. ✅ MediatorEventBridge（Mediator → AG-UI SSE 事件轉換）
2. ✅ SSEEventBuffer（斷線重連事件暫存）
3. ✅ 中間事件類型新增（THINKING_TOKEN、TOOL_CALL_PROGRESS、STEP_PROGRESS）
4. ✅ MemoryManager 接入 ContextHandler（自動記憶注入）
5. ✅ Bootstrap 更新接線 MemoryManager

## User Stories 進度

| Story | 名稱 | 點數 | 狀態 | 完成度 |
|-------|------|------|------|--------|
| S135-1 | MediatorEventBridge | 3 | ✅ 完成 | 100% |
| S135-2 | AG-UI /run-v2 endpoint 基礎 | 2 | ✅ 完成 | 100% |
| S135-3 | 中間事件串流 | 3 | ✅ 完成 | 100% |
| S135-4 | Session-aware SSE Buffer | 2 | ✅ 完成 | 100% |
| S135-5 | MemoryManager 接入 ContextHandler | 2 | ✅ 完成 | 100% |

## 完成項目詳情

### S135-1: MediatorEventBridge (3 SP)
- **新增**: `backend/src/integrations/ag_ui/mediator_bridge.py`
  - `MediatorEventBridge` class: Mediator 事件 → AG-UI SSE 格式轉換
  - `stream_events()` — 執行 mediator pipeline 並產生 SSE 串流
  - `convert_event()` — 單事件轉換
  - EVENT_MAP: 17 個 mediator event → 10 種 AG-UI event 映射
  - SSE 格式含 event_id 供重連定位

### S135-3: 中間事件串流 (3 SP)
- **修改**: `backend/src/integrations/hybrid/orchestrator/events.py`
  - 新增 3 個 EventType: THINKING_TOKEN、TOOL_CALL_PROGRESS、STEP_PROGRESS
- 文字串流分 chunk 推送（50 字元/chunk + 10ms 延遲）

### S135-4: SSEEventBuffer (2 SP)
- **新增**: `backend/src/integrations/ag_ui/sse_buffer.py`
  - Redis-backed 事件暫存（TTL 5 分鐘，最大 100 事件）
  - `buffer_event()` / `replay_from()` / `cleanup()`
  - In-memory fallback（無 Redis 時）

### S135-5: MemoryManager 接入 ContextHandler (2 SP)
- **修改**: `backend/src/integrations/hybrid/orchestrator/handlers/context.py`
  - `__init__` 新增 `memory_manager` 參數
  - `handle()` 自動調用 `retrieve_relevant_memories()` 注入上下文
  - 記憶寫入 `context["memory_context"]` 和 `context["retrieved_memories"]`
- **修改**: `backend/src/integrations/hybrid/orchestrator/bootstrap.py`
  - `_wire_context_handler()` 建立 OrchestratorMemoryManager 並注入

## 檔案變更清單

| 操作 | 檔案路徑 |
|------|---------|
| 新增 | `backend/src/integrations/ag_ui/mediator_bridge.py` |
| 新增 | `backend/src/integrations/ag_ui/sse_buffer.py` |
| 修改 | `backend/src/integrations/hybrid/orchestrator/events.py` |
| 修改 | `backend/src/integrations/hybrid/orchestrator/handlers/context.py` |
| 修改 | `backend/src/integrations/hybrid/orchestrator/bootstrap.py` |

## 相關文檔

- [Sprint 135 Plan](../../sprint-planning/phase-39/sprint-135-plan.md)
- [Sprint 135 Checklist](../../sprint-planning/phase-39/sprint-135-checklist.md)
- [Sprint 134 Progress](../sprint-134/progress.md)
