# Sprint 77 Plan: SandboxOrchestrator + SandboxWorker

## Sprint Overview

| Metric | Value |
|--------|-------|
| **Sprint Number** | 77 |
| **Phase** | Phase 21 - Sandbox Security Architecture |
| **Duration** | 1 sprint |
| **Story Points** | 21 pts |
| **Priority** | 🔴 P0 最高優先 |

---

## Sprint Goals

1. 設計並實現 SandboxOrchestrator - 管理沙箱子進程的生命週期
2. 實現 SandboxWorker - 在隔離子進程中運行 Claude Agent
3. 建立進程隔離的安全邊界

---

## Stories

### S77-1: 沙箱架構設計與 Orchestrator (13 pts)

**Priority**: P0

**Description**:
設計完整的沙箱架構，實現 SandboxOrchestrator 負責子進程調度和生命週期管理。

**Tasks**:
1. 設計沙箱架構文檔
   - 進程隔離邊界定義
   - IPC 協議設計 (JSON-RPC over stdin/stdout)
   - 錯誤處理和恢復策略
   - 資源限制規範

2. 實現 SandboxConfig
   ```python
   # backend/src/core/sandbox/config.py
   @dataclass
   class SandboxConfig:
       sandbox_base_dir: Path
       max_workers: int = 10
       worker_timeout: int = 300
       startup_timeout: int = 30
       allowed_env_vars: List[str]
   ```

3. 實現 SandboxOrchestrator
   ```python
   # backend/src/core/sandbox/orchestrator.py
   class SandboxOrchestrator:
       async def execute(user_id, message, attachments, session_id)
       async def _get_or_create_worker(user_id)
       async def _cleanup_idle_workers()
       async def shutdown()
   ```

4. 實現進程池管理
   - Worker 複用邏輯
   - 空閒 Worker 回收
   - 最大 Worker 數限制

**Acceptance Criteria**:
- [ ] SandboxOrchestrator 能創建子進程
- [ ] 進程池複用邏輯正確
- [ ] 空閒進程自動回收
- [ ] 配置可通過環境變量調整

**Files**:
- `backend/src/core/sandbox/__init__.py` (新建)
- `backend/src/core/sandbox/config.py` (新建)
- `backend/src/core/sandbox/orchestrator.py` (新建)

---

### S77-2: SandboxWorker 實現 (8 pts)

**Priority**: P0

**Description**:
實現 SandboxWorker，在隔離子進程中運行 Claude Agent，確保安全邊界。

**Tasks**:
1. 實現 SandboxWorker 類
   ```python
   # backend/src/core/sandbox/worker.py
   class SandboxWorker:
       async def start()
       async def execute(message, attachments, session_id)
       async def stop()
       def _create_restricted_env()
       def _setup_sandbox_directory()
   ```

2. 實現 Worker 入口點
   ```python
   # backend/src/core/sandbox/worker_main.py
   # 子進程入口點，初始化 Claude SDK 並處理請求
   ```

3. 實現受限環境
   - 只傳遞必要的環境變量
   - 設置工作目錄為沙箱目錄
   - 限制文件系統訪問

4. 實現沙箱目錄管理
   - 創建用戶沙箱目錄
   - 清理過期文件
   - 權限控制

**Acceptance Criteria**:
- [ ] Worker 在隔離進程中啟動
- [ ] 子進程無法訪問主進程環境變量
- [ ] 子進程只能訪問沙箱目錄
- [ ] Claude SDK 在子進程中正確初始化

**Files**:
- `backend/src/core/sandbox/worker.py` (新建)
- `backend/src/core/sandbox/worker_main.py` (新建)

---

## Technical Details

### 架構設計

```
主進程                              沙箱進程
┌─────────────────────┐            ┌─────────────────────┐
│ FastAPI Server      │            │ SandboxWorker       │
│                     │            │                     │
│ ┌─────────────────┐ │   IPC      │ ┌─────────────────┐ │
│ │ Orchestrator    │◄┼───────────►┼►│ Worker Main     │ │
│ │                 │ │  JSON-RPC  │ │                 │ │
│ │ - 進程管理       │ │  stdin/    │ │ - Claude SDK    │ │
│ │ - 請求路由       │ │  stdout    │ │ - Tool Executor │ │
│ │ - 事件轉發       │ │            │ │ - Hook Handler  │ │
│ └─────────────────┘ │            │ └─────────────────┘ │
│                     │            │                     │
│ 敏感資源:           │            │ 受限環境:           │
│ - DB Connection     │            │ - ANTHROPIC_API_KEY │
│ - Redis Connection  │            │ - SANDBOX_DIR      │
│ - 完整 ENV          │            │ - 無 DB 訪問        │
└─────────────────────┘            └─────────────────────┘
```

### IPC 協議

```json
// Request
{
    "jsonrpc": "2.0",
    "method": "execute",
    "params": {
        "message": "分析這個文件",
        "attachments": [{"id": "file-123", "type": "image/png"}],
        "session_id": "session-456",
        "config": {
            "model": "claude-sonnet-4-5",
            "max_tokens": 4096
        }
    },
    "id": "req-001"
}

// Response
{
    "jsonrpc": "2.0",
    "result": {
        "content": "這是一張圖片...",
        "tool_calls": [],
        "tokens_used": 1234,
        "duration": 2.5
    },
    "id": "req-001"
}

// Streaming Event
{
    "jsonrpc": "2.0",
    "method": "event",
    "params": {
        "type": "TEXT_DELTA",
        "data": {"delta": "部分"}
    }
}
```

### 環境變量隔離

```python
# 主進程環境變量 (完整)
ANTHROPIC_API_KEY=sk-xxx
AZURE_OPENAI_API_KEY=xxx
DB_HOST=localhost
DB_PASSWORD=xxx
REDIS_PASSWORD=xxx
SECRET_KEY=xxx

# 沙箱進程環境變量 (受限)
ANTHROPIC_API_KEY=sk-xxx  # 只有 Claude API
SANDBOX_USER_ID=user-123
SANDBOX_DIR=/data/sandbox/user-123
PYTHONPATH=/app  # Python 路徑
```

---

## Dependencies

- Python subprocess 模組 (標準庫)
- asyncio 協程支持
- 現有 Claude SDK 整合

---

## Risks

| Risk | Mitigation |
|------|------------|
| 進程啟動延遲 | 實現進程池複用 |
| 子進程崩潰 | 自動重啟機制 |
| 資源洩漏 | 定期清理空閒進程 |

---

## Verification

### 單元測試
- [ ] Orchestrator 進程管理測試
- [ ] Worker 隔離環境測試
- [ ] IPC 通信測試

### 整合測試
- [ ] 端到端請求處理測試
- [ ] 進程池壓力測試
- [ ] 錯誤恢復測試

### 安全測試
- [ ] 環境變量隔離驗證
- [ ] 文件系統隔離驗證

---

**Created**: 2026-01-12
**Story Points**: 21 pts
