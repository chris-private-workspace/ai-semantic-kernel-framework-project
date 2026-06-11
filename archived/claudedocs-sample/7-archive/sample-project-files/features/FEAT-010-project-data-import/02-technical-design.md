# FEAT-010: 技術設計文檔

> **建立日期**: 2025-12-12
> **最後更新**: 2025-12-12

## 1. 數據模型設計

### 1.1 Project 模型擴展

```prisma
model Project {
  // ... 現有欄位 ...

  // FEAT-010: 新增欄位
  fiscalYear          Int?     // 財務年度
  isCdoReviewRequired Boolean  @default(false) // CDO 審核需求
  isManagerConfirmed  Boolean  @default(false) // Manager 確認
  payForWhat          String?  // 付款原因
  payToWhom           String?  // 付款對象

  // ... 現有關聯 ...

  // FEAT-010: 新增索引
  @@index([fiscalYear])
  @@index([isCdoReviewRequired])
}
```

### 1.2 欄位說明

| 欄位 | 類型 | 必填 | 索引 | 說明 |
|------|------|------|------|------|
| fiscalYear | Int? | 否 | 是 | 財務年度，如 2025, 2026 |
| isCdoReviewRequired | Boolean | 否 | 是 | CDO 審核需求，預設 false |
| isManagerConfirmed | Boolean | 否 | 否 | Manager 確認狀態 |
| payForWhat | String? | 否 | 否 | 付款原因描述 |
| payToWhom | String? | 否 | 否 | 付款對象 |

## 2. API 設計

### 2.1 importProjects Procedure

```typescript
// packages/api/src/routers/project.ts

importProjects: protectedProcedure
  .input(z.object({
    projects: z.array(z.object({
      fiscalYear: z.number(),
      projectCategory: z.string().nullable(),
      name: z.string().min(1),
      description: z.string().nullable(),
      expenseType: z.string(),
      budgetCategoryName: z.string(),   // 需要查找
      projectCode: z.string().min(1),
      globalFlag: z.string(),
      probability: z.string(),
      team: z.string().nullable(),
      personInCharge: z.string().nullable(),
      currencyCode: z.string(),          // 需要查找
      isCdoReviewRequired: z.boolean(),
      isManagerConfirmed: z.boolean(),
      payForWhat: z.string().nullable(),
      payToWhom: z.string().nullable(),
      requestedBudget: z.number(),
    })),
    defaultManagerId: z.string(),       // 預設 Manager
    defaultSupervisorId: z.string(),    // 預設 Supervisor
    defaultBudgetPoolId: z.string(),    // 預設 Budget Pool
  }))
  .mutation(async ({ ctx, input }) => {
    // 1. 查找 BudgetCategory 映射
    // 2. 查找 Currency 映射
    // 3. 檢測重複 (by projectCode)
    // 4. 批量創建/更新
    // 5. 返回結果統計
  })
```

### 2.2 API 返回結構

```typescript
interface ImportResult {
  success: boolean;
  totalProcessed: number;
  created: number;
  updated: number;
  skipped: number;
  errors: Array<{
    row: number;
    projectCode: string;
    message: string;
  }>;
}
```

### 2.3 getAll 擴展 - FY 過濾

```typescript
// 現有 getAll 新增 fiscalYear 參數
getAll: protectedProcedure
  .input(z.object({
    // ... 現有參數 ...
    fiscalYear: z.number().optional(),  // 新增
  }))
```

## 3. 前端設計

### 3.1 新增頁面

```
apps/web/src/app/[locale]/project-data-import/
└── page.tsx    # 專案導入頁面
```

### 3.2 頁面流程（3 步驟）

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Step 1        │     │   Step 2        │     │   Step 3        │
│   上傳 Excel    │ ──► │   預覽資料      │ ──► │   確認導入      │
│                 │     │   - 新增/更新   │     │   - 執行導入    │
│                 │     │   - 錯誤標示    │     │   - 顯示結果    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 3.3 Excel 欄位映射

```typescript
const EXCEL_COLUMN_MAP = {
  fiscalYear: 'Fiscal Year',           // B
  projectCategory: 'Project Category', // C
  name: 'Project Name',                // D
  description: 'Project Description',  // E
  expenseType: 'Expense Type',         // F
  budgetCategoryName: 'Bugget Category', // G (注意拼寫)
  projectCode: 'Project Code',         // H
  globalFlag: 'Global Flag',           // I
  probability: 'Probability',          // J
  team: 'Team',                        // K
  personInCharge: 'PIC',               // L
  currencyCode: 'Currency',            // M
  isCdoReviewRequired: 'Is CDO review required', // N
  isManagerConfirmed: 'Is Manager Confirmed',    // O
  payForWhat: 'Pay for what',          // P
  payToWhom: 'Pay to whom',            // Q
  requestedBudget: 'Total Amount (USD)', // R
};
```

### 3.4 驗證規則

```typescript
const validateProjectRow = (row: ExcelRow): ValidationResult => {
  const errors: string[] = [];

  // 必填欄位
  if (!row.name) errors.push('Project Name is required');
  if (!row.projectCode) errors.push('Project Code is required');
  if (!row.fiscalYear) errors.push('Fiscal Year is required');
  if (!row.budgetCategoryName) errors.push('Budget Category is required');

  // 格式驗證
  if (row.fiscalYear && (row.fiscalYear < 2020 || row.fiscalYear > 2030)) {
    errors.push('Fiscal Year must be between 2020 and 2030');
  }

  // Y/N 轉換
  row.isCdoReviewRequired = row.isCdoReviewRequired === 'Y';
  row.isManagerConfirmed = row.isManagerConfirmed === 'Y';

  return { valid: errors.length === 0, errors };
};
```

## 4. 重複檢測邏輯

### 4.1 唯一鍵
- **主鍵**: `projectCode` (唯一)

### 4.2 檢測策略
```typescript
// 前端預覽時
const existingProjects = await api.project.getByProjectCodes(projectCodes);
const existingMap = new Map(existingProjects.map(p => [p.projectCode, p]));

rows.forEach(row => {
  if (existingMap.has(row.projectCode)) {
    row.status = 'update'; // 將更新現有
  } else {
    row.status = 'create'; // 將新建
  }
});
```

## 5. 錯誤處理

### 5.1 錯誤類型

| 類型 | 說明 | 處理方式 |
|------|------|----------|
| INVALID_FORMAT | 資料格式錯誤 | 顯示錯誤，跳過該行 |
| MISSING_REQUIRED | 必填欄位缺失 | 顯示錯誤，跳過該行 |
| INVALID_REFERENCE | 找不到關聯資料 | 顯示錯誤，跳過該行 |
| DUPLICATE | 重複的 projectCode | 提示為更新操作 |

### 5.2 Transaction 處理
```typescript
// 使用 Transaction 確保原子性
await ctx.prisma.$transaction(async (tx) => {
  // 批量操作
}, {
  maxWait: 10000,   // 10 秒
  timeout: 300000,  // 5 分鐘
});
```

## 6. 現有頁面調整

### 6.1 Project 列表頁
- 新增 Fiscal Year 下拉過濾器
- 過濾選項：全部 + 最近 5 年

### 6.2 Project 表單頁
- 新增 5 個欄位的輸入控件
- Fiscal Year: 數字輸入
- isCdoReviewRequired: Checkbox
- isManagerConfirmed: Checkbox
- payForWhat: 文字輸入
- payToWhom: 文字輸入

## 7. i18n 翻譯鍵

```json
{
  "projects": {
    "fiscalYear": {
      "label": "Fiscal Year",
      "placeholder": "Select fiscal year",
      "filter": "Filter by Fiscal Year"
    },
    "isCdoReviewRequired": {
      "label": "CDO Review Required"
    },
    "isManagerConfirmed": {
      "label": "Manager Confirmed"
    },
    "payForWhat": {
      "label": "Pay For What",
      "placeholder": "Enter payment reason"
    },
    "payToWhom": {
      "label": "Pay To Whom",
      "placeholder": "Enter payment recipient"
    }
  },
  "projectDataImport": {
    "title": "Project Data Import",
    "description": "Import projects from Excel file",
    // ... 其他翻譯鍵
  }
}
```

## 8. 依賴和風險

### 8.1 依賴
- xlsx 套件（已安裝，用於 OM Expense 導入）
- 現有 BudgetCategory 和 Currency 資料

### 8.2 風險
| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| BudgetCategory 名稱不匹配 | 導入失敗 | 預覽時顯示錯誤，允許手動選擇 |
| 大量資料導入超時 | Transaction 失敗 | 增加 timeout 設定 |
| projectCode 重複策略 | 資料覆蓋 | 預覽時明確顯示更新項 |
