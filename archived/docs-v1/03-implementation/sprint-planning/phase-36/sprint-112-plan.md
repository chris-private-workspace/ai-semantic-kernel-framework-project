# Sprint 112: Orchestrator 完整化 + 更多 Tools

## Sprint 目標

1. OrchestratorToolRegistry（6 個內建工具定義）
2. AgentHandler 整合 Tool Registry
3. 基礎 RBAC（Admin/Operator/Viewer）
4. Per-Session Orchestrator Factory
5. Orchestrator Chat Endpoint 更新

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 36 — E2E Assembly A1 |
| **Sprint** | 112 |
| **Story Points** | 12 點 |
| **狀態** | ✅ 完成 |

## Sprint 概述

Sprint 112 是 Phase 36 的最後一個 Sprint，專注於 Orchestrator 完整化。新增核心 tools（`assess_risk()`, `search_memory()`, `request_approval()`, `create_task()` 等），定義 Synchronous 與 Async Dispatch 兩類工具分類，實現基礎 RBAC 三種角色控制，以及 Per-Session Orchestrator 獨立實例策略，確保每個 session 獨立 Agent 實例、共享 LLM Pool、避免跨 session 狀態污染。

## User Stories

### S112-1: Orchestrator Tools (3 SP)

**作為** Orchestrator 開發者
**我希望** 有完整的內建工具定義與註冊機制
**以便** Orchestrator 能夠執行風險評估、記憶搜尋、審批請求、任務建立等操作

**技術規格**:
- 新增 `backend/src/integrations/hybrid/orchestrator/tools.py`
- OrchestratorToolRegistry 定義 6 個內建工具
- 工具包含：`assess_risk()`, `search_memory()`, `request_approval()`, `create_task()` 等
- Synchronous Tools（< 5s 同步回傳）vs Async Dispatch Tools（返回 task_id，後續查詢）
- 工具元資料包含名稱、描述、參數定義、分類

### S112-2: AgentHandler Tools 整合 (2 SP)

**作為** 後端開發者
**我希望** AgentHandler 整合 Tool Registry
**以便** Orchestrator Agent 能透過 AgentHandler 呼叫已註冊的工具

**技術規格**:
- 修改 `backend/src/integrations/hybrid/orchestrator/agent_handler.py`
- 整合 OrchestratorToolRegistry
- AgentHandler 可查詢並呼叫已註冊工具
- 工具呼叫經過 Security Gateway（Sprint 109）驗證

### S112-3: 基礎 RBAC (3 SP)

**作為** 平台管理員
**我希望** 有基礎的角色權限控制機制
**以便** 不同角色的用戶只能存取對應權限的工具和操作

**技術規格**:
- 新增 `backend/src/core/security/rbac.py`
- 定義三種角色：Admin（全部權限）/ Operator（核心操作）/ Viewer（唯讀）
- 角色與工具權限對應表
- 與 Tool Security Gateway（Sprint 109）整合
- 更新 `backend/src/core/security/__init__.py` 匯出

### S112-4: Per-Session Factory (2 SP)

**作為** 後端架構師
**我希望** 每個 Session 有獨立的 Orchestrator Agent 實例
**以便** 避免跨 session 狀態污染，同時共享 LLM Pool 資源

**技術規格**:
- 新增 `backend/src/integrations/hybrid/orchestrator/session_factory.py`
- `SessionOrchestratorManager` 管理 per-session 實例
- 共享 LLM Pool（Sprint 109），獨立 session 上下文
- 支援 session 最大數量限制 + idle timeout
- 更新 `backend/src/integrations/hybrid/orchestrator/__init__.py` 匯出

### S112-5: Endpoint 更新 (2 SP)

**作為** 前端開發者
**我希望** Orchestrator Chat Endpoint 支援 Per-Session 實例和工具呼叫
**以便** 前端可以透過統一端點進行對話，並享受 SSE 串流回應

**技術規格**:
- 修改 `backend/src/api/v1/orchestrator/routes.py`
- 整合 Per-Session Orchestrator Factory
- 支援 AG-UI SSE 串流回應
- 追問問題和回應通過 SSE 串流到前端

## 相關連結

- [Phase 36 計劃](./README.md)
- [Sprint 112 Progress](../../sprint-execution/sprint-112/progress.md)
- [Sprint 111 Plan](./sprint-111-plan.md)

---

**Sprint 狀態**: ✅ 完成
**Story Points**: 12
**完成日期**: 2026-03-19
