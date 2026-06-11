# Sprint 5 Checklist: 前端 UI

**Sprint 目標**: 建立現代化 React 前端界面和監控儀表板
**週期**: Week 11-12
**總點數**: 45 點
**MVP 功能**: F12, F13

---

## 快速驗證命令

```bash
# 啟動前端開發服務器
cd frontend && npm run dev

# 運行測試
cd frontend && npm run test

# 構建生產版本
cd frontend && npm run build

# 運行 E2E 測試
cd frontend && npm run test:e2e
```

---

## S5-1: 前端架構設置 (8 點)

### 項目初始化
- [ ] 創建 Vite + React + TypeScript 項目
- [ ] 配置 TypeScript (strict mode)
- [ ] 配置路徑別名 (@/)

### 樣式系統
- [ ] 安裝和配置 TailwindCSS
- [ ] 安裝 Shadcn/ui
- [ ] 配置主題顏色
- [ ] 創建全局樣式

### 路由設置
- [ ] 安裝 React Router v6
- [ ] 配置路由結構
  - [ ] / → Dashboard
  - [ ] /workflows → Workflows
  - [ ] /workflows/:id → Workflow Detail
  - [ ] /agents → Agents
  - [ ] /agents/:id → Agent Detail
  - [ ] /templates → Templates
  - [ ] /approvals → Approvals
  - [ ] /audit → Audit

### API 客戶端
- [ ] 創建 `src/api/client.ts`
  - [ ] fetchApi 基礎函數
  - [ ] 錯誤處理
  - [ ] 認證 token 處理
- [ ] 創建 API hooks
  - [ ] useWorkflows
  - [ ] useAgents
  - [ ] useExecutions
  - [ ] useCheckpoints

### 佈局組件
- [ ] 創建 AppLayout
- [ ] 創建 Sidebar
- [ ] 創建 Header
- [ ] 創建 Loading 組件
- [ ] 創建 Error Boundary

### 驗證標準
- [ ] npm run dev 啟動正常
- [ ] 路由切換正常
- [ ] API 調用正常
- [ ] 樣式渲染正確

---

## S5-2: Dashboard 頁面 (10 點)

### 統計卡片
- [ ] 創建 StatsCards 組件
  - [ ] 總執行數
  - [ ] 成功率
  - [ ] 待審批數
  - [ ] 今日 LLM 成本
- [ ] 添加 loading 狀態
- [ ] 添加錯誤處理

### 執行統計圖表
- [ ] 安裝 Recharts
- [ ] 創建 ExecutionChart 組件
  - [ ] 日執行量折線圖
  - [ ] 成功/失敗比例
  - [ ] 時間範圍選擇
- [ ] 創建 CostChart 組件
  - [ ] LLM 成本趨勢

### 最近執行列表
- [ ] 創建 RecentExecutions 組件
  - [ ] 執行 ID
  - [ ] 工作流名稱
  - [ ] 狀態徽章
  - [ ] 開始時間
  - [ ] 持續時間
- [ ] 添加分頁

### 待審批預覽
- [ ] 創建 PendingApprovals 組件
  - [ ] 顯示前 5 個待審批
  - [ ] 快速審批按鈕
  - [ ] 查看全部鏈接

### Dashboard API
- [ ] GET /dashboard/stats
- [ ] GET /dashboard/executions/chart
- [ ] GET /dashboard/cost/chart

### 驗證標準
- [ ] 統計數據正確顯示
- [ ] 圖表渲染正常
- [ ] 加載時間 < 2 秒

---

## S5-3: 工作流管理頁面 (10 點)

### 工作流列表
- [ ] 創建 WorkflowsPage
- [ ] 創建 WorkflowTable 組件
  - [ ] 名稱
  - [ ] 狀態
  - [ ] 觸發類型
  - [ ] 最後執行時間
  - [ ] 操作按鈕
- [ ] 添加搜索和過濾
- [ ] 添加分頁

### 工作流詳情
- [ ] 創建 WorkflowDetailPage
- [ ] 顯示工作流信息
- [ ] 顯示節點和邊
- [ ] 執行歷史列表

### 執行操作
- [ ] 手動執行按鈕
- [ ] 執行參數輸入
- [ ] 執行狀態更新

### 工作流創建 (基礎)
- [ ] 創建工作流表單
- [ ] 名稱和描述輸入
- [ ] JSON 定義輸入

### 驗證標準
- [ ] 列表加載正常
- [ ] 詳情頁面正確
- [ ] 執行觸發正常

---

## S5-4: Agent 管理頁面 (8 點)

### Agent 列表
- [ ] 創建 AgentsPage
- [ ] 創建 AgentCard 組件
  - [ ] 名稱和描述
  - [ ] 類別標籤
  - [ ] 狀態徽章
  - [ ] 使用統計
- [ ] 添加搜索和過濾
- [ ] 添加分頁

### Agent 詳情
- [ ] 創建 AgentDetailPage
- [ ] 顯示 Agent 配置
- [ ] 顯示工具列表
- [ ] 顯示執行歷史

### Agent 測試
- [ ] 測試輸入框
- [ ] 執行按鈕
- [ ] 結果顯示

### 從模板創建
- [ ] 模板選擇器
- [ ] 參數配置表單
- [ ] 創建確認

### 驗證標準
- [ ] 列表顯示正常
- [ ] 測試執行正常
- [ ] 模板創建正常

---

## S5-5: 審批工作台 (9 點)

### 待審批列表
- [ ] 創建 ApprovalsPage
- [ ] 創建 ApprovalCard 組件
  - [ ] 工作流名稱
  - [ ] 步驟信息
  - [ ] 創建時間
  - [ ] 查看詳情按鈕
- [ ] 添加過濾 (工作流、時間)
- [ ] 添加排序

### 審批詳情
- [ ] 創建審批詳情對話框
- [ ] 顯示待審批內容
- [ ] 顯示上下文信息
- [ ] 顯示執行軌跡

### 審批操作
- [ ] 批准按鈕
- [ ] 拒絕按鈕
- [ ] 反饋輸入框
- [ ] 確認對話框

### 批量操作
- [ ] 多選審批項
- [ ] 批量批准
- [ ] 批量拒絕

### 驗證標準
- [ ] 列表加載正常
- [ ] 審批操作正常
- [ ] 狀態實時更新

---

## 共享組件

### UI 組件
- [ ] Button (variants)
- [ ] Card
- [ ] Dialog
- [ ] Table
- [ ] Form
- [ ] Input
- [ ] Select
- [ ] Textarea
- [ ] Badge
- [ ] Avatar
- [ ] Tabs
- [ ] Tooltip

### 業務組件
- [ ] StatusBadge
- [ ] LoadingSpinner
- [ ] EmptyState
- [ ] ErrorState
- [ ] Pagination
- [ ] SearchInput
- [ ] DateRangePicker

---

## 測試完成

### 組件測試
- [ ] StatsCards.test.tsx
- [ ] ExecutionChart.test.tsx
- [ ] WorkflowTable.test.tsx
- [ ] ApprovalCard.test.tsx

### 頁面測試
- [ ] DashboardPage.test.tsx
- [ ] WorkflowsPage.test.tsx
- [ ] AgentsPage.test.tsx
- [ ] ApprovalsPage.test.tsx

### E2E 測試
- [ ] 登錄流程
- [ ] Dashboard 加載
- [ ] 工作流執行
- [ ] 審批流程

### 覆蓋率
- [ ] 組件測試覆蓋率 >= 70%

---

## 每日站會檢查點

### Day 1
- [ ] 項目初始化
- [ ] TailwindCSS 配置

### Day 2
- [ ] 路由設置
- [ ] 佈局組件

### Day 3
- [ ] API 客戶端
- [ ] StatsCards

### Day 4
- [ ] ExecutionChart
- [ ] Dashboard 完成

### Day 5
- [ ] RecentExecutions
- [ ] PendingApprovals

### Day 6
- [ ] WorkflowsPage
- [ ] WorkflowTable

### Day 7
- [ ] WorkflowDetailPage
- [ ] 執行操作

### Day 8
- [ ] AgentsPage
- [ ] AgentCard

### Day 9
- [ ] ApprovalsPage
- [ ] 審批操作

### Day 10
- [ ] E2E 測試
- [ ] 性能優化
- [ ] Sprint 回顧

---

## Sprint 完成標準

### 必須完成 (Must Have)
- [ ] Dashboard 頁面可用
- [ ] 工作流列表可用
- [ ] Agent 列表可用
- [ ] 審批工作台可用
- [ ] 首屏加載 < 2 秒

### 應該完成 (Should Have)
- [ ] 圖表可視化
- [ ] 批量審批
- [ ] 響應式設計

### 可以延後 (Could Have)
- [ ] 工作流可視化編輯器
- [ ] 深色模式

---

## 依賴確認

### 前置 Sprint
- [x] Sprint 4 完成
  - [x] 模板 API 可用
  - [x] DevUI API 可用

### 外部依賴
- [ ] 設計規格確認
- [ ] API 端點穩定

---

## 相關連結

- [Sprint 5 Plan](./sprint-5-plan.md) - 詳細計劃
- [Sprint 4 Checklist](./sprint-4-checklist.md) - 前置 Sprint
- [Sprint 6 Plan](./sprint-6-plan.md) - 後續 Sprint
- [UI/UX 設計規格](../../01-planning/ui-ux/)
