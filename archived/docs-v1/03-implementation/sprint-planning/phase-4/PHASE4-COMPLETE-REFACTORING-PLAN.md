# Phase 4 完整重構計劃

**創建日期**: 2025-12-06
**目標**: 將所有自行實現的功能完整連接回官方 Microsoft Agent Framework 架構
**預計時程**: Sprint 20-25 (6 Sprints, 約 12 週)
**總預估點數**: 約 180 Story Points

---

## 執行摘要

### 重構目標

| 指標 | 當前值 | 目標值 | 改善幅度 |
|------|--------|--------|----------|
| **自行實現代碼** | 19,844 行 | < 3,000 行 | -85% |
| **官方 API 使用率** | 2.4% (5/205 文件) | > 80% | +3,200% |
| **重複功能** | 60-70% 重疊 | < 5% 重疊 | -90% |
| **技術債** | 高 | 低 | -75% |

### 重構範圍

```
需要重構的模組 (19,844 行):
├── domain/orchestration/groupchat/     3,853 行  → GroupChatBuilderAdapter
├── domain/orchestration/handoff/       3,341 行  → HandoffBuilderAdapter
├── domain/orchestration/nested/        4,138 行  → NestedWorkflowAdapter (新建)
├── domain/orchestration/planning/      3,156 行  → PlanningAdapter (新建)
├── domain/orchestration/memory/        2,017 行  → 官方 Memory API
├── domain/orchestration/multiturn/     1,842 行  → 官方 Checkpoint API
├── domain/orchestration/collaboration/ 1,497 行  → 整合到 GroupChat
└── domain/workflows/executors/         1,529 行  → ConcurrentBuilderAdapter
```

---

## Sprint 總覽

| Sprint | 名稱 | 點數 | 主要目標 |
|--------|------|------|----------|
| **Sprint 20** | GroupChat 完整遷移 | 34 pts | 將 GroupChat API 遷移到適配器 |
| **Sprint 21** | Handoff 完整遷移 | 32 pts | 將 Handoff API 遷移到適配器 |
| **Sprint 22** | Concurrent & Memory 遷移 | 28 pts | 並行執行器和記憶體遷移 |
| **Sprint 23** | Nested Workflow 重構 | 35 pts | 創建 NestedWorkflowAdapter |
| **Sprint 24** | Planning & Multi-turn | 30 pts | 動態規劃和多輪對話整合 |
| **Sprint 25** | 清理、測試、文檔 | 21 pts | 棄用舊代碼、完善測試和文檔 |
| **總計** | | **180 pts** | |

---

## Sprint 20: GroupChat 完整遷移 (34 pts)

### 目標
將 `domain/orchestration/groupchat/` 的所有功能遷移到 `GroupChatBuilderAdapter`，確保 API 層完全使用適配器。

### Story 列表

#### S20-1: 重構 GroupChat API 路由 (8 pts)

**範圍**: `api/v1/groupchat/routes.py`, `api/v1/planning/routes.py`

**修改前**:
```python
# api/v1/groupchat/routes.py
from domain.orchestration.groupchat.manager import GroupChatManager

@router.post("/create")
async def create_groupchat(request: GroupChatCreateRequest):
    manager = GroupChatManager(...)  # ❌ 直接使用自行實現
    return await manager.run(request.initial_message)
```

**修改後**:
```python
# api/v1/groupchat/routes.py
from integrations.agent_framework.builders.groupchat import GroupChatBuilderAdapter

@router.post("/create")
async def create_groupchat(request: GroupChatCreateRequest):
    adapter = GroupChatBuilderAdapter(
        id=request.id,
        participants=request.participants,
        selection_method=request.selection_method,
        max_rounds=request.max_rounds,
    )  # ✅ 使用適配器
    workflow = adapter.build()
    return await adapter.run(request.initial_message)
```

**驗證**:
- [ ] `grep "from domain.orchestration.groupchat" api/` 返回 0 結果
- [ ] 所有 GroupChat API 測試通過
- [ ] API 端點功能不變

---

#### S20-2: 整合 SpeakerSelector 到適配器 (8 pts)

**範圍**: 將 `domain/orchestration/groupchat/speaker_selector.py` 邏輯遷移

**目標**: 使用官方 `set_select_speakers_func()` 實現所有選擇策略

**修改內容**:
```python
# integrations/agent_framework/builders/groupchat.py

class GroupChatBuilderAdapter:
    def _create_speaker_selector(self) -> Callable:
        """將 IPA 選擇方法映射到官方 selector_fn"""

        if self._selection_method == SpeakerSelectionMethod.ROUND_ROBIN:
            def round_robin_selector(state: GroupChatStateSnapshot) -> str:
                participants = list(state.participants.keys())
                current_idx = state.round_number % len(participants)
                return participants[current_idx]
            return round_robin_selector

        elif self._selection_method == SpeakerSelectionMethod.RANDOM:
            def random_selector(state: GroupChatStateSnapshot) -> str:
                import random
                return random.choice(list(state.participants.keys()))
            return random_selector

        elif self._selection_method == SpeakerSelectionMethod.EXPERTISE:
            def expertise_selector(state: GroupChatStateSnapshot) -> str:
                # 保留 Phase 2 的專業能力匹配邏輯
                from domain.orchestration.groupchat.speaker_selector import (
                    ExpertiseMatcher
                )
                matcher = ExpertiseMatcher(state.participants)
                return matcher.select_best_match(state.current_topic)
            return expertise_selector

        # ... 其他方法
```

**驗證**:
- [ ] 所有 5 種選擇策略正常工作
- [ ] 測試覆蓋每種策略
- [ ] 效能基準測試通過

---

#### S20-3: 整合 Termination 條件 (5 pts)

**範圍**: 將 `domain/orchestration/groupchat/termination.py` 邏輯遷移

**修改內容**:
```python
# integrations/agent_framework/builders/groupchat.py

class GroupChatBuilderAdapter:
    def _create_termination_condition(self) -> Callable:
        """將 IPA 終止條件映射到官方 termination_condition"""

        conditions = []

        # 輪數限制
        if self._max_rounds:
            conditions.append(
                lambda state: state.round_number >= self._max_rounds
            )

        # 關鍵詞終止
        if self._termination_keywords:
            conditions.append(
                lambda state: any(
                    kw in state.last_message.content
                    for kw in self._termination_keywords
                )
            )

        # 共識達成終止
        if self._consensus_required:
            conditions.append(
                lambda state: self._check_consensus(state)
            )

        # 組合所有條件
        def combined_termination(state: GroupChatStateSnapshot) -> bool:
            return any(cond(state) for cond in conditions)

        return combined_termination
```

---

#### S20-4: 保留 Voting 系統作為擴展 (5 pts)

**範圍**: 將投票系統封裝為適配器擴展

**創建新文件**: `integrations/agent_framework/builders/groupchat_voting.py`

```python
from .groupchat import GroupChatBuilderAdapter
from domain.orchestration.groupchat.voting import VotingSystem, VotingMethod

class GroupChatVotingAdapter(GroupChatBuilderAdapter):
    """
    擴展 GroupChatBuilderAdapter，添加投票功能。

    這是 IPA Platform 的自定義功能，不在官方 API 中。
    通過擴展適配器模式保留此功能。
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._voting_system: Optional[VotingSystem] = None

    def with_voting(
        self,
        voting_method: VotingMethod = VotingMethod.MAJORITY,
        min_votes: int = 2,
    ) -> "GroupChatVotingAdapter":
        """啟用投票系統"""
        self._voting_system = VotingSystem(
            method=voting_method,
            min_votes=min_votes,
        )
        return self

    def _create_speaker_selector(self) -> Callable:
        base_selector = super()._create_speaker_selector()

        if not self._voting_system:
            return base_selector

        def voting_enhanced_selector(state: GroupChatStateSnapshot) -> str:
            # 先收集投票
            votes = self._voting_system.collect_votes(state)

            if votes:
                # 如果有投票結果，使用投票選出的發言者
                return self._voting_system.tally_and_select(votes)
            else:
                # 否則使用基礎選擇器
                return base_selector(state)

        return voting_enhanced_selector
```

---

#### S20-5: 遷移 GroupChat 測試 (5 pts)

**範圍**: 將測試從 domain 遷移到適配器

**測試文件**:
- `tests/unit/test_groupchat_adapter.py` (新建)
- `tests/integration/test_groupchat_api.py` (更新)

**測試清單**:
- [ ] 基本創建和執行測試
- [ ] 5 種選擇策略測試
- [ ] 終止條件測試
- [ ] 投票系統測試
- [ ] API 端點集成測試

---

#### S20-6: 標記舊代碼為 Deprecated (3 pts)

**範圍**: 標記 `domain/orchestration/groupchat/` 為棄用

**修改內容**:
```python
# domain/orchestration/groupchat/__init__.py

import warnings

warnings.warn(
    "domain.orchestration.groupchat 模組已棄用，將在 Sprint 25 移除。"
    "請使用 integrations.agent_framework.builders.groupchat 代替。"
    "遷移指南: docs/03-implementation/migration/groupchat-migration.md",
    DeprecationWarning,
    stacklevel=2,
)

# 保留導出以保持向後兼容
from .manager import GroupChatManager  # noqa: F401
from .speaker_selector import SpeakerSelector  # noqa: F401
```

---

### Sprint 20 完成標準

- [ ] `grep -r "from domain.orchestration.groupchat" api/` 返回 0 結果
- [ ] 所有 GroupChat 相關 API 測試通過
- [ ] 官方 API 使用驗證: `verify_official_api_usage.py` 通過
- [ ] 投票系統作為擴展正常工作
- [ ] 舊代碼標記為 deprecated

---

## Sprint 21: Handoff 完整遷移 (32 pts)

### 目標
將 `domain/orchestration/handoff/` 的所有功能遷移到 `HandoffBuilderAdapter`。

### Story 列表

#### S21-1: 設計政策映射層 (5 pts)

**目標**: 創建 `HandoffPolicyAdapter` 映射 Phase 2 政策到官方 API

```python
# integrations/agent_framework/builders/handoff_policy.py

from enum import Enum
from typing import Callable, Optional
from domain.orchestration.handoff.controller import HandoffPolicy as LegacyPolicy

class HandoffPolicyAdapter:
    """
    將 Phase 2 HandoffPolicy 映射到官方 API 的 interaction_mode 和 termination_condition。
    """

    @staticmethod
    def adapt(
        legacy_policy: LegacyPolicy,
        condition_evaluator: Optional[Callable] = None,
    ) -> dict:
        """
        返回適配後的配置字典。

        Returns:
            {
                "interaction_mode": str,
                "termination_condition": Optional[Callable],
            }
        """

        if legacy_policy == LegacyPolicy.IMMEDIATE:
            return {
                "interaction_mode": "autonomous",
                "termination_condition": None,
            }

        elif legacy_policy == LegacyPolicy.GRACEFUL:
            return {
                "interaction_mode": "human_in_loop",
                "termination_condition": None,
            }

        elif legacy_policy == LegacyPolicy.CONDITIONAL:
            if not condition_evaluator:
                raise ValueError("CONDITIONAL 政策需要提供 condition_evaluator")

            return {
                "interaction_mode": "autonomous",
                "termination_condition": lambda conv: condition_evaluator(conv),
            }

        else:
            raise ValueError(f"未知政策: {legacy_policy}")
```

---

#### S21-2: 整合 CapabilityMatcher (8 pts)

**目標**: 將能力匹配邏輯封裝為選擇器函數

```python
# integrations/agent_framework/builders/handoff.py

class HandoffBuilderAdapter:
    def with_capability_matching(
        self,
        capabilities: Dict[str, List[str]],
        matching_strategy: MatchStrategy = MatchStrategy.BEST_FIT,
    ) -> "HandoffBuilderAdapter":
        """
        啟用能力匹配功能。

        Args:
            capabilities: Agent ID -> 能力列表
            matching_strategy: 匹配策略
        """
        from domain.orchestration.handoff.capability_matcher import CapabilityMatcher

        matcher = CapabilityMatcher(
            capabilities=capabilities,
            strategy=matching_strategy,
        )

        def capability_selector(state) -> str:
            task = state.get("current_task", {})
            required_capabilities = task.get("required_capabilities", [])

            # 使用 Phase 2 的匹配邏輯
            best_match = matcher.find_best_match(required_capabilities)
            return best_match.agent_id

        self._custom_selector = capability_selector
        return self
```

---

#### S21-3: 整合 ContextTransfer (5 pts)

**目標**: 保留上下文傳遞邏輯

```python
# integrations/agent_framework/builders/handoff.py

class HandoffBuilderAdapter:
    def with_context_transfer(
        self,
        transfer_strategy: ContextTransferStrategy = ContextTransferStrategy.FULL,
        context_filter: Optional[Callable] = None,
    ) -> "HandoffBuilderAdapter":
        """
        配置上下文傳遞策略。
        """
        from domain.orchestration.handoff.context_transfer import ContextTransfer

        self._context_transfer = ContextTransfer(
            strategy=transfer_strategy,
            filter_fn=context_filter,
        )
        return self

    async def _prepare_handoff_context(self, source_state, target_agent):
        """在交接時準備上下文"""
        if self._context_transfer:
            return await self._context_transfer.prepare(source_state, target_agent)
        return source_state
```

---

#### S21-4: 重構 Handoff API 路由 (8 pts)

**範圍**: `api/v1/handoff/routes.py`

**修改前後對比**:
```python
# BEFORE
from domain.orchestration.handoff.controller import HandoffController

@router.post("/initiate")
async def initiate_handoff(request: HandoffRequest):
    controller = HandoffController(...)
    return await controller.initiate(request)

# AFTER
from integrations.agent_framework.builders.handoff import HandoffBuilderAdapter
from integrations.agent_framework.builders.handoff_policy import HandoffPolicyAdapter

@router.post("/initiate")
async def initiate_handoff(request: HandoffRequest):
    # 適配政策
    policy_config = HandoffPolicyAdapter.adapt(request.policy)

    adapter = HandoffBuilderAdapter(
        id=request.id,
        participants=request.participants,
        **policy_config,
    )

    if request.capability_matching:
        adapter.with_capability_matching(
            capabilities=request.capabilities,
            matching_strategy=request.matching_strategy,
        )

    if request.context_transfer:
        adapter.with_context_transfer(
            transfer_strategy=request.transfer_strategy,
        )

    workflow = adapter.build()
    return await adapter.run(request.initial_context)
```

---

#### S21-5: 遷移測試和文檔 (6 pts)

**測試文件**:
- `tests/unit/test_handoff_adapter.py`
- `tests/unit/test_handoff_policy_adapter.py`
- `tests/integration/test_handoff_api.py`

**文檔更新**:
- `docs/03-implementation/migration/handoff-migration.md`

---

### Sprint 21 完成標準

- [ ] `grep -r "from domain.orchestration.handoff" api/` 返回 0 結果
- [ ] 政策映射正確工作
- [ ] 能力匹配功能保留
- [ ] 上下文傳遞功能保留
- [ ] 所有 Handoff API 測試通過

---

## Sprint 22: Concurrent & Memory 遷移 (28 pts)

### 目標
將並行執行器和記憶體系統遷移到官方 API。

### Story 列表

#### S22-1: 重構 Concurrent 執行器 (8 pts)

**範圍**: `domain/workflows/executors/concurrent.py` → `ConcurrentBuilderAdapter`

```python
# BEFORE: domain/workflows/executors/concurrent.py 使用
from domain.workflows.executors.concurrent import ConcurrentExecutor

executor = ConcurrentExecutor(tasks=[task1, task2, task3])
results = await executor.execute_parallel()

# AFTER: 使用適配器
from integrations.agent_framework.builders.concurrent import ConcurrentBuilderAdapter

adapter = ConcurrentBuilderAdapter(
    id="concurrent-001",
    executors=[executor1, executor2, executor3],
)
adapter.with_aggregator(lambda results: merge_results(results))
workflow = adapter.build()
results = await adapter.run(input_data)
```

---

#### S22-2: 整合 ParallelGateway (6 pts)

**範圍**: 將 `parallel_gateway.py` 功能整合

```python
# integrations/agent_framework/builders/concurrent.py

class ConcurrentBuilderAdapter:
    def with_gateway_config(
        self,
        gateway_type: GatewayType = GatewayType.PARALLEL_SPLIT,
        join_condition: JoinCondition = JoinCondition.ALL,
        timeout: Optional[float] = None,
    ) -> "ConcurrentBuilderAdapter":
        """
        配置並行網關。

        使用官方 ConcurrentBuilder 實現，保留 Phase 2 的網關語義。
        """
        self._gateway_type = gateway_type
        self._join_condition = join_condition
        self._timeout = timeout

        # 根據 join_condition 設置官方 API 的 aggregator
        if join_condition == JoinCondition.ALL:
            self._aggregator = lambda results: all(results)
        elif join_condition == JoinCondition.ANY:
            self._aggregator = lambda results: any(results)
        elif join_condition == JoinCondition.FIRST:
            self._aggregator = lambda results: results[0]

        return self
```

---

#### S22-3: 遷移 Memory 系統 (8 pts)

**範圍**: `domain/orchestration/memory/` → 官方 Memory API

**目標**: 使用 `agent_framework` 的 Memory 功能替代自行實現

```python
# BEFORE: 自行實現的 Memory
from domain.orchestration.memory.redis_store import RedisMemoryStore
from domain.orchestration.memory.postgres_store import PostgresMemoryStore

# AFTER: 使用官方 API + 自定義後端
from agent_framework import Memory, MemoryStorage

class RedisMemoryStorage(MemoryStorage):
    """使用官方 MemoryStorage 接口，保留 Redis 後端"""

    def __init__(self, redis_client):
        self._redis = redis_client

    async def store(self, key: str, value: Any) -> None:
        await self._redis.set(key, json.dumps(value))

    async def retrieve(self, key: str) -> Optional[Any]:
        data = await self._redis.get(key)
        return json.loads(data) if data else None

    async def search(self, query: str, limit: int = 10) -> List[Any]:
        # 實現向量搜索或關鍵詞搜索
        pass

# 創建 Memory 實例
memory = Memory(storage=RedisMemoryStorage(redis_client))
```

---

#### S22-4: 測試和文檔 (6 pts)

**測試文件**:
- `tests/unit/test_concurrent_adapter.py`
- `tests/unit/test_memory_integration.py`
- `tests/integration/test_concurrent_api.py`

---

### Sprint 22 完成標準

- [ ] 所有並行執行使用 `ConcurrentBuilderAdapter`
- [ ] Memory 系統使用官方 API 接口
- [ ] `domain/workflows/executors/concurrent.py` 標記為 deprecated
- [ ] 測試覆蓋率 > 80%

---

## Sprint 23: Nested Workflow 重構 (35 pts)

### 目標
創建 `NestedWorkflowAdapter`，使用官方 Workflow 組合功能實現嵌套工作流。

### Story 列表

#### S23-1: 設計 NestedWorkflowAdapter 架構 (8 pts)

**新文件**: `integrations/agent_framework/builders/nested_workflow.py`

```python
from agent_framework import WorkflowBuilder, Workflow, WorkflowExecutor
from typing import Dict, List, Any, Optional
from domain.orchestration.nested.context_propagation import (
    ContextPropagation,
    ContextPropagationStrategy,
)
from domain.orchestration.nested.recursive_handler import RecursiveDepthTracker

class NestedWorkflowAdapter:
    """
    嵌套工作流適配器。

    使用官方 WorkflowBuilder 組合功能實現嵌套執行，
    同時保留 Phase 2 的上下文傳播和遞歸深度控制。
    """

    def __init__(
        self,
        id: str,
        max_depth: int = 5,
        context_strategy: ContextPropagationStrategy = ContextPropagationStrategy.INHERITED,
    ):
        self._id = id
        self._max_depth = max_depth
        self._context_strategy = context_strategy

        # 子工作流註冊表
        self._sub_workflows: Dict[str, WorkflowBuilder] = {}
        self._sub_adapters: Dict[str, Any] = {}  # 可以是任何 BuilderAdapter

        # Phase 2 邏輯保留
        self._depth_tracker = RecursiveDepthTracker(max_depth)
        self._context_propagator = ContextPropagation(context_strategy)

        # 官方 Builder
        self._main_builder: Optional[WorkflowBuilder] = None

    def add_sub_workflow(
        self,
        name: str,
        workflow: Union[Workflow, WorkflowBuilder, "BuilderAdapter"],
    ) -> "NestedWorkflowAdapter":
        """
        添加子工作流。

        支持:
        - 官方 Workflow 實例
        - 官方 WorkflowBuilder
        - 任何 BuilderAdapter (GroupChat, Handoff, Concurrent)
        """
        if isinstance(workflow, Workflow):
            self._sub_workflows[name] = workflow
        elif isinstance(workflow, WorkflowBuilder):
            self._sub_workflows[name] = workflow.build()
        elif hasattr(workflow, 'build'):
            # BuilderAdapter
            self._sub_adapters[name] = workflow
            self._sub_workflows[name] = workflow.build()
        else:
            raise TypeError(f"不支持的工作流類型: {type(workflow)}")

        return self

    def with_sequential_execution(
        self,
        order: List[str],
    ) -> "NestedWorkflowAdapter":
        """順序執行子工作流"""
        self._execution_order = order
        self._execution_mode = "sequential"
        return self

    def with_conditional_execution(
        self,
        conditions: Dict[str, Callable],
    ) -> "NestedWorkflowAdapter":
        """條件執行子工作流"""
        self._conditions = conditions
        self._execution_mode = "conditional"
        return self

    def build(self) -> Workflow:
        """構建嵌套工作流"""
        from agent_framework import SequentialBuilder

        if self._execution_mode == "sequential":
            builder = SequentialBuilder()
            for name in self._execution_order:
                sub_workflow = self._sub_workflows[name]
                builder.add_step(name, sub_workflow)
            return builder.build()

        elif self._execution_mode == "conditional":
            # 使用自定義執行邏輯
            return self._build_conditional_workflow()

        else:
            raise ValueError("請先設置執行模式")

    async def run(self, input_data: Any) -> Any:
        """執行嵌套工作流"""
        # 檢查遞歸深度
        if not self._depth_tracker.can_enter():
            raise RecursionError(f"超過最大遞歸深度: {self._max_depth}")

        self._depth_tracker.enter()
        try:
            # 準備上下文
            context = self._context_propagator.prepare(input_data)

            # 執行工作流
            workflow = self.build()
            result = await workflow.run(context)

            # 處理結果上下文
            return self._context_propagator.finalize(result)

        finally:
            self._depth_tracker.exit()
```

---

#### S23-2: 實現上下文傳播邏輯 (8 pts)

**保留**: `domain/orchestration/nested/context_propagation.py` 作為內部依賴

```python
# 保留 Phase 2 的上下文傳播邏輯，但透過適配器調用

class ContextPropagationStrategy(Enum):
    INHERITED = "inherited"    # 完全繼承父上下文
    ISOLATED = "isolated"      # 隔離，不繼承
    MERGED = "merged"          # 合併父子上下文
    FILTERED = "filtered"      # 過濾特定字段

class ContextPropagation:
    """上下文傳播管理器"""

    def prepare(self, parent_context: Dict) -> Dict:
        """準備子工作流的上下文"""
        if self._strategy == ContextPropagationStrategy.INHERITED:
            return parent_context.copy()
        elif self._strategy == ContextPropagationStrategy.ISOLATED:
            return {}
        elif self._strategy == ContextPropagationStrategy.MERGED:
            return {**parent_context, **self._additional_context}
        elif self._strategy == ContextPropagationStrategy.FILTERED:
            return {k: v for k, v in parent_context.items() if k in self._allowed_keys}

    def finalize(self, child_result: Any) -> Any:
        """處理子工作流的結果"""
        # 可以在這裡添加結果轉換邏輯
        return child_result
```

---

#### S23-3: 實現遞歸深度控制 (5 pts)

**保留**: `domain/orchestration/nested/recursive_handler.py` 作為安全機制

---

#### S23-4: 重構 Nested API 路由 (8 pts)

**範圍**: `api/v1/nested/routes.py` (如果存在)

```python
from integrations.agent_framework.builders.nested_workflow import NestedWorkflowAdapter
from integrations.agent_framework.builders.groupchat import GroupChatBuilderAdapter
from integrations.agent_framework.builders.handoff import HandoffBuilderAdapter

@router.post("/execute")
async def execute_nested_workflow(request: NestedWorkflowRequest):
    adapter = NestedWorkflowAdapter(
        id=request.id,
        max_depth=request.max_depth,
        context_strategy=request.context_strategy,
    )

    # 添加子工作流
    for sub in request.sub_workflows:
        if sub.type == "groupchat":
            sub_adapter = GroupChatBuilderAdapter(**sub.config)
        elif sub.type == "handoff":
            sub_adapter = HandoffBuilderAdapter(**sub.config)
        else:
            raise ValueError(f"未知子工作流類型: {sub.type}")

        adapter.add_sub_workflow(sub.name, sub_adapter)

    # 設置執行順序
    adapter.with_sequential_execution(request.execution_order)

    return await adapter.run(request.input_data)
```

---

#### S23-5: 測試和文檔 (6 pts)

**測試用例**:
- 基本嵌套執行
- 多層嵌套 (深度 = 3)
- 上下文傳播策略測試
- 遞歸深度限制測試
- 錯誤處理測試

---

### Sprint 23 完成標準

- [ ] `NestedWorkflowAdapter` 完整實現
- [ ] 上下文傳播正常工作
- [ ] 遞歸深度控制正常工作
- [ ] 可以嵌套 GroupChat、Handoff、Concurrent
- [ ] 測試覆蓋率 > 80%

---

## Sprint 24: Planning & Multi-turn (30 pts)

### 目標
評估並整合動態規劃和多輪對話功能。

### Story 列表

#### S24-1: 評估 Planning 模組 (5 pts)

**目標**: 分析 `domain/orchestration/planning/` 是否有對應官方 API

**分析結果預期**:
| 功能 | 官方 API 對應 | 建議 |
|------|---------------|------|
| DynamicPlanner | MagenticBuilder | 使用適配器 |
| TaskDecomposer | 無 | 保留為擴展 |
| DecisionEngine | 無 | 保留為擴展 |
| TrialError | 無 | 保留為擴展 |

---

#### S24-2: 創建 PlanningAdapter (10 pts)

**新文件**: `integrations/agent_framework/builders/planning.py`

```python
from agent_framework import MagenticBuilder
from domain.orchestration.planning.task_decomposer import TaskDecomposer
from domain.orchestration.planning.decision_engine import DecisionEngine

class PlanningAdapter:
    """
    動態規劃適配器。

    使用官方 MagenticBuilder 作為核心規劃引擎，
    擴展 Phase 2 的任務分解和決策引擎功能。
    """

    def __init__(self, id: str):
        self._id = id
        self._magentic_builder = MagenticBuilder()

        # Phase 2 擴展功能
        self._task_decomposer: Optional[TaskDecomposer] = None
        self._decision_engine: Optional[DecisionEngine] = None

    def with_task_decomposition(
        self,
        decomposition_strategy: DecompositionStrategy,
    ) -> "PlanningAdapter":
        """啟用任務分解功能"""
        self._task_decomposer = TaskDecomposer(strategy=decomposition_strategy)
        return self

    def with_decision_engine(
        self,
        decision_rules: List[DecisionRule],
    ) -> "PlanningAdapter":
        """啟用決策引擎"""
        self._decision_engine = DecisionEngine(rules=decision_rules)
        return self

    def build(self) -> Workflow:
        """構建規劃工作流"""
        return self._magentic_builder.build()

    async def run(self, task: str) -> Any:
        """執行動態規劃"""
        # 1. 任務分解
        if self._task_decomposer:
            subtasks = await self._task_decomposer.decompose(task)
        else:
            subtasks = [task]

        # 2. 使用官方 MagenticBuilder 執行
        workflow = self.build()
        results = []

        for subtask in subtasks:
            # 3. 決策引擎選擇策略
            if self._decision_engine:
                strategy = await self._decision_engine.decide(subtask)
                result = await workflow.run(subtask, strategy=strategy)
            else:
                result = await workflow.run(subtask)

            results.append(result)

        return self._aggregate_results(results)
```

---

#### S24-3: 遷移 Multi-turn 到 Checkpoint (8 pts)

**目標**: 使用官方 Checkpoint API 管理多輪對話狀態

```python
from agent_framework import CheckpointStorage, InMemoryCheckpointStorage

class MultiTurnAdapter:
    """
    多輪對話適配器。

    使用官方 Checkpoint API 管理對話狀態，
    保留 Phase 2 的會話管理語義。
    """

    def __init__(
        self,
        session_id: str,
        checkpoint_storage: Optional[CheckpointStorage] = None,
    ):
        self._session_id = session_id
        self._checkpoint_storage = checkpoint_storage or InMemoryCheckpointStorage()

        # 從 Phase 2 遷移的會話追蹤
        from domain.orchestration.multiturn.session_manager import SessionManager
        self._session_manager = SessionManager(session_id)

    async def add_turn(self, message: str) -> str:
        """添加一輪對話"""
        # 從 Checkpoint 恢復狀態
        state = await self._checkpoint_storage.load(self._session_id)

        if state:
            self._session_manager.restore(state)

        # 處理對話
        response = await self._session_manager.process_turn(message)

        # 保存 Checkpoint
        await self._checkpoint_storage.save(
            self._session_id,
            self._session_manager.get_state(),
        )

        return response
```

---

#### S24-4: 更新 API 路由 (4 pts)

---

#### S24-5: 測試和文檔 (3 pts)

---

### Sprint 24 完成標準

- [ ] PlanningAdapter 使用官方 MagenticBuilder
- [ ] 多輪對話使用官方 Checkpoint API
- [ ] 保留 Phase 2 的擴展功能
- [ ] 測試覆蓋完整

---

## Sprint 25: 清理、測試、文檔 (21 pts)

### 目標
移除棄用代碼、完善測試、更新所有文檔。

### Story 列表

#### S25-1: 移除 Deprecated 代碼 (8 pts)

**刪除範圍**:
```
domain/orchestration/
├── groupchat/        ❌ 刪除 (已遷移到適配器)
├── handoff/          ❌ 刪除 (已遷移到適配器)
├── collaboration/    ❌ 刪除 (已整合到 GroupChat)
├── nested/           ⚠️ 保留核心邏輯，刪除冗餘
├── planning/         ⚠️ 保留擴展功能，刪除冗餘
├── memory/           ⚠️ 保留後端實現，刪除接口層
└── multiturn/        ⚠️ 保留會話管理，刪除狀態存儲

domain/workflows/executors/
├── concurrent.py         ❌ 刪除 (已遷移到適配器)
├── concurrent_state.py   ❌ 刪除
└── parallel_gateway.py   ❌ 刪除
```

**預計刪除代碼量**: ~12,000 行

---

#### S25-2: 完善測試覆蓋 (5 pts)

**測試清單**:
- [ ] 所有適配器單元測試
- [ ] API 集成測試
- [ ] 端到端測試
- [ ] 性能基準測試
- [ ] 遷移兼容性測試

---

#### S25-3: 更新所有文檔 (5 pts)

**文檔更新**:
- [ ] `CLAUDE.md` - 更新架構說明
- [ ] `docs/02-architecture/technical-architecture.md` - 更新技術架構
- [ ] 創建 `docs/03-implementation/migration/` 遷移指南
- [ ] 更新 API 文檔
- [ ] 更新 README.md

---

#### S25-4: 最終驗證 (3 pts)

**驗證清單**:
- [ ] `python scripts/verify_official_api_usage.py` 通過
- [ ] 所有測試通過
- [ ] 無 deprecated 警告
- [ ] 代碼行數統計符合目標

---

### Sprint 25 完成標準

- [ ] 自行實現代碼 < 3,000 行
- [ ] 官方 API 使用率 > 80%
- [ ] 所有測試通過
- [ ] 文檔完整更新
- [ ] 無技術債遺留

---

## 風險管理

### 技術風險

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|----------|
| 官方 API 功能不足 | 中 | 高 | 保留擴展機制，透過適配器擴展 |
| 遷移引入 Bug | 高 | 高 | 嚴格測試 + 保留舊代碼 1 Sprint |
| 性能下降 | 低 | 中 | 性能基準測試對比 |
| API 破壞性變更 | 低 | 中 | API 層接口保持不變 |

### 組織風險

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|----------|
| 時間壓力 | 高 | 中 | 分階段執行，允許調整 |
| 知識流失 | 低 | 高 | 完整文檔 + 代碼審查 |

---

## 成功指標

### 定量指標

| 指標 | 當前值 | Sprint 22 | Sprint 24 | Sprint 25 |
|------|--------|-----------|-----------|-----------|
| 自行實現代碼 | 19,844 | 11,000 | 5,000 | < 3,000 |
| 官方 API 使用率 | 2.4% | 40% | 70% | > 80% |
| 重複代碼 | 60-70% | 30% | 10% | < 5% |
| 測試覆蓋率 | 分散 | 60% | 75% | > 80% |

### 定性指標

- [ ] 所有新功能使用官方 API
- [ ] 官方 API 升級路徑清晰
- [ ] 團隊對架構達成共識
- [ ] 技術文檔完整

---

## 附錄

### A. 驗證腳本更新

更新 `backend/scripts/verify_official_api_usage.py`:

```python
#!/usr/bin/env python3
"""Phase 4 完整驗證腳本"""

import subprocess
import sys
from pathlib import Path

def check_domain_usage():
    """檢查 API 層是否還在直接使用 domain/orchestration"""
    result = subprocess.run(
        ["grep", "-r", "from domain.orchestration", "api/"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent / "src",
    )

    if result.stdout:
        print("❌ API 層仍在使用 domain/orchestration:")
        print(result.stdout)
        return False

    print("✅ API 層已完全遷移到適配器")
    return True

def check_adapter_coverage():
    """檢查適配器覆蓋率"""
    adapters = [
        "concurrent.py",
        "groupchat.py",
        "handoff.py",
        "magentic.py",
        "workflow_executor.py",
        "nested_workflow.py",  # Sprint 23 新增
        "planning.py",          # Sprint 24 新增
    ]

    adapter_path = Path(__file__).parent.parent / "src/integrations/agent_framework/builders"

    missing = []
    for adapter in adapters:
        if not (adapter_path / adapter).exists():
            missing.append(adapter)

    if missing:
        print(f"❌ 缺少適配器: {missing}")
        return False

    print(f"✅ 所有 {len(adapters)} 個適配器已實現")
    return True

def main():
    checks = [
        ("Domain 使用檢查", check_domain_usage),
        ("適配器覆蓋檢查", check_adapter_coverage),
    ]

    passed = 0
    for name, check in checks:
        print(f"\n=== {name} ===")
        if check():
            passed += 1

    print(f"\n{'='*50}")
    print(f"結果: {passed}/{len(checks)} 通過")

    return 0 if passed == len(checks) else 1

if __name__ == "__main__":
    sys.exit(main())
```

### B. 相關文檔

- 執行摘要: `docs/03-implementation/sprint-execution/EXECUTIVE-SUMMARY-ARCHITECTURE-AUDIT.md`
- 完整分析: `docs/03-implementation/sprint-execution/phase-3-architecture-comprehensive-analysis.md`
- Sprint 19 清單: `docs/03-implementation/sprint-planning/phase-3/sprint-19-checklist.md`

---

**報告生成**: Claude Code
**版本**: 1.0
**最後更新**: 2025-12-06
