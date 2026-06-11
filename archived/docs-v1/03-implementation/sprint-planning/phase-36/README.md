# Phase 36: E2E Assembly A1 — 基礎組裝

## 概述

Phase 36 專注於 **端到端基礎組裝**，在 Phase 35 (A0) 驗證通過的基礎上，將各層模組串接為可運作的完整流程。用戶可以登入、進行對話、由 Orchestrator 理解意圖、直接回答簡單問題，並在高風險操作時觸發審批。

本 Phase 是 IPA Platform 從「模組可用」邁向「流程可用」的關鍵里程碑，聚焦於安全基礎、持久化遷移、審批統一、以及 Orchestrator 完整化四大主軸。

> **Status**: ✅ 完成 — 4 Sprints (109-112), ~48 SP

## 目標

1. **安全基礎** — Tool Security Gateway + Prompt Injection 防護，確保所有 tool 呼叫經過安全層
2. **LLM Call Pool** — asyncio.Semaphore 併發控制 + Priority Queue，避免 LLM API 過載
3. **持久化遷移** — 核心 InMemory 儲存遷移至 Redis/PostgreSQL，至少完成 15/28+ 處
4. **統一審批** — 將 4-5 套分散的審批系統統一為 1 套，以 Orchestration HITLController 為主
5. **Orchestrator 完整化** — 新增核心 tools、RBAC 角色控制、Per-Session 實例策略
6. **E2E 流程串通** — 登入 → 對話 → 意圖理解 → 回答/審批 完整可用

## 前置條件

- ✅ Phase 35 (A0) 驗證通過（核心模組可獨立運作）
- ✅ Orchestrator 基礎意圖路由可用（Phase 28 三層路由）
- ✅ AG-UI SSE 基礎設施就緒
- ✅ PostgreSQL + Redis 基礎設施可用
- ✅ Claude SDK / MAF 整合層穩定

## Sprint 規劃

| Sprint | 名稱 | Story Points | 狀態 |
|--------|------|-------------|------|
| [Sprint 109](./sprint-109-plan.md) | 安全基礎 + LLM Call Pool | ~12 pts | ✅ 完成 |
| [Sprint 110](./sprint-110-plan.md) | InMemory → Redis/PostgreSQL 遷移（核心模組） | ~12 pts | ✅ 完成 |
| [Sprint 111](./sprint-111-plan.md) | 統一審批系統 + Chat History 後端同步 | ~12 pts | ✅ 完成 |
| [Sprint 112](./sprint-112-plan.md) | Orchestrator 完整化 + 更多 Tools | ~12 pts | ✅ 完成 |

**總計**: ~48 Story Points（4 Sprints）

---

## Sprint 明細

### Sprint 109（~12 SP）：安全基礎 + LLM Call Pool

| Story | 說明 | SP |
|-------|------|----|
| **Tool Security Gateway** | 所有 Orchestrator tool 呼叫必須經過安全層：Input Sanitization + Permission Check + Rate Limiting + Audit Logging | 4 |
| **Prompt Injection 防護** | L1 Input Filtering + L2 System Prompt 隔離 + L3 Tool Call 驗證，三層防護機制 | 3 |
| **LLM Call Pool** | asyncio.Semaphore 控制 LLM API 併發 + Priority Queue（優先順序：直接回答 > 意圖路由 > Extended Thinking > Swarm） | 3 |
| **修復 H-04** | ContextSynchronizer 加 asyncio.Lock，解決併發競態問題 | 2 |

### Sprint 110（~12 SP）：InMemory → Redis/PostgreSQL 遷移（核心模組）

| Story | 說明 | SP |
|-------|------|----|
| **Dialog Sessions → Redis** | 對話 session 狀態從 InMemory dict 遷移到 Redis，支援 TTL 過期 | 3 |
| **Approval State → PostgreSQL** | 審批狀態從 InMemory 遷移到 PostgreSQL，確保重啟不丟失 | 2 |
| **Audit Log → PostgreSQL** | 審計日誌持久化到 PostgreSQL，支援查詢與合規需求 | 2 |
| **Rate Limiter → Redis** | 限速器狀態遷移到 Redis，支援分散式環境 | 2 |
| **核心 Checkpoint → PostgreSQL** | `agent_framework/checkpoint.py` + `multiturn/checkpoint_storage.py` 遷移到 PostgreSQL | 3 |

> **目標**：至少完成 15/28+ 處 InMemory 遷移

### Sprint 111（~12 SP）：統一審批系統 + Chat History 後端同步

| Story | 說明 | SP |
|-------|------|----|
| **統一審批系統** | 將 4-5 套審批系統統一為 1 套，以 Orchestration HITLController 為主體 | 4 |
| **AG-UI ApprovalStorage 代理** | AG-UI ApprovalStorage 改為代理（delegate）到 HITLController，不再獨立存儲 | 2 |
| **Claude SDK ApprovalHook 代理** | Claude SDK ApprovalHook 改為代理到 HITLController，統一審批入口 | 2 |
| **MAF handoff_hitl 共享狀態** | MAF handoff_hitl 保持現有介面，但底層共享 HITLController 狀態存儲 | 2 |
| **Chat History 後端同步** | Chat history 從 localStorage 同步到後端 PostgreSQL，支援跨裝置 | 2 |

### Sprint 112（~12 SP）：Orchestrator 完整化 + 更多 Tools

| Story | 說明 | SP |
|-------|------|----|
| **新增 Orchestrator Tools** | `assess_risk()`, `search_memory()`, `request_approval()`, `create_task()` | 3 |
| **Tools 分類定義** | Synchronous Tools（< 5s 同步回傳）vs Async Dispatch Tools（返回 task_id，後續查詢） | 2 |
| **基礎 RBAC** | Admin / Operator / Viewer 三種角色，控制 tool 呼叫權限 | 3 |
| **Per-Session Orchestrator** | 每個 Session 獨立 Agent 實例，共享 LLM Pool，避免跨 session 狀態污染 | 2 |
| **AG-UI SSE 串流整合** | 追問問題和回應通過 SSE 串流到前端，實現即時對話體驗 | 2 |

---

## 架構概覽

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Phase 36: E2E Assembly A1 — 基礎組裝                       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                        Frontend (React 18)                             │  │
│  │                                                                        │  │
│  │   ┌─────────────┐    ┌──────────────┐    ┌──────────────────────┐    │  │
│  │   │  Login Page  │───▶│  Chat UI     │───▶│  Approval Dialog     │    │  │
│  │   │  (Auth)      │    │  (SSE Stream)│    │  (HITL Unified)      │    │  │
│  │   └─────────────┘    └──────┬───────┘    └──────────────────────┘    │  │
│  │                              │ SSE                                     │  │
│  └──────────────────────────────┼────────────────────────────────────────┘  │
│                                 ↓                                            │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                        Backend (FastAPI)                                │  │
│  │                                                                        │  │
│  │   ┌──────────────────────────────────────────────────────────────┐    │  │
│  │   │              Tool Security Gateway (Sprint 109)               │    │  │
│  │   │   Input Sanitization → Permission Check → Rate Limit → Audit │    │  │
│  │   └──────────────────────────┬───────────────────────────────────┘    │  │
│  │                               ↓                                        │  │
│  │   ┌──────────────────────────────────────────────────────────────┐    │  │
│  │   │          Prompt Injection 防護 (Sprint 109)                   │    │  │
│  │   │   L1 Input Filter → L2 System Prompt 隔離 → L3 Tool 驗證     │    │  │
│  │   └──────────────────────────┬───────────────────────────────────┘    │  │
│  │                               ↓                                        │  │
│  │   ┌──────────────────────────────────────────────────────────────┐    │  │
│  │   │        Per-Session Orchestrator (Sprint 112)                  │    │  │
│  │   │   ┌──────────────┐   ┌───────────────┐   ┌──────────────┐   │    │  │
│  │   │   │ Intent Route  │──▶│ Direct Answer │   │ Tool Dispatch │   │    │  │
│  │   │   │ (三層路由)     │   │ (簡單問題)     │   │ (複雜操作)    │   │    │  │
│  │   │   └──────────────┘   └───────────────┘   └──────┬───────┘   │    │  │
│  │   │                                                   │           │    │  │
│  │   │   Tools (Sprint 112):                             ↓           │    │  │
│  │   │   • assess_risk()      [Sync  < 5s]     ┌──────────────┐   │    │  │
│  │   │   • search_memory()    [Sync  < 5s]     │ RBAC Check   │   │    │  │
│  │   │   • request_approval() [Async → task_id] │ Admin/Op/View│   │    │  │
│  │   │   • create_task()      [Async → task_id] └──────────────┘   │    │  │
│  │   └──────────────────────────────────────────────────────────────┘    │  │
│  │                               ↓                                        │  │
│  │   ┌──────────────────────────────────────────────────────────────┐    │  │
│  │   │           LLM Call Pool (Sprint 109)                          │    │  │
│  │   │   asyncio.Semaphore + Priority Queue                          │    │  │
│  │   │   Priority: Direct > Intent Route > ExtThinking > Swarm       │    │  │
│  │   └──────────────────────────────────────────────────────────────┘    │  │
│  │                               ↓                                        │  │
│  │   ┌──────────────────────────────────────────────────────────────┐    │  │
│  │   │        統一審批系統 (Sprint 111)                               │    │  │
│  │   │   ┌──────────────────────────────────┐                        │    │  │
│  │   │   │   HITLController (主體)           │                        │    │  │
│  │   │   │   ├── AG-UI ApprovalStorage      │ ← delegate             │    │  │
│  │   │   │   ├── Claude SDK ApprovalHook    │ ← delegate             │    │  │
│  │   │   │   └── MAF handoff_hitl           │ ← 共享狀態存儲          │    │  │
│  │   │   └──────────────────────────────────┘                        │    │  │
│  │   └──────────────────────────────────────────────────────────────┘    │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                               ↓                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │              持久化層 (Sprint 110)                                      │  │
│  │                                                                        │  │
│  │   ┌──────────────────┐        ┌──────────────────────────────────┐    │  │
│  │   │     Redis         │        │         PostgreSQL                │    │  │
│  │   │  • Dialog Sessions│        │  • Approval State                │    │  │
│  │   │  • Rate Limiter   │        │  • Audit Log                     │    │  │
│  │   │  • Session Cache  │        │  • Checkpoint (MAF + Multiturn)  │    │  │
│  │   └──────────────────┘        │  • Chat History                   │    │  │
│  │                                └──────────────────────────────────┘    │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 技術要點

### 1. Tool Security Gateway（Sprint 109）

```
Tool 呼叫流程：
Orchestrator.tool_call()
  → SecurityGateway.validate(tool_name, args, user_context)
    → InputSanitizer.sanitize(args)          # 移除危險字元、驗證格式
    → PermissionChecker.check(user, tool)     # RBAC 權限檢查
    → RateLimiter.acquire(user, tool)         # 限速控制
    → AuditLogger.log(tool_call_event)        # 審計記錄
  → tool.execute(sanitized_args)
  → SecurityGateway.validate_output(result)   # 輸出驗證
```

### 2. Prompt Injection 三層防護（Sprint 109）

| 層級 | 機制 | 說明 |
|------|------|------|
| L1 | Input Filtering | 正則過濾已知 injection pattern（ignore previous, system prompt leak） |
| L2 | System Prompt 隔離 | User input 與 system prompt 嚴格分離，使用 delimiter tokens |
| L3 | Tool Call 驗證 | 驗證 LLM 產生的 tool call 參數是否在允許範圍內 |

### 3. LLM Call Pool 優先級（Sprint 109）

| 優先級 | 類型 | 說明 |
|--------|------|------|
| P0 | 直接回答 | 用戶等待中，最高優先 |
| P1 | 意圖路由 | 決定下一步動作 |
| P2 | Extended Thinking | 深度思考，可容忍延遲 |
| P3 | Swarm Worker | 背景任務，最低優先 |

### 4. InMemory 遷移策略（Sprint 110）

採用 **介面不變、實作替換** 策略：
- 定義統一的 `StorageBackend` 抽象介面
- Redis 實作用於高頻讀寫、短期狀態（sessions、rate limiter）
- PostgreSQL 實作用於持久化、可查詢資料（approval、audit、checkpoint）
- 遷移過程保持 API 向後兼容

### 5. 審批統一策略（Sprint 111）

```
Before (4-5 套獨立系統):
  AG-UI ApprovalStorage      → InMemory dict
  Claude SDK ApprovalHook    → InMemory dict
  MAF handoff_hitl           → InMemory dict
  Orchestration HITLController → InMemory dict

After (1 套統一系統):
  AG-UI ApprovalStorage      → delegate → HITLController → PostgreSQL
  Claude SDK ApprovalHook    → delegate → HITLController → PostgreSQL
  MAF handoff_hitl           → shared state → HITLController → PostgreSQL
  Orchestration HITLController (主體)      → PostgreSQL
```

### 6. Per-Session Orchestrator（Sprint 112）

```python
# 每個 session 獨立 Agent 實例，共享 LLM Pool
class SessionOrchestratorManager:
    def __init__(self, llm_pool: LLMCallPool):
        self._sessions: dict[str, Orchestrator] = {}
        self._llm_pool = llm_pool  # 共享

    async def get_or_create(self, session_id: str) -> Orchestrator:
        if session_id not in self._sessions:
            self._sessions[session_id] = Orchestrator(
                llm_pool=self._llm_pool,  # 共享 LLM Pool
                session_id=session_id,     # 獨立 session 上下文
            )
        return self._sessions[session_id]
```

## 分析報告參考

> 以下報告提供 Phase 36 實施的技術背景與問題清單（同 Phase 35 參考）。

| 文件 | 用途 |
|------|------|
| `docs/07-analysis/Overview/full-codebase-analysis/MAF-Claude-Hybrid-Architecture-V8.md` | 11 層架構深度分析，62 issues 清單 |
| `docs/07-analysis/Overview/full-codebase-analysis/MAF-Features-Architecture-Mapping-V8.md` | 70+ 功能驗證，成熟度矩陣 |
| `docs/07-analysis/Overview/full-codebase-analysis/phase4-validation/phase4-validation-issue-registry.md` | 62 個去重問題（8 CRITICAL, 16 HIGH） |
| `docs/07-analysis/Overview/full-codebase-analysis/Architecture-Review-Board-Consensus-Report.md` | 架構審查委員會共識報告 |

## 風險與降級策略

| 風險 | 影響 | 可能性 | 降級策略 |
|------|------|--------|----------|
| Phase 35 (A0) 未通過驗證 | Phase 36 無法開始 | 中 | 延後啟動，優先修復 A0 阻塞問題 |
| InMemory 遷移範圍過大 | Sprint 110 超時 | 中 | 優先遷移 5 個核心模組，其餘推遲到 Phase 37 |
| 審批統一改動影響現有功能 | 回歸缺陷 | 高 | 保持舊介面不變，內部 delegate；新增整合測試覆蓋 |
| LLM API 併發限制 | Pool 配置需調整 | 低 | Semaphore 上限可配置，依實際 API quota 調整 |
| Prompt Injection 防護誤判 | 正常輸入被攔截 | 中 | L1 filter 設白名單例外；監控 false positive 率 |
| Per-Session 記憶體消耗 | 大量 session 時 OOM | 低 | 設定 session 最大數量 + LRU 淘汰 + idle timeout |
| SSE 串流穩定性 | 前端斷線丟失訊息 | 中 | SSE 重連機制 + 訊息序號 + 補發缺失事件 |

## 驗收標準

### 端到端流程驗收

- [ ] 用戶可以登入系統，session 正確建立
- [ ] 用戶輸入對話，Orchestrator 正確理解意圖
- [ ] 簡單問題（如「你好」、「幫我查資料」）直接回答，延遲 < 3s
- [ ] 高風險操作（如「刪除帳號」、「修改權限」）觸發審批流程
- [ ] 審批通過後操作繼續執行，拒絕後操作取消
- [ ] 對話通過 SSE 串流即時顯示在前端

### 安全基礎驗收

- [ ] 所有 tool 呼叫經過 Security Gateway（無旁路）
- [ ] Prompt Injection 測試案例通過率 > 95%
- [ ] Tool 呼叫有完整 audit log
- [ ] RBAC 三種角色權限正確隔離

### 持久化驗收

- [ ] 核心 InMemory 遷移完成 >= 15 處
- [ ] 服務重啟後 session 狀態不丟失（Redis）
- [ ] 服務重啟後審批狀態不丟失（PostgreSQL）
- [ ] Chat history 可從後端恢復

### 併行基礎驗收

- [ ] LLM Call Pool 正確控制併發（Semaphore 不超限）
- [ ] Priority Queue 正確排序（P0 > P1 > P2 > P3）
- [ ] Per-Session Orchestrator 實例獨立，無跨 session 狀態污染
- [ ] ContextSynchronizer (H-04) 併發安全

### 審批統一驗收

- [ ] 4 套審批系統統一為 1 套 HITLController
- [ ] AG-UI / Claude SDK / MAF 三個入口都能觸發統一審批
- [ ] 審批狀態持久化到 PostgreSQL
- [ ] 現有審批相關測試全部通過（無回歸）

---

## 交付物摘要

完成 Phase 36 後，系統具備以下能力：

1. **端到端可用** — 用戶可以登入 → 對話 → Orchestrator 理解意圖 → 直接回答簡單問題 → 高風險時觸發審批
2. **安全基礎就位** — Tool Security Gateway + Prompt Injection 三層防護 + 基礎 RBAC
3. **持久化基礎就位** — 核心 InMemory 遷移完成，服務重啟不丟失狀態
4. **併行基礎就位** — LLM Call Pool + Per-Session Orchestrator，支撐多用戶同時使用

---

**Phase 36 狀態**: 📋 規劃中
**Story Points**: ~48 pts（4 Sprints: 109-112）
**前置條件**: Phase 35 (A0) 驗證通過
**Last Updated**: 2026-03-19
