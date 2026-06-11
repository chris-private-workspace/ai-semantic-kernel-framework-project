# Sprint 125 Execution Log

## Sprint Overview

| Attribute | Value |
|-----------|-------|
| **Sprint** | 125 |
| **Phase** | 34 — Feature Expansion |
| **Story Points** | 30 |
| **Start Date** | 2026-02-24 |
| **Status** | ✅ Completed |

## Goals

1. **Story 125-1**: n8n Mode 3 — Bidirectional collaboration (IPA reasoning + n8n orchestration)
2. **Story 125-2**: Azure Data Factory MCP Server (8 MCP tools)
3. **Story 125-3**: Integration tests & monitoring

## Story 125-1: n8n Mode 3 — Bidirectional Collaboration

### New Files

- `src/integrations/n8n/__init__.py` — Module exports
- `src/integrations/n8n/orchestrator.py` — N8nOrchestrator (IPA reasoning → n8n execution → monitoring)
- `src/integrations/n8n/monitor.py` — ExecutionMonitor (polling, timeout, retry, progress)
- `src/api/v1/n8n/routes.py` — Added callback endpoint (HMAC-verified)
- `src/api/v1/n8n/schemas.py` — Added callback schemas

### Key Classes

| Class | Responsibility |
|-------|---------------|
| N8nOrchestrator | 6-phase flow: reasoning → HITL → translate → execute → monitor → consolidate |
| ExecutionMonitor | Polls n8n execution with exponential backoff, configurable MonitorConfig |
| CallbackHandler | HMAC-SHA256 verified n8n callback endpoint (POST + GET) |

### Design Decisions

- **ReasoningFn injection**: Custom reasoning functions can replace default keyword-based classifier
- **HITL gate**: Critical/high risk operations blocked pending approval
- **Callback store**: In-memory `_callback_store` for webhook data (future: Redis/DB)

## Story 125-2: Azure Data Factory MCP Server

### New Files

- `src/integrations/mcp/servers/adf/__init__.py` — Module exports
- `src/integrations/mcp/servers/adf/__main__.py` — MCP Server entry point
- `src/integrations/mcp/servers/adf/client.py` — AdfApiClient (Azure SDK wrapper)
- `src/integrations/mcp/servers/adf/server.py` — AdfMCPServer (8 MCP tools)
- `src/integrations/mcp/servers/adf/tools/__init__.py` — Tools exports
- `src/integrations/mcp/servers/adf/tools/pipeline.py` — Pipeline management tools
- `src/integrations/mcp/servers/adf/tools/monitoring.py` — Monitoring tools

### MCP Tools (8 total)

| Tool | ADF API | Permission Level |
|------|---------|-----------------|
| `adf_list_pipelines` | GET /pipelines | READ (1) |
| `adf_get_pipeline` | GET /pipelines/{name} | READ (1) |
| `adf_run_pipeline` | POST /pipelines/{name}/createRun | EXECUTE (2) |
| `adf_cancel_pipeline_run` | POST /pipelineruns/{runId}/cancel | ADMIN (3) |
| `adf_get_pipeline_run` | GET /pipelineruns/{runId} | READ (1) |
| `adf_list_pipeline_runs` | POST /queryPipelineRuns | READ (1) |
| `adf_list_datasets` | GET /datasets | READ (1) |
| `adf_list_triggers` | GET /triggers | READ (1) |

### Design Decisions

- **Service Principal auth**: client_credentials flow with token caching (5min buffer before expiry)
- **Pattern consistency**: Follows n8n MCP Server structure: `client.py` → `tools/` → `server.py`
- **3-tier permissions**: READ=1, EXECUTE=2, ADMIN=3 (aligned with existing MCP security model)

## Story 125-3: Integration Tests & Monitoring

### Test Files

| Test File | Tests | Type |
|-----------|-------|------|
| `tests/unit/integrations/n8n/test_n8n_orchestrator.py` | 28 | Unit |
| `tests/unit/integrations/n8n/test_n8n_monitor.py` | 27 | Unit |
| `tests/unit/integrations/mcp/servers/adf/test_adf_client.py` | 25 | Unit |
| `tests/unit/integrations/mcp/servers/adf/test_adf_server.py` | 16 | Unit |
| `tests/integration/n8n/test_n8n_mode3.py` | 10 | Integration |
| `tests/integration/adf/test_adf_integration.py` | 6 | Integration |
| **Total** | **112** | |

### Test Results

```
Unit tests:        96 passed
Integration tests: 16 passed
Total new tests:   112
```

## Modified Files

- `src/integrations/mcp/servers/__init__.py` — Add ADF exports
- `src/api/v1/n8n/routes.py` — Add callback endpoint
- `src/api/v1/n8n/schemas.py` — Add callback schemas

## Notes

- Integration test `test_multiple_concurrent_orchestrations` had a mock signature bug (missing `**kwargs`), fixed during verification
- `azure.core` ModuleNotFoundError affects batch test collection but individual execution works fine
