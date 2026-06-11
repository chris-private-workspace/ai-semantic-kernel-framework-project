# Sprint 128 Checklist: LLMClassifier Mock→Real + MAF ACL

## 開發任務

### Story 128-1: LLMClassifier Mock→Real
- [ ] 修改 `classifier.py` — 接入真實 LLM
  - [ ] 整合 LLMServiceFactory 取得 LLM client
  - [ ] 設計分類 Prompt（覆蓋所有 ITIntentCategory）
  - [ ] 實現結構化輸出解析（JSON → ClassificationResult）
  - [ ] 添加信心度分數（confidence score）
- [ ] 實現結果快取
  - [ ] 相似查詢 hash 計算
  - [ ] Redis 快取（TTL 可配置）
  - [ ] 快取命中/未命中指標
- [ ] 實現降級策略
  - [ ] LLM 超時 fallback 到 Mock
  - [ ] LLM 錯誤 fallback 到 Mock
  - [ ] 降級事件日誌記錄
- [ ] 更新 LLMServiceFactory
  - [ ] 移除預設 Mock fallback（改為明確配置）
  - [ ] 添加不安全 fallback 警告日誌
- [ ] 建立分類評估集
  - [ ] 50+ 測試查詢與預期分類
  - [ ] 準確率計算腳本

### Story 128-2: MAF Anti-Corruption Layer
- [ ] 建立 `src/integrations/agent_framework/acl/` 目錄
- [ ] 實現 `interfaces.py`
  - [ ] AgentBuilderInterface — 穩定的 Builder 介面
  - [ ] AgentRunnerInterface — 穩定的 Runner 介面
  - [ ] ToolInterface — 穩定的 Tool 介面
- [ ] 實現 `adapter.py`
  - [ ] MAF v1.x 適配器
  - [ ] 介面到 MAF API 的映射
  - [ ] 版本特定的差異處理
- [ ] 實現 `version_detector.py`
  - [ ] MAF 套件版本偵測
  - [ ] API 相容性檢查
  - [ ] 版本不相容警告

### Story 128-3: 測試與驗證
- [ ] LLMClassifier 測試
  - [ ] `tests/unit/orchestration/test_llm_classifier_real.py`
  - [ ] `tests/unit/orchestration/test_classification_prompt.py`
  - [ ] `tests/unit/orchestration/test_llm_cache.py`
  - [ ] `tests/unit/orchestration/test_llm_fallback.py`
- [ ] ACL 測試
  - [ ] `tests/unit/integrations/agent_framework/test_acl_interfaces.py`
  - [ ] `tests/unit/integrations/agent_framework/test_acl_adapter.py`
- [ ] 整合測試
  - [ ] `tests/integration/orchestration/test_three_layer_real.py`

## 驗證標準

- [ ] LLMClassifier 使用真實 LLM 調用
- [ ] 分類準確率 > 85%（評估集）
- [ ] 快取命中時 < 10ms 回應
- [ ] LLM 不可用時正確降級
- [ ] ACL 隔離 MAF API 變更
- [ ] 所有新測試通過
- [ ] 回歸測試無失敗
