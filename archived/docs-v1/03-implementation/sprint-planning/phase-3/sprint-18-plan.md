# Sprint 18: WorkflowExecutor 和整合

**Sprint 目標**: 將 NestedWorkflowManager 遷移並完成 Phase 3 整合
**週期**: Week 37-38 (2 週)
**Story Points**: 36 點
**Phase 3 功能**: P3-F5 (Nested Workflows 重構) + 整合

---

## Sprint 概覽

### 目標
1. 實現 WorkflowExecutor 適配器
2. 遷移 NestedWorkflowManager 功能
3. 完成整合測試 - 全功能
4. 性能測試和優化
5. 文檔更新
6. 清理舊代碼

### 成功標準
- [ ] Nested Workflow 功能通過 WorkflowExecutor 實現
- [ ] 所有 Phase 3 功能整合測試通過
- [ ] 性能不低於原有實現
- [ ] 舊代碼清理完成
- [ ] 測試覆蓋率 >= 80%

---

## User Stories

### S18-1: WorkflowExecutor 適配器 (8 點)

**技術要點**:

```python
# backend/src/integrations/agent_framework/builders/workflow_executor.py

from typing import Any, Dict, Optional
from agent_framework import (
    WorkflowExecutor,
    SubWorkflowRequestMessage,
    SubWorkflowResponseMessage,
    Workflow,
)

from ..base import BuilderAdapter


class WorkflowExecutorAdapter(BuilderAdapter):
    """
    Adapter for Agent Framework WorkflowExecutor.

    Enables nested workflow composition by wrapping workflows
    as executors within parent workflows.
    """

    def __init__(
        self,
        id: str,
        workflow: Workflow,
        allow_direct_output: bool = False,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(config)
        self._id = id
        self._workflow = workflow
        self._allow_direct_output = allow_direct_output

    def build(self) -> WorkflowExecutor:
        """Build WorkflowExecutor."""
        return WorkflowExecutor(
            workflow=self._workflow,
            id=self._id,
            allow_direct_output=self._allow_direct_output,
        )

    def create_response(
        self,
        request: SubWorkflowRequestMessage,
        data: Any,
    ) -> SubWorkflowResponseMessage:
        """Create response to sub-workflow request."""
        return request.create_response(data)
```

---

### S18-2: NestedWorkflowManager 遷移 (8 點)

**描述**: 遷移 NestedWorkflowManager 的所有功能。

**驗收標準**:
- [ ] NestedWorkflowType 功能保留
- [ ] SubWorkflowReference 功能保留
- [ ] 嵌套執行正確
- [ ] 並發隔離正確

---

### S18-3: 整合測試 - 全功能 (8 點)

**描述**: 測試所有 Phase 3 功能的整合。

**驗收標準**:
- [ ] ConcurrentBuilder + GroupChatBuilder 整合測試
- [ ] HandoffBuilder + MagenticBuilder 整合測試
- [ ] 嵌套工作流 + 檢查點整合測試
- [ ] E2E 測試通過

---

### S18-4: 性能測試和優化 (5 點)

**描述**: 確保重構後性能不低於原有實現。

**驗收標準**:
- [ ] 響應時間 < 2 秒
- [ ] 吞吐量不降低
- [ ] 內存使用合理

---

### S18-5: 文檔更新 (5 點)

**描述**: 更新所有文檔。

**驗收標準**:
- [ ] API 文檔更新
- [ ] 遷移指南完成
- [ ] 範例代碼更新

---

### S18-6: 清理舊代碼 (2 點)

**描述**: 清理不再需要的舊代碼。

**驗收標準**:
- [ ] 舊實現標記為 deprecated
- [ ] 清理不需要的文件
- [ ] 技術債務清理

---

## 完成定義 (Definition of Done)

1. **功能完成**
   - [ ] 所有適配器完成
   - [ ] 整合測試通過
   - [ ] API 向後兼容

2. **測試完成**
   - [ ] 測試覆蓋率 >= 80%
   - [ ] E2E 測試通過
   - [ ] 性能測試通過

3. **文檔完成**
   - [ ] 所有文檔更新

---

## Phase 3 完成總結

### 完成統計

| Sprint | 名稱 | 點數 | 狀態 |
|--------|------|------|------|
| 13 | 基礎設施準備 | 34 | 待開始 |
| 14 | ConcurrentBuilder | 34 | 待開始 |
| 15 | HandoffBuilder | 34 | 待開始 |
| 16 | GroupChatBuilder | 42 | 待開始 |
| 17 | MagenticBuilder | 42 | 待開始 |
| 18 | WorkflowExecutor | 36 | 待開始 |
| **總計** | | **222** | |

### 最終驗證清單

- [ ] 所有 Phase 2 功能通過官方 API 實現
- [ ] 現有 API 端點向後兼容
- [ ] 測試覆蓋率 >= 80%
- [ ] 性能不低於原有實現
- [ ] 文檔完整

---

## 相關文檔

- [Phase 3 Overview](./README.md)
- [Sprint 17 Plan](./sprint-17-plan.md) - 前置 Sprint
- [Phase 2 架構審查](../../../../claudedocs/PHASE2-ARCHITECTURE-REVIEW.md)
