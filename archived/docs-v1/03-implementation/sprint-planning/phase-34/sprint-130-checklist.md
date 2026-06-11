# Sprint 130 Checklist: Correlation/RootCause 真實資料連接

## 開發任務

### Story 130-1: Correlation 真實資料
- [ ] 實現 `src/integrations/correlation/data_source.py`
  - [ ] Azure Monitor API client
  - [ ] Application Insights 查詢
  - [ ] OTel trace/metric 提取
- [ ] 實現 `src/integrations/correlation/event_collector.py`
  - [ ] 時間窗口事件收集
  - [ ] 服務名稱關聯
  - [ ] 事件去重與聚合
- [ ] 修改 `src/integrations/correlation/analyzer.py`
  - [ ] 移除偽造資料返回邏輯
  - [ ] 接入真實資料來源
  - [ ] 保持 API 介面不變
- [ ] 更新相關 API 路由
  - [ ] 確認回應格式不變
  - [ ] 添加「無資料」時的合理回應

### Story 130-2: RootCause 真實案例庫
- [ ] 建立案例表 Alembic migration
  - [ ] historical_cases 表
  - [ ] 欄位：id, title, description, root_cause, resolution, category, severity, created_at
  - [ ] 索引：category + severity
- [ ] 實現 `src/integrations/rootcause/case_repository.py`
  - [ ] CaseRepository — CRUD 操作
  - [ ] 案例查詢（按類別、嚴重度）
  - [ ] 案例統計
- [ ] 實現 `src/integrations/rootcause/case_matcher.py`
  - [ ] 文字相似度匹配
  - [ ] LLM 輔助語義匹配（可選）
  - [ ] 匹配結果排序（相關度）
- [ ] 修改 `src/integrations/rootcause/analyzer.py`
  - [ ] 移除硬編碼 2 個 HistoricalCase
  - [ ] 接入 CaseRepository
  - [ ] 保持 API 介面不變
- [ ] 建立初始案例資料
  - [ ] 從 ServiceNow 匯入腳本
  - [ ] 10-20 個種子案例

### Story 130-3: 測試與驗證
- [ ] `tests/unit/integrations/correlation/test_correlation_data_source.py`
- [ ] `tests/unit/integrations/correlation/test_event_collector.py`
- [ ] `tests/unit/integrations/rootcause/test_case_repository.py`
- [ ] `tests/unit/integrations/rootcause/test_case_matcher.py`
- [ ] `tests/integration/test_correlation_real.py`
- [ ] `tests/integration/test_rootcause_real.py`

## 驗證標準

- [ ] Correlation 返回真實關聯資料（非偽造）
- [ ] RootCause 查詢案例庫（非硬編碼）
- [ ] 案例匹配返回相關結果
- [ ] API 回應格式向後相容
- [ ] 所有新測試通過
- [ ] 回歸測試無失敗
