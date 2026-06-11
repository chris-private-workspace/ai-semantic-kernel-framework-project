# FEAT-003: O&M Summary 頁面 - 技術設計

> **建立日期**: 2025-11-29
> **狀態**: 📋 設計完成
> **版本**: 1.0

---

## 1. 數據模型

### 1.1 現有模型（無需修改）

本功能使用現有的數據模型，不需要新增 Prisma Schema：

```prisma
// 營運公司
model OperatingCompany {
  id          String   @id @default(uuid())
  code        String   @unique  // 如: "RHK", "RTH", "RTW"
  name        String
  isActive    Boolean  @default(true)
  omExpenses  OMExpense[]
}

// O&M 費用
model OMExpense {
  id            String   @id @default(uuid())
  name          String   // 項目名稱
  description   String?  // 項目描述
  financialYear Int      // 財務年度
  category      String   // O&M 類別
  opCoId        String   // 所屬 OpCo
  budgetAmount  Float    // 預算金額
  actualSpent   Float    // 實際支出（自動計算）
  endDate       DateTime // 維護到期日

  opCo          OperatingCompany @relation(...)
}
```

### 1.2 數據流圖

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  OMSummaryPage  │────▶│  tRPC Query     │────▶│  Prisma Client  │
│  (Frontend)     │     │  getSummary     │     │  (Database)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        │ Filters               │ Aggregation           │ Raw Data
        ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ - currentYear   │     │ - Group by Cat  │     │ - OMExpense     │
│ - previousYear  │     │ - Group by OpCo │     │ - OpCo          │
│ - opCoIds[]     │     │ - Calculate %   │     │                 │
│ - categories[]  │     │ - Sum totals    │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## 2. API 設計

### 2.1 新增 Procedure: `getSummary`

**位置**: `packages/api/src/routers/omExpense.ts`

```typescript
/**
 * 獲取 O&M Summary 數據
 * 支援跨年度比較，按 Category 和 OpCo 分組匯總
 */
getSummary: protectedProcedure
  .input(z.object({
    currentYear: z.number().int().min(2000).max(2100),
    previousYear: z.number().int().min(2000).max(2100),
    opCoIds: z.array(z.string()).optional(),
    categories: z.array(z.string()).optional(),
  }))
  .query(async ({ ctx, input }) => {
    // 實現邏輯見下方
  })
```

### 2.2 返回數據結構

```typescript
interface OMSummaryResponse {
  // 類別匯總數據
  categorySummary: CategorySummaryItem[];

  // 明細數據（階層結構）
  detailData: CategoryDetailGroup[];

  // 總計
  grandTotal: TotalSummary;

  // 元數據
  meta: {
    currentYear: number;
    previousYear: number;
    selectedOpCos: string[];
    selectedCategories: string[];
  };
}

interface CategorySummaryItem {
  category: string;
  currentYearBudget: number;
  previousYearActual: number;
  changePercent: number | null;
  itemCount: number;
}

interface CategoryDetailGroup {
  category: string;
  opCoGroups: OpCoGroup[];
  categoryTotal: TotalSummary;
}

interface OpCoGroup {
  opCoId: string;
  opCoCode: string;
  opCoName: string;
  items: OMExpenseItem[];
  subTotal: TotalSummary;
}

interface OMExpenseItem {
  id: string;
  name: string;
  description: string | null;
  currentYearBudget: number;
  previousYearActual: number | null;
  changePercent: number | null;
  endDate: Date;
}

interface TotalSummary {
  currentYearBudget: number;
  previousYearActual: number;
  changePercent: number | null;
  itemCount?: number;
}
```

### 2.3 API 實現邏輯

```typescript
// 1. 獲取當前年度數據
const currentYearData = await ctx.prisma.oMExpense.findMany({
  where: {
    financialYear: input.currentYear,
    ...(input.opCoIds?.length ? { opCoId: { in: input.opCoIds } } : {}),
    ...(input.categories?.length ? { category: { in: input.categories } } : {}),
  },
  include: { opCo: true },
  orderBy: [{ category: 'asc' }, { opCoId: 'asc' }, { name: 'asc' }],
});

// 2. 獲取上年度數據（用於比較）
const previousYearData = await ctx.prisma.oMExpense.findMany({
  where: {
    financialYear: input.previousYear,
    ...(input.opCoIds?.length ? { opCoId: { in: input.opCoIds } } : {}),
    ...(input.categories?.length ? { category: { in: input.categories } } : {}),
  },
});

// 3. 建立上年度數據的查找表
const previousYearMap = new Map<string, number>();
previousYearData.forEach(item => {
  const key = `${item.category}-${item.opCoId}-${item.name}`;
  previousYearMap.set(key, item.actualSpent);
});

// 4. 分組和計算
// ... (詳細實現)
```

---

## 3. 前端組件設計

### 3.1 組件結構

```
apps/web/src/
├── app/[locale]/
│   └── om-summary/
│       └── page.tsx               # 主頁面
│
└── components/
    └── om-summary/
        ├── index.ts               # 統一導出
        ├── OMSummaryFilters.tsx   # 過濾器組件
        ├── OMSummaryCategoryGrid.tsx  # 類別匯總表格
        ├── OMSummaryDetailGrid.tsx    # 項目明細表格
        └── OMSummaryExport.tsx    # 導出功能（可選）
```

### 3.2 組件設計

#### 3.2.1 OMSummaryFilters

```typescript
interface OMSummaryFiltersProps {
  currentYear: number;
  previousYear: number;
  selectedOpCos: string[];
  selectedCategories: string[];
  availableYears: number[];
  availableOpCos: OperatingCompany[];
  availableCategories: string[];
  onFiltersChange: (filters: Filters) => void;
}

// 使用 shadcn/ui 組件
// - Select (年度選擇)
// - Combobox with multi-select (OpCo 多選)
// - Combobox with multi-select (Category 多選)
// - Button (重置)
```

#### 3.2.2 OMSummaryCategoryGrid

```typescript
interface OMSummaryCategoryGridProps {
  data: CategorySummaryItem[];
  currentYear: number;
  previousYear: number;
  isLoading: boolean;
}

// 使用 shadcn/ui Table 組件
// 欄位: Category | FY{year} Budget | FY{year} Actual | Change % | Items
```

#### 3.2.3 OMSummaryDetailGrid

```typescript
interface OMSummaryDetailGridProps {
  data: CategoryDetailGroup[];
  currentYear: number;
  previousYear: number;
  isLoading: boolean;
}

// 使用 shadcn/ui Accordion + Table 組件
// 階層結構: Category > OpCo > Items
```

### 3.3 狀態管理

```typescript
// 使用 React Query (tRPC) 管理服務器狀態
const { data, isLoading, error } = api.omExpense.getSummary.useQuery({
  currentYear: selectedYear,
  previousYear: selectedYear - 1,
  opCoIds: selectedOpCos,
  categories: selectedCategories,
});

// 使用 useState 管理過濾器狀態
const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
const [selectedOpCos, setSelectedOpCos] = useState<string[]>([]);
const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
```

---

## 4. UI/UX 設計

### 4.1 頁面佈局

```
┌──────────────────────────────────────────────────────────────────┐
│ 📊 O&M 費用總覽                                    [Export CSV]  │
├──────────────────────────────────────────────────────────────────┤
│ Filters:                                                          │
│ ┌──────────────┐ ┌──────────────────┐ ┌──────────────────┐       │
│ │ FY: 2026  ▼ │ │ OpCos: All    ▼  │ │ Category: All ▼  │ [Reset]│
│ └──────────────┘ └──────────────────┘ └──────────────────┘       │
├──────────────────────────────────────────────────────────────────┤
│ 📋 類別匯總                                                       │
│ ┌────────────────┬────────────┬────────────┬─────────┬─────────┐ │
│ │ O&M Category   │ FY26 Budget│ FY25 Actual│ Change% │ Items   │ │
│ ├────────────────┼────────────┼────────────┼─────────┼─────────┤ │
│ │ Data Lines     │ $120,000   │ $115,000   │ +4.3%   │ 15      │ │
│ │ Hardware       │ $80,000    │ $85,000    │ -5.9%   │ 10      │ │
│ │ ...            │ ...        │ ...        │ ...     │ ...     │ │
│ ├────────────────┼────────────┼────────────┼─────────┼─────────┤ │
│ │ Total          │ $500,000   │ $480,000   │ +4.2%   │ 51      │ │
│ └────────────────┴────────────┴────────────┴─────────┴─────────┘ │
├──────────────────────────────────────────────────────────────────┤
│ 📝 項目明細                                                       │
│ ▼ Data Lines                                                      │
│   ▼ RHK (3 items)                                                 │
│     ┌────────────────┬────────────┬────────────┬─────────┬──────┐│
│     │ O&M Item       │ FY26 Budget│ FY25 Actual│ Change% │ End  ││
│     ├────────────────┼────────────┼────────────┼─────────┼──────┤│
│     │ R-WAN          │ $10,000    │ $9,500     │ +5.3%   │12/26 ││
│     │ SD-WAN         │ $15,000    │ $14,000    │ +7.1%   │06/26 ││
│     ├────────────────┼────────────┼────────────┼─────────┼──────┤│
│     │ Sub Total      │ $25,000    │ $23,500    │ +6.4%   │ -    ││
│     └────────────────┴────────────┴────────────┴─────────┴──────┘│
│   ▼ RTH (2 items)                                                 │
│     ...                                                           │
│ ▶ Hardware (collapsed)                                            │
│ ▶ Software (collapsed)                                            │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 樣式規範

| 元素 | 樣式 |
|------|------|
| 正增長率 | `text-green-600` |
| 負增長率 | `text-red-600` |
| 零增長率 | `text-gray-500` |
| 小計行 | `bg-muted font-medium` |
| 總計行 | `bg-muted font-bold` |
| 金額格式 | 千分位 + 貨幣符號 (`$1,234,567`) |
| 百分比格式 | 一位小數 + 正負號 (`+5.3%`, `-2.1%`) |
| 日期格式 | `MM/YY` 或 `YYYY/MM/DD` |

### 4.3 響應式設計

| 螢幕尺寸 | 調整 |
|---------|------|
| Desktop (≥1024px) | 完整顯示所有欄位 |
| Tablet (768-1023px) | 隱藏 Description，縮短日期格式 |
| Mobile (<768px) | 卡片式佈局，垂直排列 |

---

## 5. I18N 設計

### 5.1 翻譯 Keys

```json
// zh-TW.json
{
  "omSummary": {
    "title": "O&M 費用總覽",
    "filters": {
      "financialYear": "財務年度",
      "opCos": "營運公司",
      "categories": "O&M 類別",
      "reset": "重置",
      "selectAll": "全選",
      "selected": "已選擇 {count} 項"
    },
    "summaryGrid": {
      "title": "類別匯總",
      "category": "O&M 類別",
      "currentBudget": "FY{year} 預算",
      "previousActual": "FY{year} 實際",
      "changePercent": "變化 %",
      "itemCount": "項目數",
      "total": "總計"
    },
    "detailGrid": {
      "title": "項目明細",
      "item": "O&M 項目",
      "description": "描述",
      "endDate": "到期日",
      "subTotal": "小計",
      "categoryTotal": "類別總計",
      "items": "{count} 項"
    },
    "noData": "無符合條件的資料",
    "loading": "載入中...",
    "export": "匯出 CSV"
  }
}
```

```json
// en.json
{
  "omSummary": {
    "title": "O&M Expense Summary",
    "filters": {
      "financialYear": "Financial Year",
      "opCos": "Operating Companies",
      "categories": "O&M Categories",
      "reset": "Reset",
      "selectAll": "Select All",
      "selected": "{count} selected"
    },
    "summaryGrid": {
      "title": "Category Summary",
      "category": "O&M Category",
      "currentBudget": "FY{year} Budget",
      "previousActual": "FY{year} Actual",
      "changePercent": "Change %",
      "itemCount": "Items",
      "total": "Total"
    },
    "detailGrid": {
      "title": "Item Details",
      "item": "O&M Item",
      "description": "Description",
      "endDate": "End Date",
      "subTotal": "Sub Total",
      "categoryTotal": "Category Total",
      "items": "{count} items"
    },
    "noData": "No data matches the selected criteria",
    "loading": "Loading...",
    "export": "Export CSV"
  }
}
```

---

## 6. 技術依賴

### 6.1 現有依賴（無需新增）
- `@trpc/client`, `@trpc/react-query` - API 通訊
- `@tanstack/react-query` - 資料快取
- `zod` - 輸入驗證
- `next-intl` - 國際化
- `tailwindcss` - 樣式
- `shadcn/ui` - UI 組件
  - Table
  - Select
  - Button
  - Accordion
  - Skeleton (Loading)

### 6.2 可能需要的新依賴
- 無（使用現有組件和工具）

---

## 7. 安全性考量

- 使用 `protectedProcedure` 確保只有登入用戶可以訪問
- 數據過濾基於用戶選擇，不暴露敏感資訊
- API 輸入使用 Zod 驗證，防止注入攻擊

---

## 8. 性能考量

### 8.1 數據庫查詢優化
- 使用適當的索引（`financialYear`, `opCoId`, `category`）
- 一次查詢兩個年度的數據，減少數據庫往返
- 在應用層進行分組和計算，避免複雜的 SQL

### 8.2 前端優化
- 使用 React Query 快取查詢結果
- 使用虛擬滾動（如果項目數量超過 100）
- 延遲載入明細表格（Accordion 收合時不渲染內容）

---

**下一步**: [03-implementation-plan.md](./03-implementation-plan.md)
