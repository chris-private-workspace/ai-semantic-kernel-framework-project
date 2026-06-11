# Sprint 86 Checklist: 監控增強與災難恢復

## Sprint Status

| Metric | Value |
|--------|-------|
| **Total Stories** | 2 |
| **Total Points** | 20 pts |
| **Completed** | 0 |
| **In Progress** | 0 |
| **Status** | 計劃中 |

---

## Stories

### S86-1: Prometheus + Grafana 監控 (10 pts)

**Status**: ⬜ 待開始

**Tasks**:
- [ ] 部署 Prometheus（Helm）
  - [ ] 配置 ServiceMonitor
  - [ ] 配置 scrape_configs
  - [ ] 驗證指標收集
- [ ] 部署 Grafana（Helm）
  - [ ] 配置數據源
  - [ ] 配置認證
- [ ] 創建自定義 Dashboard
  - [ ] API Performance Dashboard
  - [ ] Execution Stats Dashboard
  - [ ] Claude Usage Dashboard
  - [ ] System Resources Dashboard
- [ ] 配置告警規則
  - [ ] HighErrorRate 告警
  - [ ] HighResponseTime 告警
  - [ ] ClaudeAPIErrors 告警
  - [ ] ResourceExhaustion 告警
- [ ] 配置通知渠道
  - [ ] Teams Webhook
  - [ ] Email 通知

**Acceptance Criteria**:
- [ ] Prometheus 收集指標
- [ ] Grafana Dashboard 正常
- [ ] 告警規則生效
- [ ] 通知配置完成

---

### S86-2: 災難恢復 (10 pts)

**Status**: ⬜ 待開始

**Tasks**:
- [ ] 編寫災難恢復計劃文檔
  - [ ] 災難類型識別
  - [ ] 恢復優先級定義
  - [ ] 聯繫人清單
  - [ ] 恢復步驟詳細說明
- [ ] 創建備份腳本
  - [ ] PostgreSQL 備份
  - [ ] Redis 備份
  - [ ] 上傳到 Azure Blob Storage
  - [ ] 清理舊備份
- [ ] 創建恢復腳本
  - [ ] 下載備份
  - [ ] PostgreSQL 恢復
  - [ ] Redis 恢復
  - [ ] 驗證恢復結果
- [ ] 配置定時備份（CronJob）
  - [ ] 每日備份
  - [ ] 備份監控告警
- [ ] 執行恢復演練
  - [ ] 模擬災難場景
  - [ ] 執行恢復流程
  - [ ] 記錄恢復時間
  - [ ] 驗證數據完整性
- [ ] 驗證 RTO < 4h

**Acceptance Criteria**:
- [ ] 自動備份策略
- [ ] 恢復文檔完整
- [ ] 演練成功
- [ ] RTO < 4 小時
- [ ] RPO < 1 小時

---

## Verification Checklist

### Monitoring Tests
- [ ] Prometheus 運行正常
- [ ] 指標收集完整
- [ ] Grafana Dashboard 渲染正確
- [ ] 告警觸發正確
- [ ] 通知發送成功

### Backup Tests
- [ ] 備份 CronJob 執行成功
- [ ] 備份文件完整
- [ ] 上傳到 Azure 成功
- [ ] 舊備份清理正常

### Recovery Tests
- [ ] 恢復腳本可執行
- [ ] 數據恢復完整
- [ ] 服務恢復正常
- [ ] RTO 達標
- [ ] RPO 達標

---

**Last Updated**: 2026-01-12
