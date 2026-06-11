# Sprint 14: ConcurrentBuilder 重構

**Sprint 目標**: 將自定義 ConcurrentExecutor 遷移至 Agent Framework ConcurrentBuilder
**週期**: Week 29-30 (2 週)
**Story Points**: 34 點
**Phase 3 功能**: P3-F1 (並行執行重構)

---

## Sprint 概覽

### 目標
1. 實現 ConcurrentBuilder 適配器
2. 遷移 ConcurrentExecutor 功能
3. 整合 fan-out/fan-in edge routing
4. 更新 API 端點
5. 完成測試

### 成功標準
- [ ] 並行執行功能通過 ConcurrentBuilder 實現
- [ ] 現有 API 端點向後兼容
- [ ] 所有並行模式正常工作 (ALL, ANY, MAJORITY, FIRST_SUCCESS)
- [ ] 測試覆蓋率 >= 80%

---

## User Stories

### S14-1: ConcurrentBuilder 適配器 (8 點)

**描述**: 實現 ConcurrentBuilder 的適配器層。

**驗收標準**:
- [ ] ConcurrentBuilderAdapter 類完成
- [ ] 支持所有並行模式
- [ ] 整合 Agent Framework API

**技術要點**:

```python
# backend/src/integrations/agent_framework/builders/concurrent.py

from typing import Any, Dict, List, Optional, Callable
from agent_framework import (
    ConcurrentBuilder,
    AgentExecutor,
    Executor,
    Workflow,
)

from ..base import BuilderAdapter


class ConcurrentBuilderAdapter(BuilderAdapter):
    """
    Adapter for Agent Framework ConcurrentBuilder.

    Maps our ConcurrentExecutor API to ConcurrentBuilder.
    """

    def __init__(
        self,
        id: str,
        participants: List[Executor],
        mode: str = "all",  # all, any, majority, first_success
        aggregator: Optional[Callable] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(config)
        self._id = id
        self._participants = participants
        self._mode = mode
        self._aggregator = aggregator
        self._builder = ConcurrentBuilder()

    def build(self) -> Workflow:
        """Build concurrent workflow using ConcurrentBuilder."""
        # Add participants
        for participant in self._participants:
            self._builder.participants(participant)

        # Configure aggregation based on mode
        if self._mode == "all":
            self._builder.with_aggregator(self._collect_all_aggregator)
        elif self._mode == "any":
            self._builder.with_aggregator(self._any_aggregator)
        elif self._mode == "majority":
            self._builder.with_aggregator(self._majority_aggregator)
        elif self._mode == "first_success":
            self._builder.with_aggregator(self._first_success_aggregator)

        # Use custom aggregator if provided
        if self._aggregator:
            self._builder.with_aggregator(self._aggregator)

        return self._builder.build()

    @staticmethod
    def _collect_all_aggregator(results: List[Any]) -> Dict[str, Any]:
        """Collect all results."""
        return {
            "mode": "all",
            "results": results,
            "count": len(results),
        }

    @staticmethod
    def _any_aggregator(results: List[Any]) -> Dict[str, Any]:
        """Return first completed result."""
        return {
            "mode": "any",
            "result": results[0] if results else None,
        }

    @staticmethod
    def _majority_aggregator(results: List[Any]) -> Dict[str, Any]:
        """Return when majority completed."""
        return {
            "mode": "majority",
            "results": results,
            "count": len(results),
        }

    @staticmethod
    def _first_success_aggregator(results: List[Any]) -> Dict[str, Any]:
        """Return first successful result."""
        for result in results:
            if isinstance(result, dict) and result.get("success"):
                return {"mode": "first_success", "result": result}
        return {"mode": "first_success", "result": results[0] if results else None}
```

---

### S14-2: ConcurrentExecutor 功能遷移 (8 點)

**描述**: 遷移現有 ConcurrentExecutor 的所有功能。

**驗收標準**:
- [ ] 所有並行模式功能保留
- [ ] 超時處理正常
- [ ] 錯誤處理正確
- [ ] 結果合併正確

---

### S14-3: Fan-out/Fan-in Edge Routing (8 點)

**描述**: 整合 Agent Framework 的 edge routing 系統。

**驗收標準**:
- [ ] FanOutEdgeGroup 正確分發任務
- [ ] FanInEdgeGroup 正確收集結果
- [ ] Edge 條件正確評估

---

### S14-4: API 端點更新 (5 點)

**描述**: 更新現有 API 端點以使用新的適配器。

**驗收標準**:
- [ ] 現有端點向後兼容
- [ ] 請求/響應 schema 不變
- [ ] 文檔更新

---

### S14-5: 測試完成 (5 點)

**描述**: 完成所有測試用例。

**驗收標準**:
- [ ] 單元測試覆蓋率 >= 80%
- [ ] 整合測試通過
- [ ] 遷移測試通過

---

## 完成定義 (Definition of Done)

1. **功能完成**
   - [ ] ConcurrentBuilder 適配器完成
   - [ ] 所有並行模式工作
   - [ ] API 向後兼容

2. **測試完成**
   - [ ] 測試覆蓋率 >= 80%
   - [ ] 整合測試通過

3. **文檔完成**
   - [ ] API 文檔更新
   - [ ] 遷移說明

---

## 相關文檔

- [Phase 3 Overview](./README.md)
- [Sprint 13 Plan](./sprint-13-plan.md) - 前置 Sprint
- [Sprint 15 Plan](./sprint-15-plan.md) - 後續 Sprint
