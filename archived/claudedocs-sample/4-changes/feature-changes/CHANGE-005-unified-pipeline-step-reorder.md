# CHANGE-005: 統一管道步驟重排序

> **日期**: 2026-01-05
> **狀態**: ✅ 已完成
> **Epic**: Epic 15 - 統一 3 層機制到日常處理流程

---

## 變更摘要

將統一處理管道的步驟順序從「先提取 → 再識別」調整為「先識別 → 再依配置提取」，實現更智能的處理流程。

## 核心變更

### 步驟順序調整

| 調整前 | 調整後 | 說明 |
|--------|--------|------|
| Step 3: Azure DI 提取 | Step 3: 發行者識別 | ISSUER_IDENTIFICATION 提前 |
| Step 4: 發行者識別 | Step 4: 格式匹配 | FORMAT_MATCHING 提前 |
| Step 5: 格式匹配 | Step 5: 配置獲取 | CONFIG_FETCHING 提前 |
| Step 6: 配置獲取 | Step 6: Azure DI 提取 | AZURE_DI_EXTRACTION 移後 |

### 新處理流程

```
Step 1: FILE_TYPE_DETECTION     - 偵測文件類型（PDF/Image）
Step 2: SMART_ROUTING           - 智能路由決策
Step 3: ISSUER_IDENTIFICATION   - 使用 GPT Vision classifyDocument() 識別發行者
Step 4: FORMAT_MATCHING         - 依發行者匹配文件格式
Step 5: CONFIG_FETCHING         - 獲取動態配置（Prompt/Mapping）
Step 6: AZURE_DI_EXTRACTION     - 使用 Azure DI 提取結構化數據
Step 7: GPT_ENHANCED_EXTRACTION - GPT 增強提取（可選）
Step 8: FIELD_MAPPING           - 欄位映射轉換
Step 9: TERM_RECORDING          - 術語記錄
Step 10: CONFIDENCE_CALCULATION - 信心度計算
Step 11: ROUTING_DECISION       - 路由決策
```

## 修改文件列表

### Phase 1: 類型與配置

| 文件 | 變更內容 |
|------|----------|
| `src/types/unified-processor.ts` | ProcessingStep enum 順序調整 |
| `src/constants/processing-steps.ts` | PROCESSING_STEP_ORDER 數組順序調整 |

### Phase 2: 發行者識別步驟

| 文件 | 變更內容 |
|------|----------|
| `src/services/unified-processor/steps/issuer-identification.step.ts` | 改用 `classifyDocument()` 輕量識別，不調用完整 Azure DI |
| `src/services/unified-processor/adapters/issuer-identifier-adapter.ts` | 修正 `issuerIdentification` → `documentIssuer` 欄位映射 |

### Phase 3: 其他步驟調整

| 文件 | 變更內容 |
|------|----------|
| `src/services/unified-processor/steps/azure-di-extraction.step.ts` | Step 3 → Step 6，整合真實 Azure DI 服務 |
| `src/services/unified-processor/steps/config-fetching.step.ts` | Step 6 → Step 5 |

## 技術細節

### GPT Vision classifyDocument()
- **用途**: 輕量級文件分類，僅識別發行者和格式
- **成本**: 比完整 Azure DI 便宜
- **輸出**: `{ documentIssuer, documentFormat, pageCount }`

### Azure DI 整合
- **服務**: `processPdfWithAzureDI(pdfPath, config)`
- **模型**: prebuilt-invoice
- **臨時文件處理**: Buffer → 臨時文件 → API 調用 → 清理

### 類型修正
- `issuerIdentification` 欄位映射到 `documentIssuer`
- `name` 欄位空值檢查（確保必填欄位有值）

## 驗證結果

- ✅ TypeScript 類型檢查：0 errors
- ✅ ESLint：0 errors（4 console warnings 為正常日誌）
- ✅ 步驟順序配置正確
- ✅ 欄位映射修復完成

## 相關文檔

- [Tech Spec: Story 15.1](../../docs/04-implementation/tech-specs/epic-15/)
- [Epic 15 Overview](../1-planning/epics/epic-15/)
- [FIX-005: issuer-identifier 欄位映射](../bug-fixes/FIX-005-issuer-identifier-field-mapping.md)

---

**完成日期**: 2026-01-05
**開發者**: AI Assistant (Claude)
