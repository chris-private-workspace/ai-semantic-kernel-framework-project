# 群組對話指南 (GroupChat)

## 概述

GroupChat 功能讓多個 Agent 可以協作討論、共同決策，實現複雜任務的集體智慧。訊息延遲目標 **< 200ms**。

---

## 核心概念

### 發言選擇模式

| 模式 | 說明 | 適用場景 |
|------|------|----------|
| `round_robin` | 輪流發言 | 公平討論 |
| `random` | 隨機選擇 | 多樣化觀點 |
| `auto` | AI 自動選擇 | 智能對話 |
| `selector` | 指定選擇器 | 專家主導 |
| `manual` | 手動指定 | 用戶控制 |

### 終止條件

| 條件 | 說明 |
|------|------|
| `max_rounds` | 達到最大輪數 |
| `consensus` | 達成共識 |
| `timeout` | 超時 |
| `keyword` | 出現特定關鍵詞 |
| `external` | 外部觸發 |

### 對話流程

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Agent A │     │  Agent B │     │  Agent C │
└────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │
     │  Round 1       │                │
     │───────────────>│                │
     │                │                │
     │                │  Round 2       │
     │                │───────────────>│
     │                │                │
     │                │                │  Round 3
     │<───────────────────────────────│
     │                │                │
     │        ... 持續對話 ...        │
     │                │                │
     │       達成共識或終止條件         │
     │                │                │
```

---

## 使用方式

### 建立群組

```python
from src.core.groupchat import GroupChatManager, GroupConfig

# 建立管理器
manager = GroupChatManager()

# 建立討論群組
group = await manager.create_group(
    name="Technical Discussion",
    agent_ids=["analyst_agent", "developer_agent", "qa_agent"],
    config=GroupConfig(
        max_rounds=10,
        speaker_selection="round_robin",
        allow_repeat_speaker=False,
        admin_name="moderator"
    )
)

print(f"Group ID: {group.id}")
```

### 開始討論

```python
# 開始討論
result = await manager.start_discussion(
    group_id=group.id,
    initial_message="我們需要討論新功能的技術方案",
    context={
        "project": "IPA Platform",
        "feature": "User Authentication"
    }
)

# 輸出對話
for message in result.messages:
    print(f"[{message.agent_name}]: {message.content}")
```

### 使用自動選擇器

```python
from src.core.groupchat import SpeakerSelector

# 建立自動選擇器
selector = SpeakerSelector(
    strategy="relevance",  # 根據相關性選擇
    llm_provider=llm_client
)

group = await manager.create_group(
    name="AI Discussion",
    agent_ids=agents,
    config=GroupConfig(
        speaker_selection="selector",
        speaker_selector=selector
    )
)
```

### 對話記憶管理

```python
from src.core.groupchat import ConversationMemory

# 建立記憶管理器
memory = ConversationMemory(
    max_messages=100,
    summary_threshold=50  # 超過 50 則訊息自動摘要
)

# 添加到群組
group = await manager.create_group(
    name="Long Discussion",
    agent_ids=agents,
    config=GroupConfig(
        memory=memory,
        enable_summary=True
    )
)

# 獲取對話摘要
summary = await memory.get_summary(group.id)
print(f"Discussion summary: {summary}")
```

### 多輪對話

```python
# 持續對話
while True:
    # 檢查是否達到終止條件
    if await manager.should_terminate(group.id):
        break

    # 執行一輪對話
    round_result = await manager.execute_round(group.id)

    print(f"Round {round_result.round_number}:")
    print(f"Speaker: {round_result.speaker}")
    print(f"Message: {round_result.message}")

    # 檢查共識
    if round_result.consensus_reached:
        print("Consensus reached!")
        break

# 獲取最終結果
final_result = await manager.get_result(group.id)
```

---

## API 參考

### POST /api/v1/groupchat

建立群組。

**請求體：**

```json
{
  "name": "Technical Discussion",
  "agent_ids": ["uuid1", "uuid2", "uuid3"],
  "config": {
    "max_rounds": 10,
    "speaker_selection_method": "round_robin",
    "allow_repeat_speaker": false,
    "termination_condition": "consensus"
  }
}
```

**響應：**

```json
{
  "group_id": "uuid",
  "name": "Technical Discussion",
  "agents": ["uuid1", "uuid2", "uuid3"],
  "status": "created",
  "created_at": "2025-12-05T10:00:00Z"
}
```

### POST /api/v1/groupchat/{group_id}/start

開始討論。

**請求體：**

```json
{
  "content": "討論主題",
  "context": {
    "key": "value"
  }
}
```

**響應：**

```json
{
  "session_id": "uuid",
  "messages": [
    {
      "id": "uuid",
      "agent_id": "uuid",
      "agent_name": "Analyst",
      "content": "我認為...",
      "round": 1,
      "timestamp": "2025-12-05T10:00:01Z"
    }
  ],
  "status": "in_progress",
  "current_round": 1
}
```

### GET /api/v1/groupchat/{group_id}/messages

獲取對話訊息。

**查詢參數：**

- `limit`: 返回訊息數量 (預設 50)
- `offset`: 偏移量
- `since`: 時間戳，只返回之後的訊息

### POST /api/v1/groupchat/{group_id}/message

發送訊息到群組。

**請求體：**

```json
{
  "content": "這是我的觀點...",
  "sender_id": "uuid",
  "metadata": {}
}
```

### GET /api/v1/groupchat/{group_id}/summary

獲取對話摘要。

**響應：**

```json
{
  "group_id": "uuid",
  "summary": "討論主要圍繞...",
  "key_points": [
    "觀點 1",
    "觀點 2"
  ],
  "consensus": "達成共識：...",
  "action_items": [
    "待辦事項 1"
  ]
}
```

---

## 最佳實踐

### 1. 設置適當的輪數限制

```python
# 簡單討論
simple_config = GroupConfig(max_rounds=5)

# 複雜討論
complex_config = GroupConfig(
    max_rounds=20,
    early_termination=True,
    termination_condition="consensus"
)
```

### 2. 使用角色專業化

```python
# 定義專門角色
analyst_agent = create_agent(
    name="Data Analyst",
    system_prompt="你是數據分析專家，專注於數據相關的討論..."
)

developer_agent = create_agent(
    name="Developer",
    system_prompt="你是資深開發者，專注於技術實現..."
)
```

### 3. 啟用對話摘要

```python
config = GroupConfig(
    enable_summary=True,
    summary_frequency=10,  # 每 10 輪生成摘要
    memory=ConversationMemory(max_messages=100)
)
```

### 4. 處理長時間對話

```python
# 使用檢查點
await manager.create_checkpoint(group_id)

# 恢復對話
await manager.restore_from_checkpoint(group_id, checkpoint_id)
```

---

## 效能指標

| 指標 | 目標值 | 說明 |
|------|--------|------|
| 訊息延遲 | < 200ms | 單輪訊息延遲 |
| 並發支援 | ≥ 50 Agent | 單群組支援 |
| 記憶檢索 | < 100ms | 記憶查詢時間 |
| 摘要生成 | < 3s | 摘要生成時間 |

---

## 常見問題

### Q: 如何避免無限對話？

A: 設置多重終止條件：

```python
config = GroupConfig(
    max_rounds=20,
    timeout_seconds=600,
    termination_keywords=["結論", "達成共識"],
    max_no_progress_rounds=3
)
```

### Q: 如何處理 Agent 無響應？

A: 使用超時和回退：

```python
config = GroupConfig(
    agent_response_timeout=30,
    skip_unresponsive=True,
    fallback_message="[Agent 無響應]"
)
```

### Q: 如何讓用戶參與對話？

A: 使用 manual 模式：

```python
config = GroupConfig(
    speaker_selection="manual",
    allow_human_intervention=True
)

# 用戶發送訊息
await manager.send_human_message(
    group_id=group.id,
    content="我有一個建議..."
)
```

---

## 相關文檔

- [API 參考](../api-reference/groupchat-api.md)
- [教學：建立群組對話](../tutorials/create-groupchat.md)
- [對話記憶管理](./conversation-memory.md)
