# Sprint 114: MAF Workflow + Claude Worker 接通 + TaskResult Protocol

## Sprint 目標

1. TaskResult Protocol（統一 Worker 結果格式）
2. TaskResultNormaliser（MAF / Claude / Swarm 結果正規化）
3. ResultSynthesiser（LLM 驅動多結果整合）
4. DispatchHandlers 升級（真正調用框架 + 結果正規化）
5. Orchestrator routes 接線 ResultSynthesiser

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 37 — E2E Assembly B |
| **Sprint** | 114 |
| **Story Points** | 12 點 |
| **狀態** | ✅ 完成 |

## Sprint 概述

Sprint 114 是 Phase 37 的第二個 Sprint，專注於讓 Orchestrator 能實際驅動 MAF Workflow 和 Claude Worker，並統一結果回傳。包含 TaskResult Protocol（WorkerType / ResultStatus / WorkerResult / TaskResultEnvelope）、TaskResultNormaliser 靜態類別（from_maf_execution / from_claude_response / from_swarm_coordination）、ResultSynthesiser（單結果 pass-through + 多結果 LLM 綜合 + 無 LLM fallback 拼接），以及 DispatchHandlers 升級為真正調用框架並經過結果正規化。

## User Stories

### S114-1: TaskResult Protocol (3 SP)

**作為** 系統架構師
**我希望** 有統一的 Worker 結果回傳格式
**以便** 不同類型的 Worker（MAF / Claude / Swarm）結果能被統一處理與綜合

**技術規格**:
- 新增 `backend/src/integrations/hybrid/orchestrator/task_result_protocol.py`
- `WorkerType` enum: MAF_WORKFLOW / CLAUDE_WORKER / SWARM / DIRECT
- `ResultStatus` enum: SUCCESS / PARTIAL / FAILED / TIMEOUT / CANCELLED
- `WorkerResult` model: worker_id, worker_type, output, error, tool_calls, tokens_used, duration_ms
- `TaskResultEnvelope` model: 包裝多個 WorkerResult，自動聚合 duration 和 tokens
  - `add_result()` 方法自動降級 overall_status
  - `get_outputs()` 提取所有有效輸出

### S114-2: TaskResultNormaliser (3 SP)

**作為** 後端開發者
**我希望** 各框架的結果能自動正規化為統一格式
**以便** 消除不同框架返回值的差異，簡化下游處理邏輯

**技術規格**:
- `TaskResultNormaliser` 靜態類別，3 個正規化方法：
  - `from_maf_execution()` — 處理 dict / object 兩種 MAF 結果格式
  - `from_claude_response()` — 處理 dict / str / object，提取 token 用量
  - `from_swarm_coordination()` — 處理 swarm 狀態和子結果

### S114-3: ResultSynthesiser (3 SP)

**作為** Orchestrator 系統
**我希望** 多個 Worker 的結果能被智能綜合為最終回應
**以便** 用戶收到連貫統一的回應，而非零散的多個結果

**技術規格**:
- 新增 `backend/src/integrations/hybrid/orchestrator/result_synthesiser.py`
- 單結果直接 pass-through（無需 LLM）
- 多結果用 LLM 綜合（繁中 prompt template）
- 無 LLM 時 fallback 結構化拼接
- 綜合結果自動寫回 `envelope.synthesised_response`

### S114-4: DispatchHandlers 升級 + routes 接線 (3 SP)

**作為** 系統整合工程師
**我希望** DispatchHandlers 能真正調用各框架並正規化結果
**以便** Orchestrator 的 dispatch 路徑從 stub 升級為端到端可執行

**技術規格**:
- 修改 `backend/src/integrations/hybrid/orchestrator/dispatch_handlers.py`
  - 所有 dispatch handlers 建立 `TaskResultEnvelope`
  - `handle_dispatch_workflow` — 調用 WorkflowExecutorAdapter + TaskResultNormaliser
  - `handle_dispatch_swarm` — 調用 SwarmIntegration.on_coordination_started() + TaskResultNormaliser
  - `handle_dispatch_to_claude` — 準備 ClaudeCoordinator dispatch + TaskResultNormaliser
  - `register_all()` 新增 update_task_status handler
  - 構造函數新增 `result_synthesiser` 參數
- 修改 `backend/src/api/v1/orchestrator/routes.py`
  - `_get_tool_registry()` 建立 ResultSynthesiser 並注入 DispatchHandlers
- 修改 `backend/src/integrations/hybrid/orchestrator/__init__.py`
  - 新增匯出: TaskResultEnvelope, TaskResultNormaliser, WorkerResult, WorkerType, ResultStatus, ResultSynthesiser

## 相關連結

- [Phase 37 計劃](./README.md)
- [Sprint 113 Plan](./sprint-113-plan.md)
- [Sprint 114 Progress](../../sprint-execution/sprint-114/progress.md)
- [Sprint 115 Plan](./sprint-115-plan.md)

---

**Sprint 狀態**: ✅ 完成
**Story Points**: 12
**完成日期**: 2026-03-19
