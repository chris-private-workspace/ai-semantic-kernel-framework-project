# FEAT-008: 技術設計文檔

> **建立日期**: 2025-12-09
> **最後更新**: 2025-12-09

---

## 1. 架構評估

### 1.1 現有架構支援

| 項目 | 狀態 | 說明 |
|------|------|------|
| 資料模型 | ✅ 支援 | OMExpense, OMExpenseItem, OMExpenseMonthly 模型已存在 (FEAT-007) |
| Operating Company | ✅ 支援 | 模型已存在，需新增導入時自動建立邏輯 |
| ExpenseCategory | ✅ 支援 | 9 個類別已定義 |
| API Router | ⚠️ 需擴展 | 需在 omExpense.ts 新增 importData procedure |
| 前端頁面 | ❌ 需新建 | 需建立 `/data-import` 頁面 |

### 1.2 需要新增的部分

**資料模型：**
1. **新增 OMExpenseItem 欄位**: `lastFYActualExpense Float?` - 上年度實際支出

**後端：**
1. **新增 API Procedure**: `omExpense.importData`
2. **新增 Zod Schema**: `importOMExpenseDataSchema`
3. **新增 Helper 函數**: 處理 OpCo 建立和唯一性檢查
4. **更新 API Procedure**: `omExpense.addItem`, `omExpense.updateItem` 支援 lastFYActualExpense

**前端：**
1. **新增頁面**: `apps/web/src/app/[locale]/data-import/page.tsx`
2. **新增組件**: `DataImportForm.tsx`, `ImportResult.tsx`
3. **新增翻譯**: `en.json`, `zh-TW.json` 新增 dataImport namespace
4. **更新組件**: OMExpenseItemForm 新增 "Last year actual expense" 輸入欄位

---

## 2. API 設計

### 2.1 新增 Procedure: `importData`

```typescript
// Input Schema
const importOMExpenseItemSchema = z.object({
  // Header 資訊
  headerName: z.string().min(1),
  headerDescription: z.string().nullable().optional(),
  category: z.string().min(1),

  // Item 資訊
  itemName: z.string().min(1),
  itemDescription: z.string().nullable().optional(),
  budgetAmount: z.number().nonnegative().default(0),
  opCoName: z.string().min(1),
  endDate: z.string().nullable().optional(),
  lastFYActualExpense: z.number().nullable().optional(), // 上年度實際支出 (新增)
});

const importOMExpenseDataSchema = z.object({
  financialYear: z.number().int().min(2000).max(2100),
  items: z.array(importOMExpenseItemSchema).min(1),
});

// Output Schema
type ImportResult = {
  success: boolean;
  statistics: {
    totalItems: number;
    createdOpCos: number;
    createdHeaders: number;
    createdItems: number;
    createdMonthlyRecords: number;
  };
  details: {
    opCos: string[];
    headers: string[];
  };
  error?: {
    message: string;
    duplicateItem?: {
      headerName: string;
      itemName: string;
      opCoName: string;
    };
  };
};
```

### 2.2 處理流程（全部 Rollback 策略）

```
開始 Prisma Transaction
         ↓
Step 1: 解析輸入資料
         ↓
Step 2: 收集所有唯一的 OpCo 名稱
         ↓
Step 3: 查詢現有 OpCo，建立缺失的 OpCo
         ↓
Step 4: 收集所有唯一的 Header (name + category)
         ↓
Step 5: 查詢現有 Header，建立缺失的 Header
         ↓
Step 6: 逐筆處理 Item 資料
         ├─ 唯一性檢查 (header + item + opCo)
         ├─ 如果重複 → 拋出錯誤，觸發 Rollback
         └─ 如果唯一 → 建立 OMExpenseItem + 12 個 OMExpenseMonthly
         ↓
Step 7: Transaction Commit
         ↓
Step 8: 返回成功結果

如果任何步驟失敗 → Transaction Rollback → 返回錯誤結果
```

### 2.3 唯一性檢查邏輯（全部 Rollback）

```typescript
// 在 Transaction 內執行唯一性檢查
const existingItem = await tx.oMExpenseItem.findFirst({
  where: {
    omExpenseId: header.id,
    name: itemName,
    opCoId: opCo.id,
  },
});

if (existingItem) {
  // 拋出錯誤，觸發 Transaction Rollback
  throw new TRPCError({
    code: 'CONFLICT',
    message: `發現重複資料: Header="${headerName}", Item="${itemName}", OpCo="${opCoName}"`,
  });
}
```

---

## 3. 資料流設計

### 3.1 Operating Company 處理

```typescript
// 1. 收集所有 OpCo 名稱
const opCoNames = [...new Set(items.map(i => i.opCoName))];

// 2. 查詢現有 OpCo (以 name 為主，不是 code)
const existingOpCos = await tx.operatingCompany.findMany({
  where: { name: { in: opCoNames } },
});
const existingOpCoMap = new Map(existingOpCos.map(o => [o.name, o]));

// 3. 建立缺失的 OpCo
const missingOpCoNames = opCoNames.filter(n => !existingOpCoMap.has(n));
const createdOpCos: string[] = [];

for (const name of missingOpCoNames) {
  const opCo = await tx.operatingCompany.create({
    data: {
      code: generateOpCoCode(name),
      name: name,
      isActive: true,
    },
  });
  existingOpCoMap.set(name, opCo);
  createdOpCos.push(name);
}
```

### 3.2 OpCo Code 生成規則

```typescript
function generateOpCoCode(name: string): string {
  // 移除括號內容，取前綴
  const base = name.replace(/\s*\([^)]*\)/g, '').trim();
  // 轉為大寫，移除非字母數字
  const cleaned = base.toUpperCase().replace(/[^A-Z0-9]/g, '');
  // 取前 10 個字符
  const code = cleaned.substring(0, 10) || 'OPCO';
  // 加上時間戳避免重複
  return `${code}-${Date.now().toString(36).toUpperCase()}`;
}
```

### 3.3 OM Expense Header 處理

```typescript
// 1. 收集唯一 Header (name + category + financialYear)
const headerKeys = [...new Set(items.map(i =>
  `${i.headerName}|${i.category}|${financialYear}`
))];

// 2. 查詢現有 Header
const existingHeaders = await tx.oMExpense.findMany({
  where: {
    financialYear,
  },
});
const headerMap = new Map(existingHeaders.map(h =>
  [`${h.name}|${h.category}|${financialYear}`, h]
));

// 3. 建立缺失的 Header
const createdHeaders: string[] = [];
const processedHeaderKeys = new Set<string>();

for (const item of items) {
  const headerKey = `${item.headerName}|${item.category}|${financialYear}`;

  if (!headerMap.has(headerKey) && !processedHeaderKeys.has(headerKey)) {
    const header = await tx.oMExpense.create({
      data: {
        name: item.headerName,
        description: item.headerDescription,
        financialYear,
        category: item.category,
        // categoryId 需要查詢 ExpenseCategory
      },
    });
    headerMap.set(headerKey, header);
    createdHeaders.push(item.headerName);
    processedHeaderKeys.add(headerKey);
  }
}
```

### 3.4 OM Expense Item 建立（含 12 個月度記錄）

```typescript
// 建立 Item 和 12 個 Monthly 記錄
let sortOrderCounter = 0;
const createdItems: string[] = [];

for (const item of items) {
  const headerKey = `${item.headerName}|${item.category}|${financialYear}`;
  const header = headerMap.get(headerKey)!;
  const opCo = existingOpCoMap.get(item.opCoName)!;

  // 唯一性檢查
  const existingItem = await tx.oMExpenseItem.findFirst({
    where: {
      omExpenseId: header.id,
      name: item.itemName,
      opCoId: opCo.id,
    },
  });

  if (existingItem) {
    throw new TRPCError({
      code: 'CONFLICT',
      message: `發現重複資料`,
      // 附加資訊用於前端顯示
    });
  }

  // 建立 Item + 12 個 Monthly 記錄
  const newItem = await tx.oMExpenseItem.create({
    data: {
      omExpenseId: header.id,
      name: item.itemName,
      description: item.itemDescription,
      budgetAmount: item.budgetAmount ?? 0,
      lastFYActualExpense: item.lastFYActualExpense ?? null, // 上年度實際支出 (新增)
      opCoId: opCo.id,
      endDate: item.endDate ? new Date(item.endDate) : null,
      sortOrder: sortOrderCounter++,
      // 建立 12 個月度記錄
      monthlyRecords: {
        create: Array.from({ length: 12 }, (_, i) => ({
          month: i + 1,
          actualAmount: 0,
          opCoId: opCo.id,
        })),
      },
    },
  });

  createdItems.push(`${item.headerName} - ${item.itemName}`);
}
```

---

## 4. 前端設計

### 4.1 頁面結構

```
apps/web/src/app/[locale]/data-import/
├── page.tsx              # 主頁面
└── components/
    ├── DataImportForm.tsx    # 檔案上傳表單
    ├── ImportResult.tsx      # 導入結果顯示
    └── ImportProgress.tsx    # 處理中狀態
```

### 4.2 頁面組件

```typescript
// page.tsx
'use client';

import { useState } from 'react';
import { api } from '@/lib/trpc';
import { DataImportForm } from './components/DataImportForm';
import { ImportResult } from './components/ImportResult';

export default function DataImportPage() {
  const [importData, setImportData] = useState<ImportInput | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);

  const importMutation = api.omExpense.importData.useMutation({
    onSuccess: (data) => setResult(data),
    onError: (error) => setResult({ success: false, error: error.message }),
  });

  const handleImport = () => {
    if (importData) {
      importMutation.mutate(importData);
    }
  };

  return (
    <div className="container mx-auto py-8">
      <h1>資料導入</h1>
      <DataImportForm
        onDataLoaded={setImportData}
        onImport={handleImport}
        isLoading={importMutation.isLoading}
      />
      {result && <ImportResult result={result} />}
    </div>
  );
}
```

### 4.3 狀態管理

```typescript
type ImportPageState =
  | { status: 'idle' }
  | { status: 'file-loaded'; data: ImportInput; itemCount: number }
  | { status: 'importing'; itemCount: number }
  | { status: 'success'; result: ImportResult }
  | { status: 'error'; error: string; duplicateInfo?: DuplicateInfo };
```

---

## 5. ExpenseCategory 映射

Excel 中的 9 個 Category 需要映射到系統的 ExpenseCategory：

| Excel Category | ExpenseCategory.code | ExpenseCategory.name |
|----------------|---------------------|----------------------|
| Application System | APP | Application System |
| Cloud | CLOUD | Cloud |
| Computer Room Maintenance | MAINT | Computer Room Maintenance |
| Datalines | DATA | Datalines |
| Hardware | HW | Hardware |
| IT Security | SEC | IT Security |
| Network | NET | Network |
| Others | OTHERS | Others |
| Software | SW | Software |

```typescript
const categoryMap: Record<string, string> = {
  'Application System': 'APP',
  'Cloud': 'CLOUD',
  'Computer Room Maintenance': 'MAINT',
  'Datalines': 'DATA',
  'Hardware': 'HW',
  'IT Security': 'SEC',
  'Network': 'NET',
  'Others': 'OTHERS',
  'Software': 'SW',
};
```

---

## 6. 錯誤處理（全部 Rollback）

### 6.1 錯誤分類

1. **驗證錯誤**: Zod schema 驗證失敗 → 直接拒絕，不開始 Transaction
2. **唯一性衝突**: 發現重複資料 → 拋出錯誤，Transaction Rollback
3. **系統錯誤**: 資料庫操作失敗 → 拋出錯誤，Transaction Rollback

### 6.2 錯誤處理策略

```typescript
importData: protectedProcedure
  .input(importOMExpenseDataSchema)
  .mutation(async ({ ctx, input }) => {
    const { financialYear, items } = input;

    try {
      // 使用 Prisma Transaction - 全部成功或全部回滾
      const result = await ctx.prisma.$transaction(async (tx) => {
        // ... 所有操作在 Transaction 內執行

        return {
          success: true,
          statistics: { ... },
          details: { ... },
        };
      });

      return result;
    } catch (error) {
      // Transaction 自動 Rollback
      if (error instanceof TRPCError) {
        throw error; // 重新拋出 tRPC 錯誤
      }
      throw new TRPCError({
        code: 'INTERNAL_SERVER_ERROR',
        message: '導入失敗，所有資料已回滾',
        cause: error,
      });
    }
  }),
```

---

## 7. 影響範圍

### 7.1 新增文件

| 文件 | 說明 |
|------|------|
| `packages/api/src/routers/omExpense.ts` | 新增 `importData` procedure |
| `apps/web/src/app/[locale]/data-import/page.tsx` | 新增頁面 |
| `apps/web/src/app/[locale]/data-import/components/*.tsx` | 新增組件 |
| `apps/web/src/messages/en.json` | 新增 dataImport 翻譯 |
| `apps/web/src/messages/zh-TW.json` | 新增 dataImport 翻譯 |

### 7.2 修改文件

| 文件 | 變更 |
|------|------|
| `packages/db/prisma/schema.prisma` | OMExpenseItem 新增 lastFYActualExpense 欄位 |
| `packages/api/src/routers/omExpense.ts` | 更新 addItem, updateItem 支援新欄位 |
| `apps/web/src/components/layout/Sidebar.tsx` | 新增 Data Import 導航項目 |
| `apps/web/src/components/om-expense/OMExpenseItemForm.tsx` | 新增 "Last year actual expense" 輸入欄位 |

---

## 8. 測試計劃

### 8.1 單元測試

1. OpCo Code 生成函數
2. Category 映射函數
3. 唯一性檢查邏輯

### 8.2 整合測試

1. 空資料導入 → 拒絕
2. 單筆資料導入 → 成功
3. 批量資料導入（500 筆）→ 成功
4. 重複資料測試 → Rollback + 錯誤訊息
5. OpCo 自動建立測試
6. Header 自動建立測試
7. Monthly 記錄建立測試（確認 12 筆）

### 8.3 前端測試

1. 檔案上傳功能
2. 處理中狀態顯示
3. 成功結果顯示
4. 錯誤結果顯示

---

## 9. 相關文檔

- `docs/import-data-analysis.json` - 導入資料分析結果
- `packages/api/src/routers/omExpense.ts` - OM Expense API
- `packages/api/src/routers/operatingCompany.ts` - Operating Company API
- `packages/db/prisma/schema.prisma` - 資料模型
