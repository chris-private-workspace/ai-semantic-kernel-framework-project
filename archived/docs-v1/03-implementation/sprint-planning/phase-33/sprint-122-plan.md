# Sprint 122: Azure 部署 + 可觀測性

## 概述

Sprint 122 將平台部署到 Azure App Service，並建立完整的可觀測性基礎設施。包含 OpenTelemetry 整合 Azure Monitor、結構化日誌替換、以及 X-Request-ID 全鏈路追蹤。

## 目標

1. 成功部署 Backend 到 Azure App Service B2 tier
2. 整合 OpenTelemetry + Azure Monitor / Application Insights
3. 替換非結構化日誌為 JSON 結構化日誌 + X-Request-ID 追蹤

## Story Points: 45 點

## 前置條件

- ⬜ Sprint 121 完成（Dockerfile + CI/CD Pipeline 就緒）
- ⬜ Azure 訂閱可用
- ⬜ Azure Resource Group 已建立
- ⬜ Azure Container Registry (ACR) 已配置
- ⬜ Azure Database for PostgreSQL 已建立
- ⬜ Azure Cache for Redis 已建立

## 任務分解

### Story 122-1: Azure App Service 部署 (3 天, P0)

**目標**: 將 Backend 部署到 Azure App Service B2 tier，配置環境變量、Managed Identity 和網路設定

**交付物**:
- Azure App Service 配置腳本 / ARM template / Bicep
- 環境變量配置文件
- 部署驗證文件

**部署架構**:

```
Azure Resource Group: rg-ipa-platform
├── App Service Plan (B2): asp-ipa-backend
│   └── Web App: app-ipa-backend
│       ├── Container: backend Docker image from ACR
│       ├── Environment Variables: DB, Redis, LLM keys
│       └── Managed Identity: for Azure resources access
├── App Service Plan (B1): asp-ipa-frontend
│   └── Web App: app-ipa-frontend
│       └── Container: frontend Docker image from ACR
├── Azure Database for PostgreSQL (Flexible, B1ms)
│   └── Database: ipa_platform
├── Azure Cache for Redis (Basic C0)
├── Azure Container Registry: acripa
├── Application Insights: appi-ipa
└── Virtual Network (optional, for private endpoints)
```

**配置項目**:

| 配置類別 | 項目 | 值 |
|---------|------|---|
| App Service | SKU | B2 (2 vCPU, 3.5 GB RAM) |
| App Service | Container Source | Azure Container Registry |
| App Service | Always On | Enabled |
| App Service | HTTPS Only | Enabled |
| Environment | ENVIRONMENT | production |
| Environment | DB_HOST | PostgreSQL FQDN |
| Environment | DB_NAME | ipa_platform |
| Environment | REDIS_HOST | Redis FQDN |
| Environment | AZURE_OPENAI_ENDPOINT | 從 Key Vault 或 App Settings |
| Networking | CORS | frontend App Service URL |
| Security | Managed Identity | System-assigned |

**驗收標準**:
- [ ] Backend App Service 成功啟動，health check 通過
- [ ] Frontend App Service 成功啟動，可訪問 SPA
- [ ] Backend 可連接 Azure Database for PostgreSQL
- [ ] Backend 可連接 Azure Cache for Redis
- [ ] HTTPS 強制啟用
- [ ] CORS 配置正確（僅允許 frontend URL）
- [ ] 環境變量不包含明文密鑰（使用 Key Vault 或 App Settings）
- [ ] CI/CD Pipeline 可自動部署到 App Service
- [ ] 基本功能驗證通過（API 呼叫、Agent 對話）

### Story 122-2: OpenTelemetry + Azure Monitor 整合 (3 天, P1)

**目標**: 使用 OpenTelemetry 為 Backend 添加分散式追蹤、指標和日誌，連接 Azure Monitor / Application Insights

**交付物**:
- `backend/src/core/observability/` 模組
- OpenTelemetry 配置
- Azure Monitor exporter 配置
- 自定義 metrics 和 spans

**整合架構**:

```
Backend (FastAPI)
├── OTel SDK
│   ├── TracerProvider → AzureMonitorTraceExporter
│   ├── MeterProvider → AzureMonitorMetricExporter
│   └── LoggerProvider → AzureMonitorLogExporter
├── Auto-Instrumentation
│   ├── FastAPI (HTTP requests)
│   ├── httpx/aiohttp (outgoing HTTP)
│   ├── redis (cache operations)
│   └── psycopg2/asyncpg (database)
└── Custom Instrumentation
    ├── Agent execution spans
    ├── LLM call spans (with token metrics)
    ├── MCP tool call spans
    └── Business metrics (latency, throughput)
```

**關鍵 Metrics**:

| Metric 名稱 | 類型 | 說明 |
|------------|------|------|
| `agent.execution.duration` | Histogram | Agent 執行耗時 |
| `agent.execution.count` | Counter | Agent 執行次數 |
| `llm.call.duration` | Histogram | LLM API 呼叫耗時 |
| `llm.tokens.used` | Counter | Token 使用量 |
| `mcp.tool.call.duration` | Histogram | MCP 工具調用耗時 |
| `api.request.duration` | Histogram | API 請求耗時 |
| `api.request.error_rate` | Counter | API 錯誤率 |

**實現方式**:

```python
# backend/src/core/observability/setup.py
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from azure.monitor.opentelemetry.exporter import (
    AzureMonitorTraceExporter,
    AzureMonitorMetricExporter,
)

def setup_observability(connection_string: str):
    """初始化 OpenTelemetry + Azure Monitor"""

    # Traces
    trace_exporter = AzureMonitorTraceExporter(
        connection_string=connection_string
    )
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(
        BatchSpanProcessor(trace_exporter)
    )
    trace.set_tracer_provider(tracer_provider)

    # Metrics
    metric_exporter = AzureMonitorMetricExporter(
        connection_string=connection_string
    )
    meter_provider = MeterProvider(
        metric_readers=[PeriodicExportingMetricReader(metric_exporter)]
    )
    metrics.set_meter_provider(meter_provider)
```

**驗收標準**:
- [ ] OpenTelemetry SDK 初始化成功
- [ ] FastAPI 請求自動生成 trace spans
- [ ] Database / Redis 操作自動追蹤
- [ ] 自定義 Agent execution span 正常記錄
- [ ] LLM call metrics 正常記錄（duration、tokens）
- [ ] Azure Application Insights 中可看到 traces
- [ ] Azure Application Insights 中可看到 metrics
- [ ] Application Map 正確顯示服務依賴關係
- [ ] 性能影響 < 5%（OTel overhead）

### Story 122-3: 結構化日誌 + Request ID 追蹤 (2 天, P1)

**目標**: 替換非結構化 print/logging 為 JSON 結構化日誌，添加 X-Request-ID header 全鏈路追蹤

**交付物**:
- `backend/src/core/logging/` 模組
- FastAPI middleware（Request ID 注入）
- 日誌格式化器配置

**結構化日誌格式**:

```json
{
  "timestamp": "2026-02-21T10:30:45.123Z",
  "level": "INFO",
  "logger": "ipa.api.agents",
  "message": "Agent execution completed",
  "request_id": "req-abc123",
  "user_id": "user-def456",
  "agent_id": "agent-ghi789",
  "duration_ms": 1250,
  "extra": {
    "tokens_used": 350,
    "tool_calls": 2
  }
}
```

**Request ID 追蹤流程**:

```
Client Request
    ↓ (X-Request-ID header, or auto-generate UUID)
FastAPI Middleware
    ↓ (inject request_id into context)
API Handler
    ↓ (request_id in all log messages)
Service Layer
    ↓ (request_id propagated)
Integration Layer (LLM, MCP, etc.)
    ↓ (request_id in outgoing headers)
Response
    ↓ (X-Request-ID in response header)
Client
```

**實現方式**:

```python
# Request ID Middleware
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="")

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_var.set(request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


# Structured Logger
import structlog

def setup_logging():
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
    )
```

**驗收標準**:
- [ ] 所有 API 請求自動帶有 X-Request-ID（client 提供或自動生成）
- [ ] Response header 包含 X-Request-ID
- [ ] 所有日誌輸出為 JSON 格式
- [ ] 日誌中包含 request_id 欄位
- [ ] 日誌中包含 timestamp、level、logger、message 基本欄位
- [ ] 替換所有 `print()` 語句為 structlog 呼叫
- [ ] 替換所有 `logging.info()` 為 structlog 呼叫
- [ ] 敏感資訊不出現在日誌中（密碼、token 等）
- [ ] OTel trace_id 與 request_id 關聯

## 技術設計

### 新增目錄結構

```
backend/src/core/
├── observability/
│   ├── __init__.py
│   ├── setup.py           # OTel 初始化
│   ├── spans.py            # 自定義 span helpers
│   └── metrics.py          # 自定義 metrics
└── logging/
    ├── __init__.py
    ├── setup.py            # structlog 配置
    ├── middleware.py        # RequestIdMiddleware
    └── filters.py          # 敏感資訊過濾器
```

## 依賴

```
# OpenTelemetry
opentelemetry-api>=1.20
opentelemetry-sdk>=1.20
opentelemetry-instrumentation-fastapi>=0.40
opentelemetry-instrumentation-httpx>=0.40
opentelemetry-instrumentation-redis>=0.40
opentelemetry-instrumentation-psycopg2>=0.40

# Azure Monitor
azure-monitor-opentelemetry-exporter>=1.0

# Structured Logging
structlog>=23.0
```

## 風險

| 風險 | 緩解措施 |
|------|----------|
| Azure 資源建立權限不足 | 提前確認訂閱權限，準備 ARM template |
| OTel overhead 影響性能 | 使用 sampling（如 50% sampling rate） |
| 結構化日誌替換遺漏 | grep 掃描 `print(` 和 `logging.` 確保全面替換 |
| Application Insights 成本 | 設定 daily cap，使用 sampling |
| 部署後功能異常 | staging slot 先行驗證，確認後 swap to production |

## 完成標準

- [ ] Backend + Frontend 成功部署到 Azure App Service
- [ ] OpenTelemetry traces/metrics 在 Application Insights 中可見
- [ ] 結構化 JSON 日誌 + X-Request-ID 全鏈路追蹤
- [ ] 所有服務互連正常（App Service ↔ PostgreSQL ↔ Redis）
- [ ] CI/CD 可自動部署

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 45
**開始日期**: 待定
