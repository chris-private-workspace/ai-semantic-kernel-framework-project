# CHANGE-090: Tenant-display real-data wiring (chrome fixtures → real `authStore.tenant`)

**Date**: 2026-06-15
**Sprint**: 57.123
**Scope**: Frontend chrome (Sidebar / Topbar / UserMenu) + backend `/auth/me` (cross-cutting: platform identity)
**Slice**: `AD-FE-Tenant-Display-Fixture-Phase58` (C-class 主流量 Potemkin)

## Problem

The always-visible app chrome rendered a **hardcoded fixture tenant** on every page for every logged-in user — an AP-4 Potemkin sitting on the 主流量:

- `Sidebar.tsx:90` — `FIXTURE_TENANT = { name:"acme-prod", meta:"tenant_01h9a2 · Pro" }`
- `Topbar.tsx:122` — `tenantName = "acme-prod"`
- `UserMenu.tsx:142-146` — a 3-element `TENANT_FIXTURES` (acme-prod / globex-eu / initech-jp + fake regions ap-east-1 / eu-west-1 / ap-northeast-1)

The displayed tenant name / id / plan / region were the same literals regardless of which tenant the user actually belonged to, and the "· Pro" plan + `globex-eu`/`initech-jp` rows were pure invention.

## Root Cause

The chrome was built as a verbatim mockup re-point (Sprint 57.18-57.30) with the mockup's static fixture VALUES left in place; the "wire real" follow-up (the comments said "Sprint 57.20+/57.21+ wires real") never happened. The real tenant was already in `authStore.tenant` (`{id,name,code}`, fed by `GET /auth/me`), but `/auth/me` did not return `plan` or `region`, so the chrome's plan badge + region row had no real source.

## Solution

1. **Backend** (`api/v1/auth.py`): `AuthMeTenant` += `plan: str` + `region: str` (real `Tenant` columns — `plan` Sprint 56.1, `region` Sprint 57.46). Populated at **all 3** `AuthMeTenant` build sites (`me()` + `dev_login()` + `issue_session()` — a Day-0 catch; a single un-updated site would 500). The `dev_login` new-tenant branch sets explicit `plan=TenantPlan.ENTERPRISE, region="global"` (the cols use `server_default`, so a freshly-constructed object has no Python-side value → an async lazy-load risk).
2. **FE types** (`authStore.ts`): `AuthTenant` += `plan` + `region`. `bootstrap`/`fetchAuthMe` UNCHANGED (the whole-object `set` + the hand-written `as AuthMeResponse` cast auto-thread the new fields; no codegen).
3. **Sidebar / Topbar**: drop the fixtures → read `authStore.tenant` (name + `{code} · {Plan}` meta / name · role); null "—" fallback; CSS classes byte-identical (only the component-logic data layer changed → mockup-fidelity preserved).
4. **UserMenu**: drop `TENANT_FIXTURES` → a single real current-tenant **info row** (name + real region, check, aria-current — not a menuitem, so no dead control); the section label `userMenu.switchTenant` → a new `userMenu.currentTenant` ("Current tenant" / "目前租戶") since a single-item list under "Switch tenant" would be a misleading label.

NO migration / new wire event / codegen / `styles-mockup.css` change. NO real multi-tenant switcher (each user is JWT-scoped to one tenant; deferred).

## Verification

- **Backend**: `test_auth_me.py` — `test_me_200_with_cookie` asserts plan/region defaults; NEW `test_me_tenant_plan_and_region_are_real` overrides region to `ap-southeast-7` and asserts `/auth/me` returns it (proves the value flows from the real DB col, not a hardcoded "global"). Full pytest **2696 passed / 5 skip**.
- **FE**: `Sidebar.test.tsx` (+1) / `UserMenu.test.tsx` (+1) / `authStore.test.ts` (+2 assertions) / `Topbar.test.tsx` (NEW, 2). Full Vitest **892 passed**.
- **Gates**: mypy `src` **0/371** · run_all **10/10** (AP-4 placeholder detector green; wire count 24) · ESLint clean · build ✅ · `check:mockup-fidelity` **51** (byte-identical, no new oklch/hex literal).
- **Drive-through (real chrome + real backend + real login)** — Risk Class E clean restart (an orphan worker held :8000 with old code via SO_REUSEADDR; `Win32_Process` sweep + clean restart):
  - **acme-prod**: sidebar `Dev Tenant (acme-prod)` + `acme-prod · Enterprise`, topbar `Dev Tenant (acme-prod) · user`, UserMenu single real tenant + region `global`; the old `tenant_01h9a2 · Pro` + globex-eu/initech-jp are GONE.
  - **globex-eu** (2nd login): the chrome FOLLOWS → `Dev Tenant (globex-eu)` + `globex-eu · Enterprise`; no acme-prod leak.
  - = the chrome display follows the real logged-in tenant (different tenant → different chrome), NOT a fixture — AP-4 closed, load-bearing proven LIVE. Screenshots in `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-123/artifacts/`.

## Impact

Frontend chrome (3 components) + backend `/auth/me` (1 endpoint, additive). Backend change is additive (2 always-present fields → no breaking change for other `/auth/me` consumers). No migration / wire / codegen. The plan now shows the real (Stage-1 = "Enterprise") value — honest, replacing the fake "Pro". The dev-login picker labels ("Pro · ap-east-1") remain a dev-only-tool fixture (out of scope — not 主流量 chrome).
