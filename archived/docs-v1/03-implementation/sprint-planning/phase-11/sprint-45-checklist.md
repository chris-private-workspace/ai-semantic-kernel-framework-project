# Sprint 45 Checklist: Agent Executor Core

> **Phase 11**: Agent-Session Integration
> **Sprint 目標**: 建立統一的 Agent 執行器，整合 LLM 調用與串流支援

---

## 實施檢查清單

### S45-1: AgentExecutor 核心類別 (13 pts)

#### 檔案創建
- [ ] 創建 `backend/src/domain/sessions/executor.py`
- [ ] 創建 `backend/src/domain/sessions/__init__.py` (更新 exports)

#### ExecutionEventType 枚舉
- [ ] CONTENT - 文字內容事件
- [ ] TOOL_CALL - 工具調用事件
- [ ] TOOL_RESULT - 工具結果事件
- [ ] ERROR - 錯誤事件
- [ ] DONE - 完成事件

#### ExecutionEvent 數據類
- [ ] type: ExecutionEventType
- [ ] data: Any
- [ ] metadata: Optional[Dict]
- [ ] to_dict() 方法
- [ ] to_json() 方法

#### AgentExecutor 類別
- [ ] `__init__(llm_service, tool_registry, mcp_client)`
- [ ] `execute(agent, messages, stream)` - 主執行方法
- [ ] `_build_messages(agent, messages)` - 構建 LLM 訊息
- [ ] `_get_available_tools(agent)` - 獲取可用工具
- [ ] 同步執行模式支援
- [ ] 非同步執行模式支援

#### 測試
- [ ] `tests/unit/domain/sessions/test_executor.py`
- [ ] test_build_messages_with_system_prompt
- [ ] test_build_messages_with_history
- [ ] test_get_available_tools_empty
- [ ] test_get_available_tools_with_tools
- [ ] test_execute_sync_mode
- [ ] test_execute_stream_mode

---

### S45-2: LLM 串流整合 (10 pts)

#### 檔案創建
- [ ] 創建 `backend/src/domain/sessions/streaming.py`

#### StreamingLLMHandler 類別
- [ ] `__init__(client, deployment, timeout, max_retries)`
- [ ] `stream_completion(messages, tools, temperature, max_tokens)`
- [ ] `_accumulate_tool_call(tool_calls, delta_tc)` - 累積工具調用
- [ ] `_estimate_usage(messages, response)` - Token 使用量估算

#### 串流處理
- [ ] Azure OpenAI 串流調用
- [ ] Content delta 處理
- [ ] Tool call delta 累積
- [ ] 完成事件發送

#### 錯誤處理
- [ ] Timeout 處理 (asyncio.TimeoutError)
- [ ] API 錯誤處理
- [ ] 重試邏輯實現
- [ ] 錯誤事件發送

#### 測試
- [ ] `tests/unit/domain/sessions/test_streaming.py`
- [ ] test_stream_completion_success
- [ ] test_stream_completion_timeout
- [ ] test_stream_completion_api_error
- [ ] test_accumulate_tool_call
- [ ] test_estimate_usage

---

### S45-3: 工具調用框架 (8 pts)

#### 檔案創建
- [ ] 創建 `backend/src/domain/sessions/tool_handler.py`

#### ToolCall 數據結構
- [ ] id: str
- [ ] function: ToolFunction

#### ToolFunction 數據結構
- [ ] name: str
- [ ] arguments: str (JSON)

#### ToolCallHandler 類別
- [ ] `__init__(mcp_client, permission_checker)`
- [ ] `handle_tool_calls(tool_calls, session_context)`
- [ ] 權限檢查整合
- [ ] MCP 工具執行
- [ ] 結果格式化

#### 權限檢查
- [ ] PermissionChecker 介面定義
- [ ] 需要審批的工具識別
- [ ] approval_required 事件發送

#### 測試
- [ ] `tests/unit/domain/sessions/test_tool_handler.py`
- [ ] test_handle_tool_call_success
- [ ] test_handle_tool_call_error
- [ ] test_permission_check_required
- [ ] test_permission_check_approved
- [ ] test_multiple_tool_calls

---

### S45-4: 執行事件系統 (4 pts)

#### 檔案創建
- [ ] 創建 `backend/src/domain/sessions/events.py`

#### ExecutionEventType 完整定義
- [ ] CONTENT - 完整內容
- [ ] CONTENT_DELTA - 內容增量
- [ ] TOOL_CALL - 工具調用
- [ ] TOOL_RESULT - 工具結果
- [ ] APPROVAL_REQUIRED - 需要審批
- [ ] APPROVAL_RESPONSE - 審批回應
- [ ] STARTED - 開始執行
- [ ] DONE - 執行完成
- [ ] ERROR - 執行錯誤
- [ ] HEARTBEAT - 心跳

#### ExecutionEvent 類別
- [ ] event_id 自動生成
- [ ] timestamp 自動設定
- [ ] to_dict() 序列化
- [ ] to_json() JSON 格式
- [ ] to_sse() SSE 格式
- [ ] to_websocket() WebSocket 格式

#### 測試
- [ ] `tests/unit/domain/sessions/test_events.py`
- [ ] test_event_creation_auto_fields
- [ ] test_to_dict_serialization
- [ ] test_to_json_format
- [ ] test_to_sse_format
- [ ] test_to_websocket_format

---

## 代碼品質檢查

### 格式化與 Lint
- [ ] `black backend/src/domain/sessions/`
- [ ] `isort backend/src/domain/sessions/`
- [ ] `flake8 backend/src/domain/sessions/`
- [ ] `mypy backend/src/domain/sessions/`

### 測試執行
- [ ] `pytest tests/unit/domain/sessions/ -v`
- [ ] 測試覆蓋率 > 85%
- [ ] 無跳過的測試

### 文檔
- [ ] 所有公開類別有 docstring
- [ ] 所有公開方法有 docstring
- [ ] 複雜邏輯有行內註釋

---

## 整合驗證

### 依賴確認
- [ ] LLMService (Phase 3) 可用
- [ ] MCPClient (Phase 9) 可用
- [ ] ToolRegistry (Phase 9) 可用
- [ ] SessionService (Phase 10) 可用

### 功能驗證
- [ ] AgentExecutor 可正常實例化
- [ ] 訊息構建正確包含 system prompt
- [ ] 串流回應正確生成事件
- [ ] 工具調用正確執行
- [ ] 錯誤正確捕獲和報告

### 效能驗證
- [ ] 首個 token 回應 < 2秒
- [ ] 串流無明顯延遲
- [ ] Token 計數準確

---

## 完成確認

### Story 完成
- [ ] S45-1: AgentExecutor 核心類別 ✅
- [ ] S45-2: LLM 串流整合 ✅
- [ ] S45-3: 工具調用框架 ✅
- [ ] S45-4: 執行事件系統 ✅

### Sprint 完成標準
- [ ] 所有 Story 驗收標準達成
- [ ] 單元測試覆蓋率 > 85%
- [ ] 代碼審查完成
- [ ] 無 Critical/High 問題
- [ ] 文檔更新完成

---

**創建日期**: 2025-12-23
**Sprint 編號**: 45
**計劃點數**: 35 pts
