# S4-5: Workflow List View - 實現摘要

**Story ID**: S4-5
**標題**: Workflow List View
**Story Points**: 5
**狀態**: ✅ 已完成
**完成日期**: 2025-11-26

---

## 驗收標準達成情況

| 驗收標準 | 狀態 | 說明 |
|---------|------|------|
| 顯示工作流列表 | ✅ | 表格顯示名稱、描述、狀態、版本、時間 |
| 搜索功能 | ✅ | 按名稱和描述搜索 |
| 按狀態過濾 | ✅ | 支援 active/draft/inactive/archived/all |
| 分頁 | ✅ | 每頁 10 筆，支持上下頁導航 |
| 創建/編輯/刪除操作 | ✅ | 完整 CRUD + 複製功能 |

---

## 技術實現

### 主要組件

| 組件 | 用途 |
|------|------|
| `WorkflowListPage.tsx` | 主列表頁面 |
| `workflows.ts` | Workflow API 服務 |
| `WorkflowStatusBadge` | 狀態標籤組件 |
| `Pagination` | 分頁組件 |
| `DeleteDialog` | 刪除確認對話框 |

### API 服務

| 函數 | 端點 | 說明 |
|------|------|------|
| `getWorkflows` | GET /api/v1/workflows | 獲取列表（支援分頁、搜索、過濾） |
| `getWorkflow` | GET /api/v1/workflows/:id | 獲取單個工作流 |
| `createWorkflow` | POST /api/v1/workflows | 創建工作流 |
| `updateWorkflow` | PATCH /api/v1/workflows/:id | 更新工作流 |
| `deleteWorkflow` | DELETE /api/v1/workflows/:id | 刪除工作流 |
| `duplicateWorkflow` | POST /api/v1/workflows/:id/duplicate | 複製工作流 |

### 關鍵代碼

```typescript
// src/api/workflows.ts - 查詢參數
export interface WorkflowListParams {
  page?: number
  page_size?: number
  status?: WorkflowStatus | 'all'
  search?: string
  sort_by?: 'name' | 'created_at' | 'updated_at' | 'status'
  sort_order?: 'asc' | 'desc'
}

// src/features/workflows/WorkflowListPage.tsx - 數據獲取
const { data: workflowsData, isLoading, error } = useQuery({
  queryKey: ['workflows', queryParams],
  queryFn: () => getWorkflows(queryParams),
})

// 刪除 mutation
const deleteMutation = useMutation({
  mutationFn: deleteWorkflow,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['workflows'] })
    setDeleteTarget(null)
  },
})
```

### 頁面功能

| 功能 | 實現方式 |
|------|---------|
| **搜索** | Input + 即時過濾 |
| **狀態過濾** | Select 下拉選單 |
| **分頁** | Previous/Next 按鈕 + 頁碼顯示 |
| **編輯** | 導航到 /workflows/:id/edit |
| **複製** | useMutation + invalidateQueries |
| **刪除** | Dialog 確認 + useMutation |

---

## 代碼位置

```
frontend/src/
├── api/
│   └── workflows.ts          # Workflow API 服務（含 mock 數據）
└── features/
    └── workflows/
        ├── index.ts           # Feature 導出
        └── WorkflowListPage.tsx  # 列表頁面
```

---

## Mock 數據

開發模式下提供 10 個示例工作流：
- Customer Onboarding (active)
- Daily Report Generation (active)
- Support Ticket Routing (active)
- Inventory Sync (draft)
- Email Campaign Automation (inactive)
- Data Backup Process (active)
- Invoice Processing (active)
- User Feedback Analysis (draft)
- Legacy System Migration (archived)
- Compliance Checker (active)

---

## 測試覆蓋

| 測試文件 | 測試數量 | 狀態 |
|---------|---------|------|
| 單元測試 | 待 S4-10 | ⏳ |
| E2E 測試 | 待 S4-10 | ⏳ |

### 構建驗證
- ✅ `npm run build` 成功
- ✅ TypeScript 編譯無錯誤
- ✅ 產出文件大小：
  - CSS: 24.38 kB (gzip: 5.41 kB)
  - JS: 459.29 kB (gzip: 147.53 kB)

---

## UI 特性

- 響應式過濾器佈局（sm:flex-row）
- 狀態顏色編碼（success/warning/secondary/default）
- 相對時間顯示（剛才/X 分鐘前/X 小時前/X 天前）
- 刪除確認對話框（防止誤刪）
- Loading 和 Error 狀態處理
- 空狀態提示

---

## 相關文檔

- [Sprint 規劃](../../sprint-planning/sprint-4-ui-frontend.md)
- [S4-4 Dashboard 摘要](./S4-4-dashboard-implementation-summary.md)
- [Workflow Service API (Sprint 1)](../sprint-1/summaries/)

---

**生成日期**: 2025-11-26
