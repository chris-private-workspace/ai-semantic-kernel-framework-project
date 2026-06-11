# Sprint 117 Checklist: Multi-Worker + ServiceNow MCP

## 開發任務

### Story 117-1: Multi-Worker Uvicorn
- [ ] 創建 `backend/src/core/server_config.py`
  - [ ] 定義 `ServerEnvironment` enum（development, staging, production）
  - [ ] 實現 `ServerConfig` 類
  - [ ] 實現 `workers` 屬性（dev: 1, prod: CPU*2+1, max 8）
  - [ ] 實現 `reload` 屬性（dev: True, 其他: False）
  - [ ] 實現 `host` 屬性
  - [ ] 實現 `port` 屬性
  - [ ] 實現 `log_level` 屬性
  - [ ] 實現 `access_log` 屬性
  - [ ] 實現 `worker_class` 屬性
  - [ ] 支持環境變量覆蓋
- [ ] 創建 `backend/gunicorn.conf.py`
  - [ ] 引入 ServerConfig
  - [ ] 配置 bind
  - [ ] 配置 workers
  - [ ] 配置 worker_class
  - [ ] 配置 reload
  - [ ] 配置 loglevel
  - [ ] 配置 accesslog
- [ ] 修改 `backend/main.py`
  - [ ] 引入 ServerConfig
  - [ ] 根據環境選擇啟動方式
  - [ ] 移除 hardcoded reload=True
- [ ] 更新 `backend/.env.example`
  - [ ] 新增 SERVER_ENV
  - [ ] 新增 UVICORN_WORKERS
  - [ ] 新增 SERVER_HOST
  - [ ] 新增 SERVER_PORT
  - [ ] 新增 LOG_LEVEL
- [ ] 創建 `backend/tests/unit/core/test_server_config.py`
  - [ ] 測試 development 環境配置
  - [ ] 測試 staging 環境配置
  - [ ] 測試 production 環境配置
  - [ ] 測試環境變量覆蓋
  - [ ] 測試預設值
  - [ ] 測試 worker 數量上限
- [ ] 驗證 Multi-Worker 啟動
  - [ ] Development 模式啟動正常
  - [ ] 確認 Redis 存儲在 Multi-Worker 下正常（無 InMemory 衝突）

### Story 117-2: ServiceNow MCP Server
- [ ] 創建 `backend/src/integrations/mcp/servicenow_config.py`
  - [ ] 定義 `ServiceNowConfig` Pydantic model
  - [ ] instance_url 欄位
  - [ ] username, password 欄位
  - [ ] api_version 欄位（預設 v2）
  - [ ] timeout 欄位（預設 30s）
  - [ ] 從環境變量讀取
- [ ] 創建 `backend/src/integrations/mcp/servicenow_client.py`
  - [ ] 實現 `ServiceNowClient` 類
  - [ ] 配置 httpx.AsyncClient（auth, timeout）
  - [ ] 實現 `create_incident()`
    - [ ] POST /api/now/v2/table/incident
    - [ ] 參數: short_description, description, category, urgency, assignment_group, caller_id
  - [ ] 實現 `update_incident()`
    - [ ] PATCH /api/now/v2/table/incident/{sys_id}
    - [ ] 參數: sys_id, updates dict
  - [ ] 實現 `get_incident()`
    - [ ] GET /api/now/v2/table/incident
    - [ ] 支持 number 或 sys_id 查詢
  - [ ] 實現 `create_ritm()`
    - [ ] POST /api/now/v2/table/sc_req_item
    - [ ] 參數: cat_item, variables, requested_for, short_description
  - [ ] 實現 `get_ritm_status()`
    - [ ] GET /api/now/v2/table/sc_req_item
    - [ ] 支持 number 或 sys_id 查詢
  - [ ] 實現 `add_attachment()`
    - [ ] POST /api/now/attachment/file
    - [ ] 參數: table, sys_id, file_name, content, content_type
  - [ ] 實現 `add_work_notes()`（add_attachment 的文字版）
    - [ ] PATCH table record 添加 work_notes 欄位
  - [ ] 錯誤處理
    - [ ] 網路連接錯誤
    - [ ] 認證失敗 (401)
    - [ ] 權限不足 (403)
    - [ ] 記錄不存在 (404)
    - [ ] 伺服器錯誤 (500)
  - [ ] 重試機制（指數退避）
- [ ] 創建 `backend/src/integrations/mcp/servicenow_server.py`
  - [ ] 實現 `ServiceNowMCPServer` 類
  - [ ] 註冊 `create_incident` 工具
    - [ ] input_schema 定義
    - [ ] handler 實現
  - [ ] 註冊 `update_incident` 工具
    - [ ] input_schema 定義
    - [ ] handler 實現
  - [ ] 註冊 `get_incident` 工具
    - [ ] input_schema 定義
    - [ ] handler 實現
  - [ ] 註冊 `create_ritm` 工具
    - [ ] input_schema 定義
    - [ ] handler 實現
  - [ ] 註冊 `get_ritm_status` 工具
    - [ ] input_schema 定義
    - [ ] handler 實現
  - [ ] 註冊 `add_attachment` 工具
    - [ ] input_schema 定義
    - [ ] handler 實現
  - [ ] 工具列表導出方法
  - [ ] 工具描述文檔（tool description 用於 LLM）
- [ ] 更新 `backend/.env.example`
  - [ ] SERVICENOW_INSTANCE_URL
  - [ ] SERVICENOW_USERNAME
  - [ ] SERVICENOW_PASSWORD
  - [ ] SERVICENOW_API_VERSION
  - [ ] SERVICENOW_TIMEOUT
- [ ] 創建 `backend/tests/unit/mcp/test_servicenow_client.py`
  - [ ] 測試 create_incident（Mock HTTP）
  - [ ] 測試 update_incident
  - [ ] 測試 get_incident（by number / by sys_id）
  - [ ] 測試 create_ritm
  - [ ] 測試 get_ritm_status
  - [ ] 測試 add_attachment
  - [ ] 測試錯誤處理（401, 403, 404, 500）
  - [ ] 測試重試機制
- [ ] 創建 `backend/tests/unit/mcp/test_servicenow_server.py`
  - [ ] 測試工具註冊
  - [ ] 測試每個工具的 handler
  - [ ] 測試 input_schema 正確性
  - [ ] 測試工具列表導出
- [ ] 創建 `backend/tests/integration/mcp/test_servicenow_api.py`
  - [ ] 測試連接 ServiceNow 開發實例
  - [ ] 測試建立 Incident
  - [ ] 測試查詢 Incident
  - [ ] 測試更新 Incident
  - [ ] 測試 RITM 操作

## 品質檢查

### 代碼品質
- [ ] 類型提示完整
- [ ] Docstrings 完整
- [ ] 遵循專案代碼風格
- [ ] 模組導出正確
- [ ] 無硬編碼機密

### 測試
- [ ] 單元測試覆蓋率 > 85%
- [ ] 整合測試創建
- [ ] Mock 正確（httpx Mock for ServiceNow）
- [ ] 錯誤場景覆蓋完整

### 安全
- [ ] ServiceNow 密碼從環境變量讀取
- [ ] 不在日誌中輸出密碼或 Token
- [ ] API 回應不洩漏敏感資訊

### 基礎設施
- [ ] Gunicorn 在 Linux 環境測試通過
- [ ] Windows 開發環境仍可用 Uvicorn 直接啟動
- [ ] Multi-Worker 下 Redis session 正常

## 驗收標準

- [ ] ServerConfig 正確區分 dev/staging/prod
- [ ] Gunicorn Multi-Worker 配置就緒（prod 模式）
- [ ] ServiceNow MCP Server 6 個工具全部可用
- [ ] 所有單元測試通過
- [ ] 整合測試通過（ServiceNow 開發實例）
- [ ] 環境變量文檔更新完成

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 40
**開始日期**: TBD
