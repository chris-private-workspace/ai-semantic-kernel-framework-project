# IPA Platform 故障排除指南

本指南幫助您診斷和解決 IPA Platform 的常見問題。

---

## 目錄

1. [診斷工具](#診斷工具)
2. [常見問題](#常見問題)
3. [錯誤代碼參考](#錯誤代碼參考)
4. [效能問題](#效能問題)
5. [整合問題](#整合問題)
6. [升級問題](#升級問題)

---

## 診斷工具

### 健康檢查 API

```bash
# 系統健康檢查
curl http://localhost:8000/health

# 詳細健康檢查
curl http://localhost:8000/health/detailed

# 預期回應
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "database": {"status": "healthy", "latency_ms": 5},
    "redis": {"status": "healthy", "latency_ms": 2},
    "azure_openai": {"status": "healthy", "latency_ms": 150}
  }
}
```

### 日誌查看

```bash
# Docker 環境
docker-compose logs -f backend
docker-compose logs -f --tail=100 backend

# Kubernetes 環境
kubectl logs -f deployment/backend -n ipa-platform
kubectl logs -f -l app=backend -n ipa-platform --all-containers

# 系統日誌
journalctl -u ipa-platform -f
```

### 資源監控

```bash
# Docker 資源使用
docker stats

# Kubernetes 資源
kubectl top pods -n ipa-platform
kubectl top nodes

# 數據庫連接
docker-compose exec postgres psql -U ipa_user -c "SELECT count(*) FROM pg_stat_activity;"

# Redis 狀態
docker-compose exec redis redis-cli -a <password> INFO
```

---

## 常見問題

### 1. 無法啟動服務

**症狀**: 服務啟動失敗或立即退出

**診斷步驟**:
```bash
# 檢查日誌
docker-compose logs backend

# 檢查配置
docker-compose config

# 驗證環境變數
docker-compose exec backend env | grep -E "(DATABASE|REDIS|AZURE)"
```

**常見原因和解決方案**:

| 錯誤訊息 | 原因 | 解決方案 |
|----------|------|----------|
| `Connection refused` | 數據庫未啟動 | `docker-compose up -d postgres` |
| `Authentication failed` | 密碼錯誤 | 檢查 `.env` 中的密碼 |
| `Missing required config` | 缺少環境變數 | 補充必要的環境變數 |
| `Port already in use` | 端口衝突 | 更改端口或停止佔用進程 |

### 2. 數據庫連接失敗

**症狀**: `Connection refused` 或 `timeout`

**診斷步驟**:
```bash
# 檢查 PostgreSQL 狀態
docker-compose ps postgres

# 測試連接
docker-compose exec postgres pg_isready

# 檢查連接數
docker-compose exec postgres psql -U ipa_user -c \
  "SELECT state, count(*) FROM pg_stat_activity GROUP BY state;"
```

**解決方案**:

```bash
# 重啟 PostgreSQL
docker-compose restart postgres

# 檢查磁碟空間
df -h

# 增加連接數限制 (postgresql.conf)
max_connections = 200
```

### 3. Redis 連接失敗

**症狀**: `Connection refused` 或 `AUTH failed`

**診斷步驟**:
```bash
# 檢查 Redis 狀態
docker-compose exec redis redis-cli -a <password> ping

# 檢查記憶體使用
docker-compose exec redis redis-cli -a <password> INFO memory
```

**解決方案**:

```bash
# 重啟 Redis
docker-compose restart redis

# 清除緩存 (謹慎使用)
docker-compose exec redis redis-cli -a <password> FLUSHDB
```

### 4. API 響應慢

**症狀**: API 響應時間過長 (> 2 秒)

**診斷步驟**:
```bash
# 檢查 API 延遲
curl -w "\nTime: %{time_total}s\n" http://localhost:8000/api/v1/workflows

# 檢查數據庫查詢
docker-compose exec postgres psql -U ipa_user -c \
  "SELECT pid, query, state, wait_event FROM pg_stat_activity WHERE state = 'active';"
```

**解決方案**:

1. **數據庫索引**: 確保常用查詢有適當索引
2. **連接池**: 增加數據庫連接池大小
3. **緩存**: 啟用 Redis 緩存
4. **查詢優化**: 檢查 N+1 查詢問題

### 5. 工作流執行失敗

**症狀**: 執行狀態為 `FAILED`

**診斷步驟**:
```bash
# 獲取執行詳情
curl http://localhost:8000/api/v1/executions/{execution_id}

# 獲取執行日誌
curl http://localhost:8000/api/v1/executions/{execution_id}/logs
```

**常見原因**:

| 錯誤類型 | 原因 | 解決方案 |
|----------|------|----------|
| `NodeTimeout` | 節點執行超時 | 增加超時時間或優化節點 |
| `ValidationError` | 輸入參數無效 | 檢查參數格式 |
| `ExternalServiceError` | 外部服務失敗 | 檢查服務狀態和憑證 |
| `AgentError` | AI Agent 失敗 | 檢查 Azure OpenAI 配置 |

### 6. 身份驗證問題

**症狀**: `401 Unauthorized` 或 `403 Forbidden`

**診斷步驟**:
```bash
# 驗證 Token
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/users/me

# 檢查 Token 內容 (JWT)
echo "<token>" | cut -d. -f2 | base64 -d 2>/dev/null | jq
```

**解決方案**:

1. **Token 過期**: 重新登入獲取新 Token
2. **權限不足**: 檢查用戶角色和權限
3. **JWT 密鑰不匹配**: 確保所有實例使用相同密鑰

---

## 錯誤代碼參考

### HTTP 錯誤代碼

| 代碼 | 含義 | 常見原因 |
|------|------|----------|
| 400 | Bad Request | 請求參數無效 |
| 401 | Unauthorized | Token 無效或過期 |
| 403 | Forbidden | 權限不足 |
| 404 | Not Found | 資源不存在 |
| 409 | Conflict | 資源衝突 (如重複名稱) |
| 422 | Validation Error | 數據驗證失敗 |
| 429 | Too Many Requests | 超過速率限制 |
| 500 | Internal Error | 服務器內部錯誤 |
| 503 | Service Unavailable | 服務不可用 |

### 應用錯誤代碼

| 代碼 | 含義 | 處理方式 |
|------|------|----------|
| `WF001` | 工作流不存在 | 檢查工作流 ID |
| `WF002` | 工作流未啟用 | 啟用工作流 |
| `WF003` | 工作流配置無效 | 檢查工作流定義 |
| `EX001` | 執行不存在 | 檢查執行 ID |
| `EX002` | 執行已完成 | 無需操作 |
| `EX003` | 執行超時 | 增加超時或優化 |
| `AG001` | Agent 不存在 | 檢查 Agent ID |
| `AG002` | Agent 呼叫失敗 | 檢查 AI 服務 |
| `DB001` | 數據庫錯誤 | 檢查數據庫連接 |
| `RD001` | Redis 錯誤 | 檢查 Redis 連接 |

---

## 效能問題

### 診斷效能瓶頸

```bash
# 檢查 API 效能指標
curl http://localhost:8000/api/v1/performance/summary

# 檢查緩存命中率
curl http://localhost:8000/api/v1/performance/cache/stats

# 檢查數據庫查詢統計
curl http://localhost:8000/api/v1/performance/query/stats
```

### 效能優化檢查清單

- [ ] **數據庫索引**: 確保常用查詢字段有索引
- [ ] **緩存命中率**: 目標 ≥ 60%
- [ ] **連接池**: 根據負載調整大小
- [ ] **N+1 查詢**: 使用 eager loading
- [ ] **API 響應**: P95 < 500ms

### 效能調優參數

```bash
# 數據庫連接池
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=10

# Redis 連接
REDIS_MAX_CONNECTIONS=20

# 工作進程數
WORKERS=4

# 請求超時
REQUEST_TIMEOUT=30
```

---

## 整合問題

### Azure OpenAI

**問題**: `429 Too Many Requests`

```bash
# 檢查配額使用
curl -X POST "$AZURE_OPENAI_ENDPOINT/openai/deployments/$DEPLOYMENT/chat/completions?api-version=2024-02-01" \
  -H "api-key: $AZURE_OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"test"}]}'
```

**解決方案**:
1. 實施重試邏輯和指數退避
2. 增加 Azure OpenAI 配額
3. 使用多個部署分散負載

### ServiceNow

**問題**: 連接失敗

```bash
# 測試 ServiceNow 連接
curl -u "$SERVICENOW_USER:$SERVICENOW_PASS" \
  "https://$SERVICENOW_INSTANCE.service-now.com/api/now/table/incident?sysparm_limit=1"
```

**解決方案**:
1. 驗證 API 憑證
2. 檢查 IP 白名單
3. 確認 API 權限

### n8n

**問題**: Webhook 觸發失敗

```bash
# 測試 Webhook
curl -X POST http://n8n:5678/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

**解決方案**:
1. 確認 n8n 服務運行中
2. 檢查 Webhook URL 配置
3. 驗證簽名密鑰

---

## 升級問題

### 升級前檢查

```bash
# 備份數據庫
pg_dump -h localhost -U ipa_user ipa_platform > backup.sql

# 檢查當前版本
curl http://localhost:8000/health | jq .version

# 檢查遷移狀態
alembic current
```

### 升級步驟

```bash
# 1. 停止服務
docker-compose stop backend

# 2. 拉取新版本
docker-compose pull backend

# 3. 執行遷移
docker-compose run --rm backend alembic upgrade head

# 4. 啟動服務
docker-compose up -d backend

# 5. 驗證
curl http://localhost:8000/health
```

### 回滾步驟

```bash
# 1. 停止服務
docker-compose stop backend

# 2. 回滾遷移
docker-compose run --rm backend alembic downgrade -1

# 3. 使用舊版本
docker-compose up -d backend:v1.0.0

# 4. 恢復數據庫 (如需要)
psql -h localhost -U ipa_user ipa_platform < backup.sql
```

---

## 獲取支援

### 收集診斷資訊

在聯繫支援前，請收集以下資訊：

```bash
# 系統資訊
uname -a
docker version
docker-compose version

# 服務狀態
docker-compose ps
docker-compose logs --tail=500 backend > backend.log

# 配置 (移除敏感資訊)
docker-compose config > config.txt
```

### 支援管道

- **文檔**: [docs.ipa-platform.com](https://docs.ipa-platform.com)
- **Email**: support@ipa-platform.com
- **緊急熱線**: +886-2-1234-5678 (24/7)

---

*最後更新: 2025-11-26*
