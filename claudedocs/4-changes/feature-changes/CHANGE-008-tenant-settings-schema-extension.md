# CHANGE-008: TenantSettings Backend Schema Extension

**Date**: 2026-05-26
**Sprint**: 57.46 (Track B of multi-domain bundle)
**Scope**: Backend / Cat Identity & Tenancy (DB migration + ORM + API + tests)
**Closes**: `AD-TenantSettings-Backend-Schema-Extension` (Sprint 57.44 D-DAY0-4 BLOCKING Phase 58+)

## Problem

Sprint 57.44 `/tenant-settings` 6-tab rebuild was forced to use fixture-first data because the backend Tenant ORM was missing 5 columns required for the SaaS settings page real-data migration:

- `region` (apac/emea/americas/global)
- `locale` (BCP-47 code)
- `retention_days` (GDPR-relevant)
- `sso_enabled` (Identity/SSO toggle)
- `seats` (plan seat limit)

This blocked Phase 58+ from migrating `frontend/src/features/tenant-settings/_fixtures.ts` to a real backend API.

## Root Cause

Tenant ORM was last enhanced in Sprint 56.1 (Day 1) when SaaS Stage 1 lifecycle (`state` Enum + `plan` Enum + 2 progress JSONB) was added (migration 0014). SaaS settings columns specific to the tenant-settings UI surface were never added — the page mockup landed in Sprint 57.44 but the backend schema lagged behind. Sprint 57.44 D-DAY0-4 caught the gap; fixture-first was selected as the carry-forward path with this AD blocking Phase 58+.

## Solution

Sprint 57.46 Track B adds the 5 columns end-to-end:

### 1. Alembic migration `0018_tenant_settings_extension.py`

- `down_revision = '0017_verification_log'`
- 5× `op.add_column()` with NOT NULL + sensible `server_default` so existing rows backfill safely:
  - `region VARCHAR(32) DEFAULT 'global'`
  - `locale VARCHAR(16) DEFAULT 'en-US'`
  - `retention_days INTEGER DEFAULT 90`
  - `sso_enabled BOOLEAN DEFAULT FALSE`
  - `seats INTEGER DEFAULT 5`
- Reversible `downgrade()` drops the 5 columns in reverse order
- No RLS policy needed — `tenants` is listed under "Tables intentionally global (no RLS)" per `0009_rls_policies.py:36` (Tenant table IS the multi-tenant root; has no `tenant_id` itself)

### 2. Tenant ORM `backend/src/infrastructure/db/models/identity.py`

- 5 typed `Mapped[T]` columns added on `Tenant` class (between `meta_data` and `created_at`):
  - `region: Mapped[str]` with `String(32)` + `server_default=text("'global'")`
  - `locale: Mapped[str]` with `String(16)` + `server_default=text("'en-US'")`
  - `retention_days: Mapped[int]` with `Integer` + `server_default=text("90")`
  - `sso_enabled: Mapped[bool]` with `Boolean` + `server_default=text("FALSE")`
  - `seats: Mapped[int]` with `Integer` + `server_default=text("5")`
- Added `Boolean` + `Integer` imports
- Updated module-level Modification History (1-line MHist within E501 budget)

### 3. API `backend/src/api/v1/admin/tenants.py`

- `TenantResponse` Pydantic extended from 10 → 15 fields (5 baseline + 5 SaaS settings inserted between `meta_data` and `created_at`)
- `TenantUpdateRequest` Pydantic extended from 2 → 7 editable fields with validators:
  - `region`: optional + `field_validator` whitelist (`apac`/`emea`/`americas`/`global`)
  - `locale`: optional + max_length 16 + BCP-47 regex pattern (2-3 alpha + optional 2-3 alphanum region)
  - `retention_days`: optional + `Field(ge=1, le=3650)` (10 years max)
  - `sso_enabled`: optional bool
  - `seats`: optional + `Field(ge=1)`
- `extra='forbid'` preserved — immutable fields (id/code/state/plan/created_at/updated_at/progress) still reject with 422
- `update_tenant` endpoint body extended with 5 new field-change branches; each writes (old → new) into the audit chain `operation_data` JSONB (operation `tenant_settings_updated` continues to be the single audit operation type)
- Added `field_validator` import from pydantic

### 4. Integration tests `backend/tests/integration/api/test_admin_tenant_settings_extension.py`

12 NEW tests (exceeds ≥10 target):

- 1 GET default (asserts all 5 server-default values for fresh tenant)
- 5 PATCH happy-path (one per field; first asserts full audit chain entry shape with old_values + new_values + changed_fields)
- 1 PATCH batch (all 5 in single request → 1 audit entry with all 5 in changed_fields set)
- 4 PATCH 422 (region invalid, locale malformed BCP-47, retention_days=0, seats=0)
- 1 multi-tenant isolation (PATCH tenant_a's region+seats; verify tenant_b retains defaults; only 1 audit entry against tenant_a)

Mirrors the `test_admin_tenant_patch.py` pattern (FastAPI test app + role middleware + db_session + `require_admin_platform_role` + `require_tenant_match_or_platform_admin` overrides + audit chain assertion via `select(AuditLog).where(operation=...)`).

**Test path correction (D-DAY0-1)**: Original plan §5 placed file at `backend/tests/api/v1/admin/` but that directory does not exist; the existing pattern is `backend/tests/integration/api/test_admin_tenant_*.py`. File placed at the correct location.

## Verification

- `alembic upgrade head` succeeds locally (NEW head = 0018)
- `alembic current` shows `0018_tenant_settings_extension`
- `grep "region\|locale\|retention_days\|sso_enabled\|seats" backend/src/infrastructure/db/models/identity.py` → ≥5 matches (Tenant class only)
- `grep "region:\|locale:\|retention_days:\|sso_enabled:\|seats:" backend/src/api/v1/admin/tenants.py` → ≥10 matches (TenantResponse + TenantUpdateRequest)
- `pytest backend/tests/integration/api/test_admin_tenant_settings_extension.py -v` → 12 PASSED
- `mypy backend/src` → 0 errors (cross-platform `unused-ignore` pattern not triggered)
- `black + isort + flake8 backend/src backend/tests` → exit 0
- `python scripts/lint/run_all.py` → 9/9 green

## Impact

- **Scope**: backend-only; 0 frontend code change
- **Downstream**: Unblocks Phase 58+ `/tenant-settings` fixture-first → real-API migration (Sprint 57.44 carry-forward); enables real GET for the 6 settings tabs (General/FeatureFlags/Quotas/HITLPolicies/Members/DangerZone) — fixture file `frontend/src/features/tenant-settings/_fixtures.ts` can now be swapped to TanStack Query consumers calling `GET /api/v1/admin/tenants/{tenant_id}`
- **Audit trail**: every PATCH writes a `tenant_settings_updated` audit entry containing the exact changed fields + before/after values; no-op short-circuit (empty payload) still skips audit entry write
- **Migration safety**: defaults are sensible; `op.add_column(server_default=...)` performs backfill in a single statement so existing tenants get auto-populated defaults during `upgrade()`
- **Multi-tenant rule**: preserved — `tenants` is intentionally global (no tenant_id, no RLS); per-tenant settings ARE the rows on this root table

## Drift findings absorbed

- D-DAY0-1: test path corrected to `backend/tests/integration/api/`
- D-DAY0-2: column name `code` (not `tenant_code` as Sprint 57.44 retro called it)
- D-DAY0-3: `state` Enum + `plan` Enum (not `status` String / `plan_id`)
- D-DAY0-4: `extra='forbid'` preserved while extending TenantUpdateRequest (not relaxed)

## Cross-references

- `backend/src/infrastructure/db/migrations/versions/0018_tenant_settings_extension.py` (NEW)
- `backend/src/infrastructure/db/models/identity.py` (MOD — Tenant +5 columns)
- `backend/src/api/v1/admin/tenants.py` (MOD — TenantResponse + TenantUpdateRequest + update_tenant body + field_validator import)
- `backend/tests/integration/api/test_admin_tenant_settings_extension.py` (NEW — 12 tests)
- Sprint 57.44 retro — D-DAY0-4 origin
- Sprint 57.44 memory subfile — fixture-first lock-in narrative
- `frontend/src/features/tenant-settings/_fixtures.ts` — still in use until Phase 58+ swap
- `claudedocs/4-changes/feature-changes/CHANGE-007-mockup-fidelity-auditdocsync-rule.md` — sibling Track A
- `claudedocs/4-changes/feature-changes/CHANGE-009-mockup-capture-method.md` — sibling Track C
