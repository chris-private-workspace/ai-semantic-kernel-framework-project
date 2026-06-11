# Sprint 113 Checklist: MCP Security + Validation

## 開發任務

### Story 113-1: MCP Permission 運行時啟用
- [ ] **分析現有 Permission 定義**
  - [ ] 搜索 `backend/src/integrations/mcp/` 中所有 permission pattern 定義
  - [ ] 記錄 28 個 permission patterns 清單
  - [ ] 搜索 `check_permission` 函數定義位置
  - [ ] 確認 0 處運行時調用（驗證問題存在）
- [ ] **實現 Permission 檢查機制**
  - [ ] 確認/新增 `check_permission()` 函數
  - [ ] 添加 `MCP_PERMISSION_MODE` 環境變量支持 (log/enforce)
  - [ ] 實現 log-only 模式（WARNING 日誌，不阻斷）
  - [ ] 實現 enforce 模式（拒絕無權限操作，返回 403）
  - [ ] 實現 `_evaluate_permission()` 內部邏輯
- [ ] **Azure MCP Server**
  - [ ] 找到所有 handler 函數
  - [ ] 在每個 handler 中插入 `check_permission` 調用
  - [ ] 對應 `azure:*` permission patterns
- [ ] **Filesystem MCP Server**
  - [ ] 找到所有 handler 函數
  - [ ] 在 read handler 中插入 `filesystem:read` 檢查
  - [ ] 在 write handler 中插入 `filesystem:write` 檢查
  - [ ] 在 delete handler 中插入 `filesystem:delete` 檢查
- [ ] **LDAP MCP Server**
  - [ ] 找到所有 handler 函數
  - [ ] 在 read handler 中插入 `ldap:read` 檢查
  - [ ] 在 write handler 中插入 `ldap:write` 檢查
- [ ] **Shell MCP Server**
  - [ ] 找到 execute handler
  - [ ] 插入 `shell:execute` 檢查
- [ ] **SSH MCP Server**
  - [ ] 找到 connect handler
  - [ ] 插入 `ssh:connect` 檢查
  - [ ] 找到 execute handler
  - [ ] 插入 `ssh:execute` 檢查
- [ ] **測試**
  - [ ] 單元測試: log-only 模式不阻斷但記錄 WARNING
  - [ ] 單元測試: enforce 模式拒絕無權限操作
  - [ ] 單元測試: 有權限操作正常通過
  - [ ] 驗證 28 個 patterns 全部有對應檢查

### Story 113-2: Shell/SSH MCP 命令白名單
- [ ] **建立白名單模組**
  - [ ] 創建 `backend/src/integrations/mcp/security/` 目錄
  - [ ] 創建 `__init__.py`
  - [ ] 創建 `command_whitelist.py`
- [ ] **實現 CommandWhitelist 類**
  - [ ] 定義 `DEFAULT_WHITELIST` 常量（安全唯讀命令）
  - [ ] 定義 `BLOCKED_PATTERNS` 常量（明確封鎖的危險模式）
  - [ ] 實現 `__init__()` (支持額外白名單擴展)
  - [ ] 實現 `check_command()` → "allowed"/"blocked"/"requires_approval"
  - [ ] 編譯 BLOCKED_PATTERNS 正則表達式
  - [ ] 添加類型註解和 docstrings
- [ ] **整合到 Shell MCP handler**
  - [ ] 匯入 CommandWhitelist
  - [ ] 在命令執行前調用 `check_command()`
  - [ ] "allowed" → 直接執行
  - [ ] "blocked" → 拒絕並返回 403
  - [ ] "requires_approval" → 觸發 HITL 審批
  - [ ] HITL 拒絕 → 不執行
  - [ ] HITL 批准 → 執行
- [ ] **整合到 SSH MCP handler**
  - [ ] 匯入 CommandWhitelist
  - [ ] 在命令執行前調用 `check_command()`
  - [ ] 與 Shell handler 相同的三路邏輯
- [ ] **配置支持**
  - [ ] 支持環境變量 `MCP_ADDITIONAL_WHITELIST` (逗號分隔)
  - [ ] 支持配置文件擴展白名單（可選）
- [ ] **測試**
  - [ ] 單元測試: 白名單命令 → "allowed"
  - [ ] 單元測試: 封鎖命令 → "blocked" (rm -rf, format, dd 等)
  - [ ] 單元測試: 非白名單命令 → "requires_approval"
  - [ ] 單元測試: 額外白名單擴展生效
  - [ ] 整合測試: Shell handler 白名單流程
  - [ ] 整合測試: SSH handler 白名單流程

### Story 113-3: ContextSynchronizer asyncio.Lock
- [ ] 搜索 `class ContextSynchronizer` 定義位置 (預期 2 處)
- [ ] **第 1 個 ContextSynchronizer**
  - [ ] 記錄文件路徑
  - [ ] 匯入 `asyncio`
  - [ ] 在 `__init__` 中添加 `self._lock = asyncio.Lock()`
  - [ ] 在 `sync_context()` 中添加 `async with self._lock:`
  - [ ] 在 `get_context()` 中添加 `async with self._lock:`
  - [ ] 返回 context 副本（`{**ctx}`）而非原始引用
  - [ ] 存儲 context 時使用副本（`{**context}`）
- [ ] **第 2 個 ContextSynchronizer**
  - [ ] 記錄文件路徑
  - [ ] 匯入 `asyncio`
  - [ ] 在 `__init__` 中添加 `self._lock = asyncio.Lock()`
  - [ ] 在 `sync_context()` 中添加 `async with self._lock:`
  - [ ] 在 `get_context()` 中添加 `async with self._lock:`
  - [ ] 返回 context 副本而非原始引用
  - [ ] 存儲 context 時使用副本
- [ ] **測試**
  - [ ] 單元測試: 並發寫入不丟失數據 (asyncio.gather)
  - [ ] 單元測試: 並發讀取不返回部分更新的數據
  - [ ] 單元測試: 返回的是副本不是原始引用

### Story 113-4: 全局異常處理器修復
- [ ] 搜索全局異常處理器定義位置
- [ ] 確認當前是否洩漏 `error_type`
- [ ] 確認當前是否洩漏 `traceback`
- [ ] 修改 production 環境回應：僅 `"error": "Internal server error"`
- [ ] 修改 development 環境回應：包含 `detail`（不含 error_type/traceback）
- [ ] 添加 `logger.error()` 記錄完整錯誤（含 exc_info=True）
- [ ] 添加 request path 到日誌上下文
- [ ] 確認 HTTPException (4xx) 不受影響（正常返回）
- [ ] 單元測試: production 環境回應無 error_type
- [ ] 單元測試: development 環境回應有 detail
- [ ] 單元測試: 錯誤正確記錄到日誌

### Story 113-5: Phase 31 整合測試 + 安全掃描
- [ ] **整合測試文件**
  - [ ] 創建 `backend/tests/integration/security/` 目錄
  - [ ] 創建 `__init__.py`
  - [ ] 創建 `test_phase31_integration.py`
- [ ] **Sprint 111 驗證測試**
  - [ ] test_cors_origin_correct
  - [ ] test_no_hardcoded_jwt_secret
  - [ ] test_no_console_log_in_auth_store
  - [ ] test_unauthenticated_request_returns_401
  - [ ] test_expired_token_returns_401
  - [ ] test_valid_token_passes
  - [ ] test_public_routes_no_auth
  - [ ] test_rate_limiting_returns_429
- [ ] **Sprint 112 驗證測試**
  - [ ] test_no_mock_in_production_code
  - [ ] test_factory_production_no_fallback
  - [ ] test_redis_approval_storage
- [ ] **Sprint 113 驗證測試**
  - [ ] test_mcp_permission_check_called
  - [ ] test_shell_whitelist_blocks_dangerous
  - [ ] test_shell_non_whitelist_requires_approval
  - [ ] test_context_synchronizer_thread_safe
  - [ ] test_error_response_no_leak
- [ ] **安全掃描**
  - [ ] 掃描硬編碼 secrets → 0 結果
  - [ ] 掃描 console.log PII → 0 結果
  - [ ] 掃描 Mock in production → 0 結果
  - [ ] Auth 覆蓋率全端點驗證 → 100%
  - [ ] Rate Limiting 觸發驗證 → 429
  - [ ] MCP Permission 調用驗證 → 被調用
  - [ ] 錯誤回應洩漏驗證 → 無洩漏
- [ ] **安全評分確認**
  - [ ] Auth 覆蓋率: 7% → 100%
  - [ ] Rate Limiting: 無 → 全局
  - [ ] JWT Secret: 硬編碼 → 環境變量
  - [ ] MCP Permission: 0 檢查 → 28 啟用
  - [ ] Mock in Production: 18 → 0
  - [ ] PII 洩漏: 5 → 0
  - [ ] 預設弱密碼: 有 → 無
  - [ ] 整體安全評分: 1/10 → 6/10

## 品質檢查

### 代碼品質
- [ ] Black 格式化通過 (backend)
- [ ] isort 排序通過 (backend)
- [ ] flake8 檢查通過 (backend)
- [ ] mypy 類型檢查通過 (backend)
- [ ] 無 unused imports
- [ ] Docstrings 完整

### 測試
- [ ] MCP Permission 單元測試通過
- [ ] CommandWhitelist 單元測試通過
- [ ] ContextSynchronizer 並發測試通過
- [ ] 全局異常處理器測試通過
- [ ] Phase 31 整合測試全部通過
- [ ] 安全掃描全部通過
- [ ] 現有測試套件無回歸

### 文檔
- [ ] MCP Permission 使用方式文檔
- [ ] 命令白名單配置文檔
- [ ] Phase 31 安全改善總結

## 驗收標準

- [ ] MCP 28 permission patterns 全部有運行時 check_permission 調用
- [ ] Shell/SSH 命令白名單生效
- [ ] 封鎖命令返回 403
- [ ] 非白名單命令觸發 HITL
- [ ] 2 個 ContextSynchronizer 有 asyncio.Lock
- [ ] 全局異常處理器不洩漏 error_type
- [ ] Phase 31 整合測試 = 全部通過
- [ ] 安全掃描 = 無 CRITICAL
- [ ] 安全評分 = 6/10 (從 1/10 提升)

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 40
**開始日期**: TBD
