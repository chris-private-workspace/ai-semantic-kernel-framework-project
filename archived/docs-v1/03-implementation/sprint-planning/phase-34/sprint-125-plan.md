# Sprint 125: n8n 整合 Mode 3 + Azure Data Factory MCP

## 概述

Sprint 125 完成 n8n 三種協作模式的最後一種（雙向協作），並啟動 Azure Data Factory MCP Server 的實現，為 ETL 場景自動化提供基礎。

## 目標

1. 實現 n8n Mode 3（雙向協作：IPA 推理 + n8n 編排）
2. 實現 Azure Data Factory MCP Server
3. 完善 n8n 整合的錯誤處理與監控
4. ADF Pipeline 觸發與監控能力

## Story Points: 30 點

## 前置條件

- ⬜ Sprint 124 完成（n8n Mode 1 + Mode 2）
- ⬜ Azure Data Factory 資源已建立
- ⬜ ADF Service Principal 配置就緒

## 任務分解

### Story 125-1: n8n Mode 3 — 雙向協作 (2 天, P1)

**目標**: IPA 做推理決策，n8n 編排執行，IPA 監控結果

**協作流程**:
```
用戶請求 → IPA 推理決策 → n8n 編排執行 → IPA 監控結果 → 回報用戶
```

**交付物**:
- `src/integrations/n8n/orchestrator.py` — N8nOrchestrator
- `src/integrations/n8n/monitor.py` — 執行監控
- Callback 機制（n8n → IPA 回報進度）

**關鍵類別**:

| 類別 | 職責 |
|------|------|
| N8nOrchestrator | 協調 IPA 推理 → n8n 執行 → 結果監控 |
| ExecutionMonitor | 輪詢 n8n 執行狀態，處理超時與失敗 |
| CallbackHandler | 處理 n8n 異步回調通知 |

### Story 125-2: Azure Data Factory MCP Server (3 天, P1)

**目標**: 建立 ADF MCP Server，支援 ETL Pipeline 管理

**MCP Tools**:

| Tool | 說明 | ADF API |
|------|------|---------|
| `list_pipelines` | 列出所有 Pipeline | GET /pipelines |
| `get_pipeline` | 取得 Pipeline 詳情 | GET /pipelines/{name} |
| `run_pipeline` | 觸發 Pipeline 執行 | POST /pipelines/{name}/createRun |
| `get_pipeline_run` | 查詢執行狀態 | GET /pipelineruns/{runId} |
| `list_pipeline_runs` | 列出執行歷史 | POST /queryPipelineRuns |
| `cancel_pipeline_run` | 取消執行 | POST /pipelineruns/{runId}/cancel |
| `list_datasets` | 列出資料集 | GET /datasets |
| `list_triggers` | 列出觸發器 | GET /triggers |

**檔案結構**:
```
src/integrations/mcp/servers/adf/
├── __init__.py
├── __main__.py
├── server.py             # AdfMCPServer
├── client.py             # AdfApiClient（Azure SDK 封裝）
└── tools/
    ├── __init__.py
    ├── pipeline.py        # Pipeline 管理 tools
    └── monitoring.py      # 執行監控 tools
```

### Story 125-3: 整合測試與監控 (2 天, P1)

**目標**: n8n + ADF 的整合測試與監控指標

**測試範圍**:

| 測試檔案 | 範圍 |
|----------|------|
| `test_n8n_orchestrator.py` | Mode 3 雙向協作流程 |
| `test_n8n_monitor.py` | 執行監控與超時處理 |
| `test_adf_client.py` | ADF API client |
| `test_adf_server.py` | ADF MCP Server tools |
| `test_adf_integration.py` | Pipeline 端到端觸發 |

## 風險

| 風險 | 影響 | 緩解 |
|------|------|------|
| n8n 回調延遲 | 雙向協作超時 | 設定合理超時 + 輪詢 fallback |
| ADF 權限不足 | Pipeline 觸發失敗 | Service Principal 權限驗證 |
| 跨服務網路延遲 | 回應時間長 | 異步處理 + SSE 進度通知 |

## 依賴

- Sprint 124 n8n Mode 1+2 基礎
- 改善提案 Phase D P1: n8n 整合 + Azure Data Factory MCP
