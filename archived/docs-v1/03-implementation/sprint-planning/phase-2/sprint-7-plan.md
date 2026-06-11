# Sprint 7: 並行執行引擎 - Concurrent Execution

**Sprint 目標**: 實現多 Agent 並行執行能力，提升工作流處理效率
**週期**: Week 15-16 (2 週)
**Story Points**: 34 點
**Phase 2 功能**: P2-F1 (Concurrent 並行執行), P2-F2 (Enhanced Gateway 增強閘道)

---

## Sprint 概覽

### 目標
1. 實現並行執行引擎 (Concurrent Executor)
2. 增強 Gateway 節點支援 PARALLEL 和 JOIN 模式
3. 建立並行執行狀態管理機制
4. 實現結果合併策略 (Merge Strategy)
5. 建立死鎖檢測和超時處理

### 成功標準
- [ ] 可配置多個 Agent 節點並行執行
- [ ] 並行執行效率達到 3x 吞吐量提升
- [ ] 支援 Fork-Join 模式
- [ ] 結果可正確合併並傳遞給下游節點
- [ ] 死鎖和超時情況可正確處理

---

## 核心概念

### 並行執行架構

```
┌─────────────────────────────────────────────────────────────────┐
│                    Concurrent Execution Flow                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐                                                │
│  │   START      │                                                │
│  └──────┬───────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐     ┌─────────────────────────────────┐       │
│  │   PARALLEL   │     │        Concurrent Executor       │       │
│  │   GATEWAY    │────▶│   ┌─────────┐   ┌─────────┐     │       │
│  │   (Fork)     │     │   │ Agent A │   │ Agent B │     │       │
│  └──────────────┘     │   │ (async) │   │ (async) │     │       │
│                       │   └────┬────┘   └────┬────┘     │       │
│                       │        │             │          │       │
│                       │        ▼             ▼          │       │
│                       │   ┌─────────┐   ┌─────────┐     │       │
│                       │   │Result A │   │Result B │     │       │
│                       │   └────┬────┘   └────┬────┘     │       │
│                       └────────┼─────────────┼──────────┘       │
│                                │             │                   │
│                                └──────┬──────┘                   │
│                                       ▼                          │
│                              ┌──────────────┐                    │
│                              │    JOIN      │                    │
│                              │   GATEWAY    │                    │
│                              │   (Merge)    │                    │
│                              └──────┬───────┘                    │
│                                     │                            │
│                                     ▼                            │
│                              ┌──────────────┐                    │
│                              │  Next Node   │                    │
│                              └──────────────┘                    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Framework 並行 API

```python
# Agent Framework 並行執行相關 API
from agent_framework import (
    WorkflowBuilder,
    AgentExecutor,
    Executor,
    WorkflowContext,
    handler,
)
import asyncio

# 並行執行模式
class ConcurrentExecutionMode:
    ALL = "all"              # 等待所有完成
    ANY = "any"              # 任一完成即可
    MAJORITY = "majority"    # 多數完成即可
    FIRST_SUCCESS = "first_success"  # 第一個成功
```

---

## User Stories

### S7-1: 並行執行引擎實現 (13 點)

**描述**: 作為開發者，我需要讓多個 Agent 可以同時執行，以提升處理效率。

**驗收標準**:
- [ ] 支援配置多個節點並行執行
- [ ] 並行執行使用 asyncio 異步機制
- [ ] 每個並行分支可獨立追蹤狀態
- [ ] 支援設定並行數量上限

**技術任務**:

1. **並行執行器 (src/domain/workflows/executors/concurrent.py)**
```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from uuid import UUID
from enum import Enum
import asyncio
from datetime import datetime

from agent_framework import Executor, WorkflowContext, handler


class ConcurrentMode(str, Enum):
    """並行執行模式"""
    ALL = "all"                    # 等待所有任務完成
    ANY = "any"                    # 任一任務完成即返回
    MAJORITY = "majority"          # 多數任務完成即返回
    FIRST_SUCCESS = "first_success"  # 第一個成功的任務


@dataclass
class ConcurrentTask:
    """並行任務定義"""
    id: str
    executor_id: str
    input_data: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[int] = None  # 秒


@dataclass
class ConcurrentResult:
    """並行執行結果"""
    task_id: str
    success: bool
    result: Any
    error: Optional[str] = None
    duration_ms: int = 0


class ConcurrentExecutor(Executor):
    """
    並行執行器 - 同時執行多個 Agent/任務

    支援多種並行模式和結果合併策略
    """

    def __init__(
        self,
        id: str,
        tasks: List[ConcurrentTask],
        mode: ConcurrentMode = ConcurrentMode.ALL,
        max_concurrency: int = 10,
        timeout: int = 300,  # 總超時時間(秒)
    ):
        super().__init__(id=id)
        self._tasks = tasks
        self._mode = mode
        self._max_concurrency = max_concurrency
        self._timeout = timeout
        self._results: Dict[str, ConcurrentResult] = {}

    @handler
    async def on_start(self, ctx: WorkflowContext) -> None:
        """開始並行執行"""
        start_time = datetime.utcnow()

        # 創建信號量控制並行數量
        semaphore = asyncio.Semaphore(self._max_concurrency)

        async def execute_task(task: ConcurrentTask) -> ConcurrentResult:
            """執行單個任務"""
            async with semaphore:
                task_start = datetime.utcnow()
                try:
                    # 發送消息給目標執行器
                    result = await ctx.send_message_and_wait(
                        message=task.input_data,
                        target_id=task.executor_id,
                        timeout=task.timeout or self._timeout,
                    )

                    duration = (datetime.utcnow() - task_start).total_seconds() * 1000
                    return ConcurrentResult(
                        task_id=task.id,
                        success=True,
                        result=result,
                        duration_ms=int(duration),
                    )

                except asyncio.TimeoutError:
                    duration = (datetime.utcnow() - task_start).total_seconds() * 1000
                    return ConcurrentResult(
                        task_id=task.id,
                        success=False,
                        result=None,
                        error="Task timeout",
                        duration_ms=int(duration),
                    )
                except Exception as e:
                    duration = (datetime.utcnow() - task_start).total_seconds() * 1000
                    return ConcurrentResult(
                        task_id=task.id,
                        success=False,
                        result=None,
                        error=str(e),
                        duration_ms=int(duration),
                    )

        # 根據模式執行
        if self._mode == ConcurrentMode.ALL:
            results = await self._execute_all(execute_task)
        elif self._mode == ConcurrentMode.ANY:
            results = await self._execute_any(execute_task)
        elif self._mode == ConcurrentMode.FIRST_SUCCESS:
            results = await self._execute_first_success(execute_task)
        elif self._mode == ConcurrentMode.MAJORITY:
            results = await self._execute_majority(execute_task)
        else:
            results = await self._execute_all(execute_task)

        # 存儲結果
        self._results = {r.task_id: r for r in results}

        # 輸出合併結果
        await ctx.yield_output({
            "mode": self._mode.value,
            "total_tasks": len(self._tasks),
            "completed_tasks": len([r for r in results if r.success]),
            "failed_tasks": len([r for r in results if not r.success]),
            "results": {r.task_id: r.result for r in results if r.success},
            "errors": {r.task_id: r.error for r in results if not r.success},
        })

    async def _execute_all(self, execute_fn) -> List[ConcurrentResult]:
        """等待所有任務完成"""
        tasks = [execute_fn(task) for task in self._tasks]
        return await asyncio.gather(*tasks)

    async def _execute_any(self, execute_fn) -> List[ConcurrentResult]:
        """任一任務完成即返回"""
        tasks = [asyncio.create_task(execute_fn(task)) for task in self._tasks]
        done, pending = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_COMPLETED,
        )

        # 取消未完成的任務
        for task in pending:
            task.cancel()

        return [task.result() for task in done]

    async def _execute_first_success(self, execute_fn) -> List[ConcurrentResult]:
        """第一個成功的任務"""
        tasks = [asyncio.create_task(execute_fn(task)) for task in self._tasks]
        results = []

        while tasks:
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in done:
                result = task.result()
                results.append(result)
                if result.success:
                    # 找到成功的，取消其餘任務
                    for p in pending:
                        p.cancel()
                    return results

            tasks = list(pending)

        return results

    async def _execute_majority(self, execute_fn) -> List[ConcurrentResult]:
        """多數任務完成"""
        majority_count = len(self._tasks) // 2 + 1
        tasks = [asyncio.create_task(execute_fn(task)) for task in self._tasks]
        results = []

        while len(results) < majority_count and tasks:
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in done:
                results.append(task.result())

            tasks = list(pending)

        # 取消剩餘任務
        for task in tasks:
            task.cancel()

        return results

    def get_results(self) -> Dict[str, ConcurrentResult]:
        """獲取執行結果"""
        return self._results
```

2. **並行狀態管理 (src/domain/workflows/concurrent_state.py)**
```python
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from uuid import UUID
from datetime import datetime
from enum import Enum


class BranchStatus(str, Enum):
    """分支狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class ParallelBranch:
    """並行分支"""
    id: str
    executor_id: str
    status: BranchStatus = BranchStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None


@dataclass
class ConcurrentExecutionState:
    """並行執行狀態"""
    execution_id: UUID
    parent_node_id: str
    branches: Dict[str, ParallelBranch] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def add_branch(self, branch: ParallelBranch) -> None:
        """添加分支"""
        self.branches[branch.id] = branch

    def update_branch_status(
        self,
        branch_id: str,
        status: BranchStatus,
        result: Any = None,
        error: Optional[str] = None,
    ) -> None:
        """更新分支狀態"""
        if branch_id in self.branches:
            branch = self.branches[branch_id]
            branch.status = status

            if status == BranchStatus.RUNNING:
                branch.started_at = datetime.utcnow()
            elif status in [BranchStatus.COMPLETED, BranchStatus.FAILED,
                           BranchStatus.CANCELLED, BranchStatus.TIMEOUT]:
                branch.completed_at = datetime.utcnow()
                branch.result = result
                branch.error = error

    def is_completed(self) -> bool:
        """檢查是否所有分支都已完成"""
        terminal_statuses = {
            BranchStatus.COMPLETED,
            BranchStatus.FAILED,
            BranchStatus.CANCELLED,
            BranchStatus.TIMEOUT,
        }
        return all(
            b.status in terminal_statuses
            for b in self.branches.values()
        )

    def get_successful_results(self) -> Dict[str, Any]:
        """獲取成功的結果"""
        return {
            branch_id: branch.result
            for branch_id, branch in self.branches.items()
            if branch.status == BranchStatus.COMPLETED
        }

    def get_failed_branches(self) -> List[ParallelBranch]:
        """獲取失敗的分支"""
        return [
            branch for branch in self.branches.values()
            if branch.status in [BranchStatus.FAILED, BranchStatus.TIMEOUT]
        ]


class ConcurrentStateManager:
    """並行狀態管理器"""

    def __init__(self):
        self._states: Dict[UUID, ConcurrentExecutionState] = {}

    def create_state(
        self,
        execution_id: UUID,
        parent_node_id: str,
        branch_configs: List[Dict],
    ) -> ConcurrentExecutionState:
        """創建並行執行狀態"""
        state = ConcurrentExecutionState(
            execution_id=execution_id,
            parent_node_id=parent_node_id,
        )

        for config in branch_configs:
            branch = ParallelBranch(
                id=config["id"],
                executor_id=config["executor_id"],
            )
            state.add_branch(branch)

        self._states[execution_id] = state
        return state

    def get_state(self, execution_id: UUID) -> Optional[ConcurrentExecutionState]:
        """獲取並行執行狀態"""
        return self._states.get(execution_id)

    def update_branch(
        self,
        execution_id: UUID,
        branch_id: str,
        status: BranchStatus,
        result: Any = None,
        error: Optional[str] = None,
    ) -> None:
        """更新分支狀態"""
        state = self._states.get(execution_id)
        if state:
            state.update_branch_status(branch_id, status, result, error)

    def cleanup(self, execution_id: UUID) -> None:
        """清理狀態"""
        if execution_id in self._states:
            del self._states[execution_id]
```

---

### S7-2: 增強型閘道節點 (13 點)

**描述**: 作為開發者，我需要增強的 Gateway 節點來支援並行分支和合併。

**驗收標準**:
- [ ] 支援 PARALLEL (Fork) 閘道
- [ ] 支援 JOIN (Merge) 閘道
- [ ] 支援 INCLUSIVE 閘道 (部分分支執行)
- [ ] 支援多種合併策略

**技術任務**:

1. **增強型閘道模型 (src/domain/workflows/models.py 擴展)**
```python
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


class GatewayType(str, Enum):
    """閘道類型 - 擴展"""
    EXCLUSIVE = "exclusive"      # 排他 (XOR) - 只選一條路徑
    PARALLEL = "parallel"        # 並行 (AND) - 所有路徑同時執行
    INCLUSIVE = "inclusive"      # 包容 (OR) - 滿足條件的路徑執行
    EVENT_BASED = "event_based"  # 基於事件 - 等待事件決定路徑


class JoinStrategy(str, Enum):
    """合併策略"""
    WAIT_ALL = "wait_all"        # 等待所有分支
    WAIT_ANY = "wait_any"        # 等待任一分支
    WAIT_MAJORITY = "wait_majority"  # 等待多數分支
    WAIT_N = "wait_n"            # 等待 N 個分支


class MergeStrategy(str, Enum):
    """結果合併策略"""
    COLLECT_ALL = "collect_all"  # 收集所有結果為列表
    MERGE_DICT = "merge_dict"    # 合併為字典
    FIRST_RESULT = "first_result"  # 取第一個結果
    AGGREGATE = "aggregate"      # 聚合 (需要自定義函數)


@dataclass
class ParallelGatewayConfig:
    """並行閘道配置"""
    max_concurrency: int = 10
    timeout: int = 300  # 秒
    join_strategy: JoinStrategy = JoinStrategy.WAIT_ALL
    merge_strategy: MergeStrategy = MergeStrategy.COLLECT_ALL
    wait_n_count: int = 1  # 當 join_strategy 為 WAIT_N 時使用
    aggregate_function: Optional[str] = None  # 聚合函數名稱


@dataclass
class EnhancedWorkflowNode:
    """增強型工作流節點"""
    id: str
    type: str  # "start", "end", "agent", "gateway"
    name: str = ""

    # Agent 節點配置
    agent_id: Optional[str] = None

    # Gateway 節點配置
    gateway_type: Optional[GatewayType] = None
    gateway_config: Optional[ParallelGatewayConfig] = None

    # 通用配置
    config: Dict[str, Any] = field(default_factory=dict)
    position: Optional[Dict[str, int]] = None

    def is_parallel_gateway(self) -> bool:
        """是否為並行閘道"""
        return self.gateway_type == GatewayType.PARALLEL

    def is_join_gateway(self) -> bool:
        """是否為合併閘道 (檢查配置)"""
        return (
            self.gateway_type == GatewayType.PARALLEL and
            self.config.get("is_join", False)
        )
```

2. **並行閘道執行器 (src/domain/workflows/executors/parallel_gateway.py)**
```python
from typing import List, Dict, Any, Optional, override
from dataclasses import dataclass
import asyncio

from agent_framework import Executor, WorkflowContext, handler

from src.domain.workflows.models import (
    ParallelGatewayConfig,
    JoinStrategy,
    MergeStrategy,
)


class ParallelForkGateway(Executor):
    """
    並行分支閘道 (Fork)

    將執行流分成多個並行分支
    """

    def __init__(
        self,
        id: str,
        branch_targets: List[str],
        config: ParallelGatewayConfig,
    ):
        super().__init__(id=id)
        self._branch_targets = branch_targets
        self._config = config

    @handler
    async def on_input(self, input_data: Any, ctx: WorkflowContext) -> None:
        """接收輸入並分發到所有分支"""
        # 記錄分支信息到上下文
        await ctx.set_state("parallel_branches", self._branch_targets)
        await ctx.set_state("parallel_config", vars(self._config))

        # 使用信號量控制並行數
        semaphore = asyncio.Semaphore(self._config.max_concurrency)

        async def send_to_branch(target_id: str):
            async with semaphore:
                await ctx.send_message(
                    message={
                        "input": input_data,
                        "branch_id": target_id,
                        "fork_gateway_id": self.id,
                    },
                    target_id=target_id,
                )

        # 並行發送到所有分支
        await asyncio.gather(*[
            send_to_branch(target) for target in self._branch_targets
        ])


class ParallelJoinGateway(Executor):
    """
    並行合併閘道 (Join)

    等待並行分支完成並合併結果
    """

    def __init__(
        self,
        id: str,
        expected_branches: List[str],
        config: ParallelGatewayConfig,
    ):
        super().__init__(id=id)
        self._expected_branches = expected_branches
        self._config = config
        self._received_results: Dict[str, Any] = {}
        self._completion_event = asyncio.Event()

    @handler
    async def on_branch_result(
        self,
        branch_id: str,
        result: Any,
        ctx: WorkflowContext,
    ) -> None:
        """接收分支結果"""
        self._received_results[branch_id] = result

        # 檢查是否滿足合併條件
        if self._should_proceed():
            self._completion_event.set()

            # 合併結果
            merged = self._merge_results()

            # 輸出合併後的結果
            await ctx.yield_output({
                "merged_result": merged,
                "received_branches": list(self._received_results.keys()),
                "total_branches": len(self._expected_branches),
            })

    def _should_proceed(self) -> bool:
        """檢查是否應該繼續執行"""
        received_count = len(self._received_results)
        total_count = len(self._expected_branches)

        if self._config.join_strategy == JoinStrategy.WAIT_ALL:
            return received_count >= total_count
        elif self._config.join_strategy == JoinStrategy.WAIT_ANY:
            return received_count >= 1
        elif self._config.join_strategy == JoinStrategy.WAIT_MAJORITY:
            return received_count > total_count // 2
        elif self._config.join_strategy == JoinStrategy.WAIT_N:
            return received_count >= self._config.wait_n_count
        else:
            return received_count >= total_count

    def _merge_results(self) -> Any:
        """合併結果"""
        results = self._received_results

        if self._config.merge_strategy == MergeStrategy.COLLECT_ALL:
            return list(results.values())
        elif self._config.merge_strategy == MergeStrategy.MERGE_DICT:
            merged = {}
            for result in results.values():
                if isinstance(result, dict):
                    merged.update(result)
            return merged
        elif self._config.merge_strategy == MergeStrategy.FIRST_RESULT:
            return next(iter(results.values()), None)
        elif self._config.merge_strategy == MergeStrategy.AGGREGATE:
            return self._apply_aggregation(results)
        else:
            return list(results.values())

    def _apply_aggregation(self, results: Dict[str, Any]) -> Any:
        """應用聚合函數"""
        func_name = self._config.aggregate_function
        if func_name == "sum":
            return sum(v for v in results.values() if isinstance(v, (int, float)))
        elif func_name == "count":
            return len(results)
        elif func_name == "concat":
            return "".join(str(v) for v in results.values())
        else:
            return list(results.values())

    @override
    async def on_checkpoint_save(self) -> Dict[str, Any]:
        """保存檢查點"""
        return {
            "received_results": self._received_results,
            "expected_branches": self._expected_branches,
        }

    @override
    async def on_checkpoint_restore(self, state: Dict[str, Any]) -> None:
        """恢復檢查點"""
        self._received_results = state.get("received_results", {})
```

---

### S7-3: 死鎖檢測與超時處理 (8 點)

**描述**: 作為系統管理員，我需要系統能自動檢測死鎖並處理超時情況。

**驗收標準**:
- [ ] 可檢測並行執行中的死鎖
- [ ] 支援任務級別超時
- [ ] 支援整體執行超時
- [ ] 超時後可正確清理資源

**技術任務**:

1. **死鎖檢測器 (src/domain/workflows/deadlock_detector.py)**
```python
from typing import Dict, Set, List, Optional
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime, timedelta
import asyncio


@dataclass
class WaitingTask:
    """等待中的任務"""
    task_id: str
    waiting_for: Set[str]  # 等待的任務 ID 集合
    started_at: datetime
    timeout: int  # 秒


class DeadlockDetector:
    """
    死鎖檢測器

    使用等待圖 (Wait-for Graph) 檢測循環依賴
    """

    def __init__(self, check_interval: int = 5):
        self._waiting_tasks: Dict[str, WaitingTask] = {}
        self._check_interval = check_interval
        self._running = False

    def register_waiting(
        self,
        task_id: str,
        waiting_for: Set[str],
        timeout: int = 300,
    ) -> None:
        """註冊等待中的任務"""
        self._waiting_tasks[task_id] = WaitingTask(
            task_id=task_id,
            waiting_for=waiting_for,
            started_at=datetime.utcnow(),
            timeout=timeout,
        )

    def unregister(self, task_id: str) -> None:
        """取消註冊"""
        if task_id in self._waiting_tasks:
            del self._waiting_tasks[task_id]

    def detect_deadlock(self) -> Optional[List[str]]:
        """
        檢測死鎖

        返回形成循環的任務 ID 列表，如果沒有死鎖則返回 None
        """
        # 構建等待圖
        graph: Dict[str, Set[str]] = {
            task_id: task.waiting_for
            for task_id, task in self._waiting_tasks.items()
        }

        # DFS 檢測循環
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        cycle_path: List[str] = []

        def dfs(node: str, path: List[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    # 找到循環
                    cycle_start = path.index(neighbor)
                    cycle_path.extend(path[cycle_start:])
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for task_id in graph:
            if task_id not in visited:
                if dfs(task_id, []):
                    return cycle_path

        return None

    def get_timed_out_tasks(self) -> List[WaitingTask]:
        """獲取超時的任務"""
        now = datetime.utcnow()
        timed_out = []

        for task in self._waiting_tasks.values():
            elapsed = (now - task.started_at).total_seconds()
            if elapsed > task.timeout:
                timed_out.append(task)

        return timed_out

    async def start_monitoring(
        self,
        on_deadlock: callable,
        on_timeout: callable,
    ) -> None:
        """開始監控"""
        self._running = True

        while self._running:
            # 檢測死鎖
            deadlock = self.detect_deadlock()
            if deadlock:
                await on_deadlock(deadlock)

            # 檢測超時
            timed_out = self.get_timed_out_tasks()
            for task in timed_out:
                await on_timeout(task)
                self.unregister(task.task_id)

            await asyncio.sleep(self._check_interval)

    def stop_monitoring(self) -> None:
        """停止監控"""
        self._running = False


class TimeoutHandler:
    """超時處理器"""

    @staticmethod
    async def handle_task_timeout(
        execution_id: UUID,
        task_id: str,
        cleanup_fn: callable,
    ) -> Dict[str, Any]:
        """處理任務超時"""
        # 執行清理
        await cleanup_fn(task_id)

        return {
            "execution_id": str(execution_id),
            "task_id": task_id,
            "status": "timeout",
            "message": f"Task {task_id} timed out and was cancelled",
        }

    @staticmethod
    async def handle_deadlock(
        execution_id: UUID,
        cycle: List[str],
        resolution_strategy: str = "cancel_youngest",
    ) -> Dict[str, Any]:
        """處理死鎖"""
        if resolution_strategy == "cancel_youngest":
            # 取消最新的任務
            task_to_cancel = cycle[-1]
        elif resolution_strategy == "cancel_oldest":
            # 取消最舊的任務
            task_to_cancel = cycle[0]
        else:
            # 取消所有
            task_to_cancel = None

        return {
            "execution_id": str(execution_id),
            "deadlock_detected": True,
            "cycle": cycle,
            "cancelled_task": task_to_cancel,
            "strategy": resolution_strategy,
        }
```

---

## 時間規劃

### Week 15 (Day 1-5)

| 日期 | 任務 | 負責人 | 產出 |
|------|------|--------|------|
| Day 1-2 | S7-1: ConcurrentExecutor 核心實現 | Backend | concurrent.py |
| Day 2-3 | S7-1: 並行狀態管理 | Backend | concurrent_state.py |
| Day 3-4 | S7-2: ParallelForkGateway | Backend | parallel_gateway.py |
| Day 4-5 | S7-2: ParallelJoinGateway | Backend | parallel_gateway.py |

### Week 16 (Day 6-10)

| 日期 | 任務 | 負責人 | 產出 |
|------|------|--------|------|
| Day 6-7 | S7-2: 合併策略實現 | Backend | merge_strategies.py |
| Day 7-8 | S7-3: 死鎖檢測器 | Backend | deadlock_detector.py |
| Day 8-9 | S7-3: 超時處理器 | Backend | timeout_handler.py |
| Day 9-10 | 單元測試 + 集成測試 | 全員 | 測試用例 |

---

## 測試要求

### 單元測試

```python
# tests/unit/test_concurrent_executor.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from src.domain.workflows.executors.concurrent import (
    ConcurrentExecutor,
    ConcurrentTask,
    ConcurrentMode,
)


class TestConcurrentExecutor:

    @pytest.mark.asyncio
    async def test_execute_all_mode(self):
        """測試 ALL 模式 - 等待所有任務完成"""
        tasks = [
            ConcurrentTask(id="task1", executor_id="exec1"),
            ConcurrentTask(id="task2", executor_id="exec2"),
            ConcurrentTask(id="task3", executor_id="exec3"),
        ]

        executor = ConcurrentExecutor(
            id="concurrent_test",
            tasks=tasks,
            mode=ConcurrentMode.ALL,
        )

        # Mock context
        ctx = AsyncMock()
        ctx.send_message_and_wait = AsyncMock(return_value={"status": "ok"})

        await executor.on_start(ctx)

        # 驗證所有任務都被執行
        assert ctx.send_message_and_wait.call_count == 3

    @pytest.mark.asyncio
    async def test_execute_any_mode(self):
        """測試 ANY 模式 - 任一完成即返回"""
        tasks = [
            ConcurrentTask(id="task1", executor_id="exec1"),
            ConcurrentTask(id="task2", executor_id="exec2"),
        ]

        executor = ConcurrentExecutor(
            id="concurrent_test",
            tasks=tasks,
            mode=ConcurrentMode.ANY,
        )

        ctx = AsyncMock()
        ctx.send_message_and_wait = AsyncMock(return_value={"status": "ok"})

        await executor.on_start(ctx)

        # 驗證至少有一個結果
        assert ctx.yield_output.called


# tests/unit/test_deadlock_detector.py
import pytest

from src.domain.workflows.deadlock_detector import DeadlockDetector


class TestDeadlockDetector:

    def test_no_deadlock(self):
        """測試無死鎖情況"""
        detector = DeadlockDetector()

        detector.register_waiting("A", {"B"})
        detector.register_waiting("B", {"C"})
        detector.register_waiting("C", set())

        cycle = detector.detect_deadlock()
        assert cycle is None

    def test_simple_deadlock(self):
        """測試簡單死鎖 A->B->A"""
        detector = DeadlockDetector()

        detector.register_waiting("A", {"B"})
        detector.register_waiting("B", {"A"})

        cycle = detector.detect_deadlock()
        assert cycle is not None
        assert "A" in cycle
        assert "B" in cycle

    def test_complex_deadlock(self):
        """測試複雜死鎖 A->B->C->A"""
        detector = DeadlockDetector()

        detector.register_waiting("A", {"B"})
        detector.register_waiting("B", {"C"})
        detector.register_waiting("C", {"A"})

        cycle = detector.detect_deadlock()
        assert cycle is not None
        assert len(cycle) == 3
```

### 集成測試

```python
# tests/integration/test_concurrent_workflow.py
import pytest
from httpx import AsyncClient

from main import app


class TestConcurrentWorkflow:

    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_parallel_workflow_execution(self, client):
        """測試並行工作流執行"""
        # 創建三個 Agent
        agents = []
        for i in range(3):
            response = await client.post("/api/v1/agents/", json={
                "name": f"parallel-agent-{i}",
                "instructions": "Process input and return result",
            })
            agents.append(response.json()["id"])

        # 創建並行工作流
        workflow_response = await client.post("/api/v1/workflows/", json={
            "name": "parallel-test-workflow",
            "graph_definition": {
                "nodes": [
                    {"id": "start", "type": "start"},
                    {
                        "id": "parallel_fork",
                        "type": "gateway",
                        "gateway_type": "parallel",
                        "config": {"is_fork": True}
                    },
                    {"id": "agent1", "type": "agent", "agent_id": agents[0]},
                    {"id": "agent2", "type": "agent", "agent_id": agents[1]},
                    {"id": "agent3", "type": "agent", "agent_id": agents[2]},
                    {
                        "id": "parallel_join",
                        "type": "gateway",
                        "gateway_type": "parallel",
                        "config": {"is_join": True}
                    },
                    {"id": "end", "type": "end"},
                ],
                "edges": [
                    {"source": "start", "target": "parallel_fork"},
                    {"source": "parallel_fork", "target": "agent1"},
                    {"source": "parallel_fork", "target": "agent2"},
                    {"source": "parallel_fork", "target": "agent3"},
                    {"source": "agent1", "target": "parallel_join"},
                    {"source": "agent2", "target": "parallel_join"},
                    {"source": "agent3", "target": "parallel_join"},
                    {"source": "parallel_join", "target": "end"},
                ],
            },
        })

        assert workflow_response.status_code == 200
        workflow_id = workflow_response.json()["id"]

        # 執行工作流
        execute_response = await client.post(
            f"/api/v1/workflows/{workflow_id}/execute",
            json={"message": "Process this in parallel"},
        )

        assert execute_response.status_code == 200
```

---

## 完成定義 (Definition of Done)

1. **功能完成**
   - [ ] ConcurrentExecutor 支援 4 種並行模式
   - [ ] ParallelGateway 支援 Fork/Join
   - [ ] 死鎖檢測正常運作
   - [ ] 超時處理正確

2. **測試完成**
   - [ ] 單元測試覆蓋率 >= 80%
   - [ ] 並行執行集成測試通過
   - [ ] 死鎖場景測試通過
   - [ ] 超時場景測試通過

3. **文檔完成**
   - [ ] 並行執行 API 文檔
   - [ ] Gateway 配置指南
   - [ ] 最佳實踐文檔

---

## 相關文檔

- [Phase 2 Overview](./README.md)
- [Sprint 8 Plan](./sprint-8-plan.md) - 後續 Sprint
- [Phase 1 Sprint 1](../sprint-1-plan.md) - 順序執行基礎
