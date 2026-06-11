# Sprint 111 Checklist: 統一審批系統 + Chat History 後端同步

## Sprint 目標

| 項目 | 值 |
|------|-----|
| **總點數** | 12 點 |
| **狀態** | ✅ 完成 |

---

## 開發任務

### S111-1: UnifiedApprovalManager (4 SP)
- [x] 新增 `backend/src/integrations/orchestration/hitl/unified_manager.py`
- [x] 以 Orchestration HITLController 為主體
- [x] 實作統一審批建立介面
- [x] 實作統一審批查詢介面
- [x] 實作統一審批更新介面
- [x] 實作統一審批取消介面
- [x] 審批狀態持久化到 PostgreSQL
- [x] 更新 `backend/src/integrations/orchestration/hitl/__init__.py` 匯出

### S111-2: AG-UI Approval Delegate (2 SP)
- [x] 新增 `backend/src/integrations/ag_ui/features/approval_delegate.py`
- [x] 保持 AG-UI ApprovalStorage 原有介面
- [x] 內部 delegate 到 UnifiedApprovalManager
- [x] 向後兼容現有 AG-UI 審批流程

### S111-3: Claude SDK Approval Delegate (2 SP)
- [x] 新增 `backend/src/integrations/claude_sdk/hooks/approval_delegate.py`
- [x] 保持 Claude SDK ApprovalHook 原有介面
- [x] 內部 delegate 到 UnifiedApprovalManager
- [x] 向後兼容現有 Claude SDK 審批流程

### S111-4: Chat History API (2 SP)
- [x] 新增 `backend/src/domain/chat_history/__init__.py`
- [x] 新增 `backend/src/domain/chat_history/models.py`
- [x] 新增 `backend/src/api/v1/chat_history/__init__.py`
- [x] 新增 `backend/src/api/v1/chat_history/routes.py`
- [x] Chat History CRUD API 端點實作
- [x] Chat history 持久化到 PostgreSQL

### S111-5: 路由註冊 + 匯出 (2 SP)
- [x] 修改 `backend/src/api/v1/__init__.py` — 註冊 chat_history 路由
- [x] 修改 `backend/src/integrations/orchestration/hitl/__init__.py` — 匯出更新
- [x] 確保所有新增模組正確匯出

## 驗證標準

- [x] 4 套審批系統統一為 1 套 HITLController
- [x] AG-UI / Claude SDK 兩個入口都 delegate 到 UnifiedApprovalManager
- [x] 審批狀態持久化到 PostgreSQL
- [x] Chat History API 端點可用（CRUD）
- [x] 所有路由正確註冊
- [x] 所有新增檔案模組匯出正確

## 相關連結

- [Phase 36 計劃](./README.md)
- [Sprint 111 Progress](../../sprint-execution/sprint-111/progress.md)
- [Sprint 111 Plan](./sprint-111-plan.md)

---

**Sprint 狀態**: ✅ 完成
**Story Points**: 12
**完成日期**: 2026-03-19
