# 嵌套工作流指南 (Nested Workflows)

## 概述

嵌套工作流支援工作流的階層式組合，實現複雜流程的模組化設計。最大支援 **10 層嵌套**，成功率目標 **≥ 95%**。

---

## 核心概念

### 嵌套模式

| 模式 | 說明 | 適用場景 |
|------|------|----------|
| `SEQUENTIAL` | 順序嵌套 | 流程串接 |
| `PARALLEL` | 並行嵌套 | 同時執行多個子流程 |
| `RECURSIVE` | 遞歸執行 | 重複處理 |
| `DYNAMIC` | 動態嵌套 | 運行時決定子流程 |

### 上下文傳遞

| 策略 | 說明 |
|------|------|
| `INHERIT` | 繼承父工作流上下文 |
| `ISOLATED` | 隔離上下文 |
| `SELECTIVE` | 選擇性傳遞 |
| `MERGE` | 合併上下文 |

### 執行流程

```
┌────────────────────────────────────────────────────────┐
│                   Parent Workflow                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │                                                  │   │
│  │   Start ──▶ Task A ──▶ ┌─────────────────┐      │   │
│  │                        │ Child Workflow 1 │      │   │
│  │                        │  ┌───────────┐  │      │   │
│  │                        │  │ Sub-task  │  │      │   │
│  │                        │  └───────────┘  │      │   │
│  │                        └────────┬────────┘      │   │
│  │                                 │               │   │
│  │   End ◀── Task B ◀─────────────┘               │   │
│  │                                                  │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

---

## 使用方式

### 基本嵌套

```python
from src.core.nested import NestedExecutor, SubWorkflowConfig

# 建立嵌套執行器
executor = NestedExecutor(max_depth=5)

# 執行嵌套工作流
result = await executor.execute_nested(
    parent_workflow_id="workflow_main",
    child_workflow_id="workflow_sub",
    node_id="sub_workflow_node",
    inputs={"data": "input_data"},
    config=SubWorkflowConfig(
        inherit_context=True,
        propagate_errors=True,
        timeout_seconds=300
    )
)

print(f"Status: {result.status}")
print(f"Output: {result.output}")
```

### 並行嵌套

```python
# 並行執行多個子工作流
results = await executor.execute_parallel_nested(
    parent_workflow_id="workflow_main",
    child_workflows=[
        {"workflow_id": "sub_1", "inputs": {"type": "A"}},
        {"workflow_id": "sub_2", "inputs": {"type": "B"}},
        {"workflow_id": "sub_3", "inputs": {"type": "C"}}
    ],
    join_mode="all"
)

for sub_result in results:
    print(f"Sub-workflow {sub_result.workflow_id}: {sub_result.status}")
```

### 遞歸執行

```python
from src.core.nested import RecursionConfig

# 配置遞歸
recursion_config = RecursionConfig(
    max_depth=10,
    max_iterations=100,
    termination_condition="result.value > 1000"
)

# 遞歸執行
result = await executor.execute_recursive(
    workflow_id="recursive_workflow",
    initial_inputs={"value": 1},
    config=recursion_config
)

print(f"Final result: {result.output}")
print(f"Iterations: {result.iterations}")
print(f"Max depth reached: {result.max_depth_reached}")
```

### 動態嵌套

```python
from src.core.nested import DynamicNestedWorkflow

# 建立動態嵌套工作流
dynamic = DynamicNestedWorkflow(executor)

# 根據條件動態選擇子工作流
result = await dynamic.execute(
    parent_workflow_id="main_workflow",
    selector=lambda context: select_child_workflow(context),
    inputs={"task_type": "complex"}
)

async def select_child_workflow(context):
    """根據上下文動態選擇子工作流"""
    task_type = context.get("task_type")

    if task_type == "simple":
        return "simple_workflow"
    elif task_type == "complex":
        return "complex_workflow"
    else:
        return "default_workflow"
```

### 上下文管理

```python
from src.core.nested import ContextManager, ContextScope

# 建立上下文管理器
context_manager = ContextManager()

# 設置上下文傳遞規則
context_manager.set_propagation_rules(
    parent_workflow_id="main_workflow",
    rules={
        "inherit": ["user_id", "session_id"],
        "override": ["config"],
        "isolate": ["temporary_data"]
    }
)

# 執行時使用
result = await executor.execute_nested(
    parent_workflow_id="main_workflow",
    child_workflow_id="sub_workflow",
    context_manager=context_manager
)
```

### 範圍管理

```python
from src.core.nested import ScopeManager

# 建立範圍管理器
scope_manager = ScopeManager()

# 定義變數範圍
scope_manager.define_scope(
    workflow_id="main_workflow",
    variables={
        "global_var": ScopeManager.GLOBAL,
        "local_var": ScopeManager.LOCAL,
        "inherited_var": ScopeManager.INHERITED
    }
)

# 在子工作流中存取
child_context = scope_manager.create_child_scope(
    parent_scope="main_workflow",
    child_workflow_id="sub_workflow"
)
```

---

## API 參考

### POST /api/v1/nested/execute

執行嵌套工作流。

**請求體：**

```json
{
  "parent_workflow_id": "uuid",
  "child_workflow_id": "uuid",
  "node_id": "sub_workflow_node",
  "inputs": {"key": "value"},
  "config": {
    "inherit_context": true,
    "propagate_errors": true,
    "timeout_seconds": 300
  }
}
```

**響應：**

```json
{
  "execution_id": "uuid",
  "parent_workflow_id": "uuid",
  "child_workflow_id": "uuid",
  "status": "completed",
  "output": {"result": "value"},
  "depth": 1,
  "duration_ms": 1500
}
```

### POST /api/v1/nested/execute/recursive

遞歸執行工作流。

**請求體：**

```json
{
  "workflow_id": "uuid",
  "initial_inputs": {"value": 1},
  "max_depth": 10,
  "max_iterations": 100,
  "termination_condition": "output.done == true"
}
```

**響應：**

```json
{
  "execution_id": "uuid",
  "status": "completed",
  "iterations": 15,
  "max_depth_reached": 3,
  "final_output": {"value": 1024, "done": true}
}
```

### GET /api/v1/nested/executions/{execution_id}/tree

獲取執行樹。

**響應：**

```json
{
  "execution_id": "uuid",
  "workflow_id": "uuid",
  "status": "completed",
  "depth": 0,
  "children": [
    {
      "execution_id": "uuid",
      "workflow_id": "uuid",
      "status": "completed",
      "depth": 1,
      "children": []
    }
  ]
}
```

### POST /api/v1/nested/sub-workflows

註冊子工作流。

**請求體：**

```json
{
  "parent_workflow_id": "uuid",
  "workflow_id": "uuid",
  "node_id": "sub_workflow_node",
  "config": {
    "max_depth": 5,
    "timeout_seconds": 300
  }
}
```

### GET /api/v1/nested/depth/{execution_id}

獲取當前嵌套深度。

**響應：**

```json
{
  "execution_id": "uuid",
  "current_depth": 3,
  "max_allowed_depth": 10,
  "path": ["main", "sub_1", "sub_2", "current"]
}
```

---

## 最佳實踐

### 1. 控制嵌套深度

```python
# 設置合理的最大深度
executor = NestedExecutor(
    max_depth=5,  # 不建議超過 10 層
    depth_exceeded_action="fail"  # fail, truncate, warn
)
```

### 2. 使用選擇性上下文傳遞

```python
# 只傳遞必要的上下文
config = SubWorkflowConfig(
    context_propagation="selective",
    propagate_keys=["user_id", "session_id"],
    exclude_keys=["sensitive_data", "temp_vars"]
)
```

### 3. 設置適當的超時

```python
# 子工作流超時應小於父工作流
parent_timeout = 600  # 10 分鐘
child_config = SubWorkflowConfig(
    timeout_seconds=300  # 5 分鐘，留出緩衝
)
```

### 4. 處理錯誤傳播

```python
# 控制錯誤傳播行為
config = SubWorkflowConfig(
    propagate_errors=True,
    error_handling="retry",  # retry, skip, fail
    max_retries=3
)
```

### 5. 監控執行樹

```python
# 獲取完整執行樹
tree = await executor.get_execution_tree(execution_id)

def print_tree(node, indent=0):
    print("  " * indent + f"- {node.workflow_id}: {node.status}")
    for child in node.children:
        print_tree(child, indent + 1)

print_tree(tree)
```

---

## 效能指標

| 指標 | 目標值 | 說明 |
|------|--------|------|
| 最大深度 | 10 層 | 支援的最大嵌套深度 |
| 子工作流執行 | < 1s 額外開銷 | 嵌套調用開銷 |
| 上下文傳遞 | < 50ms | 上下文傳遞時間 |
| 成功率 | ≥ 95% | 嵌套執行成功率 |

---

## 常見問題

### Q: 如何避免無限遞歸？

A: 設置多重保護：

```python
config = RecursionConfig(
    max_depth=10,
    max_iterations=100,
    termination_condition="...",
    max_execution_time_seconds=600
)
```

### Q: 子工作流失敗時如何處理？

A: 使用錯誤處理策略：

```python
config = SubWorkflowConfig(
    on_failure="compensate",  # compensate, rollback, skip
    compensation_workflow_id="cleanup_workflow"
)
```

### Q: 如何追蹤嵌套執行的效能？

A: 使用執行追蹤：

```python
# 啟用詳細追蹤
executor = NestedExecutor(
    enable_tracing=True,
    trace_level="detailed"
)

# 獲取追蹤資訊
trace = await executor.get_trace(execution_id)
for event in trace.events:
    print(f"{event.timestamp}: {event.type} - {event.details}")
```

### Q: 如何在子工作流間共享資料？

A: 使用共享上下文：

```python
# 定義共享變數
shared_context = SharedContext(
    variables={"shared_counter": 0},
    access_mode="read_write"
)

result = await executor.execute_parallel_nested(
    parent_workflow_id="main",
    child_workflows=[...],
    shared_context=shared_context
)
```

---

## 相關文檔

- [API 參考](../api-reference/nested-api.md)
- [教學：設計嵌套工作流](../tutorials/design-nested-workflow.md)
- [上下文管理](./context-management.md)
