# Sprint 146 Checklist: Swarm UI 整合 + HITL 審批

**Sprint**: 146 | **Phase**: 42 | **Story Points**: 10
**Plan**: [sprint-146-plan.md](./sprint-146-plan.md)

---

## S146-1: AgentSwarmPanel 嵌入 Chat (4 SP)

- [x] UnifiedChat 嵌入 AgentSwarmPanel（右側 360px）
- [x] pipelineMode === 'swarm' 或 showSwarmPanel 時顯示
- [x] SSE SWARM_WORKER_START -> swarmStore.setSwarmStatus + addWorker
- [x] SSE SWARM_PROGRESS -> swarmStore.updateWorkerProgress
- [x] AgentSwarmPanel 接收 swarmStatus props

## S146-2: HITL 審批流程 (3 SP)

- [x] Mediator: risk HIGH/CRITICAL -> APPROVAL_REQUIRED SSE 事件
- [x] asyncio.Event 暫停 Pipeline（120s timeout）
- [x] resolve_approval() 解鎖等待
- [x] POST /orchestrator/approval/{id} 端點
- [x] 前端 InlineApproval 卡片（批准/拒絕按鈕）
- [x] 審批後 Pipeline 繼續或取消

## S146-3: DialogHandler + HITLController 初始化修復 (3 SP)

- [x] GuidedDialogEngine: pass router=create_router_with_llm()
- [x] HITLController: use create_hitl_controller() or InMemoryApprovalStorage
- [x] Bootstrap 依賴完整注入

---

**Status**: Done
