# Sprint 11: 嵌套工作流 (Nested Workflows & Advanced Orchestration)

**Sprint 目標**: 實現工作流嵌套和遞歸執行能力，支援複雜的階層式流程編排

**週期**: Week 23-24 (2 週)
**Story Points**: 39 點
**前置條件**: Sprint 7-10 完成

---

## Sprint 概述

### 核心交付物

| ID | 功能 | 優先級 | Story Points | 狀態 |
|----|------|--------|--------------|------|
| P2-F11 | Nested Workflows 嵌套工作流 | 🟢 低 | 18 | 待開發 |
| P2-F12 | Sub-workflow Execution 子工作流執行 | 🟢 低 | 13 | 待開發 |
| P2-F13 | Recursive Patterns 遞歸模式 | 🟢 低 | 8 | 待開發 |

### 設計概念

```
┌─────────────────────────────────────────────────────────────┐
│                    Parent Workflow                          │
│                                                             │
│  ┌─────────┐     ┌─────────────────────────────┐           │
│  │  Task A │ ──▶ │     Sub-Workflow 1          │           │
│  └─────────┘     │  ┌─────┐  ┌─────┐  ┌─────┐  │           │
│                  │  │ 1.1 │─▶│ 1.2 │─▶│ 1.3 │  │           │
│                  │  └─────┘  └─────┘  └─────┘  │           │
│                  └─────────────────────────────┘           │
│                              │                              │
│                              ▼                              │
│  ┌─────────────────────────────────────────────┐           │
│  │         Parallel Sub-Workflows               │           │
│  │  ┌──────────────┐    ┌──────────────┐       │           │
│  │  │ Sub-WF 2.1   │    │ Sub-WF 2.2   │       │           │
│  │  │ ┌───┐ ┌───┐  │    │ ┌───┐ ┌───┐  │       │           │
│  │  │ │ A │─│ B │  │    │ │ X │─│ Y │  │       │           │
│  │  │ └───┘ └───┘  │    │ └───┘ └───┘  │       │           │
│  │  └──────────────┘    └──────────────┘       │           │
│  └─────────────────────────────────────────────┘           │
│                              │                              │
│                              ▼                              │
│                        ┌─────────┐                          │
│                        │  Task Z │                          │
│                        └─────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

---

## User Stories

### Story 11-1: Nested Workflow Manager (8 點)

**作為** 系統架構師
**我希望** 實現嵌套工作流管理器
**以便** 工作流可以包含子工作流，形成階層結構

#### 技術規格

```python
# backend/src/domain/orchestration/nested/workflow_manager.py

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
import asyncio


class NestedWorkflowType(str, Enum):
    """嵌套工作流類型"""
    INLINE = "inline"           # 內聯定義的子工作流
    REFERENCE = "reference"     # 引用現有工作流
    DYNAMIC = "dynamic"         # 動態生成的子工作流
    RECURSIVE = "recursive"     # 遞歸調用自身


class WorkflowScope(str, Enum):
    """工作流作用域"""
    ISOLATED = "isolated"       # 完全隔離，獨立上下文
    INHERITED = "inherited"     # 繼承父工作流上下文
    SHARED = "shared"           # 共享上下文，雙向同步


@dataclass
class NestedWorkflowConfig:
    """嵌套工作流配置"""
    workflow_type: NestedWorkflowType
    scope: WorkflowScope = WorkflowScope.INHERITED
    max_depth: int = 5          # 最大嵌套深度
    timeout_seconds: int = 600  # 子工作流超時
    retry_on_failure: bool = True
    max_retries: int = 2
    pass_context: bool = True   # 是否傳遞上下文
    return_outputs: bool = True # 是否返回輸出


@dataclass
class SubWorkflowReference:
    """子工作流引用"""
    id: UUID
    parent_workflow_id: UUID
    workflow_id: Optional[UUID]  # 引用的工作流 ID（REFERENCE 類型）
    definition: Optional[Dict[str, Any]]  # 內聯定義（INLINE/DYNAMIC 類型）
    config: NestedWorkflowConfig
    input_mapping: Dict[str, str]   # 父上下文 -> 子輸入的映射
    output_mapping: Dict[str, str]  # 子輸出 -> 父上下文的映射
    position: int  # 在父工作流中的位置
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class NestedExecutionContext:
    """嵌套執行上下文"""
    execution_id: UUID
    parent_execution_id: Optional[UUID]
    workflow_id: UUID
    depth: int
    path: List[UUID]  # 從根到當前的執行路徑
    variables: Dict[str, Any]
    parent_variables: Optional[Dict[str, Any]]
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class NestedWorkflowManager:
    """
    嵌套工作流管理器

    負責：
    - 管理工作流的階層結構
    - 處理子工作流的執行
    - 管理上下文傳遞
    - 深度限制和循環檢測
    """

    def __init__(
        self,
        workflow_service: Any,
        execution_service: Any,
        max_global_depth: int = 10
    ):
        self.workflow_service = workflow_service
        self.execution_service = execution_service
        self.max_global_depth = max_global_depth

        # 活躍的嵌套執行
        self._active_executions: Dict[UUID, NestedExecutionContext] = {}

        # 工作流依賴圖（用於循環檢測）
        self._dependency_graph: Dict[UUID, Set[UUID]] = {}

    async def register_sub_workflow(
        self,
        parent_workflow_id: UUID,
        sub_workflow: SubWorkflowReference
    ) -> None:
        """
        註冊子工作流

        Args:
            parent_workflow_id: 父工作流 ID
            sub_workflow: 子工作流引用
        """
        # 更新依賴圖
        if parent_workflow_id not in self._dependency_graph:
            self._dependency_graph[parent_workflow_id] = set()

        if sub_workflow.workflow_id:
            self._dependency_graph[parent_workflow_id].add(sub_workflow.workflow_id)

        # 檢查循環依賴
        if self._has_cycle(parent_workflow_id):
            raise ValueError(
                f"Circular dependency detected when adding sub-workflow "
                f"to {parent_workflow_id}"
            )

    def _has_cycle(self, start_id: UUID) -> bool:
        """檢測循環依賴"""
        visited = set()
        rec_stack = set()

        def dfs(node_id: UUID) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            for neighbor in self._dependency_graph.get(node_id, set()):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        return dfs(start_id)

    async def execute_sub_workflow(
        self,
        parent_context: NestedExecutionContext,
        sub_workflow: SubWorkflowReference
    ) -> Dict[str, Any]:
        """
        執行子工作流

        Args:
            parent_context: 父執行上下文
            sub_workflow: 子工作流引用

        Returns:
            執行結果
        """
        # 檢查深度限制
        new_depth = parent_context.depth + 1
        if new_depth > sub_workflow.config.max_depth:
            raise ValueError(
                f"Maximum nesting depth ({sub_workflow.config.max_depth}) exceeded"
            )

        if new_depth > self.max_global_depth:
            raise ValueError(
                f"Global maximum nesting depth ({self.max_global_depth}) exceeded"
            )

        # 建立子執行上下文
        child_context = self._create_child_context(
            parent_context,
            sub_workflow
        )

        self._active_executions[child_context.execution_id] = child_context

        try:
            # 根據類型執行
            if sub_workflow.config.workflow_type == NestedWorkflowType.REFERENCE:
                result = await self._execute_reference_workflow(
                    child_context, sub_workflow
                )
            elif sub_workflow.config.workflow_type == NestedWorkflowType.INLINE:
                result = await self._execute_inline_workflow(
                    child_context, sub_workflow
                )
            elif sub_workflow.config.workflow_type == NestedWorkflowType.DYNAMIC:
                result = await self._execute_dynamic_workflow(
                    child_context, sub_workflow
                )
            elif sub_workflow.config.workflow_type == NestedWorkflowType.RECURSIVE:
                result = await self._execute_recursive_workflow(
                    child_context, sub_workflow
                )
            else:
                raise ValueError(f"Unknown workflow type: {sub_workflow.config.workflow_type}")

            # 映射輸出到父上下文
            if sub_workflow.config.return_outputs:
                self._map_outputs(parent_context, sub_workflow, result)

            child_context.completed_at = datetime.utcnow()
            return result

        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Sub-workflow {sub_workflow.id} timed out "
                f"after {sub_workflow.config.timeout_seconds} seconds"
            )
        finally:
            del self._active_executions[child_context.execution_id]

    def _create_child_context(
        self,
        parent_context: NestedExecutionContext,
        sub_workflow: SubWorkflowReference
    ) -> NestedExecutionContext:
        """建立子執行上下文"""
        child_variables = {}

        # 根據作用域處理變數
        if sub_workflow.config.scope == WorkflowScope.INHERITED:
            child_variables = parent_context.variables.copy()
        elif sub_workflow.config.scope == WorkflowScope.SHARED:
            child_variables = parent_context.variables  # 共享引用
        # ISOLATED: 保持空的 child_variables

        # 應用輸入映射
        for parent_key, child_key in sub_workflow.input_mapping.items():
            if parent_key in parent_context.variables:
                child_variables[child_key] = parent_context.variables[parent_key]

        return NestedExecutionContext(
            execution_id=uuid4(),
            parent_execution_id=parent_context.execution_id,
            workflow_id=sub_workflow.workflow_id or sub_workflow.id,
            depth=parent_context.depth + 1,
            path=parent_context.path + [parent_context.execution_id],
            variables=child_variables,
            parent_variables=parent_context.variables if sub_workflow.config.scope == WorkflowScope.SHARED else None
        )

    async def _execute_reference_workflow(
        self,
        context: NestedExecutionContext,
        sub_workflow: SubWorkflowReference
    ) -> Dict[str, Any]:
        """執行引用的工作流"""
        return await asyncio.wait_for(
            self.execution_service.execute_workflow(
                workflow_id=sub_workflow.workflow_id,
                inputs=context.variables,
                parent_execution_id=context.parent_execution_id
            ),
            timeout=sub_workflow.config.timeout_seconds
        )

    async def _execute_inline_workflow(
        self,
        context: NestedExecutionContext,
        sub_workflow: SubWorkflowReference
    ) -> Dict[str, Any]:
        """執行內聯定義的工作流"""
        # 從定義中建立臨時工作流
        definition = sub_workflow.definition
        if not definition:
            raise ValueError("Inline workflow requires definition")

        # 使用工作流服務執行定義
        return await asyncio.wait_for(
            self.execution_service.execute_workflow_definition(
                definition=definition,
                inputs=context.variables,
                parent_execution_id=context.parent_execution_id
            ),
            timeout=sub_workflow.config.timeout_seconds
        )

    async def _execute_dynamic_workflow(
        self,
        context: NestedExecutionContext,
        sub_workflow: SubWorkflowReference
    ) -> Dict[str, Any]:
        """執行動態生成的工作流"""
        # 動態工作流的定義可能是一個生成器函數
        generator = sub_workflow.definition.get("generator")
        if callable(generator):
            definition = await generator(context.variables)
        else:
            definition = sub_workflow.definition

        return await asyncio.wait_for(
            self.execution_service.execute_workflow_definition(
                definition=definition,
                inputs=context.variables,
                parent_execution_id=context.parent_execution_id
            ),
            timeout=sub_workflow.config.timeout_seconds
        )

    async def _execute_recursive_workflow(
        self,
        context: NestedExecutionContext,
        sub_workflow: SubWorkflowReference
    ) -> Dict[str, Any]:
        """
        執行遞歸工作流

        遞歸工作流調用自身，直到滿足終止條件
        """
        # 檢查終止條件
        termination_condition = sub_workflow.definition.get("termination_condition")
        if termination_condition and termination_condition(context.variables):
            return {"status": "terminated", "depth": context.depth}

        # 遞歸執行
        return await self._execute_reference_workflow(context, sub_workflow)

    def _map_outputs(
        self,
        parent_context: NestedExecutionContext,
        sub_workflow: SubWorkflowReference,
        result: Dict[str, Any]
    ) -> None:
        """將子工作流輸出映射回父上下文"""
        for child_key, parent_key in sub_workflow.output_mapping.items():
            if child_key in result:
                parent_context.variables[parent_key] = result[child_key]

    def get_execution_tree(
        self,
        root_execution_id: UUID
    ) -> Dict[str, Any]:
        """獲取執行樹結構"""
        def build_tree(exec_id: UUID) -> Dict[str, Any]:
            context = self._active_executions.get(exec_id)
            if not context:
                return {"id": str(exec_id), "status": "not_found"}

            children = [
                build_tree(child_id)
                for child_id, child_ctx in self._active_executions.items()
                if child_ctx.parent_execution_id == exec_id
            ]

            return {
                "id": str(exec_id),
                "workflow_id": str(context.workflow_id),
                "depth": context.depth,
                "started_at": context.started_at.isoformat(),
                "children": children
            }

        return build_tree(root_execution_id)

    async def cancel_nested_execution(
        self,
        execution_id: UUID,
        cascade: bool = True
    ) -> None:
        """
        取消嵌套執行

        Args:
            execution_id: 執行 ID
            cascade: 是否級聯取消所有子執行
        """
        if cascade:
            # 找出所有子執行
            children_to_cancel = [
                child_id
                for child_id, ctx in self._active_executions.items()
                if execution_id in ctx.path
            ]

            for child_id in children_to_cancel:
                await self.execution_service.cancel_execution(child_id)

        await self.execution_service.cancel_execution(execution_id)
```

#### 驗收標準
- [ ] 支援工作流嵌套結構
- [ ] 正確的深度限制
- [ ] 循環依賴檢測
- [ ] 上下文傳遞正確
- [ ] 單元測試覆蓋率 > 85%

---

### Story 11-2: Sub-workflow Executor (5 點)

**作為** 系統架構師
**我希望** 實現子工作流執行器
**以便** 子工作流可以獨立執行並返回結果

#### 技術規格

```python
# backend/src/domain/orchestration/nested/sub_executor.py

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Awaitable
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
import asyncio


class SubWorkflowExecutionMode(str, Enum):
    """子工作流執行模式"""
    SYNC = "sync"               # 同步等待完成
    ASYNC = "async"             # 異步執行，不等待
    FIRE_AND_FORGET = "fire_and_forget"  # 發射即忘
    CALLBACK = "callback"       # 完成後回調


@dataclass
class SubExecutionState:
    """子執行狀態"""
    execution_id: UUID
    sub_workflow_id: UUID
    mode: SubWorkflowExecutionMode
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    callback: Optional[Callable] = None


class SubWorkflowExecutor:
    """
    子工作流執行器

    負責執行嵌套的子工作流
    """

    def __init__(
        self,
        workflow_engine: Any,
        checkpoint_service: Any
    ):
        self.workflow_engine = workflow_engine
        self.checkpoint_service = checkpoint_service

        # 執行狀態追蹤
        self._executions: Dict[UUID, SubExecutionState] = {}

        # 異步執行的任務
        self._async_tasks: Dict[UUID, asyncio.Task] = {}

    async def execute(
        self,
        sub_workflow_id: UUID,
        inputs: Dict[str, Any],
        mode: SubWorkflowExecutionMode = SubWorkflowExecutionMode.SYNC,
        callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        執行子工作流

        Args:
            sub_workflow_id: 子工作流 ID
            inputs: 輸入參數
            mode: 執行模式
            callback: 完成回調（CALLBACK 模式使用）

        Returns:
            執行結果（同步模式）或執行 ID（異步模式）
        """
        execution_id = uuid4()

        state = SubExecutionState(
            execution_id=execution_id,
            sub_workflow_id=sub_workflow_id,
            mode=mode,
            callback=callback
        )
        self._executions[execution_id] = state

        if mode == SubWorkflowExecutionMode.SYNC:
            return await self._execute_sync(state, inputs)

        elif mode == SubWorkflowExecutionMode.ASYNC:
            task = asyncio.create_task(
                self._execute_async(state, inputs)
            )
            self._async_tasks[execution_id] = task
            return {"execution_id": str(execution_id), "status": "started"}

        elif mode == SubWorkflowExecutionMode.FIRE_AND_FORGET:
            asyncio.create_task(self._execute_fire_forget(state, inputs))
            return {"execution_id": str(execution_id), "status": "dispatched"}

        elif mode == SubWorkflowExecutionMode.CALLBACK:
            if not callback:
                raise ValueError("Callback mode requires a callback function")
            task = asyncio.create_task(
                self._execute_with_callback(state, inputs)
            )
            self._async_tasks[execution_id] = task
            return {"execution_id": str(execution_id), "status": "started"}

    async def _execute_sync(
        self,
        state: SubExecutionState,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """同步執行"""
        state.status = "running"
        state.started_at = datetime.utcnow()

        try:
            result = await self.workflow_engine.execute(
                workflow_id=state.sub_workflow_id,
                inputs=inputs
            )

            state.status = "completed"
            state.result = result
            state.completed_at = datetime.utcnow()

            return result

        except Exception as e:
            state.status = "failed"
            state.error = str(e)
            state.completed_at = datetime.utcnow()
            raise

    async def _execute_async(
        self,
        state: SubExecutionState,
        inputs: Dict[str, Any]
    ) -> None:
        """異步執行"""
        await self._execute_sync(state, inputs)

    async def _execute_fire_forget(
        self,
        state: SubExecutionState,
        inputs: Dict[str, Any]
    ) -> None:
        """發射即忘執行"""
        try:
            await self._execute_sync(state, inputs)
        except Exception:
            # 記錄錯誤但不拋出
            pass

    async def _execute_with_callback(
        self,
        state: SubExecutionState,
        inputs: Dict[str, Any]
    ) -> None:
        """帶回調的執行"""
        try:
            result = await self._execute_sync(state, inputs)
            if state.callback:
                await state.callback(result)
        except Exception as e:
            if state.callback:
                await state.callback({"error": str(e)})

    async def get_execution_status(
        self,
        execution_id: UUID
    ) -> Dict[str, Any]:
        """獲取執行狀態"""
        state = self._executions.get(execution_id)
        if not state:
            return {"error": "Execution not found"}

        return {
            "execution_id": str(execution_id),
            "sub_workflow_id": str(state.sub_workflow_id),
            "status": state.status,
            "result": state.result,
            "error": state.error,
            "started_at": state.started_at.isoformat() if state.started_at else None,
            "completed_at": state.completed_at.isoformat() if state.completed_at else None
        }

    async def wait_for_completion(
        self,
        execution_id: UUID,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """等待執行完成"""
        task = self._async_tasks.get(execution_id)
        if not task:
            state = self._executions.get(execution_id)
            if state and state.status in ["completed", "failed"]:
                return await self.get_execution_status(execution_id)
            return {"error": "Execution not found or not async"}

        try:
            await asyncio.wait_for(task, timeout=timeout)
        except asyncio.TimeoutError:
            return {"error": "Wait timeout", "status": "running"}

        return await self.get_execution_status(execution_id)

    async def cancel_execution(
        self,
        execution_id: UUID
    ) -> bool:
        """取消執行"""
        task = self._async_tasks.get(execution_id)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

            state = self._executions.get(execution_id)
            if state:
                state.status = "cancelled"

            return True

        return False

    async def execute_parallel(
        self,
        sub_workflows: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        並行執行多個子工作流

        Args:
            sub_workflows: 子工作流配置列表
                [{"id": UUID, "inputs": {...}}, ...]

        Returns:
            執行結果列表
        """
        tasks = []
        for sw in sub_workflows:
            task = self._execute_sync(
                SubExecutionState(
                    execution_id=uuid4(),
                    sub_workflow_id=sw["id"],
                    mode=SubWorkflowExecutionMode.SYNC
                ),
                sw.get("inputs", {})
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return [
            result if not isinstance(result, Exception)
            else {"error": str(result)}
            for result in results
        ]

    async def execute_sequential(
        self,
        sub_workflows: List[Dict[str, Any]],
        pass_outputs: bool = True
    ) -> List[Dict[str, Any]]:
        """
        順序執行多個子工作流

        Args:
            sub_workflows: 子工作流配置列表
            pass_outputs: 是否將前一個輸出傳給下一個

        Returns:
            執行結果列表
        """
        results = []
        previous_output = {}

        for sw in sub_workflows:
            inputs = sw.get("inputs", {})
            if pass_outputs:
                inputs = {**previous_output, **inputs}

            state = SubExecutionState(
                execution_id=uuid4(),
                sub_workflow_id=sw["id"],
                mode=SubWorkflowExecutionMode.SYNC
            )

            try:
                result = await self._execute_sync(state, inputs)
                results.append(result)
                previous_output = result
            except Exception as e:
                results.append({"error": str(e)})
                if sw.get("stop_on_error", True):
                    break

        return results
```

#### 驗收標準
- [ ] 支援同步/異步執行模式
- [ ] 支援回調機制
- [ ] 支援並行/順序執行
- [ ] 執行狀態追蹤
- [ ] 取消執行功能

---

### Story 11-3: Recursive Pattern Handler (5 點)

**作為** 系統架構師
**我希望** 實現遞歸模式處理器
**以便** 工作流可以安全地遞歸執行

#### 技術規格

```python
# backend/src/domain/orchestration/nested/recursive_handler.py

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable, List
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum


class RecursionStrategy(str, Enum):
    """遞歸策略"""
    DEPTH_FIRST = "depth_first"     # 深度優先
    BREADTH_FIRST = "breadth_first" # 廣度優先
    PARALLEL = "parallel"           # 並行遞歸


class TerminationType(str, Enum):
    """終止類型"""
    CONDITION = "condition"         # 條件滿足
    MAX_DEPTH = "max_depth"         # 達到最大深度
    MAX_ITERATIONS = "max_iterations"  # 達到最大迭代
    TIMEOUT = "timeout"             # 超時
    CONVERGENCE = "convergence"     # 結果收斂


@dataclass
class RecursionConfig:
    """遞歸配置"""
    max_depth: int = 10
    max_iterations: int = 100
    timeout_seconds: int = 300
    strategy: RecursionStrategy = RecursionStrategy.DEPTH_FIRST
    termination_condition: Optional[Callable[[Dict[str, Any], int], bool]] = None
    convergence_threshold: Optional[float] = None
    memoization: bool = True  # 是否啟用記憶化


@dataclass
class RecursionState:
    """遞歸狀態"""
    id: UUID
    workflow_id: UUID
    current_depth: int
    iteration_count: int
    history: List[Dict[str, Any]] = field(default_factory=list)
    memo: Dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.utcnow)
    terminated: bool = False
    termination_type: Optional[TerminationType] = None


class RecursivePatternHandler:
    """
    遞歸模式處理器

    安全地處理工作流的遞歸執行
    """

    def __init__(
        self,
        sub_executor: "SubWorkflowExecutor",
        config: RecursionConfig
    ):
        self.sub_executor = sub_executor
        self.config = config

        # 活躍的遞歸狀態
        self._states: Dict[UUID, RecursionState] = {}

    async def execute_recursive(
        self,
        workflow_id: UUID,
        initial_inputs: Dict[str, Any],
        recursive_inputs_fn: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        執行遞歸工作流

        Args:
            workflow_id: 工作流 ID
            initial_inputs: 初始輸入
            recursive_inputs_fn: 生成下一次遞歸輸入的函數

        Returns:
            最終結果
        """
        state = RecursionState(
            id=uuid4(),
            workflow_id=workflow_id,
            current_depth=0,
            iteration_count=0
        )
        self._states[state.id] = state

        try:
            return await self._recursive_execute(
                state=state,
                inputs=initial_inputs,
                recursive_inputs_fn=recursive_inputs_fn
            )
        finally:
            del self._states[state.id]

    async def _recursive_execute(
        self,
        state: RecursionState,
        inputs: Dict[str, Any],
        recursive_inputs_fn: Callable
    ) -> Dict[str, Any]:
        """內部遞歸執行"""
        # 檢查記憶化
        if self.config.memoization:
            memo_key = self._generate_memo_key(inputs)
            if memo_key in state.memo:
                return state.memo[memo_key]

        # 檢查終止條件
        termination = self._check_termination(state, inputs)
        if termination:
            state.terminated = True
            state.termination_type = termination
            return self._build_termination_result(state, inputs, termination)

        # 執行當前層
        state.current_depth += 1
        state.iteration_count += 1

        result = await self.sub_executor.execute(
            sub_workflow_id=state.workflow_id,
            inputs=inputs,
            mode=SubWorkflowExecutionMode.SYNC
        )

        state.history.append({
            "depth": state.current_depth,
            "inputs": inputs,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })

        # 檢查是否需要繼續遞歸
        if self._should_continue(state, result):
            # 生成下一次輸入
            next_inputs = recursive_inputs_fn(result)

            # 根據策略執行
            if self.config.strategy == RecursionStrategy.DEPTH_FIRST:
                result = await self._recursive_execute(
                    state, next_inputs, recursive_inputs_fn
                )
            elif self.config.strategy == RecursionStrategy.PARALLEL:
                # 並行遞歸（如果有多個分支）
                if isinstance(next_inputs, list):
                    import asyncio
                    tasks = [
                        self._recursive_execute(state, inp, recursive_inputs_fn)
                        for inp in next_inputs
                    ]
                    results = await asyncio.gather(*tasks)
                    result = self._merge_results(results)
                else:
                    result = await self._recursive_execute(
                        state, next_inputs, recursive_inputs_fn
                    )

        # 記憶化結果
        if self.config.memoization:
            memo_key = self._generate_memo_key(inputs)
            state.memo[memo_key] = result

        state.current_depth -= 1
        return result

    def _check_termination(
        self,
        state: RecursionState,
        inputs: Dict[str, Any]
    ) -> Optional[TerminationType]:
        """檢查終止條件"""
        # 檢查最大深度
        if state.current_depth >= self.config.max_depth:
            return TerminationType.MAX_DEPTH

        # 檢查最大迭代
        if state.iteration_count >= self.config.max_iterations:
            return TerminationType.MAX_ITERATIONS

        # 檢查超時
        elapsed = (datetime.utcnow() - state.started_at).total_seconds()
        if elapsed >= self.config.timeout_seconds:
            return TerminationType.TIMEOUT

        # 檢查自定義條件
        if self.config.termination_condition:
            if self.config.termination_condition(inputs, state.current_depth):
                return TerminationType.CONDITION

        # 檢查收斂
        if self.config.convergence_threshold and len(state.history) >= 2:
            if self._check_convergence(state):
                return TerminationType.CONVERGENCE

        return None

    def _check_convergence(self, state: RecursionState) -> bool:
        """檢查結果是否收斂"""
        if len(state.history) < 2:
            return False

        last_result = state.history[-1].get("result", {})
        prev_result = state.history[-2].get("result", {})

        # 簡單的收斂檢查：比較結果的變化
        try:
            diff = self._calculate_diff(last_result, prev_result)
            return diff < self.config.convergence_threshold
        except:
            return False

    def _calculate_diff(
        self,
        result1: Dict[str, Any],
        result2: Dict[str, Any]
    ) -> float:
        """計算結果差異"""
        # 簡單實現：計算數值欄位的平均變化
        diffs = []
        for key in result1:
            if key in result2:
                val1 = result1[key]
                val2 = result2[key]
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    diffs.append(abs(val1 - val2))

        return sum(diffs) / len(diffs) if diffs else float('inf')

    def _should_continue(
        self,
        state: RecursionState,
        result: Dict[str, Any]
    ) -> bool:
        """判斷是否繼續遞歸"""
        if state.terminated:
            return False

        # 檢查結果中是否有繼續信號
        if result.get("continue_recursion") is False:
            return False

        return True

    def _generate_memo_key(self, inputs: Dict[str, Any]) -> str:
        """生成記憶化鍵"""
        import hashlib
        import json

        # 將輸入轉為可哈希的字串
        serialized = json.dumps(inputs, sort_keys=True, default=str)
        return hashlib.md5(serialized.encode()).hexdigest()

    def _build_termination_result(
        self,
        state: RecursionState,
        last_inputs: Dict[str, Any],
        termination_type: TerminationType
    ) -> Dict[str, Any]:
        """構建終止結果"""
        return {
            "status": "terminated",
            "termination_type": termination_type.value,
            "depth_reached": state.current_depth,
            "total_iterations": state.iteration_count,
            "last_inputs": last_inputs,
            "history_length": len(state.history)
        }

    def _merge_results(
        self,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """合併並行遞歸結果"""
        merged = {
            "branches": len(results),
            "results": results
        }

        # 嘗試合併數值欄位
        numeric_keys = set()
        for r in results:
            for k, v in r.items():
                if isinstance(v, (int, float)):
                    numeric_keys.add(k)

        for key in numeric_keys:
            values = [r.get(key) for r in results if key in r]
            if values:
                merged[f"{key}_sum"] = sum(values)
                merged[f"{key}_avg"] = sum(values) / len(values)

        return merged

    def get_recursion_stats(
        self,
        state_id: UUID
    ) -> Dict[str, Any]:
        """獲取遞歸統計"""
        state = self._states.get(state_id)
        if not state:
            return {"error": "State not found"}

        return {
            "id": str(state_id),
            "workflow_id": str(state.workflow_id),
            "current_depth": state.current_depth,
            "iteration_count": state.iteration_count,
            "history_length": len(state.history),
            "memo_size": len(state.memo),
            "terminated": state.terminated,
            "termination_type": state.termination_type.value if state.termination_type else None,
            "elapsed_seconds": (datetime.utcnow() - state.started_at).total_seconds()
        }
```

#### 驗收標準
- [ ] 支援多種遞歸策略
- [ ] 正確的終止條件檢測
- [ ] 記憶化功能
- [ ] 收斂檢測
- [ ] 遞歸統計

---

### Story 11-4: Workflow Composition Builder (5 點)

**作為** 系統架構師
**我希望** 實現工作流組合建構器
**以便** 可以靈活組合子工作流

#### 技術規格

```python
# backend/src/domain/orchestration/nested/composition_builder.py

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from uuid import UUID, uuid4
from enum import Enum


class CompositionType(str, Enum):
    """組合類型"""
    SEQUENCE = "sequence"       # 順序組合
    PARALLEL = "parallel"       # 並行組合
    CONDITIONAL = "conditional" # 條件組合
    LOOP = "loop"               # 迴圈組合
    SWITCH = "switch"           # 分支組合


@dataclass
class WorkflowNode:
    """工作流節點"""
    id: UUID
    workflow_id: Optional[UUID]  # 引用現有工作流
    inline_definition: Optional[Dict[str, Any]]  # 內聯定義
    name: str
    inputs_mapping: Dict[str, str] = field(default_factory=dict)
    outputs_mapping: Dict[str, str] = field(default_factory=dict)


@dataclass
class CompositionBlock:
    """組合塊"""
    id: UUID
    composition_type: CompositionType
    nodes: List[Union[WorkflowNode, "CompositionBlock"]]
    condition: Optional[str] = None  # 條件表達式
    loop_config: Optional[Dict[str, Any]] = None
    switch_cases: Optional[Dict[str, Any]] = None


class WorkflowCompositionBuilder:
    """
    工作流組合建構器

    提供流暢的 API 來組合子工作流
    """

    def __init__(self):
        self._root: Optional[CompositionBlock] = None
        self._current_block: Optional[CompositionBlock] = None
        self._block_stack: List[CompositionBlock] = []

    def sequence(self) -> "WorkflowCompositionBuilder":
        """開始順序組合"""
        block = CompositionBlock(
            id=uuid4(),
            composition_type=CompositionType.SEQUENCE,
            nodes=[]
        )
        self._push_block(block)
        return self

    def parallel(self) -> "WorkflowCompositionBuilder":
        """開始並行組合"""
        block = CompositionBlock(
            id=uuid4(),
            composition_type=CompositionType.PARALLEL,
            nodes=[]
        )
        self._push_block(block)
        return self

    def conditional(
        self,
        condition: str
    ) -> "WorkflowCompositionBuilder":
        """開始條件組合"""
        block = CompositionBlock(
            id=uuid4(),
            composition_type=CompositionType.CONDITIONAL,
            nodes=[],
            condition=condition
        )
        self._push_block(block)
        return self

    def loop(
        self,
        max_iterations: int = 10,
        condition: Optional[str] = None
    ) -> "WorkflowCompositionBuilder":
        """開始迴圈組合"""
        block = CompositionBlock(
            id=uuid4(),
            composition_type=CompositionType.LOOP,
            nodes=[],
            loop_config={
                "max_iterations": max_iterations,
                "condition": condition
            }
        )
        self._push_block(block)
        return self

    def switch(
        self,
        expression: str
    ) -> "WorkflowCompositionBuilder":
        """開始分支組合"""
        block = CompositionBlock(
            id=uuid4(),
            composition_type=CompositionType.SWITCH,
            nodes=[],
            switch_cases={"expression": expression, "cases": {}}
        )
        self._push_block(block)
        return self

    def case(
        self,
        value: Any
    ) -> "WorkflowCompositionBuilder":
        """添加 switch case"""
        if not self._current_block or self._current_block.composition_type != CompositionType.SWITCH:
            raise ValueError("case() must be called within switch()")

        self._current_block.switch_cases["cases"][value] = []
        return self

    def add_workflow(
        self,
        workflow_id: UUID,
        name: Optional[str] = None,
        inputs_mapping: Optional[Dict[str, str]] = None,
        outputs_mapping: Optional[Dict[str, str]] = None
    ) -> "WorkflowCompositionBuilder":
        """添加工作流引用"""
        node = WorkflowNode(
            id=uuid4(),
            workflow_id=workflow_id,
            inline_definition=None,
            name=name or f"workflow_{workflow_id}",
            inputs_mapping=inputs_mapping or {},
            outputs_mapping=outputs_mapping or {}
        )
        self._add_node(node)
        return self

    def add_inline(
        self,
        definition: Dict[str, Any],
        name: Optional[str] = None,
        inputs_mapping: Optional[Dict[str, str]] = None,
        outputs_mapping: Optional[Dict[str, str]] = None
    ) -> "WorkflowCompositionBuilder":
        """添加內聯工作流定義"""
        node = WorkflowNode(
            id=uuid4(),
            workflow_id=None,
            inline_definition=definition,
            name=name or f"inline_{uuid4().hex[:8]}",
            inputs_mapping=inputs_mapping or {},
            outputs_mapping=outputs_mapping or {}
        )
        self._add_node(node)
        return self

    def end(self) -> "WorkflowCompositionBuilder":
        """結束當前組合塊"""
        self._pop_block()
        return self

    def build(self) -> Dict[str, Any]:
        """構建最終的組合定義"""
        if not self._root:
            raise ValueError("No composition defined")

        return self._serialize_block(self._root)

    def _push_block(self, block: CompositionBlock) -> None:
        """壓入新的組合塊"""
        if self._current_block:
            self._current_block.nodes.append(block)
            self._block_stack.append(self._current_block)
        else:
            self._root = block

        self._current_block = block

    def _pop_block(self) -> None:
        """彈出當前組合塊"""
        if self._block_stack:
            self._current_block = self._block_stack.pop()
        else:
            self._current_block = None

    def _add_node(self, node: WorkflowNode) -> None:
        """添加節點到當前塊"""
        if not self._current_block:
            raise ValueError("No active composition block")

        if self._current_block.composition_type == CompositionType.SWITCH:
            # 添加到最後一個 case
            cases = self._current_block.switch_cases["cases"]
            if cases:
                last_case = list(cases.keys())[-1]
                cases[last_case].append(node)
        else:
            self._current_block.nodes.append(node)

    def _serialize_block(
        self,
        block: CompositionBlock
    ) -> Dict[str, Any]:
        """序列化組合塊"""
        serialized = {
            "id": str(block.id),
            "type": block.composition_type.value,
            "nodes": []
        }

        for node in block.nodes:
            if isinstance(node, CompositionBlock):
                serialized["nodes"].append(self._serialize_block(node))
            else:
                serialized["nodes"].append(self._serialize_node(node))

        if block.condition:
            serialized["condition"] = block.condition

        if block.loop_config:
            serialized["loop_config"] = block.loop_config

        if block.switch_cases:
            serialized["switch"] = block.switch_cases

        return serialized

    def _serialize_node(self, node: WorkflowNode) -> Dict[str, Any]:
        """序列化節點"""
        return {
            "id": str(node.id),
            "name": node.name,
            "workflow_id": str(node.workflow_id) if node.workflow_id else None,
            "inline_definition": node.inline_definition,
            "inputs_mapping": node.inputs_mapping,
            "outputs_mapping": node.outputs_mapping
        }


# 使用範例
def create_complex_workflow():
    """建立複雜的組合工作流範例"""
    builder = WorkflowCompositionBuilder()

    composition = (
        builder
        .sequence()
            .add_workflow(
                workflow_id=uuid4(),
                name="data_preparation",
                inputs_mapping={"raw_data": "input_data"}
            )
            .parallel()
                .add_workflow(
                    workflow_id=uuid4(),
                    name="process_branch_a"
                )
                .add_workflow(
                    workflow_id=uuid4(),
                    name="process_branch_b"
                )
            .end()  # end parallel
            .conditional("result.status == 'success'")
                .add_workflow(
                    workflow_id=uuid4(),
                    name="success_handler"
                )
            .end()  # end conditional
            .loop(max_iterations=5, condition="not converged")
                .add_workflow(
                    workflow_id=uuid4(),
                    name="refinement_step"
                )
            .end()  # end loop
        .end()  # end sequence
        .build()
    )

    return composition
```

#### 驗收標準
- [ ] 流暢的 API 設計
- [ ] 支援所有組合類型
- [ ] 正確的嵌套結構
- [ ] 序列化功能
- [ ] 使用範例完整

---

### Story 11-5: Nested Workflow API (8 點)

**作為** 前端開發者
**我希望** 有完整的嵌套工作流 API
**以便** 在 UI 中管理和監控嵌套執行

#### 技術規格

```python
# backend/src/api/v1/nested/routes.py

from fastapi import APIRouter, Depends, HTTPException, WebSocket
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime

router = APIRouter(prefix="/nested", tags=["Nested Workflows"])


# ============ Schemas ============

class SubWorkflowRequest(BaseModel):
    """子工作流請求"""
    parent_workflow_id: UUID
    workflow_id: Optional[UUID] = None
    inline_definition: Optional[dict] = None
    config: dict = Field(default_factory=dict)
    input_mapping: dict = Field(default_factory=dict)
    output_mapping: dict = Field(default_factory=dict)
    position: int = 0


class ExecuteNestedRequest(BaseModel):
    """執行嵌套工作流請求"""
    sub_workflow_id: UUID
    inputs: dict = Field(default_factory=dict)
    mode: str = "sync"  # sync, async, fire_and_forget, callback


class CompositionRequest(BaseModel):
    """組合請求"""
    name: str
    definition: dict


class RecursiveExecuteRequest(BaseModel):
    """遞歸執行請求"""
    workflow_id: UUID
    initial_inputs: dict
    max_depth: int = 10
    max_iterations: int = 100
    termination_condition: Optional[str] = None


class NestedExecutionResponse(BaseModel):
    """嵌套執行回應"""
    execution_id: str
    parent_execution_id: Optional[str]
    workflow_id: str
    depth: int
    status: str
    started_at: datetime


class ExecutionTreeResponse(BaseModel):
    """執行樹回應"""
    id: str
    workflow_id: str
    depth: int
    status: str
    children: List["ExecutionTreeResponse"] = []

ExecutionTreeResponse.model_rebuild()


# ============ Routes ============

@router.post("/sub-workflows")
async def register_sub_workflow(
    request: SubWorkflowRequest,
    manager: NestedWorkflowManager = Depends(get_nested_manager)
):
    """
    註冊子工作流

    將子工作流與父工作流關聯
    """
    sub_workflow = SubWorkflowReference(
        id=uuid4(),
        parent_workflow_id=request.parent_workflow_id,
        workflow_id=request.workflow_id,
        definition=request.inline_definition,
        config=NestedWorkflowConfig(**request.config),
        input_mapping=request.input_mapping,
        output_mapping=request.output_mapping,
        position=request.position
    )

    try:
        await manager.register_sub_workflow(
            parent_workflow_id=request.parent_workflow_id,
            sub_workflow=sub_workflow
        )

        return {
            "sub_workflow_id": str(sub_workflow.id),
            "parent_workflow_id": str(request.parent_workflow_id),
            "status": "registered"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/execute", response_model=dict)
async def execute_nested_workflow(
    request: ExecuteNestedRequest,
    executor: SubWorkflowExecutor = Depends(get_sub_executor)
):
    """
    執行嵌套工作流
    """
    from src.domain.orchestration.nested.sub_executor import SubWorkflowExecutionMode

    mode = SubWorkflowExecutionMode(request.mode)

    try:
        result = await executor.execute(
            sub_workflow_id=request.sub_workflow_id,
            inputs=request.inputs,
            mode=mode
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions/{execution_id}/status")
async def get_execution_status(
    execution_id: UUID,
    executor: SubWorkflowExecutor = Depends(get_sub_executor)
):
    """獲取執行狀態"""
    return await executor.get_execution_status(execution_id)


@router.post("/executions/{execution_id}/wait")
async def wait_for_execution(
    execution_id: UUID,
    timeout: Optional[float] = None,
    executor: SubWorkflowExecutor = Depends(get_sub_executor)
):
    """等待執行完成"""
    return await executor.wait_for_completion(execution_id, timeout)


@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(
    execution_id: UUID,
    cascade: bool = True,
    manager: NestedWorkflowManager = Depends(get_nested_manager)
):
    """取消執行"""
    await manager.cancel_nested_execution(execution_id, cascade)
    return {"status": "cancelled", "execution_id": str(execution_id)}


@router.get("/executions/{execution_id}/tree", response_model=ExecutionTreeResponse)
async def get_execution_tree(
    execution_id: UUID,
    manager: NestedWorkflowManager = Depends(get_nested_manager)
):
    """獲取執行樹"""
    tree = manager.get_execution_tree(execution_id)
    return ExecutionTreeResponse(**tree)


@router.post("/execute/parallel")
async def execute_parallel(
    sub_workflows: List[dict],
    executor: SubWorkflowExecutor = Depends(get_sub_executor)
):
    """並行執行多個子工作流"""
    results = await executor.execute_parallel(sub_workflows)
    return {"results": results}


@router.post("/execute/sequential")
async def execute_sequential(
    sub_workflows: List[dict],
    pass_outputs: bool = True,
    executor: SubWorkflowExecutor = Depends(get_sub_executor)
):
    """順序執行多個子工作流"""
    results = await executor.execute_sequential(sub_workflows, pass_outputs)
    return {"results": results}


@router.post("/execute/recursive")
async def execute_recursive(
    request: RecursiveExecuteRequest,
    handler: RecursivePatternHandler = Depends(get_recursive_handler)
):
    """
    執行遞歸工作流
    """
    # 簡單的遞歸輸入生成函數
    def recursive_inputs_fn(result: Dict[str, Any]) -> Dict[str, Any]:
        # 可以根據實際需求自定義
        return {**result, "iteration": result.get("iteration", 0) + 1}

    try:
        result = await handler.execute_recursive(
            workflow_id=request.workflow_id,
            initial_inputs=request.initial_inputs,
            recursive_inputs_fn=recursive_inputs_fn
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recursive/{state_id}/stats")
async def get_recursion_stats(
    state_id: UUID,
    handler: RecursivePatternHandler = Depends(get_recursive_handler)
):
    """獲取遞歸統計"""
    return handler.get_recursion_stats(state_id)


@router.post("/compositions")
async def create_composition(
    request: CompositionRequest,
    composition_service: Any = Depends(get_composition_service)
):
    """
    建立工作流組合
    """
    composition_id = await composition_service.create(
        name=request.name,
        definition=request.definition
    )

    return {
        "composition_id": str(composition_id),
        "name": request.name,
        "status": "created"
    }


@router.get("/compositions/{composition_id}")
async def get_composition(
    composition_id: UUID,
    composition_service: Any = Depends(get_composition_service)
):
    """獲取組合詳情"""
    composition = await composition_service.get(composition_id)
    if not composition:
        raise HTTPException(status_code=404, detail="Composition not found")
    return composition


@router.post("/compositions/{composition_id}/execute")
async def execute_composition(
    composition_id: UUID,
    inputs: dict,
    composition_service: Any = Depends(get_composition_service)
):
    """執行組合工作流"""
    result = await composition_service.execute(
        composition_id=composition_id,
        inputs=inputs
    )
    return result


@router.websocket("/executions/{execution_id}/ws")
async def execution_websocket(
    websocket: WebSocket,
    execution_id: UUID,
    manager: NestedWorkflowManager = Depends(get_nested_manager)
):
    """
    WebSocket 監控嵌套執行

    實時獲取執行狀態更新
    """
    await websocket.accept()

    try:
        while True:
            # 發送當前執行樹
            tree = manager.get_execution_tree(execution_id)
            await websocket.send_json({
                "type": "tree_update",
                "data": tree
            })

            # 等待一段時間再更新
            import asyncio
            await asyncio.sleep(1)

            # 檢查是否完成
            if tree.get("status") in ["completed", "failed", "cancelled"]:
                await websocket.send_json({
                    "type": "execution_complete",
                    "data": tree
                })
                break

    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        await websocket.close()
```

#### 驗收標準
- [ ] 完整的 CRUD API
- [ ] 支援並行/順序/遞歸執行
- [ ] 執行樹視覺化
- [ ] WebSocket 實時監控
- [ ] API 文檔完整

---

## 測試計劃

### 單元測試

```python
# tests/unit/test_nested_workflow.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.domain.orchestration.nested.workflow_manager import (
    NestedWorkflowManager,
    NestedWorkflowConfig,
    NestedWorkflowType,
    WorkflowScope,
    SubWorkflowReference
)


@pytest.fixture
def nested_manager():
    return NestedWorkflowManager(
        workflow_service=MagicMock(),
        execution_service=MagicMock(),
        max_global_depth=10
    )


def test_cycle_detection(nested_manager):
    """測試循環依賴檢測"""
    wf_a = uuid4()
    wf_b = uuid4()
    wf_c = uuid4()

    # A -> B -> C -> A (循環)
    nested_manager._dependency_graph[wf_a] = {wf_b}
    nested_manager._dependency_graph[wf_b] = {wf_c}
    nested_manager._dependency_graph[wf_c] = {wf_a}

    assert nested_manager._has_cycle(wf_a) is True


def test_no_cycle(nested_manager):
    """測試無循環情況"""
    wf_a = uuid4()
    wf_b = uuid4()
    wf_c = uuid4()

    # A -> B -> C (無循環)
    nested_manager._dependency_graph[wf_a] = {wf_b}
    nested_manager._dependency_graph[wf_b] = {wf_c}
    nested_manager._dependency_graph[wf_c] = set()

    assert nested_manager._has_cycle(wf_a) is False


@pytest.mark.asyncio
async def test_depth_limit(nested_manager):
    """測試深度限制"""
    parent_context = MagicMock()
    parent_context.depth = 5
    parent_context.path = [uuid4() for _ in range(5)]
    parent_context.variables = {}

    sub_workflow = SubWorkflowReference(
        id=uuid4(),
        parent_workflow_id=uuid4(),
        workflow_id=uuid4(),
        definition=None,
        config=NestedWorkflowConfig(max_depth=5),
        input_mapping={},
        output_mapping={},
        position=0
    )

    with pytest.raises(ValueError, match="depth"):
        await nested_manager.execute_sub_workflow(
            parent_context,
            sub_workflow
        )


# tests/unit/test_recursive_handler.py

@pytest.mark.asyncio
async def test_recursive_termination():
    """測試遞歸終止"""
    executor = MagicMock()
    executor.execute = AsyncMock(return_value={"value": 100})

    handler = RecursivePatternHandler(
        sub_executor=executor,
        config=RecursionConfig(
            max_depth=3,
            termination_condition=lambda inputs, depth: depth >= 3
        )
    )

    result = await handler.execute_recursive(
        workflow_id=uuid4(),
        initial_inputs={"value": 0},
        recursive_inputs_fn=lambda r: {"value": r["value"] + 1}
    )

    assert result["status"] == "terminated"
    assert result["termination_type"] == "max_depth"


@pytest.mark.asyncio
async def test_memoization():
    """測試記憶化"""
    executor = MagicMock()
    call_count = 0

    async def execute_fn(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return {"result": "computed"}

    executor.execute = execute_fn

    handler = RecursivePatternHandler(
        sub_executor=executor,
        config=RecursionConfig(memoization=True, max_iterations=10)
    )

    # 執行兩次相同輸入
    await handler._recursive_execute(
        state=RecursionState(
            id=uuid4(),
            workflow_id=uuid4(),
            current_depth=0,
            iteration_count=0
        ),
        inputs={"same": "input"},
        recursive_inputs_fn=lambda r: r
    )

    # 由於終止條件，應該只執行一次
    assert call_count >= 1
```

### 整合測試

```python
# tests/integration/test_nested_api.py

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_and_execute_sub_workflow(client: AsyncClient, test_workflows):
    """測試註冊和執行子工作流"""
    parent_wf = test_workflows[0]
    child_wf = test_workflows[1]

    # 註冊子工作流
    response = await client.post(
        "/api/v1/nested/sub-workflows",
        json={
            "parent_workflow_id": str(parent_wf.id),
            "workflow_id": str(child_wf.id),
            "config": {"max_depth": 5},
            "input_mapping": {"parent_data": "child_input"},
            "output_mapping": {"child_result": "parent_result"}
        }
    )
    assert response.status_code == 200
    sub_wf_id = response.json()["sub_workflow_id"]

    # 執行
    response = await client.post(
        "/api/v1/nested/execute",
        json={
            "sub_workflow_id": sub_wf_id,
            "inputs": {"parent_data": "test_value"},
            "mode": "sync"
        }
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_parallel_execution(client: AsyncClient, test_workflows):
    """測試並行執行"""
    response = await client.post(
        "/api/v1/nested/execute/parallel",
        json=[
            {"id": str(test_workflows[0].id), "inputs": {"x": 1}},
            {"id": str(test_workflows[1].id), "inputs": {"x": 2}}
        ]
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 2
```

---

## 資料庫遷移

```sql
-- migrations/versions/011_nested_workflow_tables.sql

-- 子工作流引用表
CREATE TABLE sub_workflow_references (
    id UUID PRIMARY KEY,
    parent_workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    workflow_id UUID REFERENCES workflows(id),
    definition JSONB,
    config JSONB NOT NULL DEFAULT '{}',
    input_mapping JSONB DEFAULT '{}',
    output_mapping JSONB DEFAULT '{}',
    position INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 嵌套執行記錄表
CREATE TABLE nested_executions (
    id UUID PRIMARY KEY,
    parent_execution_id UUID REFERENCES nested_executions(id),
    workflow_id UUID NOT NULL,
    depth INTEGER NOT NULL DEFAULT 0,
    path UUID[] DEFAULT '{}',
    variables JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

-- 遞歸狀態表
CREATE TABLE recursion_states (
    id UUID PRIMARY KEY,
    workflow_id UUID NOT NULL,
    current_depth INTEGER DEFAULT 0,
    iteration_count INTEGER DEFAULT 0,
    history JSONB DEFAULT '[]',
    memo JSONB DEFAULT '{}',
    terminated BOOLEAN DEFAULT false,
    termination_type VARCHAR(50),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- 工作流組合表
CREATE TABLE workflow_compositions (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    definition JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_sub_wf_parent ON sub_workflow_references(parent_workflow_id);
CREATE INDEX idx_nested_exec_parent ON nested_executions(parent_execution_id);
CREATE INDEX idx_nested_exec_workflow ON nested_executions(workflow_id);
CREATE INDEX idx_recursion_workflow ON recursion_states(workflow_id);
```

---

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 無限遞歸 | 高 | 強制深度限制、迭代上限 |
| 記憶體爆發 | 高 | 限制歷史記錄大小、定期清理 |
| 循環依賴 | 中 | 依賴圖檢測 |
| 上下文污染 | 中 | 作用域隔離機制 |
| 執行追蹤困難 | 低 | 完整的執行樹和日誌 |

---

## Definition of Done

- [ ] 所有 User Stories 完成
- [ ] 單元測試覆蓋率 > 85%
- [ ] 整合測試通過
- [ ] API 文檔更新
- [ ] 資料庫遷移腳本準備完成
- [ ] 程式碼審查完成
- [ ] 效能測試通過（10 層嵌套 < 30秒）

---

**下一步**: [Sprint 12 - 整合與優化](./sprint-12-plan.md)
