# Sprint 86: 監控增強與災難恢復

## Sprint Info

| Field | Value |
|-------|-------|
| **Sprint Number** | 86 |
| **Phase** | 25 - 生產環境擴展 |
| **Duration** | 5-7 days |
| **Story Points** | 20 pts |
| **Status** | 計劃中 |
| **Priority** | 🔵 P3 視需求 |

---

## Sprint Goal

實現完整 Prometheus + Grafana 監控體系，建立災難恢復計劃並進行測試。

---

## Prerequisites

- Sprint 85 完成（K8s 部署）✅
- AKS 集群運行正常 ✅

---

## User Stories

### S86-1: Prometheus + Grafana 監控 (10 pts)

**Description**: 部署完整監控體系，創建自定義 Dashboard。

**Acceptance Criteria**:
- [ ] Prometheus 收集所有指標
- [ ] 自定義 Grafana Dashboard
- [ ] 告警規則配置
- [ ] 告警通知（Teams/Email）

**Files to Create**:
- `helm/monitoring/prometheus-values.yaml` (~100 行)
- `helm/monitoring/grafana-values.yaml` (~80 行)
- `helm/monitoring/alerting-rules.yaml` (~150 行)
- `docs/monitoring/dashboards/` (目錄)
  - `api-performance.json`
  - `execution-stats.json`
  - `claude-usage.json`
  - `system-resources.json`

**Technical Design**:

**Prometheus 配置重點**:
```yaml
# helm/monitoring/prometheus-values.yaml
serverFiles:
  prometheus.yml:
    scrape_configs:
      - job_name: 'ipa-backend'
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_label_app]
            action: keep
            regex: ipa-backend
```

**告警規則示例**:
```yaml
# helm/monitoring/alerting-rules.yaml
groups:
  - name: ipa-platform
    rules:
      - alert: HighErrorRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 5% for 5 minutes"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is above 2 seconds"

      - alert: ClaudeAPIErrors
        expr: sum(rate(claude_api_errors_total[5m])) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Claude API errors detected"
```

**Grafana Dashboard 指標**:

| Dashboard | 關鍵指標 |
|-----------|----------|
| API Performance | 請求延遲、吞吐量、錯誤率 |
| Execution Stats | 執行成功率、平均執行時間、並發數 |
| Claude Usage | Token 使用量、API 調用次數、成本估算 |
| System Resources | CPU、Memory、Network、Disk |

---

### S86-2: 災難恢復 + 自動備份 (10 pts)

**Description**: 建立災難恢復計劃，實現自動備份和恢復流程。

**Acceptance Criteria**:
- [ ] 自動備份策略（每日/每週）
- [ ] 恢復流程文檔
- [ ] 恢復演練成功
- [ ] RTO < 4 小時
- [ ] RPO < 1 小時

**Files to Create**:
- `docs/operations/disaster-recovery-plan.md` (~200 行)
- `scripts/backup/backup.sh` (~100 行)
- `scripts/backup/restore.sh` (~100 行)
- `helm/backup/cronjob.yaml` (~50 行)

**Technical Design**:

**備份腳本**:
```bash
#!/bin/bash
# scripts/backup/backup.sh

# 配置
BACKUP_DIR="/backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# PostgreSQL 備份
echo "Starting PostgreSQL backup..."
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME | gzip > ${BACKUP_DIR}/postgres_${TIMESTAMP}.sql.gz

# Redis 備份
echo "Starting Redis backup..."
redis-cli -h $REDIS_HOST BGSAVE
sleep 10
cp /data/dump.rdb ${BACKUP_DIR}/redis_${TIMESTAMP}.rdb

# 上傳到 Azure Blob Storage
echo "Uploading to Azure Blob Storage..."
az storage blob upload-batch \
  --account-name $STORAGE_ACCOUNT \
  --destination backups \
  --source $BACKUP_DIR \
  --pattern "*_${TIMESTAMP}*"

# 清理舊備份
echo "Cleaning up old backups..."
find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete

echo "Backup completed: ${TIMESTAMP}"
```

**恢復流程**:
```bash
#!/bin/bash
# scripts/backup/restore.sh

# 參數
BACKUP_TIMESTAMP=$1

# 從 Azure Blob Storage 下載
echo "Downloading backup from Azure..."
az storage blob download-batch \
  --account-name $STORAGE_ACCOUNT \
  --source backups \
  --destination /restore \
  --pattern "*_${BACKUP_TIMESTAMP}*"

# PostgreSQL 恢復
echo "Restoring PostgreSQL..."
gunzip -c /restore/postgres_${BACKUP_TIMESTAMP}.sql.gz | \
  psql -h $DB_HOST -U $DB_USER -d $DB_NAME

# Redis 恢復
echo "Restoring Redis..."
redis-cli -h $REDIS_HOST SHUTDOWN NOSAVE
cp /restore/redis_${BACKUP_TIMESTAMP}.rdb /data/dump.rdb
redis-server --daemonize yes

echo "Restore completed"
```

**Kubernetes CronJob**:
```yaml
# helm/backup/cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: ipa-backup
spec:
  schedule: "0 2 * * *"  # 每日凌晨 2 點
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: your-acr.azurecr.io/ipa-backup:latest
            command: ["/scripts/backup.sh"]
            envFrom:
            - secretRef:
                name: backup-credentials
          restartPolicy: OnFailure
```

---

## Disaster Recovery Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| **RTO** | < 4 小時 | Recovery Time Objective - 最大停機時間 |
| **RPO** | < 1 小時 | Recovery Point Objective - 最大數據丟失時間 |
| **備份頻率** | 每日 | 完整備份 |
| **備份保留** | 30 天 | 歷史備份保留期限 |

---

## Definition of Done

- [ ] 所有 Stories 完成
- [ ] Prometheus 收集所有指標
- [ ] Grafana 儀表板顯示正確
- [ ] 備份按計劃執行
- [ ] 災難恢復演練成功
- [ ] RTO < 4 小時驗證

---

## Success Metrics

| Metric | Target |
|--------|--------|
| 監控指標覆蓋率 | 100% |
| 告警準確率 | > 95% |
| 備份成功率 | > 99.9% |
| 災難恢復 RTO | < 4 小時 |
| 災難恢復 RPO | < 1 小時 |

---

**Created**: 2026-01-12
**Story Points**: 20 pts
