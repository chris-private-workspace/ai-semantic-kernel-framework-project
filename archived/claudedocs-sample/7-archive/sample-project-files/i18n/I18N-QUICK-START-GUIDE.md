# i18n 遷移快速入門指南

> **目標**: 幫助您高效完成剩餘 36 個文件的 i18n 遷移
> **預計時間**: 8-12 小時 (可分多次完成)
> **當前進度**: 37% (22/59 文件已完成)

---

## 📋 快速開始

### 1. 使用遷移輔助工具

我們已創建了自動化分析工具,幫助您識別需要遷移的內容:

```bash
# 分析單個文件
node scripts/i18n-migration-helper.js apps/web/src/app/[locale]/proposals/page.tsx

# 輸出會顯示:
# - 重複 import (需修復)
# - 硬編碼中文位置
# - 已使用的翻譯 hooks
# - 建議添加的 hooks
```

### 2. 遷移步驟 (每個文件 10-15 分鐘)

#### Step 1: 檢查文件狀態
```bash
node scripts/i18n-migration-helper.js <file-path>
```

#### Step 2: 修復重複 import (如果有)
```typescript
// 錯誤 ❌
import { useTranslations } from 'next-intl';
import { useRouter } from "@/i18n/routing";
import { useTranslations } from 'next-intl';  // 重複!

// 正確 ✅
import { useTranslations } from 'next-intl';
import { useRouter } from "@/i18n/routing";
```

#### Step 3: 添加翻譯 hooks
```typescript
// 在組件頂部添加
const t = useTranslations('namespace');  // 主要 namespace
const tCommon = useTranslations('common');  // 通用文字
const tValidation = useTranslations('validation');  // 驗證訊息
const tToast = useTranslations('toast');  // Toast 訊息
```

#### Step 4: 替換硬編碼文字
```typescript
// Before ❌
<h1>專案列表</h1>
<button>新增</button>

// After ✅
<h1>{t('list.title')}</h1>
<button>{tCommon('actions.create')}</button>
```

#### Step 5: 驗證結果
```bash
# TypeScript 類型檢查
pnpm typecheck

# 啟動開發服務器
pnpm dev

# 測試兩種語言
# http://localhost:3006/zh-TW/... (繁體中文)
# http://localhost:3006/en/... (英文)
```

---

## 🎯 優先遷移順序

### 第一階段: 完成 Batch 2 (11 個文件,約 4 小時)

#### 1. Projects 模組剩餘 (2 個文件,1 小時)
```bash
# 1.1 修復 quotes/page.tsx 重複 import
# 1.2 完成 projects/[id]/page.tsx 遷移
# 1.3 完成 projects/[id]/quotes/page.tsx 遷移
```

**關鍵文件**:
- `apps/web/src/app/[locale]/projects/[id]/page.tsx` - 詳情頁
- `apps/web/src/app/[locale]/projects/[id]/quotes/page.tsx` - 報價頁

**Namespace**: `projects.detail`, `projects.quotes`

---

#### 2. Proposals 模組 (6 個文件,2 小時)
```bash
# 2.1 proposals/page.tsx (已修復 import)
# 2.2 proposals/[id]/page.tsx
# 2.3 proposals/new/page.tsx
# 2.4 proposals/[id]/edit/page.tsx
# 2.5 components/proposal/BudgetProposalForm.tsx
# 2.6 components/proposal/ProposalActions.tsx
```

**Namespace**: `proposals.list`, `proposals.detail`, `proposals.form`, `proposals.actions`

---

#### 3. BudgetPools 模組 (5 個文件,1.5 小時)
```bash
# 3.1 budget-pools/page.tsx
# 3.2 budget-pools/[id]/page.tsx
# 3.3 budget-pools/new/page.tsx
# 3.4 budget-pools/[id]/edit/page.tsx
# 3.5 components/budget-pool/BudgetPoolForm.tsx
```

**Namespace**: `budgetPools.list`, `budgetPools.detail`, `budgetPools.form`

---

### 第二階段: 完成 Batch 3 (23 個文件,約 8 小時)

可分批次完成,每批 5-8 個文件:

#### Batch 3.1: Vendors + Quotes (7 個文件,2.5 小時)
- `vendors/page.tsx`
- `vendors/[id]/page.tsx`
- `vendors/new/page.tsx`
- `components/vendor/VendorForm.tsx`
- `quotes/page.tsx`
- `quotes/new/page.tsx`
- `components/quote/QuoteUploadForm.tsx`

#### Batch 3.2: PurchaseOrders + Expenses (10 個文件,3.5 小時)
- `purchase-orders/page.tsx`
- `purchase-orders/[id]/page.tsx`
- `purchase-orders/new/page.tsx`
- `components/purchase-order/PurchaseOrderForm.tsx`
- `components/purchase-order/PurchaseOrderActions.tsx`
- `expenses/page.tsx`
- `expenses/[id]/page.tsx`
- `expenses/new/page.tsx`
- `components/expense/ExpenseForm.tsx`
- `components/expense/ExpenseActions.tsx`

#### Batch 3.3: 其他模組 (6 個文件,2 小時)
- `notifications/page.tsx`
- `settings/page.tsx`
- `components/notification/NotificationBell.tsx`
- `components/notification/NotificationDropdown.tsx` (已完成)
- `components/theme/ThemeToggle.tsx`
- 其他輔助組件

---

## 📚 常用翻譯 Key 參考

### 通用操作 (common.actions)
```typescript
tCommon('actions.save')          // 儲存
tCommon('actions.cancel')        // 取消
tCommon('actions.delete')        // 刪除
tCommon('actions.edit')          // 編輯
tCommon('actions.create')        // 新增
tCommon('actions.submit')        // 提交
tCommon('actions.search')        // 搜尋
tCommon('actions.filter')        // 篩選
tCommon('actions.export')        // 匯出
tCommon('actions.back')          // 返回
tCommon('actions.view')          // 查看
tCommon('actions.approve')       // 批准
tCommon('actions.reject')        // 駁回
```

### 狀態標籤 (common.status)
```typescript
tStatus('draft')                 // 草稿
tStatus('pending')               // 待審批
tStatus('pendingApproval')       // 待審批
tStatus('approved')              // 已批准
tStatus('rejected')              // 已駁回
tStatus('moreInfoRequired')      // 需要更多資訊
tStatus('completed')             // 已完成
tStatus('paid')                  // 已支付
tStatus('active')                // 進行中
```

### 驗證訊息 (validation)
```typescript
tValidation('required')          // 此欄位為必填
tValidation('email')             // 請輸入有效的電子郵件地址
tValidation('minLength')         // 至少需要 {min} 個字元
tValidation('maxLength')         // 不能超過 {max} 個字元
tValidation('invalidAmount')     // 請輸入有效的金額
tValidation('endDateBeforeStart') // 結束日期必須晚於開始日期
```

### Toast 訊息 (toast)
```typescript
// 成功訊息
tToast('success.title')          // 成功
tToast('success.created', { entity: t('entityName') })  // {entity} 創建成功！
tToast('success.updated', { entity: t('entityName') })  // {entity} 更新成功！
tToast('success.deleted', { entity: t('entityName') })  // {entity} 刪除成功！
tToast('success.approved', { entity: t('entityName') }) // {entity} 批准成功！

// 錯誤訊息
tToast('error.title')            // 錯誤
tToast('error.general')          // 操作失敗，請稍後再試
tToast('error.network')          // 網路錯誤，請檢查您的連線
tToast('error.unauthorized')     // 您沒有權限執行此操作
tToast('error.validation')       // 請檢查輸入的資料
```

---

## 🛠️ 常見問題解決

### Q1: 如何處理動態內容?
```typescript
// 使用變數插值
{t('budget.summary', {
  total: formatCurrency(pool.totalAmount),
  used: formatCurrency(pool.usedAmount),
  remaining: formatCurrency(pool.totalAmount - pool.usedAmount)
})}

// 翻譯文件中對應:
{
  "budget.summary": "總預算：{total}，已使用：{used}，剩餘：{remaining}"
}
```

### Q2: 如何處理複數形式?
```typescript
// 使用 count 參數
{t('projects.count', { count: projects.length })}

// 翻譯文件中對應:
{
  "projects.count": {
    "zero": "無專案",
    "one": "{count} 個專案",
    "other": "{count} 個專案"
  }
}
```

### Q3: 如何處理 HTML 內容?
```typescript
// 使用 dangerouslySetInnerHTML
<p
  dangerouslySetInnerHTML={{
    __html: t.raw('suggestion', { project: 'Q4 雲端服務' })
  }}
/>

// 翻譯文件中對應:
{
  "suggestion": "系統分析顯示：<strong>{project}</strong> 預算使用率偏低"
}
```

### Q4: 如何格式化日期和貨幣?
```typescript
import { useFormatter } from 'next-intl';

const format = useFormatter();

// 貨幣
{format.number(amount, { style: 'currency', currency: 'MYR' })}
// 輸出: RM 12,345.67

// 日期
{format.dateTime(date, { year: 'numeric', month: 'long', day: 'numeric' })}
// zh-TW: 2024年11月3日
// en: November 3, 2024
```

---

## ✅ 遷移檢查清單

每完成一個文件,請檢查:

### 編譯檢查
- [ ] 無 TypeScript 類型錯誤 (`pnpm typecheck`)
- [ ] 無 ESLint 警告 (`pnpm lint`)
- [ ] 無重複 import (使用 `i18n-migration-helper.js`)
- [ ] 所有 import 路徑正確 (`@/i18n/routing`)

### 功能檢查
- [ ] zh-TW 語言顯示正確 (`http://localhost:3006/zh-TW/...`)
- [ ] en 語言顯示正確 (`http://localhost:3006/en/...`)
- [ ] 表單提交功能正常
- [ ] Toast 訊息顯示正確
- [ ] 狀態標籤翻譯正確
- [ ] 驗證錯誤訊息翻譯正確

### UI 檢查
- [ ] 無 UI 破損或布局錯亂
- [ ] 不同語言的文字長度適配
- [ ] 按鈕和連結可點擊
- [ ] 圖標和樣式保持一致

---

## 📊 進度追蹤

建議每完成一批文件後更新 `I18N-MIGRATION-STATUS.md`:

```markdown
### Batch 2: Proposals 模組 (6/6 完成 = 100%)

#### 已完成 (6 個)
- ✅ `app/[locale]/proposals/page.tsx` - 列表頁 (2025-11-03 完成)
- ✅ `app/[locale]/proposals/[id]/page.tsx` - 詳情頁 (2025-11-03 完成)
- ✅ `app/[locale]/proposals/new/page.tsx` - 新增頁 (2025-11-03 完成)
- ✅ `app/[locale]/proposals/[id]/edit/page.tsx` - 編輯頁 (2025-11-03 完成)
- ✅ `components/proposal/BudgetProposalForm.tsx` - 表單組件 (2025-11-03 完成)
- ✅ `components/proposal/ProposalActions.tsx` - 操作按鈕 (2025-11-03 完成)
```

---

## 🎓 學習資源

### 官方文檔
- **next-intl**: https://next-intl-docs.vercel.app/
- **Next.js i18n**: https://nextjs.org/docs/app/building-your-application/routing/internationalization

### 項目內部文檔
- `STAGE-3-4-IMPLEMENTATION-PLAN.md` - 完整實施計劃
- `I18N-MIGRATION-STATUS.md` - 當前狀態追蹤
- `I18N-ISSUES-LOG.md` - 問題記錄和解決方案

### 翻譯文件
- `apps/web/src/messages/zh-TW.json` - 繁體中文翻譯 (1015 行)
- `apps/web/src/messages/en.json` - 英文翻譯 (1014 行)

---

## 💪 加油!

您已經完成了 **37% 的工作** (22/59 文件)!

核心的 Layout、Dashboard 和 Auth 組件已經全部完成,這是最重要的基礎。剩下的都是業務模組頁面,遵循相同的遷移模式即可。

**預估剩餘時間**:
- Batch 2 完成: 約 4 小時
- Batch 3 完成: 約 8 小時
- **總計**: 約 12 小時 (可分 2-3 天完成)

---

**維護者**: Development Team + AI Assistant
**最後更新**: 2025-11-03
**版本**: 1.0
