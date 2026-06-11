# Sprint 115 Checklist: 三層 Checkpoint + Session Resume

## Sprint 目標

| 項目 | 值 |
|------|-----|
| **總點數** | 12 點 |
| **狀態** | ✅ 完成 |

---

## 開發任務

### S115-1: L1 Conversation State Store (3 SP)
- [x] 新增 `backend/src/infrastructure/storage/conversation_state.py`
- [x] 實作 `ConversationMessage` model（role, content, timestamp, metadata）
- [x] 實作 `ConversationState` model（session_id, messages, routing_decision, approval_status, active_tool_calls）
- [x] 實作 `ConversationStateStore` Redis-backed with 24h TTL
- [x] 實作 `save()` / `load()` / `delete()` / `exists()`
- [x] 實作 `add_message()` — 自動建立新 state 或追加
- [x] 實作 `set_routing_decision()` — 更新路由決策
- [x] 實作 `list_active_sessions()` — 列出所有活躍 session IDs
- [x] 自動 StorageFactory 選擇 Redis（fallback memory）

### S115-2: L3 Execution State Store (3 SP)
- [x] 新增 `backend/src/infrastructure/storage/execution_state.py`
- [x] 實作 `ToolCallRecord` model（tool_name, input_params, output, success, duration_ms）
- [x] 實作 `AgentExecutionState` model（session_id, execution_id, agent_context, tool_calls, intermediate_results, progress）
- [x] 實作 `ExecutionStateStore` PostgreSQL-backed（無 TTL，永久保存）
- [x] 實作 `save()` — 同時建立 session → execution_id 索引
- [x] 實作 `load()` / `load_by_session()` — 按 ID 或 session 查詢
- [x] 實作 `update_progress()` — 更新執行進度
- [x] 實作雙重索引：by execution_id + by session_id

### S115-3: SessionRecoveryManager (3 SP)
- [x] 新增 `backend/src/integrations/hybrid/orchestrator/session_recovery.py`
- [x] 實作 `SessionSummary` model（可恢復 session 摘要）
- [x] 實作 `RecoveryResult` model（含 layers_restored/missing）
- [x] 實作 `list_recoverable_sessions()` — 掃描三層找出有殘留狀態的 sessions
- [x] 實作 `recover_session()` — 依序恢復 L1 → L2 → L3
- [x] 實作 best-effort 策略（任一層缺失不阻止其他層恢復）
- [x] L1: 恢復最近 10 條消息 + routing decision
- [x] L2: 恢復所有相關 tasks（含 pending count）
- [x] L3: 恢復最新 execution state（含 tool call count）

### S115-4: Session Resume API (3 SP)
- [x] 新增 `backend/src/api/v1/orchestrator/session_routes.py`
- [x] 實作 `GET /api/v1/sessions/recoverable` — 列出可恢復 sessions
- [x] 實作 `POST /api/v1/sessions/{session_id}/resume` — 恢復 session 狀態
- [x] 實作 Lazy-init RecoveryManager 自動接線三層 store
- [x] 修改 `backend/src/api/v1/__init__.py` — 註冊 session_resume_router
- [x] 修改 `backend/src/integrations/hybrid/orchestrator/__init__.py` — 匯出 recovery 類

## 驗證標準

- [x] L1 Conversation State Redis 持久化正常（24h TTL）
- [x] L3 Execution State PostgreSQL 永久保存正常
- [x] L2 Task State 複用 Sprint 113 TaskStore 正常
- [x] SessionRecoveryManager 三層恢復邏輯完整
- [x] Best-effort 策略：任一層缺失不阻止其他層恢復
- [x] Session Resume API 2 個 endpoints 可用
- [x] 路由註冊 + 模組匯出正確

## 相關連結

- [Phase 37 計劃](./README.md)
- [Sprint 115 Progress](../../sprint-execution/sprint-115/progress.md)
- [Sprint 115 Plan](./sprint-115-plan.md)

---

**Sprint 狀態**: ✅ 完成
**Story Points**: 12
**完成日期**: 2026-03-19
