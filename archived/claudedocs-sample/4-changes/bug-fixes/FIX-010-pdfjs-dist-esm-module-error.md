# FIX-010: pdfjs-dist v5 ESM Module Error

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

## 根本原因

pdfjs-dist v5.4.x 的 ESM 模組與 webpack 的 eval-based source maps 不兼容。這是一個已知的上游 bug：

- [mozilla/pdf.js#20478](https://github.com/mozilla/pdf.js/issues/20478)
- [mozilla/pdf.js#20435](https://github.com/mozilla/pdf.js/issues/20435)
- [wojtekmaj/react-pdf#1813](https://github.com/wojtekmaj/react-pdf/issues/1813)

當 webpack 使用 `eval-*` 類型的 devtool（如 `eval-cheap-module-source-map`）時，pdfjs-dist v5.4.x 的 ESM 模組初始化會失敗。

## 解決方案

### 方案選擇

| 方案 | 說明 | 選擇 |
|------|------|------|
| A | 修改 webpack devtool 設定 | ❌ Next.js 會自動覆蓋回預設值 |
| B | 降級 pdfjs-dist 到 5.3.93 | ✅ 使用 npm overrides |
| C | 等待上游修復 | ❌ 不確定時程 |

### 實施步驟

1. **添加 npm overrides** (`package.json`)
   ```json
   {
     "overrides": {
       "pdfjs-dist": "5.3.93"
     }
   }
   ```

2. **重新安裝依賴**
   ```bash
   npm install
   ```

3. **驗證版本**
   ```bash
   npm ls pdfjs-dist
   # 應顯示 5.3.93 overridden
   ```

## 修改的文件

| 文件 | 變更 |
|------|------|
| `package.json` | 添加 `overrides.pdfjs-dist: "5.3.93"` |
| `next.config.ts` | 保留 devtool 設定作為文檔（雖然會被 Next.js 覆蓋） |

## 驗證結果

### 修復前
- PDF 上傳後立即報錯 `Object.defineProperty called on non-object`
- PDF 無法渲染

### 修復後
- Console 顯示: `[PDFViewer] Worker initialized with version: 5.3.93`
- PDF 正確渲染並可翻頁、縮放
- 測試文件: `DHL_HEX0185_88348.pdf` (2 頁) ✅

## 技術債務

| 項目 | 說明 |
|------|------|
| 依賴版本鎖定 | pdfjs-dist 被鎖定在 5.3.93，需要定期檢查上游是否修復 |
| 預計修復 | 當 pdfjs-dist v5.5+ 或 react-pdf v10.3+ 發布修復後移除 override |

## 後續追蹤

- [ ] 關注 [mozilla/pdf.js#20478](https://github.com/mozilla/pdf.js/issues/20478) 進度
- [ ] pdfjs-dist v5.5 發布後測試移除 override
- [ ] react-pdf v10.3 發布後測試更新

---
**修復日期**: 2026-01-03
**修復者**: Claude Code
**相關 Story**: Epic 13 - 文件預覽與欄位映射
