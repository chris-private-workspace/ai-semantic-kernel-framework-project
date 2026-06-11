# FEAT-005: OM Expense Category Management - 實施計劃

> **建立日期**: 2025-12-01
> **狀態**: 🚧 開發中

## 1. 開發階段

### Phase 1: 後端開發 (Prisma + API)

| 任務 | 描述 | 狀態 |
|------|------|------|
| 1.1 | 新增 OMExpenseCategory Model | ⏳ |
| 1.2 | 修改 OMExpense Model (新增 categoryId) | ⏳ |
| 1.3 | 執行資料庫遷移 | ⏳ |
| 1.4 | 建立 omExpenseCategory Router | ⏳ |
| 1.5 | 註冊到 root.ts | ⏳ |
| 1.6 | 更新 Seed Data | ⏳ |

### Phase 2: 前端開發 (Components + Pages)

| 任務 | 描述 | 狀態 |
|------|------|------|
| 2.1 | 建立 OMExpenseCategoryForm 組件 | ⏳ |
| 2.2 | 建立 OMExpenseCategoryActions 組件 | ⏳ |
| 2.3 | 建立列表頁 page.tsx | ⏳ |
| 2.4 | 建立新增頁 new/page.tsx | ⏳ |
| 2.5 | 建立編輯頁 [id]/edit/page.tsx | ⏳ |
| 2.6 | 修改 OMExpenseForm (類別下拉選單) | ⏳ |

### Phase 3: I18N + 導航

| 任務 | 描述 | 狀態 |
|------|------|------|
| 3.1 | 新增 zh-TW.json 翻譯 | ⏳ |
| 3.2 | 新增 en.json 翻譯 | ⏳ |
| 3.3 | 更新 Sidebar 導航 | ⏳ |
| 3.4 | 執行 i18n 驗證 | ⏳ |

### Phase 4: 整合測試

| 任務 | 描述 | 狀態 |
|------|------|------|
| 4.1 | TypeScript 檢查 | ⏳ |
| 4.2 | ESLint 檢查 | ⏳ |
| 4.3 | 手動功能測試 | ⏳ |

## 2. 任務分解

### 2.1 Prisma Schema 變更

```prisma
// 新增 Model
model OMExpenseCategory {
  id          String   @id @default(uuid())
  code        String   @unique
  name        String
  description String?
  sortOrder   Int      @default(0)
  isActive    Boolean  @default(true)
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
  omExpenses  OMExpense[]

  @@index([code])
  @@index([isActive])
}

// 修改 OMExpense
model OMExpense {
  // 新增
  categoryId String?
  expenseCategory OMExpenseCategory? @relation(fields: [categoryId], references: [id])
  // 保留舊的 category 欄位直到遷移完成
}
```

### 2.2 API Router 結構

```typescript
// packages/api/src/routers/omExpenseCategory.ts
export const omExpenseCategoryRouter = createTRPCRouter({
  getAll: protectedProcedure.input(...).query(...),
  getById: protectedProcedure.input(...).query(...),
  getActive: protectedProcedure.query(...),
  create: protectedProcedure.input(...).mutation(...),
  update: protectedProcedure.input(...).mutation(...),
  delete: protectedProcedure.input(...).mutation(...),
  toggleStatus: protectedProcedure.input(...).mutation(...),
});
```

### 2.3 前端頁面結構

```
om-expense-categories/
├── page.tsx          # 列表：表格 + 搜尋 + 過濾
├── new/page.tsx      # 新增：表單
└── [id]/edit/page.tsx # 編輯：表單 + 預載資料
```

## 3. 依賴關係

```
Phase 1 (後端)
    ↓
Phase 2 (前端) ← 依賴 API
    ↓
Phase 3 (I18N) ← 依賴頁面結構
    ↓
Phase 4 (測試) ← 依賴所有前置任務
```

## 4. 風險緩解

### 4.1 資料遷移風險
- **策略**: 先新增 categoryId 為可選欄位
- **後續**: 確認所有資料已遷移後再移除舊欄位

### 4.2 向後兼容性
- **策略**: 保留舊 category String 欄位
- **過渡期**: 同時支援新舊欄位直到遷移完成

## 5. 驗收檢查

- [ ] OMExpenseCategory CRUD 功能正常
- [ ] OMExpense 表單顯示類別下拉選單
- [ ] 側邊欄導航項目正確
- [ ] 中英文翻譯完整
- [ ] TypeScript 無新增錯誤
- [ ] ESLint 無新增錯誤
