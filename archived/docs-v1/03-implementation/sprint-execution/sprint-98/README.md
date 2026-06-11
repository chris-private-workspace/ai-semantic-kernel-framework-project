# Sprint 98: HybridOrchestratorV2 整合

## Sprint 概述

| 屬性 | 值 |
|------|-----|
| **Sprint 編號** | 98 |
| **Phase** | 28 - Three-Tier Routing Architecture |
| **名稱** | HybridOrchestratorV2 整合 |
| **目標** | 將 Phase 28 的所有新組件整合到現有的 HybridOrchestratorV2 架構中 |
| **總點數** | 25 Story Points |
| **開始日期** | 2026-01-16 |
| **完成日期** | 2026-01-16 |
| **狀態** | ✅ 完成 |

---

## 前置條件

- ✅ Sprint 93: BusinessIntentRouter + CompletenessChecker
- ✅ Sprint 94: GuidedDialogEngine + Incremental Update
- ✅ Sprint 95: InputGateway + SourceHandlers
- ✅ Sprint 96: RiskAssessor + Policies
- ✅ Sprint 97: HITLController + ApprovalHandler

---

## User Stories

| Story | 名稱 | 點數 | 優先級 | 狀態 |
|-------|------|------|--------|------|
| S98-1 | 重命名 IntentRouter → FrameworkSelector | 2 | P0 | ✅ 完成 |
| S98-2 | 整合 BusinessIntentRouter 到 Orchestrator | 4 | P0 | ✅ 完成 |
| S98-3 | 整合 GuidedDialogEngine 到 API 層 | 4 | P0 | ✅ 完成 |
| S98-4 | 整合 HITL 到現有審批流程 | 4 | P0 | ✅ 完成 |

---

## Story 詳情

### S98-1: 重命名 IntentRouter → FrameworkSelector (2 pts)

**描述**: 重命名現有 IntentRouter 以避免與 BusinessIntentRouter 混淆

**交付物**:
- 更新 `backend/src/integrations/hybrid/intent/router.py`
  - `IntentRouter` → `FrameworkSelector`
  - `IntentAnalysis` → `FrameworkAnalysis`
  - `analyze_intent()` → `select_framework()`
- 更新所有引用文件
- 更新測試文件

**驗收標準**:
- [ ] 重命名完成
- [ ] 所有現有測試通過
- [ ] 無破壞性變更

---

### S98-2: 整合 BusinessIntentRouter (4 pts)

**描述**: 在 Orchestrator 入口整合業務意圖路由

**交付物**:
- 更新 `backend/src/integrations/hybrid/orchestrator_v2.py`
- 添加 Phase 28 新組件參數
- 更新 execute() 流程

**新執行流程**:
1. InputGateway 處理輸入
2. BusinessIntentRouter 分類意圖
3. 檢查完整度，需要時啟動 GuidedDialog
4. RiskAssessor 評估風險
5. 需要時啟動 HITL 審批
6. FrameworkSelector 選擇執行框架
7. 執行工作流

**驗收標準**:
- [ ] 整合完成
- [ ] 流程正確
- [ ] 向後相容

---

### S98-3: 整合 GuidedDialogEngine 到 API 層 (4 pts)

**描述**: 在 API 層支援引導式對話

**交付物**:
- `backend/src/api/v1/orchestration/dialog_routes.py`

**API 端點**:
- `POST /api/v1/orchestration/dialog/start` - 啟動對話
- `POST /api/v1/orchestration/dialog/{dialog_id}/respond` - 提交回答
- `GET /api/v1/orchestration/dialog/{dialog_id}/status` - 獲取狀態
- `DELETE /api/v1/orchestration/dialog/{dialog_id}` - 取消對話

**驗收標準**:
- [ ] API 路由實現完成
- [ ] 多輪對話正常工作
- [ ] 狀態管理正確

---

### S98-4: 整合 HITL 到現有審批流程 (4 pts)

**描述**: 整合新的 HITL 到現有審批機制

**交付物**:
- `backend/src/api/v1/orchestration/approval_routes.py`
- 更新 `orchestrator_v2.py`

**API 端點**:
- `GET /api/v1/orchestration/approvals` - 獲取待審批列表
- `GET /api/v1/orchestration/approvals/{approval_id}` - 獲取審批詳情
- `POST /api/v1/orchestration/approvals/{approval_id}/decision` - 提交審批決定
- `POST /api/v1/orchestration/approvals/{approval_id}/callback` - Teams Webhook 回調

**驗收標準**:
- [ ] 審批 API 實現完成
- [ ] 與現有 ApprovalHook 整合
- [ ] Teams 回調正常工作

---

## 技術設計

### 更新後的執行流程

```
ExecutionRequest
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│ 1. InputGateway.process()                               │
│    來源識別 → 分流處理                                  │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│ 2. 檢查 completeness.is_sufficient                      │
└───────────────────────────┬─────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
           No                              Yes
            │                               │
            ▼                               │
┌─────────────────────────────┐            │
│ GuidedDialogEngine          │            │
│   生成問題 → 收集回答       │            │
│   增量更新 → 重新檢查       │            │
└─────────────┬───────────────┘            │
              │                             │
              └─────────────────────────────┤
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────┐
│ 3. RiskAssessor.assess()                                │
│    評估風險等級                                         │
└───────────────────────────┬─────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │ requires_approval?            │
            └───────────────┬───────────────┘
                            │
           Yes              │              No
            │               │               │
            ▼               │               │
┌─────────────────────────────┐            │
│ HITLController              │            │
│   發送審批請求              │            │
│   等待審批結果              │            │
└─────────────┬───────────────┘            │
              │                             │
              └─────────────────────────────┤
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────┐
│ 4. FrameworkSelector.select_framework()                 │
│    選擇 WORKFLOW_MODE / CHAT_MODE                       │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│ 5. 執行                                                 │
│    WORKFLOW_MODE → MAF Worker                           │
│    CHAT_MODE → Claude SDK                               │
└─────────────────────────────────────────────────────────┘
```

---

## 實作文件

| 文件 | 描述 |
|------|------|
| `story-98-1-framework-selector.md` | Story 98-1 實作紀錄 |
| `story-98-2-orchestrator-integration.md` | Story 98-2 實作紀錄 |
| `story-98-3-dialog-routes.md` | Story 98-3 實作紀錄 |
| `story-98-4-approval-routes.md` | Story 98-4 實作紀錄 |

---

## 相關文檔

- [Sprint 98 Plan](../../sprint-planning/phase-28/sprint-98-plan.md)
- [Sprint 98 Checklist](../../sprint-planning/phase-28/sprint-98-checklist.md)
- [Phase 28 README](../../sprint-planning/phase-28/README.md)

---

**創建日期**: 2026-01-16
**更新日期**: 2026-01-16
