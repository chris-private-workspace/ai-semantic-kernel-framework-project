# Sprint 125 Checklist: n8n 整合 Mode 3 + Azure Data Factory MCP

## 開發任務

### Story 125-1: n8n Mode 3 — 雙向協作
- [ ] 建立 `src/integrations/n8n/` 模組
- [ ] 實現 `orchestrator.py` — N8nOrchestrator
  - [ ] 接收用戶請求，調用 IPA 推理
  - [ ] 將推理結果轉換為 n8n 工作流參數
  - [ ] 觸發 n8n 工作流執行
  - [ ] 監控執行狀態（輪詢 + 回調）
  - [ ] 整合結果回報用戶
- [ ] 實現 `monitor.py` — ExecutionMonitor
  - [ ] 執行狀態輪詢機制
  - [ ] 超時處理（可配置超時時間）
  - [ ] 失敗重試策略
  - [ ] 進度通知（SSE 推送）
- [ ] 實現 Callback Handler
  - [ ] n8n 異步回調端點
  - [ ] 回調驗證（HMAC）
  - [ ] 更新執行狀態

### Story 125-2: Azure Data Factory MCP Server
- [ ] 建立 `src/integrations/mcp/servers/adf/` 目錄結構
- [ ] 實現 `client.py` — AdfApiClient
  - [ ] Azure SDK 認證（Service Principal）
  - [ ] Pipeline CRUD 操作
  - [ ] Pipeline 執行觸發與監控
  - [ ] Dataset 和 Trigger 查詢
  - [ ] 錯誤處理
- [ ] 實現 `server.py` — AdfMCPServer
  - [ ] MCP Server 框架設定
  - [ ] 8 個 MCP tools 註冊
- [ ] 實現 `tools/pipeline.py`
  - [ ] list_pipelines / get_pipeline tools
  - [ ] run_pipeline / cancel_pipeline_run tools
- [ ] 實現 `tools/monitoring.py`
  - [ ] get_pipeline_run / list_pipeline_runs tools
  - [ ] list_datasets / list_triggers tools

### Story 125-3: 整合測試與監控
- [ ] n8n Mode 3 測試
  - [ ] `tests/unit/integrations/n8n/test_n8n_orchestrator.py`
  - [ ] `tests/unit/integrations/n8n/test_n8n_monitor.py`
- [ ] ADF MCP 測試
  - [ ] `tests/unit/integrations/mcp/servers/adf/test_adf_client.py`
  - [ ] `tests/unit/integrations/mcp/servers/adf/test_adf_server.py`
- [ ] 整合測試
  - [ ] `tests/integration/n8n/test_n8n_mode3.py`
  - [ ] `tests/integration/adf/test_adf_integration.py`

## 驗證標準

- [ ] n8n Mode 3 雙向協作流程端到端可用
- [ ] ADF MCP Server 可列出和觸發 Pipeline
- [ ] 執行監控正確追蹤狀態變化
- [ ] 所有新測試通過
- [ ] 回歸測試無失敗
