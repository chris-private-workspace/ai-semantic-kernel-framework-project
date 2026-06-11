# Sprint 126 Checklist: IT 事件處理場景

## 開發任務

### Story 126-1: 事件接收與分類
- [ ] 實現 `src/integrations/orchestration/input/incident_handler.py`
  - [ ] ServiceNow Incident Webhook payload 解析
  - [ ] 事件標準化為 InputGateway 格式
  - [ ] 嚴重度映射（P1-P4 → CRITICAL/HIGH/MEDIUM/LOW）
- [ ] 擴展 PatternMatcher 規則庫
  - [ ] 網路事件規則（10+ 規則）
  - [ ] 伺服器事件規則（10+ 規則）
  - [ ] 應用程式事件規則（5+ 規則）
  - [ ] 安全事件規則（5+ 規則）
- [ ] 擴展 ITIntentCategory
  - [ ] INCIDENT 子分類（NETWORK, SERVER, APPLICATION, SECURITY）
  - [ ] 事件分類信心度閾值

### Story 126-2: 智能分析與建議
- [ ] 建立 `src/integrations/incident/` 模組
- [ ] 實現 `analyzer.py` — IncidentAnalyzer
  - [ ] 歷史事件比對（Correlation 模組整合）
  - [ ] LLM 根因分析 prompt 設計
  - [ ] 知識庫查詢（過去解決方案匹配）
  - [ ] 根因分析結果結構化輸出
- [ ] 實現 `recommender.py` — ActionRecommender
  - [ ] 從根因生成修復建議列表
  - [ ] 建議信心度排序
  - [ ] 風險等級評估（RiskAssessor 整合）
  - [ ] 建議分類（自動/需審批）

### Story 126-3: 自動修復與審批
- [ ] 實現 `executor.py` — IncidentExecutor
  - [ ] 自動修復行動執行（低風險）
  - [ ] HITL 審批流程觸發（高風險）
  - [ ] 執行結果回報
- [ ] 實現自動修復行動庫
  - [ ] 重啟應用服務（Shell MCP）
  - [ ] 清理磁碟空間（Shell MCP）
  - [ ] AD 帳號解鎖（LDAP MCP）
- [ ] 實現 ServiceNow 狀態回寫
  - [ ] 更新 Incident 狀態
  - [ ] 添加 Work Notes
  - [ ] 關閉已解決的 Incident

### Story 126-4: 測試與驗證
- [ ] `tests/unit/integrations/incident/test_incident_handler.py`
- [ ] `tests/unit/integrations/incident/test_incident_analyzer.py`
- [ ] `tests/unit/integrations/incident/test_incident_recommender.py`
- [ ] `tests/unit/integrations/incident/test_incident_executor.py`
- [ ] `tests/e2e/test_incident_e2e.py`

## 驗證標準

- [ ] ServiceNow Incident → IPA 分類正確率 > 85%
- [ ] 低風險行動自動執行成功
- [ ] 高風險行動正確觸發 HITL 審批
- [ ] ServiceNow 狀態回寫正確
- [ ] 所有新測試通過
- [ ] 回歸測試無失敗
