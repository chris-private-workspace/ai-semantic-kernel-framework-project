# FEAT-006: Project Summary Tab - 技術設計

> **建立日期**: 2025-12-05
> **狀態**: 📋 設計中

---

## 1. 數據模型變更

### 1.1 Project 模型擴展

```prisma
model Project {
  // ... 現有欄位 ...

  // FEAT-006: Project Summary 新增欄位
  projectCategory   String?   // 專案類別 (Data Lines, Hardware, Software, etc.)
  projectType       String    @default("Project")  // "Project" | "Budget"
  expenseType       String    @default("Expense")  // "Expense" | "Capital" | "Collection"
  chargeBackToOpCo  Boolean   @default(false)      // 是否向 OpCo 收費
  chargeOutMethod   String?   @db.Text             // 如何向 OpCo 收費 (free text)
  probability       String    @default("Medium")   // "High" | "Medium" | "Low"
  team              String?                        // 團隊
  personInCharge    String?                        // 負責人 (PIC)

  // 多對多關係
  chargeOutOpCos    ProjectChargeOutOpCo[]

  // 新索引
  @@index([projectCategory])
  @@index([projectType])
  @@index([expenseType])
  @@index([chargeBackToOpCo])
  @@index([probability])
  @@index([team])
}
```

### 1.2 新增中間表：ProjectChargeOutOpCo

```prisma
// Project 與 OperatingCompany 的多對多關係 (費用轉嫁目標)
model ProjectChargeOutOpCo {
  id        String @id @default(uuid())
  projectId String
  opCoId    String

  project   Project          @relation(fields: [projectId], references: [id], onDelete: Cascade)
  opCo      OperatingCompany @relation(fields: [opCoId], references: [id], onDelete: Cascade)

  createdAt DateTime @default(now())

  @@unique([projectId, opCoId])
  @@index([projectId])
  @@index([opCoId])
}
```

### 1.3 OperatingCompany 模型更新

```prisma
model OperatingCompany {
  // ... 現有欄位 ...

  // FEAT-006: 新增反向關係
  projectChargeOuts ProjectChargeOutOpCo[]
}
```

---

## 2. API 設計

### 2.1 新增 API Endpoints

#### `project.getProjectSummary`

```typescript
// packages/api/src/routers/project.ts

getProjectSummary: protectedProcedure
  .input(z.object({
    financialYear: z.number(),
    budgetCategoryIds: z.array(z.string()).optional(),
    opCoIds: z.array(z.string()).optional(),
  }))
  .query(async ({ ctx, input }) => {
    // 1. 獲取符合條件的 Projects
    const projects = await ctx.prisma.project.findMany({
      where: {
        budgetPool: { financialYear: input.financialYear },
        ...(input.budgetCategoryIds?.length && {
          budgetCategoryId: { in: input.budgetCategoryIds }
        }),
        ...(input.opCoIds?.length && {
          chargeOutOpCos: {
            some: { opCoId: { in: input.opCoIds } }
          }
        }),
      },
      include: {
        budgetPool: true,
        budgetCategory: true,
        currency: true,
        chargeOutOpCos: {
          include: { opCo: true }
        },
      },
    });

    // 2. 計算 Category 匯總
    const categorySummary = calculateCategorySummary(projects);

    // 3. 計算明細數據（按 OpCo → Category 分組）
    const detailData = calculateDetailData(projects);

    // 4. 計算 Grand Total
    const grandTotal = calculateGrandTotal(projects);

    return {
      categorySummary,
      detailData,
      grandTotal,
    };
  }),
```

#### `project.getProjectCategories`

```typescript
// 獲取所有 Project Categories（用於篩選器）
getProjectCategories: protectedProcedure
  .query(async ({ ctx }) => {
    const categories = await ctx.prisma.project.findMany({
      where: { projectCategory: { not: null } },
      select: { projectCategory: true },
      distinct: ['projectCategory'],
    });
    return categories.map(c => c.projectCategory).filter(Boolean);
  }),
```

### 2.2 更新現有 API

#### `project.create` / `project.update`

```typescript
// 添加新欄位到 input schema
const projectInputSchema = z.object({
  // ... 現有欄位 ...

  // FEAT-006 新增欄位
  projectCategory: z.string().optional(),
  projectType: z.enum(['Project', 'Budget']).default('Project'),
  expenseType: z.enum(['Expense', 'Capital', 'Collection']).default('Expense'),
  chargeBackToOpCo: z.boolean().default(false),
  chargeOutOpCoIds: z.array(z.string()).optional(), // 多選 OpCo
  chargeOutMethod: z.string().optional(),
  probability: z.enum(['High', 'Medium', 'Low']).default('Medium'),
  team: z.string().optional(),
  personInCharge: z.string().optional(),
});
```

---

## 3. 組件設計

### 3.1 新增組件

```
apps/web/src/components/
├── summary/                          # 通用 Summary 組件
│   ├── index.ts                      # 導出
│   ├── SummaryTabs.tsx               # Tab 切換組件
│   └── types.ts                      # 類型定義
│
└── project-summary/                  # Project Summary 專用組件
    ├── index.ts                      # 導出
    ├── ProjectSummaryFilters.tsx     # 篩選器
    ├── ProjectSummaryCategoryGrid.tsx # Category 匯總表格
    └── ProjectSummaryDetailGrid.tsx  # 明細表格
```

### 3.2 組件規格

#### SummaryTabs

```typescript
interface SummaryTabsProps {
  activeTab: 'om' | 'project';
  onTabChange: (tab: 'om' | 'project') => void;
}
```

#### ProjectSummaryFilters

```typescript
interface ProjectSummaryFiltersProps {
  filters: {
    financialYear: number;
    budgetCategoryIds: string[];
  };
  onFiltersChange: (filters: FilterState) => void;
  availableYears: number[];
  budgetCategoryOptions: BudgetCategory[];
  isLoading: boolean;
}
```

#### ProjectSummaryCategoryGrid

```typescript
interface CategorySummary {
  categoryId: string;
  categoryName: string;
  budgetTotal: number;
  projectCount: number;
}

interface ProjectSummaryCategoryGridProps {
  data: CategorySummary[];
  grandTotal: {
    budgetTotal: number;
    projectCount: number;
  };
  financialYear: number;
  isLoading: boolean;
}
```

#### ProjectSummaryDetailGrid

```typescript
interface OpCoGroup {
  opCoId: string;
  opCoName: string;
  categories: {
    categoryId: string;
    categoryName: string;
    projects: ProjectDetail[];
    subtotal: number;
  }[];
  subtotal: number;
}

interface ProjectSummaryDetailGridProps {
  data: OpCoGroup[];
  financialYear: number;
  isLoading: boolean;
}
```

---

## 4. 頁面結構變更

### 4.1 重構 OM Summary 頁面

```
apps/web/src/app/[locale]/om-summary/page.tsx

原結構:
├── OMSummaryFilters
├── OMSummaryCategoryGrid
└── OMSummaryDetailGrid

新結構:
├── SummaryTabs
│   ├── Tab: "OM Summary"
│   │   ├── OMSummaryFilters
│   │   ├── OMSummaryCategoryGrid
│   │   └── OMSummaryDetailGrid
│   │
│   └── Tab: "Project Summary"
│       ├── ProjectSummaryFilters
│       ├── ProjectSummaryCategoryGrid
│       └── ProjectSummaryDetailGrid
```

### 4.2 路由保持不變
- 頁面 URL 仍為 `/om-summary`
- Tab 狀態可通過 URL query param 保存：`/om-summary?tab=project`

---

## 5. I18N 翻譯鍵

### 5.1 新增翻譯命名空間

```json
// apps/web/src/messages/zh-TW.json
{
  "summary": {
    "tabs": {
      "omSummary": "O&M 費用總覽",
      "projectSummary": "專案總覽"
    }
  },
  "projectSummary": {
    "title": "專案總覽",
    "description": "查看各年度專案預算和分佈情況",
    "filters": {
      "financialYear": "財務年度",
      "budgetCategory": "預算類別",
      "selectAll": "全選",
      "clearAll": "清除",
      "reset": "重置篩選器"
    },
    "categoryGrid": {
      "category": "預算類別",
      "budgetTotal": "預算總額",
      "projectCount": "專案數量",
      "grandTotal": "總計"
    },
    "detailGrid": {
      "opCo": "營運公司",
      "category": "類別",
      "projectName": "專案名稱",
      "description": "描述",
      "budget": "預算",
      "subtotal": "小計"
    },
    "noData": "沒有符合條件的專案",
    "loading": "載入中..."
  },
  "project": {
    "form": {
      "projectCategory": {
        "label": "專案類別",
        "placeholder": "選擇專案類別"
      },
      "projectType": {
        "label": "專案或預算",
        "options": {
          "project": "Project",
          "budget": "Budget"
        }
      },
      "expenseType": {
        "label": "費用類型",
        "options": {
          "expense": "Expense",
          "capital": "Capital",
          "collection": "Collection"
        }
      },
      "chargeBackToOpCo": {
        "label": "是否向 OpCo 收費"
      },
      "chargeOutOpCos": {
        "label": "向哪些 OpCo 收費",
        "placeholder": "選擇 OpCo"
      },
      "chargeOutMethod": {
        "label": "收費方式",
        "placeholder": "說明如何向 OpCo 收費"
      },
      "probability": {
        "label": "機率",
        "options": {
          "high": "High",
          "medium": "Medium",
          "low": "Low"
        }
      },
      "team": {
        "label": "團隊",
        "placeholder": "輸入團隊名稱"
      },
      "personInCharge": {
        "label": "負責人 (PIC)",
        "placeholder": "輸入負責人姓名"
      }
    }
  }
}
```

---

## 6. 資料庫遷移計劃

### 6.1 遷移步驟

1. 新增 Project 欄位（所有新欄位設為可選或有預設值）
2. 新增 ProjectChargeOutOpCo 中間表
3. 更新 OperatingCompany 關係
4. 新增索引

### 6.2 遷移 SQL 預覽

```sql
-- 新增 Project 欄位
ALTER TABLE "Project" ADD COLUMN "projectCategory" TEXT;
ALTER TABLE "Project" ADD COLUMN "projectType" TEXT NOT NULL DEFAULT 'Project';
ALTER TABLE "Project" ADD COLUMN "expenseType" TEXT NOT NULL DEFAULT 'Expense';
ALTER TABLE "Project" ADD COLUMN "chargeBackToOpCo" BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE "Project" ADD COLUMN "chargeOutMethod" TEXT;
ALTER TABLE "Project" ADD COLUMN "probability" TEXT NOT NULL DEFAULT 'Medium';
ALTER TABLE "Project" ADD COLUMN "team" TEXT;
ALTER TABLE "Project" ADD COLUMN "personInCharge" TEXT;

-- 新增索引
CREATE INDEX "Project_projectCategory_idx" ON "Project"("projectCategory");
CREATE INDEX "Project_projectType_idx" ON "Project"("projectType");
CREATE INDEX "Project_expenseType_idx" ON "Project"("expenseType");
CREATE INDEX "Project_chargeBackToOpCo_idx" ON "Project"("chargeBackToOpCo");
CREATE INDEX "Project_probability_idx" ON "Project"("probability");
CREATE INDEX "Project_team_idx" ON "Project"("team");

-- 新增中間表
CREATE TABLE "ProjectChargeOutOpCo" (
    "id" TEXT NOT NULL,
    "projectId" TEXT NOT NULL,
    "opCoId" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "ProjectChargeOutOpCo_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "ProjectChargeOutOpCo_projectId_opCoId_key" ON "ProjectChargeOutOpCo"("projectId", "opCoId");
CREATE INDEX "ProjectChargeOutOpCo_projectId_idx" ON "ProjectChargeOutOpCo"("projectId");
CREATE INDEX "ProjectChargeOutOpCo_opCoId_idx" ON "ProjectChargeOutOpCo"("opCoId");

ALTER TABLE "ProjectChargeOutOpCo" ADD CONSTRAINT "ProjectChargeOutOpCo_projectId_fkey"
  FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "ProjectChargeOutOpCo" ADD CONSTRAINT "ProjectChargeOutOpCo_opCoId_fkey"
  FOREIGN KEY ("opCoId") REFERENCES "OperatingCompany"("id") ON DELETE CASCADE ON UPDATE CASCADE;
```

---

## 7. 技術風險

### 7.1 已識別風險

| 風險 | 嚴重度 | 緩解措施 |
|------|--------|----------|
| 數據遷移影響現有功能 | 中 | 所有新欄位設預設值，分階段遷移 |
| 多對多關係複雜度 | 低 | 使用 Prisma 標準模式，有文檔支援 |
| API 性能（大量 Project） | 中 | 添加適當索引，分頁查詢 |
| Azure 環境 Schema 同步 | 中 | 使用 Health API 診斷工具驗證 |

### 7.2 依賴項

- FEAT-003: OM Summary Page（需要參考其結構）
- FEAT-004: Operating Company Management（OpCo 數據）
- 現有 Project CRUD 功能

---

**最後更新**: 2025-12-05
**作者**: AI Assistant
