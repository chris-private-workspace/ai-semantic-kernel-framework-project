# Sprint 115: 三層 Checkpoint + Session Resume

## Sprint 目標

1. L1 Conversation State（Redis, TTL 24h）
2. L3 Agent Execution State（PostgreSQL, 永久）
3. SessionRecoveryManager（三層狀態恢復邏輯）
4. Session Resume API（GET /sessions/recoverable + POST /sessions/{id}/resume）
5. 路由註冊 + 匯出更新

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 37 — E2E Assembly B |
| **Sprint** | 115 |
| **Story Points** | 12 點 |
| **狀態** | ✅ 完成 |

## Sprint 概述

Sprint 115 是 Phase 37 的第三個 Sprint，專注於實現完整的狀態持久化與 Session 恢復機制。包含 L1 Conversation State（Redis-backed, 24h TTL, 自動 StorageFactory 選擇）、L3 Agent Execution State（PostgreSQL-backed, 無 TTL, 雙重索引 by execution_id + by session_id）、SessionRecoveryManager（list_recoverable_sessions + recover_session, best-effort 策略依序恢復 L1 → L2 → L3），以及 Session Resume API endpoints。L2 Task State 複用 Sprint 113 的 TaskStore。

## User Stories

### S115-1: L1 Conversation State Store (3 SP)

**作為** Orchestrator 系統
**我希望** 會話狀態能即時持久化到 Redis
**以便** 短期內的 session 中斷能快速恢復對話上下文

**技術規格**:
- 新增 `backend/src/infrastructure/storage/conversation_state.py`
- `ConversationMessage` model: role, content, timestamp, metadata
- `ConversationState` model: session_id, messages, routing_decision, approval_status, active_tool_calls
- `ConversationStateStore`: Redis-backed with 24h TTL
  - `save()` / `load()` / `delete()` / `exists()`
  - `add_message()` — 自動建立新 state 或追加
  - `set_routing_decision()` — 更新路由決策
  - `list_active_sessions()` — 列出所有活躍 session IDs
- 自動 StorageFactory 選擇 Redis（fallback memory）

### S115-2: L3 Execution State Store (3 SP)

**作為** 系統管理員
**我希望** Agent 執行狀態永久保存
**以便** 長期審計分析與完整的執行歷史追蹤

**技術規格**:
- 新增 `backend/src/infrastructure/storage/execution_state.py`
- `ToolCallRecord` model: tool_name, input_params, output, success, duration_ms
- `AgentExecutionState` model: session_id, execution_id, agent_context, tool_calls, intermediate_results, progress
- `ExecutionStateStore`: PostgreSQL-backed（無 TTL，永久保存）
  - `save()` — 同時建立 session → execution_id 索引
  - `load()` / `load_by_session()` — 按 ID 或 session 查詢
  - `update_progress()` — 更新執行進度
- 雙重索引：by execution_id + by session_id

### S115-3: SessionRecoveryManager (3 SP)

**作為** 平台用戶
**我希望** 中斷的 session 能被自動恢復
**以便** 不需要重新開始整個對話和任務執行流程

**技術規格**:
- 新增 `backend/src/integrations/hybrid/orchestrator/session_recovery.py`
- `SessionSummary` model: 可恢復 session 摘要
- `RecoveryResult` model: 恢復結果（含 layers_restored/missing）
- `SessionRecoveryManager`:
  - `list_recoverable_sessions()` — 掃描三層找出有殘留狀態的 sessions
  - `recover_session()` — 依序恢復 L1 → L2 → L3，best-effort 策略
  - L1: 恢復最近 10 條消息 + routing decision
  - L2: 恢復所有相關 tasks（含 pending count）
  - L3: 恢復最新 execution state（含 tool call count）

### S115-4: Session Resume API (3 SP)

**作為** 前端開發者
**我希望** 有 Session Resume 的 REST API
**以便** 前端能展示可恢復的 sessions 並觸發恢復流程

**技術規格**:
- 新增 `backend/src/api/v1/orchestrator/session_routes.py`
  - `GET /api/v1/sessions/recoverable` — 列出可恢復 sessions
  - `POST /api/v1/sessions/{session_id}/resume` — 恢復 session 狀態
  - Lazy-init RecoveryManager 自動接線三層 store
- 修改 `backend/src/api/v1/__init__.py` — 註冊 session_resume_router
- 修改 `backend/src/integrations/hybrid/orchestrator/__init__.py` — 匯出 recovery 類

## 相關連結

- [Phase 37 計劃](./README.md)
- [Sprint 114 Plan](./sprint-114-plan.md)
- [Sprint 115 Progress](../../sprint-execution/sprint-115/progress.md)
- [Sprint 116 Plan](./sprint-116-plan.md)

---

**Sprint 狀態**: ✅ 完成
**Story Points**: 12
**完成日期**: 2026-03-19
