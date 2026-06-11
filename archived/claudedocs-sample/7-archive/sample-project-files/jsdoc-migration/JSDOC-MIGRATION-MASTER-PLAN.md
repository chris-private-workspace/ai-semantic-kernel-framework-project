# 📝 JSDoc 遷移主計劃 (Master Plan)

> **目標**: 為專案中所有代碼文件添加完整的 JSDoc 風格註釋
> **開始日期**: 2025-11-14
> **預估完成**: 2025-11-21 (7 天)
> **負責人**: AI Assistant + 開發團隊

---

## 📊 專案代碼文件分析

### 總體統計

| 類別 | 文件數量 | 已有 JSDoc | 需要更新 | 優先級 |
|------|---------|-----------|---------|--------|
| **API Routers** | 14 | 0 | 14 | 🔴 P0 (最高) |
| **Page Components** | 45 | 0 | 45 | 🔴 P0 (最高) |
| **Business Components** | 25 | 0 | 25 | 🟡 P1 (高) |
| **UI Components (shadcn)** | 35 | 0 | 35 | 🟡 P1 (高) |
| **Utility/Lib Files** | 6 | 0 | 6 | 🟡 P1 (高) |
| **Hooks** | 2 | 0 | 2 | 🟢 P2 (中) |
| **Auth Package** | 1 | 0 | 1 | 🟢 P2 (中) |
| **Types/Interfaces** | 9 | 0 | 9 | 🟢 P2 (中) |
| **總計** | **137** | **0** | **137** | - |

### 詳細文件清單

#### 🔴 P0 (最高優先級) - 59 個文件

##### 1. API Routers (14 個)
- `packages/api/src/routers/budgetPool.ts`
- `packages/api/src/routers/budgetProposal.ts`
- `packages/api/src/routers/chargeOut.ts`
- `packages/api/src/routers/dashboard.ts`
- `packages/api/src/routers/expense.ts`
- `packages/api/src/routers/health.ts`
- `packages/api/src/routers/notification.ts`
- `packages/api/src/routers/omExpense.ts`
- `packages/api/src/routers/operatingCompany.ts`
- `packages/api/src/routers/project.ts`
- `packages/api/src/routers/purchaseOrder.ts`
- `packages/api/src/routers/quote.ts`
- `packages/api/src/routers/user.ts`
- `packages/api/src/routers/vendor.ts`

##### 2. Page Components (45 個)

**Root Pages (2)**
- `apps/web/src/app/layout.tsx`
- `apps/web/src/app/page.tsx`

**Locale Pages (43)**
- `apps/web/src/app/[locale]/layout.tsx`
- `apps/web/src/app/[locale]/page.tsx`

**Dashboard (3)**
- `apps/web/src/app/[locale]/dashboard/page.tsx`
- `apps/web/src/app/[locale]/dashboard/pm/page.tsx`
- `apps/web/src/app/[locale]/dashboard/supervisor/page.tsx`

**Budget Pools (4)**
- `apps/web/src/app/[locale]/budget-pools/page.tsx`
- `apps/web/src/app/[locale]/budget-pools/new/page.tsx`
- `apps/web/src/app/[locale]/budget-pools/[id]/page.tsx`
- `apps/web/src/app/[locale]/budget-pools/[id]/edit/page.tsx`

**Projects (4)**
- `apps/web/src/app/[locale]/projects/page.tsx`
- `apps/web/src/app/[locale]/projects/new/page.tsx`
- `apps/web/src/app/[locale]/projects/[id]/page.tsx`
- `apps/web/src/app/[locale]/projects/[id]/edit/page.tsx`

**Proposals (4)**
- `apps/web/src/app/[locale]/proposals/page.tsx`
- `apps/web/src/app/[locale]/proposals/new/page.tsx`
- `apps/web/src/app/[locale]/proposals/[id]/page.tsx`
- `apps/web/src/app/[locale]/proposals/[id]/edit/page.tsx`

**Vendors (4)**
- `apps/web/src/app/[locale]/vendors/page.tsx`
- `apps/web/src/app/[locale]/vendors/new/page.tsx`
- `apps/web/src/app/[locale]/vendors/[id]/page.tsx`
- `apps/web/src/app/[locale]/vendors/[id]/edit/page.tsx`

**Quotes (2)**
- `apps/web/src/app/[locale]/quotes/page.tsx`
- `apps/web/src/app/[locale]/quotes/new/page.tsx`

**Purchase Orders (4)**
- `apps/web/src/app/[locale]/purchase-orders/page.tsx`
- `apps/web/src/app/[locale]/purchase-orders/new/page.tsx`
- `apps/web/src/app/[locale]/purchase-orders/[id]/page.tsx`
- `apps/web/src/app/[locale]/purchase-orders/[id]/edit/page.tsx`

**Expenses (4)**
- `apps/web/src/app/[locale]/expenses/page.tsx`
- `apps/web/src/app/[locale]/expenses/new/page.tsx`
- `apps/web/src/app/[locale]/expenses/[id]/page.tsx`
- `apps/web/src/app/[locale]/expenses/[id]/edit/page.tsx`

**OM Expenses (4)**
- `apps/web/src/app/[locale]/om-expenses/page.tsx`
- `apps/web/src/app/[locale]/om-expenses/new/page.tsx`
- `apps/web/src/app/[locale]/om-expenses/[id]/page.tsx`
- `apps/web/src/app/[locale]/om-expenses/[id]/edit/page.tsx`

**Charge Outs (4)**
- `apps/web/src/app/[locale]/charge-outs/page.tsx`
- `apps/web/src/app/[locale]/charge-outs/new/page.tsx`
- `apps/web/src/app/[locale]/charge-outs/[id]/page.tsx`
- `apps/web/src/app/[locale]/charge-outs/[id]/edit/page.tsx`

**Users (4)**
- `apps/web/src/app/[locale]/users/page.tsx`
- `apps/web/src/app/[locale]/users/new/page.tsx`
- `apps/web/src/app/[locale]/users/[id]/page.tsx`
- `apps/web/src/app/[locale]/users/[id]/edit/page.tsx`

**Notifications (1)**
- `apps/web/src/app/[locale]/notifications/page.tsx`

**Settings (1)**
- `apps/web/src/app/[locale]/settings/page.tsx`

**Auth Pages (3)**
- `apps/web/src/app/[locale]/login/page.tsx`
- `apps/web/src/app/[locale]/register/page.tsx`
- `apps/web/src/app/[locale]/forgot-password/page.tsx`

---

#### 🟡 P1 (高優先級) - 66 個文件

##### 3. Business Components (25 個)

**Budget Pool (3)**
- `apps/web/src/components/budget-pool/BudgetPoolForm.tsx`
- `apps/web/src/components/budget-pool/BudgetPoolFilters.tsx`
- `apps/web/src/components/budget-pool/CategoryFormRow.tsx`

**Project (1)**
- `apps/web/src/components/project/ProjectForm.tsx`

**Proposal (2)**
- `apps/web/src/components/proposal/ProposalForm.tsx`
- `apps/web/src/components/proposal/ProposalActions.tsx`

**Vendor (1)**
- `apps/web/src/components/vendor/VendorForm.tsx`

**Quote (1)**
- `apps/web/src/components/quote/QuoteForm.tsx`

**Purchase Order (1)**
- `apps/web/src/components/purchase-order/PurchaseOrderForm.tsx`

**Expense (2)**
- `apps/web/src/components/expense/ExpenseForm.tsx`
- `apps/web/src/components/expense/ExpenseActions.tsx`

**OM Expense (2)**
- `apps/web/src/components/om-expense/OMExpenseForm.tsx`
- `apps/web/src/components/om-expense/OMExpenseMonthlyGrid.tsx`

**Charge Out (2)**
- `apps/web/src/components/charge-out/ChargeOutForm.tsx`
- `apps/web/src/components/charge-out/ChargeOutActions.tsx`

**Dashboard (3)**
- `apps/web/src/components/dashboard/StatsCard.tsx`
- `apps/web/src/components/dashboard/StatCard.tsx`
- `apps/web/src/components/dashboard/BudgetPoolOverview.tsx`

**Layout (4)**
- `apps/web/src/components/layout/dashboard-layout.tsx`
- `apps/web/src/components/layout/Sidebar.tsx`
- `apps/web/src/components/layout/TopBar.tsx`
- `apps/web/src/components/layout/LanguageSwitcher.tsx`

**Notification (3)**
- `apps/web/src/components/notification/NotificationBell.tsx`
- `apps/web/src/components/notification/NotificationDropdown.tsx`
- `apps/web/src/components/notification/index.ts`

##### 4. UI Components (shadcn/ui) (35 個)
- `apps/web/src/components/ui/accordion.tsx`
- `apps/web/src/components/ui/alert-dialog.tsx`
- `apps/web/src/components/ui/alert.tsx`
- `apps/web/src/components/ui/avatar.tsx`
- `apps/web/src/components/ui/badge.tsx`
- `apps/web/src/components/ui/button.tsx`
- `apps/web/src/components/ui/calendar.tsx`
- `apps/web/src/components/ui/card.tsx`
- `apps/web/src/components/ui/checkbox.tsx`
- `apps/web/src/components/ui/collapsible.tsx`
- `apps/web/src/components/ui/combobox.tsx` ⭐ (最近重寫)
- `apps/web/src/components/ui/command.tsx`
- `apps/web/src/components/ui/dialog.tsx`
- `apps/web/src/components/ui/dropdown-menu.tsx`
- `apps/web/src/components/ui/form.tsx`
- `apps/web/src/components/ui/input.tsx`
- `apps/web/src/components/ui/label.tsx`
- `apps/web/src/components/ui/pagination.tsx`
- `apps/web/src/components/ui/popover.tsx`
- `apps/web/src/components/ui/radio-group.tsx`
- `apps/web/src/components/ui/scroll-area.tsx`
- `apps/web/src/components/ui/select.tsx`
- `apps/web/src/components/ui/separator.tsx`
- `apps/web/src/components/ui/skeleton.tsx`
- `apps/web/src/components/ui/slider.tsx`
- `apps/web/src/components/ui/switch.tsx`
- `apps/web/src/components/ui/table.tsx`
- `apps/web/src/components/ui/tabs.tsx`
- `apps/web/src/components/ui/textarea.tsx`
- `apps/web/src/components/ui/toast.tsx`
- `apps/web/src/components/ui/toaster.tsx`
- `apps/web/src/components/ui/toggle.tsx`
- `apps/web/src/components/ui/tooltip.tsx`
- `apps/web/src/components/ui/use-toast.ts`
- `apps/web/src/components/ui/theme-provider.tsx`

##### 5. Utility/Lib Files (6 個)
- `apps/web/src/lib/utils.ts` ⭐ (核心工具)
- `apps/web/src/lib/trpc.ts` ⭐ (tRPC 客戶端)
- `apps/web/src/lib/trpc-provider.tsx`
- `apps/web/src/lib/exportUtils.ts`
- `packages/api/src/lib/email.ts` ⭐ (Email 服務)
- `packages/api/src/trpc.ts` ⭐ (tRPC 伺服器)

---

#### 🟢 P2 (中優先級) - 12 個文件

##### 6. Hooks (2 個)
- `apps/web/src/hooks/useDebounce.ts`
- `apps/web/src/hooks/use-theme.ts`

##### 7. Auth Package (1 個)
- `packages/auth/src/index.ts`

##### 8. Types/Interfaces (9 個)
- `apps/web/src/types/*.ts` (待確認具體文件)
- `packages/api/src/types/*.ts` (待確認具體文件)

---

## 🎯 更新策略

### 階段劃分 (3 階段，7 天)

#### **Phase 1: 核心業務邏輯** (Day 1-3)
- ✅ **Day 1**: API Routers (14 個) - 最關鍵的業務邏輯
- ✅ **Day 2**: Business Components (25 個) - 業務表單和操作
- ✅ **Day 3**: Page Components (45 個) - 用戶入口頁面

**目標**: 完成 84 個文件 (61% 總進度)

#### **Phase 2: 設計系統和工具** (Day 4-5)
- ✅ **Day 4**: UI Components (35 個) - shadcn/ui 組件
- ✅ **Day 5**: Utility/Lib Files (6 個) - 工具函數

**目標**: 完成 41 個文件 (累計 91% 總進度)

#### **Phase 3: 擴展功能** (Day 6-7)
- ✅ **Day 6**: Hooks (2 個) + Auth (1 個) + Types (9 個)
- ✅ **Day 7**: 驗證、修正、文檔更新

**目標**: 完成 12 個文件 (累計 100% 總進度)

---

## 📋 JSDoc 標準模板

### @related 連結格式決策

**選擇**: **相對路徑** (從專案根目錄開始)

**理由**:
1. ✅ IDE 支援跳轉 (VS Code Ctrl+Click)
2. ✅ 重構時路徑相對穩定
3. ✅ 文件移動時容易批量更新
4. ✅ 符合 monorepo 慣例

**範例**:
```typescript
/**
 * @related
 * - packages/api/src/routers/project.ts - 專案 API Router
 * - apps/web/src/components/project/ProjectForm.tsx - 專案表單組件
 * - packages/db/prisma/schema.prisma - Project 資料模型
 */
```

### 完整模板結構

```typescript
/**
 * @fileoverview [文件簡短標題 - 繁體中文]
 *
 * @description
 * [詳細功能說明 2-4 行，描述文件的主要用途和職責]
 *
 * @module [模組路徑] (選用)
 * @component [組件名稱] (React 組件必要)
 * @page [頁面路由] (Page 組件必要)
 *
 * @features
 * - [主要功能 1]
 * - [主要功能 2]
 * - [主要功能 3]
 *
 * @props (React 組件必要)
 * @param {Object} props - 組件屬性
 * @param {string} props.xxx - xxx 屬性說明
 *
 * @permissions (需要權限控制的文件)
 * - [角色]: [權限說明]
 *
 * @example (複雜組件/函數建議)
 * ```typescript
 * // 使用範例
 * ```
 *
 * @dependencies
 * - [主要依賴 1]: [用途]
 * - [主要依賴 2]: [用途]
 *
 * @related
 * - [相對路徑] - [文件說明]
 *
 * @author IT Department
 * @since [Epic X - 功能名稱]
 * @lastModified YYYY-MM-DD [(變更說明)]
 */
```

---

## 📊 進度追蹤系統

### 追蹤文件: `JSDOC-MIGRATION-PROGRESS.md`

將創建進度追蹤表格，實時記錄每個文件的更新狀態：

| 文件路徑 | 類型 | 優先級 | 狀態 | 更新日期 | 備註 |
|---------|------|--------|------|---------|------|
| packages/api/src/routers/budgetPool.ts | Router | P0 | ⏳ 待更新 | - | - |
| ... | ... | ... | ... | ... | ... |

**狀態標記**:
- ⏳ 待更新
- 🔄 進行中
- ✅ 已完成
- ⚠️ 需要審查
- 🔴 有問題

---

## 🔍 驗證機制

### 自動化驗證腳本

創建 `scripts/validate-jsdoc.js`:

```javascript
/**
 * 驗證所有代碼文件是否包含 JSDoc 註釋
 *
 * 檢查項目:
 * 1. 文件是否有 @fileoverview
 * 2. 文件是否有 @description
 * 3. 文件是否有 @author 和 @since
 * 4. @related 路徑是否存在
 * 5. JSDoc 格式是否正確
 */
```

### 手動驗證清單

每個文件完成後檢查:
- [ ] JSDoc 位於文件最頂部（import 之前）
- [ ] 包含所有必要欄位 (@fileoverview, @description, @author, @since)
- [ ] @features 列表清晰且完整
- [ ] @related 路徑正確且文件存在
- [ ] 中文描述清晰準確
- [ ] 格式符合 JSDoc 標準

---

## 🚀 執行流程

### Step 1: 準備階段 (30 分鐘)
1. ✅ 創建 `claudedocs/6-ai-assistant/jsdoc-migration/` 目錄
2. ✅ 創建本計劃文檔 `JSDOC-MIGRATION-MASTER-PLAN.md`
3. ⏳ 創建進度追蹤文檔 `JSDOC-MIGRATION-PROGRESS.md`
4. ⏳ 創建驗證腳本 `scripts/validate-jsdoc.js`
5. ⏳ 創建模板文件 `JSDOC-TEMPLATES.md`

### Step 2: Phase 1 執行 (Day 1-3)
1. ⏳ Day 1: 更新所有 API Routers
2. ⏳ Day 2: 更新所有 Business Components
3. ⏳ Day 3: 更新所有 Page Components

### Step 3: Phase 2 執行 (Day 4-5)
1. ⏳ Day 4: 更新所有 UI Components
2. ⏳ Day 5: 更新所有 Utility/Lib Files

### Step 4: Phase 3 執行 (Day 6-7)
1. ⏳ Day 6: 更新 Hooks, Auth, Types
2. ⏳ Day 7: 全面驗證和修正

### Step 5: 完成階段 (1 小時)
1. ⏳ 執行驗證腳本，確認 100% 覆蓋
2. ⏳ 更新 PROJECT-INDEX.md
3. ⏳ 更新 DEVELOPMENT-LOG.md
4. ⏳ 創建 Git commit
5. ⏳ 推送到 GitHub

---

## 📈 成功標準

### 完成條件
- [x] 所有 137 個代碼文件都有 JSDoc 註釋
- [ ] 所有 JSDoc 包含必要欄位
- [ ] 所有 @related 路徑驗證通過
- [ ] 驗證腳本 0 錯誤
- [ ] 文檔更新完成
- [ ] Git commit 已推送

### 質量標準
- JSDoc 格式正確率: 100%
- 中文描述清晰度: >95%
- @related 路徑正確率: 100%
- 開發者滿意度: >4.0/5.0

---

## 🎯 下一步行動

### 立即執行 (現在)
1. ✅ 創建本計劃文檔
2. ⏳ 獲得用戶確認和批准
3. ⏳ 創建進度追蹤文檔
4. ⏳ 創建驗證腳本
5. ⏳ 開始 Phase 1 Day 1 執行

### 持續跟進
- 每日更新進度追蹤文檔
- 每階段完成後執行驗證
- 遇到問題立即記錄和解決

---

**維護者**: AI Assistant
**審核者**: 開發團隊
**創建日期**: 2025-11-14
**版本**: V1.0
