# Phase 42: E2E Pipeline Deep Integration — SSE + Task Dispatch + Swarm UI

## 概述

Phase 41 完成了 Chat Pipeline 的基礎接通（7 Handler 連接、IntentStatusChip、記憶系統），但經過詳細分析發現**核心架構缺口**：Pipeline 使用同步 POST 而非 SSE 串流，導致多個關鍵功能無法運作。

Phase 42 專注於**修復這些深層整合問題**，讓 10 步 E2E 流程真正端到端可運作。

> **Status**: 📋 規劃中 — 4 Sprints (144-147), ~40 SP

## 核心問題（Phase 41 後的 Gap 分析）

### Top 5 Critical Blockers（阻止 E2E 的根因）

| # | 問題 | 影響 | 涉及檔案 |
|---|------|------|---------|
| 1 | **FrameworkSelector 空分類器** — 初始化時 classifiers=[]，全歸 CHAT_MODE | 步驟 4-8 全不觸發 | `hybrid/intent/router.py` |
| 2 | **AgentHandler 無 Function Calling** — 用 `generate()` 不用 tool_use API，LLM 無法實際調用工具 | 工具/任務/Swarm 都無法被 LLM 觸發 | `agent_handler.py` |
| 3 | **SSE 完全斷線** — MediatorEventBridge 存在但未被任何端點使用；AG-UI 路由用舊 bridge | 無即時串流、HITL 無法中斷 | `ag_ui/routes.py`, `mediator_bridge.py` |
| 4 | **OrchestratorMemoryManager.memory_client=None** — Bootstrap 沒傳 mem0/UnifiedMemoryManager | 記憶讀寫在 pipeline 內是 no-op | `bootstrap.py:209` |
| 5 | **Session/Checkpoint 只在記憶體** — Mediator 用 Python dict，SessionRecoveryManager 無 API | 重啟全丟失 | `mediator.py:89`, `session_recovery.py` |

### 同步 POST vs SSE 串流問題

Phase 41 將 Chat 接到 `/orchestrator/chat`（同步 POST），收到完整回應後用 typewriter 模擬串流。這破壞了：

| 功能 | 預期行為 | 實際行為 | 根因 |
|------|---------|---------|------|
| SSE 即時串流 | 逐 token 串流 | 同步等待 + 假打字 | 用 POST 不用 SSE |
| HITL 審批 | 中途暫停等審批 | 無法暫停 | 同步不可中斷 |
| Swarm 進度 | 即時顯示 Worker 狀態 | 無顯示 | swarmStore 未被填充 |
| 工具調用追蹤 | 即時顯示執行中 | 只顯示完成後 | 同步回傳全部結果 |
| 任務分發 | 顯示 TaskProgressCard | 無 task_id | AgentHandler 全 short-circuit |
| Function Calling | LLM 調用 dispatch 工具 | LLM 只生成文字 | generate() 不是 tool_use |

### 10 步流程整合狀態

| 步驟 | 功能 | 後端 | 前端 | 綜合 |
|------|------|------|------|------|
| ① 多入口 + Gateway | InputGateway | PARTIAL | N/A | ⚠️ |
| ② Session 管理 | CRUD + 持久化 | PARTIAL（記憶體） | INTEGRATED | ⚠️ |
| ③ 三層路由 + 風險 | Pattern→Semantic→LLM + 7維度 | PARTIAL（Semantic 需訓練、風險簡化） | INTEGRATED（IntentStatusChip）| ⚠️ |
| ④ Orchestrator 決策 | 5 種分發模式 | PARTIAL（FrameworkSelector 全歸 CHAT） | PARTIAL（OrchestrationPanel 空閒）| ❌ |
| ⑤ 任務分發 | MAF/Claude/Swarm | PARTIAL（連接但不觸發） | PARTIAL（TaskProgressCard 就緒）| ❌ |
| ⑥ MCP 工具調用 | 8 個工具 | REGISTERED（未被 pipeline 調用） | PARTIAL（ToolCallTracker 就緒）| ❌ |
| ⑦ SSE 串流 | AG-UI 即時事件 | NOT_CONNECTED | NOT_INTEGRATED（用 typewriter）| ❌ |
| ⑧ 結果整合 | 多 Worker 結果合併 | PARTIAL | INTEGRATED（MessageList）| ⚠️ |
| ⑨ Session Resume | 恢復 + Checkpoint | PARTIAL（對話恢復、無 pipeline 狀態）| PARTIAL | ⚠️ |
| ⑩ 記憶 + 知識 | mem0 + RAG | CONNECTED（mem0）/ REGISTERED（RAG）| INTEGRATED（MemoryHint）| ⚠️ |

## 架構方案

### 方案 A（選用）：Orchestrator SSE 端點

新增 `POST /orchestrator/chat/stream` SSE 端點，mediator pipeline 每個步驟發送事件：

```
PIPELINE_START → ROUTING_COMPLETE → APPROVAL_REQUIRED → AGENT_THINKING →
TOOL_CALL_START → TOOL_CALL_END → TEXT_DELTA → TASK_DISPATCHED →
SWARM_WORKER_START → SWARM_PROGRESS → PIPELINE_COMPLETE
```

前端用 `EventSource` 或 `ReadableStream` 接收，即時更新 UI。

### 方案 B（備選）：AG-UI 事件橋接

利用現有 AG-UI SSE 基礎設施（`MediatorEventBridge`），將 mediator 事件映射到 AG-UI 協議事件。

## Sprint 規劃

| Sprint | 名稱 | Story Points | 重點 |
|--------|------|-------------|------|
| [Sprint 144](./sprint-144-plan.md) | FrameworkSelector 智能分發 + 任務創建 | ~10 | 讓複雜任務走 WORKFLOW/SWARM mode |
| [Sprint 145](./sprint-145-plan.md) | Orchestrator SSE 串流端點 | ~12 | 後端 SSE + 前端接收即時事件 |
| [Sprint 146](./sprint-146-plan.md) | Swarm UI 整合 + HITL 審批 | ~10 | AgentSwarmPanel 在 Chat + 審批流程 |
| [Sprint 147](./sprint-147-plan.md) | RAG Pipeline + Checkpoint + QA | ~8 | 知識檢索 + 狀態持久化 + 完整驗證 |

**總計**: ~40 Story Points (4 Sprints)

## Sprint 144: FrameworkSelector + Function Calling + Memory 修復

### 目標
修復 3 個 Critical Blockers：FrameworkSelector 空分類器、AgentHandler 無 Function Calling、Memory client 未接入。

### User Stories

**S144-1: FrameworkSelector 分類器註冊 (4 SP)**
- 在 Bootstrap 中為 FrameworkSelector 註冊 LLM-based classifier
- 利用三層路由的 RoutingDecision 來判斷模式（而非只靠 FrameworkSelector 獨立判斷）
- 關鍵字 + RoutingDecision 組合規則：
  - intent=query/greeting + low risk → CHAT_MODE
  - intent=request/change + 多步驟 → WORKFLOW_MODE
  - intent=incident + 多系統 → SWARM_MODE
- 驗證：不同類型輸入能正確分派到對應 mode

**S144-2: AgentHandler Function Calling (4 SP)**
- 將 `generate()` 替換為 Azure OpenAI function calling API
- 定義 tool schemas（create_task, dispatch_workflow, dispatch_swarm, assess_risk, search_memory, search_knowledge）
- LLM 判斷需要時自動調用工具 → 取得結果 → 繼續生成
- 工具調用結果附加到 PipelineResponse metadata

**S144-3: Memory Client + Bootstrap 修復 (2 SP)**
- Bootstrap 傳入 UnifiedMemoryManager 到 OrchestratorMemoryManager
- 確認 pipeline 內記憶讀寫真正生效（不是 no-op）
- InputGateway 註冊基本 source handlers

## Sprint 145: Orchestrator SSE 串流端點

### 目標
新增 SSE 串流端點，Pipeline 每個步驟即時推送事件到前端。

### User Stories

**S145-1: 後端 SSE 端點 (5 SP)**
- `POST /orchestrator/chat/stream` → SSE EventSource
- Mediator pipeline 每步發送事件（routing、approval、agent、execution）
- 事件格式對齊 AG-UI 協議

**S145-2: 前端 SSE 接收 (4 SP)**
- UnifiedChat 改用 SSE 端點（取代同步 POST）
- 即時更新 IntentStatusChip、ToolCallTracker、MessageList
- 移除 typewriter 假串流，改用真實 token streaming

**S145-3: AG-UI 事件橋接 (3 SP)**
- MediatorEventBridge 將 pipeline 事件映射到 AG-UI 事件
- 統一事件格式，支援前端重用

## Sprint 146: Swarm UI 整合 + HITL 審批

### 目標
在 Chat 中顯示 Swarm 多 Worker 執行視覺化，並啟用 HITL 審批流程。

### User Stories

**S146-1: AgentSwarmPanel 嵌入 Chat (4 SP)**
- Swarm 事件填充 swarmStore（透過 SSE）
- UnifiedChat 顯示 AgentSwarmPanel（右側/下方）
- WorkerCard 即時更新進度

**S146-2: HITL 審批流程 (3 SP)**
- 高風險操作暫停 Pipeline 等待審批
- SSE 推送 APPROVAL_REQUIRED 事件
- InlineApproval 在 Chat 中渲染，用戶批准/拒絕
- 批准後 Pipeline 繼續執行

**S146-3: DialogHandler + HITLController 修復 (3 SP)**
- 修復 GuidedDialogEngine 初始化（缺 router 參數）
- 修復 HITLController 初始化（缺 storage 參數）
- 對話引導流程在 Chat 中可視化

## Sprint 147: Session 持久化 + RAG + Checkpoint + QA

### 目標
Session/Checkpoint 從記憶體遷移到 PostgreSQL，連接 RAG 知識檢索，完整 E2E 驗證。

### User Stories

**S147-1: Session 持久化 (3 SP)**
- Mediator 用 ConversationStateStore（Redis/PostgreSQL）取代 Python dict
- SessionRecoveryManager 暴露為 API 端點
- Session Resume 恢復完整 pipeline 狀態

**S147-2: Checkpoint PostgreSQL Backend (2 SP)**
- 切換 CheckpointStorage 到 PostgresCheckpointStorage
- Pipeline 每步自動保存 Checkpoint
- 服務重啟後可恢復

**S147-3: RAG Pipeline 連接 (2 SP)**
- search_knowledge 工具在 function calling 中可調用
- 知識檢索結果注入 LLM prompt
- 前端顯示知識來源引用

**S147-4: E2E 完整驗證 (1 SP)**
- 6 個 Scenario (A-F) 全部在 Chat 中可演示
- 10 步流程全部有可視化對應
- Playwright 自動化測試

## 前置條件

- ✅ Phase 41 — Chat Pipeline 基礎接通（7 Handler）
- ✅ 記憶系統啟用（mem0 + Redis）
- ✅ 三層路由 + IntentStatusChip
- ✅ semantic-router 已安裝
- ✅ ExecutionHandler: claude=True, maf=True, swarm=True

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|---------|
| SSE 端點改動大 | 高 | 漸進式：先加 SSE 端點，保留 POST fallback |
| Swarm 實際執行複雜 | 中 | 先用模擬 Worker，後接真實 Agent |
| FrameworkSelector 分類不準 | 中 | 加 LLM fallback + 用戶可手動選模式 |
| HITL 暫停機制需改 mediator | 中 | 用 async event + callback pattern |

---

**Phase 42 前置**: Phase 41 (Chat Pipeline Integration)
**總 Story Points**: ~40 pts
**Sprint 範圍**: Sprint 144-147
**技術棧**: FastAPI SSE + React EventSource + Zustand + AG-UI Protocol
