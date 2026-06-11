# Sprint 113 Checklist: 任務分派 Tools + Task Registry

## Sprint 目標

| 項目 | 值 |
|------|-----|
| **總點數** | 12 點 |
| **狀態** | ✅ 完成 |

---

## 開發任務

### S113-1: Task 領域模型 + TaskStore (3 SP)
- [x] 新增 `backend/src/domain/tasks/__init__.py`
- [x] 新增 `backend/src/domain/tasks/models.py`
- [x] 實作 `Task` Pydantic model（task_id, title, description, task_type, status, priority, progress, timestamps）
- [x] 實作 `TaskStatus` enum（PENDING/QUEUED/IN_PROGRESS/WAITING_APPROVAL/COMPLETED/FAILED/CANCELLED）
- [x] 實作 `TaskPriority` enum（CRITICAL/HIGH/NORMAL/LOW）
- [x] 實作 `TaskType` enum（WORKFLOW/CLAUDE_WORKER/SWARM/MANUAL/APPROVAL）
- [x] 實作 `TaskResult` unified result format
- [x] 實作 state transition methods（mark_started/mark_completed/mark_failed/update_progress）
- [x] 新增 `backend/src/domain/tasks/service.py`
- [x] 實作 `TaskService` CRUD（create/get/list/update/delete）
- [x] 實作 `TaskService` state transitions（start/complete/fail/progress）
- [x] 新增 `backend/src/infrastructure/storage/task_store.py`
- [x] 實作 `TaskStore` wrapping StorageBackendABC
- [x] 實作 lazy backend init via StorageFactory

### S113-2: Dispatch Tool handlers (4 SP)
- [x] 新增 `backend/src/integrations/hybrid/orchestrator/dispatch_handlers.py`
- [x] 實作 `handle_create_task` → TaskService.create_task()
- [x] 實作 `handle_update_task_status` → TaskService.update_task()
- [x] 實作 `handle_dispatch_workflow` → MAF WorkflowExecutorAdapter
- [x] 實作 `handle_dispatch_swarm` → SwarmIntegration
- [x] 實作 `handle_dispatch_to_claude` → ClaudeCoordinator
- [x] 實作 `handle_assess_risk` → RiskAssessmentEngine
- [x] 實作 `handle_search_memory` → Mem0Service
- [x] 實作 `handle_request_approval` → HITLController
- [x] 實作 `register_all()` bulk handler registration
- [x] 實作 graceful degradation（ImportError → warning + fallback）

### S113-3: Task CRUD API (3 SP)
- [x] 新增 `backend/src/api/v1/tasks/__init__.py`
- [x] 新增 `backend/src/api/v1/tasks/routes.py`
- [x] 實作 `POST /api/v1/tasks` — 建立任務
- [x] 實作 `GET /api/v1/tasks` — 列出任務（支援過濾）
- [x] 實作 `GET /api/v1/tasks/{task_id}` — 取得任務詳情
- [x] 實作 `PUT /api/v1/tasks/{task_id}` — 更新任務
- [x] 實作 `DELETE /api/v1/tasks/{task_id}` — 刪除任務
- [x] 實作 `POST /api/v1/tasks/{task_id}/start` — 啟動任務
- [x] 實作 `POST /api/v1/tasks/{task_id}/complete` — 完成任務
- [x] 實作 `POST /api/v1/tasks/{task_id}/fail` — 標記失敗
- [x] 實作 `POST /api/v1/tasks/{task_id}/progress` — 更新進度
- [x] 實作 Pydantic schemas（TaskCreateRequest, TaskUpdateRequest, TaskProgressRequest, TaskResponse）

### S113-4: Tool Registry handler 接線 (2 SP)
- [x] 修改 `backend/src/api/v1/orchestrator/routes.py` — 自動建立 TaskStore + TaskService + DispatchHandlers
- [x] 調用 `handlers.register_all()` 接線 6 個 real handlers
- [x] 修改 `backend/src/integrations/hybrid/orchestrator/tools.py` — 新增 `update_task_status` tool
- [x] 修改 `backend/src/integrations/hybrid/orchestrator/__init__.py` — 匯出 DispatchHandlers
- [x] 修改 `backend/src/api/v1/__init__.py` — 註冊 tasks_router

## 驗證標準

- [x] Task 領域模型（Task, TaskStatus, TaskPriority, TaskType）定義完整
- [x] TaskStore 持久化層正常運作（StorageBackendABC）
- [x] TaskService CRUD + 狀態轉換功能完整
- [x] 7 個 dispatch tool handlers 全部實作
- [x] 9 個 Task CRUD API endpoints 可用
- [x] Phase 36 stubs 被 real handlers 取代
- [x] update_task_status tool 新增完成

## 相關連結

- [Phase 37 計劃](./README.md)
- [Sprint 113 Progress](../../sprint-execution/sprint-113/progress.md)
- [Sprint 113 Plan](./sprint-113-plan.md)

---

**Sprint 狀態**: ✅ 完成
**Story Points**: 12
**完成日期**: 2026-03-19
