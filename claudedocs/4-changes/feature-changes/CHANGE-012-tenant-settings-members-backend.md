# CHANGE-012: TenantSettings MEMBERS Tab — Backend GET Endpoint

**Date**: 2026-05-26
**Sprint**: 57.47 (Day 1 Track B Stretch)
**Scope**: API Layer (`backend/src/api/v1/admin/tenants.py`) + Integration tests
**Closes**: `AD-TenantSettings-Members-Backend` (CHANGE-011 audit's cheapest tab)

## Problem

`/tenant-settings` Members tab (Sprint 57.44 rebuild) displayed an 8-member
fixture with no backend backing; future real-data migration was blocked.

## Root Cause

Sprint 57.44 shipped Option A fixture-first across all 6 tabs without backend
audit; the Members tab fixture (`MEMBERS` array in `_fixtures.ts`) lists
{name, email, role, last_active_relative, capacity_pct} which had no read
endpoint, even though the `User` ORM (Sprint 49.x baseline) already has the
needed columns via `TenantScopedMixin`.

## Solution

Added one read-only endpoint to `backend/src/api/v1/admin/tenants.py`:

```
GET /api/v1/admin/tenants/{tenant_id}/members
  → TenantMemberListResponse { items, total, limit, offset }
```

- **Auth**: `require_tenant_match_or_platform_admin` (mirrors Sprint 57.13 US-A3 GET pattern — platform admins read any tenant; regular users read only their own)
- **Pagination**: standard `limit` (1-200, default 50) + `offset` (≥0, default 0)
- **Order**: `created_at DESC, id DESC` (deterministic, mirrors LIST endpoint)
- **404**: when `tenant_id` does not exist (via existing `_load_tenant_or_404`)
- **5 fields per item**: `id / email / display_name / status / created_at` (from User ORM via `from_attributes=True`)

Pydantic models added at end of file:
- `TenantMemberItem(BaseModel)` — projected User row
- `TenantMemberListResponse(BaseModel)` — paginated envelope

Notes:
- The fixture's `role / last_active / capacity_pct` fields are NOT in the
  current `User` ORM. Frontend will display placeholders for those columns
  until Phase 58+ adds role + activity tracking; this CHANGE deliberately
  scopes to data already present on User to honor the Day 0.8 ≤ 2 hr budget.

## Verification

8 NEW pytest tests in `backend/tests/integration/api/test_admin_tenant_members.py`:

1. `test_list_members_401_without_auth` — no JWT context → 401
2. `test_list_members_404_when_tenant_not_found` — non-existent tenant_id → 404
3. `test_list_members_happy_path_returns_users_for_tenant` — 2 seeded users → 200 + both in items
4. `test_list_members_response_shape_has_5_fields` — id/email/display_name/status/created_at
5. `test_list_members_tenant_isolation` — **CRITICAL** per `.claude/rules/multi-tenant-data.md` — tenant B's user does not leak into tenant A's response
6. `test_list_members_pagination` — limit=2/offset=0 + limit=2/offset=2 produces disjoint slices summing to 3
7. `test_list_members_empty_when_no_users` — tenant with 0 users → items=[] + total=0 (not 404)
8. `test_list_members_invalid_query_limit` — limit=500 → 422 (Query validation)

Run: `pytest backend/tests/integration/api/test_admin_tenant_members.py -v`

## Impact

- **Frontend**: `/tenant-settings` Members tab can swap MEMBERS fixture for
  `useQuery(['tenant', tenantId, 'members'])` hook in next sprint
- **Multi-tenant rule §Rule 3** (API endpoint must accept tenant via path/dep) — preserved via path `tenant_id` + `require_tenant_match_or_platform_admin`
- **Multi-tenant rule §Rule 2** (all queries filter by tenant_id) — preserved via `select(User).where(User.tenant_id == tenant_id)`
- **No migration**: User ORM already has all needed columns from Sprint 49.x baseline
- **Pickup order from CHANGE-011 audit**: HITL_POLICIES next (~2-3 hr; concrete `DBHITLPolicyStore` already exists)
