# Sprint 57.123 Progress — Tenant-display real-data wiring (`AD-FE-Tenant-Display-Fixture-Phase58`)

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-123-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-123-checklist.md)

**Branch**: `feature/sprint-57-123-tenant-display-real-data` (from `main` `937dd5ca`, post-#297).

---

## Day 0 — Plan-vs-Repo Verify (三-prong) — 2026-06-15

### Prong 1 — path verify ✅
All anchors present: `Sidebar.tsx` · `layout/Topbar.tsx` · `UserMenu.tsx` · `auth/store/authStore.ts` · `auth/services/authService.ts` · `api/v1/auth.py` · `db/models/identity.py`. Test homes: `test_auth_me.py` · `Sidebar.test.tsx` · `UserMenu.test.tsx` · `auth/authStore.test.ts` present; **NO** `Topbar.test.tsx` → NEW. `CHANGE-090-*.md` free (089 = 57.122). i18n `locales/{en,zh-TW}/common.json` present (`userMenu` block at en:57, `switchTenant` at :63).

### Prong 2 — content verify (drift findings)

| ID | Finding | Implication |
|----|---------|-------------|
| **D-bootstrap-spread** ✅ | `authStore.ts:72-86` `bootstrap` does `set({ tenant: me.tenant })` (whole object); `fetchAuthMe` (`authService.ts:135-142`) is `as AuthMeResponse` (NO codegen) | +2 `AuthTenant` interface fields suffice — NO `set`/service change; values auto-thread |
| **D-me-orm** ✅ | `auth.py:372` `me()` loads full `Tenant` via `select`; `:382-386` builds `AuthMeTenant` | `.plan`/`.region` available at the `me()` construction |
| **D-tenant-cols** ✅ | `identity.py:124-128` `Tenant.plan` (NOT NULL, `.value`="enterprise") + `:146-150` `Tenant.region` (NOT NULL, "global", Sprint 57.46) | both always present on a select-loaded tenant; NO new migration |
| **D-3-construction-sites** ⚠️ NEW | `AuthMeTenant(` is built at **3** sites, not 1: `me()`:384 + `dev_login()`:450 + `issue_session()`:511 (password-login + MFA-verify shared) | adding `plan`/`region` as REQUIRED fields → ALL 3 must be updated or Pydantic 500s. `me()`:487-style + `issue_session()`:487 use `select(Tenant)` (loaded ✅); `dev_login()` has a new-tenant branch (see next) |
| **D-dev-login-new-tenant** ⚠️ NEW | `dev_login()` (`auth.py:420-423`) auto-creates `Tenant(code=…, display_name="Dev Tenant (…)")` with NO Python-side plan/region (server_default only) → accessing `.plan` on the fresh object before a DB round-trip risks async lazy-load | construct the new dev Tenant with explicit `plan=TenantPlan.ENTERPRISE, region="global"` (= the server_defaults; dev-only path; import `TenantPlan`). The existing-tenant select path is already loaded |
| **D-other-consumers** ✅ | FE `/auth/me`/`AuthMeResponse` consumers: `App.tsx` (bootstrap call), `pages/auth/dev/index.tsx` (its OWN `TenantOption` type — NOT `AuthTenant`), `authService.ts`, `authStore.ts` | the +2 required `AuthTenant` fields do NOT break any FE literal construction (dev page builds its own type) |
| **D-i18n-keys** ✅ | `userMenu.switchTenant` (en:63) + `userMenu.region` (used by UserMenu:314) exist | add `userMenu.currentTenant` to en + zh-TW |
| **D-seeded-tenant** ✅ | dev-login picker offers 3 tenant_codes (`acme-prod`/`globex-eu`/`initech-jp`); `dev_login` resolves/creates a Tenant per code; a NEW code → `display_name="Dev Tenant (<code>)"` | **multi-tenant drive-through feasible** (log in as ≥2 codes → chrome must follow). NOTE: the dev-login picker labels ("Pro · ap-east-1") are themselves dev-tool fixtures but OUT OF SCOPE (dev-only tool, not 主流量 chrome) |

### Prong 3 — schema ✅
`Tenant.plan` (Sprint 56.1) + `Tenant.region` (Sprint 57.46) columns EXIST — **NO new table / migration this sprint**.

### Baselines
Trusted from 57.122 closeout (main just merged at `937dd5ca`): pytest **2695+5skip** · wire **24** · mockup **51** · mypy `src` **0/371** · run_all **10/10**. Vitest re-capture Day 3. Full re-verify Day 4.

### Go/no-go
**GO.** Scope shift small: the only material finding (D-3-construction-sites + D-dev-login-new-tenant) stays within "EDIT `auth.py`" (3 edit spots + 1 explicit construction + 1 import vs the plan's single `me()` mention) — ≤20% shift. Plan §8 updated with the two NEW risks (do NOT silently edit §3). Branch created.

---

## Day 1 — Backend `/auth/me` plan + region (US-1) + FE types (US-2) — 2026-06-15

- **`auth.py`**: `AuthMeTenant` += `plan: str` + `region: str`; ALL **3** build sites (`me()` + `dev_login()` + `issue_session()`) carry `plan=tenant.plan.value`, `region=tenant.region` (replace_all on the identical line); `dev_login` new-tenant branch constructs explicit `plan=TenantPlan.ENTERPRISE, region="global"` (D-dev-login-new-tenant fix); `TenantPlan` import added. MHist.
- **`test_auth_me.py`**: `test_me_200_with_cookie` asserts plan/region defaults; NEW `test_me_tenant_plan_and_region_are_real` overrides region to `ap-southeast-7` → proves the value flows from the real DB col (a hardcoded "global" would fail). → **6 passed**.
- **`authStore.ts`**: `AuthTenant` += `plan: string` + `region: string`. `bootstrap`/`fetchAuthMe` UNCHANGED (whole-object `set` + `as` cast auto-thread). MHist.
- **Gate**: 1 E501 on the MHist line (trimmed) → black/isort/flake8 clean · mypy `src` **0/371** · test_auth_me **6 passed**.

## Day 2 — Components (US-3 / US-4) + i18n — 2026-06-15

- **`Sidebar.tsx`**: dropped `FIXTURE_TENANT`; reads `authStore.tenant`; `formatPlan` title-case helper; `initial`/`name`/`meta=${code} · ${Plan}` (null "—" fallback). CSS classes byte-identical. MHist.
- **`Topbar.tsx`**: dropped `tenantName="acme-prod"`; `tenantName = tenant?.name ?? "—"`. MHist.
- **`UserMenu.tsx`**: dropped `TENANT_FIXTURES`; `activeTenant = tenant`; single real-tenant info row (`data-testid="usermenu-current-tenant"`, name + real region, check, aria-current — an info row, NOT a menuitem → no dead control); region row real; section label `userMenu.switchTenant` → `userMenu.currentTenant`. MHist.
- **i18n**: `userMenu.currentTenant` added to en ("Current tenant") + zh-TW ("目前租戶"); kept `switchTenant` (pre-existing).
- **Gate**: ESLint clean · build ✅ (tsc thread OK) · `styles-mockup.css` byte-identical · `check:mockup-fidelity` **51 baseline 51** (no new oklch/hex literal — reused existing `oklch(from var(--primary) …)`).

## Day 3 — Tests (US-5) + Drive-through (US-6) — 2026-06-15

### FE tests (US-5)
All 4 test files had a `tenant` literal missing the new required `plan`/`region` (would break test-tsc) → updated:
- **`Sidebar.test.tsx`**: +1 test (real tenant pill name + `code · Plan` meta; old fixture gone) — 5 tests.
- **`UserMenu.test.tsx`**: `setAuthed` tenant += plan/region; +1 test (single real current tenant + region; no globex-eu/initech-jp; "Current tenant" label) — 7 tests.
- **`authStore.test.ts`**: `ME_PAYLOAD.tenant` += plan/region; +2 assertions — 5 tests.
- **`Topbar.test.tsx`** (NEW): 2 tests (real name · role; em-dash fallback).
- → **19 passed (4 files)**.

### Drive-through (US-6) — real chrome + real backend + real LLM-less login (Risk Class E clean restart)

**Risk Class E (resolved)**: `dev.py restart` reported new PID 42016 but a dev-login probe returned tenant WITHOUT plan/region = STILL OLD CODE. `Win32_Process` sweep found the cause: orphan worker **6824** (PPID 42820 — a DEAD reloader; StartTime 7:32PM = old 57.122 code) still held :8000 via SO_REUSEADDR, shadowing the new worker 27480. Killed 6824 + the new pair → :8000 free → clean `dev.py start backend` → fresh reloader **38744** + worker **7984** (10:56PM) sole owner. Re-probe dev-login → `plan:"enterprise", region:"global"` present = new code live (and proves the `dev_login` construction-site fix). Vite :3007 (node) NOT stopped.

**Drive A — login `dan@acme.com` / `acme-prod`** (→ /chat-v2):
| Surface | Observed (real) | Old fixture (gone) |
|---------|-----------------|--------------------|
| Sidebar name | `Dev Tenant (acme-prod)` | `acme-prod` |
| Sidebar meta | `acme-prod · Enterprise` | `tenant_01h9a2 · Pro` |
| Topbar pill | `Dev Tenant (acme-prod) · user` | `acme-prod · operator` |
| UserMenu | "Current tenant" → `Dev Tenant (acme-prod)` + region `global`, aria-current=true; **NO globex-eu/initech-jp** | "Switch tenant" → 3 fixtures |

`hasOldFixtureAcmeProd:false` (the `tenant_01h9a2 · Pro` literal is gone). Screenshot `artifacts/sprint-57-123-driveA-acme-prod-chrome-usermenu.png`.

**Drive B — login `globex-eu`** (→ /cost-dashboard): the chrome **FOLLOWS the session** → Sidebar `Dev Tenant (globex-eu)` · meta `globex-eu · Enterprise` · Topbar `Dev Tenant (globex-eu) · user`; `stillShowsAcmeProd:false` (no stale leak). Screenshot `artifacts/sprint-57-123-driveB-globex-eu-chrome-follows.png`.

**Verdict**: the chrome display FOLLOWS the real logged-in tenant (different tenant → different chrome), NOT a hardcoded fixture = **AP-4 Potemkin closed, load-bearing proven LIVE** (not gate-only). The "· Pro" → real "Enterprise" plan + the 3→1 tenant collapse are both visible. Note the topbar role label shows "user" (= `roles[0]` of the dev `_DEV_LOGIN_ROLES`; pre-existing behavior, unrelated to this change).

---
