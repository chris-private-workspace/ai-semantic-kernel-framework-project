# Sprint 10: 動態規劃引擎 (Dynamic Planning & Autonomous Decision)

**Sprint 目標**: 實現自主規劃和決策能力，讓 Agent 能夠動態分解任務並自主決策

**週期**: Week 21-22 (2 週)
**Story Points**: 42 點
**前置條件**: Sprint 7-9 完成

---

## Sprint 概述

### 核心交付物

| ID | 功能 | 優先級 | Story Points | 狀態 |
|----|------|--------|--------------|------|
| P2-F8 | Dynamic Planning 動態規劃 | 🟡 中 | 21 | 待開發 |
| P2-F9 | Autonomous Decision 自主決策 | 🟡 中 | 13 | 待開發 |
| P2-F10 | Trial-and-Error 試錯機制 | 🟢 低 | 8 | 待開發 |

### 與 Microsoft Agent Framework 對照

```python
# Microsoft Agent Framework 自主規劃概念
# 參考 AutoGen 的 AssistantAgent 自主能力

from autogen import AssistantAgent, UserProxyAgent

# 具有規劃能力的 Agent
planner_agent = AssistantAgent(
    name="Planner",
    system_message="""
    You are a planning agent. Your job is to:
    1. Analyze the task
    2. Break it down into subtasks
    3. Assign subtasks to appropriate agents
    4. Monitor progress and adjust plan as needed
    """,
    llm_config={"model": "gpt-4"}
)

# 具有執行和反饋能力的 Agent
executor_agent = AssistantAgent(
    name="Executor",
    system_message="You execute tasks and report results.",
    llm_config={"model": "gpt-4"}
)
```

---

## User Stories

### Story 10-1: Task Decomposer 任務分解器 (8 點)

**作為** 系統架構師
**我希望** 實現智能任務分解
**以便** 複雜任務可以被自動拆解為可執行的子任務

#### 技術規格

```python
# backend/src/domain/orchestration/planning/task_decomposer.py

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from enum import Enum
from datetime import datetime


class TaskPriority(str, Enum):
    """任務優先級"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, Enum):
    """任務狀態"""
    PENDING = "pending"
    READY = "ready"         # 依賴滿足，可執行
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"     # 依賴未滿足


class DependencyType(str, Enum):
    """依賴類型"""
    FINISH_TO_START = "finish_to_start"   # 前置任務完成後開始
    START_TO_START = "start_to_start"     # 前置任務開始後開始
    FINISH_TO_FINISH = "finish_to_finish" # 前置任務完成時完成
    DATA_DEPENDENCY = "data_dependency"    # 需要前置任務的數據


@dataclass
class SubTask:
    """子任務"""
    id: UUID
    parent_task_id: UUID
    name: str
    description: str
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent_id: Optional[str] = None
    dependencies: List[UUID] = field(default_factory=list)
    dependency_type: DependencyType = DependencyType.FINISH_TO_START
    estimated_duration_minutes: int = 0
    actual_duration_minutes: Optional[int] = None
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "parent_task_id": str(self.parent_task_id),
            "name": self.name,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "assigned_agent_id": self.assigned_agent_id,
            "dependencies": [str(d) for d in self.dependencies],
            "dependency_type": self.dependency_type.value,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "metadata": self.metadata
        }


@dataclass
class DecompositionResult:
    """分解結果"""
    task_id: UUID
    original_task: str
    subtasks: List[SubTask]
    execution_order: List[List[UUID]]  # 分層執行順序
    estimated_total_duration: int
    confidence_score: float  # 分解信心分數 0-1
    decomposition_strategy: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskDecomposer:
    """
    任務分解器

    使用 LLM 智能分解複雜任務為可執行的子任務
    """

    def __init__(
        self,
        llm_service: Any,
        agent_registry: Any,
        max_subtasks: int = 20,
        max_depth: int = 3
    ):
        self.llm_service = llm_service
        self.agent_registry = agent_registry
        self.max_subtasks = max_subtasks
        self.max_depth = max_depth

        # 分解策略
        self._strategies = {
            "hierarchical": self._decompose_hierarchical,
            "sequential": self._decompose_sequential,
            "parallel": self._decompose_parallel,
            "hybrid": self._decompose_hybrid
        }

    async def decompose(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
        strategy: str = "hybrid"
    ) -> DecompositionResult:
        """
        分解任務

        Args:
            task_description: 任務描述
            context: 上下文信息
            strategy: 分解策略

        Returns:
            分解結果
        """
        task_id = uuid4()

        # 選擇分解策略
        decompose_fn = self._strategies.get(strategy, self._decompose_hybrid)

        # 執行分解
        subtasks = await decompose_fn(task_id, task_description, context)

        # 分析依賴關係
        execution_order = self._analyze_execution_order(subtasks)

        # 估算總時間
        total_duration = self._estimate_total_duration(subtasks, execution_order)

        # 計算信心分數
        confidence = await self._calculate_confidence(task_description, subtasks)

        return DecompositionResult(
            task_id=task_id,
            original_task=task_description,
            subtasks=subtasks,
            execution_order=execution_order,
            estimated_total_duration=total_duration,
            confidence_score=confidence,
            decomposition_strategy=strategy,
            metadata={"context": context} if context else {}
        )

    async def _decompose_hierarchical(
        self,
        task_id: UUID,
        task_description: str,
        context: Optional[Dict[str, Any]]
    ) -> List[SubTask]:
        """階層式分解"""
        prompt = self._build_decomposition_prompt(
            task_description,
            context,
            approach="hierarchical"
        )

        response = await self.llm_service.generate(
            prompt=prompt,
            max_tokens=2000
        )

        return self._parse_decomposition_response(task_id, response)

    async def _decompose_sequential(
        self,
        task_id: UUID,
        task_description: str,
        context: Optional[Dict[str, Any]]
    ) -> List[SubTask]:
        """順序式分解"""
        prompt = self._build_decomposition_prompt(
            task_description,
            context,
            approach="sequential"
        )

        response = await self.llm_service.generate(
            prompt=prompt,
            max_tokens=2000
        )

        subtasks = self._parse_decomposition_response(task_id, response)

        # 設置順序依賴
        for i in range(1, len(subtasks)):
            subtasks[i].dependencies = [subtasks[i-1].id]

        return subtasks

    async def _decompose_parallel(
        self,
        task_id: UUID,
        task_description: str,
        context: Optional[Dict[str, Any]]
    ) -> List[SubTask]:
        """並行式分解"""
        prompt = self._build_decomposition_prompt(
            task_description,
            context,
            approach="parallel"
        )

        response = await self.llm_service.generate(
            prompt=prompt,
            max_tokens=2000
        )

        subtasks = self._parse_decomposition_response(task_id, response)

        # 並行任務沒有相互依賴
        return subtasks

    async def _decompose_hybrid(
        self,
        task_id: UUID,
        task_description: str,
        context: Optional[Dict[str, Any]]
    ) -> List[SubTask]:
        """
        混合式分解

        結合階層和並行，智能識別可並行的任務
        """
        prompt = f"""
        分析以下任務並將其分解為子任務。識別哪些任務可以並行執行，哪些必須順序執行。

        任務: {task_description}

        上下文: {context if context else "無額外上下文"}

        請以 JSON 格式返回分解結果：
        {{
            "subtasks": [
                {{
                    "name": "子任務名稱",
                    "description": "詳細描述",
                    "priority": "high/medium/low",
                    "dependencies": ["依賴的子任務名稱"],
                    "estimated_minutes": 30,
                    "required_capabilities": ["capability1", "capability2"]
                }}
            ],
            "reasoning": "分解理由"
        }}

        注意事項：
        1. 子任務數量應在 3-{self.max_subtasks} 之間
        2. 識別真正的依賴關係，避免過度串行化
        3. 考慮任務的原子性和可測試性
        4. 優先級應基於業務影響和依賴關係
        """

        response = await self.llm_service.generate(
            prompt=prompt,
            max_tokens=3000
        )

        return self._parse_decomposition_response(task_id, response)

    def _build_decomposition_prompt(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]],
        approach: str
    ) -> str:
        """構建分解提示"""
        approach_instructions = {
            "hierarchical": "使用階層式方法，先分解為主要階段，再細分每個階段",
            "sequential": "按執行順序分解，每個步驟依賴前一個步驟",
            "parallel": "識別可以同時執行的獨立任務"
        }

        return f"""
        任務分解請求:

        任務描述: {task_description}
        分解方法: {approach_instructions.get(approach, "")}
        上下文: {context if context else "無"}

        請返回 JSON 格式的子任務列表。
        """

    def _parse_decomposition_response(
        self,
        task_id: UUID,
        response: str
    ) -> List[SubTask]:
        """解析 LLM 的分解回應"""
        import json

        try:
            data = json.loads(response)
            subtasks_data = data.get("subtasks", [])
        except json.JSONDecodeError:
            # 嘗試從文本中提取
            subtasks_data = self._extract_tasks_from_text(response)

        subtasks = []
        name_to_id = {}

        for task_data in subtasks_data[:self.max_subtasks]:
            subtask_id = uuid4()
            name = task_data.get("name", f"Subtask {len(subtasks) + 1}")
            name_to_id[name] = subtask_id

            subtask = SubTask(
                id=subtask_id,
                parent_task_id=task_id,
                name=name,
                description=task_data.get("description", ""),
                priority=TaskPriority(task_data.get("priority", "medium")),
                estimated_duration_minutes=task_data.get("estimated_minutes", 30),
                metadata={
                    "required_capabilities": task_data.get("required_capabilities", [])
                }
            )
            subtasks.append(subtask)

        # 解析依賴關係
        for i, task_data in enumerate(subtasks_data[:self.max_subtasks]):
            dep_names = task_data.get("dependencies", [])
            subtasks[i].dependencies = [
                name_to_id[name] for name in dep_names
                if name in name_to_id
            ]

        return subtasks

    def _extract_tasks_from_text(self, text: str) -> List[Dict[str, Any]]:
        """從純文本中提取任務"""
        tasks = []
        lines = text.strip().split('\n')

        for line in lines:
            if line.strip() and (line.startswith('-') or line.startswith('*') or line[0].isdigit()):
                task_text = line.lstrip('-*0123456789. ')
                tasks.append({
                    "name": task_text[:50],
                    "description": task_text,
                    "priority": "medium"
                })

        return tasks

    def _analyze_execution_order(
        self,
        subtasks: List[SubTask]
    ) -> List[List[UUID]]:
        """
        分析執行順序

        使用拓撲排序確定執行層級

        Returns:
            分層的任務 ID 列表，同一層可並行執行
        """
        # 建立任務索引
        task_index = {task.id: task for task in subtasks}

        # 計算入度
        in_degree = {task.id: 0 for task in subtasks}
        for task in subtasks:
            for dep_id in task.dependencies:
                if dep_id in in_degree:
                    in_degree[task.id] += 1

        # 拓撲排序
        execution_order = []
        remaining = set(in_degree.keys())

        while remaining:
            # 找出入度為 0 的任務（可並行執行）
            ready = [
                task_id for task_id in remaining
                if in_degree[task_id] == 0
            ]

            if not ready:
                # 存在循環依賴，打破循環
                ready = [min(remaining)]

            execution_order.append(ready)

            # 更新入度
            for task_id in ready:
                remaining.remove(task_id)
                task = task_index[task_id]
                for other_task in subtasks:
                    if task_id in other_task.dependencies:
                        in_degree[other_task.id] -= 1

        return execution_order

    def _estimate_total_duration(
        self,
        subtasks: List[SubTask],
        execution_order: List[List[UUID]]
    ) -> int:
        """
        估算總執行時間

        考慮並行執行的任務
        """
        task_index = {task.id: task for task in subtasks}
        total = 0

        for layer in execution_order:
            # 每層取最長的任務時間（並行執行）
            layer_max = max(
                task_index[task_id].estimated_duration_minutes
                for task_id in layer
            ) if layer else 0
            total += layer_max

        return total

    async def _calculate_confidence(
        self,
        original_task: str,
        subtasks: List[SubTask]
    ) -> float:
        """計算分解信心分數"""
        # 基於多個因素評估信心
        factors = []

        # 1. 子任務數量合理性
        task_count = len(subtasks)
        if 3 <= task_count <= 10:
            factors.append(1.0)
        elif 2 <= task_count <= 15:
            factors.append(0.8)
        else:
            factors.append(0.5)

        # 2. 描述完整性
        described = sum(1 for t in subtasks if len(t.description) > 20)
        factors.append(described / len(subtasks) if subtasks else 0)

        # 3. 依賴關係合理性（無孤立任務）
        has_deps = sum(1 for t in subtasks if t.dependencies)
        if len(subtasks) > 1:
            factors.append(min(has_deps / (len(subtasks) - 1), 1.0))
        else:
            factors.append(1.0)

        return sum(factors) / len(factors)

    async def refine_decomposition(
        self,
        result: DecompositionResult,
        feedback: str
    ) -> DecompositionResult:
        """
        根據反饋精煉分解結果

        Args:
            result: 原始分解結果
            feedback: 改進反饋

        Returns:
            精煉後的分解結果
        """
        prompt = f"""
        原始任務: {result.original_task}

        當前分解:
        {[t.to_dict() for t in result.subtasks]}

        反饋: {feedback}

        請根據反饋改進任務分解。返回更新後的 JSON 格式子任務列表。
        """

        response = await self.llm_service.generate(
            prompt=prompt,
            max_tokens=3000
        )

        new_subtasks = self._parse_decomposition_response(result.task_id, response)
        new_execution_order = self._analyze_execution_order(new_subtasks)

        return DecompositionResult(
            task_id=result.task_id,
            original_task=result.original_task,
            subtasks=new_subtasks,
            execution_order=new_execution_order,
            estimated_total_duration=self._estimate_total_duration(new_subtasks, new_execution_order),
            confidence_score=await self._calculate_confidence(result.original_task, new_subtasks),
            decomposition_strategy=result.decomposition_strategy,
            metadata={**result.metadata, "refined": True, "feedback": feedback}
        )
```

#### 驗收標準
- [ ] 支援 4 種分解策略
- [ ] 正確識別任務依賴
- [ ] 計算合理的執行順序
- [ ] 信心分數準確反映分解質量
- [ ] 單元測試覆蓋率 > 85%

---

### Story 10-2: Dynamic Planner 動態規劃器 (8 點)

**作為** 系統架構師
**我希望** 實現動態規劃引擎
**以便** 根據執行情況實時調整計劃

#### 技術規格

```python
# backend/src/domain/orchestration/planning/dynamic_planner.py

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
import asyncio


class PlanStatus(str, Enum):
    """計劃狀態"""
    DRAFT = "draft"
    APPROVED = "approved"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    REPLANNING = "replanning"


class PlanEvent(str, Enum):
    """計劃事件"""
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    RESOURCE_UNAVAILABLE = "resource_unavailable"
    NEW_INFORMATION = "new_information"
    USER_INTERVENTION = "user_intervention"
    DEADLINE_APPROACHING = "deadline_approaching"


@dataclass
class PlanAdjustment:
    """計劃調整"""
    id: UUID
    plan_id: UUID
    trigger_event: PlanEvent
    original_state: Dict[str, Any]
    new_state: Dict[str, Any]
    reason: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    approved: bool = False
    approved_by: Optional[str] = None


@dataclass
class ExecutionPlan:
    """執行計劃"""
    id: UUID
    name: str
    description: str
    goal: str
    decomposition: "DecompositionResult"
    status: PlanStatus = PlanStatus.DRAFT
    current_phase: int = 0
    progress_percentage: float = 0.0
    adjustments: List[PlanAdjustment] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DynamicPlanner:
    """
    動態規劃器

    負責：
    - 建立執行計劃
    - 監控執行進度
    - 根據情況動態調整計劃
    - 處理異常和重新規劃
    """

    def __init__(
        self,
        task_decomposer: "TaskDecomposer",
        decision_engine: "AutonomousDecisionEngine",
        llm_service: Any,
        require_approval_for_changes: bool = True
    ):
        self.decomposer = task_decomposer
        self.decision_engine = decision_engine
        self.llm_service = llm_service
        self.require_approval = require_approval_for_changes

        # 計劃存儲
        self._plans: Dict[UUID, ExecutionPlan] = {}

        # 事件處理器
        self._event_handlers: Dict[PlanEvent, List[Callable]] = {
            event: [] for event in PlanEvent
        }

        # 監控任務
        self._monitoring_tasks: Dict[UUID, asyncio.Task] = {}

    async def create_plan(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
        deadline: Optional[datetime] = None
    ) -> ExecutionPlan:
        """
        建立執行計劃

        Args:
            goal: 目標描述
            context: 上下文信息
            deadline: 截止時間

        Returns:
            執行計劃
        """
        # 分解任務
        decomposition = await self.decomposer.decompose(
            task_description=goal,
            context=context,
            strategy="hybrid"
        )

        plan = ExecutionPlan(
            id=uuid4(),
            name=f"Plan for: {goal[:50]}...",
            description=goal,
            goal=goal,
            decomposition=decomposition,
            deadline=deadline
        )

        self._plans[plan.id] = plan
        return plan

    async def approve_plan(self, plan_id: UUID, approver: str) -> None:
        """批准計劃"""
        plan = self._plans.get(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        plan.status = PlanStatus.APPROVED
        plan.metadata["approved_by"] = approver
        plan.metadata["approved_at"] = datetime.utcnow().isoformat()

    async def execute_plan(
        self,
        plan_id: UUID,
        execution_callback: Callable[[SubTask], Any]
    ) -> Dict[str, Any]:
        """
        執行計劃

        Args:
            plan_id: 計劃 ID
            execution_callback: 執行子任務的回調函數

        Returns:
            執行結果
        """
        plan = self._plans.get(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        if plan.status not in [PlanStatus.APPROVED, PlanStatus.PAUSED]:
            raise ValueError(f"Plan is not in executable state: {plan.status}")

        plan.status = PlanStatus.EXECUTING
        plan.started_at = plan.started_at or datetime.utcnow()

        # 啟動監控
        self._start_monitoring(plan_id)

        results = []
        execution_order = plan.decomposition.execution_order

        try:
            for phase_index, phase_tasks in enumerate(execution_order):
                plan.current_phase = phase_index

                # 並行執行同一層級的任務
                phase_results = await self._execute_phase(
                    plan=plan,
                    task_ids=phase_tasks,
                    callback=execution_callback
                )
                results.extend(phase_results)

                # 更新進度
                completed_count = sum(
                    1 for t in plan.decomposition.subtasks
                    if t.status == TaskStatus.COMPLETED
                )
                plan.progress_percentage = (
                    completed_count / len(plan.decomposition.subtasks) * 100
                )

                # 檢查是否需要重新規劃
                if await self._should_replan(plan, phase_results):
                    await self._replan(plan, phase_results)

            plan.status = PlanStatus.COMPLETED
            plan.completed_at = datetime.utcnow()

        except Exception as e:
            plan.status = PlanStatus.FAILED
            plan.metadata["failure_reason"] = str(e)
            raise

        finally:
            self._stop_monitoring(plan_id)

        return {
            "plan_id": str(plan_id),
            "status": plan.status.value,
            "results": results,
            "adjustments_made": len(plan.adjustments)
        }

    async def _execute_phase(
        self,
        plan: ExecutionPlan,
        task_ids: List[UUID],
        callback: Callable
    ) -> List[Dict[str, Any]]:
        """執行一個階段的任務"""
        task_index = {t.id: t for t in plan.decomposition.subtasks}

        async def execute_single_task(task_id: UUID):
            task = task_index[task_id]
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.utcnow()

            await self._emit_event(PlanEvent.TASK_STARTED, plan, task)

            try:
                result = await callback(task)
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                task.outputs = result if isinstance(result, dict) else {"result": result}

                await self._emit_event(PlanEvent.TASK_COMPLETED, plan, task)

                return {"task_id": str(task_id), "status": "completed", "result": result}

            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)

                await self._emit_event(PlanEvent.TASK_FAILED, plan, task)

                return {"task_id": str(task_id), "status": "failed", "error": str(e)}

        # 並行執行
        tasks = [execute_single_task(tid) for tid in task_ids]
        return await asyncio.gather(*tasks)

    async def _should_replan(
        self,
        plan: ExecutionPlan,
        phase_results: List[Dict[str, Any]]
    ) -> bool:
        """判斷是否需要重新規劃"""
        # 檢查失敗任務
        failed_tasks = [r for r in phase_results if r["status"] == "failed"]
        if len(failed_tasks) > len(phase_results) * 0.3:  # 超過 30% 失敗
            return True

        # 檢查截止時間
        if plan.deadline:
            remaining_tasks = sum(
                1 for t in plan.decomposition.subtasks
                if t.status in [TaskStatus.PENDING, TaskStatus.READY]
            )
            estimated_remaining = remaining_tasks * 30  # 假設每個任務 30 分鐘

            from datetime import timedelta
            if datetime.utcnow() + timedelta(minutes=estimated_remaining) > plan.deadline:
                await self._emit_event(PlanEvent.DEADLINE_APPROACHING, plan, None)
                return True

        return False

    async def _replan(
        self,
        plan: ExecutionPlan,
        recent_results: List[Dict[str, Any]]
    ) -> None:
        """重新規劃"""
        plan.status = PlanStatus.REPLANNING

        # 分析當前情況
        analysis = await self._analyze_situation(plan, recent_results)

        # 使用決策引擎決定最佳行動
        decision = await self.decision_engine.make_decision(
            situation=analysis,
            options=[
                "retry_failed_tasks",
                "skip_failed_tasks",
                "modify_remaining_tasks",
                "abort_plan"
            ]
        )

        # 記錄調整
        adjustment = PlanAdjustment(
            id=uuid4(),
            plan_id=plan.id,
            trigger_event=PlanEvent.TASK_FAILED,
            original_state={"results": recent_results},
            new_state={"decision": decision},
            reason=analysis.get("reason", "Automatic replanning")
        )

        if self.require_approval:
            # 等待人工批准
            adjustment.approved = False
            plan.adjustments.append(adjustment)
            # 這裡可以發送通知等待批准
        else:
            adjustment.approved = True
            plan.adjustments.append(adjustment)
            await self._apply_adjustment(plan, decision)

        plan.status = PlanStatus.EXECUTING

    async def _analyze_situation(
        self,
        plan: ExecutionPlan,
        recent_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析當前情況"""
        failed_tasks = [r for r in recent_results if r["status"] == "failed"]
        completed_tasks = [r for r in recent_results if r["status"] == "completed"]

        prompt = f"""
        分析以下執行情況並提供建議：

        計劃目標: {plan.goal}
        當前進度: {plan.progress_percentage}%
        截止時間: {plan.deadline}

        最近結果:
        - 成功: {len(completed_tasks)} 個任務
        - 失敗: {len(failed_tasks)} 個任務
        - 失敗詳情: {[r.get('error') for r in failed_tasks]}

        請分析情況並建議下一步行動。
        """

        response = await self.llm_service.generate(
            prompt=prompt,
            max_tokens=500
        )

        return {
            "analysis": response,
            "failed_count": len(failed_tasks),
            "success_rate": len(completed_tasks) / len(recent_results) if recent_results else 0,
            "reason": "Automatic situation analysis"
        }

    async def _apply_adjustment(
        self,
        plan: ExecutionPlan,
        decision: Dict[str, Any]
    ) -> None:
        """應用計劃調整"""
        action = decision.get("action")

        if action == "retry_failed_tasks":
            # 重置失敗任務
            for task in plan.decomposition.subtasks:
                if task.status == TaskStatus.FAILED:
                    task.status = TaskStatus.READY
                    task.error_message = None

        elif action == "skip_failed_tasks":
            # 標記失敗任務為跳過
            for task in plan.decomposition.subtasks:
                if task.status == TaskStatus.FAILED:
                    task.status = TaskStatus.COMPLETED
                    task.metadata["skipped"] = True

        elif action == "modify_remaining_tasks":
            # 修改剩餘任務
            modifications = decision.get("modifications", {})
            for task in plan.decomposition.subtasks:
                if task.status == TaskStatus.PENDING:
                    task.description = modifications.get(
                        str(task.id),
                        task.description
                    )

    def _start_monitoring(self, plan_id: UUID) -> None:
        """啟動計劃監控"""
        async def monitor():
            while True:
                await asyncio.sleep(60)  # 每分鐘檢查一次
                plan = self._plans.get(plan_id)
                if not plan or plan.status != PlanStatus.EXECUTING:
                    break
                # 可以添加額外的監控邏輯

        self._monitoring_tasks[plan_id] = asyncio.create_task(monitor())

    def _stop_monitoring(self, plan_id: UUID) -> None:
        """停止計劃監控"""
        task = self._monitoring_tasks.pop(plan_id, None)
        if task:
            task.cancel()

    async def _emit_event(
        self,
        event: PlanEvent,
        plan: ExecutionPlan,
        task: Optional[SubTask]
    ) -> None:
        """發送事件"""
        for handler in self._event_handlers.get(event, []):
            try:
                await handler(plan, task)
            except Exception:
                pass

    def on_event(
        self,
        event: PlanEvent,
        handler: Callable
    ) -> None:
        """註冊事件處理器"""
        self._event_handlers[event].append(handler)

    def get_plan_status(self, plan_id: UUID) -> Dict[str, Any]:
        """獲取計劃狀態"""
        plan = self._plans.get(plan_id)
        if not plan:
            return {"error": "Plan not found"}

        return {
            "id": str(plan.id),
            "name": plan.name,
            "status": plan.status.value,
            "progress": plan.progress_percentage,
            "current_phase": plan.current_phase,
            "total_phases": len(plan.decomposition.execution_order),
            "adjustments": len(plan.adjustments),
            "subtasks": [
                {
                    "id": str(t.id),
                    "name": t.name,
                    "status": t.status.value
                }
                for t in plan.decomposition.subtasks
            ]
        }
```

#### 驗收標準
- [ ] 支援計劃建立和執行
- [ ] 實時進度追蹤
- [ ] 自動重新規劃
- [ ] 事件通知機制
- [ ] 人工審批流程

---

### Story 10-3: Autonomous Decision Engine (8 點)

**作為** 系統架構師
**我希望** 實現自主決策引擎
**以便** Agent 可以在執行過程中自主做出合理決策

#### 技術規格

```python
# backend/src/domain/orchestration/planning/decision_engine.py

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
import json


class DecisionType(str, Enum):
    """決策類型"""
    ROUTING = "routing"           # 路由決策
    RESOURCE = "resource"         # 資源分配
    ERROR_HANDLING = "error_handling"  # 錯誤處理
    PRIORITY = "priority"         # 優先級調整
    ESCALATION = "escalation"     # 升級決策
    OPTIMIZATION = "optimization" # 優化決策


class DecisionConfidence(str, Enum):
    """決策信心等級"""
    HIGH = "high"       # > 80% 信心，可自動執行
    MEDIUM = "medium"   # 50-80% 信心，建議人工確認
    LOW = "low"         # < 50% 信心，需要人工決策


@dataclass
class DecisionOption:
    """決策選項"""
    id: str
    name: str
    description: str
    pros: List[str]
    cons: List[str]
    risk_level: float  # 0-1
    estimated_impact: float  # 0-1，正面影響
    prerequisites: List[str] = field(default_factory=list)


@dataclass
class Decision:
    """決策結果"""
    id: UUID
    decision_type: DecisionType
    situation: str
    options_considered: List[DecisionOption]
    selected_option: str
    confidence: DecisionConfidence
    reasoning: str
    risk_assessment: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    human_approved: Optional[bool] = None
    execution_result: Optional[Dict[str, Any]] = None


class AutonomousDecisionEngine:
    """
    自主決策引擎

    使用 LLM 進行智能決策，支援：
    - 多選項評估
    - 風險評估
    - 信心計算
    - 可解釋性
    """

    def __init__(
        self,
        llm_service: Any,
        risk_threshold: float = 0.7,
        auto_decision_confidence: float = 0.8
    ):
        self.llm_service = llm_service
        self.risk_threshold = risk_threshold
        self.auto_decision_confidence = auto_decision_confidence

        # 決策歷史
        self._decision_history: List[Decision] = []

        # 決策規則
        self._rules: Dict[str, Callable] = {}

    async def make_decision(
        self,
        situation: str,
        options: List[str],
        context: Optional[Dict[str, Any]] = None,
        decision_type: DecisionType = DecisionType.ROUTING
    ) -> Dict[str, Any]:
        """
        做出決策

        Args:
            situation: 情況描述
            options: 可選選項
            context: 上下文信息
            decision_type: 決策類型

        Returns:
            決策結果
        """
        # 1. 擴展選項信息
        expanded_options = await self._expand_options(options, situation, context)

        # 2. 評估每個選項
        evaluations = await self._evaluate_options(expanded_options, situation, context)

        # 3. 選擇最佳選項
        selected, reasoning = await self._select_best_option(evaluations)

        # 4. 計算信心和風險
        confidence = self._calculate_confidence(evaluations, selected)
        risk_assessment = self._assess_risk(selected, evaluations)

        # 5. 建立決策記錄
        decision = Decision(
            id=uuid4(),
            decision_type=decision_type,
            situation=situation,
            options_considered=expanded_options,
            selected_option=selected.id,
            confidence=confidence,
            reasoning=reasoning,
            risk_assessment=risk_assessment
        )

        self._decision_history.append(decision)

        return {
            "decision_id": str(decision.id),
            "action": selected.id,
            "confidence": confidence.value,
            "reasoning": reasoning,
            "risk_level": risk_assessment.get("overall_risk", 0),
            "requires_approval": confidence != DecisionConfidence.HIGH,
            "options": [
                {
                    "id": opt.id,
                    "name": opt.name,
                    "score": evaluations.get(opt.id, {}).get("score", 0)
                }
                for opt in expanded_options
            ]
        }

    async def _expand_options(
        self,
        options: List[str],
        situation: str,
        context: Optional[Dict[str, Any]]
    ) -> List[DecisionOption]:
        """擴展選項信息"""
        prompt = f"""
        針對以下情況，分析每個選項的優缺點和風險：

        情況: {situation}
        上下文: {context if context else "無"}

        選項:
        {json.dumps(options, ensure_ascii=False)}

        請以 JSON 格式返回每個選項的分析：
        [
            {{
                "id": "選項ID",
                "name": "選項名稱",
                "description": "詳細描述",
                "pros": ["優點1", "優點2"],
                "cons": ["缺點1", "缺點2"],
                "risk_level": 0.3,
                "estimated_impact": 0.7,
                "prerequisites": ["前提條件"]
            }}
        ]
        """

        response = await self.llm_service.generate(
            prompt=prompt,
            max_tokens=1500
        )

        try:
            options_data = json.loads(response)
            return [
                DecisionOption(
                    id=opt.get("id", str(i)),
                    name=opt.get("name", options[i] if i < len(options) else f"Option {i}"),
                    description=opt.get("description", ""),
                    pros=opt.get("pros", []),
                    cons=opt.get("cons", []),
                    risk_level=opt.get("risk_level", 0.5),
                    estimated_impact=opt.get("estimated_impact", 0.5),
                    prerequisites=opt.get("prerequisites", [])
                )
                for i, opt in enumerate(options_data)
            ]
        except json.JSONDecodeError:
            # 簡單處理
            return [
                DecisionOption(
                    id=opt,
                    name=opt,
                    description="",
                    pros=[],
                    cons=[],
                    risk_level=0.5,
                    estimated_impact=0.5
                )
                for opt in options
            ]

    async def _evaluate_options(
        self,
        options: List[DecisionOption],
        situation: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """評估選項"""
        evaluations = {}

        for option in options:
            # 計算綜合分數
            # 分數 = 影響 * (1 - 風險) * 前提條件滿足度
            prerequisites_met = 1.0  # 假設所有前提條件滿足

            score = (
                option.estimated_impact *
                (1 - option.risk_level) *
                prerequisites_met
            )

            # 考慮優缺點數量
            pros_bonus = len(option.pros) * 0.05
            cons_penalty = len(option.cons) * 0.05
            score = score + pros_bonus - cons_penalty
            score = max(0, min(1, score))  # 限制在 0-1

            evaluations[option.id] = {
                "score": score,
                "risk": option.risk_level,
                "impact": option.estimated_impact,
                "pros_count": len(option.pros),
                "cons_count": len(option.cons)
            }

        return evaluations

    async def _select_best_option(
        self,
        evaluations: Dict[str, Dict[str, Any]]
    ) -> Tuple[DecisionOption, str]:
        """選擇最佳選項"""
        if not evaluations:
            raise ValueError("No options to evaluate")

        # 按分數排序
        sorted_options = sorted(
            evaluations.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )

        best_id = sorted_options[0][0]
        best_score = sorted_options[0][1]["score"]

        # 生成理由
        reasoning = f"選擇 {best_id}，因為它的綜合評分最高 ({best_score:.2f})。"

        if len(sorted_options) > 1:
            second_id = sorted_options[1][0]
            second_score = sorted_options[1][1]["score"]
            reasoning += f" 相比第二選項 {second_id} ({second_score:.2f})，有更好的風險收益比。"

        # 這裡需要找到對應的 DecisionOption
        # 假設我們保存了選項列表
        return DecisionOption(
            id=best_id,
            name=best_id,
            description="",
            pros=[],
            cons=[],
            risk_level=evaluations[best_id]["risk"],
            estimated_impact=evaluations[best_id]["impact"]
        ), reasoning

    def _calculate_confidence(
        self,
        evaluations: Dict[str, Dict[str, Any]],
        selected: DecisionOption
    ) -> DecisionConfidence:
        """計算決策信心"""
        if not evaluations:
            return DecisionConfidence.LOW

        scores = [e["score"] for e in evaluations.values()]
        max_score = max(scores)
        avg_score = sum(scores) / len(scores)

        # 計算領先優勢
        lead = max_score - avg_score

        # 考慮風險
        risk_factor = 1 - selected.risk_level

        # 綜合信心分數
        confidence_score = (
            max_score * 0.4 +
            lead * 0.3 +
            risk_factor * 0.3
        )

        if confidence_score >= self.auto_decision_confidence:
            return DecisionConfidence.HIGH
        elif confidence_score >= 0.5:
            return DecisionConfidence.MEDIUM
        else:
            return DecisionConfidence.LOW

    def _assess_risk(
        self,
        selected: DecisionOption,
        evaluations: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """評估風險"""
        return {
            "overall_risk": selected.risk_level,
            "risk_category": self._categorize_risk(selected.risk_level),
            "potential_issues": selected.cons,
            "mitigation_suggestions": self._generate_mitigations(selected.cons),
            "reversible": selected.risk_level < 0.5
        }

    def _categorize_risk(self, risk_level: float) -> str:
        """分類風險等級"""
        if risk_level < 0.3:
            return "low"
        elif risk_level < 0.6:
            return "medium"
        else:
            return "high"

    def _generate_mitigations(self, cons: List[str]) -> List[str]:
        """生成風險緩解建議"""
        mitigations = []
        for con in cons:
            if "time" in con.lower() or "slow" in con.lower():
                mitigations.append("設置超時限制，必要時終止")
            elif "cost" in con.lower() or "expensive" in con.lower():
                mitigations.append("設定預算上限，監控資源使用")
            elif "fail" in con.lower() or "error" in con.lower():
                mitigations.append("實施重試機制和備選方案")
            else:
                mitigations.append(f"監控相關指標: {con}")
        return mitigations

    async def explain_decision(self, decision_id: UUID) -> str:
        """解釋決策"""
        decision = next(
            (d for d in self._decision_history if d.id == decision_id),
            None
        )

        if not decision:
            return "Decision not found"

        explanation = f"""
        決策解釋：

        情況: {decision.situation}

        考慮的選項:
        """

        for opt in decision.options_considered:
            explanation += f"""
            - {opt.name}:
              優點: {', '.join(opt.pros)}
              缺點: {', '.join(opt.cons)}
              風險: {opt.risk_level:.0%}
            """

        explanation += f"""

        選擇: {decision.selected_option}

        理由: {decision.reasoning}

        信心等級: {decision.confidence.value}

        風險評估: {decision.risk_assessment}
        """

        return explanation

    def add_rule(
        self,
        name: str,
        condition: Callable[[str, List[str]], bool],
        action: str
    ) -> None:
        """
        添加決策規則

        Args:
            name: 規則名稱
            condition: 條件函數
            action: 觸發時的行動
        """
        self._rules[name] = {"condition": condition, "action": action}

    async def apply_rules(
        self,
        situation: str,
        options: List[str]
    ) -> Optional[str]:
        """
        應用決策規則

        Returns:
            如果有規則匹配，返回對應行動；否則返回 None
        """
        for name, rule in self._rules.items():
            if rule["condition"](situation, options):
                return rule["action"]
        return None
```

#### 驗收標準
- [ ] 支援多選項評估
- [ ] 風險評估準確
- [ ] 信心計算合理
- [ ] 決策可解釋
- [ ] 支援自定義規則

---

### Story 10-4: Trial-and-Error Engine (5 點)

**作為** 系統架構師
**我希望** 實現試錯學習機制
**以便** Agent 可以從失敗中學習並改進

#### 技術規格

```python
# backend/src/domain/orchestration/planning/trial_error.py

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
import json


class TrialStatus(str, Enum):
    """試驗狀態"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"


class LearningType(str, Enum):
    """學習類型"""
    PARAMETER_TUNING = "parameter_tuning"  # 參數調整
    STRATEGY_SWITCH = "strategy_switch"    # 策略切換
    ERROR_PATTERN = "error_pattern"        # 錯誤模式識別
    SUCCESS_PATTERN = "success_pattern"    # 成功模式識別


@dataclass
class Trial:
    """試驗記錄"""
    id: UUID
    task_id: UUID
    attempt_number: int
    parameters: Dict[str, Any]
    strategy: str
    status: TrialStatus = TrialStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "task_id": str(self.task_id),
            "attempt_number": self.attempt_number,
            "parameters": self.parameters,
            "strategy": self.strategy,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms
        }


@dataclass
class LearningInsight:
    """學習洞察"""
    id: UUID
    learning_type: LearningType
    pattern: str
    confidence: float
    evidence: List[UUID]  # 相關試驗 ID
    recommendation: str
    created_at: datetime = field(default_factory=datetime.utcnow)


class TrialAndErrorEngine:
    """
    試錯學習引擎

    負責：
    - 管理試驗執行
    - 分析失敗原因
    - 自動調整策略
    - 學習和改進
    """

    def __init__(
        self,
        llm_service: Any,
        max_retries: int = 3,
        learning_threshold: int = 5  # 需要多少試驗才開始學習
    ):
        self.llm_service = llm_service
        self.max_retries = max_retries
        self.learning_threshold = learning_threshold

        # 試驗歷史
        self._trials: Dict[UUID, List[Trial]] = {}  # task_id -> trials

        # 學習洞察
        self._insights: List[LearningInsight] = []

        # 錯誤模式快取
        self._error_patterns: Dict[str, List[str]] = {}

        # 成功策略快取
        self._success_strategies: Dict[str, Dict[str, Any]] = {}

    async def execute_with_retry(
        self,
        task_id: UUID,
        execution_fn: Callable[..., Any],
        initial_params: Dict[str, Any],
        strategy: str = "default"
    ) -> Dict[str, Any]:
        """
        帶重試的執行

        Args:
            task_id: 任務 ID
            execution_fn: 執行函數
            initial_params: 初始參數
            strategy: 策略名稱

        Returns:
            執行結果
        """
        if task_id not in self._trials:
            self._trials[task_id] = []

        params = initial_params.copy()
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            trial = Trial(
                id=uuid4(),
                task_id=task_id,
                attempt_number=attempt,
                parameters=params.copy(),
                strategy=strategy
            )

            trial.status = TrialStatus.RUNNING
            trial.started_at = datetime.utcnow()

            try:
                import time
                start_time = time.time()

                result = await execution_fn(**params)

                trial.status = TrialStatus.SUCCESS
                trial.result = result
                trial.duration_ms = int((time.time() - start_time) * 1000)
                trial.completed_at = datetime.utcnow()

                self._trials[task_id].append(trial)

                # 記錄成功策略
                self._record_success(task_id, params, strategy)

                return {
                    "success": True,
                    "result": result,
                    "attempts": attempt,
                    "final_params": params
                }

            except Exception as e:
                trial.status = TrialStatus.FAILURE
                trial.error = str(e)
                trial.completed_at = datetime.utcnow()

                self._trials[task_id].append(trial)
                last_error = e

                # 分析錯誤並調整
                if attempt < self.max_retries:
                    adjustment = await self._analyze_and_adjust(
                        task_id, trial, params, strategy
                    )
                    params = adjustment.get("new_params", params)
                    strategy = adjustment.get("new_strategy", strategy)

        # 所有重試都失敗
        return {
            "success": False,
            "error": str(last_error),
            "attempts": self.max_retries,
            "trials": [t.to_dict() for t in self._trials[task_id]]
        }

    async def _analyze_and_adjust(
        self,
        task_id: UUID,
        failed_trial: Trial,
        current_params: Dict[str, Any],
        current_strategy: str
    ) -> Dict[str, Any]:
        """分析失敗並調整"""
        # 檢查是否有已知的錯誤模式
        known_fix = self._check_known_patterns(failed_trial.error)
        if known_fix:
            return known_fix

        # 使用 LLM 分析
        prompt = f"""
        分析以下執行失敗並建議調整：

        任務 ID: {task_id}
        嘗試次數: {failed_trial.attempt_number}
        當前參數: {json.dumps(current_params, ensure_ascii=False)}
        當前策略: {current_strategy}
        錯誤信息: {failed_trial.error}

        之前的嘗試:
        {[t.to_dict() for t in self._trials.get(task_id, [])[:-1]]}

        請建議：
        1. 參數調整
        2. 是否需要切換策略
        3. 可能的根本原因

        以 JSON 格式返回：
        {{
            "new_params": {{}},
            "new_strategy": "strategy_name",
            "analysis": "原因分析",
            "confidence": 0.8
        }}
        """

        response = await self.llm_service.generate(
            prompt=prompt,
            max_tokens=500
        )

        try:
            adjustment = json.loads(response)
            # 記錄錯誤模式
            self._record_error_pattern(
                failed_trial.error,
                adjustment.get("analysis", ""),
                adjustment.get("new_params", {})
            )
            return adjustment
        except json.JSONDecodeError:
            # 簡單的參數調整
            return {
                "new_params": self._simple_param_adjustment(current_params),
                "new_strategy": current_strategy
            }

    def _check_known_patterns(
        self,
        error: str
    ) -> Optional[Dict[str, Any]]:
        """檢查已知的錯誤模式"""
        error_lower = error.lower()

        # 內建的常見錯誤處理
        patterns = {
            "timeout": {
                "new_params": {"timeout": "increase"},
                "analysis": "增加超時時間"
            },
            "rate limit": {
                "new_params": {"delay": "increase"},
                "analysis": "增加請求間隔"
            },
            "memory": {
                "new_params": {"batch_size": "decrease"},
                "analysis": "減少批次大小"
            },
            "connection": {
                "new_strategy": "retry_with_backoff",
                "analysis": "使用指數退避重試"
            }
        }

        for pattern, fix in patterns.items():
            if pattern in error_lower:
                return fix

        # 檢查學習到的模式
        for error_pattern, fixes in self._error_patterns.items():
            if error_pattern in error_lower and fixes:
                return {"analysis": f"已知模式: {fixes[0]}"}

        return None

    def _simple_param_adjustment(
        self,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """簡單的參數調整"""
        adjusted = params.copy()

        # 調整數值參數
        for key, value in adjusted.items():
            if isinstance(value, (int, float)):
                # 增加 20%
                adjusted[key] = value * 1.2
            elif isinstance(value, bool):
                # 翻轉布爾值
                adjusted[key] = not value

        return adjusted

    def _record_success(
        self,
        task_id: UUID,
        params: Dict[str, Any],
        strategy: str
    ) -> None:
        """記錄成功策略"""
        key = self._generate_task_key(task_id)
        self._success_strategies[key] = {
            "params": params,
            "strategy": strategy,
            "timestamp": datetime.utcnow().isoformat()
        }

    def _record_error_pattern(
        self,
        error: str,
        analysis: str,
        fix: Dict[str, Any]
    ) -> None:
        """記錄錯誤模式"""
        # 提取錯誤關鍵詞
        keywords = self._extract_error_keywords(error)

        for keyword in keywords:
            if keyword not in self._error_patterns:
                self._error_patterns[keyword] = []
            self._error_patterns[keyword].append(analysis)

    def _extract_error_keywords(self, error: str) -> List[str]:
        """提取錯誤關鍵詞"""
        # 簡單實現：提取常見錯誤類型
        keywords = []
        common_errors = [
            "timeout", "connection", "memory", "permission",
            "not found", "invalid", "failed", "error"
        ]

        error_lower = error.lower()
        for keyword in common_errors:
            if keyword in error_lower:
                keywords.append(keyword)

        return keywords

    def _generate_task_key(self, task_id: UUID) -> str:
        """生成任務鍵"""
        return str(task_id)

    async def learn_from_history(self) -> List[LearningInsight]:
        """
        從歷史試驗中學習

        分析所有試驗歷史，提取洞察
        """
        if sum(len(trials) for trials in self._trials.values()) < self.learning_threshold:
            return []

        insights = []

        # 分析成功模式
        success_insight = await self._analyze_success_patterns()
        if success_insight:
            insights.append(success_insight)

        # 分析失敗模式
        failure_insight = await self._analyze_failure_patterns()
        if failure_insight:
            insights.append(failure_insight)

        # 分析參數效果
        param_insight = await self._analyze_parameter_effects()
        if param_insight:
            insights.append(param_insight)

        self._insights.extend(insights)
        return insights

    async def _analyze_success_patterns(self) -> Optional[LearningInsight]:
        """分析成功模式"""
        successful_trials = [
            trial
            for trials in self._trials.values()
            for trial in trials
            if trial.status == TrialStatus.SUCCESS
        ]

        if len(successful_trials) < 3:
            return None

        # 找出共同參數
        common_params = self._find_common_parameters(
            [t.parameters for t in successful_trials]
        )

        if common_params:
            return LearningInsight(
                id=uuid4(),
                learning_type=LearningType.SUCCESS_PATTERN,
                pattern=f"成功案例的共同參數: {common_params}",
                confidence=len(common_params) / 10,  # 簡化的信心計算
                evidence=[t.id for t in successful_trials[:5]],
                recommendation=f"建議使用參數: {common_params}"
            )

        return None

    async def _analyze_failure_patterns(self) -> Optional[LearningInsight]:
        """分析失敗模式"""
        failed_trials = [
            trial
            for trials in self._trials.values()
            for trial in trials
            if trial.status == TrialStatus.FAILURE
        ]

        if len(failed_trials) < 3:
            return None

        # 統計錯誤類型
        error_counts: Dict[str, int] = {}
        for trial in failed_trials:
            keywords = self._extract_error_keywords(trial.error or "")
            for kw in keywords:
                error_counts[kw] = error_counts.get(kw, 0) + 1

        if error_counts:
            most_common = max(error_counts.items(), key=lambda x: x[1])
            return LearningInsight(
                id=uuid4(),
                learning_type=LearningType.ERROR_PATTERN,
                pattern=f"最常見錯誤: {most_common[0]} (出現 {most_common[1]} 次)",
                confidence=most_common[1] / len(failed_trials),
                evidence=[t.id for t in failed_trials[:5]],
                recommendation=f"優先處理 {most_common[0]} 相關問題"
            )

        return None

    async def _analyze_parameter_effects(self) -> Optional[LearningInsight]:
        """分析參數效果"""
        all_trials = [
            trial
            for trials in self._trials.values()
            for trial in trials
        ]

        if len(all_trials) < 5:
            return None

        # 簡化分析：比較成功和失敗的參數差異
        success_params = [
            t.parameters for t in all_trials
            if t.status == TrialStatus.SUCCESS
        ]
        failure_params = [
            t.parameters for t in all_trials
            if t.status == TrialStatus.FAILURE
        ]

        if not success_params or not failure_params:
            return None

        # 找出差異
        differences = self._find_parameter_differences(
            success_params, failure_params
        )

        if differences:
            return LearningInsight(
                id=uuid4(),
                learning_type=LearningType.PARAMETER_TUNING,
                pattern=f"影響成功率的參數: {differences}",
                confidence=0.7,
                evidence=[t.id for t in all_trials[:5]],
                recommendation=f"調整參數: {differences}"
            )

        return None

    def _find_common_parameters(
        self,
        param_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """找出共同參數"""
        if not param_list:
            return {}

        common = {}
        first = param_list[0]

        for key, value in first.items():
            if all(p.get(key) == value for p in param_list):
                common[key] = value

        return common

    def _find_parameter_differences(
        self,
        success_params: List[Dict[str, Any]],
        failure_params: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """找出成功和失敗的參數差異"""
        differences = {}

        # 計算每個參數的成功率
        all_keys = set()
        for p in success_params + failure_params:
            all_keys.update(p.keys())

        for key in all_keys:
            success_values = [p.get(key) for p in success_params if key in p]
            failure_values = [p.get(key) for p in failure_params if key in p]

            if success_values and failure_values:
                # 簡化：如果值不同，記錄
                if set(str(v) for v in success_values) != set(str(v) for v in failure_values):
                    differences[key] = {
                        "success_common": success_values[0],
                        "failure_common": failure_values[0]
                    }

        return differences

    def get_recommendations(
        self,
        task_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """獲取建議"""
        recommendations = []

        for insight in self._insights:
            rec = {
                "type": insight.learning_type.value,
                "pattern": insight.pattern,
                "recommendation": insight.recommendation,
                "confidence": insight.confidence
            }
            recommendations.append(rec)

        # 按信心排序
        recommendations.sort(key=lambda x: x["confidence"], reverse=True)

        return recommendations
```

#### 驗收標準
- [ ] 支援自動重試
- [ ] 錯誤模式識別
- [ ] 自動參數調整
- [ ] 學習洞察提取
- [ ] 建議生成

---

### Story 10-5: Planning API 路由 (5 點)

**作為** 前端開發者
**我希望** 有完整的規劃 API
**以便** 在 UI 中展示和管理執行計劃

#### 技術規格

```python
# backend/src/api/v1/planning/routes.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime

router = APIRouter(prefix="/planning", tags=["Planning"])


# ============ Schemas ============

class DecomposeTaskRequest(BaseModel):
    """任務分解請求"""
    task_description: str = Field(..., description="任務描述")
    context: Optional[dict] = Field(None, description="上下文信息")
    strategy: str = Field(default="hybrid", description="分解策略")

    class Config:
        json_schema_extra = {
            "example": {
                "task_description": "實現用戶認證系統",
                "context": {"framework": "FastAPI", "database": "PostgreSQL"},
                "strategy": "hybrid"
            }
        }


class CreatePlanRequest(BaseModel):
    """建立計劃請求"""
    goal: str = Field(..., description="目標描述")
    context: Optional[dict] = Field(None, description="上下文")
    deadline: Optional[datetime] = Field(None, description="截止時間")


class DecisionRequest(BaseModel):
    """決策請求"""
    situation: str = Field(..., description="情況描述")
    options: List[str] = Field(..., description="可選選項")
    context: Optional[dict] = Field(None, description="上下文")
    decision_type: str = Field(default="routing", description="決策類型")


class SubTaskResponse(BaseModel):
    """子任務回應"""
    id: str
    name: str
    description: str
    priority: str
    status: str
    dependencies: List[str]
    estimated_duration_minutes: int


class DecompositionResponse(BaseModel):
    """分解結果回應"""
    task_id: str
    original_task: str
    subtasks: List[SubTaskResponse]
    execution_order: List[List[str]]
    estimated_total_duration: int
    confidence_score: float
    strategy: str


class PlanResponse(BaseModel):
    """計劃回應"""
    id: str
    name: str
    goal: str
    status: str
    progress: float
    current_phase: int
    total_phases: int
    subtasks_count: int
    created_at: datetime


class DecisionResponse(BaseModel):
    """決策回應"""
    decision_id: str
    action: str
    confidence: str
    reasoning: str
    risk_level: float
    requires_approval: bool


# ============ Routes ============

@router.post("/decompose", response_model=DecompositionResponse)
async def decompose_task(
    request: DecomposeTaskRequest,
    decomposer: TaskDecomposer = Depends(get_task_decomposer)
):
    """
    分解任務

    將複雜任務分解為可執行的子任務
    """
    try:
        result = await decomposer.decompose(
            task_description=request.task_description,
            context=request.context,
            strategy=request.strategy
        )

        return DecompositionResponse(
            task_id=str(result.task_id),
            original_task=result.original_task,
            subtasks=[
                SubTaskResponse(
                    id=str(t.id),
                    name=t.name,
                    description=t.description,
                    priority=t.priority.value,
                    status=t.status.value,
                    dependencies=[str(d) for d in t.dependencies],
                    estimated_duration_minutes=t.estimated_duration_minutes
                )
                for t in result.subtasks
            ],
            execution_order=[[str(tid) for tid in layer] for layer in result.execution_order],
            estimated_total_duration=result.estimated_total_duration,
            confidence_score=result.confidence_score,
            strategy=result.decomposition_strategy
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/decompose/{task_id}/refine")
async def refine_decomposition(
    task_id: UUID,
    feedback: str,
    decomposer: TaskDecomposer = Depends(get_task_decomposer)
):
    """根據反饋精煉分解結果"""
    # 需要保存原始結果以便精煉
    # 這裡簡化處理
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/plans", response_model=PlanResponse)
async def create_plan(
    request: CreatePlanRequest,
    planner: DynamicPlanner = Depends(get_dynamic_planner)
):
    """建立執行計劃"""
    try:
        plan = await planner.create_plan(
            goal=request.goal,
            context=request.context,
            deadline=request.deadline
        )

        return PlanResponse(
            id=str(plan.id),
            name=plan.name,
            goal=plan.goal,
            status=plan.status.value,
            progress=plan.progress_percentage,
            current_phase=plan.current_phase,
            total_phases=len(plan.decomposition.execution_order),
            subtasks_count=len(plan.decomposition.subtasks),
            created_at=plan.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/plans/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: UUID,
    planner: DynamicPlanner = Depends(get_dynamic_planner)
):
    """獲取計劃詳情"""
    status = planner.get_plan_status(plan_id)
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])

    return status


@router.post("/plans/{plan_id}/approve")
async def approve_plan(
    plan_id: UUID,
    approver: str,
    planner: DynamicPlanner = Depends(get_dynamic_planner)
):
    """批准計劃"""
    await planner.approve_plan(plan_id, approver)
    return {"status": "approved", "plan_id": str(plan_id)}


@router.post("/plans/{plan_id}/execute")
async def execute_plan(
    plan_id: UUID,
    background_tasks: BackgroundTasks,
    planner: DynamicPlanner = Depends(get_dynamic_planner)
):
    """
    開始執行計劃

    在背景執行，立即返回
    """
    async def execution_callback(subtask):
        # 實際的任務執行邏輯
        import asyncio
        await asyncio.sleep(1)  # 模擬執行
        return {"executed": subtask.name}

    # 在背景執行
    background_tasks.add_task(
        planner.execute_plan,
        plan_id,
        execution_callback
    )

    return {
        "status": "started",
        "plan_id": str(plan_id),
        "message": "Plan execution started in background"
    }


@router.get("/plans/{plan_id}/status")
async def get_plan_execution_status(
    plan_id: UUID,
    planner: DynamicPlanner = Depends(get_dynamic_planner)
):
    """獲取計劃執行狀態"""
    return planner.get_plan_status(plan_id)


@router.post("/plans/{plan_id}/pause")
async def pause_plan(
    plan_id: UUID,
    planner: DynamicPlanner = Depends(get_dynamic_planner)
):
    """暫停計劃執行"""
    # 實現暫停邏輯
    return {"status": "paused", "plan_id": str(plan_id)}


@router.post("/decisions", response_model=DecisionResponse)
async def make_decision(
    request: DecisionRequest,
    decision_engine: AutonomousDecisionEngine = Depends(get_decision_engine)
):
    """
    請求決策

    根據情況和選項做出最佳決策
    """
    try:
        from src.domain.orchestration.planning.decision_engine import DecisionType

        result = await decision_engine.make_decision(
            situation=request.situation,
            options=request.options,
            context=request.context,
            decision_type=DecisionType(request.decision_type)
        )

        return DecisionResponse(
            decision_id=result["decision_id"],
            action=result["action"],
            confidence=result["confidence"],
            reasoning=result["reasoning"],
            risk_level=result["risk_level"],
            requires_approval=result["requires_approval"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/decisions/{decision_id}/explain")
async def explain_decision(
    decision_id: UUID,
    decision_engine: AutonomousDecisionEngine = Depends(get_decision_engine)
):
    """解釋決策"""
    explanation = await decision_engine.explain_decision(decision_id)
    return {"explanation": explanation}


@router.post("/trial")
async def execute_with_trial(
    task_id: UUID,
    params: dict,
    strategy: str = "default",
    trial_engine: TrialAndErrorEngine = Depends(get_trial_engine)
):
    """
    使用試錯機制執行任務
    """
    async def dummy_execution(**kwargs):
        import random
        if random.random() < 0.3:  # 30% 失敗率
            raise Exception("Random failure for testing")
        return {"success": True, **kwargs}

    result = await trial_engine.execute_with_retry(
        task_id=task_id,
        execution_fn=dummy_execution,
        initial_params=params,
        strategy=strategy
    )

    return result


@router.get("/trial/insights")
async def get_learning_insights(
    trial_engine: TrialAndErrorEngine = Depends(get_trial_engine)
):
    """獲取學習洞察"""
    insights = await trial_engine.learn_from_history()

    return {
        "insights": [
            {
                "id": str(i.id),
                "type": i.learning_type.value,
                "pattern": i.pattern,
                "confidence": i.confidence,
                "recommendation": i.recommendation
            }
            for i in insights
        ]
    }


@router.get("/recommendations")
async def get_recommendations(
    task_type: Optional[str] = None,
    trial_engine: TrialAndErrorEngine = Depends(get_trial_engine)
):
    """獲取執行建議"""
    return {"recommendations": trial_engine.get_recommendations(task_type)}
```

#### 驗收標準
- [ ] 任務分解 API 完整
- [ ] 計劃管理 API 完整
- [ ] 決策 API 完整
- [ ] 試錯執行 API 完整
- [ ] API 文檔完整

---

## 測試計劃

### 單元測試

```python
# tests/unit/test_task_decomposer.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.domain.orchestration.planning.task_decomposer import (
    TaskDecomposer,
    TaskPriority,
    DependencyType
)


@pytest.fixture
def mock_llm_service():
    service = MagicMock()
    service.generate = AsyncMock(return_value="""
    {
        "subtasks": [
            {
                "name": "設計資料庫架構",
                "description": "設計用戶表和認證相關表",
                "priority": "high",
                "dependencies": [],
                "estimated_minutes": 60
            },
            {
                "name": "實現用戶註冊",
                "description": "建立註冊 API 和驗證邏輯",
                "priority": "high",
                "dependencies": ["設計資料庫架構"],
                "estimated_minutes": 120
            },
            {
                "name": "實現用戶登入",
                "description": "建立登入 API 和 JWT 生成",
                "priority": "high",
                "dependencies": ["設計資料庫架構"],
                "estimated_minutes": 90
            }
        ],
        "reasoning": "按照依賴關係分解"
    }
    """)
    return service


@pytest.fixture
def decomposer(mock_llm_service):
    return TaskDecomposer(
        llm_service=mock_llm_service,
        agent_registry=MagicMock(),
        max_subtasks=20
    )


@pytest.mark.asyncio
async def test_decompose_task(decomposer):
    """測試任務分解"""
    result = await decomposer.decompose(
        task_description="實現用戶認證系統",
        strategy="hybrid"
    )

    assert result.original_task == "實現用戶認證系統"
    assert len(result.subtasks) == 3
    assert result.confidence_score > 0


@pytest.mark.asyncio
async def test_execution_order(decomposer):
    """測試執行順序"""
    result = await decomposer.decompose(
        task_description="測試任務",
        strategy="sequential"
    )

    # 應該有分層的執行順序
    assert len(result.execution_order) > 0

    # 第一層應該沒有依賴
    first_layer = result.execution_order[0]
    for task_id in first_layer:
        task = next(t for t in result.subtasks if t.id == task_id)
        assert len(task.dependencies) == 0


@pytest.mark.asyncio
async def test_duration_estimation(decomposer):
    """測試時間估算"""
    result = await decomposer.decompose(
        task_description="測試任務",
        strategy="parallel"
    )

    # 並行任務的總時間應該等於最長路徑
    assert result.estimated_total_duration > 0
    assert result.estimated_total_duration <= sum(
        t.estimated_duration_minutes for t in result.subtasks
    )


# tests/unit/test_decision_engine.py

@pytest.mark.asyncio
async def test_make_decision():
    """測試決策"""
    llm_service = MagicMock()
    llm_service.generate = AsyncMock(return_value="""
    [
        {
            "id": "option_a",
            "name": "Option A",
            "description": "First option",
            "pros": ["Fast", "Simple"],
            "cons": ["Limited"],
            "risk_level": 0.2,
            "estimated_impact": 0.8
        },
        {
            "id": "option_b",
            "name": "Option B",
            "description": "Second option",
            "pros": ["Comprehensive"],
            "cons": ["Complex", "Slow"],
            "risk_level": 0.5,
            "estimated_impact": 0.9
        }
    ]
    """)

    engine = AutonomousDecisionEngine(
        llm_service=llm_service
    )

    result = await engine.make_decision(
        situation="選擇實現方案",
        options=["option_a", "option_b"]
    )

    assert "action" in result
    assert "confidence" in result
    assert "reasoning" in result
    assert result["action"] in ["option_a", "option_b"]


@pytest.mark.asyncio
async def test_decision_with_rules():
    """測試帶規則的決策"""
    engine = AutonomousDecisionEngine(
        llm_service=MagicMock()
    )

    # 添加規則
    engine.add_rule(
        name="urgent_rule",
        condition=lambda s, o: "urgent" in s.lower(),
        action="immediate_action"
    )

    # 測試規則匹配
    action = await engine.apply_rules(
        situation="This is urgent!",
        options=["a", "b", "c"]
    )

    assert action == "immediate_action"
```

### 整合測試

```python
# tests/integration/test_planning_flow.py

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_full_planning_flow(client: AsyncClient):
    """測試完整的規劃流程"""
    # 1. 分解任務
    response = await client.post(
        "/api/v1/planning/decompose",
        json={
            "task_description": "建立 REST API 服務",
            "strategy": "hybrid"
        }
    )
    assert response.status_code == 200
    decomposition = response.json()
    assert len(decomposition["subtasks"]) > 0

    # 2. 建立計劃
    response = await client.post(
        "/api/v1/planning/plans",
        json={
            "goal": "建立 REST API 服務"
        }
    )
    assert response.status_code == 200
    plan = response.json()
    plan_id = plan["id"]

    # 3. 批准計劃
    response = await client.post(
        f"/api/v1/planning/plans/{plan_id}/approve",
        params={"approver": "test_user"}
    )
    assert response.status_code == 200

    # 4. 獲取狀態
    response = await client.get(
        f"/api/v1/planning/plans/{plan_id}/status"
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
```

---

## 資料庫遷移

```sql
-- migrations/versions/010_planning_tables.sql

-- 任務分解表
CREATE TABLE task_decompositions (
    id UUID PRIMARY KEY,
    original_task TEXT NOT NULL,
    strategy VARCHAR(50) NOT NULL,
    confidence_score DECIMAL(3,2),
    estimated_total_duration INTEGER,
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 子任務表
CREATE TABLE subtasks (
    id UUID PRIMARY KEY,
    decomposition_id UUID REFERENCES task_decompositions(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    assigned_agent_id UUID REFERENCES agents(id),
    dependencies UUID[] DEFAULT '{}',
    dependency_type VARCHAR(50) DEFAULT 'finish_to_start',
    estimated_duration_minutes INTEGER DEFAULT 30,
    actual_duration_minutes INTEGER,
    inputs JSONB DEFAULT '{}',
    outputs JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 執行計劃表
CREATE TABLE execution_plans (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    goal TEXT NOT NULL,
    decomposition_id UUID REFERENCES task_decompositions(id),
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    current_phase INTEGER DEFAULT 0,
    progress_percentage DECIMAL(5,2) DEFAULT 0,
    deadline TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- 計劃調整表
CREATE TABLE plan_adjustments (
    id UUID PRIMARY KEY,
    plan_id UUID REFERENCES execution_plans(id) ON DELETE CASCADE,
    trigger_event VARCHAR(50) NOT NULL,
    original_state JSONB NOT NULL,
    new_state JSONB NOT NULL,
    reason TEXT,
    approved BOOLEAN DEFAULT false,
    approved_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 決策記錄表
CREATE TABLE decisions (
    id UUID PRIMARY KEY,
    decision_type VARCHAR(50) NOT NULL,
    situation TEXT NOT NULL,
    options_considered JSONB NOT NULL,
    selected_option VARCHAR(255) NOT NULL,
    confidence VARCHAR(20) NOT NULL,
    reasoning TEXT,
    risk_assessment JSONB DEFAULT '{}',
    human_approved BOOLEAN,
    execution_result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 試驗記錄表
CREATE TABLE trials (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL,
    attempt_number INTEGER NOT NULL,
    parameters JSONB NOT NULL,
    strategy VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    result JSONB,
    error TEXT,
    duration_ms INTEGER,
    metadata JSONB DEFAULT '{}',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 學習洞察表
CREATE TABLE learning_insights (
    id UUID PRIMARY KEY,
    learning_type VARCHAR(50) NOT NULL,
    pattern TEXT NOT NULL,
    confidence DECIMAL(3,2),
    evidence UUID[] DEFAULT '{}',
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_subtasks_decomposition ON subtasks(decomposition_id);
CREATE INDEX idx_subtasks_status ON subtasks(status);
CREATE INDEX idx_execution_plans_status ON execution_plans(status);
CREATE INDEX idx_decisions_type ON decisions(decision_type);
CREATE INDEX idx_trials_task ON trials(task_id);
CREATE INDEX idx_trials_status ON trials(status);
```

---

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| LLM 分解質量不穩定 | 高 | 多次分解取最佳、人工審核 |
| 自主決策錯誤 | 高 | 信心閾值、人工確認機制 |
| 無限重試循環 | 中 | 最大重試次數限制 |
| 規劃時間過長 | 中 | 異步執行、進度反饋 |
| 學習數據不足 | 低 | 設置最小閾值、提供預設規則 |

---

## Definition of Done

- [ ] 所有 User Stories 完成
- [ ] 單元測試覆蓋率 > 85%
- [ ] 整合測試通過
- [ ] API 文檔更新
- [ ] 資料庫遷移腳本準備完成
- [ ] 程式碼審查完成
- [ ] 效能測試通過（分解 < 10秒，決策 < 5秒）

---

**下一步**: [Sprint 11 - 嵌套工作流](./sprint-11-plan.md)
