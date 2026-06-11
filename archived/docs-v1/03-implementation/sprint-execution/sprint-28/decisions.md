# Sprint 28 Decisions: 人工審批遷移

**Sprint 目標**: 將 CheckpointService 遷移到官方 RequestResponseExecutor

---

## 決策記錄

### D28-001: RequestResponseExecutor 實現策略

**日期**: 2025-12-07
**狀態**: ✅ 已決定
**背景**:
需要將現有 CheckpointService 的審批功能遷移到官方 RequestResponseExecutor。

**選項**:
1. 直接繼承 RequestResponseExecutor
2. 使用適配器包裝現有審批邏輯
3. 混合方式 - 核心用官方，擴展用適配器

**決定**: 選項 1 - 直接繼承 RequestResponseExecutor
**理由**:
- 官方 API 已提供完整的 Human-in-the-loop 模式
- HumanApprovalExecutor 使用 `@Executor.register` 裝飾器
- 繼承 `RequestResponseExecutor[ApprovalRequest, ApprovalResponse]` 獲得類型安全
- 擴展回調方法 (on_request_created, on_response_received) 保留自定義邏輯
- 與官方 API 完全兼容，可直接在 Workflow 中使用
- 保留 EscalationPolicy 和 NotificationConfig 作為增強功能

---

### D28-002: CheckpointService 職責分離

**日期**: 2025-12-07
**狀態**: ✅ 已決定
**背景**:
現有 CheckpointService 混合了存儲和審批兩個概念，需要分離。

**選項**:
1. 完全分離為兩個服務
2. CheckpointService 只保留存儲，審批移到 HumanApprovalExecutor
3. 保持原有服務，新增 HumanApprovalExecutor 作為替代

**決定**: 選項 3 - 保持原有服務，新增 HumanApprovalExecutor 作為替代
**理由**:
- 保留 CheckpointService 所有現有功能確保向後兼容
- approve_checkpoint() 和 reject_checkpoint() 添加 deprecation warnings
- 新增橋接方法 (create_checkpoint_with_approval, handle_approval_response)
- 允許漸進式遷移：現有代碼繼續工作，新代碼使用官方 API
- CheckpointService 可選擇性整合 HumanApprovalExecutor (_approval_executor)
- 這種方式最小化對現有系統的影響

---

## 技術約束

1. **必須使用官方 API**:
   - `from agent_framework.workflows import RequestResponseExecutor`
   - `from agent_framework.workflows import Executor`

2. **與 Sprint 27 整合**:
   - 依賴 `ExecutionAdapter` (execution.py)
   - 依賴 `WorkflowStatusEventAdapter` (events.py)

3. **向後兼容**:
   - 現有 CheckpointService API 需保持可用 (with deprecation warnings)
   - 現有審批功能不能退化

---

## 參考資料

- [官方 Workflows API - Human-in-the-Loop](../../../../.claude/skills/microsoft-agent-framework/references/workflows-api.md)
- [Sprint 27 Decisions](../sprint-27/decisions.md)
- [技術架構文檔](../../02-architecture/technical-architecture.md)
