# Sprint 123 — Gap Analysis & Coverage Recommendations

## Executive Summary

Sprint 123 added **213 new tests** across 3 modules (Orchestration, Auth, MCP), bringing targeted coverage improvements. Below is the gap analysis identifying what remains uncovered and recommended next steps.

---

## Module-by-Module Analysis

### 1. Orchestration Module (52.6% coverage)

**Well-Covered (>80%)**:
| File | Coverage | Notes |
|------|----------|-------|
| `intent_router/router.py` | 98% | Core routing coordinator |
| `intent_router/models.py` | 87% | Data models |
| `semantic_router/routes.py` | 86% | Route definitions |

**Partially Covered (30-80%)**:
| File | Coverage | Gap Description |
|------|----------|-----------------|
| `guided_dialog/context_manager.py` | 60% | Multi-turn context tracking paths |
| `intent_router/completeness/checker.py` | 72% | Complex validation branches |
| `guided_dialog/refinement_rules.py` | 69% | Edge case refinement paths |
| `risk_assessor/policies.py` | 42% | Policy evaluation branches |
| `hitl/controller.py` | 32% | Approval workflow paths |
| `hitl/notification.py` | 27% | Notification dispatch paths |
| `metrics.py` | 25% | OpenTelemetry metric recording |

**Uncovered (0%)**:
| File | Statements | Reason |
|------|-----------|--------|
| `audit/logger.py` | ~50 | Audit logging (Phase 23 scope) |
| `input/ritm_intent_mapper.py` | ~80 | ServiceNow RITM mapping |
| `semantic_router/migration.py` | 133 | One-time migration script |
| `semantic_router/route_manager.py` | 140 | Route lifecycle management |
| `semantic_router/setup_index.py` | 174 | Index initialization |

**Recommendation**: Priority targets for next sprint:
1. `hitl/controller.py` (32%) — Critical HITL approval paths
2. `metrics.py` (25%) — Observability verification
3. `guided_dialog/engine.py` (37%) — Core dialog engine paths

---

### 2. Auth Module (60.0% coverage)

**Well-Covered (>80%)**:
| File | Coverage | Notes |
|------|----------|-------|
| `auth/service.py` | 100% | Core auth service |
| `security/password.py` | 100% | Password hashing (real bcrypt) |
| `security/jwt.py` | 97% | JWT token management |
| `middleware/rate_limit.py` | 95% | Rate limiting |
| `auth/schemas.py` | 85% | Pydantic schemas |

**Uncovered (0%)**:
| File | Statements | Reason |
|------|-----------|--------|
| `security/audit_report.py` | 112 | Audit report generation |
| `api/v1/auth/dependencies.py` | ~40 | RBAC dependency injection (route-level) |
| `api/v1/auth/routes.py` | ~50 | Auth route handlers (integration scope) |
| `api/v1/auth/migration.py` | ~30 | One-time migration |

**Recommendation**: Auth core is well-covered. Remaining gaps are:
1. `audit_report.py` — Add unit tests for report generation
2. `auth/routes.py` — Integration test scope (not unit test)

---

### 3. MCP Module (23.3% coverage)

**Well-Covered (>80%)**:
| File | Coverage | Notes |
|------|----------|-------|
| `security/permission_checker.py` | 98% | Permission enforcement |
| `security/command_whitelist.py` | 97% | Command whitelisting |
| `security/redis_audit.py` | 85% | Redis-based audit logging |
| `security/permissions.py` | 82% | RBAC permissions |

**Partially Covered (20-50%)**:
| File | Coverage | Gap Description |
|------|----------|-----------------|
| `core/types.py` | 49% | MCP protocol type definitions |
| `security/audit.py` | 45% | File-based audit logging |
| `registry/server_registry.py` | 39% | Server lifecycle management |
| `core/transport.py` | 24% | MCP transport layer |
| `registry/config_loader.py` | 22% | YAML config loading |
| `core/protocol.py` | 22% | MCP protocol handling |
| `core/client.py` | 21% | MCP client communication |

**Uncovered (0%) — 36 files**:
- `servers/azure/` — 11 files (Azure MCP server)
- `servers/filesystem/` — 4 files
- `servers/ldap/` — 5 files
- `servers/servicenow/` — 4 files (new)
- `servers/shell/` — 4 files
- `servers/ssh/` — 4 files
- `servers/win_ad/` — 4 files

**Recommendation**: Security layer is well-covered. Large uncovered area is MCP servers:
1. `registry/server_registry.py` (39%) — Improve lifecycle tests
2. `core/client.py` (21%) — MCP client communication
3. `servers/` — Each server is independent; test individually per priority

---

## Overall Gap Summary

| Category | Coverage | Status |
|----------|----------|--------|
| **Core Routing Logic** | 98% | ✅ Excellent |
| **Auth Service** | 100% | ✅ Excellent |
| **Security (MCP)** | 82-98% | ✅ Good |
| **Dialog Management** | 60% | ⚠️ Needs improvement |
| **HITL Approval** | 32% | ⚠️ Needs improvement |
| **Observability/Metrics** | 25% | ⚠️ Needs improvement |
| **MCP Servers** | 0% | ❌ Not tested (36 files) |
| **MCP Core** | 21-49% | ⚠️ Needs improvement |

## Recommended Next Sprint Priorities

### P0 (Critical)
1. HITL approval paths (`hitl/controller.py`, `approval_handler.py`)
2. MCP core client/protocol/transport

### P1 (Important)
3. Guided dialog engine paths
4. Metrics/observability verification
5. MCP server registry deep coverage

### P2 (Nice-to-have)
6. Individual MCP server tests (Azure, Filesystem, etc.)
7. Input gateway source handlers
8. Audit logging paths

---

**Generated**: 2026-02-24
**Sprint**: 123 (Phase 33 — Production Hardening)
