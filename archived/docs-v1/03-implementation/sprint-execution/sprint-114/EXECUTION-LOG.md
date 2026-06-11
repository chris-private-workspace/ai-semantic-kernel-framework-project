# Sprint 114 Execution Log

**Sprint**: 114 — AD 場景基礎建設 (Phase 32)
**Date**: 2026-02-23
**Status**: COMPLETED

---

## Sprint Overview

| Item | Value |
|------|-------|
| Stories | 4 |
| Tests | 96 (33 + 20 + 21 + 22) |
| New Files | 14 source + 4 test + 1 config |
| Modified Files | 5 |
| Estimated SP | 13 |

---

## Story Execution

### Story 114-1: PatternMatcher AD 規則庫 (3 SP)

**Status**: COMPLETED | **Tests**: 33/33 PASSED

**Changes**:
- `src/integrations/orchestration/intent_router/pattern_matcher/rules.yaml` — Added 5 AD rules (34→39 total)
  - `ad_account_unlock`: EN/ZH patterns, risk=medium
  - `ad_password_reset`: EN/ZH patterns, risk=high
  - `ad_group_membership`: EN/ZH patterns, risk=medium
  - `ad_account_create`: EN/ZH patterns, risk=high
  - `ad_account_disable`: EN/ZH patterns, risk=high

**Test File**: `tests/unit/integrations/orchestration/intent_router/test_ad_pattern_rules.py`
- 5 test classes: unlock(4), reset(4), group(5), create(4), disable(4)
- Metadata validation: 4 tests
- Regression suite: 5 tests (existing rules preserved)
- False positive prevention: 3 tests

### Story 114-2: LDAP MCP Server AD 配置擴展 (3 SP)

**Status**: COMPLETED | **Tests**: 20/20 PASSED

**New Files**:
- `src/integrations/mcp/servers/ldap/ad_config.py` — ADConfig dataclass (extends LDAPConfig)
- `src/integrations/mcp/servers/ldap/ad_operations.py` — ADOperations service layer

**Modified**:
- `src/integrations/mcp/servers/ldap/__init__.py` — Updated exports
- `backend/.env.example` — Added LDAP_* and SERVICENOW_* environment variables

**Test File**: `tests/integration/mcp/test_ldap_ad_operations.py`
- ADConfig validation: 7 tests
- find_user: 2 tests
- unlock_account: 3 tests
- reset_password: 2 tests
- modify_group_membership: 4 tests
- get_group_members: 2 tests

### Story 114-3: ServiceNow Webhook 真實實現 (3 SP)

**Status**: COMPLETED | **Tests**: 21/21 PASSED

**New Files**:
- `src/integrations/orchestration/input/__init__.py` — Module exports
- `src/integrations/orchestration/input/servicenow_webhook.py` — Webhook receiver (~280 LOC)
  - `ServiceNowRITMEvent` (Pydantic model with validation)
  - `WebhookAuthConfig` (shared_secret + IP whitelist)
  - `ServiceNowWebhookReceiver` (auth, idempotency, event processing)
  - `WebhookValidationError` (status code aware)
- `src/api/v1/orchestration/webhook_routes.py` — API endpoints (POST + health)

**Modified**:
- `src/api/v1/orchestration/__init__.py` — Added webhook_router export
- `src/api/v1/__init__.py` — Registered orchestration_webhook_router

**Test File**: `tests/unit/integrations/orchestration/test_servicenow_webhook.py`
- RITM event model: 5 tests
- Authentication: 4 tests
- IP validation: 4 tests
- Idempotency: 4 tests
- Event processing: 4 tests (including async)
- Disabled webhook: 1 test (async, 503 status)

### Story 114-4: RITM→Intent 映射管道 (4 SP)

**Status**: COMPLETED | **Tests**: 22/22 PASSED

**New Files**:
- `src/integrations/orchestration/input/ritm_intent_mapper.py` — YAML-driven mapper (~260 LOC)
  - `IntentMappingResult` dataclass
  - `RITMIntentMapper` (case-insensitive lookup, variable extraction, fallback)
- `src/integrations/orchestration/input/ritm_mappings.yaml` — 5 AD intent mappings

**Bug Fix During Testing**:
- `mappings_dict={}` (empty dict) was falsy, fell through to default YAML loading
- Fix: Changed `if mappings_dict:` → `if mappings_dict is not None:`

**Test File**: `tests/unit/integrations/orchestration/test_ritm_intent_mapper.py`
- YAML mapping: 7 tests (5 AD intents + count + supported intents)
- Case insensitive: 3 tests
- Fallback strategy: 3 tests
- Variable extraction: 3 tests (top-level, nested, missing)
- Custom mappings: 3 tests
- Error handling: 2 tests (missing file, empty dict)

---

## Test Summary

```
$ pytest [4 test files] -v
96 passed in 58.92s
```

| Story | Test File | Tests | Status |
|-------|-----------|-------|--------|
| 114-1 | test_ad_pattern_rules.py | 33 | PASSED |
| 114-2 | test_ldap_ad_operations.py | 20 | PASSED |
| 114-3 | test_servicenow_webhook.py | 21 | PASSED |
| 114-4 | test_ritm_intent_mapper.py | 22 | PASSED |
| **Total** | | **96** | **ALL PASSED** |

---

## Architecture Decisions

1. **YAML-driven mappings** over hardcoded intent mapping — extensible without code changes
2. **Pydantic validation** for webhook payloads — strict input validation at system boundary
3. **Bounded set** for idempotency cache — prevents unbounded memory growth
4. **Case-insensitive lookup** via pre-built index — O(1) matching performance
5. **Dotted path syntax** for variable extraction — supports `variables.key` nesting
6. **ADConfig extends LDAPConfig** via dataclass inheritance — reuses base LDAP configuration
7. **ADOperations as service layer** — abstracts LDAP operations into business-level methods

---

## Files Created/Modified

### New Source Files (10)
1. `src/integrations/mcp/servers/ldap/ad_config.py`
2. `src/integrations/mcp/servers/ldap/ad_operations.py`
3. `src/integrations/orchestration/input/__init__.py`
4. `src/integrations/orchestration/input/servicenow_webhook.py`
5. `src/integrations/orchestration/input/ritm_intent_mapper.py`
6. `src/integrations/orchestration/input/ritm_mappings.yaml`
7. `src/api/v1/orchestration/webhook_routes.py`
8. `tests/unit/integrations/orchestration/__init__.py`
9. `tests/unit/integrations/orchestration/intent_router/__init__.py`
10. `tests/integration/mcp/__init__.py`

### New Test Files (4)
1. `tests/unit/integrations/orchestration/intent_router/test_ad_pattern_rules.py`
2. `tests/integration/mcp/test_ldap_ad_operations.py`
3. `tests/unit/integrations/orchestration/test_servicenow_webhook.py`
4. `tests/unit/integrations/orchestration/test_ritm_intent_mapper.py`

### Modified Files (5)
1. `src/integrations/orchestration/intent_router/pattern_matcher/rules.yaml` — +5 AD rules
2. `src/integrations/mcp/servers/ldap/__init__.py` — Added ADConfig/ADOperations exports
3. `src/api/v1/orchestration/__init__.py` — Added webhook_router
4. `src/api/v1/__init__.py` — Registered orchestration_webhook_router
5. `backend/.env.example` — Added LDAP/ServiceNow env vars
