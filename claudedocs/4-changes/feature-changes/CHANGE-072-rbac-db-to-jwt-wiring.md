# CHANGE-072: RBAC DB→JWT wiring — issue-time DB-sourced roles claims

**Date**: 2026-06-12
**Sprint**: 57.105
**Scope**: platform_layer.identity × api/v1 (cross-cutting identity; NOT one of the 11+1 harness categories)
**Closes**: `AD-RBAC-DB-To-JWT-Wiring-Phase58` (note 23 §5) + drive-through-audit ISSUE-6 ("every page renders role=user")

## Problem

The DB role grant machinery was real (Role / UserRole tables, `RBACManager.has_role_code`,
registration seeds a founding `admin` UserRole — Sprint 57.7/57.87), but **no JWT issue site
read it**: the OIDC callback hardcoded `roles=["user"]` (`api/v1/auth.py:302`) and
password-login used a `_PASSWORD_LOGIN_ROLES` constant. Gates (`require_admin_platform_role`
Path 1) read the claim → a DB-granted admin was never authz-effective. AP-4 shape: the grant
existed; turning it off changed nothing.

## Design (Option A — issue-time DB roles)

At login, query the user's tenant-scoped role codes and bake them into the claim. Single
truth source = the JWT; per-request gates stay claim-only (no hot-path DB hit).

- **Rejected** Path-2 flag flip (`rbac_db_backed_fallback=True`): claim stays wrong; per-request
  DB fallback on every gated call = hot-path cost + two truth sources.
- **Rejected** per-request middleware role loading: same hot-path cost, larger blast radius.
- **Rejected** token refresh on grant change: no refresh infrastructure exists (AP-6 —
  building it for this slice is "為未來預留").
- **Documented invariant (not a bug)**: a grant/revoke AFTER issue takes effect at next
  login (claim staleness until re-login).

## Solution

| File | Change |
|------|--------|
| `platform_layer/identity/rbac.py` | NEW `RBACManager.get_user_role_codes(*, user_id, tenant_id, session) -> list[str]` — `select(Role.code) JOIN UserRole` tenant-scoped projection, sorted+deduped; session REQUIRED (login handlers pass the request session). |
| `api/v1/auth.py` | OIDC callback (`roles=["user"]` literal retired) + password-login (`_PASSWORD_LOGIN_ROLES` deleted) both issue `roles = sorted({"user", *db_codes})` into `JWTManager.encode(roles=...)` AND the login response body (the SPA sets `authStore` from the payload). 3 stale "per-request RBAC" comments fixed. **dev-login untouched** (`_DEV_LOGIN_ROLES` kept — dev-only debt; `_is_production()` → 404 in prod). |
| `platform_layer/identity/registration.py` | Honest-boundary docstring resolved (the seeded admin grant is now JWT-effective at login). |

Founding role code `"admin"` ∈ `_ADMIN_PLATFORM_ROLES` (`auth.py`) → the claim passes the
existing gate with **zero gate-code change**.

## Verification

- **Unit**: `TestGetUserRoleCodes` (sorted+dedup / empty) — `test_rbac.py` 9/9.
- **Integration** (`test_password_login.py` 12/12, +3 tests + 1 assertion, 0 conversions / 0
  deletions): founding-admin chain (register HTTP → `set_password` → login → JWT-decoded
  claim + body `== ["admin","user"]`) · admin-grant test · cross-tenant isolation
  (foreign-tenant grant invisible → `["user"]`, multi-tenant 鐵律) · invite e2e extended
  (`["member","user"]` claim-effective).
- **Gates**: mypy `src` 0/357 · run_all 10/10 (event count unchanged) · full pytest
  **2384 + 4 skipped** (+5, 0 deletions) · `loop.py` / DB / migration / wire schema /
  frontend diff = 0.
- **Drive-through PASS** (real UI :3007 + fresh no-reload backend PID 7672, NO dev-login):
  `/auth/register` wizard → tenant `dt57105-rbac` 201 → out-of-band
  `CredentialsService.set_password` (D11: register collects no password; 57.86-proven
  primitive) → `/auth/password-login` 200 → sidebar renders **"DT Founder / admin"**
  (ISSUE-6 closed) → Tenant Settings → Model Policy tab → edit → **PUT
  `/admin/tenants/{id}/model-policy` 200** (first admin write ever driven without
  dev-login) → override cleared (revert) → negative probe: role-less JWT same user/tenant →
  **403 "Platform admin role required"**. Screenshots:
  `sprint-57-105/artifacts/dt57105-{admin-renders,model-policy-put200}.png`.

## Open Invariants (still deferred)

- `AD-Register-OIDC-User-Linkage-Phase58` — register-by-email vs callback-upsert-by-external_id
  can still create a second user row on a later OIDC login (why the drive-through spine is
  password-login).
- dev-login `_DEV_LOGIN_ROLES` hardcode divergence — dev-only (prod 404); documented, not hidden.
- Claim staleness until re-login — documented invariant (above).

## Impact

Backend-only (3 src files + 2 test files). No migration, no new event, no frontend change
(`authStore.roles` self-heals via the login payload / `/auth/me` echo — D10: zero FE roles
source other than those two).
