# Phase 10: Session Mode API

> **目標**: 實現互動式 Session Mode，讓用戶能與 Agent 進行對話式交互

---

## Phase 概述

### 背景

IPA Platform 目前專注於 Workflow 自動化場景。Phase 10 將增加 **Session Mode**，讓用戶能夠：
- 與 Agent 進行即時對話 (類似 ChatGPT/Claude)
- 上傳文件讓 Agent 分析
- 讓 Agent 生成和下載文件
- 在對話中調用 MCP 工具

### 雙模式架構

```
┌─────────────────────────────────────────────────────────────────┐
│                     IPA Platform                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     API Gateway                           │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                      │
│           ┌───────────────┴───────────────┐                     │
│           │                               │                      │
│           ▼                               ▼                      │
│  ┌────────────────┐             ┌────────────────┐              │
│  │  Workflow Mode │             │  Session Mode  │              │
│  │  (Phase 1-8)   │             │  (Phase 10)    │              │
│  │                │             │                │              │
│  │ • 後台自動化    │             │ • 即時對話     │              │
│  │ • 定時觸發      │             │ • 文件分析     │              │
│  │ • 批量處理      │             │ • 互動生成     │              │
│  │ • 審批流程      │             │ • 工具調用     │              │
│  └───────┬────────┘             └───────┬────────┘              │
│          │                              │                        │
│          └──────────────┬───────────────┘                       │
│                         │                                        │
│                         ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  Shared Infrastructure                    │   │
│  │  • Agent Execution Engine                                 │   │
│  │  • MCP Tool Layer (Phase 9)                              │   │
│  │  • LLM Integration                                       │   │
│  │  • Memory & Storage                                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 核心功能

1. **Session 管理**
   - 創建/恢復/結束 Session
   - Session 狀態持久化
   - Session 超時處理

2. **即時通訊**
   - WebSocket 雙向通訊
   - 串流響應 (Streaming)
   - 打字指示器

3. **文件交互**
   - 文件上傳 (多格式支援)
   - 文件分析 (Code Interpreter)
   - 文件生成和下載

4. **工具調用**
   - 在對話中調用 MCP 工具
   - 工具執行狀態回報
   - 需要審批的工具處理

---

## Sprint 規劃

| Sprint | 名稱 | 點數 | 主要內容 |
|--------|------|------|---------|
| Sprint 42 | Session Management Core | 35 pts | Session 生命週期、狀態管理、存儲 |
| Sprint 43 | Real-time Communication | 35 pts | WebSocket、串流響應、事件推送 |
| Sprint 44 | Session Features | 30 pts | 文件交互、工具調用、歷史記錄 |

**Phase 10 總計**: 100 Story Points

---

## 技術設計

### Session 狀態機

```
          create
            │
            ▼
    ┌───────────────┐
    │    CREATED    │
    └───────┬───────┘
            │ connect
            ▼
    ┌───────────────┐
    │    ACTIVE     │◄────────┐
    └───────┬───────┘         │
            │                 │ resume
            │ disconnect      │
            ▼                 │
    ┌───────────────┐         │
    │   SUSPENDED   │─────────┘
    └───────┬───────┘
            │ timeout/end
            ▼
    ┌───────────────┐
    │    ENDED      │
    └───────────────┘
```

### 數據模型

```python
@dataclass
class Session:
    id: str
    user_id: str
    agent_id: str
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    metadata: Dict[str, Any]

@dataclass
class Message:
    id: str
    session_id: str
    role: MessageRole  # user, assistant, system, tool
    content: str
    attachments: List[Attachment]
    tool_calls: List[ToolCall]
    created_at: datetime

@dataclass
class Attachment:
    id: str
    filename: str
    content_type: str
    size: int
    storage_path: str
```

### WebSocket 協議

```json
// 客戶端 → 服務器
{
  "type": "message",
  "content": "幫我分析這個文件",
  "attachments": ["attachment_id_1"]
}

// 服務器 → 客戶端 (串流)
{
  "type": "stream_start",
  "message_id": "msg_123"
}
{
  "type": "stream_delta",
  "message_id": "msg_123",
  "delta": "根據文件內容"
}
{
  "type": "stream_end",
  "message_id": "msg_123"
}

// 工具調用
{
  "type": "tool_call",
  "tool": "shell.run_command",
  "arguments": {"command": "ls -la"},
  "requires_approval": true
}
{
  "type": "tool_approval_request",
  "tool_call_id": "tc_456",
  "tool": "shell.run_command",
  "arguments": {"command": "ls -la"}
}
```

---

## 關鍵設計決策

### 1. Session 存儲策略

| 數據類型 | 存儲位置 | 保留時間 |
|----------|---------|---------|
| Session 元數據 | PostgreSQL | 永久 |
| 對話歷史 | PostgreSQL | 可配置 (預設 30 天) |
| 附件文件 | Azure Blob / 本地 | 可配置 (預設 7 天) |
| 實時狀態 | Redis | Session 期間 |

### 2. 串流響應

使用 Server-Sent Events (SSE) 或 WebSocket 實現串流：
- 首選 WebSocket (雙向通訊)
- SSE 作為降級方案

### 3. 文件處理

- 上傳: 先存儲到臨時位置，驗證後移至永久存儲
- 分析: 使用 Code Interpreter (Phase 8)
- 生成: 存儲到用戶空間，提供下載連結

### 4. 安全考慮

- Session Token 驗證
- 文件類型白名單
- 文件大小限制
- 工具調用審批 (繼承 MCP 權限系統)

---

## 依賴關係

### 前置條件
- Phase 8 完成 (Code Interpreter)
- Phase 9 完成 (MCP Architecture)

### 技術依賴
- `websockets` (WebSocket 支援)
- `aiofiles` (異步文件 I/O)
- `python-multipart` (文件上傳)
- `azure-storage-blob` (文件存儲，可選)

---

## API 端點設計

### REST API

```
# Session 管理
POST   /api/v1/sessions                    # 創建 Session
GET    /api/v1/sessions/{id}               # 獲取 Session
DELETE /api/v1/sessions/{id}               # 結束 Session
GET    /api/v1/sessions/{id}/messages      # 獲取對話歷史

# 文件管理
POST   /api/v1/sessions/{id}/attachments   # 上傳文件
GET    /api/v1/sessions/{id}/attachments   # 列出文件
GET    /api/v1/sessions/{id}/attachments/{aid}  # 下載文件
DELETE /api/v1/sessions/{id}/attachments/{aid}  # 刪除文件
```

### WebSocket API

```
# WebSocket 連接
WS /api/v1/sessions/{id}/ws

# 事件類型
- message: 發送訊息
- typing: 打字狀態
- stream_start/delta/end: 串流響應
- tool_call: 工具調用
- tool_approval_request/response: 工具審批
- error: 錯誤
```

---

## 風險評估

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|---------|
| WebSocket 連接不穩定 | 中 | 中 | 自動重連、降級到輪詢 |
| 大文件處理效能 | 中 | 中 | 分塊上傳、背景處理 |
| Session 洩漏 | 低 | 高 | 超時清理、資源限制 |
| 並發連接過多 | 中 | 高 | 連接限制、負載均衡 |

---

## 交付物

### 代碼產物
```
backend/src/
├── api/v1/sessions/
│   ├── __init__.py
│   ├── routes.py           # REST API 路由
│   ├── schemas.py          # Pydantic 模型
│   └── websocket.py        # WebSocket 處理
│
├── domain/sessions/
│   ├── __init__.py
│   ├── models.py           # Session 領域模型
│   ├── service.py          # Session 服務
│   ├── repository.py       # Session 存儲
│   └── events.py           # Session 事件
│
└── infrastructure/
    ├── websocket/
    │   ├── __init__.py
    │   ├── manager.py      # WebSocket 連接管理
    │   └── protocols.py    # 協議定義
    │
    └── storage/
        └── attachments.py  # 附件存儲
```

### 文檔產物
- Session Mode API 參考文檔
- WebSocket 協議文檔
- 客戶端整合指南
- 安全配置指南

---

**創建日期**: 2025-12-22
**上次更新**: 2025-12-22
