# CHANGE-001: Native PDF 雙重處理架構增強

> **狀態**: ✅ 已完成
> **建立日期**: 2025-12-27
> **完成日期**: 2025-12-27
> **影響範圍**: Story 0.8, Story 0.9, batch-processor.service.ts, processing-router.service.ts, gpt-vision.service.ts
> **優先級**: 高

---

## 變更摘要

### 問題發現

在審查 Story 0.8（文件發行者識別）和 Story 0.9（文件格式術語重組）的實作時，發現以下架構缺口：

| 處理類型 | 當前行為 | 問題 |
|---------|---------|------|
| **Native PDF** | 僅使用 Azure DI | ❌ 無法取得 `documentIssuer` 和 `documentFormat` |
| **Scanned PDF / Image** | 使用 GPT Vision | ✅ 完整支援 |

### 根本原因

1. **Azure DI 輸出結構**：
   - `invoiceData` (vendorName, customerName, lineItems, amounts)
   - `rawText`, `confidence`, `pageCount`
   - ❌ 不包含 `documentIssuer` 或 `documentFormat`

2. **GPT Vision 輸出結構**：
   - `documentIssuer` (name, identificationMethod: LOGO/HEADER/LETTERHEAD/FOOTER)
   - `documentFormat` (documentType, documentSubtype)
   - ✅ 包含完整分類資訊

3. **Story 0.8/0.9 的依賴**：
   - `document-issuer.service.ts` 第 139-142 行需要 `extractionResult.documentIssuer`
   - `document-format.service.ts` 需要 `extractionResult.documentFormat`
   - Native PDF 使用 Azure DI 時，這些欄位為空，導致功能失效

---

## 解決方案：Option C（用戶確認）

### 設計決策

**Native PDF 採用雙重處理**：
1. **第一階段 - GPT Vision（分類）**：
   - 發行者識別（LOGO/HEADER 優先）
   - 文件格式分類（Invoice/DN/CN + Ocean/Air/Land）

2. **第二階段 - Azure DI（數據）**：
   - 文件內容提取（vendorName, customerName, lineItems）
   - 費用術語提取（lineItems → terms）

**Scanned PDF / Image 維持現狀**：
- GPT Vision 處理所有任務（OCR + 分類 + 提取）

### 處理流程圖

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         文件上傳入口                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Step 1: 文件類型檢測 (file-detection.service.ts)                        │
│  - 分析 MIME type, 內容結構                                              │
│  - 輸出: NATIVE_PDF / SCANNED_PDF / IMAGE                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
        ┌───────────────────┐           ┌───────────────────┐
        │    Native PDF     │           │ Scanned PDF/Image │
        └───────────────────┘           └───────────────────┘
                    │                               │
                    ▼                               │
┌─────────────────────────────────────┐             │
│  Step 2A: GPT Vision (分類模式)     │             │
│  - 發行者識別 (LOGO/HEADER)         │             │
│  - 文件格式分類                      │             │
│  - 成本: ~$0.01/頁                  │             │
└─────────────────────────────────────┘             │
                    │                               │
                    ▼                               │
┌─────────────────────────────────────┐             │
│  Step 2B: Azure DI (數據模式)       │             │
│  - 發票欄位提取                      │             │
│  - 術語數據提取                      │             │
│  - 成本: ~$0.01/頁                  │             │
└─────────────────────────────────────┘             │
                    │                               │
                    │                               ▼
                    │               ┌─────────────────────────────────────┐
                    │               │  Step 2: GPT Vision (完整模式)       │
                    │               │  - OCR 文字識別                      │
                    │               │  - 發行者識別                        │
                    │               │  - 文件格式分類                      │
                    │               │  - 術語數據提取                      │
                    │               │  - 成本: ~$0.03/頁                  │
                    │               └─────────────────────────────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Step 3: 發行者識別 (document-issuer.service.ts) - Story 0.8            │
│  - 從 documentIssuer 提取公司資訊                                        │
│  - 匹配或建立 Company 記錄                                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Step 4: 文件格式分類 (document-format.service.ts) - Story 0.9          │
│  - 識別文件類型 (Invoice/DN/CN/Statement)                               │
│  - 識別子類型 (Ocean/Air/Land/Courier)                                  │
│  - 建立 Company → Format → Terms 三層聚合結構                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Step 5: 三層映射處理 (mapping.service.ts)                              │
│  - Tier 1: Universal Mapping (70-80%)                                   │
│  - Tier 2: Company-Specific Override (10-15%)                          │
│  - Tier 3: LLM Classification (5-10%)                                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Step 6: 信心度路由 (routing.service.ts)                                │
│  - ≥90%: AUTO_APPROVE                                                   │
│  - 70-89%: QUICK_REVIEW                                                │
│  - <70%: FULL_REVIEW                                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 成本估算

| 文件類型 | 處理方式 | 成本/頁 |
|---------|---------|--------|
| Native PDF | GPT Vision (分類) + Azure DI (數據) | ~$0.02 |
| Scanned PDF / Image | GPT Vision (完整) | ~$0.03 |

---

## 需要修改的文件

### 1. `src/services/processing-router.service.ts`

```typescript
// 當前實作
export function determineProcessingMethod(
  detectedType: DetectedFileType
): ProcessingMethod {
  switch (detectedType) {
    case DetectedFileType.NATIVE_PDF:
      return ProcessingMethod.AZURE_DI  // ← 問題點
    // ...
  }
}

// 建議修改：新增雙重處理模式
export function determineProcessingMethod(
  detectedType: DetectedFileType
): ProcessingMethod {
  switch (detectedType) {
    case DetectedFileType.NATIVE_PDF:
      return ProcessingMethod.DUAL_PROCESSING  // GPT Vision + Azure DI
    case DetectedFileType.SCANNED_PDF:
    case DetectedFileType.IMAGE:
      return ProcessingMethod.GPT_VISION
  }
}
```

### 2. `src/services/batch-processor.service.ts`

新增雙重處理邏輯：

```typescript
async function processDualMode(filePath: string): Promise<ExtractionResult> {
  // 第一階段：GPT Vision 分類
  const classificationResult = await gptVisionService.classifyDocument(filePath)

  // 第二階段：Azure DI 數據提取
  const dataResult = await azureDIService.extractInvoiceData(filePath)

  // 合併結果
  return {
    ...dataResult,
    documentIssuer: classificationResult.documentIssuer,
    documentFormat: classificationResult.documentFormat,
  }
}
```

### 3. `src/services/gpt-vision.service.ts`

新增分類專用方法（減少 token 使用）：

```typescript
async classifyDocument(filePath: string): Promise<ClassificationResult> {
  // 使用簡化的 prompt，只要求分類資訊
  // 不要求完整的數據提取
}
```

---

## 驗收標準

- [x] Native PDF 能正確識別文件發行者（LOGO/HEADER）
- [x] Native PDF 能正確分類文件格式（類型 + 子類型）
- [x] Native PDF 的 lineItems 能正確提取
- [x] 處理成本維持在 $0.02/頁以內
- [x] Story 0.8 和 0.9 功能對所有文件類型均有效

---

## 相關文檔

- [Story 0.8: 文件發行者識別](../../docs/04-implementation/stories/0-8-document-issuer-identification.md)
- [Story 0.9: 文件格式術語重組](../../docs/04-implementation/stories/0-9-document-format-term-reorganization.md)
- [Azure DI Service](../../src/services/azure-di.service.ts)
- [GPT Vision Service](../../src/services/gpt-vision.service.ts)
- [Processing Router](../../src/services/processing-router.service.ts)

---

## 變更歷史

| 日期 | 變更 | 作者 |
|------|------|------|
| 2025-12-27 | 初始設計文檔建立 | AI Assistant |
| 2025-12-27 | 實作完成：DUAL_PROCESSING enum、classifyDocument()、executeAIProcessing() | AI Assistant |

---

**用戶確認**: 2025-12-27
**確認內容**: 選擇 Option C（Native PDF 雙重處理）

---

## 實作摘要

### 已修改的文件

| 文件 | 變更內容 |
|------|---------|
| `prisma/schema.prisma` | 新增 `DUAL_PROCESSING` 至 `ProcessingMethod` enum |
| `src/services/processing-router.service.ts` | 修改路由邏輯：`NATIVE_PDF` → `DUAL_PROCESSING` |
| `src/services/gpt-vision.service.ts` | 新增 `ClassificationResult` interface、`CLASSIFICATION_ONLY_PROMPT`、`classifyDocument()` 函數 |
| `src/services/batch-processor.service.ts` | 新增 `DUAL_PROCESSING` 分支處理邏輯（Phase 1: GPT Vision 分類、Phase 2: Azure DI 數據提取） |

### 關鍵實作細節

1. **classifyDocument() 函數**：
   - 使用輕量 prompt，僅請求 `documentIssuer` 和 `documentFormat`
   - 使用 `detail: 'low'` 減少 token 消耗
   - `maxTokens: 1024`（相比完整處理的 4096）
   - 預估成本：~$0.01/頁

2. **DUAL_PROCESSING 模式流程**：
   - Phase 1: 調用 `classifyDocument()` 取得分類資訊
   - Phase 2: 調用 `processPdfWithAzureDI()` 取得發票數據
   - 合併結果：Azure DI 數據 + GPT Vision 分類資訊
