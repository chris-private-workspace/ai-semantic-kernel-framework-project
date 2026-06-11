# FEAT-005: OM Expense Category Management - 技術設計

> **建立日期**: 2025-12-01
> **狀態**: 🚧 開發中

## 1. 數據模型設計

### 1.1 新增 OMExpenseCategory Model

```prisma
model OMExpenseCategory {
  id          String   @id @default(uuid())
  code        String   @unique  // 類別代碼（如 MAINT, LICENSE）
  name        String            // 類別名稱
  description String?           // 描述（選填）
  sortOrder   Int      @default(0)  // 排序順序
  isActive    Boolean  @default(true)  // 是否啟用
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  // 關聯
  omExpenses  OMExpense[]

  @@index([code])
  @@index([isActive])
}
```

### 1.2 修改 OMExpense Model

**現有結構：**
```prisma
model OMExpense {
  category String  // 自由文字
  // ...
}
```

**新結構：**
```prisma
model OMExpense {
  // 移除: category String
  categoryId String  // 新增外鍵
  category   OMExpenseCategory @relation(fields: [categoryId], references: [id])
  // ...
}
```

### 1.3 資料遷移策略

1. **新增 OMExpenseCategory Model**
2. **新增 categoryId 欄位（可選）** - 暫時允許 null
3. **執行資料遷移腳本** - 根據現有 category 字串建立/關聯類別
4. **移除舊 category 欄位，categoryId 改為必填**

## 2. API 設計

### 2.1 omExpenseCategory Router

| Procedure | Method | 輸入 | 輸出 | 權限 |
|-----------|--------|------|------|------|
| `getAll` | Query | `{ page?, limit?, search?, isActive? }` | `{ categories, total, page, totalPages }` | Protected |
| `getById` | Query | `{ id }` | `OMExpenseCategory` | Protected |
| `getActive` | Query | - | `OMExpenseCategory[]` | Protected |
| `create` | Mutation | `{ code, name, description?, sortOrder? }` | `OMExpenseCategory` | Admin |
| `update` | Mutation | `{ id, code?, name?, description?, sortOrder?, isActive? }` | `OMExpenseCategory` | Admin |
| `delete` | Mutation | `{ id }` | `{ success }` | Admin |
| `toggleStatus` | Mutation | `{ id }` | `OMExpenseCategory` | Admin |

### 2.2 Zod Schemas

```typescript
// 輸入驗證
const createCategoryInput = z.object({
  code: z.string().min(1).max(20).regex(/^[A-Z0-9_]+$/),
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional(),
  sortOrder: z.number().int().min(0).default(0),
});

const updateCategoryInput = z.object({
  id: z.string().uuid(),
  code: z.string().min(1).max(20).regex(/^[A-Z0-9_]+$/).optional(),
  name: z.string().min(1).max(100).optional(),
  description: z.string().max(500).optional(),
  sortOrder: z.number().int().min(0).optional(),
  isActive: z.boolean().optional(),
});
```

## 3. 前端設計

### 3.1 頁面結構

```
apps/web/src/app/[locale]/
└── om-expense-categories/
    ├── page.tsx           # 列表頁
    ├── new/
    │   └── page.tsx       # 新增頁
    └── [id]/
        └── edit/
            └── page.tsx   # 編輯頁
```

### 3.2 組件結構

```
apps/web/src/components/
└── om-expense-category/
    ├── OMExpenseCategoryForm.tsx    # 表單組件
    ├── OMExpenseCategoryActions.tsx # 操作按鈕
    └── index.ts                     # 統一導出
```

### 3.3 修改現有組件

**OMExpenseForm.tsx:**
- 將 category 文字輸入改為下拉選單
- 呼叫 `omExpenseCategory.getActive` 取得選項
- 必填驗證

## 4. I18N 設計

### 4.1 新增 Namespace: `omExpenseCategories`

```json
{
  "omExpenseCategories": {
    "title": "OM 費用類別",
    "description": "管理 O&M 費用的分類",
    "table": {
      "code": "類別代碼",
      "name": "類別名稱",
      "description": "描述",
      "status": "狀態",
      "omExpenses": "關聯費用數",
      "actions": "操作"
    },
    "form": { ... },
    "actions": { ... },
    "messages": { ... }
  }
}
```

## 5. 側邊欄導航

在 System 區塊添加「OM 費用類別」導航項目：
- **位置**: System 區塊，Users 之後
- **圖標**: `Tags` (lucide-react)
- **路徑**: `/om-expense-categories`

## 6. 依賴關係

```
OMExpenseCategory (新)
       ↓
   OMExpense (修改)
       ↓
  OMExpenseForm (修改)
```

## 7. 風險評估

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 現有 OMExpense 資料需遷移 | Medium | 分階段遷移，先允許 null |
| 類別刪除影響關聯資料 | High | 禁止刪除有關聯的類別 |
| API 向後兼容性 | Medium | 保留舊欄位直到前端完全遷移 |
