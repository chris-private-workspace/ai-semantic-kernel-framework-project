# Sprint 137: 安全加固 + E2E 整合測試

## Sprint 目標

1. ToolSecurityGateway 接入 OrchestratorToolRegistry.execute()
2. HITL 審批持久化到 PostgreSQL（取代 in-memory）
3. 統一 RiskAssessor 和 RiskAssessmentEngine
4. E2E 整合煙霧測試（完整 10 步流程）
5. Extended Thinking 執行模式

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 39 — E2E Assembly D |
| **Sprint** | 137 |
| **Story Points** | 10 點 |
| **狀態** | 📋 計劃中 |

## Sprint 概述

Sprint 137 是 Phase 39 的最後一個 Sprint，也是整個 E2E Assembly 計劃（Phase 35-39）的收官 Sprint。專注於安全層最終接入（ToolSecurityGateway 攔截所有工具調用）、HITL 審批從 in-memory 遷移到 PostgreSQL 持久化、統一兩個並存的風險評估引擎、實現 Extended Thinking 執行模式，以及撰寫完整的 E2E 10 步煙霧測試驗證端到端管線正確性。

## User Stories

### S137-1: ToolSecurityGateway 接入 (2 SP)

**作為** 安全管理員
**我希望** 所有工具調用都經過 ToolSecurityGateway 安全檢查
**以便** 防止未授權的工具執行和危險操作

**技術規格**:
- 修改 `backend/src/integrations/hybrid/orchestrator/tools.py`
  - `OrchestratorToolRegistry.execute()` 在調用工具前先過 `ToolSecurityGateway.check()`
  - 引入 `backend/src/core/security/tool_gateway.py` 的 `ToolSecurityGateway`
  - 安全檢查失敗時返回 `{"error": "blocked", "reason": "..."}` 而非拋出異常
  - 記錄所有安全攔截事件到 audit log
- 修改 `backend/src/core/security/tool_gateway.py`
  - 確保 `check()` 方法接受 tool_name + params + user_context
  - 新增 `audit_blocked_call(tool_name, reason, user_id)` — 記錄攔截日誌
  - 確保與 RBAC 系統 (`backend/src/core/security/rbac.py`) 整合

### S137-2: HITL 審批持久化到 PostgreSQL (2 SP)

**作為** 平台運維人員
**我希望** HITL 審批記錄持久化到 PostgreSQL
**以便** 系統重啟後審批狀態不丟失，支援審計追蹤

**技術規格**:
- 修改 `backend/src/infrastructure/storage/approval_store.py`
  - 新增 `PostgresApprovalStore` 類（取代現有 in-memory 實作）
  - `save_approval()` — 寫入 PostgreSQL
  - `load_approval()` — 從 PostgreSQL 讀取
  - `list_pending()` — 查詢所有 pending 狀態的審批
  - `update_status()` — 更新審批狀態（approved/rejected）
  - 保留 `InMemoryApprovalStore` 作為 fallback
- 修改 `backend/src/infrastructure/storage/storage_factories.py`
  - `create_approval_store()` 優先建立 PostgresApprovalStore
  - PostgreSQL 不可用時 fallback 到 InMemoryApprovalStore
- 修改 `backend/src/integrations/hybrid/orchestrator/handlers/approval.py`
  - `ApprovalHandler` 使用 StorageFactory 取得 approval store
  - 確保審批流程使用持久化 store

### S137-3: 統一 RiskAssessor 和 RiskAssessmentEngine (2 SP)

**作為** 系統架構師
**我希望** 統一兩個並存的風險評估引擎
**以便** 消除重複邏輯，降低維護成本

**技術規格**:
- 修改 `backend/src/integrations/orchestration/risk_assessor/assessor.py`
  - `RiskAssessor` 作為統一的風險評估入口
  - 整合 `backend/src/integrations/hybrid/risk/engine.py` 的 `RiskAssessmentEngine` 邏輯
  - 統一風險評分算法：合併兩個引擎的評估維度
  - 統一回傳格式：`RiskAssessmentResult(score, level, factors, recommendation)`
- 修改 `backend/src/integrations/hybrid/risk/engine.py`
  - `RiskAssessmentEngine` 改為 `RiskAssessor` 的 thin wrapper（向後兼容）
  - 標記為 `@deprecated`，引導使用者遷移到 `RiskAssessor`
- 修改 `backend/src/integrations/hybrid/orchestrator/dispatch_handlers.py`
  - 統一使用 `RiskAssessor` 進行風險評估
- 修改 `backend/src/integrations/orchestration/risk_assessor/__init__.py`
  - 更新匯出：統一的 `RiskAssessor` + `RiskAssessmentResult`
- 修改 `backend/src/integrations/hybrid/risk/__init__.py`
  - 匯出 deprecated wrapper

### S137-4: E2E 整合煙霧測試 (2 SP)

**作為** QA 工程師
**我希望** 有完整的 E2E 10 步煙霧測試
**以便** 驗證端到端管線在組裝後正確運作

**技術規格**:
- 新增 `tests/integration/test_e2e_smoke.py`
  - 10 步煙霧測試流程：
    1. Auth — JWT token 取得
    2. Session — 建立新 session
    3. InputGateway — 發送用戶訊息
    4. Routing — 驗證路由決策
    5. Risk Assessment — 風險評估通過
    6. Agent Execution — agent 處理（mock LLM）
    7. Tool Call — 工具調用（mock tool）
    8. Result — 結果返回
    9. Checkpoint — 狀態持久化驗證
    10. Session Resume — 恢復 session 驗證
  - 使用 `pytest` + `httpx.AsyncClient` 測試 FastAPI app
  - Mock 外部依賴：LLM API、Redis、PostgreSQL
  - 每步驗證狀態正確性和資料完整性
- 修改 `backend/src/integrations/hybrid/orchestrator/e2e_validator.py`
  - 更新 `E2EValidator` 支援 10 步驗證（原有驗證邏輯擴展）
  - 新增 `validate_full_pipeline()` — 完整管線驗證

### S137-5: Extended Thinking 執行模式 (2 SP)

**作為** 進階用戶
**我希望** 能啟用 Extended Thinking 模式
**以便** 對複雜問題獲得更深入的推理分析結果

**技術規格**:
- 新增 `backend/src/integrations/claude_sdk/extended_thinking.py`
  - `ExtendedThinkingConfig` model: enabled, budget_tokens, max_thinking_time
  - `ExtendedThinkingExecutor` 類：
    - `execute(prompt, config)` — 帶 thinking 的 Claude API 調用
    - `stream_thinking(prompt, config)` — 串流 thinking tokens
    - 整合 AG-UI 事件：thinking tokens 作為中間事件串流
- 修改 `backend/src/integrations/hybrid/orchestrator/dispatch_handlers.py`
  - 新增 `dispatch_extended_thinking(session_id, prompt, thinking_config)` 方法
  - 根據 routing decision 自動啟用 extended thinking
- 修改 `backend/src/integrations/claude_sdk/__init__.py`
  - 匯出 `ExtendedThinkingConfig`, `ExtendedThinkingExecutor`

## 檔案變更清單

### 新增檔案
| 檔案 | 說明 |
|------|------|
| `tests/integration/test_e2e_smoke.py` | E2E 10 步煙霧測試 |
| `backend/src/integrations/claude_sdk/extended_thinking.py` | Extended Thinking 執行器 |

### 修改檔案
| 檔案 | 說明 |
|------|------|
| `backend/src/integrations/hybrid/orchestrator/tools.py` | 接入 ToolSecurityGateway |
| `backend/src/core/security/tool_gateway.py` | 新增 audit 方法、完善 check() |
| `backend/src/infrastructure/storage/approval_store.py` | 新增 PostgresApprovalStore |
| `backend/src/infrastructure/storage/storage_factories.py` | approval store factory 更新 |
| `backend/src/integrations/hybrid/orchestrator/handlers/approval.py` | 使用持久化 store |
| `backend/src/integrations/orchestration/risk_assessor/assessor.py` | 統一風險評估邏輯 |
| `backend/src/integrations/hybrid/risk/engine.py` | 改為 deprecated wrapper |
| `backend/src/integrations/hybrid/orchestrator/dispatch_handlers.py` | 統一 RiskAssessor + Extended Thinking |
| `backend/src/integrations/orchestration/risk_assessor/__init__.py` | 更新匯出 |
| `backend/src/integrations/hybrid/risk/__init__.py` | 匯出 deprecated wrapper |
| `backend/src/integrations/hybrid/orchestrator/e2e_validator.py` | 擴展 10 步驗證 |
| `backend/src/integrations/claude_sdk/__init__.py` | 匯出 Extended Thinking |

## 驗收標準

- [ ] ToolSecurityGateway 攔截所有 OrchestratorToolRegistry.execute() 調用
- [ ] 安全攔截事件記錄到 audit log
- [ ] HITL 審批記錄持久化到 PostgreSQL
- [ ] 系統重啟後審批狀態不丟失
- [ ] PostgreSQL 不可用時 fallback 到 InMemoryApprovalStore
- [ ] RiskAssessor 統一兩個引擎的評估邏輯
- [ ] RiskAssessmentEngine 標記為 deprecated 並保持向後兼容
- [ ] E2E 10 步煙霧測試全部通過
- [ ] Extended Thinking 模式可正確執行並串流 thinking tokens
- [ ] 完整管線 Auth → Session → Mediator → Worker → Response 端到端可跑通

## 相關連結

- [Phase 39 計劃](./README.md)
- [Sprint 136 Plan](./sprint-136-plan.md)

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 10
