# Sprint 109: 安全基礎 + LLM Call Pool

## Sprint 目標

1. Tool Security Gateway（4 層安全驗證）
2. Prompt Injection 防護（3 層防禦）
3. LLM Call Pool（併發控制 + 優先級佇列）
4. 修復 H-04 ContextSynchronizer（asyncio.Lock）

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 36 — E2E Assembly A1 |
| **Sprint** | 109 |
| **Story Points** | 12 點 |
| **狀態** | ✅ 完成 |

## Sprint 概述

Sprint 109 是 Phase 36 的第一個 Sprint，專注於建立安全基礎設施與 LLM 併發控制機制。包含 Tool Security Gateway 四層安全驗證（Input Sanitization → Permission Check → Rate Limiting → Audit Logging）、Prompt Injection 三層防護（L1 Input Filtering → L2 System Prompt 隔離 → L3 Tool Call 驗證）、LLM Call Pool 優先級排程，以及修復 H-04 ContextSynchronizer 併發競態問題。

## User Stories

### S109-1: Tool Security Gateway (4 SP)

**作為** 平台管理員
**我希望** 所有 Orchestrator tool 呼叫都經過安全層驗證
**以便** 確保 tool 呼叫的安全性，防止未授權操作

**技術規格**:
- 新增 `backend/src/core/security/tool_gateway.py`
- 4 層安全：Input Sanitization (18 regex patterns) → Permission Check (UserRole enum) → Rate Limiting → Audit Logging
- 角色權限：Admin (全部), Operator (核心 tools), Viewer (唯讀 tools)
- Rate limit：30 calls/min 一般, 5 calls/min 高風險 tools
- 支援 decorator 和 standalone validation 兩種使用模式

### S109-2: Prompt Injection 防護 (3 SP)

**作為** 系統安全工程師
**我希望** 用戶輸入經過多層 prompt injection 防護
**以便** 防止惡意輸入操控 LLM 行為或洩漏系統資訊

**技術規格**:
- 新增 `backend/src/core/security/prompt_guard.py`
- L1: Input Filtering (20+ injection patterns — role confusion, boundary escape, exfiltration, code injection)
- L2: System Prompt Isolation (`wrap_user_input()` with `<user_message>` boundaries)
- L3: Tool Call Validation (whitelist + arg safety checks)
- 最大輸入長度 4000 characters

### S109-3: LLM Call Pool (3 SP)

**作為** 後端開發者
**我希望** LLM API 呼叫有併發控制與優先級排程
**以便** 避免 LLM API 過載，確保高優先級請求優先處理

**技術規格**:
- 新增 `backend/src/core/performance/llm_pool.py`
- `asyncio.Semaphore` 控制最大併發 LLM 呼叫
- `asyncio.PriorityQueue` 優先級排程：CRITICAL > DIRECT_RESPONSE > INTENT_ROUTING > EXTENDED_THINKING > SWARM_WORKER
- Per-minute rate tracking + token budget tracking
- `LLMCallToken` async context manager 自動釋放
- Singleton 模式，全域共享

### S109-4: H-04 ContextSynchronizer 修復 (2 SP)

**作為** 後端開發者
**我希望** ContextSynchronizer 的併發競態問題被修復
**以便** 消除多個 session 同時操作時的資料競爭風險

**技術規格**:
- 修改 `backend/src/integrations/hybrid/context/sync/synchronizer.py`
- 新增 `self._state_lock = asyncio.Lock()` 保護 in-memory dicts
- 7 個存取點更新：`_context_versions` 和 `_rollback_snapshots` 的讀寫均受 lock 保護
- `_save_snapshot` 轉為 async 方法，加入 state lock
- 保留原有 `self._lock` 用於跨操作同步

## 相關連結

- [Phase 36 計劃](./README.md)
- [Sprint 109 Progress](../../sprint-execution/sprint-109/progress.md)
- [Sprint 110 Plan](./sprint-110-plan.md)

---

**Sprint 狀態**: ✅ 完成
**Story Points**: 12
**完成日期**: 2026-03-19
