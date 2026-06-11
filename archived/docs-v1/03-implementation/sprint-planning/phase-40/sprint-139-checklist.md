# Sprint 139 Checklist: Task Dashboard + 內聯進度組件

## Sprint 目標

| 項目 | 值 |
|------|-----|
| **總點數** | 10 點 |
| **狀態** | ✅ 已完成 |

---

## 開發任務

### S139-1: Task API + hooks (2 SP)
- [x] 新增 `frontend/src/api/endpoints/tasks.ts`
- [x] 實作 `getTasks(filters)` — GET /tasks（支援 status / priority / agent_id 篩選）
- [x] 實作 `getTask(id)` — GET /tasks/{id}
- [x] 實作 `getTaskSteps(id)` — GET /tasks/{id}/steps
- [x] 實作 `cancelTask(id)` — POST /tasks/{id}/cancel
- [x] 實作 `retryTask(id)` — POST /tasks/{id}/retry
- [x] 新增 `frontend/src/hooks/useTasks.ts`
- [x] 實作 `useTasks(filters)` — 任務列表查詢 hook（React Query，支援分頁）
- [x] 實作 `useTask(id)` — 單一任務查詢 hook（含自動 refetch 間隔）
- [x] 實作 `useTaskSteps(id)` — 任務步驟查詢 hook
- [x] 實作 `useCancelTask()` — 取消任務 mutation hook
- [x] 實作 `useRetryTask()` — 重試任務 mutation hook

### S139-2: Task Dashboard 頁面 (3 SP)
- [x] 新增 `frontend/src/pages/tasks/TaskDashboardPage.tsx`
- [x] 實作狀態篩選器（pending / running / completed / failed / cancelled）
- [x] 實作優先級篩選器（LOW / MEDIUM / HIGH / CRITICAL）
- [x] 實作表格欄位：Task ID、名稱、狀態、進度百分比、Agent、建立時間、耗時
- [x] 實作狀態 Badge 色彩：pending=灰色、running=藍色、completed=綠色、failed=紅色、cancelled=黃色
- [x] 實作操作按鈕：查看詳情、取消（running）、重試（failed）
- [x] 實作分頁（每頁 20 筆）
- [x] 實作自動 refetch（每 5 秒更新 running 狀態的任務）
- [x] 使用 Shadcn UI DataTable 組件
- [x] 新增 `frontend/src/pages/tasks/TaskDetailPage.tsx`
- [x] 實作任務 metadata 顯示（ID、名稱、狀態、建立時間、完成時間、Agent 資訊）
- [x] 實作進度條（百分比 + 視覺化）
- [x] 實作步驟列表（每個步驟：名稱、狀態、耗時、輸出摘要）
- [x] 實作執行結果區塊（成功顯示結果、失敗顯示錯誤）
- [x] 實作操作按鈕：取消、重試、返回列表
- [x] 使用 Shadcn UI Card + Progress + Table + Badge 組件

### S139-3: TaskProgressCard 內聯組件 (3 SP)
- [x] 新增 `frontend/src/components/unified-chat/TaskProgressCard.tsx`
- [x] 實作 Props interface: `{ taskId, taskName, status, progress, steps }`
- [x] 實作頂部：Task ID + 名稱 + 狀態 Badge
- [x] 實作中間：進度條（百分比 + 動畫效果，running 時脈動動畫）
- [x] 實作下方：步驟列表（可摺疊，每個步驟顯示名稱 + 狀態圖標）
- [x] 實作即時更新：使用 useTask hook 自動 refetch（running 狀態每 3 秒）
- [x] 實作點擊 Task ID 跳轉到 TaskDetailPage
- [x] 實作狀態轉換動畫（pending → running → completed）
- [x] 使用 Shadcn UI Card + Progress + Collapsible + Badge 組件
- [x] 支援多個 TaskProgressCard 同時顯示

### S139-4: 路由 + 導航更新 (2 SP)
- [x] 修改 `frontend/src/App.tsx` — 新增路由 `/tasks` → TaskDashboardPage
- [x] 修改 `frontend/src/App.tsx` — 新增路由 `/tasks/:id` → TaskDetailPage
- [x] Lazy import 新增頁面組件
- [x] 修改 `frontend/src/components/layout/Sidebar.tsx` — 新增「任務中心」導航項目
- [x] 設定導航圖標（ListTodo 或 CheckSquare icon）
- [x] 路由指向 `/tasks`
- [x] 可選：顯示 running 任務數量 Badge

## 驗證標準

- [x] Task API client 能正確呼叫所有 /tasks 端點
- [x] useTasks hook 支援狀態/優先級篩選和分頁
- [x] Task Dashboard 頁面能顯示任務列表並支援篩選
- [x] Task Dashboard 自動更新 running 狀態的任務（每 5 秒）
- [x] TaskDetailPage 能顯示完整任務詳情含步驟列表
- [x] TaskProgressCard 在 Chat 中正確顯示任務進度
- [x] TaskProgressCard 即時更新進度（running 狀態每 3 秒 refetch）
- [x] 點擊 Task ID 可跳轉到 TaskDetailPage
- [x] Sidebar 包含任務中心導航入口
- [x] 所有新增組件使用 TypeScript + Shadcn UI
- [x] 所有新增程式碼通過 ESLint 檢查
- [x] npm run build 無錯誤

## 相關連結

- [Phase 40 計劃](./README.md)
- [Sprint 139 Plan](./sprint-139-plan.md)
- [Sprint 140 Plan](./sprint-140-plan.md)

---

**Sprint 狀態**: ✅ 已完成
**Story Points**: 10
