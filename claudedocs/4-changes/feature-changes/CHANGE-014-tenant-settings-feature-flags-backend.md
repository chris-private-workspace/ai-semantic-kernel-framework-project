# CHANGE-014: TenantSettings FeatureFlags Admin GET Backend

**Date**: 2026-05-26
**Sprint**: 57.48 (Track B)
**Scope**: API Layer / Admin (`backend/src/api/v1/admin/tenants.py`) + integration tests
**Closes**: `AD-TenantSettings-FeatureFlags-Backend-AdminGet` (carried since Sprint 57.44 audit)

## Problem
TenantSettings `FeatureFlagsTab` was wired to `_fixtures.ts FEATURE_FLAGS` (8-row fixture). Sprint 57.44 audit flagged this as fixture-only. Phase 56.1 shipped `feature_flags` global registry table + `FeatureFlagsService` (Phase 56 SaaS) but admin layer never exposed a per-tenant read.

## Root Cause
Sprint 56.1 designed `feature_flags` as a **global registry** with `tenant_overrides JSONB` map (analogous to `tools_registry`), NOT per-tenant rows. Plan §4.2 assumed per-tenant rows; D-DAY0-3 drift correction projects the JSONB override resolution at admin-layer.

## Solution
- Add `FeatureFlagItem` + `FeatureFlagListResponse` Pydantic models
- Add `GET /admin/tenants/{tenant_id}/feature-flags` endpoint
- For each `FeatureFlag` row: resolved value = `tenant_overrides.get(str(tenant_id), default_enabled)`; include `overridden: bool` indicator
- Order by `name` ASC; paginated `limit`/`offset`
- 6 fields per item: `name / value / default_enabled / overridden / description / updated_at`

## Verification
- 8 NEW integration tests in `test_admin_tenant_feature_flags.py` (auth + 404 + empty + default resolution + override resolution + shape + isolation + pagination) — ALL PASS
- Critical multi-tenant test: same flag's override for tenant A does NOT bleed into tenant B's response
- 9/9 V2 lints green
- mypy --strict clean

## Impact
- **Backend-only** addition
- Frontend FeatureFlagsTab Phase 58+ migration to live data unblocked
- D-DAY0-3 drift handled via JSONB resolution helper (avoids ORM schema change)

## File Touches
- `backend/src/api/v1/admin/tenants.py` — +FeatureFlagItem/FeatureFlagListResponse + list_tenant_feature_flags endpoint (~75 lines)
- `backend/tests/integration/api/test_admin_tenant_feature_flags.py` — NEW (213 lines, 8 tests)
