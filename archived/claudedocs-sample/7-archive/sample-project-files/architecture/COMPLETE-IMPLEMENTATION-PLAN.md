# IT 專案流程管理平台 - 完整實施計劃

> **生成日期**: 2025-10-26
> **版本**: 2.0
> **基於**: 用戶需求澄清和優先級確認
> **估計總工時**: 35-40 工作天（7-8 週）

---

## 📋 執行摘要

### 重要澄清

1. **項目計劃書 = 預算提案 (BudgetProposal)**
   - 不需要新增獨立的 ProjectProposal 模型
   - 需要擴展現有的 BudgetProposal 模型以支持：
     * 計劃書文件上傳
     * 會議記錄功能
     * 介紹人員信息

2. **確認的模塊優先順序**:
   ```
   1. 預算池 (Budget Pool)           - 需重構支持多類別
   2. 項目管理 (Project)              - 需新增欄位
   3. 預算提案 (Budget Proposal)      - 需擴展功能
   4. 採購管理 (Purchase Order)       - 需新增表頭-明細
   5. 支出/費用管理 (Expense)         - 需重構和擴展
   6. 操作與維護費用 (OM Expense)     - 需新增模塊
   7. 費用轉嫁 (Charge Out)           - 需新增模塊
   8. 費用轉嫁確認 (Charge Out Conf)  - 需新增工作流
   ```

### 核心設計原則

- **UI/UX**: 基於現有 shadcn/ui + Radix UI 設計系統
- **設計風格**: 保持與現有系統一致（專業、簡潔、高效）
- **色彩方案**: Light/Dark 雙主題支持
- **響應式**: Mobile-first 設計理念
- **可訪問性**: WCAG 2.1 AA 標準

---

## 🎨 UI/UX 設計規範

### 設計系統基礎

#### 色彩系統 (基於現有設計)

```css
/* Light Mode */
--background: 0 0% 100%;        /* 白色背景 */
--foreground: 222.2 84% 4.9%;   /* 深色文字 */
--card: 0 0% 100%;              /* 卡片背景 */
--card-foreground: 222.2 84% 4.9%;
--primary: 221.2 83.2% 53.3%;   /* 主色調（藍色）*/
--primary-foreground: 210 40% 98%;
--secondary: 210 40% 96.1%;     /* 次要色 */
--muted: 210 40% 96.1%;         /* 靜音色 */
--accent: 210 40% 96.1%;        /* 強調色 */
--destructive: 0 84.2% 60.2%;   /* 破壞性操作（紅色）*/
--border: 214.3 31.8% 91.4%;    /* 邊框色 */
--input: 214.3 31.8% 91.4%;     /* 輸入框 */
--ring: 221.2 83.2% 53.3%;      /* 焦點環 */

/* Dark Mode */
--background: 222.2 84% 4.9%;
--foreground: 210 40% 98%;
--primary: 217.2 91.2% 59.8%;
/* ... 其他暗色模式顏色 */
```

#### 業務狀態色彩

```css
/* 預算池健康狀態 */
.budget-healthy   { @apply bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300; }
.budget-warning   { @apply bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300; }
.budget-critical  { @apply bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300; }

/* 審批狀態 */
.status-draft     { @apply bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300; }
.status-pending   { @apply bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300; }
.status-approved  { @apply bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300; }
.status-rejected  { @apply bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300; }
.status-moreinfo  { @apply bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300; }
```

#### 組件庫擴展

基於現有 26 個 shadcn/ui 組件，新增：

```yaml
需要新增的組件:
  - FileUpload: 文件上傳組件（支持拖放）
  - DataTable: 可編輯數據表格（for 明細）
  - MonthlyGrid: 月度數據輸入網格
  - StatusBadge: 狀態徽章組件
  - AmountDisplay: 金額顯示組件（支持格式化）
  - CategorySelect: 分類選擇器
  - OpCoSelect: OpCo 選擇器
```

---

## 📊 模塊詳細設計

## 模塊 1: 預算池 (Budget Pool) - 多類別重構

### 業務需求重述

```yaml
核心需求:
  - 一個預算池包含多個預算類別（Hardware, Software, Services等）
  - 每個類別有獨立的預算金額和使用追蹤
  - 支持按類別查看預算使用情況
  - 關聯的項目可以指定使用哪個類別的預算
```

### 數據庫 Schema 設計

#### 新增 BudgetCategory 模型

```prisma
// ✅ 新增：預算類別
model BudgetCategory {
  id          String   @id @default(uuid())
  budgetPoolId String  // 所屬預算池

  // 分類信息
  categoryName String  // "Hardware", "Software", "Services", "Consulting", etc.
  categoryCode String? // 可選的類別代碼（如 HW, SW, SVC）
  description  String? // 類別描述

  // 預算金額
  totalAmount  Float   // 該類別的總預算
  usedAmount   Float   @default(0)  // 已使用金額

  // 元數據
  sortOrder    Int     @default(0)  // 顯示順序
  isActive     Boolean @default(true)
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt

  // 關聯
  budgetPool   BudgetPool @relation(fields: [budgetPoolId], references: [id], onDelete: Cascade)
  projects     Project[]  // 使用此類別的項目
  expenses     Expense[]  // 關聯的支出

  @@unique([budgetPoolId, categoryName])
  @@index([budgetPoolId])
  @@index([isActive])
}
```

#### 修改 BudgetPool 模型

```prisma
model BudgetPool {
  id            String   @id @default(uuid())
  name          String   // 如: "FY2025 IT Budget"

  // ❌ 移除: totalAmount, usedAmount (改由 categories 計算)
  // ✅ 保留: financialYear
  financialYear Int
  description   String?  // ✅ 新增：預算池描述

  createdAt     DateTime @default(now())
  updatedAt     DateTime @updatedAt

  // 關聯
  categories    BudgetCategory[]  // ✅ 新增：多個預算類別
  projects      Project[]

  @@index([financialYear])
}
```

### 後端 API 設計 (tRPC)

```typescript
// packages/api/src/routers/budgetPool.ts

export const budgetPoolRouter = createTRPCRouter({

  // ========== BudgetPool CRUD ==========

  /**
   * 獲取所有預算池（含類別摘要）
   */
  getAll: protectedProcedure
    .input(z.object({
      financialYear: z.number().optional(),
      page: z.number().default(1),
      limit: z.number().max(100).default(20),
    }))
    .query(async ({ ctx, input }) => {
      const pools = await ctx.prisma.budgetPool.findMany({
        where: {
          ...(input.financialYear && { financialYear: input.financialYear }),
        },
        include: {
          categories: {
            where: { isActive: true },
            orderBy: { sortOrder: 'asc' },
          },
          _count: {
            select: { projects: true },
          },
        },
        skip: (input.page - 1) * input.limit,
        take: input.limit,
        orderBy: { financialYear: 'desc' },
      });

      // 計算總預算和已用金額
      const poolsWithTotals = pools.map(pool => ({
        ...pool,
        totalAmount: pool.categories.reduce((sum, cat) => sum + cat.totalAmount, 0),
        usedAmount: pool.categories.reduce((sum, cat) => sum + cat.usedAmount, 0),
      }));

      return { items: poolsWithTotals, pagination: {...} };
    }),

  /**
   * 獲取單個預算池詳情（含所有類別）
   */
  getById: protectedProcedure
    .input(z.object({ id: z.string().min(1) }))
    .query(async ({ ctx, input }) => {
      const pool = await ctx.prisma.budgetPool.findUnique({
        where: { id: input.id },
        include: {
          categories: {
            where: { isActive: true },
            orderBy: { sortOrder: 'asc' },
            include: {
              _count: {
                select: { projects: true, expenses: true },
              },
            },
          },
          projects: {
            select: {
              id: true,
              name: true,
              status: true,
              budgetCategoryId: true,
            },
          },
        },
      });

      if (!pool) throw new TRPCError({ code: 'NOT_FOUND' });
      return pool;
    }),

  /**
   * 創建預算池（含初始類別）
   */
  create: protectedProcedure
    .input(z.object({
      name: z.string().min(1),
      financialYear: z.number(),
      description: z.string().optional(),
      categories: z.array(z.object({
        categoryName: z.string().min(1),
        categoryCode: z.string().optional(),
        totalAmount: z.number().min(0),
        description: z.string().optional(),
        sortOrder: z.number().default(0),
      })),
    }))
    .mutation(async ({ ctx, input }) => {
      return await ctx.prisma.budgetPool.create({
        data: {
          name: input.name,
          financialYear: input.financialYear,
          description: input.description,
          categories: {
            create: input.categories,
          },
        },
        include: {
          categories: true,
        },
      });
    }),

  /**
   * 更新預算池（含類別）
   */
  update: protectedProcedure
    .input(z.object({
      id: z.string().min(1),
      name: z.string().min(1).optional(),
      description: z.string().optional(),
      categories: z.array(z.object({
        id: z.string().optional(),  // 有 id = 更新，無 id = 新增
        categoryName: z.string().min(1),
        categoryCode: z.string().optional(),
        totalAmount: z.number().min(0),
        description: z.string().optional(),
        sortOrder: z.number().default(0),
        isActive: z.boolean().optional(),
      })).optional(),
    }))
    .mutation(async ({ ctx, input }) => {
      // 使用 transaction 確保數據一致性
      return await ctx.prisma.$transaction(async (tx) => {
        // 更新預算池基本信息
        const pool = await tx.budgetPool.update({
          where: { id: input.id },
          data: {
            ...(input.name && { name: input.name }),
            ...(input.description !== undefined && { description: input.description }),
          },
        });

        // 處理類別
        if (input.categories) {
          for (const cat of input.categories) {
            if (cat.id) {
              // 更新現有類別
              await tx.budgetCategory.update({
                where: { id: cat.id },
                data: {
                  categoryName: cat.categoryName,
                  categoryCode: cat.categoryCode,
                  totalAmount: cat.totalAmount,
                  description: cat.description,
                  sortOrder: cat.sortOrder,
                  isActive: cat.isActive,
                },
              });
            } else {
              // 新增類別
              await tx.budgetCategory.create({
                data: {
                  budgetPoolId: input.id,
                  categoryName: cat.categoryName,
                  categoryCode: cat.categoryCode,
                  totalAmount: cat.totalAmount,
                  description: cat.description,
                  sortOrder: cat.sortOrder,
                },
              });
            }
          }
        }

        return pool;
      });
    }),

  // ========== BudgetCategory 操作 ==========

  /**
   * 獲取類別使用統計
   */
  getCategoryStats: protectedProcedure
    .input(z.object({ categoryId: z.string().min(1) }))
    .query(async ({ ctx, input }) => {
      const category = await ctx.prisma.budgetCategory.findUnique({
        where: { id: input.categoryId },
        include: {
          budgetPool: true,
          _count: {
            select: { projects: true, expenses: true },
          },
          expenses: {
            select: {
              amount: true,
              status: true,
            },
          },
        },
      });

      if (!category) throw new TRPCError({ code: 'NOT_FOUND' });

      return {
        category,
        utilizationRate: (category.usedAmount / category.totalAmount) * 100,
        remainingAmount: category.totalAmount - category.usedAmount,
      };
    }),

  /**
   * 更新類別已用金額（內部使用，當費用審批時調用）
   */
  updateCategoryUsage: protectedProcedure
    .input(z.object({
      categoryId: z.string().min(1),
      amount: z.number(),  // 正數=增加，負數=減少
    }))
    .mutation(async ({ ctx, input }) => {
      return await ctx.prisma.budgetCategory.update({
        where: { id: input.categoryId },
        data: {
          usedAmount: {
            increment: input.amount,
          },
        },
      });
    }),
});
```

### 前端頁面設計

#### 1. 預算池列表頁 (`/budget-pools/page.tsx`)

**UI 結構**:

```typescript
// apps/web/src/app/budget-pools/page.tsx

export default function BudgetPoolsPage() {
  return (
    <DashboardLayout>
      {/* 頂部操作欄 */}
      <PageHeader
        title="預算池管理"
        description="管理不同年度的預算池和預算類別"
      >
        <div className="flex gap-2">
          <Select value={selectedYear} onValueChange={setSelectedYear}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="選擇年度" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="2025">FY2025</SelectItem>
              <SelectItem value="2024">FY2024</SelectItem>
            </SelectContent>
          </Select>

          <Button onClick={() => router.push('/budget-pools/new')}>
            <Plus className="h-4 w-4 mr-2" />
            新增預算池
          </Button>
        </div>
      </PageHeader>

      {/* 預算池卡片列表 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {pools.map(pool => (
          <BudgetPoolCard key={pool.id} pool={pool} />
        ))}
      </div>
    </DashboardLayout>
  );
}
```

**BudgetPoolCard 組件設計**:

```typescript
// components/budget-pool/BudgetPoolCard.tsx

interface BudgetPoolCardProps {
  pool: BudgetPoolWithCategories;
}

function BudgetPoolCard({ pool }: BudgetPoolCardProps) {
  const totalBudget = pool.categories.reduce((sum, cat) => sum + cat.totalAmount, 0);
  const usedBudget = pool.categories.reduce((sum, cat) => sum + cat.usedAmount, 0);
  const utilizationRate = (usedBudget / totalBudget) * 100;

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">{pool.name}</CardTitle>
            <CardDescription>FY{pool.financialYear}</CardDescription>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => router.push(`/budget-pools/${pool.id}`)}>
                查看詳情
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => router.push(`/budget-pools/${pool.id}/edit`)}>
                編輯
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* 總預算摘要 */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">總預算</span>
            <span className="font-semibold">
              {formatCurrency(totalBudget)}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">已使用</span>
            <span className={cn(
              "font-semibold",
              utilizationRate > 90 ? "text-red-600" :
              utilizationRate > 70 ? "text-yellow-600" :
              "text-green-600"
            )}>
              {formatCurrency(usedBudget)}
            </span>
          </div>

          {/* 使用率進度條 */}
          <Progress
            value={utilizationRate}
            className={cn(
              "h-2",
              utilizationRate > 90 ? "bg-red-200" :
              utilizationRate > 70 ? "bg-yellow-200" :
              "bg-green-200"
            )}
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>使用率</span>
            <span>{utilizationRate.toFixed(1)}%</span>
          </div>
        </div>

        {/* 預算類別列表 */}
        <div className="space-y-1">
          <p className="text-sm font-medium">預算類別 ({pool.categories.length})</p>
          <div className="space-y-1">
            {pool.categories.slice(0, 3).map(cat => (
              <div key={cat.id} className="flex justify-between text-sm">
                <span className="text-muted-foreground truncate">
                  {cat.categoryName}
                </span>
                <span className="font-mono text-xs">
                  {formatCurrency(cat.usedAmount)} / {formatCurrency(cat.totalAmount)}
                </span>
              </div>
            ))}
            {pool.categories.length > 3 && (
              <p className="text-xs text-muted-foreground">
                + {pool.categories.length - 3} 個類別...
              </p>
            )}
          </div>
        </div>

        {/* 關聯項目數量 */}
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <FolderIcon className="h-4 w-4" />
          <span>{pool._count.projects} 個關聯項目</span>
        </div>
      </CardContent>
    </Card>
  );
}
```

#### 2. 預算池詳情/編輯頁 (`/budget-pools/[id]/page.tsx`)

**UI 結構** (Tabs 佈局):

```typescript
export default function BudgetPoolDetailPage({ params }: { params: { id: string } }) {
  return (
    <DashboardLayout>
      <PageHeader
        title={pool.name}
        description={`FY${pool.financialYear} 預算池詳情`}
        backLink="/budget-pools"
      >
        <Button variant="outline" onClick={() => router.push(`/budget-pools/${pool.id}/edit`)}>
          <Edit className="h-4 w-4 mr-2" />
          編輯
        </Button>
      </PageHeader>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">概覽</TabsTrigger>
          <TabsTrigger value="categories">預算類別</TabsTrigger>
          <TabsTrigger value="projects">關聯項目</TabsTrigger>
        </TabsList>

        {/* Tab 1: 概覽 */}
        <TabsContent value="overview">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* 統計卡片 */}
            <StatsCard
              title="總預算"
              value={formatCurrency(totalBudget)}
              icon={DollarSign}
            />
            <StatsCard
              title="已使用"
              value={formatCurrency(usedBudget)}
              trend={utilizationRate}
              icon={TrendingUp}
            />
            <StatsCard
              title="剩餘預算"
              value={formatCurrency(remaining)}
              icon={PiggyBank}
            />
          </div>

          {/* 預算使用趨勢圖 */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>預算使用趨勢</CardTitle>
            </CardHeader>
            <CardContent>
              <BudgetUsageChart data={chartData} />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 2: 預算類別 */}
        <TabsContent value="categories">
          <BudgetCategoriesTable categories={pool.categories} />
        </TabsContent>

        {/* Tab 3: 關聯項目 */}
        <TabsContent value="projects">
          <ProjectsTable projects={pool.projects} />
        </TabsContent>
      </Tabs>
    </DashboardLayout>
  );
}
```

#### 3. 新增/編輯預算池表單 (`/budget-pools/new` & `/budget-pools/[id]/edit`)

**表單組件設計**:

```typescript
// components/budget-pool/BudgetPoolForm.tsx

interface BudgetPoolFormProps {
  initialData?: BudgetPool & { categories: BudgetCategory[] };
  isEdit?: boolean;
}

export function BudgetPoolForm({ initialData, isEdit }: BudgetPoolFormProps) {
  const [categories, setCategories] = useState<CategoryFormData[]>(
    initialData?.categories || [{ categoryName: '', totalAmount: 0, sortOrder: 0 }]
  );

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        {/* 基本信息 */}
        <Card>
          <CardHeader>
            <CardTitle>基本信息</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>預算池名稱</FormLabel>
                  <FormControl>
                    <Input placeholder="如: FY2025 IT 預算" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="financialYear"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>財務年度</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value?.toString()}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="選擇年度" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="2025">FY2025</SelectItem>
                      <SelectItem value="2026">FY2026</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>描述（可選）</FormLabel>
                  <FormControl>
                    <Textarea placeholder="預算池描述..." {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </CardContent>
        </Card>

        {/* 預算類別 */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>預算類別</CardTitle>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleAddCategory}
              >
                <Plus className="h-4 w-4 mr-2" />
                新增類別
              </Button>
            </div>
            <CardDescription>
              定義不同的預算類別及其金額
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {categories.map((category, index) => (
                <CategoryFormRow
                  key={index}
                  category={category}
                  index={index}
                  onUpdate={handleUpdateCategory}
                  onRemove={handleRemoveCategory}
                />
              ))}

              {categories.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  <p>尚未添加預算類別</p>
                  <p className="text-sm">點擊上方「新增類別」按鈕開始</p>
                </div>
              )}
            </div>

            {/* 總預算摘要 */}
            {categories.length > 0 && (
              <div className="mt-6 p-4 bg-muted rounded-lg">
                <div className="flex justify-between items-center">
                  <span className="font-semibold">總預算金額</span>
                  <span className="text-2xl font-bold">
                    {formatCurrency(
                      categories.reduce((sum, cat) => sum + (cat.totalAmount || 0), 0)
                    )}
                  </span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 提交按鈕 */}
        <div className="flex gap-4">
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isEdit ? '更新預算池' : '創建預算池'}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => router.back()}
          >
            取消
          </Button>
        </div>
      </form>
    </Form>
  );
}
```

**CategoryFormRow 子組件**:

```typescript
function CategoryFormRow({ category, index, onUpdate, onRemove }) {
  return (
    <div className="grid grid-cols-12 gap-4 p-4 border rounded-lg">
      <div className="col-span-4">
        <Label>類別名稱</Label>
        <Input
          value={category.categoryName}
          onChange={(e) => onUpdate(index, 'categoryName', e.target.value)}
          placeholder="如: Hardware"
        />
      </div>

      <div className="col-span-2">
        <Label>類別代碼</Label>
        <Input
          value={category.categoryCode}
          onChange={(e) => onUpdate(index, 'categoryCode', e.target.value)}
          placeholder="如: HW"
        />
      </div>

      <div className="col-span-3">
        <Label>預算金額</Label>
        <Input
          type="number"
          value={category.totalAmount}
          onChange={(e) => onUpdate(index, 'totalAmount', parseFloat(e.target.value))}
          placeholder="0.00"
        />
      </div>

      <div className="col-span-2">
        <Label>排序</Label>
        <Input
          type="number"
          value={category.sortOrder}
          onChange={(e) => onUpdate(index, 'sortOrder', parseInt(e.target.value))}
          placeholder="0"
        />
      </div>

      <div className="col-span-1 flex items-end">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => onRemove(index)}
        >
          <Trash2 className="h-4 w-4 text-destructive" />
        </Button>
      </div>

      <div className="col-span-12">
        <Label>描述（可選）</Label>
        <Textarea
          value={category.description}
          onChange={(e) => onUpdate(index, 'description', e.target.value)}
          placeholder="類別描述..."
          rows={2}
        />
      </div>
    </div>
  );
}
```

---

## 模塊 2: 項目管理 (Project) - 欄位擴展

### 業務需求重述

```yaml
新增欄位:
  - budgetCategoryId: 關聯到具體預算類別
  - requestedBudget: 請求的預算金額
  - approvedBudget: 批准的預算金額

保留現有欄位:
  - 項目名稱、描述、狀態
  - 項目負責人、主管
  - 開始日期、結束日期
```

### 數據庫 Schema 修改

```prisma
model Project {
  id             String    @id @default(uuid())
  name           String
  description    String?   @db.Text
  status         String    @default("Draft")  // Draft, InProgress, Completed, Archived

  // ✅ 新增：預算相關
  budgetCategoryId String?  // 關聯到具體預算類別
  requestedBudget  Float?   // 請求的預算金額
  approvedBudget   Float?   // 批准的預算金額

  // 現有欄位
  managerId      String
  supervisorId   String
  budgetPoolId   String
  startDate      DateTime
  endDate        DateTime?
  chargeOutDate  DateTime?

  createdAt      DateTime  @default(now())
  updatedAt      DateTime  @updatedAt

  // 關聯
  manager        User             @relation("ProjectManager", fields: [managerId], references: [id])
  supervisor     User             @relation("Supervisor", fields: [supervisorId], references: [id])
  budgetPool     BudgetPool       @relation(fields: [budgetPoolId], references: [id])
  budgetCategory BudgetCategory?  @relation(fields: [budgetCategoryId], references: [id])  // ✅ 新增
  proposals      BudgetProposal[]
  quotes         Quote[]
  purchaseOrders PurchaseOrder[]

  @@index([budgetCategoryId])  // ✅ 新增索引
  @@index([managerId])
  @@index([supervisorId])
  @@index([budgetPoolId])
  @@index([status])
}
```

### 後端 API 修改

```typescript
// packages/api/src/routers/project.ts

export const projectRouter = createTRPCRouter({

  create: protectedProcedure
    .input(z.object({
      name: z.string().min(1),
      description: z.string().optional(),
      budgetPoolId: z.string().min(1),
      budgetCategoryId: z.string().optional(),  // ✅ 新增
      requestedBudget: z.number().min(0).optional(),  // ✅ 新增
      managerId: z.string().min(1),
      supervisorId: z.string().min(1),
      startDate: z.string(),
      endDate: z.string().optional(),
    }))
    .mutation(async ({ ctx, input }) => {
      // 驗證 budgetCategoryId 是否屬於選擇的 budgetPool
      if (input.budgetCategoryId) {
        const category = await ctx.prisma.budgetCategory.findFirst({
          where: {
            id: input.budgetCategoryId,
            budgetPoolId: input.budgetPoolId,
          },
        });

        if (!category) {
          throw new TRPCError({
            code: 'BAD_REQUEST',
            message: '選擇的預算類別不屬於此預算池',
          });
        }
      }

      return await ctx.prisma.project.create({
        data: {
          ...input,
          startDate: new Date(input.startDate),
          endDate: input.endDate ? new Date(input.endDate) : null,
        },
      });
    }),

  // 獲取項目預算使用情況
  getBudgetUsage: protectedProcedure
    .input(z.object({ id: z.string().min(1) }))
    .query(async ({ ctx, input }) => {
      const project = await ctx.prisma.project.findUnique({
        where: { id: input.id },
        include: {
          budgetCategory: true,
          purchaseOrders: {
            include: {
              expenses: {
                where: {
                  status: { in: ['Approved', 'Paid'] },
                },
              },
            },
          },
        },
      });

      if (!project) throw new TRPCError({ code: 'NOT_FOUND' });

      // 計算實際支出
      const actualSpent = project.purchaseOrders.reduce((sum, po) => {
        return sum + po.expenses.reduce((expSum, exp) => expSum + exp.amount, 0);
      }, 0);

      return {
        requestedBudget: project.requestedBudget || 0,
        approvedBudget: project.approvedBudget || 0,
        actualSpent,
        remaining: (project.approvedBudget || 0) - actualSpent,
        utilizationRate: project.approvedBudget
          ? (actualSpent / project.approvedBudget) * 100
          : 0,
      };
    }),
});
```

### 前端頁面修改

#### 項目表單新增欄位

```typescript
// components/project/ProjectForm.tsx

export function ProjectForm({ initialData, isEdit }: ProjectFormProps) {
  const [selectedBudgetPool, setSelectedBudgetPool] = useState<string | null>(null);
  const [availableCategories, setAvailableCategories] = useState<BudgetCategory[]>([]);

  // 當選擇預算池時，載入其類別
  useEffect(() => {
    if (selectedBudgetPool) {
      api.budgetPool.getById.useQuery({ id: selectedBudgetPool })
        .then(pool => setAvailableCategories(pool.categories));
    }
  }, [selectedBudgetPool]);

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <Card>
          <CardHeader>
            <CardTitle>預算信息</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* 預算池選擇 */}
            <FormField
              control={form.control}
              name="budgetPoolId"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>預算池</FormLabel>
                  <Select
                    onValueChange={(value) => {
                      field.onChange(value);
                      setSelectedBudgetPool(value);
                    }}
                    defaultValue={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="選擇預算池" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {budgetPools.map(pool => (
                        <SelectItem key={pool.id} value={pool.id}>
                          {pool.name} (FY{pool.financialYear})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* ✅ 新增：預算類別選擇 */}
            {selectedBudgetPool && availableCategories.length > 0 && (
              <FormField
                control={form.control}
                name="budgetCategoryId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>預算類別</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="選擇預算類別" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {availableCategories.map(cat => (
                          <SelectItem key={cat.id} value={cat.id}>
                            {cat.categoryName} - 可用: {formatCurrency(cat.totalAmount - cat.usedAmount)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormDescription>
                      選擇此項目將使用哪個預算類別的資金
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            {/* ✅ 新增：請求預算金額 */}
            <FormField
              control={form.control}
              name="requestedBudget"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>請求預算金額</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      step="0.01"
                      placeholder="0.00"
                      {...field}
                      onChange={(e) => field.onChange(parseFloat(e.target.value))}
                    />
                  </FormControl>
                  <FormDescription>
                    項目負責人請求的預算金額
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* ✅ 新增：批准預算金額（僅主管可編輯）*/}
            {canApprove && (
              <FormField
                control={form.control}
                name="approvedBudget"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>批准預算金額</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        step="0.01"
                        placeholder="0.00"
                        {...field}
                        onChange={(e) => field.onChange(parseFloat(e.target.value))}
                      />
                    </FormControl>
                    <FormDescription>
                      主管批准的實際預算金額
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}
          </CardContent>
        </Card>

        {/* ... 其他現有欄位 ... */}
      </form>
    </Form>
  );
}
```

---

## 模塊 3: 預算提案 (Budget Proposal) = 項目計劃書 - 功能擴展

### 業務需求重述

```yaml
擴展 BudgetProposal 模型以支持:
  - 計劃書文件上傳 (PDF/PPT)
  - 會議記錄功能
  - 會議日期
  - 負責介紹人員
  - 批准預算金額
  - 審核狀態和日期
  - 批准者信息

保留現有功能:
  - 評論系統 (Comment)
  - 審批歷史 (History)
  - 審批工作流 (狀態機)
```

### 數據庫 Schema 修改

```prisma
model BudgetProposal {
  id        String   @id @default(uuid())
  title     String   // 提案標題
  amount    Float    // 請求金額
  status    String   @default("Draft")  // Draft, PendingApproval, Approved, Rejected, MoreInfoRequired
  projectId String

  // ✅ 新增：項目計劃書相關
  proposalFilePath String?  // 計劃書文件路徑（PDF/PPT）
  proposalFileName String?  // 原始文件名
  proposalFileSize Int?     // 文件大小（bytes）

  // ✅ 新增：會議相關
  meetingDate      DateTime? // 會議日期
  meetingNotes     String?   @db.Text  // 會議記錄
  presentedBy      String?   // 負責介紹人員（User ID 或姓名）

  // ✅ 新增：批准相關
  approvedAmount   Float?    // 批准的預算金額（可能與請求金額不同）
  approvedBy       String?   // 批准者 User ID
  approvedAt       DateTime? // 批准日期
  rejectionReason  String?   @db.Text  // 拒絕原因

  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  // 關聯
  project      Project   @relation(fields: [projectId], references: [id])
  approver     User?     @relation("ProposalApprover", fields: [approvedBy], references: [id])  // ✅ 新增
  comments     Comment[]
  historyItems History[]

  @@index([projectId])
  @@index([status])
  @@index([approvedBy])  // ✅ 新增索引
}
```

### User 模型需要新增關聯

```prisma
model User {
  // ... 現有欄位 ...

  approvedProposals BudgetProposal[] @relation("ProposalApprover")  // ✅ 新增

  // ... 其他現有關聯 ...
}
```

### 後端 API 擴展

```typescript
// packages/api/src/routers/budgetProposal.ts

export const budgetProposalRouter = createTRPCRouter({

  /**
   * 創建提案（含文件上傳）
   */
  create: protectedProcedure
    .input(z.object({
      title: z.string().min(1),
      amount: z.number().min(0),
      projectId: z.string().min(1),
      proposalFilePath: z.string().optional(),
      proposalFileName: z.string().optional(),
      proposalFileSize: z.number().optional(),
      meetingDate: z.string().optional(),
      meetingNotes: z.string().optional(),
      presentedBy: z.string().optional(),
    }))
    .mutation(async ({ ctx, input }) => {
      return await ctx.prisma.budgetProposal.create({
        data: {
          ...input,
          meetingDate: input.meetingDate ? new Date(input.meetingDate) : null,
        },
      });
    }),

  /**
   * 上傳提案文件
   */
  uploadProposalFile: protectedProcedure
    .input(z.object({
      proposalId: z.string().min(1),
      filePath: z.string(),
      fileName: z.string(),
      fileSize: z.number(),
    }))
    .mutation(async ({ ctx, input }) => {
      return await ctx.prisma.budgetProposal.update({
        where: { id: input.proposalId },
        data: {
          proposalFilePath: input.filePath,
          proposalFileName: input.fileName,
          proposalFileSize: input.fileSize,
        },
      });
    }),

  /**
   * 批准提案（擴展功能）
   */
  approve: supervisorProcedure  // 只有主管可以批准
    .input(z.object({
      id: z.string().min(1),
      approvedAmount: z.number().min(0),  // ✅ 新增：批准金額
      comments: z.string().optional(),
    }))
    .mutation(async ({ ctx, input }) => {
      return await ctx.prisma.$transaction(async (tx) => {
        // 更新提案狀態
        const proposal = await tx.budgetProposal.update({
          where: { id: input.id },
          data: {
            status: 'Approved',
            approvedAmount: input.approvedAmount,  // ✅ 記錄批准金額
            approvedBy: ctx.session.user.id,
            approvedAt: new Date(),
          },
          include: {
            project: {
              include: {
                budgetCategory: true,
              },
            },
          },
        });

        // ✅ 同步更新項目的批准預算
        await tx.project.update({
          where: { id: proposal.projectId },
          data: {
            approvedBudget: input.approvedAmount,
            status: 'InProgress',  // 批准後項目變為進行中
          },
        });

        // 記錄審批歷史
        await tx.history.create({
          data: {
            action: 'APPROVED',
            details: input.comments,
            userId: ctx.session.user.id,
            budgetProposalId: input.id,
          },
        });

        // ✅ 發送通知給項目負責人
        await tx.notification.create({
          data: {
            userId: proposal.project.managerId,
            type: 'PROPOSAL_APPROVED',
            title: '提案已批准',
            message: `您的提案「${proposal.title}」已獲批准，批准金額: ${formatCurrency(input.approvedAmount)}`,
            link: `/proposals/${proposal.id}`,
            entityType: 'PROPOSAL',
            entityId: proposal.id,
          },
        });

        return proposal;
      });
    }),

  /**
   * 更新會議記錄
   */
  updateMeetingNotes: protectedProcedure
    .input(z.object({
      id: z.string().min(1),
      meetingDate: z.string(),
      meetingNotes: z.string(),
      presentedBy: z.string().optional(),
    }))
    .mutation(async ({ ctx, input }) => {
      return await ctx.prisma.budgetProposal.update({
        where: { id: input.id },
        data: {
          meetingDate: new Date(input.meetingDate),
          meetingNotes: input.meetingNotes,
          presentedBy: input.presentedBy,
        },
      });
    }),
});
```

### 前端頁面設計

#### 1. 提案詳情頁增強 (`/proposals/[id]/page.tsx`)

```typescript
export default function ProposalDetailPage({ params }: { params: { id: string } }) {
  const { data: proposal } = api.budgetProposal.getById.useQuery({ id: params.id });

  return (
    <DashboardLayout>
      <PageHeader title={proposal.title} backLink="/proposals" />

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">提案概覽</TabsTrigger>
          <TabsTrigger value="proposal">計劃書文件</TabsTrigger>
          <TabsTrigger value="meeting">會議記錄</TabsTrigger>
          <TabsTrigger value="comments">評論討論</TabsTrigger>
          <TabsTrigger value="history">審批歷史</TabsTrigger>
        </TabsList>

        {/* Tab 1: 提案概覽 */}
        <TabsContent value="overview">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>提案信息</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <InfoRow label="提案標題" value={proposal.title} />
                <InfoRow label="請求金額" value={formatCurrency(proposal.amount)} />
                <InfoRow label="批准金額" value={
                  proposal.approvedAmount
                    ? formatCurrency(proposal.approvedAmount)
                    : '尚未批准'
                } />
                <InfoRow label="狀態" value={
                  <StatusBadge status={proposal.status} />
                } />
                <InfoRow label="關聯項目" value={
                  <Link href={`/projects/${proposal.project.id}`} className="text-primary hover:underline">
                    {proposal.project.name}
                  </Link>
                } />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>時間線</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <InfoRow label="創建時間" value={formatDate(proposal.createdAt)} />
                <InfoRow label="會議日期" value={
                  proposal.meetingDate ? formatDate(proposal.meetingDate) : '未設定'
                } />
                <InfoRow label="批准時間" value={
                  proposal.approvedAt ? formatDate(proposal.approvedAt) : '-'
                } />
                <InfoRow label="批准者" value={
                  proposal.approver ? proposal.approver.name : '-'
                } />
              </CardContent>
            </Card>
          </div>

          {/* 審批操作按鈕（僅主管可見）*/}
          {isSupervisor && proposal.status === 'PendingApproval' && (
            <Card className="mt-6">
              <CardHeader>
                <CardTitle>審批操作</CardTitle>
              </CardHeader>
              <CardContent>
                <ProposalActions proposalId={proposal.id} />
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Tab 2: 計劃書文件 */}
        <TabsContent value="proposal">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>項目計劃書文件</CardTitle>
                {canEdit && !proposal.proposalFilePath && (
                  <Button onClick={() => setShowUploadDialog(true)}>
                    <Upload className="h-4 w-4 mr-2" />
                    上傳計劃書
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {proposal.proposalFilePath ? (
                <div className="space-y-4">
                  {/* 文件信息 */}
                  <div className="flex items-center gap-4 p-4 border rounded-lg">
                    <div className="p-3 bg-primary/10 rounded-lg">
                      <FileText className="h-8 w-8 text-primary" />
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold">{proposal.proposalFileName}</p>
                      <p className="text-sm text-muted-foreground">
                        {formatFileSize(proposal.proposalFileSize)} ·
                        上傳於 {formatDate(proposal.updatedAt)}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={handlePreview}>
                        <Eye className="h-4 w-4 mr-2" />
                        預覽
                      </Button>
                      <Button variant="outline" size="sm" onClick={handleDownload}>
                        <Download className="h-4 w-4 mr-2" />
                        下載
                      </Button>
                    </div>
                  </div>

                  {/* PDF 預覽（如果是 PDF）*/}
                  {proposal.proposalFileName?.endsWith('.pdf') && (
                    <div className="border rounded-lg p-4">
                      <embed
                        src={proposal.proposalFilePath}
                        type="application/pdf"
                        width="100%"
                        height="600px"
                      />
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>尚未上傳項目計劃書</p>
                  {canEdit && (
                    <Button className="mt-4" onClick={() => setShowUploadDialog(true)}>
                      <Upload className="h-4 w-4 mr-2" />
                      上傳計劃書
                    </Button>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 3: 會議記錄 */}
        <TabsContent value="meeting">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>會議記錄</CardTitle>
                {canEdit && (
                  <Button onClick={() => setShowMeetingDialog(true)}>
                    <Edit className="h-4 w-4 mr-2" />
                    編輯會議記錄
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {proposal.meetingNotes ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <InfoRow label="會議日期" value={formatDate(proposal.meetingDate!)} />
                    <InfoRow label="介紹人員" value={proposal.presentedBy || '-'} />
                  </div>

                  <div>
                    <Label className="text-sm font-semibold">會議記錄</Label>
                    <div className="mt-2 p-4 bg-muted rounded-lg whitespace-pre-wrap">
                      {proposal.meetingNotes}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  <Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>尚未添加會議記錄</p>
                  {canEdit && (
                    <Button className="mt-4" onClick={() => setShowMeetingDialog(true)}>
                      <Plus className="h-4 w-4 mr-2" />
                      添加會議記錄
                    </Button>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 4 & 5: 現有的評論和歷史 */}
        <TabsContent value="comments">
          <CommentSection proposalId={proposal.id} />
        </TabsContent>

        <TabsContent value="history">
          <HistoryTimeline items={proposal.historyItems} />
        </TabsContent>
      </Tabs>

      {/* 文件上傳對話框 */}
      <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>上傳項目計劃書</DialogTitle>
            <DialogDescription>
              支持 PDF、PPT、PPTX 格式，最大 10MB
            </DialogDescription>
          </DialogHeader>

          <FileUploadZone
            accept=".pdf,.ppt,.pptx"
            maxSize={10 * 1024 * 1024}
            onUpload={handleFileUpload}
          />
        </DialogContent>
      </Dialog>

      {/* 會議記錄編輯對話框 */}
      <Dialog open={showMeetingDialog} onOpenChange={setShowMeetingDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>編輯會議記錄</DialogTitle>
          </DialogHeader>

          <Form {...meetingForm}>
            <form onSubmit={meetingForm.handleSubmit(onMeetingSubmit)} className="space-y-4">
              <FormField
                control={meetingForm.control}
                name="meetingDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>會議日期</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={meetingForm.control}
                name="presentedBy"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>介紹人員</FormLabel>
                    <FormControl>
                      <Input placeholder="負責介紹的人員姓名" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={meetingForm.control}
                name="meetingNotes"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>會議記錄</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="記錄會議討論的重點、決議等..."
                        rows={10}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="flex gap-2">
                <Button type="submit">保存會議記錄</Button>
                <Button type="button" variant="outline" onClick={() => setShowMeetingDialog(false)}>
                  取消
                </Button>
              </div>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
}
```

#### 2. 提案審批對話框增強

```typescript
// components/proposal/ProposalApprovalDialog.tsx

export function ProposalApprovalDialog({ proposal, onApprove }: Props) {
  const [approvedAmount, setApprovedAmount] = useState(proposal.amount);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>批准提案</DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            {/* 請求金額（只讀）*/}
            <div>
              <Label>請求金額</Label>
              <div className="p-3 bg-muted rounded-lg">
                <p className="text-2xl font-bold">{formatCurrency(proposal.amount)}</p>
              </div>
            </div>

            {/* ✅ 批准金額（可編輯）*/}
            <FormField
              control={form.control}
              name="approvedAmount"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>批准金額</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      step="0.01"
                      {...field}
                      onChange={(e) => field.onChange(parseFloat(e.target.value))}
                    />
                  </FormControl>
                  <FormDescription>
                    實際批准的預算金額（可與請求金額不同）
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 金額差異提示 */}
            {approvedAmount !== proposal.amount && (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>金額差異</AlertTitle>
                <AlertDescription>
                  批准金額與請求金額相差: {formatCurrency(Math.abs(approvedAmount - proposal.amount))}
                  {approvedAmount > proposal.amount ? ' (增加)' : ' (減少)'}
                </AlertDescription>
              </Alert>
            )}

            {/* 批准意見 */}
            <FormField
              control={form.control}
              name="comments"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>批准意見（可選）</FormLabel>
                  <FormControl>
                    <Textarea placeholder="批准理由、條件或說明..." rows={4} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex gap-2">
              <Button type="submit" className="flex-1">
                確認批准
              </Button>
              <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                取消
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
```

---

## 模塊 4: 採購管理 (Purchase Order) - 表頭明細重構

### 業務需求重述

```yaml
核心需求:
  - 表頭-明細結構（Header-Detail Pattern）
  - 表頭欄位: 名稱、描述、採購單號、日期、金額、關聯項目、關聯供應商、狀態
  - 明細欄位: 品項名稱、描述、數量、單價、小計
  - 關聯支出/費用記錄
  - 自動計算總金額（從明細加總）
```

### 數據庫 Schema 設計

#### 新增 OperatingCompany 模型

```prisma
// ✅ 新增：營運公司（OpCo）
model OperatingCompany {
  id          String   @id @default(uuid())
  code        String   @unique  // 如: "OpCo-HK", "OpCo-SG"
  name        String   // 如: "Hong Kong Operations"
  description String?
  isActive    Boolean  @default(true)
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  // 關聯
  chargeOuts         ChargeOut[]
  omExpenses         OMExpense[]
  omExpenseMonthly   OMExpenseMonthly[]

  @@index([isActive])
}
```

#### 修改 PurchaseOrder 模型（表頭）

```prisma
model PurchaseOrder {
  id          String   @id @default(uuid())
  poNumber    String   @unique @default(cuid())

  // ✅ 新增：基本信息
  name        String   // PO 名稱
  description String?  @db.Text

  // 財務信息
  totalAmount Float    // ❌ 不再手動輸入，改由明細自動計算
  status      String   @default("Draft")  // ✅ 新增: Draft, Submitted, Approved, Completed, Cancelled

  // 關聯
  projectId   String
  vendorId    String
  quoteId     String?

  // 日期
  date        DateTime @default(now())  // PO 日期
  approvedDate DateTime?  // ✅ 新增：批准日期
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  // 關聯
  project  Project           @relation(fields: [projectId], references: [id])
  vendor   Vendor            @relation(fields: [vendorId], references: [id])
  quote    Quote?            @relation(fields: [quoteId], references: [id])
  items    PurchaseOrderItem[]  // ✅ 新增：明細項目
  expenses Expense[]

  @@index([projectId])
  @@index([vendorId])
  @@index([status])
}
```

#### 新增 PurchaseOrderItem 模型（明細）

```prisma
// ✅ 新增：採購單明細
model PurchaseOrderItem {
  id              String @id @default(uuid())
  purchaseOrderId String

  // 品項信息
  itemName        String   // 品項名稱
  description     String?  @db.Text
  quantity        Int      // 數量
  unitPrice       Float    // 單價
  subtotal        Float    // 小計（quantity * unitPrice）

  // 元數據
  sortOrder       Int      @default(0)
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt

  // 關聯
  purchaseOrder PurchaseOrder @relation(fields: [purchaseOrderId], references: [id], onDelete: Cascade)

  @@index([purchaseOrderId])
}
```

### 後端 API 設計 (tRPC)

```typescript
// packages/api/src/routers/purchaseOrder.ts

export const purchaseOrderRouter = createTRPCRouter({

  /**
   * 創建採購單（含明細）
   */
  create: protectedProcedure
    .input(z.object({
      name: z.string().min(1),
      description: z.string().optional(),
      projectId: z.string().min(1),
      vendorId: z.string().min(1),
      quoteId: z.string().optional(),
      date: z.string(),
      items: z.array(z.object({
        itemName: z.string().min(1),
        description: z.string().optional(),
        quantity: z.number().int().min(1),
        unitPrice: z.number().min(0),
        sortOrder: z.number().default(0),
      })),
    }))
    .mutation(async ({ ctx, input }) => {
      // 驗證至少要有一個品項
      if (input.items.length === 0) {
        throw new TRPCError({
          code: 'BAD_REQUEST',
          message: '至少需要一個採購品項',
        });
      }

      // 計算總金額
      const totalAmount = input.items.reduce((sum, item) => {
        return sum + (item.quantity * item.unitPrice);
      }, 0);

      return await ctx.prisma.$transaction(async (tx) => {
        // 創建採購單表頭
        const po = await tx.purchaseOrder.create({
          data: {
            name: input.name,
            description: input.description,
            projectId: input.projectId,
            vendorId: input.vendorId,
            quoteId: input.quoteId,
            date: new Date(input.date),
            totalAmount,
            status: 'Draft',
          },
        });

        // 創建明細
        await tx.purchaseOrderItem.createMany({
          data: input.items.map(item => ({
            purchaseOrderId: po.id,
            itemName: item.itemName,
            description: item.description,
            quantity: item.quantity,
            unitPrice: item.unitPrice,
            subtotal: item.quantity * item.unitPrice,
            sortOrder: item.sortOrder,
          })),
        });

        return po;
      });
    }),

  /**
   * 更新採購單（含明細）
   */
  update: protectedProcedure
    .input(z.object({
      id: z.string().min(1),
      name: z.string().min(1).optional(),
      description: z.string().optional(),
      vendorId: z.string().optional(),
      date: z.string().optional(),
      items: z.array(z.object({
        id: z.string().optional(),  // 有 id = 更新，無 id = 新增
        itemName: z.string().min(1),
        description: z.string().optional(),
        quantity: z.number().int().min(1),
        unitPrice: z.number().min(0),
        sortOrder: z.number().default(0),
        _delete: z.boolean().optional(),  // true = 刪除此品項
      })).optional(),
    }))
    .mutation(async ({ ctx, input }) => {
      return await ctx.prisma.$transaction(async (tx) => {
        // 更新表頭
        let updateData: any = {};
        if (input.name) updateData.name = input.name;
        if (input.description !== undefined) updateData.description = input.description;
        if (input.vendorId) updateData.vendorId = input.vendorId;
        if (input.date) updateData.date = new Date(input.date);

        // 處理明細
        if (input.items) {
          // 刪除標記為刪除的品項
          const itemsToDelete = input.items.filter(item => item._delete && item.id);
          if (itemsToDelete.length > 0) {
            await tx.purchaseOrderItem.deleteMany({
              where: {
                id: { in: itemsToDelete.map(item => item.id!) },
              },
            });
          }

          // 處理更新和新增
          const itemsToProcess = input.items.filter(item => !item._delete);
          for (const item of itemsToProcess) {
            const subtotal = item.quantity * item.unitPrice;

            if (item.id) {
              // 更新現有品項
              await tx.purchaseOrderItem.update({
                where: { id: item.id },
                data: {
                  itemName: item.itemName,
                  description: item.description,
                  quantity: item.quantity,
                  unitPrice: item.unitPrice,
                  subtotal,
                  sortOrder: item.sortOrder,
                },
              });
            } else {
              // 新增品項
              await tx.purchaseOrderItem.create({
                data: {
                  purchaseOrderId: input.id,
                  itemName: item.itemName,
                  description: item.description,
                  quantity: item.quantity,
                  unitPrice: item.unitPrice,
                  subtotal,
                  sortOrder: item.sortOrder,
                },
              });
            }
          }

          // 重新計算總金額
          const items = await tx.purchaseOrderItem.findMany({
            where: { purchaseOrderId: input.id },
          });
          const totalAmount = items.reduce((sum, item) => sum + item.subtotal, 0);
          updateData.totalAmount = totalAmount;
        }

        // 更新表頭
        const po = await tx.purchaseOrder.update({
          where: { id: input.id },
          data: updateData,
          include: {
            items: {
              orderBy: { sortOrder: 'asc' },
            },
          },
        });

        return po;
      });
    }),

  /**
   * 獲取採購單詳情（含明細）
   */
  getById: protectedProcedure
    .input(z.object({ id: z.string().min(1) }))
    .query(async ({ ctx, input }) => {
      const po = await ctx.prisma.purchaseOrder.findUnique({
        where: { id: input.id },
        include: {
          project: {
            select: {
              id: true,
              name: true,
              budgetPool: { select: { name: true, financialYear: true } },
            },
          },
          vendor: true,
          quote: true,
          items: {
            orderBy: { sortOrder: 'asc' },
          },
          expenses: {
            select: {
              id: true,
              amount: true,
              status: true,
              expenseDate: true,
            },
          },
        },
      });

      if (!po) throw new TRPCError({ code: 'NOT_FOUND' });
      return po;
    }),

  /**
   * 提交採購單（狀態變更）
   */
  submit: protectedProcedure
    .input(z.object({ id: z.string().min(1) }))
    .mutation(async ({ ctx, input }) => {
      // 驗證至少有一個品項
      const itemCount = await ctx.prisma.purchaseOrderItem.count({
        where: { purchaseOrderId: input.id },
      });

      if (itemCount === 0) {
        throw new TRPCError({
          code: 'BAD_REQUEST',
          message: '無法提交空的採購單',
        });
      }

      return await ctx.prisma.purchaseOrder.update({
        where: { id: input.id },
        data: {
          status: 'Submitted',
        },
      });
    }),

  /**
   * 批准採購單（主管）
   */
  approve: supervisorProcedure
    .input(z.object({ id: z.string().min(1) }))
    .mutation(async ({ ctx, input }) => {
      return await ctx.prisma.purchaseOrder.update({
        where: { id: input.id },
        data: {
          status: 'Approved',
          approvedDate: new Date(),
        },
      });
    }),
});
```

### 前端頁面設計

#### 1. 採購單列表頁 (`/purchase-orders/page.tsx`)

```typescript
export default function PurchaseOrdersPage() {
  const { data } = api.purchaseOrder.getAll.useQuery();

  return (
    <DashboardLayout>
      <PageHeader
        title="採購管理"
        description="管理所有採購單和採購品項"
      >
        <Button onClick={() => router.push('/purchase-orders/new')}>
          <Plus className="h-4 w-4 mr-2" />
          新增採購單
        </Button>
      </PageHeader>

      <DataTable
        columns={[
          { key: 'poNumber', label: 'PO 編號' },
          { key: 'name', label: '採購單名稱' },
          { key: 'vendor.name', label: '供應商' },
          { key: 'project.name', label: '關聯項目' },
          { key: 'totalAmount', label: '總金額', format: 'currency' },
          { key: 'status', label: '狀態', component: StatusBadge },
          { key: 'date', label: '採購日期', format: 'date' },
        ]}
        data={data?.items || []}
      />
    </DashboardLayout>
  );
}
```

#### 2. 採購單詳情頁 (`/purchase-orders/[id]/page.tsx`)

```typescript
export default function PurchaseOrderDetailPage({ params }: { params: { id: string } }) {
  const { data: po } = api.purchaseOrder.getById.useQuery({ id: params.id });

  return (
    <DashboardLayout>
      <PageHeader
        title={`${po.poNumber} - ${po.name}`}
        backLink="/purchase-orders"
      >
        <div className="flex gap-2">
          {po.status === 'Draft' && (
            <Button onClick={handleSubmit}>提交審批</Button>
          )}
          {isSupervisor && po.status === 'Submitted' && (
            <Button onClick={handleApprove}>批准</Button>
          )}
          <Button variant="outline" onClick={() => router.push(`/purchase-orders/${po.id}/edit`)}>
            <Edit className="h-4 w-4 mr-2" />
            編輯
          </Button>
        </div>
      </PageHeader>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 左側：基本信息 */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>基本信息</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-4">
              <InfoRow label="PO 編號" value={po.poNumber} />
              <InfoRow label="狀態" value={<StatusBadge status={po.status} />} />
              <InfoRow label="供應商" value={po.vendor.name} />
              <InfoRow label="關聯項目" value={
                <Link href={`/projects/${po.project.id}`} className="text-primary hover:underline">
                  {po.project.name}
                </Link>
              } />
              <InfoRow label="採購日期" value={formatDate(po.date)} />
              <InfoRow label="批准日期" value={
                po.approvedDate ? formatDate(po.approvedDate) : '-'
              } />
              <div className="col-span-2">
                <Label className="text-sm font-semibold">描述</Label>
                <p className="mt-1 text-sm text-muted-foreground">{po.description || '-'}</p>
              </div>
            </CardContent>
          </Card>

          {/* 明細品項 */}
          <Card>
            <CardHeader>
              <CardTitle>採購品項</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>品項名稱</TableHead>
                    <TableHead>描述</TableHead>
                    <TableHead className="text-right">數量</TableHead>
                    <TableHead className="text-right">單價</TableHead>
                    <TableHead className="text-right">小計</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {po.items.map(item => (
                    <TableRow key={item.id}>
                      <TableCell className="font-medium">{item.itemName}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {item.description || '-'}
                      </TableCell>
                      <TableCell className="text-right">{item.quantity}</TableCell>
                      <TableCell className="text-right">{formatCurrency(item.unitPrice)}</TableCell>
                      <TableCell className="text-right font-semibold">
                        {formatCurrency(item.subtotal)}
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow>
                    <TableCell colSpan={4} className="text-right font-bold">總計</TableCell>
                    <TableCell className="text-right font-bold text-lg">
                      {formatCurrency(po.totalAmount)}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* 關聯費用 */}
          {po.expenses.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>關聯費用記錄</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {po.expenses.map(expense => (
                    <div key={expense.id} className="flex justify-between p-3 border rounded-lg">
                      <div>
                        <p className="font-medium">費用 #{expense.id.slice(0, 8)}</p>
                        <p className="text-sm text-muted-foreground">
                          {formatDate(expense.expenseDate)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold">{formatCurrency(expense.amount)}</p>
                        <StatusBadge status={expense.status} size="sm" />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* 右側：統計信息 */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>採購統計</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <StatsCard
                label="品項總數"
                value={po.items.length}
                icon={Package}
              />
              <StatsCard
                label="總數量"
                value={po.items.reduce((sum, item) => sum + item.quantity, 0)}
                icon={Hash}
              />
              <StatsCard
                label="總金額"
                value={formatCurrency(po.totalAmount)}
                icon={DollarSign}
              />
              <StatsCard
                label="已記錄費用"
                value={po.expenses.length}
                icon={Receipt}
              />
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
```

#### 3. 採購單表單（新增/編輯）(`/purchase-orders/new` & `/[id]/edit`)

```typescript
// components/purchase-order/PurchaseOrderForm.tsx

export function PurchaseOrderForm({ initialData, isEdit }: PurchaseOrderFormProps) {
  const [items, setItems] = useState<POItemFormData[]>(
    initialData?.items || [{ itemName: '', quantity: 1, unitPrice: 0, sortOrder: 0 }]
  );

  const totalAmount = items.reduce((sum, item) => {
    return sum + (item.quantity * item.unitPrice);
  }, 0);

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        {/* 基本信息卡片 */}
        <Card>
          <CardHeader>
            <CardTitle>基本信息</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>採購單名稱</FormLabel>
                  <FormControl>
                    <Input placeholder="如: Q1 伺服器採購" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="date"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>採購日期</FormLabel>
                  <FormControl>
                    <Input type="date" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="projectId"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>關聯項目</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="選擇項目" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {projects.map(proj => (
                        <SelectItem key={proj.id} value={proj.id}>
                          {proj.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="vendorId"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>供應商</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="選擇供應商" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {vendors.map(vendor => (
                        <SelectItem key={vendor.id} value={vendor.id}>
                          {vendor.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="col-span-2">
              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>描述（可選）</FormLabel>
                    <FormControl>
                      <Textarea placeholder="採購單描述..." {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          </CardContent>
        </Card>

        {/* 採購品項明細 */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>採購品項</CardTitle>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleAddItem}
              >
                <Plus className="h-4 w-4 mr-2" />
                新增品項
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {items.map((item, index) => (
                <POItemFormRow
                  key={index}
                  item={item}
                  index={index}
                  onUpdate={handleUpdateItem}
                  onRemove={handleRemoveItem}
                />
              ))}

              {items.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>尚未添加採購品項</p>
                  <Button
                    type="button"
                    variant="outline"
                    className="mt-4"
                    onClick={handleAddItem}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    新增第一個品項
                  </Button>
                </div>
              )}

              {/* 總計顯示 */}
              {items.length > 0 && (
                <div className="mt-6 p-4 bg-primary/5 rounded-lg">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-sm text-muted-foreground">總品項數</p>
                      <p className="text-2xl font-bold">{items.length}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-muted-foreground">採購總金額</p>
                      <p className="text-3xl font-bold text-primary">
                        {formatCurrency(totalAmount)}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 提交按鈕 */}
        <div className="flex gap-4">
          <Button type="submit" disabled={isSubmitting || items.length === 0}>
            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isEdit ? '更新採購單' : '創建採購單'}
          </Button>
          <Button type="button" variant="outline" onClick={() => router.back()}>
            取消
          </Button>
        </div>
      </form>
    </Form>
  );
}

// POItemFormRow 子組件
function POItemFormRow({ item, index, onUpdate, onRemove }) {
  const subtotal = item.quantity * item.unitPrice;

  return (
    <div className="grid grid-cols-12 gap-4 p-4 border rounded-lg bg-card">
      <div className="col-span-4">
        <Label>品項名稱</Label>
        <Input
          value={item.itemName}
          onChange={(e) => onUpdate(index, 'itemName', e.target.value)}
          placeholder="如: Dell Server R740"
        />
      </div>

      <div className="col-span-2">
        <Label>數量</Label>
        <Input
          type="number"
          value={item.quantity}
          onChange={(e) => onUpdate(index, 'quantity', parseInt(e.target.value))}
          min="1"
        />
      </div>

      <div className="col-span-2">
        <Label>單價</Label>
        <Input
          type="number"
          step="0.01"
          value={item.unitPrice}
          onChange={(e) => onUpdate(index, 'unitPrice', parseFloat(e.target.value))}
          placeholder="0.00"
        />
      </div>

      <div className="col-span-3">
        <Label>小計</Label>
        <div className="p-2 bg-muted rounded-lg">
          <p className="text-lg font-semibold">{formatCurrency(subtotal)}</p>
        </div>
      </div>

      <div className="col-span-1 flex items-end">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => onRemove(index)}
        >
          <Trash2 className="h-4 w-4 text-destructive" />
        </Button>
      </div>

      <div className="col-span-12">
        <Label>描述（可選）</Label>
        <Textarea
          value={item.description}
          onChange={(e) => onUpdate(index, 'description', e.target.value)}
          placeholder="品項描述..."
          rows={2}
        />
      </div>
    </div>
  );
}
```

---

## 模塊 5: 費用管理 (Expense) - 重構和擴展

### 業務需求重述

```yaml
核心需求:
  - 表頭-明細結構（Header-Detail Pattern）
  - 表頭欄位: 支出名稱、描述、關聯項目、關聯預算類別、發票號碼、發票總金額、
              是否需要charge out、發票日期、是否operation maintenance、供應商
  - 明細欄位: 費用項目名稱、描述、金額、費用類別
  - 審批工作流
  - 自動更新預算池使用金額

重要設計決策:
  - ✅ Expense 直接關聯 Project (projectId)
    理由: 提升查詢效率，支持項目級別的費用統計和報表生成
    驗證: expense.projectId 必須與 expense.purchaseOrder.projectId 一致
```

### 數據庫 Schema 設計

#### 修改 Expense 模型（表頭）

```prisma
model Expense {
  id              String   @id @default(uuid())

  // ✅ 新增：基本信息
  name            String   // 費用名稱
  description     String?  @db.Text

  // 財務信息
  totalAmount     Float    // ❌ 不再手動輸入，改由明細自動計算
  status          String   @default("Draft")  // Draft, PendingApproval, Approved, Paid, Rejected

  // ✅ 新增：發票信息
  invoiceNumber   String?  // 發票號碼
  invoiceDate     DateTime // 發票日期
  invoiceFilePath String?  // 發票文件路徑

  // ✅ 新增：分類標記
  requiresChargeOut Boolean @default(false)  // 是否需要費用轉嫁
  isOperationMaint  Boolean @default(false)  // 是否為運維費用

  // 關聯
  projectId       String    // ✅ 新增：直接關聯項目（提升查詢效率）
  purchaseOrderId String
  budgetCategoryId String?  // ✅ 新增：關聯預算類別
  vendorId        String?   // ✅ 新增：直接關聯供應商

  expenseDate     DateTime  @default(now())
  approvedDate    DateTime?
  paidDate        DateTime?
  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt

  // 關聯
  project        Project         @relation(fields: [projectId], references: [id])  // ✅ 新增
  purchaseOrder  PurchaseOrder   @relation(fields: [purchaseOrderId], references: [id])
  budgetCategory BudgetCategory? @relation(fields: [budgetCategoryId], references: [id])
  vendor         Vendor?         @relation(fields: [vendorId], references: [id])
  items          ExpenseItem[]   // ✅ 新增：明細項目
  chargeOuts     ChargeOut[]     // ✅ 新增：關聯的費用轉嫁

  @@index([projectId])           // ✅ 新增索引
  @@index([purchaseOrderId])
  @@index([budgetCategoryId])
  @@index([vendorId])
  @@index([status])
  @@index([requiresChargeOut])
  @@index([isOperationMaint])
}
```

#### 新增 ExpenseItem 模型（明細）

```prisma
// ✅ 新增：費用明細
model ExpenseItem {
  id          String @id @default(uuid())
  expenseId   String

  // 費用項目信息
  itemName    String   // 費用項目名稱
  description String?  @db.Text
  amount      Float    // 金額
  category    String?  // 費用類別（如: Hardware, Software, Consulting）

  // 元數據
  sortOrder   Int      @default(0)
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  // 關聯
  expense Expense @relation(fields: [expenseId], references: [id], onDelete: Cascade)

  @@index([expenseId])
}
```

#### Vendor 模型需要新增關聯

```prisma
model Vendor {
  // ... 現有欄位 ...

  expenses Expense[]  // ✅ 新增
}
```

#### Project 模型需要新增關聯

```prisma
model Project {
  // ... 現有欄位 ...

  expenses Expense[]  // ✅ 新增：直接關聯費用記錄
}
```

**設計說明**：
- **雙重關聯**：Expense 同時關聯 Project 和 PurchaseOrder
- **查詢效率**：可直接查詢 `project.expenses` 獲取所有費用，無需通過 PurchaseOrder
- **業務邏輯**：支持項目級別的費用統計和報表生成
- **數據一致性**：驗證 `expense.projectId` 必須與 `expense.purchaseOrder.projectId` 一致

### 後端 API 設計 (tRPC)

```typescript
// packages/api/src/routers/expense.ts

export const expenseRouter = createTRPCRouter({

  /**
   * 創建費用記錄（含明細）
   */
  create: protectedProcedure
    .input(z.object({
      name: z.string().min(1),
      description: z.string().optional(),
      projectId: z.string().min(1),          // ✅ 新增：直接指定項目
      purchaseOrderId: z.string().min(1),
      budgetCategoryId: z.string().optional(),
      vendorId: z.string().optional(),
      invoiceNumber: z.string().optional(),
      invoiceDate: z.string(),
      invoiceFilePath: z.string().optional(),
      requiresChargeOut: z.boolean().default(false),
      isOperationMaint: z.boolean().default(false),
      items: z.array(z.object({
        itemName: z.string().min(1),
        description: z.string().optional(),
        amount: z.number().min(0),
        category: z.string().optional(),
        sortOrder: z.number().default(0),
      })),
    }))
    .mutation(async ({ ctx, input }) => {
      // 驗證至少要有一個費用項目
      if (input.items.length === 0) {
        throw new TRPCError({
          code: 'BAD_REQUEST',
          message: '至少需要一個費用項目',
        });
      }

      // 計算總金額
      const totalAmount = input.items.reduce((sum, item) => sum + item.amount, 0);

      // 驗證 PO 存在
      const po = await ctx.prisma.purchaseOrder.findUnique({
        where: { id: input.purchaseOrderId },
        include: {
          project: {
            include: {
              budgetCategory: true,
            },
          },
        },
      });

      if (!po) {
        throw new TRPCError({
          code: 'NOT_FOUND',
          message: '找不到對應的採購單',
        });
      }

      // ✅ 驗證 projectId 與 PO 的 projectId 一致
      if (input.projectId !== po.projectId) {
        throw new TRPCError({
          code: 'BAD_REQUEST',
          message: '費用的項目必須與採購單的項目一致',
        });
      }

      return await ctx.prisma.$transaction(async (tx) => {
        // 創建費用表頭
        const expense = await tx.expense.create({
          data: {
            name: input.name,
            description: input.description,
            projectId: input.projectId,  // ✅ 新增
            purchaseOrderId: input.purchaseOrderId,
            budgetCategoryId: input.budgetCategoryId || po.project.budgetCategoryId,
            vendorId: input.vendorId,
            invoiceNumber: input.invoiceNumber,
            invoiceDate: new Date(input.invoiceDate),
            invoiceFilePath: input.invoiceFilePath,
            requiresChargeOut: input.requiresChargeOut,
            isOperationMaint: input.isOperationMaint,
            totalAmount,
            status: 'Draft',
          },
        });

        // 創建費用明細
        await tx.expenseItem.createMany({
          data: input.items.map(item => ({
            expenseId: expense.id,
            itemName: item.itemName,
            description: item.description,
            amount: item.amount,
            category: item.category,
            sortOrder: item.sortOrder,
          })),
        });

        return expense;
      });
    }),

  /**
   * 批准費用（自動更新預算池使用金額）
   */
  approve: supervisorProcedure
    .input(z.object({
      id: z.string().min(1),
      comments: z.string().optional(),
    }))
    .mutation(async ({ ctx, input }) => {
      return await ctx.prisma.$transaction(async (tx) => {
        // 獲取費用詳情
        const expense = await tx.expense.findUnique({
          where: { id: input.id },
          include: {
            budgetCategory: true,
            purchaseOrder: {
              include: {
                project: true,
              },
            },
          },
        });

        if (!expense) throw new TRPCError({ code: 'NOT_FOUND' });

        // 更新費用狀態
        const updatedExpense = await tx.expense.update({
          where: { id: input.id },
          data: {
            status: 'Approved',
            approvedDate: new Date(),
          },
        });

        // ✅ 更新預算類別使用金額
        if (expense.budgetCategoryId) {
          await tx.budgetCategory.update({
            where: { id: expense.budgetCategoryId },
            data: {
              usedAmount: {
                increment: expense.totalAmount,
              },
            },
          });
        }

        // 發送通知給項目負責人
        await tx.notification.create({
          data: {
            userId: expense.purchaseOrder.project.managerId,
            type: 'EXPENSE_APPROVED',
            title: '費用已批准',
            message: `費用「${expense.name}」已獲批准，金額: ${formatCurrency(expense.totalAmount)}`,
            link: `/expenses/${expense.id}`,
            entityType: 'EXPENSE',
            entityId: expense.id,
          },
        });

        return updatedExpense;
      });
    }),

  /**
   * 更新費用（含明細）
   */
  update: protectedProcedure
    .input(z.object({
      id: z.string().min(1),
      name: z.string().optional(),
      description: z.string().optional(),
      invoiceNumber: z.string().optional(),
      invoiceDate: z.string().optional(),
      requiresChargeOut: z.boolean().optional(),
      isOperationMaint: z.boolean().optional(),
      items: z.array(z.object({
        id: z.string().optional(),
        itemName: z.string().min(1),
        description: z.string().optional(),
        amount: z.number().min(0),
        category: z.string().optional(),
        sortOrder: z.number().default(0),
        _delete: z.boolean().optional(),
      })).optional(),
    }))
    .mutation(async ({ ctx, input }) => {
      return await ctx.prisma.$transaction(async (tx) => {
        // 更新表頭
        let updateData: any = {};
        if (input.name) updateData.name = input.name;
        if (input.description !== undefined) updateData.description = input.description;
        if (input.invoiceNumber !== undefined) updateData.invoiceNumber = input.invoiceNumber;
        if (input.invoiceDate) updateData.invoiceDate = new Date(input.invoiceDate);
        if (input.requiresChargeOut !== undefined) updateData.requiresChargeOut = input.requiresChargeOut;
        if (input.isOperationMaint !== undefined) updateData.isOperationMaint = input.isOperationMaint;

        // 處理明細
        if (input.items) {
          // 刪除標記為刪除的項目
          const itemsToDelete = input.items.filter(item => item._delete && item.id);
          if (itemsToDelete.length > 0) {
            await tx.expenseItem.deleteMany({
              where: {
                id: { in: itemsToDelete.map(item => item.id!) },
              },
            });
          }

          // 處理更新和新增
          const itemsToProcess = input.items.filter(item => !item._delete);
          for (const item of itemsToProcess) {
            if (item.id) {
              // 更新現有項目
              await tx.expenseItem.update({
                where: { id: item.id },
                data: {
                  itemName: item.itemName,
                  description: item.description,
                  amount: item.amount,
                  category: item.category,
                  sortOrder: item.sortOrder,
                },
              });
            } else {
              // 新增項目
              await tx.expenseItem.create({
                data: {
                  expenseId: input.id,
                  itemName: item.itemName,
                  description: item.description,
                  amount: item.amount,
                  category: item.category,
                  sortOrder: item.sortOrder,
                },
              });
            }
          }

          // 重新計算總金額
          const items = await tx.expenseItem.findMany({
            where: { expenseId: input.id },
          });
          const totalAmount = items.reduce((sum, item) => sum + item.amount, 0);
          updateData.totalAmount = totalAmount;
        }

        // 更新表頭
        const expense = await tx.expense.update({
          where: { id: input.id },
          data: updateData,
          include: {
            items: {
              orderBy: { sortOrder: 'asc' },
            },
          },
        });

        return expense;
      });
    }),
});
```

### 前端頁面設計

由於費用管理的前端設計與採購管理非常相似（都是表頭-明細模式），這裡僅列出關鍵差異：

#### 費用表單新增欄位

**1. 項目選擇器** (✅ 新增)
```typescript
// 在 ExpenseForm 中新增項目選擇欄位

<FormField
  control={form.control}
  name="projectId"
  render={({ field }) => (
    <FormItem>
      <FormLabel>關聯項目 *</FormLabel>
      <FormControl>
        <Select
          value={field.value}
          onValueChange={field.onChange}
        >
          <SelectTrigger>
            <SelectValue placeholder="請選擇項目" />
          </SelectTrigger>
          <SelectContent>
            {projects?.map((project) => (
              <SelectItem key={project.id} value={project.id}>
                {project.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </FormControl>
      <FormDescription>
        費用將直接關聯到此項目
      </FormDescription>
    </FormItem>
  )}
/>
```

**設計說明**：
- **自動填充**：選擇採購單後，自動填入對應的項目（可手動調整）
- **數據一致性**：前端驗證確保選擇的項目與採購單的項目一致
- **查詢優化**：項目選擇器僅顯示當前用戶有權限查看的項目

**2. 分類標記欄位** (✅ 新增)
```typescript
// 在 ExpenseForm 中新增的特殊欄位

<FormField
  control={form.control}
  name="requiresChargeOut"
  render={({ field }) => (
    <FormItem className="flex items-center space-x-2">
      <FormControl>
        <Checkbox
          checked={field.value}
          onCheckedChange={field.onChange}
        />
      </FormControl>
      <FormLabel>需要費用轉嫁</FormLabel>
      <FormDescription>
        此費用是否需要向其他 OpCo 轉嫁收費
      </FormDescription>
    </FormItem>
  )}
/>

<FormField
  control={form.control}
  name="isOperationMaint"
  render={({ field }) => (
    <FormItem className="flex items-center space-x-2">
      <FormControl>
        <Checkbox
          checked={field.value}
          onCheckedChange={field.onChange}
        />
      </FormControl>
      <FormLabel>操作與維護費用</FormLabel>
      <FormDescription>
        標記為 O&M 費用以便於統計分析
      </FormDescription>
    </FormItem>
  )}
/>
```

---

## 模塊 6: 操作與維護費用 (OM Expense) - 新增模塊

### 業務需求重述

```yaml
核心需求:
  - 表頭-明細結構（Header-Detail Pattern）
  - 表頭欄位: 名稱、描述、年度、O&M類別、供應商、預算金額、實際支出金額、
              增長率(對比上年度)、OpCo持有者、開始日期、終結日期
  - 月度記錄: 每年度 1-12月 的每月實際支出記錄
  - 自動計算實際支出總額和增長率
```

### 數據庫 Schema 設計

#### 新增 OMExpense 模型（表頭）

```prisma
// ✅ 新增：操作與維護費用（表頭）
model OMExpense {
  id          String @id @default(uuid())

  // 基本信息
  name        String   // OM費用名稱
  description String?  @db.Text

  // 年度和類別
  financialYear Int    // 財務年度
  category      String // OM類別（如: Server Maintenance, License Renewal, Support Contract）

  // OpCo 歸屬
  opCoId      String // 持有此費用的 OpCo

  // 預算和實際
  budgetAmount Float  // 預算金額
  actualSpent  Float  @default(0)  // ❌ 不手動輸入，由月度記錄自動計算

  // 增長率（對比上年度）
  yoyGrowthRate Float? // Year-over-Year Growth Rate (%)

  // 供應商
  vendorId    String?

  // 日期範圍
  startDate   DateTime
  endDate     DateTime

  // 元數據
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  // 關聯
  opCo           OperatingCompany @relation(fields: [opCoId], references: [id])
  vendor         Vendor?          @relation(fields: [vendorId], references: [id])
  monthlyRecords OMExpenseMonthly[] // ✅ 月度支出記錄（1-12月）

  @@index([opCoId])
  @@index([vendorId])
  @@index([financialYear])
  @@index([category])
}
```

#### 新增 OMExpenseMonthly 模型（月度記錄）

```prisma
// ✅ 新增：OM費用月度記錄
model OMExpenseMonthly {
  id          String @id @default(uuid())
  omExpenseId String

  // 月份 (1-12)
  month       Int   // 1 = January, 12 = December

  // 實際支出
  actualAmount Float // 該月實際支出金額

  // OpCo（冗余，方便查詢）
  opCoId      String

  // 元數據
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  // 關聯
  omExpense OMExpense        @relation(fields: [omExpenseId], references: [id], onDelete: Cascade)
  opCo      OperatingCompany @relation(fields: [opCoId], references: [id])

  @@unique([omExpenseId, month]) // 每個 OM 費用每月只能有一條記錄
  @@index([omExpenseId])
  @@index([opCoId])
  @@index([month])
}
```

#### Vendor 模型需要新增關聯

```prisma
model Vendor {
  // ... 現有欄位 ...

  omExpenses OMExpense[]  // ✅ 新增
}
```

### 後端 API 設計 (tRPC)

```typescript
// packages/api/src/routers/omExpense.ts

export const omExpenseRouter = createTRPCRouter({

  /**
   * 創建 OM 費用（含初始月度記錄）
   */
  create: protectedProcedure
    .input(z.object({
      name: z.string().min(1),
      description: z.string().optional(),
      financialYear: z.number(),
      category: z.string().min(1),
      opCoId: z.string().min(1),
      budgetAmount: z.number().min(0),
      vendorId: z.string().optional(),
      startDate: z.string(),
      endDate: z.string(),
      monthlyRecords: z.array(z.object({
        month: z.number().min(1).max(12),
        actualAmount: z.number().min(0),
      })).optional(), // 可選：創建時可以不輸入月度記錄
    }))
    .mutation(async ({ ctx, input }) => {
      return await ctx.prisma.$transaction(async (tx) => {
        // 創建 OM 費用表頭
        const omExpense = await tx.omExpense.create({
          data: {
            name: input.name,
            description: input.description,
            financialYear: input.financialYear,
            category: input.category,
            opCoId: input.opCoId,
            budgetAmount: input.budgetAmount,
            vendorId: input.vendorId,
            startDate: new Date(input.startDate),
            endDate: new Date(input.endDate),
          },
        });

        // 如果提供了月度記錄，創建它們
        if (input.monthlyRecords && input.monthlyRecords.length > 0) {
          await tx.omExpenseMonthly.createMany({
            data: input.monthlyRecords.map(record => ({
              omExpenseId: omExpense.id,
              opCoId: input.opCoId,
              month: record.month,
              actualAmount: record.actualAmount,
            })),
          });

          // 計算總實際支出
          const actualSpent = input.monthlyRecords.reduce(
            (sum, record) => sum + record.actualAmount,
            0
          );

          // 更新 actualSpent
          await tx.omExpense.update({
            where: { id: omExpense.id },
            data: { actualSpent },
          });
        }

        return omExpense;
      });
    }),

  /**
   * 更新月度記錄（單月或批量）
   */
  updateMonthlyRecords: protectedProcedure
    .input(z.object({
      omExpenseId: z.string().min(1),
      records: z.array(z.object({
        month: z.number().min(1).max(12),
        actualAmount: z.number().min(0),
      })),
    }))
    .mutation(async ({ ctx, input }) => {
      return await ctx.prisma.$transaction(async (tx) => {
        // 獲取 OM 費用以便取得 opCoId
        const omExpense = await tx.omExpense.findUnique({
          where: { id: input.omExpenseId },
        });

        if (!omExpense) throw new TRPCError({ code: 'NOT_FOUND' });

        // 更新或創建月度記錄
        for (const record of input.records) {
          await tx.omExpenseMonthly.upsert({
            where: {
              omExpenseId_month: {
                omExpenseId: input.omExpenseId,
                month: record.month,
              },
            },
            update: {
              actualAmount: record.actualAmount,
            },
            create: {
              omExpenseId: input.omExpenseId,
              opCoId: omExpense.opCoId,
              month: record.month,
              actualAmount: record.actualAmount,
            },
          });
        }

        // 重新計算總實際支出
        const allRecords = await tx.omExpenseMonthly.findMany({
          where: { omExpenseId: input.omExpenseId },
        });

        const actualSpent = allRecords.reduce(
          (sum, record) => sum + record.actualAmount,
          0
        );

        // 更新 OM 費用的 actualSpent
        await tx.omExpense.update({
          where: { id: input.omExpenseId },
          data: { actualSpent },
        });

        return { success: true, actualSpent };
      });
    }),

  /**
   * 計算增長率（對比上年度）
   */
  calculateYoYGrowth: protectedProcedure
    .input(z.object({ id: z.string().min(1) }))
    .mutation(async ({ ctx, input }) => {
      const currentOMExpense = await ctx.prisma.omExpense.findUnique({
        where: { id: input.id },
      });

      if (!currentOMExpense) throw new TRPCError({ code: 'NOT_FOUND' });

      // 查找上年度同類別同名稱的 OM 費用
      const previousYear = currentOMExpense.financialYear - 1;
      const previousOMExpense = await ctx.prisma.omExpense.findFirst({
        where: {
          name: currentOMExpense.name,
          category: currentOMExpense.category,
          opCoId: currentOMExpense.opCoId,
          financialYear: previousYear,
        },
      });

      if (!previousOMExpense || previousOMExpense.actualSpent === 0) {
        // 無法計算增長率
        return { yoyGrowthRate: null, message: '無上年度數據可比較' };
      }

      // 計算增長率 = (本年 - 上年) / 上年 * 100
      const yoyGrowthRate =
        ((currentOMExpense.actualSpent - previousOMExpense.actualSpent) /
          previousOMExpense.actualSpent) *
        100;

      // 更新增長率
      await ctx.prisma.omExpense.update({
        where: { id: input.id },
        data: { yoyGrowthRate },
      });

      return {
        yoyGrowthRate,
        currentYear: currentOMExpense.financialYear,
        currentAmount: currentOMExpense.actualSpent,
        previousYear,
        previousAmount: previousOMExpense.actualSpent,
      };
    }),

  /**
   * 獲取 OM 費用詳情（含月度記錄）
   */
  getById: protectedProcedure
    .input(z.object({ id: z.string().min(1) }))
    .query(async ({ ctx, input }) => {
      const omExpense = await ctx.prisma.omExpense.findUnique({
        where: { id: input.id },
        include: {
          opCo: true,
          vendor: true,
          monthlyRecords: {
            orderBy: { month: 'asc' },
          },
        },
      });

      if (!omExpense) throw new TRPCError({ code: 'NOT_FOUND' });
      return omExpense;
    }),

  /**
   * 按 OpCo 和年度獲取所有 OM 費用
   */
  getAll: protectedProcedure
    .input(z.object({
      opCoId: z.string().optional(),
      financialYear: z.number().optional(),
      category: z.string().optional(),
    }))
    .query(async ({ ctx, input }) => {
      const omExpenses = await ctx.prisma.omExpense.findMany({
        where: {
          ...(input.opCoId && { opCoId: input.opCoId }),
          ...(input.financialYear && { financialYear: input.financialYear }),
          ...(input.category && { category: input.category }),
        },
        include: {
          opCo: true,
          vendor: {
            select: {
              id: true,
              name: true,
            },
          },
          _count: {
            select: { monthlyRecords: true },
          },
        },
        orderBy: [
          { financialYear: 'desc' },
          { category: 'asc' },
        ],
      });

      return omExpenses;
    }),
});
```

### 前端頁面設計

#### 1. OM 費用列表頁 (`/om-expenses/page.tsx`)

```typescript
export default function OMExpensesPage() {
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [selectedOpCo, setSelectedOpCo] = useState<string | null>(null);

  const { data: omExpenses } = api.omExpense.getAll.useQuery({
    financialYear: selectedYear,
    opCoId: selectedOpCo || undefined,
  });

  return (
    <DashboardLayout>
      <PageHeader
        title="操作與維護費用管理"
        description="管理年度 O&M 費用和月度支出記錄"
      >
        <Button onClick={() => router.push('/om-expenses/new')}>
          <Plus className="h-4 w-4 mr-2" />
          新增 OM 費用
        </Button>
      </PageHeader>

      {/* 篩選器 */}
      <Card className="mb-6">
        <CardContent className="flex gap-4 pt-6">
          <Select value={selectedYear.toString()} onValueChange={(val) => setSelectedYear(parseInt(val))}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="選擇年度" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="2025">FY2025</SelectItem>
              <SelectItem value="2024">FY2024</SelectItem>
              <SelectItem value="2023">FY2023</SelectItem>
            </SelectContent>
          </Select>

          <OpCoSelect value={selectedOpCo} onChange={setSelectedOpCo} />
        </CardContent>
      </Card>

      {/* OM 費用卡片列表 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {omExpenses?.map(om => (
          <OMExpenseCard key={om.id} omExpense={om} />
        ))}
      </div>
    </DashboardLayout>
  );
}
```

#### 2. OM 費用詳情頁（含月度編輯網格）(`/om-expenses/[id]/page.tsx`)

```typescript
export default function OMExpenseDetailPage({ params }: { params: { id: string } }) {
  const { data: om } = api.omExpense.getById.useQuery({ id: params.id });
  const updateMonthly = api.omExpense.updateMonthlyRecords.useMutation();

  // 月度數據（1-12月）
  const monthlyData = useMemo(() => {
    const data = Array.from({ length: 12 }, (_, i) => ({
      month: i + 1,
      actualAmount: 0,
    }));

    om?.monthlyRecords.forEach(record => {
      data[record.month - 1].actualAmount = record.actualAmount;
    });

    return data;
  }, [om?.monthlyRecords]);

  const handleSaveMonthly = async (updatedData: typeof monthlyData) => {
    await updateMonthly.mutateAsync({
      omExpenseId: params.id,
      records: updatedData,
    });
  };

  return (
    <DashboardLayout>
      <PageHeader
        title={om.name}
        backLink="/om-expenses"
      >
        <div className="flex gap-2">
          <Button onClick={handleCalculateGrowth}>
            計算增長率
          </Button>
          <Button variant="outline" onClick={() => router.push(`/om-expenses/${om.id}/edit`)}>
            <Edit className="h-4 w-4 mr-2" />
            編輯
          </Button>
        </div>
      </PageHeader>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 左側：基本信息和月度記錄 */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>基本信息</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-4">
              <InfoRow label="OM 類別" value={om.category} />
              <InfoRow label="財務年度" value={`FY${om.financialYear}`} />
              <InfoRow label="OpCo 持有者" value={om.opCo.name} />
              <InfoRow label="供應商" value={om.vendor?.name || '-'} />
              <InfoRow label="開始日期" value={formatDate(om.startDate)} />
              <InfoRow label="結束日期" value={formatDate(om.endDate)} />
              <div className="col-span-2">
                <Label>描述</Label>
                <p className="mt-1 text-sm text-muted-foreground">{om.description || '-'}</p>
              </div>
            </CardContent>
          </Card>

          {/* 月度支出記錄編輯網格 */}
          <Card>
            <CardHeader>
              <CardTitle>月度支出記錄</CardTitle>
              <CardDescription>
                點擊單元格編輯每月實際支出金額
              </CardDescription>
            </CardHeader>
            <CardContent>
              <MonthlyGrid
                data={monthlyData}
                onSave={handleSaveMonthly}
              />

              {/* 月度總計 */}
              <div className="mt-6 p-4 bg-muted rounded-lg">
                <div className="flex justify-between items-center">
                  <span className="font-semibold">年度總計</span>
                  <span className="text-2xl font-bold">
                    {formatCurrency(om.actualSpent)}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 右側：預算對比和增長率 */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>預算對比</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <StatsCard
                label="預算金額"
                value={formatCurrency(om.budgetAmount)}
                icon={Target}
              />
              <StatsCard
                label="實際支出"
                value={formatCurrency(om.actualSpent)}
                icon={DollarSign}
              />
              <StatsCard
                label="剩餘預算"
                value={formatCurrency(om.budgetAmount - om.actualSpent)}
                icon={PiggyBank}
                variant={om.actualSpent > om.budgetAmount ? 'danger' : 'success'}
              />

              {/* 使用率進度條 */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>預算使用率</span>
                  <span>{((om.actualSpent / om.budgetAmount) * 100).toFixed(1)}%</span>
                </div>
                <Progress
                  value={(om.actualSpent / om.budgetAmount) * 100}
                  className={cn(
                    "h-2",
                    om.actualSpent > om.budgetAmount ? "bg-red-200" :
                    om.actualSpent > om.budgetAmount * 0.9 ? "bg-yellow-200" :
                    "bg-green-200"
                  )}
                />
              </div>
            </CardContent>
          </Card>

          {/* 增長率 */}
          {om.yoyGrowthRate !== null && (
            <Card>
              <CardHeader>
                <CardTitle>同比增長率</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <p className={cn(
                    "text-4xl font-bold",
                    om.yoyGrowthRate > 0 ? "text-red-600" :
                    om.yoyGrowthRate < 0 ? "text-green-600" :
                    "text-muted-foreground"
                  )}>
                    {om.yoyGrowthRate > 0 ? '+' : ''}{om.yoyGrowthRate.toFixed(1)}%
                  </p>
                  <p className="text-sm text-muted-foreground mt-2">
                    對比 FY{om.financialYear - 1}
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
```

#### 3. MonthlyGrid 組件（可編輯月度網格）

```typescript
// components/om-expense/MonthlyGrid.tsx

interface MonthlyGridProps {
  data: Array<{ month: number; actualAmount: number }>;
  onSave: (data: Array<{ month: number; actualAmount: number }>) => Promise<void>;
}

export function MonthlyGrid({ data, onSave }: MonthlyGridProps) {
  const [editingData, setEditingData] = useState(data);
  const [isDirty, setIsDirty] = useState(false);

  const monthNames = [
    '1月', '2月', '3月', '4月', '5月', '6月',
    '7月', '8月', '9月', '10月', '11月', '12月'
  ];

  const handleAmountChange = (month: number, amount: number) => {
    const newData = editingData.map(item =>
      item.month === month ? { ...item, actualAmount: amount } : item
    );
    setEditingData(newData);
    setIsDirty(true);
  };

  const handleSave = async () => {
    await onSave(editingData);
    setIsDirty(false);
    toast.success('月度記錄已更新');
  };

  const handleReset = () => {
    setEditingData(data);
    setIsDirty(false);
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {editingData.map((item, index) => (
          <Card key={item.month} className="p-4">
            <div className="space-y-2">
              <Label className="text-sm font-semibold">
                {monthNames[index]}
              </Label>
              <Input
                type="number"
                step="0.01"
                value={item.actualAmount}
                onChange={(e) => handleAmountChange(item.month, parseFloat(e.target.value) || 0)}
                className="font-mono"
              />
            </div>
          </Card>
        ))}
      </div>

      {/* 保存/重置按鈕 */}
      {isDirty && (
        <div className="flex gap-2">
          <Button onClick={handleSave}>
            <Save className="h-4 w-4 mr-2" />
            保存更改
          </Button>
          <Button variant="outline" onClick={handleReset}>
            <X className="h-4 w-4 mr-2" />
            重置
          </Button>
        </div>
      )}
    </div>
  );
}
```

---

## 模塊 7: 費用轉嫁 (Charge Out) - 新增模塊

### 業務需求重述

```yaml
核心需求:
  - 表頭-明細結構（Header-Detail Pattern）
  - 表頭欄位: 名稱、描述、關聯項目、OpCo名稱、總金額、Debit Note號碼、收款日期
  - 明細欄位: 關聯的費用記錄、分攤金額
  - 審核/確認工作流（模塊8）
```

### 數據庫 Schema 設計

#### 新增 ChargeOut 模型（表頭）

```prisma
// ✅ 新增：費用轉嫁（表頭）
model ChargeOut {
  id          String @id @default(uuid())

  // 基本信息
  name        String   // Charge Out 名稱
  description String?  @db.Text

  // 關聯項目
  projectId   String

  // OpCo 信息
  opCoId      String   // 向哪個 OpCo 收費

  // 財務信息
  totalAmount Float    // ❌ 不手動輸入，由明細自動計算
  status      String   @default("Draft")  // Draft, Submitted, Confirmed, Paid, Rejected

  // Debit Note 信息
  debitNoteNumber String?  @unique  // Debit Note 號碼
  issueDate       DateTime?         // 開立日期
  paymentDate     DateTime?         // 收款日期

  // 審核信息
  confirmedBy     String?   // 確認者 User ID
  confirmedAt     DateTime? // 確認時間

  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  // 關聯
  project    Project          @relation(fields: [projectId], references: [id])
  opCo       OperatingCompany @relation(fields: [opCoId], references: [id])
  confirmer  User?            @relation("ChargeOutConfirmer", fields: [confirmedBy], references: [id])
  items      ChargeOutItem[]  // ✅ 明細項目（關聯的費用）

  @@index([projectId])
  @@index([opCoId])
  @@index([status])
  @@index([confirmedBy])
}
```

#### 新增 ChargeOutItem 模型（明細）

```prisma
// ✅ 新增：費用轉嫁明細
model ChargeOutItem {
  id           String @id @default(uuid())
  chargeOutId  String

  // 關聯的費用
  expenseId    String  // 關聯到哪筆費用

  // 分攤金額
  amount       Float   // 向此 OpCo 分攤的金額（可能與費用總額不同）
  description  String? @db.Text // 分攤說明

  // 元數據
  sortOrder    Int     @default(0)
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt

  // 關聯
  chargeOut ChargeOut @relation(fields: [chargeOutId], references: [id], onDelete: Cascade)
  expense   Expense   @relation(fields: [expenseId], references: [id])

  @@index([chargeOutId])
  @@index([expenseId])
}
```

#### User 模型需要新增關聯

```prisma
model User {
  // ... 現有欄位 ...

  confirmedChargeOuts ChargeOut[] @relation("ChargeOutConfirmer")  // ✅ 新增
}
```

#### Project 模型需要新增關聯

```prisma
model Project {
  // ... 現有欄位 ...

  chargeOuts ChargeOut[]  // ✅ 新增
}
```

### 後端 API 設計 (tRPC)

```typescript
// packages/api/src/routers/chargeOut.ts

export const chargeOutRouter = createTRPCRouter({

  /**
   * 創建費用轉嫁（含明細）
   */
  create: protectedProcedure
    .input(z.object({
      name: z.string().min(1),
      description: z.string().optional(),
      projectId: z.string().min(1),
      opCoId: z.string().min(1),
      debitNoteNumber: z.string().optional(),
      issueDate: z.string().optional(),
      items: z.array(z.object({
        expenseId: z.string().min(1),
        amount: z.number().min(0),
        description: z.string().optional(),
        sortOrder: z.number().default(0),
      })),
    }))
    .mutation(async ({ ctx, input }) => {
      // 驗證至少要有一個費用項目
      if (input.items.length === 0) {
        throw new TRPCError({
          code: 'BAD_REQUEST',
          message: '至少需要一個費用項目',
        });
      }

      // 驗證所有費用都標記為需要轉嫁
      const expenseIds = input.items.map(item => item.expenseId);
      const expenses = await ctx.prisma.expense.findMany({
        where: {
          id: { in: expenseIds },
        },
      });

      const invalidExpenses = expenses.filter(exp => !exp.requiresChargeOut);
      if (invalidExpenses.length > 0) {
        throw new TRPCError({
          code: 'BAD_REQUEST',
          message: `某些費用未標記為需要轉嫁: ${invalidExpenses.map(e => e.name).join(', ')}`,
        });
      }

      // 計算總金額
      const totalAmount = input.items.reduce((sum, item) => sum + item.amount, 0);

      return await ctx.prisma.$transaction(async (tx) => {
        // 創建費用轉嫁表頭
        const chargeOut = await tx.chargeOut.create({
          data: {
            name: input.name,
            description: input.description,
            projectId: input.projectId,
            opCoId: input.opCoId,
            debitNoteNumber: input.debitNoteNumber,
            issueDate: input.issueDate ? new Date(input.issueDate) : null,
            totalAmount,
            status: 'Draft',
          },
        });

        // 創建明細
        await tx.chargeOutItem.createMany({
          data: input.items.map(item => ({
            chargeOutId: chargeOut.id,
            expenseId: item.expenseId,
            amount: item.amount,
            description: item.description,
            sortOrder: item.sortOrder,
          })),
        });

        return chargeOut;
      });
    }),

  /**
   * 提交費用轉嫁（狀態變更）
   */
  submit: protectedProcedure
    .input(z.object({ id: z.string().min(1) }))
    .mutation(async ({ ctx, input }) => {
      // 驗證至少有一個費用項目
      const itemCount = await ctx.prisma.chargeOutItem.count({
        where: { chargeOutId: input.id },
      });

      if (itemCount === 0) {
        throw new TRPCError({
          code: 'BAD_REQUEST',
          message: '無法提交空的費用轉嫁',
        });
      }

      return await ctx.prisma.chargeOut.update({
        where: { id: input.id },
        data: {
          status: 'Submitted',
        },
      });
    }),

  /**
   * 確認費用轉嫁（主管或財務）
   */
  confirm: supervisorProcedure
    .input(z.object({
      id: z.string().min(1),
      comments: z.string().optional(),
    }))
    .mutation(async ({ ctx, input }) => {
      return await ctx.prisma.$transaction(async (tx) => {
        const chargeOut = await tx.chargeOut.findUnique({
          where: { id: input.id },
          include: {
            project: {
              include: {
                manager: true,
              },
            },
          },
        });

        if (!chargeOut) throw new TRPCError({ code: 'NOT_FOUND' });

        // 更新狀態
        const updated = await tx.chargeOut.update({
          where: { id: input.id },
          data: {
            status: 'Confirmed',
            confirmedBy: ctx.session.user.id,
            confirmedAt: new Date(),
          },
        });

        // 發送通知
        await tx.notification.create({
          data: {
            userId: chargeOut.project.managerId,
            type: 'CHARGEOUT_CONFIRMED',
            title: '費用轉嫁已確認',
            message: `費用轉嫁「${chargeOut.name}」已確認，金額: ${formatCurrency(chargeOut.totalAmount)}`,
            link: `/charge-outs/${chargeOut.id}`,
            entityType: 'CHARGEOUT',
            entityId: chargeOut.id,
          },
        });

        return updated;
      });
    }),

  /**
   * 標記為已收款
   */
  markAsPaid: supervisorProcedure
    .input(z.object({
      id: z.string().min(1),
      paymentDate: z.string(),
    }))
    .mutation(async ({ ctx, input }) => {
      return await ctx.prisma.chargeOut.update({
        where: { id: input.id },
        data: {
          status: 'Paid',
          paymentDate: new Date(input.paymentDate),
        },
      });
    }),

  /**
   * 獲取費用轉嫁詳情（含明細）
   */
  getById: protectedProcedure
    .input(z.object({ id: z.string().min(1) }))
    .query(async ({ ctx, input }) => {
      const chargeOut = await ctx.prisma.chargeOut.findUnique({
        where: { id: input.id },
        include: {
          project: {
            select: {
              id: true,
              name: true,
            },
          },
          opCo: true,
          confirmer: {
            select: {
              id: true,
              name: true,
              email: true,
            },
          },
          items: {
            include: {
              expense: {
                select: {
                  id: true,
                  name: true,
                  totalAmount: true,
                  invoiceNumber: true,
                },
              },
            },
            orderBy: { sortOrder: 'asc' },
          },
        },
      });

      if (!chargeOut) throw new TRPCError({ code: 'NOT_FOUND' });
      return chargeOut;
    }),

  /**
   * 獲取所有費用轉嫁
   */
  getAll: protectedProcedure
    .input(z.object({
      projectId: z.string().optional(),
      opCoId: z.string().optional(),
      status: z.string().optional(),
    }))
    .query(async ({ ctx, input }) => {
      const chargeOuts = await ctx.prisma.chargeOut.findMany({
        where: {
          ...(input.projectId && { projectId: input.projectId }),
          ...(input.opCoId && { opCoId: input.opCoId }),
          ...(input.status && { status: input.status }),
        },
        include: {
          project: {
            select: {
              id: true,
              name: true,
            },
          },
          opCo: {
            select: {
              id: true,
              name: true,
              code: true,
            },
          },
          _count: {
            select: { items: true },
          },
        },
        orderBy: {
          createdAt: 'desc',
        },
      });

      return chargeOuts;
    }),
});
```

### 前端頁面設計

#### 1. 費用轉嫁列表頁 (`/charge-outs/page.tsx`)

```typescript
export default function ChargeOutsPage() {
  const { data: chargeOuts } = api.chargeOut.getAll.useQuery({});

  return (
    <DashboardLayout>
      <PageHeader
        title="費用轉嫁管理"
        description="管理向其他 OpCo 的費用轉嫁"
      >
        <Button onClick={() => router.push('/charge-outs/new')}>
          <Plus className="h-4 w-4 mr-2" />
          新增費用轉嫁
        </Button>
      </PageHeader>

      <DataTable
        columns={[
          { key: 'debitNoteNumber', label: 'DN 編號' },
          { key: 'name', label: '轉嫁名稱' },
          { key: 'project.name', label: '關聯項目' },
          { key: 'opCo.name', label: '目標 OpCo' },
          { key: 'totalAmount', label: '總金額', format: 'currency' },
          { key: 'status', label: '狀態', component: StatusBadge },
          { key: 'issueDate', label: '開立日期', format: 'date' },
          { key: 'paymentDate', label: '收款日期', format: 'date' },
        ]}
        data={chargeOuts || []}
      />
    </DashboardLayout>
  );
}
```

#### 2. 費用轉嫁詳情頁 (`/charge-outs/[id]/page.tsx`)

```typescript
export default function ChargeOutDetailPage({ params }: { params: { id: string } }) {
  const { data: co } = api.chargeOut.getById.useQuery({ id: params.id });

  return (
    <DashboardLayout>
      <PageHeader
        title={`${co.debitNoteNumber || 'DN-XXX'} - ${co.name}`}
        backLink="/charge-outs"
      >
        <div className="flex gap-2">
          {co.status === 'Draft' && (
            <Button onClick={handleSubmit}>提交確認</Button>
          )}
          {isSupervisor && co.status === 'Submitted' && (
            <Button onClick={handleConfirm}>確認</Button>
          )}
          {isSupervisor && co.status === 'Confirmed' && (
            <Button onClick={handleMarkAsPaid}>標記為已收款</Button>
          )}
          <Button variant="outline" onClick={() => router.push(`/charge-outs/${co.id}/edit`)}>
            <Edit className="h-4 w-4 mr-2" />
            編輯
          </Button>
        </div>
      </PageHeader>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 左側：基本信息和明細 */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>基本信息</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-4">
              <InfoRow label="DN 編號" value={co.debitNoteNumber || '-'} />
              <InfoRow label="狀態" value={<StatusBadge status={co.status} />} />
              <InfoRow label="目標 OpCo" value={co.opCo.name} />
              <InfoRow label="關聯項目" value={
                <Link href={`/projects/${co.project.id}`} className="text-primary hover:underline">
                  {co.project.name}
                </Link>
              } />
              <InfoRow label="開立日期" value={
                co.issueDate ? formatDate(co.issueDate) : '-'
              } />
              <InfoRow label="收款日期" value={
                co.paymentDate ? formatDate(co.paymentDate) : '-'
              } />
              <InfoRow label="確認者" value={co.confirmer?.name || '-'} />
              <InfoRow label="確認時間" value={
                co.confirmedAt ? formatDate(co.confirmedAt) : '-'
              } />
              <div className="col-span-2">
                <Label>描述</Label>
                <p className="mt-1 text-sm text-muted-foreground">{co.description || '-'}</p>
              </div>
            </CardContent>
          </Card>

          {/* 費用明細 */}
          <Card>
            <CardHeader>
              <CardTitle>費用明細</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>費用名稱</TableHead>
                    <TableHead>發票號碼</TableHead>
                    <TableHead className="text-right">費用總額</TableHead>
                    <TableHead className="text-right">分攤金額</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {co.items.map(item => (
                    <TableRow key={item.id}>
                      <TableCell className="font-medium">
                        <Link
                          href={`/expenses/${item.expense.id}`}
                          className="text-primary hover:underline"
                        >
                          {item.expense.name}
                        </Link>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {item.expense.invoiceNumber || '-'}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(item.expense.totalAmount)}
                      </TableCell>
                      <TableCell className="text-right font-semibold">
                        {formatCurrency(item.amount)}
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow>
                    <TableCell colSpan={3} className="text-right font-bold">
                      總計
                    </TableCell>
                    <TableCell className="text-right font-bold text-lg">
                      {formatCurrency(co.totalAmount)}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>

        {/* 右側：統計信息 */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>轉嫁統計</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <StatsCard
                label="費用項目數"
                value={co.items.length}
                icon={FileText}
              />
              <StatsCard
                label="總轉嫁金額"
                value={formatCurrency(co.totalAmount)}
                icon={DollarSign}
              />
              <StatsCard
                label="狀態"
                value={co.status}
                icon={Info}
              />
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
```

---

## 模塊 8: 費用轉嫁確認 (Charge Out Confirmation) - 工作流

### 業務需求重述

```yaml
核心需求:
  - 費用轉嫁的審核/確認工作流
  - 狀態流程: Draft → Submitted → Confirmed → Paid
  - 確認者記錄和確認時間
  - 通知機制
```

### 實施說明

**模塊 8 已整合到模塊 7 的 ChargeOut 模型中：**

1. **狀態流程**：
   - `status` 欄位定義了完整的工作流狀態
   - Draft → Submitted → Confirmed → Paid (或 Rejected)

2. **審核記錄**：
   - `confirmedBy` - 記錄確認者
   - `confirmedAt` - 記錄確認時間

3. **API 支持**：
   - `chargeOut.submit()` - 提交確認
   - `chargeOut.confirm()` - 確認費用轉嫁（主管權限）
   - `chargeOut.markAsPaid()` - 標記為已收款

4. **通知機制**：
   - 確認時自動發送通知給項目負責人
   - 使用現有的 Notification 系統（Epic 8）

### 前端審批界面

在費用轉嫁詳情頁已包含審批按鈕：

```typescript
{/* 在 ChargeOutDetailPage 中 */}
{isSupervisor && co.status === 'Submitted' && (
  <Button onClick={handleConfirm}>確認</Button>
)}
```

確認對話框：

```typescript
// components/charge-out/ConfirmDialog.tsx

export function ConfirmChargeOutDialog({ chargeOut, onConfirm }: Props) {
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>確認費用轉嫁</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="p-4 bg-muted rounded-lg">
            <div className="flex justify-between items-center">
              <span className="font-semibold">轉嫁金額</span>
              <span className="text-2xl font-bold">
                {formatCurrency(chargeOut.totalAmount)}
              </span>
            </div>
            <div className="flex justify-between items-center mt-2">
              <span className="text-sm text-muted-foreground">目標 OpCo</span>
              <span className="text-sm font-medium">{chargeOut.opCo.name}</span>
            </div>
          </div>

          <FormField
            control={form.control}
            name="comments"
            render={({ field }) => (
              <FormItem>
                <FormLabel>確認意見（可選）</FormLabel>
                <FormControl>
                  <Textarea placeholder="確認意見..." rows={4} {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <div className="flex gap-2">
            <Button
              onClick={() => form.handleSubmit(onConfirm)()}
              className="flex-1"
            >
              確認費用轉嫁
            </Button>
            <Button
              variant="outline"
              onClick={() => setOpen(false)}
            >
              取消
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

---

## 📦 完整實施計劃總結

### 已完成設計的模塊

1. ✅ **模塊 1: 預算池** - 多類別重構（BudgetPool + BudgetCategory）
2. ✅ **模塊 2: 項目管理** - 欄位擴展（budgetCategoryId, requestedBudget, approvedBudget）
3. ✅ **模塊 3: 預算提案** - 功能擴展（文件上傳、會議記錄、批准金額）
4. ✅ **模塊 4: 採購管理** - 表頭明細重構（PurchaseOrder + PurchaseOrderItem）
5. ✅ **模塊 5: 費用管理** - 重構和擴展（Expense + ExpenseItem）
6. ✅ **模塊 6: OM 費用** - 新增模塊（OMExpense + OMExpenseMonthly）
7. ✅ **模塊 7: 費用轉嫁** - 新增模塊（ChargeOut + ChargeOutItem）
8. ✅ **模塊 8: 費用轉嫁確認** - 工作流（整合到 ChargeOut）

### 新增的資料模型

**完全新增**：
- `OperatingCompany` - OpCo 管理
- `BudgetCategory` - 預算類別
- `PurchaseOrderItem` - 採購品項明細
- `ExpenseItem` - 費用明細
- `OMExpense` - 操作維護費用表頭
- `OMExpenseMonthly` - OM 月度記錄
- `ChargeOut` - 費用轉嫁表頭
- `ChargeOutItem` - 費用轉嫁明細

**修改的模型**：
- `BudgetPool` - 移除 totalAmount/usedAmount，改由類別計算
- `Project` - 新增 budgetCategoryId, requestedBudget, approvedBudget
- `BudgetProposal` - 新增 11 個欄位（文件、會議、批准）
- `PurchaseOrder` - 新增 name, description, status, approvedDate
- `Expense` - 新增 name, description, budgetCategoryId, vendorId, requiresChargeOut, isOperationMaint
- `User` - 新增 approvedProposals, confirmedChargeOuts 關聯
- `Vendor` - 新增 expenses, omExpenses 關聯

### 實施工時估算

| 階段 | 工時 | 說明 |
|------|------|------|
| **Phase 1: 數據庫遷移** | 5-7 天 | Prisma schema 修改、遷移腳本、資料備份 |
| **Phase 2: 後端 API** | 8-10 天 | tRPC routers、業務邏輯、事務處理 |
| **Phase 3: 前端 UI** | 12-15 天 | 頁面、表單、組件、工作流 |
| **Phase 4: 測試** | 5-6 天 | 單元測試、整合測試、E2E 測試 |
| **Phase 5: 部署** | 2-3 天 | 生產部署、監控、回滾計劃 |
| **總計** | **32-41 天** | **約 6-8 週** |

### 關鍵技術挑戰

1. **數據遷移**：
   - 現有 PurchaseOrder 和 Expense 需要遷移到新的表頭-明細結構
   - BudgetPool 的 totalAmount/usedAmount 需要遷移到 BudgetCategory

2. **業務邏輯複雜度**：
   - 預算池使用金額的實時更新
   - OM 費用的月度記錄和增長率計算
   - 費用轉嫁的多方關聯

3. **性能優化**：
   - 表頭-明細的批量操作優化
   - 月度網格的高效更新
   - 預算使用金額的計算緩存

### 下一步行動

1. **用戶確認**：
   - 確認所有業務需求是否完整覆蓋
   - 確認 UI/UX 設計符合預期
   - 確認數據模型設計合理

2. **創建支持文檔**：
   - `DATABASE-MIGRATION-GUIDE.md` - 完整的遷移策略
   - `API-SPECIFICATION.md` - API 端點詳細文檔
   - `TESTING-PLAN.md` - 測試策略和用例

3. **開始實施**：
   - 按優先順序逐個模塊實施
   - 每個模塊完成後進行測試
   - 持續與用戶溝通確認

---

**文檔版本**: 3.0 (完整版)
**最後更新**: 2025-10-26
**狀態**: ✅ 全部 8 個模塊設計完成
**覆蓋範圍**: Database Schema + Backend API + Frontend UI + Workflows

