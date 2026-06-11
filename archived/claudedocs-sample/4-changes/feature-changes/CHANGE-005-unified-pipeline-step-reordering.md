# CHANGE-005: 統一處理管道步驟重新排序

> **狀態**: 📋 規劃中
> **類型**: Architecture Refactoring
> **影響範圍**: Epic 15 - 統一 3 層機制到日常處理流程
> **建立日期**: 2026-01-05
> **優先級**: High

---

## 變更摘要

重新排序 UnifiedDocumentProcessor 的 11 步處理管道，將 **發行者識別 (ISSUER_IDENTIFICATION)** 移至 **Azure DI 提取** 之前執行，使系統能夠：

1. 先識別文件發行者和格式
2. 獲取對應的動態配置（包含 QueryFields 定義）
3. 根據配置決定 Azure DI 調用方式（基礎 vs 自定義 QueryFields）

---

## 變更原因

### 現況問題

1. **Azure DI 調用時機不佳**
   - 目前 Azure DI 在 Step 3 最先執行
   - 此時尚未識別發行者、格式，無法獲取配置
   - 無法使用 QueryFields API 提取自定義欄位

2. **配置獲取順序顛倒**
   - Config Fetching 在 Azure DI 之後（Step 6）
   - 即使配置中有定義 QueryFields，也無法在 Azure DI 調用時使用

3. **需要多次調用 Azure DI**（用戶明確拒絕）
   - 若要支援 QueryFields，需先調用基礎 Azure DI，再調用帶 QueryFields 的 Azure DI
   - 成本翻倍、效能下降
   - **用戶明確表示不接受此方案**

### 用戶需求

> "如果文件沒有建立/設定配置 Query Fields, 才直接使用基礎 Azure DI 提取"

- 單次 Azure DI 調用
- 根據配置存在與否決定調用方式
- 發行者識別應該每份文件都先執行

---

## 技術設計

### 步驟順序對照

| 順序 | 原始設計 (Epic 15) | 提議的新設計 |
|------|-------------------|-------------|
| Step 1 | FILE_TYPE_DETECTION | FILE_TYPE_DETECTION |
| Step 2 | SMART_ROUTING | SMART_ROUTING |
| **Step 3** | **AZURE_DI_EXTRACTION** | **ISSUER_IDENTIFICATION** ← GPT classifyDocument |
| **Step 4** | ISSUER_IDENTIFICATION | **FORMAT_MATCHING** |
| **Step 5** | FORMAT_MATCHING | **CONFIG_FETCHING** |
| **Step 6** | CONFIG_FETCHING | **AZURE_DI_EXTRACTION** ← 可含 QueryFields |
| Step 7 | GPT_ENHANCED_EXTRACTION | GPT_ENHANCED_EXTRACTION |
| Step 8 | FIELD_MAPPING | FIELD_MAPPING |
| Step 9 | TERM_RECORDING | TERM_RECORDING |
| Step 10 | CONFIDENCE_CALCULATION | CONFIDENCE_CALCULATION |
| Step 11 | ROUTING_DECISION | ROUTING_DECISION |

### 新流程圖

```
┌─────────────────────────────────────────────────────────────────────┐
│ Step 1: FILE_TYPE_DETECTION                                         │
│   → 檢測文件類型 (Native PDF / Scanned PDF / Image)                 │
├─────────────────────────────────────────────────────────────────────┤
│ Step 2: SMART_ROUTING                                               │
│   → 決定處理方法 (DUAL_PROCESSING / GPT_VISION_ONLY / AZURE_DI_ONLY)│
├─────────────────────────────────────────────────────────────────────┤
│ Step 3: ISSUER_IDENTIFICATION (新位置)                              │
│   → GPT classifyDocument() 輕量分類 (~$0.01/page)                   │
│   → 識別發行者 + 匹配/創建公司                                      │
├─────────────────────────────────────────────────────────────────────┤
│ Step 4: FORMAT_MATCHING (新位置)                                    │
│   → 匹配或創建 DocumentFormat                                       │
│   → 需要 companyId 從 Step 3 獲得                                   │
├─────────────────────────────────────────────────────────────────────┤
│ Step 5: CONFIG_FETCHING (新位置)                                    │
│   → 根據 companyId + documentFormatId 獲取配置                      │
│   → 包含 Prompt 配置和 QueryFields 定義                             │
├─────────────────────────────────────────────────────────────────────┤
│ Step 6: AZURE_DI_EXTRACTION (新位置)                                │
│   → IF config.queryFields 存在:                                     │
│       → 調用 Azure DI 帶 QueryFields                                │
│   → ELSE:                                                           │
│       → 調用基礎 Azure DI (prebuilt-invoice)                        │
├─────────────────────────────────────────────────────────────────────┤
│ Step 7: GPT_ENHANCED_EXTRACTION                                     │
│   → 條件觸發 (Scanned/Image, 低信心度, 缺失欄位, 有 Prompt 配置)   │
├─────────────────────────────────────────────────────────────────────┤
│ Step 8-11: 後續處理步驟 (不變)                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 發行者識別調整

目前的 `issuer-identification.step.ts` 依賴 Azure DI 提取結果：

```typescript
// 現有邏輯 (Line 126-152)
private buildExtractionResultForIssuer(context): ExtractionResultForIssuer {
  const extractedData = context.extractedData ?? {};
  // 從 Azure DI 結果中獲取 invoiceData
  return {
    invoiceData: extractedData.invoiceData,
    // ...
  };
}
```

**需要修改為**：直接使用 GPT `classifyDocument()` 進行輕量分類

```typescript
// 新邏輯 (基於實際的 classifyDocument 方法簽名)
protected async doExecute(context, flags): Promise<StepResult> {
  // 直接調用 GPT classifyDocument()
  // 方法簽名: classifyDocument(filePath, config?, options?)
  const classificationResult = await gptVisionService.classifyDocument(
    context.input.filePath,
    { /* GPTVisionConfig */ },
    { promptConfigId: context.promptConfigId }  // 支援動態 Prompt
  );

  if (!classificationResult.success) {
    return this.createErrorResult('Classification failed');
  }

  // 更新上下文 (基於實際的 ClassificationResult 輸出結構)
  context.extractedData = {
    ...context.extractedData,
    documentIssuer: {
      name: classificationResult.documentIssuer.name,           // ← 正確路徑
      identificationMethod: classificationResult.documentIssuer.identificationMethod,
      confidence: classificationResult.documentIssuer.confidence,
      rawText: classificationResult.documentIssuer.rawText,
    },
    documentFormat: classificationResult.documentFormat,
  };

  // 調用公司匹配邏輯
  const matchResult = await this.issuerIdentifierAdapter.identifyAndMatch(context);
  // ...
}
```

**classifyDocument() 實際輸出結構**：
```typescript
interface ClassificationResult {
  success: boolean;
  documentIssuer: {
    name: string;                    // 發行者名稱
    identificationMethod: 'HEADER' | 'LOGO' | 'CONTENT';
    confidence: number;              // 0-1
    rawText?: string;
  };
  documentFormat: {
    name: string;
    category: string;
  };
  pageCount: number;
  error?: string;
}
```

### Azure DI 條件調用

修改 `azure-di-extraction.step.ts` 支援 QueryFields：

```typescript
// 新邏輯概念
protected async doExecute(context, flags): Promise<StepResult> {
  // 檢查是否有 QueryFields 配置
  const queryFields = context.mappingConfig?.queryFields ?? null;

  // 決定調用方式
  if (queryFields && queryFields.length > 0) {
    // 使用 QueryFields API
    return await this.callAzureDIWithQueryFields(context, queryFields);
  } else {
    // 使用基礎 prebuilt-invoice
    return await this.callAzureDIBasic(context);
  }
}
```

---

## 影響的文件

### 必須修改

| 文件 | 變更類型 | 說明 |
|------|----------|------|
| `src/constants/processing-steps.ts` | 修改 | 更新 `PROCESSING_STEP_ORDER` 和 `DEFAULT_STEP_CONFIGS` |
| `src/services/unified-processor/steps/issuer-identification.step.ts` | 重構 | 改為直接調用 GPT classifyDocument，不依賴 Azure DI 結果 |
| `src/services/unified-processor/adapters/issuer-identifier-adapter.ts` | 修改 | 調整輸入類型以接收 classifyDocument() 的輸出格式 |
| `src/services/azure-di.service.ts` | 修改 | 新增 QueryFields 參數支援 |
| `src/services/unified-processor/steps/azure-di-extraction.step.ts` | 修改 | 支援條件性 QueryFields 調用，從 context.mappingConfig 讀取 |
| `src/services/unified-processor/steps/config-fetching.step.ts` | 修改 | 確保解析 QueryFields 配置 |

### 可能影響

| 文件 | 變更類型 | 說明 |
|------|----------|------|
| `src/services/unified-processor/factory/step-factory.ts` | 檢查 | 確認步驟順序變更無副作用 |
| `src/types/unified-processor.ts` | 可能修改 | 新增 QueryFields 相關類型 |
| `src/types/dynamic-config.ts` | 可能修改 | 確保 QueryFields 類型定義完整 |
| `src/services/gpt-vision.service.ts` | 檢查 | 確認 `classifyDocument()` 方法可用 |

### 不需修改

| 文件 | 原因 |
|------|------|
| `file-type-detection.step.ts` | Step 1-2 順序不變 |
| `smart-routing.step.ts` | Step 1-2 順序不變 |
| `format-matching.step.ts` | 邏輯不變，只是位置移動 |
| `gpt-enhanced-extraction.step.ts` | 邏輯不變 |
| `field-mapping.step.ts` | 邏輯不變 |
| `term-recording.step.ts` | 邏輯不變 |
| `confidence-calculation.step.ts` | 邏輯不變 |
| `routing-decision.step.ts` | 邏輯不變 |

---

## 實作計劃

### Phase 1: 類型和常數更新 (預估 1-2 小時)

**步驟 1.1**: 更新 `src/types/unified-processor.ts`
- 確保 `UnifiedProcessingContext` 支援 QueryFields
- 確保步驟間資料傳遞正確

**步驟 1.2**: 更新 `src/constants/processing-steps.ts`
- 修改 `PROCESSING_STEP_ORDER`
- 更新 `DEFAULT_STEP_CONFIGS` 順序

### Phase 2: 發行者識別重構 (預估 2-3 小時)

**步驟 2.1**: 修改 `issuer-identification.step.ts`
- 移除對 Azure DI 結果的依賴
- 實作直接調用 GPT `classifyDocument()`
- 保留公司匹配邏輯

**步驟 2.2**: 修改 `issuer-identifier-adapter.ts`
- 調整輸入類型以匹配 `ClassificationResult` 結構
- 確保 `documentIssuer.name` 路徑正確

**步驟 2.3**: 確認 `gpt-vision.service.ts`
- 確保 `classifyDocument()` 可獨立調用
- 確認輸出格式符合需求

### Phase 3: Azure DI 條件調用 (預估 2-3 小時)

**步驟 3.1**: 修改 `azure-di.service.ts`
- 新增 `queryFields` 參數支援
- 實作 `AnalyzeDocumentOptions.queryFields` 調用

**步驟 3.2**: 修改 `azure-di-extraction.step.ts`
- 從 `context.mappingConfig.queryFields` 讀取配置
- 條件性傳遞 QueryFields 給 service

**步驟 3.3**: 確認 `config-fetching.step.ts`
- 確保 QueryFields 配置正確解析
- 確保配置傳遞到上下文

### Phase 4: 整合測試 (預估 1-2 小時)

**步驟 4.1**: 更新現有單元測試
- 測試新的步驟順序
- 測試 classifyDocument() 獨立調用

**步驟 4.2**: 新增整合測試案例
- 測試無 QueryFields 配置時的基礎流程
- 測試有 QueryFields 配置時的進階流程

**步驟 4.3**: E2E 測試驗證
- 完整文件處理流程測試
- 驗證單次 Azure DI 調用

---

## 實作順序總覽

```
1. processing-steps.ts          ← 調整步驟順序
2. issuer-identification.step.ts ← 調用 classifyDocument()
3. issuer-identifier-adapter.ts  ← 調整輸入類型
4. azure-di.service.ts           ← 新增 QueryFields 支援
5. azure-di-extraction.step.ts   ← 讀取配置並傳遞
6. 單元測試更新
7. E2E 測試驗證
```

---

## 風險評估

| 風險 | 等級 | 緩解措施 |
|------|------|----------|
| 步驟間資料依賴破壞 | 中 | 詳細分析各步驟的輸入/輸出依賴關係 |
| classifyDocument() 輸出與 adapter 類型不相容 | 中 | 需調整 issuer-identifier-adapter 的輸入類型定義 |
| GPT classifyDocument 成本增加 | 低 | 輕量分類 ~$0.01/page，影響可控 |
| QueryFields API 兼容性 | 低 | Azure DI 官方支援，已有文檔 |
| Azure DI QueryFields 調用失敗 | 低 | 使用 try-catch 降級到基礎 prebuilt-invoice 調用 |
| 現有流程回歸問題 | 中 | 保留 Feature Flag，可隨時回退 |
| 測試覆蓋不足 | 低 | 新增專用測試案例 |

---

## 驗收標準

### 功能驗收

- [ ] 發行者識別在 Azure DI 之前執行
- [ ] 無 QueryFields 配置時，使用基礎 Azure DI
- [ ] 有 QueryFields 配置時，Azure DI 調用包含 QueryFields
- [ ] 單次 Azure DI 調用（不重複調用）
- [ ] 現有功能無回歸

### 效能驗收

- [ ] 處理時間無顯著增加（< 10%）
- [ ] GPT classifyDocument 成本在預期範圍內

### 測試驗收

- [ ] 單元測試通過
- [ ] 整合測試通過
- [ ] E2E 測試通過

---

## 相關文檔

| 文檔 | 說明 |
|------|------|
| `claudedocs/1-planning/epics/epic-15/epic-15-overview.md` | Epic 15 原始設計 |
| `docs/04-implementation/tech-specs/epic-15-unified-processing/tech-spec-story-15-1.md` | Story 15.1 技術規格 |
| `CHANGE-004-azure-di-boundingbox-extraction.md` | 相關的 BoundingBox 提取變更 |

---

## 審核記錄

| 日期 | 審核者 | 決定 | 備註 |
|------|--------|------|------|
| 2026-01-05 | - | 📋 待審核 | 初稿建立 |
| 2026-01-05 | AI 助手 | ✅ 程式碼分析完成 | 深入分析 classifyDocument()、azure-di.service.ts 等核心文件，更新實作計劃和風險評估 |

---

## 附錄：現有程式碼參考

### 現有步驟順序 (processing-steps.ts:220-232)

```typescript
export const PROCESSING_STEP_ORDER: ProcessingStep[] = [
  ProcessingStep.FILE_TYPE_DETECTION,
  ProcessingStep.SMART_ROUTING,
  ProcessingStep.AZURE_DI_EXTRACTION,        // 目前 Step 3
  ProcessingStep.ISSUER_IDENTIFICATION,      // 目前 Step 4
  ProcessingStep.FORMAT_MATCHING,            // 目前 Step 5
  ProcessingStep.CONFIG_FETCHING,            // 目前 Step 6
  ProcessingStep.GPT_ENHANCED_EXTRACTION,
  ProcessingStep.FIELD_MAPPING,
  ProcessingStep.TERM_RECORDING,
  ProcessingStep.CONFIDENCE_CALCULATION,
  ProcessingStep.ROUTING_DECISION,
];
```

### 提議的新步驟順序

```typescript
export const PROCESSING_STEP_ORDER: ProcessingStep[] = [
  ProcessingStep.FILE_TYPE_DETECTION,
  ProcessingStep.SMART_ROUTING,
  ProcessingStep.ISSUER_IDENTIFICATION,      // 新 Step 3 ← GPT classifyDocument
  ProcessingStep.FORMAT_MATCHING,            // 新 Step 4
  ProcessingStep.CONFIG_FETCHING,            // 新 Step 5 ← 獲取 QueryFields 配置
  ProcessingStep.AZURE_DI_EXTRACTION,        // 新 Step 6 ← 條件性 QueryFields
  ProcessingStep.GPT_ENHANCED_EXTRACTION,
  ProcessingStep.FIELD_MAPPING,
  ProcessingStep.TERM_RECORDING,
  ProcessingStep.CONFIDENCE_CALCULATION,
  ProcessingStep.ROUTING_DECISION,
];
```
