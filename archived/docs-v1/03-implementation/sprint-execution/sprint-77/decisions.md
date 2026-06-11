# Sprint 77 Decisions: SandboxOrchestrator + SandboxWorker

**Sprint 目標**: 建立進程隔離的安全執行環境

---

## 決策記錄

### D77-001: 沙箱架構設計策略

**日期**: 2026-01-12
**狀態**: 🔄 進行中

**背景**:
目前 Claude Agent 在 FastAPI 主進程中執行，可能訪問敏感資源（DB、Redis 連接、完整環境變量）。需要建立進程隔離的安全執行環境。

**問題分析**:
```
修改前：
  API → Bridge → ClaudeSDKClient → Tools
                 ↑
            (同一進程，共享敏感資源)

修改後：
  API → Bridge → Orchestrator → [Sandbox Process] → ClaudeSDKClient → Tools
                      ↑                    ↑
                 (主進程)              (隔離進程)
                 保護敏感資源          受限環境
```

**選項**:
1. **子進程隔離** (subprocess)
   - 優點：Python 標準庫、進程級隔離、環境變量完全隔離
   - 缺點：啟動延遲、IPC 開銷

2. **Docker 容器隔離**
   - 優點：完整隔離、資源限制
   - 缺點：複雜度高、需要 Docker 環境

3. **進程池 + 進程複用**
   - 優點：減少啟動延遲、資源效率
   - 缺點：狀態管理複雜

**決定**: 選項 1 + 選項 3 組合 - 子進程隔離 + 進程池複用

**理由**:
- 標準庫實現，無外部依賴
- 進程池複用減少啟動延遲
- 真正的進程隔離，環境變量不洩露
- Phase 25 可升級到 Docker/K8s 容器

---

### D77-002: IPC 協議選擇

**日期**: 2026-01-12
**狀態**: 🔄 進行中

**背景**:
主進程與沙箱子進程需要雙向通信，支持：
- 請求/響應模式（同步）
- 事件流模式（SSE 轉發）

**選項**:
1. **stdin/stdout JSON-RPC**
   - 優點：簡單、跨平台、無端口衝突
   - 缺點：單通道，需要協議設計

2. **Unix Socket / Named Pipe**
   - 優點：雙向通信、性能好
   - 缺點：Windows 兼容性問題

3. **TCP Socket**
   - 優點：標準化、工具豐富
   - 缺點：需要端口管理、安全考慮

**決定**: 選項 1 - stdin/stdout JSON-RPC

**協議設計**:
```json
// Request (主進程 → 沙箱)
{
    "jsonrpc": "2.0",
    "method": "execute",
    "params": {
        "message": "分析這個文件",
        "attachments": [],
        "session_id": "session-456",
        "config": {}
    },
    "id": "req-001"
}

// Response (沙箱 → 主進程)
{
    "jsonrpc": "2.0",
    "result": {
        "content": "分析結果...",
        "tool_calls": [],
        "tokens_used": 1234
    },
    "id": "req-001"
}

// Streaming Event (沙箱 → 主進程)
{
    "jsonrpc": "2.0",
    "method": "event",
    "params": {
        "type": "TEXT_DELTA",
        "data": {"delta": "部分內容"}
    }
}
```

---

### D77-003: 環境變量隔離策略

**日期**: 2026-01-12
**狀態**: 🔄 進行中

**背景**:
需要定義哪些環境變量可以傳遞到沙箱進程。

**安全原則**:
- 最小權限原則：只傳遞必要的環境變量
- 顯式允許列表：必須明確列出允許的變量

**允許傳遞的環境變量**:
```python
ALLOWED_ENV_VARS = [
    # Claude API
    "ANTHROPIC_API_KEY",

    # 沙箱配置
    "SANDBOX_USER_ID",
    "SANDBOX_DIR",
    "SANDBOX_TIMEOUT",

    # Python 環境
    "PYTHONPATH",
    "PATH",

    # 語言環境
    "LANG",
    "LC_ALL",
]
```

**禁止傳遞的環境變量**:
```python
BLOCKED_ENV_VARS = [
    # 資料庫
    "DB_HOST", "DB_PASSWORD", "DB_USER", "DATABASE_URL",

    # Redis
    "REDIS_HOST", "REDIS_PASSWORD", "REDIS_URL",

    # 其他敏感資訊
    "SECRET_KEY", "JWT_SECRET", "AZURE_*", "AWS_*",
]
```

---

### D77-004: 進程池配置策略

**日期**: 2026-01-12
**狀態**: 🔄 進行中

**配置參數**:

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `max_workers` | 10 | 最大 Worker 數量 |
| `worker_timeout` | 300s | Worker 執行超時 |
| `startup_timeout` | 30s | Worker 啟動超時 |
| `idle_timeout` | 300s | 空閒 Worker 回收時間 |
| `max_requests_per_worker` | 100 | 每個 Worker 最大請求數（防止記憶體洩漏）|

**Worker 生命週期**:
```
建立 → 啟動 → 就緒 → 執行 → 空閒 → 回收
         ↑           ↓
         ←←← 複用 ←←←
```

---

## 技術約束

1. **進程隔離**:
   - 子進程必須無法訪問主進程的環境變量
   - 子進程只能訪問指定的沙箱目錄

2. **性能要求**:
   - 首次啟動延遲 < 500ms
   - 進程複用後延遲 < 50ms

3. **可靠性要求**:
   - 子進程崩潰不影響主進程
   - 自動重啟機制

4. **兼容性**:
   - 現有 Hook 系統在沙箱進程內使用
   - 現有工具代碼在沙箱進程內使用
   - API 接口保持不變

---

## 參考資料

- [Sprint 77 Plan](../../sprint-planning/phase-21/sprint-77-plan.md)
- [Sprint 77 Checklist](../../sprint-planning/phase-21/sprint-77-checklist.md)
- [Phase 21-25 Roadmap](../../sprint-planning/PHASE-21-24-ROADMAP.md)
