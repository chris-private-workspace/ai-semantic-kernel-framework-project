# Phase 3 架構審查報告

**審查日期**: 2025-12-06
**審查範圍**: Sprint 13-18 (Phase 3 Agent Framework 遷移)
**審查結論**: 🔴 **嚴重問題 - 需要重新實現**

---

## 執行摘要

Phase 3 的實現存在與 Phase 2 相同的根本性問題：**沒有使用 Microsoft Agent Framework 的官方 API，而是自行開發了類似的功能**。

雖然代碼註釋中說明「適配到 Agent Framework」、「封裝 Agent Framework API」，但實際上：
- 沒有 import 官方的 `ConcurrentBuilder`、`GroupChatBuilder`、`HandoffBuilder` 等類
- 自行實現了 `ConcurrentBuilderAdapter`、`GroupChatBuilderAdapter` 等類
- 這些實現是**獨立開發**的，不是對官方 API 的封裝

---

## 問題詳述

### 1. 官方 API 使用情況

**官方 Agent Framework 提供的 Builder 類：**
```python
# 正確的 import 方式
from agent_framework import (
    ConcurrentBuilder,       # 並行執行
    GroupChatBuilder,        # 群組對話
    HandoffBuilder,          # Agent 交接
    MagenticBuilder,         # 動態規劃
    WorkflowExecutor,        # 嵌套工作流
    SequentialBuilder,       # 順序執行
    WorkflowBuilder,         # 基礎工作流構建
    # 輔助類
    GroupChatDirective,
    GroupChatStateSnapshot,
    ManagerSelectionResponse,
    SubWorkflowRequestMessage,
    SubWorkflowResponseMessage,
    # ...
)
```

**我們的實現情況：**

| 模組 | 是否 import 官方 API | 問題 |
|------|---------------------|------|
| `concurrent.py` | ❌ 否 | 自行實現 `ConcurrentBuilderAdapter` |
| `handoff.py` | ❌ 否 | 自行實現 `HandoffBuilderAdapter` |
| `groupchat.py` | ❌ 否 | 自行實現 `GroupChatBuilderAdapter` |
| `magentic.py` | ❌ 否 | 自行實現 `MagenticBuilderAdapter` |
| `workflow_executor.py` | ❌ 否 | 自行實現 `WorkflowExecutorAdapter` |

### 2. 代碼證據

在整個 `backend/src/integrations/agent_framework/` 目錄中搜索官方 API import：

```bash
$ grep -r "from agent_framework" backend/src/integrations/agent_framework/
# 結果：只有 2 處
workflow.py:425:  from agent_framework import WorkflowBuilder
checkpoint.py:102: from agent_framework import WorkflowCheckpoint
```

**關鍵發現**：Phase 3 的 5 個核心 Builder 適配器都沒有使用任何官方 Agent Framework API。

### 3. 具體問題分析

#### Sprint 14: ConcurrentBuilder 重構
- **期望**: 使用官方 `ConcurrentBuilder` 類
- **實際**: 自行實現 `ConcurrentBuilderAdapter`，包含：
  - 自定義 `ConcurrentMode` enum
  - 自定義 `ExecutorProtocol` 協議
  - 自定義 `ConcurrentTaskConfig` 數據類
  - 自行實現的並行執行邏輯

```python
# 應該這樣做
from agent_framework import ConcurrentBuilder
builder = ConcurrentBuilder()
builder.participants([agent1, agent2])
builder.with_aggregator(my_aggregator)
workflow = builder.build()

# 實際上我們這樣做
class ConcurrentBuilderAdapter(BuilderAdapter):  # 自行實現
    def __init__(self, ...):
        self._tasks = []  # 自行管理任務
    def add_executor(self, ...):  # 自定義方法
        ...
```

#### Sprint 15: HandoffBuilder 重構
- **期望**: 使用官方 `HandoffBuilder` 類
- **實際**: 自行實現 `HandoffBuilderAdapter`，包含：
  - 自定義 `HandoffMode` enum
  - 自定義 `HandoffStatus` enum
  - 自定義 `HandoffRoute` 數據類
  - 自行實現的交接邏輯

#### Sprint 16: GroupChatBuilder 重構
- **期望**: 使用官方 `GroupChatBuilder` 類和相關類型
  - `GroupChatDirective`
  - `GroupChatStateSnapshot`
  - `ManagerSelectionResponse`
- **實際**: 自行實現 `GroupChatBuilderAdapter`，包含：
  - 自定義 `SpeakerSelectionMethod` enum
  - 自定義 `GroupChatParticipant` 數據類
  - 自行實現的發言者選擇邏輯

#### Sprint 17: MagenticBuilder 重構
- **期望**: 使用官方 `MagenticBuilder` 和 `StandardMagenticManager`
- **實際**: 自行實現 `MagenticBuilderAdapter`，包含：
  - 自定義規劃邏輯
  - 自行實現的任務管理

#### Sprint 18: WorkflowExecutor 重構
- **期望**: 使用官方 `WorkflowExecutor`、`ExecutionContext`、`SubWorkflowRequestMessage`
- **實際**: 自行實現 `WorkflowExecutorAdapter`，包含：
  - 自定義 `ExecutionContext` 數據類
  - 自定義消息類型
  - 自行實現的嵌套工作流邏輯

---

## 官方 API 結構參考

### ConcurrentBuilder (官方)
```python
# reference/agent-framework/.../concurrent.py
class ConcurrentBuilder:
    def participants(self, agents: Sequence[AgentProtocol]) -> "ConcurrentBuilder"
    def with_aggregator(self, aggregator: AggregatorFn) -> "ConcurrentBuilder"
    def with_checkpointing(self, storage: CheckpointStorage) -> "ConcurrentBuilder"
    def build(self) -> Workflow
```

### GroupChatBuilder (官方)
```python
# reference/agent-framework/.../group_chat.py
class GroupChatBuilder:
    def set_manager(self, manager: AgentProtocol) -> "GroupChatBuilder"
    def set_select_speakers_func(self, selector: SelectorFn) -> "GroupChatBuilder"
    def participants(self, agents: Mapping | Sequence) -> "GroupChatBuilder"
    def with_max_rounds(self, max_rounds: int) -> "GroupChatBuilder"
    def with_termination_condition(self, condition: ConditionFn) -> "GroupChatBuilder"
    def with_checkpointing(self, storage: CheckpointStorage) -> "GroupChatBuilder"
    def build(self) -> Workflow
```

### WorkflowExecutor (官方)
```python
# reference/agent-framework/.../workflow_executor.py
class WorkflowExecutor(Executor):
    def __init__(self, workflow: Workflow, id: str, allow_direct_output: bool = False)
    # 使用 ExecutionContext 追蹤執行狀態
    # 使用 SubWorkflowRequestMessage/SubWorkflowResponseMessage 進行通信
```

---

## 修復建議

### 選項 A: 完全重寫 (推薦)

1. **刪除現有實現**：移除 `builders/` 目錄下所有自行開發的類

2. **創建真正的適配器**：
```python
# 正確的適配器模式
from agent_framework import ConcurrentBuilder, GroupChatBuilder, ...

class ConcurrentBuilderAdapter:
    """薄適配層，封裝官方 API 以符合 IPA 接口"""

    def __init__(self, ...):
        # 使用官方 Builder
        self._builder = ConcurrentBuilder()

    def add_executor(self, executor):
        # 轉發到官方 API
        self._builder.participants([executor])
        return self

    def build(self):
        # 使用官方 build
        return self._builder.build()
```

3. **保持 Phase 2 兼容**：使用 migration layer 提供向後兼容

### 選項 B: 增量修復

1. 保留現有代碼作為 "Phase 2 兼容層"
2. 添加新的 "官方 API 適配器"，使用 `agent_framework` 包
3. 逐步遷移到官方 API

### 選項 C: 混合模式

1. 核心功能使用官方 API
2. 擴展功能保留自定義實現
3. 明確標記哪些使用官方 API，哪些是自定義

---

## 時間表影響

| 選項 | 估計工作量 | 風險 |
|------|-----------|------|
| A: 完全重寫 | 3-4 週 | 低 (使用經過驗證的官方 API) |
| B: 增量修復 | 2-3 週 | 中 (維護兩套代碼) |
| C: 混合模式 | 1-2 週 | 高 (複雜度增加) |

---

## 下一步行動

1. **確認方向**：與團隊討論選擇哪個修復選項
2. **驗證依賴**：確認 `agent_framework` 包已正確安裝並可用
3. **制定計劃**：創建詳細的重構計劃
4. **執行重構**：按計劃進行修復

---

## 附錄：官方 API Import 清單

以下是應該使用的官方 Agent Framework API：

```python
from agent_framework import (
    # Builders
    ConcurrentBuilder,
    GroupChatBuilder,
    HandoffBuilder,
    MagenticBuilder,
    SequentialBuilder,
    WorkflowBuilder,

    # Executors
    Executor,
    FunctionExecutor,
    AgentExecutor,
    WorkflowExecutor,

    # GroupChat 相關
    GroupChatDirective,
    GroupChatStateSnapshot,
    ManagerSelectionRequest,
    ManagerSelectionResponse,

    # Magentic 相關
    MagenticManagerBase,
    StandardMagenticManager,
    MagenticContext,

    # WorkflowExecutor 相關
    SubWorkflowRequestMessage,
    SubWorkflowResponseMessage,

    # Checkpoint
    CheckpointStorage,
    InMemoryCheckpointStorage,
    FileCheckpointStorage,

    # 工作流
    Workflow,
    WorkflowContext,
    WorkflowRunResult,
    WorkflowRunState,

    # 其他
    handler,
    response_handler,
)
```

---

**報告結論**：Phase 3 需要重新評估和修復，以確保正確使用 Microsoft Agent Framework 官方 API。
