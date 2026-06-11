# Sprint 14 Decisions Log

**Sprint**: 14 - ConcurrentBuilder 重構
**記錄開始日期**: 2025-12-05

---

## DECISION-14-01: ConcurrentBuilder 適配策略

**日期**: 2025-12-05
**狀態**: 已決定

### 背景

Agent Framework ConcurrentBuilder 使用 FanOut/FanIn 邊和 aggregator callback 模式，
與 Phase 2 ConcurrentExecutor 的四種模式 (ALL, ANY, MAJORITY, FIRST_SUCCESS) 有結構差異。

### 選項

1. **完全替換**: 直接使用 ConcurrentBuilder，棄用模式概念
2. **適配層**: 創建適配器，將模式映射到 aggregator
3. **混合模式**: 部分功能用 ConcurrentBuilder，部分保留自定義

### 決定

選擇 **選項 2 - 適配層**

### 理由

- 保持 API 向後兼容，現有代碼無需修改
- 模式 (ALL, ANY, MAJORITY, FIRST_SUCCESS) 透過自定義 aggregator 實現
- 底層使用官方 ConcurrentBuilder，獲得框架支持
- 適配層隔離 Agent Framework API 變更

### 實現方式

```python
class ConcurrentBuilderAdapter:
    def __init__(self, mode: ConcurrentMode, ...):
        self._mode = mode
        self._builder = ConcurrentBuilder()

    def build(self):
        # 根據 mode 選擇不同的 aggregator
        aggregator = self._get_aggregator_for_mode(self._mode)
        return self._builder.with_aggregator(aggregator).build()
```

### 影響

- 需要為每種模式實現對應的 aggregator
- MAJORITY 和 FIRST_SUCCESS 模式需要自定義邏輯
- 測試需要覆蓋所有模式

---

## DECISION-14-02: 完成條件 (Completion Condition) 設計

**日期**: 2025-12-05
**狀態**: 已決定

### 背景

Agent Framework 使用 aggregator 收集所有結果後處理，
而 Phase 2 的 ANY/FIRST_SUCCESS 模式需要提前終止。

### 分析

- **ALL 模式**: aggregator 收集所有結果 → 直接映射
- **ANY 模式**: 返回第一個完成的結果 → 需要自定義 aggregator
- **MAJORITY 模式**: 返回 >50% 完成的結果 → 需要自定義 aggregator
- **FIRST_SUCCESS 模式**: 返回第一個成功的結果 → 需要自定義 aggregator

### 決定

為每種模式實現專門的 aggregator callback

### 實現計劃

1. `AllModeAggregator`: 收集所有結果
2. `AnyModeAggregator`: 返回第一個結果
3. `MajorityModeAggregator`: 計數後返回
4. `FirstSuccessModeAggregator`: 過濾成功結果

---

## DECISION-14-03: Executor 包裝策略

**日期**: 2025-12-05
**狀態**: 已決定

### 背景

Phase 2 使用 ConcurrentTask + task_executor callback 模式，
Agent Framework 使用 AgentProtocol/Executor 作為 participants。

### 決定

創建 TaskExecutorWrapper 將 ConcurrentTask 包裝為 Agent Framework Executor

### 實現方式

```python
class TaskExecutorWrapper(Executor):
    """將 ConcurrentTask 包裝為 Agent Framework Executor"""

    def __init__(self, task: ConcurrentTask, executor_fn: Callable):
        super().__init__(id=task.id)
        self._task = task
        self._executor_fn = executor_fn

    @handler
    async def handle(self, input_data: Any, ctx: WorkflowContext) -> None:
        result = await self._executor_fn(self._task, input_data)
        await ctx.yield_output(result)
```

### 影響

- 支持現有 ConcurrentTask 結構
- 兼容 Agent Framework Executor 介面
- 保留任務超時和元數據

---

## 相關連結

- [Sprint 13 Decisions](../sprint-13/decisions.md)
- [Phase 3 Migration Guide](../../../migration/phase3-migration-guide.md)
