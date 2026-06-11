# I18N 國際化遷移問題記錄

本文檔記錄在 next-intl 國際化遷移過程中遇到的問題、解決方案和經驗教訓。

---

## 問題索引

| 問題編號 | 問題描述 | 優先級 | 狀態 | 解決日期 |
|---------|---------|-------|------|---------|
| FIX-056 | Nested Links 警告 | P2 | ✅ 已解決 | 2025-11-03 |
| FIX-057 | 大規模重複 Import | P0 | ✅ 已解決 | 2025-11-03 |
| FIX-058 | Webpack 緩存導致翻譯未更新 | P1 | ✅ 已解決 | 2025-11-03 |
| FIX-060 | 英文版顯示中文內容 | P0 | ✅ 已解決 | 2025-11-04 |
| FIX-062 | Login 頁面翻譯鍵缺失 | P1 | ✅ 已解決 | 2025-11-05 |
| FIX-063 | 四大頁面系統性翻譯問題 | P0 | ✅ 已解決 | 2025-11-05 |
| FIX-064 | 剩餘翻譯問題修復 | P1 | ✅ 已解決 | 2025-11-05 |
| **FIX-077** | **4 個 I18N 缺失翻譯鍵** | **P1** | ✅ **已解決** | **2025-11-07** |
| **FIX-078** | **34 頁面 Breadcrumb 路由問題** | **P0** | ✅ **已解決** | **2025-11-07** |
| **FIX-079** | **Breadcrumb 修復導致運行時錯誤** | **P0** | ✅ **已解決** | **2025-11-07** |
| **FIX-080** | **OM Expenses 和 ChargeOut 翻譯** | **P1** | ✅ **已解決** | **2025-11-07** |
| **FIX-081** | **Budget Proposals 搜索/過濾缺失** | **P1** | ✅ **已解決** | **2025-11-08** |
| **FIX-082** | **Budget Pools 年度過濾失效** | **P1** | ✅ **已解決** | **2025-11-08** |
| **FIX-083** | **Expenses 狀態過濾 400 錯誤** | **P0** | ✅ **已解決** | **2025-11-08** |
| **FIX-084** | **Users 頁面英文版顯示中文** | **P0** | ✅ **已解決** | **2025-11-08** |
| **FIX-085** | **TopBar 語言切換快捷按鈕** | **P1** | ✅ **已解決** | **2025-11-08** |
| **FIX-086** | **語言切換器 Hydration 錯誤** | **P0** | ✅ **已解決** | **2025-11-08** |
| **FIX-087** | **共用組件硬編碼中文系統性問題** | **P0** | ✅ **已解決** | **2025-11-08** |

---

## FIX-080: OM Expenses 月度統計和 ChargeOut 操作按鈕翻譯

### 問題描述
**發現時間**: 2025-11-07 14:00
**影響範圍**: OM Expenses 詳情頁、Charge-Outs 詳情頁
**優先級**: P1 (影響用戶體驗)

手動測試發現兩個 i18n 問題:
1. OM Expenses 詳情頁 MonthlyGrid 組件缺少 9 個翻譯鍵
2. Charge-Outs 詳情頁操作按鈕和對話框顯示中文硬編碼

### 問題 1: OM Expenses MonthlyGrid 缺失翻譯

**影響頁面**:
- `http://localhost:3000/zh-TW/om-expenses/[id]`
- `http://localhost:3000/en/om-expenses/[id]`

**錯誤信息**:
```
IntlError: MISSING_MESSAGE: Could not resolve `omExpenses.monthlyGrid.description`
IntlError: MISSING_MESSAGE: Could not resolve `omExpenses.monthlyGrid.saveButton`
IntlError: MISSING_MESSAGE: Could not resolve `omExpenses.monthlyGrid.monthColumn`
IntlError: MISSING_MESSAGE: Could not resolve `omExpenses.monthlyGrid.amountColumn`
IntlError: MISSING_MESSAGE: Could not resolve `omExpenses.monthlyGrid.tips.title`
IntlError: MISSING_MESSAGE: Could not resolve `omExpenses.monthlyGrid.tips.enterAmounts`
IntlError: MISSING_MESSAGE: Could not resolve `omExpenses.monthlyGrid.tips.autoCalculate`
IntlError: MISSING_MESSAGE: Could not resolve `omExpenses.monthlyGrid.tips.clickSave`
IntlError: MISSING_MESSAGE: Could not resolve `omExpenses.monthlyGrid.tips.autoUpdate`
```

**根本原因**:
- 組件 `OMExpenseMonthlyGrid.tsx` 使用了這些翻譯鍵
- 但翻譯文件中只有 `monthlyGrid.title` 和 `monthlyGrid.total`
- 缺少表格使用說明、欄位標題和使用提示

### 問題 2: ChargeOut 操作按鈕硬編碼中文

**影響頁面**:
- `http://localhost:3000/en/charge-outs/[id]` (英文版顯示中文)

**硬編碼內容統計**:
- 6 個按鈕文字: 編輯、提交審核、確認、拒絕、標記為已付款、刪除
- 15 個 Toast 訊息: 成功/失敗提示
- 20 個對話框字串: 標題、描述、按鈕文字

**問題組件**: `ChargeOutActions.tsx` (377 lines)

**根本原因**:
- 組件使用硬編碼中文字串
- 未使用 `useTranslations` hook
- 所有用戶提示都是中文

### 解決方案

#### 修復 1: 添加 OM Expenses MonthlyGrid 翻譯鍵

**en.json** (lines 1768-1796):
```json
"monthlyGrid": {
  "title": "Monthly Expense Statistics",
  "description": "Edit actual spending amounts for months 1-12, system will automatically calculate total",
  "saveButton": "Save Monthly Records",
  "monthColumn": "Month",
  "amountColumn": "Actual Spending (HKD)",
  "total": "Total",
  "tips": {
    "title": "Usage Tips",
    "enterAmounts": "Enter actual spending amount for each month",
    "autoCalculate": "System will automatically calculate total actual spending and utilization rate",
    "clickSave": "Click \"Save Monthly Records\" button to save all changes",
    "autoUpdate": "After saving, system will automatically update OM expense actualSpent field"
  }
}
```

**zh-TW.json** (lines 1768-1796):
```json
"monthlyGrid": {
  "title": "月度費用統計",
  "description": "編輯 1-12 月的實際支出金額，系統將自動計算總額",
  "saveButton": "保存月度記錄",
  "monthColumn": "月份",
  "amountColumn": "實際支出 (HKD)",
  "total": "總計",
  "tips": {
    "title": "使用提示",
    "enterAmounts": "輸入每個月的實際支出金額",
    "autoCalculate": "系統會自動計算總實際支出和使用率",
    "clickSave": "點擊「保存月度記錄」按鈕保存所有更改",
    "autoUpdate": "保存後，系統會自動更新 OM 費用的 actualSpent 欄位"
  }
}
```

#### 修復 2: ChargeOutActions 組件完整 i18n 遷移

**步驟 1**: 新增翻譯鍵結構

**en.json** (lines 1953-2009):
```json
"chargeOuts": {
  "actions": {
    "edit": "Edit",
    "submit": "Submit for Review",
    "confirm": "Confirm",
    "reject": "Reject",
    "markAsPaid": "Mark as Paid",
    "delete": "Delete",
    "dialogs": {
      "submit": {
        "title": "Confirm Submission",
        "description": "Are you sure you want to submit ChargeOut \"{name}\"?...",
        "cancel": "Cancel",
        "confirm": "Confirm Submit"
      },
      // ... 其他 4 個對話框
    },
    "messages": {
      "submitSuccess": "Submitted Successfully",
      "submitSuccessDesc": "ChargeOut {name} has been submitted for review",
      // ... 其他 12 個訊息
    }
  }
}
```

**步驟 2**: 修改 ChargeOutActions.tsx

使用 surgical-task-executor 批量替換:
1. 添加 `import { useTranslations } from 'next-intl';`
2. 添加 `const t = useTranslations('chargeOuts.actions');`
3. 替換所有 41 個硬編碼字串為翻譯鍵調用

**修改前** (line 215):
```typescript
<Button variant="outline" onClick={handleEdit}>
  <Edit className="mr-2 h-4 w-4" />
  編輯
</Button>
```

**修改後** (line 215):
```typescript
<Button variant="outline" onClick={handleEdit}>
  <Edit className="mr-2 h-4 w-4" />
  {t('edit')}
</Button>
```

### 修復文件清單

1. **apps/web/src/messages/en.json**
   - 新增 `omExpenses.monthlyGrid.description` 等 9 個鍵
   - 新增 `chargeOuts.actions` 完整結構 (41 個鍵)

2. **apps/web/src/messages/zh-TW.json**
   - 對應的中文翻譯 (50 個鍵)

3. **apps/web/src/components/charge-out/ChargeOutActions.tsx**
   - 添加 useTranslations hook
   - 替換 41 個硬編碼字串

### 影響評估

**修復前**:
- ❌ OM Expenses MonthlyGrid 顯示 MISSING_MESSAGE 錯誤
- ❌ Charge-Outs 英文版操作按鈕顯示中文
- ❌ 所有對話框和提示都是中文

**修復後**:
- ✅ OM Expenses MonthlyGrid 完整顯示雙語
- ✅ Charge-Outs 操作按鈕正確顯示英文/中文
- ✅ 所有對話框和提示支援雙語

**統計數據**:
- **新增翻譯鍵 (en)**: 50 個
- **新增翻譯鍵 (zh-TW)**: 50 個
- **總翻譯鍵數**: 1577 個 (從 1527 增加)
- **修復時間**: 1.5 小時
- **修改檔案**: 3 個
- **影響頁面**: 2 個

### 技術實施細節

#### Translation Key 參數化

使用 next-intl 的參數傳遞功能:

```typescript
// Toast 訊息
toast({
  title: t('messages.submitSuccess'),
  description: t('messages.submitSuccessDesc', { name: chargeOut.name })
});

// 對話框
<AlertDialogDescription>
  {t('dialogs.submit.description', { name: chargeOut.name })}
</AlertDialogDescription>
```

#### Surgical-task-executor 批量替換策略

1. **識別模式**: 找出所有硬編碼中文字串
2. **分層替換**: 按鈕 → Toast → 對話框
3. **參數化處理**: 包含變數的字串轉換為參數化翻譯
4. **保持邏輯不變**: 只替換字串，不修改業務邏輯

### 經驗教訓

#### 技術層面
1. **完整測試覆蓋**: 手動測試應覆蓋所有頁面和語言版本
2. **組件級別檢查**: 不僅檢查頁面，還要檢查所有組件
3. **參數化設計**: 使用參數傳遞而非模板字串拼接

#### 流程層面
1. **系統性排查**: 使用自動化工具掃描所有硬編碼字串
2. **分批修復**: 按頁面/組件分批處理，避免遺漏
3. **驗證機制**: pre-commit hook 自動驗證翻譯文件

### 相關文檔
- 📄 **Commit**: FIX-080 (commit 038765f)
- 📊 **進度記錄**: `I18N-PROGRESS.md` (2025-11-07 section)
- 📝 **問題記錄**: `I18N-ISSUES-LOG.md` (本文檔)

---

## FIX-079: Breadcrumb 路由修復導致的運行時錯誤

### 問題描述
**發現時間**: 2025-11-07 12:00
**影響範圍**: projects/[id]/page.tsx, proposals/page.tsx, 7 個 new 頁面
**優先級**: P0 (阻塞性問題 - 無法訪問頁面)

在 FIX-078 完成後，用戶報告兩個關鍵運行時錯誤:
1. `ReferenceError: locale is not defined` (projects/[id]/page.tsx line 285)
2. `Build Error: the name Link is defined multiple times` (proposals/page.tsx lines 15-16)
3. 7 個頁面缺少 Link import 導致 TypeScript 錯誤

### 錯誤 1: locale 變數未定義

**錯誤信息**:
```
Unhandled Runtime Error
ReferenceError: locale is not defined

Source: src\app\[locale]\projects\[id]\page.tsx (285:71)
{new Date(project.createdAt).toLocaleDateString(locale === 'zh-TW' ? 'zh-TW' : 'en-US')}
```

**根本原因**:
- FIX-078 的自動化腳本 `remove-locale-prefix.js` 錯誤地移除了 `const locale = params.locale as string;`
- 但檔案中仍有 4 處使用 locale 變數進行日期格式化 (lines 285, 291, 412, 494)
- 導致運行時 ReferenceError

**影響**: 無法訪問任何 projects/[id] 頁面

### 錯誤 2: Link 重複 import

**錯誤信息**:
```
Build Error
Failed to compile
Error: x the name `Link` is defined multiple times

Source: src\app\[locale]\proposals\page.tsx
Line 15: import { Link } from "@/i18n/routing";
Line 16: import { Link, useRouter } from "@/i18n/routing";
```

**根本原因**:
- FIX-078 的 `fix-breadcrumb-routing.js` 腳本未檢查是否已存在 Link import
- 自動添加了重複的 import 語句

**影響**: proposals 頁面無法編譯

### 錯誤 3: 7 個頁面缺少 Link import

**影響檔案**:
- expenses/new/page.tsx
- proposals/new/page.tsx
- purchase-orders/new/page.tsx
- quotes/new/page.tsx
- settings/page.tsx
- users/new/page.tsx
- vendors/new/page.tsx

**根本原因**: 這些頁面在 FIX-078 修復過程中被遺漏

### 解決方案

#### 修復 1: 恢復 locale 變數聲明

**檔案**: `apps/web/src/app/[locale]/projects/[id]/page.tsx`

**修改** (line 50):
```typescript
const params = useParams();
const router = useRouter();
const { toast } = useToast();
const id = params.id as string;
const locale = params.locale as string; // ✅ 重新添加 - 用於日期格式化
```

**使用位置** (4 處):
- Line 285: `{new Date(project.createdAt).toLocaleDateString(locale === 'zh-TW' ? 'zh-TW' : 'en-US')}`
- Line 291: `{new Date(project.updatedAt).toLocaleDateString(locale === 'zh-TW' ? 'zh-TW' : 'en-US')}`
- Line 412: `{new Date(proposal.createdAt).toLocaleDateString(locale === 'zh-TW' ? 'zh-TW' : 'en-US')}`
- Line 494: `{new Date(po.date).toLocaleDateString(locale === 'zh-TW' ? 'zh-TW' : 'en-US')}`

#### 修復 2: 移除重複 Link import

**檔案**: `apps/web/src/app/[locale]/proposals/page.tsx`

**修改前** (lines 15-16):
```typescript
import { Link } from "@/i18n/routing";
import { Link, useRouter } from "@/i18n/routing";
```

**修改後** (line 15):
```typescript
import { Link, useRouter } from "@/i18n/routing";
```

#### 修復 3: 批量添加缺失的 Link import

**創建工具**: `scripts/add-missing-link-import.js` (70 lines)

**核心邏輯**:
```javascript
// 在 next-intl import 之後插入 Link import
let nextIntlImportMatch = content.match(/import\s+{[^}]+}\s+from\s+['"]next-intl['"];?\n/);

if (!nextIntlImportMatch) {
  // 嘗試匹配不帶換行符的格式
  nextIntlImportMatch = content.match(/import\s+{[^}]+}\s+from\s+['"]next-intl['"]/);
}

if (nextIntlImportMatch) {
  const insertPosition = nextIntlImportMatch.index + nextIntlImportMatch[0].length;
  const separator = nextIntlImportMatch[0].endsWith('\n') ? '' : '\n';
  content = content.slice(0, insertPosition) +
            separator +
            'import { Link } from "@/i18n/routing";\n' +
            content.slice(insertPosition);
}
```

**執行結果**:
```
✅ 修復: apps/web/src/app/[locale]/expenses/new/page.tsx
✅ 修復: apps/web/src/app/[locale]/proposals/new/page.tsx
✅ 修復: apps/web/src/app/[locale]/purchase-orders/new/page.tsx
✅ 修復: apps/web/src/app/[locale]/quotes/new/page.tsx
✅ 修復: apps/web/src/app/[locale]/settings/page.tsx
✅ 修復: apps/web/src/app/[locale]/users/new/page.tsx
✅ 修復: apps/web/src/app/[locale]/vendors/new/page.tsx

🎉 修復完成! 修復: 7 個檔案
```

#### 修復 4: 修正 import 分號格式

**問題**: 批量添加 import 後產生多餘分號

**創建工具**: `scripts/fix-import-semicolons.js` (65 lines)

**修正前**:
```typescript
import { useTranslations } from 'next-intl'
import { Link } from "@/i18n/routing";
;
```

**修正後**:
```typescript
import { useTranslations } from 'next-intl';
import { Link } from "@/i18n/routing";
```

**執行結果**: 成功修復 6 個檔案的分號格式問題

### 修復文件清單

1. **apps/web/src/app/[locale]/projects/[id]/page.tsx**
   - 重新添加 `const locale = params.locale as string;` (line 50)

2. **apps/web/src/app/[locale]/proposals/page.tsx**
   - 移除重複的 Link import (line 15)

3. **7 個 /new 頁面**
   - 批量添加 Link import
   - 修正 import 分號格式

4. **scripts/add-missing-link-import.js** (新增)
   - 自動化添加 Link import 工具

5. **scripts/fix-import-semicolons.js** (新增)
   - 自動化修正分號格式工具

### 影響評估

**修復前**:
- ❌ 無法訪問 projects/[id] 頁面 (ReferenceError)
- ❌ proposals 頁面無法編譯 (Duplicate import)
- ❌ 7 個頁面有 TypeScript 錯誤

**修復後**:
- ✅ projects/[id] 頁面正常顯示
- ✅ proposals 頁面成功編譯
- ✅ 所有 /new 頁面無編譯錯誤
- ✅ 日期格式化正確顯示 (zh-TW/en-US)
- ✅ Breadcrumb 導航保持 locale 上下文

**統計數據**:
- **修改檔案**: 9 個頁面組件
- **新增腳本**: 2 個自動化工具
- **修復錯誤**: 4 類問題
- **總代碼行**: ~140 行修改
- **修復時間**: 1 小時

### 技術實施細節

#### 自動化腳本改進

**問題分析**:
- `remove-locale-prefix.js` 過於激進，未檢查 locale 變數是否仍在使用
- `fix-breadcrumb-routing.js` 未檢查 import 是否已存在

**改進建議**:
1. **依賴分析**: 刪除變數前檢查是否有引用
2. **重複檢測**: 添加 import 前檢查是否已存在
3. **Dry-run 模式**: 先預覽變更再實際執行
4. **分階段執行**: 每階段後驗證編譯

### 經驗教訓

#### 技術層面
1. **自動化工具限制**: 批量修改工具需要完善的檢查機制
2. **變數依賴追蹤**: 刪除變數前必須檢查所有引用
3. **Import 重複檢測**: 添加 import 前檢查現有 import
4. **多輪驗證**: 自動化修復後需要人工驗證

#### 流程層面
1. **增量修復**: 大規模修改應分批次執行和驗證
2. **快速響應**: 用戶報告問題後立即修復
3. **根因分析**: 深入分析自動化工具的問題
4. **工具改進**: 基於問題改進自動化工具

### 相關文檔
- 📄 **Commit**: FIX-079 (commit be57548)
- 📊 **進度記錄**: `I18N-PROGRESS.md` (2025-11-07 section)
- 📝 **問題記錄**: `I18N-ISSUES-LOG.md` (本文檔)

---

## FIX-078: 34 頁面 Breadcrumb 路由語言環境問題

### 問題描述
**發現時間**: 2025-11-07 10:00
**影響範圍**: 34 個頁面的 breadcrumb 導航
**優先級**: P0 (嚴重影響用戶體驗)

**用戶報告**:
"發現了一個重大問題，請重新檢查所有頁面的麵包屑路由問題，因為我發現有一些有麵包屑路由的頁面都有問題，就是英文版本的話，會跳轉到中文版本的頁，所以請重新檢查一次，中文的是應該跳轉回中文，本來是英文就應該繼續跳轉到英文版的"

**症狀**:
- 在 `/en/dashboard` 點擊 breadcrumb 鏈接跳轉到 `/zh-TW/*`
- 在 `/zh-TW/dashboard` 點擊 breadcrumb 鏈接跳轉到 `/en/*`
- Breadcrumb 導航無法保持當前語言環境

### 根本原因分析

#### 問題模式識別

掃描發現 34 個頁面存在兩種錯誤模式:

**模式 1: 直接使用 href 屬性 (不包含 locale)**
```typescript
// ❌ 錯誤: BreadcrumbLink 直接使用 href，不會自動添加 locale
<BreadcrumbLink href="/dashboard">{tNav('home')}</BreadcrumbLink>
```

**模式 2: 使用模板字串手動添加 locale**
```typescript
// ❌ 錯誤: 當使用 next-intl Link 時會導致雙重 locale 前綴
<BreadcrumbLink href={\`/${locale}/dashboard\`}>{tNav('home')}</BreadcrumbLink>
```

#### 技術原理

**BreadcrumbLink 組件**:
- 來自 shadcn/ui
- 預設渲染為 `<a>` 標籤
- 不支援 next-intl 的 locale 自動處理

**next-intl Link 組件**:
- 自動在 href 前添加當前 locale
- 例如: `<Link href="/dashboard">` → `/en/dashboard` 或 `/zh-TW/dashboard`

**asChild 模式**:
- Radix UI 提供的組合模式
- 允許將子組件的屬性合併到父組件
- `<BreadcrumbLink asChild><Link href="/path">...</Link></BreadcrumbLink>`

### 解決方案

#### 正確模式

```typescript
import { Link } from "@/i18n/routing";
import { Breadcrumb, BreadcrumbList, BreadcrumbItem, BreadcrumbLink, BreadcrumbSeparator, BreadcrumbPage } from '@/components/ui/breadcrumb';

<Breadcrumb>
  <BreadcrumbList>
    <BreadcrumbItem>
      <BreadcrumbLink asChild>
        <Link href="/dashboard">{tNav('home')}</Link>
      </BreadcrumbLink>
    </BreadcrumbItem>
    <BreadcrumbSeparator />
    <BreadcrumbItem>
      <BreadcrumbPage>{t('title')}</BreadcrumbPage>
    </BreadcrumbItem>
  </BreadcrumbList>
</Breadcrumb>
```

**關鍵要點**:
1. `BreadcrumbLink` 使用 `asChild` prop
2. 內部使用 next-intl 的 `Link` 組件
3. `Link` 的 `href` 不包含 locale (自動添加)
4. 最後一項使用 `BreadcrumbPage` (不需要鏈接)

#### 自動化修復工具

**創建工具 1**: `scripts/fix-breadcrumb-routing.js` (154 lines)

**核心邏輯**:
```javascript
// 模式 1: 替換 href 屬性為 asChild + Link
content = content.replace(
  /<BreadcrumbLink\s+href=["']([^"']+)["']>([^<]+)<\/BreadcrumbLink>/g,
  '<BreadcrumbLink asChild><Link href="$1">$2</Link></BreadcrumbLink>'
);

// 模式 2: 替換模板字串
content = content.replace(
  /<BreadcrumbLink\s+href=\{`([^`]+)`\}>((?:(?!<\/BreadcrumbLink>).)*)<\/BreadcrumbLink>/gs,
  (match, href, children) => {
    if (children.includes('<Link')) return match;
    return \`<BreadcrumbLink asChild><Link href={\\\`\${href}\\\`}>\${children}</Link></BreadcrumbLink>\`;
  }
);

// 檢查並添加 Link import
if (!hasLinkImport && hasBreadcrumbLinks) {
  // 在 next-intl import 後添加
  content = content.replace(
    /(import\s+{[^}]*}\s+from\s+['"]next-intl['"];?\n)/,
    \`$1import { Link } from "@/i18n/routing";\n\`
  );
}
```

**創建工具 2**: `scripts/remove-locale-prefix.js` (65 lines)

**目的**: 移除手動添加的 `/${locale}/` 前綴

```javascript
// 移除 /${locale}/ 前綴
content = content.replace(/href=\{`\/\$\{locale\}\/([^`]+)`\}/g, 'href="/$1"');

// 移除不再使用的 locale 變數
const localeUsageCount = (content.match(/\$\{locale\}/g) || []).length;
if (localeUsageCount === 0) {
  content = content.replace(/\s*const locale = params\.locale as string;\n/, '');
}
```

**執行結果**:
```
🔧 開始修復 breadcrumb 路由問題...

✅ 修復: apps/web/src/app/[locale]/proposals/[id]/page.tsx (2 處 breadcrumb)
✅ 修復: apps/web/src/app/[locale]/projects/[id]/page.tsx (3 處 breadcrumb)
... (共 34 個檔案)

🎉 第一輪修復完成! 修復: 25 個檔案
執行第二輪腳本...
🎉 第二輪修復完成! 修復: 17 個檔案
```

### 修復文件清單

**34 個受影響的頁面**:

**Projects 模組** (5 頁面):
- projects/page.tsx
- projects/[id]/page.tsx
- projects/[id]/quotes/page.tsx
- projects/new/page.tsx
- projects/[id]/edit/page.tsx

**Proposals 模組** (5 頁面):
- proposals/page.tsx
- proposals/[id]/page.tsx
- proposals/new/page.tsx
- proposals/[id]/edit/page.tsx
- proposals/[id]/comments/page.tsx

**Budget Pools 模組** (4 頁面):
- budget-pools/page.tsx
- budget-pools/[id]/page.tsx
- budget-pools/new/page.tsx
- budget-pools/[id]/edit/page.tsx

**其他模組** (20 頁面):
- Vendors (4)
- Purchase Orders (4)
- Expenses (4)
- OM Expenses (4)
- Charge-Outs (4)

### 影響評估

**修復前**:
- ❌ Breadcrumb 鏈接無法保持 locale
- ❌ 英文版點擊跳轉到中文版
- ❌ 中文版點擊跳轉到英文版
- ❌ 用戶體驗嚴重受影響

**修復後**:
- ✅ 所有 breadcrumb 鏈接保持當前 locale
- ✅ 英文版始終在英文環境中導航
- ✅ 中文版始終在中文環境中導航
- ✅ 用戶體驗恢復正常

**統計數據**:
- **影響頁面**: 34 個
- **修復 breadcrumb**: ~100 個鏈接
- **新增 Link import**: 25 個檔案
- **移除 locale 前綴**: 9 個檔案
- **修復時間**: 2 小時
- **自動化工具**: 2 個腳本

### 技術實施細節

#### asChild 模式深入理解

**Radix UI Slot API**:
```typescript
// BreadcrumbLink 的內部實現
const BreadcrumbLink = ({ asChild, ...props }) => {
  const Comp = asChild ? Slot : "a";
  return <Comp {...props} />;
}

// 使用 asChild 時
<BreadcrumbLink asChild>
  <Link href="/dashboard">Home</Link>
</BreadcrumbLink>

// 實際渲染結果
<Link href="/dashboard" className="breadcrumb-link-class">Home</Link>
```

**好處**:
1. 保留 BreadcrumbLink 的樣式
2. 使用 Link 的路由功能
3. 完美結合兩個組件的優點

#### Next-intl Link 自動 Locale 處理

```typescript
// 在 /en/dashboard 環境下
<Link href="/projects">Projects</Link>
// 實際渲染: <a href="/en/projects">Projects</a>

// 在 /zh-TW/dashboard 環境下
<Link href="/projects">專案</Link>
// 實際渲染: <a href="/zh-TW/projects">專案</a>
```

### 經驗教訓

#### 技術層面
1. **組件組合**: 理解 asChild 模式對多庫整合至關重要
2. **自動化規模**: 大規模修復需要可靠的自動化工具
3. **Locale 處理**: 讓框架處理 locale，不要手動添加

#### 流程層面
1. **完整測試**: 修復後需要全面測試所有語言版本
2. **工具驗證**: 自動化工具需要多輪驗證確保正確性
3. **增量提交**: 分階段提交便於問題追蹤

#### 預防措施
1. **代碼審查**: 嚴格審查 breadcrumb 實現
2. **組件文檔**: 建立 breadcrumb 最佳實踐文檔
3. **E2E 測試**: 添加語言切換的 E2E 測試

### 相關文檔
- 📄 **Commit**: FIX-078 (commit e197b0a)
- 📊 **進度記錄**: `I18N-PROGRESS.md` (2025-11-07 section)
- 📝 **問題記錄**: `I18N-ISSUES-LOG.md` (本文檔)

---

## FIX-077: 4 個 I18N 缺失翻譯鍵問題

### 問題描述
**發現時間**: 2025-11-07 08:00
**影響範圍**: Vendors、Projects、OM Expenses、Charge-Outs 四個頁面
**優先級**: P1 (影響用戶體驗)

手動測試發現 4 個具體問題:
1. Vendors 編輯頁面缺少 `common.actions.update` 翻譯鍵
2. Projects 詳情頁 Quotes 標籤缺少 `navigation.projects` 翻譯鍵
3. OM Expenses 新建頁面缺少 12+ 個表單相關翻譯鍵
4. Charge-Outs 列表頁面全部內容顯示中文硬編碼

### 問題 1: common.actions.update 缺失

**影響頁面**: `http://localhost:3000/en/vendors/[id]/edit`

**錯誤信息**:
```
IntlError: MISSING_MESSAGE: Could not resolve `common.actions.update` in messages for locale `en`.
```

**根本原因**:
- 編輯頁面使用 `tCommon('actions.update')`
- 但 common.actions 只有 `save`, `cancel`, `delete` 等
- 缺少 `update` 鍵

**解決方案**:
```json
// en.json
"common": {
  "actions": {
    "update": "Update"
  }
}

// zh-TW.json
"common": {
  "actions": {
    "update": "更新"
  }
}
```

### 問題 2: navigation.projects 缺失

**影響頁面**: `http://localhost:3000/en/projects/[id]/quotes`

**錯誤信息**:
```
IntlError: MISSING_MESSAGE: Could not resolve `navigation.projects` in messages for locale `en`.
```

**根本原因**:
- Breadcrumb 使用 `tNav('projects')`
- 但 navigation 命名空間只有 `navigation.menu.projects`
- 缺少頂層 `navigation.projects` 鍵

**解決方案**:
```json
// en.json
"navigation": {
  "projects": "Projects",
  "menu": {
    "projects": "Project Management"
  }
}

// zh-TW.json
"navigation": {
  "projects": "專案管理",
  "menu": {
    "projects": "專案管理"
  }
}
```

### 問題 3: OM Expenses 表單翻譯鍵缺失

**影響頁面**: `http://localhost:3000/en/om-expenses/new`

**錯誤信息** (12+ 個):
```
IntlError: MISSING_MESSAGE: Could not resolve `omExpenses.form.basicInfo.title`
IntlError: MISSING_MESSAGE: Could not resolve `omExpenses.form.basicInfo.description`
IntlError: MISSING_MESSAGE: Could not resolve `omExpenses.form.opCoAndVendor.title`
IntlError: MISSING_MESSAGE: Could not resolve `omExpenses.form.opCoAndVendor.description`
IntlError: MISSING_MESSAGE: Could not resolve `omExpenses.form.budgetAndDates.title`
IntlError: MISSING_MESSAGE: Could not resolve `omExpenses.form.budgetAndDates.description`
IntlError: MISSING_MESSAGE: Could not resolve `omExpenses.form.categoryDescription`
IntlError: MISSING_MESSAGE: Could not resolve `omExpenses.form.vendorDescription`
IntlError: MISSING_MESSAGE: Could not resolve `omExpenses.form.budgetDescription`
IntlError: MISSING_MESSAGE: Could not resolve `omExpenses.form.startDate`
IntlError: MISSING_MESSAGE: Could not resolve `omExpenses.form.endDate`
IntlError: MISSING_MESSAGE: Could not resolve `omExpenses.form.createNotice`
```

**根本原因**:
- OMExpenseForm 組件使用卡片式表單佈局
- 每個卡片需要 title 和 description
- 所有這些翻譯鍵都缺失

**解決方案**:
```json
// en.json
"omExpenses": {
  "form": {
    "basicInfo": {
      "title": "Basic Information",
      "description": "OM expense name, category, and fiscal year"
    },
    "opCoAndVendor": {
      "title": "OpCo and Vendor",
      "description": "Select operating company and vendor information"
    },
    "budgetAndDates": {
      "title": "Budget and Date Range",
      "description": "Budget amount and expense period"
    },
    "categoryDescription": "Select the expense category for this OM expense",
    "vendorDescription": "Select a vendor if applicable (optional)",
    "budgetDescription": "Total budget amount allocated for this OM expense",
    "startDate": "Start Date",
    "endDate": "End Date",
    "createNotice": "After creating, you can add monthly expense amounts on the detail page"
  }
}
```

### 問題 4: Charge-Outs 列表頁硬編碼中文

**影響頁面**: `http://localhost:3000/en/charge-outs`

**問題描述**:
- 整個列表頁面 100+ 個中文硬編碼字串
- 頁面標題、搜尋框、篩選器、表格標題、按鈕文字等全部是中文
- 無任何 i18n 支援

**根本原因**:
- charge-outs/page.tsx 未進行 i18n 遷移
- 所有文字都是硬編碼的中文字串

**解決方案**:

使用 surgical-task-executor 進行批量修復:

1. **添加 imports**:
```typescript
import { useTranslations } from 'next-intl';
import { Link } from "@/i18n/routing";
```

2. **添加 translation hooks**:
```typescript
const t = useTranslations('chargeOuts');
const tNav = useTranslations('navigation');
const tCommon = useTranslations('common');
```

3. **替換內容**:
- 頁面標題: `費用轉嫁管理` → `{t('list.title')}`
- 搜尋框: `搜尋 ChargeOut...` → `{t('list.search')}`
- 篩選器: `全部狀態` → `{t('list.filters.allStatuses')}`
- 表格標題: `ChargeOut 名稱` → `{t('list.name')}`
- 按鈕: `新增 ChargeOut` → `{t('list.newChargeOut')}`

4. **新增翻譯鍵** (17 個):
```json
"chargeOuts": {
  "list": {
    "title": "Charge Out Management",
    "subtitle": "Manage IT department charge-outs to operating companies (OpCo)",
    "newChargeOut": "New Charge Out",
    "search": "Search charge outs...",
    "filters": {
      "status": "Status",
      "allStatuses": "All Statuses",
      "opCo": "Operating Company (OpCo)",
      "allOpCos": "All OpCos",
      "project": "Project",
      "allProjects": "All Projects"
    },
    // ... 其他 8 個鍵
  }
}
```

### 修復文件清單

1. **apps/web/src/messages/en.json**
   - 新增 `common.actions.update` (line 13)
   - 新增 `navigation.projects` (line 113)
   - 新增 `omExpenses.form.*` 11 個鍵 (lines 1702-1719)
   - 新增 `chargeOuts.list.*` 17 個鍵 (lines 1807-1830)
   - 新增 `common.pagination.previous/next` (lines 75-76)

2. **apps/web/src/messages/zh-TW.json**
   - 對應的中文翻譯 (31 個鍵)

3. **apps/web/src/app/[locale]/charge-outs/page.tsx**
   - 添加 imports 和 translation hooks
   - 替換 100+ 個硬編碼字串

### 影響評估

**修復前**:
- ❌ Vendors 編輯頁面顯示 `common.actions.update`
- ❌ Projects Quotes 頁面 breadcrumb 顯示 `navigation.projects`
- ❌ OM Expenses 新建頁面顯示 12+ 個 MISSING_MESSAGE 錯誤
- ❌ Charge-Outs 列表頁英文版顯示中文

**修復後**:
- ✅ Vendors 編輯頁面正確顯示「更新」/「Update」
- ✅ Projects breadcrumb 正確顯示「專案管理」/「Projects」
- ✅ OM Expenses 表單完整顯示雙語
- ✅ Charge-Outs 列表頁完整支援雙語

**統計數據**:
- **新增翻譯鍵 (en)**: 31 個
- **新增翻譯鍵 (zh-TW)**: 31 個
- **總翻譯鍵數**: 1527 個 (驗證通過)
- **修復時間**: 1.5 小時
- **修改檔案**: 3 個
- **影響頁面**: 4 個

### 技術實施細節

#### Surgical-task-executor 批量替換

**優勢**:
- 快速處理 100+ 個字串替換
- 保持代碼格式和結構
- 自動添加必要的 imports

**執行流程**:
1. 分析現有代碼結構
2. 識別所有硬編碼中文字串
3. 建立翻譯鍵映射
4. 批量替換並添加 imports
5. 驗證語法正確性

#### Status Function 本地化

**修改前**:
```typescript
const getStatusText = (status: string) => {
  switch (status) {
    case 'Draft': return '草稿';
    case 'Submitted': return '已提交';
    // ...
  }
}
```

**修改後**:
```typescript
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'Draft': tCommon('status.draft'),
    'Submitted': tCommon('status.submitted'),
    'Confirmed': tCommon('status.confirmed'),
    'Paid': tCommon('status.paid'),
    'Rejected': tCommon('status.rejected'),
  };
  return statusMap[status] || status;
};
```

### 經驗教訓

#### 技術層面
1. **完整測試**: 手動測試每個頁面的每個語言版本
2. **命名一致性**: 保持翻譯鍵命名的一致性
3. **批量處理**: 使用自動化工具處理大量替換

#### 流程層面
1. **優先級排序**: 先修復影響大的問題
2. **增量驗證**: 每個問題修復後立即驗證
3. **文檔同步**: 及時更新文檔記錄

### 相關文檔
- 📄 **Commit**: FIX-077 (commit 56a8359)
- 📊 **進度記錄**: `I18N-PROGRESS.md` (2025-11-07 section)
- 📝 **問題記錄**: `I18N-ISSUES-LOG.md` (本文檔)

---

## FIX-064: 剩餘翻譯問題修復

### 問題描述
**發現時間**: 2025-11-05 00:00
**影響範圍**: Projects 頁面、Proposals 列表頁、Proposals 詳情頁
**優先級**: P1 (影響用戶體驗)

在完成 FIX-062 和 FIX-063 後,測試發現還有 3 個問題:

#### 問題 1: Projects 頁面 pagination.showing 格式錯誤
```
IntlError: FORMATTING_ERROR: The intl string context variable "from" was not provided to the string "顯示 {from} - {to} / {total} 個專案"
```

**根本原因**: 翻譯鍵使用 `{from}`, `{to}` 但代碼傳遞 `start`, `end` 變數名不匹配。

#### 問題 2: Proposals 列表頁面 - common 翻譯鍵缺失
```
IntlError: MISSING_MESSAGE: Could not resolve `common.fields.createdAt`
IntlError: MISSING_MESSAGE: Could not resolve `common.fields.actions`
IntlError: MISSING_MESSAGE: Could not resolve `common.actions.view`
IntlError: MISSING_MESSAGE: Could not resolve `common.actions.edit`
IntlError: MISSING_MESSAGE: Could not resolve `proposals.actions.create`
```

#### 問題 3: Proposals 詳情頁面 - 詳情頁翻譯鍵缺失
大量缺失的翻譯鍵包括:
- `proposals.actions.requestInfo`
- `common.actions.back`
- `proposals.detail.tabs.*` (basic, project, file, meeting)
- `proposals.detail.info.title`
- `proposals.status.rejected.message`

### 解決方案

#### 1. 修復 Projects 頁面 pagination 變數名稱

**zh-TW.json** (line 296-298):
```json
"pagination": {
  "showing": "顯示 {start} - {end} / {total} 個專案",
  "pageInfo": "第 {current} 頁,共 {total} 頁"
}
```

**en.json** (line 296-298):
```json
"pagination": {
  "showing": "Showing {start} - {end} / {total} projects",
  "pageInfo": "Page {current} of {total}"
}
```

**變更**: `{from} - {to}` → `{start} - {end}` 以匹配代碼傳遞的變數名

#### 2. 新增 common 通用翻譯鍵

**zh-TW.json** (line 3-13):
```json
"common": {
  "actions": {
    "actions": "操作",
    "view": "查看",
    "edit": "編輯",
    "back": "返回"
  },
  "fields": {
    "createdAt": "創建時間",
    "updatedAt": "更新時間",
    "actions": "操作"
  }
}
```

#### 3. 新增 Proposals 操作和詳情頁翻譯鍵

**Proposals Actions** (zh-TW.json line 479-492):
```json
"actions": {
  "create": "新增提案",
  "submit": "提交審批",
  "approve": "批准",
  "reject": "駁回",
  "requestInfo": "要求更多資訊",
  "requestMoreInfo": "要求更多資訊",
  "withdraw": "撤回",
  "confirmApprove": "確認批准此提案?",
  "confirmReject": "確認駁回此提案?",
  "rejectReason": "駁回原因",
  "moreInfoReason": "需要補充的資訊",
  "title": "操作"
}
```

**Proposals Detail Tabs** (zh-TW.json line 534-550):
```json
"detail": {
  "title": "提案詳情",
  "basicInfo": "基本資訊",
  "budgetDetails": "預算明細",
  "attachments": "附件",
  "comments": "討論",
  "history": "審批歷史",
  "tabs": {
    "basic": "基本資訊",
    "project": "專案資訊",
    "file": "附件",
    "meeting": "會議記錄"
  },
  "info": {
    "title": "提案資訊"
  }
}
```

**Proposals Status** (zh-TW.json line 493-500):
```json
"status": {
  "draft": "草稿",
  "pendingApproval": "待審批",
  "approved": "已批准",
  "rejected": "已駁回",
  "moreInfoRequired": "需要更多資訊",
  "rejectedMessage": "此提案已被駁回"
}
```

### ⚠️ 後續修正: INVALID_KEY 錯誤

**問題**: 使用 `rejected.message` 作為鍵名導致錯誤:
```
IntlError: INVALID_KEY: Namespace keys can not contain the character "." as this is used to express nesting.
Invalid key: rejected.message (at proposals.status)
```

**原因**: `next-intl` 不允許在鍵名中使用點號 `.`,因為點號用於表示嵌套結構。

**修正**: 將 `rejected.message` 改為 `rejectedMessage`

**修改位置**:
- zh-TW.json line 499: `"rejectedMessage": "此提案已被駁回"`
- en.json line 432: `"rejectedMessage": "This proposal has been rejected"`

**教訓**: 在 `next-intl` 翻譯鍵中:
- ✅ 正確: `rejectedMessage`, `moreInfoRequired`, `createdAt`
- ❌ 錯誤: `rejected.message`, `more.info.required`, `created.at`

點號只能用於**命名空間分隔**,不能用於**鍵名本身**。

### 修復文件清單

1. **apps/web/src/messages/zh-TW.json**
   - 修復 pagination 變數名 (line 297)
   - 新增 common.actions (line 5-7)
   - 新增 common.fields (line 10-12)
   - 新增 proposals.actions (line 480, 484, 491)
   - 新增 proposals.detail.tabs (line 542-545)
   - 新增 proposals.detail.info (line 548)
   - 修正 proposals.status.rejectedMessage (line 499)

2. **apps/web/src/messages/en.json**
   - 相同的翻譯鍵,英文版本

### 影響評估

**修復前**:
- ❌ Projects 頁面 pagination 顯示格式化錯誤
- ❌ Proposals 列表頁面顯示原始翻譯鍵
- ❌ Proposals 詳情頁面缺少大量翻譯

**修復後**:
- ✅ Projects 頁面 pagination 正確顯示「顯示 1 - 10 / 50 個專案」
- ✅ Proposals 列表頁面「新增提案」、「查看」、「編輯」正確顯示
- ✅ Proposals 詳情頁面 tabs、操作按鈕、狀態訊息完整顯示

**統計數據**:
- **新增翻譯鍵 (zh-TW)**: 15 個
- **新增翻譯鍵 (en)**: 15 個
- **修復變數名稱**: 2 個 (from→start, to→end)
- **修正鍵格式**: 1 個 (rejected.message→rejectedMessage)
- **修復時間**: 45 分鐘
- **修改檔案**: 2 個 (zh-TW.json, en.json)
- **影響頁面**: 3 個 (Projects, Proposals 列表, Proposals 詳情)

### 經驗教訓

#### 技術層面
1. **變數名稱一致性**: 翻譯字符串中的變數名必須與代碼傳遞的變數名完全匹配
2. **鍵名命名規範**: next-intl 不允許在鍵名本身使用點號,點號僅用於命名空間分隔
3. **完整測試**: 修復後應在無痕模式下測試所有受影響頁面,避免緩存干擾

#### 流程層面
1. **系統性排查**: 在完成批次修復後,應系統性測試所有頁面,避免遺漏問題
2. **快速修正**: 發現 INVALID_KEY 錯誤後立即修正,避免問題擴散
3. **文檔同步**: 及時更新文檔記錄,確保知識傳承

### 相關文檔
- 📄 **詳細報告**: `FIX-064-I18N-REMAINING-ISSUES.md`
- 📊 **進度記錄**: `I18N-PROGRESS.md` (2025-11-05 section)
- 📝 **問題記錄**: `I18N-ISSUES-LOG.md` (本文檔)

---

## FIX-063: 四大頁面系統性翻譯問題

### 問題描述
**發現時間**: 2025-11-05 00:00
**影響範圍**: Projects、Proposals、Budget Pools、Expenses 四大核心頁面
**優先級**: P0 (阻塞性問題)

在完成 FIX-062 後,測試發現四大核心頁面存在系統性翻譯鍵缺失問題,大量內容顯示為原始翻譯鍵而非正確文本。

### 問題統計

| 頁面模組 | 缺失翻譯鍵數量 | 影響範圍 |
|---------|--------------|---------|
| Projects | 42 keys | 列表頁、詳情頁、新建/編輯頁、表單組件 |
| Proposals | 35 keys | 列表頁、詳情頁、表單組件、評論系統 |
| Budget Pools | 28 keys | 列表頁、詳情頁、表單組件 |
| Expenses | 26 keys | 列表頁、詳情頁、表單組件、審批流程 |
| **總計** | **131 keys** | **四大核心業務模組** |

### 根本原因

#### 問題分層分析
1. **Layer 1 - 頁面層**: 列表頁、詳情頁、新建/編輯頁的翻譯鍵缺失
2. **Layer 2 - 組件層**: 表單組件、操作組件的翻譯鍵缺失
3. **Layer 3 - 業務邏輯層**: 狀態配置、驗證訊息、業務提示的翻譯鍵缺失

#### 系統性問題
- 在 i18n 遷移過程中,這四個模組的翻譯文件未完整建立
- 代碼已使用 `t()` 函數,但對應的翻譯鍵未添加到 `zh-TW.json` 和 `en.json`
- 缺失的翻譯鍵涵蓋了完整的 CRUD 流程

### 解決方案

#### Projects 模組 (42 keys)

**頁面翻譯** (`projects` namespace):
```json
{
  "title": "專案管理",
  "list": "專案列表",
  "detail": "專案詳情",
  "create": "新增專案",
  "edit": "編輯專案",
  "delete": "刪除專案",
  "search": "搜尋專案",
  "filter": "篩選",
  "status": {
    "all": "全部狀態",
    "planning": "規劃中",
    "active": "進行中",
    "completed": "已完成",
    "onHold": "暫停",
    "cancelled": "已取消"
  },
  "fields": {
    "name": "專案名稱",
    "code": "專案代碼",
    "budgetPool": "預算池",
    "manager": "專案經理",
    "supervisor": "主管",
    "startDate": "開始日期",
    "endDate": "結束日期",
    "description": "專案描述",
    "totalBudget": "總預算",
    "usedBudget": "已使用預算",
    "remainingBudget": "剩餘預算"
  },
  "actions": {
    "createProject": "新增專案",
    "editProject": "編輯專案",
    "deleteProject": "刪除專案",
    "viewDetails": "查看詳情",
    "exportData": "匯出資料"
  },
  "messages": {
    "createSuccess": "專案創建成功",
    "updateSuccess": "專案更新成功",
    "deleteSuccess": "專案刪除成功",
    "deleteConfirm": "確認刪除此專案?",
    "noProjects": "暫無專案"
  }
}
```

#### Proposals 模組 (35 keys)

**詳情頁翻譯** (`proposals.detail` namespace):
```json
{
  "detail": {
    "title": "提案詳情",
    "basicInfo": "基本資訊",
    "budgetDetails": "預算明細",
    "attachments": "附件",
    "comments": "討論",
    "history": "審批歷史",
    "tabs": {
      "basic": "基本資訊",
      "budget": "預算明細",
      "files": "附件",
      "comments": "討論記錄",
      "history": "審批歷史"
    },
    "fields": {
      "proposalId": "提案編號",
      "project": "所屬專案",
      "proposer": "提案人",
      "amount": "申請金額",
      "purpose": "申請用途",
      "status": "審批狀態",
      "submittedAt": "提交時間",
      "approvedAt": "批准時間"
    },
    "actions": {
      "addComment": "新增評論",
      "uploadFile": "上傳附件",
      "submitForApproval": "提交審批",
      "approve": "批准",
      "reject": "駁回",
      "requestMoreInfo": "要求更多資訊"
    }
  }
}
```

#### Budget Pools 模組 (28 keys)

**表單翻譯** (`budgetPools.form` namespace):
```json
{
  "form": {
    "title": "預算池資訊",
    "fields": {
      "name": "預算池名稱",
      "code": "預算池代碼",
      "fiscalYear": "財政年度",
      "totalAmount": "總金額",
      "usedAmount": "已使用金額",
      "remainingAmount": "剩餘金額",
      "department": "所屬部門",
      "description": "描述"
    },
    "placeholders": {
      "name": "請輸入預算池名稱",
      "code": "請輸入預算池代碼",
      "fiscalYear": "選擇財政年度",
      "totalAmount": "請輸入總金額",
      "description": "請輸入預算池描述"
    },
    "validation": {
      "nameRequired": "預算池名稱為必填項",
      "codeRequired": "預算池代碼為必填項",
      "amountRequired": "總金額為必填項",
      "amountPositive": "金額必須大於 0",
      "fiscalYearRequired": "請選擇財政年度"
    }
  }
}
```

#### Expenses 模組 (26 keys)

**審批流程翻譯** (`expenses.approval` namespace):
```json
{
  "approval": {
    "title": "費用審批",
    "status": {
      "draft": "草稿",
      "pending": "待審批",
      "approved": "已批准",
      "rejected": "已駁回",
      "paid": "已支付"
    },
    "actions": {
      "submit": "提交審批",
      "approve": "批准",
      "reject": "駁回",
      "pay": "標記為已支付"
    },
    "fields": {
      "approver": "審批人",
      "approvalDate": "審批日期",
      "approvalComment": "審批意見",
      "paymentDate": "支付日期",
      "invoiceNumber": "發票號碼"
    },
    "messages": {
      "submitSuccess": "提交審批成功",
      "approveSuccess": "費用已批准",
      "rejectSuccess": "費用已駁回",
      "confirmApprove": "確認批准此費用?",
      "confirmReject": "確認駁回此費用?"
    }
  }
}
```

### 修復文件清單

1. **apps/web/src/messages/zh-TW.json**
   - 新增 `projects` 完整 namespace (42 keys)
   - 新增 `proposals.detail` 完整區塊 (35 keys)
   - 新增 `budgetPools.form` 完整區塊 (28 keys)
   - 新增 `expenses.approval` 完整區塊 (26 keys)

2. **apps/web/src/messages/en.json**
   - 相同結構的英文翻譯 (131 keys)

### 影響評估

**修復前**:
- ❌ Projects 頁面大量顯示 `projects.title`, `projects.fields.name` 等原始鍵
- ❌ Proposals 詳情頁顯示 `proposals.detail.title`, `proposals.detail.tabs.basic` 等
- ❌ Budget Pools 表單顯示 `budgetPools.form.fields.name` 等
- ❌ Expenses 審批頁面顯示 `expenses.approval.status.pending` 等

**修復後**:
- ✅ Projects 頁面完整顯示中文:「專案管理」、「專案名稱」、「預算池」等
- ✅ Proposals 詳情頁完整顯示:「提案詳情」、「基本資訊」、「預算明細」等
- ✅ Budget Pools 表單完整顯示:「預算池名稱」、「財政年度」、「總金額」等
- ✅ Expenses 審批流程完整顯示:「費用審批」、「待審批」、「已批准」等

**統計數據**:
- **新增翻譯鍵 (zh-TW)**: 131 keys
- **新增翻譯鍵 (en)**: 131 keys
- **修復時間**: 2.5 小時
- **修改檔案**: 2 個 (zh-TW.json, en.json)
- **影響頁面**: 12 個頁面 (4 模組 × 3 頁面類型)
- **受益用戶**: 所有使用該系統的用戶

### 技術實施細節

#### 翻譯鍵命名規範
```
{namespace}.{category}.{subcategory}.{key}

範例:
- projects.fields.name          (專案欄位: 名稱)
- proposals.detail.tabs.basic   (提案詳情標籤: 基本資訊)
- budgetPools.form.validation.nameRequired  (預算池表單驗證: 名稱必填)
- expenses.approval.messages.submitSuccess  (費用審批訊息: 提交成功)
```

#### 狀態配置本地化
```typescript
// 修復前 (硬編碼)
const statusConfig = {
  draft: { label: "草稿", variant: "secondary" },
  pending: { label: "待審批", variant: "warning" }
}

// 修復後 (本地化)
const statusConfig = {
  draft: { label: t('expenses.approval.status.draft'), variant: "secondary" },
  pending: { label: t('expenses.approval.status.pending'), variant: "warning" }
}
```

### 經驗教訓

#### 技術層面
1. **系統性遷移**: 大型模組的 i18n 遷移需要系統性規劃,確保完整覆蓋
2. **分層翻譯**: 頁面層、組件層、業務邏輯層都需要完整的翻譯鍵
3. **命名空間設計**: 清晰的命名空間結構有助於維護和擴展

#### 流程層面
1. **完整測試**: 每個模組遷移後應進行完整的功能測試
2. **文檔先行**: 先設計翻譯鍵結構,再執行代碼遷移
3. **增量提交**: 按模組提交,便於問題追蹤和回滾

#### 品質保證
1. **雙語對齊**: 確保 zh-TW 和 en 翻譯鍵完全對應
2. **語義準確**: 翻譯文本應準確反映業務語義
3. **用戶驗收**: 完成後邀請實際用戶進行驗收測試

### 相關文檔
- 📄 **詳細報告**: `FIX-063-FOUR-PAGES-I18N-ISSUES.md`
- 📊 **進度記錄**: `I18N-PROGRESS.md` (2025-11-05 section)
- 📝 **問題記錄**: `I18N-ISSUES-LOG.md` (本文檔)

---

## FIX-062: Login 頁面翻譯鍵缺失

### 問題描述
**發現時間**: 2025-11-05 00:00
**影響範圍**: Login 頁面 (`apps/web/src/app/[locale]/login/page.tsx`)
**優先級**: P1 (影響用戶體驗)

Login 頁面存在多個翻譯鍵缺失,導致頁面顯示原始翻譯鍵而非正確文本:

```
auth.login.title
auth.login.subtitle
auth.login.emailPlaceholder
auth.login.passwordPlaceholder
auth.login.rememberMe
auth.login.forgotPassword
auth.login.submit
auth.login.noAccount
auth.login.signUp
```

### 根本原因

在 i18n 遷移過程中,Login 頁面的代碼已經使用 `useTranslations('auth.login')`,但對應的翻譯鍵未添加到 `zh-TW.json` 和 `en.json` 翻譯文件中。

### 解決方案

#### 新增翻譯鍵到 zh-TW.json

```json
{
  "auth": {
    "login": {
      "title": "登入",
      "subtitle": "歡迎回來!請登入您的帳戶",
      "emailPlaceholder": "請輸入電子郵件",
      "passwordPlaceholder": "請輸入密碼",
      "rememberMe": "記住我",
      "forgotPassword": "忘記密碼?",
      "submit": "登入",
      "noAccount": "還沒有帳戶?",
      "signUp": "立即註冊"
    }
  }
}
```

#### 新增翻譯鍵到 en.json

```json
{
  "auth": {
    "login": {
      "title": "Login",
      "subtitle": "Welcome back! Please login to your account",
      "emailPlaceholder": "Enter your email",
      "passwordPlaceholder": "Enter your password",
      "rememberMe": "Remember me",
      "forgotPassword": "Forgot password?",
      "submit": "Login",
      "noAccount": "Don't have an account?",
      "signUp": "Sign up"
    }
  }
}
```

### 修復文件清單

1. **apps/web/src/messages/zh-TW.json**
   - 新增 `auth.login` namespace
   - 9 個翻譯鍵

2. **apps/web/src/messages/en.json**
   - 新增 `auth.login` namespace
   - 9 個翻譯鍵

### 影響評估

**修復前**:
- ❌ Login 頁面標題顯示 `auth.login.title`
- ❌ 輸入框 placeholder 顯示 `auth.login.emailPlaceholder`
- ❌ 按鈕文字顯示 `auth.login.submit`

**修復後**:
- ✅ Login 頁面標題顯示「登入」(中文) 或 "Login" (英文)
- ✅ 輸入框 placeholder 正確顯示引導文字
- ✅ 按鈕文字正確顯示「登入」或 "Login"

**統計數據**:
- **新增翻譯鍵 (zh-TW)**: 9 keys
- **新增翻譯鍵 (en)**: 9 keys
- **修復時間**: 15 分鐘
- **修改檔案**: 2 個 (zh-TW.json, en.json)
- **影響頁面**: 1 個 (Login 頁面)

### 經驗教訓

1. **完整性檢查**: 在 i18n 遷移過程中,應確保每個頁面的翻譯鍵都完整添加
2. **測試驗證**: 遷移完成後應逐頁測試,確認無遺漏的翻譯鍵
3. **文檔同步**: 及時更新文檔記錄,避免重複問題

### 相關文檔
- 📊 **進度記錄**: `I18N-PROGRESS.md` (2025-11-05 section)
- 📝 **問題記錄**: `I18N-ISSUES-LOG.md` (本文檔)

---

## FIX-060: 英文版顯示中文內容 (重大修復)

### 問題描述
**發現時間**: 2025-11-04 00:30
**影響範圍**: 所有英文版頁面 (`/en/*`)
**優先級**: P0 (阻塞性問題)

訪問 `/en/dashboard` 時，雖然 URL 路徑正確，但頁面內容（特別是 Sidebar 導航菜單和其他組件）仍然顯示**中文**而非英文。

**症狀**:
```
URL: http://localhost:3001/en/dashboard  ✅ 正確
Sidebar: 儀表板、專案、預算提案         ❌ 顯示中文
Dashboard: 歡迎回來！每月預算           ❌ 顯示中文
預期: Dashboard, Projects, Budget Proposals ✅ 應顯示英文
```

### 診斷過程

#### 階段 1: 初步排查 (00:30-00:45)
1. ✅ 檢查 i18n 配置 (`i18n/routing.ts`, `i18n/request.ts`) → 配置正確
2. ✅ 檢查翻譯文件 `en.json` → Dashboard 區塊完整
3. ❌ 發現 `navigation.descriptions` 未翻譯
   - **FIX-060A**: 翻譯所有 navigation.descriptions (14 個描述)

#### 階段 2: Provider 層面檢查 (00:45-01:00)
4. ❌ 發現 `NextIntlClientProvider` 缺少 `locale` prop
   - **FIX-060B 部分修復**: 添加 `locale={locale}` prop
   - ✅ 連結路徑修復：`/en/*` 路徑正確生成
5. ❌ **新問題出現**: 翻譯文本仍顯示中文（矛盾現象）

#### 階段 3: 深入調查 (01:00-01:15)
6. 🔍 添加 Debug Logging 到 `Sidebar.tsx`:
   ```typescript
   const locale = useLocale()
   const t = useTranslations('navigation')
   console.log('[Sidebar Debug]', {
     locale,
     'menu.dashboard': t('menu.dashboard'),
   })
   ```

7. 🔍 **關鍵發現**（Debug 輸出）:
   ```javascript
   {
     locale: 'en',                // ✅ locale 正確
     'menu.dashboard': '儀表板',  // ❌ 但翻譯是中文
     'expected (en)': 'Dashboard'
   }
   ```

8. 🔍 **矛盾點分析**:
   - `useLocale()` 正確返回 `'en'`
   - `Link` 組件正確生成 `/en/*` 路徑
   - **但** `useTranslations()` 仍返回中文翻譯
   - **推論**: `Link` 和 `useTranslations()` 從不同來源獲取數據

#### 階段 4: 根本原因確認 (01:15)
9. ✅ **找到根源**: `getMessages()` 未傳遞 `locale` 參數

**問題代碼** (`apps/web/src/app/[locale]/layout.tsx:38`):
```typescript
const messages = await getMessages();  // ❌ 未傳遞 locale 參數
```

**根本原因**:
- `getMessages()` 在沒有參數時，使用**默認語言** (zh-TW)
- 雖然 `NextIntlClientProvider` 接收了 `locale='en'` prop
- 但 `messages` 已經是中文翻譯的內容
- 導致 Client Component 使用了錯誤的翻譯文件

### 解決方案

**修復代碼** (`apps/web/src/app/[locale]/layout.tsx:41`):
```typescript
// 🔧 FIX-060: 明確傳遞 locale 參數給 getMessages()
const messages = await getMessages({ locale });  // ✅ 正確傳遞 locale
```

**修復邏輯**:
1. `getMessages({ locale })` 根據傳入的 `locale` 參數
2. 調用 `i18n/request.ts` 中的配置邏輯
3. 動態加載正確的翻譯文件：`messages/${locale}.json`
4. 確保 `messages` 是當前語言的翻譯內容

### 關鍵技術點

#### next-intl 的 Server vs Client 機制
- **Server Component**:
  - `getMessages()` 在 Server Component 中執行
  - 必須明確傳遞 `locale` 參數
  - 返回的 `messages` 對象傳遞給 `NextIntlClientProvider`

- **Client Component**:
  - `useTranslations()` 從 `NextIntlClientProvider` 獲取 `messages`
  - `useLocale()` 從 `NextIntlClientProvider` 獲取 `locale`
  - 兩者必須匹配才能正確工作

#### Debug 策略
1. **分層驗證**: 逐層檢查 locale 值的傳遞
2. **對比測試**: 比較不同 hook 的行為（`useLocale()` vs `useTranslations()`）
3. **Console Logging**: 使用 `console.log` 確認實際值
4. **矛盾分析**: 當出現矛盾現象時，深入分析數據流

### 修復文件清單

1. **FIX-060A**: `apps/web/src/messages/en.json`
   - 翻譯 `navigation.descriptions` (14 個描述)
   - 確保所有導航相關文字都有英文版本

2. **FIX-060B**: `apps/web/src/app/[locale]/layout.tsx`
   - 添加 `NextIntlClientProvider` 的 `locale` prop
   - 修復 `getMessages()` 調用，傳遞 `{ locale }` 參數

3. **Debug工具**: `apps/web/src/components/layout/Sidebar.tsx`
   - 添加 `useLocale()` 和 Debug Logging
   - 驗證修復後可移除

### 影響評估

**修復前**:
- ❌ 所有 `/en/*` 頁面顯示中文
- ❌ 語言切換功能失效
- ❌ 國際化功能無法使用

**修復後**:
- ✅ `/en/dashboard` 完整顯示英文
- ✅ `/zh-TW/dashboard` 完整顯示中文
- ✅ Sidebar 導航菜單正確翻譯
- ✅ TopBar 組件正確翻譯
- ✅ 所有 Client Component 正確獲取對應語言的翻譯
- ✅ 語言切換功能完全正常

**統計數據**:
- **修復時間**: 1.5 小時（含診斷、調查、修復、驗證）
- **涉及文件**: 3 個文件
- **修復難度**: ⭐⭐⭐⭐ (高難度)
- **測試狀態**: ✅ 通過手動測試，兩語言完全正常

### 經驗教訓

#### 技術層面
1. **明確傳參原則**: Server Component 的所有配置都應明確傳遞參數，不依賴隱式行為
2. **Debug First 策略**: 遇到矛盾現象時，先添加 Debug Logging 確認實際值，再推測原因
3. **分層診斷方法**: 從配置層 → Provider 層 → Component 層逐層排查
4. **next-intl 機制理解**: 深入理解 Server Component 和 Client Component 的數據流

#### 流程層面
1. **問題記錄**: 詳細記錄診斷過程，形成完整的問題解決知識庫
2. **分階段修復**: 將複雜問題分解為多個階段，每階段驗證一個假設
3. **工具輔助**: 使用 Debug Logging 工具快速定位問題
4. **文檔先行**: 先創建診斷報告，再執行修復，確保思路清晰

#### 預防措施
1. **代碼審查**: 對 Server Component 的配置進行嚴格審查
2. **測試用例**: 建立 E2E 測試確保語言切換功能正常
3. **文檔補充**: 更新 i18n 實施指南，明確 `getMessages()` 的正確用法
4. **團隊分享**: 分享此次修復經驗，避免類似問題重複出現

### 相關文檔
- 📄 **診斷報告**: `FIX-060-ENGLISH-DISPLAYS-CHINESE-DIAGNOSIS.md`
- 📊 **進度記錄**: `I18N-PROGRESS.md` (2025-11-04 section)
- 📝 **問題記錄**: `I18N-ISSUES-LOG.md` (本文檔)

---

## FIX-056: Nested Links 警告

### 問題描述
**發現時間**: 2025-11-03 15:00
**影響範圍**: `apps/web/src/app/[locale]/proposals/page.tsx`

在 proposals 列表頁面中,整個卡片使用 `<Link>` 包裹,同時內部操作按鈕也使用 `<a>` 標籤,導致 React 發出警告:

```
Warning: validateDOMNesting(...): <a> cannot appear as a descendant of <a>
```

### 根本原因
HTML 規範不允許 `<a>` 標籤嵌套。React Router 的 `<Link>` 組件最終渲染為 `<a>` 標籤,因此造成嵌套衝突。

### 解決方案
採用 **onClick + stopPropagation** 模式:

**修改前**:
```tsx
<Link href={\`/proposals/\${proposal.id}\`}>
  <Card>
    {/* Card 內容 */}
    <a href={\`/proposals/\${proposal.id}\`}>查看詳情</a>
  </Card>
</Link>
```

**修改後**:
```tsx
<Card
  className="cursor-pointer hover:shadow-md transition-shadow"
  onClick={() => router.push(\`/\${locale}/proposals/\${proposal.id}\`)}
>
  {/* Card 內容 */}
  <Button
    onClick={(e) => {
      e.stopPropagation(); // 阻止事件冒泡
      router.push(\`/\${locale}/proposals/\${proposal.id}\`);
    }}
  >
    {t('common.viewDetails')}
  </Button>
</Card>
```

### 關鍵技術點
1. **事件冒泡控制**: 使用 \`e.stopPropagation()\` 防止按鈕點擊觸發卡片的 onClick
2. **Cursor 提示**: 添加 \`cursor-pointer\` 提示用戶可點擊
3. **Hover 反饋**: 添加 \`hover:shadow-md\` 提供視覺反饋
4. **語言路由**: 確保 router.push 包含 \`locale\` 參數

### 影響評估
- **優先級**: P2 (不影響功能,但影響開發體驗)
- **修復時間**: 15 分鐘
- **涉及文件**: 1 個文件
- **測試狀態**: ✅ 通過手動測試,警告消失

### 經驗教訓
1. 在 Card 組件設計時,應避免整體包裹 Link,改用 onClick 模式
2. 對於複雜交互組件,onClick + stopPropagation 比嵌套 Link 更靈活
3. 需要建立組件庫最佳實踐文檔,避免類似問題重複出現

---

## FIX-057: 大規模重複 Import

### 問題描述
**發現時間**: 2025-11-03 15:30
**影響範圍**: 39 個文件,327 個重複 import 語句

在 Batch 2 (Projects 模組) 遷移過程中,surgical-task-executor 代理錯誤地在每個文件中重複添加 \`import { useTranslations } from 'next-intl'\`,導致:

1. **TypeScript 編譯錯誤**: 重複聲明標識符
2. **應用程式無法啟動**: 阻塞開發流程
3. **代碼品質問題**: 大量冗餘代碼

### 問題統計

#### 受影響文件分佈
| 模組 | 文件數量 | 重複 import 數量 |
|-----|---------|----------------|
| Projects | 5 | 48 |
| Proposals | 7 | 89 |
| Budget Pools | 4 | 52 |
| Purchase Orders | 3 | 38 |
| Expenses | 5 | 61 |
| Vendors | 3 | 39 |
| 其他 | 12 | 100+ |
| **總計** | **39** | **327+** |

#### 重複模式範例
```typescript
// ❌ 錯誤: 同一文件中出現 8-12 次
import { useTranslations } from 'next-intl';
import { useTranslations } from 'next-intl';
import { useTranslations } from 'next-intl';
import { useTranslations } from 'next-intl';
import { useTranslations } from 'next-intl';
import { useTranslations } from 'next-intl';
import { useTranslations } from 'next-intl';
import { useTranslations } from 'next-intl';

// ✅ 正確: 只需要一次
import { useTranslations } from 'next-intl';
```

### 根本原因分析

#### 代理行為異常
Surgical-task-executor 代理在處理多文件批量操作時出現邏輯錯誤:

1. **任務循環**: 代理重複執行相同的 "添加 import" 任務
2. **缺乏檢查**: 未驗證 import 語句是否已存在
3. **批量操作風險**: 一次性處理多個文件時,錯誤被放大

#### 觸發條件
- 使用批量編輯命令處理 5+ 個文件
- 涉及模板化操作 (如統一添加 import)
- 在自動化工作流程中未設置檢查點

### 解決方案

#### 階段 1: 問題檢測工具
創建 \`scripts/check-duplicate-imports.js\` 自動化檢測工具:

```javascript
const fs = require('fs');
const path = require('path');

function checkDuplicateImports(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const importRegex = /^import\s+\{[^}]*useTranslations[^}]*\}\s+from\s+['"]next-intl['"];?\s*$/gm;
  const matches = content.match(importRegex) || [];

  if (matches.length > 1) {
    return {
      file: filePath,
      count: matches.length,
      duplicates: matches
    };
  }
  return null;
}

// 掃描 apps/web/src 目錄
const issues = scanDirectory('apps/web/src');
console.log(\`發現 \${issues.length} 個文件存在重複 import\`);
console.log(\`總共 \${issues.reduce((sum, i) => sum + i.count - 1, 0)} 個重複語句需要移除\`);
```

**檢測結果**:
- 掃描文件: 120+ 個 TypeScript/TSX 文件
- 發現問題: 39 個文件
- 重複總數: 327 個重複語句

#### 階段 2: 批量修復工具
創建 \`scripts/fix-duplicate-imports.py\` Python 批量修復工具:

```python
import re
import os

def fix_duplicate_imports(file_path):
    """移除重複的 next-intl import 語句"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 正則匹配所有 next-intl import
    import_pattern = r"^import\s+\{[^}]*useTranslations[^}]*\}\s+from\s+['\"]next-intl['\"];?\s*\n"
    matches = re.findall(import_pattern, content, re.MULTILINE)

    if len(matches) <= 1:
        return False  # 無需修復

    # 保留第一個,移除其餘
    first_import = matches[0]
    content_fixed = re.sub(import_pattern, '', content, flags=re.MULTILINE)

    # 在文件開頭添加回第一個 import (在其他 import 之後)
    lines = content_fixed.split('\n')
    import_end_index = 0
    for i, line in enumerate(lines):
        if line.strip() and not line.strip().startswith('import '):
            import_end_index = i
            break

    lines.insert(import_end_index, first_import.rstrip())
    content_fixed = '\n'.join(lines)

    # 寫回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content_fixed)

    return True

# 批量處理
fixed_count = 0
for file in issue_files:
    if fix_duplicate_imports(file):
        fixed_count += 1
        print(f"✅ 修復: {file}")

print(f"\n🎉 總共修復 {fixed_count} 個文件")
```

**修復結果**:
- 處理文件: 39 個
- 成功修復: 39 個 (100%)
- 移除重複: 327 個語句
- 執行時間: < 5 秒

#### 階段 3: 驗證與測試
```bash
# 1. 重新檢測確認無遺留問題
node scripts/check-duplicate-imports.js
# 輸出: ✅ 未發現重複 import

# 2. TypeScript 編譯驗證
pnpm typecheck
# 輸出: ✅ 無編譯錯誤

# 3. 開發服務器啟動測試
pnpm dev
# 輸出: ✅ 成功啟動於 PORT 3006
```

### 預防措施

#### 1. 代碼檢查 Pre-commit Hook
```bash
# .husky/pre-commit
node scripts/check-duplicate-imports.js
if [ $? -ne 0 ]; then
  echo "❌ 發現重複 import,請先修復"
  exit 1
fi
```

#### 2. CI/CD 流程集成
```yaml
# .github/workflows/code-quality.yml
- name: Check Duplicate Imports
  run: node scripts/check-duplicate-imports.js
```

#### 3. 開發流程規範
- **小批量操作**: 一次處理 ≤ 5 個文件
- **設置檢查點**: 每批次完成後驗證編譯
- **手動審查**: 對自動化工具生成的代碼進行人工審查

#### 4. 工具優化建議
- 為 surgical-task-executor 添加 "dry-run" 模式
- 實現操作前的代碼存在性檢查
- 提供 rollback 機制用於錯誤恢復

### 影響評估
- **優先級**: P0 (阻塞開發)
- **發現階段**: 開發階段 (未進入生產)
- **修復時間**: 30 分鐘
- **涉及文件**: 39 個文件
- **技術債務**: 已完全清除

### 經驗教訓

#### 技術層面
1. **批量操作需要額外驗證**: 自動化工具在處理多文件時必須包含去重邏輯
2. **建立安全網**: 在自動化流程中添加多層檢查機制
3. **工具可靠性測試**: 對自動化工具進行壓力測試和邊界條件測試

#### 流程層面
1. **分階段執行**: 大規模遷移應分批次進行,每批次後驗證
2. **快速反饋循環**: 及早發現問題,避免錯誤擴散
3. **建立檢測工具**: 在問題發生前建立自動化檢測機制

#### 團隊協作
1. **文檔記錄**: 詳細記錄問題和解決方案,供團隊學習
2. **知識分享**: 將修復工具集成到項目工具鏈
3. **代碼審查**: 批量操作結果必須經過 code review

### 相關文件
- 檢測工具: \`scripts/check-duplicate-imports.js\`
- 修復工具: \`scripts/fix-duplicate-imports.py\`
- 受影響文件清單: 見 \`I18N-MIGRATION-STATUS.md\` Batch 2-7 章節

### 後續行動
- [x] 創建自動化檢測工具
- [x] 批量修復所有重複 import
- [x] 驗證編譯和運行時正常
- [ ] 集成到 CI/CD 流程
- [ ] 更新開發規範文檔
- [ ] 為團隊提供培訓

---

## 最佳實踐總結

### Import 語句管理
1. **唯一性檢查**: 在添加 import 前檢查是否已存在
2. **組織規範**:
   - React 相關 import 放在最上方
   - 第三方庫 import 放在中間
   - 本地模組 import 放在最後
3. **自動化排序**: 使用 ESLint \`simple-import-sort\` 插件

### 批量操作安全
1. **小批量原則**: 每次處理 ≤ 5 個文件
2. **檢查點機制**: 每批次後執行 \`pnpm typecheck\`
3. **回滾準備**: 使用 Git 分支保護,隨時可回滾

### 工具開發規範
1. **Dry-run 模式**: 所有破壞性操作先預覽
2. **詳細日志**: 記錄操作的文件和具體更改
3. **錯誤處理**: 遇到異常停止並報告,不靜默失敗

### 代碼審查重點
1. **Import 檢查**: 確認無重複,無未使用
2. **語法驗證**: 確認編譯無錯誤
3. **功能測試**: 確認運行時行為正常

---

## 附錄

### 快速參考命令
```bash
# 檢測重複 import
node scripts/check-duplicate-imports.js

# 修復重複 import (謹慎使用)
python scripts/fix-duplicate-imports.py

# 驗證修復結果
pnpm typecheck && pnpm dev
```

### 相關資源
- Next-intl 官方文檔: https://next-intl-docs.vercel.app/
- ESLint Import 規則: https://github.com/import-js/eslint-plugin-import
- TypeScript 編譯器選項: https://www.typescriptlang.org/tsconfig

---

**文檔版本**: 1.0.0
**最後更新**: 2025-11-03 16:00
**維護者**: IT Project Management Team

---

## FIX-081 至 FIX-087: 搜索/過濾功能和語言切換問題修復

### 問題描述
**發現時間**: 2025-11-08
**影響範圍**: 多個頁面的搜索、過濾功能和語言切換器
**優先級**: P0-P1 (影響核心功能)

手動測試發現以下 7 個問題,已全部修復完成。

---

### FIX-081: Budget Proposals 搜索和狀態過濾功能缺失

**問題**: Budget Proposals 頁面缺少像 Projects 頁面一樣的搜索和過濾功能

**影響頁面**: `/proposals`

**解決方案**:
1. 在 API 添加 search 參數支持
2. 實現 PostgreSQL case-insensitive 搜索
3. 添加搜索輸入框和狀態過濾下拉框
4. 使用 useDebounce hook 優化 API 請求

**修改檔案**:
- packages/api/src/routers/budgetProposal.ts
- apps/web/src/app/[locale]/proposals/page.tsx
- apps/web/src/messages/en.json
- apps/web/src/messages/zh-TW.json

**狀態**: ✅ 已解決

---

### FIX-082: Budget Pools 年度過濾功能失效

**問題**: 年度過濾下拉框選擇後沒有反應

**根本原因**: TypeScript 類型不匹配,yearFilter 是 number 但 select 需要 string

**解決方案**: value={yearFilter?.toString() ?? ''}

**修改檔案**: apps/web/src/app/[locale]/budget-pools/page.tsx

**狀態**: ✅ 已解決

---

### FIX-083: Expenses 狀態過濾導致 400 Bad Request

**問題**: 選擇待審批狀態時出現 400 錯誤

**根本原因**: 前端使用 PendingApproval 但 API 期望 Submitted

**解決方案**: 統一使用 Submitted 狀態值

**修改檔案**: apps/web/src/app/[locale]/expenses/page.tsx

**狀態**: ✅ 已解決

---

### FIX-084: Users 頁面英文版顯示中文

**問題**: 所有 Users 相關頁面在英文版仍顯示中文內容

**影響頁面**: 列表頁、新增頁、詳情頁、編輯頁

**根本原因**: UserForm.tsx 組件有大量硬編碼中文

**解決方案**: 
- 修復 4 個頁面文件
- 完全國際化 UserForm.tsx 組件
- 添加角色翻譯函數

**修改檔案**: 6 個檔案 + 翻譯檔案

**狀態**: ✅ 已解決

---

### FIX-085: TopBar 語言切換快捷按鈕

**問題**: 缺少快速切換語言的 UI 元素

**解決方案**: 創建 LanguageSwitcher 組件

**修改檔案**: 
- apps/web/src/components/layout/LanguageSwitcher.tsx (新建)
- apps/web/src/components/layout/TopBar.tsx

**狀態**: ✅ 已解決

---

### FIX-086: 語言切換器 Hydration 錯誤

**問題**: 使用語言切換器時出現 React hydration 警告

**根本原因**: Next.js App Router 的客戶端導航嘗試重新渲染整個 layout

**解決方案**: 使用 window.location.href 進行完整頁面重新載入

**修改檔案**: apps/web/src/components/layout/LanguageSwitcher.tsx

**狀態**: ✅ 已解決

---

### FIX-087: 共用組件硬編碼中文系統性問題

**問題**: 三個已修復的頁面再次出現中文內容

**影響頁面**:
1. /en/budget-pools/[id]/edit - 預算類別標題和表單欄位
2. /en/projects/new - 創建專案按鈕
3. /en/projects/[id]/edit - 更新專案按鈕

**根本原因**: 共用組件層級存在硬編碼中文

**核心問題組件**:
1. CategoryFormRow.tsx - 硬編碼類別表單欄位
2. ProjectForm.tsx - 翻譯檔案中按鈕文字仍為中文
3. BudgetPoolForm.tsx - 標題翻譯錯誤

**為什麼問題會反覆出現**:
1. 組件復用 - 多個頁面使用相同組件
2. 動態載入 - dynamic() 組件可能未觸發測試
3. 修復策略不完整 - 只修復頁面層級未深入組件
4. 缺乏系統性檢查 - 沒有從底層到頂層審查

**正確的修復策略**:
從底層到頂層:
- Level 1: 最底層共用組件
- Level 2: 功能組件
- Level 3: 頁面組件
- Level 4: 翻譯檔案

**解決方案**:
1. CategoryFormRow.tsx 完全國際化 (7 個欄位)
2. 修復翻譯檔案錯誤 (projects.form.actions)
3. 修復 Budget Categories 標題翻譯
4. 新增完整的類別表單翻譯結構

**修改檔案**:
- apps/web/src/components/budget-pool/CategoryFormRow.tsx
- apps/web/src/messages/en.json
- apps/web/src/messages/zh-TW.json

**關鍵經驗教訓**:
1. 共用組件的 i18n 優先級最高
2. 系統性檢查要深入組件層級
3. 動態載入組件要特別注意
4. 翻譯檔案要檢查現有 key 的值
5. 兩種語言都要完整測試

**預防措施**:
- 新建表單組件時立即實施 i18n
- 代碼審查重點檢查共用組件
- 建立翻譯檔案驗證腳本
- 完整的雙語言測試覆蓋

**狀態**: ✅ 已解決

---

## 總結: FIX-081 至 FIX-087

### 修復統計

| 類型 | 數量 | 詳情 |
|-----|------|------|
| 功能缺失 | 2 | 搜索/過濾功能 |
| 類型錯誤 | 1 | Select value 類型不匹配 |
| API 不一致 | 1 | 狀態值前後端不同步 |
| 硬編碼中文 | 2 | Users 頁面、共用組件 |
| 架構問題 | 1 | Hydration 錯誤 |

### 修改檔案總覽

**總計**: 15 個檔案修改, 1 個新建

**後端 API** (1 個):
- packages/api/src/routers/budgetProposal.ts

**前端組件** (6 個):
- apps/web/src/components/budget-pool/CategoryFormRow.tsx
- apps/web/src/components/user/UserForm.tsx
- apps/web/src/components/layout/LanguageSwitcher.tsx (新建)
- apps/web/src/components/layout/TopBar.tsx

**前端頁面** (6 個):
- apps/web/src/app/[locale]/proposals/page.tsx
- apps/web/src/app/[locale]/budget-pools/page.tsx
- apps/web/src/app/[locale]/expenses/page.tsx
- apps/web/src/app/[locale]/users/*.tsx (4 個頁面)

**翻譯檔案** (2 個):
- apps/web/src/messages/en.json
- apps/web/src/messages/zh-TW.json

### 核心經驗

1. 共用組件的 i18n 優先級最高
2. 前後端 API 契約要保持一致
3. TypeScript 類型在 HTML 屬性綁定時需要轉換
4. Next.js App Router 的 hydration 要特別注意
5. 系統性問題需要系統性解決方案

### 下一步建議

1. 建立翻譯檔案驗證腳本
2. 加強共用組件的代碼審查
3. 完善雙語測試覆蓋
4. 建立 i18n 最佳實踐文檔

