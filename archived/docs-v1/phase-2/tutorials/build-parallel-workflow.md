# 教學：建立並行工作流

## 目標

學習如何建立和執行一個使用 Fork-Join 模式的並行工作流。

---

## 前置需求

- IPA Platform 已安裝並運行
- 已建立至少 2 個 Agent
- 熟悉基本的工作流概念

---

## 步驟一：設計工作流

假設我們要建立一個資料處理工作流，需要同時從多個來源獲取資料：

```
Start → Fork → [Fetch DB] → Join → Merge → End
              → [Fetch API]
              → [Fetch Cache]
```

---

## 步驟二：建立 Agent

首先建立處理各資料來源的 Agent：

```python
# 建立 Agent
agents = []

# 資料庫 Agent
db_agent = await create_agent(
    name="Database Agent",
    description="從資料庫獲取資料",
    capabilities=["database_query"]
)
agents.append(db_agent)

# API Agent
api_agent = await create_agent(
    name="API Agent",
    description="從外部 API 獲取資料",
    capabilities=["api_call"]
)
agents.append(api_agent)

# 快取 Agent
cache_agent = await create_agent(
    name="Cache Agent",
    description="從快取獲取資料",
    capabilities=["cache_read"]
)
agents.append(cache_agent)
```

---

## 步驟三：建立工作流定義

```python
from src.domain.workflows import WorkflowBuilder

workflow = (
    WorkflowBuilder("data_aggregation_workflow")
    .add_start_node("start")
    .add_fork_node("fork_data_sources")
    .add_agent_node("fetch_db", agent_id=db_agent.id)
    .add_agent_node("fetch_api", agent_id=api_agent.id)
    .add_agent_node("fetch_cache", agent_id=cache_agent.id)
    .add_join_node("join_results", mode="all")
    .add_agent_node("merge_data", agent_id=merger_agent.id)
    .add_end_node("end")
    # 連接節點
    .connect("start", "fork_data_sources")
    .connect("fork_data_sources", "fetch_db")
    .connect("fork_data_sources", "fetch_api")
    .connect("fork_data_sources", "fetch_cache")
    .connect("fetch_db", "join_results")
    .connect("fetch_api", "join_results")
    .connect("fetch_cache", "join_results")
    .connect("join_results", "merge_data")
    .connect("merge_data", "end")
    .build()
)

# 儲存工作流
saved_workflow = await workflow_service.create(workflow)
print(f"Workflow created: {saved_workflow.id}")
```

---

## 步驟四：執行工作流

```python
from src.domain.executions import ExecutionService

execution_service = ExecutionService()

# 準備輸入
inputs = {
    "query": "SELECT * FROM users",
    "api_endpoint": "https://api.example.com/users",
    "cache_key": "users_data"
}

# 執行工作流
execution = await execution_service.start(
    workflow_id=saved_workflow.id,
    inputs=inputs,
    timeout_seconds=300
)

print(f"Execution started: {execution.id}")
```

---

## 步驟五：監控執行

```python
import asyncio

# 監控執行進度
while True:
    status = await execution_service.get_status(execution.id)

    print(f"Status: {status.status}")
    print(f"Progress: {status.progress}%")

    if status.is_terminal:
        break

    await asyncio.sleep(1)

# 獲取結果
if status.status == "completed":
    result = await execution_service.get_result(execution.id)
    print(f"Result: {result}")
else:
    errors = await execution_service.get_errors(execution.id)
    print(f"Errors: {errors}")
```

---

## 步驟六：使用 API

也可以通過 API 執行相同操作：

```bash
# 建立工作流
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Data Aggregation",
    "nodes": [
      {"id": "start", "type": "start"},
      {"id": "fork", "type": "parallel_gateway", "gateway_type": "fork"},
      {"id": "fetch_db", "type": "agent_task", "agent_id": "..."},
      {"id": "fetch_api", "type": "agent_task", "agent_id": "..."},
      {"id": "fetch_cache", "type": "agent_task", "agent_id": "..."},
      {"id": "join", "type": "parallel_gateway", "gateway_type": "join"},
      {"id": "merge", "type": "agent_task", "agent_id": "..."},
      {"id": "end", "type": "end"}
    ],
    "edges": [
      {"source": "start", "target": "fork"},
      {"source": "fork", "target": "fetch_db"},
      {"source": "fork", "target": "fetch_api"},
      {"source": "fork", "target": "fetch_cache"},
      {"source": "fetch_db", "target": "join"},
      {"source": "fetch_api", "target": "join"},
      {"source": "fetch_cache", "target": "join"},
      {"source": "join", "target": "merge"},
      {"source": "merge", "target": "end"}
    ]
  }'

# 執行工作流
curl -X POST http://localhost:8000/api/v1/executions \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "<workflow_id>",
    "inputs": {
      "query": "SELECT * FROM users"
    }
  }'
```

---

## 進階：錯誤處理

```python
# 設置錯誤處理策略
workflow = (
    WorkflowBuilder("robust_workflow")
    .add_fork_node("fork", config={
        "error_handling": {
            "on_failure": "continue",
            "max_retries": 3
        }
    })
    # ... 其他節點
    .build()
)
```

---

## 小結

您已學會：
1. 設計並行工作流
2. 使用 Fork-Join 模式
3. 監控執行進度
4. 處理錯誤情況

下一步：
- [設置 Agent 交接](./setup-agent-handoff.md)
- [建立群組對話](./create-groupchat.md)
