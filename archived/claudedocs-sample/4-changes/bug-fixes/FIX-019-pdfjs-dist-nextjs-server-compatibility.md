# FIX-019: pdfjs-dist Next.js 伺服器環境相容性問題

> **Bug ID**: FIX-019
> **日期**: 2026-01-05
> **狀態**: ✅ 已解決
> **嚴重度**: 🔴 Critical
> **發現於**: TEST-PLAN-003 E2E 測試
> **解決日期**: 2026-01-05

---

## 1. 問題描述

### 1.1 錯誤訊息

```
TypeError: intentState.renderTasks is not iterable
    at Object.cleanup (file:///C:/.../@pdfjs/display/api.mjs:...)

Cannot read properties of undefined (reading 'canvas')

Warning: Unable to load font data at: standard_fonts/LiberationSans-Regular.ttf
```

### 1.2 問題觸發位置

- **檔案**: `src/services/gpt-vision.service.ts`
- **函數**: `convertPdfToImages()`
- **操作**: 使用 `pdf-to-img` 將 PDF 頁面渲染為 PNG 圖片

### 1.3 影響範圍

| 功能 | 影響 |
|------|------|
| GPT Vision 發行者識別 | ❌ 完全無法執行 |
| GPT Vision 文件分類 | ❌ 完全無法執行 |
| DUAL_PROCESSING GPT 階段 | ❌ 失敗（但可回退至 Azure DI） |
| GPT_VISION 專用模式 | ❌ 完全失敗（無回退） |
| CHANGE-005 發行者識別 | ❌ 無法驗證 |

---

## 2. 根本原因分析

### 2.1 實際根本原因：版本不相容

調查發現問題**不是** Canvas 缺失或字型路徑問題，而是 **pdfjs-dist 版本不相容**。

#### 依賴關係

| 套件 | 需要的 pdfjs-dist 版本 |
|------|----------------------|
| `pdf-to-img@5.0.0` | `~5.4.0` (任何 5.4.x) |
| `react-pdf@10.2.0` | `5.4.296` |
| **package.json 覆蓋** | `5.3.93` ❌ |

#### package.json 覆蓋設定

```json
"overrides": {
  "pdfjs-dist": "5.3.93"  // ❌ 與 pdf-to-img 不相容
}
```

### 2.2 問題機制

1. `pdf-to-img@5.0.0` 內部使用 `pdfjs-dist`
2. `package.json` 強制覆蓋所有 `pdfjs-dist` 到 `5.3.93`
3. `5.3.x` 與 `pdf-to-img` 的 API 調用不相容
4. 導致 `intentState.renderTasks` 未正確初始化
5. 清理函數執行時發生錯誤

---

## 3. 解決方案

### 3.1 修復方式

更新 `package.json` 中的 `pdfjs-dist` 覆蓋版本：

```diff
  "overrides": {
-   "pdfjs-dist": "5.3.93"
+   "pdfjs-dist": "5.4.296"
  },
```

### 3.2 修復步驟

1. 編輯 `package.json`
2. 執行 `npm install`
3. 驗證版本更新：
   ```bash
   npm ls pdfjs-dist
   ```

### 3.3 修復後依賴狀態

```
ai-document-extraction-project@1.0.0
├─┬ pdf-to-img@5.0.0
│ └── pdfjs-dist@5.4.296 overridden ✅
└─┬ react-pdf@10.2.0
  └── pdfjs-dist@5.4.296 deduped ✅
```

---

## 4. 測試驗證

### 4.1 GPT Vision 服務測試

| 測試項目 | 結果 |
|---------|------|
| `convertPdfToImages()` 成功將 PDF 轉為 PNG | ✅ 通過 |
| 圖片品質足以進行 OCR | ✅ 通過 |
| 多頁 PDF 正確處理 | ✅ 通過 |

### 4.2 E2E 驗證測試結果

```
=== FIX-019 E2E Test Results ===
PDF Conversion: 10/10 success
Total Pages: 17
Total Image Size: 3.72 MB
Success Rate: 100.0%

🎉 FIX-019 E2E TEST PASSED!
```

### 4.3 測試檔案清單

| 檔案 | 頁數 | 結果 |
|------|------|------|
| ACCEL_HEX250274_0163D.pdf | 1 | ✅ |
| BSI_HEX250124_00238.pdf | 2 | ✅ |
| CARGO LINK_HEX240447C_0692_09649.pdf | 1 | ✅ |
| CARGO LINK_HEX240655B_09047.pdf | 1 | ✅ |
| CARGO PARTER_HEX240906,907,908_97847.pdf | 3 | ✅ |
| CARGO PARTNER_HEX240574_77626.pdf | 3 | ✅ |
| CARGO PARTNER_HEX240735,0747_13289.pdf | 3 | ✅ |
| CEVA LOGISTICS_CEX240464_39613.pdf | 1 | ✅ |
| CEVA LOGISTICS_CEX240471_41608.pdf | 1 | ✅ |
| CEVA_CEX250440_52240.pdf | 1 | ✅ |

---

## 5. 已知限制

### 5.1 字型警告

轉換過程中仍會出現字型載入警告，但**不影響功能**：

```
Warning: UnknownErrorException: Unable to load font data at: standard_fonts/LiberationSans-Regular.ttf
```

這是 pdfjs-dist 在 Node.js 環境中的已知限制，可在未來透過配置標準字型路徑來消除。

---

## 6. 修改的檔案

| 檔案 | 變更 |
|------|------|
| `package.json` | 更新 `overrides.pdfjs-dist` 從 `5.3.93` 到 `5.4.296` |

---

## 7. 相關資源

| 資源 | 連結 |
|------|------|
| pdf-to-img npm | https://www.npmjs.com/package/pdf-to-img |
| react-pdf releases | https://github.com/wojtekmaj/react-pdf/releases |
| pdfjs-dist npm | https://www.npmjs.com/package/pdfjs-dist |

---

## 8. 更新記錄

| 日期 | 狀態 | 說明 |
|------|------|------|
| 2026-01-05 | 🚧 調查中 | 問題識別，初步認為是 Canvas/字型問題 |
| 2026-01-05 | 🔍 深入調查 | 發現實際是 pdfjs-dist 版本覆蓋不相容 |
| 2026-01-05 | ✅ 已解決 | 更新版本覆蓋至 5.4.296，E2E 測試 100% 通過 |

---

**建立日期**: 2026-01-05
**解決日期**: 2026-01-05
**負責人**: Claude AI Assistant
