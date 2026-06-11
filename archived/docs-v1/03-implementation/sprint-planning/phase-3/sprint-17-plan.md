# Sprint 17: MagenticBuilder 重構

**Sprint 目標**: 將自定義 DynamicPlanner 遷移至 Agent Framework MagenticBuilder
**週期**: Week 35-36 (2 週)
**Story Points**: 42 點
**Phase 3 功能**: P3-F4 (Dynamic Planning 重構)

---

## Sprint 概覽

### 目標
1. 實現 MagenticBuilder 適配器
2. 實現 StandardMagenticManager
3. 整合 Task/Progress Ledger
4. 實現 Human Intervention 系統
5. 更新 API 端點
6. 完成測試

### 成功標準
- [ ] Dynamic Planning 功能通過 MagenticBuilder 實現
- [ ] Task Ledger 正確追蹤
- [ ] Progress Ledger 正確評估
- [ ] Human Intervention 正常工作
- [ ] 測試覆蓋率 >= 80%

---

## User Stories

### S17-1: MagenticBuilder 適配器 (8 點)

**技術要點**:

```python
# backend/src/integrations/agent_framework/builders/magentic.py

from typing import Any, Dict, List, Optional
from agent_framework import (
    MagenticBuilder,
    MagenticContext,
    MagenticManagerBase,
    StandardMagenticManager,
    MagenticHumanInterventionRequest,
    MagenticHumanInterventionReply,
    MagenticHumanInterventionKind,
    AgentProtocol,
    Executor,
    Workflow,
)

from ..base import BuilderAdapter


class MagenticBuilderAdapter(BuilderAdapter):
    """
    Adapter for Agent Framework MagenticBuilder (Magentic One).

    Maps our DynamicPlanner API to MagenticBuilder.
    """

    def __init__(
        self,
        id: str,
        participants: Dict[str, AgentProtocol | Executor],
        manager: Optional[MagenticManagerBase] = None,
        max_round_count: int = 20,
        max_stall_count: int = 3,
        enable_plan_review: bool = False,
        enable_stall_intervention: bool = False,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(config)
        self._id = id
        self._participants = participants
        self._manager = manager
        self._max_round_count = max_round_count
        self._max_stall_count = max_stall_count
        self._enable_plan_review = enable_plan_review
        self._enable_stall_intervention = enable_stall_intervention

    def build(self) -> Workflow:
        """Build Magentic One workflow."""
        builder = MagenticBuilder()

        # Add participants
        builder.participants(**self._participants)

        # Set manager
        if self._manager:
            builder.with_manager(self._manager)
        else:
            # Use standard manager with configuration
            builder.with_standard_manager(
                max_round_count=self._max_round_count,
                max_stall_count=self._max_stall_count,
            )

        # Configure plan review
        if self._enable_plan_review:
            builder.with_plan_review(enable=True)

        # Configure stall intervention
        if self._enable_stall_intervention:
            builder.with_stall_intervention(enable=True)

        return builder.build()
```

---

### S17-2: StandardMagenticManager 實現 (8 點)

**描述**: 實現或自定義 MagenticManager。

**驗收標準**:
- [ ] Task Ledger 創建正確
- [ ] Progress Ledger 評估正確
- [ ] 發言者選擇正確
- [ ] Final Answer 生成正確

---

### S17-3: Task/Progress Ledger 整合 (8 點)

**描述**: 整合 Magentic One 的 Ledger 系統。

**驗收標準**:
- [ ] Facts extraction 正確
- [ ] Plan creation 正確
- [ ] Progress evaluation 正確
- [ ] Replan trigger 正確

---

### S17-4: Human Intervention 系統 (8 點)

**描述**: 實現完整的人機互動系統。

**驗收標準**:
- [ ] PLAN_REVIEW intervention 正常
- [ ] TOOL_APPROVAL intervention 正常
- [ ] STALL intervention 正常

---

### S17-5: API 端點更新 (5 點)

---

### S17-6: 測試完成 (5 點)

---

## 完成定義 (Definition of Done)

1. **功能完成**
   - [ ] MagenticBuilder 適配器完成
   - [ ] Ledger 系統工作
   - [ ] Human Intervention 工作

2. **測試完成**
   - [ ] 測試覆蓋率 >= 80%

---

## 相關文檔

- [Phase 3 Overview](./README.md)
- [Sprint 16 Plan](./sprint-16-plan.md) - 前置 Sprint
- [Sprint 18 Plan](./sprint-18-plan.md) - 後續 Sprint
