# Sprint 113: 任務分派 Tools + Task Registry

## Sprint 目標

1. Task 領域模型（Task, TaskStatus, TaskPriority, TaskType, TaskResult）
2. TaskStore（StorageBackendABC 持久化）
3. TaskService（CRUD + 狀態轉換）
4. DispatchHandlers（6 個 tool handler 實作）
5. Task CRUD API（9 個 REST endpoints）
6. Tool Registry handler 接線（Phase 36 stubs → real handlers）
7. update_task_status tool 新增

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 37 — E2E Assembly B |
| **Sprint** | 113 |
| **Story Points** | 12 點 |
| **狀態** | ✅ 完成 |

## Sprint 概述

Sprint 113 是 Phase 37 的第一個 Sprint，專注於建立 Orchestrator 的任務分派能力與任務追蹤基礎設施。包含 Task 領域模型定義（TaskStatus/TaskPriority/TaskType enums + TaskResult 統一格式）、TaskStore 持久化層（複用 StorageBackendABC）、TaskService CRUD 與狀態轉換、DispatchHandlers 七個 tool handler 實作（create_task / update_task_status / dispatch_workflow / dispatch_swarm / dispatch_to_claude / assess_risk / search_memory / request_approval）、Task CRUD API 九個 REST endpoints，以及將 Phase 36 的 stub responses 替換為 real handler 接線。

## User Stories

### S113-1: Task 領域模型 + TaskStore (3 SP)

**作為** 後端開發者
**我希望** 有完整的 Task 領域模型和持久化層
**以便** 統一管理任務的生命週期與狀態轉換

**技術規格**:
- 新增 `backend/src/domain/tasks/__init__.py`
- 新增 `backend/src/domain/tasks/models.py`
  - `Task` Pydantic model: task_id, title, description, task_type, status, priority, progress, timestamps
  - `TaskStatus` enum: PENDING/QUEUED/IN_PROGRESS/WAITING_APPROVAL/COMPLETED/FAILED/CANCELLED
  - `TaskPriority` enum: CRITICAL/HIGH/NORMAL/LOW
  - `TaskType` enum: WORKFLOW/CLAUDE_WORKER/SWARM/MANUAL/APPROVAL
  - `TaskResult` unified result format
  - State transition methods: mark_started(), mark_completed(), mark_failed(), update_progress()
- 新增 `backend/src/domain/tasks/service.py`
  - `TaskService`: CRUD (create/get/list/update/delete) + state transitions (start/complete/fail/progress)
- 新增 `backend/src/infrastructure/storage/task_store.py`
  - `TaskStore`: Wraps StorageBackendABC with task-specific key prefixing
  - Lazy backend init via StorageFactory (PostgreSQL preferred, memory fallback)

### S113-2: Dispatch Tool handlers (4 SP)

**作為** Orchestrator 系統
**我希望** 擁有完整的 dispatch tool handlers
**以便** 能夠將任務派發給 MAF Workflow / Claude Worker / Swarm 等不同執行引擎

**技術規格**:
- 新增 `backend/src/integrations/hybrid/orchestrator/dispatch_handlers.py`
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

**作為** 前端開發者
**我希望** 有完整的 Task REST API
**以便** 前端能展示任務列表、追蹤進度、管理任務生命週期

**技術規格**:
- 新增 `backend/src/api/v1/tasks/__init__.py`
- 新增 `backend/src/api/v1/tasks/routes.py`
- 9 個 endpoints:
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

**作為** 系統整合工程師
**我希望** Phase 36 的 stub responses 被 real handler 取代
**以便** Orchestrator tool 呼叫能實際觸發對應的業務邏輯

**技術規格**:
- 修改 `backend/src/api/v1/orchestrator/routes.py`
  - `_get_tool_registry()` 自動建立 TaskStore + TaskService + DispatchHandlers
  - 調用 `handlers.register_all()` 將 6 個 real handlers 接線到 tool registry
- 修改 `backend/src/integrations/hybrid/orchestrator/tools.py`
  - 新增 `update_task_status` tool 定義（SYNC, operator role）
- 修改 `backend/src/integrations/hybrid/orchestrator/__init__.py`
  - 匯出 `DispatchHandlers`
- 修改 `backend/src/api/v1/__init__.py`
  - 註冊 `tasks_router` 到 protected_router

## 相關連結

- [Phase 37 計劃](./README.md)
- [Sprint 113 Progress](../../sprint-execution/sprint-113/progress.md)
- [Sprint 114 Plan](./sprint-114-plan.md)

---

**Sprint 狀態**: ✅ 完成
**Story Points**: 12
**完成日期**: 2026-03-19
