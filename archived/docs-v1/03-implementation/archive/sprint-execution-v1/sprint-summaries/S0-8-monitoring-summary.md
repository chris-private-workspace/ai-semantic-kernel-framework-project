# S0-8: Monitoring Setup 完成總結

**Story ID**: S0-8
**Story Points**: 5
**完成日期**: 2025-11-20
**負責人**: DevOps Team

---

## 📋 目標達成情況

✅ **主要目標**: 配置混合監控方案（Azure Monitor + Application Insights + OpenTelemetry）

### 已完成項目

| 項目 | 狀態 | 說明 |
|-----|------|------|
| Azure Monitor 配置 | ✅ | Terraform 配置文件創建 |
| Application Insights | ✅ | 完整整合，自動檢測 |
| OpenTelemetry SDK | ✅ | FastAPI、SQL、Redis、HTTP 自動檢測 |
| 健康檢查端點 | ✅ | 4 個端點（/、liveness、readiness、detailed） |
| 告警規則 | ✅ | 8 個 Terraform 告警規則 |
| 監控架構設計 | ✅ | 完整技術設計文檔 |
| 使用指南 | ✅ | 詳細使用文檔 |

---

## 📁 新增文件

### 核心實現文件

1. **OpenTelemetry 配置** (`backend/src/core/telemetry/`)
   - `otel_config.py` (189 行) - Application Insights 整合
   - `__init__.py` - 模組導出

2. **健康檢查端點** (`backend/src/api/v1/health/`)
   - `routes.py` (273 行) - 4 個健康檢查端點
   - `__init__.py` - Router 導出

### Infrastructure as Code

1. **Terraform 配置** (`infrastructure/terraform/`)
   - `monitoring.tf` (71 行) - Log Analytics + App Insights
   - `monitoring_alerts.tf` (244 行) - 8 個告警規則

### 文檔文件

1. **架構設計**: `docs/03-implementation/monitoring-design.md` (詳細技術設計)
2. **使用指南**: `docs/04-usage/monitoring-guide.md` (使用文檔)
3. **實現總結**: `docs/03-implementation/S0-8-monitoring-summary.md` (本文檔)

### 配置更新

1. **應用配置**: `backend/src/core/config.py` (+8 行監控配置)
2. **環境變量**: `backend/.env.example` (+7 行)
3. **依賴管理**: `backend/requirements.txt` (+7 個包)
4. **主應用**: `backend/main.py` (集成監控和健康檢查)

---

## 🔧 技術實現細節

### 1. Azure Monitor 架構

```
Application → OpenTelemetry SDK → Application Insights → Azure Monitor
                                                          ↓
                                                    Log Analytics
                                                          ↓
                                                     Dashboards
```

**關鍵組件**:
- Log Analytics Workspace: 統一日誌存儲
- Application Insights: 應用性能監控
- Alert Rules: 自動告警

### 2. OpenTelemetry 整合

#### 自動檢測

```python
# 自動追蹤以下組件:
- FastAPIInstrumentor       # HTTP 請求
- SQLAlchemyInstrumentor    # 數據庫查詢
- RedisInstrumentor         # Redis 操作
- HTTPXClientInstrumentor   # 外部 HTTP 調用
```

#### 採樣策略

```python
# 開發環境: 100% 採樣
OTEL_TRACES_SAMPLER=always_on

# 生產環境: 20% 採樣（降低成本）
OTEL_TRACES_SAMPLER=traceidratio
OTEL_TRACES_SAMPLER_ARG=0.2
```

### 3. 健康檢查端點

#### 端點設計

| 端點 | 用途 | 檢查內容 |
|------|------|---------|
| `GET /api/v1/health/` | 基本檢查 | 應用版本和狀態 |
| `GET /api/v1/health/liveness` | K8s Liveness | 應用是否存活 |
| `GET /api/v1/health/readiness` | K8s Readiness | DB + Redis + Queue |
| `GET /api/v1/health/detailed` | 詳細報告 | 所有組件 + 延遲 |

#### Readiness 檢查邏輯

```python
checks = {}

# 數據庫檢查
await session.execute(text("SELECT 1"))
checks["database"] = {"status": "healthy"}

# Redis 檢查（讀寫測試）
await cache.set("health_check", "ok", ttl=10)
result = await cache.get("health_check")
checks["redis"] = {"status": "healthy"}

# 消息隊列檢查
queue_provider = get_queue_provider()
checks["queue"] = {"status": "healthy"}

# 整體狀態判斷
overall_status = "ready" if all healthy else "not_ready"
```

### 4. 告警規則

#### 8 個預設告警

| 告警名稱 | 條件 | 嚴重性 | 窗口 |
|---------|------|--------|------|
| HTTP 5xx 錯誤 | > 10 次 | 中 (2) | 5 分鐘 |
| HTTP 4xx 錯誤 | > 50 次 | 低 (3) | 5 分鐘 |
| 高 CPU 使用 | > 80% | 低 (3) | 5 分鐘 |
| 高記憶體使用 | > 85% | 低 (3) | 5 分鐘 |
| 響應時間慢 | > 2 秒 | 低 (3) | 5 分鐘 |
| 可用性低 | < 95% | 高 (1) | 5 分鐘 |
| 異常數量高 | > 10 次 | 中 (2) | 5 分鐘 |
| 依賴失敗 | > 10 次 | 中 (2) | 5 分鐘 |

#### 通知配置

```hcl
# Email 通知
email_receiver {
  name          = "DevOps Team"
  email_address = var.alert_email
}

# Webhook 通知（Slack）
webhook_receiver {
  name        = "Slack Webhook"
  service_uri = var.slack_webhook_url
}
```

---

## 🌐 監控能力

### 自動收集的數據

#### 請求追蹤
- ✅ HTTP 請求路徑、方法、狀態碼
- ✅ 請求/響應大小
- ✅ 處理時間
- ✅ 用戶代理

#### 依賴追蹤
- ✅ SQL 查詢（參數化）
- ✅ Redis 命令
- ✅ 外部 HTTP 調用
- ✅ 消息隊列操作

#### 異常追蹤
- ✅ 異常類型和堆棧
- ✅ 發生時間和頻率
- ✅ 影響的請求數

#### 性能指標
- ✅ 服務器響應時間
- ✅ 依賴調用時間
- ✅ CPU 和記憶體使用率
- ✅ 請求速率

### 自定義追蹤範例

```python
from src.core.telemetry import get_tracer, get_meter

tracer = get_tracer(__name__)
meter = get_meter(__name__)

# 自定義 Span
with tracer.start_as_current_span("process_workflow") as span:
    span.set_attribute("workflow.id", workflow_id)
    span.set_attribute("workflow.type", "automated")
    # 執行業務邏輯
    span.set_attribute("workflow.status", "success")

# 自定義指標
workflow_counter = meter.create_counter(
    name="workflow.executions.total",
    description="Total workflow executions"
)
workflow_counter.add(1, {"status": "success"})
```

---

## 📊 代碼統計

### 新增代碼量

| 類別 | 文件數 | 代碼行數 |
|------|--------|----------|
| OpenTelemetry | 2 | 189 |
| 健康檢查 | 2 | 273 |
| Terraform IaC | 2 | 315 |
| 配置更新 | 4 | ~30 |
| **總計** | **10** | **~807** |

### 文檔

| 類別 | 文件數 | 字數 (估計) |
|------|--------|--------------|
| 架構設計 | 1 | ~6,000 |
| 使用指南 | 1 | ~3,000 |
| 實現總結 | 1 | ~2,000 |
| **總計** | **3** | **~11,000** |

---

## 🧪 驗證方法

### 本地測試

```bash
# 1. 啟動應用
uvicorn main:app --reload

# 2. 測試健康檢查
curl http://localhost:8000/api/v1/health/
curl http://localhost:8000/api/v1/health/readiness
curl http://localhost:8000/api/v1/health/detailed

# 3. 驗證響應
# 應該返回 200 OK 和 JSON 響應
```

### Azure 部署後驗證

```bash
# 1. 檢查 Application Insights 連接
# Azure Portal → Application Insights → Live Metrics

# 2. 生成測試流量
for i in {1..10}; do
  curl https://your-app.azurewebsites.net/api/v1/health/
done

# 3. 查看追蹤數據
# Azure Portal → Application Insights → Transaction Search

# 4. 測試告警
# 觸發某個告警條件，檢查是否收到通知
```

---

## 🔄 與其他 Stories 的集成

### 依賴關係

| Story | 關係 | 說明 |
|-------|------|------|
| S0-2 (App Service) | ✅ 已完成 | 部署目標平台 |
| S0-4 (Database) | ✅ 已完成 | 健康檢查依賴 |
| S0-5 (Redis) | ✅ 已完成 | 健康檢查依賴 |
| S0-6 (Message Queue) | ✅ 已完成 | 健康檢查依賴 |

### 被依賴

| Story | 如何使用 | 說明 |
|-------|---------|------|
| S0-9 (App Insights Logging) | 日誌整合 | 使用相同的 App Insights 資源 |
| 所有未來 Stories | 監控和追蹤 | 自動收集性能數據 |

---

## 📝 使用範例

### Kubernetes 健康探針配置

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: backend
        livenessProbe:
          httpGet:
            path: /api/v1/health/liveness
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10

        readinessProbe:
          httpGet:
            path: /api/v1/health/readiness
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

### 自定義業務指標

```python
# 工作流執行監控
from src.core.telemetry import get_tracer, get_meter

class WorkflowService:
    def __init__(self):
        self.tracer = get_tracer(__name__)
        self.meter = get_meter(__name__)

        # 創建指標
        self.executions = self.meter.create_counter(
            "workflow.executions.total",
            description="Total workflow executions"
        )
        self.duration = self.meter.create_histogram(
            "workflow.duration",
            description="Workflow execution duration in ms"
        )

    async def execute(self, workflow_id: str):
        with self.tracer.start_as_current_span("execute_workflow") as span:
            span.set_attribute("workflow.id", workflow_id)

            start = time.time()
            try:
                result = await self._do_execute(workflow_id)
                duration_ms = (time.time() - start) * 1000

                # 記錄成功指標
                self.executions.add(1, {"status": "success"})
                self.duration.record(duration_ms, {"status": "success"})
                span.set_attribute("workflow.status", "success")

                return result

            except Exception as e:
                # 記錄失敗指標
                self.executions.add(1, {"status": "failed"})
                span.set_attribute("workflow.status", "failed")
                span.record_exception(e)
                raise
```

---

## 🚀 部署注意事項

### Terraform 部署

```bash
cd infrastructure/terraform

# 初始化
terraform init

# 規劃
terraform plan -var-file=environments/production.tfvars

# 應用（創建 App Insights + 告警）
terraform apply -var-file=environments/production.tfvars

# 獲取 Connection String
terraform output -raw appinsights_connection_string
```

### 環境變量配置

```bash
# 從 Terraform 輸出複製連接字符串
export APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=xxx..."

# 生產環境採樣配置
export OTEL_TRACES_SAMPLER=traceidratio
export OTEL_TRACES_SAMPLER_ARG=0.2

# 可選：啟用 Prometheus
export PROMETHEUS_ENABLED=true
```

### Azure App Service 配置

```bash
# 通過 Azure CLI 配置
az webapp config appsettings set \
  --name ai-framework-backend-prod \
  --resource-group ai-framework-rg \
  --settings \
    APPLICATIONINSIGHTS_CONNECTION_STRING="$CONN_STRING" \
    OTEL_SERVICE_NAME=ai-framework-backend \
    OTEL_TRACES_SAMPLER=traceidratio \
    OTEL_TRACES_SAMPLER_ARG=0.2
```

---

## 🎯 成本優化

### 預估成本（生產環境）

- **Application Insights**: ~$50-100/月
  - 採樣率 20% = 大幅降低成本
  - 資料保留 90 天
  - 預估 1M 請求/月

- **Log Analytics**: ~$20-40/月
  - 基於數據攝入量
  - 90 天保留

- **告警**: ~$0.10/告警/月

**總計**: ~$70-150/月

### 成本控制建議

1. ✅ 調整採樣率（生產環境 20%）
2. ✅ 設置適當的保留期限
3. ✅ 排除健康檢查端點
4. ✅ 使用 Workspace 模式（更經濟）

---

## 📖 相關文檔

- [監控架構設計](./monitoring-design.md)
- [監控使用指南](../04-usage/monitoring-guide.md)
- [Sprint Status](./sprint-status.yaml)
- [Azure Monitor 文檔](https://docs.microsoft.com/azure/azure-monitor/)
- [OpenTelemetry 文檔](https://opentelemetry.io/docs/)

---

## ✅ 驗收標準

| 標準 | 狀態 | 說明 |
|------|------|------|
| Application Insights 整合 | ✅ | 自動追蹤請求、依賴、異常 |
| OpenTelemetry SDK 配置 | ✅ | 完整自動檢測 |
| 健康檢查端點 | ✅ | 4 個端點（/、liveness、readiness、detailed） |
| Terraform 配置 | ✅ | App Insights + 8 個告警規則 |
| 自定義追蹤 API | ✅ | get_tracer + get_meter |
| 監控文檔 | ✅ | 架構設計 + 使用指南 |
| 成本優化 | ✅ | 採樣策略 + 排除健康檢查 |

---

**狀態**: ✅ **已完成**
**完成時間**: 2025-11-20
**總代碼量**: ~807 行
**總文檔量**: ~11,000 字

---

**下一步**: S0-9 (Application Insights Logging) - 3 points
**備註**: S0-9 可能已包含在 S0-8 中，因為 Application Insights 已經自動收集日誌。S0-9 可能只需要添加配置和文檔。
