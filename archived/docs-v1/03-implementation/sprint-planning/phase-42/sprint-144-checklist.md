# Sprint 144 Checklist: FrameworkSelector + Function Calling + Memory + Mode Selector

**Sprint**: 144 | **Phase**: 42 | **Story Points**: 10
**Plan**: [sprint-144-plan.md](./sprint-144-plan.md)

---

## S144-1: FrameworkSelector 分類器註冊 (4 SP)

### RoutingDecisionClassifier 實作
- [x] `hybrid/intent/classifiers/routing_decision.py` — 新增 `RoutingDecisionClassifier` class
- [x] 分類規則：intent=query/greeting + low risk -> CHAT_MODE
- [x] 分類規則：intent=request/change -> WORKFLOW_MODE
- [x] 分類規則：intent=incident + CRITICAL -> SWARM_MODE
- [x] 分類規則：intent=incident + HIGH -> WORKFLOW_MODE

### Bootstrap 註冊
- [x] `bootstrap.py` — FrameworkSelector 初始化傳入 RuleBasedClassifier + RoutingDecisionClassifier
- [x] FrameworkSelector 在 pipeline 中被正確調用（2 classifiers, threshold=0.6）

### FrameworkSelector 改動
- [x] `router.py` — select_framework() 注入 routing_decision 到 RoutingDecisionClassifier
- [x] `router.py` — _determine_framework() 支援 SWARM_MODE -> MAF
- [x] `router.py` — fallback: 直接從 routing_decision 產生分類結果

## S144-2: AgentHandler Function Calling (4 SP)

### Function Calling 替換
- [x] `agent_handler.py` — generate() 替換為 Azure OpenAI function calling API
- [x] 定義 8 個 tool schemas（via OrchestratorToolRegistry.get_openai_tool_schemas()）
- [x] 實作 tool call 處理迴圈（最多 5 次迭代）
- [x] 工具調用結果附加到 HandlerResult.data.tool_calls

### ToolRegistry OpenAI Schema
- [x] `tools.py` — 新增 get_openai_tool_schemas() 方法
- [x] `tools.py` — 新增 _param_type_to_json_schema() 轉換器
- [x] 8 個 built-in 工具自動轉換為 OpenAI function calling schema

## S144-3: Memory Client + Bootstrap 修復 (2 SP)

- [x] `bootstrap.py` — 建立 UnifiedMemoryManager 並傳入 OrchestratorMemoryManager
- [x] `bootstrap.py` — 使用 create_input_gateway() 工廠函數註冊 source handlers

## S144-bonus: Mode Selector + Pipeline UX

- [x] `PipelineRequest` — 新增 mode 欄位（user-selected mode）
- [x] `PipelineResponse` — 新增 execution_mode, suggested_mode, tool_calls
- [x] `routes.py` — map mode -> force_mode 傳入 OrchestratorRequest
- [x] `RoutingHandler` — 三層路由永遠執行（安全守門），force_mode 只控制模式
- [x] `RoutingHandler` — 生成 suggested_mode 供前端建議橫幅
- [x] `mediator.py` — 空回應 fallback 到 AgentHandler 內容
- [x] `mediator.py` — metadata 包含 execution_mode, suggested_mode
- [x] 前端 Mode Selector UI（Chat/Workflow/Swarm 三按鈕）
- [x] 前端 suggested_mode 黃色建議橫幅
- [x] 前端 isPipelineSending loading 狀態
- [x] 前端 orchestrator API 類型更新

---

**Status**: Done
