# FIX-009: Zustand Selector 在 Next.js 15 中導致的無限循環錯誤

> **狀態**: ✅ 已修復並驗證
> **發現日期**: 2026-01-03
> **修復日期**: 2026-01-03
> **影響範圍**: 文件預覽測試頁面 Store (Story 13-6)

---

## 問題描述

### 症狀
- 修復 FIX-008 後，頁面可載入但 Console 顯示錯誤
- 錯誤訊息: `Maximum update depth exceeded`
- 伴隨警告: `The result of getServerSnapshot should be cached to avoid an infinite loop`
- React 陷入無限重新渲染循環

### 錯誤訊息
```
Warning: Maximum update depth exceeded. This can happen when a component calls
setState inside useEffect, but useEffect either doesn't have a dependency array,
or one of the dependencies changes on every render.

The result of getServerSnapshot should be cached to avoid an infinite loop.
Something may be wrong with this component's useSyncExternalStore usage.
```

### 根本原因
`document-preview-test-store.ts` 中的 selector hooks 返回新建立的物件：

```typescript
// ❌ 問題代碼 - 每次 render 都返回新物件引用
export const useFileState = () =>
  useDocumentPreviewTestStore((state) => ({
    currentFile: state.currentFile,
    processingStatus: state.processingStatus,
    processingProgress: state.processingProgress,
    error: state.error,
  }));
```

在 Next.js 15 中，React 使用 `useSyncExternalStore` 實作 Zustand。由於 selector 每次都返回新物件（`{ ... }` 是新引用），React 認為狀態已改變並觸發重新渲染，但重新渲染後又產生新物件，導致無限循環。

---

## 影響分析

| 影響項目 | 說明 |
|---------|------|
| **功能影響** | 頁面可載入但有錯誤，可能導致效能問題或閃爍 |
| **用戶影響** | Console 錯誤訊息，潛在的頁面不穩定 |
| **範圍** | 所有使用 selector hooks 的組件（4 個 hooks） |

---

## 修復方案

### 使用 `useShallow` 進行淺比較

**修改位置**: `src/stores/document-preview-test-store.ts`

```typescript
// ✅ 修復後 - 使用 useShallow 進行淺比較
import { useShallow } from 'zustand/react/shallow';

export const useFileState = () =>
  useDocumentPreviewTestStore(
    useShallow((state) => ({
      currentFile: state.currentFile,
      processingStatus: state.processingStatus,
      processingProgress: state.processingProgress,
      error: state.error,
    }))
  );

export const useFieldsState = () =>
  useDocumentPreviewTestStore(
    useShallow((state) => ({
      extractedFields: state.extractedFields,
      selectedFieldId: state.selectedFieldId,
      fieldFilters: state.fieldFilters,
    }))
  );

export const useMappingState = () =>
  useDocumentPreviewTestStore(
    useShallow((state) => ({
      currentScope: state.currentScope,
      selectedCompanyId: state.selectedCompanyId,
      selectedFormatId: state.selectedFormatId,
      mappingRules: state.mappingRules,
    }))
  );

export const usePdfState = () =>
  useDocumentPreviewTestStore(
    useShallow((state) => ({
      currentPage: state.currentPage,
      totalPages: state.totalPages,
      zoomLevel: state.zoomLevel,
    }))
  );
```

### `useShallow` 工作原理
`useShallow` 是 Zustand 提供的淺比較 hook，它會比較 selector 返回物件的每個屬性值：
- 如果所有屬性值都相同（使用 `===` 比較），則認為狀態未改變
- 只有當至少一個屬性值不同時，才認為狀態改變並觸發重新渲染

---

## 修改的檔案

| 檔案 | 變更類型 | 說明 |
|------|---------|------|
| `src/stores/document-preview-test-store.ts` | 修改 | 添加 `useShallow` import，包裝所有 4 個 selector hooks |

---

## 代碼變更詳情

### 添加 Import
```typescript
// 第 27 行
import { useShallow } from 'zustand/react/shallow';
```

### 添加 JSDoc 文檔
```typescript
/**
 * @bugfix FIX-009 (2026-01-03)
 *   修復 Zustand selectors 在 Next.js 15 中導致的 "Maximum update depth exceeded" 錯誤。
 *   Selector hooks 返回的物件在每次 render 時都是新引用，導致 React useSyncExternalStore 無限循環。
 *   解決方案：使用 useShallow 進行淺比較，避免不必要的重新渲染。
 */
```

---

## 測試驗證

### 驗證步驟
1. 啟動開發伺服器 `npm run dev`
2. 導航到 `/admin/document-preview-test`
3. 開啟瀏覽器 Console
4. 確認無 `Maximum update depth exceeded` 錯誤
5. 確認無 `getServerSnapshot should be cached` 警告

### 驗證結果
- ✅ 頁面載入成功 (HTTP 200)
- ✅ Console 無錯誤或警告
- ✅ 三個面板正常渲染
- ✅ 頁面互動正常（無閃爍或卡頓）

---

## 經驗教訓

### 重要認知
1. **Zustand Selector 陷阱**: 在 Next.js 15 + React 18/19 中，Zustand 使用 `useSyncExternalStore`，對 selector 返回值的引用敏感度更高
2. **物件引用問題**: `{ a: state.a, b: state.b }` 每次都是新物件，即使內容相同
3. **useShallow 是標準解法**: Zustand 官方提供 `useShallow` 專門解決此問題

### 何時使用 `useShallow`
- ✅ Selector 返回物件 `{ ... }`
- ✅ Selector 返回陣列 `[ ... ]`
- ❌ Selector 返回基本類型（string, number, boolean）不需要

### 替代方案
如果不想使用 `useShallow`，也可以：
1. **分開多個 selectors**: 每個 selector 只返回一個基本值
2. **使用 `subscribeWithSelector`**: 自定義訂閱邏輯
3. **使用 `useMemo`**: 手動緩存 selector 結果

---

## 相關文件

- `src/stores/document-preview-test-store.ts` - 修復的 Store 文件
- `FIX-008-pdfjs-dist-ssr-barrel-export.md` - 先行修復的相關 Bug
- [Zustand 官方文檔 - Extracting state slices](https://docs.pmnd.rs/zustand/recipes/recipes#extracting-state-slices)

---

**修復者**: AI 助手
**驗證者**: Development Team
