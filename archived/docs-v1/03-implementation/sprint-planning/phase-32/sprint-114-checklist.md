# Sprint 114 Checklist: AD 場景基礎建設

## 開發任務

### Story 114-1: PatternMatcher AD 規則庫
- [ ] 備份現有 `rules.yaml`
- [ ] 新增 `ad_account_management` 頂層區塊
- [ ] 定義 `account_unlock` 規則（3+ patterns, intent, risk_level）
- [ ] 定義 `password_reset` 規則（3+ patterns, intent, risk_level）
- [ ] 定義 `group_membership` 規則（4+ patterns, intent, risk_level）
- [ ] 定義 `account_create` 規則（3+ patterns, intent, risk_level）
- [ ] 定義 `account_disable` 規則（3+ patterns, intent, risk_level）
- [ ] 每條規則包含 `required_tools` 欄位
- [ ] 每條規則包含 `workflow_type` 欄位
- [ ] 驗證現有 34 條規則未受影響
- [ ] 創建 `backend/tests/unit/orchestration/test_ad_pattern_rules.py`
  - [ ] 測試帳號解鎖中文匹配
  - [ ] 測試帳號解鎖英文匹配
  - [ ] 測試密碼重設匹配
  - [ ] 測試群組異動匹配
  - [ ] 測試帳號建立匹配
  - [ ] 測試帳號停用匹配
  - [ ] 測試不匹配場景（fallback）
  - [ ] 回歸測試現有規則

### Story 114-2: LDAP MCP Server 配置
- [ ] 創建 `backend/src/integrations/mcp/ldap_config.py`
  - [ ] 定義 `LDAPConfig` Pydantic model
  - [ ] 定義 server_url, bind_dn, bind_password 等欄位
  - [ ] 定義 search_base, user_search_base, group_search_base
  - [ ] 定義 use_ssl, connection_timeout, operation_timeout, pool_size
- [ ] 修改 `backend/src/integrations/mcp/ldap_server.py`
  - [ ] 注入 `LDAPConfig`
  - [ ] 配置連接池
  - [ ] 驗證帳號查詢操作（search_s）
  - [ ] 驗證帳號解鎖操作（modify_s lockoutTime）
  - [ ] 驗證密碼重設操作（modify_s unicodePwd）
  - [ ] 驗證群組查詢操作
  - [ ] 驗證群組修改操作（modify_s member）
- [ ] 更新 `backend/.env.example` 添加 LDAP 環境變量
- [ ] 創建 `backend/tests/integration/mcp/test_ldap_connectivity.py`
  - [ ] 測試連接建立
  - [ ] 測試認證成功/失敗
  - [ ] 測試帳號查詢
  - [ ] 測試操作逾時處理
  - [ ] 測試連接池回收

### Story 114-3: ServiceNow Webhook 真實實現
- [ ] 創建 `backend/src/integrations/orchestration/input/` 目錄
- [ ] 創建 `__init__.py`
- [ ] 創建 `servicenow_webhook.py`
  - [ ] 定義 `ServiceNowRITMEvent` Pydantic model
  - [ ] 定義 `WebhookAuthConfig` model
  - [ ] 實現 `ServiceNowWebhookReceiver` 類
  - [ ] 實現 `validate_request()` — shared secret 驗證
  - [ ] 實現 `validate_request()` — IP 白名單驗證
  - [ ] 實現 `parse_ritm_event()` — payload 解析
  - [ ] 實現 `process_event()` — 事件處理轉換
  - [ ] 實現冪等處理（重複事件檢測）
- [ ] 創建 `backend/src/api/v1/orchestration/webhooks.py`
  - [ ] 定義 `POST /api/v1/orchestration/webhooks/servicenow` 端點
  - [ ] 注入 `ServiceNowWebhookReceiver` 依賴
  - [ ] 實現請求驗證 middleware
  - [ ] 返回 tracking_id
  - [ ] 錯誤處理（401, 400, 409, 500）
- [ ] 在主 router 中註冊 webhook 端點
- [ ] 創建 `backend/tests/unit/orchestration/test_servicenow_webhook.py`
  - [ ] 測試 payload 解析（有效/無效）
  - [ ] 測試認證驗證（成功/失敗）
  - [ ] 測試冪等處理
- [ ] 創建 `backend/tests/integration/orchestration/test_webhook_api.py`
  - [ ] 測試端點可存取
  - [ ] 測試完整請求流程
  - [ ] 測試認證失敗回應

### Story 114-4: RITM→Intent 映射管道
- [ ] 創建 `backend/src/integrations/orchestration/input/ritm_mappings.yaml`
  - [ ] 定義 AD Account Unlock 映射
  - [ ] 定義 AD Password Reset 映射
  - [ ] 定義 AD Group Membership Change 映射
  - [ ] 定義 New AD Account 映射
  - [ ] 定義 Disable AD Account 映射
  - [ ] 定義 fallback 策略配置
- [ ] 創建 `backend/src/integrations/orchestration/input/ritm_intent_mapper.py`
  - [ ] 實現 `RITMIntentMapper` 類
  - [ ] 實現 `_load_mappings()` — YAML 讀取
  - [ ] 實現 `map_ritm_to_intent()` — 映射邏輯
  - [ ] 實現 `extract_variables()` — 變量提取（支持巢狀路徑）
  - [ ] 實現 fallback 處理
- [ ] 創建 `backend/tests/unit/orchestration/test_ritm_intent_mapper.py`
  - [ ] 測試各 Catalog Item 映射正確性
  - [ ] 測試變量提取（一般路徑、巢狀路徑）
  - [ ] 測試未知 Catalog Item fallback
  - [ ] 測試映射文件載入錯誤處理

## 品質檢查

### 代碼品質
- [ ] 類型提示完整
- [ ] Docstrings 完整（所有公開類和函數）
- [ ] 遵循專案代碼風格（Black + isort）
- [ ] 模組導出正確（`__all__`）
- [ ] 無硬編碼機密（密碼、金鑰從環境變量讀取）

### 測試
- [ ] 單元測試創建且通過
- [ ] 整合測試創建且通過
- [ ] 測試覆蓋率 > 85%
- [ ] 回歸測試：現有 PatternMatcher 規則不受影響

### 安全
- [ ] Webhook 認證機制完整
- [ ] LDAP 密碼不在日誌中出現
- [ ] IP 白名單功能可用
- [ ] 環境變量文檔已更新

## 驗收標準

- [ ] PatternMatcher 正確匹配所有 5 類 AD 帳號管理模式
- [ ] LDAP MCP Server 連接 AD 並完成 5 項基本操作驗證
- [ ] ServiceNow Webhook 接收、驗證、解析 RITM 事件
- [ ] RITM Catalog Item 正確映射到 IPA Business Intent
- [ ] 所有單元測試和整合測試通過
- [ ] 環境變量文檔更新完成

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 40
**開始日期**: TBD
