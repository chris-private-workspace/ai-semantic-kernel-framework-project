# Sprint 48 Checklist: Core SDK Integration - Claude Agent SDK 核心整合

**Sprint 目標**: 實現 Claude Agent SDK 核心功能
**週期**: Week 1-2
**總點數**: 35 點
**狀態**: ✅ 已完成 (35/35 點)
**完成日期**: 2025-12-25

---

## 快速驗證命令

```bash
# 啟動服務
cd backend
uvicorn main:app --reload --port 8000

# 執行單元測試
pytest tests/unit/integrations/claude_sdk/ -v

# 執行整合測試
pytest tests/integration/claude_sdk/ -v

# 測試 API 端點
curl -X POST http://localhost:8000/api/v1/claude-sdk/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"prompt": "What is 2+2?"}'

# 檢查型別
mypy src/integrations/claude_sdk/
```

---

## S48-1: ClaudeSDKClient 核心封裝 (10 點) ✅

### 檔案結構
- [x] 建立 `backend/src/integrations/claude_sdk/` 目錄
- [x] 建立 `backend/src/integrations/claude_sdk/__init__.py`
- [x] 建立 `backend/src/integrations/claude_sdk/client.py`
- [x] 建立 `backend/src/integrations/claude_sdk/config.py`
- [x] 建立 `backend/src/integrations/claude_sdk/exceptions.py`

### ClaudeSDKClient 實現
- [x] `ClaudeSDKClient.__init__()` 支援 api_key 參數
- [x] `ClaudeSDKClient.__init__()` 支援 model 參數
- [x] `ClaudeSDKClient.__init__()` 支援 max_tokens 參數
- [x] `ClaudeSDKClient.__init__()` 支援 timeout 參數
- [x] `ClaudeSDKClient.__init__()` 支援 system_prompt 參數
- [x] `ClaudeSDKClient.__init__()` 支援 tools 參數
- [x] `ClaudeSDKClient.__init__()` 支援 hooks 參數
- [x] `ClaudeSDKClient.__init__()` 支援 mcp_servers 參數

### 配置管理
- [x] `ClaudeSDKConfig` 從環境變數讀取 API Key
- [x] `ClaudeSDKConfig` 從環境變數讀取模型設定
- [x] `ClaudeSDKConfig.from_env()` 方法實現
- [x] `ClaudeSDKConfig.from_yaml()` 方法實現

### 異常類別
- [x] `ClaudeSDKError` 基礎異常類別
- [x] `AuthenticationError` 認證錯誤
- [x] `RateLimitError` 速率限制錯誤
- [x] `TimeoutError` 超時錯誤
- [x] `ToolError` 工具執行錯誤 (使用 tool_args 避免與 Exception.args 衝突)
- [x] `HookRejectionError` Hook 拒絕錯誤
- [x] `MCPError` MCP 相關錯誤
- [x] `MCPConnectionError` MCP 連接錯誤
- [x] `MCPToolError` MCP 工具錯誤

### 測試
- [x] `test_client_init_with_api_key` 通過
- [x] `test_client_init_from_env` 通過
- [x] `test_client_init_missing_key_raises_error` 通過
- [x] `test_config_from_yaml` 通過

---

## S48-2: Query API 實現 (8 點) ✅

### Query 模組
- [x] 建立 `backend/src/integrations/claude_sdk/query.py`
- [x] 建立 `backend/src/integrations/claude_sdk/types.py`

### QueryResult 類別
- [x] `QueryResult.content` 屬性
- [x] `QueryResult.tool_calls` 屬性
- [x] `QueryResult.tokens_used` 屬性
- [x] `QueryResult.duration` 屬性
- [x] `QueryResult.status` 屬性
- [x] `QueryResult.successful` 屬性

### execute_query 函數
- [x] 接受 prompt 參數
- [x] 接受 tools 參數
- [x] 接受 max_tokens 參數
- [x] 接受 timeout 參數
- [x] 接受 working_directory 參數
- [x] 實現 agentic loop (工具調用循環)
- [x] 正確累計 token 使用量
- [x] 超時處理實現
- [x] 錯誤處理實現

### 型別定義
- [x] `ToolCall` dataclass 定義
- [x] `Message` dataclass 定義
- [x] `ToolCallContext` dataclass 定義
- [x] `ToolResultContext` dataclass 定義
- [x] `QueryContext` dataclass 定義
- [x] `HookResult` 類別定義

### 測試
- [x] `test_query_returns_result` 通過
- [x] `test_query_with_tools` 通過
- [x] `test_query_timeout` 通過
- [x] `test_query_error_handling` 通過

---

## S48-3: Session 管理實現 (10 點) ✅

### Session 模組
- [x] 建立 `backend/src/integrations/claude_sdk/session.py`

### Session 類別
- [x] `Session.__init__()` 實現
- [x] `Session.session_id` 屬性
- [x] `Session.is_closed` 屬性
- [x] `Session.get_history()` 方法
- [x] `Session.get_context()` 方法
- [x] `Session.add_context()` 方法
- [x] `Session.query()` 方法
- [x] `Session.fork()` 方法
- [x] `Session.close()` 方法

### SessionResponse 類別
- [x] `SessionResponse.content` 屬性
- [x] `SessionResponse.tool_calls` 屬性
- [x] `SessionResponse.tokens_used` 屬性
- [x] `SessionResponse.message_index` 屬性

### 歷史管理
- [x] 用戶訊息正確加入歷史
- [x] 助理回應正確加入歷史
- [x] 工具調用記錄在歷史中
- [x] `_build_messages()` 正確構建 API 訊息

### Hook 整合
- [x] `on_session_start` 在建立時觸發
- [x] `on_query_start` 在查詢前觸發
- [x] `on_tool_call` 在工具調用前觸發
- [x] `on_tool_result` 在工具完成後觸發
- [x] `on_query_end` 在查詢完成後觸發
- [x] `on_session_end` 在關閉時觸發

### ClaudeSDKClient Session 方法
- [x] `create_session()` 方法實現
- [x] `resume_session()` 方法實現
- [x] Session 儲存在 `_sessions` 字典中

### 測試
- [x] `test_create_session` 通過
- [x] `test_session_query` 通過
- [x] `test_session_history` 通過
- [x] `test_session_fork` 通過
- [x] `test_session_close` 通過
- [x] `test_session_context` 通過

---

## S48-4: API 端點整合 (7 點) ✅

### API 路由
- [x] 建立 `backend/src/api/v1/claude_sdk/` 目錄
- [x] 建立 `backend/src/api/v1/claude_sdk/__init__.py`
- [x] 建立 `backend/src/api/v1/claude_sdk/routes.py`
- [x] 建立 `backend/src/api/v1/claude_sdk/schemas.py`

### 端點實現
- [x] `POST /api/v1/claude-sdk/query` 端點
- [x] `POST /api/v1/claude-sdk/sessions` 端點
- [x] `POST /api/v1/claude-sdk/sessions/{id}/query` 端點
- [x] `DELETE /api/v1/claude-sdk/sessions/{id}` 端點
- [x] `GET /api/v1/claude-sdk/sessions/{id}/history` 端點
- [x] `GET /api/v1/claude-sdk/health` 端點 (健康檢查)

### Request/Response Schema
- [x] `QueryRequest` schema
- [x] `QueryResponse` schema
- [x] `CreateSessionRequest` schema
- [x] `SessionResponse` schema
- [x] `SessionQueryRequest` schema
- [x] `SessionQueryResponse` schema
- [x] `SessionHistoryMessageSchema` schema (timestamp 使用 float 格式)

### 整合
- [x] 路由註冊到 FastAPI app
- [x] 依賴注入 (`get_client`, `get_optional_client`)
- [x] 錯誤處理整合

### 測試
- [x] `test_query_endpoint` 通過
- [x] `test_create_session_endpoint` 通過
- [x] `test_session_query_endpoint` 通過
- [x] `test_close_session_endpoint` 通過
- [x] `test_session_history_endpoint` 通過
- [x] `test_health_check_healthy` 通過
- [x] `test_health_check_unconfigured` 通過

---

## 測試完成

### 單元測試
- [x] `tests/unit/integrations/claude_sdk/test_client.py`
- [x] `tests/unit/integrations/claude_sdk/test_query.py`
- [x] `tests/unit/integrations/claude_sdk/test_session.py`
- [x] `tests/unit/integrations/claude_sdk/test_config.py`
- [x] `tests/unit/integrations/claude_sdk/test_exceptions.py`
- [x] `tests/unit/api/v1/claude_sdk/test_routes.py`

### 整合測試
- [x] 基礎整合測試 (透過單元測試驗證)

### 覆蓋率
- [x] 單元測試覆蓋率 ≥ 85%
- [x] 所有 91 個測試通過

---

## 修復記錄

### 問題 1: ToolError.args 屬性衝突
- **問題**: Python 的 `Exception` 基類有內建的 `args` 屬性，與 `ToolError.args` 衝突
- **解決**: 將屬性從 `args` 重命名為 `tool_args`
- **影響檔案**:
  - `exceptions.py`
  - `test_exceptions.py`

### 問題 2: SessionHistoryMessageSchema timestamp 類型
- **問題**: Schema 期望 `timestamp: float`，但測試提供 `datetime.now()`
- **解決**: 改用 `time.time()` 返回 Unix 時間戳 (float)
- **影響檔案**: `test_routes.py`

### 問題 3: Health Check 依賴注入
- **問題**: 使用 `patch()` 無法正確覆蓋 FastAPI 依賴
- **解決**: 使用 `app.dependency_overrides[get_optional_client] = mock_get_optional`
- **影響檔案**: `test_routes.py`

---

## Sprint 完成標準

- [x] 所有 checkbox 完成
- [x] 所有測試通過 (91/91)
- [x] Code Review 完成
- [x] 無 Critical/High Bug
- [x] 文檔更新完成

---

## 依賴確認

### 外部依賴
- [x] `anthropic` Python SDK 安裝
- [x] `ANTHROPIC_API_KEY` 環境變數配置 (測試使用 mock)
- [x] Redis 服務運行中 (用於 Session 狀態)

### 內部依賴
- [x] Phase 11 Agent-Session Integration 完成
- [x] 認證系統正常運作

---

## 完成統計表

| Story | 點數 | 狀態 | 完成日期 |
|-------|------|------|----------|
| S48-1 | 10 | ✅ | 2025-12-25 |
| S48-2 | 8 | ✅ | 2025-12-25 |
| S48-3 | 10 | ✅ | 2025-12-25 |
| S48-4 | 7 | ✅ | 2025-12-25 |
| **總計** | **35** | **100%** | 2025-12-25 |
