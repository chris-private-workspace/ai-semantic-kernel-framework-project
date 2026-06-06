# CHANGE-055: C-12 IAM Block B — self-service tenant registration backend

**Date**: 2026-06-06
**Sprint**: 57.87
**Scope**: platform_layer.identity + api/v1 + frontend (no LLM; no migration)
**Closes**: `AD-Auth-Register-Backend-IAM-Block-B-Phase58` (3rd C-12 spike, after 57.85 invites + 57.86 credentials)

## Problem

There was no self-service path for a brand-new org to register itself. The shipped `/auth/register` 4-step wizard posted to `POST /api/v1/tenants/register` but the backend returned a 501 stub (frontend showed `register.errorStubbed` + an AP-2 demo banner). The only tenant-creation paths were dev-login (dev-only) and admin-create (`require_admin_platform_role`, runs the all-stub ProvisioningWorkflow).

## Root Cause

Block B was intentionally deferred (registration backend never built). Two facts shaped the design (Day-0 three-prong): the codebase had **no real `Role(...)` creation** anywhere (`seed_default_roles` is a stub), and authorization is **JWT-claim-based** (the OIDC callback bakes `roles=["user"]`).

## Solution

NEW `platform_layer/identity/registration.py` `RegistrationService.register()` — mirrors `invites.accept`'s User+UserRole+audit pattern + adds Tenant-creation and the first real Role seed:
1. slug-unique check (`tenants` RLS-free) → `TenantSlugTakenError` (409) on collision.
2. create `Tenant` (state **ACTIVE** immediately — skips the all-stub ProvisioningWorkflow; plan ENTERPRISE; `{requested_plan, company_size}` → `meta_data`).
3. `_set_tenant(tenant.id)` RLS context → seed an `admin` `Role` (first real Role-creation) → `User` (status active, no password — OIDC-first) → `UserRole` (founding admin self-grant) → `tenant_registered` WORM audit.

NEW public `api/v1/tenants.py` (`POST /tenants/register`, status 201, EXEMPT) → mounted in `api/main.py` → `tenant_context.py` EXEMPT `/api/v1/tenants/register`. Frontend un-stub: removed the 501-stub copy + AP-2 demo banner; wired 201 → `/auth/callback` (OIDC) + 409 → slug-taken inline error; i18n `register.errorSlugTaken` + `register.error` (en + zh-TW).

**Honest boundary**: the seeded admin role is DB-real but NOT yet JWT-authz-effective (carryover `AD-RBAC-DB-To-JWT-Wiring-Phase58`); register-user (by email) ≠ OIDC-login-user (by external_id) → dup-user (carryover `AD-Register-OIDC-User-Linkage-Phase58`). What ships is real + verifiable; the unblock is that the tenant now exists so OIDC `/auth/callback` no longer 400s "tenant not found".

## Verification

- `cd backend && python -m pytest tests/unit/platform_layer/identity/test_registration_service.py tests/integration/api/test_tenant_register.py -q` → 12 passed.
- Full backend: mypy `src/` **0/344** · flake8 0 · `run_all.py` **10/10** (check_rls_policies green — no new table) · pytest **2214 passed** / 4 skipped.
- Frontend: lint (no `--silent`) + build clean · `check:mockup-fidelity` ✓ (styles-mockup.css byte-identical; oklch baseline **53 UNCHANGED** — banner removal uses existing classes) · Vitest **763 passed**.

## Impact

Backend + frontend; no LLM / no migration / no schema change / no mockup-CSS change. The `/auth/register` wizard is now a real main-flow consumer. The first real `Role(...)` creation in the codebase. Carryovers (RBAC-JWT wiring / OIDC-user linkage / plan tiers / MFA / recovery / lockout) tracked in `next-phase-candidates.md`.
