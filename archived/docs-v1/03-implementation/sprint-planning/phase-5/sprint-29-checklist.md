# Sprint 29 Checklist: API Routes 遷移

**Sprint 目標**: 將 API routes 從直接使用 domain 遷移到使用 Adapter
**週期**: 2 週
**總點數**: 38 點
**Phase 5 功能**: P5-F4 API Routes 遷移
**狀態**: 待執行

---

## 快速驗證命令

```bash
# 驗證無 domain 直接 import (Phase 2-5 功能)
grep -r "from src.domain.orchestration" backend/src/api/v1/ | grep -v "#"

# 運行 API 整合測試
cd backend && pytest tests/integration/test_handoff_api.py -v
cd backend && pytest tests/integration/test_workflows_api.py -v
cd backend && pytest tests/integration/test_executions_api.py -v
cd backend && pytest tests/integration/test_checkpoints_api.py -v

# 運行所有 API 測試
cd backend && pytest tests/integration/test_*_api.py -v
```

---

## S29-1: handoff/routes.py 遷移 (8 點) - 待執行

### 移除 mock 實現
- [ ] 移除 `_handoffs` in-memory 字典
- [ ] 移除 `_agent_capabilities` in-memory 字典
- [ ] 移除 `_agent_availability` in-memory 字典
- [ ] 移除所有 mock 函數

### 使用 HandoffBuilderAdapter
- [ ] Import `HandoffBuilderAdapter`
- [ ] 創建 `get_handoff_adapter()` 依賴
- [ ] 更新 `initiate_handoff` 端點
- [ ] 更新 `complete_handoff` 端點
- [ ] 更新 `get_handoff` 端點
- [ ] 更新 `get_handoff_history` 端點
- [ ] 更新 capability 相關端點

### 驗證
- [ ] 所有端點功能正常
- [ ] API 行為不變
- [ ] 無 mock 殘留

### 整合測試
- [ ] `test_initiate_handoff.py`
- [ ] `test_complete_handoff.py`
- [ ] `test_get_handoff_status.py`
- [ ] `test_capability_matching.py`

---

## S29-2: workflows/routes.py 遷移 (8 點) - 待執行

### 更新 imports
- [ ] Import `WorkflowDefinitionAdapter`
- [ ] 創建 `get_workflow_adapter()` 依賴
- [ ] 移除直接 domain service import

### 更新端點
- [ ] `POST /workflows` - 創建工作流
- [ ] `GET /workflows/{id}` - 獲取工作流
- [ ] `PUT /workflows/{id}` - 更新工作流
- [ ] `DELETE /workflows/{id}` - 刪除工作流
- [ ] `POST /workflows/{id}/run` - 執行工作流
- [ ] `GET /workflows` - 列表工作流

### 驗證
- [ ] 所有端點功能正常
- [ ] API 行為不變
- [ ] 使用適配器

### 整合測試
- [ ] `test_create_workflow.py`
- [ ] `test_run_workflow.py`
- [ ] `test_workflow_crud.py`

---

## S29-3: executions/routes.py 遷移 (8 點) - 待執行

### 更新 imports
- [ ] Import `ExecutionAdapter`
- [ ] 創建 `get_execution_adapter()` 依賴
- [ ] 移除直接 domain service import

### 更新端點
- [ ] `GET /executions/{id}` - 獲取執行狀態
- [ ] `GET /executions/{id}/events` - 獲取事件流
- [ ] `POST /executions/{id}/cancel` - 取消執行
- [ ] `GET /executions` - 列表執行

### 驗證
- [ ] 所有端點功能正常
- [ ] API 行為不變
- [ ] 事件流正確

### 整合測試
- [ ] `test_get_execution.py`
- [ ] `test_execution_events.py`
- [ ] `test_cancel_execution.py`

---

## S29-4: checkpoints/routes.py 遷移 (8 點) - 待執行

### 更新 imports
- [ ] Import `ApprovalAdapter`
- [ ] 創建 `get_approval_adapter()` 依賴
- [ ] 整合 `HumanApprovalExecutor`

### 更新端點
- [ ] `GET /checkpoints/pending` - 待審批列表
- [ ] `POST /checkpoints/{id}/approve` - 審批
- [ ] `POST /checkpoints/{id}/reject` - 拒絕
- [ ] `GET /checkpoints/{id}` - 獲取詳情

### 驗證
- [ ] 所有端點功能正常
- [ ] 與工作流正確整合
- [ ] 審批後工作流恢復

### 整合測試
- [ ] `test_pending_approvals.py`
- [ ] `test_approve_request.py`
- [ ] `test_reject_request.py`
- [ ] `test_approval_workflow_integration.py`

---

## S29-5: API 整合測試 (6 點) - 待執行

### 測試覆蓋
- [ ] handoff API 所有端點
- [ ] workflows API 所有端點
- [ ] executions API 所有端點
- [ ] checkpoints API 所有端點

### 代碼品質檢查
- [ ] 無 domain 直接 import
- [ ] 所有 deprecated imports 清理
- [ ] API 文檔更新

### 文檔更新
- [ ] 更新 progress.md
- [ ] 記錄 decisions.md
- [ ] 更新 checklist (本文件)

---

## Sprint 29 完成標準

### 必須完成 (Must Have)
- [ ] handoff/routes.py 完全重寫
- [ ] workflows/routes.py 遷移完成
- [ ] executions/routes.py 遷移完成
- [ ] checkpoints/routes.py 遷移完成
- [ ] 所有 API 測試通過

### 應該完成 (Should Have)
- [ ] 無 domain 直接 import
- [ ] deprecated imports 清理
- [ ] 代碼審查完成

### 可以延後 (Could Have)
- [ ] API 效能優化
- [ ] 進階錯誤處理

---

## 依賴確認

### 前置條件
- [ ] Sprint 26-28 完成
  - [ ] WorkflowDefinitionAdapter 可用
  - [ ] ExecutionAdapter 可用
  - [ ] HumanApprovalExecutor 可用
- [ ] HandoffBuilderAdapter 可用 (Phase 4)

### 外部依賴
- [ ] 所有適配器正常運作
- [ ] 現有 API 測試套件可用

---

## 相關連結

- [Sprint 29 Plan](./sprint-29-plan.md) - 詳細計劃
- [Sprint 28 Checklist](./sprint-28-checklist.md) - 前置 Sprint
- [Sprint 30 Plan](./sprint-30-plan.md) - 後續 Sprint
