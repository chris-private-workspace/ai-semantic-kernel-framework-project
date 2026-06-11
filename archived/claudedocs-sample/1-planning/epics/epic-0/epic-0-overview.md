# Epic 0: 歷史數據初始化

> **建立日期**: 2025-12-23
> **完成日期**: 2025-12-26
> **狀態**: ✅ 已完成
> **優先級**: High

---

## 1. Epic 目標

### 主要目標
建立歷史數據批次處理能力，讓系統能夠從現有發票數據中學習和建立初始映射規則。

### 業務價值
- 利用現有歷史數據快速建立映射規則基礎
- 減少手動配置工作量
- 加速系統上線準備時間
- 為 Forwarder 特定規則提供數據支持

### 成功定義
- 能夠批次上傳歷史發票文件
- 系統自動識別公司和文檔類型
- 自動聚合術語並建議初始映射規則
- 提供完整的處理進度追蹤

---

## 2. Epic 範圍

### 包含功能（In Scope）

| Story | 名稱 | 描述 | 狀態 |
|-------|------|------|------|
| 0-1 | 批次文件上傳與元數據偵測 | 支援多檔案上傳，自動偵測 Forwarder 和文件類型 | ✅ |
| 0-2 | 智能處理路由 | 根據文件特徵自動選擇處理流程 | ✅ |
| 0-3 | Just-in-Time 公司配置 | 動態建立新發現的公司配置 | ✅ |
| 0-4 | 批次處理進度追蹤 | 即時顯示批次處理狀態和進度 | ✅ |
| 0-5 | 術語聚合與初始規則 | 從提取結果聚合術語，建議映射規則 | ✅ |
| 0-6 | 批次公司識別整合 | 整合公司識別到批次處理流程 | ✅ |
| 0-7 | 批次術語聚合整合 | 整合術語聚合到批次處理 UI | ✅ |
| 0-8 | 文件發行者識別 | GPT Vision 識別文件 Logo/標題中的發行公司 | ✅ |
| 0-9 | 文件格式術語重組 | 建立 Company → DocumentFormat → Terms 三層聚合結構 | ✅ |
| 0-10 | AI 術語驗證服務 | GPT-5.2 批量術語分類，過濾無效術語 (7 類別) | ✅ |
| 0-11 | GPT Vision Prompt 優化 | 5 步驟結構化 Prompt，源頭過濾 60-70% 錯誤 | ✅ |

### 排除功能（Out of Scope）
- 即時發票處理（屬於 Epic 2）
- 人工審核工作流（屬於 Epic 3）
- 規則管理界面（屬於 Epic 4）

### 依賴項
- Azure Document Intelligence OCR 服務
- Azure OpenAI GPT-4o 服務
- PostgreSQL 資料庫
- Prisma ORM

---

## 3. 技術架構概覽

### 7 階段處理流程

> **詳細分析**: 參見 `claudedocs/6-ai-assistant/analysis/ANALYSIS-001-HISTORICAL-DATA-FLOW.md`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      歷史數據初始化處理流程 (7 階段)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Phase 1: 文件上傳與類型檢測                                                │
│       │                                                                     │
│       ▼                                                                     │
│   Phase 2: 智能處理路由                                                      │
│   ┌─────────────────────┬─────────────────────┐                             │
│   │ Native PDF          │ Scanned PDF/Image   │                             │
│   │ → DUAL_PROCESSING   │ → GPT_VISION        │                             │
│   └─────────────────────┴─────────────────────┘                             │
│       │                                                                     │
│       ▼                                                                     │
│   Phase 3: 發行者識別                                                        │
│       │                                                                     │
│       ▼                                                                     │
│   Phase 4: 格式識別                                                          │
│       │                                                                     │
│       ▼                                                                     │
│   Phase 5: 數據提取                    ◄─── Story 0-11 (5 步驟 Prompt)       │
│       │                                                                     │
│       ▼                                                                     │
│   Phase 6: 術語聚合                    ◄─── Story 0-10 (AI 術語驗證)         │
│       │                                                                     │
│       ▼                                                                     │
│   Phase 7: 報告輸出                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 雙層錯誤過濾機制 (Stories 0-10 + 0-11)

```
原始術語輸入 (100% 錯誤可能性)
        │
        ▼
┌───────────────────────────────┐
│ 第一層: Story 0-11 (Phase 5) │
│ 5 步驟結構化 Prompt          │
│ → 過濾 60-70% 錯誤           │
└───────────────────────────────┘
        │ (剩餘 30-40%)
        ▼
┌───────────────────────────────┐
│ 第二層: Story 0-10 (Phase 6) │
│ AI 術語驗證服務 (7 類別)     │
│ → 捕獲剩餘 20-30%            │
└───────────────────────────────┘
        │
        ▼
最終輸出: < 5% 錯誤率
```

### 關鍵服務

| 服務 | 檔案位置 | 功能 | Story |
|------|---------|------|-------|
| BatchProcessingService | `src/services/batch-processor.service.ts` | 批次處理協調 | 0-1~0-4 |
| ProcessingRouterService | `src/services/processing-router.service.ts` | 智能處理路由 | 0-2 |
| DocumentIssuerService | `src/services/document-issuer.service.ts` | 發行者識別 | 0-8 |
| DocumentFormatService | `src/services/document-format.service.ts` | 格式識別與管理 | 0-9 |
| GptVisionService | `src/services/gpt-vision.service.ts` | GPT Vision 數據提取 | 0-11 |
| AiTermValidatorService | `src/services/ai-term-validator.service.ts` | AI 術語驗證 | 0-10 |
| HierarchicalTermAggregationService | `src/services/hierarchical-term-aggregation.service.ts` | 三層術語聚合 | 0-5~0-7, 0-9 |
| CompanyAutoCreateService | `src/services/company-auto-create.service.ts` | JIT 公司建立 | 0-3 |

### 資料模型

```prisma
model Batch {
  id            String   @id @default(cuid())
  name          String
  status        BatchStatus
  totalFiles    Int
  processedFiles Int
  createdAt     DateTime @default(now())
  files         BatchFile[]
}

model BatchFile {
  id            String   @id @default(cuid())
  batchId       String
  fileName      String
  status        FileStatus
  companyId     String?
  documentType  DocumentType?
  extractedData Json?
}
```

---

## 4. 開發時間線

### 階段規劃

| 階段 | 時間 | 內容 | 狀態 |
|------|------|------|------|
| Phase 1 | 2025-12-23 | 批次上傳與元數據偵測 (Story 0-1, 0-2) | ✅ |
| Phase 2 | 2025-12-24 | 公司配置與進度追蹤 (Story 0-3, 0-4) | ✅ |
| Phase 3 | 2025-12-25 | 術語聚合 (Story 0-5) | ✅ |
| Phase 4 | 2025-12-26 | 整合優化 (Story 0-6, 0-7) | ✅ |
| Phase 5 | 2025-12-26 | 發行者與格式識別 (Story 0-8, 0-9) | ✅ |
| Phase 6 | 2025-12-31 | AI 術語驗證 (Story 0-10) | ✅ |
| Phase 7 | 2026-01-01 | Prompt 優化 (Story 0-11) | ✅ |

### 里程碑

- ✅ M1: 批次上傳 MVP (2025-12-23)
- ✅ M2: 智能路由完成 (2025-12-24)
- ✅ M3: 術語聚合完成 (2025-12-25)
- ✅ M4: 基礎整合完成 (2025-12-26)
- ✅ M5: 發行者/格式識別完成 (2025-12-26)
- ✅ M6: AI 術語驗證完成 (2025-12-31)
- ✅ M7: Prompt 優化完成，Epic 完成 (2026-01-01)

---

## 5. 成功指標

### 功能指標

| 指標 | 目標 | 實際 |
|------|------|------|
| 批次上傳成功率 | ≥ 99% | ✅ 達成 |
| 公司識別準確率 | ≥ 90% | ✅ 達成 |
| 術語聚合覆蓋率 | ≥ 85% | ✅ 達成 |
| 處理進度即時性 | < 2s 延遲 | ✅ 達成 |

### 技術指標

| 指標 | 目標 | 實際 |
|------|------|------|
| 單檔處理時間 | < 30s | ✅ 達成 |
| 批次並行處理數 | ≥ 5 | ✅ 達成 |
| API 回應時間 | < 500ms | ✅ 達成 |

---

## 6. 風險與挑戰

### 已解決風險

| 風險 | 影響 | 解決方案 |
|------|------|----------|
| OCR 品質不一 | 高 | 實施預處理和品質檢查 |
| 公司識別模糊 | 中 | 多策略識別 + 用戶確認 |
| 大量文件處理效能 | 高 | 實施隊列和並行處理 |

### 技術債務

| 項目 | 優先級 | 計劃修復時間 |
|------|--------|-------------|
| 批次處理錯誤重試機制 | Medium | Epic 12 |
| 大文件分片處理 | Low | 未規劃 |

---

## 7. 相關文檔

### 規劃文檔
- PRD: `docs/01-planning/prd/prd.md`
- UX 設計: `docs/01-planning/ux/ux-design.md`

### 技術文檔
- 架構設計: `docs/02-architecture/architecture.md`
- API 文檔: `docs/02-architecture/api-design.md`

### 分析文檔
- **流程架構分析**: `claudedocs/6-ai-assistant/analysis/ANALYSIS-001-HISTORICAL-DATA-FLOW.md`
  - 7 階段處理流程詳細說明
  - Stories 0-10/0-11 增強分析
  - 雙層錯誤過濾機制說明

### 實施文檔
- Sprint 狀態: `docs/04-implementation/sprint-status.yaml`
- 故事列表: `docs/03-stories/`
- Story 0-10: `docs/04-implementation/stories/0-10-ai-term-validation.md`
- Story 0-11: `docs/04-implementation/stories/0-11-gpt-vision-prompt-optimization.md`

### Prompt 文檔
- 優化版提取 Prompt: `src/lib/prompts/optimized-extraction-prompt.ts`

---

**維護者**: Development Team
**最後更新**: 2026-01-02
