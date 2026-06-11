# Sprint 19: Official Agent Framework API Integration

## Sprint Overview

| Property | Value |
|----------|-------|
| **Sprint** | 19 |
| **Phase** | 3 - Agent Framework Migration |
| **Focus** | 整合官方 Microsoft Agent Framework API |
| **Duration** | 1 Sprint |
| **Total Story Points** | 20 |

## Sprint Goal

修改 Phase 3 builders 以正確 wrap 官方 Microsoft Agent Framework API，確保：
1. 所有 adapter 都 import 官方類別
2. 所有 adapter 都使用官方 Builder 實例
3. 所有 build() 方法都呼叫官方 API

---

## 問題分析

### 現狀問題

Phase 3 的 5 個 builder adapter 目前存在以下問題：

| Builder | 代碼行數 | 問題 |
|---------|---------|------|
| `concurrent.py` | 188 | 無 `from agent_framework import ConcurrentBuilder` |
| `handoff.py` | 1222 | 無 `from agent_framework import HandoffBuilder` |
| `groupchat.py` | 1240 | 無 `from agent_framework import GroupChatBuilder`，使用 `_MockGroupChatWorkflow` |
| `magentic.py` | 1653 | 無官方 API import，自己實現 `MagenticManagerBase`, `StandardMagenticManager` |
| `workflow_executor.py` | 1280 | 無 `from agent_framework import WorkflowExecutor` |

### 官方 API 導出清單

根據 `agent_framework/_workflows/__init__.py`，可用的官方類別：

```python
# Builders
from agent_framework import (
    ConcurrentBuilder,      # 並行執行 workflow
    GroupChatBuilder,       # 群組對話 workflow
    HandoffBuilder,         # 交接 workflow
    MagenticBuilder,        # Magentic One 風格 workflow
)

# Magentic Components
from agent_framework import (
    MagenticManagerBase,           # 抽象基類
    StandardMagenticManager,       # 標準實現
    MagenticContext,               # 上下文
    MagenticHumanInterventionKind, # 人工介入類型
)

# WorkflowExecutor
from agent_framework import (
    WorkflowExecutor,              # 嵌套 workflow 執行器
    SubWorkflowRequestMessage,     # 子 workflow 請求
    SubWorkflowResponseMessage,    # 子 workflow 響應
)

# GroupChat Components
from agent_framework import (
    GroupChatDirective,            # 群組指令
    ManagerSelectionResponse,      # 管理者選擇響應
)
```

---

## User Stories

### S19-1: ConcurrentBuilder 整合 (4 points)

**目標**: 修改 `concurrent.py` 以 wrap 官方 `ConcurrentBuilder`

**驗收標準**:
- [ ] 添加 `from agent_framework import ConcurrentBuilder`
- [ ] `ConcurrentBuilderAdapter.__init__` 創建 `self._builder = ConcurrentBuilder()`
- [ ] `build()` 方法呼叫 `self._builder.participants(...).build()`
- [ ] 保留現有的 IPA 平台特定功能作為擴展

**技術細節**:

```python
# 官方 API 用法示例
from agent_framework import ConcurrentBuilder

class ConcurrentBuilderAdapter:
    def __init__(self, ...):
        self._builder = ConcurrentBuilder()
        # 保留 IPA 平台特定的配置

    def participants(self, agents: List[AgentProtocol]) -> "ConcurrentBuilderAdapter":
        self._builder.participants(agents)
        return self

    def with_aggregator(self, aggregator) -> "ConcurrentBuilderAdapter":
        self._builder.with_aggregator(aggregator)
        return self

    def build(self) -> Workflow:
        # 先呼叫官方 API
        workflow = self._builder.build()
        # 然後添加 IPA 平台特定的包裝
        return workflow
```

---

### S19-2: HandoffBuilder 整合 (4 points)

**目標**: 修改 `handoff.py` 以 wrap 官方 `HandoffBuilder`

**驗收標準**:
- [ ] 添加 `from agent_framework import HandoffBuilder, HandoffUserInputRequest`
- [ ] `HandoffBuilderAdapter.__init__` 創建 `self._builder = HandoffBuilder(...)`
- [ ] `build()` 方法呼叫 `self._builder.set_coordinator(...).build()`
- [ ] 保留現有的觸發器和策略作為擴展

**技術細節**:

```python
from agent_framework import HandoffBuilder, HandoffUserInputRequest

class HandoffBuilderAdapter:
    def __init__(self, name: str = None, participants: List = None):
        self._builder = HandoffBuilder(name=name, participants=participants)
        # 保留 IPA 平台的 HandoffPolicy, HandoffTrigger 等

    def set_coordinator(self, agent) -> "HandoffBuilderAdapter":
        self._builder.set_coordinator(agent)
        return self

    def add_handoff(self, source, targets) -> "HandoffBuilderAdapter":
        self._builder.add_handoff(source, targets)
        return self

    def build(self) -> Workflow:
        return self._builder.build()
```

---

### S19-3: GroupChatBuilder 整合 (4 points)

**目標**: 修改 `groupchat.py` 以 wrap 官方 `GroupChatBuilder`，移除 `_MockGroupChatWorkflow`

**驗收標準**:
- [ ] 添加 `from agent_framework import GroupChatBuilder, GroupChatDirective, ManagerSelectionResponse`
- [ ] 移除 `_MockGroupChatWorkflow` 類
- [ ] `GroupChatBuilderAdapter.__init__` 創建 `self._builder = GroupChatBuilder()`
- [ ] `build()` 方法呼叫官方 `self._builder.build()`

**技術細節**:

```python
from agent_framework import (
    GroupChatBuilder,
    GroupChatDirective,
    ManagerSelectionResponse,
)

class GroupChatBuilderAdapter:
    def __init__(self):
        self._builder = GroupChatBuilder()

    def participants(self, **agents) -> "GroupChatBuilderAdapter":
        self._builder.participants(**agents)
        return self

    def set_manager(self, manager, display_name=None) -> "GroupChatBuilderAdapter":
        self._builder.set_manager(manager, display_name=display_name)
        return self

    def build(self) -> Workflow:
        return self._builder.build()
```

---

### S19-4: MagenticBuilder 整合 (4 points)

**目標**: 修改 `magentic.py` 以 wrap 官方 `MagenticBuilder`, `MagenticManagerBase`, `StandardMagenticManager`

**驗收標準**:
- [ ] 添加官方 imports
- [ ] 移除自定義 `MagenticManagerBase` 和 `StandardMagenticManager` 實現
- [ ] 使用官方類別作為基類或直接實例化
- [ ] `build()` 方法呼叫官方 API

**技術細節**:

```python
from agent_framework import (
    MagenticBuilder,
    MagenticManagerBase,
    StandardMagenticManager,
    MagenticContext,
)

class MagenticBuilderAdapter:
    def __init__(self):
        self._builder = MagenticBuilder()

    def participants(self, **agents) -> "MagenticBuilderAdapter":
        self._builder.participants(**agents)
        return self

    def with_standard_manager(self, chat_client=None, agent=None, **kwargs) -> "MagenticBuilderAdapter":
        if agent:
            manager = StandardMagenticManager(agent=agent, **kwargs)
        else:
            # 創建預設 agent
            pass
        self._builder.with_standard_manager(manager)
        return self

    def build(self) -> Workflow:
        return self._builder.build()
```

---

### S19-5: WorkflowExecutor 整合 (4 points)

**目標**: 修改 `workflow_executor.py` 以 wrap 官方 `WorkflowExecutor`

**驗收標準**:
- [ ] 添加 `from agent_framework import WorkflowExecutor, SubWorkflowRequestMessage, SubWorkflowResponseMessage`
- [ ] `WorkflowExecutorAdapter` 繼承或包裝官方 `WorkflowExecutor`
- [ ] 保留 IPA 平台的擴展功能

**技術細節**:

```python
from agent_framework import (
    WorkflowExecutor,
    SubWorkflowRequestMessage,
    SubWorkflowResponseMessage,
)

class WorkflowExecutorAdapter(WorkflowExecutor):
    """IPA 平台的 WorkflowExecutor 擴展"""

    def __init__(self, workflow: Workflow, id: str, **kwargs):
        super().__init__(workflow=workflow, id=id, **kwargs)
        # 添加 IPA 平台特定的配置
```

---

## 驗證腳本

每個 story 完成後必須運行驗證腳本：

```bash
cd backend
python scripts/verify_official_api_usage.py
```

預期結果：5/5 checks passed

---

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 官方 API 與現有實現不兼容 | 高 | 使用 Adapter 模式包裝，保持對外接口不變 |
| 測試失敗 | 中 | 逐步修改，每個 story 完成後運行測試 |
| 功能缺失 | 中 | 保留 IPA 平台特定功能作為擴展層 |

---

## Definition of Done

- [ ] 所有 5 個 builder 都有正確的官方 API import
- [ ] 所有 adapter 都創建並使用官方 Builder 實例
- [ ] 所有 build() 方法都呼叫官方 API
- [ ] 驗證腳本通過 (5/5)
- [ ] 所有現有測試通過
- [ ] 代碼審查完成

---

## 時間規劃

| Story | Points | 依賴 |
|-------|--------|------|
| S19-1: ConcurrentBuilder | 4 | 無 |
| S19-2: HandoffBuilder | 4 | 無 |
| S19-3: GroupChatBuilder | 4 | 無 |
| S19-4: MagenticBuilder | 4 | 無 |
| S19-5: WorkflowExecutor | 4 | 無 |

**注意**: 所有 story 可以並行開發，因為它們修改的是不同的文件。
