# Sprint 136: 後台任務執行 + ARQ 整合

## Sprint 目標

1. ARQ worker 設置（Redis-backed 非同步任務佇列）
2. dispatch_workflow/swarm 改為 ARQ 提交（脫離 HTTP 請求週期）
3. 任務狀態輪詢 API + SSE 完成推送
4. Session Resume 接通後台任務（恢復執行中的背景任務）

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 39 — E2E Assembly D |
| **Sprint** | 136 |
| **Story Points** | 10 點 |
| **狀態** | 📋 計劃中 |

## Sprint 概述

Sprint 136 是 Phase 39 的第三個 Sprint，專注於將長時間任務從 HTTP 請求週期脫離，改為透過 ARQ（Redis-backed async task queue）在後台 worker 執行。包含 ARQ worker 基礎設施建置、dispatch_workflow/dispatch_swarm 改為 ARQ 任務提交、任務狀態輪詢 API 與 SSE 完成推送，以及 Session Resume 接通後台執行中的任務。解決 Phase 39 核心問題之二：用戶斷開連接不再導致任務中止。

## User Stories

### S136-1: ARQ Worker 設置 (2 SP)

**作為** 平台運維人員
**我希望** 有獨立的 ARQ worker 進程處理後台任務
**以便** 長時間任務不佔用 HTTP 連接，系統可獨立擴展 worker 數量

**技術規格**:
- 新增 `backend/src/infrastructure/workers/__init__.py`
- 新增 `backend/src/infrastructure/workers/arq_worker.py`
  - `WorkerSettings` 類：Redis 連線設定、任務佇列名稱、max_jobs、job_timeout
  - `create_worker_settings()` — 從 app settings 建立 ARQ WorkerSettings
  - 註冊 task functions：`execute_workflow_task`, `execute_swarm_task`
  - Startup/shutdown hooks：初始化 DB 連線池、Redis 連線
- 新增 `backend/src/infrastructure/workers/task_functions.py`
  - `execute_workflow_task(ctx, session_id, workflow_config)` — 呼叫 ExecutionHandler
  - `execute_swarm_task(ctx, session_id, swarm_config)` — 呼叫 SwarmHandler
  - 任務結果寫入 TaskStore（L2 state）
  - 異常處理：捕獲並記錄錯誤，更新任務狀態為 FAILED
- 新增 `backend/arq_worker.py` — worker 啟動入口腳本

### S136-2: dispatch_workflow/swarm 改為 ARQ 提交 (3 SP)

**作為** Orchestrator 系統
**我希望** dispatch_workflow 和 dispatch_swarm 改為提交到 ARQ 佇列
**以便** 任務在獨立 worker 進程執行，HTTP 請求立即返回 task_id

**技術規格**:
- 修改 `backend/src/integrations/hybrid/orchestrator/dispatch_handlers.py`
  - `dispatch_workflow()` — 改為建立 ARQ job，返回 `task_id`
  - `dispatch_swarm()` — 改為建立 ARQ job，返回 `task_id`
  - 新增 `_enqueue_arq_job(func_name, session_id, config)` 輔助方法
  - 保留同步執行 fallback（ARQ 不可用時降級為直接執行）
- 修改 `backend/src/integrations/hybrid/orchestrator/tools.py`
  - `OrchestratorToolRegistry.execute()` 中調用 dispatch 後返回 task_id
  - 更新回傳格式：`{"task_id": "xxx", "status": "queued"}`
- 新增 `backend/src/infrastructure/workers/arq_client.py`
  - `ArqClient` 類：封裝 ARQ job 提交邏輯
  - `enqueue()` — 提交任務到佇列
  - `get_job_result()` — 查詢任務結果
  - `get_job_status()` — 查詢任務狀態
  - 自動連線池管理（Redis connection pool）

### S136-3: 任務狀態輪詢 API + SSE 完成推送 (2 SP)

**作為** 前端開發者
**我希望** 能輪詢任務狀態並在完成時收到 SSE 推送
**以便** 前端即時更新任務進度和結果

**技術規格**:
- 修改 `backend/src/api/v1/tasks/routes.py`
  - `GET /api/v1/tasks/{task_id}/status` — 查詢任務狀態（queued/running/completed/failed）
  - `GET /api/v1/tasks/{task_id}/result` — 取得任務結果（僅 completed 時返回）
  - `GET /api/v1/tasks/{task_id}/stream` — SSE endpoint，任務完成時推送結果
- 新增 `backend/src/infrastructure/workers/task_notifier.py`
  - `TaskNotifier` 類：Redis Pub/Sub 任務完成通知
  - `notify_completion(task_id, result)` — worker 完成時發布通知
  - `subscribe(task_id)` — SSE endpoint 訂閱特定任務完成事件
  - 支援多 SSE client 訂閱同一 task_id

### S136-4: Session Resume 接通後台任務 (3 SP)

**作為** 平台用戶
**我希望** 恢復 session 時能接通仍在後台執行的任務
**以便** 斷線重連後能繼續追蹤任務進度和接收結果

**技術規格**:
- 修改 `backend/src/integrations/hybrid/orchestrator/session_recovery.py`
  - `SessionRecoveryManager.recover_session()` 增加 L4 層：ARQ 任務恢復
  - `_recover_arq_tasks(session_id)` — 查詢 session 關聯的 pending ARQ jobs
  - 返回活躍 task_ids，前端可重新訂閱 SSE stream
- 修改 `backend/src/api/v1/orchestrator/session_routes.py`
  - `POST /api/v1/sessions/{session_id}/resume` 回傳增加 `active_tasks` 欄位
  - 包含仍在執行中的 task_id 列表
- 新增 `backend/src/infrastructure/workers/task_tracker.py`
  - `TaskTracker` 類：session_id ↔ task_id 映射管理
  - `register(session_id, task_id)` — 記錄 session 的活躍任務
  - `get_active_tasks(session_id)` — 查詢 session 的所有活躍任務
  - `mark_completed(task_id)` — 標記任務完成
  - Redis-backed with TTL（匹配 ARQ job 最大生命週期）

## 檔案變更清單

### 新增檔案
| 檔案 | 說明 |
|------|------|
| `backend/src/infrastructure/workers/__init__.py` | Workers 模組初始化 |
| `backend/src/infrastructure/workers/arq_worker.py` | ARQ worker 設定與啟動 |
| `backend/src/infrastructure/workers/task_functions.py` | ARQ 任務函數定義 |
| `backend/src/infrastructure/workers/arq_client.py` | ARQ 客戶端封裝 |
| `backend/src/infrastructure/workers/task_notifier.py` | 任務完成通知（Redis Pub/Sub） |
| `backend/src/infrastructure/workers/task_tracker.py` | Session-Task 映射追蹤 |
| `backend/arq_worker.py` | Worker 啟動入口腳本 |

### 修改檔案
| 檔案 | 說明 |
|------|------|
| `backend/src/integrations/hybrid/orchestrator/dispatch_handlers.py` | dispatch 改為 ARQ 提交 |
| `backend/src/integrations/hybrid/orchestrator/tools.py` | execute() 回傳 task_id |
| `backend/src/api/v1/tasks/routes.py` | 新增狀態輪詢 + SSE endpoints |
| `backend/src/integrations/hybrid/orchestrator/session_recovery.py` | 增加 ARQ 任務恢復層 |
| `backend/src/api/v1/orchestrator/session_routes.py` | resume 回傳增加 active_tasks |

## 驗收標準

- [ ] ARQ worker 可獨立啟動並連線 Redis
- [ ] dispatch_workflow 提交到 ARQ 佇列，HTTP 立即返回 task_id
- [ ] dispatch_swarm 提交到 ARQ 佇列，HTTP 立即返回 task_id
- [ ] ARQ 不可用時自動降級為同步執行
- [ ] `GET /tasks/{task_id}/status` 正確返回任務狀態
- [ ] `GET /tasks/{task_id}/stream` SSE 在任務完成時推送結果
- [ ] Session resume 能返回仍在執行的 active_tasks 列表
- [ ] Worker 異常時任務狀態正確標記為 FAILED
- [ ] TaskTracker 正確維護 session ↔ task 映射

## 相關連結

- [Phase 39 計劃](./README.md)
- [Sprint 135 Plan](./sprint-135-plan.md)
- [Sprint 137 Plan](./sprint-137-plan.md)

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 10
