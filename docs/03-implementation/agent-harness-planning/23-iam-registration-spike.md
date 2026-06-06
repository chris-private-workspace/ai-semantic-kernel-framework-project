# 23 — IAM Block B: Self-Service Tenant Registration (Spike Design Note)

**Purpose**: Extract the verified invariants of the self-service tenant registration slice (Sprint 57.87) — the 3rd C-12 IAM Block B vertical spike (after 57.85 invites + 57.86 local credentials).
**Category / Scope**: platform_layer.identity / C-12 IAM Block B / Phase 57.87
**Created**: 2026-06-06
**Status**: Active (extracted from shipped + tested implementation)
**Closes**: `AD-Auth-Register-Backend-IAM-Block-B-Phase58`

> **Modification History**
> - 2026-06-06: Initial creation — extracted from Sprint 57.87 shipped impl (8-point gate self-check in retrospective)

---

## 1. Spike Summary (what shipped, as wired)

A prospective customer self-registers a new workspace from the shipped 4-step `/auth/register` wizard. **US-1**: `POST /api/v1/tenants/register` (public, EXEMPT) creates a `Tenant` (state ACTIVE) + a founding admin `User`. **US-2**: a real `admin` `Role` is seeded in the new tenant + granted to the founding user (`UserRole`) — the codebase's first real `Role(...)` creation. **US-3**: a duplicate slug returns a generic 409, the route runs under the new tenant's RLS context, and a `tenant_registered` WORM audit row is written. **US-4**: the wizard consumes the real endpoint (201 → `/auth/callback` OIDC; 409 → slug-taken error; the AP-2 demo banner is removed).

- Service: `backend/src/platform_layer/identity/registration.py:97-194` (`RegistrationService.register`).
- Endpoint: `backend/src/api/v1/tenants.py:101-141` (`POST /tenants/register`, status 201).
- Frontend un-stub: `frontend/src/pages/auth/register/index.tsx:121-153` (submit handler 201/409 branches).

## 2. Decision Matrix

| # | Decision | Options considered | Chosen | Why (rejected the rest) |
|---|----------|--------------------|--------|--------------------------|
| D1 | Tenant state at registration | (a) ACTIVE now / (b) REQUESTED + ProvisioningWorkflow / (c) REQUESTED only | **(a) ACTIVE now** (`registration.py:128` `state=TenantState.ACTIVE`) | The 8-step `ProvisioningWorkflow` is all stubs (`platform_layer/tenant/provisioning.py:19,77` — "stub now") + onboarding 6-step + health-check unimplemented, so (b)/(c) would strand the tenant in REQUESTED/PROVISIONING (never auto-advances). Self-serve trial wants immediate usability. |
| D2 | First-admin authority | (a) seed real admin Role + UserRole / (b) no DB role / (c) promote `seed_default_roles` stub | **(a) seed real admin Role + UserRole** (`registration.py:135-152`) | (b) leaves the founding user a non-admin (broken "register"); (c) is a larger cross-cutting slice (touches provisioning.py + admin-create + default role-set decision). (a) is the minimal real owner-of-record + matches `invites.accept`'s pre-existing `role_id` assumption. |
| D3 | Service home | (a) `identity/registration.py` / (b) `tenant/registration.py` | **(a)** | The bulk of the logic (User + Role + UserRole + audit + RLS context) is identity; it mirrors `invites.accept` (`identity/invites.py:251-327`). |
| D4 | Local password at registration | (a) none (OIDC-first) / (b) add password field | **(a) none** | The shipped wizard + `AuthRegister` mockup have NO password field (`page-auth-extras.jsx`); local-password is invite-accept's job (57.86). Adding one would violate mockup-fidelity. |
| D5 | Plan tiers | (a) map ENTERPRISE + meta_data / (b) add enum values | **(a)** (`registration.py:130` + `meta_data={requested_plan, company_size}`) | `TenantPlan` only has `ENTERPRISE` (`identity.py:92-96`; "Stage 2 will add BASIC/STANDARD"). Real tiers are Phase 56+ Stage 2 (carryover). |
| D6 | Migration | (a) none / (b) new table | **(a) none** | Reuses `tenants`/`users`/`roles`/`user_roles` — all exist. |

## 3. Verified Invariants (file:line + test)

| Invariant | Evidence | Verified by |
|-----------|----------|-------------|
| Slug-unique → generic 409 (no enumeration) | `registration.py:118-122` (`TenantSlugTakenError` status 409) + `tenants.py:124` (→ `HTTPException(409)`) | `test_tenant_register.py::test_register_duplicate_slug_409` + `test_registration_service.py::test_register_duplicate_slug_raises` |
| Invalid slug pattern → 422 | `tenants.py:71` (`pattern=r"^[a-z0-9][a-z0-9_-]*$"`) | `test_tenant_register.py::test_register_invalid_slug_422` |
| Tenant ACTIVE + plan ENTERPRISE + meta_data | `registration.py:127-133` | `test_registration_service.py::test_register_tenant_is_active_plan_enterprise_meta` + `test_tenant_register.py::test_register_tenant_is_active_in_db` |
| First real admin Role + UserRole seeded | `registration.py:135-152` | `test_registration_service.py::test_register_seeds_exactly_one_admin_role` + `…creates_tenant_admin_role_user_and_audit` |
| RLS context set before user/role writes | `registration.py:133` (`_set_tenant`) + `:196-202` | `test_registration_service.py::test_register_two_tenants_isolated` (app-layer) |
| `tenant_registered` WORM audit row | `registration.py:154-166` | both happy-path tests assert the audit row |
| EXEMPT (pre-JWT) | `tenant_context.py` EXEMPT_PATH_PREFIXES `+ /api/v1/tenants/register` | `test_tenant_register.py::test_exempt_path_contract` |
| Router mounted at `/api/v1/tenants/register` | `api/main.py` (`include_router(tenants_router, prefix="/api/v1")`) | `test_tenant_register.py` (hits the real path via `_build_app`) |
| Wizard un-stubbed (banner gone; 201/409 wired) | `register/index.tsx:143-149` + banner removed | `register.test.tsx` (banner-absent + 409 + 201 tests) |

**Verification command**: `cd backend && python -m pytest tests/unit/platform_layer/identity/test_registration_service.py tests/integration/api/test_tenant_register.py -q` (12 passed) · frontend `npx vitest run tests/unit/pages/auth/register.test.tsx` (6 passed).

**Test fixtures**: `backend/tests/conftest.py` (`db_session` real docker Postgres, rolled back; the register service self-creates the tenant so no `seed_tenant` needed). Integration uses `_build_app` (`get_db_session` override, no commit).

## 4. Cross-Category Contracts

N/A to `17-cross-category-interfaces.md` — identity is a `platform_layer` surface, NOT one of the 11+1 agent-harness categories (same call as 57.84 / 57.85 / 57.86). No new ABC; the registration flow reuses the identity ORM + `append_audit`. Contracts live in this note + the service docstring + CHANGE-055.

## 5. Open Invariants (Deferred — NOT verified this spike)

- **`AD-RBAC-DB-To-JWT-Wiring-Phase58`** (NEW) — the seeded admin `UserRole` is DB-real but **NOT yet authz-effective**: gating reads the JWT `roles` claim (`platform_layer/identity/auth.py` `_require_role`) and the OIDC callback bakes `roles=["user"]` (`api/v1/auth.py:302`). Making the DB role grant JWT admin is a separate slice.
- **`AD-Register-OIDC-User-Linkage-Phase58`** (NEW) — register creates the user by `email` (no `external_id`); the OIDC callback upserts by `(tenant_id, external_id)` (`auth.py:177-209`) → a later OIDC login would create a SECOND user row. Linkage (callback link-by-email OR register OIDC-initiated) deferred.
- **`AD-Tenant-Plan-Tiers-Phase58`** (NEW) — `TenantPlan` only has ENTERPRISE; real tiers + enforcement are Stage 2.
- MFA (`AD-Auth-MFA-Backend-IAM-Block-C-Phase58`) / recovery (`AD-Auth-Recovery-Page-Phase58`) / lockout (`AD-Auth-PasswordLogin-Lockout-Phase58`, also covers register-spam throttle) — separate slices.
- `seed_default_roles` full promotion (a default role-set for admin-create too) — separate slice.

## 6. Rollback

Low-risk, additive. To revert: drop `app.include_router(tenants_router, …)` + the import in `api/main.py`, remove the EXEMPT entry in `tenant_context.py`, delete `api/v1/tenants.py` + `platform_layer/identity/registration.py`, and restore the `/auth/register` stub copy + banner (git revert the Day-3 commits). No migration / no schema change → no DB rollback. Est. < 30 min. The tenant/user/role rows created by any real registration are valid data (not corrupt) even if the endpoint is removed.

## 7. References

- `sprint-57-87-plan.md` / `sprint-57-87-checklist.md` — sprint contract
- `21-iam-invites-spike.md` / `22-iam-credentials-spike.md` — prior C-12 spikes (pattern source)
- `platform_layer/identity/invites.py` — the User+UserRole+audit + `_set_tenant` mirror
- `09-db-schema-design.md §Group 1 Identity & Tenancy` — Tenant/User/Role/UserRole ORM
- `.claude/rules/multi-tenant-data.md` 鐵律 — RLS context per write
- `claudedocs/4-changes/feature-changes/CHANGE-055-iam-tenant-registration.md`
