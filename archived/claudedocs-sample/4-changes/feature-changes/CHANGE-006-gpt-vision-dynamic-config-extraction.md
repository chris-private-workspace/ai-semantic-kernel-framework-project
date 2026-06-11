# CHANGE-006: GPT Vision 動態配置提取與 Term 記錄

> **狀態**: 🚧 進行中 - 需要建立 PromptConfig
> **類型**: Feature Enhancement
> **影響範圍**: Epic 14/15 - PromptConfig 系統與統一處理管道
> **建立日期**: 2026-01-06
> **完成日期**: -
> **補充修復日期**: 2026-01-06
> **E2E 測試日期**: 2026-01-06
> **優先級**: High

---

## 變更摘要

完成 Step 7 (GPT Enhanced Extraction) 的實現，讓其能夠：
1. 讀取 Step 5 獲取的 PromptConfig 配置
2. 根據配置使用自定義 Prompt 調用 GPT Vision
3. 從 rawText 中提取額外欄位（如 DHL 的 Extra Charges）
4. 將額外提取的欄位記錄到 Term 系統

---

## 變更原因

### 現況問題

1. **Step 7 是空殼**
   - `performClassification()` 和 `performFullExtraction()` 都是 TODO
   - 返回空對象，沒有實際調用 GPT

2. **配置已獲取但未使用**
   - Step 5 (ConfigFetching) 已能獲取 `context.resolvedPrompt`
   - 但 Step 7 沒有讀取這個配置

3. **額外欄位無法進入 Term 系統**
   - Step 9 只讀取 `lineItems`
   - GPT 額外提取的欄位（如 extraCharges）無法記錄為 Terms

### 用戶需求

> "不同的文件格式都會有不同的數據提取策略，以 DHL 文件為例，第1頁的 Type of Service 和 Analysis of Extra Charges 等資料都是要提取的，但只有這個公司的這個文件格式才需要這樣做。"

- PromptConfig 是通用功能，用戶可在 UI 上為每間公司設定
- GPT 提取的額外欄位需要記錄為 Terms

---

## 技術設計

### 數據流

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Step 5: CONFIG_FETCHING                                                  │
│   → 根據 companyId + documentFormatId 查詢 PromptConfig                 │
│   → 三層解析 (GLOBAL → COMPANY → FORMAT)                                │
│   → 設置 context.resolvedPrompt                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ Step 6: AZURE_DI_EXTRACTION                                              │
│   → 提取標準欄位 + rawText                                              │
│   → 設置 context.extractedData.rawText                                  │
├─────────────────────────────────────────────────────────────────────────┤
│ Step 7: GPT_ENHANCED_EXTRACTION (本次修改)                               │
│   → 讀取 context.resolvedPrompt                                         │
│   → 讀取 context.extractedData.rawText                                  │
│   → 調用 gpt-vision.service 並傳入自定義 prompt                         │
│   → 設置 context.extractedData.gptExtraction = {                        │
│       extraCharges: [...],                                              │
│       typeOfService: "...",                                             │
│     }                                                                   │
├─────────────────────────────────────────────────────────────────────────┤
│ Step 9: TERM_RECORDING (本次修改)                                        │
│   → 讀取 context.extractedData.lineItems (現有)                         │
│   → 讀取 context.extractedData.gptExtraction.extraCharges (新增)        │
│   → 將 extraCharges 的 description 記錄為 Term                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Step 7 修改詳情

**文件**: `src/services/unified-processor/steps/gpt-enhanced-extraction.step.ts`

**performClassification() 實現**:
```typescript
private async performClassification(context: UnifiedProcessingContext) {
  const { input, resolvedPrompt } = context;

  // 準備圖片路徑
  const imagePath = await this.prepareImageFromBuffer(input.fileBuffer, input.fileName);

  // 構建自定義 prompt（如果有配置）
  const customPrompt = resolvedPrompt?.userPromptTemplate;

  // 調用 GPT Vision 分類
  const result = await classifyDocument(imagePath, config, {
    customPrompt,
    companyId: context.companyId,
    documentFormatId: context.documentFormatId,
  });

  return {
    extractedFields: {
      documentIssuer: result.documentIssuer,
      documentFormat: result.documentFormat,
      // 如果有額外欄位
      ...(result.extraFields || {}),
    },
    confidence: result.confidence,
    mode: 'classification' as const,
  };
}
```

**performFullExtraction() 實現**:
```typescript
private async performFullExtraction(context: UnifiedProcessingContext) {
  const { input, resolvedPrompt, extractedData } = context;

  // 準備圖片路徑
  const imagePath = await this.prepareImageFromBuffer(input.fileBuffer, input.fileName);

  // 構建自定義 prompt
  const basePrompt = resolvedPrompt?.userPromptTemplate || DEFAULT_EXTRACTION_PROMPT;

  // 如果有 rawText，可以附加到 prompt 中
  const promptWithContext = extractedData?.rawText
    ? `${basePrompt}\n\n以下是文件的原始文字：\n${extractedData.rawText}`
    : basePrompt;

  // 調用 GPT Vision 完整提取
  const result = await processImageWithVision(imagePath, config, {
    customPrompt: promptWithContext,
    companyId: context.companyId,
    documentFormatId: context.documentFormatId,
  });

  return {
    extractedFields: {
      ...result.invoiceData,
      extraCharges: result.extraCharges || [],
      typeOfService: result.typeOfService,
    },
    confidence: result.confidence,
    mode: 'full_extraction' as const,
  };
}
```

### Step 9 修改詳情

**文件**: `src/services/unified-processor/steps/term-recording.step.ts`

**新增邏輯**:
```typescript
protected async doExecute(context, flags) {
  // 現有：從 lineItems 提取
  const lineItemTerms = this.extractTermsFromLineItems(
    context.extractedData?.lineItems || []
  );

  // 新增：從 gptExtraction 提取
  const gptExtractionTerms = this.extractTermsFromGptExtraction(
    context.extractedData?.gptExtraction
  );

  // 合併所有 terms
  const allTerms = [...lineItemTerms, ...gptExtractionTerms];

  // 記錄到資料庫
  await this.recordTerms(allTerms, context);
}

/**
 * 從 GPT 額外提取的數據中提取 terms
 */
private extractTermsFromGptExtraction(
  gptExtraction?: Record<string, unknown>
): TermData[] {
  if (!gptExtraction) return [];

  const terms: TermData[] = [];

  // 處理 extraCharges
  const extraCharges = gptExtraction.extraCharges as Array<{
    description: string;
    amount?: number;
  }> | undefined;

  if (extraCharges && Array.isArray(extraCharges)) {
    for (const charge of extraCharges) {
      if (charge.description) {
        terms.push({
          rawTerm: charge.description,
          source: 'GPT_EXTRACTION',  // 標記來源
          amount: charge.amount,
        });
      }
    }
  }

  return terms;
}
```

---

## 影響的文件

### 必須修改

| 文件 | 變更類型 | 說明 |
|------|----------|------|
| `src/services/unified-processor/steps/gpt-enhanced-extraction.step.ts` | 重構 | 實現 performClassification + performFullExtraction |
| `src/services/unified-processor/steps/term-recording.step.ts` | 修改 | 新增讀取 gptExtraction 邏輯 |

### 可能修改

| 文件 | 變更類型 | 說明 |
|------|----------|------|
| `src/services/gpt-vision.service.ts` | 檢查/修改 | 確認支持 customPrompt 參數 |
| `src/types/unified-processor.ts` | 可能修改 | 確保 gptExtraction 類型定義完整 |

### 不需修改

| 文件 | 原因 |
|------|------|
| `config-fetching.step.ts` | 已完整實現 |
| `prompt-resolver.service.ts` | 已完整實現 |
| `/admin/prompt-configs/` (UI) | 已完整實現 |
| `/api/v1/prompt-configs/` (API) | 已完整實現 |

---

## 實作計劃

### Phase 1: Step 7 GPT 集成 (預估 2-3 小時)

**步驟 1.1**: 確認 GPT Vision 服務支持
- 檢查 `processImageWithVision()` 參數
- 檢查 `classifyDocument()` 參數
- 如需要，添加 customPrompt 參數支持

**步驟 1.2**: 實現 performClassification()
- 讀取 context.resolvedPrompt
- 調用 gpt-vision.service.classifyDocument()
- 返回分類結果

**步驟 1.3**: 實現 performFullExtraction()
- 讀取 context.resolvedPrompt 和 context.extractedData.rawText
- 調用 gpt-vision.service.processImageWithVision()
- 返回完整提取結果（含額外欄位）

### Phase 2: Step 9 Term 記錄 (預估 1-2 小時)

**步驟 2.1**: 新增 extractTermsFromGptExtraction()
- 處理 gptExtraction.extraCharges
- 標記 Term 來源為 GPT_EXTRACTION

**步驟 2.2**: 修改 doExecute() 合併所有 terms
- 合併 lineItemTerms + gptExtractionTerms
- 處理去重邏輯（如需要）

### Phase 3: 配置與測試 (預估 1-2 小時)

**步驟 3.1**: 啟用 enableDynamicConfig Flag
- 找到調用 UnifiedProcessor 的地方
- 設置 flags.enableDynamicConfig = true

**步驟 3.2**: 通過 UI 創建測試 PromptConfig
- 訪問 /admin/prompt-configs/new
- 創建 DHL 專屬的 FIELD_EXTRACTION 配置

**步驟 3.3**: E2E 測試
- 處理 DHL 發票
- 驗證 extraCharges 被提取
- 驗證 Terms 被記錄

---

## 驗收標準

### 功能驗收

- [ ] Step 7 能讀取 context.resolvedPrompt
- [ ] Step 7 能調用 GPT Vision 並傳入自定義 prompt
- [ ] GPT 返回的額外欄位存入 context.extractedData.gptExtraction
- [ ] Step 9 能讀取 gptExtraction 中的額外欄位
- [ ] 額外欄位的 description 被記錄為 Terms
- [ ] Terms 正確出現在 Hierarchical Terms 報告中

### 效能驗收

- [ ] GPT 調用成本在預期範圍內 (~$0.01/頁)
- [ ] 處理時間無顯著增加

### UI 驗收

- [ ] 用戶可通過 /admin/prompt-configs/ 創建配置
- [ ] 配置支持 FORMAT 級別範圍
- [ ] 配置支持 APPEND 合併策略

---

## 風險評估

| 風險 | 等級 | 緩解措施 |
|------|------|----------|
| GPT 服務不支持 customPrompt 參數 | 中 | 需要檢查並可能修改服務 |
| 圖片轉換失敗（PDF to Image） | 低 | 使用現有的 pdf-poppler 服務 |
| GPT 返回格式不穩定 | 中 | 在 prompt 中明確指定 JSON 格式 |
| Term 去重問題 | 低 | 使用現有的去重邏輯 |

---

## 相關文檔

| 文檔 | 說明 |
|------|------|
| `claudedocs/4-changes/feature-changes/CHANGE-005-unified-pipeline-step-reordering.md` | 步驟重排序變更 |
| `docs/03-stories/tech-specs/epic-14/` | Epic 14 PromptConfig 技術規格 |
| `docs/03-stories/tech-specs/epic-15/` | Epic 15 統一處理管道技術規格 |

---

## 審核記錄

| 日期 | 審核者 | 決定 | 備註 |
|------|--------|------|------|
| 2026-01-06 | User | ✅ 已批准 | 用戶確認計劃可行 |
| 2026-01-06 | User | ✅ 補充修復批准 | E2E 測試發現 DUAL_PROCESSING 模式遺漏 |

---

## 補充修復記錄 (2026-01-06)

### 問題發現

E2E 測試時發現：處理 DHL 發票後，`extractionResult` 中缺少 `gptExtraction` 欄位，導致 Term 聚合為 0。

### 根因分析

Step 7 在 `DUAL_PROCESSING` 模式下只執行 `performClassification()`，該方法僅提取 `documentIssuer` 和 `documentFormat`，沒有填充 `extraCharges` 等額外欄位。

**問題代碼** (`gpt-enhanced-extraction.step.ts:114-120`):
```typescript
// 原邏輯 ❌
if (processingMethod === UnifiedProcessingMethod.DUAL_PROCESSING) {
  gptResult = await this.performClassification(context);  // 只提取分類
} else {
  gptResult = await this.performFullExtraction(context);  // 提取完整數據
}
```

**DHL (Native PDF) 執行路徑**:
```
NATIVE_PDF → DUAL_PROCESSING → performClassification() → 只有 { documentIssuer, documentFormat }
↓
gptExtraction 缺少 extraCharges → Step 9 無法記錄 Terms → Terms 聚合 = 0
```

### 修復方案

**方案 B**：當有 `resolvedPrompt` 配置時，DUAL_PROCESSING 模式也執行 `performFullExtraction()`

**修復代碼** (`gpt-enhanced-extraction.step.ts:114-129`):
```typescript
// 修復後邏輯 ✅
if (processingMethod === UnifiedProcessingMethod.DUAL_PROCESSING) {
  // CHANGE-006 補充: 如果有動態 Prompt 配置，執行完整提取以獲取額外欄位
  if (context.resolvedPrompt?.userPromptTemplate) {
    console.log(`[Step 7] DUAL_PROCESSING with dynamic prompt: using full extraction for extra fields`);
    gptResult = await this.performFullExtraction(context);
  } else {
    // 沒有 Prompt 配置，只分類
    gptResult = await this.performClassification(context);
  }
} else {
  gptResult = await this.performFullExtraction(context);
}
```

### 影響的文件

| 文件 | 變更 |
|------|------|
| `gpt-enhanced-extraction.step.ts` | Line 114-129: 修改 DUAL_PROCESSING 執行邏輯 |

### 驗證標準

- [ ] DUAL_PROCESSING 模式下有 Prompt 配置時執行 performFullExtraction()
- [ ] gptExtraction 包含 extraCharges 欄位
- [ ] Step 9 能讀取 gptExtraction 並記錄 Terms
- [ ] Terms 聚合數量 > 0

---

## E2E 測試結果 (2026-01-06)

### 測試批次資訊

| 項目 | 值 |
|------|-----|
| 批次名稱 | CHANGE-006-UnifiedProcessor-Test-2026-01-06 |
| 批次 ID | 52dd5638-abcf-463c-ab5a-c13af102a1ec |
| 文件 | DHL_HEX240522_41293.pdf |
| 文件 ID | 71c2d926-fd28-4668-aa42-1bae7a149e16 |
| 處理狀態 | ✅ COMPLETED |
| 處理方法 | DUAL_PROCESSING |
| 處理成本 | $0.02 |

### UnifiedProcessor 執行確認

**✅ 成功使用 UnifiedProcessor**：
- `usedLegacyProcessor: false`
- 執行了完整 11 步管道

**11 步執行結果**：

| Step | 名稱 | 結果 | 耗時 |
|------|------|------|------|
| 1 | FILE_TYPE_DETECTION | ✅ success | 1ms |
| 2 | SMART_ROUTING | ✅ success | 0ms |
| 3 | ISSUER_IDENTIFICATION | ✅ success | 9,212ms |
| 4 | FORMAT_MATCHING | ❌ failed | 7ms |
| 5 | CONFIG_FETCHING | ✅ success | 165ms |
| 6 | AZURE_DI_EXTRACTION | ✅ success | 14,671ms |
| 7 | GPT_ENHANCED_EXTRACTION | ✅ success | 6,569ms |
| 8 | FIELD_MAPPING | ✅ success | 52ms |
| 9 | TERM_RECORDING | ⏭️ skipped | 0ms |
| 10 | CONFIDENCE_CALCULATION | ✅ success | 34ms |
| 11 | ROUTING_DECISION | ✅ success | 10ms |

### extraCharges 提取結果

**❌ extraCharges 未被提取**

**gptExtraction 實際內容**：
```json
{
  "documentIssuer": {
    "name": "DHL Express",
    "rawText": "DHL Express INVOICE",
    "confidence": 97,
    "identificationMethod": "LOGO"
  }
}
```

### 根本原因分析

1. **FORMAT_MATCHING 失敗** (Step 4)
   - 錯誤：`Invalid value for argument 'documentType'. Expected DocumentType.`
   - 原因：`documentType: "UNKNOWN"` 不是有效的 Prisma 枚舉值

2. **沒有 PromptConfig**
   - CONFIG_FETCHING 成功執行，但由於沒有匹配的 DocumentFormat
   - 無法獲取到有效的 PromptConfig 配置

3. **執行 performClassification() 而非 performFullExtraction()**
   - 關鍵判斷（gpt-enhanced-extraction.step.ts:118-126）：
   ```typescript
   if (context.resolvedPrompt?.userPromptTemplate) {
     gptResult = await this.performFullExtraction(context);  // ← 提取 extraCharges
   } else {
     gptResult = await this.performClassification(context);  // ← 只提取 documentIssuer
   }
   ```
   - `context.resolvedPrompt` 為空 → 執行 `performClassification()`
   - `performClassification()` 只提取 documentIssuer，不提取 extraCharges

### 結論

**代碼層面**：
- ✅ batch-processor.service.ts 已正確整合 UnifiedProcessor
- ✅ gpt-enhanced-extraction.step.ts 邏輯正確
- ✅ 11 步管道執行正常

**配置層面**：
- ❌ 缺少 DHL 的 PromptConfig 配置
- ❌ FORMAT_MATCHING 因 documentType 枚舉問題失敗

---

## 下一步行動

### 必要條件（讓 extraCharges 提取正常運作）

1. **修復 FORMAT_MATCHING 枚舉問題**
   - 確保 documentType 使用有效的 DocumentType 枚舉值
   - 或修改 FORMAT_MATCHING 步驟處理 UNKNOWN 類型

2. **建立 DHL PromptConfig**
   - 通過 UI `/admin/prompt-configs/new` 建立
   - 或通過 API/腳本建立
   - 配置內容應包含提取 extraCharges 的指令

### PromptConfig 建議配置

```json
{
  "name": "DHL Invoice Extra Charges",
  "promptType": "FIELD_EXTRACTION",
  "scope": "COMPANY",
  "companyId": "<DHL Company ID>",
  "userPromptTemplate": "從這份 DHL 發票中提取以下資訊：\n1. Analysis of Extra Charges（包含 description 和 amount）\n2. Type of Service\n\n請以 JSON 格式返回 extraCharges 數組和 typeOfService 字串。"
}
```

---

## 狀態更新

| 日期 | 狀態 | 說明 |
|------|------|------|
| 2026-01-06 | 🚧 代碼完成 | Step 7 + Step 9 代碼修改完成 |
| 2026-01-06 | 🚧 整合完成 | batch-processor 整合 UnifiedProcessor |
| 2026-01-06 | ⚠️ 待配置 | 需要建立 PromptConfig 才能提取 extraCharges |
