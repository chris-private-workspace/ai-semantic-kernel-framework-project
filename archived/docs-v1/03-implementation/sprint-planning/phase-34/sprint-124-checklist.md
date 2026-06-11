# Sprint 124 Checklist: n8n 整合 — Mode 1 + Mode 2

## 開發任務

### Story 124-1: n8n MCP Server — IPA 觸發 n8n
- [ ] 建立 `src/integrations/mcp/servers/n8n/` 目錄結構
- [ ] 實現 `client.py` — N8nApiClient
  - [ ] 認證（API Key header）
  - [ ] GET /workflows（列出工作流）
  - [ ] GET /workflows/{id}（取得詳情）
  - [ ] POST /workflows/{id}/execute（觸發執行）
  - [ ] GET /executions/{id}（查詢狀態）
  - [ ] GET /executions（列出歷史）
  - [ ] PATCH /workflows/{id}（啟用/停用）
  - [ ] 錯誤處理與重試機制
- [ ] 實現 `server.py` — N8nMCPServer
  - [ ] MCP Server 框架設定
  - [ ] 6 個 MCP tools 註冊
  - [ ] 參數驗證
- [ ] 實現 `tools/workflow.py`
  - [ ] list_workflows tool
  - [ ] get_workflow tool
  - [ ] activate_workflow tool
- [ ] 實現 `tools/execution.py`
  - [ ] execute_workflow tool
  - [ ] get_execution tool
  - [ ] list_executions tool
- [ ] 實現 `__main__.py` — MCP Server 入口

### Story 124-2: n8n Webhook 入口 — n8n 觸發 IPA
- [ ] 建立 `src/api/v1/n8n/` 路由模組
- [ ] 實現 Webhook 端點
  - [ ] POST `/api/v1/n8n/webhook` — 通用 Webhook
  - [ ] POST `/api/v1/n8n/webhook/{workflow_id}` — 指定工作流
  - [ ] Webhook payload 驗證（Pydantic schema）
  - [ ] HMAC 簽名驗證
- [ ] 實現連線管理端點
  - [ ] GET `/api/v1/n8n/status` — 連線狀態
  - [ ] GET `/api/v1/n8n/config` — 取得配置
  - [ ] PUT `/api/v1/n8n/config` — 更新配置
- [ ] 在 `main.py` 註冊路由

### Story 124-3: 連線管理與測試
- [ ] 實現 n8n 連線配置
  - [ ] 環境變數（N8N_BASE_URL, N8N_API_KEY）
  - [ ] 健康檢查（定期 ping）
  - [ ] 連線池管理
- [ ] 編寫測試
  - [ ] `tests/unit/integrations/mcp/servers/n8n/test_n8n_client.py`
  - [ ] `tests/unit/integrations/mcp/servers/n8n/test_n8n_server.py`
  - [ ] `tests/unit/api/n8n/test_n8n_webhook.py`
  - [ ] `tests/integration/n8n/test_n8n_integration.py`

## 驗證標準

- [ ] n8n MCP Server 可列出工作流
- [ ] n8n MCP Server 可觸發工作流執行
- [ ] Webhook 端點可接收 n8n 回調
- [ ] HMAC 簽名驗證正常
- [ ] 所有新測試通過
- [ ] 回歸測試無失敗
