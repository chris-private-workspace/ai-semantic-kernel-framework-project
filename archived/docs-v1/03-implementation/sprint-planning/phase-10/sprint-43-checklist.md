# Sprint 43 Checklist: Real-time Communication

**Sprint 目標**: 實現 WebSocket 即時通訊和串流響應
**總點數**: 35 Story Points
**狀態**: 📋 計劃中
**前置條件**: Sprint 42 完成
**開始日期**: TBD

---

## 前置條件檢查

### Sprint 42 完成確認
- [ ] Session 領域模型完整
- [ ] Session 存儲層正常
- [ ] Session REST API 可用

### 環境準備
- [ ] 確認 websockets 已安裝
- [ ] 確認 Redis Pub/Sub 可用

---

## Story Checklist

### S43-1: WebSocket 基礎設施 (10 pts)

**狀態**: ⏳ 未開始

#### 實現任務

**創建目錄結構**
- [ ] 創建 `backend/src/infrastructure/websocket/`
- [ ] 創建 `backend/src/infrastructure/websocket/__init__.py`

**實現 Connection 類** (`infrastructure/websocket/manager.py`)
- [ ] `Connection` 數據類
  - [ ] websocket, session_id, user_id
  - [ ] connected_at, last_ping
  - [ ] `send()` 方法
  - [ ] `close()` 方法

**實現 ConnectionManager**
- [ ] `__init__(heartbeat_interval)` 初始化
- [ ] `connect()` 建立連接
  - [ ] 接受 WebSocket
  - [ ] 關閉舊連接
  - [ ] 記錄連接
- [ ] `disconnect()` 斷開連接
- [ ] `send_to_session()` 發送到 Session
- [ ] `broadcast_to_user()` 廣播給用戶
- [ ] `get_connection()` 獲取連接
- [ ] `is_connected()` 檢查連接狀態
- [ ] `start_heartbeat()` 啟動心跳
- [ ] `stop_heartbeat()` 停止心跳
- [ ] `_heartbeat_loop()` 心跳循環

**實現 WebSocket 協議** (`infrastructure/websocket/protocols.py`)
- [ ] `MessageType` 枚舉
  - [ ] MESSAGE, TYPING, TOOL_APPROVAL, PONG (客戶端)
  - [ ] STREAM_START, STREAM_DELTA, STREAM_END (串流)
  - [ ] TOOL_CALL, TOOL_APPROVAL_REQUEST, TOOL_RESULT (工具)
  - [ ] ERROR, PING (系統)
- [ ] `WSMessage` 數據類
  - [ ] type, data, message_id
  - [ ] `to_dict()` 方法
  - [ ] `from_dict()` 類方法
- [ ] 預定義訊息函數
  - [ ] `stream_start()`
  - [ ] `stream_delta()`
  - [ ] `stream_end()`
  - [ ] `tool_approval_request()`
  - [ ] `error_message()`

#### 單元測試
- [ ] 創建 `tests/unit/infrastructure/websocket/test_manager.py`
- [ ] 創建 `tests/unit/infrastructure/websocket/test_protocols.py`
- [ ] 測試連接管理
- [ ] 測試心跳檢測
- [ ] 測試訊息格式

#### 驗證
```bash
python -m py_compile src/infrastructure/websocket/manager.py
python -m py_compile src/infrastructure/websocket/protocols.py
pytest tests/unit/infrastructure/websocket/ -v
```

---

### S43-2: 串流響應處理 (10 pts)

**狀態**: ⏳ 未開始

#### 實現任務

**實現 StreamingHandler** (`domain/sessions/streaming.py`)
- [ ] `StreamingHandler` 類
  - [ ] `__init__()` 初始化依賴
  - [ ] `handle_message()` 處理訊息
    - [ ] 保存用戶訊息
    - [ ] 獲取對話歷史
    - [ ] 發送串流開始
    - [ ] 調用 Agent 串流
    - [ ] 發送串流結束
    - [ ] 保存助手回覆
  - [ ] `_stream_agent_response()` 串流 Agent 響應

**實現 WebSocket 端點** (`api/v1/sessions/websocket.py`)
- [ ] `session_websocket()` WebSocket 端點
  - [ ] Token 驗證
  - [ ] Session 驗證
  - [ ] 權限檢查
  - [ ] 建立連接
  - [ ] 激活 Session
  - [ ] 訊息處理循環
  - [ ] 斷開處理
  - [ ] 錯誤處理
- [ ] `handle_ws_message()` 訊息處理
  - [ ] MESSAGE 類型
  - [ ] TYPING 類型
  - [ ] TOOL_APPROVAL 類型
  - [ ] PONG 類型

**更新路由註冊**
- [ ] 添加 WebSocket 路由

#### 單元測試
- [ ] 創建 `tests/unit/domain/sessions/test_streaming.py`
- [ ] 測試串流響應
- [ ] 測試訊息處理
- [ ] 測試錯誤處理

#### 整合測試
- [ ] 創建 `tests/integration/websocket/test_session_ws.py`
- [ ] 測試 WebSocket 連接
- [ ] 測試訊息發送接收
- [ ] 測試串流響應

#### 驗證
```bash
python -m py_compile src/domain/sessions/streaming.py
python -m py_compile src/api/v1/sessions/websocket.py
pytest tests/unit/domain/sessions/test_streaming.py -v
pytest tests/integration/websocket/ -v
```

---

### S43-3: 工具調用處理 (10 pts)

**狀態**: ⏳ 未開始

#### 實現任務

**實現 ToolCallHandler** (`domain/sessions/tool_handler.py`)
- [ ] `ToolCallHandler` 類
  - [ ] `__init__()` 初始化依賴
  - [ ] `handle_tool_call()` 處理工具調用
    - [ ] 權限檢查
    - [ ] 創建 ToolCall 記錄
    - [ ] 判斷是否需要審批
    - [ ] 執行或請求審批
  - [ ] `_request_approval()` 請求審批
    - [ ] 保存待審批調用
    - [ ] 發送審批請求
  - [ ] `handle_approval_response()` 處理審批響應
    - [ ] 驗證調用存在
    - [ ] 處理拒絕
    - [ ] 更新審批信息
    - [ ] 執行工具
  - [ ] `_execute_tool()` 執行工具
    - [ ] 解析工具名稱
    - [ ] 調用 MCP
    - [ ] 更新狀態
    - [ ] 發送結果

**整合 MCP 權限系統**
- [ ] 注入 MCPPermissionManager
- [ ] 實現權限檢查

**整合 MCP 客戶端**
- [ ] 注入 MCPClient
- [ ] 實現工具調用

#### 單元測試
- [ ] 創建 `tests/unit/domain/sessions/test_tool_handler.py`
- [ ] 測試權限檢查
- [ ] 測試審批流程
- [ ] 測試工具執行

#### 驗證
```bash
python -m py_compile src/domain/sessions/tool_handler.py
pytest tests/unit/domain/sessions/test_tool_handler.py -v
```

---

### S43-4: 事件系統整合 (5 pts)

**狀態**: ⏳ 未開始

#### 實現任務

**擴展 MessageType**
- [ ] 添加 AGENT_STATUS
- [ ] 添加 WORKFLOW_PROGRESS
- [ ] 添加 EXTERNAL_EVENT

**實現 SessionEventHandler** (`domain/sessions/event_handler.py`)
- [ ] `SessionEventHandler` 類
  - [ ] `__init__(connection_manager)` 初始化
  - [ ] `on_agent_status_change()` Agent 狀態變更
  - [ ] `on_workflow_progress()` 工作流進度
  - [ ] `on_external_event()` 外部事件

**整合事件系統**
- [ ] 訂閱 Agent 事件
- [ ] 訂閱 Workflow 事件
- [ ] 處理外部事件推送

#### 單元測試
- [ ] 創建 `tests/unit/domain/sessions/test_event_handler.py`
- [ ] 測試事件處理
- [ ] 測試廣播

#### 驗證
```bash
python -m py_compile src/domain/sessions/event_handler.py
pytest tests/unit/domain/sessions/test_event_handler.py -v
```

---

## 驗證命令匯總

```bash
# 1. 語法檢查
cd backend
python -m py_compile src/infrastructure/websocket/manager.py
python -m py_compile src/infrastructure/websocket/protocols.py
python -m py_compile src/domain/sessions/streaming.py
python -m py_compile src/domain/sessions/tool_handler.py
python -m py_compile src/domain/sessions/event_handler.py
python -m py_compile src/api/v1/sessions/websocket.py

# 2. 運行單元測試
pytest tests/unit/infrastructure/websocket/ -v
pytest tests/unit/domain/sessions/ -v --cov=src

# 3. 整合測試
pytest tests/integration/websocket/ -v

# 4. WebSocket 手動測試
# 使用 websocat 或其他工具
websocat ws://localhost:8000/api/v1/sessions/{session_id}/ws?token=xxx
```

---

## 完成定義

- [ ] 所有 S43 Story 完成
- [ ] WebSocket 連接穩定
- [ ] 串流響應正常
- [ ] 工具調用和審批正常
- [ ] 事件即時推送
- [ ] 測試覆蓋率 > 85%
- [ ] 代碼審查完成

---

## 輸出產物

| 文件 | 類型 | 說明 |
|------|------|------|
| `infrastructure/websocket/__init__.py` | 新增 | WebSocket 模組 |
| `infrastructure/websocket/manager.py` | 新增 | 連接管理 |
| `infrastructure/websocket/protocols.py` | 新增 | 協議定義 |
| `domain/sessions/streaming.py` | 新增 | 串流處理 |
| `domain/sessions/tool_handler.py` | 新增 | 工具調用 |
| `domain/sessions/event_handler.py` | 新增 | 事件處理 |
| `api/v1/sessions/websocket.py` | 新增 | WebSocket 端點 |
| `tests/unit/infrastructure/websocket/` | 新增 | 單元測試 |
| `tests/integration/websocket/` | 新增 | 整合測試 |

---

## 下一步

- Sprint 44: Session Features

---

**創建日期**: 2025-12-22
**上次更新**: 2025-12-22
