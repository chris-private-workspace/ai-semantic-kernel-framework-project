# FIX-026: pdfjs-dist v5 ESM 模組問題 - 最終解決方案

## 問題描述

### 錯誤訊息
```
TypeError: Object.defineProperty called on non-object
  at (app-pages-browser)/./node_modules/pdfjs-dist/build/pdf.mjs
```

### 影響範圍
- `/admin/document-preview-test` 頁面的 PDF 預覽功能
- 所有使用 `react-pdf` 組件的頁面

### 觸發條件
- 上傳任何 PDF 文件時
- PDFViewer 組件載入 pdfjs-dist ESM 模組時

### 背景
此問題之前在 FIX-010 中嘗試使用 `npm overrides` 降級到 `pdfjs-dist 5.3.93` 解決，但該方案失敗（API 不兼容）。

## 根本原因

pdfjs-dist v5.4.x 的 ESM 模組與 webpack 的 eval-based source maps 不兼容。這是一個已知的上游 bug：

- [mozilla/pdf.js#20478](https://github.com/mozilla/pdf.js/issues/20478)
- [mozilla/pdf.js#20435](https://github.com/mozilla/pdf.js/issues/20435)
- [wojtekmaj/react-pdf#1813](https://github.com/wojtekmaj/react-pdf/issues/1813)

當 webpack 使用 `eval-*` 類型的 devtool 時，pdfjs-dist v5.4.x 的 ESM 模組初始化會失敗。

## 嘗試過的方案

| # | 方案 | 結果 | 原因 |
|---|------|------|------|
| 1 | npm overrides 降級到 pdfjs-dist 5.3.93 | ❌ 失敗 | API 不兼容，react-pdf v10 需要 v5.4 API |
| 2 | webpack alias 重定向到 legacy build | ❌ 失敗 | alias 沒有生效 |
| 3 | 降級到 react-pdf v9 + pdfjs-dist v4 | ✅ 成功 | 穩定版本組合，ESM 問題不存在 |

## 最終解決方案

### 版本降級策略

降級到 `react-pdf v9` 搭配 `pdfjs-dist v4`，避開 v5.4.x 的 ESM 問題：

| 套件 | 修改前 | 修改後 |
|------|--------|--------|
| react-pdf | 10.2.0 | 9.2.1 |
| pdfjs-dist | 5.4.296 (via overrides) | 4.10.38 (由 react-pdf 管理) |

### 實施步驟

1. **修改 package.json**
   ```json
   {
     "dependencies": {
       "pdfjs-dist": "^4.10.38",
       "react-pdf": "^9.2.1"
     }
   }
   ```
   - 移除 `overrides` 配置

2. **簡化 next.config.ts**
   ```typescript
   webpack: (config, { isServer }) => {
     // Client-side: disable canvas (not available in browser)
     if (!isServer) {
       config.resolve.alias.canvas = false
     }

     // Mark native modules and PDF libraries as external for server
     if (isServer) {
       config.externals = config.externals || []
       config.externals.push({
         canvas: 'commonjs canvas',
         'pdf-to-img': 'commonjs pdf-to-img',
         'pdfjs-dist': 'commonjs pdfjs-dist',
       })
     }

     return config
   }
   ```

3. **更新 PDFViewer.tsx Worker 配置**
   ```typescript
   // react-pdf v9 + pdfjs-dist v4 的 worker 配置
   pdfjs.GlobalWorkerOptions.workerSrc =
     `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`
   ```

4. **重新安裝依賴**
   ```bash
   npm install
   ```

## 修改的文件

| 文件 | 變更 |
|------|------|
| `package.json` | 移除 `overrides`，降級 react-pdf 到 9.2.1，pdfjs-dist 到 4.10.38 |
| `next.config.ts` | 簡化 webpack 配置，移除不再需要的 legacy build alias |
| `src/components/features/document-preview/PDFViewer.tsx` | 更新版本說明註釋，維持 CDN worker 配置 |

## 驗證結果

### 修復前
- PDF 上傳後立即報錯 `Object.defineProperty called on non-object`
- PDF 無法渲染

### 修復後
- Console 顯示: `[PDFViewer] Worker initialized with version: 4.10.38`
- PDF 正確渲染並可翻頁、縮放
- 測試頁面: `/admin/document-preview-test` ✅

## 技術債務

| 項目 | 說明 |
|------|------|
| 版本鎖定 | react-pdf 被鎖定在 v9，無法使用 v10 新功能 |
| 預計修復 | 當 pdfjs-dist v5.5+ 修復 ESM 問題後，可升級回 react-pdf v10 |

## 後續追蹤

- [ ] 關注 [mozilla/pdf.js#20478](https://github.com/mozilla/pdf.js/issues/20478) 進度
- [ ] pdfjs-dist v5.5 發布後測試是否修復 ESM 問題
- [ ] react-pdf v10.3+ 發布後測試是否可以升級

## 相關 Bug Fix

- **FIX-008**: pdfjs-dist SSR barrel export 問題
- **FIX-010**: pdfjs-dist v5 ESM module error（舊方案，已被本 FIX 取代）
- **FIX-019**: pdfjs-dist Next.js server compatibility

---
**修復日期**: 2026-01-12
**修復者**: Claude Code
**相關 Story**: Epic 13 - 文件預覽與欄位映射
