# Agent 交接指南 (Agent Handoff)

## 概述

Agent 交接功能允許在 Agent 之間智能地傳遞任務和上下文，實現無縫協作。交接成功率目標 **≥ 95%**。

---

## 核心概念

### 交接策略

| 策略 | 說明 | 適用場景 |
|------|------|----------|
| `IMMEDIATE` | 立即交接 | 緊急任務切換 |
| `GRACEFUL` | 優雅交接 | 正常任務轉移 |
| `CONDITIONAL` | 條件式交接 | 根據條件決定 |

### 觸發類型

| 類型 | 說明 | 範例 |
|------|------|------|
| `CONDITION` | 條件觸發 | 當任務狀態為完成時 |
| `EVENT` | 事件觸發 | 收到特定訊息時 |
| `TIMEOUT` | 超時觸發 | 執行超過 5 分鐘 |
| `ERROR` | 錯誤觸發 | 發生異常時 |
| `CAPABILITY` | 能力觸發 | 需要特定能力時 |
| `EXPLICIT` | 明確觸發 | 手動觸發交接 |

### 交接流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Source    │     │   Handoff   │     │   Target    │
│   Agent     │     │ Controller  │     │   Agent     │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       │  1. 觸發交接      │                   │
       │──────────────────>│                   │
       │                   │                   │
       │                   │  2. 選擇目標      │
       │                   │  (能力匹配)       │
       │                   │                   │
       │  3. 準備上下文    │                   │
       │<──────────────────│                   │
       │                   │                   │
       │  4. 傳輸上下文    │                   │
       │───────────────────────────────────────>│
       │                   │                   │
       │                   │  5. 確認接收      │
       │                   │<──────────────────│
       │                   │                   │
       │  6. 完成交接      │                   │
       │<──────────────────│                   │
       │                   │                   │
```

---

## 使用方式

### 基本交接

```python
from src.core.handoff import HandoffController, HandoffPolicy

# 建立交接控制器
controller = HandoffController()

# 執行交接
handoff = await controller.execute_handoff(
    source_agent_id="agent_a",
    target_agent_id="agent_b",
    execution_id="exec_123",
    policy=HandoffPolicy.GRACEFUL,
    context={
        "task_state": "in_progress",
        "data": {"key": "value"},
        "conversation_history": [...]
    }
)

print(f"Handoff ID: {handoff.id}")
print(f"Status: {handoff.status}")
```

### 使用觸發器

```python
from src.core.handoff import HandoffTrigger, TriggerType

# 建立觸發器
trigger = HandoffTrigger()

# 設置條件觸發
await trigger.register(
    execution_id="exec_123",
    trigger_type=TriggerType.CONDITION,
    condition="task.status == 'needs_specialist'",
    target_capability="data_analysis",
    metadata={"priority": "high"}
)

# 設置超時觸發
await trigger.register(
    execution_id="exec_123",
    trigger_type=TriggerType.TIMEOUT,
    timeout_seconds=300,
    fallback_agent_id="supervisor_agent"
)
```

### 能力匹配

```python
from src.core.handoff import CapabilityMatcher, MatchStrategy

# 建立能力匹配器
matcher = CapabilityMatcher()

# 註冊 Agent 能力
await matcher.register_capabilities(
    agent_id="agent_a",
    capabilities=[
        "text_processing",
        "translation",
        "summarization"
    ]
)

# 尋找匹配的 Agent
matched_agents = await matcher.find_agents(
    required_capabilities=["data_analysis"],
    strategy=MatchStrategy.BEST_FIT,
    exclude_agents=["agent_a"]  # 排除當前 Agent
)

print(f"Found {len(matched_agents)} matching agents")
```

### 協作協議

```python
from src.core.handoff import CollaborationProtocol, MessageType

# 建立協作協議
protocol = CollaborationProtocol()

# 建立協作會話
session = await protocol.create_session(
    agents=["agent_a", "agent_b", "agent_c"],
    topic="Complete complex task",
    timeout_seconds=600
)

# 發送訊息
await protocol.send_message(
    session_id=session.id,
    sender_id="agent_a",
    message_type=MessageType.REQUEST,
    content="Need help with data analysis"
)

# 接收回應
response = await protocol.receive_message(
    session_id=session.id,
    receiver_id="agent_b",
    timeout_seconds=30
)
```

---

## API 參考

### POST /api/v1/handoff/trigger

觸發 Agent 交接。

**請求體：**

```json
{
  "execution_id": "uuid",
  "source_agent_id": "uuid",
  "target_agent_id": "uuid",
  "policy": "graceful",
  "context": {
    "task_state": "in_progress",
    "data": {}
  },
  "priority": "normal"
}
```

**響應：**

```json
{
  "handoff_id": "uuid",
  "status": "initiated",
  "source_agent": "agent_a",
  "target_agent": "agent_b",
  "initiated_at": "2025-12-05T10:00:00Z"
}
```

### GET /api/v1/handoff/{handoff_id}/status

查詢交接狀態。

**響應：**

```json
{
  "handoff_id": "uuid",
  "status": "completed",
  "source_agent": "agent_a",
  "target_agent": "agent_b",
  "context_transferred": true,
  "completed_at": "2025-12-05T10:00:30Z",
  "duration_ms": 30000
}
```

### GET /api/v1/handoff/agents/capabilities

獲取所有 Agent 能力列表。

**響應：**

```json
{
  "agents": [
    {
      "agent_id": "uuid",
      "name": "Data Analyst",
      "capabilities": ["data_analysis", "visualization", "reporting"],
      "availability": "available"
    }
  ]
}
```

### POST /api/v1/handoff/match

根據能力匹配 Agent。

**請求體：**

```json
{
  "required_capabilities": ["data_analysis"],
  "preferred_capabilities": ["python"],
  "strategy": "best_fit",
  "limit": 5
}
```

---

## 內建能力類型

系統預定義的 Agent 能力：

| 能力 | 說明 |
|------|------|
| `text_processing` | 文字處理 |
| `code_generation` | 程式碼生成 |
| `data_analysis` | 數據分析 |
| `translation` | 翻譯 |
| `summarization` | 摘要 |
| `qa_response` | 問答回應 |
| `image_processing` | 圖像處理 |
| `audio_processing` | 音訊處理 |
| `planning` | 規劃 |
| `decision_making` | 決策 |
| `research` | 研究 |
| `writing` | 寫作 |
| `calculation` | 計算 |
| `web_search` | 網路搜尋 |
| `database_query` | 資料庫查詢 |

---

## 最佳實踐

### 1. 使用優雅交接

```python
# 推薦：優雅交接確保任務完整性
await controller.execute_handoff(
    source_agent_id="agent_a",
    target_agent_id="agent_b",
    policy=HandoffPolicy.GRACEFUL,
    wait_for_completion=True  # 等待當前任務完成
)
```

### 2. 完整傳遞上下文

```python
# 確保傳遞所有必要上下文
context = {
    "task_state": current_state,
    "conversation_history": history,
    "user_preferences": preferences,
    "intermediate_results": results,
    "metadata": {
        "original_request": request,
        "attempt_count": attempts
    }
}
```

### 3. 設置回退機制

```python
# 設置回退 Agent
await trigger.register(
    execution_id="exec_123",
    trigger_type=TriggerType.ERROR,
    fallback_agent_id="supervisor_agent",
    retry_count=3
)
```

### 4. 監控交接狀態

```python
# 輪詢交接狀態
while True:
    status = await controller.get_status(handoff_id)
    if status.is_terminal:
        break
    await asyncio.sleep(1)
```

---

## 效能指標

| 指標 | 目標值 | 說明 |
|------|--------|------|
| 交接延遲 | < 500ms | 平均交接時間 |
| 成功率 | ≥ 95% | 交接成功率 |
| 上下文完整率 | ≥ 99% | 上下文傳遞完整性 |
| 能力匹配時間 | < 100ms | Agent 匹配時間 |

---

## 常見問題

### Q: 交接失敗時如何處理？

A: 使用錯誤回調：

```python
async def on_handoff_failure(handoff_id, error):
    logger.error(f"Handoff {handoff_id} failed: {error}")
    # 嘗試回退到原 Agent
    await controller.rollback(handoff_id)

await controller.execute_handoff(
    ...,
    on_failure=on_handoff_failure
)
```

### Q: 如何避免循環交接？

A: 使用交接歷史追蹤：

```python
controller = HandoffController(
    max_handoff_chain=5,  # 最大交接鏈長度
    prevent_circular=True  # 防止循環
)
```

### Q: 如何處理多 Agent 同時請求交接？

A: 使用優先級隊列：

```python
await controller.execute_handoff(
    ...,
    priority="high",  # high, normal, low
    queue_on_conflict=True
)
```

---

## 相關文檔

- [API 參考](../api-reference/handoff-api.md)
- [教學：設置 Agent 交接](../tutorials/setup-agent-handoff.md)
- [協作協議](./collaboration-protocol.md)
