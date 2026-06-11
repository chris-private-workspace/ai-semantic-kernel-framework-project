# TEST-PLAN-003: Epic 0 完整功能測試

> **建立日期**: 2026-01-02
> **版本**: 1.0.0
> **覆蓋範圍**: Epic 0 Stories 0-1 至 0-11（完整版）
> **狀態**: 📋 待執行

---

## 1. 測試計劃概述

### 1.1 測試目標

驗證 Epic 0（歷史數據初始化）的完整功能，特別是：

| 重點領域 | 說明 | 關聯 Story |
|----------|------|------------|
| 7 階段處理流程 | 完整批次處理流程驗證 | 0-1 至 0-9 |
| 5 步驟結構化 Prompt | GPT Vision 優化提取 | 0-11 |
| AI 術語驗證服務 | 7 類別分類過濾 | 0-10 |
| 雙層錯誤過濾機制 | 源頭 + 終端雙重防護 | 0-10 + 0-11 |

### 1.2 與現有測試計劃關係

| 計劃 | 覆蓋範圍 | 狀態 |
|------|----------|------|
| TEST-PLAN-001 | CHANGE-001 雙重處理專用 | 保留 |
| TEST-PLAN-002 | Stories 0-1 至 0-9 | 歷史參考 |
| **TEST-PLAN-003** | **Stories 0-1 至 0-11** | **最新完整版** |

### 1.3 成功標準

| 指標 | 目標值 | 說明 |
|------|--------|------|
| 處理成功率 | ≥ 99% | 文件處理無錯誤 |
| 第一層過濾效果 | 60-70% | Story 0-11 源頭過濾 |
| 第二層過濾效果 | 20-30% | Story 0-10 終端過濾 |
| 最終錯誤率 | < 5% | 雙層防護後 |
| 術語分類準確率 | ≥ 95% | AI 驗證分類 |

---

## 2. 測試數據

### 2.1 數據來源

```
路徑: docs/Doc Sample/
總計: 131 個 PDF 文件

分類:
├─ Native PDF: 91 files → DUAL_PROCESSING 路由
└─ Scanned PDF: 40 files → GPT_VISION 路由
```

### 2.2 特殊測試術語

#### 有效術語（應保留）

| 術語 | 預期分類 |
|------|----------|
| AIR FREIGHT | FREIGHT_CHARGE |
| OCEAN FREIGHT | FREIGHT_CHARGE |
| FUEL SURCHARGE | SURCHARGE |
| PEAK SEASON SURCHARGE | SURCHARGE |
| HANDLING FEE | SERVICE_FEE |
| CUSTOMS CLEARANCE | SERVICE_FEE |
| IMPORT DUTY | DUTY_TAX |
| VAT | DUTY_TAX |

#### 無效術語（應過濾）

| 術語 | 預期分類 | 應被過濾原因 |
|------|----------|--------------|
| HKG, HONG KONG | ADDRESS | 機場/地址代碼 |
| BLR, BANGALORE | ADDRESS | 機場/地址代碼 |
| KATHY LAM | PERSON_NAME | 人名 |
| Nguyen Van Anh | PERSON_NAME | 越南人名 |
| RICOH LIMITED | COMPANY_NAME | 公司名稱 |
| DHL EXPRESS | COMPANY_NAME | 公司名稱 |
| CENTRAL PLAZA | BUILDING_NAME | 建築名稱 |
| 123 QUEEN'S ROAD | ADDRESS | 街道地址 |

---

## 3. 7 階段處理流程測試

### 3.1 流程概覽

```
┌─────────────────────────────────────────────────────────────────┐
│                    7 階段處理流程測試架構                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Phase 1: 文件上傳與類型檢測                                    │
│       │                                                         │
│       ▼                                                         │
│   Phase 2: 智能處理路由                                          │
│   ┌─────────────────────┬─────────────────────┐                 │
│   │ Native PDF          │ Scanned PDF/Image   │                 │
│   │ → DUAL_PROCESSING   │ → GPT_VISION        │                 │
│   └─────────────────────┴─────────────────────┘                 │
│       │                                                         │
│       ▼                                                         │
│   Phase 3: 發行者識別                                            │
│       │                                                         │
│       ▼                                                         │
│   Phase 4: 格式識別                                              │
│       │                                                         │
│       ▼                                                         │
│   Phase 5: 數據提取              ◄─── Story 0-11 測試重點        │
│   ┌─────────────────────────────────────────────┐               │
│   │ 5 步驟結構化 Prompt (V2.0.0)                │               │
│   │ • 區域識別 → 提取規則 → 排除規則            │               │
│   │ • 負面範例 → 自我驗證                       │               │
│   │ → 過濾 60-70% 錯誤                          │               │
│   └─────────────────────────────────────────────┘               │
│       │                                                         │
│       ▼                                                         │
│   Phase 6: 術語聚合              ◄─── Story 0-10 測試重點        │
│   ┌─────────────────────────────────────────────┐               │
│   │ AI 術語驗證服務 (7 類別)                    │               │
│   │ • 有效: FREIGHT_CHARGE, SURCHARGE, etc.    │               │
│   │ • 無效: ADDRESS, PERSON_NAME, etc.         │               │
│   │ → 捕獲剩餘 20-30% 錯誤                      │               │
│   └─────────────────────────────────────────────┘               │
│       │                                                         │
│       ▼                                                         │
│   Phase 7: 報告輸出                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Phase 1: 文件上傳與類型檢測

| TC ID | 測試名稱 | 測試步驟 | 預期結果 | 狀態 |
|-------|----------|----------|----------|------|
| TC-1.1 | 單檔上傳 | 上傳單個 PDF 文件 | 文件成功上傳，狀態為 PENDING | ⬜ |
| TC-1.2 | 批次上傳 | 上傳 10+ 個 PDF 文件 | 所有文件成功上傳，批次建立 | ⬜ |
| TC-1.3 | 文件類型檢測 | 上傳 Native/Scanned PDF | 正確識別文件類型 | ⬜ |
| TC-1.4 | 無效文件拒絕 | 上傳非 PDF 文件 | 返回錯誤，文件被拒絕 | ⬜ |
| TC-1.5 | 大文件處理 | 上傳 >10MB 文件 | 正確處理或返回大小限制錯誤 | ⬜ |

### 3.3 Phase 2: 智能處理路由

| TC ID | 測試名稱 | 測試步驟 | 預期結果 | 狀態 |
|-------|----------|----------|----------|------|
| TC-2.1 | Native PDF 路由 | 處理 Native PDF | 路由到 DUAL_PROCESSING | ⬜ |
| TC-2.2 | Scanned PDF 路由 | 處理 Scanned PDF | 路由到 GPT_VISION | ⬜ |
| TC-2.3 | 混合批次路由 | 處理包含兩種類型的批次 | 每個文件正確路由 | ⬜ |
| TC-2.4 | 路由決策記錄 | 檢查處理記錄 | processingMethod 欄位正確 | ⬜ |

### 3.4 Phase 3: 發行者識別

| TC ID | 測試名稱 | 測試步驟 | 預期結果 | 狀態 |
|-------|----------|----------|----------|------|
| TC-3.1 | HEADER 識別 | 處理有明確標題的文件 | 識別方法為 HEADER | ⬜ |
| TC-3.2 | LOGO 識別 | 處理有 Logo 的文件 | 識別方法為 LOGO | ⬜ |
| TC-3.3 | 信心度評估 | 檢查識別信心度 | 信心度在 0-1 範圍 | ⬜ |
| TC-3.4 | 公司匹配 | 識別結果匹配現有公司 | documentIssuerId 正確關聯 | ⬜ |
| TC-3.5 | JIT 公司建立 | 識別新公司 | 自動建立新公司記錄 | ⬜ |

### 3.5 Phase 4: 格式識別

| TC ID | 測試名稱 | 測試步驟 | 預期結果 | 狀態 |
|-------|----------|----------|----------|------|
| TC-4.1 | 格式匹配 | 處理已知格式文件 | 正確匹配 DocumentFormat | ⬜ |
| TC-4.2 | 新格式建立 | 處理新格式文件 | 自動建立新 DocumentFormat | ⬜ |
| TC-4.3 | Company-Format 關聯 | 檢查關聯關係 | Company → DocumentFormat 正確 | ⬜ |

### 3.6 Phase 5: 數據提取 【Story 0-11 重點】

| TC ID | 測試名稱 | 測試步驟 | 預期結果 | 狀態 |
|-------|----------|----------|----------|------|
| TC-5.1 | 5 步驟 Prompt 結構 | 檢查 Prompt 內容 | 包含所有 5 個步驟 | ⬜ |
| TC-5.2 | 區域識別功能 | 處理標準發票 | regionsIdentified 包含 header/lineItems/footer | ⬜ |
| TC-5.3 | Location 排除 | 輸入包含 "HKG, HONG KONG" | 出現在 excludedItems | ⬜ |
| TC-5.4 | Contact 排除 | 輸入包含 "KATHY LAM" | 出現在 excludedItems | ⬜ |
| TC-5.5 | Company 排除 | 輸入包含 "RICOH LIMITED" | 出現在 excludedItems | ⬜ |
| TC-5.6 | Address 排除 | 輸入包含 "CENTRAL PLAZA" | 出現在 excludedItems | ⬜ |
| TC-5.7 | 負面範例過濾 | 處理包含常見錯誤的文件 | 錯誤術語被過濾 | ⬜ |
| TC-5.8 | 自我驗證機制 | 檢查提取結果 | extractionConfidence 有值 | ⬜ |
| TC-5.9 | excludedItems 追蹤 | 檢查排除項記錄 | 包含 text, reason, region | ⬜ |
| TC-5.10 | Prompt V1.0.0 | 使用舊版 Prompt | 返回基本提取結果 | ⬜ |
| TC-5.11 | Prompt V2.0.0 | 使用新版 Prompt | 返回優化提取結果 + excludedItems | ⬜ |
| TC-5.12 | 版本切換對比 | A/B 測試兩版本 | V2.0.0 錯誤率明顯低於 V1.0.0 | ⬜ |

### 3.7 Phase 6: 術語聚合 【Story 0-10 重點】

| TC ID | 測試名稱 | 測試步驟 | 預期結果 | 狀態 |
|-------|----------|----------|----------|------|
| TC-6.1 | AI 驗證啟用 | 設定 aiValidationEnabled: true | AI 驗證服務被調用 | ⬜ |
| TC-6.2 | AI 驗證停用 | 設定 aiValidationEnabled: false | 使用規則過濾 | ⬜ |
| TC-6.3 | FREIGHT_CHARGE 分類 | 輸入 "AIR FREIGHT" | 分類為 FREIGHT_CHARGE | ⬜ |
| TC-6.4 | SURCHARGE 分類 | 輸入 "FUEL SURCHARGE" | 分類為 SURCHARGE | ⬜ |
| TC-6.5 | SERVICE_FEE 分類 | 輸入 "HANDLING FEE" | 分類為 SERVICE_FEE | ⬜ |
| TC-6.6 | DUTY_TAX 分類 | 輸入 "IMPORT DUTY" | 分類為 DUTY_TAX | ⬜ |
| TC-6.7 | ADDRESS 過濾 | 輸入 "HKG, HONG KONG" | 分類為 ADDRESS，被過濾 | ⬜ |
| TC-6.8 | PERSON_NAME 過濾 | 輸入 "KATHY LAM" | 分類為 PERSON_NAME，被過濾 | ⬜ |
| TC-6.9 | COMPANY_NAME 過濾 | 輸入 "RICOH LIMITED" | 分類為 COMPANY_NAME，被過濾 | ⬜ |
| TC-6.10 | BUILDING_NAME 過濾 | 輸入 "CENTRAL PLAZA" | 分類為 BUILDING_NAME，被過濾 | ⬜ |
| TC-6.11 | 批量處理 50 術語 | 輸入 50 個術語 | 單批次處理完成 | ⬜ |
| TC-6.12 | 批量處理 100 術語 | 輸入 100 個術語 | 分批處理完成 | ⬜ |
| TC-6.13 | 快取命中 | 重複輸入相同術語 | 使用快取，API 調用減少 | ⬜ |
| TC-6.14 | Fallback 機制 | 模擬 API 失敗 | 降級至 isAddressLikeTerm() | ⬜ |
| TC-6.15 | 成本追蹤 | 檢查 API 調用記錄 | token 使用量有記錄 | ⬜ |

### 3.8 Phase 7: 報告輸出

| TC ID | 測試名稱 | 測試步驟 | 預期結果 | 狀態 |
|-------|----------|----------|----------|------|
| TC-7.1 | 聚合結果統計 | 完成批次處理 | 正確統計公司/格式/術語數量 | ⬜ |
| TC-7.2 | Excel 報告導出 | 點擊導出按鈕 | 生成 4 個工作表的 Excel | ⬜ |
| TC-7.3 | Summary 工作表 | 檢查 Summary | 包含批次資訊和統計 | ⬜ |
| TC-7.4 | Companies 工作表 | 檢查 Companies | 列出所有識別的公司 | ⬜ |
| TC-7.5 | Formats 工作表 | 檢查 Formats | 列出所有文件格式 | ⬜ |
| TC-7.6 | Terms 工作表 | 檢查 Terms | 列出所有有效術語及頻率 | ⬜ |

---

## 4. 雙層錯誤過濾機制整合測試

### 4.1 測試架構

```
┌─────────────────────────────────────────────────────────────────┐
│                      雙層錯誤過濾測試                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   測試輸入: 包含已知錯誤的術語集合                               │
│   │                                                             │
│   │  已知有效術語: 30 個                                        │
│   │  已知無效術語: 70 個 (地址/人名/公司等)                      │
│   │  總計: 100 個術語                                           │
│   │                                                             │
│   ▼                                                             │
│   ┌─────────────────────────────────────────┐                   │
│   │ 第一層: Story 0-11 (Phase 5)            │                   │
│   │ 5 步驟結構化 Prompt                      │                   │
│   │ 預期: 過濾 42-49 個無效術語 (60-70%)    │                   │
│   └─────────────────────────────────────────┘                   │
│   │                                                             │
│   │  剩餘: 51-58 個術語 (30 有效 + 21-28 無效)                   │
│   │                                                             │
│   ▼                                                             │
│   ┌─────────────────────────────────────────┐                   │
│   │ 第二層: Story 0-10 (Phase 6)            │                   │
│   │ AI 術語驗證服務 (7 類別)                 │                   │
│   │ 預期: 過濾 14-17 個無效術語 (20-30%)    │                   │
│   └─────────────────────────────────────────┘                   │
│   │                                                             │
│   ▼                                                             │
│   最終輸出: 30 有效 + 4-7 漏網 (錯誤率 < 5%)                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 整合測試案例

| TC ID | 測試名稱 | 測試方法 | 成功標準 | 狀態 |
|-------|----------|----------|----------|------|
| TC-INT-1 | 第一層過濾效果 | 計算 excludedItems 數量 | 過濾 60-70% 無效術語 | ⬜ |
| TC-INT-2 | 第二層過濾效果 | 計算 AI 驗證過濾數量 | 過濾剩餘的 20-30% | ⬜ |
| TC-INT-3 | 最終錯誤率 | 計算最終術語中無效比例 | 錯誤率 < 5% | ⬜ |
| TC-INT-4 | 有效術語保留 | 檢查有效術語是否保留 | 100% 有效術語保留 | ⬜ |
| TC-INT-5 | 過濾追蹤完整性 | 檢查過濾記錄 | 每個被過濾項有原因記錄 | ⬜ |

### 4.3 效能基準測試

| TC ID | 測試名稱 | 測試方法 | 成功標準 | 狀態 |
|-------|----------|----------|----------|------|
| TC-PERF-1 | 單檔處理時間 | 計時單個文件處理 | < 30 秒 | ⬜ |
| TC-PERF-2 | 批次並行處理 | 處理 10 個文件 | 並行數 ≥ 5 | ⬜ |
| TC-PERF-3 | AI 驗證延遲 | 計時 AI 驗證調用 | < 5 秒 / 100 術語 | ⬜ |
| TC-PERF-4 | 快取效率 | 重複術語處理 | 快取命中率 > 80% | ⬜ |

---

## 5. E2E 測試場景

### 5.1 完整批次處理場景

```
場景: 歷史數據初始化完整流程
前置條件:
- 資料庫已清空或使用測試環境
- docs/Doc Sample/ 有 131 個測試文件

測試步驟:
1. 建立新批次，上傳 131 個 PDF 文件
2. 啟動批次處理
3. 等待處理完成
4. 驗證各階段結果
5. 導出 Excel 報告

驗證點:
□ 批次狀態變為 COMPLETED
□ 所有文件處理成功 (131/131)
□ 發行者識別完成 (識別數量 > 0)
□ 公司自動建立 (新公司數量 > 0)
□ 術語聚合完成 (唯一術語數量 > 0)
□ excludedItems 有記錄
□ Excel 報告可正常導出
```

### 5.2 Prompt 版本 A/B 測試場景

```
場景: Prompt V1.0.0 vs V2.0.0 對比測試
前置條件:
- 準備 20 個已知包含錯誤術語的文件

測試步驟:
1. 使用 V1.0.0 Prompt 處理 10 個文件
2. 記錄提取的術語和錯誤數量
3. 使用 V2.0.0 Prompt 處理相同 10 個文件
4. 記錄提取的術語、excludedItems 和錯誤數量
5. 對比兩版本結果

驗證點:
□ V2.0.0 錯誤術語數量明顯少於 V1.0.0
□ V2.0.0 有 excludedItems 記錄
□ V2.0.0 有 extractionMetadata
□ 處理時間差異可接受 (< 20%)
```

### 5.3 AI 驗證開關對比場景

```
場景: aiValidationEnabled 開關效果對比
前置條件:
- 準備包含 50 個術語的批次

測試步驟:
1. aiValidationEnabled: false 處理批次
2. 記錄最終術語數量
3. aiValidationEnabled: true 處理相同批次
4. 記錄最終術語數量和過濾數量

驗證點:
□ 啟用 AI 驗證後無效術語數量減少
□ 有效術語數量保持不變
□ API 調用有成本記錄
```

---

## 6. 測試腳本

### 6.1 腳本列表

| 腳本名稱 | 用途 | 路徑 |
|----------|------|------|
| test-plan-003-e2e.ts | 完整 E2E 測試 | scripts/test-plan-003-e2e.ts |
| test-prompt-versions.ts | Prompt 版本對比 | scripts/test-prompt-versions.ts |
| test-ai-validation.ts | AI 驗證功能測試 | scripts/test-ai-validation.ts |
| test-dual-layer-filter.ts | 雙層過濾效果測試 | scripts/test-dual-layer-filter.ts |

### 6.2 執行命令

```bash
# 執行完整 E2E 測試
npx ts-node scripts/test-plan-003-e2e.ts

# 執行 Prompt 版本對比
npx ts-node scripts/test-prompt-versions.ts

# 執行 AI 驗證功能測試
npx ts-node scripts/test-ai-validation.ts

# 執行雙層過濾效果測試
npx ts-node scripts/test-dual-layer-filter.ts
```

---

## 7. 測試環境

### 7.1 環境要求

| 項目 | 要求 |
|------|------|
| Node.js | v18+ |
| PostgreSQL | 容器運行中 |
| Azure OpenAI | API 可用 |
| Azure Document Intelligence | API 可用 |

### 7.2 環境變數

```bash
# 必需
DATABASE_URL=postgresql://...
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_API_KEY=...
AZURE_DI_ENDPOINT=https://...
AZURE_DI_API_KEY=...

# 可選（測試專用）
TEST_PROMPT_VERSION=2.0.0
TEST_AI_VALIDATION_ENABLED=true
```

---

## 8. 測試報告模板

### 8.1 報告命名

```
TEST-REPORT-003-YYYY-MM-DD.md
```

### 8.2 報告結構

```markdown
# TEST-REPORT-003: Epic 0 完整功能測試報告

## 執行資訊
- 執行日期: YYYY-MM-DD
- 執行環境: 開發/測試/生產
- 測試人員: XXX

## 測試摘要
| 指標 | 結果 |
|------|------|
| 總測試案例 | XX |
| 通過 | XX |
| 失敗 | XX |
| 跳過 | XX |

## 階段結果
[各階段測試結果詳細記錄]

## 問題記錄
[發現的問題和建議]

## 附件
- Excel 報告
- 錯誤截圖
- 日誌文件
```

---

## 9. 相關文檔

| 文檔 | 路徑 |
|------|------|
| Epic 0 概述 | `claudedocs/1-planning/epics/epic-0/epic-0-overview.md` |
| 流程架構分析 | `claudedocs/6-ai-assistant/analysis/ANALYSIS-001-HISTORICAL-DATA-FLOW.md` |
| 優化版 Prompt | `src/lib/prompts/optimized-extraction-prompt.ts` |
| AI 術語驗證服務 | `src/services/ai-term-validator.service.ts` |
| GPT Vision 服務 | `src/services/gpt-vision.service.ts` |
| TEST-PLAN-002 (舊版) | `claudedocs/5-status/testing/plans/TEST-PLAN-002-EPIC-0-COMPLETE.md` |

---

**建立者**: Claude AI Assistant
**建立日期**: 2026-01-02
**文檔版本**: 1.0.0
