# Sprint 42 Checklist: Session Management Core

**Sprint 目標**: 實現 Session 管理核心功能
**總點數**: 35 Story Points
**狀態**: 📋 計劃中
**前置條件**: Phase 9 完成
**開始日期**: TBD

---

## 前置條件檢查

### Phase 9 完成確認
- [ ] MCP Core Framework 可用
- [ ] Azure MCP Server 可用
- [ ] 其他 MCP Servers 可用

### 環境準備
- [ ] 安裝依賴套件
  ```bash
  pip install websockets python-multipart aiofiles
  ```
- [ ] 確認 PostgreSQL 連接
- [ ] 確認 Redis 連接

---

## Story Checklist

### S42-1: Session 領域模型 (8 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] 閱讀領域模型設計文檔
- [ ] 確認與 Agent 模型的關係

#### 實現任務

**創建目錄結構**
- [ ] 創建 `backend/src/domain/sessions/`
- [ ] 創建 `backend/src/domain/sessions/__init__.py`

**實現枚舉類型** (`domain/sessions/models.py`)
- [ ] `SessionStatus` 枚舉
  - [ ] CREATED
  - [ ] ACTIVE
  - [ ] SUSPENDED
  - [ ] ENDED
- [ ] `MessageRole` 枚舉
  - [ ] USER
  - [ ] ASSISTANT
  - [ ] SYSTEM
  - [ ] TOOL
- [ ] `AttachmentType` 枚舉
  - [ ] IMAGE
  - [ ] DOCUMENT
  - [ ] CODE
  - [ ] DATA
  - [ ] OTHER

**實現 Attachment 模型**
- [ ] `Attachment` 數據類
  - [ ] id, filename, content_type, size
  - [ ] storage_path, attachment_type
  - [ ] uploaded_at, metadata
- [ ] `from_upload()` 類方法
- [ ] `_detect_type()` 靜態方法

**實現 ToolCall 模型**
- [ ] `ToolCall` 數據類
  - [ ] id, tool_name, arguments
  - [ ] result, status, requires_approval
  - [ ] approved_by, approved_at
  - [ ] executed_at, error

**實現 Message 模型**
- [ ] `Message` 數據類
  - [ ] id, session_id, role, content
  - [ ] attachments, tool_calls
  - [ ] created_at, metadata
- [ ] `add_attachment()` 方法
- [ ] `add_tool_call()` 方法

**實現 SessionConfig 模型**
- [ ] `SessionConfig` 數據類
  - [ ] max_messages, max_attachments
  - [ ] max_attachment_size
  - [ ] timeout_minutes
  - [ ] enable_code_interpreter
  - [ ] enable_mcp_tools
  - [ ] allowed_tools

**實現 Session 模型**
- [ ] `Session` 數據類
  - [ ] id, user_id, agent_id
  - [ ] status, config, messages
  - [ ] created_at, updated_at
  - [ ] expires_at, ended_at, metadata
- [ ] `__post_init__()` 初始化過期時間
- [ ] `activate()` 激活 Session
- [ ] `suspend()` 暫停 Session
- [ ] `end()` 結束 Session
- [ ] `is_expired()` 檢查過期
- [ ] `add_message()` 添加訊息
- [ ] `_extend_expiry()` 延長過期
- [ ] `get_conversation_history()` 獲取歷史

#### 單元測試
- [ ] 創建 `tests/unit/domain/sessions/test_models.py`
- [ ] 測試 Session 狀態機
- [ ] 測試 Message 添加
- [ ] 測試 Attachment 類型檢測
- [ ] 測試過期檢查

#### 驗證
```bash
python -m py_compile src/domain/sessions/models.py
pytest tests/unit/domain/sessions/test_models.py -v
```

---

### S42-2: Session 存儲層 (10 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] S42-1 完成
- [ ] 確認數據庫連接

#### 實現任務

**創建數據庫模型** (`infrastructure/database/models/session.py`)
- [ ] `SessionModel` 表
  - [ ] id, user_id, agent_id
  - [ ] status, config
  - [ ] created_at, updated_at
  - [ ] expires_at, ended_at, metadata
  - [ ] messages 關係
- [ ] `MessageModel` 表
  - [ ] id, session_id, role
  - [ ] content, attachments, tool_calls
  - [ ] created_at, metadata
  - [ ] session 關係
- [ ] `AttachmentModel` 表
  - [ ] id, session_id, message_id
  - [ ] filename, content_type, size
  - [ ] storage_path, attachment_type
  - [ ] uploaded_at, metadata

**創建數據庫遷移**
- [ ] 創建 Alembic 遷移腳本
- [ ] 運行遷移

**實現 Repository 抽象** (`domain/sessions/repository.py`)
- [ ] `SessionRepository` 抽象類
  - [ ] `create()` 抽象方法
  - [ ] `get()` 抽象方法
  - [ ] `update()` 抽象方法
  - [ ] `delete()` 抽象方法
  - [ ] `list_by_user()` 抽象方法
  - [ ] `add_message()` 抽象方法
  - [ ] `get_messages()` 抽象方法

**實現 SQLAlchemy Repository**
- [ ] `SQLAlchemySessionRepository` 類
  - [ ] `__init__(db)` 初始化
  - [ ] `create()` 創建 Session
  - [ ] `get()` 獲取 Session
  - [ ] `update()` 更新 Session
  - [ ] `delete()` 刪除 Session
  - [ ] `list_by_user()` 列出用戶 Sessions
  - [ ] `add_message()` 添加訊息
  - [ ] `get_messages()` 獲取訊息 (分頁)
  - [ ] `cleanup_expired()` 清理過期 Sessions
  - [ ] `_to_domain()` 轉換為領域模型
  - [ ] `_message_to_domain()` 轉換訊息

**實現 Redis Cache** (`domain/sessions/cache.py`)
- [ ] `SessionCache` 類
  - [ ] `__init__(redis, ttl)` 初始化
  - [ ] `_key(session_id)` 生成 key
  - [ ] `get()` 獲取快取
  - [ ] `set()` 設置快取
  - [ ] `delete()` 刪除快取
  - [ ] `extend()` 延長過期

#### 單元測試
- [ ] 創建 `tests/unit/domain/sessions/test_repository.py`
- [ ] 創建 `tests/unit/domain/sessions/test_cache.py`
- [ ] 測試 CRUD 操作
- [ ] 測試分頁查詢
- [ ] 測試快取操作

#### 驗證
```bash
python -m py_compile src/infrastructure/database/models/session.py
python -m py_compile src/domain/sessions/repository.py
python -m py_compile src/domain/sessions/cache.py
pytest tests/unit/domain/sessions/ -v
```

---

### S42-3: Session 服務層 (10 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] S42-2 完成
- [ ] 確認 Agent 服務可用

#### 實現任務

**實現事件類型** (`domain/sessions/events.py`)
- [ ] `SessionEvent` 基類
- [ ] `SessionCreatedEvent`
- [ ] `SessionActivatedEvent`
- [ ] `SessionEndedEvent`
- [ ] `MessageAddedEvent`

**實現 SessionService** (`domain/sessions/service.py`)
- [ ] `SessionService` 類
  - [ ] `__init__()` 初始化依賴
  - [ ] `create_session()` 創建 Session
    - [ ] 驗證 Agent 存在
    - [ ] 創建 Session
    - [ ] 添加系統訊息
    - [ ] 持久化
    - [ ] 發布事件
  - [ ] `get_session()` 獲取 Session
    - [ ] 先查快取
    - [ ] 再查資料庫
    - [ ] 更新快取
  - [ ] `activate_session()` 激活 Session
    - [ ] 過期檢查
    - [ ] 狀態更新
    - [ ] 發布事件
  - [ ] `suspend_session()` 暫停 Session
  - [ ] `end_session()` 結束 Session
    - [ ] 狀態更新
    - [ ] 清除快取
    - [ ] 發布事件
  - [ ] `send_message()` 發送訊息 (串流)
    - [ ] 狀態驗證
    - [ ] 創建用戶訊息
    - [ ] 獲取對話歷史
    - [ ] 調用 Agent (串流)
    - [ ] 保存助手回覆
    - [ ] 更新快取
  - [ ] `_invoke_agent()` 調用 Agent
  - [ ] `get_messages()` 獲取訊息歷史
  - [ ] `cleanup_expired_sessions()` 清理過期

**整合 Agent 服務**
- [ ] 注入 AgentService 依賴
- [ ] 實現 stream_completion 調用
- [ ] 處理 MCP 工具調用

#### 單元測試
- [ ] 創建 `tests/unit/domain/sessions/test_service.py`
- [ ] 測試 Session 創建
- [ ] 測試訊息發送
- [ ] 測試串流響應
- [ ] 測試 Agent 整合

#### 驗證
```bash
python -m py_compile src/domain/sessions/events.py
python -m py_compile src/domain/sessions/service.py
pytest tests/unit/domain/sessions/test_service.py -v
```

---

### S42-4: Session REST API (7 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] S42-3 完成

#### 實現任務

**創建 API 目錄**
- [ ] 創建 `backend/src/api/v1/sessions/`
- [ ] 創建 `backend/src/api/v1/sessions/__init__.py`

**實現 Schema** (`api/v1/sessions/schemas.py`)
- [ ] `CreateSessionRequest`
  - [ ] agent_id, config
- [ ] `SessionConfigSchema`
  - [ ] 所有配置項
  - [ ] 驗證規則
- [ ] `SessionResponse`
  - [ ] 所有響應字段
  - [ ] `from_domain()` 類方法
- [ ] `MessageResponse`
  - [ ] 所有響應字段
- [ ] `AttachmentResponse`
  - [ ] 所有響應字段
- [ ] `ToolCallResponse`
  - [ ] 所有響應字段

**實現 Routes** (`api/v1/sessions/routes.py`)
- [ ] `POST /sessions` - 創建 Session
  - [ ] 認證
  - [ ] 調用服務
  - [ ] 返回響應
- [ ] `GET /sessions/{id}` - 獲取 Session
  - [ ] 認證
  - [ ] 權限檢查
  - [ ] 返回響應
- [ ] `DELETE /sessions/{id}` - 結束 Session
  - [ ] 認證
  - [ ] 權限檢查
  - [ ] 調用服務
- [ ] `GET /sessions/{id}/messages` - 獲取訊息
  - [ ] 認證
  - [ ] 權限檢查
  - [ ] 分頁參數
- [ ] `POST /sessions/{id}/attachments` - 上傳附件
  - [ ] 認證
  - [ ] 權限檢查
  - [ ] 文件驗證
  - [ ] 存儲文件
- [ ] `GET /sessions/{id}/attachments/{aid}` - 下載附件
  - [ ] 認證
  - [ ] 返回文件
- [ ] `DELETE /sessions/{id}/attachments/{aid}` - 刪除附件
  - [ ] 認證
  - [ ] 權限檢查

**實現附件存儲** (`infrastructure/storage/attachments.py`)
- [ ] `AttachmentStorage` 類
  - [ ] `store()` 存儲文件
  - [ ] `get()` 獲取文件
  - [ ] `delete()` 刪除文件
  - [ ] `list()` 列出文件

**更新路由註冊**
- [ ] 更新 `api/v1/__init__.py`

#### API 測試
```bash
# 創建 Session
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "agent-123"}'

# 獲取 Session
curl http://localhost:8000/api/v1/sessions/{id} \
  -H "Authorization: Bearer $TOKEN"

# 獲取訊息
curl "http://localhost:8000/api/v1/sessions/{id}/messages?limit=50" \
  -H "Authorization: Bearer $TOKEN"

# 上傳附件
curl -X POST http://localhost:8000/api/v1/sessions/{id}/attachments \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf"
```

#### 驗證
```bash
python -m py_compile src/api/v1/sessions/schemas.py
python -m py_compile src/api/v1/sessions/routes.py
python -m py_compile src/infrastructure/storage/attachments.py
pytest tests/unit/api/v1/test_sessions.py -v
```

---

## 驗證命令匯總

```bash
# 1. 語法檢查
cd backend
python -m py_compile src/domain/sessions/models.py
python -m py_compile src/domain/sessions/repository.py
python -m py_compile src/domain/sessions/cache.py
python -m py_compile src/domain/sessions/service.py
python -m py_compile src/domain/sessions/events.py
python -m py_compile src/infrastructure/database/models/session.py
python -m py_compile src/infrastructure/storage/attachments.py
python -m py_compile src/api/v1/sessions/schemas.py
python -m py_compile src/api/v1/sessions/routes.py
# 預期: 無輸出 (無錯誤)

# 2. 類型檢查
mypy src/domain/sessions/ src/api/v1/sessions/
# 預期: Success

# 3. 運行單元測試
pytest tests/unit/domain/sessions/ tests/unit/api/v1/test_sessions.py -v --cov=src
# 預期: 全部通過，覆蓋率 > 85%

# 4. 數據庫遷移
alembic upgrade head
# 預期: 成功創建 sessions, messages, attachments 表
```

---

## 完成定義

- [ ] 所有 S42 Story 完成
- [ ] Session 領域模型完整
- [ ] Session 存儲 (PostgreSQL + Redis) 正常
- [ ] Session 服務層功能完整
- [ ] REST API 可用
- [ ] 文件上傳/下載正常
- [ ] 測試覆蓋率 > 85%
- [ ] 代碼審查完成

---

## 輸出產物

| 文件 | 類型 | 說明 |
|------|------|------|
| `domain/sessions/__init__.py` | 新增 | Sessions 領域模組 |
| `domain/sessions/models.py` | 新增 | 領域模型 |
| `domain/sessions/repository.py` | 新增 | 存儲層 |
| `domain/sessions/cache.py` | 新增 | Redis 快取 |
| `domain/sessions/service.py` | 新增 | 服務層 |
| `domain/sessions/events.py` | 新增 | 事件定義 |
| `infrastructure/database/models/session.py` | 新增 | 數據庫模型 |
| `infrastructure/storage/attachments.py` | 新增 | 附件存儲 |
| `api/v1/sessions/__init__.py` | 新增 | API 模組 |
| `api/v1/sessions/schemas.py` | 新增 | Pydantic 模型 |
| `api/v1/sessions/routes.py` | 新增 | REST API |
| `tests/unit/domain/sessions/` | 新增 | 單元測試 |
| `tests/unit/api/v1/test_sessions.py` | 新增 | API 測試 |

---

## 下一步

- Sprint 43: Real-time Communication (WebSocket)
- Sprint 44: Session Features

---

**創建日期**: 2025-12-22
**上次更新**: 2025-12-22
