# Sprint 13: 基礎設施準備 - Agent Framework 整合基礎

**Sprint 目標**: 建立 Phase 3 重構所需的基礎設施和適配層
**週期**: Week 27-28 (2 週)
**Story Points**: 34 點
**Phase 3 功能**: P3-F0 (基礎設施)

---

## Sprint 概覽

### 目標
1. 建立 Agent Framework API wrapper 層
2. 整合 WorkflowBuilder 基礎設施
3. 實現 CheckpointStorage 適配器
4. 建立測試框架和 mock 工具
5. 編寫遷移指南文檔

### 成功標準
- [ ] 可以 import 所有 Agent Framework 核心 API
- [ ] WorkflowBuilder 基礎功能可用
- [ ] Checkpoint 可正確保存和恢復
- [ ] 測試框架支持 mock Agent Framework 組件
- [ ] 遷移指南文檔完成

---

## 架構概念

### Agent Framework 整合層

```
┌─────────────────────────────────────────────────────────────────┐
│                    IPA Platform 應用層                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │               Wrapper Layer (新建)                           │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │ │
│  │  │ Concurrent  │ │  Handoff    │ │    GroupChat        │   │ │
│  │  │  Adapter    │ │  Adapter    │ │     Adapter         │   │ │
│  │  └──────┬──────┘ └──────┬──────┘ └──────────┬──────────┘   │ │
│  │         │               │                    │              │ │
│  │  ┌──────┴──────┐ ┌──────┴──────┐ ┌──────────┴──────────┐   │ │
│  │  │ Magentic    │ │  Workflow   │ │   Checkpoint        │   │ │
│  │  │  Adapter    │ │  Executor   │ │    Storage          │   │ │
│  │  └──────┬──────┘ └──────┬──────┘ └──────────┬──────────┘   │ │
│  └─────────┼───────────────┼────────────────────┼──────────────┘ │
│            │               │                    │                │
├────────────┼───────────────┼────────────────────┼────────────────┤
│            │               │                    │                │
│  ┌─────────┴───────────────┴────────────────────┴──────────────┐ │
│  │              Agent Framework Core API                        │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │ │
│  │  │ Concurrent  │ │  Handoff    │ │    GroupChat        │   │ │
│  │  │  Builder    │ │  Builder    │ │     Builder         │   │ │
│  │  └─────────────┘ └─────────────┘ └─────────────────────┘   │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │ │
│  │  │ Magentic    │ │  Workflow   │ │   Checkpoint        │   │ │
│  │  │  Builder    │ │  Executor   │ │    Storage          │   │ │
│  │  └─────────────┘ └─────────────┘ └─────────────────────┘   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## User Stories

### S13-1: Agent Framework API Wrapper 層 (8 點)

**描述**: 建立包裝層以隔離 Agent Framework API 變更的影響。

**驗收標準**:
- [ ] 建立 `backend/src/integrations/agent_framework/` 模組
- [ ] 提供統一的 API 入口
- [ ] 支持版本適配
- [ ] 異常處理統一

**技術任務**:

```python
# backend/src/integrations/agent_framework/__init__.py
"""
Agent Framework Integration Layer

提供與 Microsoft Agent Framework 的整合介面
"""

from .builders import (
    ConcurrentBuilderAdapter,
    GroupChatBuilderAdapter,
    HandoffBuilderAdapter,
    MagenticBuilderAdapter,
    WorkflowExecutorAdapter,
)
from .checkpoint import CheckpointStorageAdapter
from .executor import ExecutorBase
from .workflow import WorkflowAdapter

__all__ = [
    "ConcurrentBuilderAdapter",
    "GroupChatBuilderAdapter",
    "HandoffBuilderAdapter",
    "MagenticBuilderAdapter",
    "WorkflowExecutorAdapter",
    "CheckpointStorageAdapter",
    "ExecutorBase",
    "WorkflowAdapter",
]
```

```python
# backend/src/integrations/agent_framework/base.py
"""
Base classes for Agent Framework integration
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

from agent_framework import (
    Workflow,
    WorkflowBuilder,
    Executor,
    WorkflowContext,
)

logger = logging.getLogger(__name__)


class BaseAdapter(ABC):
    """Base adapter class for Agent Framework components."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = config or {}
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the adapter."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources."""
        pass

    @property
    def is_initialized(self) -> bool:
        return self._initialized


class BuilderAdapter(BaseAdapter):
    """Base class for Builder adapters."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._builder = None
        self._workflow = None

    @abstractmethod
    def build(self) -> Workflow:
        """Build the workflow."""
        pass

    async def run(self, input_data: Any) -> Any:
        """Run the workflow."""
        if not self._workflow:
            self._workflow = self.build()
        return await self._workflow.run(input_data)
```

---

### S13-2: WorkflowBuilder 基礎整合 (8 點)

**描述**: 整合 Agent Framework WorkflowBuilder 作為所有工作流的基礎。

**驗收標準**:
- [ ] WorkflowBuilder 可創建基本工作流
- [ ] Edge routing 正確工作
- [ ] Executor 註冊和調用正常
- [ ] 事件系統整合

**技術任務**:

```python
# backend/src/integrations/agent_framework/workflow.py
"""
Workflow adapter for Agent Framework
"""

from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass, field

from agent_framework import (
    Workflow,
    WorkflowBuilder,
    WorkflowRunResult,
    Executor,
    Edge,
    SingleEdgeGroup,
    FanOutEdgeGroup,
    FanInEdgeGroup,
)


@dataclass
class WorkflowConfig:
    """Configuration for workflow creation."""
    id: str
    name: str
    description: str = ""
    max_iterations: int = 100
    enable_checkpointing: bool = False
    checkpoint_storage: Optional[Any] = None


class WorkflowAdapter:
    """
    Adapter for Agent Framework Workflow.

    提供簡化的 API 來創建和管理工作流。
    """

    def __init__(self, config: WorkflowConfig):
        self._config = config
        self._builder = WorkflowBuilder(id=config.id)
        self._executors: Dict[str, Executor] = {}
        self._edges: List[Edge] = []
        self._workflow: Optional[Workflow] = None

    def add_executor(self, executor: Executor) -> "WorkflowAdapter":
        """Add an executor to the workflow."""
        self._executors[executor.id] = executor
        return self

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        condition: Optional[str] = None,
    ) -> "WorkflowAdapter":
        """Add an edge between executors."""
        edge = Edge(
            source_id=source_id,
            target_id=target_id,
            condition=condition,
        )
        self._edges.append(edge)
        return self

    def add_fan_out_edges(
        self,
        source_id: str,
        target_ids: List[str],
    ) -> "WorkflowAdapter":
        """Add fan-out edges for parallel execution."""
        for target_id in target_ids:
            self.add_edge(source_id, target_id)
        return self

    def add_fan_in_edges(
        self,
        source_ids: List[str],
        target_id: str,
    ) -> "WorkflowAdapter":
        """Add fan-in edges for joining parallel branches."""
        for source_id in source_ids:
            self.add_edge(source_id, target_id)
        return self

    def build(self) -> Workflow:
        """Build the workflow."""
        # Add executors
        for executor in self._executors.values():
            self._builder.add_executor(executor)

        # Add edges
        for edge in self._edges:
            self._builder.add_edge(
                SingleEdgeGroup(
                    source_id=edge.source_id,
                    target_id=edge.target_id,
                )
            )

        # Configure checkpointing if enabled
        if self._config.enable_checkpointing and self._config.checkpoint_storage:
            self._builder.with_checkpointing(self._config.checkpoint_storage)

        self._workflow = self._builder.build()
        return self._workflow

    async def run(self, input_data: Any) -> WorkflowRunResult:
        """Run the workflow."""
        if not self._workflow:
            self.build()
        return await self._workflow.run(input_data)

    async def run_stream(self, input_data: Any):
        """Run the workflow with streaming events."""
        if not self._workflow:
            self.build()
        async for event in self._workflow.run_stream(input_data):
            yield event
```

---

### S13-3: CheckpointStorage 適配器 (8 點)

**描述**: 實現 CheckpointStorage 適配器，整合現有的數據庫存儲。

**驗收標準**:
- [ ] 支持 PostgreSQL 存儲
- [ ] 支持 Redis 緩存
- [ ] 實現 save/load/delete 操作
- [ ] 支持檢查點列表和查詢

**技術任務**:

```python
# backend/src/integrations/agent_framework/checkpoint.py
"""
Checkpoint storage adapter for Agent Framework
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import uuid

from agent_framework import (
    CheckpointStorage,
    WorkflowCheckpoint,
)

from src.infrastructure.database.repositories import BaseRepository


class PostgresCheckpointStorage(CheckpointStorage):
    """
    PostgreSQL-based checkpoint storage.

    Implements Agent Framework CheckpointStorage interface
    using PostgreSQL as the backend.
    """

    def __init__(self, repository: BaseRepository):
        self._repository = repository

    async def save(
        self,
        checkpoint_id: str,
        workflow_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkflowCheckpoint:
        """Save a checkpoint."""
        checkpoint = WorkflowCheckpoint(
            id=checkpoint_id,
            workflow_id=workflow_id,
            data=data,
            metadata=metadata or {},
            created_at=datetime.utcnow(),
        )

        await self._repository.create({
            "id": checkpoint_id,
            "workflow_id": workflow_id,
            "data": json.dumps(data),
            "metadata": json.dumps(metadata or {}),
            "created_at": datetime.utcnow(),
        })

        return checkpoint

    async def load(
        self,
        checkpoint_id: str,
    ) -> Optional[WorkflowCheckpoint]:
        """Load a checkpoint by ID."""
        record = await self._repository.get_by_id(checkpoint_id)
        if not record:
            return None

        return WorkflowCheckpoint(
            id=record["id"],
            workflow_id=record["workflow_id"],
            data=json.loads(record["data"]),
            metadata=json.loads(record["metadata"]),
            created_at=record["created_at"],
        )

    async def delete(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint."""
        return await self._repository.delete(checkpoint_id)

    async def list_checkpoints(
        self,
        workflow_id: str,
        limit: int = 100,
    ) -> List[WorkflowCheckpoint]:
        """List checkpoints for a workflow."""
        records = await self._repository.find_by_workflow_id(
            workflow_id=workflow_id,
            limit=limit,
        )

        return [
            WorkflowCheckpoint(
                id=r["id"],
                workflow_id=r["workflow_id"],
                data=json.loads(r["data"]),
                metadata=json.loads(r["metadata"]),
                created_at=r["created_at"],
            )
            for r in records
        ]


class RedisCheckpointCache:
    """
    Redis-based checkpoint cache for fast access.

    Provides caching layer on top of PostgresCheckpointStorage.
    """

    def __init__(self, redis_client, ttl_seconds: int = 3600):
        self._redis = redis_client
        self._ttl = ttl_seconds

    def _key(self, checkpoint_id: str) -> str:
        return f"checkpoint:{checkpoint_id}"

    async def get(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Get cached checkpoint."""
        data = await self._redis.get(self._key(checkpoint_id))
        if data:
            return json.loads(data)
        return None

    async def set(self, checkpoint_id: str, data: Dict[str, Any]) -> None:
        """Cache checkpoint."""
        await self._redis.setex(
            self._key(checkpoint_id),
            self._ttl,
            json.dumps(data),
        )

    async def delete(self, checkpoint_id: str) -> None:
        """Remove from cache."""
        await self._redis.delete(self._key(checkpoint_id))


class CachedCheckpointStorage(CheckpointStorage):
    """
    Checkpoint storage with caching layer.

    Combines PostgreSQL storage with Redis caching.
    """

    def __init__(
        self,
        storage: PostgresCheckpointStorage,
        cache: RedisCheckpointCache,
    ):
        self._storage = storage
        self._cache = cache

    async def save(
        self,
        checkpoint_id: str,
        workflow_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkflowCheckpoint:
        """Save checkpoint to storage and cache."""
        checkpoint = await self._storage.save(
            checkpoint_id, workflow_id, data, metadata
        )
        await self._cache.set(checkpoint_id, {
            "workflow_id": workflow_id,
            "data": data,
            "metadata": metadata,
        })
        return checkpoint

    async def load(
        self,
        checkpoint_id: str,
    ) -> Optional[WorkflowCheckpoint]:
        """Load from cache first, then storage."""
        # Try cache first
        cached = await self._cache.get(checkpoint_id)
        if cached:
            return WorkflowCheckpoint(
                id=checkpoint_id,
                workflow_id=cached["workflow_id"],
                data=cached["data"],
                metadata=cached.get("metadata", {}),
                created_at=datetime.utcnow(),  # Approximate
            )

        # Fall back to storage
        checkpoint = await self._storage.load(checkpoint_id)
        if checkpoint:
            await self._cache.set(checkpoint_id, {
                "workflow_id": checkpoint.workflow_id,
                "data": checkpoint.data,
                "metadata": checkpoint.metadata,
            })
        return checkpoint

    async def delete(self, checkpoint_id: str) -> bool:
        """Delete from both cache and storage."""
        await self._cache.delete(checkpoint_id)
        return await self._storage.delete(checkpoint_id)

    async def list_checkpoints(
        self,
        workflow_id: str,
        limit: int = 100,
    ) -> List[WorkflowCheckpoint]:
        """List checkpoints (from storage)."""
        return await self._storage.list_checkpoints(workflow_id, limit)
```

---

### S13-4: 測試框架和 Mock (5 點)

**描述**: 建立支持 Agent Framework 組件的測試框架和 mock 工具。

**驗收標準**:
- [ ] Mock Executor 可模擬 Agent 行為
- [ ] Mock WorkflowContext 支持測試
- [ ] Mock CheckpointStorage 可用
- [ ] 提供測試輔助函數

**技術任務**:

```python
# tests/mocks/agent_framework_mocks.py
"""
Mock implementations for Agent Framework testing
"""

from typing import Any, Dict, List, Optional, Callable
from unittest.mock import AsyncMock, MagicMock
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

from agent_framework import (
    Executor,
    WorkflowContext,
    CheckpointStorage,
    WorkflowCheckpoint,
    handler,
)


class MockExecutor(Executor):
    """
    Mock executor for testing.

    可配置返回值、延遲和錯誤行為。
    """

    def __init__(
        self,
        id: str,
        return_value: Any = None,
        delay_seconds: float = 0,
        raise_error: Optional[Exception] = None,
    ):
        super().__init__(id=id)
        self._return_value = return_value
        self._delay = delay_seconds
        self._error = raise_error
        self._call_count = 0
        self._call_history: List[Dict[str, Any]] = []

    @handler
    async def handle_input(self, input_data: Any, ctx: WorkflowContext) -> None:
        """Handle input and produce output."""
        self._call_count += 1
        self._call_history.append({
            "input": input_data,
            "timestamp": datetime.utcnow(),
        })

        if self._delay > 0:
            await asyncio.sleep(self._delay)

        if self._error:
            raise self._error

        await ctx.yield_output(self._return_value or input_data)

    @property
    def call_count(self) -> int:
        return self._call_count

    @property
    def call_history(self) -> List[Dict[str, Any]]:
        return self._call_history

    def reset(self) -> None:
        self._call_count = 0
        self._call_history = []


class MockWorkflowContext:
    """
    Mock workflow context for testing.
    """

    def __init__(self):
        self.outputs: List[Any] = []
        self.messages: List[Dict[str, Any]] = []
        self.state: Dict[str, Any] = {}

    async def yield_output(self, output: Any) -> None:
        """Mock yield_output."""
        self.outputs.append(output)

    async def send_message(
        self,
        message: Any,
        target_id: Optional[str] = None,
    ) -> None:
        """Mock send_message."""
        self.messages.append({
            "message": message,
            "target_id": target_id,
        })

    async def set_state(self, key: str, value: Any) -> None:
        """Mock set_state."""
        self.state[key] = value

    async def get_state(self, key: str) -> Any:
        """Mock get_state."""
        return self.state.get(key)


class MockCheckpointStorage(CheckpointStorage):
    """
    In-memory checkpoint storage for testing.
    """

    def __init__(self):
        self._checkpoints: Dict[str, WorkflowCheckpoint] = {}

    async def save(
        self,
        checkpoint_id: str,
        workflow_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkflowCheckpoint:
        checkpoint = WorkflowCheckpoint(
            id=checkpoint_id,
            workflow_id=workflow_id,
            data=data,
            metadata=metadata or {},
            created_at=datetime.utcnow(),
        )
        self._checkpoints[checkpoint_id] = checkpoint
        return checkpoint

    async def load(
        self,
        checkpoint_id: str,
    ) -> Optional[WorkflowCheckpoint]:
        return self._checkpoints.get(checkpoint_id)

    async def delete(self, checkpoint_id: str) -> bool:
        if checkpoint_id in self._checkpoints:
            del self._checkpoints[checkpoint_id]
            return True
        return False

    async def list_checkpoints(
        self,
        workflow_id: str,
        limit: int = 100,
    ) -> List[WorkflowCheckpoint]:
        return [
            cp for cp in self._checkpoints.values()
            if cp.workflow_id == workflow_id
        ][:limit]

    def clear(self) -> None:
        """Clear all checkpoints."""
        self._checkpoints = {}


# Pytest fixtures
import pytest

@pytest.fixture
def mock_executor():
    """Create a mock executor."""
    def _create(
        id: str = "test-executor",
        return_value: Any = {"status": "ok"},
        delay: float = 0,
        error: Optional[Exception] = None,
    ):
        return MockExecutor(
            id=id,
            return_value=return_value,
            delay_seconds=delay,
            raise_error=error,
        )
    return _create

@pytest.fixture
def mock_context():
    """Create a mock workflow context."""
    return MockWorkflowContext()

@pytest.fixture
def mock_checkpoint_storage():
    """Create a mock checkpoint storage."""
    return MockCheckpointStorage()
```

---

### S13-5: 文檔和遷移指南 (5 點)

**描述**: 編寫遷移指南和 API 參考文檔。

**驗收標準**:
- [ ] 遷移概述文檔完成
- [ ] API 映射表完成
- [ ] 代碼範例提供
- [ ] 常見問題解答

---

## 測試要求

### 單元測試

```python
# tests/unit/test_workflow_adapter.py
import pytest
from src.integrations.agent_framework.workflow import (
    WorkflowAdapter,
    WorkflowConfig,
)
from tests.mocks.agent_framework_mocks import MockExecutor, MockCheckpointStorage


class TestWorkflowAdapter:

    @pytest.mark.asyncio
    async def test_build_simple_workflow(self, mock_executor):
        """Test building a simple workflow."""
        config = WorkflowConfig(id="test-workflow", name="Test")
        adapter = WorkflowAdapter(config)

        executor = mock_executor(id="exec1", return_value={"result": "ok"})
        adapter.add_executor(executor)

        workflow = adapter.build()

        assert workflow is not None
        assert workflow.id == "test-workflow"

    @pytest.mark.asyncio
    async def test_run_workflow(self, mock_executor):
        """Test running a workflow."""
        config = WorkflowConfig(id="test-workflow", name="Test")
        adapter = WorkflowAdapter(config)

        executor = mock_executor(id="start", return_value={"processed": True})
        adapter.add_executor(executor)

        result = await adapter.run({"input": "test"})

        assert result is not None

    @pytest.mark.asyncio
    async def test_workflow_with_checkpointing(
        self,
        mock_executor,
        mock_checkpoint_storage,
    ):
        """Test workflow with checkpointing enabled."""
        config = WorkflowConfig(
            id="test-workflow",
            name="Test",
            enable_checkpointing=True,
            checkpoint_storage=mock_checkpoint_storage,
        )
        adapter = WorkflowAdapter(config)

        executor = mock_executor(id="exec1")
        adapter.add_executor(executor)

        workflow = adapter.build()

        assert workflow is not None
```

---

## 完成定義 (Definition of Done)

1. **功能完成**
   - [ ] Agent Framework API 可正常 import
   - [ ] WorkflowBuilder 基礎功能可用
   - [ ] CheckpointStorage 適配器完成
   - [ ] 測試 mock 工具完成

2. **測試完成**
   - [ ] 單元測試覆蓋率 >= 80%
   - [ ] 整合測試通過
   - [ ] Mock 工具測試通過

3. **文檔完成**
   - [ ] 遷移指南完成
   - [ ] API 參考文檔
   - [ ] 範例代碼

---

## 相關文檔

- [Phase 3 Overview](./README.md)
- [Sprint 14 Plan](./sprint-14-plan.md) - ConcurrentBuilder 重構
- [Phase 2 架構審查](../../../../claudedocs/PHASE2-ARCHITECTURE-REVIEW.md)
