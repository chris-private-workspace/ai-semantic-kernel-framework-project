# Sprint 113 Progress: 任務分派 Tools + Task Registry

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

1. ✅ Task 領域模型（Task, TaskStatus, TaskPriority, TaskType, TaskResult）
2. ✅ TaskStore（StorageBackendABC 持久化）
3. ✅ TaskService（CRUD + 狀態轉換）
4. ✅ DispatchHandlers（6 個 tool handler 實作）
5. ✅ Task CRUD API（9 個 REST endpoints）
6. ✅ Tool Registry handler 接線（Phase 36 stubs → real handlers）
7. ✅ update_task_status tool 新增

## User Stories 進度

| Story | 名稱 | 點數 | 狀態 | 完成度 |
|-------|------|------|------|--------|
| S113-1 | Task 領域模型 + TaskStore | 3 | ✅ 完成 | 100% |
| S113-2 | Dispatch Tool handlers | 4 | ✅ 完成 | 100% |
| S113-3 | Task CRUD API | 3 | ✅ 完成 | 100% |
| S113-4 | Tool Registry handler 接線 | 2 | ✅ 完成 | 100% |

## 完成項目詳情

### S113-1: Task 領域模型 + TaskStore (3 SP)
- **新增**: `backend/src/domain/tasks/__init__.py`
- **新增**: `backend/src/domain/tasks/models.py`
  - `Task` Pydantic model: task_id, title, description, task_type, status, priority, progress, timestamps
  - `TaskStatus` enum: PENDING/QUEUED/IN_PROGRESS/WAITING_APPROVAL/COMPLETED/FAILED/CANCELLED
  - `TaskPriority` enum: CRITICAL/HIGH/NORMAL/LOW
  - `TaskType` enum: WORKFLOW/CLAUDE_WORKER/SWARM/MANUAL/APPROVAL
  - `TaskResult` unified result format
  - State transition methods: mark_started(), mark_completed(), mark_failed(), update_progress()
- **新增**: `backend/src/domain/tasks/service.py`
  - `TaskService`: CRUD (create/get/list/update/delete) + state transitions (start/complete/fail/progress)
- **新增**: `backend/src/infrastructure/storage/task_store.py`
  - `TaskStore`: Wraps StorageBackendABC with task-specific key prefixing
  - Lazy backend init via StorageFactory (PostgreSQL preferred, memory fallback)

### S113-2: Dispatch Tool handlers (4 SP)
- **新增**: `backend/src/integrations/hybrid/orchestrator/dispatch_handlers.py`
  - `DispatchHandlers` class with 7 handler methods:
    - `handle_create_task` → TaskService.create_task()
    - `handle_update_task_status` → TaskService.update_task()
    - `handle_dispatch_workflow` → MAF WorkflowExecutorAdapter
    - `handle_dispatch_swarm` → SwarmIntegration
    - `handle_dispatch_to_claude` → ClaudeCoordinator
    - `handle_assess_risk` → RiskAssessmentEngine
    - `handle_search_memory` → Mem0Service
    - `handle_request_approval` → HITLController
  - `register_all()` helper for bulk handler registration
  - Graceful degradation: ImportError → warning + fallback response

### S113-3: Task CRUD API (3 SP)
- **新增**: `backend/src/api/v1/tasks/__init__.py`
- **新增**: `backend/src/api/v1/tasks/routes.py`
  - 9 endpoints:
    - `POST /api/v1/tasks` — 建立任務
    - `GET /api/v1/tasks` — 列出任務（支援 session_id/user_id/status 過濾）
    - `GET /api/v1/tasks/{task_id}` — 取得任務詳情
    - `PUT /api/v1/tasks/{task_id}` — 更新任務
    - `DELETE /api/v1/tasks/{task_id}` — 刪除任務
    - `POST /api/v1/tasks/{task_id}/start` — 啟動任務
    - `POST /api/v1/tasks/{task_id}/complete` — 完成任務
    - `POST /api/v1/tasks/{task_id}/fail` — 標記失敗
    - `POST /api/v1/tasks/{task_id}/progress` — 更新進度
  - Pydantic schemas: TaskCreateRequest, TaskUpdateRequest, TaskProgressRequest, TaskResponse

### S113-4: Tool Registry handler 接線 (2 SP)
- **修改**: `backend/src/api/v1/orchestrator/routes.py`
  - `_get_tool_registry()` 現在自動建立 TaskStore + TaskService + DispatchHandlers
  - 調用 `handlers.register_all()` 將 6 個 real handlers 接線到 tool registry
  - Phase 36 的 stub responses 被 real handler 取代
- **修改**: `backend/src/integrations/hybrid/orchestrator/tools.py`
  - 新增 `update_task_status` tool 定義（SYNC, operator role）
- **修改**: `backend/src/integrations/hybrid/orchestrator/__init__.py`
  - 匯出 `DispatchHandlers`
- **修改**: `backend/src/api/v1/__init__.py`
  - 註冊 `tasks_router` 到 protected_router

## 檔案變更清單

| 操作 | 檔案路徑 |
|------|---------|
| 新增 | `backend/src/domain/tasks/__init__.py` |
| 新增 | `backend/src/domain/tasks/models.py` |
| 新增 | `backend/src/domain/tasks/service.py` |
| 新增 | `backend/src/infrastructure/storage/task_store.py` |
| 新增 | `backend/src/integrations/hybrid/orchestrator/dispatch_handlers.py` |
| 新增 | `backend/src/api/v1/tasks/__init__.py` |
| 新增 | `backend/src/api/v1/tasks/routes.py` |
| 修改 | `backend/src/integrations/hybrid/orchestrator/tools.py` |
| 修改 | `backend/src/integrations/hybrid/orchestrator/__init__.py` |
| 修改 | `backend/src/api/v1/orchestrator/routes.py` |
| 修改 | `backend/src/api/v1/__init__.py` |

## 架構決策

| 決策 | 理由 |
|------|------|
| Task 獨立領域模型（非複用 SubTask） | SubTask 在 deprecated planning 模組，Task 需要更完整的生命週期 |
| TaskStore 用 StorageBackendABC | 複用 Sprint 110 的統一儲存抽象，自動選擇最佳 backend |
| DispatchHandlers 集中管理 | 單一類別管理所有 tool handlers，方便測試和依賴注入 |
| Lazy import 外部依賴 | 各 handler 用 try/except ImportError 保護，避免啟動失敗 |
| update_task_status 新增為第 7 個 tool | Orchestrator 需要能在對話中更新任務狀態 |

## 相關文檔

- [Phase 37 計劃](../../sprint-planning/phase-37/README.md)
- [Sprint 112 Progress](../sprint-112/progress.md)
