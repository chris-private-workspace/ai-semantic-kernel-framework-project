# Deprecated Modules Reference

**版本**: 2.7
**更新日期**: 2025-12-08
**狀態**: Phase 6 - Sprint 32 In Progress

---

## 概述

本文件記錄 IPA Platform 中已棄用的模組及其對應的替代方案。所有棄用模組都會在運行時發出 `DeprecationWarning`，並將在未來版本中移除。

### Sprint 32 更新摘要

- ✅ `groupchat/routes.py` 會話端點已遷移至 `MultiTurnAPIService`
- ✅ `domain.orchestration.multiturn` 導入已從 GroupChat API 移除
- ✅ `domain.orchestration.memory` 導入已從 GroupChat API 移除
- ✅ 創建 `multiturn_service.py` 作為 API 兼容包裝器
- ✅ 8 個 Session 端點完成遷移

### Sprint 31 更新摘要

- ✅ `domain.agents.service` 中的官方 API 導入已移至 `AgentExecutorAdapter`
- ✅ `domain.workflows.executors.ConcurrentStateManager` 已完全棄用
- ✅ `domain.workflows.deadlock_detector` 已完全棄用，功能由適配器內部處理
- ✅ 所有 Concurrent API routes 已遷移至使用 `ConcurrentAPIService`

---

## 棄用模組清單

### 1. domain.orchestration (根模組)

**棄用版本**: Sprint 30
**替代方案**: `integrations.agent_framework.builders`

```python
# 舊方式 (已棄用)
from src.domain.orchestration import ...

# 新方式 (推薦)
from src.integrations.agent_framework.builders import (
    GroupChatBuilderAdapter,
    HandoffBuilderAdapter,
    ConcurrentBuilderAdapter,
    NestedWorkflowAdapter,
    PlanningAdapter,
)
```

---

### 2. domain.orchestration.multiturn

**棄用版本**: Sprint 30
**遷移完成**: Sprint 32
**替代方案**: `integrations.agent_framework.multiturn`

| 舊類/函數 | 新適配器 | 狀態 |
|-----------|----------|------|
| `MultiTurnSessionManager` | `MultiTurnAdapter` | ✅ |
| `MultiTurnSession` | `SessionInfo` | ✅ |
| `TurnTracker` | `TurnTracker` (內建) | ✅ |
| `SessionContextManager` | `ContextManager` (內建) | ✅ |
| `SessionStatus` | `SessionState` | ✅ |

**Sprint 32 API 遷移**:

```python
# GroupChat API 使用方式 (Sprint 32)
from src.api.v1.groupchat.multiturn_service import (
    MultiTurnAPIService,
    MultiTurnSession,
    SessionStatus,
    get_multiturn_service,
)

# 或直接使用適配器
from src.integrations.agent_framework.multiturn import (
    MultiTurnAdapter,
    SessionState,
    Message,
    TurnResult,
    create_multiturn_adapter,
)
```

---

### 3. domain.orchestration.memory

**棄用版本**: Sprint 30
**替代方案**: `integrations.agent_framework.memory`

| 舊類/函數 | 新適配器 |
|-----------|----------|
| `ConversationMemoryStore` | `MemoryStorageAdapter` |
| `InMemoryConversationMemoryStore` | `InMemoryStorageAdapter` |
| `RedisConversationMemoryStore` | `RedisStorageAdapter` |
| `PostgresConversationMemoryStore` | `PostgresStorageAdapter` |

```python
# 舊方式 (已棄用)
from src.domain.orchestration.memory import (
    ConversationMemoryStore,
    InMemoryConversationMemoryStore,
)

# 新方式 (推薦)
from src.integrations.agent_framework.memory import (
    MemoryStorageAdapter,
    InMemoryStorageAdapter,
)
```

---

### 4. domain.orchestration.planning

**棄用版本**: Sprint 30
**替代方案**: `integrations.agent_framework.builders.planning`

| 舊類/函數 | 新適配器 |
|-----------|----------|
| `TaskDecomposer` | `TaskDecomposerAdapter` |
| `DynamicPlanner` | `DynamicPlannerAdapter` |
| `AutonomousDecisionEngine` | `PlanningAdapter.decide()` |
| `TrialAndErrorEngine` | `PlanningAdapter.trial_run()` |

```python
# 舊方式 (已棄用)
from src.domain.orchestration.planning import (
    TaskDecomposer,
    DynamicPlanner,
)

# 新方式 (推薦)
from src.integrations.agent_framework.builders import PlanningAdapter
from src.integrations.agent_framework.builders.planning import (
    TaskDecomposerAdapter,
    DynamicPlannerAdapter,
)
```

---

### 5. domain.orchestration.nested

**棄用版本**: Sprint 30
**替代方案**: `integrations.agent_framework.builders.nested_workflow`

| 舊類/函數 | 新適配器 |
|-----------|----------|
| `NestedWorkflowManager` | `NestedWorkflowAdapter` |
| `SubWorkflowExecutor` | `NestedWorkflowAdapter.execute_sub()` |
| `RecursivePatternHandler` | `NestedWorkflowAdapter.handle_recursive()` |
| `WorkflowCompositionBuilder` | `CompositionBuilderAdapter` |
| `ContextPropagator` | `NestedWorkflowAdapter.propagate_context()` |

```python
# 舊方式 (已棄用)
from src.domain.orchestration.nested import (
    NestedWorkflowManager,
    WorkflowCompositionBuilder,
)

# 新方式 (推薦)
from src.integrations.agent_framework.builders import NestedWorkflowAdapter
from src.integrations.agent_framework.builders.nested_workflow import (
    CompositionBuilderAdapter,
)
```

---

### 6. domain.workflows.executors (部分)

**棄用版本**: Sprint 25 (擴展於 Sprint 31)
**替代方案**: `integrations.agent_framework.builders.concurrent`

| 舊類/函數 | 新適配器 | 備註 |
|-----------|----------|------|
| `ConcurrentExecutor` | `ConcurrentBuilderAdapter` | 已棄用 |
| `ConcurrentStateManager` | `ConcurrentAPIService` 內部管理 | Sprint 31 完全棄用 |
| `ParallelGateway` | `ConcurrentBuilderAdapter.fan_out/fan_in` | 已棄用 |
| `ApprovalGateway` | 保留 | 核心功能，未棄用 |

```python
# 舊方式 (已棄用)
from src.domain.workflows.executors import (
    ConcurrentExecutor,
    ConcurrentStateManager,  # Sprint 31 完全棄用
    ParallelGateway,
)

# 新方式 (推薦)
from src.integrations.agent_framework.builders import ConcurrentBuilderAdapter
from src.api.v1.concurrent.adapter_service import ConcurrentAPIService

# ApprovalGateway 仍然可用
from src.domain.workflows.executors import ApprovalGateway
```

---

### 7. domain.workflows.deadlock_detector

**棄用版本**: Sprint 31
**替代方案**: 適配器內部處理 (無需外部導入)

| 舊類/函數 | 新適配器 | 備註 |
|-----------|----------|------|
| `DeadlockDetector` | 適配器內部處理 | Sprint 31 完全棄用 |
| `get_deadlock_detector()` | 不需要 | 功能由適配器自動提供 |

```python
# 舊方式 (已棄用)
from src.domain.workflows.deadlock_detector import (
    DeadlockDetector,
    get_deadlock_detector,
)

# 新方式 (推薦)
# 無需導入 - 死鎖檢測由 ConcurrentBuilderAdapter 內部處理
from src.integrations.agent_framework.builders import ConcurrentBuilderAdapter
```

---

### 8. domain.agents.service 官方 API 導入

**棄用版本**: Sprint 31
**替代方案**: `integrations.agent_framework.builders.agent_executor`

| 舊導入 | 新適配器 | 備註 |
|--------|----------|------|
| `agent_framework.ChatAgent` | `AgentExecutorAdapter` | Sprint 31 集中 |
| `agent_framework.ChatMessage` | `AgentExecutorAdapter` | Sprint 31 集中 |
| `agent_framework.Role` | `AgentExecutorAdapter` | Sprint 31 集中 |
| `AzureOpenAIResponsesClient` | `AgentExecutorAdapter` | Sprint 31 集中 |

```python
# 舊方式 (已棄用) - 在 domain 層直接導入官方 API
from agent_framework import ChatAgent, ChatMessage, Role
from agent_framework.azure import AzureOpenAIResponsesClient

# 新方式 (推薦) - 透過適配器使用
from src.integrations.agent_framework.builders import (
    AgentExecutorAdapter,
    AgentExecutorConfig,
    create_agent_executor_adapter,
)
```

---

## 遷移指南

### 步驟 1: 識別棄用導入

運行以下命令識別使用棄用模組的文件：

```bash
cd backend
grep -r "from src.domain.orchestration" src/api/
```

### 步驟 2: 更新導入語句

將舊的導入語句替換為新的適配器導入。

### 步驟 3: 更新實例化代碼

適配器通常提供相同的接口，但可能需要調整初始化參數。

### 步驟 4: 測試

運行單元測試和整合測試確保遷移正確：

```bash
pytest tests/unit/ -v
pytest tests/e2e/ -v
```

---

## 時間線

| 階段 | 版本 | 日期 | 動作 |
|------|------|------|------|
| 初始棄用警告 | v2.5 | 2025-12-07 | 發出 DeprecationWarning |
| Sprint 31 擴展 | v2.6 | 2025-12-08 | 新增 AgentExecutor, DeadlockDetector 棄用 |
| 移除準備 | v3.0 | TBD | 更新所有內部使用 |
| 完全移除 | v4.0 | TBD | 移除棄用模組 |

---

## 相關連結

- [Technical Architecture v2.6](../../02-architecture/technical-architecture.md)
- [Sprint 30 Progress](../sprint-execution/sprint-30/progress.md)
- [Sprint 31 Progress](../sprint-execution/sprint-31/progress.md)
- [Agent Framework Adapters](../../../backend/src/integrations/agent_framework/builders/__init__.py)
