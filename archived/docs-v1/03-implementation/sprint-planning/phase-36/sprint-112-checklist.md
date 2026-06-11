# Sprint 112 Checklist: Orchestrator 完整化 + 更多 Tools

## Sprint 目標

| 項目 | 值 |
|------|-----|
| **總點數** | 12 點 |
| **狀態** | ✅ 完成 |

---

## 開發任務

### S112-1: Orchestrator Tools (3 SP)
- [x] 新增 `backend/src/integrations/hybrid/orchestrator/tools.py`
- [x] 實作 OrchestratorToolRegistry
- [x] 定義 6 個內建工具（assess_risk, search_memory, request_approval, create_task 等）
- [x] 定義 Synchronous Tools 分類（< 5s 同步回傳）
- [x] 定義 Async Dispatch Tools 分類（返回 task_id）
- [x] 工具元資料：名稱、描述、參數定義、分類

### S112-2: AgentHandler Tools 整合 (2 SP)
- [x] 修改 `backend/src/integrations/hybrid/orchestrator/agent_handler.py`
- [x] 整合 OrchestratorToolRegistry
- [x] AgentHandler 可查詢並呼叫已註冊工具
- [x] 工具呼叫經過 Security Gateway 驗證

### S112-3: 基礎 RBAC (3 SP)
- [x] 新增 `backend/src/core/security/rbac.py`
- [x] 定義 Admin 角色（全部權限）
- [x] 定義 Operator 角色（核心操作）
- [x] 定義 Viewer 角色（唯讀）
- [x] 實作角色與工具權限對應表
- [x] 與 Tool Security Gateway 整合
- [x] 更新 `backend/src/core/security/__init__.py` 匯出

### S112-4: Per-Session Factory (2 SP)
- [x] 新增 `backend/src/integrations/hybrid/orchestrator/session_factory.py`
- [x] 實作 `SessionOrchestratorManager`
- [x] 共享 LLM Pool，獨立 session 上下文
- [x] 支援 session 最大數量限制
- [x] 支援 idle timeout
- [x] 更新 `backend/src/integrations/hybrid/orchestrator/__init__.py` 匯出

### S112-5: Endpoint 更新 (2 SP)
- [x] 修改 `backend/src/api/v1/orchestrator/routes.py`
- [x] 整合 Per-Session Orchestrator Factory
- [x] 支援 AG-UI SSE 串流回應
- [x] 追問問題和回應通過 SSE 串流到前端

## 驗證標準

- [x] OrchestratorToolRegistry 定義 6 個內建工具
- [x] AgentHandler 可透過 Tool Registry 呼叫工具
- [x] RBAC 三種角色權限正確隔離（Admin/Operator/Viewer）
- [x] Per-Session Orchestrator 實例獨立，無跨 session 狀態污染
- [x] Chat Endpoint 支援 SSE 串流回應
- [x] 所有新增檔案模組匯出正確

## 相關連結

- [Phase 36 計劃](./README.md)
- [Sprint 112 Progress](../../sprint-execution/sprint-112/progress.md)
- [Sprint 112 Plan](./sprint-112-plan.md)

---

**Sprint 狀態**: ✅ 完成
**Story Points**: 12
**完成日期**: 2026-03-19
