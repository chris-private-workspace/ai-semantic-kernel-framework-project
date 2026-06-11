# Sprint 155 Plan - Step 6 LLM 選路 + 分派層

## Phase 45: Orchestration Core

### Sprint 目標
從 PoC 提取 LLM 選路決策邏輯，建立完整的分派執行層（DispatchService + 5 個 Executor）。

---

## User Stories

### US-155-1: LLMRouteStep（LLM 選路決策）
**作為** orchestration pipeline，
**我希望** 在收集所有上下文後用 LLM + select_route() function calling 選擇最佳執行路線，
**以便** 動態決策取代固定映射表。

### US-155-2: DirectAnswerExecutor
**作為** DispatchService，
**我希望** 對簡單查詢直接用 LLM 串流回應，
**以便** 低風險問答不需要啟動 agent 團隊。

### US-155-3: SubagentExecutor
**作為** DispatchService，
**我希望** 對獨立並行任務啟動多個 MAF agent 並行執行，
**以便** 多個子任務可同時處理。

### US-155-4: TeamExecutor
**作為** DispatchService，
**我希望** 對需要協作的複雜任務啟動 expert agent 團隊，
**以便** 專家之間能交換資訊並協作解決問題。

---

## 檔案變更

| 檔案 | 動作 | 說明 |
|------|------|------|
| `pipeline/steps/step6_llm_route.py` | NEW | LLMRouteStep |
| `dispatch/__init__.py` | NEW | 模組入口 |
| `dispatch/service.py` | NEW | DispatchService |
| `dispatch/models.py` | NEW | DispatchRequest, DispatchResult |
| `dispatch/sse_emitter.py` | NEW | SSE 事件輔助 |
| `dispatch/executors/__init__.py` | NEW | 模組入口 |
| `dispatch/executors/base.py` | NEW | BaseExecutor 抽象基類 |
| `dispatch/executors/direct_answer.py` | NEW | DirectAnswerExecutor |
| `dispatch/executors/subagent.py` | NEW | SubagentExecutor |
| `dispatch/executors/team.py` | NEW | TeamExecutor |
| `dispatch/executors/swarm.py` | NEW | SwarmExecutor (stub) |
| `dispatch/executors/workflow.py` | NEW | WorkflowExecutor (stub) |

---

**Story Points**: 23
