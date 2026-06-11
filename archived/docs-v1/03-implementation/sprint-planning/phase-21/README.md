# Phase 21: Sandbox Security Architecture

## Overview

Phase 21 建立進程隔離的安全執行環境，確保 Agent 無法訪問主進程敏感資源。這是安全基礎設施，必須在功能開發之前完成。

## Phase Status

| Status | Value |
|--------|-------|
| **Phase Status** | 計劃中 |
| **Duration** | 2 sprints |
| **Total Story Points** | 38 pts |
| **Priority** | 🔴 P0 最高優先 (安全基礎設施) |
| **Target Start** | Phase 20 完成後 |

## Sprint Overview

| Sprint | Focus | Story Points | Status | Documents |
|--------|-------|--------------|--------|-----------|
| **Sprint 77** | SandboxOrchestrator + SandboxWorker | 21 pts | 計劃中 | [Plan](sprint-77-plan.md) / [Checklist](sprint-77-checklist.md) |
| **Sprint 78** | IPC 通信 + 代碼適配 + 安全驗證 | 17 pts | 計劃中 | [Plan](sprint-78-plan.md) / [Checklist](sprint-78-checklist.md) |
| **Total** | | **38 pts** | | |

---

## 問題背景

### 安全問題發現 (2026-01-12)

| 發現 | 風險等級 | 影響 |
|------|----------|------|
| Claude Agent 在主進程執行 | 🔴 高 | 可訪問主進程環境變量、敏感資源 |
| Hook 系統已實現但未啟用 | 🟡 中 | 安全機制未生效 |
| Chat 頁面可訪問項目源代碼 | 🔴 高 | 潛在數據洩露風險 |

### 當前架構問題

```
當前架構（不安全）:
API → Bridge → ClaudeSDKClient → Tools
              ↑
         (同一進程，共享內存空間)
         - 共享環境變量
         - 共享文件系統訪問
         - 無進程邊界
```

### 為什麼 Hook 不夠？

Hook 是「邏輯隔離」，可能被繞過：
- 路徑遍歷攻擊 (`../../etc/passwd`)
- 符號連結攻擊
- 編碼繞過 (Unicode, Base64 path)
- Race condition

**進程隔離是最低安全標準**

---

## Architecture

### 目標架構

```
安全架構:
API → Bridge → Orchestrator → [Sandbox Process] → ClaudeSDKClient → Tools
                    ↑                    ↑
               (主進程)              (隔離進程)
               保護敏感資源          受限環境
               - 環境變量            - 只能訪問 /sandbox/{user_id}/
               - 數據庫連接          - 無環境變量訪問
               - 配置文件            - 限制系統調用
```

### 核心組件

```
backend/src/core/sandbox/
├── __init__.py
├── orchestrator.py      (~200 行) - 進程調度和生命週期管理
├── worker.py            (~250 行) - 隔離子進程中執行 Claude Agent
├── ipc.py               (~150 行) - stdin/stdout JSON-RPC 通信
└── config.py            (~100 行) - 沙箱環境配置
```

### IPC 協議設計

```
主進程 ←→ 沙箱進程 通信：

Request (主進程 → 沙箱):
{
    "jsonrpc": "2.0",
    "method": "execute",
    "params": {
        "message": "用戶訊息",
        "attachments": [...],
        "session_id": "xxx"
    },
    "id": "req-001"
}

Response (沙箱 → 主進程):
{
    "jsonrpc": "2.0",
    "result": {
        "content": "Claude 回覆",
        "tool_calls": [...],
        "tokens_used": 1234
    },
    "id": "req-001"
}

Event (沙箱 → 主進程，SSE 轉發):
{
    "jsonrpc": "2.0",
    "method": "event",
    "params": {
        "type": "TEXT_DELTA",
        "data": {"delta": "部分回覆..."}
    }
}
```

---

## Features

### Sprint 77: SandboxOrchestrator + SandboxWorker (21 pts)

| Story | Description | Points | Priority |
|-------|-------------|--------|----------|
| S77-1 | 沙箱架構設計與 Orchestrator | 13 pts | P0 |
| S77-2 | SandboxWorker 實現 | 8 pts | P0 |

### Sprint 78: IPC 通信 + 代碼適配 + 安全驗證 (17 pts)

| Story | Description | Points | Priority |
|-------|-------------|--------|----------|
| S78-1 | IPC 通信與事件轉發 | 7 pts | P0 |
| S78-2 | 現有代碼適配 | 5 pts | P1 |
| S78-3 | 安全測試與驗證 | 5 pts | P1 |

---

## Technical Details

### SandboxOrchestrator

```python
class SandboxOrchestrator:
    """管理沙箱子進程的生命週期"""

    async def execute(
        self,
        user_id: str,
        message: str,
        attachments: List[Attachment],
        session_id: str,
    ) -> AsyncGenerator[Event, None]:
        """在沙箱中執行 Claude Agent"""

        # 1. 獲取或創建沙箱進程
        worker = await self._get_or_create_worker(user_id)

        # 2. 通過 IPC 發送請求
        async for event in worker.execute(message, attachments, session_id):
            yield event
```

### SandboxWorker

```python
class SandboxWorker:
    """在隔離子進程中運行 Claude Agent"""

    def __init__(self, user_id: str, sandbox_config: SandboxConfig):
        self.user_id = user_id
        self.config = sandbox_config
        self.process: Optional[subprocess.Popen] = None

    async def start(self) -> None:
        """啟動隔離子進程"""
        env = self._create_restricted_env()

        self.process = subprocess.Popen(
            [sys.executable, "-m", "src.core.sandbox.worker_main"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=self.config.sandbox_dir,
        )

    def _create_restricted_env(self) -> Dict[str, str]:
        """創建受限環境變量"""
        return {
            "SANDBOX_USER_ID": self.user_id,
            "SANDBOX_DIR": self.config.sandbox_dir,
            "ANTHROPIC_API_KEY": settings.ANTHROPIC_API_KEY,
            # 不包含: DB_*, REDIS_*, 敏感配置
        }
```

### 沙箱目錄結構

```
data/sandbox/
├── {user_id_1}/
│   ├── uploads/       # 用戶上傳的文件
│   ├── outputs/       # Claude 生成的文件
│   └── workspace/     # 工作目錄
├── {user_id_2}/
│   └── ...
└── shared/            # 共享只讀資源 (可選)
```

---

## File Changes Summary

### New Files (~600-800 行)

| File | Lines | Description |
|------|-------|-------------|
| `backend/src/core/sandbox/__init__.py` | ~10 | Package init |
| `backend/src/core/sandbox/orchestrator.py` | ~200 | 進程調度和生命週期 |
| `backend/src/core/sandbox/worker.py` | ~250 | 隔離進程執行 |
| `backend/src/core/sandbox/worker_main.py` | ~100 | Worker 入口點 |
| `backend/src/core/sandbox/ipc.py` | ~150 | IPC 協議實現 |
| `backend/src/core/sandbox/config.py` | ~100 | 沙箱配置 |

### Modified Files (~150-200 行改動)

| File | Changes | Description |
|------|---------|-------------|
| `api/v1/sessions/chat.py` | ~50 行 | 使用 Orchestrator |
| `api/v1/claude_sdk/routes.py` | ~30 行 | 使用 Orchestrator |
| `domain/sessions/bridge.py` | ~50 行 | 委派執行到沙箱 |
| `domain/sessions/executor.py` | ~30 行 | 適配接口 |

### No Changes Required

- ✅ 所有現有 Hook 代碼 - 在沙箱進程內使用
- ✅ 所有現有工具代碼 - 在沙箱進程內使用
- ✅ 數據庫層 - 完全不變
- ✅ 前端 - 完全不變
- ✅ Workflow 定義 - 完全不變

---

## Dependencies

### Prerequisites
- Phase 20 completed (File Attachment Support)
- Phase 12 completed (Claude SDK Integration)
- Existing Hook system (will be used inside sandbox)

### New Dependencies
- None (使用 Python 標準庫 subprocess)

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| 進程啟動延遲 | Medium | Medium | 進程池預熱，複用進程 |
| IPC 通信開銷 | Low | Low | JSON 序列化已優化 |
| 進程崩潰影響 | Low | Low | 自動重啟機制 |
| 沙箱逃逸 | Critical | Very Low | 多層防護，定期安全審計 |

---

## Verification Criteria

### Sprint 77 驗證
- [ ] SandboxOrchestrator 能創建和管理子進程
- [ ] SandboxWorker 在隔離環境中啟動
- [ ] 子進程無法訪問主進程環境變量
- [ ] 子進程只能訪問指定沙箱目錄

### Sprint 78 驗證
- [ ] IPC 通信正確傳遞請求和響應
- [ ] SSE 事件正確從沙箱轉發到前端
- [ ] 現有 API 端點正常工作
- [ ] 錯誤處理和超時機制有效

### 安全驗證
- [ ] 路徑遍歷攻擊無法訪問沙箱外文件
- [ ] 環境變量洩露測試通過
- [ ] 進程崩潰不影響主應用
- [ ] 性能損耗 < 200ms（首次啟動）

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| 進程隔離有效性 | 100% | 安全測試通過率 |
| 首次啟動延遲 | < 200ms | 性能測試 |
| 進程複用率 | > 90% | 監控指標 |
| 沙箱崩潰恢復時間 | < 1s | 故障測試 |

---

**Created**: 2026-01-12
**Total Story Points**: 38 pts
**Priority**: P0 - 安全基礎設施
