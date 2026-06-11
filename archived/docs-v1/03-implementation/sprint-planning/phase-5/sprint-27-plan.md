# Sprint 27: 執行引擎遷移

**Sprint 目標**: 將 WorkflowExecutionService 遷移到 SequentialOrchestration
**週期**: 2 週
**Story Points**: 38 點
**Phase 5 功能**: P5-F2 (執行引擎遷移)

---

## Sprint 概覽

### 目標
1. 創建 SequentialOrchestrationAdapter (順序執行適配器)
2. 創建 WorkflowStatusEventAdapter (狀態事件流適配器)
3. 重構 ExecutionStateMachine (整合官方事件系統)
4. 遷移 ExecutionService 使用新適配器
5. 完整整合測試

### 成功標準
- [ ] 可以使用官方 `SequentialOrchestration` 執行順序工作流
- [ ] 可以接收和處理 `WorkflowStatusEvent` 事件流
- [ ] ExecutionStateMachine 整合官方事件系統
- [ ] 現有執行功能無退化

---

## 架構設計

### 目前實現 (需遷移)

```python
# domain/workflows/service.py - 自行實現的執行邏輯
class WorkflowExecutionService:
    async def execute(self, workflow_id: UUID, input_data: Dict) -> ExecutionResult:
        workflow = await self._get_workflow(workflow_id)
        execution = await self._create_execution(workflow_id)

        for node in self._topological_sort(workflow.nodes, workflow.edges):
            result = await self._execute_node(node, execution)
            if not result.success:
                return self._handle_failure(execution, result)

        return ExecutionResult(success=True, execution_id=execution.id)

    async def _execute_sequential(self, nodes: List[WorkflowNode]) -> ExecutionResult:
        """順序執行節點 - 應該使用 SequentialOrchestration"""
        for node in nodes:
            result = await self._execute_node(node)
        return result
```

### 目標架構 (使用官方 API)

```python
# integrations/agent_framework/core/execution.py
from agent_framework.workflows.orchestrations import SequentialOrchestration
from agent_framework import WorkflowStatusEvent

class SequentialOrchestrationAdapter:
    """
    順序編排適配器

    使用官方 SequentialOrchestration 執行順序工作流
    """

    def __init__(self, agents: List[ChatAgent], name: str = "sequential-workflow"):
        self._orchestration = SequentialOrchestration(
            agents=agents,
            name=name
        )

    async def run(self, input_data: Any) -> WorkflowRunResult:
        """執行順序工作流"""
        return await self._orchestration.run(input_data)

    async def run_stream(self, input_data: Any):
        """流式執行，接收狀態事件"""
        async for event in self._orchestration.run_stream(input_data):
            yield event


class WorkflowStatusEventAdapter:
    """
    工作流狀態事件適配器

    將官方 WorkflowStatusEvent 轉換為內部事件格式
    """

    def __init__(self, event_handler: Callable):
        self._handler = event_handler

    async def handle(self, event: WorkflowStatusEvent) -> None:
        """處理狀態事件"""
        internal_event = self._convert_to_internal(event)
        await self._handler(internal_event)

    def _convert_to_internal(self, event: WorkflowStatusEvent) -> InternalEvent:
        """轉換為內部事件格式"""
        return InternalEvent(
            type=event.event_type,
            execution_id=event.workflow_id,
            node_id=event.executor_id,
            status=self._map_status(event.status),
            data=event.data,
            timestamp=event.timestamp
        )
```

---

## User Stories

### S27-1: SequentialOrchestrationAdapter (10 點)

**描述**: 創建基於官方 `SequentialOrchestration` 的順序執行適配器。

**驗收標準**:
- [ ] 實現 `SequentialOrchestrationAdapter` 類
- [ ] 可從 WorkflowNodeExecutor 列表創建 agents
- [ ] 支持同步執行 `run()`
- [ ] 支持流式執行 `run_stream()`
- [ ] 結果格式符合預期
- [ ] 單元測試覆蓋

**檔案**:
- `backend/src/integrations/agent_framework/core/execution.py`
- `backend/tests/unit/test_sequential_orchestration_adapter.py`

**技術任務**:

```python
# backend/src/integrations/agent_framework/core/execution.py
"""
執行引擎適配器 - 基於官方 Agent Framework Orchestrations

將現有的工作流執行邏輯適配到官方編排 API
"""

from typing import Any, Dict, List, Optional, AsyncIterator
from uuid import UUID

from agent_framework import ChatAgent
from agent_framework.workflows.orchestrations import SequentialOrchestration
from agent_framework.workflows import WorkflowRunResult

from src.integrations.agent_framework.core.executor import WorkflowNodeExecutor


class SequentialOrchestrationAdapter:
    """
    順序編排適配器

    使用官方 SequentialOrchestration 執行順序工作流。
    將多個 WorkflowNodeExecutor 包裝為順序執行的編排。
    """

    def __init__(
        self,
        executors: List[WorkflowNodeExecutor],
        name: str = "sequential-workflow"
    ):
        """
        初始化順序編排適配器

        Args:
            executors: 節點執行器列表 (按執行順序排列)
            name: 編排名稱
        """
        self._executors = executors
        self._name = name
        self._orchestration = self._build_orchestration()

    def _build_orchestration(self) -> SequentialOrchestration:
        """構建官方 SequentialOrchestration"""
        # 將 Executor 轉換為 ChatAgent 介面
        agents = [self._executor_to_agent(exe) for exe in self._executors]

        return SequentialOrchestration(
            agents=agents,
            name=self._name
        )

    def _executor_to_agent(self, executor: WorkflowNodeExecutor) -> ChatAgent:
        """將 Executor 包裝為 ChatAgent"""
        # 使用 workflow.as_agent() 模式
        return executor.as_agent(name=executor.id)

    async def run(self, input_data: Any) -> WorkflowRunResult:
        """
        執行順序工作流

        Args:
            input_data: 輸入數據

        Returns:
            WorkflowRunResult: 執行結果
        """
        return await self._orchestration.run(input_data)

    async def run_stream(self, input_data: Any) -> AsyncIterator:
        """
        流式執行順序工作流

        Yields:
            WorkflowStatusEvent: 狀態事件
        """
        async for event in self._orchestration.run_stream(input_data):
            yield event


class ExecutionAdapter:
    """
    工作流執行適配器

    替代原有的 WorkflowExecutionService，使用官方 API 執行工作流。
    """

    def __init__(
        self,
        workflow_adapter: 'WorkflowDefinitionAdapter',
        checkpoint_store: Optional['CheckpointStorage'] = None
    ):
        self._workflow_adapter = workflow_adapter
        self._checkpoint_store = checkpoint_store
        self._event_handlers: List[callable] = []

    def add_event_handler(self, handler: callable) -> None:
        """添加事件處理器"""
        self._event_handlers.append(handler)

    async def execute(
        self,
        execution_id: UUID,
        input_data: Dict[str, Any]
    ) -> 'ExecutionResult':
        """
        執行工作流

        Args:
            execution_id: 執行 ID
            input_data: 輸入數據

        Returns:
            ExecutionResult: 執行結果
        """
        try:
            # 構建工作流
            workflow = self._workflow_adapter.build()

            # 配置檢查點 (如果需要)
            if self._checkpoint_store:
                workflow = workflow.with_checkpointing(self._checkpoint_store)

            # 執行並處理事件
            result = None
            async for event in workflow.run_stream(input_data):
                await self._handle_event(execution_id, event)
                if event.is_final:
                    result = event.result

            return ExecutionResult(
                execution_id=execution_id,
                success=True,
                result=result
            )

        except Exception as e:
            return ExecutionResult(
                execution_id=execution_id,
                success=False,
                error=str(e)
            )

    async def _handle_event(self, execution_id: UUID, event) -> None:
        """處理工作流事件"""
        for handler in self._event_handlers:
            await handler(execution_id, event)
```

---

### S27-2: WorkflowStatusEventAdapter (8 點)

**描述**: 創建狀態事件流適配器，處理官方 `WorkflowStatusEvent`。

**驗收標準**:
- [ ] 實現 `WorkflowStatusEventAdapter` 類
- [ ] 可接收和處理所有事件類型
- [ ] 事件轉換正確
- [ ] 可註冊多個事件處理器
- [ ] 單元測試覆蓋

**檔案**:
- `backend/src/integrations/agent_framework/core/events.py`
- `backend/tests/unit/test_workflow_status_event_adapter.py`

**技術任務**:

```python
# backend/src/integrations/agent_framework/core/events.py
"""
工作流事件適配器

處理官方 WorkflowStatusEvent 並轉換為內部事件格式
"""

from typing import Any, Callable, Dict, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from agent_framework.workflows import WorkflowStatusEvent


class ExecutionStatus(str, Enum):
    """執行狀態枚舉"""
    PENDING = "pending"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class InternalExecutionEvent:
    """內部執行事件"""
    execution_id: UUID
    event_type: str
    node_id: Optional[str]
    status: ExecutionStatus
    data: Dict[str, Any]
    timestamp: datetime
    is_final: bool = False


class WorkflowStatusEventAdapter:
    """
    工作流狀態事件適配器

    將官方 WorkflowStatusEvent 轉換為內部事件格式，
    並分發給註冊的處理器。
    """

    def __init__(self):
        self._handlers: List[Callable[[InternalExecutionEvent], None]] = []
        self._status_mapping = {
            "started": ExecutionStatus.RUNNING,
            "executor_started": ExecutionStatus.RUNNING,
            "executor_completed": ExecutionStatus.RUNNING,
            "completed": ExecutionStatus.COMPLETED,
            "failed": ExecutionStatus.FAILED,
            "waiting_input": ExecutionStatus.WAITING_APPROVAL,
        }

    def add_handler(self, handler: Callable[[InternalExecutionEvent], None]) -> None:
        """添加事件處理器"""
        self._handlers.append(handler)

    def remove_handler(self, handler: Callable) -> None:
        """移除事件處理器"""
        self._handlers.remove(handler)

    async def handle(self, execution_id: UUID, event: WorkflowStatusEvent) -> None:
        """
        處理狀態事件

        Args:
            execution_id: 執行 ID
            event: 官方狀態事件
        """
        internal_event = self._convert_to_internal(execution_id, event)

        for handler in self._handlers:
            try:
                await handler(internal_event)
            except Exception as e:
                # 記錄錯誤但不中斷其他處理器
                logger.error(f"Event handler error: {e}")

    def _convert_to_internal(
        self,
        execution_id: UUID,
        event: WorkflowStatusEvent
    ) -> InternalExecutionEvent:
        """轉換為內部事件格式"""
        return InternalExecutionEvent(
            execution_id=execution_id,
            event_type=event.event_type,
            node_id=getattr(event, 'executor_id', None),
            status=self._map_status(event.event_type),
            data=event.data if hasattr(event, 'data') else {},
            timestamp=datetime.utcnow(),
            is_final=event.event_type in ('completed', 'failed')
        )

    def _map_status(self, event_type: str) -> ExecutionStatus:
        """映射事件類型到執行狀態"""
        return self._status_mapping.get(event_type, ExecutionStatus.RUNNING)
```

---

### S27-3: ExecutionStateMachine 重構 (8 點)

**描述**: 重構 ExecutionStateMachine 整合官方事件系統。

**驗收標準**:
- [ ] ExecutionStateMachine 可接收官方事件
- [ ] 狀態轉換邏輯保持不變
- [ ] 與 WorkflowStatusEventAdapter 整合
- [ ] 現有 API 不變
- [ ] 單元測試覆蓋

**檔案**:
- `backend/src/domain/executions/state_machine.py` (修改)
- `backend/tests/unit/test_execution_state_machine.py` (更新)

---

### S27-4: ExecutionService 遷移 (7 點)

**描述**: 遷移 ExecutionService 使用新的執行適配器。

**驗收標準**:
- [ ] ExecutionService 使用 ExecutionAdapter
- [ ] 現有功能保持不變
- [ ] 向後兼容
- [ ] 整合測試通過

**檔案**:
- `backend/src/domain/workflows/service.py` (修改)
- `backend/tests/integration/test_execution_service_migration.py`

---

### S27-5: 整合測試 (5 點)

**描述**: 完成執行引擎的整合測試。

**驗收標準**:
- [ ] E2E 順序執行測試通過
- [ ] 事件流測試通過
- [ ] 狀態機轉換測試通過
- [ ] 錯誤恢復測試通過

**測試範例**:

```python
# tests/integration/test_execution_adapter_integration.py
import pytest
from uuid import uuid4

from src.integrations.agent_framework.core.execution import (
    SequentialOrchestrationAdapter,
    ExecutionAdapter
)
from src.integrations.agent_framework.core.events import (
    WorkflowStatusEventAdapter,
    InternalExecutionEvent
)


class TestExecutionAdapterIntegration:

    @pytest.fixture
    def workflow_with_three_nodes(self, agent_service):
        """創建包含三個節點的工作流"""
        nodes = [
            WorkflowNode(id="node-1", type=NodeType.AGENT, agent_id=uuid4()),
            WorkflowNode(id="node-2", type=NodeType.FUNCTION, config={"function_name": "process"}),
            WorkflowNode(id="node-3", type=NodeType.AGENT, agent_id=uuid4()),
        ]
        executors = [
            WorkflowNodeExecutor(node, agent_service) for node in nodes
        ]
        return executors

    @pytest.mark.asyncio
    async def test_sequential_execution(self, workflow_with_three_nodes):
        """測試順序執行"""
        adapter = SequentialOrchestrationAdapter(
            executors=workflow_with_three_nodes,
            name="test-workflow"
        )

        result = await adapter.run({"input": "test data"})

        assert result.success is True
        assert result.executed_count == 3

    @pytest.mark.asyncio
    async def test_event_stream(self, workflow_with_three_nodes):
        """測試事件流"""
        adapter = SequentialOrchestrationAdapter(
            executors=workflow_with_three_nodes,
            name="test-workflow"
        )

        events = []
        async for event in adapter.run_stream({"input": "test data"}):
            events.append(event)

        # 應該至少有開始和完成事件
        assert len(events) >= 2
        assert events[0].event_type == "started"
        assert events[-1].event_type in ("completed", "failed")

    @pytest.mark.asyncio
    async def test_event_adapter_integration(self, workflow_with_three_nodes):
        """測試事件適配器整合"""
        received_events = []

        async def event_handler(event: InternalExecutionEvent):
            received_events.append(event)

        event_adapter = WorkflowStatusEventAdapter()
        event_adapter.add_handler(event_handler)

        orchestration = SequentialOrchestrationAdapter(
            executors=workflow_with_three_nodes
        )

        execution_id = uuid4()
        async for event in orchestration.run_stream({"input": "test"}):
            await event_adapter.handle(execution_id, event)

        assert len(received_events) > 0
        assert all(e.execution_id == execution_id for e in received_events)
```

---

## 完成定義 (Definition of Done)

1. **功能完成**
   - [ ] SequentialOrchestrationAdapter 實現並通過測試
   - [ ] WorkflowStatusEventAdapter 實現並通過測試
   - [ ] ExecutionStateMachine 重構完成
   - [ ] ExecutionService 遷移完成

2. **測試完成**
   - [ ] 單元測試覆蓋率 >= 80%
   - [ ] 整合測試通過
   - [ ] E2E 測試通過

3. **驗證完成**
   - [ ] `from agent_framework.workflows.orchestrations import SequentialOrchestration` 成功
   - [ ] 現有執行功能無退化
   - [ ] 代碼審查完成

---

## 相關文檔

- [Sprint 26 Plan](./sprint-26-plan.md) - Workflow 模型遷移
- [Sprint 28 Plan](./sprint-28-plan.md) - 人工審批遷移
- [Workflows API Reference](../../../../.claude/skills/microsoft-agent-framework/references/workflows-api.md)
