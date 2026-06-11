# FIX-008: pdfjs-dist 模組在 SSR 環境中的 Object.defineProperty 錯誤

> **狀態**: ✅ 已修復並驗證
> **發現日期**: 2026-01-03
> **修復日期**: 2026-01-03
> **影響範圍**: 文件預覽測試頁面 (Story 13-6)

---

## 問題描述

### 症狀
- 導航到 `/admin/document-preview-test` 頁面時，頁面顯示 500 錯誤
- Console 顯示 `TypeError: Object.defineProperty called on non-object`
- 錯誤發生在 `pdfjs-dist/legacy/build/pdf.mjs` 模組評估階段

### 錯誤堆疊
```
⨯ TypeError: Object.defineProperty called on non-object
    at Object.defineProperty (<anonymous>)
    at (ssr)/./node_modules/pdfjs-dist/legacy/build/pdf.mjs
    at eval (webpack-internal:///(ssr)/./src/components/features/document-preview/PDFViewer.tsx:9:67)
    at (ssr)/./src/components/features/document-preview/PDFViewer.tsx
    at eval (webpack-internal:///(ssr)/./src/components/features/document-preview/index.ts:18:68)
```

### 根本原因
`pdfjs-dist` 模組在設計上只能在瀏覽器環境中執行。當透過 barrel export (`index.ts`) 導出 `PDFViewer` 組件時，即使實際只使用 `DynamicPDFViewer`（已設定 `ssr: false`），JavaScript 模組系統仍會評估整個 `index.ts` 文件，導致 `PDFViewer.tsx` 被載入，進而觸發 `pdfjs-dist` 初始化。

**問題代碼路徑**:
```
1. 頁面 import from '@/components/features/document-preview'
2. → 評估 index.ts (barrel export)
3. → 評估 PDFViewer.tsx (因為 index.ts export 它)
4. → 評估 pdfjs-dist (在 SSR 環境失敗)
```

---

## 影響分析

| 影響項目 | 說明 |
|---------|------|
| **功能影響** | 文件預覽測試頁面無法載入 |
| **用戶影響** | 管理員無法使用文件預覽功能 |
| **範圍** | Story 13-6 新增的頁面 |

---

## 修復方案

### 1. 移除 PDFViewer 從 barrel export (`index.ts`)

**修改位置**: `src/components/features/document-preview/index.ts`

```typescript
// ❌ 移除的 export（會導致 SSR 評估錯誤）
export { PDFViewer } from './PDFViewer'

// ✅ 僅保留 SSR 安全的 DynamicPDFViewer
export { DynamicPDFViewer } from './DynamicPDFViewer'
```

### 2. 增加 Worker 初始化保護 (`PDFViewer.tsx`)

**修改位置**: `src/components/features/document-preview/PDFViewer.tsx`

```typescript
// 新增初始化標記和函數
let workerInitialized = false

function initializePdfWorker(): void {
  if (workerInitialized || typeof window === 'undefined') {
    return
  }

  try {
    pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/legacy/build/pdf.worker.min.mjs`
    workerInitialized = true
  } catch (error) {
    console.error('[PDFViewer] Failed to initialize PDF.js worker:', error)
  }
}

// 在組件中使用 useEffect 初始化
React.useEffect(() => {
  initializePdfWorker()
}, [])
```

### 3. 更新文檔註釋

在 `index.ts` 頂部添加說明：
```typescript
/**
 * @bugfix FIX-008 (2026-01-03)
 *   移除 PDFViewer 的 barrel export 以避免 SSR 錯誤。
 *
 * @note
 *   PDFViewer 不在此處 export，因為 pdfjs-dist 無法在 SSR 環境中執行。
 *   請使用 DynamicPDFViewer，它會在客戶端動態載入 PDFViewer。
 *   如需直接使用 PDFViewer，請從 './PDFViewer' 直接 import（僅限客戶端組件）。
 */
```

---

## 修改的檔案

| 檔案 | 變更類型 | 說明 |
|------|---------|------|
| `src/components/features/document-preview/index.ts` | 修改 | 移除 PDFViewer export，添加文檔註釋 |
| `src/components/features/document-preview/PDFViewer.tsx` | 修改 | 添加 worker 初始化保護和 bugfix 標籤 |

---

## 測試驗證

### 驗證步驟
1. 啟動開發伺服器 `npm run dev`
2. 導航到 `/admin/document-preview-test`
3. 確認頁面正常載入，無 500 錯誤
4. 確認三個面板（提取欄位、PDF 預覽、映射配置）正常顯示

### 驗證結果
- ✅ 頁面載入成功 (HTTP 200)
- ✅ 無 SSR 錯誤
- ✅ PDF 預覽區域正常顯示空白狀態
- ✅ Console 無相關錯誤

---

## 經驗教訓

### 重要認知
1. **Barrel Export 的隱患**: 在 Next.js App Router 中，barrel export 會導致所有 exported 模組被評估，即使只 import 其中一個
2. **SSR 不兼容庫的處理**: 對於瀏覽器專用庫（如 pdfjs-dist），不應透過 barrel export 導出，應使用 `next/dynamic` 包裝
3. **模組評估時機**: JavaScript 模組在 import 時就會被評估，而非等到實際使用時

### 建議做法
- 對於瀏覽器專用組件，創建 `Dynamic*` 包裝組件並僅導出該包裝
- 原始組件可保留在目錄中，但不透過 index.ts 導出
- 在文檔中明確說明使用方式

---

## 相關文件

- `src/components/features/document-preview/DynamicPDFViewer.tsx` - SSR 安全的動態版本
- `FIX-009-zustand-selector-infinite-loop.md` - 連帶發現的另一個 Bug

---

**修復者**: AI 助手
**驗證者**: Development Team
