# Sprint 111: 統一審批系統 + Chat History 後端同步

## Sprint 目標

1. UnifiedApprovalManager（統一審批管理器）
2. AG-UI Approval Delegate
3. Claude SDK Approval Delegate
4. Chat History 後端同步 API
5. 路由註冊 + 匯出更新

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 36 — E2E Assembly A1 |
| **Sprint** | 111 |
| **Story Points** | 12 點 |
| **狀態** | ✅ 完成 |

## Sprint 概述

Sprint 111 專注於將 4-5 套分散的審批系統統一為 1 套，以 Orchestration HITLController 為主體。AG-UI ApprovalStorage 和 Claude SDK ApprovalHook 改為代理（delegate）到 HITLController，不再獨立存儲。同時實現 Chat History 後端同步，將 localStorage 中的對話歷史同步到 PostgreSQL，支援跨裝置存取。

## User Stories

### S111-1: UnifiedApprovalManager (4 SP)

**作為** 平台架構師
**我希望** 將 4-5 套獨立的審批系統統一為 1 套
**以便** 消除審批狀態分散導致的不一致性，所有審批入口共用同一資料源

**技術規格**:
- 新增 `backend/src/integrations/orchestration/hitl/unified_manager.py`
- 以 Orchestration HITLController 為主體
- 統一審批建立、查詢、更新、取消介面
- 審批狀態持久化到 PostgreSQL（透過 Sprint 110 的 ApprovalStore）
- 更新 `backend/src/integrations/orchestration/hitl/__init__.py` 匯出

### S111-2: AG-UI Approval Delegate (2 SP)

**作為** AG-UI 整合開發者
**我希望** AG-UI ApprovalStorage 改為代理到 HITLController
**以便** AG-UI 審批入口與統一審批系統共享狀態，不再獨立存儲

**技術規格**:
- 新增 `backend/src/integrations/ag_ui/features/approval_delegate.py`
- 保持 AG-UI ApprovalStorage 原有介面不變
- 內部 delegate 所有操作到 UnifiedApprovalManager
- 向後兼容現有 AG-UI 審批流程

### S111-3: Claude SDK Approval Delegate (2 SP)

**作為** Claude SDK 整合開發者
**我希望** Claude SDK ApprovalHook 改為代理到 HITLController
**以便** Claude SDK 審批入口與統一審批系統共享狀態

**技術規格**:
- 新增 `backend/src/integrations/claude_sdk/hooks/approval_delegate.py`
- 保持 Claude SDK ApprovalHook 原有介面不變
- 內部 delegate 所有操作到 UnifiedApprovalManager
- 向後兼容現有 Claude SDK 審批流程

### S111-4: Chat History API (2 SP)

**作為** 平台用戶
**我希望** Chat history 從 localStorage 同步到後端 PostgreSQL
**以便** 支援跨裝置存取對話歷史，服務端可查詢與分析

**技術規格**:
- 新增 `backend/src/domain/chat_history/__init__.py`
- 新增 `backend/src/domain/chat_history/models.py` — Chat History 資料模型
- 新增 `backend/src/api/v1/chat_history/__init__.py`
- 新增 `backend/src/api/v1/chat_history/routes.py` — CRUD API 端點
- Chat history 持久化到 PostgreSQL

### S111-5: 路由註冊 + 匯出 (2 SP)

**作為** 後端開發者
**我希望** 新增的 API 路由正確註冊並匯出
**以便** 所有新增端點可被前端正確呼叫

**技術規格**:
- 修改 `backend/src/api/v1/__init__.py` — 註冊 chat_history 路由
- 修改 `backend/src/integrations/orchestration/hitl/__init__.py` — 匯出 UnifiedApprovalManager
- 確保所有新增模組正確匯出

## 相關連結

- [Phase 36 計劃](./README.md)
- [Sprint 111 Progress](../../sprint-execution/sprint-111/progress.md)
- [Sprint 110 Plan](./sprint-110-plan.md)
- [Sprint 112 Plan](./sprint-112-plan.md)

---

**Sprint 狀態**: ✅ 完成
**Story Points**: 12
**完成日期**: 2026-03-19
