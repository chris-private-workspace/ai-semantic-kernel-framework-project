# FEAT-002: 貨幣功能系統化擴展 - 技術架構設計

> **功能編號**: FEAT-002
> **創建日期**: 2025-11-17
> **狀態**: 📋 規劃階段
> **前置需求**: FEAT-001 (專案頁面貨幣功能) ✅ 已完成

---

## 🏗️ 架構概覽

### 設計原則

1. **最小化資料庫變更**: 優先使用關聯關係繼承貨幣，避免冗余欄位
2. **一致性優先**: 所有金額顯示必須包含貨幣信息
3. **向後兼容**: 現有資料自動設定預設貨幣（TWD）
4. **類型安全**: 完整的 TypeScript 類型定義和 Zod 驗證

### 貨幣繼承架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                    Currency (Master Table)                   │
│  - id, code, name, symbol, exchangeRate, active              │
└─────────────────────────────────────────────────────────────┘
                              ↑
                              │
              ┌───────────────┼───────────────┐
              │               │               │
         (直接關聯)      (直接關聯)       (直接關聯)
              │               │               │
    ┌─────────▼─────┐  ┌─────▼──────┐  ┌────▼─────────┐
    │  BudgetPool   │  │  Project   │  │  OMExpense   │
    │  currencyId   │  │  currencyId│  │  currencyId  │
    └───────────────┘  └─────┬──────┘  └──────────────┘
                             │
                    ┌────────┴────────┬──────────┬─────────┐
                    │                 │          │         │
               (繼承專案)         (繼承專案)  (繼承專案) (繼承專案)
                    │                 │          │         │
          ┌─────────▼──────┐  ┌──────▼─────┐  ┌▼────────┐ ┌▼─────────┐
          │ BudgetProposal │  │   Quote    │  │ChargeOut│ │PurchaseOrder│
          │ (繼承 project) │  │ (繼承 project)│ │(繼承project)│(繼承 project)│
          └────────────────┘  └────────────┘  └─────────┘ └──┬───────┘
                                                              │
                                                         (繼承採購單)
                                                              │
                                                        ┌─────▼─────┐
                                                        │  Expense  │
                                                        │(繼承 PO)  │
                                                        └───────────┘
```

---

## 📊 資料庫架構

### 1. Currency Model (已存在，FEAT-001)

```prisma
model Currency {
  id           String   @id @default(uuid())
  code         String   @unique // ISO 4217 貨幣代碼
  name         String   // 貨幣名稱
  symbol       String   // 貨幣符號
  exchangeRate Float?   // 對基準貨幣的匯率
  active       Boolean  @default(true) // 是否啟用
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt

  // 關聯 (新增)
  projects      Project[]      // FEAT-001 已存在
  budgetPools   BudgetPool[]   // FEAT-002 新增
  omExpenses    OMExpense[]    // FEAT-002 新增

  @@index([code])
  @@index([active])
}
```

### 2. BudgetPool Model (需要更新)

```prisma
model BudgetPool {
  id            String   @id @default(uuid())
  name          String
  totalAmount   Float
  usedAmount    Float    @default(0)
  financialYear Int
  description   String?

  // FEAT-002: 新增貨幣欄位
  currencyId    String   // 必填欄位

  createdAt     DateTime @default(now())
  updatedAt     DateTime @updatedAt

  // 關聯
  currency   Currency         @relation(fields: [currencyId], references: [id])
  categories BudgetCategory[]
  projects   Project[]

  @@index([financialYear])
  @@index([currencyId]) // 新增索引
}
```

**Migration 策略**:
```sql
-- 1. 新增 currencyId 欄位（允許 null）
ALTER TABLE "BudgetPool" ADD COLUMN "currencyId" TEXT;

-- 2. 取得 TWD 貨幣 ID
-- 假設 TWD ID 為 'xxx-xxx-xxx'

-- 3. 更新所有現有預算池為 TWD
UPDATE "BudgetPool"
SET "currencyId" = (SELECT id FROM "Currency" WHERE code = 'TWD' LIMIT 1)
WHERE "currencyId" IS NULL;

-- 4. 將欄位改為必填
ALTER TABLE "BudgetPool" ALTER COLUMN "currencyId" SET NOT NULL;

-- 5. 新增索引和外鍵
CREATE INDEX "BudgetPool_currencyId_idx" ON "BudgetPool"("currencyId");
```

### 3. OMExpense Model (需要更新)

```prisma
model OMExpense {
  id            String   @id @default(uuid())
  name          String
  description   String?  @db.Text
  financialYear Int
  category      String
  opCoId        String

  // FEAT-002: 新增貨幣欄位
  currencyId    String   // 必填欄位

  budgetAmount  Float
  actualSpent   Float    @default(0)
  yoyGrowthRate Float?
  vendorId      String?
  startDate     DateTime
  endDate       DateTime
  createdAt     DateTime @default(now())
  updatedAt     DateTime @updatedAt

  // 關聯
  currency       Currency            @relation(fields: [currencyId], references: [id])
  opCo           OperatingCompany    @relation(fields: [opCoId], references: [id])
  vendor         Vendor?             @relation(fields: [vendorId], references: [id])
  monthlyRecords OMExpenseMonthly[]

  @@index([opCoId])
  @@index([vendorId])
  @@index([financialYear])
  @@index([category])
  @@index([currencyId]) // 新增索引
}
```

**Migration 策略**: 與 BudgetPool 相同

### 4. 其他模型（不需要資料庫變更）

以下模型透過關聯關係取得貨幣，**不需要新增 `currencyId` 欄位**：

- **BudgetProposal**: `project.currency`
- **Quote**: `project.currency`
- **PurchaseOrder**: `project.currency`
- **Expense**: `purchaseOrder.project.currency`
- **ChargeOut**: `project.currency`

---

## 🔧 API 架構

### 1. Currency Router (已存在，FEAT-001)

無需變更，已提供完整 CRUD 功能。

### 2. BudgetPool Router (需要更新)

```typescript
// packages/api/src/routers/budgetPool.ts

export const budgetPoolRouter = createTRPCRouter({
  // 更新 create procedure
  create: protectedProcedure
    .input(
      z.object({
        name: z.string().min(1),
        totalAmount: z.number().positive(),
        financialYear: z.number().int(),
        description: z.string().optional(),
        currencyId: z.string().min(1), // 新增：必填
      })
    )
    .mutation(async ({ ctx, input }) => {
      return ctx.prisma.budgetPool.create({
        data: {
          ...input,
        },
        include: {
          currency: true, // 新增：返回貨幣信息
        },
      });
    }),

  // 更新 getAll procedure
  getAll: protectedProcedure
    .input(
      z.object({
        page: z.number().int().positive().default(1),
        limit: z.number().int().positive().default(10),
        year: z.number().int().optional(),
        currencyId: z.string().optional(), // 新增：貨幣篩選
        sortBy: z.enum(['name', 'year', 'totalAmount']).default('year'),
        sortOrder: z.enum(['asc', 'desc']).default('desc'),
      })
    )
    .query(async ({ ctx, input }) => {
      const where = {
        ...(input.year && { financialYear: input.year }),
        ...(input.currencyId && { currencyId: input.currencyId }), // 新增
      };

      const items = await ctx.prisma.budgetPool.findMany({
        where,
        include: {
          currency: true, // 新增：包含貨幣信息
          _count: { select: { projects: true } },
        },
        // ... pagination and sorting
      });

      return { items, total, page, limit, totalPages };
    }),

  // 更新 getById procedure
  getById: protectedProcedure
    .input(z.object({ id: z.string().min(1) }))
    .query(async ({ ctx, input }) => {
      return ctx.prisma.budgetPool.findUnique({
        where: { id: input.id },
        include: {
          currency: true, // 新增：包含貨幣信息
          projects: {
            include: {
              manager: true,
              supervisor: true,
            },
          },
        },
      });
    }),

  // update procedure - 注意：currencyId 不可修改
  update: protectedProcedure
    .input(
      z.object({
        id: z.string().min(1),
        name: z.string().min(1).optional(),
        totalAmount: z.number().positive().optional(),
        description: z.string().optional(),
        // currencyId 不在更新欄位中（不可修改）
      })
    )
    .mutation(async ({ ctx, input }) => {
      const { id, ...data } = input;
      return ctx.prisma.budgetPool.update({
        where: { id },
        data,
        include: {
          currency: true,
        },
      });
    }),
});
```

### 3. BudgetProposal Router (需要更新)

```typescript
// packages/api/src/routers/budgetProposal.ts

export const budgetProposalRouter = createTRPCRouter({
  // 更新 getAll - 包含專案貨幣
  getAll: protectedProcedure
    .input(/* ... */)
    .query(async ({ ctx, input }) => {
      const items = await ctx.prisma.budgetProposal.findMany({
        where,
        include: {
          project: {
            include: {
              currency: true, // 新增：透過專案取得貨幣
            },
          },
        },
      });
      return { items, total, page, limit, totalPages };
    }),

  // 更新 getById - 包含專案貨幣
  getById: protectedProcedure
    .input(z.object({ id: z.string().min(1) }))
    .query(async ({ ctx, input }) => {
      return ctx.prisma.budgetProposal.findUnique({
        where: { id: input.id },
        include: {
          project: {
            include: {
              currency: true, // 新增：透過專案取得貨幣
              manager: true,
              supervisor: true,
            },
          },
          comments: {
            include: { user: true },
            orderBy: { createdAt: 'desc' },
          },
          historyItems: {
            include: { user: true },
            orderBy: { createdAt: 'desc' },
          },
        },
      });
    }),
});
```

### 4. 其他 Router 更新模式

所有其他 Router（Quote, PurchaseOrder, Expense, OMExpense, ChargeOut）都遵循相同模式：

1. **在 `getAll` 和 `getById` 中**:
   - 透過 `include` 包含關聯的 `currency` 或 `project.currency`

2. **create 和 update 不需要接收 `currencyId`**:
   - 貨幣自動繼承自專案或採購單

---

## 🎨 前端架構

### 1. 貨幣顯示組件（共用）

創建可重用的貨幣顯示組件：

```typescript
// apps/web/src/components/common/CurrencyDisplay.tsx

interface CurrencyDisplayProps {
  amount: number;
  currency?: {
    code: string;
    symbol: string;
    name?: string;
  };
  showSymbol?: boolean; // 是否顯示符號
  showCode?: boolean;   // 是否顯示代碼
  showName?: boolean;   // 是否顯示名稱
}

export function CurrencyDisplay({
  amount,
  currency,
  showSymbol = true,
  showCode = true,
  showName = false,
}: CurrencyDisplayProps) {
  if (!currency) {
    return <span>{amount.toLocaleString()}</span>;
  }

  return (
    <span className="inline-flex items-center gap-1">
      {showSymbol && <span className="text-muted-foreground">{currency.symbol}</span>}
      <span className="font-medium">{amount.toLocaleString()}</span>
      {showCode && <span className="text-sm text-muted-foreground">{currency.code}</span>}
      {showName && <span className="text-sm text-muted-foreground">({currency.name})</span>}
    </span>
  );
}
```

**使用範例**:
```tsx
// 列表頁 - 簡潔顯示
<CurrencyDisplay
  amount={budgetPool.totalAmount}
  currency={budgetPool.currency}
  showName={false}
/>
// 輸出: $ 1,000,000 TWD

// 詳情頁 - 完整顯示
<CurrencyDisplay
  amount={budgetPool.totalAmount}
  currency={budgetPool.currency}
  showName={true}
/>
// 輸出: $ 1,000,000 TWD (新台幣)
```

### 2. 貨幣選擇器組件（共用）

```typescript
// apps/web/src/components/common/CurrencySelect.tsx

interface CurrencySelectProps {
  value?: string;
  onChange: (currencyId: string) => void;
  disabled?: boolean;
  required?: boolean;
}

export function CurrencySelect({
  value,
  onChange,
  disabled = false,
  required = false,
}: CurrencySelectProps) {
  const { data: currencies } = api.currency.getAll.useQuery({
    includeInactive: false,
  });

  return (
    <Select value={value} onValueChange={onChange} disabled={disabled} required={required}>
      <SelectTrigger>
        <SelectValue placeholder={t('selectCurrency')} />
      </SelectTrigger>
      <SelectContent>
        {currencies?.map((currency) => (
          <SelectItem key={currency.id} value={currency.id}>
            {currency.code} - {currency.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
```

### 3. 頁面更新模式

#### 模式 A: 獨立貨幣欄位（BudgetPool, OMExpense）

```tsx
// 建立頁面
<CurrencySelect
  value={currencyId}
  onChange={setCurrencyId}
  required={true}
/>

// 編輯頁面 (BudgetPool - 不可修改)
<div className="flex items-center gap-2">
  <Label>貨幣</Label>
  <span className="font-medium">
    {budgetPool.currency.code} - {budgetPool.currency.name}
  </span>
  <Badge variant="secondary">不可修改</Badge>
</div>

// 列表頁
<CurrencyDisplay
  amount={item.totalAmount}
  currency={item.currency}
/>
```

#### 模式 B: 繼承專案貨幣（BudgetProposal, Quote, PurchaseOrder, ChargeOut）

```tsx
// 建立/編輯頁面 - 只顯示，不可選擇
<div className="flex items-center gap-2">
  <Label>專案貨幣</Label>
  <span className="font-medium">
    {project.currency?.code} - {project.currency?.name}
  </span>
  <Badge variant="outline">繼承自專案</Badge>
</div>

// 金額輸入框
<div className="relative">
  <Input
    type="number"
    value={amount}
    onChange={(e) => setAmount(parseFloat(e.target.value))}
  />
  <span className="absolute right-3 top-2.5 text-muted-foreground">
    {project.currency?.symbol}
  </span>
</div>

// 列表頁
<CurrencyDisplay
  amount={item.amount}
  currency={item.project.currency}
/>
```

#### 模式 C: 繼承採購單貨幣（Expense）

```tsx
// 建立/編輯頁面
<div className="flex items-center gap-2">
  <Label>採購單貨幣</Label>
  <span className="font-medium">
    {purchaseOrder.project.currency?.code}
  </span>
  <Badge variant="outline">繼承自採購單</Badge>
</div>

// 列表頁
<CurrencyDisplay
  amount={expense.totalAmount}
  currency={expense.purchaseOrder.project.currency}
/>
```

---

## 🔐 安全性考量

### 1. 貨幣變更權限

```typescript
// 只有管理員可以修改 OMExpense 的貨幣
// BudgetPool 的貨幣建立後完全不可修改

// middleware 範例
export const adminProcedure = protectedProcedure.use(async ({ ctx, next }) => {
  if (ctx.session.user.role.name !== 'Admin') {
    throw new TRPCError({ code: 'FORBIDDEN' });
  }
  return next();
});
```

### 2. 貨幣一致性驗證

```typescript
// 驗證提案金額的貨幣與專案一致
// （雖然前端已限制，但後端仍需驗證）

async function validateCurrencyConsistency(
  projectId: string,
  expectedCurrencyId: string,
  prisma: PrismaClient
) {
  const project = await prisma.project.findUnique({
    where: { id: projectId },
    select: { currencyId: true },
  });

  if (project?.currencyId !== expectedCurrencyId) {
    throw new Error('Currency mismatch with project');
  }
}
```

---

## 🎯 效能優化

### 1. 關聯查詢優化

```typescript
// 使用 select 減少不必要的資料
const budgetPools = await prisma.budgetPool.findMany({
  select: {
    id: true,
    name: true,
    totalAmount: true,
    currency: {
      select: {
        code: true,
        symbol: true,
        // 不需要 exchangeRate, active 等
      },
    },
  },
});
```

### 2. 貨幣資料快取

```typescript
// 前端快取啟用的貨幣列表
const { data: currencies } = api.currency.getAll.useQuery(
  { includeInactive: false },
  {
    staleTime: 5 * 60 * 1000, // 5 分鐘內不重新取得
    cacheTime: 10 * 60 * 1000, // 快取 10 分鐘
  }
);
```

---

## 📱 回應式設計

### 貨幣顯示適配

```tsx
// 桌面版 - 完整顯示
<div className="hidden md:flex items-center gap-2">
  <CurrencyDisplay
    amount={amount}
    currency={currency}
    showSymbol={true}
    showCode={true}
    showName={true}
  />
</div>

// 手機版 - 簡潔顯示
<div className="md:hidden flex items-center gap-1">
  <CurrencyDisplay
    amount={amount}
    currency={currency}
    showSymbol={true}
    showCode={true}
    showName={false}
  />
</div>
```

---

## 🔗 相關文檔

- [01-requirements.md](./01-requirements.md) - 需求文檔
- [03-development.md](./03-development.md) - 開發指南
- [04-progress.md](./04-progress.md) - 開發進度追蹤
- [FEAT-001 Architecture](../FEAT-001-project-fields-enhancement/02-architecture.md) - 專案貨幣功能架構參考

---

**文檔維護者**: AI Assistant + 開發團隊
**最後更新**: 2025-11-17
**狀態**: 📋 規劃階段
