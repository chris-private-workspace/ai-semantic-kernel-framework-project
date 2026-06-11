# Phase A 交接文檔 - Module 1 (BudgetPool) 前端實施

> **創建時間**: 2025-10-26 21:50
> **目的**: 為新的 Claude Code 會話提供完整的上下文
> **當前進度**: Phase A 準備完成，即將開始前端開發

---

## 📋 快速摘要

### 當前狀態
- ✅ **階段 1**: 數據庫 Schema 實施 - **100% 完成**
- ✅ **階段 2.1**: BudgetPool API - **100% 完成**
- 🔄 **階段 3.1**: BudgetPool 前端 - **0% 完成** ← **當前任務**

### Phase A 目標
讓 Module 1 (BudgetPool) 完全可用 - 從後端到前端完整打通

---

## 🎯 立即要做的事

### 核心任務（按順序）

#### 1️⃣ 重寫 BudgetPoolForm.tsx（優先級：最高）
**檔案**: `apps/web/src/components/budget-pool/BudgetPoolForm.tsx`

**當前問題**:
- ❌ 仍使用舊的 `totalAmount` 欄位
- ❌ 不支持 `categories` 陣列
- ❌ 無法創建多個預算類別

**需要實作**:
```typescript
// 新的狀態結構
const [categories, setCategories] = useState<CategoryInput[]>([
  { categoryName: '', categoryCode: '', totalAmount: 0, description: '', sortOrder: 0 }
]);

// Categories CRUD 操作
- 新增類別行
- 刪除類別行
- 排序類別
- 驗證類別（至少1個，名稱不重複）
```

**API 已準備好**:
- ✅ `budgetPool.create` - 支持 nested create categories
- ✅ `budgetPool.update` - 使用 transaction 更新 categories
- ✅ Zod 驗證: `budgetCategorySchema`

---

#### 2️⃣ 創建 CategoryFormRow.tsx
**新檔案**: `apps/web/src/components/budget-pool/CategoryFormRow.tsx`

**功能需求**:
- 分類名稱輸入（必填）
- 分類代碼輸入（選填）
- 預算金額輸入（必填，≥0）
- 說明輸入（選填）
- 排序輸入（選填）
- 刪除按鈕（第一行不可刪除）

**UI 組件**:
使用 shadcn/ui 組件：
- `Input` - 文字輸入
- `Button` - 刪除按鈕
- `Label` - 欄位標籤
- 使用 Tailwind CSS 排版

---

#### 3️⃣ 更新列表頁
**檔案**: `apps/web/src/app/budget-pools/page.tsx`

**需要顯示**:
- 預算池名稱
- 財政年度
- **總預算**（computedTotalAmount - 來自 categories 總和）
- **已使用**（computedUsedAmount）
- **使用率**
- **類別數量**（例如："3個類別"）

---

#### 4️⃣ 更新詳情頁
**檔案**: `apps/web/src/app/budget-pools/[id]/page.tsx`

**需要顯示**:
- 預算池基本資訊
- **Categories 表格**（完整展示）:
  - 類別名稱
  - 類別代碼
  - 總預算
  - 已使用
  - 使用率
  - 關聯專案數
  - 排序
- 關聯專案列表

---

#### 5️⃣ 完整測試
- [ ] 創建預算池（含2-3個類別）
- [ ] 編輯預算池（新增/修改/刪除類別）
- [ ] 列表頁正確顯示 categories 摘要
- [ ] 詳情頁完整展示 categories
- [ ] 計算邏輯正確（總預算 = categories 總和）

---

## 📚 關鍵技術信息

### 1. API 端點（已完成）

**Router**: `packages/api/src/routers/budgetPool.ts`

```typescript
// 創建（支持 nested create）
budgetPool.create.useMutation({
  input: {
    name: string,
    financialYear: number,
    description?: string,
    categories: [
      { categoryName, categoryCode?, totalAmount, description?, sortOrder }
    ]
  }
});

// 更新（使用 transaction）
budgetPool.update.useMutation({
  input: {
    id: string,
    name?: string,
    description?: string,
    categories?: [
      { id?, categoryName, categoryCode?, totalAmount, ... }
      // 有 id = 更新現有，無 id = 新增
    ]
  }
});

// 查詢（含 categories）
budgetPool.getById.useQuery({ id: string });
// 返回：{ ..., categories: [...], computedTotalAmount, computedUsedAmount }
```

### 2. Prisma Schema（已完成）

**檔案**: `packages/db/prisma/schema.prisma`

```prisma
model BudgetPool {
  id            String   @id @default(uuid())
  name          String
  description   String?
  financialYear Int
  totalAmount   Float    // DEPRECATED - 向後兼容
  usedAmount    Float    // DEPRECATED - 向後兼容

  categories    BudgetCategory[]  // 新增關聯
  projects      Project[]
}

model BudgetCategory {
  id           String     @id @default(uuid())
  budgetPoolId String
  categoryName String
  categoryCode String?
  description  String?
  totalAmount  Float
  usedAmount   Float      @default(0)
  sortOrder    Int        @default(0)
  isActive     Boolean    @default(true)

  budgetPool   BudgetPool @relation(...)
  projects     Project[]
  expenses     Expense[]

  @@unique([budgetPoolId, categoryName])
}
```

### 3. TypeScript 類型

```typescript
// 從 Zod schema 推導
import { z } from "zod";

export const budgetCategorySchema = z.object({
  id: z.string().uuid().optional(),
  categoryName: z.string().min(1, 'Category name is required'),
  categoryCode: z.string().optional(),
  totalAmount: z.number().min(0, 'Amount must be non-negative'),
  description: z.string().optional(),
  sortOrder: z.number().int().default(0),
  isActive: z.boolean().default(true),
});

type CategoryInput = z.infer<typeof budgetCategorySchema>;
```

---

## ⚠️ 重要注意事項

### 1. Migration 文件未創建（技術限制）
**問題**: `prisma migrate dev` 需要交互式終端，Claude Code 無法執行

**當前狀態**:
- ✅ Schema 已透過 `db push` 應用到資料庫
- ✅ 資料庫結構正確
- ⚠️ 沒有 migration 歷史記錄

**手動解決方案**（稍後執行）:
```powershell
# 在 PowerShell 執行
$env:DATABASE_URL="postgresql://postgres:localdev123@localhost:5434/itpm_dev"
cd packages\db
npx prisma migrate dev --name add_budget_categories_and_enhancements --create-only
```

**策略**: 先完成前端開發，Migration 稍後補充（不影響開發）

---

### 2. 向後兼容性
BudgetPool 的 `totalAmount` 和 `usedAmount` 標記為 **DEPRECATED**，但仍保留：
- ✅ API 自動計算 `computedTotalAmount`（從 categories 總和）
- ✅ 前端應該使用 `computedTotalAmount` 而非 `totalAmount`
- ⚠️ 舊資料可能沒有 categories，需要處理邊緣情況

---

### 3. 設計系統組件
使用 shadcn/ui + Radix UI：

**可用組件** (26個):
- `Button`, `Input`, `Label`, `Card`
- `Table`, `Form`, `Dialog`, `Alert`
- `Accordion`, `Badge`, `Checkbox`, `Select`
- 完整列表: `apps/web/src/components/ui/`

**工具函數**:
- `cn()` from `lib/utils.ts` - className 合併
- `useTheme()` - 主題管理（Light/Dark/System）

---

## 📂 關鍵檔案位置

### 需要修改
```
apps/web/src/
├── components/budget-pool/
│   ├── BudgetPoolForm.tsx          ← 重寫（優先）
│   └── CategoryFormRow.tsx         ← 新增
├── app/budget-pools/
│   ├── page.tsx                    ← 更新列表
│   └── [id]/page.tsx               ← 更新詳情
```

### 已完成（參考）
```
packages/
├── api/src/routers/
│   └── budgetPool.ts               ✅ API 完成
├── db/prisma/
│   └── schema.prisma               ✅ Schema 完成
```

### 進度追蹤
```
claudedocs/
├── COMPLETE-IMPLEMENTATION-PROGRESS.md   ← 更新進度
└── REQUIREMENT-GAP-ANALYSIS.md           ← 需求參考

DEVELOPMENT-LOG.md                        ← 記錄開發
```

---

## 🚀 啟動新會話的步驟

### 1. 載入上下文（推薦順序）
```bash
# 第一優先
@PHASE-A-HANDOFF.md                          # 本文檔

# 第二優先
@claudedocs/COMPLETE-IMPLEMENTATION-PROGRESS.md  # 進度追蹤
@DEVELOPMENT-LOG.md                          # 開發記錄（前50行）

# 第三優先（需要時）
@packages/api/src/routers/budgetPool.ts      # API 參考
@packages/db/prisma/schema.prisma            # Schema 參考
@apps/web/src/components/budget-pool/BudgetPoolForm.tsx  # 待重寫檔案
```

### 2. 確認環境
```bash
# 檢查開發服務器是否運行
pnpm dev

# 確認資料庫連接
pnpm db:studio
```

### 3. 開始開發
直接從 Task 1 開始：重寫 BudgetPoolForm.tsx

---

## 📊 進度檢查清單

### Phase A 任務（剩餘 6/7 項）
- [x] 專案維護檢查清單（5/5）
- [ ] 重寫 BudgetPoolForm.tsx
- [ ] 創建 CategoryFormRow.tsx
- [ ] 更新列表頁
- [ ] 更新詳情頁
- [ ] 完整測試
- [ ] 更新進度文檔

### 完成標準
- ✅ 可以創建含多個類別的預算池
- ✅ 可以編輯類別（新增/修改/刪除/排序）
- ✅ 列表頁正確顯示類別摘要
- ✅ 詳情頁完整展示類別
- ✅ 統計數據正確計算
- ✅ 所有操作經過測試

---

## 🔄 下一步（Phase A 完成後）

### 選項 A: 繼續階段 2（推薦）
- Module 2: Project API（使用新的 budgetCategoryId）
- Module 3: BudgetProposal API（新增檔案上傳）
- Module 4-8: 其他模塊

### 選項 B: 優化 Module 1
- 根據測試反饋調整
- 再決定其他模塊

### 選項 C: 暫停評估
- 重新評估其他模塊必要性
- 可能調整計劃

---

## 📞 聯絡資訊

**Git 狀態**:
- 最新提交: `4953dbd` - "docs: 文檔重組與 COMPLETE-IMPLEMENTATION-PLAN 進度追蹤系統"
- 分支: `main`
- 狀態: 已推送到 origin/main

**項目狀態**:
- MVP: ✅ 100% 完成（Epic 1-8）
- Post-MVP: ✅ 100% 完成
- COMPLETE-IMPLEMENTATION-PLAN: 🔄 22% 完成

---

**準備好開始了嗎？**

直接從重寫 BudgetPoolForm.tsx 開始，使用 `@packages/api/src/routers/budgetPool.ts` 作為 API 參考！

**祝開發順利！** 🚀
