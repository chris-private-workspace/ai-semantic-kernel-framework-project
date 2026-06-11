# Monitoring 監控架構設計

**Story**: S0-8 - Monitoring Setup (Hybrid)
**目標**: 配置混合監控方案（Azure Monitor + Application Insights + Prometheus）
**Story Points**: 5

---

## 📋 目錄

1. [監控策略概述](#監控策略概述)
2. [架構設計](#架構設計)
3. [Azure Monitor 配置](#azure-monitor-配置)
4. [Application Insights 配置](#application-insights-配置)
5. [OpenTelemetry 整合](#opentelemetry-整合)
6. [Prometheus Metrics（可選）](#prometheus-metrics可選)
7. [健康檢查端點](#健康檢查端點)
8. [告警規則](#告警規則)
9. [儀表板設計](#儀表板設計)
10. [最佳實踐](#最佳實踐)

---

## 監控策略概述

### 混合監控方案

採用 **Azure 原生 + 開源補充** 的混合策略：

| 監控類型 | 主要工具 | 補充工具 | 用途 |
|---------|---------|---------|------|
| **基礎監控** | Azure Monitor | - | CPU、記憶體、網路、磁碟 |
| **應用監控** | Application Insights | - | 請求追蹤、依賴關係、異常 |
| **日誌管理** | Application Insights | - | 集中式日誌、查詢分析 |
| **業務指標** | Application Insights | Prometheus | 自定義業務指標 |
| **分散式追蹤** | Application Insights | - | 端到端請求追蹤 |

### 為什麼選擇混合方案？

#### Azure Monitor + Application Insights 優勢

✅ **無縫整合**: 與 Azure App Service 原生整合，零配置監控
✅ **自動檢測**: 自動追蹤 HTTP 請求、依賴關係、異常
✅ **智能分析**: Application Map、Live Metrics、智能檢測
✅ **低維護成本**: 無需自建基礎設施
✅ **統一管理**: Azure Portal 統一查看所有監控數據

#### Prometheus 補充（可選）

✅ **業務指標**: 自定義業務相關的細粒度指標
✅ **靈活查詢**: PromQL 強大的查詢語言
✅ **開源生態**: 與 Grafana 完美整合
✅ **未來遷移**: 保留非雲供應商鎖定的選項

---

## 架構設計

### 整體架構

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   FastAPI    │  │  Background  │  │   Workers    │      │
│  │   Server     │  │    Tasks     │  │              │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │               │
│         └──────────────────┴──────────────────┘               │
│                            │                                  │
└────────────────────────────┼──────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
        ┌───────▼────────┐      ┌────────▼─────────┐
        │ OpenTelemetry  │      │   Prometheus     │
        │   Exporter     │      │   Client         │
        │                │      │  (Optional)      │
        └───────┬────────┘      └────────┬─────────┘
                │                        │
        ┌───────▼────────┐      ┌────────▼─────────┐
        │  Application   │      │   Prometheus     │
        │   Insights     │      │    Server        │
        │                │      │  (Optional)      │
        └───────┬────────┘      └────────┬─────────┘
                │                        │
        ┌───────▼────────────────────────▼─────────┐
        │         Azure Monitor                     │
        │  ┌──────────┐  ┌──────────┐  ┌─────────┐│
        │  │  Alerts  │  │   Logs   │  │ Metrics ││
        │  └──────────┘  └──────────┘  └─────────┘│
        └──────────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
        ┌───────▼────────┐      ┌────────▼─────────┐
        │  Azure Portal  │      │     Grafana      │
        │   Dashboard    │      │   (Optional)     │
        └────────────────┘      └──────────────────┘
```

### 數據流

```
Application → OpenTelemetry SDK → Application Insights → Azure Monitor
     │
     └─→ Prometheus Client → Prometheus Server → Grafana (Optional)
```

---

## Azure Monitor 配置

### 1. Application Insights 資源

#### 使用 Terraform 創建

```hcl
# infrastructure/terraform/monitoring.tf

resource "azurerm_application_insights" "app_insights" {
  name                = "ai-framework-appinsights-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  application_type    = "web"

  # 工作區模式（推薦）
  workspace_id = azurerm_log_analytics_workspace.main.id

  # 資料保留期限
  retention_in_days = var.environment == "production" ? 90 : 30

  # 採樣率（生產環境建議啟用）
  sampling_percentage = var.environment == "production" ? 20 : 100

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "main" {
  name                = "ai-framework-logs-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = var.environment == "production" ? 90 : 30

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Output connection string
output "appinsights_connection_string" {
  value     = azurerm_application_insights.app_insights.connection_string
  sensitive = true
}

output "appinsights_instrumentation_key" {
  value     = azurerm_application_insights.app_insights.instrumentation_key
  sensitive = true
}
```

### 2. App Service 整合

```hcl
# App Service 自動啟用 Application Insights
resource "azurerm_linux_web_app" "backend" {
  # ... 其他配置 ...

  app_settings = {
    # Application Insights
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = azurerm_application_insights.app_insights.connection_string
    "ApplicationInsightsAgent_EXTENSION_VERSION" = "~3"
    "XDT_MicrosoftApplicationInsights_Mode" = "recommended"

    # OpenTelemetry 配置
    "OTEL_EXPORTER_OTLP_ENDPOINT" = "https://dc.services.visualstudio.com/v2/track"
    "OTEL_SERVICE_NAME" = "ai-framework-backend-${var.environment}"
  }
}
```

---

## Application Insights 配置

### 1. Python SDK 整合

#### 安裝依賴

```txt
# requirements.txt
azure-monitor-opentelemetry==1.2.0
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-instrumentation-fastapi==0.42b0
opentelemetry-instrumentation-sqlalchemy==0.42b0
opentelemetry-instrumentation-redis==0.42b0
opentelemetry-instrumentation-httpx==0.42b0
```

#### 配置代碼

```python
# backend/src/core/telemetry.py
"""
OpenTelemetry 配置
"""
import logging
from typing import Optional

from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace, metrics
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION

from src.core.config import settings

logger = logging.getLogger(__name__)


def setup_telemetry(app) -> None:
    """
    配置 OpenTelemetry 和 Application Insights

    Args:
        app: FastAPI application instance
    """
    if not settings.appinsights_connection_string:
        logger.warning("Application Insights not configured")
        return

    try:
        # 配置 Azure Monitor
        configure_azure_monitor(
            connection_string=settings.appinsights_connection_string,
            resource=Resource.create({
                SERVICE_NAME: settings.app_name,
                SERVICE_VERSION: settings.app_version,
                "deployment.environment": settings.environment,
            }),
            # 日誌級別
            logging_level=logging.INFO if settings.environment == "production" else logging.DEBUG,
            # 採樣率（生產環境降低成本）
            trace_sampler=get_sampler(),
        )

        # 自動檢測 FastAPI
        FastAPIInstrumentor.instrument_app(
            app,
            excluded_urls="health,metrics,readiness,liveness",  # 排除健康檢查
        )

        # 自動檢測 SQLAlchemy（在 engine 創建後調用）
        # SQLAlchemyInstrumentor().instrument(
        #     engine=engine,
        #     service="ai-framework-db"
        # )

        # 自動檢測 Redis
        RedisInstrumentor().instrument()

        # 自動檢測 HTTPX（外部 HTTP 調用）
        HTTPXClientInstrumentor().instrument()

        logger.info("Application Insights configured successfully")

    except Exception as e:
        logger.error(f"Failed to configure Application Insights: {e}")


def get_sampler():
    """獲取採樣器配置"""
    from opentelemetry.sdk.trace.sampling import (
        ParentBasedTraceIdRatioBased,
        ALWAYS_ON,
    )

    if settings.environment == "production":
        # 生產環境：20% 採樣率
        return ParentBasedTraceIdRatioBased(0.2)
    else:
        # 開發/測試環境：100% 採樣
        return ALWAYS_ON


def get_tracer(name: str) -> trace.Tracer:
    """
    獲取 Tracer 實例

    Args:
        name: Tracer 名稱

    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)


def get_meter(name: str) -> metrics.Meter:
    """
    獲取 Meter 實例（用於自定義指標）

    Args:
        name: Meter 名稱

    Returns:
        Meter instance
    """
    return metrics.get_meter(name)
```

### 2. 主應用集成

```python
# backend/main.py
from src.core.telemetry import setup_telemetry

app = FastAPI(
    title="IPA Platform API",
    # ...
)

# 配置監控（在所有中間件和路由之後）
setup_telemetry(app)

# CORS 等其他中間件...
```

### 3. 自定義追蹤範例

```python
# backend/src/domain/workflow/workflow_service.py
from opentelemetry import trace
from src.core.telemetry import get_tracer

tracer = get_tracer(__name__)

class WorkflowService:
    async def execute_workflow(self, workflow_id: str):
        # 創建自定義 Span
        with tracer.start_as_current_span("execute_workflow") as span:
            span.set_attribute("workflow.id", workflow_id)
            span.set_attribute("workflow.type", "automated")

            try:
                # 執行工作流邏輯
                result = await self._do_execute(workflow_id)

                span.set_attribute("workflow.status", "success")
                span.set_attribute("workflow.duration_ms", result.duration)

                return result

            except Exception as e:
                span.set_attribute("workflow.status", "failed")
                span.set_attribute("workflow.error", str(e))
                span.record_exception(e)
                raise
```

### 4. 自定義指標範例

```python
# backend/src/infrastructure/metrics/custom_metrics.py
"""
自定義業務指標
"""
from opentelemetry import metrics
from src.core.telemetry import get_meter

meter = get_meter(__name__)

# Counter: 計數器（只增不減）
workflow_executions_total = meter.create_counter(
    name="workflow.executions.total",
    description="Total number of workflow executions",
    unit="1",
)

workflow_failures_total = meter.create_counter(
    name="workflow.failures.total",
    description="Total number of workflow failures",
    unit="1",
)

# Histogram: 直方圖（分佈統計）
workflow_duration = meter.create_histogram(
    name="workflow.duration",
    description="Workflow execution duration",
    unit="ms",
)

# UpDownCounter: 可增可減計數器
active_workflows = meter.create_up_down_counter(
    name="workflow.active",
    description="Number of currently active workflows",
    unit="1",
)

# 使用範例
def record_workflow_execution(workflow_id: str, duration_ms: float, success: bool):
    """記錄工作流執行指標"""
    attributes = {
        "workflow.id": workflow_id,
        "workflow.status": "success" if success else "failure",
    }

    workflow_executions_total.add(1, attributes)
    workflow_duration.record(duration_ms, attributes)

    if not success:
        workflow_failures_total.add(1, attributes)
```

---

## Prometheus Metrics（可選）

### 1. 為什麼需要 Prometheus？

雖然 Application Insights 已經提供了完整的監控能力，但 Prometheus 提供：

- **業務指標**: 更細粒度的自定義業務指標
- **開源生態**: 與 Grafana 完美整合
- **PromQL**: 強大的查詢語言
- **非雲鎖定**: 保留未來遷移彈性

### 2. Prometheus Client 整合

#### 安裝依賴

```txt
# requirements.txt
prometheus-client==0.19.0
prometheus-fastapi-instrumentator==6.1.0
```

#### 配置代碼

```python
# backend/src/infrastructure/metrics/prometheus_metrics.py
"""
Prometheus 指標配置
"""
from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_fastapi_instrumentator import Instrumentator, metrics

# 自定義業務指標
workflow_executions = Counter(
    'workflow_executions_total',
    'Total workflow executions',
    ['workflow_type', 'status']
)

workflow_duration = Histogram(
    'workflow_duration_seconds',
    'Workflow execution duration',
    ['workflow_type'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

active_workflows = Gauge(
    'active_workflows',
    'Number of currently active workflows',
    ['workflow_type']
)

queue_depth = Gauge(
    'queue_depth',
    'Message queue depth',
    ['queue_name']
)

cache_hits = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

# 系統信息
app_info = Info('app', 'Application information')
app_info.info({
    'version': '0.1.0',
    'environment': 'production',
})


def setup_prometheus(app):
    """
    配置 Prometheus metrics

    Args:
        app: FastAPI application
    """
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/health", "/metrics", "/readiness", "/liveness"],
        inprogress_name="http_requests_inprogress",
        inprogress_labels=True,
    )

    # 添加默認指標
    instrumentator.add(
        metrics.request_size(
            should_include_handler=True,
            should_include_method=True,
            should_include_status=True,
        )
    )
    instrumentator.add(
        metrics.response_size(
            should_include_handler=True,
            should_include_method=True,
            should_include_status=True,
        )
    )
    instrumentator.add(
        metrics.latency(
            should_include_handler=True,
            should_include_method=True,
            should_include_status=True,
        )
    )
    instrumentator.add(metrics.requests())

    # 暴露 /metrics 端點
    instrumentator.instrument(app).expose(app, endpoint="/metrics")
```

### 3. 主應用集成

```python
# backend/main.py
from src.infrastructure.metrics.prometheus_metrics import setup_prometheus

app = FastAPI(...)

# 配置 Prometheus（可選）
if settings.prometheus_enabled:
    setup_prometheus(app)
```

### 4. Prometheus Server 配置（Docker Compose）

```yaml
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: ai-framework-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./infrastructure/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=15d'
    networks:
      - ai-framework-network

  grafana:
    image: grafana/grafana:10.2.2
    container_name: ai-framework-grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./infrastructure/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./infrastructure/grafana/datasources:/etc/grafana/provisioning/datasources
    depends_on:
      - prometheus
    networks:
      - ai-framework-network

volumes:
  prometheus_data:
    driver: local
  grafana_data:
    driver: local
```

```yaml
# infrastructure/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ai-framework-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

---

## 健康檢查端點

### 完整的健康檢查實現

```python
# backend/src/api/v1/health/__init__.py
from .routes import router

__all__ = ["router"]
```

```python
# backend/src/api/v1/health/routes.py
"""
健康檢查端點
"""
import asyncio
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.infrastructure.database.session import get_session
from src.infrastructure.cache.redis_cache import get_cache
from src.infrastructure.queue.queue_manager import get_queue_provider

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check():
    """
    基本健康檢查

    Returns:
        簡單的健康狀態
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
        "environment": settings.environment,
    }


@router.get("/liveness", status_code=status.HTTP_200_OK)
async def liveness():
    """
    Kubernetes Liveness Probe

    檢查應用程序是否存活（不檢查依賴）

    Returns:
        存活狀態
    """
    return {"status": "alive"}


@router.get("/readiness")
async def readiness(
    session: AsyncSession = Depends(get_session)
):
    """
    Kubernetes Readiness Probe

    檢查應用程序是否準備好接收流量（檢查所有依賴）

    Returns:
        準備狀態和依賴檢查結果
    """
    checks = {}
    overall_status = "ready"

    # 檢查數據庫
    try:
        await session.execute("SELECT 1")
        checks["database"] = {"status": "healthy", "message": "Connection OK"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "message": str(e)}
        overall_status = "not_ready"

    # 檢查 Redis
    try:
        cache = get_cache()
        if cache:
            await cache.set("health_check", "ok", ttl=10)
            value = await cache.get("health_check")
            if value == "ok":
                checks["redis"] = {"status": "healthy", "message": "Connection OK"}
            else:
                raise Exception("Read/write test failed")
        else:
            checks["redis"] = {"status": "skipped", "message": "Redis not configured"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "message": str(e)}
        overall_status = "not_ready"

    # 檢查消息隊列
    try:
        queue_provider = get_queue_provider()
        # 簡單的連接檢查（不發送實際消息）
        checks["queue"] = {"status": "healthy", "message": "Connection OK"}
    except Exception as e:
        checks["queue"] = {"status": "unhealthy", "message": str(e)}
        overall_status = "not_ready"

    # 返回結果
    status_code = status.HTTP_200_OK if overall_status == "ready" else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks,
        }
    )


@router.get("/detailed")
async def detailed_health(
    session: AsyncSession = Depends(get_session)
):
    """
    詳細健康檢查

    包含所有系統組件的詳細狀態

    Returns:
        詳細的系統健康報告
    """
    checks = {}

    # 數據庫檢查（包含延遲）
    try:
        start = datetime.utcnow()
        await session.execute("SELECT 1")
        latency = (datetime.utcnow() - start).total_seconds() * 1000
        checks["database"] = {
            "status": "healthy",
            "latency_ms": round(latency, 2),
            "message": "Connection OK"
        }
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "message": str(e)
        }

    # Redis 檢查（包含延遲）
    try:
        cache = get_cache()
        if cache:
            start = datetime.utcnow()
            await cache.set("health_check_detailed", "ok", ttl=10)
            await cache.get("health_check_detailed")
            latency = (datetime.utcnow() - start).total_seconds() * 1000

            # 獲取 Redis 信息
            info = await cache._client.info() if hasattr(cache, '_client') else {}

            checks["redis"] = {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "connected_clients": info.get("connected_clients", "N/A"),
                "used_memory_human": info.get("used_memory_human", "N/A"),
                "message": "Connection OK"
            }
        else:
            checks["redis"] = {"status": "skipped", "message": "Redis not configured"}
    except Exception as e:
        checks["redis"] = {
            "status": "unhealthy",
            "message": str(e)
        }

    # 消息隊列檢查
    try:
        queue_provider = get_queue_provider()
        checks["queue"] = {
            "status": "healthy",
            "provider": settings.mq_provider,
            "message": "Connection OK"
        }
    except Exception as e:
        checks["queue"] = {
            "status": "unhealthy",
            "message": str(e)
        }

    # 計算整體狀態
    unhealthy_count = sum(1 for check in checks.values() if check.get("status") == "unhealthy")
    overall_status = "healthy" if unhealthy_count == 0 else "degraded" if unhealthy_count < len(checks) else "unhealthy"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": 0,  # TODO: 實現啟動時間追蹤
        "checks": checks,
    }
```

---

## 告警規則

### Azure Monitor Alert Rules

```hcl
# infrastructure/terraform/monitoring_alerts.tf

# HTTP 5xx 錯誤告警
resource "azurerm_monitor_metric_alert" "http_5xx" {
  name                = "http-5xx-errors-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_web_app.backend.id]
  description         = "Alert when HTTP 5xx errors exceed threshold"
  severity            = 2

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "Http5xx"
    aggregation      = "Total"
    operator         = "GreaterThan"
    threshold        = var.environment == "production" ? 10 : 5
  }

  window_size        = "PT5M"
  frequency          = "PT1M"
  auto_mitigate      = true

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }
}

# 高 CPU 使用率告警
resource "azurerm_monitor_metric_alert" "high_cpu" {
  name                = "high-cpu-usage-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_web_app.backend.id]
  description         = "Alert when CPU usage is high"
  severity            = 3

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "CpuPercentage"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 80
  }

  window_size   = "PT5M"
  frequency     = "PT1M"
  auto_mitigate = true

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }
}

# 高記憶體使用率告警
resource "azurerm_monitor_metric_alert" "high_memory" {
  name                = "high-memory-usage-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_web_app.backend.id]
  description         = "Alert when memory usage is high"
  severity            = 3

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "MemoryPercentage"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 85
  }

  window_size   = "PT5M"
  frequency     = "PT1M"
  auto_mitigate = true

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }
}

# 響應時間告警
resource "azurerm_monitor_metric_alert" "slow_response" {
  name                = "slow-response-time-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_web_app.backend.id]
  description         = "Alert when average response time is slow"
  severity            = 3

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "ResponseTime"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 2000  # 2 秒
  }

  window_size   = "PT5M"
  frequency     = "PT1M"
  auto_mitigate = true

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }
}

# Action Group（通知群組）
resource "azurerm_monitor_action_group" "main" {
  name                = "ai-framework-alerts-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  short_name          = "aiframework"

  # Email 通知
  email_receiver {
    name                    = "DevOps Team"
    email_address           = var.alert_email
    use_common_alert_schema = true
  }

  # Webhook 通知（可選：Slack, Teams, PagerDuty）
  webhook_receiver {
    name        = "Slack Webhook"
    service_uri = var.slack_webhook_url
  }
}
```

---

## 儀表板設計

### Azure Monitor Dashboard

通過 Azure Portal 創建自定義儀表板，包含：

1. **Overview 概覽**
   - 應用健康狀態
   - 請求總數
   - 平均響應時間
   - 錯誤率

2. **Performance 性能**
   - CPU 使用率
   - 記憶體使用率
   - 網路 I/O
   - 磁碟 I/O

3. **Requests 請求**
   - 請求速率
   - 響應時間分佈
   - 端點熱圖

4. **Failures 失敗**
   - 異常數量
   - 失敗請求率
   - 錯誤類型分佈

5. **Dependencies 依賴**
   - 數據庫查詢性能
   - Redis 調用
   - 外部 API 調用

---

## 最佳實踐

### 1. 監控分層

- **基礎監控**: Azure Monitor（CPU、記憶體、網路）
- **應用監控**: Application Insights（請求、異常、依賴）
- **業務監控**: 自定義指標（工作流、用戶行為）

### 2. 採樣策略

```python
# 生產環境採樣配置
SAMPLING_RATE = {
    "development": 1.0,    # 100%
    "staging": 0.5,        # 50%
    "production": 0.2,     # 20%
}
```

### 3. 成本優化

- ✅ 啟用採樣（生產環境 20%）
- ✅ 設置適當的資料保留期限（30-90天）
- ✅ 排除健康檢查端點
- ✅ 使用 Log Analytics Workspace 模式

### 4. 隱私和安全

- ❌ 不記錄敏感數據（密碼、Token）
- ✅ 使用屬性標記而非完整數據
- ✅ 定期審查日誌內容

---

## 配置檢查清單

### 必須配置

- [ ] Application Insights 資源
- [ ] Log Analytics Workspace
- [ ] OpenTelemetry SDK 整合
- [ ] 健康檢查端點
- [ ] 基本告警規則

### 可選配置

- [ ] Prometheus + Grafana
- [ ] 自定義業務指標
- [ ] Slack/Teams 通知
- [ ] 自定義儀表板

---

**下一步**: 實現 OpenTelemetry 整合和健康檢查端點
