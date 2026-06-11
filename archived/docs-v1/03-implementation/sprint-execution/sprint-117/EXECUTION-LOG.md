# Sprint 117 Execution Log

**Sprint**: 117 — Multi-Worker + ServiceNow MCP (Phase 32)
**Date**: 2026-02-24
**Status**: COMPLETED

---

## Sprint Overview

| Item | Value |
|------|-------|
| Stories | 2 |
| Tests | 155 (47 + 50 + 38 + 20) |
| New Files | 7 source + 4 test + 1 config |
| Modified Files | 2 |
| Estimated SP | 40 |

---

## Story Execution

### Story 117-1: Multi-Worker Uvicorn (P1)

**Status**: COMPLETED | **Tests**: 47/47 PASSED

**New Files**:
- `src/core/server_config.py` (~140 LOC)
  - `ServerEnvironment` enum (development, staging, production)
  - `ServerConfig` class with environment-aware properties:
    - `workers` — dev: 1, prod: min(CPU*2+1, 8), overridable via UVICORN_WORKERS
    - `reload` — True only in development
    - `host`, `port` — configurable via SERVER_HOST, SERVER_PORT
    - `log_level` — dev: debug, staging/prod: info
    - `access_log` — disabled in production for performance
    - `worker_class` — always "uvicorn.workers.UvicornWorker"
    - `bind`, `is_development`, `is_production` — convenience properties
    - `to_dict()`, `__repr__()` — serialization and debugging
  - Case-insensitive environment parsing with fallback to development
- `gunicorn.conf.py` (~40 LOC)
  - Imports ServerConfig for all configuration values
  - Configures: bind, workers, worker_class, reload, loglevel, accesslog
  - Timeout/keepalive settings (120s/5s)
  - Security limits (request line, fields, field size)
  - Preload app in non-reload mode for better memory usage

**Modified**:
- `main.py` — Replaced hardcoded uvicorn.run() with ServerConfig-based launch (host, port, reload, workers, log_level all from config)
- `.env.example` — Added 5 Server Configuration + 8 ServiceNow environment variables

**Test Files**:
- `tests/unit/core/test_server_config.py` — 47 tests (9 test classes)
  - ServerEnvironment: 5 tests (values, string subclass, completeness)
  - ServerConfig defaults: 6 tests (env, host, port, worker_class, bind, explicit param)
  - Development: 5 tests (1 worker, reload, debug log, access log, is_development)
  - Staging: 5 tests (multi-worker, no reload, info log, access log, not dev/prod)
  - Production: 5 tests (multi-worker, no reload, info log, no access log, is_production)
  - Environment overrides: 8 tests (SERVER_ENV, HOST, PORT, UVICORN_WORKERS, LOG_LEVEL, bind)
  - Worker limits: 5 tests (minimum 1, maximum 32, auto cap 8, formula CPU*2+1, single CPU)
  - Serialization: 4 tests (to_dict keys, dev values, prod values, repr format)
  - Edge cases: 4 tests (invalid env, invalid port, invalid workers, case insensitive)

### Story 117-2: ServiceNow MCP Server (P1)

**Status**: COMPLETED | **Tests**: 108/108 PASSED (50 unit client + 38 unit server + 20 integration)

**New Files**:
- `src/integrations/mcp/servicenow_config.py` (~140 LOC)
  - `AuthMethod` enum (BASIC, OAUTH2)
  - `ServiceNowConfig` frozen dataclass
    - Properties: base_url, attachment_url, auth_tuple, auth_headers
    - `validate()` — Configuration validation with error list
    - `from_env()` — Factory from environment variables
    - `to_dict()` — Safe export (excludes secrets)
- `src/integrations/mcp/servicenow_client.py` (~440 LOC)
  - Exception hierarchy: ServiceNowError → Auth/Permission/NotFound/ServerError
  - `ServiceNowClient` async client with httpx.AsyncClient
    - `create_incident()` — POST /table/incident
    - `update_incident()` — PATCH /table/incident/{sys_id}
    - `get_incident()` — GET by number or sys_id (returns None on not found)
    - `create_ritm()` — POST /table/sc_req_item
    - `get_ritm_status()` — GET by number or sys_id
    - `add_work_notes()` — PATCH table/{sys_id} with work_notes
    - `add_attachment()` — POST /attachment/file with binary content
  - Retry: exponential backoff on 429/5xx/connect/timeout errors
  - No retry on 401/403/404 (immediate raise)
  - Lazy client initialization, async context manager
- `src/integrations/mcp/servicenow_server.py` (~530 LOC)
  - `ServiceNowMCPServer` with 6 registered MCP tools:
    1. `create_incident` — Create new Incident (permission level 2)
    2. `update_incident` — Update Incident fields (permission level 2)
    3. `get_incident` — Query Incident (permission level 1)
    4. `create_ritm` — Create RITM (permission level 2)
    5. `get_ritm_status` — Query RITM status (permission level 1)
    6. `add_attachment` — Attach file to record (permission level 2)
  - Full ToolSchema definitions with ToolParameter, ToolInputType enums
  - Handlers convert ServiceNowError to ToolResult(success=False)
  - JSON string → dict parsing for variables parameter
  - Context manager support (sync + async)
  - `call_tool()` via MCPProtocol JSON-RPC flow
  - `get_tools()`, `get_tool_names()` for discovery

**Test Files**:
- `tests/unit/mcp/test_servicenow_client.py` — 50 tests (10 test classes)
  - ServiceNowConfig: 10 tests (creation, URLs, auth tuple/headers, validate, from_env)
  - create_incident: 5 tests (success, optional fields, defaults, URL, auth error)
  - update_incident: 4 tests (success, PATCH method, URL with sys_id, not found)
  - get_incident: 5 tests (by number, by sys_id, not found × 2, requires identifier)
  - create_ritm: 4 tests (success, URL, payload structure, permission denied)
  - get_ritm_status: 4 tests (by number, by sys_id, not found, requires identifier)
  - add_attachment: 3 tests (success, URL format, content type header)
  - add_work_notes: 2 tests (success, PATCH method)
  - Error handling: 8 tests (401, 403, 404, 500, error detail, connection, timeout, non-JSON)
  - Retry: 5 tests (retry on 500, no retry on 401/403/404, max retries exhausted)
- `tests/unit/mcp/test_servicenow_server.py` — 38 tests (11 test classes)
  - Initialization: 4 tests (name, version, running flag, protocol)
  - Tool registration: 5 tests (6 tools, names, schema match, permission levels, read level)
  - Schema correctness: 6 tests (required/optional params, enums)
  - create_incident handler: 4 tests (success, optional params, auth error, generic error)
  - update_incident handler: 4 tests (success, no updates, filter None, not found)
  - get_incident handler: 4 tests (found, not found, missing identifiers, API error)
  - create_ritm handler: 3 tests (success, JSON string variables, error)
  - get_ritm_status handler: 3 tests (found, not found, missing identifiers)
  - add_attachment handler: 3 tests (success, bytes encoding, error)
  - Context manager: 2 tests (sync, async)
- `tests/integration/mcp/test_servicenow_api.py` — 20 tests (5 test classes)
  - Full tool chain: 6 tests (one per tool, end-to-end handler → client → result)
  - Error propagation: 4 tests (auth, network, RITM, attachment errors)
  - MCP protocol flow: 4 tests (tools list, descriptions, parameters, registered_tools)
  - Configuration integration: 3 tests (from_env, validation valid/invalid)
  - Tool discovery: 3 tests (schemas, names, LLM descriptions)

---

## Test Summary

```
$ pytest tests/unit/core/test_server_config.py tests/unit/mcp/test_servicenow_client.py tests/unit/mcp/test_servicenow_server.py tests/integration/mcp/test_servicenow_api.py -v --no-cov
155 passed in 11.48s
```

| Story | Test File(s) | Tests | Status |
|-------|-------------|-------|--------|
| 117-1 | test_server_config.py | 47 | PASSED |
| 117-2 | test_servicenow_client.py | 50 | PASSED |
| 117-2 | test_servicenow_server.py | 38 | PASSED |
| 117-2 | test_servicenow_api.py | 20 | PASSED |
| **Total** | | **155** | **ALL PASSED** |

---

## Architecture Decisions

1. **ServerConfig as separate module** — Decoupled from main.py for testability and reuse by gunicorn.conf.py.
2. **Case-insensitive environment parsing** — `ServerConfig(env="PRODUCTION")` works, with fallback to development for invalid values.
3. **Worker count formula** — `min(CPU*2+1, 8)` with override via UVICORN_WORKERS (capped at 32 for safety).
4. **Development always 1 worker** — UVICORN_WORKERS ignored in development to maintain hot-reload compatibility.
5. **ServiceNow files directly in mcp/** — Not under `mcp/servers/` subfolder, following sprint plan file structure.
6. **Frozen dataclass for config** — `ServiceNowConfig` is immutable after creation, preventing accidental mutation.
7. **Exception hierarchy** — `ServiceNowError` base class with Auth/Permission/NotFound/Server subclasses enables selective retry (only retry on Server/Connect/Timeout, never on Auth/Permission/NotFound).
8. **Lazy httpx client** — Client created on first request, not at init time, to support dependency injection and testing.
9. **ToolResult for errors** — All ServiceNow errors wrapped in `ToolResult(success=False)` instead of raising, following MCP convention.
10. **Read-only tools lower permission** — get_incident (1) and get_ritm_status (1) vs create/update tools (2), following principle of least privilege.

---

## New Environment Variables (13)

### Server Configuration (5)

| Variable | Default | Description |
|----------|---------|-------------|
| SERVER_ENV | development | Server environment (development/staging/production) |
| UVICORN_WORKERS | auto | Override worker count (staging/prod only) |
| SERVER_HOST | 0.0.0.0 | Bind address |
| SERVER_PORT | 8000 | Bind port |
| LOG_LEVEL | debug/info | Log verbosity (debug in dev, info otherwise) |

### ServiceNow (8)

| Variable | Default | Description |
|----------|---------|-------------|
| SERVICENOW_INSTANCE_URL | (required) | ServiceNow instance base URL |
| SERVICENOW_USERNAME | | Basic Auth username |
| SERVICENOW_PASSWORD | | Basic Auth password |
| SERVICENOW_OAUTH_TOKEN | | OAuth2 bearer token |
| SERVICENOW_AUTH_METHOD | basic | Auth method (basic/oauth2) |
| SERVICENOW_API_VERSION | v2 | Table API version |
| SERVICENOW_TIMEOUT | 30 | Request timeout (seconds) |
| SERVICENOW_MAX_RETRIES | 3 | Max retry attempts |

---

## Files Created/Modified

### New Source Files (4)
1. `src/core/server_config.py` (~140 LOC)
2. `src/integrations/mcp/servicenow_config.py` (~140 LOC)
3. `src/integrations/mcp/servicenow_client.py` (~440 LOC)
4. `src/integrations/mcp/servicenow_server.py` (~530 LOC)

### New Config Files (1)
5. `gunicorn.conf.py` (~40 LOC)

### New Test Files (4 + 2 __init__)
6. `tests/unit/core/__init__.py`
7. `tests/unit/core/test_server_config.py` (47 tests)
8. `tests/unit/mcp/__init__.py`
9. `tests/unit/mcp/test_servicenow_client.py` (50 tests)
10. `tests/unit/mcp/test_servicenow_server.py` (38 tests)
11. `tests/integration/mcp/test_servicenow_api.py` (20 tests)

### Modified Files (2)
12. `main.py` — Replaced hardcoded uvicorn.run() with ServerConfig
13. `.env.example` — Added 13 environment variables

---

## Dependencies Added

```
gunicorn>=21.2.0          # Multi-Worker WSGI/ASGI (production only)
httpx>=0.25.0             # Async HTTP Client (already in project)
```

Note: gunicorn is Linux-only (not used on Windows development). httpx is already a project dependency.

---

## Startup Modes

```bash
# Development (1 worker + reload)
SERVER_ENV=development python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Alternative: via main.py (uses ServerConfig)
SERVER_ENV=development python main.py

# Production (N workers via Gunicorn, Linux only)
SERVER_ENV=production gunicorn main:app -c gunicorn.conf.py

# Production via uvicorn directly (cross-platform)
SERVER_ENV=production python main.py
```

---

## Next Steps (Sprint 118+)

1. Register ServiceNow MCP Server in ServerRegistry for auto-discovery
2. Add ServiceNow tool usage in hybrid orchestrator workflow
3. Implement RITM → Incident linking (auto-create incident from RITM)
4. Add rate limiting middleware for ServiceNow API calls
5. Performance benchmark: ServiceNow API latency P95
6. Wire up Gunicorn in Dockerfile for container deployment
