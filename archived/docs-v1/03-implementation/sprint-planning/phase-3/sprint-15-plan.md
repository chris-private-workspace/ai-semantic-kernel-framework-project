# Sprint 15: HandoffBuilder 重構

**Sprint 目標**: 將自定義 HandoffController 遷移至 Agent Framework HandoffBuilder
**週期**: Week 31-32 (2 週)
**Story Points**: 34 點
**Phase 3 功能**: P3-F2 (Agent Handoff 重構)

---

## Sprint 概覽

### 目標
1. 實現 HandoffBuilder 適配器
2. 遷移 HandoffController 功能
3. 實現 HandoffUserInputRequest 人機互動
4. 更新 API 端點
5. 完成測試

### 成功標準
- [ ] Agent Handoff 功能通過 HandoffBuilder 實現
- [ ] 現有 API 端點向後兼容
- [ ] Human-in-the-loop 功能正常
- [ ] 測試覆蓋率 >= 80%

---

## User Stories

### S15-1: HandoffBuilder 適配器 (8 點)

**描述**: 實現 HandoffBuilder 的適配器層。

**技術要點**:

```python
# backend/src/integrations/agent_framework/builders/handoff.py

from typing import Any, Dict, List, Optional
from agent_framework import (
    HandoffBuilder,
    HandoffUserInputRequest,
    AgentProtocol,
    Executor,
    Workflow,
)

from ..base import BuilderAdapter


class HandoffBuilderAdapter(BuilderAdapter):
    """
    Adapter for Agent Framework HandoffBuilder.

    Maps our HandoffController API to HandoffBuilder.
    """

    def __init__(
        self,
        id: str,
        participants: Dict[str, AgentProtocol | Executor],
        coordinator_id: Optional[str] = None,
        interaction_mode: str = "autonomous",  # autonomous, human_in_loop
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(config)
        self._id = id
        self._participants = participants
        self._coordinator_id = coordinator_id
        self._interaction_mode = interaction_mode
        self._handoff_routes: Dict[str, List[str]] = {}

    def add_handoff(
        self,
        source_agent: str,
        target_agents: List[str],
        condition: Optional[str] = None,
    ) -> "HandoffBuilderAdapter":
        """Add a handoff route."""
        self._handoff_routes[source_agent] = target_agents
        return self

    def build(self) -> Workflow:
        """Build handoff workflow using HandoffBuilder."""
        builder = HandoffBuilder()

        # Add participants
        builder.participants(**self._participants)

        # Set coordinator
        if self._coordinator_id:
            builder.set_coordinator(self._coordinator_id)

        # Add handoff routes
        for source, targets in self._handoff_routes.items():
            for target in targets:
                builder.add_handoff(source, target)

        # Set interaction mode
        if self._interaction_mode == "human_in_loop":
            builder.with_interaction_mode("human_in_loop")
        else:
            builder.with_interaction_mode("autonomous")

        # Enable return to previous if configured
        if self._config.get("enable_return_to_previous"):
            builder.enable_return_to_previous()

        return builder.build()
```

---

### S15-2: HandoffController 功能遷移 (8 點)

**描述**: 遷移現有 HandoffController 的所有功能。

**驗收標準**:
- [ ] HandoffPolicy 功能保留 (IMMEDIATE, GRACEFUL, CONDITIONAL)
- [ ] HandoffContext 正確傳遞
- [ ] HandoffResult 正確返回

---

### S15-3: HandoffUserInputRequest HITL (8 點)

**描述**: 實現人機互動 (Human-in-the-loop) 功能。

**驗收標準**:
- [ ] HandoffUserInputRequest 正確觸發
- [ ] 用戶輸入正確處理
- [ ] 工作流正確恢復

---

### S15-4: API 端點更新 (5 點)

**描述**: 更新現有 API 端點。

---

### S15-5: 測試完成 (5 點)

**描述**: 完成所有測試。

---

## 完成定義 (Definition of Done)

1. **功能完成**
   - [ ] HandoffBuilder 適配器完成
   - [ ] HITL 功能工作
   - [ ] API 向後兼容

2. **測試完成**
   - [ ] 測試覆蓋率 >= 80%

3. **文檔完成**
   - [ ] API 文檔更新

---

## 相關文檔

- [Phase 3 Overview](./README.md)
- [Sprint 14 Plan](./sprint-14-plan.md) - 前置 Sprint
- [Sprint 16 Plan](./sprint-16-plan.md) - 後續 Sprint
