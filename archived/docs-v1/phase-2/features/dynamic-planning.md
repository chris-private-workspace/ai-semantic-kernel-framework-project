# 動態規劃指南 (Dynamic Planning)

## 概述

動態規劃功能使用 AI 驅動的任務分解和執行規劃，實現複雜任務的智能編排。規劃準確率目標 **≥ 85%**。

---

## 核心概念

### 分解策略

| 策略 | 說明 | 適用場景 |
|------|------|----------|
| `HIERARCHICAL` | 階層式分解 | 大型專案 |
| `DEPENDENCY` | 依賴分析 | 有依賴關係的任務 |
| `HYBRID` | 混合模式 | 一般複雜任務 |

### 計劃狀態

| 狀態 | 說明 |
|------|------|
| `DRAFT` | 草稿，待審核 |
| `PENDING_APPROVAL` | 等待批准 |
| `APPROVED` | 已批准 |
| `EXECUTING` | 執行中 |
| `COMPLETED` | 已完成 |
| `FAILED` | 失敗 |
| `CANCELLED` | 已取消 |

### 決策類型

| 類型 | 說明 |
|------|------|
| `TASK_ALLOCATION` | 任務分配 |
| `RESOURCE_SELECTION` | 資源選擇 |
| `ERROR_RECOVERY` | 錯誤恢復 |
| `PLAN_ADJUSTMENT` | 計劃調整 |
| `PRIORITY_CHANGE` | 優先級變更 |

---

## 使用方式

### 任務分解

```python
from src.core.planning import DynamicPlanner, DecompositionStrategy

# 建立規劃器
planner = DynamicPlanner()

# 分解任務
decomposition = await planner.decompose_task(
    description="建立完整的用戶認證系統，包含登入、註冊、密碼重置、雙因素驗證",
    strategy=DecompositionStrategy.HYBRID,
    max_subtasks=10,
    context={
        "tech_stack": "Python FastAPI + React",
        "database": "PostgreSQL"
    }
)

print(f"分解為 {len(decomposition.subtasks)} 個子任務:")
for task in decomposition.subtasks:
    print(f"  - {task.description}")
    print(f"    優先級: {task.priority}")
    print(f"    估計時間: {task.estimated_duration}")
```

### 建立計劃

```python
from src.core.planning import PlanBuilder

# 建立計劃
plan = await planner.create_plan(
    goal="完成用戶認證系統",
    subtasks=decomposition.subtasks,
    constraints={
        "deadline": "2025-12-15",
        "resources": ["developer_agent", "qa_agent"]
    }
)

print(f"Plan ID: {plan.id}")
print(f"Steps: {len(plan.steps)}")
```

### 計劃審核與批准

```python
# 獲取計劃詳情供審核
plan_details = await planner.get_plan_details(plan.id)

print("計劃步驟:")
for step in plan_details.steps:
    print(f"  {step.order}. {step.description}")
    print(f"     Agent: {step.assigned_agent}")
    print(f"     依賴: {step.dependencies}")

# 批准計劃
approved_plan = await planner.approve_plan(
    plan_id=plan.id,
    approver="admin_user",
    comments="計劃看起來合理"
)
```

### 執行計劃

```python
# 開始執行
execution = await planner.execute_plan(plan.id)

# 監控進度
async for progress in planner.monitor_progress(execution.id):
    print(f"Progress: {progress.percentage}%")
    print(f"Current step: {progress.current_step}")
    print(f"Status: {progress.status}")

    if progress.is_complete:
        break
```

### 自主決策

```python
from src.core.planning import DecisionMaker, DecisionType

# 建立決策器
decision_maker = DecisionMaker(
    confidence_threshold=0.8,
    human_approval_required=False
)

# 自動處理決策
async def handle_decision(decision_context):
    decision = await decision_maker.make_decision(
        decision_type=DecisionType.ERROR_RECOVERY,
        context=decision_context,
        options=[
            {"action": "retry", "risk": 0.2},
            {"action": "skip", "risk": 0.5},
            {"action": "escalate", "risk": 0.1}
        ]
    )

    print(f"Decision: {decision.action}")
    print(f"Confidence: {decision.confidence}")
    print(f"Reasoning: {decision.reasoning}")

    return decision
```

### 試錯機制

```python
from src.core.planning import TrialAndError

# 建立試錯執行器
trial_executor = TrialAndError(
    max_attempts=3,
    learning_enabled=True
)

# 執行帶試錯的任務
result = await trial_executor.execute_with_retry(
    task=task_to_execute,
    on_failure=lambda e: analyze_failure(e),
    on_success=lambda r: record_success(r)
)

# 獲取學習結果
lessons = await trial_executor.get_lessons_learned(task.id)
```

---

## API 參考

### POST /api/v1/planning/decompose

分解任務。

**請求體：**

```json
{
  "task_description": "建立用戶認證系統",
  "strategy": "hybrid",
  "max_subtasks": 10,
  "context": {
    "tech_stack": "Python FastAPI"
  }
}
```

**響應：**

```json
{
  "decomposition_id": "uuid",
  "original_task": "建立用戶認證系統",
  "subtasks": [
    {
      "id": "uuid",
      "description": "設計資料庫 schema",
      "priority": 1,
      "estimated_duration": "2h",
      "dependencies": [],
      "required_capabilities": ["database_design"]
    }
  ],
  "total_estimated_duration": "16h"
}
```

### POST /api/v1/planning/plans

建立計劃。

**請求體：**

```json
{
  "goal": "完成用戶認證系統",
  "subtasks": ["uuid1", "uuid2"],
  "constraints": {
    "deadline": "2025-12-15",
    "budget_hours": 20
  }
}
```

### POST /api/v1/planning/plans/{plan_id}/approve

批准計劃。

**查詢參數：**

- `approver`: 批准者名稱

**響應：**

```json
{
  "plan_id": "uuid",
  "status": "approved",
  "approved_by": "admin",
  "approved_at": "2025-12-05T10:00:00Z"
}
```

### POST /api/v1/planning/plans/{plan_id}/execute

執行計劃。

**響應：**

```json
{
  "execution_id": "uuid",
  "plan_id": "uuid",
  "status": "executing",
  "started_at": "2025-12-05T10:00:00Z"
}
```

### GET /api/v1/planning/plans/{plan_id}/progress

獲取執行進度。

**響應：**

```json
{
  "plan_id": "uuid",
  "progress_percentage": 60,
  "current_step": 3,
  "total_steps": 5,
  "completed_steps": [1, 2],
  "status": "executing",
  "estimated_completion": "2025-12-05T12:00:00Z"
}
```

### POST /api/v1/planning/plans/{plan_id}/adjust

調整計劃。

**請求體：**

```json
{
  "adjustments": [
    {
      "step_id": "uuid",
      "action": "reschedule",
      "new_deadline": "2025-12-10"
    }
  ],
  "reason": "需求變更"
}
```

---

## 最佳實踐

### 1. 提供詳細的上下文

```python
decomposition = await planner.decompose_task(
    description="建立 API",
    context={
        "existing_code": "FastAPI framework",
        "database": "PostgreSQL",
        "auth_method": "JWT",
        "api_style": "RESTful",
        "documentation_required": True
    }
)
```

### 2. 使用適當的分解策略

```python
# 大型專案 - 階層式
large_project = await planner.decompose_task(
    description="...",
    strategy=DecompositionStrategy.HIERARCHICAL
)

# 有依賴的任務 - 依賴分析
dependent_tasks = await planner.decompose_task(
    description="...",
    strategy=DecompositionStrategy.DEPENDENCY
)
```

### 3. 設置適當的審批流程

```python
# 高風險計劃需要人工審批
plan = await planner.create_plan(
    ...,
    approval_required=True,
    approval_levels=["team_lead", "manager"]
)
```

### 4. 監控和調整

```python
# 設置自動調整閾值
planner.configure(
    auto_adjust_on_delay=True,
    delay_threshold_percent=20,
    notification_on_adjustment=True
)
```

---

## 效能指標

| 指標 | 目標值 | 說明 |
|------|--------|------|
| 任務分解 | < 5s | 分解時間 |
| 決策時間 | < 3s | 自主決策時間 |
| 計劃調整 | < 2s | 計劃修改時間 |
| 準確率 | ≥ 85% | 規劃準確率 |

---

## 常見問題

### Q: 分解結果不理想怎麼辦？

A: 提供更詳細的上下文或手動調整：

```python
# 手動調整分解結果
adjusted = await planner.adjust_decomposition(
    decomposition_id=decomposition.id,
    add_subtasks=[{"description": "新增的子任務"}],
    remove_subtasks=["uuid_to_remove"],
    reorder=True
)
```

### Q: 計劃執行中如何處理意外？

A: 使用動態調整：

```python
# 處理執行異常
await planner.handle_exception(
    plan_id=plan.id,
    step_id=failed_step.id,
    exception=error,
    recovery_action="retry_with_modification"
)
```

### Q: 如何追蹤決策歷史？

A: 使用決策日誌：

```python
# 獲取決策歷史
decisions = await planner.get_decision_history(plan.id)
for d in decisions:
    print(f"{d.timestamp}: {d.decision_type} - {d.action}")
```

---

## 相關文檔

- [API 參考](../api-reference/planning-api.md)
- [教學：設計動態規劃](../tutorials/design-dynamic-planning.md)
- [試錯機制](./trial-and-error.md)
