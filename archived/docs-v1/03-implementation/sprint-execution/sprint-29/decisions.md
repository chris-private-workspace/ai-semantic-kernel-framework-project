# Sprint 29 Decisions: API Routes 遷移

**Sprint 目標**: 將 API routes 從直接使用 domain 遷移到使用 Adapter

---

## 決策記錄

### D29-001: handoff/routes.py 遷移策略

**日期**: 2025-12-07
**狀態**: ✅ 已決定
**背景**:
現有 handoff API 是純 mock 實現 (in-memory dictionaries)，需要遷移到使用 HandoffBuilderAdapter。

**選項**:
1. 完全重寫，直接使用 HandoffBuilderAdapter
2. 保留部分 mock 邏輯，漸進式遷移
3. 創建 HandoffService 橋接層

**決定**: 選項 3 - 使用 HandoffService 橋接層
**理由**:
- HandoffService (Sprint 21) 已經整合了所有 Handoff 相關適配器
- 提供統一的 API 接口: trigger_handoff, get_handoff_status, cancel_handoff, get_handoff_history
- 整合 CapabilityMatcherAdapter 提供能力匹配功能
- 完全向後兼容現有 API schema
- HITL 功能保留在 API 層，未來可遷移到 WorkflowApprovalAdapter

---

### D29-002: API 依賴注入模式

**日期**: 2025-12-07
**狀態**: ✅ 已決定
**背景**:
需要決定如何在 FastAPI routes 中注入適配器。

**選項**:
1. 使用 FastAPI Depends + 工廠函數
2. 使用全局單例適配器
3. 使用請求範圍的依賴注入容器

**決定**: 選項 1 - 使用 FastAPI Depends + 工廠函數
**理由**:
- FastAPI 原生支持，無需額外依賴
- 工廠函數可配置和測試
- 支持 mock 替換進行單元測試
- 與現有 domain 服務注入模式一致
- 實現範例:
```python
# 單例服務實例
_handoff_service: Optional[HandoffService] = None

def get_handoff_service() -> HandoffService:
    global _handoff_service
    if _handoff_service is None:
        _handoff_service = create_handoff_service()
    return _handoff_service

# 在 route 中使用
@router.post("/trigger")
async def trigger_handoff(
    request: HandoffTriggerRequest,
    service: HandoffService = Depends(get_handoff_service),
):
    ...
```

---

## 技術約束

1. **必須使用適配器層**:
   - handoff: `HandoffBuilderAdapter`
   - workflows: `WorkflowDefinitionAdapter`
   - executions: `ExecutionAdapter`
   - checkpoints: `HumanApprovalExecutor` + `ApprovalWorkflowManager`

2. **與 Sprint 26-28 整合**:
   - 依賴 Sprint 26 的 WorkflowDefinitionAdapter
   - 依賴 Sprint 27 的 ExecutionAdapter
   - 依賴 Sprint 28 的 HumanApprovalExecutor

3. **向後兼容**:
   - 所有現有 API 行為不變
   - 回傳格式保持一致
   - 錯誤處理保持一致

---

## 參考資料

- [官方 Workflows API](../../../../.claude/skills/microsoft-agent-framework/references/workflows-api.md)
- [Sprint 28 Decisions](../sprint-28/decisions.md)
- [技術架構文檔](../../02-architecture/technical-architecture.md)
