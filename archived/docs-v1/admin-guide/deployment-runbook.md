# IPA Platform 部署運維手冊 (Deployment Runbook)

本手冊提供 IPA Platform 的完整部署流程、檢查清單、回滾程序和災難恢復計劃。

---

## 目錄

1. [部署前檢查清單](#部署前檢查清單)
2. [部署步驟](#部署步驟)
3. [回滾程序](#回滾程序)
4. [監控和告警配置](#監控和告警配置)
5. [災難恢復計劃](#災難恢復計劃)
6. [維護作業](#維護作業)

---

## 部署前檢查清單

### 基礎設施檢查

| 項目 | 檢查內容 | 命令/方法 | 預期結果 |
|------|----------|-----------|----------|
| Kubernetes 集群 | 節點健康狀態 | `kubectl get nodes` | All nodes Ready |
| PostgreSQL | 數據庫連接 | `pg_isready -h <host>` | accepting connections |
| Redis | 緩存連接 | `redis-cli ping` | PONG |
| 磁碟空間 | 可用空間 > 20% | `df -h` | 各分區 > 20% |
| 網路連通性 | 服務間通訊 | `curl health endpoints` | 200 OK |

### 數據備份檢查

| 項目 | 檢查內容 | 狀態 |
|------|----------|------|
| 數據庫備份 | 完整備份已完成 | ☐ |
| Redis 快照 | RDB/AOF 備份完成 | ☐ |
| 配置備份 | ConfigMaps/Secrets 已備份 | ☐ |
| 備份驗證 | 備份文件可讀取 | ☐ |

### 配置檢查

| 項目 | 檢查內容 | 狀態 |
|------|----------|------|
| 環境變數 | 所有必要變數已設置 | ☐ |
| Secrets | Azure Key Vault / K8s Secrets 可訪問 | ☐ |
| SSL 證書 | 證書有效期 > 30 天 | ☐ |
| DNS 記錄 | DNS 指向正確 | ☐ |
| CORS 設置 | 允許的 origins 正確 | ☐ |

### 測試檢查

| 項目 | 檢查內容 | 狀態 |
|------|----------|------|
| 單元測試 | 全部通過 | ☐ |
| 集成測試 | 全部通過 | ☐ |
| E2E 測試 | 關鍵流程通過 | ☐ |
| 負載測試 | 性能指標達標 | ☐ |
| 安全掃描 | 無 P0/P1 漏洞 | ☐ |
| UAT | 用戶驗收通過 | ☐ |

### 監控檢查

| 項目 | 檢查內容 | 狀態 |
|------|----------|------|
| Prometheus | 抓取端點正常 | ☐ |
| Grafana | Dashboard 可訪問 | ☐ |
| AlertManager | 告警規則已配置 | ☐ |
| 日誌收集 | Jaeger/ELK 正常 | ☐ |

---

## 部署步驟

### 階段 1: 準備階段

#### 1.1 通知相關人員

```bash
# 發送部署通知
echo "IPA Platform 部署將於 $(date -d '+30 minutes' '+%Y-%m-%d %H:%M') 開始"
```

**通知清單**:
- [ ] 開發團隊
- [ ] DevOps 團隊
- [ ] QA 團隊
- [ ] 產品負責人
- [ ] 客戶支援團隊

#### 1.2 創建數據庫備份

```bash
# PostgreSQL 完整備份
pg_dump -h $DB_HOST -U $DB_USER -d ipa_platform \
  --format=custom \
  --file=backup_$(date +%Y%m%d_%H%M%S).dump

# 驗證備份
pg_restore --list backup_*.dump | head -20

# 上傳到 Azure Blob Storage
az storage blob upload \
  --account-name $STORAGE_ACCOUNT \
  --container-name backups \
  --name db/$(date +%Y%m%d)/backup.dump \
  --file backup_*.dump
```

#### 1.3 創建 Redis 快照

```bash
# 觸發 RDB 快照
redis-cli -h $REDIS_HOST -a $REDIS_PASSWORD BGSAVE

# 等待完成
redis-cli -h $REDIS_HOST -a $REDIS_PASSWORD LASTSAVE
```

### 階段 2: 部署階段

#### 2.1 Docker Compose 部署（開發/測試）

```bash
# 1. 拉取最新鏡像
docker-compose pull

# 2. 停止當前服務（保留數據卷）
docker-compose stop backend frontend

# 3. 備份當前版本標籤
docker tag ipa-platform/backend:latest ipa-platform/backend:rollback

# 4. 啟動新版本
docker-compose up -d backend frontend

# 5. 檢查服務狀態
docker-compose ps
docker-compose logs -f --tail=50 backend

# 6. 健康檢查
curl http://localhost:8000/health
curl http://localhost:3000
```

#### 2.2 Kubernetes 部署（生產）

```bash
# 1. 設置環境變數
export VERSION=v1.2.0
export NAMESPACE=ipa-platform

# 2. 更新鏡像版本
kubectl set image deployment/backend \
  backend=ipa-platform/backend:$VERSION \
  -n $NAMESPACE

kubectl set image deployment/frontend \
  frontend=ipa-platform/frontend:$VERSION \
  -n $NAMESPACE

# 3. 監控部署狀態
kubectl rollout status deployment/backend -n $NAMESPACE --timeout=300s
kubectl rollout status deployment/frontend -n $NAMESPACE --timeout=300s

# 4. 檢查 Pod 狀態
kubectl get pods -n $NAMESPACE -l app=backend
kubectl get pods -n $NAMESPACE -l app=frontend

# 5. 查看部署日誌
kubectl logs -f deployment/backend -n $NAMESPACE --tail=100
```

#### 2.3 數據庫遷移

```bash
# 1. 檢查當前遷移版本
kubectl exec -it deployment/backend -n $NAMESPACE -- alembic current

# 2. 查看待執行遷移
kubectl exec -it deployment/backend -n $NAMESPACE -- alembic history

# 3. 執行遷移
kubectl exec -it deployment/backend -n $NAMESPACE -- alembic upgrade head

# 4. 驗證遷移
kubectl exec -it deployment/backend -n $NAMESPACE -- alembic current
```

### 階段 3: 驗證階段

#### 3.1 健康檢查

```bash
# API 健康檢查
curl -s https://api.ipa-platform.com/health | jq

# 預期回應
# {
#   "status": "healthy",
#   "version": "1.2.0",
#   "database": "connected",
#   "redis": "connected"
# }

# 詳細健康檢查
curl -s https://api.ipa-platform.com/health/detailed | jq
```

#### 3.2 功能驗證

```bash
# 1. 登錄測試
TOKEN=$(curl -s -X POST https://api.ipa-platform.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass"}' | jq -r '.access_token')

# 2. 工作流 API 測試
curl -s https://api.ipa-platform.com/api/v1/workflows \
  -H "Authorization: Bearer $TOKEN" | jq '.total'

# 3. 創建測試工作流
curl -s -X POST https://api.ipa-platform.com/api/v1/workflows \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Deployment Test Workflow",
    "description": "Verify deployment",
    "status": "draft"
  }' | jq
```

#### 3.3 監控驗證

```bash
# Prometheus 目標檢查
curl -s http://prometheus:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Grafana Dashboard 檢查
curl -s http://grafana:3000/api/health | jq
```

### 階段 4: 完成階段

#### 4.1 清理和記錄

```bash
# 清理舊鏡像
docker image prune -f

# 記錄部署信息
cat >> deployment.log << EOF
========================================
Deployment: $(date)
Version: $VERSION
Status: SUCCESS
Duration: $SECONDS seconds
Deployed by: $(whoami)
========================================
EOF
```

#### 4.2 發送完成通知

```bash
# 發送部署成功通知
curl -X POST $TEAMS_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{
    "title": "IPA Platform 部署完成",
    "text": "版本 '"$VERSION"' 已成功部署到生產環境",
    "themeColor": "00FF00"
  }'
```

---

## 回滾程序

### 回滾決策標準

執行回滾的情況：
- 健康檢查失敗超過 5 分鐘
- 錯誤率超過 5%
- P95 延遲超過 10 秒
- 關鍵功能無法使用
- 數據一致性問題

### Docker Compose 回滾

```bash
# 1. 停止當前版本
docker-compose stop backend frontend

# 2. 恢復到之前的鏡像
docker tag ipa-platform/backend:rollback ipa-platform/backend:latest

# 3. 重啟服務
docker-compose up -d backend frontend

# 4. 驗證回滾
curl http://localhost:8000/health
```

### Kubernetes 回滾

```bash
# 1. 查看部署歷史
kubectl rollout history deployment/backend -n $NAMESPACE

# 2. 回滾到上一版本
kubectl rollout undo deployment/backend -n $NAMESPACE
kubectl rollout undo deployment/frontend -n $NAMESPACE

# 3. 回滾到指定版本
kubectl rollout undo deployment/backend -n $NAMESPACE --to-revision=3

# 4. 監控回滾狀態
kubectl rollout status deployment/backend -n $NAMESPACE

# 5. 驗證回滾
kubectl get pods -n $NAMESPACE
curl https://api.ipa-platform.com/health
```

### 數據庫回滾

```bash
# 1. 回滾遷移（降級一個版本）
kubectl exec -it deployment/backend -n $NAMESPACE -- alembic downgrade -1

# 2. 回滾到指定版本
kubectl exec -it deployment/backend -n $NAMESPACE -- alembic downgrade <revision_id>

# 3. 從備份恢復（完全回滾）
pg_restore -h $DB_HOST -U $DB_USER -d ipa_platform \
  --clean --if-exists \
  backup_before_deployment.dump
```

### 回滾後檢查清單

| 項目 | 狀態 |
|------|------|
| 健康檢查通過 | ☐ |
| 登錄功能正常 | ☐ |
| 工作流 CRUD 正常 | ☐ |
| 執行功能正常 | ☐ |
| 監控數據正常 | ☐ |
| 通知相關人員 | ☐ |
| 記錄回滾原因 | ☐ |

---

## 監控和告警配置

### Prometheus 告警規則

```yaml
# monitoring/prometheus/alert-rules.yml
groups:
  - name: ipa-platform-alerts
    rules:
      # 服務不可用
      - alert: ServiceDown
        expr: up{job="ipa-backend"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "IPA Backend 服務不可用"
          description: "{{ $labels.instance }} 已停止響應超過 1 分鐘"

      # 高錯誤率
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m]))
          / sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "API 錯誤率過高"
          description: "錯誤率超過 5%，當前: {{ $value | humanizePercentage }}"

      # 高延遲
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
          ) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API P95 延遲過高"
          description: "P95 延遲超過 5 秒，當前: {{ $value }}s"

      # 數據庫連接池耗盡
      - alert: DatabaseConnectionPoolExhausted
        expr: db_connection_pool_available < 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "數據庫連接池即將耗盡"
          description: "可用連接數: {{ $value }}"

      # Redis 連接失敗
      - alert: RedisConnectionFailed
        expr: redis_connected == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis 連接失敗"

      # 磁碟空間不足
      - alert: DiskSpaceLow
        expr: |
          (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 20
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "磁碟空間不足"
          description: "可用空間低於 20%"

      # Pod 重啟過多
      - alert: PodRestartingTooMuch
        expr: increase(kube_pod_container_status_restarts_total[1h]) > 5
        labels:
          severity: warning
        annotations:
          summary: "Pod 重啟次數過多"
          description: "{{ $labels.pod }} 在過去 1 小時內重啟了 {{ $value }} 次"
```

### AlertManager 配置

```yaml
# monitoring/alertmanager/alertmanager.yml
global:
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alerts@ipa-platform.com'

route:
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
      continue: true
    - match:
        severity: warning
      receiver: 'warning-alerts'

receivers:
  - name: 'default'
    email_configs:
      - to: 'devops@example.com'

  - name: 'critical-alerts'
    email_configs:
      - to: 'oncall@example.com'
    webhook_configs:
      - url: 'https://hooks.slack.com/services/xxx/yyy/zzz'
        send_resolved: true

  - name: 'warning-alerts'
    email_configs:
      - to: 'devops@example.com'
```

### Grafana Dashboard 配置

**必要的 Dashboard**:

| Dashboard | 用途 | 刷新間隔 |
|-----------|------|----------|
| System Overview | 整體系統狀態 | 30s |
| API Performance | API 延遲和吞吐量 | 10s |
| Database Metrics | 數據庫性能 | 30s |
| Business Metrics | 業務指標 | 1m |
| Security Dashboard | 安全事件 | 1m |

---

## 災難恢復計劃

### RTO 和 RPO 目標

| 指標 | 目標值 | 說明 |
|------|--------|------|
| RTO (Recovery Time Objective) | 4 小時 | 服務恢復時間 |
| RPO (Recovery Point Objective) | 1 小時 | 可接受的數據丟失時間 |

### 備份策略

#### 數據庫備份

```bash
# 每日完整備份（凌晨 2:00）
0 2 * * * pg_dump -h $DB_HOST -U $DB_USER -d ipa_platform \
  --format=custom \
  --file=/backups/daily/ipa_$(date +\%Y\%m\%d).dump

# 每小時增量備份
0 * * * * pg_basebackup -h $DB_HOST -U replication \
  -D /backups/wal/$(date +\%Y\%m\%d\%H) \
  --wal-method=stream

# 備份到遠程存儲
0 3 * * * az storage blob upload-batch \
  --source /backups/daily \
  --destination backups \
  --account-name $STORAGE_ACCOUNT
```

#### Redis 備份

```yaml
# Redis 持久化配置
save 900 1      # 900 秒內有 1 次寫入則保存
save 300 10     # 300 秒內有 10 次寫入則保存
save 60 10000   # 60 秒內有 10000 次寫入則保存

appendonly yes
appendfsync everysec
```

### 災難恢復流程

#### 場景 1: 數據庫故障

```bash
# 1. 確認主數據庫不可用
pg_isready -h $DB_HOST

# 2. 切換到備用數據庫
kubectl patch service postgres \
  -p '{"spec":{"selector":{"app":"postgres-standby"}}}'

# 3. 從備份恢復（如果需要）
pg_restore -h $DB_HOST -U $DB_USER -d ipa_platform \
  --clean backup_latest.dump

# 4. 驗證數據完整性
psql -h $DB_HOST -U $DB_USER -d ipa_platform \
  -c "SELECT COUNT(*) FROM workflows;"
```

#### 場景 2: 完整站點故障

```bash
# 1. 激活備用站點
kubectl config use-context disaster-recovery-cluster

# 2. 恢復數據庫
pg_restore -h $DR_DB_HOST -U $DB_USER -d ipa_platform \
  --clean latest_backup.dump

# 3. 部署應用
kubectl apply -f k8s/

# 4. 更新 DNS
az network dns record-set a update \
  --resource-group ipa-platform \
  --zone-name ipa-platform.com \
  --name api \
  --set aRecords[0].ipv4Address=$DR_IP

# 5. 驗證服務
curl https://api.ipa-platform.com/health
```

#### 場景 3: 數據損壞

```bash
# 1. 識別損壞的時間點
SELECT * FROM audit_logs WHERE timestamp > '2025-01-01 12:00:00' ORDER BY timestamp;

# 2. 恢復到指定時間點（PITR）
pg_restore -h $DB_HOST -U $DB_USER -d ipa_platform \
  --target-time="2025-01-01 11:59:00" \
  backup_with_wal.dump

# 3. 重放必要的事務
# (根據審計日誌手動重做)
```

### 災難恢復演練

**季度演練計劃**:

| 季度 | 演練類型 | 目標 |
|------|----------|------|
| Q1 | 數據庫故障轉移 | RTO < 30 分鐘 |
| Q2 | 完整站點恢復 | RTO < 4 小時 |
| Q3 | 數據損壞恢復 | RPO < 1 小時 |
| Q4 | 全面災難恢復 | 驗證完整流程 |

---

## 維護作業

### 定期維護任務

#### 每日

| 任務 | 時間 | 負責人 |
|------|------|--------|
| 檢查系統健康 | 09:00 | DevOps |
| 審查告警 | 09:30 | DevOps |
| 驗證備份完成 | 10:00 | DevOps |

#### 每週

| 任務 | 時間 | 負責人 |
|------|------|--------|
| 安全更新檢查 | 週一 | DevOps |
| 性能報告審查 | 週五 | 團隊 |
| 清理舊日誌 | 週日 | 自動化 |

#### 每月

| 任務 | 時間 | 負責人 |
|------|------|--------|
| SSL 證書檢查 | 每月 1 日 | DevOps |
| 資源使用審計 | 每月 15 日 | DevOps |
| 安全漏洞掃描 | 每月最後一週 | 安全團隊 |

### 維護腳本

```bash
#!/bin/bash
# maintenance.sh - 每日維護腳本

echo "=== IPA Platform 每日維護 $(date) ==="

# 1. 健康檢查
echo ">>> 健康檢查..."
curl -s http://localhost:8000/health | jq

# 2. 清理過期會話
echo ">>> 清理過期會話..."
redis-cli -h $REDIS_HOST -a $REDIS_PASSWORD KEYS "session:*" | \
  xargs -I {} redis-cli -h $REDIS_HOST -a $REDIS_PASSWORD TTL {} | \
  grep -c "^-2$" | \
  xargs echo "已過期會話數:"

# 3. 清理舊審計日誌（保留 90 天）
echo ">>> 清理舊審計日誌..."
psql -h $DB_HOST -U $DB_USER -d ipa_platform -c \
  "DELETE FROM audit_logs WHERE timestamp < NOW() - INTERVAL '90 days';"

# 4. 優化數據庫
echo ">>> 分析數據庫表..."
psql -h $DB_HOST -U $DB_USER -d ipa_platform -c "ANALYZE;"

# 5. 檢查磁碟空間
echo ">>> 磁碟空間檢查..."
df -h | grep -E '^/dev'

# 6. 發送維護報告
echo ">>> 發送維護報告..."
# (發送 email 或 Teams 通知)

echo "=== 維護完成 ==="
```

---

## 緊急聯繫人

| 角色 | 姓名 | 電話 | Email |
|------|------|------|-------|
| DevOps 主管 | - | - | devops-lead@example.com |
| 後端主管 | - | - | backend-lead@example.com |
| 安全負責人 | - | - | security@example.com |
| 產品負責人 | - | - | product@example.com |

**24/7 On-Call 熱線**: +886-2-1234-5678

---

*最後更新: 2025-11-27*
