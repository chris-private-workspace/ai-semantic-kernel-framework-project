# Sprint 129 Checklist: D365 MCP Server

## 開發任務

### Story 129-1: D365 API Client
- [ ] 建立 `src/integrations/mcp/servers/d365/` 目錄
- [ ] 實現 `auth.py` — OAuth 認證
  - [ ] Client Credentials Grant 流程
  - [ ] Token 快取與刷新
  - [ ] 多租戶支援
- [ ] 實現 `client.py` — D365ApiClient
  - [ ] OData 查詢建構器（$filter, $select, $top, $orderby）
  - [ ] GET 查詢實體
  - [ ] GET 取得單筆記錄
  - [ ] POST 建立記錄
  - [ ] PATCH 更新記錄
  - [ ] DELETE 刪除記錄
  - [ ] 分頁處理（@odata.nextLink）
  - [ ] 錯誤處理（401, 403, 404, 429）

### Story 129-2: D365 MCP Server
- [ ] 實現 `server.py` — D365MCPServer
  - [ ] MCP Server 框架設定
  - [ ] 6 個 MCP tools 註冊
- [ ] 實現 `tools/query.py`
  - [ ] query_entities tool（支援 OData 語法）
  - [ ] get_record tool
  - [ ] list_entity_types tool
  - [ ] get_entity_metadata tool
- [ ] 實現 `tools/crud.py`
  - [ ] create_record tool
  - [ ] update_record tool
- [ ] 實現 `__main__.py` — MCP Server 入口

### Story 129-3: 測試與驗證
- [ ] `tests/unit/integrations/mcp/servers/d365/test_d365_client.py`
- [ ] `tests/unit/integrations/mcp/servers/d365/test_d365_auth.py`
- [ ] `tests/unit/integrations/mcp/servers/d365/test_d365_server.py`
- [ ] `tests/unit/integrations/mcp/servers/d365/test_odata_builder.py`
- [ ] `tests/integration/d365/test_d365_integration.py`

## 驗證標準

- [ ] D365 OAuth 認證成功
- [ ] OData 查詢正確返回結果
- [ ] CRUD 操作全部正常
- [ ] 分頁處理正確
- [ ] 所有新測試通過
- [ ] 回歸測試無失敗
