# Sprint 23: Nested Workflow 重構

## Sprint Overview

| Property | Value |
|----------|-------|
| **Sprint** | 23 |
| **Phase** | 4 - 完整重構 |
| **Focus** | 創建 NestedWorkflowAdapter |
| **Duration** | 2 週 |
| **Total Story Points** | 35 |

## Sprint Goal

創建 `NestedWorkflowAdapter`，使用官方 Workflow 組合功能實現嵌套工作流，同時保留 Phase 2 的上下文傳播、遞歸深度控制等自定義功能。

---

## 問題分析

### 當前狀態

| 模組 | 行數 | 問題 |
|------|------|------|
| `domain/orchestration/nested/` | 4,138 | 自行實現嵌套工作流 |
| 上下文傳播 | ~1,200 | 未使用官方 Workflow 組合 |
| 遞歸控制 | ~800 | 自行實現深度追蹤 |

### 目標架構

```
NestedWorkflowAdapter
    ├─ 使用官方 WorkflowBuilder 組合子工作流
    ├─ 保留上下文傳播邏輯 (ContextPropagation)
    └─ 保留遞歸深度控制 (RecursiveDepthTracker)

支持的子工作流類型:
    ├─ GroupChatBuilderAdapter
    ├─ HandoffBuilderAdapter
    ├─ ConcurrentBuilderAdapter
    └─ 官方 Workflow 實例
```

---

## User Stories

### S23-1: 設計 NestedWorkflowAdapter 架構 (8 pts)

**目標**: 創建嵌套工作流適配器的核心架構

**範圍**: 新建 `integrations/agent_framework/builders/nested_workflow.py`

**架構設計**:
```python
from agent_framework import WorkflowBuilder, Workflow, WorkflowExecutor
from typing import Dict, List, Any, Optional, Union, Callable
from domain.orchestration.nested.context_propagation import (
    ContextPropagation,
    ContextPropagationStrategy,
)
from domain.orchestration.nested.recursive_handler import RecursiveDepthTracker

class NestedWorkflowAdapter:
    """
    嵌套工作流適配器。

    使用官方 WorkflowBuilder 組合功能實現嵌套執行，
    同時保留 Phase 2 的上下文傳播和遞歸深度控制。
    """

    def __init__(
        self,
        id: str,
        max_depth: int = 5,
        context_strategy: ContextPropagationStrategy = ContextPropagationStrategy.INHERITED,
    ):
        self._id = id
        self._max_depth = max_depth
        self._context_strategy = context_strategy

        # 子工作流註冊表
        self._sub_workflows: Dict[str, Workflow] = {}
        self._sub_adapters: Dict[str, Any] = {}

        # Phase 2 邏輯保留
        self._depth_tracker = RecursiveDepthTracker(max_depth)
        self._context_propagator = ContextPropagation(context_strategy)

        # 執行模式
        self._execution_mode: Optional[str] = None
        self._execution_order: List[str] = []
        self._conditions: Dict[str, Callable] = {}

    def add_sub_workflow(
        self,
        name: str,
        workflow: Union[Workflow, "BuilderAdapter"],
    ) -> "NestedWorkflowAdapter":
        """
        添加子工作流。

        支持:
        - 官方 Workflow 實例
        - 任何 BuilderAdapter (GroupChat, Handoff, Concurrent)
        """
        if isinstance(workflow, Workflow):
            self._sub_workflows[name] = workflow
        elif hasattr(workflow, 'build'):
            # BuilderAdapter
            self._sub_adapters[name] = workflow
            self._sub_workflows[name] = workflow.build()
        else:
            raise TypeError(f"不支持的工作流類型: {type(workflow)}")

        return self
```

**驗收標準**:
- [ ] `NestedWorkflowAdapter` 類結構完整
- [ ] 支持添加多種類型的子工作流
- [ ] 整合 `RecursiveDepthTracker`
- [ ] 整合 `ContextPropagation`
- [ ] 基本測試通過

---

### S23-2: 實現上下文傳播邏輯 (8 pts)

**目標**: 整合並保留 Phase 2 的上下文傳播功能

**範圍**:
- `integrations/agent_framework/builders/nested_workflow.py`
- 保留 `domain/orchestration/nested/context_propagation.py`

**上下文策略**:

| 策略 | 說明 | 用途 |
|------|------|------|
| `INHERITED` | 完全繼承父上下文 | 默認行為 |
| `ISOLATED` | 隔離，不繼承 | 獨立執行 |
| `MERGED` | 合併父子上下文 | 混合執行 |
| `FILTERED` | 過濾特定字段 | 敏感數據控制 |

**實現方式**:
```python
class NestedWorkflowAdapter:
    def with_context_strategy(
        self,
        strategy: ContextPropagationStrategy,
        allowed_keys: Optional[List[str]] = None,
        additional_context: Optional[Dict] = None,
    ) -> "NestedWorkflowAdapter":
        """
        配置上下文傳播策略。
        """
        self._context_propagator = ContextPropagation(
            strategy=strategy,
            allowed_keys=allowed_keys,
            additional_context=additional_context,
        )
        return self

    def _prepare_child_context(self, parent_context: Dict) -> Dict:
        """準備子工作流的上下文"""
        return self._context_propagator.prepare(parent_context)

    def _finalize_result(self, child_result: Any, parent_context: Dict) -> Any:
        """處理子工作流的結果"""
        return self._context_propagator.finalize(child_result, parent_context)
```

**驗收標準**:
- [ ] 所有 4 種策略正常工作
- [ ] 上下文數據正確傳遞
- [ ] 結果正確處理
- [ ] 測試覆蓋每種策略

---

### S23-3: 實現遞歸深度控制 (5 pts)

**目標**: 保留遞歸深度控制作為安全機制

**範圍**:
- `integrations/agent_framework/builders/nested_workflow.py`
- 保留 `domain/orchestration/nested/recursive_handler.py`

**功能說明**:
1. **深度追蹤** - 追蹤當前嵌套深度
2. **深度限制** - 防止無限遞歸
3. **深度報告** - 記錄執行深度

**實現方式**:
```python
class NestedWorkflowAdapter:
    async def run(self, input_data: Any) -> Any:
        """執行嵌套工作流"""
        # 檢查遞歸深度
        if not self._depth_tracker.can_enter():
            raise RecursionError(
                f"超過最大遞歸深度: {self._max_depth}，"
                f"當前深度: {self._depth_tracker.current_depth}"
            )

        self._depth_tracker.enter()
        try:
            # 準備上下文
            context = self._prepare_child_context(input_data)

            # 執行工作流
            workflow = self.build()
            result = await workflow.run(context)

            # 處理結果
            return self._finalize_result(result, input_data)

        finally:
            self._depth_tracker.exit()
```

**驗收標準**:
- [ ] 深度追蹤正確
- [ ] 超過深度限制時拋出錯誤
- [ ] 正常退出時深度正確減少
- [ ] 異常情況下深度正確恢復

---

### S23-4: 重構 Nested API 路由 (8 pts)

**目標**: 修改 API 層以使用 `NestedWorkflowAdapter`

**範圍**: `api/v1/nested/routes.py` 或相關路由

**修改前**:
```python
from domain.orchestration.nested.executor import NestedWorkflowExecutor

@router.post("/execute")
async def execute_nested(request: NestedWorkflowRequest):
    executor = NestedWorkflowExecutor(...)
    return await executor.execute(request.workflows, request.input_data)
```

**修改後**:
```python
from integrations.agent_framework.builders.nested_workflow import NestedWorkflowAdapter
from integrations.agent_framework.builders.groupchat import GroupChatBuilderAdapter
from integrations.agent_framework.builders.handoff import HandoffBuilderAdapter
from integrations.agent_framework.builders.concurrent import ConcurrentBuilderAdapter

@router.post("/execute")
async def execute_nested(request: NestedWorkflowRequest):
    adapter = NestedWorkflowAdapter(
        id=request.id,
        max_depth=request.max_depth,
        context_strategy=request.context_strategy,
    )

    # 添加子工作流
    for sub in request.sub_workflows:
        if sub.type == "groupchat":
            sub_adapter = GroupChatBuilderAdapter(**sub.config)
        elif sub.type == "handoff":
            sub_adapter = HandoffBuilderAdapter(**sub.config)
        elif sub.type == "concurrent":
            sub_adapter = ConcurrentBuilderAdapter(**sub.config)
        else:
            raise ValueError(f"未知子工作流類型: {sub.type}")

        adapter.add_sub_workflow(sub.name, sub_adapter)

    # 設置執行模式
    if request.execution_mode == "sequential":
        adapter.with_sequential_execution(request.execution_order)
    elif request.execution_mode == "conditional":
        adapter.with_conditional_execution(request.conditions)
    elif request.execution_mode == "parallel":
        adapter.with_parallel_execution()

    return await adapter.run(request.input_data)
```

**驗收標準**:
- [ ] API 層使用 `NestedWorkflowAdapter`
- [ ] 支持所有子工作流類型
- [ ] 支持所有執行模式
- [ ] API 響應格式保持不變
- [ ] 集成測試通過

---

### S23-5: 測試和文檔 (6 pts)

**測試文件**:
- 新建 `tests/unit/test_nested_workflow_adapter.py`
- 更新 `tests/integration/test_nested_api.py`

**測試用例**:
- [ ] 基本嵌套執行
- [ ] 多層嵌套 (深度 = 3)
- [ ] 上下文傳播策略測試 (INHERITED, ISOLATED, MERGED, FILTERED)
- [ ] 遞歸深度限制測試
- [ ] 子工作流類型測試 (GroupChat, Handoff, Concurrent)
- [ ] 執行模式測試 (sequential, conditional, parallel)
- [ ] 錯誤處理測試
- [ ] 邊界情況測試

**文檔更新**:
- [ ] 創建 `docs/03-implementation/migration/nested-workflow-migration.md`

**驗收標準**:
- [ ] 所有測試通過
- [ ] 測試覆蓋率 > 80%
- [ ] 遷移指南完成

---

## Sprint 完成標準 (Definition of Done)

### 代碼驗證

```bash
# 1. 檢查 API 層不再直接使用 domain/orchestration/nested
cd backend
grep -r "from domain.orchestration.nested" src/api/
# 預期: 返回 0 結果

# 2. 運行所有測試
pytest tests/unit/test_nested*.py tests/integration/test_nested*.py -v
# 預期: 所有測試通過
```

### 完成確認清單

- [ ] S23-1: NestedWorkflowAdapter 架構完成
- [ ] S23-2: 上下文傳播整合完成
- [ ] S23-3: 遞歸深度控制完成
- [ ] S23-4: API 路由重構完成
- [ ] S23-5: 測試和文檔完成
- [ ] 可以嵌套 GroupChat、Handoff、Concurrent
- [ ] 測試覆蓋率 > 80%
- [ ] 代碼審查完成
- [ ] 更新 bmm-workflow-status.yaml

---

## 風險與緩解

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|----------|
| 上下文傳播不正確 | 中 | 高 | 詳細測試每種策略 |
| 遞歸深度控制失效 | 低 | 高 | 添加額外安全檢查 |
| 子工作流執行順序錯誤 | 中 | 中 | 執行順序驗證測試 |

---

## 依賴關係

| 依賴項 | 狀態 | 說明 |
|--------|------|------|
| Sprint 22 | 待完成 | Concurrent & Memory 遷移 |
| `GroupChatBuilderAdapter` | ✅ (Sprint 20) | 子工作流類型 |
| `HandoffBuilderAdapter` | ✅ (Sprint 21) | 子工作流類型 |
| `ConcurrentBuilderAdapter` | ✅ (Sprint 22) | 子工作流類型 |
| 官方 `WorkflowBuilder` | ✅ 可用 | 組合子工作流 |

---

## 時間規劃

| Story | Points | 建議順序 | 依賴 |
|-------|--------|----------|------|
| S23-1: 架構設計 | 8 | 1 | 無 |
| S23-2: 上下文傳播 | 8 | 2 | S23-1 |
| S23-3: 遞歸深度控制 | 5 | 3 | S23-1 |
| S23-4: API 路由重構 | 8 | 4 | S23-1, S23-2, S23-3 |
| S23-5: 測試和文檔 | 6 | 5 | S23-4 |

---

**創建日期**: 2025-12-06
**最後更新**: 2025-12-06
**版本**: 1.0
