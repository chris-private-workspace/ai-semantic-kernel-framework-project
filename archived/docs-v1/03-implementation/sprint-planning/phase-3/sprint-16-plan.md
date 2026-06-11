# Sprint 16: GroupChatBuilder 重構

**Sprint 目標**: 將自定義 GroupChatManager 遷移至 Agent Framework GroupChatBuilder
**週期**: Week 33-34 (2 週)
**Story Points**: 42 點
**Phase 3 功能**: P3-F3 (GroupChat 重構)

---

## Sprint 概覽

### 目標
1. 實現 GroupChatBuilder 適配器
2. 遷移 GroupChatManager 核心功能
3. 實現 GroupChatOrchestratorExecutor
4. 整合 ManagerSelectionResponse
5. 更新 API 端點
6. 完成測試

### 成功標準
- [ ] GroupChat 功能通過 GroupChatBuilder 實現
- [ ] 發言者選擇正確工作
- [ ] 終止條件正確判斷
- [ ] 測試覆蓋率 >= 80%

---

## User Stories

### S16-1: GroupChatBuilder 適配器 (8 點)

**技術要點**:

```python
# backend/src/integrations/agent_framework/builders/groupchat.py

from typing import Any, Dict, List, Optional, Callable
from agent_framework import (
    GroupChatBuilder,
    GroupChatDirective,
    GroupChatStateSnapshot,
    ManagerSelectionRequest,
    ManagerSelectionResponse,
    AgentProtocol,
    Executor,
    Workflow,
)

from ..base import BuilderAdapter


class GroupChatBuilderAdapter(BuilderAdapter):
    """
    Adapter for Agent Framework GroupChatBuilder.

    Maps our GroupChatManager API to GroupChatBuilder.
    """

    def __init__(
        self,
        id: str,
        participants: List[AgentProtocol | Executor],
        speaker_selection_method: str = "auto",
        max_rounds: int = 10,
        termination_condition: Optional[Callable] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(config)
        self._id = id
        self._participants = participants
        self._speaker_selection_method = speaker_selection_method
        self._max_rounds = max_rounds
        self._termination_condition = termination_condition

    def build(self) -> Workflow:
        """Build group chat workflow."""
        builder = GroupChatBuilder()

        # Add participants
        for participant in self._participants:
            builder.participants(participant)

        # Set speaker selection
        if self._speaker_selection_method == "auto":
            builder.set_manager(self._auto_select_manager)
        elif self._speaker_selection_method == "round_robin":
            builder.set_select_speakers_func(self._round_robin_selector)
        else:
            builder.set_select_speakers_func(self._custom_selector)

        # Set max rounds
        builder.with_max_rounds(self._max_rounds)

        # Set termination condition
        if self._termination_condition:
            builder.with_termination_condition(self._termination_condition)

        return builder.build()

    async def _auto_select_manager(
        self,
        request: ManagerSelectionRequest,
    ) -> ManagerSelectionResponse:
        """Auto select next speaker using manager."""
        # Implementation
        pass

    def _round_robin_selector(
        self,
        state: GroupChatStateSnapshot,
    ) -> str:
        """Round-robin speaker selection."""
        # Implementation
        pass
```

---

### S16-2: GroupChatManager 功能遷移 (8 點)

**驗收標準**:
- [ ] SpeakerSelectionMethod 功能保留
- [ ] GroupMessage 正確處理
- [ ] GroupChatState 正確維護
- [ ] 事件系統正確觸發

---

### S16-3: GroupChatOrchestratorExecutor (8 點)

**描述**: 實現或整合 Orchestrator Executor。

---

### S16-4: ManagerSelectionResponse 整合 (8 點)

**描述**: 整合結構化的發言者選擇響應。

---

### S16-5: API 端點更新 (5 點)

---

### S16-6: 測試完成 (5 點)

---

## 完成定義 (Definition of Done)

1. **功能完成**
   - [ ] GroupChatBuilder 適配器完成
   - [ ] 所有發言者選擇方法工作
   - [ ] API 向後兼容

2. **測試完成**
   - [ ] 測試覆蓋率 >= 80%

---

## 相關文檔

- [Phase 3 Overview](./README.md)
- [Sprint 15 Plan](./sprint-15-plan.md) - 前置 Sprint
- [Sprint 17 Plan](./sprint-17-plan.md) - 後續 Sprint
