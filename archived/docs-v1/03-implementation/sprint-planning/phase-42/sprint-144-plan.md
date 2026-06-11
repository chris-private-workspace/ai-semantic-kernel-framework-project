# Sprint 144: FrameworkSelector + Function Calling + Memory 修復

## Sprint 目標

1. FrameworkSelector 註冊智能分類器，利用 RoutingDecision 判斷分發模式（CHAT/WORKFLOW/SWARM）
2. AgentHandler 從 `generate()` 切換到 Azure OpenAI function calling API，讓 LLM 能實際調用工具
3. Bootstrap 修復 memory_client 傳入，確保 pipeline 內記憶讀寫非 no-op
4. InputGateway 註冊基本 source handlers

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 42 — E2E Pipeline Deep Integration |
| **Sprint** | 144 |
| **Story Points** | 10 點 |
| **狀態** | 📋 計劃中 |

## User Stories

### S144-1: FrameworkSelector 分類器註冊 (4 SP)

**作為** Orchestrator Pipeline 的使用者
**我希望** 系統能根據意圖和風險自動判斷使用 CHAT_MODE、WORKFLOW_MODE 或 SWARM_MODE
**以便** 複雜任務不會全部歸入 CHAT_MODE，而是走正確的分發路徑

**技術規格**:

**改動 1: `backend/src/integrations/hybrid/intent/router.py` — FrameworkSelector 分類器**
- 為 FrameworkSelector 註冊分類器（取代空的 `classifiers=[]`）
- 實作 `RoutingDecisionClassifier`，基於三層路由的 RoutingDecision 來判斷模式
- 分類規則：
  - `intent=query/greeting` + `risk_level=LOW` → `CHAT_MODE`
  - `intent=request/change` + 多步驟指標 → `WORKFLOW_MODE`
  - `intent=incident` + 多系統指標 → `SWARM_MODE`
  - `intent=analysis` + 單系統 → `AGENT_MODE`
- 加入 LLM fallback：當 confidence < 0.6 時，用 LLM 二次判斷

**改動 2: `backend/src/integrations/orchestration/bootstrap.py` — 註冊分類器**
- Bootstrap 初始化 FrameworkSelector 時傳入 `RoutingDecisionClassifier`
- 確保 FrameworkSelector 在 pipeline 中被正確調用

**改動 3: 單元測試**
- 測試不同 intent + risk 組合的分類結果
- 測試 LLM fallback 觸發條件
- 測試邊界情況（unknown intent、missing fields）

### S144-2: AgentHandler Function Calling (4 SP)

**作為** Pipeline 中的 AgentHandler
**我希望** 使用 Azure OpenAI function calling API 讓 LLM 判斷何時調用工具
**以便** 工具調用、任務分發、Swarm 啟動能由 LLM 智能觸發，而非 short-circuit

**技術規格**:

**改動 1: `backend/src/integrations/orchestration/handlers/agent_handler.py` — Function Calling**
- 將 `generate()` 替換為 Azure OpenAI Chat Completions with `tools` 參數
- 定義 tool schemas：
  ```python
  tools = [
      {"type": "function", "function": {"name": "create_task", "description": "建立新任務", "parameters": {...}}},
      {"type": "function", "function": {"name": "dispatch_workflow", "description": "分發工作流程", "parameters": {...}}},
      {"type": "function", "function": {"name": "dispatch_swarm", "description": "啟動 Swarm 多 Agent 協作", "parameters": {...}}},
      {"type": "function", "function": {"name": "assess_risk", "description": "評估操作風險等級", "parameters": {...}}},
      {"type": "function", "function": {"name": "search_memory", "description": "搜尋記憶系統", "parameters": {...}}},
      {"type": "function", "function": {"name": "search_knowledge", "description": "搜尋知識庫 (RAG)", "parameters": {...}}},
  ]
  ```
- 實作 tool call 處理迴圈：
  1. 發送 messages + tools 到 Azure OpenAI
  2. 如果回應含 `tool_calls`，執行對應工具
  3. 將工具結果附加到 messages，再次呼叫 LLM
  4. 重複直到 LLM 回傳純文字回應（或達到 max_iterations=5）
- 工具調用結果附加到 `PipelineResponse.metadata.tool_calls`

**改動 2: `backend/src/integrations/orchestration/handlers/tool_registry.py` — 工具註冊表**
- 新增 `ToolRegistry` class，管理可用工具及其執行函數
- 每個工具對應一個 `async def execute(params) -> dict` 方法
- Bootstrap 時註冊所有工具到 registry

**改動 3: 單元測試**
- Mock Azure OpenAI response with tool_calls
- 測試 tool call 迴圈（單次 / 多次 / max_iterations）
- 測試工具執行失敗的錯誤處理

### S144-3: Memory Client + Bootstrap 修復 (2 SP)

**作為** 系統管理者
**我希望** Pipeline 內的記憶讀寫真正生效
**以便** 對話上下文能被持久化，跨 session 記憶可用

**技術規格**:

**改動 1: `backend/src/integrations/orchestration/bootstrap.py` (line ~209) — 傳入 memory_client**
- 修改 Bootstrap 中 OrchestratorMemoryManager 初始化
- 傳入 `UnifiedMemoryManager` instance（從 mem0 或 Redis 取得）
- 確認 `memory_client` 不再為 `None`

**改動 2: `backend/src/integrations/orchestration/handlers/input_gateway.py` — Source Handlers**
- 為 InputGateway 註冊基本 source handlers：
  - `user` source handler（處理用戶直接輸入）
  - `api` source handler（處理 API 呼叫）
  - `system` source handler（處理系統事件）
- 每個 handler 負責標準化輸入格式

**改動 3: 驗證測試**
- 測試 memory_client 在 pipeline 中非 None
- 測試記憶寫入後可讀取
- 測試 InputGateway 各 source handler 路由正確

## 驗收標準

- [ ] FrameworkSelector 對 query/greeting 輸入分派 CHAT_MODE
- [ ] FrameworkSelector 對多步驟 request 分派 WORKFLOW_MODE
- [ ] FrameworkSelector 對多系統 incident 分派 SWARM_MODE
- [ ] AgentHandler 使用 function calling API（非 generate()）
- [ ] LLM 能觸發 create_task / dispatch_workflow / dispatch_swarm 工具
- [ ] 工具調用結果出現在 PipelineResponse.metadata
- [ ] OrchestratorMemoryManager.memory_client 非 None
- [ ] Pipeline 內記憶讀寫真正生效（可驗證）
- [ ] InputGateway 能處理 user / api / system 三種 source
- [ ] 所有新增程式碼含 type hints 和 docstrings
- [ ] 單元測試覆蓋率 ≥ 80%
- [ ] `black . && isort . && flake8 .` 通過

## 相關連結

- [Phase 42 計劃](./README.md)
- [Sprint 145 Plan](./sprint-145-plan.md)

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 10
