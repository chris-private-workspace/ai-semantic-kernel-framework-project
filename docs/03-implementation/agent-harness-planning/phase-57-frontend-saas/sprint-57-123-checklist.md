# Sprint 57.123 — Checklist (Tenant-display real-data wiring: the app chrome renders a hardcoded fixture tenant — `Sidebar.tsx:90` `FIXTURE_TENANT`, `Topbar.tsx:122` `tenantName="acme-prod"`, `UserMenu.tsx:142-146` 3-element `TENANT_FIXTURES` — regardless of the logged-in tenant. The real tenant is ALREADY in `authStore.tenant` (`/auth/me`); this swaps the 3 fixtures to real data, adds `plan`+`region` to `/auth/me` (real `Tenant` columns), and collapses the UserMenu to the single real tenant. Visual/CSS byte-identical; NO migration/wire/codegen. CHANGE-090; NO design note)

[Plan](./sprint-57-123-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong; Prong-3 schema: confirm `Tenant.plan`/`Tenant.region` columns exist, NO new migration) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `937dd5ca`) — catalogue in progress.md
- [x] **Prong 1 — path verify**: all anchors present; NO existing `Topbar.test.tsx` (NEW); `CHANGE-090-*.md` free; i18n present (`userMenu` block en:57)
- [x] **Prong 2 — content verify** (drift findings → progress.md):
  - [x] **D-bootstrap-spread** ✅: whole-object `set` + `as AuthMeResponse` (no codegen) → +2 interface fields suffice
  - [x] **D-me-orm** ✅: `me()` loads full `Tenant` (`.plan`/`.region` available)
  - [x] **D-tenant-cols** ✅: `Tenant.plan` + `Tenant.region` NOT NULL, always present
  - [x] **D-3-construction-sites** ⚠️ NEW: `AuthMeTenant(` built at 3 sites (`me()`:384 + `dev_login()`:450 + `issue_session()`:511) → ALL 3 need +plan/+region (plan §8 updated)
  - [x] **D-dev-login-new-tenant** ⚠️ NEW: `dev_login` new-tenant branch has no Python-side plan/region → construct explicit `plan=ENTERPRISE, region="global"` (plan §8 updated)
  - [x] **D-i18n-keys** ✅: `switchTenant`/`region` exist → add `userMenu.currentTenant`
  - [x] **D-fixture-anchors** ✅: 3 fixtures confirmed; tenant-switcher only `!sidebarCollapsed`
  - [x] **D-other-consumers** ✅: dev page uses own `TenantOption` (not `AuthTenant`) → +2 required fields safe
  - [x] **D-seeded-tenant** ✅: dev-login offers 3 codes → multi-tenant drive-through feasible; picker labels OUT OF SCOPE (dev tool)
- [x] **Prong 3 — schema** ✅: `Tenant.plan`/`Tenant.region` columns EXIST — NO new table/migration
- [x] **D-baselines**: pytest **2695+5skip** · wire **24** · mockup **51** · mypy `src` **0/371** · run_all **10/10** (trusted from 57.122 merge; Vitest re-capture Day 3; full re-verify Day 4)
- [x] **Catalog drift**: progress.md Day-0 table + plan §8 +2 risk rows (NOT silently editing §3)
- [x] **Go/no-go**: GO (scope shift ≤20% — 3-construction-sites stays within "EDIT auth.py")

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-123-tenant-display-real-data` (from `main` `937dd5ca`)

---

## Day 1 — Backend `/auth/me` plan + region (US-1) + FE types (US-2)

### 1.1 `AuthMeTenant` + handlers (3 build sites per Day-0 D-3-construction-sites)
- [x] **`backend/src/api/v1/auth.py`** (EDIT): `AuthMeTenant` += `plan: str` + `region: str`; ALL 3 build sites (`me()`:384 + `dev_login()`:450 + `issue_session()`:511) carry `plan=tenant.plan.value`, `region=tenant.region`; `dev_login` new-tenant branch sets explicit `plan=TenantPlan.ENTERPRISE, region="global"`; `TenantPlan` import added. MHist + Last Modified
  - DoD: `/auth/me` JSON carries `tenant.plan` + `tenant.region`; mypy clean ✅
- [x] **`backend/tests/integration/api/test_auth_me.py`** (EDIT): `test_me_200_with_cookie` asserts plan/region defaults; NEW `test_me_tenant_plan_and_region_are_real` overrides region → proves real DB value
  - Verify: `pytest tests/integration/api/test_auth_me.py -q` → **6 passed** ✅

### 1.2 FE `AuthTenant` interface
- [x] **`frontend/src/features/auth/store/authStore.ts`** (EDIT): `AuthTenant` += `plan: string` + `region: string`; `bootstrap`/`fetchAuthMe` UNCHANGED. MHist
  - DoD: values flow via the unchanged whole-object `set` (tsc verified Day 2 build)

### 1.3 Backend + type gate
- [x] black/isort/flake8 ✅ · mypy `src` **0/371** ✅ · pytest test_auth_me **6 passed** ✅ (run_all deferred to Day 4 final sweep — backend src lints unaffected by this REST change)
  - Verify: `python -m black/isort/flake8 ... && python -m mypy src && pytest tests/integration/api/test_auth_me.py -q`

---

## Day 2 — Components (US-3 / US-4) + i18n

### 2.1 Sidebar tenant pill (US-3)
- [x] **`Sidebar.tsx`** (EDIT): dropped `FIXTURE_TENANT`; reads `authStore.tenant`; `formatPlan` title-case; `initial`/`name`/`meta=${code} · ${Plan}` from `tenant` ("—" fallback); classes byte-identical. MHist ✅
  - DoD: `FIXTURE_TENANT` gone; `.tenant-switcher`/`.tenant-avatar`/`.tenant-name`/`.tenant-meta` unchanged ✅

### 2.2 Topbar tenant pill (US-3)
- [x] **`layout/Topbar.tsx`** (EDIT): dropped `tenantName="acme-prod"`; `tenantName = tenant?.name ?? "—"`; render line unchanged. MHist ✅
  - DoD: "acme-prod" gone; `.tenant-pill`/`.dot` unchanged ✅

### 2.3 UserMenu collapse (US-4)
- [x] **`UserMenu.tsx`** (EDIT): dropped `TENANT_FIXTURES`; `activeTenant = tenant`; single real-tenant info row (name + real region, check, aria-current, `data-testid="usermenu-current-tenant"`); region row real; label → `userMenu.currentTenant`. MHist ✅
  - DoD: `globex-eu`/`initech-jp`/`TENANT_FIXTURES` gone; single real row; info row (not menuitem) = no dead control ✅

### 2.4 i18n key (US-4)
- [x] **en/common.json** + `userMenu.currentTenant` = "Current tenant" ✅
- [x] **zh-TW/common.json** + `userMenu.currentTenant` = "目前租戶" ✅ (kept `switchTenant` — pre-existing, not deleting)

### 2.5 FE gate
- [x] `npm run lint` clean ✅ · `npm run build` ✅ (tsc thread OK) · `styles-mockup.css` byte-identical ✅ · `check:mockup-fidelity` **51 baseline 51** ✅

---

## Day 3 — Tests (US-5) + Drive-through (US-6) — real chrome + real backend + real login

### 3.1 Frontend tests (US-5)
- [x] **`Sidebar.test.tsx`** (EDIT): +1 test — real pill name + `{code} · Plan`, NOT "acme-prod"/"tenant_01h9a2 · Pro" (5 tests) ✅
- [x] **`UserMenu.test.tsx`** (EDIT): `setAuthed` +plan/region; +1 test — single real tenant + region; NO globex-eu/initech-jp; "Current tenant" (7 tests) ✅
- [x] **`auth/authStore.test.ts`** (EDIT): `ME_PAYLOAD.tenant` +plan/region + 2 assertions (5 tests) ✅
- [x] **`Topbar.test.tsx`** (NEW): real name · role + em-dash fallback (2 tests) ✅
  - Verify: 4 files **19 passed** ✅

### 3.2 Clean restart / probe (Risk Class E — `auth.py` changed)
- [x] Orphan worker 6824 (PPID dead 42820, old code) held :8000 via SO_REUSEADDR — `Win32_Process` sweep → killed 6824 + new pair → clean `dev.py start` → fresh **38744**+**7984** sole owner; dev-login probe → `plan/region` present = new code live. Vite :3007 (node) NOT stopped ✅
  - DoD: backend serves NEW `/auth/me` (plan + region) ✅

### 3.3 Drive-through (chrome follows real session)
- [x] **Tenant A** (`dan@acme.com`/`acme-prod`): sidebar `Dev Tenant (acme-prod)` + `acme-prod · Enterprise`, topbar `Dev Tenant (acme-prod) · user`, UserMenu single real tenant + region `global`; NO globex-eu/initech-jp; `hasOldFixtureAcmeProd:false` ✅
- [x] **Tenant B** (`globex-eu`): chrome FOLLOWS → `Dev Tenant (globex-eu)` + `globex-eu · Enterprise`; `stillShowsAcmeProd:false` ✅
- [x] observed-vs-intended + 2 screenshots in progress.md + artifacts/. **AP-4 clear** — chrome follows real session (load-bearing LIVE, not gate-only) ✅

---

## Day 4 — CHANGE-090 + closeout (NO design note)

### 4.1 CHANGE-090
- [x] **`CHANGE-090-tenant-display-real-data.md`** (1-page, incl. the 2-tenant drive-through delta) ✅

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`frontend-fixture-to-real-data-wiring` 0.75 → re-point 0.90, ratio ~1.33) + progress.md final ✅
- [x] Final gate sweep: mypy **0/371** · run_all **10/10** (count 24) · full pytest **2696+5skip** · Vitest **892** · mockup **51** · `diff styles-mockup.css` empty ✅
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + memory subfile `project_phase57_123_tenant_display_real_data.md` · next-phase-candidates (`AD-FE-Tenant-Display-Fixture-Phase58` SHIPPED) · sprint-workflow matrix `frontend-fixture-to-real-data-wiring` 0.75→0.90 1st-point ✅
- [x] **Anti-pattern self-check** (retro Q5): AP-4 closed (chrome follows session — drive-through) / AP-1 / AP-2 / AP-3 / AP-6 → 0 violations ✅
- [ ] PR (push + open) — local commit done; **awaiting user confirm before `git push`** (destructive-confirm rule); CI → merge on green (gh-verified MERGED before main sync)
