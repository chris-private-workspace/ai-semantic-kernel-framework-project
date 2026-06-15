# Sprint 57.123 Plan — Tenant-display real-data wiring (`AD-FE-Tenant-Display-Fixture-Phase58`): the app chrome (sidebar tenant-switcher pill + topbar tenant pill + UserMenu tenant-switch list) renders a HARDCODED fixture tenant — `Sidebar.tsx:90` `FIXTURE_TENANT={name:"acme-prod", meta:"tenant_01h9a2 · Pro"}`, `Topbar.tsx:122` `tenantName="acme-prod"`, `UserMenu.tsx:142-146` a 3-element `TENANT_FIXTURES` (acme-prod/globex-eu/initech-jp + fake regions) — regardless of which tenant the logged-in user actually belongs to. The real tenant is ALREADY in `authStore.tenant` (`{id,name,code}`, fed by `GET /auth/me`), so the sidebar/topbar are a pure-frontend swap; the only backend touch is adding `plan` + `region` (real `Tenant` columns) to the `/auth/me` `AuthMeTenant` response so the fixture's fake "· Pro" plan badge + the UserMenu region row show real data. The 3-tenant UserMenu switcher (no real "list my tenants" backend — each user is JWT-scoped to ONE tenant) collapses to the single real current tenant. Closes the next C-class 主流量 Potemkin after the HITL载重 gap (57.122). Full-stack but small; NO migration / wire (count 24) / codegen. CHANGE-090; NO design note (feature-continuation data wiring — no new semantics, per `.claude/rules/sprint-workflow.md` §5.5).

**Status**: Approved-to-execute (user 2026-06-15: picked `AD-FE-Tenant-Display-Fixture-Phase58` as the next C-class Potemkin; scope resolved via AskUserQuestion 2026-06-15 — **後端補真 plan** (extend `/auth/me`) + **UserMenu 收斂成單一真租戶**).
**Branch**: `feature/sprint-57-123-tenant-display-real-data`
**Base**: `main` HEAD `937dd5ca` (post-#297 — Sprint 57.122 HITL policy read-side load-bearing).
**Slice**: `AD-FE-Tenant-Display-Fixture-Phase58` (a C-class 主流量 Potemkin — a fixture masquerading as real data on the always-visible chrome). Pure pattern-reuse (the authStore consumption pattern already powers the user/roles display in the SAME 3 components) → NO design note; CHANGE-090.
**Scope decisions** (AskUserQuestion 2026-06-15): (a) **後端補真 plan** — add `plan` + `region` (both real, NOT-NULL `Tenant` columns) to the `/auth/me` `AuthMeTenant` response; the sidebar meta shows `{code} · {Plan}` (real plan, Stage-1 = "Enterprise", honest — the fixture's "Pro" was fake) and the UserMenu region row shows the real region. (b) **UserMenu 收斂成單一真租戶** — drop the 3-fixture switcher; render only the single real current tenant (each user is JWT-scoped to one tenant; there is no "list my tenants" backend, so a multi-tenant switcher would itself be a Potemkin). (c) **Visual layer untouched** — the 3 components are verbatim mockup re-points; only the DATA (the component-logic layer per the CLAUDE.md Mockup-Fidelity two-layer split) is swapped fixture→real; the `.tenant-switcher` / `.tenant-pill` / tenant-row CSS classes + structure stay byte-identical → mockup-fidelity 51 UNCHANGED, no new oklch/hex literal. (d) NO migration (the columns exist — `plan` Sprint 56.1, `region` Sprint 57.46), NO new wire event / codegen (`/auth/me` is REST + a hand-written `as AuthMeResponse` cast, not SSE/codegen), NO new dependency.

---

## 0. Background

The always-visible app chrome shows a **hardcoded fixture tenant** on every page, for every logged-in user:

- **Sidebar** (`frontend/src/components/Sidebar.tsx:90`): `const FIXTURE_TENANT = { initial:"A", name:"acme-prod", meta:"tenant_01h9a2 · Pro" }` → rendered in the `.tenant-switcher` pill (`:152-156`). The comment at `:89` even says "AD-UserMenu-Tenant-Switch Sprint 57.21+ wires real".
- **Topbar** (`frontend/src/components/layout/Topbar.tsx:122`): `const tenantName = "acme-prod"` → rendered in the `.tenant-pill` (`:146-149`) as `{tenantName} · {roleLabel}`. Comment `:121`: "fixture name + first role; … Sprint 57.21+ wires real tenant API".
- **UserMenu** (`frontend/src/components/UserMenu.tsx:142-146`): a 3-element `TENANT_FIXTURES` array (`acme-prod`/`globex-eu`/`initech-jp` + fake regions `ap-east-1`/`eu-west-1`/`ap-northeast-1`) → rendered as a "Switch tenant" list (`:245-272`); `activeTenant` (`:184`) feeds the region row (`:313-316`). Comment `:141`: "Mockup fixture tenant list — replace with real API in Sprint 57.20+".

All three are **AP-4 Potemkin** (fixture masquerading as real on the 主流量): the displayed tenant is the same literal for every tenant, and the "· Pro" plan / `globex-eu`,`initech-jp` rows / `ap-east-1` regions are pure invention.

**The real data is ALREADY available** (Day-0 confirmed):

- `authStore.tenant` (`authStore.ts:41-45`, `AuthTenant = {id, name, code}`) is fed by `GET /api/v1/auth/me` via `fetchAuthMe()` → `bootstrap()` (`:72-86`, which does `set({ tenant: me.tenant })` — the WHOLE object). The same 3 components already consume `authStore.user` + `authStore.roles` from this store.
- `/auth/me` (`backend/src/api/v1/auth.py:344-386`) loads the full `Tenant` ORM (`:372` `select(Tenant)`) and returns `AuthMeTenant(id, name=tenant.display_name, code=tenant.code)` (`:382-386`). It does NOT currently return `plan` or `region`.
- `Tenant` (`backend/src/infrastructure/db/models/identity.py:102-182`) has `plan: TenantPlan` (`:124-128`, NOT NULL, `.value`="enterprise", Stage-1 single value per Sprint 56.1) and `region: str` (`:146-150`, NOT NULL, default "global", added Sprint 57.46). Both are always present.

### Design decision (extend `/auth/me` `AuthMeTenant` with `plan` + `region` [2 real columns, 1 handler line] → thread through the hand-written FE `AuthTenant` interface [+2 fields; `bootstrap` already spreads the whole tenant object] → swap the 3 fixtures to `authStore.tenant`, collapsing the UserMenu list to the single real tenant; visual/CSS layer byte-identical; NO migration / wire / codegen)

- **US-1** (backend): `AuthMeTenant` (`auth.py:134-137`) += `plan: str` + `region: str`; the `me()` handler (`:384`) builds them from `tenant.plan.value` + `tenant.region` (the full ORM is already loaded at `:372`). Extend `test_auth_me.py` to assert the two new fields carry the real DB values.
- **US-2** (frontend types): `AuthTenant` (`authStore.ts:41-45`) += `plan: string` + `region: string`. No other store change — `bootstrap` already does `set({ tenant: me.tenant })` (whole object) and `fetchAuthMe` is a hand-written `as AuthMeResponse` cast (no codegen), so the new fields flow automatically once the interface declares them.
- **US-3** (sidebar + topbar): `Sidebar.tsx` drops `FIXTURE_TENANT`, reads `authStore.tenant`, renders `initial = name[0]`, `name = tenant.name`, `meta = `${code} · ${Plan}`` (Plan = title-cased `tenant.plan`); `Topbar.tsx` drops `tenantName="acme-prod"`, reads `authStore.tenant.name`. Both keep the `.tenant-switcher`/`.tenant-pill` classes + structure byte-identical; null-tenant fallback "—" (defensive; the chrome renders behind `<RequireAuth>` so `tenant` is normally set).
- **US-4** (UserMenu collapse): drop `TENANT_FIXTURES`; read `authStore.tenant`; render ONE current-tenant row (name + real region, active check); the region row (`:313-316`) reads the real `tenant.region`; relabel the section from "Switch tenant" → "Current tenant" (a new i18n key `userMenu.currentTenant` in en + zh-TW) since a single-item list under "Switch tenant" would be a misleading label (AP-4).
- **US-5** (tests): backend `test_auth_me.py` (plan + region present + real values); frontend `Sidebar.test.tsx` / `UserMenu.test.tsx` / `authStore.test.ts` extended + a NEW `Topbar.test.tsx` — each asserts the chrome renders the MOCKED real tenant (name/code/plan/region), NOT the old "acme-prod"/"globex-eu" literals.
- **US-6** (drive-through): real chat-v2 chrome + real backend + real login — log in as tenant A → the sidebar/topbar/UserMenu show A's real name/code/plan/region; log in as a DIFFERENT real tenant → the chrome changes to follow the logged-in tenant (the load-bearing proof: the display follows the real session, not a fixture). Screenshots + observed-vs-intended.
- **US-7** (closeout): CHANGE-090 + retro Q1-Q7 + calibration (NEW class `frontend-fixture-to-real-data-wiring` 0.75 1st point) + navigators + next-phase-candidates (`AD-FE-Tenant-Display-Fixture-Phase58` shipped; the residual sidebar-chevron / future multi-tenant-switcher noted). NO design note (feature-continuation data wiring; no new decision semantics — per §5.5).
- **Rejected / deferred**: a real multi-tenant switcher (no "list my tenants" backend; each user is JWT-scoped to one tenant — a future RBAC/multi-membership slice); adding a `GET /tenants/current` endpoint (`/auth/me` already serves it — 95% per the Day-0 Explore); removing the sidebar tenant-switcher chevron / the "Switch tenant" tooltip (a deeper UX change = mockup structural drift; the pill now shows the REAL tenant, the chevron stays per mockup-fidelity); title-casing the plan on the backend (the backend returns the raw `.value`; the frontend formats for display — clean layer separation).

### Ground truth (Day-0 head-start — direct reads on `main` HEAD `937dd5ca`; ALL re-verified in the formal Day-0 三-prong §checklist 0.1)

**The fixtures (to change):**
- `Sidebar.tsx:90` `FIXTURE_TENANT` (render `:152-156`); already imports `useAuthStore` (`:58`), reads `user`/`roles` (`:97-98`).
- `Topbar.tsx:122` `tenantName="acme-prod"` (render `:146-149`); already imports `useAuthStore` (`:57`), reads `roles` (`:114`).
- `UserMenu.tsx:142-146` `TENANT_FIXTURES` (render `:245-272`); `activeTenant` (`:184`) → region row (`:313-316`); already imports `useAuthStore` (`:58`), reads `status`/`user`/`roles` (`:160-162`).

**The real-data sources (confirmed wired):**
- `authStore.ts:41-45` `AuthTenant={id,name,code}`; `:72-86` `bootstrap` `set({tenant: me.tenant})` (whole object). `authService.ts:135-142` `fetchAuthMe()` → `as AuthMeResponse` (hand-written cast, NO codegen).
- `auth.py:344-386` `me()` loads full `Tenant` (`:372`); builds `AuthMeTenant` (`:382-386`); `:134-137` `AuthMeTenant={id,name,code}`.
- `identity.py:124-128` `Tenant.plan` (NOT NULL, `.value`="enterprise"); `:146-150` `Tenant.region` (NOT NULL, "global").

**The contract (to extend):** `AuthMeTenant` (`auth.py:134-137`) + `AuthTenant` (`authStore.ts:41-45`) — both hand-written, mirrored by comment; add the same 2 fields to each.

**Test homes (confirmed):** `backend/tests/integration/api/test_auth_me.py` (EXTEND) · `frontend/tests/unit/components/Sidebar.test.tsx` (EXTEND) · `frontend/tests/unit/components/UserMenu.test.tsx` (EXTEND) · `frontend/tests/unit/auth/authStore.test.ts` (EXTEND) · `frontend/tests/unit/components/Topbar.test.tsx` (NEW — no existing Topbar test).

**Baselines (57.122 closeout)**: full pytest **2695+5skip** · wire **24** · FE Vitest (re-capture Day-0) · mockup-fidelity **51** · mypy `src` **0/371** · run_all **10/10**. Re-verify Day-0.

### STALE / drift anchors to re-confirm in the formal Day-0 三-prong (§ checklist 0.1)

(1) **Prong-1 path**: the 3 component files + `authStore.ts` / `authService.ts` / `auth.py` / `identity.py` + the 4 test homes exist as above; `CHANGE-090-*.md` free; NO new src file except the NEW `Topbar.test.tsx`. (2) **Prong-2 content**: `bootstrap` really spreads the whole `me.tenant` (so +2 interface fields suffice — no `set` change); `fetchAuthMe` is a hand-written cast (no codegen regen); the `me()` handler has the full `Tenant` ORM in hand (`.plan`/`.region` available); the i18n key `userMenu.switchTenant` + `userMenu.region` exist (locate the en + zh-TW `common.json` to add `userMenu.currentTenant`); confirm the Sidebar/Topbar tenant-switcher renders only when `!sidebarCollapsed` (no collapsed-state regression). (3) **Prong-3 schema**: N/A — `Tenant.plan` + `Tenant.region` columns EXIST (no new table / migration); confirm only. (4) Baselines re-verify (pytest 2695+5skip / wire 24 / Vitest re-capture / mockup 51 / mypy 0/371 / run_all 10/10). (5) The seeded `acme-prod` tenant's `display_name` / `code` (so the drive-through knows what "real" should render — and whether a 2nd tenant is needed to make the name-change visible).

## 1. Sprint Goal

The app chrome (sidebar tenant pill + topbar tenant pill + UserMenu tenant section) renders the REAL logged-in tenant — name + code + plan + region from `authStore.tenant` (fed by `/auth/me`, which now returns `plan` + `region` from the real `Tenant` columns) — instead of the hardcoded `acme-prod` / `tenant_01h9a2 · Pro` / 3-tenant fixture. The UserMenu collapses to the single real current tenant (no fake `globex-eu`/`initech-jp`). Closes `AD-FE-Tenant-Display-Fixture-Phase58` (a C-class 主流量 Potemkin). Proven by a real-login drive-through showing the chrome follows the logged-in tenant. Full-stack but small; NO migration / wire (count 24) / codegen; visual/CSS layer byte-identical (mockup-fidelity 51 unchanged). CHANGE-090; NO design note.

## 2. User Stories

- **US-1**: 作為 frontend chrome，我希望 `/auth/me` 回傳 `plan` + `region`（真實 `Tenant` 欄位），以便側欄 meta 與 UserMenu region 列能顯示真資料（取代假 "· Pro" / 假 region）。
- **US-2**: 作為 authStore，我希望 `AuthTenant` interface 加 `plan` + `region`（`bootstrap` 已整包灌入、`fetchAuthMe` 無 codegen），以便兩欄自動流通到所有消費者。
- **US-3**: 作為 Sidebar + Topbar，我希望租戶 pill 讀 `authStore.tenant`（name/code/plan），渲染真租戶名與 `{code} · {Plan}` meta，CSS class 與結構 byte-identical，以便消除假 `acme-prod` 顯示而不違反 mockup-fidelity。
- **US-4**: 作為 UserMenu，我希望收斂 `TENANT_FIXTURES` 成單一真租戶（name + 真 region + active check），section 標籤改 "Current tenant"，以便消除 3 假租戶 + 誤導的 "Switch tenant" 標籤。
- **US-5**: 作為 platform，我希望測試守住：後端 `test_auth_me.py`（plan + region 真值）+ 前端 Sidebar/Topbar/UserMenu/authStore 測試（渲染 mock 真租戶、非 "acme-prod"/"globex-eu" 字面），以便回歸受保護。
- **US-6**: 作為 user，我希望真 drive-through（真 chrome + 真 backend + 真 login）：登入租戶 A → chrome 顯示 A 的真名/code/plan/region；換登入另一真租戶 → chrome 隨之改變（顯示跟隨真 session，非 fixture）；截圖 + observed-vs-intended。
- **US-7**: 作為 future dev，我希望 CHANGE-090 + 收尾（retro Q1-Q7 + calibration + navigators + next-phase-candidates）記錄此 Potemkin 已修，以便可溯。

## 3. Technical Specifications

### 3.0 Architecture (backend `/auth/me` +2 fields → FE interface +2 fields [auto-thread] → 3 fixtures → `authStore.tenant`; UserMenu list collapse; visual/CSS byte-identical; NO migration / wire / codegen)

```
backend/src/api/v1/auth.py (EDIT): AuthMeTenant += plan + region; me() builds them from tenant.plan.value + tenant.region
backend/tests/integration/api/test_auth_me.py (EDIT): assert plan + region present + real values
frontend/src/features/auth/store/authStore.ts (EDIT): AuthTenant += plan + region  [bootstrap unchanged — already spreads whole tenant]
frontend/src/components/Sidebar.tsx (EDIT): drop FIXTURE_TENANT → authStore.tenant (name + code + Plan); null fallback "—"
frontend/src/components/layout/Topbar.tsx (EDIT): drop tenantName="acme-prod" → authStore.tenant.name
frontend/src/components/UserMenu.tsx (EDIT): drop TENANT_FIXTURES → single real tenant row + real region; relabel section
frontend/src/i18n/locales/{en,zh-TW}/common.json (EDIT): + userMenu.currentTenant
frontend/tests/unit/components/{Sidebar,UserMenu}.test.tsx (EDIT) + authStore.test.ts (EDIT) + Topbar.test.tsx (NEW)
docs: CHANGE-090 (NO design note)
migrations / events / sse / codegen / styles-mockup.css: UNTOUCHED
```

### 3.1 Backend `/auth/me` plan + region (US-1) — `auth.py`

- `AuthMeTenant` (`:134-137`): add `plan: str` + `region: str`.
- `me()` (`:382-386`): `AuthMeTenant(id=tenant.id, name=tenant.display_name, code=tenant.code, plan=tenant.plan.value, region=tenant.region)`. The full `Tenant` is already loaded (`:372`); `.plan` is `TenantPlan` (`.value` = the raw string) and `.region` is `str` — both NOT NULL.
- No other backend change (no migration — columns exist; no new endpoint).

### 3.2 Frontend types (US-2) — `authStore.ts`

- `AuthTenant` (`:41-45`): add `plan: string` + `region: string`. The comment "Mirrors backend AuthMeResponse" stays accurate.
- `bootstrap` (`:72-86`) UNCHANGED — `set({ tenant: me.tenant })` already carries the whole object. `fetchAuthMe` (`authService.ts:135-142`) UNCHANGED — `as AuthMeResponse` picks up the new JSON fields. MHist on `authStore.ts`.

### 3.3 Components (US-3 / US-4)

- **Sidebar.tsx**: drop `FIXTURE_TENANT` (`:90`); add `const tenant = useAuthStore((s) => s.tenant)`; in the `.tenant-switcher` block (`:144-159`): `initial = tenant?.name?.[0]?.toUpperCase() ?? "—"`, `name = tenant?.name ?? "—"`, `meta = tenant ? `${tenant.code} · ${formatPlan(tenant.plan)}` : "—"` (a tiny inline `formatPlan` = title-case). Classes/structure unchanged. MHist.
- **Topbar.tsx**: drop `const tenantName = "acme-prod"` (`:122`); add `const tenant = useAuthStore((s) => s.tenant)`; `const tenantName = tenant?.name ?? "—"`. Render line (`:148`) unchanged (`{tenantName} · {roleLabel}`). MHist.
- **UserMenu.tsx**: drop `TENANT_FIXTURES` (`:142-146`); add `const tenant = useAuthStore((s) => s.tenant)`; `const activeTenant = tenant` (real); the tenant section (`:241-272`) renders ONE row from `tenant` (name + region, active check, `aria-current`); the region row (`:313-316`) uses `tenant?.region ?? "—"`; relabel the section header (`:242`) `userMenu.switchTenant` → `userMenu.currentTenant`. The single row's onClick closes the menu (it IS the current selection — harmless, not a dead control; the check mark + aria-current make it honest). MHist.

### 3.4 i18n (US-4)

- Add `userMenu.currentTenant` to `frontend/src/i18n/locales/en/common.json` ("Current tenant") + `zh-TW/common.json` ("目前租戶"). Locate the existing `userMenu.switchTenant` block Day-0.

### 3.5 Drive-through (US-6) — real chrome + real backend + real login

1. Real backend (:8000) + Vite (:3007). Dev-login as tenant A (e.g. `acme-prod`).
2. Observe the sidebar pill (real name + `{code} · Enterprise` meta), the topbar pill (real name · role), the UserMenu (single real tenant + real region; NO globex-eu/initech-jp).
3. Log in as a DIFFERENT real tenant (a 2nd dev-login `tenant_code`) → the chrome changes to follow the logged-in tenant = the load-bearing proof (display follows session, not fixture).
4. Screenshots + observed-vs-intended in progress.md. AP-4 clear — every tenant field is real.

> If only one seeded tenant is reachable, the proof falls back to: the rendered meta (`code · Enterprise`) ≠ the old `tenant_01h9a2 · Pro`, AND the UserMenu shows 1 real tenant (not 3 fixtures) — both visibly real. The 2-tenant version is preferred (proves "follows session").

### 3.6 What is explicitly NOT done

A real multi-tenant switcher (no "list my tenants" backend; user is JWT-scoped to one tenant); a `GET /tenants/current` endpoint (`/auth/me` suffices); removing the sidebar chevron / "Switch tenant" tooltip (mockup structural drift — the pill now shows the real tenant); a migration / new wire event / codegen; any `styles-mockup.css` / CSS-class change.

### 3.7 Validation (US-1..US-7)

Gates: mypy strict `src` **0/371** (1 handler line + 2 schema fields — count unchanged or +0) · run_all **10/10** (count 24) · full pytest **2695+5skip + 0/-+** (test_auth_me extended) · Vitest **+N** (3 extended + 1 new) · mockup-fidelity **51 UNCHANGED** (no CSS/oklch change) · `diff styles-mockup.css` empty · migrations / events / sse / codegen **UNTOUCHED**. Plus: each FE test asserts the MOCKED real tenant renders (not the fixture literal); the drive-through proves the chrome follows the real session.

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/api/v1/auth.py` | EDIT — `AuthMeTenant` += `plan: str` + `region: str`; `me()` builds `plan=tenant.plan.value`, `region=tenant.region` |
| 2 | `backend/tests/integration/api/test_auth_me.py` | EDIT — assert `plan` + `region` present with real DB values |
| 3 | `frontend/src/features/auth/store/authStore.ts` | EDIT — `AuthTenant` += `plan: string` + `region: string` (bootstrap/fetchAuthMe UNCHANGED) |
| 4 | `frontend/src/components/Sidebar.tsx` | EDIT — drop `FIXTURE_TENANT` → `authStore.tenant` (name + `{code} · {Plan}` meta); null fallback |
| 5 | `frontend/src/components/layout/Topbar.tsx` | EDIT — drop `tenantName="acme-prod"` → `authStore.tenant.name` |
| 6 | `frontend/src/components/UserMenu.tsx` | EDIT — drop `TENANT_FIXTURES` → single real tenant + real region; relabel section |
| 7 | `frontend/src/i18n/locales/en/common.json` | EDIT — + `userMenu.currentTenant` ("Current tenant") |
| 8 | `frontend/src/i18n/locales/zh-TW/common.json` | EDIT — + `userMenu.currentTenant` ("目前租戶") |
| 9 | `frontend/tests/unit/components/Sidebar.test.tsx` | EDIT — render mocked real tenant (name + code + plan), not "acme-prod" |
| 10 | `frontend/tests/unit/components/UserMenu.test.tsx` | EDIT — single real tenant + real region, no globex-eu/initech-jp |
| 11 | `frontend/tests/unit/auth/authStore.test.ts` | EDIT — tenant shape includes plan + region from /auth/me |
| 12 | `frontend/tests/unit/components/Topbar.test.tsx` | NEW — pill renders mocked real tenant name |
| 13 | `claudedocs/4-changes/feature-changes/CHANGE-090-tenant-display-real-data.md` | NEW — change record (incl. the drive-through delta) |
| — | migrations / `events.py` / `sse.py` / codegen / `styles-mockup.css` / design note | **UNTOUCHED / NONE** |

## 5. Acceptance Criteria

1. `/auth/me` returns `plan` + `region` (real `Tenant` columns) in `AuthMeTenant`; `test_auth_me.py` asserts the real values.
2. `AuthTenant` (FE) declares `plan` + `region`; the values flow via the unchanged `bootstrap`/`fetchAuthMe`.
3. Sidebar pill renders `authStore.tenant` (real name + `{code} · {Plan}`), Topbar pill renders the real tenant name — the `acme-prod` / `tenant_01h9a2 · Pro` literals are gone; `grep "acme-prod" frontend/src` → 0 hits.
4. UserMenu renders the single real current tenant (name + real region, active check); `TENANT_FIXTURES` / `globex-eu` / `initech-jp` are gone; the section label is "Current tenant".
5. Visual/CSS layer byte-identical: `diff styles-mockup.css` empty; mockup-fidelity 51 unchanged; no new oklch/hex literal.
6. Gates: mypy 0/371 · run_all 10/10 (count 24) · pytest 2695+5skip (test_auth_me extended) · Vitest +N · migrations/events/sse/codegen UNTOUCHED.
7. Real drive-through PASS: the chrome shows the real logged-in tenant and changes when a different real tenant logs in (display follows session, not fixture); screenshots + observed-vs-intended (live, NOT gate-only).
8. `AD-FE-Tenant-Display-Fixture-Phase58` shipped; CHANGE-090; calibration recorded (`frontend-fixture-to-real-data-wiring` 0.75 1st point); navigators + next-phase-candidates updated. NO design note (feature-continuation).

## 6. Deliverables

- [ ] US-1 backend `/auth/me` += `plan` + `region` (`AuthMeTenant` + `me()` handler)
- [ ] US-2 FE `AuthTenant` += `plan` + `region` (auto-thread)
- [ ] US-3 Sidebar + Topbar real tenant pill (drop fixtures; classes byte-identical)
- [ ] US-4 UserMenu collapse to single real tenant + real region + relabel section + i18n key
- [ ] US-5 tests (backend test_auth_me + FE Sidebar/Topbar/UserMenu/authStore)
- [ ] US-6 drive-through PASS (chrome follows real session; screenshots + observed-vs-intended)
- [ ] US-7 CHANGE-090 + closeout (retro Q1-Q7 + calibration + navigators + next-phase-candidates: `AD-FE-Tenant-Display-Fixture-Phase58` shipped)

## 7. Workload Calibration

- Scope class **`frontend-fixture-to-real-data-wiring` 0.75** (NEW, 1st data point; pending 2-3 sprint validation). Shape: a C-class Potemkin fix — a small backend display-field add (2 real columns onto an existing endpoint, 1 handler line) + a FE type thread (auto via whole-object spread, no codegen) + a 3-component fixture→authStore data-swap (mechanical, the consumption pattern already exists for user/roles) + a UserMenu list collapse + i18n + 4 tests + a 2-tenant drive-through. More code than the tiny-code `chatv2-inspector-existing-field-surface` 0.85 (3 components + backend + 4 test files vs ~10 lines) but mechanical pattern-reuse; full ceremony MINUS a design note (feature-continuation). Set **0.75** explicitly informed by the Sprint 57.120/57.122 ceremony-not-code-accelerated lesson (full-ceremony parent-direct lands ~0.85-1.0; this is a touch lower for the mechanical FE swaps + no design note). If the 1st point lands > 1.20, re-point toward 0.90; if < 0.7, toward 0.55.
- **Agent-delegated: no** (parent-direct; the cross-stack thread + the UserMenu collapse + the live 2-tenant drive-through are best hand-authored). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~6.0 hr (backend schema+populate+test ~0.75 · FE type ~0.25 · Sidebar swap ~0.5 · Topbar swap ~0.25 · UserMenu collapse + i18n ~1.0 · FE tests (3 edit + 1 new) ~1.25 · drive-through ~1.0 · CHANGE-090 + closeout ~1.0) → class-calibrated commit ~4.5 hr (mult 0.75). Day-4 retro Q2 verifies (1st `frontend-fixture-to-real-data-wiring` data point).

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **D-3-construction-sites (Day-0 ⚠️)**: `AuthMeTenant(` is built at **3** sites (`me()`:384 + `dev_login()`:450 + `issue_session()`:511, password-login + MFA shared), not the single `me()` the plan §3.1 named → adding `plan`/`region` as REQUIRED fields breaks the 2 un-updated sites with a Pydantic 500 | update ALL 3 sites in the same `auth.py` edit (`me()`/`issue_session()` use `select(Tenant)` → loaded; see next row for `dev_login`); stays within the §4 #1 "EDIT auth.py" scope |
| **D-dev-login-new-tenant (Day-0 ⚠️)**: `dev_login()` (`auth.py:420-423`) auto-creates `Tenant(code,…)` with NO Python-side plan/region (server_default only) → accessing `.plan` on the fresh object risks an async lazy-load before a DB round-trip | construct the new dev Tenant with explicit `plan=TenantPlan.ENTERPRISE, region="global"` (= the server_defaults; dev-only path; add a `TenantPlan` import); the existing-tenant select path is already loaded |
| The seeded `acme-prod` tenant's `display_name` IS literally "acme-prod" → the sidebar/topbar NAME wouldn't visibly change → weak drive-through proof | Day-0 confirmed `dev_login` sets `display_name="Dev Tenant (<code>)"` for a new code; the meta (`code · Enterprise` ≠ `tenant_01h9a2 · Pro`) + the UserMenu collapse (3→1) are visible regardless; PREFER the 2-tenant drive-through (log in as a 2nd real tenant code) so the name change is unambiguous |
| `tenant` is `null` mid-bootstrap (status "unknown") → the pill renders "—" briefly | the chrome renders behind `<RequireAuth>` (tenant resolved before render); the `?? "—"` fallback is defensive only; acceptable transient |
| Touching the 3 verbatim-mockup components risks a mockup-fidelity regression | swap ONLY the data (component-logic layer); keep every CSS class + inline-style literal + structure byte-identical; `diff styles-mockup.css` empty + `check:mockup-fidelity` 51 in the gate; no new oklch/hex literal (the HEX_OKLCH baseline check) |
| `tenant.plan.value` formatting — raw "enterprise" looks unpolished vs the fixture's "Pro" | the backend returns the raw `.value`; the FE title-cases for display (`formatPlan`); "Enterprise" is honest (Stage-1 single plan) — the point is REAL, not pretty |
| A hidden 2nd consumer of `/auth/me` or `AuthMeResponse` breaks on the +2 required fields | the new fields are additive + always-present (NOT NULL columns); the FE interface makes them required but every real response carries them; Day-0 grep for other `AuthMeResponse`/`/auth/me` consumers |
| Frontend test setup for the NEW `Topbar.test.tsx` (router + i18n + theme + authStore providers) | mirror the existing `Sidebar.test.tsx` provider setup (same chrome component family); if the provider cost is high, fold the topbar assertion into an existing shell test instead (note in progress.md) |
| Risk Class E — a stale `--reload` backend serves old `/auth/me` (this sprint changes `auth.py`) | clean restart before the drive-through (kill ALL stale uvicorn reloader+worker PIDs / `Win32_Process` PID/PPID/StartTime sweep); confirm the fresh PID is the sole :8000 owner; capture a startup log line |
| Vite HMR serves stale FE during the drive-through | hard-reload the browser; do NOT stop the Vite/node process (per the user constraint — node also runs Claude Code) |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- **A real multi-tenant switcher** (list-my-tenants backend + membership model) — a future RBAC/multi-membership slice; today each user is JWT-scoped to one tenant.
- **A `GET /tenants/current` endpoint** — `/auth/me` already serves the chrome's need (95% per the Day-0 Explore).
- **Removing the sidebar tenant-switcher chevron / the "Switch tenant" tooltip** — a deeper UX/mockup change; the pill now shows the real tenant, the chevron stays per mockup-fidelity.
- **The `FIXTURE_UNREAD_COUNT=3`** notification fixture (`AppShellV2.tsx:79`) — a separate (non-tenant) chrome fixture; a different AD.
- Any migration / new wire event / codegen / SSE / `styles-mockup.css` change (count 24 unchanged).
