# Sprint 122 Execution Log

## Sprint Overview

| Attribute | Value |
|-----------|-------|
| **Sprint** | 122 |
| **Phase** | 33 — Production Hardening |
| **Story Points** | 45 |
| **Start Date** | 2026-02-24 |
| **Status** | Executing |

## Goals

1. **Story 122-1**: Azure App Service 部署 (Bicep IaC + CI/CD 更新)
2. **Story 122-2**: OpenTelemetry + Azure Monitor 整合 (observability module)
3. **Story 122-3**: 結構化日誌 + X-Request-ID 全鏈路追蹤 (logging module)

## Story 122-1: Azure App Service Deployment

### Azure Resource Architecture

```
Azure Resource Group: rg-ipa-platform
├── App Service Plan (B2): asp-ipa-backend
│   └── Web App: app-ipa-backend (Docker from ACR)
├── App Service Plan (B1): asp-ipa-frontend
│   └── Web App: app-ipa-frontend (Docker from ACR)
├── Azure Database for PostgreSQL Flexible (B1ms)
├── Azure Cache for Redis (Basic C0)
├── Azure Container Registry: acripa
├── Application Insights: appi-ipa
└── Log Analytics Workspace: law-ipa
```

### New Files

- `infra/main.bicep` — Orchestrator Bicep template
- `infra/modules/app-service.bicep` — App Service module
- `infra/modules/database.bicep` — PostgreSQL Flexible Server module
- `infra/modules/redis.bicep` — Redis Cache module
- `infra/modules/monitoring.bicep` — Application Insights + Log Analytics
- `infra/modules/container-registry.bicep` — ACR module
- `infra/parameters/production.bicepparam` — Production parameters
- `infra/deploy.sh` — Deployment script

### CI/CD Updates

- `.github/workflows/deploy-production.yml` — Add frontend staging slot deploy + health check

## Story 122-2: OpenTelemetry + Azure Monitor

### New Module: `backend/src/core/observability/`

- `__init__.py` — Module exports
- `setup.py` — OTel SDK initialization + Azure Monitor exporters
- `spans.py` — Custom span helpers (agent, LLM, MCP, orchestration)
- `metrics.py` — Custom metrics (7 business metrics)

### Auto-Instrumentation

| Target | Package | Traces |
|--------|---------|--------|
| FastAPI | opentelemetry-instrumentation-fastapi | HTTP requests |
| httpx | opentelemetry-instrumentation-httpx | Outgoing HTTP |
| Redis | opentelemetry-instrumentation-redis | Cache ops |
| asyncpg | opentelemetry-instrumentation-asyncpg | DB ops |

### Custom Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `agent.execution.duration` | Histogram | Agent execution time |
| `agent.execution.count` | Counter | Agent execution count |
| `llm.call.duration` | Histogram | LLM API call time |
| `llm.tokens.used` | Counter | Token usage |
| `mcp.tool.call.duration` | Histogram | MCP tool call time |
| `api.request.duration` | Histogram | API request time |
| `api.request.error_rate` | Counter | API error count |

## Story 122-3: Structured Logging + Request ID

### New Module: `backend/src/core/logging/`

- `__init__.py` — Module exports
- `setup.py` — structlog configuration (JSON output)
- `middleware.py` — RequestIdMiddleware (X-Request-ID)
- `filters.py` — Sensitive information filter

### Request ID Flow

```
Client → X-Request-ID header (or auto-generated UUID)
  → RequestIdMiddleware → ContextVar
    → All log messages include request_id
      → Response header: X-Request-ID
```

### Key Design Decisions

- Use `contextvars.ContextVar` for request-scoped request_id propagation
- structlog with JSON renderer for machine-parseable logs
- OTel trace_id correlation via structlog processor
- Sensitive field patterns: password, secret, token, api_key, authorization

## Change Summary

### New Files
- [ ] `infra/main.bicep`
- [ ] `infra/modules/app-service.bicep`
- [ ] `infra/modules/database.bicep`
- [ ] `infra/modules/redis.bicep`
- [ ] `infra/modules/monitoring.bicep`
- [ ] `infra/modules/container-registry.bicep`
- [ ] `infra/parameters/production.bicepparam`
- [ ] `infra/deploy.sh`
- [ ] `backend/src/core/observability/__init__.py`
- [ ] `backend/src/core/observability/setup.py`
- [ ] `backend/src/core/observability/spans.py`
- [ ] `backend/src/core/observability/metrics.py`
- [ ] `backend/src/core/logging/__init__.py`
- [ ] `backend/src/core/logging/setup.py`
- [ ] `backend/src/core/logging/middleware.py`
- [ ] `backend/src/core/logging/filters.py`

### Modified Files
- [ ] `backend/requirements.txt` — Add Azure Monitor OTel exporter deps
- [ ] `backend/src/core/config.py` — Add observability config fields
- [ ] `backend/main.py` — Wire observability + logging + middleware
- [ ] `.github/workflows/deploy-production.yml` — Frontend staging deploy

### Test Files
- [ ] `tests/unit/core/test_observability_setup.py`
- [ ] `tests/unit/core/test_spans.py`
- [ ] `tests/unit/core/test_metrics.py`
- [ ] `tests/unit/core/test_request_id_middleware.py`
- [ ] `tests/unit/core/test_structured_logging.py`
- [ ] `tests/unit/core/test_sensitive_filter.py`

## Execution Timeline

| Time | Action |
|------|--------|
| 2026-02-24 | Sprint 122 starts |
| | Story 122-1: Azure Bicep IaC + CI/CD updates |
| | Story 122-2: OpenTelemetry observability module |
| | Story 122-3: Structured logging + Request ID |
| | Tests + integration |
