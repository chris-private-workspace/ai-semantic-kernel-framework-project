# Sprint 28 Checklist: 人工審批遷移

**Sprint 目標**: 將 CheckpointService 遷移到 RequestResponseExecutor
**週期**: 2 週
**總點數**: 34 點
**Phase 5 功能**: P5-F3 人工審批遷移
**狀態**: 待執行

---

## 快速驗證命令

```bash
# 驗證官方 API 可用
python -c "from agent_framework.workflows import RequestResponseExecutor; print('OK')"

# 驗證適配器模組
python -c "from src.integrations.agent_framework.core.approval import HumanApprovalExecutor; print('OK')"

# 運行單元測試
cd backend && pytest tests/unit/test_human_approval_executor.py -v
cd backend && pytest tests/unit/test_approval_models.py -v

# 運行整合測試
cd backend && pytest tests/integration/test_approval_workflow_integration.py -v

# 檢查測試覆蓋率
cd backend && pytest tests/unit/test_*approval*.py --cov=src/integrations/agent_framework/core --cov-report=term-missing
```

---

## S28-1: HumanApprovalExecutor (10 點) - 待執行

### 模組結構 (src/integrations/agent_framework/core/)
- [ ] 創建 `approval.py`
  - [ ] `HumanApprovalExecutor` 類
    - [ ] 繼承 `RequestResponseExecutor[ApprovalRequest, ApprovalResponse]`
    - [ ] `__init__()` 初始化
    - [ ] `on_request_created()` 請求創建回調
    - [ ] `on_response_received()` 回應接收回調
    - [ ] `_handle_rejection()` 拒絕處理
  - [ ] `EscalationPolicy` 類
    - [ ] `schedule_escalation()` 安排升級
    - [ ] `cancel_escalation()` 取消升級

### 功能驗證
- [ ] 可創建 HumanApprovalExecutor 實例
- [ ] 請求創建時觸發通知
- [ ] 回應接收時取消升級
- [ ] 工作流在此暫停

### 單元測試
- [ ] `test_create_executor.py`
- [ ] `test_request_callback.py`
- [ ] `test_response_callback.py`
- [ ] `test_escalation_policy.py`

---

## S28-2: ApprovalRequest/Response 模型 (8 點) - 待執行

### 模型定義
- [ ] `ApprovalRequest` 模型
  - [ ] `request_id: str`
  - [ ] `execution_id: UUID`
  - [ ] `node_id: str`
  - [ ] `action: str`
  - [ ] `risk_level: str`
  - [ ] `details: str`
  - [ ] `payload: Dict`
  - [ ] `timeout_seconds: int`
  - [ ] `required_approvers: int`
- [ ] `ApprovalResponse` 模型
  - [ ] `request_id: str`
  - [ ] `approved: bool`
  - [ ] `reason: str`
  - [ ] `approver: str`
  - [ ] `approved_at: datetime`
  - [ ] `signature: Optional[str]`
  - [ ] `metadata: Dict`

### 驗證規則
- [ ] risk_level 只能是 low/medium/high/critical
- [ ] timeout_seconds 必須 > 0
- [ ] request_id 格式驗證

### 單元測試
- [ ] `test_approval_request_validation.py`
- [ ] `test_approval_response_validation.py`

---

## S28-3: CheckpointService 重構 (8 點) - 待執行

### 修改檔案
- [ ] 更新 `domain/checkpoints/service.py`
  - [ ] 分離存儲功能
  - [ ] 添加 deprecation 警告
  - [ ] 保持 API 向後兼容
  - [ ] 新增 `save_state()` 方法
  - [ ] 新增 `load_state()` 方法

### 功能驗證
- [ ] 存儲功能正常
- [ ] 審批功能已標記棄用
- [ ] 向後兼容測試通過

### 單元測試
- [ ] 更新 `test_checkpoint_service.py`
- [ ] 添加 deprecation 警告測試

---

## S28-4: 審批工作流整合 (5 點) - 待執行

### 整合測試
- [ ] 在工作流中使用 HumanApprovalExecutor
- [ ] 工作流暫停測試
- [ ] `workflow.respond()` 恢復測試
- [ ] 拒絕處理測試
- [ ] 超時處理測試

### 功能驗證
- [ ] 工作流正確暫停
- [ ] 審批回應正確處理
- [ ] 拒絕時工作流正確結束

---

## S28-5: 單元測試 (3 點) - 待執行

### 測試覆蓋
- [ ] approval.py 覆蓋率 >= 80%
- [ ] 所有邊界案例覆蓋
- [ ] 錯誤處理覆蓋

### 驗證通過
- [ ] 所有單元測試通過
- [ ] 整合測試通過
- [ ] 語法檢查通過

---

## Sprint 28 完成標準

### 必須完成 (Must Have)
- [ ] HumanApprovalExecutor 實現並通過測試
- [ ] ApprovalRequest/Response 模型完成
- [ ] CheckpointService 重構完成
- [ ] 測試覆蓋率 >= 80%

### 應該完成 (Should Have)
- [ ] 審批工作流整合完成
- [ ] 向後兼容測試通過
- [ ] 代碼審查完成

### 可以延後 (Could Have)
- [ ] 多人審批支持
- [ ] 簽名驗證

---

## 依賴確認

### 前置條件
- [ ] Sprint 26-27 完成
  - [ ] WorkflowDefinitionAdapter 可用
  - [ ] ExecutionAdapter 可用
- [ ] 官方 API 可用
  - [ ] `RequestResponseExecutor` 可用

### 外部依賴
- [ ] NotificationService 可用 (可選)
- [ ] AuditLogger 可用 (可選)

---

## 相關連結

- [Sprint 28 Plan](./sprint-28-plan.md) - 詳細計劃
- [Sprint 27 Checklist](./sprint-27-checklist.md) - 前置 Sprint
- [Sprint 29 Plan](./sprint-29-plan.md) - 後續 Sprint
