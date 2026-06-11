# Sprint 155 Checklist - Step 6 LLM 選路 + 分派層

## Reference
- Plan: [sprint-155-plan.md](sprint-155-plan.md)
- Phase: 45 (Orchestration Core)

---

## LLMRouteStep (Step 6)

- [ ] `pipeline/steps/step6_llm_route.py`
  - [ ] 建構完整上下文 prompt（task + memory + knowledge + intent + risk）
  - [ ] select_route() tool 定義（route, reasoning 參數）
  - [ ] OrchestratorAgent 呼叫 LLM
  - [ ] 解析回應提取 selected_route
  - [ ] 寫入 context.selected_route
  - [ ] 記錄 TranscriptEntry

## Dispatch 模組結構

- [ ] `dispatch/__init__.py`
- [ ] `dispatch/models.py` — DispatchRequest, DispatchResult, ExecutorConfig
- [ ] `dispatch/executors/__init__.py`
- [ ] `dispatch/executors/base.py` — BaseExecutor 抽象基類
  - [ ] `name` 屬性
  - [ ] `async execute(request: DispatchRequest) -> DispatchResult`

## DirectAnswerExecutor

- [ ] `dispatch/executors/direct_answer.py`
  - [ ] LLM 串流回應
  - [ ] 發射 TEXT_DELTA SSE 事件
  - [ ] 收集完整回應到 DispatchResult

## SubagentExecutor

- [ ] `dispatch/executors/subagent.py`
  - [ ] 根據任務建構並行 agent 配置
  - [ ] 啟動 MAF agents 並行執行
  - [ ] 每個 agent 寫入 transcript sidechain
  - [ ] 發射 AGENT_THINKING / AGENT_COMPLETE SSE 事件
  - [ ] 聚合結果到 DispatchResult

## TeamExecutor

- [ ] `dispatch/executors/team.py`
  - [ ] 從 PoC team 邏輯提取
  - [ ] TeamLead 分工 → agents 協作
  - [ ] 發射 agent SSE 事件
  - [ ] Synthesis 結果到 DispatchResult

## Stub Executors

- [ ] `dispatch/executors/swarm.py` — SwarmExecutor stub
- [ ] `dispatch/executors/workflow.py` — WorkflowExecutor stub

## DispatchService

- [ ] `dispatch/service.py`
  - [ ] 根據 selected_route 選擇 executor
  - [ ] 呼叫 executor.execute()
  - [ ] 寫入 context.dispatch_result

## 驗證

- [ ] Pipeline 端到端通過 Steps 1-7（使用 direct_answer 路線）
- [ ] SubagentExecutor 能啟動並行 agents
- [ ] TeamExecutor 能啟動協作 agents
- [ ] Swarm/Workflow stubs 返回 NotImplemented 訊息
