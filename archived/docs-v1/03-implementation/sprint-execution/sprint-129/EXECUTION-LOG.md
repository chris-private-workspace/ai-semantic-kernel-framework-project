# Sprint 129 Execution Log

## Sprint Overview

| Attribute | Value |
|-----------|-------|
| **Sprint** | 129 |
| **Phase** | 34 — Feature Expansion (P2) |
| **Story Points** | 25 |
| **Start Date** | 2026-02-25 |
| **End Date** | 2026-02-25 |
| **Status** | Completed |

## Goals

1. **Story 129-1**: D365 API Client (OAuth + OData query builder + CRUD)
2. **Story 129-2**: D365 MCP Server (6 MCP tools + server framework)
3. **Story 129-3**: Tests & Verification (95 tests across 5 test files)

## Story 129-1: D365 API Client

### New Files

- `src/integrations/mcp/servers/d365/auth.py` — D365AuthProvider (OAuth 2.0 Client Credentials Grant)
- `src/integrations/mcp/servers/d365/client.py` — D365ApiClient + ODataQueryBuilder + D365Config

### D365 Authentication Architecture

```
D365AuthProvider
  ├── D365AuthConfig (frozen dataclass)
  │   ├── tenant_id, client_id, client_secret, d365_url
  │   └── from_env() class method
  ├── TOKEN_URL: login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token
  ├── TOKEN_SCOPE: {d365_url}/.default
  ├── TOKEN_REFRESH_BUFFER: 300s (5 min before expiry)
  ├── ensure_token() — cached or acquire new
  ├── invalidate_token() — for 401 retry
  └── get_auth_headers() → {"Authorization": "Bearer {token}"}
```

### OData Query Builder

| Method | OData Param | Example |
|--------|-------------|---------|
| `select(*fields)` | `$select` | `name,accountnumber` |
| `filter(expr)` | `$filter` | `statecode eq 0` |
| `top(count)` | `$top` | `10` |
| `skip(count)` | `$skip` | `5` |
| `orderby(field, desc)` | `$orderby` | `name asc` |
| `expand(*navs)` | `$expand` | `contact_customer_accounts` |
| `count()` | `$count` | `true` |

### D365 API Client Capabilities

| Operation | HTTP | Endpoint |
|-----------|------|----------|
| Query entities | GET | `{base}/{entity_set}?$filter=...` |
| Get record | GET | `{base}/{entity_set}({guid})` |
| Create record | POST | `{base}/{entity_set}` |
| Update record | PATCH | `{base}/{entity_set}({guid})` |
| Delete record | DELETE | `{base}/{entity_set}({guid})` |
| Entity metadata | GET | `{base}/EntityDefinitions(LogicalName='{name}')` |
| List entity types | GET | `{base}/EntityDefinitions?$filter=...` |
| Health check | GET | `{base}/WhoAmI` |

### Error Handling

| HTTP Status | Exception | Retry |
|-------------|-----------|-------|
| 400 | D365ValidationError | No |
| 401/403 | D365AuthenticationError | Once (token refresh) |
| 404 | D365NotFoundError | No |
| 429 | D365RateLimitError | Yes (Retry-After header) |
| 5xx | D365ApiError | Yes (exponential backoff) |
| Connection | D365ConnectionError | Yes (exponential backoff) |

### Known Entity Set Map

```python
ENTITY_SET_MAP = {
    "account": "accounts",
    "contact": "contacts",
    "incident": "incidents",       # Cases
    "msdyn_workorder": "msdyn_workorders",
    "systemuser": "systemusers",
    "team": "teams",
    "businessunit": "businessunits",
    "opportunity": "opportunities",
    "lead": "leads",
    "task": "tasks",
    "annotation": "annotations",
}
```

## Story 129-2: D365 MCP Server

### New Files

- `src/integrations/mcp/servers/d365/server.py` — D365MCPServer
- `src/integrations/mcp/servers/d365/tools/query.py` — QueryTools (4 tools)
- `src/integrations/mcp/servers/d365/tools/crud.py` — CrudTools (2 tools)
- `src/integrations/mcp/servers/d365/tools/__init__.py` — Tools exports
- `src/integrations/mcp/servers/d365/__init__.py` — Module exports
- `src/integrations/mcp/servers/d365/__main__.py` — Entry point

### MCP Tools

| # | Tool | Permission | Description |
|---|------|------------|-------------|
| 1 | `d365_query_entities` | READ (1) | Query records with OData filtering |
| 2 | `d365_get_record` | READ (1) | Get single record by ID |
| 3 | `d365_list_entity_types` | READ (1) | List customizable entity types |
| 4 | `d365_get_entity_metadata` | READ (1) | Get entity schema metadata |
| 5 | `d365_create_record` | EXECUTE (2) | Create new entity record |
| 6 | `d365_update_record` | EXECUTE (2) | Update existing record |

### Server Architecture

```
D365MCPServer (SERVER_NAME="d365-mcp", VERSION="1.0.0")
  ├── MCPProtocol (JSON-RPC 2.0)
  ├── MCPPermissionChecker (RBAC)
  ├── D365ApiClient → D365AuthProvider → Azure AD
  ├── QueryTools (4 tools, perm level 1)
  │   ├── d365_query_entities
  │   ├── d365_get_record
  │   ├── d365_list_entity_types
  │   └── d365_get_entity_metadata
  └── CrudTools (2 tools, perm level 2)
      ├── d365_create_record
      └── d365_update_record
```

### Modified Files

| # | Path | Change |
|---|------|--------|
| 1 | `src/integrations/mcp/servers/__init__.py` | Add D365MCPServer, D365ApiClient, D365Config exports |

## Story 129-3: Tests & Verification

### New Test Files

| # | Path | Tests | Story |
|---|------|-------|-------|
| 1 | `tests/unit/.../d365/test_d365_auth.py` | 20 | 129-3 |
| 2 | `tests/unit/.../d365/test_d365_client.py` | 25 | 129-3 |
| 3 | `tests/unit/.../d365/test_d365_server.py` | 9 | 129-3 |
| 4 | `tests/unit/.../d365/test_odata_builder.py` | 32 | 129-3 |
| 5 | `tests/integration/d365/test_d365_integration.py` | 9 | 129-3 |

## File Inventory

### New Files (15)

| # | Path | LOC | Story |
|---|------|-----|-------|
| 1 | `src/.../d365/auth.py` | 295 | 129-1 |
| 2 | `src/.../d365/client.py` | 1038 | 129-1 |
| 3 | `src/.../d365/server.py` | 334 | 129-2 |
| 4 | `src/.../d365/tools/__init__.py` | 16 | 129-2 |
| 5 | `src/.../d365/tools/query.py` | 404 | 129-2 |
| 6 | `src/.../d365/tools/crud.py` | 297 | 129-2 |
| 7 | `src/.../d365/__init__.py` | 27 | 129-2 |
| 8 | `src/.../d365/__main__.py` | 10 | 129-2 |
| 9 | `tests/.../d365/test_d365_auth.py` | 328 | 129-3 |
| 10 | `tests/.../d365/test_d365_client.py` | 585 | 129-3 |
| 11 | `tests/.../d365/test_d365_server.py` | 220 | 129-3 |
| 12 | `tests/.../d365/test_odata_builder.py` | 321 | 129-3 |
| 13 | `tests/.../d365/test_d365_integration.py` | 276 | 129-3 |
| 14 | `tests/.../d365/__init__.py` (unit) | ~5 | 129-3 |
| 15 | `tests/integration/d365/__init__.py` | ~5 | 129-3 |

### Modified Files (1)

| # | Path | Change |
|---|------|--------|
| 1 | `src/.../servers/__init__.py` | Add D365 exports (D365MCPServer, D365ApiClient, D365Config) |

## Test Execution Results

```
95 passed in 83.14s
```

### Test Breakdown

| Test File | Tests | Status |
|-----------|-------|--------|
| test_d365_auth.py | 20 | ALL PASSED |
| test_d365_client.py | 25 | ALL PASSED |
| test_d365_server.py | 9 | ALL PASSED |
| test_odata_builder.py | 32 | ALL PASSED |
| test_d365_integration.py | 9 | ALL PASSED |
| **Total** | **95** | **ALL PASSED** |

## Notes

- All tests use mocked D365 API (no real D365 environment needed)
- D365AuthProvider uses frozen `D365AuthConfig` dataclass — immutable by design
- ODataQueryBuilder validates `$top` and `$skip` (raises D365ValidationError for invalid values)
- Entity set name resolution: ENTITY_SET_MAP for 11 known entities, fallback pluralization for unknown
- Client automatically follows `@odata.nextLink` for pagination (safety limit: 100 pages)
- Health check uses D365 `WhoAmI` endpoint (lightweight, always available)
- Token caching with 5-minute refresh buffer, Retry-After header respected for 429
- `Prefer: return=representation` header on POST/PATCH for created/updated record in response
