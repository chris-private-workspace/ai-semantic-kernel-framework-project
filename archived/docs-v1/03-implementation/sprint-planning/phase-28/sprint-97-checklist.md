# Sprint 97 Checklist: HITLController + ApprovalHandler

## 開發任務

### Story 97-1: 實現 HITLController
- [ ] 創建 `hitl/` 目錄
- [ ] 創建 `__init__.py`
- [ ] 創建 `controller.py`
- [ ] 定義 `ApprovalStatus` enum
- [ ] 定義 `ApprovalRequest` dataclass
- [ ] 實現 `HITLController` 類
- [ ] 實現 `request_approval()` 方法
- [ ] 實現 `check_status()` 方法
- [ ] 實現 `process_approval()` 方法
- [ ] 實現 `cancel_approval()` 方法
- [ ] 實現超時處理

### Story 97-2: 實現 ApprovalHandler
- [ ] 創建 `approval_handler.py`
- [ ] 實現 `ApprovalHandler` 類
- [ ] 實現 `approve()` 方法
- [ ] 實現 `reject()` 方法
- [ ] 實現審批狀態持久化 (Redis)
- [ ] 實現審批歷史記錄

### Story 97-3: 實現審批 Webhook
- [ ] 實現 Teams Webhook 格式
  - [ ] MessageCard 結構
  - [ ] 審批按鈕 (批准/拒絕)
  - [ ] 風險資訊展示
- [ ] 實現 `send_approval_notification()` 方法
- [ ] 實現審批回調處理
- [ ] 實現審批超時處理

### Story 97-4: 實現 LLM QuestionGenerator
- [ ] 更新 `generator.py`
- [ ] 實現 `LLMQuestionGenerator` 類
- [ ] 設計問題生成 Prompt
- [ ] 實現 `generate()` 方法
- [ ] 實現 JSON 回應解析
- [ ] 實現選項生成
- [ ] 確保延遲 < 2000ms

### Story 97-5: 多輪對話狀態管理增強
- [ ] 更新 `context_manager.py`
- [ ] 實現對話歷史持久化 (Redis)
- [ ] 實現對話超時處理
- [ ] 實現對話恢復功能
- [ ] 實現最大輪數限制

## 品質檢查

### 代碼品質
- [ ] Black 格式化通過
- [ ] isort 排序通過
- [ ] flake8 檢查通過
- [ ] mypy 類型檢查通過

### 測試
- [ ] 單元測試覆蓋率 > 85%
- [ ] 所有測試通過
- [ ] HITL 流程測試通過

### 文檔
- [ ] HITLController docstrings 完整
- [ ] ApprovalHandler docstrings 完整
- [ ] LLMQuestionGenerator docstrings 完整

## 驗收標準

- [ ] HITL 流程端到端通過
- [ ] Teams Webhook 正常工作
- [ ] LLM 問題生成品質良好
- [ ] 多輪對話狀態管理正確
- [ ] 超時處理正確

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 30
