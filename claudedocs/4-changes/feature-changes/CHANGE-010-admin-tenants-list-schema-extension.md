# CHANGE-010: Admin-Tenants LIST Schema Extension (7→12 fields + region filter)

**Date**: 2026-05-26
**Sprint**: 57.47 (Day 1 Track A)
**Scope**: API Layer (`backend/src/api/v1/admin/tenants.py`) + Integration tests
**Closes**: 🔴 `AD-AdminTenants-Backend-Schema-Extension` (Sprint 57.43 D-DAY0-6 BLOCKING)

## Problem

`GET /api/v1/admin/tenants` LIST endpoint returned a 7-field `TenantListItem`
projection (id/code/display_name/state/plan/created_at/updated_at). Sprint 57.46
landed 5 new Tenant ORM columns (region/locale/retention_days/sso_enabled/seats)
+ Alembic 0018, but only the single-tenant GET `/{tenant_id}` (`TenantResponse`)
exposed them. The `/admin-tenants` LIST page therefore had to either (a) make
N+1 GET calls per row to display these columns OR (b) hide them. Phase 58+
admin UI work was blocked.

## Root Cause

Sprint 57.43 audit (D-DAY0-6) deferred the LIST 9-column extension to a
follow-up sprint while shipping single-tenant GET first; Sprint 57.46 closed
the ORM/schema half but did not extend LIST projection.

## Solution

Two surgical changes in `backend/src/api/v1/admin/tenants.py`:

1. **`TenantListItem` Pydantic** — added 5 new fields (region/locale/
   retention_days/sso_enabled/seats) inserted between `plan` and `created_at`
   for grouped readability. `from_attributes=True` already present on
   `ConfigDict` (L181) → SQLAlchemy ORM rows auto-map without endpoint logic
   change.

2. **`list_tenants()` signature** — added optional `region: str | None = Query(None, max_length=32)` query parameter between `plan` and `search`; the
   filter logic adds one line `if region is not None: base_stmt = base_stmt.where(Tenant.region == region)` mirroring the existing state/plan filter
   pattern. Backward-compatible (no `region` param = no filter).

## Verification

- 12 NEW pytest tests in `backend/tests/integration/api/test_admin_tenant_list.py`:
  - 5 field-presence (region/locale/retention_days/sso_enabled/seats individually)
  - 1 server_default cover (region='global', locale='en-US', retention_days=90, sso_enabled=False, seats=5)
  - 2 region filter (positive match + no match)
  - 2 combined filter (region+plan, region+state)
  - 1 backward-compat (no region param)
  - 1 max-length validation (33-char region → 422)
- Existing `test_list_tenants_happy_no_filter` shape assertion updated from 7 → 12 keys
- pytest delta: ≥ +12 (Track A)
- `mypy --strict` 0 errors expected (Pydantic v2 + ORM types unchanged)

Run: `pytest backend/tests/integration/api/test_admin_tenant_list.py -v`

## Impact

- **Frontend `/admin-tenants` table**: can now display 12 columns from single LIST call (N+1 fan-out eliminated)
- **Backward-compat**: existing 7-field consumers continue to work (Pydantic adds new optional keys)
- **Multi-tenant isolation**: Tenant is global; admin-only endpoint; existing
  `require_admin_platform_role` dep unchanged
- **No migration**: Sprint 57.46 Alembic 0018 already landed the 5 ORM cols
