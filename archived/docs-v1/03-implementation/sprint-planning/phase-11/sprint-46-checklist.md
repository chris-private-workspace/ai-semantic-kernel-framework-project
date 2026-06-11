# Sprint 46 Checklist: Session-Agent Bridge

> **Phase 11**: Agent-Session Integration
> **Sprint 目標**: 建立 Session 與 Agent 的橋接層，實現完整對話流程

---

## 實施檢查清單

### S46-1: SessionAgentBridge 核心 (10 pts)

#### 檔案創建
- [ ] 創建 `backend/src/domain/sessions/bridge.py`
- [ ] 更新 `backend/src/domain/sessions/__init__.py`

#### SessionAgentBridge 類別
- [ ] `__init__(session_service, agent_executor, agent_repository)`
- [ ] `process_message(session_id, content, attachments, stream)`
- [ ] `handle_tool_approval(session_id, approval_id, approved, feedback)`
- [ ] `_get_pending_tool_call(session_id, approval_id)`

#### process_message 流程
- [ ] 驗證 Session 狀態 (必須 ACTIVE)
- [ ] 獲取 Agent 配置
- [ ] 存儲用戶訊息
- [ ] 獲取對話歷史
- [ ] 發送 STARTED 事件
- [ ] 調用 AgentExecutor
- [ ] 累積回應內容
- [ ] 存儲 Assistant 訊息
- [ ] 發送 DONE 事件

#### 錯誤處理
- [ ] Session 不存在錯誤
- [ ] Session 非活躍錯誤
- [ ] Agent 不存在錯誤
- [ ] 執行錯誤捕獲

#### 測試
- [ ] `tests/unit/domain/sessions/test_bridge.py`
- [ ] test_process_message_inactive_session
- [ ] test_process_message_agent_not_found
- [ ] test_process_message_success
- [ ] test_process_message_with_tool_calls
- [ ] test_handle_tool_approval_approved
- [ ] test_handle_tool_approval_rejected

---

### S46-2: WebSocket 訊息處理 (8 pts)

#### 檔案創建
- [ ] 創建 `backend/src/api/v1/sessions/websocket.py`
- [ ] 更新 `backend/src/api/v1/sessions/__init__.py`

#### SessionWebSocketManager 類別
- [ ] `__init__()` - 初始化連接池
- [ ] `set_bridge(bridge)` - 設定橋接層
- [ ] `connect(websocket, session_id)` - 建立連接
- [ ] `disconnect(session_id)` - 斷開連接
- [ ] `handle_message(websocket, session_id, data)` - 處理訊息

#### 訊息類型處理
- [ ] message - 用戶訊息
- [ ] approval - 工具審批
- [ ] heartbeat - 心跳

#### WebSocket 端點
- [ ] `@router.websocket("/sessions/{session_id}/ws")`
- [ ] 連接接受和確認
- [ ] 心跳任務啟動
- [ ] 訊息接收循環
- [ ] 斷線處理

#### 心跳機制
- [ ] `_send_heartbeat(websocket, interval)` 協程
- [ ] 30 秒間隔心跳
- [ ] heartbeat_ack 回應

#### 測試
- [ ] `tests/integration/api/v1/sessions/test_websocket.py`
- [ ] test_websocket_connection
- [ ] test_websocket_message
- [ ] test_websocket_heartbeat
- [ ] test_websocket_disconnect

---

### S46-3: REST API 訊息端點 (7 pts)

#### 檔案創建
- [ ] 創建 `backend/src/api/v1/sessions/chat.py`
- [ ] 更新路由註冊

#### Pydantic Schemas
- [ ] ChatRequest (content, attachments, stream)
- [ ] ChatResponse (message_id, content, tool_calls)

#### REST 端點
- [ ] `@router.post("/sessions/{session_id}/chat")`
- [ ] stream=True → SSE StreamingResponse
- [ ] stream=False → JSON ChatResponse

#### SSE 串流
- [ ] `_stream_response()` 生成器
- [ ] 正確的 `text/event-stream` media type
- [ ] SSE 格式 (`event: xxx\ndata: xxx\n\n`)

#### 同步回應
- [ ] `_sync_response()` 函數
- [ ] 累積所有事件
- [ ] 返回完整 ChatResponse

#### 依賴注入
- [ ] `get_bridge()` 依賴函數
- [ ] SessionAgentBridge 實例獲取

#### 測試
- [ ] `tests/unit/api/v1/sessions/test_chat.py`
- [ ] test_chat_stream_response
- [ ] test_chat_sync_response
- [ ] test_chat_invalid_session
- [ ] test_chat_with_attachments

---

### S46-4: 工具審批流程 (5 pts)

#### 檔案創建
- [ ] 創建 `backend/src/domain/sessions/approval.py`

#### ApprovalStatus 枚舉
- [ ] PENDING - 待審批
- [ ] APPROVED - 已批准
- [ ] REJECTED - 已拒絕
- [ ] EXPIRED - 已過期

#### ToolApprovalRequest 數據類
- [ ] id: str
- [ ] session_id: UUID
- [ ] tool_call: Dict
- [ ] created_at: datetime
- [ ] expires_at: datetime
- [ ] status: ApprovalStatus
- [ ] resolved_at: Optional[datetime]
- [ ] resolved_by: Optional[str]
- [ ] feedback: Optional[str]

#### ToolApprovalManager 類別
- [ ] `__init__(cache, default_timeout)`
- [ ] `create_approval_request(session_id, tool_call, timeout)`
- [ ] `get_approval_request(approval_id)`
- [ ] `resolve_approval(approval_id, approved, resolved_by, feedback)`
- [ ] `get_pending_approvals(session_id)`

#### Redis 存儲
- [ ] approval:{id} key 格式
- [ ] TTL 設定 (default 5 分鐘)
- [ ] 解決後保留 1 小時

#### 測試
- [ ] `tests/unit/domain/sessions/test_approval.py`
- [ ] test_create_approval_request
- [ ] test_get_approval_request
- [ ] test_resolve_approval_approved
- [ ] test_resolve_approval_rejected
- [ ] test_approval_expired
- [ ] test_get_pending_approvals

---

## 代碼品質檢查

### 格式化與 Lint
- [ ] `black backend/src/domain/sessions/`
- [ ] `black backend/src/api/v1/sessions/`
- [ ] `isort backend/src/domain/sessions/`
- [ ] `isort backend/src/api/v1/sessions/`
- [ ] `flake8 backend/src/`
- [ ] `mypy backend/src/`

### 測試執行
- [ ] `pytest tests/unit/domain/sessions/ -v`
- [ ] `pytest tests/unit/api/v1/sessions/ -v`
- [ ] `pytest tests/integration/ -v`
- [ ] 測試覆蓋率 > 85%

### 文檔
- [ ] 所有公開類別有 docstring
- [ ] WebSocket 協議文檔
- [ ] API 端點文檔更新

---

## 整合驗證

### 依賴確認
- [ ] AgentExecutor (Sprint 45) 可用
- [ ] SessionService (Phase 10) 可用
- [ ] RedisCache 可用
- [ ] FastAPI WebSocket 可用

### 功能驗證
- [ ] WebSocket 連接成功建立
- [ ] 訊息正確處理和回應
- [ ] SSE 串流正確格式
- [ ] 工具審批流程完整

### 效能驗證
- [ ] WebSocket 延遲 < 100ms
- [ ] SSE 首字節 < 2秒
- [ ] 心跳間隔穩定

---

## 完成確認

### Story 完成
- [ ] S46-1: SessionAgentBridge 核心 ✅
- [ ] S46-2: WebSocket 訊息處理 ✅
- [ ] S46-3: REST API 訊息端點 ✅
- [ ] S46-4: 工具審批流程 ✅

### Sprint 完成標準
- [ ] 所有 Story 驗收標準達成
- [ ] 單元測試覆蓋率 > 85%
- [ ] 整合測試通過
- [ ] 無 Critical/High 問題
- [ ] 文檔更新完成

---

**創建日期**: 2025-12-23
**Sprint 編號**: 46
**計劃點數**: 30 pts
