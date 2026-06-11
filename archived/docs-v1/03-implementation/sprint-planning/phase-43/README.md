# Phase 43: Agent Swarm 完整實現 — 真正的多 Agent 並行協作

## 概述

Phase 42 完成了 Swarm 的 UI 框架接入（AgentSwarmPanel 嵌入 Chat、SSE 事件定義、swarmStore），
但 Swarm 的**核心執行引擎**仍然是 stub/mock。本 Phase 的目標是讓 Swarm 模式
**從 UI 到後端引擎完整可用**，不使用任何 mock 數據，全部真實執行。

> **Status**: 📋 規劃中 — 3 Sprints (148-150), ~36 SP

## 核心問題（6 個關鍵差距）

### 完整差距分析

| # | 差距 | 現狀 | 目標 | 涉及層 |
|---|------|------|------|--------|
| 1 | **Workers 永遠循序** | `_execute_all_workers()` 用 for loop，即使 mode=parallel | `asyncio.gather()` 真正並行 | Backend Engine |
| 2 | **Workers 無工具存取** | `_execute_worker_task()` 傳 `tools=None` | 每個 Worker 有獨立 tool registry + function calling | Backend Engine |
| 3 | **SwarmEventEmitter 斷接** | 已建置但未連接到 SSE endpoint 或執行路徑 | 每個 Worker 執行時即時發射事件到前端 | Backend SSE |
| 4 | **無 thinking/tool_call 事件** | Worker 只回傳最終結果，無過程事件 | 每步思考、工具調用、進度都即時串流 | Backend + Frontend |
| 5 | **Demo SSE 格式不相容** | demo.py 用 polling+snapshot，與 AG-UI CustomEvent 格式不同 | 統一使用 AG-UI 格式或 Pipeline SSE 格式 | Backend SSE |
| 6 | **swarmStore 未整合** | 各 hook 自管狀態，swarmStore 未被使用 | Chat 中的 Swarm 由 swarmStore 統一管理 | Frontend |

### 現有基礎設施盤點

**已完成（可重用）：**
- ✅ SwarmTracker — 線程安全的 swarm/worker 狀態追蹤
- ✅ SwarmEventEmitter — 事件發射器（含節流與批次）
- ✅ SwarmModeHandler — 框架存在（analyze_for_swarm, execute）
- ✅ Frontend 15 元件 — AgentSwarmPanel, WorkerCard, WorkerDetailDrawer, ExtendedThinkingPanel, ToolCallsPanel 等
- ✅ swarmStore — Zustand store 含完整 actions
- ✅ useSwarmMock/useSwarmReal hooks — 數據流模式可參考
- ✅ AG-UI Swarm 事件類型定義（events.ts: 9 種事件）

**需要修改/新建：**
- ❌ SwarmModeHandler._execute_all_workers() — 改為真正並行
- ❌ WorkerAgent 執行邏輯 — 接入 chat_with_tools + tool registry
- ❌ SwarmEventEmitter → PipelineEventEmitter 橋接
- ❌ 每個 Worker 的 thinking/tool_call/progress SSE 事件
- ❌ ExecutionHandler → SwarmModeHandler 完整接線
- ❌ WorkerDetailDrawer 在 Chat 中接入（目前只在 SwarmTestPage）
- ❌ Task Decomposer — 將複雜任務拆解為子任務分派給 Workers

## 架構設計

### 完整執行流程

```
用戶輸入（Swarm 模式）
    ↓
Pipeline SSE → PIPELINE_START
    ↓
RoutingHandler → 三層路由（安全守門）
    ↓
AgentHandler → TaskDecomposer（LLM 分析任務，拆解為子任務）
    ↓ SSE: ROUTING_COMPLETE
SwarmModeHandler.execute()
    ├── 建立 SwarmSession（SwarmTracker）
    ├── 分派子任務到 Workers
    │   ↓ SSE: SWARM_WORKER_START (per worker)
    ├── Worker 1: NetworkExpert
    │   ├── LLM chat_with_tools()
    │   ├── SSE: WORKER_THINKING (每步思考)
    │   ├── SSE: WORKER_TOOL_CALL (工具調用)
    │   ├── SSE: WORKER_PROGRESS (進度更新)
    │   └── SSE: WORKER_COMPLETED (結果)
    ├── Worker 2: DatabaseExpert (並行)
    │   └── ... 同上
    └── Worker 3: ApplicationExpert (並行)
        └── ... 同上
    ↓
ResultAggregator（LLM 整合所有 Worker 結果）
    ↓ SSE: TEXT_DELTA (逐 token 串流整合結果)
    ↓ SSE: PIPELINE_COMPLETE
前端更新：
    ├── AgentSwarmPanel: WorkerCard 即時進度
    ├── WorkerDetailDrawer: thinking + tool calls + messages
    └── ChatArea: 整合後的最終回應
```

### Worker 執行架構

```python
class SwarmWorkerExecutor:
    """每個 Worker 的獨立執行器"""

    def __init__(self, worker_id, role, task, llm_service, tool_registry, event_emitter):
        self.worker_id = worker_id
        self.role = role          # e.g. "network_expert"
        self.task = task          # 子任務描述
        self.llm = llm_service    # chat_with_tools()
        self.tools = tool_registry
        self.emitter = event_emitter

    async def execute(self) -> WorkerResult:
        """執行子任務，過程中即時發射事件"""
        # 1. 發射 WORKER_THINKING
        await self.emitter.emit("SWARM_WORKER_THINKING", {...})

        # 2. LLM chat_with_tools (function calling loop)
        #    每次 tool call 發射 WORKER_TOOL_CALL
        result = await self._function_calling_loop()

        # 3. 發射 WORKER_COMPLETED
        await self.emitter.emit("SWARM_WORKER_COMPLETED", {...})

        return WorkerResult(content=result, worker_id=self.worker_id)
```

### SSE 事件完整定義

| 事件 | 發射時機 | 數據 |
|------|---------|------|
| SWARM_STARTED | Swarm session 建立 | swarm_id, mode, total_workers, tasks[] |
| SWARM_WORKER_START | Worker 開始執行 | worker_id, agent_name, role, task |
| SWARM_WORKER_THINKING | Worker LLM 思考中 | worker_id, thinking_content |
| SWARM_WORKER_TOOL_CALL | Worker 調用工具 | worker_id, tool_name, arguments, result |
| SWARM_WORKER_PROGRESS | Worker 進度更新 | worker_id, progress (0-100), current_action |
| SWARM_WORKER_MESSAGE | Worker 產生中間訊息 | worker_id, content |
| SWARM_WORKER_COMPLETED | Worker 完成 | worker_id, status, result, duration_ms |
| SWARM_WORKER_FAILED | Worker 失敗 | worker_id, error, partial_result |
| SWARM_PROGRESS | 整體進度更新 | overall_progress, completed_workers |
| SWARM_AGGREGATING | 開始整合結果 | aggregator_status |
| SWARM_COMPLETED | 整個 Swarm 完成 | final_result, total_duration_ms, worker_summaries |

## Sprint 規劃

| Sprint | 名稱 | Story Points | 重點 |
|--------|------|-------------|------|
| [Sprint 148](./sprint-148-plan.md) | Swarm Core Engine — 真正的多 Agent 並行 | ~14 | 任務拆解 + Worker 並行執行 + 工具存取 + SSE 事件 |
| [Sprint 149](./sprint-149-plan.md) | Worker Detail Visualization — 即時細節展示 | ~12 | WorkerDetailDrawer + Extended Thinking + Tool Calls + swarmStore |
| [Sprint 150](./sprint-150-plan.md) | Result Aggregation + Robustness + E2E | ~10 | 結果整合 + 錯誤處理 + 完整 E2E 驗證 |

**總計**: ~36 Story Points (3 Sprints)

## 設計原則

1. **先查現有基礎設施** — SwarmTracker, SwarmEventEmitter, swarmStore 都要重用，不重建
2. **使用 LLMServiceProtocol** — Worker 透過 `chat_with_tools()` 呼叫 LLM，不直接建 client
3. **AG-UI 事件格式** — 使用已定義的 AG-UI CustomEvent 格式，不建新的平行系統
4. **模式由用戶控制** — 三層路由做安全守門，Swarm 模式由用戶手動選擇
5. **不使用 mock 數據** — 所有 Worker 執行真正的 LLM 推理和工具調用

## 前置條件

- ✅ Phase 42 — SSE 串流端點、Mode Selector、HITL 審批
- ✅ LLMServiceProtocol.chat_with_tools() — REFACTOR-001
- ✅ OrchestratorToolRegistry — 8 工具已註冊
- ✅ Frontend 15 Swarm 元件 — Phase 29 已建立
- ✅ swarmStore — Zustand store 已定義

## 風險與緩解

| 風險 | 影響 | 緩解 |
|------|------|------|
| 多個 Worker 並行調 LLM → API rate limit | 高 | 加入 rate limiter + 可配置最大並行數 |
| Worker 執行時間不可預測 | 中 | 每個 Worker 設 timeout (60s default) + 超時 graceful fallback |
| Task 拆解不準確 | 中 | LLM prompt 加入結構化拆解規則 + 用戶可手動調整 |
| 前端大量即時事件造成卡頓 | 中 | SwarmEventEmitter 節流 (100ms) + React memo 優化 |
| 結果整合品質不穩 | 中 | LLM 整合 prompt 含結構化規則 + 顯示各 Worker 原始結果 |

---

**Phase 43 前置**: Phase 42 (E2E Pipeline Deep Integration)
**總 Story Points**: ~36 pts
**Sprint 範圍**: Sprint 148-150
**核心目標**: Swarm 從 mock → 真實完整可用
