# FIX-021: PDF 解析失敗 - pdf is not a function

> **Bug ID**: FIX-021
> **發現日期**: 2025-12-24
> **修復日期**: 2025-12-24
> **狀態**: ✅ 已修復
> **發現方式**: 功能測試 - 歷史文件數據初始化

## 問題描述
上傳 PDF 文件時，類型檢測失敗，錯誤訊息：`PDF 解析失敗: pdf is not a function`

## 影響範圍
- 歷史文件上傳功能
- PDF 類型檢測（NATIVE_PDF / SCANNED_PDF 判斷）
- Epic 0 - Story 0.1, 0.2

## 根本原因分析

### 第一層問題
`src/services/file-detection.service.ts` 使用 CommonJS require 語法導入 `pdf-parse`：

```typescript
const pdf = require('pdf-parse')
```

在 Next.js 15 的 ESM 環境中，這種導入方式導致模組解析問題。

### 第二層問題（修復後發現）
嘗試使用 pdf-parse v2.x 後，發現其 ESM 模組與 Next.js webpack 不兼容：

```
Module not found: Can't resolve 'pdfjs-dist/legacy/build/pdf.mjs'
```

### 第三層問題（降級後發現）
降級到 pdf-parse v1.x 後，發現其 index.js 會在 require 時嘗試讀取測試文件：

```
PDF 解析失敗: ENOENT: no such file or directory, open '...\test\data\05-versions-space.pdf'
```

## 修復過程

### 嘗試 1：動態導入 pdf-parse v2.x（失敗）
```typescript
const pdfParse = await import('pdf-parse')
const pdf = pdfParse.default || pdfParse
```
**結果**：webpack 無法解析 pdfjs-dist ESM 模組

### 嘗試 2：配置 webpack 別名（失敗）
在 `next.config.ts` 添加複雜的 webpack 配置
**結果**：仍然無法解析 .mjs 文件

### 嘗試 3：降級到 pdf-parse v1.1.1（部分成功）
```bash
npm install pdf-parse@1.1.1 --save
```
```typescript
const pdfParse = require('pdf-parse')
const data = await pdfParse(buffer)
```
**結果**：ENOENT 錯誤，index.js 嘗試讀取測試文件

### 嘗試 4：直接導入核心模組（成功 ✅）
```typescript
// 直接導入 pdf-parse 的核心模組，避開 index.js 中的測試文件讀取
const pdfParse = require('pdf-parse/lib/pdf-parse')
const data = await pdfParse(buffer)
```
**結果**：成功！PDF 類型檢測正常工作

## 最終修復

### 修改文件
`src/services/file-detection.service.ts`

### 修改內容
```typescript
private static async detectPdfType(
  buffer: Buffer,
  mimeType: string,
  fileSize: number
): Promise<FileDetectionResult> {
  try {
    // 直接導入 pdf-parse 的核心模組，避開 index.js 中的測試文件讀取
    // pdf-parse 的 index.js 會在載入時嘗試讀取測試文件，導致 ENOENT 錯誤
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const pdfParse = require('pdf-parse/lib/pdf-parse')

    // 使用 pdf-parse v1.x 的函數式 API
    const data = await pdfParse(buffer)

    const textLength = data.text?.length || 0
    const pageCount = data.numpages || 1
    // ...
  } catch (error) {
    // ...
  }
}
```

### 依賴版本
```json
{
  "pdf-parse": "1.1.1"
}
```

## 驗證結果

上傳 3 個測試 PDF 文件：
| 文件名 | 類型 | 狀態 |
|--------|------|------|
| DSV_CEX240686_15534.pdf | 原生 PDF | ✅ 已檢測 |
| CEVA_CEX250440_52240.pdf | 原生 PDF | ✅ 已檢測 |
| DHL_HEX240522_41293.pdf | 原生 PDF | ✅ 已檢測 |

## 經驗教訓

1. **pdf-parse v2.x 與 Next.js 不兼容**：ESM 模組解析問題
2. **pdf-parse v1.x index.js 有測試代碼**：需要直接導入 `lib/pdf-parse`
3. **CommonJS require 在特定路徑下可正常工作**：使用 `require('pdf-parse/lib/pdf-parse')`

## 優先級
**高** - 影響核心文件上傳功能
