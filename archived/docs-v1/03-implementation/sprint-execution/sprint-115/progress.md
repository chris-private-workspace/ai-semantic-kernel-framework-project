# Sprint 115 Progress: 三層 Checkpoint + Session Resume

## 狀態概覽

| 項目 | 狀態 |
|------|------|
| **開始日期** | 2026-03-19 |
| **預計結束** | 2026-03-19 |
| **總點數** | 12 點 |
| **完成點數** | 12 點 |
| **進度** | 100% |
| **Phase** | Phase 37 — E2E Assembly B |
| **Branch** | `feature/phase-37-e2e-b` |

## Sprint 目標

1. ✅ L1 Conversation State（Redis, TTL 24h）
2. ✅ L3 Agent Execution State（PostgreSQL, 永久）
3. ✅ SessionRecoveryManager（三層狀態恢復邏輯）
4. ✅ Session Resume API（GET /sessions/recoverable + POST /sessions/{id}/resume）
5. ✅ 路由註冊 + 匯出更新

## User Stories 進度

| Story | 名稱 | 點數 | 狀態 | 完成度 |
|-------|------|------|------|--------|
| S115-1 | L1 Conversation State Store | 3 | ✅ 完成 | 100% |
| S115-2 | L3 Execution State Store | 3 | ✅ 完成 | 100% |
| S115-3 | SessionRecoveryManager | 3 | ✅ 完成 | 100% |
| S115-4 | Session Resume API | 3 | ✅ 完成 | 100% |

## 完成項目詳情

### S115-1: L1 Conversation State Store (3 SP)
- **新增**: `backend/src/infrastructure/storage/conversation_state.py`
  - `ConversationMessage` model: role, content, timestamp, metadata
  - `ConversationState` model: session_id, messages, routing_decision, approval_status, active_tool_calls
  - `ConversationStateStore`: Redis-backed with 24h TTL
    - `save()` / `load()` / `delete()` / `exists()`
    - `add_message()` — 自動建立新 state 或追加
    - `set_routing_decision()` — 更新路由決策
    - `list_active_sessions()` — 列出所有活躍 session IDs
  - 自動 StorageFactory 選擇 Redis（fallback memory）

### S115-2: L3 Execution State Store (3 SP)
- **新增**: `backend/src/infrastructure/storage/execution_state.py`
  - `ToolCallRecord` model: tool_name, input_params, output, success, duration_ms
  - `AgentExecutionState` model: session_id, execution_id, agent_context, tool_calls, intermediate_results, progress
  - `ExecutionStateStore`: PostgreSQL-backed（無 TTL，永久保存）
    - `save()` — 同時建立 session → execution_id 索引
    - `load()` / `load_by_session()` — 按 ID 或 session 查詢
    - `update_progress()` — 更新執行進度
  - 雙重索引：by execution_id + by session_id

### S115-3: SessionRecoveryManager (3 SP)
- **新增**: `backend/src/integrations/hybrid/orchestrator/session_recovery.py`
  - `SessionSummary` model: 可恢復 session 摘要
  - `RecoveryResult` model: 恢復結果（含 layers_restored/missing）
  - `SessionRecoveryManager`:
    - `list_recoverable_sessions()` — 掃描三層找出有殘留狀態的 sessions
    - `recover_session()` — 依序恢復 L1 → L2 → L3，best-effort 策略
    - L1: 恢復最近 10 條消息 + routing decision
    - L2: 恢復所有相關 tasks（含 pending count）
    - L3: 恢復最新 execution state（含 tool call count）

### S115-4: Session Resume API (3 SP)
- **新增**: `backend/src/api/v1/orchestrator/session_routes.py`
  - `GET /api/v1/sessions/recoverable` — 列出可恢復 sessions
  - `POST /api/v1/sessions/{session_id}/resume` — 恢復 session 狀態
  - Lazy-init RecoveryManager 自動接線三層 store
- **修改**: `backend/src/api/v1/__init__.py` — 註冊 session_resume_router
- **修改**: `backend/src/integrations/hybrid/orchestrator/__init__.py` — 匯出 recovery 類

## 三層 Checkpoint 架構

```
┌─────────────────────────────────────────────────┐
│           Three-Layer Checkpoint System          │
├─────────────────────────────────────────────────┤
│                                                  │
│  L1: Conversation State (Redis, TTL 24h)        │
│      ├── Session messages (最近 10 條)           │
│      ├── Routing decision                        │
│      ├── Approval status                         │
│      └── Active tool calls                       │
│                                                  │
│  L2: Task State (PostgreSQL, 永久)              │
│      ├── Task Registry (Sprint 113)              │
│      ├── Task status + progress                  │
│      └── Pending task count                      │
│                                                  │
│  L3: Agent Execution State (PostgreSQL, 永久)   │
│      ├── Agent context snapshot                  │
│      ├── Tool call history                       │
│      └── Intermediate results                    │
│                                                  │
│  SessionRecoveryManager                          │
│      ├── list_recoverable_sessions()             │
│      └── recover_session() → ResumerContext      │
│                                                  │
└─────────────────────────────────────────────────┘
```

## 檔案變更清單

| 操作 | 檔案路徑 |
|------|---------|
| 新增 | `backend/src/infrastructure/storage/conversation_state.py` |
| 新增 | `backend/src/infrastructure/storage/execution_state.py` |
| 新增 | `backend/src/integrations/hybrid/orchestrator/session_recovery.py` |
| 新增 | `backend/src/api/v1/orchestrator/session_routes.py` |
| 修改 | `backend/src/api/v1/__init__.py` |
| 修改 | `backend/src/integrations/hybrid/orchestrator/__init__.py` |

## 架構決策

| 決策 | 理由 |
|------|------|
| L1 用 Redis TTL 24h | 會話消息是瞬態資料，24h 足夠恢復 |
| L3 用 PostgreSQL 無 TTL | 執行歷史需要永久保存供審計分析 |
| Best-effort 恢復策略 | 任一層缺失不阻止其他層恢復 |
| L2 複用 TaskStore | 避免重複建立 task 持久化邏輯 |
| Session 索引在 L3 | 避免額外索引表，用 KV 前綴查找 |

## 相關文檔

- [Phase 37 計劃](../../sprint-planning/phase-37/README.md)
- [Sprint 114 Progress](../sprint-114/progress.md)
