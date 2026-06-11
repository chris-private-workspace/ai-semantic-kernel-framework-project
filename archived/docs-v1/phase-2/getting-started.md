# Phase 2 快速開始指南

本指南幫助您快速開始使用 IPA Platform Phase 2 的進階功能。

---

## 前置需求

確保您已完成以下設置：

### 1. 系統需求

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 16+
- Redis 7+

### 2. 環境設置

```bash
# 複製環境設定
cp .env.example .env

# 啟動基礎服務
docker-compose up -d

# 安裝後端依賴
cd backend
pip install -r requirements.txt

# 安裝前端依賴
cd ../frontend
npm install
```

### 3. 啟動服務

```bash
# 後端 (Terminal 1)
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 前端 (Terminal 2)
cd frontend
npm run dev
```

---

## Phase 2 功能概覽

### 快速驗證 Phase 2 功能

```bash
# 驗證後端模組
cd backend
python -c "
from src.core.concurrent import ForkJoinExecutor, ParallelGateway
from src.core.handoff import HandoffController, HandoffTrigger
from src.core.groupchat import GroupChatManager
from src.core.planning import DynamicPlanner
from src.core.nested import NestedExecutor
from src.core.performance import PerformanceProfiler
print('All Phase 2 modules loaded successfully!')
"
```

---

## 功能示例

### 1. 並行執行 (Concurrent Execution)

建立一個 Fork-Join 並行工作流：

```python
from src.core.concurrent import ForkJoinExecutor, TaskDefinition

# 建立執行器
executor = ForkJoinExecutor()

# 定義並行任務
tasks = [
    TaskDefinition(id="task_1", agent_id="agent_a", inputs={"data": "input_1"}),
    TaskDefinition(id="task_2", agent_id="agent_b", inputs={"data": "input_2"}),
    TaskDefinition(id="task_3", agent_id="agent_c", inputs={"data": "input_3"}),
]

# 執行並行任務
results = await executor.execute_fork_join(
    tasks=tasks,
    join_mode="all",  # 等待所有任務完成
    timeout_seconds=300
)

print(f"All tasks completed: {results}")
```

### 2. Agent 交接 (Agent Handoff)

設置 Agent 之間的任務交接：

```python
from src.core.handoff import HandoffController, HandoffPolicy

# 建立交接控制器
controller = HandoffController()

# 執行優雅交接
handoff = await controller.execute_handoff(
    source_agent_id="agent_a",
    target_agent_id="agent_b",
    execution_id="exec_123",
    policy=HandoffPolicy.GRACEFUL,
    context={
        "task_state": "in_progress",
        "data": {"key": "value"}
    }
)

print(f"Handoff status: {handoff.status}")
```

### 3. 群組對話 (GroupChat)

建立多 Agent 協作討論：

```python
from src.core.groupchat import GroupChatManager, GroupConfig

# 建立群組管理器
manager = GroupChatManager()

# 建立討論群組
group = await manager.create_group(
    name="Project Discussion",
    agent_ids=["agent_1", "agent_2", "agent_3"],
    config=GroupConfig(
        max_rounds=5,
        speaker_selection="round_robin"
    )
)

# 開始討論
messages = await manager.start_discussion(
    group_id=group.id,
    initial_message="討論專案的技術方案"
)

for msg in messages:
    print(f"{msg.agent_id}: {msg.content}")
```

### 4. 動態規劃 (Dynamic Planning)

使用 AI 驅動的任務分解：

```python
from src.core.planning import DynamicPlanner, DecompositionStrategy

# 建立規劃器
planner = DynamicPlanner()

# 分解複雜任務
decomposition = await planner.decompose_task(
    description="建立用戶認證系統，包含登入、註冊、密碼重置功能",
    strategy=DecompositionStrategy.HYBRID,
    max_subtasks=10
)

print(f"Task decomposed into {len(decomposition.subtasks)} subtasks:")
for subtask in decomposition.subtasks:
    print(f"  - {subtask.description} (Priority: {subtask.priority})")
```

### 5. 嵌套工作流 (Nested Workflows)

執行階層式工作流：

```python
from src.core.nested import NestedExecutor, SubWorkflowConfig

# 建立嵌套執行器
executor = NestedExecutor(max_depth=5)

# 執行嵌套工作流
result = await executor.execute_nested(
    parent_workflow_id="workflow_parent",
    child_workflow_id="workflow_child",
    inputs={"key": "value"},
    config=SubWorkflowConfig(
        inherit_context=True,
        propagate_errors=True
    )
)

print(f"Nested execution result: {result.status}")
```

### 6. 效能監控 (Performance)

監控系統效能：

```python
from src.core.performance import PerformanceProfiler, MetricType

# 建立分析器
profiler = PerformanceProfiler()

# 開始分析會話
session = profiler.start_session("api_performance_test")

# 使用裝飾器測量延遲
@profiler.measure_latency("process_request")
async def process_request(data):
    # 處理邏輯
    await some_operation(data)
    return result

# 記錄自定義指標
profiler.record_metric(
    name="custom_metric",
    metric_type=MetricType.THROUGHPUT,
    value=150.5,
    unit="req/s"
)

# 結束會話並獲取摘要
summary = profiler.end_session()
print(f"Session summary: {summary}")

# 獲取優化建議
recommendations = profiler.get_recommendations()
for rec in recommendations:
    print(f"[{rec['severity']}] {rec['message']}")
```

---

## API 快速參考

### 並行執行 API

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/concurrent/fork-join` | POST | 執行 Fork-Join 任務組 |
| `/api/v1/concurrent/gateway/execute` | POST | 執行並行閘道 |
| `/api/v1/concurrent/executions/{id}` | GET | 查詢執行狀態 |

### 交接 API

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/handoff/trigger` | POST | 觸發交接 |
| `/api/v1/handoff/{id}/status` | GET | 查詢交接狀態 |
| `/api/v1/handoff/agents/capabilities` | GET | 獲取 Agent 能力 |

### 群組對話 API

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/groupchat` | POST | 建立群組 |
| `/api/v1/groupchat/{id}/start` | POST | 開始討論 |
| `/api/v1/groupchat/{id}/messages` | GET | 獲取訊息 |

### 動態規劃 API

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/planning/decompose` | POST | 任務分解 |
| `/api/v1/planning/plans` | POST | 建立計劃 |
| `/api/v1/planning/plans/{id}/approve` | POST | 批准計劃 |

### 嵌套工作流 API

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/nested/execute` | POST | 執行嵌套工作流 |
| `/api/v1/nested/execute/recursive` | POST | 遞歸執行 |
| `/api/v1/nested/executions/{id}/tree` | GET | 獲取執行樹 |

### 效能 API

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/performance/metrics` | GET | 獲取效能指標 |
| `/api/v1/performance/profile/start` | POST | 開始分析會話 |
| `/api/v1/performance/optimize` | POST | 執行優化分析 |

---

## 下一步

- 深入學習各功能模組：[Features](./features/)
- 查看完整 API 文檔：[API Reference](./api-reference/)
- 學習最佳實踐：[Best Practices](./best-practices/)
- 探索教學範例：[Tutorials](./tutorials/)

---

## 故障排除

### 常見問題

**Q: 導入模組時出現 ModuleNotFoundError**

確保已正確安裝所有依賴：
```bash
cd backend
pip install -r requirements.txt
```

**Q: 並行執行任務超時**

檢查 timeout 設置並調整：
```python
executor.execute_fork_join(tasks, timeout_seconds=600)  # 增加到 10 分鐘
```

**Q: 效能監控數據不準確**

確保在正確的位置使用 profiler：
```python
# 使用 context manager 確保正確記錄
with profiler.measure("operation"):
    await operation()
```

---

## 支援

如有問題，請參考：
- [FAQ 文檔](./best-practices/faq.md)
- [GitHub Issues](https://github.com/your-repo/issues)
- [技術支援信箱](mailto:support@example.com)
