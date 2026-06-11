# Sprint 139: Task Dashboard + 內聯進度組件

## Sprint 目標

1. Task API + hooks — 建立任務查詢 API client 和 React Query hooks
2. Task Dashboard 頁面 — 任務列表 + 詳情頁（含狀態篩選和進度追蹤）
3. TaskProgressCard 內聯組件 — 在 Chat 訊息中顯示任務進度條和步驟列表
4. 路由 + 導航更新 — 新增任務中心路由和 Sidebar 入口

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 40 — Frontend Enhancement: E2E Workflow UI |
| **Sprint** | 139 |
| **Story Points** | 10 點 |
| **狀態** | 📋 計劃中 |

## Sprint 概述

Sprint 139 是 Phase 40 的第二個 Sprint，專注於建立任務追蹤前端功能。包含 Task API client 和 React Query hooks、Task Dashboard 頁面（任務列表含狀態篩選 + 單一任務詳情頁）、TaskProgressCard 內聯組件（在聊天訊息中顯示 task_id、進度條、步驟列表）、以及 App.tsx 路由和 Sidebar 導航更新。

## User Stories

### S139-1: Task API + hooks (2 SP)

**作為** 前端開發者
**我希望** 有完整的 Task API client 和 React Query hooks
**以便** 任務相關頁面和組件能統一查詢和管理任務資料

**技術規格**:
- 新增 `frontend/src/api/endpoints/tasks.ts`
  - `getTasks(filters)` — GET /tasks（支援 status / priority / agent_id 篩選）
  - `getTask(id)` — GET /tasks/{id}
  - `getTaskSteps(id)` — GET /tasks/{id}/steps
  - `cancelTask(id)` — POST /tasks/{id}/cancel
  - `retryTask(id)` — POST /tasks/{id}/retry
- 新增 `frontend/src/hooks/useTasks.ts`
  - `useTasks(filters)` — 任務列表查詢 hook（React Query，支援分頁）
  - `useTask(id)` — 單一任務查詢 hook（含自動 refetch 間隔）
  - `useTaskSteps(id)` — 任務步驟查詢 hook
  - `useCancelTask()` — 取消任務 mutation hook
  - `useRetryTask()` — 重試任務 mutation hook

### S139-2: Task Dashboard 頁面 (3 SP)

**作為** 前端使用者
**我希望** 有一個任務中心頁面來追蹤所有 dispatch 出去的任務
**以便** 我能查看每個任務的狀態、進度、執行結果，並對失敗的任務進行重試

**技術規格**:
- 新增 `frontend/src/pages/tasks/TaskDashboardPage.tsx`
  - 任務列表頁面，使用 Shadcn UI DataTable
  - 狀態篩選器（pending / running / completed / failed / cancelled）
  - 優先級篩選器（LOW / MEDIUM / HIGH / CRITICAL）
  - 表格欄位：Task ID、名稱、狀態、進度百分比、Agent、建立時間、耗時
  - 狀態 Badge 色彩：pending=灰色、running=藍色、completed=綠色、failed=紅色、cancelled=黃色
  - 操作按鈕：查看詳情、取消（running 狀態）、重試（failed 狀態）
  - 支援分頁（每頁 20 筆）
  - 自動 refetch（每 5 秒更新 running 狀態的任務）
- 新增 `frontend/src/pages/tasks/TaskDetailPage.tsx`
  - 任務詳情頁面
  - 顯示任務 metadata（ID、名稱、狀態、建立時間、完成時間、Agent 資訊）
  - 進度條（百分比 + 視覺化）
  - 步驟列表（每個步驟：名稱、狀態、耗時、輸出摘要）
  - 執行結果區塊（成功時顯示結果、失敗時顯示錯誤訊息）
  - 操作按鈕：取消、重試、返回列表
  - 使用 Shadcn UI Card + Progress + Table + Badge 組件

### S139-3: TaskProgressCard 內聯組件 (3 SP)

**作為** 前端使用者
**我希望** 在 Chat 對話中直接看到任務進度
**以便** 我不需要離開 Chat 頁面就能追蹤 dispatch 出去的任務執行狀況

**技術規格**:
- 新增 `frontend/src/components/unified-chat/TaskProgressCard.tsx`
  - Props: `{ taskId: string; taskName: string; status: TaskStatus; progress: number; steps: TaskStep[]; }`
  - 內聯卡片顯示：
    - 頂部：Task ID + 名稱 + 狀態 Badge
    - 中間：進度條（百分比 + 動畫效果，running 時有脈動動畫）
    - 下方：步驟列表（可摺疊，每個步驟顯示名稱 + 狀態圖標）
  - 即時更新：使用 useTask hook 自動 refetch（running 狀態每 3 秒更新）
  - 點擊 Task ID 可跳轉到 TaskDetailPage
  - 狀態轉換動畫（pending → running → completed）
  - 使用 Shadcn UI Card + Progress + Collapsible + Badge 組件
  - 支援多個 TaskProgressCard 同時顯示（一次 dispatch 多個任務）

### S139-4: 路由 + 導航更新 (2 SP)

**作為** 前端使用者
**我希望** Sidebar 導航包含任務中心入口
**以便** 我能方便地進入任務管理頁面查看所有任務

**技術規格**:
- 修改 `frontend/src/App.tsx`
  - 新增路由 `/tasks` → `TaskDashboardPage`
  - 新增路由 `/tasks/:id` → `TaskDetailPage`
  - Lazy import 新增頁面組件
- 修改 `frontend/src/components/layout/Sidebar.tsx`
  - 在「Sessions 管理」下方新增「任務中心」導航項目
  - 圖標：ListTodo 或 CheckSquare icon
  - 路由指向 `/tasks`
  - 可選：顯示 running 任務數量 Badge

## 檔案變更清單

### 新增檔案
| 檔案路徑 | 用途 |
|----------|------|
| `frontend/src/api/endpoints/tasks.ts` | Task CRUD API client |
| `frontend/src/hooks/useTasks.ts` | Task 管理 React Query hooks |
| `frontend/src/pages/tasks/TaskDashboardPage.tsx` | 任務中心列表頁面 |
| `frontend/src/pages/tasks/TaskDetailPage.tsx` | 任務詳情頁面 |
| `frontend/src/components/unified-chat/TaskProgressCard.tsx` | 內聯任務進度卡片組件 |

### 修改檔案
| 檔案路徑 | 修改內容 |
|----------|---------|
| `frontend/src/App.tsx` | 新增 /tasks 路由 |
| `frontend/src/components/layout/Sidebar.tsx` | 新增任務中心導航項目 |

## 驗收標準

- [ ] Task API client 能正確呼叫所有 /tasks 端點
- [ ] useTasks hook 支援狀態/優先級篩選和分頁
- [ ] Task Dashboard 頁面能顯示任務列表並支援篩選
- [ ] Task Dashboard 自動更新 running 狀態的任務（每 5 秒）
- [ ] TaskDetailPage 能顯示完整任務詳情含步驟列表
- [ ] TaskProgressCard 在 Chat 中正確顯示任務進度
- [ ] TaskProgressCard 即時更新進度（running 狀態每 3 秒 refetch）
- [ ] 點擊 Task ID 可跳轉到 TaskDetailPage
- [ ] Sidebar 包含任務中心導航入口
- [ ] 所有新增組件使用 TypeScript + Shadcn UI
- [ ] 所有新增程式碼通過 ESLint 檢查
- [ ] npm run build 無錯誤

## 相關連結

- [Phase 40 計劃](./README.md)
- [Sprint 138 Plan](./sprint-138-plan.md)
- [Sprint 140 Plan](./sprint-140-plan.md)

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 10
