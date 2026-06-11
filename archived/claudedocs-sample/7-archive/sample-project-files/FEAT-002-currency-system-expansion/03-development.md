# FEAT-002: 貨幣功能系統化擴展 - 開發指南

> **功能編號**: FEAT-002
> **創建日期**: 2025-11-17
> **狀態**: 📋 規劃階段
> **前置需求**: FEAT-001 (專案頁面貨幣功能) ✅ 已完成

---

## 📋 開發流程總覽

本功能分為 **4 個 Phase**，每個 Phase 獨立可測試，按順序執行：

```
Phase 1: 核心財務模組 (4-6 小時)
  ├─ Task 1.1: 資料庫 Migration
  ├─ Task 1.2: BudgetPool 頁面更新
  ├─ Task 1.3: BudgetProposal 頁面更新
  └─ Task 1.4: Quote 頁面更新

Phase 2: 採購與費用模組 (3-4 小時)
  ├─ Task 2.1: PurchaseOrder 頁面更新
  └─ Task 2.2: Expense 頁面更新

Phase 3: 營運與轉嫁模組 (3-4 小時)
  ├─ Task 3.1: OMExpense 頁面更新
  └─ Task 3.2: ChargeOut 頁面更新

Phase 4: I18N 與測試 (2 小時)
  ├─ Task 4.1: I18N 翻譯
  ├─ Task 4.2: 完整測試
  └─ Task 4.3: 代碼品質檢查
```

---

## 🏗️ Phase 1: 核心財務模組

### Task 1.1: 資料庫 Migration (1 小時)

#### 步驟 1: 更新 Prisma Schema

**檔案**: `packages/db/prisma/schema.prisma`

```prisma
// 1. 更新 Currency Model - 新增關聯
model Currency {
  id           String   @id @default(uuid())
  code         String   @unique
  name         String
  symbol       String
  exchangeRate Float?
  active       Boolean  @default(true)
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt

  // 關聯
  projects     Project[]     // FEAT-001 已存在
  budgetPools  BudgetPool[]  // 新增
  omExpenses   OMExpense[]   // 新增

  @@index([code])
  @@index([active])
}

// 2. 更新 BudgetPool Model
model BudgetPool {
  id            String   @id @default(uuid())
  name          String
  totalAmount   Float
  usedAmount    Float    @default(0)
  financialYear Int
  description   String?
  currencyId    String   // 新增：必填

  createdAt     DateTime @default(now())
  updatedAt     DateTime @updatedAt

  currency   Currency         @relation(fields: [currencyId], references: [id])
  categories BudgetCategory[]
  projects   Project[]

  @@index([financialYear])
  @@index([currencyId]) // 新增
}

// 3. 更新 OMExpense Model
model OMExpense {
  id            String   @id @default(uuid())
  name          String
  description   String?  @db.Text
  financialYear Int
  category      String
  opCoId        String
  currencyId    String   // 新增：必填

  budgetAmount  Float
  actualSpent   Float    @default(0)
  yoyGrowthRate Float?
  vendorId      String?
  startDate     DateTime
  endDate       DateTime
  createdAt     DateTime @default(now())
  updatedAt     DateTime @updatedAt

  currency       Currency            @relation(fields: [currencyId], references: [id])
  opCo           OperatingCompany    @relation(fields: [opCoId], references: [id])
  vendor         Vendor?             @relation(fields: [vendorId], references: [id])
  monthlyRecords OMExpenseMonthly[]

  @@index([opCoId])
  @@index([vendorId])
  @@index([financialYear])
  @@index([category])
  @@index([currencyId]) // 新增
}
```

#### 步驟 2: 創建 Migration

```bash
cd packages/db
pnpm prisma migrate dev --name feat-002-add-currency-to-budget-pool-and-om-expense
```

**Migration SQL** (自動生成，僅供參考):
```sql
-- 1. BudgetPool 新增 currencyId（先允許 NULL）
ALTER TABLE "BudgetPool" ADD COLUMN "currencyId" TEXT;

-- 2. 取得 TWD 貨幣 ID 並更新所有現有預算池
UPDATE "BudgetPool"
SET "currencyId" = (SELECT id FROM "Currency" WHERE code = 'TWD' LIMIT 1)
WHERE "currencyId" IS NULL;

-- 3. 設定為必填
ALTER TABLE "BudgetPool" ALTER COLUMN "currencyId" SET NOT NULL;

-- 4. 新增外鍵和索引
ALTER TABLE "BudgetPool" ADD CONSTRAINT "BudgetPool_currencyId_fkey"
  FOREIGN KEY ("currencyId") REFERENCES "Currency"("id") ON DELETE RESTRICT;

CREATE INDEX "BudgetPool_currencyId_idx" ON "BudgetPool"("currencyId");

-- 5. 對 OMExpense 執行相同操作
ALTER TABLE "OMExpense" ADD COLUMN "currencyId" TEXT;

UPDATE "OMExpense"
SET "currencyId" = (SELECT id FROM "Currency" WHERE code = 'TWD' LIMIT 1)
WHERE "currencyId" IS NULL;

ALTER TABLE "OMExpense" ALTER COLUMN "currencyId" SET NOT NULL;

ALTER TABLE "OMExpense" ADD CONSTRAINT "OMExpense_currencyId_fkey"
  FOREIGN KEY ("currencyId") REFERENCES "Currency"("id") ON DELETE RESTRICT;

CREATE INDEX "OMExpense_currencyId_idx" ON "OMExpense"("currencyId");
```

#### 步驟 3: 重新生成 Prisma Client

```bash
pnpm db:generate
```

#### 步驟 4: 驗證 Migration

```bash
# 檢查資料庫
pnpm db:studio

# 驗證：
# 1. BudgetPool 和 OMExpense 都有 currencyId 欄位
# 2. 所有現有資料的 currencyId 都是 TWD 的 ID
# 3. 外鍵和索引已建立
```

---

### Task 1.2: BudgetPool 頁面更新 (2 小時)

#### 步驟 1: 更新 BudgetPool API Router

**檔案**: `packages/api/src/routers/budgetPool.ts`

```typescript
import { z } from 'zod';
import { createTRPCRouter, protectedProcedure } from '../trpc';

export const budgetPoolRouter = createTRPCRouter({
  // 更新 create - 新增 currencyId
  create: protectedProcedure
    .input(
      z.object({
        name: z.string().min(1, 'Name is required'),
        totalAmount: z.number().positive('Amount must be positive'),
        financialYear: z.number().int(),
        description: z.string().optional(),
        currencyId: z.string().min(1, 'Currency is required'), // 新增
      })
    )
    .mutation(async ({ ctx, input }) => {
      // 驗證貨幣是否存在且啟用
      const currency = await ctx.prisma.currency.findUnique({
        where: { id: input.currencyId },
      });

      if (!currency || !currency.active) {
        throw new Error('Invalid or inactive currency');
      }

      return ctx.prisma.budgetPool.create({
        data: input,
        include: {
          currency: true, // 新增：返回貨幣信息
        },
      });
    }),

  // 更新 getAll - 包含貨幣，新增貨幣篩選
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
      const { page, limit, year, currencyId, sortBy, sortOrder } = input;
      const skip = (page - 1) * limit;

      const where = {
        ...(year && { financialYear: year }),
        ...(currencyId && { currencyId }), // 新增
      };

      const [items, total] = await Promise.all([
        ctx.prisma.budgetPool.findMany({
          where,
          skip,
          take: limit,
          orderBy: { [sortBy]: sortOrder },
          include: {
            currency: true, // 新增
            _count: {
              select: { projects: true },
            },
          },
        }),
        ctx.prisma.budgetPool.count({ where }),
      ]);

      return {
        items,
        total,
        page,
        limit,
        totalPages: Math.ceil(total / limit),
      };
    }),

  // 更新 getById - 包含貨幣
  getById: protectedProcedure
    .input(z.object({ id: z.string().min(1) }))
    .query(async ({ ctx, input }) => {
      const budgetPool = await ctx.prisma.budgetPool.findUnique({
        where: { id: input.id },
        include: {
          currency: true, // 新增
          projects: {
            include: {
              manager: true,
              supervisor: true,
            },
          },
          _count: {
            select: { projects: true },
          },
        },
      });

      if (!budgetPool) {
        throw new Error('Budget Pool not found');
      }

      return budgetPool;
    }),

  // 更新 update - 注意：currencyId 不可修改
  update: protectedProcedure
    .input(
      z.object({
        id: z.string().min(1),
        name: z.string().min(1).optional(),
        totalAmount: z.number().positive().optional(),
        description: z.string().optional(),
        // currencyId 不在這裡（不可修改）
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

#### 步驟 2: 創建共用貨幣組件

**檔案**: `apps/web/src/components/common/CurrencyDisplay.tsx`

```typescript
/**
 * 貨幣顯示組件
 *
 * @fileoverview 統一的貨幣金額顯示組件，支援多種顯示模式
 * @features
 * - 顯示貨幣符號、代碼、名稱
 * - 支援金額格式化
 * - 響應式設計
 *
 * @example
 * <CurrencyDisplay
 *   amount={1000000}
 *   currency={currency}
 *   showSymbol={true}
 *   showCode={true}
 * />
 *
 * @author IT Department
 * @since FEAT-002
 * @lastModified 2025-11-17
 */

import React from 'react';

interface Currency {
  code: string;
  symbol: string;
  name?: string;
}

interface CurrencyDisplayProps {
  amount: number;
  currency?: Currency;
  showSymbol?: boolean;
  showCode?: boolean;
  showName?: boolean;
  className?: string;
}

export function CurrencyDisplay({
  amount,
  currency,
  showSymbol = true,
  showCode = true,
  showName = false,
  className = '',
}: CurrencyDisplayProps) {
  if (!currency) {
    return (
      <span className={className}>
        {amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-1 ${className}`}>
      {showSymbol && (
        <span className="text-muted-foreground">{currency.symbol}</span>
      )}
      <span className="font-medium">
        {amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </span>
      {showCode && (
        <span className="text-sm text-muted-foreground">{currency.code}</span>
      )}
      {showName && (
        <span className="text-sm text-muted-foreground">({currency.name})</span>
      )}
    </span>
  );
}
```

**檔案**: `apps/web/src/components/common/CurrencySelect.tsx`

```typescript
/**
 * 貨幣選擇器組件
 *
 * @fileoverview 統一的貨幣選擇下拉選單
 * @features
 * - 載入啟用的貨幣列表
 * - 支援必填和禁用狀態
 * - 顯示貨幣代碼和名稱
 *
 * @example
 * <CurrencySelect
 *   value={currencyId}
 *   onChange={setCurrencyId}
 *   required={true}
 * />
 *
 * @author IT Department
 * @since FEAT-002
 * @lastModified 2025-11-17
 */

import React from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/trpc';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface CurrencySelectProps {
  value?: string;
  onChange: (currencyId: string) => void;
  disabled?: boolean;
  required?: boolean;
  placeholder?: string;
}

export function CurrencySelect({
  value,
  onChange,
  disabled = false,
  required = false,
  placeholder,
}: CurrencySelectProps) {
  const t = useTranslations('common');

  const { data: currencies, isLoading } = api.currency.getAll.useQuery({
    includeInactive: false,
  });

  if (isLoading) {
    return <div className="text-sm text-muted-foreground">載入中...</div>;
  }

  return (
    <Select value={value} onValueChange={onChange} disabled={disabled} required={required}>
      <SelectTrigger>
        <SelectValue placeholder={placeholder || t('selectCurrency')} />
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

#### 步驟 3: 更新 BudgetPool 列表頁面

**檔案**: `apps/web/src/app/[locale]/budget-pools/page.tsx`

在現有代碼中添加：

```typescript
// 1. 新增貨幣篩選 state
const [currencyFilter, setCurrencyFilter] = useState<string | undefined>();

// 2. 更新 API 查詢
const { data, isLoading } = api.budgetPool.getAll.useQuery({
  page,
  limit: 10,
  year: yearFilter,
  currencyId: currencyFilter, // 新增
  sortBy,
  sortOrder,
});

// 3. 新增貨幣篩選器 UI
import { CurrencySelect } from '@/components/common/CurrencySelect';

// 在篩選器區域添加
<div className="flex gap-2">
  {/* 現有篩選器 */}

  {/* 新增貨幣篩選 */}
  <CurrencySelect
    value={currencyFilter}
    onChange={(id) => {
      setCurrencyFilter(id || undefined);
      setPage(1);
    }}
    placeholder={t('filters.currency.all')}
  />
</div>

// 4. 更新列表顯示 - 添加貨幣欄位
import { CurrencyDisplay } from '@/components/common/CurrencyDisplay';

<TableCell>
  <CurrencyDisplay
    amount={budgetPool.totalAmount}
    currency={budgetPool.currency}
    showName={false}
  />
</TableCell>
```

#### 步驟 4: 更新 BudgetPool 建立頁面

**檔案**: `apps/web/src/app/[locale]/budget-pools/new/page.tsx`

```typescript
// 1. 新增 currencyId state
const [currencyId, setCurrencyId] = useState<string>('');

// 2. 在表單中添加貨幣選擇器
<div className="space-y-2">
  <Label htmlFor="currency">
    {t('form.currency.label')} <span className="text-destructive">*</span>
  </Label>
  <CurrencySelect
    value={currencyId}
    onChange={setCurrencyId}
    required={true}
  />
  <p className="text-sm text-muted-foreground">
    {t('form.currency.help')}
  </p>
</div>

// 3. 更新 create mutation
const createMutation = api.budgetPool.create.useMutation({
  onSuccess: () => {
    toast({ title: t('createSuccess') });
    router.push('/budget-pools');
  },
});

const handleSubmit = (e: React.FormEvent) => {
  e.preventDefault();
  createMutation.mutate({
    name,
    totalAmount,
    financialYear,
    description,
    currencyId, // 新增
  });
};
```

#### 步驟 5: 更新 BudgetPool 編輯頁面

**檔案**: `apps/web/src/app/[locale]/budget-pools/[id]/edit/page.tsx`

```typescript
// 1. 載入貨幣信息
const { data: budgetPool } = api.budgetPool.getById.useQuery({ id });

// 2. 顯示貨幣（只讀，不可修改）
<div className="space-y-2">
  <Label>{t('form.currency.label')}</Label>
  <div className="flex items-center gap-2 rounded-md border px-3 py-2 bg-muted">
    <span className="font-medium">
      {budgetPool?.currency.code} - {budgetPool?.currency.name}
    </span>
    <Badge variant="secondary">{t('form.currency.immutable')}</Badge>
  </div>
  <p className="text-sm text-muted-foreground">
    {t('form.currency.immutableHelp')}
  </p>
</div>

// 3. update mutation 不包含 currencyId
const updateMutation = api.budgetPool.update.useMutation({
  onSuccess: () => {
    toast({ title: t('updateSuccess') });
    router.push(`/budget-pools/${id}`);
  },
});

const handleSubmit = (e: React.FormEvent) => {
  e.preventDefault();
  updateMutation.mutate({
    id,
    name,
    totalAmount,
    description,
    // currencyId 不在這裡（不可修改）
  });
};
```

#### 步驟 6: 更新 BudgetPool 詳情頁面

**檔案**: `apps/web/src/app/[locale]/budget-pools/[id]/page.tsx`

```typescript
// 在詳情顯示中添加貨幣信息
<div className="grid gap-6 md:grid-cols-2">
  {/* 現有欄位 */}

  {/* 新增貨幣欄位 */}
  <div>
    <Label className="text-muted-foreground">{t('detail.currency')}</Label>
    <p className="mt-1 font-medium">
      {budgetPool.currency.code} - {budgetPool.currency.name}
    </p>
  </div>

  {/* 金額顯示更新 */}
  <div>
    <Label className="text-muted-foreground">{t('detail.totalAmount')}</Label>
    <CurrencyDisplay
      amount={budgetPool.totalAmount}
      currency={budgetPool.currency}
      showName={true}
      className="mt-1 text-lg"
    />
  </div>

  <div>
    <Label className="text-muted-foreground">{t('detail.usedAmount')}</Label>
    <CurrencyDisplay
      amount={budgetPool.usedAmount}
      currency={budgetPool.currency}
      showName={true}
      className="mt-1 text-lg"
    />
  </div>
</div>
```

---

### Task 1.3: BudgetProposal 頁面更新 (1.5 小時)

#### 步驟 1: 更新 BudgetProposal API Router

**檔案**: `packages/api/src/routers/budgetProposal.ts`

```typescript
// 更新 getAll - 包含專案貨幣
export const budgetProposalRouter = createTRPCRouter({
  getAll: protectedProcedure
    .input(/* ... */)
    .query(async ({ ctx, input }) => {
      const items = await ctx.prisma.budgetProposal.findMany({
        where,
        include: {
          project: {
            include: {
              currency: true, // 新增：透過專案取得貨幣
              manager: true,
              supervisor: true,
            },
          },
        },
        // ...
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
              currency: true, // 新增
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

#### 步驟 2: 更新 BudgetProposal 列表頁面

**檔案**: `apps/web/src/app/[locale]/proposals/page.tsx`

```typescript
// 更新金額顯示
<TableCell>
  <CurrencyDisplay
    amount={proposal.amount}
    currency={proposal.project.currency}
    showName={false}
  />
</TableCell>

{proposal.approvedAmount && (
  <TableCell>
    <CurrencyDisplay
      amount={proposal.approvedAmount}
      currency={proposal.project.currency}
      showName={false}
    />
  </TableCell>
)}
```

#### 步驟 3: 更新 BudgetProposal 建立/編輯頁面

**檔案**: `apps/web/src/app/[locale]/proposals/new/page.tsx` 和 `[id]/edit/page.tsx`

```typescript
// 1. 載入專案信息（包含貨幣）
const { data: project } = api.project.getById.useQuery({ id: projectId });

// 2. 顯示專案貨幣（只讀）
<div className="space-y-2">
  <Label>{t('form.projectCurrency')}</Label>
  <div className="flex items-center gap-2 rounded-md border px-3 py-2 bg-muted">
    <span className="font-medium">
      {project?.currency?.code} - {project?.currency?.name}
    </span>
    <Badge variant="outline">{t('form.inheritedFromProject')}</Badge>
  </div>
</div>

// 3. 金額輸入框顯示貨幣符號
<div className="space-y-2">
  <Label htmlFor="amount">{t('form.amount.label')}</Label>
  <div className="relative">
    <Input
      id="amount"
      type="number"
      value={amount}
      onChange={(e) => setAmount(parseFloat(e.target.value))}
      step="0.01"
      min="0"
    />
    <span className="absolute right-3 top-2.5 text-sm text-muted-foreground">
      {project?.currency?.symbol}
    </span>
  </div>
</div>
```

#### 步驟 4: 更新 BudgetProposal 詳情和審批頁面

**檔案**: `apps/web/src/app/[locale]/proposals/[id]/page.tsx`

```typescript
// 顯示金額和貨幣
<div className="grid gap-6 md:grid-cols-2">
  <div>
    <Label className="text-muted-foreground">{t('detail.amount')}</Label>
    <CurrencyDisplay
      amount={proposal.amount}
      currency={proposal.project.currency}
      showName={true}
      className="mt-1 text-lg"
    />
  </div>

  {proposal.approvedAmount && (
    <div>
      <Label className="text-muted-foreground">{t('detail.approvedAmount')}</Label>
      <CurrencyDisplay
        amount={proposal.approvedAmount}
        currency={proposal.project.currency}
        showName={true}
        className="mt-1 text-lg"
      />
    </div>
  )}

  <div>
    <Label className="text-muted-foreground">{t('detail.projectCurrency')}</Label>
    <p className="mt-1 font-medium">
      {proposal.project.currency?.code} - {proposal.project.currency?.name}
    </p>
  </div>
</div>
```

---

### Task 1.4: Quote 頁面更新 (0.5 小時)

Quote 頁面更新相對簡單，因為只需要顯示專案貨幣。

#### 步驟 1: 更新 Quote API Router

**檔案**: `packages/api/src/routers/quote.ts`

```typescript
// 更新 getAll 和 getById - 包含專案貨幣
export const quoteRouter = createTRPCRouter({
  getAll: protectedProcedure
    .query(async ({ ctx }) => {
      return ctx.prisma.quote.findMany({
        include: {
          vendor: true,
          project: {
            include: {
              currency: true, // 新增
            },
          },
        },
        orderBy: { uploadDate: 'desc' },
      });
    }),
});
```

#### 步驟 2: 更新 Quote 列表頁面

**檔案**: `apps/web/src/app/[locale]/quotes/page.tsx`

```typescript
// 更新金額顯示
<TableCell>
  <CurrencyDisplay
    amount={quote.amount}
    currency={quote.project.currency}
    showName={false}
  />
</TableCell>
```

#### 步驟 3: 更新 Quote 上傳頁面

**檔案**: `apps/web/src/app/[locale]/projects/[id]/quotes/page.tsx`

```typescript
// 顯示專案貨幣
<div className="mb-4">
  <Label>{t('projectCurrency')}</Label>
  <div className="mt-1 rounded-md border px-3 py-2 bg-muted">
    <span className="font-medium">
      {project?.currency?.code} - {project?.currency?.name}
    </span>
  </div>
</div>

// 金額輸入框
<div className="relative">
  <Input
    type="number"
    value={amount}
    onChange={(e) => setAmount(parseFloat(e.target.value))}
  />
  <span className="absolute right-3 top-2.5 text-sm text-muted-foreground">
    {project?.currency?.symbol}
  </span>
</div>
```

---

## 🎯 Phase 1 完成檢查清單

完成 Phase 1 後，執行以下檢查：

### 資料庫檢查
- [x] `BudgetPool` 表有 `currencyId` 欄位
- [x] `OMExpense` 表有 `currencyId` 欄位
- [x] 所有現有資料都有 TWD 貨幣 ID
- [x] 外鍵和索引已建立

### API 檢查
- [x] `budgetPool.getAll` 返回貨幣信息
- [x] `budgetPool.create` 接受 `currencyId`
- [x] `budgetProposal.getAll` 包含專案貨幣
- [x] `quote.getAll` 包含專案貨幣

### UI 檢查
- [x] BudgetPool 列表頁顯示貨幣
- [x] BudgetPool 建立頁有貨幣選擇器
- [x] BudgetPool 編輯頁貨幣只讀
- [x] BudgetProposal 頁面顯示專案貨幣
- [x] Quote 頁面顯示專案貨幣

### 手動測試
- [x] 建立新預算池並指定貨幣
- [x] 編輯預算池（貨幣不可修改）
- [x] 建立新提案（顯示專案貨幣）
- [x] 上傳報價單（顯示專案貨幣）
- [x] 切換語言（zh-TW/en）

---

## 📝 Phase 2 和 Phase 3 開發模式

Phase 2 (PurchaseOrder, Expense) 和 Phase 3 (OMExpense, ChargeOut) 的開發模式與 Phase 1 類似：

1. **更新 API Router**: 在 `getAll` 和 `getById` 中包含貨幣關聯
2. **更新列表頁面**: 使用 `CurrencyDisplay` 顯示金額
3. **更新建立/編輯頁面**: 顯示貨幣（只讀或繼承）
4. **更新詳情頁面**: 完整顯示貨幣信息

詳細步驟請參考 Phase 1 的模式，根據各模組的貨幣來源調整。

---

## 🔗 相關文檔

- [01-requirements.md](./01-requirements.md) - 需求文檔
- [02-architecture.md](./02-architecture.md) - 技術架構設計
- [04-progress.md](./04-progress.md) - 開發進度追蹤
- [FEAT-001 Development](../FEAT-001-project-fields-enhancement/03-development.md) - 專案貨幣功能開發參考

---

**文檔維護者**: AI Assistant + 開發團隊
**最後更新**: 2025-11-17
**狀態**: 📋 規劃階段
