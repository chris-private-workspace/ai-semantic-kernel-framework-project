# Sprint 127: P1 整合測試 + E2E 驗證

## 概述

Sprint 127 是 Phase 34 P1 的收尾 Sprint，對 Sprint 124-126 實現的 n8n 整合、ADF MCP、IT 事件處理進行全面的整合測試和端到端驗證，確保三個 P1 功能在生產環境中穩定可用。

## 目標

1. n8n 三種模式的端到端驗證
2. Azure Data Factory Pipeline 觸發與監控驗證
3. IT 事件處理場景全流程驗證
4. 跨功能整合測試（n8n + ADF + Incident 聯動）
5. 效能基準測試

## Story Points: 20 點

## 前置條件

- ⬜ Sprint 124-126 全部完成
- ⬜ n8n + ADF 測試環境就緒
- ⬜ ServiceNow 測試實例可用

## 任務分解

### Story 127-1: n8n 端到端驗證 (2 天, P1)

**測試場景**:

| 場景 | 模式 | 驗證內容 |
|------|------|---------|
| IPA 觸發 n8n 發送通知 | Mode 1 | Webhook 觸發 → 執行完成 → 結果返回 |
| n8n 排程觸發 IPA 分析 | Mode 2 | 定時觸發 → IPA 分類 → 結果回傳 |
| 用戶請求→IPA 推理→n8n 執行 | Mode 3 | 完整雙向協作流程 |
| n8n 連線中斷恢復 | 容錯 | 斷線偵測 → 重連 → 恢復執行 |
| 並發觸發 | 效能 | 10 個並發工作流觸發 |

### Story 127-2: ADF + Incident E2E 驗證 (2 天, P1)

**ADF 測試場景**:
- Pipeline 列表查詢
- Pipeline 觸發執行 → 狀態監控 → 完成通知
- Pipeline 執行取消
- 權限不足錯誤處理

**Incident 測試場景**:
- ServiceNow P1 事件 → IPA 自動分析 → 建議列表
- 低風險自動修復（服務重啟）
- 高風險 HITL 審批流程
- 事件解決 → ServiceNow 狀態回寫

### Story 127-3: 跨功能整合測試 (1 天, P1)

**聯動場景**:
```
ServiceNow Incident (P1 嚴重)
  → IPA 分析判定需要 ETL Pipeline 修復
  → 觸發 ADF Pipeline 重跑
  → 監控 Pipeline 執行
  → 觸發 n8n 通知工作流（Teams/Email）
  → 回寫 ServiceNow Incident 已解決
```

### Story 127-4: 效能基準 + 文件 (1 天, P1)

**效能基準**:

| 操作 | 目標回應時間 |
|------|-------------|
| n8n 工作流觸發 | < 2s |
| ADF Pipeline 觸發 | < 3s |
| 事件分類 | < 1s（Pattern）/ < 5s（LLM）|
| 完整事件處理流程 | < 30s（自動）/ < 5min（審批）|

## 依賴

- Sprint 124-126 全部交付物
- 改善提案 Phase D P1 驗收標準
