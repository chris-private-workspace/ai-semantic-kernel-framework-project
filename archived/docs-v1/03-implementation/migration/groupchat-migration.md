# GroupChat 模組遷移指南

> **狀態**: Sprint 20 開始棄用，預計 Sprint 25 完全移除
> **最後更新**: 2025-12-06

## 概述

本文檔說明如何從舊版 `domain.orchestration.groupchat` 模組遷移到新版 `integrations.agent_framework.builders.groupchat` 模組。

新版模組基於 Microsoft Agent Framework 官方 API 構建，提供更好的：
- 與官方 SDK 的整合性
- 更清晰的 API 設計
- 更完善的類型支援
- 更靈活的擴展能力

---

## 快速遷移對照表

| 舊版 (已棄用) | 新版 (推薦) |
|--------------|-------------|
| `GroupChatManager` | `GroupChatBuilderAdapter` |
| `VotingManager` | `GroupChatVotingAdapter` |
| `SpeakerSelector` | `create_*_selector()` 函數 |
| `TerminationChecker` | `create_*_termination()` 函數 |
| `AgentInfo` | `GroupChatParticipant` |

---

## 詳細遷移步驟

### 1. 基本 GroupChat 遷移

#### 舊版寫法 (已棄用)

```python
from domain.orchestration.groupchat import (
    GroupChatManager,
    GroupChatConfig,
    AgentInfo,
    SpeakerSelectionMethod,
)

# 創建代理資訊
agents = [
    AgentInfo(id="agent-1", name="analyst", role="分析師"),
    AgentInfo(id="agent-2", name="developer", role="開發者"),
]

# 創建配置
config = GroupChatConfig(
    max_rounds=10,
    selection_method=SpeakerSelectionMethod.ROUND_ROBIN,
)

# 創建管理器
manager = GroupChatManager(agents=agents, config=config)

# 執行對話
result = await manager.run("開始討論")
```

#### 新版寫法 (推薦)

```python
from integrations.agent_framework.builders.groupchat import (
    GroupChatBuilderAdapter,
    GroupChatParticipant,
    SpeakerSelectionMethod,
)

# 創建參與者
participants = [
    GroupChatParticipant(
        name="analyst",
        description="分析師",
        capabilities=["analysis", "research"],
    ),
    GroupChatParticipant(
        name="developer",
        description="開發者",
        capabilities=["coding", "testing"],
    ),
]

# 創建適配器 (一步完成)
adapter = GroupChatBuilderAdapter(
    id="chat-001",
    participants=participants,
    selection_method=SpeakerSelectionMethod.ROUND_ROBIN,
    max_rounds=10,
)

# 構建並執行
groupchat = adapter.build()
result = await groupchat.run("開始討論")
```

---

### 2. 發言者選擇策略遷移

#### 舊版寫法

```python
from domain.orchestration.groupchat import (
    SpeakerSelector,
    RoundRobinStrategy,
    PriorityStrategy,
)

selector = SpeakerSelector(strategy=RoundRobinStrategy())
next_speaker = selector.select(agents, context)
```

#### 新版寫法

```python
from integrations.agent_framework.builders.groupchat import (
    SpeakerSelectionMethod,
    create_round_robin_selector,
    create_priority_selector,
    create_expertise_selector,
)

# 使用內建選擇方法
adapter = GroupChatBuilderAdapter(
    id="chat-001",
    participants=participants,
    selection_method=SpeakerSelectionMethod.ROUND_ROBIN,
)

# 或使用自定義選擇器
priority_selector = create_priority_selector(participants)
adapter = GroupChatBuilderAdapter(
    id="chat-001",
    participants=participants,
    selection_method=SpeakerSelectionMethod.CUSTOM,
    custom_selector=priority_selector,
)
```

#### 可用的選擇器工廠函數

| 函數 | 說明 |
|------|------|
| `create_round_robin_selector()` | 輪詢選擇 |
| `create_random_selector()` | 隨機選擇 |
| `create_priority_selector()` | 優先級選擇 (需設置 priority 屬性) |
| `create_expertise_selector()` | 專業知識匹配選擇 |

---

### 3. 終止條件遷移

#### 舊版寫法

```python
from domain.orchestration.groupchat import (
    TerminationChecker,
    TerminationCondition,
    TerminationType,
)

checker = TerminationChecker(conditions=[
    TerminationCondition(type=TerminationType.MAX_ROUNDS, value=10),
    TerminationCondition(type=TerminationType.KEYWORD, value="TERMINATE"),
])

should_terminate = checker.check(messages)
```

#### 新版寫法

```python
from integrations.agent_framework.builders.groupchat import (
    create_max_rounds_termination,
    create_keyword_termination,
    create_composite_termination,
)

# 單一條件
termination = create_max_rounds_termination(10)

# 複合條件 (任一條件滿足即終止)
termination = create_composite_termination([
    create_max_rounds_termination(10),
    create_keyword_termination(["TERMINATE", "DONE"]),
])

adapter = GroupChatBuilderAdapter(
    id="chat-001",
    participants=participants,
    termination_condition=termination,
)
```

#### 可用的終止條件工廠函數

| 函數 | 說明 |
|------|------|
| `create_max_rounds_termination(n)` | 達到 n 輪後終止 |
| `create_keyword_termination(keywords)` | 訊息包含關鍵字時終止 |
| `create_timeout_termination(seconds)` | 超時後終止 |
| `create_message_count_termination(n)` | 訊息數達到 n 則終止 |
| `create_composite_termination(conditions)` | 複合條件 (OR 邏輯) |

---

### 4. 投票功能遷移

#### 舊版寫法

```python
from domain.orchestration.groupchat import (
    VotingManager,
    VotingSession,
    VoteType,
)

voting_manager = VotingManager()
session = voting_manager.create_session(
    topic="選擇方案",
    vote_type=VoteType.MAJORITY,
    voters=agents,
)

result = await voting_manager.conduct_vote(session)
```

#### 新版寫法

```python
from integrations.agent_framework.builders.groupchat_voting import (
    GroupChatVotingAdapter,
    VotingMethod,
    VotingConfig,
)

# 創建投票適配器
adapter = GroupChatVotingAdapter(
    id="voting-chat-001",
    participants=participants,
    voting_method=VotingMethod.MAJORITY,
    voting_threshold=0.5,
)

# 或使用完整配置
config = VotingConfig(
    method=VotingMethod.RANKED,
    threshold=0.6,
    min_votes=3,
    allow_abstain=True,
)

adapter = GroupChatVotingAdapter(
    id="voting-chat-001",
    participants=participants,
    voting_config=config,
)

# 構建並執行
groupchat = adapter.build()
result = await groupchat.run("投票決定方案")
```

#### 可用的投票方法

| VotingMethod | 說明 |
|--------------|------|
| `MAJORITY` | 簡單多數 (>50%) |
| `UNANIMOUS` | 全體一致 |
| `RANKED` | 排序投票 |
| `WEIGHTED` | 加權投票 |
| `APPROVAL` | 認可投票 (多選) |

---

### 5. API 路由遷移

如果您的 API 路由使用舊版模組，請更新導入：

#### 舊版

```python
from src.domain.orchestration.groupchat import GroupChatManager
```

#### 新版

```python
from src.integrations.agent_framework.builders.groupchat import (
    GroupChatBuilderAdapter,
    create_groupchat_adapter,
)

# 使用工廠函數快速創建
adapter = create_groupchat_adapter(
    id="api-chat-001",
    participants=participants,
    selection_method="round_robin",
)
```

---

## 常見問題

### Q1: 我需要立即遷移嗎？

不需要。舊版模組將在 Sprint 25 移除，您有足夠時間進行遷移。但建議盡早開始，以利用新版的改進功能。

### Q2: 新舊版本可以共存嗎？

可以，但不建議。在遷移期間，您可能同時使用兩個版本，但請注意它們的資料結構不完全相容。

### Q3: 我的自定義策略如何遷移？

新版支援 `custom_selector` 參數，您可以傳入任何符合 `Callable[[dict], str]` 簽名的函數：

```python
def my_custom_selector(state: dict) -> str:
    # 您的選擇邏輯
    return "selected_participant_name"

adapter = GroupChatBuilderAdapter(
    id="chat-001",
    participants=participants,
    selection_method=SpeakerSelectionMethod.CUSTOM,
    custom_selector=my_custom_selector,
)
```

### Q4: 遷移後測試如何更新？

請參考 `tests/unit/test_groupchat_adapter.py` 和 `tests/unit/test_groupchat_voting_adapter.py` 中的測試範例。

---

## 支援

如有遷移問題，請：
1. 查閱本文檔和相關測試案例
2. 檢查 `integrations/agent_framework/builders/groupchat.py` 原始碼
3. 聯繫開發團隊

---

## 版本歷史

| 版本 | 日期 | 說明 |
|------|------|------|
| 1.0 | 2025-12-06 | 初版，Sprint 20 發布 |
