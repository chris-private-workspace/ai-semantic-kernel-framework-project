# 錯誤處理最佳實踐

## 概述

本文檔提供 IPA Platform Phase 2 功能的錯誤處理指南。

---

## 並行執行錯誤處理

### 部分失敗處理

```python
from src.core.concurrent import ForkJoinExecutor, ErrorHandlingMode

executor = ForkJoinExecutor(
    error_handling=ErrorHandlingMode.CONTINUE
)

result = await executor.execute_fork_join(
    tasks=tasks,
    on_failure="continue",  # 部分失敗繼續執行
    fallback_handler=handle_task_failure
)

# 檢查失敗任務
if result.errors:
    for task_id, error in result.errors.items():
        logger.error(f"Task {task_id} failed: {error}")
        await notify_admin(task_id, error)
```

### 重試機制

```python
result = await executor.execute_fork_join(
    tasks=tasks,
    error_handling={
        "on_failure": "retry",
        "max_retries": 3,
        "retry_delay_seconds": 2.0,
        "exponential_backoff": True
    }
)
```

### 回退處理

```python
async def fallback_handler(task_id: str, error: Exception):
    """任務失敗時的回退處理"""
    logger.warning(f"Task {task_id} failed, using fallback")

    # 返回預設值
    return {
        "status": "fallback",
        "data": get_default_value(task_id)
    }
```

---

## Agent 交接錯誤處理

### 交接失敗恢復

```python
try:
    handoff = await controller.execute_handoff(
        source_agent_id="agent_a",
        target_agent_id="agent_b",
        policy=HandoffPolicy.GRACEFUL
    )
except HandoffFailedException as e:
    logger.error(f"Handoff failed: {e}")

    # 回退到原 Agent
    await controller.rollback(handoff.id)

    # 或嘗試備選 Agent
    backup_agent = await matcher.find_backup_agent(
        original_target="agent_b",
        required_capabilities=["data_analysis"]
    )
    await controller.execute_handoff(
        source_agent_id="agent_a",
        target_agent_id=backup_agent.id
    )
```

### 超時處理

```python
import asyncio

async def safe_handoff(source, target, timeout=30):
    try:
        return await asyncio.wait_for(
            controller.execute_handoff(source, target),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.error(f"Handoff timeout after {timeout}s")
        # 記錄並嘗試恢復
        await controller.cancel_pending_handoff(source)
        return None
```

---

## 群組對話錯誤處理

### Agent 無響應

```python
config = GroupConfig(
    agent_response_timeout=30,
    skip_unresponsive=True,
    fallback_message="[Agent 暫時無法響應]",
    max_consecutive_failures=3
)

# 監聽錯誤事件
manager.on_agent_error(lambda agent_id, error:
    handle_agent_error(agent_id, error)
)
```

### 對話恢復

```python
# 保存檢查點
checkpoint = await manager.create_checkpoint(group_id)

try:
    await manager.execute_round(group_id)
except Exception as e:
    logger.error(f"Round failed: {e}")
    # 從檢查點恢復
    await manager.restore_from_checkpoint(group_id, checkpoint)
```

---

## 動態規劃錯誤處理

### 分解失敗

```python
try:
    decomposition = await planner.decompose_task(description)
except DecompositionError as e:
    logger.error(f"Decomposition failed: {e}")

    # 使用簡化策略重試
    decomposition = await planner.decompose_task(
        description,
        strategy=DecompositionStrategy.SIMPLE,
        max_subtasks=5
    )
```

### 執行失敗恢復

```python
# 設置執行恢復策略
result = await planner.execute_plan(
    plan_id=plan.id,
    on_step_failure="retry_then_skip",
    max_step_retries=2,
    save_progress=True  # 保存進度以便恢復
)

# 檢查跳過的步驟
if result.skipped_steps:
    logger.warning(f"Skipped steps: {result.skipped_steps}")
    await handle_skipped_steps(result.skipped_steps)
```

---

## 嵌套工作流錯誤處理

### 深度限制超過

```python
try:
    result = await executor.execute_nested(
        parent_workflow_id="main",
        child_workflow_id="sub"
    )
except MaxDepthExceededError as e:
    logger.error(f"Max depth exceeded: {e}")

    # 替代方案：扁平化執行
    result = await executor.execute_flat(
        workflow_id="sub",
        context=flatten_context(parent_context)
    )
```

### 子工作流失敗

```python
config = SubWorkflowConfig(
    propagate_errors=True,
    on_failure="compensate",
    compensation_workflow_id="cleanup_workflow"
)

try:
    result = await executor.execute_nested(
        parent_workflow_id="main",
        child_workflow_id="risky_sub",
        config=config
    )
except ChildWorkflowError as e:
    logger.error(f"Child workflow failed: {e}")
    # 補償工作流已自動執行
```

---

## 全局錯誤處理

### 統一異常處理

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(IPAException)
async def ipa_exception_handler(request: Request, exc: IPAException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "trace_id": request.state.trace_id
        }
    )
```

### 日誌記錄

```python
import structlog

logger = structlog.get_logger()

async def process_with_logging(operation):
    trace_id = generate_trace_id()

    try:
        logger.info("operation_started",
            trace_id=trace_id,
            operation=operation.name
        )

        result = await operation.execute()

        logger.info("operation_completed",
            trace_id=trace_id,
            duration_ms=result.duration
        )

        return result

    except Exception as e:
        logger.error("operation_failed",
            trace_id=trace_id,
            error=str(e),
            exc_info=True
        )
        raise
```

---

## 錯誤處理檢查清單

- [ ] 所有外部調用都有超時設置
- [ ] 實現了重試機制
- [ ] 有回退/備選方案
- [ ] 錯誤被正確記錄
- [ ] 敏感資訊不會洩露在錯誤訊息中
- [ ] 實現了熔斷機制
- [ ] 有監控和警報
- [ ] 文檔化了所有錯誤碼
