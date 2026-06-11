# FEAT-001: 專案欄位擴展 - 技術設計文檔

> **功能編號**: FEAT-001
> **創建日期**: 2025-11-14
> **狀態**: 設計中
> **技術負責人**: AI Assistant + 開發團隊

---

## 📐 架構概覽

### 系統分層

```
┌─────────────────────────────────────────────────────────┐
│ Frontend (Next.js 14 + React)                           │
├─────────────────────────────────────────────────────────┤
│ 1. ProjectForm 組件（新增 4 個欄位）                    │
│ 2. 專案列表頁（新增顯示、篩選、排序）                  │
│ 3. 專案詳情頁（新增顯示區塊）                          │
│ 4. 貨幣管理頁面（新增 CRUD 功能）                      │
└─────────────────────────────────────────────────────────┘
                          ↓ tRPC
┌─────────────────────────────────────────────────────────┐
│ API Layer (tRPC + Zod Validation)                       │
├─────────────────────────────────────────────────────────┤
│ 1. currency.ts Router（新增）                           │
│    - create, update, delete, getAll, getActive         │
│ 2. project.ts Router（更新）                            │
│    - 新增欄位驗證、唯一性檢查                          │
└─────────────────────────────────────────────────────────┘
                          ↓ Prisma
┌─────────────────────────────────────────────────────────┐
│ Database Layer (PostgreSQL 16)                          │
├─────────────────────────────────────────────────────────┤
│ 1. Currency 表（新增）                                  │
│    - id, code, name, symbol, exchangeRate, active      │
│ 2. Project 表（更新）                                   │
│    - projectCode, globalFlag, priority, currencyId     │
└─────────────────────────────────────────────────────────┘
```

---

## 🗄️ 資料庫設計

### 1. Currency Model（新增）

```prisma
model Currency {
  id           String   @id @default(uuid())
  code         String   @unique              // ISO 4217 貨幣代碼 (TWD, USD, EUR)
  name         String                        // 貨幣名稱（新台幣、美元）
  symbol       String                        // 貨幣符號 (NT$, $, €)
  exchangeRate Float?                        // 匯率（可選，對基準貨幣）
  active       Boolean  @default(true)       // 是否啟用
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt

  // 關聯
  projects     Project[]

  // 索引
  @@index([code])
  @@index([active])
}
```

**關鍵設計決策**:
- `code`: 使用 ISO 4217 標準（3 字母）
- `@unique`: 確保貨幣代碼不重複
- `active`: 軟刪除機制，停用的貨幣不顯示在表單中
- `exchangeRate`: 可選欄位，本次不強制填寫

### 2. Project Model（更新）

```prisma
model Project {
  id               String    @id @default(uuid())

  // 現有欄位
  name             String
  description      String?
  status           String    @default("Draft")
  managerId        String
  supervisorId     String
  budgetPoolId     String
  budgetCategoryId String?
  requestedBudget  Float?
  approvedBudget   Float?
  startDate        DateTime
  endDate          DateTime?
  chargeOutDate    DateTime?
  createdAt        DateTime  @default(now())
  updatedAt        DateTime  @updatedAt

  // ===== 新增欄位 =====
  projectCode      String    @unique         // FR-001: 專案編號（唯一）
  globalFlag       String    @default("Region")  // FR-002: "RCL" 或 "Region"
  priority         String    @default("Medium")  // FR-003: "High", "Medium", "Low"
  currencyId       String?                   // FR-004: 關聯到 Currency

  // 關聯
  manager          User             @relation("ProjectManager", fields: [managerId], references: [id])
  supervisor       User             @relation("Supervisor", fields: [supervisorId], references: [id])
  budgetPool       BudgetPool       @relation(fields: [budgetPoolId], references: [id])
  budgetCategory   BudgetCategory?  @relation(fields: [budgetCategoryId], references: [id])
  currency         Currency?        @relation(fields: [currencyId], references: [id])  // 新增關聯
  proposals        BudgetProposal[]
  quotes           Quote[]
  purchaseOrders   PurchaseOrder[]
  chargeOuts       ChargeOut[]

  // 索引
  @@index([managerId])
  @@index([supervisorId])
  @@index([budgetPoolId])
  @@index([budgetCategoryId])
  @@index([status])
  @@index([projectCode])        // 新增：專案編號索引（唯一性查詢）
  @@index([globalFlag])         // 新增：全域標誌索引（篩選）
  @@index([priority])           // 新增：優先權索引（篩選、排序）
  @@index([currencyId])         // 新增：貨幣索引（關聯查詢）
}
```

**關鍵設計決策**:
- `projectCode @unique`: 確保專案編號唯一
- `globalFlag`, `priority`: String 類型（而非 Enum），保持彈性
- `currencyId`: 可選欄位（nullable），支援現有專案的 Migration

### 3. Migration 策略

**Migration 檔案結構**:
```sql
-- Migration: add_project_fields_and_currency
BEGIN;

-- Step 1: 建立 Currency 表
CREATE TABLE "Currency" (
  "id" TEXT NOT NULL,
  "code" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "symbol" TEXT NOT NULL,
  "exchangeRate" DOUBLE PRECISION,
  "active" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL,

  CONSTRAINT "Currency_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "Currency_code_key" ON "Currency"("code");
CREATE INDEX "Currency_code_idx" ON "Currency"("code");
CREATE INDEX "Currency_active_idx" ON "Currency"("active");

-- Step 2: 插入預設貨幣資料
INSERT INTO "Currency" ("id", "code", "name", "symbol", "exchangeRate", "active") VALUES
  (gen_random_uuid(), 'TWD', '新台幣', 'NT$', 1.0, true),
  (gen_random_uuid(), 'USD', '美元', '$', 30.5, true),
  (gen_random_uuid(), 'EUR', '歐元', '€', 33.2, true),
  (gen_random_uuid(), 'CNY', '人民幣', '¥', 4.3, true),
  (gen_random_uuid(), 'JPY', '日圓', '¥', 0.21, true),
  (gen_random_uuid(), 'HKD', '港幣', 'HK$', 3.9, true);

-- Step 3: 在 Project 表新增欄位（先設為 nullable）
ALTER TABLE "Project"
  ADD COLUMN "projectCode" TEXT,
  ADD COLUMN "globalFlag" TEXT,
  ADD COLUMN "priority" TEXT,
  ADD COLUMN "currencyId" TEXT;

-- Step 4: 為現有專案設定預設值
-- 獲取 TWD 貨幣的 ID
DO $$
DECLARE
  twd_currency_id TEXT;
BEGIN
  SELECT id INTO twd_currency_id FROM "Currency" WHERE code = 'TWD';

  UPDATE "Project"
  SET
    "projectCode" = 'LEGACY-' || SUBSTRING(id, 1, 8),
    "globalFlag" = 'Region',
    "priority" = 'Medium',
    "currencyId" = twd_currency_id
  WHERE "projectCode" IS NULL;
END $$;

-- Step 5: 設定 NOT NULL 約束（現在所有專案都有值了）
ALTER TABLE "Project"
  ALTER COLUMN "projectCode" SET NOT NULL,
  ALTER COLUMN "globalFlag" SET NOT NULL,
  ALTER COLUMN "priority" SET NOT NULL,
  ALTER COLUMN "globalFlag" SET DEFAULT 'Region',
  ALTER COLUMN "priority" SET DEFAULT 'Medium';

-- Step 6: 建立唯一性約束和索引
CREATE UNIQUE INDEX "Project_projectCode_key" ON "Project"("projectCode");
CREATE INDEX "Project_globalFlag_idx" ON "Project"("globalFlag");
CREATE INDEX "Project_priority_idx" ON "Project"("priority");
CREATE INDEX "Project_currencyId_idx" ON "Project"("currencyId");

-- Step 7: 建立外鍵約束
ALTER TABLE "Project"
  ADD CONSTRAINT "Project_currencyId_fkey"
  FOREIGN KEY ("currencyId") REFERENCES "Currency"("id") ON DELETE SET NULL ON UPDATE CASCADE;

COMMIT;
```

**Migration 驗證檢查點**:
1. ✅ Currency 表建立成功
2. ✅ 6 個預設貨幣插入成功
3. ✅ Project 表新增 4 個欄位
4. ✅ 現有專案的預設值設定成功
5. ✅ 索引和約束建立成功
6. ✅ 外鍵關聯建立成功

---

## 🔌 API 設計

### 1. Currency Router（新增）

**檔案**: `packages/api/src/routers/currency.ts`

```typescript
import { z } from 'zod';
import { TRPCError } from '@trpc/server';
import { createTRPCRouter, protectedProcedure, adminProcedure } from '../trpc';

// Zod Validation Schemas
export const createCurrencySchema = z.object({
  code: z.string().length(3, '貨幣代碼必須為 3 個字母').toUpperCase(),
  name: z.string().min(1, '貨幣名稱為必填').max(100),
  symbol: z.string().min(1, '貨幣符號為必填').max(10),
  exchangeRate: z.number().positive().optional(),
  active: z.boolean().default(true),
});

export const updateCurrencySchema = z.object({
  id: z.string().uuid(),
  code: z.string().length(3).toUpperCase().optional(),
  name: z.string().min(1).max(100).optional(),
  symbol: z.string().min(1).max(10).optional(),
  exchangeRate: z.number().positive().optional(),
  active: z.boolean().optional(),
});

export const currencyRouter = createTRPCRouter({
  // 建立新貨幣（僅管理員）
  create: adminProcedure
    .input(createCurrencySchema)
    .mutation(async ({ ctx, input }) => {
      // 檢查貨幣代碼是否已存在
      const existing = await ctx.prisma.currency.findUnique({
        where: { code: input.code },
      });

      if (existing) {
        throw new TRPCError({
          code: 'CONFLICT',
          message: `貨幣代碼 ${input.code} 已存在`,
        });
      }

      return ctx.prisma.currency.create({
        data: input,
      });
    }),

  // 更新貨幣（僅管理員）
  update: adminProcedure
    .input(updateCurrencySchema)
    .mutation(async ({ ctx, input }) => {
      const { id, ...data } = input;

      // 如果更新貨幣代碼，檢查唯一性
      if (data.code) {
        const existing = await ctx.prisma.currency.findFirst({
          where: {
            code: data.code,
            id: { not: id },
          },
        });

        if (existing) {
          throw new TRPCError({
            code: 'CONFLICT',
            message: `貨幣代碼 ${data.code} 已存在`,
          });
        }
      }

      return ctx.prisma.currency.update({
        where: { id },
        data,
      });
    }),

  // 刪除貨幣（僅管理員）
  delete: adminProcedure
    .input(z.object({ id: z.string().uuid() }))
    .mutation(async ({ ctx, input }) => {
      // 檢查是否有專案使用此貨幣
      const projectCount = await ctx.prisma.project.count({
        where: { currencyId: input.id },
      });

      if (projectCount > 0) {
        throw new TRPCError({
          code: 'CONFLICT',
          message: `無法刪除此貨幣，有 ${projectCount} 個專案正在使用`,
        });
      }

      return ctx.prisma.currency.delete({
        where: { id: input.id },
      });
    }),

  // 查詢所有貨幣（含停用的）
  getAll: protectedProcedure
    .input(z.object({
      includeInactive: z.boolean().default(false),
    }))
    .query(async ({ ctx, input }) => {
      return ctx.prisma.currency.findMany({
        where: input.includeInactive ? {} : { active: true },
        orderBy: { code: 'asc' },
      });
    }),

  // 查詢啟用的貨幣（用於表單選項）
  getActive: protectedProcedure
    .query(async ({ ctx }) => {
      return ctx.prisma.currency.findMany({
        where: { active: true },
        orderBy: { code: 'asc' },
        select: {
          id: true,
          code: true,
          name: true,
          symbol: true,
        },
      });
    }),

  // 查詢單一貨幣詳情
  getById: protectedProcedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ ctx, input }) => {
      const currency = await ctx.prisma.currency.findUnique({
        where: { id: input.id },
        include: {
          _count: {
            select: { projects: true },
          },
        },
      });

      if (!currency) {
        throw new TRPCError({
          code: 'NOT_FOUND',
          message: '找不到此貨幣',
        });
      }

      return currency;
    }),

  // 切換貨幣啟用狀態
  toggleActive: adminProcedure
    .input(z.object({ id: z.string().uuid() }))
    .mutation(async ({ ctx, input }) => {
      const currency = await ctx.prisma.currency.findUnique({
        where: { id: input.id },
      });

      if (!currency) {
        throw new TRPCError({
          code: 'NOT_FOUND',
          message: '找不到此貨幣',
        });
      }

      return ctx.prisma.currency.update({
        where: { id: input.id },
        data: { active: !currency.active },
      });
    }),
});
```

### 2. Project Router（更新）

**檔案**: `packages/api/src/routers/project.ts`

**更新內容**:

```typescript
// 更新 createProjectSchema
export const createProjectSchema = z.object({
  // ... 現有欄位 ...

  // 新增欄位
  projectCode: z.string()
    .min(1, '專案編號為必填')
    .max(50, '專案編號最多 50 個字元')
    .regex(/^[A-Za-z0-9_-]+$/, '專案編號只能包含字母、數字、連字號和底線'),
  globalFlag: z.enum(['RCL', 'Region']).default('Region'),
  priority: z.enum(['High', 'Medium', 'Low']).default('Medium'),
  currencyId: z.string().uuid('無效的貨幣 ID').optional(),
});

// 更新 updateProjectSchema
export const updateProjectSchema = z.object({
  id: z.string().uuid(),
  // ... 現有欄位 ...

  // 新增欄位
  projectCode: z.string()
    .min(1)
    .max(50)
    .regex(/^[A-Za-z0-9_-]+$/)
    .optional(),
  globalFlag: z.enum(['RCL', 'Region']).optional(),
  priority: z.enum(['High', 'Medium', 'Low']).optional(),
  currencyId: z.string().uuid().optional(),
});

// 新增專案編號唯一性檢查 procedure
export const projectRouter = createTRPCRouter({
  // ... 現有 procedures ...

  // 新增：檢查專案編號是否可用
  checkCodeAvailability: protectedProcedure
    .input(z.object({
      code: z.string(),
      excludeId: z.string().uuid().optional(), // 編輯模式時排除自己
    }))
    .query(async ({ ctx, input }) => {
      const existing = await ctx.prisma.project.findFirst({
        where: {
          projectCode: input.code,
          ...(input.excludeId && { id: { not: input.excludeId } }),
        },
      });

      return {
        available: !existing,
        message: existing ? '此專案編號已被使用' : '此專案編號可使用',
      };
    }),

  // 更新 create procedure
  create: protectedProcedure
    .input(createProjectSchema)
    .mutation(async ({ ctx, input }) => {
      // 檢查專案編號唯一性
      const existingCode = await ctx.prisma.project.findUnique({
        where: { projectCode: input.projectCode },
      });

      if (existingCode) {
        throw new TRPCError({
          code: 'CONFLICT',
          message: '此專案編號已存在，請使用其他編號',
        });
      }

      // 如果有指定貨幣，驗證貨幣是否存在且啟用
      if (input.currencyId) {
        const currency = await ctx.prisma.currency.findFirst({
          where: {
            id: input.currencyId,
            active: true,
          },
        });

        if (!currency) {
          throw new TRPCError({
            code: 'BAD_REQUEST',
            message: '指定的貨幣不存在或已停用',
          });
        }
      }

      return ctx.prisma.project.create({
        data: input,
        include: {
          manager: true,
          supervisor: true,
          budgetPool: true,
          budgetCategory: true,
          currency: true, // 新增：包含貨幣資訊
        },
      });
    }),

  // 更新 getAll procedure（新增篩選和排序）
  getAll: protectedProcedure
    .input(z.object({
      page: z.number().min(1).default(1),
      limit: z.number().min(1).max(100).default(10),
      search: z.string().optional(),
      status: z.string().optional(),
      globalFlag: z.enum(['RCL', 'Region']).optional(),  // 新增篩選
      priority: z.enum(['High', 'Medium', 'Low']).optional(),  // 新增篩選
      currencyId: z.string().uuid().optional(),  // 新增篩選
      sortBy: z.enum(['name', 'createdAt', 'projectCode', 'priority']).default('createdAt'),  // 新增排序
      sortOrder: z.enum(['asc', 'desc']).default('desc'),
    }))
    .query(async ({ ctx, input }) => {
      const where = {
        ...(input.search && {
          OR: [
            { name: { contains: input.search, mode: 'insensitive' } },
            { projectCode: { contains: input.search, mode: 'insensitive' } },  // 新增搜尋
            { description: { contains: input.search, mode: 'insensitive' } },
          ],
        }),
        ...(input.status && { status: input.status }),
        ...(input.globalFlag && { globalFlag: input.globalFlag }),  // 新增篩選
        ...(input.priority && { priority: input.priority }),  // 新增篩選
        ...(input.currencyId && { currencyId: input.currencyId }),  // 新增篩選
      };

      // 優先權排序邏輯
      let orderBy = {};
      if (input.sortBy === 'priority') {
        // High > Medium > Low
        orderBy = [
          { priority: input.sortOrder },
          { createdAt: 'desc' },
        ];
      } else {
        orderBy = { [input.sortBy]: input.sortOrder };
      }

      const [projects, total] = await Promise.all([
        ctx.prisma.project.findMany({
          where,
          skip: (input.page - 1) * input.limit,
          take: input.limit,
          orderBy,
          include: {
            manager: true,
            supervisor: true,
            budgetPool: true,
            budgetCategory: true,
            currency: {  // 新增：包含貨幣資訊
              select: {
                id: true,
                code: true,
                name: true,
                symbol: true,
              },
            },
          },
        }),
        ctx.prisma.project.count({ where }),
      ]);

      return {
        projects,
        pagination: {
          total,
          page: input.page,
          limit: input.limit,
          totalPages: Math.ceil(total / input.limit),
        },
      };
    }),
});
```

**API 關鍵設計決策**:
1. **專案編號唯一性**: 新增 `checkCodeAvailability` procedure 用於即時驗證
2. **貨幣驗證**: create/update 時檢查貨幣是否啟用
3. **軟刪除貨幣**: 使用 `active` 欄位而非真刪除
4. **管理員權限**: Currency CRUD 使用 `adminProcedure`
5. **篩選增強**: getAll 新增 globalFlag, priority, currencyId 篩選器
6. **排序增強**: 新增 projectCode 和 priority 排序

---

## 🎨 前端設計

### 1. ProjectForm 組件更新

**檔案**: `apps/web/src/components/project/ProjectForm.tsx`

**新增狀態**:
```typescript
interface ProjectFormProps {
  initialData?: {
    // ... 現有欄位 ...
    projectCode?: string;        // 新增
    globalFlag?: 'RCL' | 'Region';  // 新增
    priority?: 'High' | 'Medium' | 'Low';  // 新增
    currencyId?: string;         // 新增
  };
  mode: 'create' | 'edit';
}

const [formData, setFormData] = useState({
  // ... 現有欄位 ...
  projectCode: initialData?.projectCode || '',
  globalFlag: initialData?.globalFlag || 'Region',
  priority: initialData?.priority || 'Medium',
  currencyId: initialData?.currencyId || '',
});

// 新增：專案編號唯一性驗證
const [codeCheckStatus, setCodeCheckStatus] = useState<{
  checking: boolean;
  available: boolean | null;
  message: string;
}>({
  checking: false,
  available: null,
  message: '',
});

// Debounced 專案編號檢查
const checkCodeDebounced = useMemo(
  () =>
    debounce(async (code: string) => {
      if (!code) {
        setCodeCheckStatus({ checking: false, available: null, message: '' });
        return;
      }

      setCodeCheckStatus({ checking: true, available: null, message: '檢查中...' });

      const result = await api.project.checkCodeAvailability.query({
        code,
        excludeId: mode === 'edit' ? initialData?.id : undefined,
      });

      setCodeCheckStatus({
        checking: false,
        available: result.available,
        message: result.message,
      });
    }, 500),
  [mode, initialData?.id]
);
```

**新增欄位 UI**:
```tsx
{/* 專案編號 */}
<div>
  <Label htmlFor="projectCode">{t('form.projectCode.label')} *</Label>
  <Input
    id="projectCode"
    value={formData.projectCode}
    onChange={(e) => {
      setFormData({ ...formData, projectCode: e.target.value });
      checkCodeDebounced(e.target.value);
    }}
    placeholder={t('form.projectCode.placeholder')}
    className={cn(
      codeCheckStatus.available === false && 'border-red-500',
      codeCheckStatus.available === true && 'border-green-500'
    )}
  />
  {codeCheckStatus.message && (
    <p className={cn(
      'text-sm mt-1',
      codeCheckStatus.checking && 'text-gray-500',
      codeCheckStatus.available === false && 'text-red-500',
      codeCheckStatus.available === true && 'text-green-500'
    )}>
      {codeCheckStatus.message}
    </p>
  )}
</div>

{/* 全域標誌 */}
<div>
  <Label htmlFor="globalFlag">{t('form.globalFlag.label')} *</Label>
  <Select
    value={formData.globalFlag}
    onValueChange={(value) => setFormData({ ...formData, globalFlag: value as 'RCL' | 'Region' })}
  >
    <SelectTrigger>
      <SelectValue />
    </SelectTrigger>
    <SelectContent>
      <SelectItem value="RCL">
        <span className="flex items-center gap-2">
          🌍 {t('form.globalFlag.options.rcl')}
        </span>
      </SelectItem>
      <SelectItem value="Region">
        <span className="flex items-center gap-2">
          📍 {t('form.globalFlag.options.region')}
        </span>
      </SelectItem>
    </SelectContent>
  </Select>
</div>

{/* 優先權 */}
<div>
  <Label htmlFor="priority">{t('form.priority.label')} *</Label>
  <Select
    value={formData.priority}
    onValueChange={(value) => setFormData({ ...formData, priority: value as 'High' | 'Medium' | 'Low' })}
  >
    <SelectTrigger>
      <SelectValue />
    </SelectTrigger>
    <SelectContent>
      <SelectItem value="High">
        <span className="flex items-center gap-2">
          🔴 {t('form.priority.options.high')}
        </span>
      </SelectItem>
      <SelectItem value="Medium">
        <span className="flex items-center gap-2">
          🟡 {t('form.priority.options.medium')}
        </span>
      </SelectItem>
      <SelectItem value="Low">
        <span className="flex items-center gap-2">
          🟢 {t('form.priority.options.low')}
        </span>
      </SelectItem>
    </SelectContent>
  </Select>
</div>

{/* 貨幣 */}
<div>
  <Label htmlFor="currency">{t('form.currency.label')} *</Label>
  <Combobox
    options={activeCurrencies.map(c => ({
      value: c.id,
      label: `${c.code} - ${c.name}`,
    }))}
    value={formData.currencyId}
    onChange={(value) => setFormData({ ...formData, currencyId: value })}
    placeholder={t('form.currency.placeholder')}
    searchPlaceholder={t('form.currency.searchPlaceholder')}
  />
</div>
```

### 2. 專案列表頁更新

**檔案**: `apps/web/src/app/[locale]/projects/page.tsx`

**新增篩選器**:
```tsx
{/* 全域標誌篩選 */}
<Select
  value={filters.globalFlag || 'all'}
  onValueChange={(value) => setFilters({
    ...filters,
    globalFlag: value === 'all' ? undefined : value as 'RCL' | 'Region',
  })}
>
  <SelectTrigger className="w-[150px]">
    <SelectValue placeholder={t('filters.globalFlag.label')} />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="all">{t('filters.all')}</SelectItem>
    <SelectItem value="RCL">🌍 RCL</SelectItem>
    <SelectItem value="Region">📍 Region</SelectItem>
  </SelectContent>
</Select>

{/* 優先權篩選 */}
<Select
  value={filters.priority || 'all'}
  onValueChange={(value) => setFilters({
    ...filters,
    priority: value === 'all' ? undefined : value as 'High' | 'Medium' | 'Low',
  })}
>
  <SelectTrigger className="w-[150px]">
    <SelectValue placeholder={t('filters.priority.label')} />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="all">{t('filters.all')}</SelectItem>
    <SelectItem value="High">🔴 {t('priority.high')}</SelectItem>
    <SelectItem value="Medium">🟡 {t('priority.medium')}</SelectItem>
    <SelectItem value="Low">🟢 {t('priority.low')}</SelectItem>
  </SelectContent>
</Select>
```

**新增表格列**:
```tsx
<Table>
  <TableHeader>
    <TableRow>
      <TableHead
        className="cursor-pointer"
        onClick={() => handleSort('projectCode')}
      >
        {t('table.projectCode')}
        <SortIcon field="projectCode" />
      </TableHead>
      <TableHead>{t('table.name')}</TableHead>
      <TableHead>{t('table.globalFlag')}</TableHead>
      <TableHead
        className="cursor-pointer"
        onClick={() => handleSort('priority')}
      >
        {t('table.priority')}
        <SortIcon field="priority" />
      </TableHead>
      <TableHead>{t('table.currency')}</TableHead>
      {/* ... 其他列 ... */}
    </TableRow>
  </TableHeader>
  <TableBody>
    {projects.map((project) => (
      <TableRow key={project.id}>
        <TableCell className="font-mono">{project.projectCode}</TableCell>
        <TableCell>{project.name}</TableCell>
        <TableCell>
          <Badge variant={project.globalFlag === 'RCL' ? 'default' : 'secondary'}>
            {project.globalFlag === 'RCL' ? '🌍 RCL' : '📍 Region'}
          </Badge>
        </TableCell>
        <TableCell>
          <Badge variant={getPriorityVariant(project.priority)}>
            {getPriorityIcon(project.priority)} {t(`priority.${project.priority.toLowerCase()}`)}
          </Badge>
        </TableCell>
        <TableCell>
          {project.currency?.code || '-'}
        </TableCell>
        {/* ... 其他列 ... */}
      </TableRow>
    ))}
  </TableBody>
</Table>
```

### 3. 貨幣管理頁面（新增）

**檔案**: `apps/web/src/app/[locale]/settings/currencies/page.tsx`

**頁面結構**:
```tsx
export default function CurrenciesPage() {
  const { data: currencies } = api.currency.getAll.useQuery({
    includeInactive: true,
  });

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">{t('title')}</h1>
          <Button onClick={() => router.push('/settings/currencies/new')}>
            <Plus className="mr-2 h-4 w-4" />
            {t('actions.create')}
          </Button>
        </div>

        {/* 貨幣列表 */}
        <Card>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t('table.code')}</TableHead>
                  <TableHead>{t('table.name')}</TableHead>
                  <TableHead>{t('table.symbol')}</TableHead>
                  <TableHead>{t('table.exchangeRate')}</TableHead>
                  <TableHead>{t('table.status')}</TableHead>
                  <TableHead>{t('table.projectCount')}</TableHead>
                  <TableHead className="text-right">{t('table.actions')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {currencies?.map((currency) => (
                  <TableRow key={currency.id}>
                    <TableCell className="font-mono">{currency.code}</TableCell>
                    <TableCell>{currency.name}</TableCell>
                    <TableCell>{currency.symbol}</TableCell>
                    <TableCell>{currency.exchangeRate || '-'}</TableCell>
                    <TableCell>
                      <Badge variant={currency.active ? 'default' : 'secondary'}>
                        {currency.active ? t('status.active') : t('status.inactive')}
                      </Badge>
                    </TableCell>
                    <TableCell>{currency._count.projects}</TableCell>
                    <TableCell className="text-right">
                      <CurrencyActions currency={currency} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
```

---

## 🌍 I18N 翻譯設計

### 繁體中文 (`apps/web/src/messages/zh-TW.json`)

```json
{
  "projects": {
    "form": {
      "projectCode": {
        "label": "專案編號",
        "placeholder": "請輸入專案編號（如 PROJ-2025-001）",
        "validation": {
          "required": "專案編號為必填",
          "maxLength": "專案編號最多 50 個字元",
          "pattern": "專案編號只能包含字母、數字、連字號和底線",
          "duplicate": "此專案編號已存在，請使用其他編號"
        },
        "checking": "檢查中...",
        "available": "此專案編號可使用",
        "unavailable": "此專案編號已被使用"
      },
      "globalFlag": {
        "label": "全域標誌",
        "options": {
          "rcl": "RCL (Regional/Corporate Level)",
          "region": "Region (區域)"
        }
      },
      "priority": {
        "label": "優先權",
        "options": {
          "high": "高",
          "medium": "中",
          "low": "低"
        }
      },
      "currency": {
        "label": "貨幣",
        "placeholder": "選擇貨幣",
        "searchPlaceholder": "搜尋貨幣代碼或名稱"
      }
    },
    "table": {
      "projectCode": "專案編號",
      "globalFlag": "全域標誌",
      "priority": "優先權",
      "currency": "貨幣"
    },
    "filters": {
      "globalFlag": {
        "label": "全域標誌",
        "all": "全部"
      },
      "priority": {
        "label": "優先權",
        "all": "全部"
      }
    }
  },
  "currencies": {
    "title": "貨幣管理",
    "table": {
      "code": "貨幣代碼",
      "name": "貨幣名稱",
      "symbol": "符號",
      "exchangeRate": "匯率",
      "status": "狀態",
      "projectCount": "使用專案數",
      "actions": "操作"
    },
    "form": {
      "code": {
        "label": "貨幣代碼",
        "placeholder": "ISO 4217 代碼（如 TWD, USD）",
        "validation": {
          "required": "貨幣代碼為必填",
          "length": "貨幣代碼必須為 3 個字母",
          "uppercase": "貨幣代碼必須為大寫字母",
          "duplicate": "此貨幣代碼已存在"
        }
      },
      "name": {
        "label": "貨幣名稱",
        "placeholder": "如：新台幣、美元"
      },
      "symbol": {
        "label": "貨幣符號",
        "placeholder": "如：NT$, $, €"
      },
      "exchangeRate": {
        "label": "匯率（可選）",
        "placeholder": "對基準貨幣的匯率"
      },
      "active": {
        "label": "啟用狀態",
        "description": "停用的貨幣不會在表單中顯示"
      }
    },
    "actions": {
      "create": "新增貨幣",
      "edit": "編輯",
      "delete": "刪除",
      "toggleActive": "切換狀態"
    },
    "status": {
      "active": "啟用",
      "inactive": "停用"
    },
    "messages": {
      "createSuccess": "貨幣建立成功",
      "updateSuccess": "貨幣更新成功",
      "deleteSuccess": "貨幣刪除成功",
      "deleteError": "無法刪除此貨幣，有 {count} 個專案正在使用"
    }
  }
}
```

### 英文 (`apps/web/src/messages/en.json`)

```json
{
  "projects": {
    "form": {
      "projectCode": {
        "label": "Project Code",
        "placeholder": "Enter project code (e.g., PROJ-2025-001)",
        "validation": {
          "required": "Project code is required",
          "maxLength": "Project code must be at most 50 characters",
          "pattern": "Project code can only contain letters, numbers, hyphens, and underscores",
          "duplicate": "This project code already exists, please use another one"
        },
        "checking": "Checking...",
        "available": "This project code is available",
        "unavailable": "This project code is already in use"
      },
      "globalFlag": {
        "label": "Global Flag",
        "options": {
          "rcl": "RCL (Regional/Corporate Level)",
          "region": "Region"
        }
      },
      "priority": {
        "label": "Priority",
        "options": {
          "high": "High",
          "medium": "Medium",
          "low": "Low"
        }
      },
      "currency": {
        "label": "Currency",
        "placeholder": "Select currency",
        "searchPlaceholder": "Search currency code or name"
      }
    },
    "table": {
      "projectCode": "Project Code",
      "globalFlag": "Global Flag",
      "priority": "Priority",
      "currency": "Currency"
    },
    "filters": {
      "globalFlag": {
        "label": "Global Flag",
        "all": "All"
      },
      "priority": {
        "label": "Priority",
        "all": "All"
      }
    }
  },
  "currencies": {
    "title": "Currency Management",
    "table": {
      "code": "Currency Code",
      "name": "Currency Name",
      "symbol": "Symbol",
      "exchangeRate": "Exchange Rate",
      "status": "Status",
      "projectCount": "Project Count",
      "actions": "Actions"
    },
    "form": {
      "code": {
        "label": "Currency Code",
        "placeholder": "ISO 4217 code (e.g., TWD, USD)",
        "validation": {
          "required": "Currency code is required",
          "length": "Currency code must be 3 letters",
          "uppercase": "Currency code must be uppercase",
          "duplicate": "This currency code already exists"
        }
      },
      "name": {
        "label": "Currency Name",
        "placeholder": "e.g., New Taiwan Dollar, US Dollar"
      },
      "symbol": {
        "label": "Currency Symbol",
        "placeholder": "e.g., NT$, $, €"
      },
      "exchangeRate": {
        "label": "Exchange Rate (optional)",
        "placeholder": "Exchange rate to base currency"
      },
      "active": {
        "label": "Active Status",
        "description": "Inactive currencies will not be displayed in forms"
      }
    },
    "actions": {
      "create": "Create Currency",
      "edit": "Edit",
      "delete": "Delete",
      "toggleActive": "Toggle Status"
    },
    "status": {
      "active": "Active",
      "inactive": "Inactive"
    },
    "messages": {
      "createSuccess": "Currency created successfully",
      "updateSuccess": "Currency updated successfully",
      "deleteSuccess": "Currency deleted successfully",
      "deleteError": "Cannot delete this currency, {count} projects are using it"
    }
  }
}
```

---

## 🧪 測試策略

### 1. 單元測試（API Layer）

**檔案**: `packages/api/src/routers/currency.test.ts`

```typescript
describe('Currency Router', () => {
  describe('create', () => {
    it('should create a new currency', async () => {
      const result = await caller.currency.create({
        code: 'TWD',
        name: '新台幣',
        symbol: 'NT$',
        exchangeRate: 1.0,
      });

      expect(result.code).toBe('TWD');
      expect(result.active).toBe(true);
    });

    it('should reject duplicate currency code', async () => {
      await caller.currency.create({
        code: 'TWD',
        name: '新台幣',
        symbol: 'NT$',
      });

      await expect(
        caller.currency.create({
          code: 'TWD',
          name: 'Duplicate',
          symbol: 'NT$',
        })
      ).rejects.toThrow('貨幣代碼 TWD 已存在');
    });

    it('should automatically uppercase currency code', async () => {
      const result = await caller.currency.create({
        code: 'usd',
        name: '美元',
        symbol: '$',
      });

      expect(result.code).toBe('USD');
    });
  });

  describe('checkCodeAvailability', () => {
    it('should return available for new code', async () => {
      const result = await caller.project.checkCodeAvailability({
        code: 'PROJ-NEW-001',
      });

      expect(result.available).toBe(true);
    });

    it('should return unavailable for existing code', async () => {
      await createProject({ projectCode: 'PROJ-EXISTS-001' });

      const result = await caller.project.checkCodeAvailability({
        code: 'PROJ-EXISTS-001',
      });

      expect(result.available).toBe(false);
    });

    it('should exclude own ID in edit mode', async () => {
      const project = await createProject({ projectCode: 'PROJ-EDIT-001' });

      const result = await caller.project.checkCodeAvailability({
        code: 'PROJ-EDIT-001',
        excludeId: project.id,
      });

      expect(result.available).toBe(true);
    });
  });
});
```

### 2. E2E 測試（Playwright）

**檔案**: `apps/web/e2e/project-fields.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Project Fields Enhancement', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'testuser@example.com');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/dashboard');
  });

  test('should create project with new fields', async ({ page }) => {
    await page.goto('/projects/new');

    // 填寫新欄位
    await page.fill('[name="projectCode"]', 'E2E-TEST-001');
    await page.fill('[name="name"]', 'E2E Test Project');

    // 選擇全域標誌
    await page.click('[data-testid="globalFlag-select"]');
    await page.click('text=RCL');

    // 選擇優先權
    await page.click('[data-testid="priority-select"]');
    await page.click('text=High');

    // 選擇貨幣
    await page.click('[data-testid="currency-combobox"]');
    await page.fill('[placeholder="搜尋貨幣"]', 'TWD');
    await page.click('text=TWD - 新台幣');

    // ... 填寫其他必填欄位 ...

    // 提交表單
    await page.click('button[type="submit"]');

    // 驗證成功訊息
    await expect(page.locator('text=專案建立成功')).toBeVisible();

    // 驗證列表頁顯示新欄位
    await page.goto('/projects');
    const row = page.locator('tr:has-text("E2E-TEST-001")');
    await expect(row).toContainText('🌍 RCL');
    await expect(row).toContainText('🔴');
    await expect(row).toContainText('TWD');
  });

  test('should validate project code uniqueness', async ({ page }) => {
    // 創建第一個專案
    await createProject({ projectCode: 'UNIQUE-001' });

    // 嘗試創建重複編號的專案
    await page.goto('/projects/new');
    await page.fill('[name="projectCode"]', 'UNIQUE-001');

    // 等待 debounce 和驗證
    await page.waitForTimeout(600);

    // 驗證錯誤訊息
    await expect(page.locator('text=此專案編號已被使用')).toBeVisible();
    await expect(page.locator('[name="projectCode"]')).toHaveClass(/border-red-500/);

    // 修改為可用編號
    await page.fill('[name="projectCode"]', 'UNIQUE-002');
    await page.waitForTimeout(600);

    // 驗證成功訊息
    await expect(page.locator('text=此專案編號可使用')).toBeVisible();
    await expect(page.locator('[name="projectCode"]')).toHaveClass(/border-green-500/);
  });

  test('should filter projects by new fields', async ({ page }) => {
    // 創建測試資料
    await createProject({ globalFlag: 'RCL', priority: 'High' });
    await createProject({ globalFlag: 'Region', priority: 'Low' });

    await page.goto('/projects');

    // 篩選全域標誌
    await page.click('[data-testid="globalFlag-filter"]');
    await page.click('text=RCL');
    await expect(page.locator('tbody tr')).toHaveCount(1);

    // 重置篩選
    await page.click('[data-testid="globalFlag-filter"]');
    await page.click('text=全部');

    // 篩選優先權
    await page.click('[data-testid="priority-filter"]');
    await page.click('text=🔴 高');
    await expect(page.locator('tbody tr')).toHaveCount(1);
  });

  test('should sort projects by priority', async ({ page }) => {
    await createProject({ projectCode: 'HIGH-001', priority: 'High' });
    await createProject({ projectCode: 'LOW-001', priority: 'Low' });
    await createProject({ projectCode: 'MED-001', priority: 'Medium' });

    await page.goto('/projects');

    // 點擊優先權排序
    await page.click('th:has-text("優先權")');

    // 驗證排序（High > Medium > Low）
    const codes = await page.locator('tbody tr td:first-child').allTextContents();
    expect(codes).toEqual(['HIGH-001', 'MED-001', 'LOW-001']);
  });
});

test.describe('Currency Management', () => {
  test('should create new currency', async ({ page }) => {
    await page.goto('/settings/currencies');
    await page.click('text=新增貨幣');

    await page.fill('[name="code"]', 'SGD');
    await page.fill('[name="name"]', '新加坡幣');
    await page.fill('[name="symbol"]', 'S$');
    await page.fill('[name="exchangeRate"]', '22.5');

    await page.click('button[type="submit"]');

    await expect(page.locator('text=貨幣建立成功')).toBeVisible();
    await expect(page.locator('text=SGD')).toBeVisible();
  });

  test('should not delete currency in use', async ({ page }) => {
    // 創建貨幣並使用於專案
    const currency = await createCurrency({ code: 'EUR' });
    await createProject({ currencyId: currency.id });

    await page.goto('/settings/currencies');
    await page.click(`[data-testid="delete-currency-${currency.id}"]`);
    await page.click('text=確認刪除');

    await expect(page.locator('text=無法刪除此貨幣，有 1 個專案正在使用')).toBeVisible();
  });

  test('should toggle currency active status', async ({ page }) => {
    const currency = await createCurrency({ code: 'JPY', active: true });

    await page.goto('/settings/currencies');
    await page.click(`[data-testid="toggle-active-${currency.id}"]`);

    await expect(page.locator('text=停用').first()).toBeVisible();

    // 驗證停用的貨幣不在專案表單中顯示
    await page.goto('/projects/new');
    await page.click('[data-testid="currency-combobox"]');
    await expect(page.locator('text=JPY')).not.toBeVisible();
  });
});
```

---

## 📝 總結

本技術設計文檔詳細說明了 FEAT-001 的實施細節：

### 關鍵技術決策
1. **資料庫設計**: 新增 Currency Model，更新 Project Model，使用索引優化查詢
2. **API 設計**: 新增 Currency Router，更新 Project Router，實作唯一性驗證
3. **前端設計**: 更新 ProjectForm、列表頁、詳情頁，新增貨幣管理頁面
4. **Migration 策略**: 自動為現有專案設定預設值，避免資料遺失
5. **測試策略**: 單元測試 + E2E 測試，確保功能正確性

### 下一步
閱讀 [03-implementation-plan.md](./03-implementation-plan.md) 了解詳細的實施步驟和時程安排。

---

**文檔維護者**: AI Assistant + 開發團隊
**最後更新**: 2025-11-14
**狀態**: ✅ 技術設計完成，待審查
