# Phase 3: 完整重構 - 遷移至 Agent Framework 官方 API

**目標**: 將 Phase 2 所有自定義實現替換為 Microsoft Agent Framework 官方 API
**週期**: Sprint 13-18 (6 個 Sprint)
**總點數**: 222 點
**前置條件**: Phase 2 完成 (Sprint 7-12)

---

## Phase 概述

### 為什麼需要重構？

Phase 2 (Sprint 7-12) 的實現存在重大架構問題：

1. **完全自定義實現**: 所有核心功能都是獨立開發，未使用 Agent Framework 官方 API
2. **技術債務風險**: 自定義實現需要持續維護，無法受益於官方更新
3. **升級困難**: 當 Agent Framework GA 發布時，可能需要大量重構
4. **生態系統隔離**: 無法與其他使用 Agent Framework 的系統整合

### 重構目標

| 我們的實現 | 遷移目標 | Sprint |
|-----------|----------|--------|
| `ConcurrentExecutor` | `ConcurrentBuilder` | Sprint 14 |
| `HandoffController` | `HandoffBuilder` | Sprint 15 |
| `GroupChatManager` | `GroupChatBuilder` | Sprint 16 |
| `DynamicPlanner` | `MagenticBuilder` | Sprint 17 |
| `NestedWorkflowManager` | `WorkflowExecutor` | Sprint 18 |

---

## Sprint 計劃

### Sprint 13: 基礎設施準備 (34 點)

建立重構所需的基礎設施和適配層。

| Story | 描述 | 點數 |
|-------|------|------|
| S13-1 | Agent Framework API wrapper 層 | 8 |
| S13-2 | WorkflowBuilder 基礎整合 | 8 |
| S13-3 | CheckpointStorage 適配器 | 8 |
| S13-4 | 測試框架和 mock | 5 |
| S13-5 | 文檔和遷移指南 | 5 |

**詳細計劃**: [sprint-13-plan.md](./sprint-13-plan.md)

---

### Sprint 14: ConcurrentBuilder 重構 (34 點)

將 `ConcurrentExecutor` 遷移至 `ConcurrentBuilder`。

| Story | 描述 | 點數 |
|-------|------|------|
| S14-1 | ConcurrentBuilder 適配器 | 8 |
| S14-2 | ConcurrentExecutor 功能遷移 | 8 |
| S14-3 | fan-out/fan-in edge routing | 8 |
| S14-4 | API 端點更新 | 5 |
| S14-5 | 測試完成 | 5 |

**詳細計劃**: [sprint-14-plan.md](./sprint-14-plan.md)

---

### Sprint 15: HandoffBuilder 重構 (34 點)

將 `HandoffController` 遷移至 `HandoffBuilder`。

| Story | 描述 | 點數 |
|-------|------|------|
| S15-1 | HandoffBuilder 適配器 | 8 |
| S15-2 | HandoffController 功能遷移 | 8 |
| S15-3 | HandoffUserInputRequest HITL | 8 |
| S15-4 | API 端點更新 | 5 |
| S15-5 | 測試完成 | 5 |

**詳細計劃**: [sprint-15-plan.md](./sprint-15-plan.md)

---

### Sprint 16: GroupChatBuilder 重構 (42 點)

將 `GroupChatManager` 遷移至 `GroupChatBuilder`。

| Story | 描述 | 點數 |
|-------|------|------|
| S16-1 | GroupChatBuilder 適配器 | 8 |
| S16-2 | GroupChatManager 功能遷移 | 8 |
| S16-3 | GroupChatOrchestratorExecutor | 8 |
| S16-4 | ManagerSelectionResponse 整合 | 8 |
| S16-5 | API 端點更新 | 5 |
| S16-6 | 測試完成 | 5 |

**詳細計劃**: [sprint-16-plan.md](./sprint-16-plan.md)

---

### Sprint 17: MagenticBuilder 重構 (42 點)

將 `DynamicPlanner` 遷移至 `MagenticBuilder`。

| Story | 描述 | 點數 |
|-------|------|------|
| S17-1 | MagenticBuilder 適配器 | 8 |
| S17-2 | StandardMagenticManager 實現 | 8 |
| S17-3 | Task/Progress Ledger 整合 | 8 |
| S17-4 | Human Intervention 系統 | 8 |
| S17-5 | API 端點更新 | 5 |
| S17-6 | 測試完成 | 5 |

**詳細計劃**: [sprint-17-plan.md](./sprint-17-plan.md)

---

### Sprint 18: WorkflowExecutor 和整合 (36 點)

將 `NestedWorkflowManager` 遷移並完成整合測試。

| Story | 描述 | 點數 |
|-------|------|------|
| S18-1 | WorkflowExecutor 適配器 | 8 |
| S18-2 | NestedWorkflowManager 遷移 | 8 |
| S18-3 | 整合測試 - 全功能 | 8 |
| S18-4 | 性能測試和優化 | 5 |
| S18-5 | 文檔更新 | 5 |
| S18-6 | 清理舊代碼 | 2 |

**詳細計劃**: [sprint-18-plan.md](./sprint-18-plan.md)

---

## 總結

| Sprint | 名稱 | 點數 | 狀態 |
|--------|------|------|------|
| 13 | 基礎設施準備 | 34 | ✅ 完成 |
| 14 | ConcurrentBuilder 重構 | 34 | ✅ 完成 |
| 15 | HandoffBuilder 重構 | 34 | ✅ 完成 |
| 16 | GroupChatBuilder 重構 | 42 | ✅ 完成 |
| 17 | MagenticBuilder 重構 | 42 | ✅ 完成 |
| 18 | WorkflowExecutor 和整合 | 36 | ✅ 完成 |
| **總計** | | **222** | **222/222 (100%) ✅** |

> **Phase 3 已全部完成**: Sprint 13-18 共 222 點，所有重構工作完成。

---

## 成功標準

### 功能完整性
- [x] 所有 Phase 2 功能通過官方 API 實現
- [x] 現有 API 端點向後兼容
- [x] 功能行為與重構前一致

### 測試覆蓋
- [x] 單元測試覆蓋率 >= 80%
- [x] 整合測試覆蓋所有主要流程
- [x] E2E 測試通過

### 性能要求
- [x] 性能不低於原有實現
- [x] 響應時間 < 2 秒
- [x] 並發處理能力維持

### 文檔完整
- [x] API 文檔更新
- [x] 遷移指南完成
- [x] 範例代碼更新

---

## 風險管理

### 高風險
| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| Agent Framework API 變更 | 需要重新調整 | 密切關注官方更新，使用 wrapper 層隔離 |
| 向後兼容問題 | 現有用戶受影響 | 維護適配層，版本化 API |

### 中風險
| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 性能下降 | 用戶體驗受損 | 每個 Sprint 進行性能測試 |
| 測試不完整 | 生產問題 | 嚴格的 DoD 檢查 |

---

## 參考資料

### Agent Framework 文檔
- `reference/agent-framework/python/packages/core/agent_framework/_workflows/`
- `reference/agent-framework/python/examples/`

### 我們的實現（待遷移）
- `backend/src/domain/workflows/executors/concurrent.py`
- `backend/src/domain/orchestration/handoff/controller.py`
- `backend/src/domain/orchestration/groupchat/manager.py`
- `backend/src/domain/orchestration/planning/dynamic_planner.py`
- `backend/src/domain/orchestration/nested/workflow_manager.py`

### 審查文檔
- [Phase 2 架構審查報告](../../../../claudedocs/PHASE2-ARCHITECTURE-REVIEW.md)
- [Phase 3 重構計劃](../../../../claudedocs/PHASE3-REFACTORING-PLAN.md)
