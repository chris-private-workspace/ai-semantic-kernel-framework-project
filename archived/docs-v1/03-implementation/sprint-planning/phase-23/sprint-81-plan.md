# Sprint 81: Claude 主導的多 Agent 協調

## Sprint Info

| Field | Value |
|-------|-------|
| **Sprint Number** | 81 |
| **Phase** | 23 - 多 Agent 協調與主動巡檢 |
| **Duration** | 5-7 days |
| **Story Points** | 26 pts |
| **Status** | 計劃中 |
| **Priority** | 🟡 P1 中優先 |

---

## Sprint Goal

實現 Claude 主導的多 Agent 協調能力，完善 A2A 通信協議，並深度融合 Claude 與 MAF。

---

## Prerequisites

- Phase 22 完成（Claude 自主能力 + mem0）✅
- MAF Adapters（Phase 3-6）✅

---

## User Stories

### S81-1: Claude 主導的多 Agent 協調 (10 pts)

**Description**: 讓 Claude 能夠作為 Orchestrator 角色，動態選擇和協調多個 Agent 完成複雜任務。

**Acceptance Criteria**:
- [ ] Claude 能分析任務並選擇合適 Agent
- [ ] 支援動態任務分配
- [ ] 跨 Agent 上下文傳遞
- [ ] 支援並行和串行協調
- [ ] 協調結果彙總

**Files to Create**:
- `backend/src/integrations/claude_sdk/orchestrator/__init__.py`
- `backend/src/integrations/claude_sdk/orchestrator/coordinator.py` (~200 行)
- `backend/src/integrations/claude_sdk/orchestrator/task_allocator.py` (~150 行)
- `backend/src/integrations/claude_sdk/orchestrator/context_manager.py` (~100 行)

**Technical Design**:
```python
class ClaudeCoordinator:
    async def coordinate_agents(
        self,
        task: ComplexTask,
        available_agents: List[Agent]
    ) -> CoordinationResult:
        """Claude 分析任務並協調多個 Agent"""
        # 1. 分析任務需求
        analysis = await self.analyze_task(task)

        # 2. 選擇合適 Agent
        selected = await self.select_agents(analysis, available_agents)

        # 3. 分配子任務
        subtasks = await self.allocate_tasks(analysis, selected)

        # 4. 執行協調
        if analysis.can_parallel:
            results = await self.parallel_execute(subtasks)
        else:
            results = await self.sequential_execute(subtasks)

        # 5. 彙總結果
        return await self.aggregate_results(results)
```

---

### S81-2: A2A 通信協議完善 (8 pts)

**Description**: 完善 Agent to Agent 通信協議，實現 Agent 發現、能力宣告和消息路由。

**Acceptance Criteria**:
- [ ] 標準化 A2A 消息格式
- [ ] Agent 發現服務
- [ ] 能力宣告和查詢
- [ ] 消息路由和追蹤
- [ ] 超時和重試處理

**Files to Create**:
- `backend/src/integrations/a2a/__init__.py`
- `backend/src/integrations/a2a/protocol.py` (~150 行)
- `backend/src/integrations/a2a/discovery.py` (~150 行)
- `backend/src/integrations/a2a/router.py` (~100 行)
- `backend/src/api/v1/a2a/routes.py` (~100 行)

**A2A Message Protocol**:
```python
class A2AMessage(BaseModel):
    message_id: str
    from_agent: str
    to_agent: str
    type: MessageType  # TASK_REQUEST, TASK_RESPONSE, STATUS_UPDATE, etc.
    payload: Dict[str, Any]
    context: Optional[Dict[str, Any]]
    timestamp: datetime
    correlation_id: Optional[str]  # 用於追蹤對話鏈
```

**API Endpoints**:
```
POST   /api/v1/a2a/message             # 發送 A2A 消息
GET    /api/v1/a2a/agents              # 獲取所有 Agent
POST   /api/v1/a2a/agents/register     # 註冊 Agent
POST   /api/v1/a2a/agents/discover     # 發現合適 Agent
```

---

### S81-3: Claude + MAF 深度融合 (8 pts)

**Description**: 在 MAF Workflow 中引入 Claude 決策點，支援動態 Workflow 修改。

**Acceptance Criteria**:
- [ ] MAF Workflow 中可插入 Claude 決策
- [ ] 支援動態修改 Workflow 路徑
- [ ] 統一調度介面
- [ ] 決策結果影響 Workflow 執行

**Files to Modify**:
- `backend/src/integrations/agent_framework/builders/sequential_builder.py` (修改 ~50 行)
- `backend/src/integrations/hybrid/orchestrator.py` (修改 ~100 行)

**Technical Design**:
```python
class HybridOrchestrator:
    async def execute_with_claude_decisions(
        self,
        workflow: Workflow,
        context: ExecutionContext
    ) -> ExecutionResult:
        """執行帶有 Claude 決策點的 Workflow"""
        for step in workflow.steps:
            if step.is_decision_point:
                # Claude 決定下一步
                decision = await self.claude.decide(step, context)
                if decision.modify_workflow:
                    workflow = await self.modify_workflow(workflow, decision)

            result = await self.execute_step(step, context)
            context.update(result)

        return ExecutionResult(context)
```

---

## Definition of Done

- [ ] 所有 Stories 完成
- [ ] Claude 能協調 3+ Agent 完成任務
- [ ] A2A 消息正確路由
- [ ] Agent 發現和能力查詢正常
- [ ] MAF + Claude 融合測試通過
- [ ] 單元測試覆蓋率 > 80%

---

## Success Metrics

| Metric | Target |
|--------|--------|
| 多 Agent 協調成功率 | > 90% |
| A2A 消息傳遞延遲 | < 500ms |
| Agent 發現準確率 | > 95% |

---

**Created**: 2026-01-12
**Story Points**: 26 pts
