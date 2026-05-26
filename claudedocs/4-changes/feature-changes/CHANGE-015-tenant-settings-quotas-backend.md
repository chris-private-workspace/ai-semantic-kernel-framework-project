# CHANGE-015: TenantSettings Quotas Admin GET Backend

**Date**: 2026-05-26
**Sprint**: 57.48 (Track C)
**Scope**: API Layer / Admin (`backend/src/api/v1/admin/tenants.py`) + integration tests
**Closes**: `AD-TenantSettings-Quotas-Backend` (carried since Sprint 57.44 audit)

## Problem
TenantSettings `QuotasTab` was wired to `_fixtures.ts QUOTAS` (5-row fixture). Sprint 57.44 audit flagged as fixture-only. `platform_layer/tenant/quota.py` shipped Sprint 56.1 / 56.2 is Redis-only (current daily-token counter); structured quota *configuration* lives elsewhere.

## Root Cause
D-DAY0-4 content-verify finding: `quota.py` exposes `get_usage()` (int counter) only. Structured per-resource quota configuration is owned by `PlanLoader.get_plan(name).quota` (`PlanQuota` dataclass: `tokens_per_day` / `cost_usd_per_day` / `sessions_per_user_concurrent` / `api_keys_max`).

## Solution
- Add `QuotaItem` + `QuotaListResponse` Pydantic models
- Add `GET /admin/tenants/{tenant_id}/quotas` endpoint
- Project `PlanLoader.get_plan(tenant.plan.value).quota` into 4 items via `_project_plan_quota_to_items()` helper using `_QUOTA_RESOURCE_META` table (attr/unit/period)
- 5 fields per item: `resource / limit / unit / period / current_usage`
- `current_usage = None` at admin layer this sprint (Phase 58+ may wire Redis counters per resource)
- Unknown plan name → defensive empty list (avoid 500)

## Verification
- 8 NEW integration tests (auth + 404 + happy + shape + unit assertion + pagination + tenant isolation + invalid limit) — ALL PASS
- 9/9 V2 lints green
- mypy --strict clean

## Impact
- **Backend-only** addition
- Frontend QuotasTab Phase 58+ migration unblocked
- `current_usage` field carried as `None` for forward compatibility (frontend can render placeholder dashes; AP-2 honest)
- D-DAY0-4 drift handled via `PlanLoader` projection (no new ORM table; no new YAML schema)

## File Touches
- `backend/src/api/v1/admin/tenants.py` — +QuotaItem/QuotaListResponse + _QUOTA_RESOURCE_META + _project_plan_quota_to_items + list_tenant_quotas (~75 lines)
- `backend/tests/integration/api/test_admin_tenant_quotas.py` — NEW (170 lines, 8 tests)
