# 並行執行指南 (Concurrent Execution)

## 概述

IPA Platform 的並行執行功能讓您可以同時執行多個 Agent 任務，大幅提升工作流執行效率，達到 **3 倍以上吞吐量提升**。

---

## 核心概念

### Fork-Join 模式

Fork-Join 是最常用的並行執行模式，將單一流程分叉成多個並行分支，完成後再合併。

```
┌─────┐     ┌──────┐     ┌─────┐
│Start│ ──▶ │ Fork │ ──▶ │Task1│ ──┐
└─────┘     └──────┘     └─────┘   │     ┌──────┐     ┌─────┐
                         ┌─────┐   │ ──▶ │ Join │ ──▶ │ End │
                         │Task2│ ──┘     └──────┘     └─────┘
                         └─────┘
```

### 執行模式

| 模式 | 說明 | 適用場景 |
|------|------|----------|
| `all` | 等待所有任務完成 | 需要所有結果才能繼續 |
| `any` | 任一任務完成即可 | 競爭式執行 |
| `majority` | 多數任務完成 | 投票/共識機制 |

### 並行閘道

並行閘道控制工作流的分支和合併：

- **Fork Gateway**: 將流程分成多個並行分支
- **Join Gateway**: 合併並行分支
- **Inclusive Gateway**: 條件式分支，可選擇性執行

---

## 使用方式

### 基本用法

```python
from src.core.concurrent import ForkJoinExecutor, TaskDefinition

# 建立執行器
executor = ForkJoinExecutor()

# 定義並行任務
tasks = [
    TaskDefinition(
        id="data_fetch_1",
        agent_id="data_agent",
        inputs={"source": "database_1"}
    ),
    TaskDefinition(
        id="data_fetch_2",
        agent_id="data_agent",
        inputs={"source": "database_2"}
    ),
    TaskDefinition(
        id="api_call",
        agent_id="api_agent",
        inputs={"endpoint": "/users"}
    ),
]

# 執行並行任務
result = await executor.execute_fork_join(
    tasks=tasks,
    join_mode="all",
    timeout_seconds=300
)

print(f"Status: {result.status}")
print(f"Results: {result.results}")
```

### 使用並行閘道

```python
from src.core.concurrent import ParallelGateway, GatewayType

# 建立閘道
gateway = ParallelGateway()

# Fork 分支
fork_result = await gateway.execute(
    gateway_type=GatewayType.FORK,
    execution_id="exec_123",
    branches=["branch_a", "branch_b", "branch_c"]
)

# 執行各分支任務...

# Join 合併
join_result = await gateway.execute(
    gateway_type=GatewayType.JOIN,
    execution_id="exec_123",
    join_mode="all"
)
```

### 錯誤處理

```python
from src.core.concurrent import ForkJoinExecutor, ErrorHandlingMode

executor = ForkJoinExecutor(
    error_handling=ErrorHandlingMode.CONTINUE  # continue, abort, retry
)

result = await executor.execute_fork_join(
    tasks=tasks,
    on_failure="continue",  # 部分失敗時繼續執行
    max_retries=3,
    retry_delay_seconds=1.0
)

# 檢查失敗的任務
for task_id, error in result.errors.items():
    print(f"Task {task_id} failed: {error}")
```

---

## API 參考

### POST /api/v1/concurrent/fork-join

執行 Fork-Join 任務組。

**請求體：**

```json
{
  "tasks": [
    {
      "id": "task_1",
      "agent_id": "uuid",
      "inputs": {"key": "value"}
    },
    {
      "id": "task_2",
      "agent_id": "uuid",
      "inputs": {"key": "value"}
    }
  ],
  "join_mode": "all",
  "timeout_seconds": 300,
  "error_handling": {
    "on_failure": "continue",
    "max_retries": 3
  }
}
```

**響應：**

```json
{
  "execution_id": "uuid",
  "status": "completed",
  "results": {
    "task_1": {"output": "result_1"},
    "task_2": {"output": "result_2"}
  },
  "errors": {},
  "metrics": {
    "total_time_ms": 1250,
    "tasks_completed": 2,
    "tasks_failed": 0
  }
}
```

### POST /api/v1/concurrent/gateway/execute

執行並行閘道。

**請求體：**

```json
{
  "execution_id": "uuid",
  "gateway_type": "fork",
  "branches": ["branch_a", "branch_b"],
  "join_mode": "all"
}
```

### GET /api/v1/concurrent/executions/{execution_id}

查詢執行狀態。

**響應：**

```json
{
  "execution_id": "uuid",
  "status": "running",
  "progress": {
    "total_tasks": 5,
    "completed_tasks": 3,
    "failed_tasks": 0,
    "pending_tasks": 2
  },
  "started_at": "2025-12-05T10:00:00Z",
  "estimated_completion": "2025-12-05T10:05:00Z"
}
```

---

## 最佳實踐

### 1. 設置合理的超時

```python
# 根據任務複雜度設置超時
short_tasks = await executor.execute_fork_join(
    tasks=simple_tasks,
    timeout_seconds=60  # 簡單任務 1 分鐘
)

long_tasks = await executor.execute_fork_join(
    tasks=complex_tasks,
    timeout_seconds=600  # 複雜任務 10 分鐘
)
```

### 2. 使用適當的合併模式

```python
# 需要所有結果 - 數據聚合場景
await executor.execute_fork_join(tasks, join_mode="all")

# 只需第一個結果 - 競爭式查詢
await executor.execute_fork_join(tasks, join_mode="any")

# 多數決 - 投票場景
await executor.execute_fork_join(tasks, join_mode="majority")
```

### 3. 監控並發數

```python
from src.core.concurrent import ConcurrentExecutor

# 設置最大並發數，避免資源耗盡
executor = ConcurrentExecutor(
    max_concurrent_tasks=10,
    semaphore_limit=100
)
```

### 4. 處理失敗分支

```python
result = await executor.execute_fork_join(
    tasks=tasks,
    on_failure="continue",  # 不中斷其他任務
    fallback_handler=handle_task_failure
)

async def handle_task_failure(task_id: str, error: Exception):
    # 記錄錯誤
    logger.error(f"Task {task_id} failed: {error}")
    # 返回預設值
    return {"status": "fallback", "data": None}
```

---

## 效能指標

| 指標 | 目標值 | 說明 |
|------|--------|------|
| 吞吐量提升 | ≥ 3x | 相比順序執行 |
| 分支延遲 | < 100ms | Fork/Join 操作延遲 |
| 死鎖檢測 | < 1s | 死鎖檢測時間 |
| 資源使用 | < 80% | CPU/Memory 使用率 |

---

## 常見問題

### Q: 如何處理任務依賴？

A: 使用任務依賴定義：

```python
tasks = [
    TaskDefinition(id="task_a", agent_id="agent_1"),
    TaskDefinition(
        id="task_b",
        agent_id="agent_2",
        depends_on=["task_a"]  # 依賴 task_a
    ),
]
```

### Q: 並行執行會影響結果順序嗎？

A: 使用 `preserve_order=True` 保持順序：

```python
result = await executor.execute_fork_join(
    tasks=tasks,
    preserve_order=True
)
```

### Q: 如何限制單一 Agent 的並發執行數？

A: 使用 per-agent 限制：

```python
executor = ForkJoinExecutor(
    per_agent_limit=5  # 每個 Agent 最多 5 個並發任務
)
```

---

## 相關文檔

- [API 參考](../api-reference/concurrent-api.md)
- [教學：建立並行工作流](../tutorials/build-parallel-workflow.md)
- [效能調優](../best-practices/performance-tuning.md)
