# Sprint 131 Checklist: 測試覆蓋率 → 80%

## 開發任務

### Story 131-1: HITL 模組測試補強
- [ ] `tests/unit/orchestration/test_hitl_controller_deep.py`
  - [ ] 審批請求建立
  - [ ] 審批通過完整流程
  - [ ] 審批拒絕完整流程
  - [ ] 審批超時處理
  - [ ] 升級策略觸發
  - [ ] 並發審批請求
  - [ ] 審批歷史查詢
- [ ] `tests/unit/orchestration/test_approval_handler.py`
  - [ ] 審批處理邏輯
  - [ ] 超時自動拒絕
  - [ ] 多級審批鏈
  - [ ] 審批委託
- [ ] `tests/unit/orchestration/test_hitl_notification.py`
  - [ ] Teams 通知分發
  - [ ] Email 通知分發
  - [ ] 通知模板渲染
  - [ ] 通知失敗重試

### Story 131-2: Metrics + MCP Core 測試
- [ ] `tests/unit/orchestration/test_orchestration_metrics.py`
  - [ ] Counter 指標記錄
  - [ ] Histogram 指標記錄
  - [ ] Gauge 指標記錄
  - [ ] 標籤（labels）正確性
  - [ ] 指標聚合
- [ ] `tests/unit/integrations/mcp/core/test_mcp_client.py`
  - [ ] 客戶端建立連線
  - [ ] 工具調用
  - [ ] 連線中斷處理
  - [ ] 超時處理
- [ ] `tests/unit/integrations/mcp/core/test_mcp_protocol.py`
  - [ ] 協議消息序列化/反序列化
  - [ ] 請求/回應匹配
  - [ ] 錯誤消息處理
- [ ] `tests/unit/integrations/mcp/core/test_mcp_transport.py`
  - [ ] stdio 傳輸
  - [ ] SSE 傳輸
  - [ ] 傳輸層錯誤處理

### Story 131-3: Dialog Engine + Input Gateway
- [ ] `tests/unit/orchestration/test_dialog_engine_deep.py`
  - [ ] 對話引擎初始化
  - [ ] 完整對話流程（start → update → complete）
  - [ ] 缺失欄位追問
  - [ ] 對話超時清理
  - [ ] 並發對話隔離
- [ ] `tests/unit/orchestration/test_input_gateway.py`
  - [ ] 用戶輸入處理
  - [ ] ServiceNow 輸入處理
  - [ ] Prometheus 告警處理
  - [ ] 輸入標準化
- [ ] `tests/unit/orchestration/test_schema_validator.py`
  - [ ] Schema 驗證成功
  - [ ] Schema 驗證失敗
  - [ ] 必填欄位檢查

### Story 131-4: 覆蓋率報告
- [ ] 生成全面覆蓋率報告
- [ ] 更新 gap analysis
- [ ] 確認 80% 目標達成
- [ ] 記錄剩餘差距

## 驗證標準

- [ ] HITL 模組覆蓋率 ≥ 80%
- [ ] Metrics 模組覆蓋率 ≥ 70%
- [ ] MCP Core 覆蓋率 ≥ 60%
- [ ] Dialog Engine 覆蓋率 ≥ 70%
- [ ] 整體覆蓋率 ≥ 80%
- [ ] 所有新測試通過
- [ ] 回歸測試無失敗
