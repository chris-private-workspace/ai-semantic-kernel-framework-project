# Sprint 47 Checklist: Integration & Polish

> **Phase 11**: Agent-Session Integration
> **Sprint 目標**: 整合測試、錯誤處理優化、文檔完善

---

## 實施檢查清單

### S47-1: 端到端整合測試 (8 pts)

#### 檔案創建
- [ ] 創建 `tests/e2e/test_session_agent_integration.py`
- [ ] 創建 `tests/e2e/conftest.py` (E2E fixtures)

#### Test Fixtures
- [ ] test_agent fixture
- [ ] test_session fixture
- [ ] test_session_with_sensitive_tools fixture
- [ ] async_client fixture

#### 對話流程測試
- [ ] test_complete_conversation_flow
  - [ ] 第一輪對話成功
  - [ ] 第二輪對話保持上下文
  - [ ] 訊息歷史正確記錄
- [ ] test_multi_turn_context_preservation
- [ ] test_long_conversation_handling

#### 工具調用測試
- [ ] test_tool_calling_flow
  - [ ] 工具正確觸發
  - [ ] 工具結果正確返回
  - [ ] 對話繼續正常
- [ ] test_multiple_tool_calls
- [ ] test_tool_call_error_handling

#### 審批流程測試
- [ ] test_tool_approval_flow
  - [ ] 審批請求正確生成
  - [ ] 審批確認正確處理
  - [ ] 審批拒絕正確處理
- [ ] test_approval_timeout
- [ ] test_approval_with_feedback

#### 串流測試
- [ ] test_streaming_response
  - [ ] 多個 chunks 正確接收
  - [ ] 最終 done 事件正確
- [ ] test_sse_format_correctness
- [ ] test_websocket_streaming

#### 並發測試
- [ ] test_concurrent_sessions
  - [ ] 5+ 並發 Session 正常
  - [ ] 各 Session 獨立運作
- [ ] test_concurrent_messages_same_session

#### 錯誤恢復測試
- [ ] test_llm_timeout_recovery
- [ ] test_tool_error_recovery
- [ ] test_websocket_reconnect

---

### S47-2: 錯誤處理與恢復 (7 pts)

#### 檔案創建
- [ ] 創建 `backend/src/domain/sessions/error_handler.py`
- [ ] 創建 `backend/src/domain/sessions/recovery.py`

#### SessionErrorCode 枚舉
- [ ] SESSION_NOT_FOUND
- [ ] SESSION_NOT_ACTIVE
- [ ] SESSION_EXPIRED
- [ ] AGENT_NOT_FOUND
- [ ] AGENT_CONFIG_ERROR
- [ ] LLM_TIMEOUT
- [ ] LLM_RATE_LIMIT
- [ ] LLM_API_ERROR
- [ ] LLM_CONTENT_FILTER
- [ ] TOOL_NOT_FOUND
- [ ] TOOL_EXECUTION_ERROR
- [ ] TOOL_TIMEOUT
- [ ] TOOL_PERMISSION_DENIED
- [ ] INTERNAL_ERROR
- [ ] RATE_LIMIT_EXCEEDED

#### SessionError 類別
- [ ] code: SessionErrorCode
- [ ] message: str
- [ ] details: Dict
- [ ] recoverable: bool
- [ ] timestamp: datetime
- [ ] to_dict() 方法
- [ ] to_event() 方法

#### SessionErrorHandler 類別
- [ ] `__init__(max_retries, retry_delay)`
- [ ] `handle_llm_error(error, context)`
- [ ] `handle_tool_error(error, tool_name, context)`
- [ ] `with_retry(operation, error_handler, context)`

#### SessionRecoveryManager 類別
- [ ] `__init__(session_service, cache)`
- [ ] `save_checkpoint(session_id, state)`
- [ ] `restore_from_checkpoint(session_id)`
- [ ] `handle_websocket_reconnect(session_id, last_event_id)`

#### 日誌記錄
- [ ] 錯誤日誌格式定義
- [ ] 錯誤上下文包含
- [ ] 敏感資訊過濾

#### 測試
- [ ] `tests/unit/domain/sessions/test_error_handler.py`
- [ ] test_handle_llm_timeout
- [ ] test_handle_llm_rate_limit
- [ ] test_handle_tool_error
- [ ] test_with_retry_success
- [ ] test_with_retry_failure
- [ ] test_checkpoint_save_restore

---

### S47-3: 效能優化與監控 (5 pts)

#### 檔案創建
- [ ] 創建 `backend/src/domain/sessions/metrics.py`
- [ ] 更新 `backend/src/core/metrics.py` (如有)

#### Prometheus Counters
- [ ] session_messages_total
- [ ] session_tool_calls_total
- [ ] session_errors_total

#### Prometheus Histograms
- [ ] session_response_time_seconds
- [ ] session_token_usage

#### Prometheus Gauges
- [ ] active_sessions
- [ ] active_websocket_connections

#### MetricsCollector 類別
- [ ] track_message()
- [ ] track_tool_call()
- [ ] track_error()
- [ ] track_response_time()
- [ ] track_tokens()
- [ ] set_active_sessions()
- [ ] set_active_connections()

#### 裝飾器
- [ ] @track_time(operation) 裝飾器

#### Prometheus 端點
- [ ] /metrics 端點暴露
- [ ] 指標正確格式化

#### 測試
- [ ] `tests/unit/domain/sessions/test_metrics.py`
- [ ] test_track_message
- [ ] test_track_response_time
- [ ] test_track_tokens

---

### S47-4: API 文檔與使用指南 (5 pts)

#### 文檔創建
- [ ] 創建 `docs/api/session-agent-integration.md`
- [ ] 更新 OpenAPI schema

#### API 文檔內容
- [ ] 概述章節
- [ ] REST API 端點說明
  - [ ] POST /sessions/{id}/chat
  - [ ] 請求/回應範例
  - [ ] 串流格式說明
- [ ] WebSocket API 說明
  - [ ] 連接流程
  - [ ] 訊息類型定義
  - [ ] 事件格式
- [ ] 錯誤碼說明表
- [ ] 最佳實踐指南

#### OpenAPI 更新
- [ ] /sessions/{id}/chat 端點
- [ ] WebSocket 端點描述
- [ ] Schema 定義
  - [ ] ChatRequest
  - [ ] ChatResponse
  - [ ] ExecutionEvent

#### 使用範例
- [ ] cURL 範例
- [ ] Python 範例
- [ ] JavaScript/WebSocket 範例

#### 測試
- [ ] 文檔範例可執行驗證
- [ ] OpenAPI 規格驗證

---

## 代碼品質檢查

### 格式化與 Lint
- [ ] `black backend/src/domain/sessions/`
- [ ] `isort backend/src/domain/sessions/`
- [ ] `flake8 backend/src/`
- [ ] `mypy backend/src/`

### 測試執行
- [ ] `pytest tests/unit/ -v --cov`
- [ ] `pytest tests/integration/ -v`
- [ ] `pytest tests/e2e/ -v`
- [ ] 單元測試覆蓋率 > 85%
- [ ] E2E 測試全部通過

### 文檔
- [ ] API 文檔完整
- [ ] 錯誤碼文檔完整
- [ ] WebSocket 協議文檔完整

---

## Phase 11 整體驗收

### 功能驗收
- [ ] Session 可與 Agent 正常對話
- [ ] 多輪對話上下文保持
- [ ] 工具調用正常執行
- [ ] 工具審批流程完整
- [ ] 串流回應穩定
- [ ] WebSocket 通訊正常

### 效能驗收
- [ ] 首 Token 延遲 < 2秒
- [ ] 串流回應延遲 < 100ms/chunk
- [ ] WebSocket 延遲 < 50ms
- [ ] 支援 100+ 並發 Session

### 穩定性驗收
- [ ] 錯誤處理覆蓋完整
- [ ] 恢復機制正常運作
- [ ] 無記憶體洩漏
- [ ] 長時間運行穩定

### 文檔驗收
- [ ] API 文檔完整準確
- [ ] 使用範例可執行
- [ ] 錯誤碼說明清楚

---

## 完成確認

### Story 完成
- [ ] S47-1: 端到端整合測試 ✅
- [ ] S47-2: 錯誤處理與恢復 ✅
- [ ] S47-3: 效能優化與監控 ✅
- [ ] S47-4: API 文檔與使用指南 ✅

### Sprint 完成標準
- [ ] 所有 Story 驗收標準達成
- [ ] E2E 測試全部通過
- [ ] 效能指標達標
- [ ] 文檔審查完成
- [ ] Phase 11 整體驗收通過

### Phase 11 總結
- [ ] 所有 Sprint 完成 (45, 46, 47)
- [ ] 總計 90 Story Points 完成
- [ ] Session-Agent 整合功能完整
- [ ] 文檔齊全
- [ ] 準備進入下一階段

---

**創建日期**: 2025-12-23
**Sprint 編號**: 47
**計劃點數**: 25 pts
**Phase 11 總計**: 90 pts
