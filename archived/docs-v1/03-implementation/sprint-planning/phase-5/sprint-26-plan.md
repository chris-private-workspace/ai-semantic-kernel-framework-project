# Sprint 26: Workflow 模型遷移

**Sprint 目標**: 將 WorkflowDefinition/Node/Edge 遷移到官方 Workflow/Executor/Edge
**週期**: 2 週
**Story Points**: 36 點
**Phase 5 功能**: P5-F1 (Workflow 模型遷移)

---

## Sprint 概覽

### 目標
1. 創建 WorkflowNodeExecutor 適配器 (基於 `Executor`)
2. 創建 WorkflowEdgeAdapter 適配器 (基於 `Edge`)
3. 創建 WorkflowDefinitionAdapter (整合 `Workflow` 構建)
4. 整合官方 WorkflowContext
5. 完整測試覆蓋

### 成功標準
- [ ] 可以使用官方 `Executor` 包裝現有 `WorkflowNode`
- [ ] 可以使用官方 `Edge` 表示 `WorkflowEdge`
- [ ] 可以構建完整的 `Workflow` 圖
- [ ] 測試覆蓋率 >= 80%

---

## 架構設計

### 目前實現 (需遷移)

```python
# domain/workflows/models.py - 自行實現
@dataclass
class WorkflowNode:
    id: str
    type: NodeType  # AGENT, FUNCTION, CONDITION, etc.
    agent_id: Optional[UUID] = None
    config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowEdge:
    id: str
    source_node_id: str
    target_node_id: str
    condition: Optional[str] = None

@dataclass
class WorkflowDefinition:
    id: UUID
    name: str
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
    variables: Dict[str, Any]
```

### 目標架構 (使用官方 API)

```python
# integrations/agent_framework/core/executor.py
from agent_framework.workflows import Executor
from pydantic import BaseModel

class NodeInput(BaseModel):
    """節點輸入模型"""
    data: Dict[str, Any]
    context: Dict[str, Any] = {}

class NodeOutput(BaseModel):
    """節點輸出模型"""
    result: Any
    metadata: Dict[str, Any] = {}

@Executor.register
class WorkflowNodeExecutor(Executor[NodeInput, NodeOutput]):
    """
    基於官方 Executor 的節點適配器

    將現有 WorkflowNode 包裝為官方 Executor
    """

    def __init__(self, node: WorkflowNode, agent_service: AgentService):
        super().__init__(id=node.id)
        self._node = node
        self._agent_service = agent_service

    async def execute(self, input: NodeInput, context) -> NodeOutput:
        """執行節點邏輯"""
        if self._node.type == NodeType.AGENT:
            result = await self._execute_agent_node(input, context)
        elif self._node.type == NodeType.FUNCTION:
            result = await self._execute_function_node(input, context)
        elif self._node.type == NodeType.CONDITION:
            result = await self._execute_condition_node(input, context)
        else:
            raise ValueError(f"Unknown node type: {self._node.type}")

        return NodeOutput(result=result, metadata={"node_id": self._node.id})

    async def _execute_agent_node(self, input: NodeInput, context) -> Any:
        """執行 Agent 節點"""
        if not self._node.agent_id:
            raise ValueError("Agent node requires agent_id")

        # 使用現有 AgentService 執行
        result = await self._agent_service.execute(
            agent_id=self._node.agent_id,
            input_data=input.data,
        )
        return result
```

```python
# integrations/agent_framework/core/edge.py
from agent_framework.workflows import Edge

class WorkflowEdgeAdapter:
    """
    工作流邊適配器

    將 WorkflowEdge 轉換為官方 Edge
    """

    def __init__(self, edge: WorkflowEdge):
        self._edge = edge

    def to_official_edge(self) -> Edge:
        """轉換為官方 Edge"""
        if self._edge.condition:
            return Edge(
                source=self._edge.source_node_id,
                target=self._edge.target_node_id,
                condition=lambda output: self._evaluate_condition(output)
            )
        else:
            return Edge(
                source=self._edge.source_node_id,
                target=self._edge.target_node_id
            )

    def _evaluate_condition(self, output: Any) -> bool:
        """評估條件表達式"""
        # 實現條件評估邏輯
        pass
```

```python
# integrations/agent_framework/core/workflow.py
from agent_framework.workflows import Workflow

class WorkflowDefinitionAdapter:
    """
    工作流定義適配器

    將 WorkflowDefinition 轉換為官方 Workflow
    """

    def __init__(
        self,
        definition: WorkflowDefinition,
        agent_service: AgentService,
        checkpoint_store: Optional[CheckpointStorage] = None
    ):
        self._definition = definition
        self._agent_service = agent_service
        self._checkpoint_store = checkpoint_store
        self._executors: List[Executor] = []
        self._edges: List[Edge] = []

    def build(self) -> Workflow:
        """構建官方 Workflow"""
        # 1. 轉換所有節點為 Executor
        for node in self._definition.nodes:
            executor = WorkflowNodeExecutor(node, self._agent_service)
            self._executors.append(executor)

        # 2. 轉換所有邊為 Edge
        for edge in self._definition.edges:
            adapter = WorkflowEdgeAdapter(edge)
            self._edges.append(adapter.to_official_edge())

        # 3. 構建 Workflow
        workflow = Workflow(
            executors=self._executors,
            edges=self._edges,
            checkpoint_store=self._checkpoint_store
        )

        return workflow

    async def run(self, input_data: Dict[str, Any]) -> WorkflowRunResult:
        """執行工作流"""
        workflow = self.build()
        return await workflow.run(input_data)
```

---

## User Stories

### S26-1: WorkflowNodeExecutor (8 點)

**描述**: 創建基於官方 `Executor` 的節點適配器，將現有 `WorkflowNode` 包裝為可執行單元。

**驗收標準**:
- [ ] 實現 `WorkflowNodeExecutor` 類繼承 `Executor`
- [ ] 支持 AGENT, FUNCTION, CONDITION 三種節點類型
- [ ] 正確處理輸入/輸出類型
- [ ] 整合現有 `AgentService`
- [ ] 單元測試覆蓋

**檔案**:
- `backend/src/integrations/agent_framework/core/__init__.py`
- `backend/src/integrations/agent_framework/core/executor.py`
- `backend/tests/unit/test_workflow_node_executor.py`

**技術任務**:

```python
# backend/src/integrations/agent_framework/core/executor.py
"""
WorkflowNode Executor - 基於官方 Agent Framework Executor

將現有的 WorkflowNode 概念適配到官方 Executor 介面
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel
from uuid import UUID

from agent_framework.workflows import Executor

from src.domain.workflows.models import WorkflowNode, NodeType
from src.domain.agents.service import AgentService


class NodeInput(BaseModel):
    """節點輸入模型"""
    data: Dict[str, Any]
    execution_id: Optional[UUID] = None
    context: Dict[str, Any] = {}


class NodeOutput(BaseModel):
    """節點輸出模型"""
    result: Any
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


@Executor.register
class WorkflowNodeExecutor(Executor[NodeInput, NodeOutput]):
    """
    工作流節點執行器

    將 WorkflowNode 包裝為官方 Executor，支持：
    - AGENT 節點：調用 Agent 執行
    - FUNCTION 節點：執行函數
    - CONDITION 節點：條件評估
    """

    def __init__(
        self,
        node: WorkflowNode,
        agent_service: AgentService,
        function_registry: Optional[Dict[str, callable]] = None
    ):
        super().__init__(id=node.id)
        self._node = node
        self._agent_service = agent_service
        self._function_registry = function_registry or {}

    async def execute(self, input: NodeInput, context) -> NodeOutput:
        """
        執行節點邏輯

        Args:
            input: 節點輸入
            context: 工作流上下文

        Returns:
            NodeOutput: 執行結果
        """
        try:
            if self._node.type == NodeType.AGENT:
                result = await self._execute_agent_node(input, context)
            elif self._node.type == NodeType.FUNCTION:
                result = await self._execute_function_node(input, context)
            elif self._node.type == NodeType.CONDITION:
                result = await self._execute_condition_node(input, context)
            else:
                raise ValueError(f"Unknown node type: {self._node.type}")

            return NodeOutput(
                result=result,
                success=True,
                metadata={
                    "node_id": self._node.id,
                    "node_type": self._node.type.value
                }
            )
        except Exception as e:
            return NodeOutput(
                result=None,
                success=False,
                error=str(e),
                metadata={"node_id": self._node.id}
            )

    async def _execute_agent_node(self, input: NodeInput, context) -> Any:
        """執行 Agent 節點"""
        if not self._node.agent_id:
            raise ValueError("Agent node requires agent_id")

        result = await self._agent_service.execute(
            agent_id=self._node.agent_id,
            input_data=input.data,
            config=self._node.config
        )
        return result

    async def _execute_function_node(self, input: NodeInput, context) -> Any:
        """執行函數節點"""
        func_name = self._node.config.get("function_name")
        if not func_name or func_name not in self._function_registry:
            raise ValueError(f"Function not found: {func_name}")

        func = self._function_registry[func_name]
        if asyncio.iscoroutinefunction(func):
            return await func(input.data)
        else:
            return func(input.data)

    async def _execute_condition_node(self, input: NodeInput, context) -> bool:
        """執行條件節點"""
        condition_expr = self._node.config.get("condition")
        if not condition_expr:
            return True

        # 評估條件表達式
        return self._evaluate_condition(condition_expr, input.data)

    def _evaluate_condition(self, expr: str, data: Dict[str, Any]) -> bool:
        """評估條件表達式"""
        # 安全的條件評估
        # 避免使用 eval，使用解析器
        pass
```

---

### S26-2: WorkflowEdgeAdapter (8 點)

**描述**: 創建工作流邊適配器，將 `WorkflowEdge` 轉換為官方 `Edge`。

**驗收標準**:
- [ ] 實現 `WorkflowEdgeAdapter` 類
- [ ] 支持無條件邊
- [ ] 支持條件邊
- [ ] 條件表達式評估正確
- [ ] 單元測試覆蓋

**檔案**:
- `backend/src/integrations/agent_framework/core/edge.py`
- `backend/tests/unit/test_workflow_edge_adapter.py`

**技術任務**:

```python
# backend/src/integrations/agent_framework/core/edge.py
"""
WorkflowEdge Adapter - 官方 Edge 介面適配

將現有的 WorkflowEdge 轉換為官方 Edge
"""

from typing import Any, Callable, Optional

from agent_framework.workflows import Edge

from src.domain.workflows.models import WorkflowEdge


class ConditionEvaluator:
    """
    條件評估器

    安全地評估條件表達式
    """

    def __init__(self, expression: str):
        self._expression = expression
        self._compiled = self._compile(expression)

    def _compile(self, expression: str):
        """編譯條件表達式"""
        # 使用安全的表達式解析
        # 避免 eval，使用 AST 或規則引擎
        pass

    def evaluate(self, output: Any) -> bool:
        """評估條件"""
        if isinstance(output, dict):
            return self._evaluate_dict(output)
        return bool(output)

    def _evaluate_dict(self, data: dict) -> bool:
        """評估字典輸出"""
        # 支持的條件格式:
        # - "$.result == 'success'"
        # - "$.value > 10"
        # - "$.status in ['completed', 'approved']"
        pass


class WorkflowEdgeAdapter:
    """
    工作流邊適配器

    將 WorkflowEdge 轉換為官方 Edge
    """

    def __init__(self, edge: WorkflowEdge):
        self._edge = edge
        self._evaluator: Optional[ConditionEvaluator] = None

        if edge.condition:
            self._evaluator = ConditionEvaluator(edge.condition)

    def to_official_edge(self) -> Edge:
        """轉換為官方 Edge"""
        if self._evaluator:
            return Edge(
                source=self._edge.source_node_id,
                target=self._edge.target_node_id,
                condition=self._evaluator.evaluate
            )
        else:
            return Edge(
                source=self._edge.source_node_id,
                target=self._edge.target_node_id
            )

    @classmethod
    def from_start(cls, target_node_id: str) -> Edge:
        """創建從起點開始的邊"""
        return Edge(source="start", target=target_node_id)

    @classmethod
    def to_end(cls, source_node_id: str) -> Edge:
        """創建到終點的邊"""
        return Edge(source=source_node_id, target="end")
```

---

### S26-3: WorkflowDefinitionAdapter (10 點)

**描述**: 創建工作流定義適配器，整合 `Workflow` 建構。

**驗收標準**:
- [ ] 實現 `WorkflowDefinitionAdapter` 類
- [ ] 可構建包含多個節點的工作流
- [ ] 正確處理複雜邊關係
- [ ] 支持檢查點存儲
- [ ] 可執行構建的工作流
- [ ] 整合測試通過

**檔案**:
- `backend/src/integrations/agent_framework/core/workflow.py`
- `backend/tests/unit/test_workflow_definition_adapter.py`
- `backend/tests/integration/test_workflow_adapter_integration.py`

---

### S26-4: WorkflowContext 適配 (5 點)

**描述**: 整合官方 WorkflowContext。

**驗收標準**:
- [ ] 現有 `WorkflowContext` 可與官方 context 互操作
- [ ] 狀態共享正確
- [ ] 元數據傳遞正確

**檔案**:
- `backend/src/integrations/agent_framework/core/context.py`
- `backend/tests/unit/test_workflow_context_adapter.py`

---

### S26-5: 單元測試和驗證 (5 點)

**描述**: 完成所有單元測試和驗證。

**驗收標準**:
- [ ] 所有單元測試通過
- [ ] 測試覆蓋率 >= 80%
- [ ] 驗證腳本通過

**測試範例**:

```python
# tests/unit/test_workflow_node_executor.py
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.integrations.agent_framework.core.executor import (
    WorkflowNodeExecutor,
    NodeInput,
    NodeOutput
)
from src.domain.workflows.models import WorkflowNode, NodeType


class TestWorkflowNodeExecutor:

    @pytest.fixture
    def mock_agent_service(self):
        service = MagicMock()
        service.execute = AsyncMock(return_value={"output": "result"})
        return service

    @pytest.fixture
    def agent_node(self):
        return WorkflowNode(
            id="node-1",
            type=NodeType.AGENT,
            agent_id=UUID("12345678-1234-5678-1234-567812345678"),
            config={}
        )

    @pytest.mark.asyncio
    async def test_execute_agent_node(self, agent_node, mock_agent_service):
        """測試執行 Agent 節點"""
        executor = WorkflowNodeExecutor(
            node=agent_node,
            agent_service=mock_agent_service
        )

        input_data = NodeInput(data={"query": "test"})
        context = MagicMock()

        result = await executor.execute(input_data, context)

        assert result.success is True
        assert result.result == {"output": "result"}
        mock_agent_service.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_node_error_handling(self, agent_node, mock_agent_service):
        """測試節點執行錯誤處理"""
        mock_agent_service.execute.side_effect = Exception("Agent error")

        executor = WorkflowNodeExecutor(
            node=agent_node,
            agent_service=mock_agent_service
        )

        input_data = NodeInput(data={"query": "test"})
        context = MagicMock()

        result = await executor.execute(input_data, context)

        assert result.success is False
        assert "Agent error" in result.error
```

---

## 完成定義 (Definition of Done)

1. **功能完成**
   - [ ] WorkflowNodeExecutor 實現並通過測試
   - [ ] WorkflowEdgeAdapter 實現並通過測試
   - [ ] WorkflowDefinitionAdapter 實現並通過測試
   - [ ] WorkflowContext 適配完成

2. **測試完成**
   - [ ] 單元測試覆蓋率 >= 80%
   - [ ] 整合測試通過
   - [ ] 所有節點類型測試覆蓋

3. **驗證完成**
   - [ ] `python -c "from agent_framework.workflows import Executor, Edge, Workflow"` 通過
   - [ ] 驗證腳本通過
   - [ ] 代碼審查完成

4. **文檔完成**
   - [ ] progress.md 更新
   - [ ] decisions.md 記錄重要決策
   - [ ] checklist 100% 完成

---

## 相關文檔

- [Phase 5 Overview](./README.md)
- [Phase 5 完整計劃](./PHASE5-MVP-REFACTORING-PLAN.md)
- [Sprint 26 Checklist](./sprint-26-checklist.md)
- [Sprint 27 Plan](./sprint-27-plan.md) - 執行引擎遷移
- [Workflows API Reference](../../../../.claude/skills/microsoft-agent-framework/references/workflows-api.md)
