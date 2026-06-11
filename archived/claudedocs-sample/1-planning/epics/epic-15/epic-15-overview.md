# Epic 15: 統一 3 層機制到日常處理流程

**Status:** 🚧 規劃中

---

## Epic 概覽

### 目標

將 Epic 0（歷史數據初始化）中開發的 3 層機制統一整合到日常文件處理流程中，確保每日上傳的發票也能享受相同的智能識別和分類功能。

### 問題陳述

目前系統存在兩條獨立的處理流程：

**歷史數據初始化流程 (Epic 0)**:
1. ✅ 文件類型檢測（Native PDF / Scanned）
2. ✅ 智能處理路由（雙重處理 / GPT Vision）
3. ✅ 發行者識別（Logo/Header → Company）
4. ✅ 文件格式分類（DocumentFormat）
5. ✅ 術語聚合（Term Aggregation）
6. ✅ AI 術語驗證（GPT-5.2）

**日常處理流程 (Epic 2-3)**:
1. ✅ 文件上傳
2. ⚠️ Azure DI 提取（固定配置）
3. ⚠️ 固定欄位映射
4. ✅ 人工審核
5. ❌ 無發行者識別
6. ❌ 無格式分類
7. ❌ 無術語聚合

這導致：
- 日常上傳的發票無法受益於 Company/Format 特定配置
- 新術語無法自動學習
- 系統知識庫不會隨日常使用而增長

### 解決方案

統一兩條流程，使日常處理也包含：
1. **發行者識別**: 識別文件來自哪家公司
2. **格式匹配/創建**: 匹配現有格式或創建新格式
3. **動態配置應用**: 使用 Company/Format 特定的映射和 Prompt
4. **持續學習**: 新術語自動記錄和建議

### 統一架構

```
┌─────────────────────────────────────────────────────────────────┐
│                    統一文件處理流程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐                                               │
│  │ 文件上傳      │                                               │
│  │ (單個/批次)   │                                               │
│  └──────┬───────┘                                               │
│         ↓                                                       │
│  ┌──────────────┐                                               │
│  │ 文件類型檢測  │ ← 第 1 層: Native PDF / Scanned              │
│  └──────┬───────┘                                               │
│         ↓                                                       │
│  ┌──────────────┐                                               │
│  │ 智能處理路由  │ ← 雙重處理 / GPT Vision Only                 │
│  └──────┬───────┘                                               │
│         ↓                                                       │
│  ┌──────────────┐                                               │
│  │ Azure DI 提取 │ ← 基礎欄位提取                               │
│  └──────┬───────┘                                               │
│         ↓                                                       │
│  ┌──────────────┐                                               │
│  │ 發行者識別    │ ← 第 2 層: Logo/Header → Company             │
│  │ + 格式匹配    │ ← 第 2 層: DocumentFormat                    │
│  └──────┬───────┘                                               │
│         ↓                                                       │
│  ┌──────────────┐                                               │
│  │ 動態配置獲取  │ ← Epic 13: 欄位映射                          │
│  │              │ ← Epic 14: Prompt 配置                        │
│  └──────┬───────┘                                               │
│         ↓                                                       │
│  ┌──────────────┐                                               │
│  │ GPT 增強提取  │ ← 使用動態 Prompt                            │
│  └──────┬───────┘                                               │
│         ↓                                                       │
│  ┌──────────────┐                                               │
│  │ 欄位映射轉換  │ ← 使用動態映射配置                           │
│  └──────┬───────┘                                               │
│         ↓                                                       │
│  ┌──────────────┐                                               │
│  │ 術語記錄      │ ← 第 3 層: 記錄新術語到 Format               │
│  └──────┬───────┘                                               │
│         ↓                                                       │
│  ┌──────────────┐                                               │
│  │ 信心度計算    │ ← 綜合評估                                   │
│  └──────┬───────┘                                               │
│         ↓                                                       │
│  ┌──────────────┐                                               │
│  │ 路由決策      │ ← AUTO_APPROVE / QUICK_REVIEW / FULL_REVIEW │
│  └──────────────┘                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3 層機制回顧

| 層級 | 名稱 | 功能 | 來源 Epic |
|------|------|------|-----------|
| 第 1 層 | 文件類型檢測 | 區分 Native PDF / Scanned PDF / Image | Epic 0 |
| 第 2 層 | 發行者/格式識別 | 識別 Company + DocumentFormat | Epic 0 |
| 第 3 層 | 術語聚合 | 記錄術語到 Format，建立知識庫 | Epic 0 |

---

## Stories 列表

| Story ID | 標題 | 估點 | 狀態 |
|----------|------|------|------|
| 15-1 | 處理流程重構 - 統一入口 | 5 | backlog |
| 15-2 | 發行者識別整合 | 5 | backlog |
| 15-3 | 格式匹配與動態配置 | 5 | backlog |
| 15-4 | 持續術語學習 | 5 | backlog |
| 15-5 | 信心度計算增強 | 5 | backlog |

**總估點**: 25 點

---

## Story 摘要

### Story 15-1: 處理流程重構 - 統一入口

重構現有的處理流程，建立統一的文件處理管道。

**關鍵產出**:
- `UnifiedDocumentProcessor` 服務
- 文件類型檢測整合
- 智能路由邏輯
- 功能開關（漸進式啟用）

### Story 15-2: 發行者識別整合

將發行者識別功能從歷史數據流程移植到日常流程。

**關鍵產出**:
- 修改 `batch-processor.service.ts` 調用發行者識別
- 公司匹配/自動創建邏輯
- 識別結果儲存

### Story 15-3: 格式匹配與動態配置

實現文件格式匹配和動態配置獲取。

**關鍵產出**:
- 格式匹配服務（基於發行者 + 特徵）
- 動態獲取 Epic 13 的欄位映射配置
- 動態獲取 Epic 14 的 Prompt 配置

### Story 15-4: 持續術語學習

實現日常處理中的術語記錄和學習。

**關鍵產出**:
- 新術語檢測（與現有術語庫比對）
- 術語自動記錄到 Format
- 術語建議機制（人工審核時顯示）

### Story 15-5: 信心度計算增強

增強信心度計算，納入更多因素。

**關鍵產出**:
- 多維度信心度計算
- 配置匹配程度影響
- 歷史準確率權重
- 路由決策優化

---

## 技術設計

### 統一處理器

```typescript
// src/services/unified-document-processor.service.ts

/**
 * @fileoverview 統一文件處理服務
 * @description
 *   整合所有文件處理步驟的統一入口
 *   包含 3 層機制和動態配置應用
 *
 * @module src/services/unified-document-processor
 * @since Epic 15 - Story 15.1
 */

interface ProcessingContext {
  fileId: string;
  batchId?: string;

  // 第 1 層: 文件類型
  fileType: 'NATIVE_PDF' | 'SCANNED_PDF' | 'IMAGE';
  processingMethod: 'DUAL_PROCESSING' | 'GPT_VISION';

  // 第 2 層: 發行者/格式
  identifiedCompanyId?: string;
  documentFormatId?: string;
  issuerConfidence?: number;
  formatConfidence?: number;

  // 動態配置
  fieldMappingConfigId?: string;
  promptConfigId?: string;

  // 提取結果
  azureDIResult?: AzureDIResult;
  gptVisionResult?: GPTVisionResult;
  mappedData?: Record<string, unknown>;

  // 術語
  extractedTerms?: string[];
  newTerms?: string[];

  // 信心度
  overallConfidence?: number;
  routingDecision?: 'AUTO_APPROVE' | 'QUICK_REVIEW' | 'FULL_REVIEW';
}

class UnifiedDocumentProcessor {
  private pipeline: ProcessingStep[] = [
    new FileTypeDetectionStep(),
    new ProcessingRouterStep(),
    new AzureDIExtractionStep(),
    new IssuerIdentificationStep(),
    new FormatMatchingStep(),
    new ConfigResolutionStep(),
    new GPTEnhancedExtractionStep(),
    new FieldMappingStep(),
    new TermRecordingStep(),
    new ConfidenceCalculationStep(),
    new RoutingDecisionStep(),
  ];

  async process(fileId: string): Promise<ProcessingResult> {
    const context: ProcessingContext = { fileId };

    for (const step of this.pipeline) {
      try {
        await step.execute(context);
      } catch (error) {
        // 錯誤處理和降級策略
        await this.handleStepError(step, context, error);
      }
    }

    return this.buildResult(context);
  }
}
```

### 處理步驟接口

```typescript
interface ProcessingStep {
  name: string;
  isOptional: boolean;
  execute(context: ProcessingContext): Promise<void>;
}

// 範例: 發行者識別步驟
class IssuerIdentificationStep implements ProcessingStep {
  name = 'IssuerIdentification';
  isOptional = false;

  async execute(context: ProcessingContext): Promise<void> {
    // 1. 調用發行者識別服務
    const issuerResult = await this.identifyIssuer(context);

    // 2. 匹配或創建公司
    const company = await this.matchOrCreateCompany(issuerResult);

    // 3. 更新上下文
    context.identifiedCompanyId = company?.id;
    context.issuerConfidence = issuerResult.confidence;
  }
}
```

### 功能開關

```typescript
// src/lib/feature-flags.ts

export const FEATURE_FLAGS = {
  // 統一處理器
  ENABLE_UNIFIED_PROCESSOR: process.env.ENABLE_UNIFIED_PROCESSOR === 'true',

  // 各步驟開關
  ENABLE_ISSUER_IDENTIFICATION: process.env.ENABLE_ISSUER_IDENTIFICATION !== 'false',
  ENABLE_FORMAT_MATCHING: process.env.ENABLE_FORMAT_MATCHING !== 'false',
  ENABLE_DYNAMIC_CONFIG: process.env.ENABLE_DYNAMIC_CONFIG !== 'false',
  ENABLE_TERM_LEARNING: process.env.ENABLE_TERM_LEARNING !== 'false',
  ENABLE_ENHANCED_CONFIDENCE: process.env.ENABLE_ENHANCED_CONFIDENCE !== 'false',
};
```

### 信心度計算增強

```typescript
interface ConfidenceFactors {
  // 提取信心度 (來自 Azure DI)
  extractionConfidence: number;  // 0-1

  // 發行者識別信心度
  issuerConfidence: number;  // 0-1

  // 格式匹配信心度
  formatMatchConfidence: number;  // 0-1

  // 配置匹配程度
  configMatchLevel: 'specific' | 'company' | 'format' | 'global' | 'default';

  // 歷史準確率 (該 Company/Format 的歷史審核通過率)
  historicalAccuracy?: number;  // 0-1

  // 欄位完整度
  fieldCompleteness: number;  // 0-1

  // 術語匹配度 (提取術語與已知術語的匹配程度)
  termMatchRate: number;  // 0-1
}

function calculateOverallConfidence(factors: ConfidenceFactors): number {
  const weights = {
    extractionConfidence: 0.25,
    issuerConfidence: 0.15,
    formatMatchConfidence: 0.10,
    configMatchBonus: 0.10,  // specific = +0.1, company = +0.05, etc.
    historicalAccuracy: 0.15,
    fieldCompleteness: 0.15,
    termMatchRate: 0.10,
  };

  // 加權計算
  let score =
    factors.extractionConfidence * weights.extractionConfidence +
    factors.issuerConfidence * weights.issuerConfidence +
    factors.formatMatchConfidence * weights.formatMatchConfidence +
    (factors.historicalAccuracy || 0.8) * weights.historicalAccuracy +
    factors.fieldCompleteness * weights.fieldCompleteness +
    factors.termMatchRate * weights.termMatchRate;

  // 配置匹配加分
  const configBonus = {
    specific: 0.10,
    company: 0.05,
    format: 0.03,
    global: 0.01,
    default: 0,
  };
  score += configBonus[factors.configMatchLevel];

  return Math.min(1, score);
}
```

---

## 依賴關係

### 上游依賴
- **Epic 0**: 3 層機制的基礎實現
- **Epic 13**: 欄位映射配置
- **Epic 14**: Prompt 配置

### 影響範圍
- **Epic 2**: 手動發票上傳流程
- **Epic 3**: 發票審核流程
- **Epic 9**: 自動化文件獲取

---

## 成功指標

| 指標 | 目標 |
|------|------|
| 日常處理自動通過率 | 從 70% 提升至 85% |
| 新術語自動學習覆蓋率 | 95%+ |
| 處理延遲增加 | < 500ms |
| 人工審核工作量減少 | 20%+ |

---

## 實施計劃

### Phase 1: 基礎整合
- Story 15-1: 統一入口
- Story 15-2: 發行者識別

### Phase 2: 動態配置
- Story 15-3: 格式匹配與配置

### Phase 3: 持續學習
- Story 15-4: 術語學習
- Story 15-5: 信心度增強

### 風險緩解
- 使用功能開關漸進式啟用
- 保留原有流程作為降級方案
- 完善的監控和告警

---

*Epic created: 2026-01-02*
*Last updated: 2026-01-02*
