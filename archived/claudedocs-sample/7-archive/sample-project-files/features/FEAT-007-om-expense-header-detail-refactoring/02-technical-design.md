# FEAT-007: OM Expense 表頭-明細架構重構 - 技術設計

> **建立日期**: 2025-12-05
> **狀態**: 📋 設計中
> **文檔版本**: 1.0

---

## 1. 架構概覽

### 1.1 現有架構

```
┌─────────────────┐
│   OMExpense     │ (表頭 + 項目資訊混合)
├─────────────────┤
│ id              │
│ name            │
│ description     │
│ financialYear   │
│ category        │
│ opCoId          │ ← 單一 OpCo
│ budgetAmount    │ ← 單一預算
│ actualSpent     │
│ startDate       │
│ endDate         │
│ vendorId        │
│ sourceExpenseId │
└────────┬────────┘
         │ 1:N
         ▼
┌─────────────────┐
│OMExpenseMonthly │
├─────────────────┤
│ omExpenseId     │
│ month (1-12)    │
│ actualAmount    │
│ opCoId          │
└─────────────────┘
```

### 1.2 目標架構

```
┌─────────────────────┐
│     OMExpense       │ (純表頭)
├─────────────────────┤
│ id                  │
│ name                │
│ description         │
│ financialYear       │
│ category            │
│ totalBudgetAmount   │ ← 自動計算
│ totalActualSpent    │ ← 自動計算
│ vendorId            │
│ sourceExpenseId     │
└──────────┬──────────┘
           │ 1:N
           ▼
┌─────────────────────┐
│   OMExpenseItem     │ (明細項目) [NEW]
├─────────────────────┤
│ id                  │
│ omExpenseId         │
│ name                │
│ description         │
│ sortOrder           │
│ opCoId              │ ← 每項目獨立
│ budgetAmount        │ ← 每項目獨立
│ actualSpent         │ ← 自動計算
│ currencyId          │
│ startDate           │
│ endDate             │
└──────────┬──────────┘
           │ 1:N
           ▼
┌─────────────────────┐
│  OMExpenseMonthly   │ (月度記錄)
├─────────────────────┤
│ omExpenseItemId     │ ← 關聯改變
│ month (1-12)        │
│ actualAmount        │
│ opCoId              │
└─────────────────────┘
```

---

## 2. 資料模型設計

### 2.1 Prisma Schema 變更

#### 2.1.1 新增模型：OMExpenseItem

```prisma
// packages/db/prisma/schema.prisma

model OMExpenseItem {
  id            String   @id @default(uuid())
  omExpenseId   String

  // 項目基本資訊
  name          String   // 項目名稱 (如 "TGT-DC", "RDC2")
  description   String?  @db.Text
  sortOrder     Int      @default(0)  // 排序順序 (用於拖曳排序)

  // 預算和實際
  budgetAmount  Float    // 此項目預算
  actualSpent   Float    @default(0)  // 由月度記錄自動計算

  // 幣別 (支援多幣別)
  currencyId    String?

  // OpCo 歸屬 (每個項目可能有不同 OpCo)
  opCoId        String

  // 日期範圍
  startDate     DateTime?
  endDate       DateTime

  // 元數據
  createdAt     DateTime @default(now())
  updatedAt     DateTime @updatedAt

  // 關聯
  omExpense      OMExpense         @relation(fields: [omExpenseId], references: [id], onDelete: Cascade)
  opCo           OperatingCompany  @relation("OMExpenseItemOpCo", fields: [opCoId], references: [id])
  currency       Currency?         @relation("OMExpenseItemCurrency", fields: [currencyId], references: [id])
  monthlyRecords OMExpenseMonthly[]

  @@index([omExpenseId])
  @@index([opCoId])
  @@index([sortOrder])
}
```

#### 2.1.2 修改模型：OMExpense

```prisma
model OMExpense {
  id String @id @default(uuid())

  // 基本信息
  name        String
  description String? @db.Text

  // 年度和類別
  financialYear Int
  category      String
  categoryId    String?

  // ========== 移除以下欄位 (移至 OMExpenseItem) ==========
  // opCoId String  // REMOVED - 改由 items 各自管理
  // budgetAmount Float  // REMOVED - 改為 totalBudgetAmount (計算欄位)
  // startDate DateTime  // REMOVED - 移至 items
  // endDate   DateTime  // REMOVED - 移至 items

  // ========== 新增欄位 ==========
  // 匯總數據 (由 items 自動計算)
  totalBudgetAmount Float @default(0)  // = SUM(items.budgetAmount)
  totalActualSpent  Float @default(0)  // = SUM(items.actualSpent)

  // 預設 OpCo (用於建立 item 時的預設值)
  defaultOpCoId String?

  // 增長率（對比上年度）
  yoyGrowthRate Float?

  // 供應商
  vendorId String?

  // CHANGE-001: 來源費用追蹤
  sourceExpenseId String?

  // 元數據
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  // ========== 關聯修改 ==========
  // 移除：monthlyRecords OMExpenseMonthly[]
  // 新增：
  items           OMExpenseItem[]  // NEW: 明細項目

  defaultOpCo     OperatingCompany?  @relation("OMExpenseDefaultOpCo", fields: [defaultOpCoId], references: [id])
  vendor          Vendor?            @relation(fields: [vendorId], references: [id])
  expenseCategory ExpenseCategory?   @relation(fields: [categoryId], references: [id])
  sourceExpense   Expense?           @relation("DerivedOMExpenses", fields: [sourceExpenseId], references: [id])

  @@index([vendorId])
  @@index([financialYear])
  @@index([category])
  @@index([categoryId])
  @@index([sourceExpenseId])
  @@index([defaultOpCoId])
}
```

#### 2.1.3 修改模型：OMExpenseMonthly

```prisma
model OMExpenseMonthly {
  id String @id @default(uuid())

  // ========== 關聯修改 ==========
  // 移除：omExpenseId String
  // 新增：
  omExpenseItemId String  // 改為關聯到 Item

  // 月份 (1-12)
  month Int

  // 實際支出
  actualAmount Float

  // OpCo（冗余，方便查詢）
  opCoId String

  // 元數據
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  // ========== 關聯修改 ==========
  // 移除：omExpense OMExpense @relation(...)
  // 新增：
  omExpenseItem OMExpenseItem    @relation(fields: [omExpenseItemId], references: [id], onDelete: Cascade)
  opCo          OperatingCompany @relation(fields: [opCoId], references: [id])

  // ========== 唯一約束修改 ==========
  @@unique([omExpenseItemId, month])  // 每個 Item 每月只能有一條記錄
  @@index([omExpenseItemId])
  @@index([opCoId])
  @@index([month])
}
```

#### 2.1.4 OperatingCompany 關聯更新

```prisma
model OperatingCompany {
  // ... 現有欄位 ...

  // ========== 新增關聯 ==========
  omExpenseItems        OMExpenseItem[]  @relation("OMExpenseItemOpCo")
  omExpenseDefaults     OMExpense[]      @relation("OMExpenseDefaultOpCo")
}
```

### 2.2 資料遷移策略

#### 2.2.1 遷移步驟

```sql
-- Step 1: 新增 OMExpenseItem 表
CREATE TABLE "OMExpenseItem" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "omExpenseId" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "description" TEXT,
  "sortOrder" INTEGER NOT NULL DEFAULT 0,
  "budgetAmount" DOUBLE PRECISION NOT NULL,
  "actualSpent" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "currencyId" TEXT,
  "opCoId" TEXT NOT NULL,
  "startDate" TIMESTAMP(3),
  "endDate" TIMESTAMP(3) NOT NULL,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL,
  CONSTRAINT "OMExpenseItem_omExpenseId_fkey" FOREIGN KEY ("omExpenseId")
    REFERENCES "OMExpense"("id") ON DELETE CASCADE,
  CONSTRAINT "OMExpenseItem_opCoId_fkey" FOREIGN KEY ("opCoId")
    REFERENCES "OperatingCompany"("id")
);

-- Step 2: 為每個現有 OMExpense 建立對應的 OMExpenseItem
INSERT INTO "OMExpenseItem" (
  "id", "omExpenseId", "name", "description", "sortOrder",
  "budgetAmount", "actualSpent", "opCoId", "startDate", "endDate",
  "createdAt", "updatedAt"
)
SELECT
  gen_random_uuid(),
  "id",
  "name",
  "description",
  0,
  "budgetAmount",
  "actualSpent",
  "opCoId",
  "startDate",
  "endDate",
  "createdAt",
  "updatedAt"
FROM "OMExpense";

-- Step 3: 更新 OMExpenseMonthly 關聯
ALTER TABLE "OMExpenseMonthly" ADD COLUMN "omExpenseItemId" TEXT;

UPDATE "OMExpenseMonthly" m
SET "omExpenseItemId" = (
  SELECT i."id" FROM "OMExpenseItem" i
  WHERE i."omExpenseId" = m."omExpenseId"
  LIMIT 1
);

-- Step 4: 設定 NOT NULL 並建立外鍵
ALTER TABLE "OMExpenseMonthly"
  ALTER COLUMN "omExpenseItemId" SET NOT NULL;

ALTER TABLE "OMExpenseMonthly"
  ADD CONSTRAINT "OMExpenseMonthly_omExpenseItemId_fkey"
  FOREIGN KEY ("omExpenseItemId") REFERENCES "OMExpenseItem"("id") ON DELETE CASCADE;

-- Step 5: 更新 OMExpense 新增匯總欄位
ALTER TABLE "OMExpense" ADD COLUMN "totalBudgetAmount" DOUBLE PRECISION DEFAULT 0;
ALTER TABLE "OMExpense" ADD COLUMN "totalActualSpent" DOUBLE PRECISION DEFAULT 0;
ALTER TABLE "OMExpense" ADD COLUMN "defaultOpCoId" TEXT;

UPDATE "OMExpense" e
SET
  "totalBudgetAmount" = "budgetAmount",
  "totalActualSpent" = "actualSpent",
  "defaultOpCoId" = "opCoId";

-- Step 6: 移除舊欄位 (最後執行)
-- 注意：建議保留一段時間再移除，確保遷移成功
-- ALTER TABLE "OMExpense" DROP COLUMN "opCoId";
-- ALTER TABLE "OMExpense" DROP COLUMN "budgetAmount";
-- ALTER TABLE "OMExpense" DROP COLUMN "actualSpent";
-- ALTER TABLE "OMExpense" DROP COLUMN "startDate";
-- ALTER TABLE "OMExpense" DROP COLUMN "endDate";
-- ALTER TABLE "OMExpenseMonthly" DROP COLUMN "omExpenseId";
```

---

## 3. API 設計

### 3.1 Zod Schema 更新

```typescript
// packages/api/src/routers/omExpense.ts

// ========== 新增 Schema ==========

// 明細項目 Schema
const omExpenseItemSchema = z.object({
  name: z.string().min(1, '項目名稱不能為空').max(200),
  description: z.string().optional(),
  sortOrder: z.number().int().min(0).default(0),
  budgetAmount: z.number().nonnegative('預算金額不能為負'),
  opCoId: z.string().min(1, 'OpCo 不能為空'),
  currencyId: z.string().optional(),
  startDate: z.string().optional(),
  endDate: z.string().min(1, '結束日期不能為空'),
});

// 建立 OM Expense (含明細)
const createOMExpenseWithItemsSchema = z.object({
  name: z.string().min(1, 'OM費用名稱不能為空').max(200),
  description: z.string().optional(),
  financialYear: z.number().int().min(2000).max(2100),
  category: z.string().min(1, '類別不能為空').max(100),
  vendorId: z.string().optional(),
  sourceExpenseId: z.string().optional(),
  defaultOpCoId: z.string().optional(),
  // 明細項目 (至少一項)
  items: z.array(omExpenseItemSchema).min(1, '至少需要一個明細項目'),
});

// 新增明細項目
const addItemSchema = z.object({
  omExpenseId: z.string().min(1),
  item: omExpenseItemSchema,
});

// 更新明細項目
const updateItemSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1).max(200).optional(),
  description: z.string().optional().nullable(),
  sortOrder: z.number().int().min(0).optional(),
  budgetAmount: z.number().nonnegative().optional(),
  opCoId: z.string().optional(),
  currencyId: z.string().optional().nullable(),
  startDate: z.string().optional().nullable(),
  endDate: z.string().optional(),
});

// 調整排序
const reorderItemsSchema = z.object({
  omExpenseId: z.string().min(1),
  itemIds: z.array(z.string()), // 按新順序排列的 ID 陣列
});

// 更新月度記錄 (改為 Item 級別)
const updateItemMonthlyRecordsSchema = z.object({
  omExpenseItemId: z.string().min(1, 'Item ID 不能為空'),
  monthlyData: z.array(z.object({
    month: z.number().int().min(1).max(12),
    actualAmount: z.number().nonnegative(),
  })).length(12, '必須提供 12 個月的數據'),
});
```

### 3.2 API Procedures 設計

| Procedure | HTTP | 描述 | 輸入 | 輸出 |
|-----------|------|------|------|------|
| `create` | POST | 建立 OM 費用 (含明細) | `createOMExpenseWithItemsSchema` | `OMExpense` (含 items) |
| `update` | PUT | 更新 OM 費用表頭 | `updateOMExpenseSchema` | `OMExpense` |
| `delete` | DELETE | 刪除 OM 費用 | `{ id }` | `{ success: boolean }` |
| `getById` | GET | 獲取 OM 費用詳情 | `{ id }` | `OMExpense` (含 items + monthly) |
| `getAll` | GET | 獲取 OM 費用列表 | 過濾條件 | `{ items, total, ... }` |
| **新增** `addItem` | POST | 新增明細項目 | `addItemSchema` | `OMExpenseItem` |
| **新增** `updateItem` | PUT | 更新明細項目 | `updateItemSchema` | `OMExpenseItem` |
| **新增** `removeItem` | DELETE | 刪除明細項目 | `{ id }` | `{ success: boolean }` |
| **新增** `reorderItems` | PUT | 調整項目排序 | `reorderItemsSchema` | `OMExpenseItem[]` |
| **修改** `updateMonthlyRecords` | PUT | 更新月度記錄 | `updateItemMonthlyRecordsSchema` | `OMExpenseItem` |
| `getSummary` | GET | 獲取 O&M Summary | 過濾條件 | `OMSummaryResponse` |

### 3.3 關鍵 Procedure 實作概念

#### 3.3.1 create (建立含明細的 OM 費用)

```typescript
create: protectedProcedure
  .input(createOMExpenseWithItemsSchema)
  .mutation(async ({ ctx, input }) => {
    const { items, ...headerData } = input;

    return ctx.prisma.$transaction(async (tx) => {
      // 1. 計算匯總數據
      const totalBudgetAmount = items.reduce((sum, item) => sum + item.budgetAmount, 0);

      // 2. 建立表頭
      const omExpense = await tx.oMExpense.create({
        data: {
          ...headerData,
          totalBudgetAmount,
          totalActualSpent: 0,
        },
      });

      // 3. 建立明細項目 + 月度記錄
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        const newItem = await tx.oMExpenseItem.create({
          data: {
            omExpenseId: omExpense.id,
            name: item.name,
            description: item.description,
            sortOrder: item.sortOrder ?? i,
            budgetAmount: item.budgetAmount,
            actualSpent: 0,
            opCoId: item.opCoId,
            currencyId: item.currencyId,
            startDate: item.startDate ? new Date(item.startDate) : null,
            endDate: new Date(item.endDate),
          },
        });

        // 4. 建立 12 個月度記錄
        const monthlyRecords = Array.from({ length: 12 }, (_, j) => ({
          omExpenseItemId: newItem.id,
          month: j + 1,
          actualAmount: 0,
          opCoId: item.opCoId,
        }));

        await tx.oMExpenseMonthly.createMany({ data: monthlyRecords });
      }

      // 5. 返回完整資料
      return tx.oMExpense.findUnique({
        where: { id: omExpense.id },
        include: {
          items: {
            include: { monthlyRecords: { orderBy: { month: 'asc' } } },
            orderBy: { sortOrder: 'asc' },
          },
        },
      });
    });
  }),
```

#### 3.3.2 updateMonthlyRecords (更新 Item 月度記錄)

```typescript
updateMonthlyRecords: protectedProcedure
  .input(updateItemMonthlyRecordsSchema)
  .mutation(async ({ ctx, input }) => {
    const { omExpenseItemId, monthlyData } = input;

    return ctx.prisma.$transaction(async (tx) => {
      // 1. 驗證 Item 存在
      const item = await tx.oMExpenseItem.findUnique({
        where: { id: omExpenseItemId },
        include: { omExpense: true },
      });

      if (!item) throw new TRPCError({ code: 'NOT_FOUND' });

      // 2. 更新月度記錄
      for (const data of monthlyData) {
        await tx.oMExpenseMonthly.upsert({
          where: { omExpenseItemId_month: { omExpenseItemId, month: data.month } },
          update: { actualAmount: data.actualAmount },
          create: {
            omExpenseItemId,
            month: data.month,
            actualAmount: data.actualAmount,
            opCoId: item.opCoId,
          },
        });
      }

      // 3. 計算 Item 實際支出
      const itemActualSpent = monthlyData.reduce((sum, d) => sum + d.actualAmount, 0);
      await tx.oMExpenseItem.update({
        where: { id: omExpenseItemId },
        data: { actualSpent: itemActualSpent },
      });

      // 4. 更新表頭匯總
      const allItems = await tx.oMExpenseItem.findMany({
        where: { omExpenseId: item.omExpenseId },
      });

      const totalActualSpent = allItems.reduce((sum, i) => sum + i.actualSpent, 0);
      const totalBudgetAmount = allItems.reduce((sum, i) => sum + i.budgetAmount, 0);

      await tx.oMExpense.update({
        where: { id: item.omExpenseId },
        data: { totalActualSpent, totalBudgetAmount },
      });

      return tx.oMExpenseItem.findUnique({
        where: { id: omExpenseItemId },
        include: { monthlyRecords: { orderBy: { month: 'asc' } } },
      });
    });
  }),
```

---

## 4. 前端組件設計

### 4.1 新增組件

| 組件 | 路徑 | 用途 |
|------|------|------|
| `OMExpenseItemForm` | `components/om-expense/OMExpenseItemForm.tsx` | 明細項目表單 (新增/編輯) |
| `OMExpenseItemList` | `components/om-expense/OMExpenseItemList.tsx` | 明細項目列表 (可拖曳排序) |
| `OMExpenseItemMonthlyGrid` | `components/om-expense/OMExpenseItemMonthlyGrid.tsx` | 單一項目的月度編輯 |

### 4.2 組件設計：OMExpenseItemForm

```typescript
interface OMExpenseItemFormProps {
  mode: 'create' | 'edit';
  omExpenseId?: string;  // create 模式可選，edit 模式必填
  initialData?: Partial<OMExpenseItem>;
  onSuccess?: (item: OMExpenseItem) => void;
  onCancel?: () => void;
}

// 欄位
// - name (必填)
// - description (可選)
// - opCoId (必填, Select)
// - budgetAmount (必填)
// - currencyId (可選, Select)
// - startDate (可選, DatePicker)
// - endDate (必填, DatePicker)
```

### 4.3 組件設計：OMExpenseItemList

```typescript
interface OMExpenseItemListProps {
  omExpenseId: string;
  items: OMExpenseItem[];
  onAddItem: () => void;
  onEditItem: (item: OMExpenseItem) => void;
  onDeleteItem: (itemId: string) => void;
  onReorder: (newOrder: string[]) => void;
  onEditMonthly: (item: OMExpenseItem) => void;
}

// 功能
// - 表格顯示所有項目
// - 拖曳排序 (react-beautiful-dnd 或 @dnd-kit)
// - 每行操作按鈕：編輯、刪除、編輯月度
// - 頂部新增按鈕
// - 底部匯總行
```

### 4.4 修改組件

| 組件 | 修改內容 |
|------|---------|
| `OMExpenseForm` | 從單一表單改為表頭表單 + 明細列表 |
| `OMExpenseMonthlyGrid` | 改為接收 `omExpenseItemId` 而非 `omExpenseId` |
| `OMSummaryDetailGrid` | 調整資料結構處理，支援 Item 層級 |
| `OMSummaryCategoryGrid` | 調整聚合計算邏輯 |

---

## 5. 頁面設計

### 5.1 om-expenses/new/page.tsx 改造

**新流程**：
1. 填寫表頭資訊（名稱、財年、類別等）
2. 點擊「新增明細項目」添加至少一個項目
3. 每個項目獨立設定 OpCo、預算、日期
4. 點擊「建立」一次性提交表頭 + 所有明細

### 5.2 om-expenses/[id]/page.tsx 改造

**新佈局**：
```
┌─────────────────────────────────────────┐
│ 表頭資訊 Card                            │
│ - 名稱、描述、財年、類別                  │
│ - 總預算、總實際、利用率                  │
├─────────────────────────────────────────┤
│ 明細項目 Card                            │
│ ┌─────────────────────────────────────┐ │
│ │ 項目列表表格                         │ │
│ │ [#] [名稱] [OpCo] [預算] [實際] [操作]│ │
│ │ 1.  TGT-DC  RHK   50000  48000  [...]│ │
│ │ 2.  RDC2    P&C   30000  28000  [...]│ │
│ │ ─────────────────────────────────── │ │
│ │ 總計              80000  76000       │ │
│ └─────────────────────────────────────┘ │
│ [+ 新增項目]                             │
├─────────────────────────────────────────┤
│ 月度記錄 (選中項目時顯示)                 │
│ [月度編輯表格 - 針對選中項目]             │
└─────────────────────────────────────────┘
```

---

## 6. I18N 新增鍵值

```json
{
  "omExpenses": {
    "items": {
      "title": "明細項目",
      "addItem": "新增項目",
      "editItem": "編輯項目",
      "removeItem": "刪除項目",
      "reorderItems": "調整順序",
      "noItems": "尚無明細項目",
      "atLeastOne": "至少需要一個明細項目",
      "confirmDelete": "確定要刪除此項目嗎？相關的月度記錄也會一併刪除。"
    },
    "itemFields": {
      "name": { "label": "項目名稱", "placeholder": "輸入項目名稱" },
      "opCo": { "label": "所屬 OpCo", "placeholder": "選擇 OpCo" },
      "budgetAmount": { "label": "項目預算", "placeholder": "0.00" },
      "currency": { "label": "幣別", "placeholder": "選擇幣別" },
      "startDate": { "label": "開始日期" },
      "endDate": { "label": "結束日期" }
    },
    "form": {
      "headerSection": "表頭資訊",
      "itemsSection": "明細項目"
    },
    "summary": {
      "totalBudget": "總預算",
      "totalActual": "總實際",
      "itemCount": "項目數量"
    }
  }
}
```

---

## 7. 待決定事項

| 編號 | 問題 | 選項 | 建議 | 決定 | 狀態 |
|------|------|------|------|------|------|
| Q-01 | 是否支援項目階層？ | A) 單層 B) 兩層 (如 1.1, 1.2) | A) 單層，保持簡單 | ✅ A) 單層 | ✅ 已確認 (2025-12-05) |
| Q-02 | 拖曳排序套件選擇 | A) react-beautiful-dnd B) @dnd-kit | B) @dnd-kit (更現代) | ✅ B) @dnd-kit | ✅ 已確認 (2025-12-05) |
| Q-03 | 舊欄位何時移除？ | A) 立即 B) 一個版本後 | B) 一個版本後，確保穩定 | ✅ B) 一個版本後 | ✅ 已確認 (2025-12-05) |
| Q-04 | API 向後兼容期？ | A) 1 週 B) 2 週 C) 1 個月 | B) 2 週 | ✅ B) 2 週 | ✅ 已確認 (2025-12-05) |

> **決定記錄日期**: 2025-12-05
> **決定者**: 專案負責人確認

---

**文檔版本**: 1.0
**最後更新**: 2025-12-05
**作者**: Claude AI Assistant
