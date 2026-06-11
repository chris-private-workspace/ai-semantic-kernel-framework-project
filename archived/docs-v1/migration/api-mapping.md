# API Mapping: Phase 2 to Agent Framework

## Overview

本文檔詳細說明 Phase 2 自定義實現與 Agent Framework 官方 API 的對應關係。

---

## 1. 並行執行 (Concurrent Execution)

### Phase 2: ConcurrentExecutor
```python
# 位置: backend/src/domain/workflows/executors/concurrent.py

class ConcurrentExecutor:
    def __init__(
        self,
        mode: ConcurrentMode,  # ALL, ANY, MAJORITY, FIRST_SUCCESS
        tasks: List[ConcurrentTask],
        timeout_seconds: float = 300,
    ): ...

    async def execute(self, input_data: Any) -> ConcurrentResult: ...
```

### Agent Framework: ConcurrentBuilder
```python
# Agent Framework API

workflow = (
    ConcurrentBuilder()
    .add_executor(exec1)
    .add_executor(exec2)
    .add_executor(exec3)
    .with_completion_condition(CompleteAll())  # or CompleteAny(), etc.
    .build()
)

result = await workflow.run(input_data)
```

### 映射對應

| Phase 2 | Agent Framework | 說明 |
|---------|-----------------|------|
| `ConcurrentMode.ALL` | `CompleteAll()` | 等待所有任務完成 |
| `ConcurrentMode.ANY` | `CompleteAny()` | 任一任務完成即返回 |
| `ConcurrentMode.MAJORITY` | 自定義 condition | 需要自定義完成條件 |
| `ConcurrentMode.FIRST_SUCCESS` | 自定義 condition | 需要自定義完成條件 |
| `ConcurrentTask` | `Executor` | 任務封裝為執行器 |
| `timeout_seconds` | Builder 配置 | 超時配置方式不同 |

### 代碼範例

```python
# Phase 2 方式
from domain.workflows.executors.concurrent import (
    ConcurrentExecutor,
    ConcurrentMode,
    ConcurrentTask,
)

executor = ConcurrentExecutor(
    mode=ConcurrentMode.ALL,
    tasks=[
        ConcurrentTask(id="t1", handler=task1_handler),
        ConcurrentTask(id="t2", handler=task2_handler),
    ],
)
result = await executor.execute(input_data)

# Phase 3 方式 (使用適配器)
from src.integrations.agent_framework.builders import ConcurrentBuilderAdapter

adapter = ConcurrentBuilderAdapter(
    id="parallel-workflow",
    executors=[executor1, executor2],
    completion_condition="all",  # 或 "any", 自定義函數
)
result = await adapter.run(input_data)
```

---

## 2. Agent Handoff

### Phase 2: HandoffController
```python
# 位置: backend/src/domain/orchestration/handoff/controller.py

class HandoffController:
    def __init__(
        self,
        policy: HandoffPolicy,  # IMMEDIATE, GRACEFUL, CONDITIONAL
        trigger: HandoffTrigger,
    ): ...

    async def execute_handoff(
        self,
        source_agent: str,
        target_agent: str,
        context: HandoffContext,
    ) -> HandoffResult: ...
```

### Agent Framework: HandoffBuilder
```python
# Agent Framework API

workflow = (
    HandoffBuilder()
    .add_agent(agent1)
    .add_agent(agent2)
    .with_handoff_policy(...)
    .build()
)

# 處理 HandoffUserInputRequest
```

### 映射對應

| Phase 2 | Agent Framework | 說明 |
|---------|-----------------|------|
| `HandoffPolicy` | Builder 配置 | 交接策略 |
| `HandoffTrigger` | Event/Condition | 觸發條件 |
| `HandoffContext` | `WorkflowContext` | 上下文傳遞 |
| `execute_handoff()` | Workflow 自動處理 | 執行方式不同 |

---

## 3. 群組聊天 (GroupChat)

### Phase 2: GroupChatManager
```python
# 位置: backend/src/domain/orchestration/groupchat/manager.py

class GroupChatManager:
    def __init__(
        self,
        participants: List[ChatParticipant],
        selection_method: SpeakerSelectionMethod,
        max_rounds: int = 10,
    ): ...

    async def run_chat(
        self,
        initial_message: str,
    ) -> GroupChatResult: ...
```

### Agent Framework: GroupChatBuilder
```python
# Agent Framework API

workflow = (
    GroupChatBuilder()
    .participants(
        agent1=agent1,
        agent2=agent2,
        agent3=agent3,
    )
    .set_manager(manager_agent)
    .build()
)

# 處理 ManagerSelectionRequest/Response
```

### 映射對應

| Phase 2 | Agent Framework | 說明 |
|---------|-----------------|------|
| `ChatParticipant` | Agent/Executor | 參與者 |
| `SpeakerSelectionMethod.AUTO` | Manager Agent | 自動選擇 |
| `SpeakerSelectionMethod.ROUND_ROBIN` | 自定義 Manager | 輪詢選擇 |
| `GroupMessage` | `Message` | 消息格式 |
| `GroupChatState` | `WorkflowContext` | 狀態管理 |

---

## 4. 動態規劃 (Dynamic Planning)

### Phase 2: DynamicPlanner
```python
# 位置: backend/src/domain/orchestration/planning/dynamic_planner.py

class DynamicPlanner:
    def __init__(
        self,
        agents: List[PlanningAgent],
        max_rounds: int = 20,
        enable_human_intervention: bool = False,
    ): ...

    async def plan_and_execute(
        self,
        task: str,
    ) -> PlanningResult: ...
```

### Agent Framework: MagenticBuilder
```python
# Agent Framework API

workflow = (
    MagenticBuilder()
    .participants(
        coder=coder_agent,
        critic=critic_agent,
        orchestrator=orchestrator_agent,
    )
    .with_manager(StandardMagenticManager(...))
    .with_plan_review(enable=True)
    .build()
)

# Task Ledger 和 Progress Ledger 自動管理
```

### 映射對應

| Phase 2 | Agent Framework | 說明 |
|---------|-----------------|------|
| `PlanningAgent` | Agent/Executor | 規劃參與者 |
| 自定義 Task Ledger | `TaskLedger` | 任務帳本 |
| 自定義 Progress Ledger | `ProgressLedger` | 進度帳本 |
| `enable_human_intervention` | `with_plan_review()` | 人機互動 |
| `max_rounds` | Manager 配置 | 最大輪數 |

---

## 5. 嵌套工作流 (Nested Workflows)

### Phase 2: NestedWorkflowManager
```python
# 位置: backend/src/domain/workflows/nested/manager.py

class NestedWorkflowManager:
    def __init__(
        self,
        workflow_type: NestedWorkflowType,
    ): ...

    async def execute_nested(
        self,
        parent_context: WorkflowContext,
        sub_workflow: SubWorkflowReference,
    ) -> NestedResult: ...
```

### Agent Framework: WorkflowExecutor
```python
# Agent Framework API

# 將子工作流包裝為 WorkflowExecutor
sub_workflow_executor = WorkflowExecutor(
    workflow=sub_workflow,
    id="sub-workflow-1",
)

# 在父工作流中使用
parent_workflow = (
    WorkflowBuilder()
    .add_executor(sub_workflow_executor)
    ...
    .build()
)

# 處理 SubWorkflowRequestMessage/ResponseMessage
```

### 映射對應

| Phase 2 | Agent Framework | 說明 |
|---------|-----------------|------|
| `NestedWorkflowType` | Builder 類型 | 工作流類型 |
| `SubWorkflowReference` | `WorkflowExecutor` | 子工作流引用 |
| 手動上下文傳遞 | 自動消息傳遞 | 上下文管理 |
| `execute_nested()` | `workflow.run()` | 執行方式 |

---

## 6. 檢查點 (Checkpoint)

### Phase 2: 自定義實現
```python
# 分散在各模組中的檢查點邏輯
```

### Agent Framework: CheckpointStorage
```python
# Agent Framework API

storage = FileCheckpointStorage("./checkpoints")
# 或
storage = InMemoryCheckpointStorage()
# 或使用我們的適配器
storage = PostgresCheckpointStorage(session_factory)

workflow = (
    WorkflowBuilder()
    ...
    .with_checkpointing(storage)
    .build()
)
```

### 映射對應

| Phase 2 | Agent Framework | 說明 |
|---------|-----------------|------|
| 自定義存儲 | `CheckpointStorage` Protocol | 存儲介面 |
| 手動保存/載入 | 自動檢查點 | 管理方式 |
| - | `WorkflowCheckpoint` | 檢查點數據 |

---

## 適配器對照表

| 適配器類 | 對應 Agent Framework API | Sprint |
|----------|--------------------------|--------|
| `WorkflowAdapter` | `WorkflowBuilder` | 13 |
| `CheckpointStorageAdapter` | `CheckpointStorage` | 13 |
| `ConcurrentBuilderAdapter` | `ConcurrentBuilder` | 14 |
| `HandoffBuilderAdapter` | `HandoffBuilder` | 15 |
| `GroupChatBuilderAdapter` | `GroupChatBuilder` | 16 |
| `MagenticBuilderAdapter` | `MagenticBuilder` | 17 |
| `WorkflowExecutorAdapter` | `WorkflowExecutor` | 18 |

---

## 相關文檔

- [Phase 3 遷移指南](./phase3-migration-guide.md)
- [Agent Framework 文檔](../../reference/agent-framework/)
- [Phase 2 架構審查](../../claudedocs/PHASE2-ARCHITECTURE-REVIEW.md)
