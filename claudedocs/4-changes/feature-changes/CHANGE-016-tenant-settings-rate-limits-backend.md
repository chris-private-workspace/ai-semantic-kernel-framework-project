# CHANGE-016: TenantSettings RateLimits Admin GET Backend (Option A)

**Date**: 2026-05-26
**Sprint**: 57.48 (Track D)
**Scope**: API Layer / Admin (`backend/src/api/v1/admin/tenants.py`) + integration tests
**Closes**: `AD-TenantSettings-RateLimits-Backend` (carried since Sprint 57.44 audit)

## Problem
TenantSettings `QuotasTab` Rate Limits section (and any future RateLimitsTab) wired to `_fixtures.ts RATE_LIMITS` (3-row fixture). Sprint 57.44 audit flagged as fixture-only. No existing rate-limit backend module to wrap.

## Root Cause
D-DAY0-5 content-verify finding: NO `rate_limit*.py` module in `backend/src/`. Real rate-limit persistence has never been required (the platform's nginx/CDN handles edge rate limits; in-process logic is per-quota/Redis only). Plan §4.3 decision tree triggered.

## Day 0.8 Decision: Option A (fixture-projection)
Option A chosen over Option B (new ORM table + Alembic 0019) per plan §4.3 because:
- Sprint 57.48 needed to ship 4 tracks in ~8 hr agent-adjusted; Option B alone is 5-6 hr (would consume 60-75% of budget)
- Rate-limit *persistence* isn't yet a real requirement (no edge enforcement layer reads from this)
- `tenants.meta_data` JSONB is already the established carrier for soft-config (existing pattern; multi-tenant rule compliant)
- If Phase 58+ needs dedicated table, migration path is straightforward (read `meta_data["rate_limits"]` → seed new table)

## Solution
- Add `RateLimitItem` + `RateLimitListResponse` Pydantic models
- Add `GET /admin/tenants/{tenant_id}/rate-limits` endpoint
- Source: `tenant.meta_data.get("rate_limits", DEFAULT_RATE_LIMITS)`
- `DEFAULT_RATE_LIMITS` mirrors `_fixtures.ts RATE_LIMITS` shape (3 items: API requests / Tool calls / SSE connections)
- Defensive parse: skip non-dict entries; missing label entries skipped
- 2 fields per item: `label / value`

## Verification
- 6 NEW integration tests (auth + 404 + default fallback + override + shape + isolation) — ALL PASS
- 9/9 V2 lints green
- mypy --strict clean

## Impact
- **Backend-only**; persistence via `tenants.meta_data` JSON only this sprint
- Phase 58+ can promote to dedicated table without API contract change (label/value shape is stable)
- D-DAY0-5 drift handled via Option A fixture-projection

## File Touches
- `backend/src/api/v1/admin/tenants.py` — +RateLimitItem/RateLimitListResponse + DEFAULT_RATE_LIMITS + list_tenant_rate_limits (~50 lines)
- `backend/tests/integration/api/test_admin_tenant_rate_limits.py` — NEW (155 lines, 6 tests)
