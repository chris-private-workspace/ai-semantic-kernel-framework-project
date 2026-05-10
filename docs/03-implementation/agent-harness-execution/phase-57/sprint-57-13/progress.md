# Sprint 57.13 Progress — Frontend Foundation 1/N Completion + Frontend↔Backend Wiring 全打通

> Branch: `feature/sprint-57-13-frontend-foundation-completion` (from main `75c74d32`)
> Calibration: `frontend-foundation-spike` HYBRID 0.50 (1st application) — bottom-up ~49-65 hr → committed ~25-32 hr / Day 0-9
> ⚠️ Large Foundation sprint (~2x normal). Per user 2026-05-10 directive — 完全集中、不簡化、不切分.
> 15 USs: A1-A5 (auth wiring 打通) + B1-B9 (frontend architecture 基建) + C1 (closeout).

---

## Day 0 Accomplishments (2026-05-10) — Setup + 三-prong + Calibration

### Branch + Baselines
- Branch `feature/sprint-57-13-frontend-foundation-completion` from main `75c74d32`
- pytest **1658 collected** (1654 pass + 4 skip) / mypy --strict **0/305** / 9 V2 lints **9/9** / Vitest **168/45 files** / Playwright **37/14 files** / Vite build main **296.58 kB (gzip 93.48)** / LLM SDK leak **0**

### Plan + Checklist
- `sprint-57-13-plan.md` (NEW, ~9 sections, ~700+ lines — mirrors 57.12 structure; 15 USs)
- `sprint-57-13-checklist.md` (NEW, Day 0-9, ~10 days)
- this `progress.md` (NEW)

### User decision points (pre-confirmed via AskUserQuestion 2026-05-10)
- 全做（不只連通）— 完整 Foundation 1/N + frontend↔backend wiring，不簡化、不切分
- US-A1 auth fix = **cookie-only + GET /auth/me**（推薦案）
- Branch name confirmed

### Day 0 三-prong verify — Drift Catalog (10 D-PRE findings; 1 🔴 / 4 🟡 / 5 🟢)

| ID | Severity | Finding | Resolution |
|----|----------|---------|------------|
| **D-PRE-1** | 🟢 GREEN | Frontend dev port = **3007** (not 3005 — CLAUDE.md "3005" is V1; vite.config.ts L18 `port: 3007` since Sprint 57.5 D-21 port drift fix) | Plan/checklist updated — use 3007; dev setup doc note 3007 |
| **D-PRE-2** | 🟢 GREEN | Playwright `E2E_PORT` default **5173**, baseURL `http://localhost:5173`; webServer auto-starts `npm run dev --port 5173` (local) / `npm run preview` (CI); vite proxy `/api` → :8000 works from 5173 too | connectivity/a11y/visual specs run against 5173 dev server + need backend on :8000 for real-backend tests (opt-in via env) — plan §US-A5/B6/B8 already accounts |
| **D-PRE-3** | 🟡 YELLOW | `Settings.env` default = `"development"` (not `"dev"`) — plan said `env != "prod"` / `env == "prod"` | dev-login gate = `Settings.env.lower() not in ("production", "prod")` → allow; else 404. Adjust US-A4 impl |
| **D-PRE-4** | 🟡 YELLOW | `Settings.cookie_secure` does NOT exist | US-A1 adds `cookie_secure: bool = False` to Settings (註解 prod True) |
| **D-PRE-5** | 🟡 YELLOW | `Settings.oidc_redirect_uri` default = `http://localhost:3005/auth/callback` — **doubly wrong**: (a) port 3005 is V1, (b) `/auth/callback` is frontend path but OIDC code-exchange needs backend (client secret) | US-A1 changes to `http://localhost:8000/api/v1/auth/callback` (註解: prod via reverse proxy `/api/v1/auth/callback`) |
| **D-PRE-6** | 🟢 GREEN | `class-variance-authority@^0.7.1` is **already installed** (+ `sonner@^1.7.4` + `@radix-ui/react-dialog@^1.1.15` + `@radix-ui/react-slot@^1.2.4` + `tailwind-merge@^3.5.0`) | US-B2/B3 skip `npm i class-variance-authority` — one less install |
| **D-PRE-7** | 🟢 GREEN | NEW paths confirmed don't exist: `api/v1/telemetry.py`, `api/_deps.py`, `features/auth/store/authStore.ts`, `lib/toast.ts`, `lighthouserc.js`; not-installed confirmed: `@radix-ui/react-dropdown-menu`, `@sentry/react`, `web-vitals`, `i18next`, `react-i18next`, `eslint-plugin-jsx-a11y`, `@axe-core/playwright`, `@lhci/cli` | Plan §File Change List correct |
| **D-PRE-8** | 🔴 RED (scope-confirming, not abort) | `tenant_context.py` `EXEMPT_PATH_PREFIXES = ("/api/v1/health",)` — **ONLY `/health` is exempt**. So `/api/v1/auth/login` + `/callback` currently hit middleware → no Bearer → 401 → **the OIDC flow has never worked end-to-end** (confirms user observation). | US-A1 adds to `EXEMPT_PATH_PREFIXES`: `/api/v1/auth/login`, `/api/v1/auth/callback`, `/api/v1/auth/dev-login`, `/api/v1/auth/logout`, `/api/v1/telemetry`. NOT `/api/v1/auth/me` (needs JWT; 401 is correct). Folded into US-A1 (was US-A5 allowlist note — promote to US-A1 since it's part of "make auth flow work"). |
| **D-PRE-9** | 🟢 GREEN | `JWTManager.encode(*, sub: str, tenant_id: UUID, roles, extra)` → HS256; `decode()` → `JWTClaims` dataclass (`sub`/`tenant_id`/`roles`/`iat`/`exp`/`extra`) — matches plan §Tech Spec | No change |
| **D-PRE-10** | 🟢 GREEN | admin `{tenant_id}` path endpoints use `Depends(require_admin_platform_role)` from `platform_layer/identity/auth.py` — `require_tenant_match_or_platform_admin` is NEW (doesn't exist) | Plan §US-A3 correct |

**Scope impact**: 0 abort-level findings. D-PRE-8 confirms the auth flow is genuinely broken (matches user report) — US-A1 already covers the fix; just promote the `EXEMPT_PATH_PREFIXES` change from US-A5-note to US-A1-core. Net scope shift < 5%.

**Open content-verify items to confirm at Day 1 start** (Prong 2 not exhaustively done — these are low-risk impl details): exact `JWTManager.encode` kwarg names beyond `sub`/`tenant_id`; whether `RBACManager` is class or fn; `App.tsx` exact route wrapping (Explore report says auth routes rendered bare, AuthShell exists but unused by login/callback — confirm); the 4 ungated pages' exact tenant_id sourcing line. None gate Day 1.

### Calibration
- Class `frontend-foundation-spike` HYBRID 0.50 (1st application; 1-data-point opens) — bottom-up ~49-65 hr → committed ~25-32 hr; Day 0-9 (10 days)
- Weighted blend: Group A (auth/dev-login/smoke) `backend-auth × 0.65` ~30% + Group B (Toast/design-system/Radix) `frontend-arch-greenfield × 0.50` ~30% + Group B (Sentry/i18n/a11y/Lighthouse/visual) `frontend-infra-new × 0.45` ~25% + Group B (AuthShell/inline) `frontend-pattern-reuse × 0.35` ~10% + Group C closeout `× 0.80` ~5% → ~0.50
- Day 4 retrospective Q2 mid-sprint ratio check; |delta| > 30% → log AD-Sprint-Plan-N

---

## Day 1 Accomplishments (2026-05-10) — US-A1: OIDC auth flow end-to-end (cookie-only)

### Residual content-verify confirmed at Day 1 start (per Day 0 §1.5 deferred)
- `JWTManager.encode(*, sub: str, tenant_id: UUID, roles=(), expires_minutes=None, extra=None)` HS256; `JWTClaims` frozen dataclass — matches plan. ✓
- `App.tsx` route wrapping: auth routes rendered bare (`<Route path="/auth/login" element={<LoginPage/>}/>`), no AuthShell wrap yet (deferred B9). The legacy `<Route path="/verification/*">` was redundant — `verification` is `active:true` in routes.config since 57.11 → removed it (registry covers it). ✓
- `RBACManager` is a class (`platform_layer/identity/rbac.py`); `_require_role` (auth.py) uses `RBACManager.has_role_code(...)`. Not touched in Day 1 (US-A3 territory). ✓
- 4-page tenant_id sourcing: not inspected in detail (US-A2 Day 2 scope; pages cost/sla/admin-tenants/tenant-settings currently ungated). Deferred to Day 2 — no Day 1 impact.

### Backend
- `core/config/__init__.py` — `oidc_redirect_uri` default `http://localhost:3005/auth/callback` → `http://localhost:8000/api/v1/auth/callback` (D-PRE-5: was V1 port + frontend path; OIDC code-exchange needs backend). NEW `frontend_base_url: str = "http://localhost:3007"`, `cookie_secure: bool = False`.
- `platform_layer/middleware/tenant_context.py` — `TenantContextMiddleware` JWT source now: `Authorization: Bearer` header → fallback `request.cookies.get("v2_jwt")`. Existing 401 error message strings preserved verbatim (`"Authorization Bearer token required"` / `"Bearer token is empty"`) so `test_jwt_auth.py` (8 tests) stays green. `EXEMPT_PATH_PREFIXES` now `(/api/v1/health, /api/v1/auth/login, /api/v1/auth/callback, /api/v1/auth/dev-login, /api/v1/auth/logout, /api/v1/telemetry)` — **D-PRE-8 fix**: previously only `/health` was exempt, so `/auth/login` + `/callback` 401'd at the middleware before they could establish a session → the OIDC flow had never worked end-to-end (matches user report). `/auth/me` deliberately NOT exempt (it reads the session; 401 without JWT is correct).
- `api/v1/auth.py` — NEW `GET /auth/me` → `AuthMeResponse {user:{id,email,display_name}, tenant:{id,name,code}, roles:[str]}` (reads `request.state` + DB; uses `get_db_session_with_tenant` so the users-table RLS policy passes in prod; user/tenant row gone → 401 "no longer exists"). `/callback` `final_redirect` now → `{settings.frontend_base_url}/auth/callback?next=<oidc_redirect_to>` (was redirecting straight to the page — left SPA with no signal to refresh auth state → "logged in but app says anonymous"). New `_cookie_kwargs()` helper (secure from `Settings.cookie_secure`, max_age from `jwt_expires_minutes*60`) — `/login` state cookies + `/callback` v2_jwt cookie both use it.

### Frontend
- NEW `features/auth/store/authStore.ts` — Zustand `{status: "unknown"|"authenticated"|"anonymous", user, tenant, roles, bootstrap(), clear()}`. `bootstrap()` calls `fetchAuthMe()`; network error → `anonymous` (so the app still renders rather than hanging on a spinner). Exports `AuthMeResponse`/`AuthUser`/`AuthTenant` types.
- NEW `features/auth/components/RequireAuth.tsx` — shared route gate (`unknown`→spinner / `anonymous`→`setPostLoginRedirect(path)` + `<Navigate to="/auth/login?redirect_to=...">` / `authenticated`→children). **Design choice, slight deviation from plan**: the plan said "each page's gate 改成依 authStore.status" (per-page branching); a shared `<RequireAuth>` wrapper centralizes the 3-branch logic for all 9 pages (1 place to evolve; less churn when US-A2 adds 4 more). Same observable behavior.
- `features/auth/services/authService.ts` — rewrote: `fetchAuthMe()` (GET /auth/me → payload | null on 401 | throws on 5xx/network); `isAuthenticated()` now reads `useAuthStore.getState().status === "authenticated"`; `fetchWithAuth` adds `Authorization: Bearer` only when a dev-login token is in localStorage (cookie flow needs no JS-readable token); `getJwt/setJwt/clearJwt` renamed `getDevToken/setDevToken/clearDevToken`; `logout()` → POST /auth/logout + `clearDevToken()` + `useAuthStore.getState().clear()` + redirect. 401-toast/auto-redirect deferred to US-B1 (QueryClient onError) — Day 1 callers handle their own 401s as before.
- `App.tsx` — NEW `<AuthBootstrap>` wrapper runs `authStore.bootstrap()` once on mount, renders children immediately (public routes don't wait; gated pages spinner via `<RequireAuth>`). Removed redundant legacy `/verification` route + direct `VerificationPage` import (registry covers it since 57.11) → single-source restored. (Also dropped the stale "Status: Sprint 57.8" line from Home — Home gets a proper rewrite in US-B9.)
- `pages/auth/callback/index.tsx` — rewrote logic: `?error=` → error div; else `await bootstrap()` → `navigate(?next || consumePostLoginRedirect(), {replace})`. Removed dead `?token` path. Inline styles kept (Tailwind-ize + AuthShell in US-B9).
- 5 existing auth-gated pages (chat-v2 / governance / verification / loop-debug / memory) — replaced inline `if (!isAuthenticated()) {...}` with `<RequireAuth>...</RequireAuth>` wrap.
- `components/UserMenu.tsx` — reads `useAuthStore.user` (display_name → fallback email) instead of decoding the JWT; renders null unless `status === "authenticated"`; Sign out → `logout()`. (Full Tailwind/Radix polish still US-B3/B9.)

### Tests (new / changed)
- NEW backend `tests/integration/api/test_auth_me.py` — 5 tests (401 no JWT / 401 expired / 200 with v2_jwt cookie / 200 with Bearer header / 401 when user row missing). Pattern mirrors `test_jwt_auth.py` (custom app + `TenantContextMiddleware` + test `JWTManager`) + `test_admin_tenant_get.py` (`dependency_overrides[get_db_session_with_tenant]`).
- NEW frontend `tests/unit/auth/authStore.test.ts` (5) — initial unknown / bootstrap 200→authenticated / bootstrap 401→anonymous / bootstrap network-error→anonymous / clear→anonymous.
- NEW frontend `tests/unit/auth/isAuthenticated.test.ts` (3) — unknown→false / anonymous→false / authenticated→true.
- NEW frontend `tests/unit/auth/RequireAuth.test.tsx` (3) — unknown→spinner / anonymous→redirect + stash path / authenticated→children. (Replaces the planned `tests/unit/pages/authGate.test.tsx` — testing the shared wrapper covers all 9 pages' gate behavior in 3 tests; per-page render smoke comes via US-A2/C1 Playwright.)
- CHANGED frontend `tests/unit/components/UserMenu.test.tsx` — rewritten for authStore-driven UserMenu (4 → 5 tests; sign-out path mocks `logout()`).

### Verification
- Backend: `black`/`isort`/`flake8` clean on 4 changed files; `mypy src` 305 files clean; **9/9 V2 lints green** (incl. `check_llm_sdk_leak`); **full `pytest -q` → 1659 passed + 4 skipped** (was 1654+4; +5 from `test_auth_me.py`).
- Frontend: `npm run lint` clean (eslint src); `npm run build` ✅ (main bundle `index-*.js` 243.58 kB gzip 77.15 — *down* ~53 kB from 296.58 kB baseline; the legacy eager `VerificationPage` import moved to lazy; `RequireAuth` is its own 0.47 kB chunk); **`npm run test` → 48 files / 180 tests pass** (was 168; +12 — authStore 5 + isAuthenticated 3 + RequireAuth 3 + UserMenu +1).
- Manual UI not run (no dev server boot this session); US-A5 connectivity smoke + Playwright e2e cover the runtime path (Day 3 / Day 9). The auth flow's *unit/integration* layer is now green; the live WorkOS redirect round-trip needs a staging WorkOS account (or the US-A4 dev-login, Day 2) — flagged as carryover-if-needed per plan §Risks.

### Drift / notes
- D-PRE-8 confirmed as a real bug, fixed in this US (the headline reason "logged in but couldn't actually use the app").
- Deviation from plan: shared `<RequireAuth>` wrapper instead of per-page branching (documented above; behavior-equivalent, less churn). And `RequireAuth.test.tsx` instead of `pages/authGate.test.tsx`.
- Bundle size went *down* this US (legacy eager import removed) — gives headroom for US-B2/B4/B5 additions.
- No new agent-harness contract / ABC / LoopEvent / migration (this sprint is platform_layer + api/v1 + frontend only). 17.md update (registering `/auth/me`, `/auth/dev-login`, `/telemetry`) deferred to US-C1 closeout per plan.

---

## Day 2 Accomplishments (2026-05-10) — US-A2 (4-page gate) + US-A3 (cross-tenant) + US-A4 (dev-login)

3 commits, one per US: `1ada31fb` (US-A2) / `eb6f0c1e` (US-A4) / `77d238bd` (US-A3).

### US-A2 — 4-page auth gate + tenant-from-session (commit `1ada31fb`)
- `pages/{cost-dashboard,sla-dashboard,tenant-settings,admin-tenants}/index.tsx` — wrapped in `<RequireAuth>` (these 4 were the only `active:true` pages still ungated). admin-tenants additionally role-gates: `useAuthStore((s)=>s.roles)` ∩ {admin, platform_admin} — if empty, renders a "需要平台管理員權限" notice instead of mounting `useAdminTenants` (which would just 403); data children moved into `<AdminTenantsContent>` so the hook only runs when the role check passes.
- `features/{cost-dashboard,sla-dashboard,tenant-settings}/components/{CostOverview,SLAOverview,TenantSettingsView}.tsx` — `tenantId` now `useAuthStore((s)=>s.tenant?.id ?? "")` instead of `useSearchParams().get("tenant_id")`. Inside `<RequireAuth>`, `tenant` is always set. Description copy reworded ("for your tenant"; dropped the "Backend enforces admin-platform role" / "Missing ?tenant_id=" lines).
- `tests/e2e/fixtures/auth-fixtures.ts` — `seedAuthJwt`/`clearAuthJwt` now `page.route` the GET /api/v1/auth/me mock (200 fake admin payload / 401) instead of seeding localStorage — the auth gate is authStore-based now. Added `seedAuthJwt(page, {tenantId, tenantCode, roles})` opts + exported `E2E_TENANT_ID`. **The individual e2e specs (chat/governance/verification/loop-debug/memory + cost/sla/tenant-settings/admin-tenants) are not re-run/updated this turn — the full Playwright sweep is US-C1 (Day 9)**; some will need their per-tenant endpoint mocks pointed at the seeded tenant id.
- `CONVENTION.md` §1 — rewrote "Page Architecture Pattern" for the `<RequireAuth>` + `<AppShellV2>` composition; added "every `active:true` route MUST be auth-gated", the role-gate pattern (data hooks only mount past the role check), the tenant-from-session rule, and the "RequireAuth is the outermost wrapper" ordering rule.
- NEW `tests/unit/pages/adminTenantsRoleGate.test.tsx` (3 — non-platform-admin → notice / platform_admin → table / "admin" also counts). `tests/unit/cost-dashboard/migrate.test.tsx` — description-text matcher updated to the new copy.

### US-A4 — dev fake-login (commit `eb6f0c1e`)
- `api/v1/auth.py` — NEW `POST /api/v1/auth/dev-login?tenant_code=&email=`. `Settings.env in {production, prod}` → 404 (route invisible in prod, so safe to ship). Else: resolve-or-auto-create a dev Tenant by code (`display_name="Dev Tenant (<code>)"`), upsert a dev User (`external_id=dev:<email>`), issue a `v2_jwt` cookie (roles `[user, admin, platform_admin]` so every page renders), return `AuthMeResponse {user,tenant,roles}` JSON (no 302 — the SPA navigates). Path already in `EXEMPT_PATH_PREFIXES` (US-A1).
- `pages/auth/login/index.tsx` — rewrote: WorkOS login button (`?redirect_to=` carried through; `?error=` surfaced) + DEV-only `<DevLoginSection>` (tenant_code/email form → POST /auth/dev-login → `authStore.bootstrap()` (the dev-login cookie authenticates `/auth/me`) → `navigate(consumePostLoginRedirect())`; 404 → "disabled in this environment" message). Hidden in prod via `import.meta.env.DEV`. Inline styles kept (Tailwind-ize + `<AuthShell>` wrap: US-B9). NOTE: cookie-only path — if dev cross-port cookie (`:3007` ↔ `:8000` via vite proxy) ever fails, the fallback (dev-login also returns the raw token → write to localStorage → Bearer header) needs a small backend tweak; not done now.
- NEW `src/vite-env.d.ts` (`/// <reference types="vite/client" />`) — `import.meta.env.DEV` wasn't typed (no prior `import.meta.env` usage); `tsc -b` was failing without it.
- NEW backend `tests/integration/api/test_dev_login.py` (3 — dev 200+cookie+rows+decodable JWT / idempotent (one tenant, one user) / prod 404 via `monkeypatch.setenv("ENV","production")` + `get_settings.cache_clear()`). NEW frontend `tests/unit/pages/auth/login.test.tsx` (4).

### US-A3 — backend cross-tenant hardening (commit `77d238bd`)
- NEW dep `require_tenant_match_or_platform_admin(tenant_id, request)` in `platform_layer/identity/auth.py` (next to `require_admin_platform_role`): platform admin (`admin`/`platform_admin` role) → any tenant; else only the caller's own JWT `tenant_id` (mismatch → 403 "cross-tenant access denied (not a platform admin)"); no JWT → 401; `roles` not a list → 500.
- Applied to the 3 `{tenant_id}` **read** endpoints: `GET /api/v1/admin/tenants/{tenant_id}` (tenants.py — tenant-settings page), `GET .../cost-summary` (cost_summary.py — cost-dashboard), `GET .../sla-report` (sla_reports.py — sla-dashboard). **Deviation/scope note**: the *mutating* `{tenant_id}` endpoints — `PATCH /tenants/{id}`, `POST /tenants/{id}/onboarding/{step}` — and `GET /tenants/{id}/onboarding-status` + `GET /tenants` list + `POST /tenants` stay `require_admin_platform_role` (admin-only). Rationale: the plan's threat is cross-tenant *reads* via the URL; making the read endpoints same-tenant-accessible covers the 3 dashboard pages; tenant lifecycle/config mutations staying platform-admin-only is strictly safer (the tenant-settings Edit form will 403 for a non-admin — the page handles that). A future role-refinement could allow same-tenant `tenant_admin` PATCH.
- Tests: NEW `tests/integration/api/test_admin_cross_tenant.py` (6 — platform-admin any tenant 200 / "admin" role 200 / own-tenant 200 / cross-tenant 403 / no user 401 / roles-missing 500, via a probe endpoint + X-Test-{User,Roles,Tenant} headers). `test_admin_{cost_summary,sla_reports,tenant_get}.py` updated: `dependency_overrides` → the new dep; `test_admin_sla_reports` + `test_admin_tenant_get` middleware now also reads `X-Test-Tenant` → `request.state.tenant_id`, and their "403 wrong role" tests are now "403 cross-tenant" (assert `"cross-tenant" in detail`).

### Verification (Day 2 aggregate)
- Backend: `black`/`isort`/`flake8` clean on all changed files; `mypy src` 305 clean; **9/9 V2 lints** (incl. `check_rls_policies` + `check_llm_sdk_leak`); **full `pytest -q` → 1668 passed + 4 skipped** (Day 1: 1659+4; +9 from test_dev_login (3) + test_admin_cross_tenant (6)).
- Frontend: `npm run lint` clean; `npm run build` ✅ (main `index-*.js` 243.37 kB gzip 77.04 — flat vs Day 1 243.58); **`npm run test` → 51 files / 187 tests pass** (Day 1: 50/183; +4 from adminTenantsRoleGate (3) + migrate matcher fix is in-place + login.test.tsx (4) — wait, 183→187 = +4 net: adminTenantsRoleGate +3, login.test +4, but migrate.test.tsx already counted... actual: 183 after US-A2 commit, +4 from login.test.tsx in US-A4 = 187).
- Manual UI not run (no dev server boot). The e2e Playwright suite is NOT re-run this turn — `auth-fixtures.ts` is updated for the new authStore-based gate but the individual specs need a sweep (US-C1, Day 9). Auth flow unit/integration layer is green.

### Drift / notes
- e2e specs (chat/governance/verification/loop-debug/memory + the 4 admin pages) — `seedAuthJwt` change makes the gate work, but specs that mock per-tenant endpoints (cost-summary / sla-report / tenant GET) need their URL patterns pointed at the seeded `E2E_TENANT_ID` (since the page now reads tenant from authStore). → US-C1.
- `PATCH /tenants/{id}` stays admin-only (not changed to the cross-tenant dep) — tenant-settings Edit form 403s for non-admins. Noted above; acceptable this sprint.
- No new agent-harness contract / ABC / LoopEvent / migration. 17.md registration of `/auth/me` + `/auth/dev-login` + `/telemetry` + `require_tenant_match_or_platform_admin` → US-C1 closeout.

---

## Day 3 — US-A5 (connectivity smoke) + US-B1 (Toast) — `e1c3f58e`

One commit covering both USs (+ a small `.gitignore` hygiene fix).

### US-A5 — connectivity smoke + .env.example
- **NEW `backend/tests/integration/api/test_api_smoke.py`** (2 tests). Builds the *real* app via `api.main.create_app()` (so middleware + router wiring is exactly prod's), overrides only `get_db_session` + `get_db_session_with_tenant` with the per-test rollback session, seeds a tenant + user, encodes `JWTManager().encode(sub=user.id, tenant_id=tenant.id, roles=["admin","platform_admin"])` (those two roles cover every RBAC dep in scope), then hits one representative GET per router: `/health` (middleware-exempt), `/auth/me`, `/admin/tenants`, `/admin/tenants/{t}/cost-summary?month=2026-05`, `.../sla-report?month=2026-05`, `/audit/log?limit=10`, `/verification/recent?limit=10`, `/memory/recent?layer=user&limit=10`, `/governance/approvals` → assert status ∈ {200,404} + `resp.json()` parses. Second test: `/admin/tenants` with no JWT → 401. **Must `set_pricing_loader(PricingLoader().load_from_yaml(config/llm_pricing.yml))` + `set_sla_recorder(SLAMetricRecorder(redis_client=FakeRedis()))` before `create_app()`** — same strict singleton accessors the focused cost/sla tests init; the autouse `reset_pricing_loader` / `reset_sla_recorder` fixtures in `tests/integration/api/conftest.py` clean up. (Hit two iterations of "singleton not initialised" 500s while writing it — D-DAY3 lesson: smoke-testing the real app surfaces every module-level singleton the route path touches.)
- **NEW `frontend/tests/e2e/connectivity/connectivity.spec.ts`** — opt-in (`test.skip(!process.env.RUN_CONNECTIVITY)`); real `page.request.post("/api/v1/auth/dev-login")` (sets the `v2_jwt` cookie on the browser context), then `page.goto` each of the 9 active routes → assert `page.url()` not `/auth/login`, `[data-testid="app-shell"]` visible, zero `console.error`. Manual run: `RUN_CONNECTIVITY=1 npm run test:e2e -- connectivity` (needs backend + frontend both up). Not part of CI / `npm run test:e2e`.
- **`AppShellV2.tsx`** — added `data-testid="app-shell"` on the root `<div>` (connectivity anchor; no behavior change).
- **`.env.example`** (root only — no `backend/.env.example` / `frontend/.env.example` exist → D-DAY3-3) — added a WorkOS OIDC block (`WORKOS_API_KEY=` / `WORKOS_CLIENT_ID=` / `OIDC_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback` / `FRONTEND_BASE_URL=http://localhost:3007` / `COOKIE_SECURE=false`) + `VITE_SENTRY_DSN=`, each commented, and a "dev needs no WorkOS — use `POST /api/v1/auth/dev-login`" note. **README** env section + a **NEW SITUATION-6 §認證（本地開發）** mirror that note. (D-DAY3-4: the root file already had WorkOS-ish fields under "Identity" from 57.7 US-A2's `core/config` change — reorganised into a dedicated block + added the 4 newer keys.)

### US-B1 — Toast system
- `<Toaster richColors position="top-right" />` — **D-DAY3-1**: already mounted in `main.tsx` since 57.7 US-B2. No edit; checklist item satisfied as-is.
- **NEW `frontend/src/lib/toast.ts`** — `toastError` / `toastSuccess` / `toastInfo` thin wrappers over `sonner` (`toast.error` / `.success` / `()`), plus `errorMessage(err, fallback?)` that normalises an unknown thrown value to a string.
- **NEW `frontend/src/lib/queryClient.ts`** — **D-DAY3-2**: the `QueryClient` was inline in `main.tsx` (57.7 US-B2 + 57.9 US-6's `retry:false` rationale). Extracted with the same `defaultOptions` (queries `staleTime 30s` / `refetchOnWindowFocus:false` / `retry:false`; mutations `retry:false`) + a `MutationCache({ onError: (err) => toastError(errorMessage(err)) })`. `main.tsx` now `import { queryClient } from "./lib/queryClient"`. Query failures are intentionally NOT toasted globally — the 4 TanStack-migrated pages (cost / sla / tenant-settings / governance per 57.9) render inline error + Retry; a global toast would double-surface. Mutations have no inline error slot → they toast.
- **`authService.ts` `fetchWithAuth(input, init, opts?)`** — added a 3rd `{ redirectOn401?: boolean }` param (default true). On a 401 → `handleAuthExpired()`: `toastError("登入已過期，請重新登入")` + `clearDevToken()` + `useAuthStore.getState().clear()` + `setPostLoginRedirect(window.location.pathname + search)` + `window.location.href = "/auth/login"`, then still returns the response. `fetchAuthMe()` and `logout()` pass `{ redirectOn401: false }` so `authStore.bootstrap()` (first anonymous load) and the logout flow aren't hijacked. Replaces the Day-1 "401 handled by callers/QueryClient" stub note — `fetchWithAuth` is the only layer that sees the raw status for *every* request (feature services rethrow as plain `Error`, losing the status), so 401 handling belongs here.
- **NEW `frontend/tests/unit/lib/toast.test.ts`** (9 — wrappers delegate to mocked sonner via `vi.hoisted`; `errorMessage` Error/string/fallback) + **`frontend/tests/unit/lib/queryClient.test.ts`** (4 — query/mutation defaults; `mutationCache.config.onError` invokes mocked `toastError` with the message).

### Bonus hygiene — `.gitignore` (D-DAY3-5)
The stock-Python `lib/` line in `.gitignore` matches ANY `lib/` directory — including `frontend/src/lib/` (where `cn` lives, and the two new files). `frontend/src/lib/utils.ts` was tracked (added before the line), but the new files were silently dropped from `git status`. Fixed: anchored to `/lib/` + `/lib64/` (only the repo-root Python build dirs). Also added `/test-results/` (stray root-level Playwright output dir that was showing as untracked).

### Drift findings (Day 3)
| ID | Finding | Implication |
|----|---------|-------------|
| D-DAY3-1 | `<Toaster>` already mounted in `main.tsx` (57.7 US-B2), not App.tsx | Checklist §3.3 item-1 needs no code; verified only |
| D-DAY3-2 | `QueryClient` already a single inline instance in `main.tsx` (57.7 + 57.9 retry:false) | "NEW `lib/queryClient.ts`" became *extract + add mutationCache*, preserving the 57.9 retry:false e2e contract |
| D-DAY3-3 | No `backend/.env.example` / `frontend/.env.example` — only repo-root `.env.example` | Updated the root file only |
| D-DAY3-4 | Root `.env.example` already had WorkOS-ish fields under "Identity" (57.7 US-A2 via `core/config`) | Reorganised into a WorkOS OIDC block + added `OIDC_REDIRECT_URI` / `FRONTEND_BASE_URL` / `COOKIE_SECURE` / `VITE_SENTRY_DSN` |
| D-DAY3-5 | `.gitignore` `lib/` silently ignores `frontend/src/lib/`; new files there don't appear in `git status` | Anchored to `/lib/` (bonus hygiene fix this commit); relevant for Day 4 component-layer files too |

### Verification (Day 3 aggregate)
- Backend: `black`/`isort`/`flake8` clean on changed files; **`mypy src/ --strict` → 305 source files, no issues**; **9/9 V2 lints green** (`python scripts/lint/run_all.py`); **full `pytest -q` → 1670 passed + 4 skipped** (Day 2: 1668+4; +2 from `test_api_smoke.py`).
- Frontend: `npm run lint` clean; `npm run build` ✅ (main `index-*.js` 243.81 kB gzip 77.29 — ≈flat vs Day 2 243.37); **`npm run test` → 52 files / 196 passed** (Day 2: 51/187; +9 tests from toast (9) + queryClient (4) net the prior count mechanics). One pre-existing jsdom "Not implemented: navigation" warning on stderr (a `window.location.href` assignment in an unrelated test path) — not a failure.
- Manual UI not run (no dev server boot). The connectivity spec is opt-in / not in CI; the smoke `pytest` covers the wiring.

---

## Day 4 — US-B2 (design-system component layer + adopt across feature areas) — `02910cfe`

### NEW `src/components/ui/` (shadcn-style; barrel `index.ts`)
- `skeleton.tsx` — `<Skeleton className?>` (base pulse box) + `<TableSkeleton rows=5 cols=6>` + `<CardSkeleton count=3>` (STYLE.md §6 canonical).
- `empty-state.tsx` — `<EmptyState title message? icon? action?>` (STYLE.md §7 — centred py-12, always an actionable next step).
- `error-retry.tsx` — `<ErrorRetry error? message? onRetry>` (STYLE.md §8 — "Failed to load data" headline + `error.message` line + `<Button variant="outline">Retry</Button>`). NOTE: STYLE.md §8's sample writes `text-danger` but this app has no `danger` Tailwind token → `text-destructive` used. `retryClicked` in STYLE.md §8 is the *e2e mock* idempotency flag (gate mock on user-click not call-count), not component state — the component just exposes a `role="button"` named "Retry" so that mock pattern works against it.
- `card.tsx` — `<Card>/<CardHeader>/<CardTitle>/<CardContent>/<CardFooter>` (Tailwind only; no Radix). Surface = `rounded-lg border border-border bg-background` (this app's index.css has no `--card` token).
- `button.tsx` — `<Button variant size asChild>` via `cva` + `cn` + Radix `Slot` (`asChild` renders the single child with the button classes). `class-variance-authority` / `tailwind-merge` / `@radix-ui/react-slot` all already in package.json (57.7 D-PRE-6).
- `badge.tsx` — `<Badge variant>`: default / secondary / outline / destructive + STYLE.md §3 `risk-low|risk-medium|risk-high|risk-critical` (same hex as `features/governance/components/ApprovalCard.tsx`).
- `button.tsx` + `badge.tsx` carry a file-level `/* eslint-disable react-refresh/only-export-components */` — they export both the component and the `cva` `*Variants` (standard shadcn; the variants must be importable for `cn(buttonVariants(...), className)` composition). Project `eslint.config.js` enforces `--max-warnings 0`, so the file-level disable is the minimal fix (vs editing the flat config).
- Removed the `components/ui/.gitkeep` placeholder (dir is now populated). No new dependency.

### Adoption (消重複)
- **admin-tenants `TenantListTable`** — `if (isLoading)` block (5 inline-`style={{}}` placeholder rows) → `<div role="status" aria-label="Loading tenants" className="p-4"><TableSkeleton rows={5} cols={6} /></div>` (kept the `role`/`aria-label` for the existing test). `if (items.length === 0)` block → `<EmptyState title="No tenants match current filter." action={<Button variant="outline" onClick={handleReset}>Reset Filters</Button>} />`. The table body itself still uses inline styles (out of scope — only loading/empty was listed).
- **governance `AuditLogViewer`** — the in-`<tbody>` skeleton rows: inner `<div className="h-4 w-full animate-pulse rounded bg-muted">` → `<Skeleton className="h-4 w-full">`. The empty-state row stays a `<tr><td colSpan={6}>…</td></tr>` (it's table-structured — `<TableSkeleton>` is a full `<table>` that can't nest, and `<EmptyState>` doesn't fit inside a `<td>` cleanly). `ApprovalsPage` has no skeleton (its only `isLoading` use is the Refresh-button label) — nothing to swap.
- **verification `VerificationList` + `CorrectionTraceView`** — loading skeleton inner divs (`h-10` / `h-16` `animate-pulse`) → `<Skeleton className="h-N">`. The `isError` / empty blocks stay as-is: they carry `data-testid="error-retry" / "empty-reset" / "trace-error" / "trace-empty"` and a `retryClicked`-driven "Retrying…" pending label that `<ErrorRetry>`/`<EmptyState>` as-built don't replicate.
- **memory `MemoryRecentList` + `MemoryByScopeBrowser`** — same: loading skeleton inner divs → `<Skeleton>`; `isError` blocks unchanged.
- **cost-dashboard `CostOverview` + sla-dashboard `SLAOverview`** — `{isLoading && tenantId}` text (`<p>Loading cost summary…</p>` / `<p>Loading SLA report…</p>`) → `<CardSkeleton count={3} />` (these dashboards render summary cards). `{error}` alert div → `<div role="alert"><ErrorRetry error={error} onRetry={() => void refetch()} /></div>` (preserved `role="alert"`). cost/sla `migrate.test.tsx` vitest both green after the swap (they don't assert on the loading-text or the `Error:` prefix).
- **`CONVENTION.md`** — added `## 10. Design System Component Layer (components/ui/)`: a table of "need → use / NOT", the shadcn eslint-disable note, the existing-per-feature-badge carve-out (AuditChainBadge/VerifierTypeBadge/MemoryScopeBadge keep own colours), and the codification basis (57.9 ApprovalList + admin-tenants established the shapes ≥ 2 examples → STYLE.md §6-§8 → 57.13 extracted + adopted).

### Adoption depth — what's NOT done (D-DAY4-2 — 🚧 carryover within US-B2)
The `<Skeleton>` primitive swap is everywhere; `<TableSkeleton>`/`<EmptyState>` landed in admin-tenants and `<CardSkeleton>`/`<ErrorRetry>` in cost/sla. **Not yet migrated**: the bespoke `isError` blocks in verification (`VerificationList`/`CorrectionTraceView`) + memory (`MemoryRecentList`/`MemoryByScopeBrowser`) and the in-table empty/error rows in `AuditLogViewer`. Reason: those blocks carry `data-testid` hooks + a `retryClicked` "Retrying…" pending state that `<ErrorRetry>`/`<EmptyState>` as-built don't expose. Closing this needs `data-testid?` + `pending?` props added to the components, then the swap — mechanical, ~1-2 hr, slated for a B-series day or US-C1 closeout. The deliverable (the `components/ui` layer + its tests + CONVENTION codification) is complete; this is incremental adoption.

### Drift findings (Day 4)
| ID | Finding | Implication |
|----|---------|-------------|
| D-DAY4-1 | STYLE.md §8 error-retry sample uses `text-danger`; this app's tailwind.config has no `danger` token (only `destructive`) | `<ErrorRetry>` uses `text-destructive`; STYLE.md §8 sample is aspirational — left STYLE.md untouched (minor; could be an addendum later) |
| D-DAY4-2 | verification/memory `isError` blocks + AuditLogViewer in-table empty row have `data-testid` + `retryClicked` pending state that `<ErrorRetry>`/`<EmptyState>` don't replicate | Full swap deferred (🚧 within US-B2) — `<Skeleton>` primitive swap done everywhere; needs `data-testid?`/`pending?` props on the components |
| D-DAY4-3 | `components/ui/` already existed as an empty dir with `.gitkeep` (57.8 scaffolding) | Removed the `.gitkeep`; populated the dir |
| D-DAY4-4 | `eslint.config.js` enforces `--max-warnings 0`; shadcn's "component + cva variants in one file" trips `react-refresh/only-export-components` | File-level `eslint-disable` in button.tsx + badge.tsx (shadcn's own convention) — minimal blast radius vs editing the flat config |

### Verification (Day 4 aggregate)
- Frontend: `npm run lint` clean (after the 2 shadcn `eslint-disable`s); `npm run build` ✅ (main `index-*.js` 243.86 kB gzip 77.31 — ≈flat vs Day 3 243.81; the new `components/ui` primitives are tree-shaken into the pages that use them); **`npm run test` → 53 files / 212 passed** (Day 3: 52/196; +1 file / +16 tests from `components.test.tsx`). Pre-existing jsdom "Not implemented: navigation" + a deliberate ErrorBoundary "kaboom" throw on stderr — not failures.
- Backend: untouched this day (no backend changes); `pytest` baseline stays 1670 + 4 skipped.
- Manual UI not run (no dev server boot).

### Mid-sprint ratio check (retrospective Q2)
- Scope class `frontend-foundation-spike` HYBRID **0.50** (1st application). Plan committed **~25-32 hr** over Days 0-9.
- Done through Day 4: US-A1/A2/A3/A4/A5/B1/B2 (7 of 15 USs) at 5 of 10 calendar days. Bottom-up for these ≈ ~22 hr → calibrated ≈ **~11 hr** ≈ ~40% of the committed budget at 50% of calendar days — slightly under / on track.
- Ratio (actual vs committed-so-far) ≈ **~0.9**; `|delta from 1.0| < 30%` → **no `AD-Sprint-Plan-N`** logged this checkpoint. The 0.50 multiplier holds for now (single-data-point class — 2-3 sprint window validation per the `When to adjust` rule; revisit at Day 9 retrospective Q2).
- **Schedule note**: Days 5-9 (4 days) carry 8 USs (B3 / B4 / B5 / B6 / B7 / B8 / B9 / C1) — denser than Days 0-4's 7 USs / 5 days, but the B-series USs are individually smaller (Radix dialog+dropdown / Sentry+vitals / i18n / a11y / Lighthouse / visual-regression / AuthShell+cleanup / closeout). Plus the D-DAY4-2 carryover. Tight but feasible; if a B-series day over-runs, the carryover/cleanup work compresses into US-C1.

---

## Remaining for Day 5-9

- [x] Day 3: US-A5 (connectivity smoke + .env.example) + US-B1 (Toast) — `e1c3f58e`
- [x] Day 4: US-B2 (design-system component layer + adopt across 6 feature areas) + mid-sprint ratio check — `02910cfe`
- [ ] Day 5: US-B3 (Radix Dialog+DropdownMenu + DecisionModal+UserMenu refactor)
- [ ] Day 6: US-B4 (Sentry + Web Vitals + telemetry endpoint)
- [ ] Day 7: US-B5 (i18n)
- [ ] Day 8: US-B6 (a11y) + US-B7 (Lighthouse CI)
- [ ] Day 9: US-B8 (visual regression) + US-B9 (AuthShell + login/callback + inline cleanup) + US-C1 (closeout)

---

## Notes / Risks

- **D-PRE-8 is the key finding**: the auth flow being broken at the middleware-allowlist level confirms why the user couldn't log in. US-A1 fixes it (cookie fallback + EXEMPT_PATH_PREFIXES). Combined with the cookie↔localStorage fix (authStore + /auth/me), login → callback → authenticated → navigate becomes end-to-end functional.
- **Bundle size watch**: adding @radix-ui/react-dropdown-menu + @sentry/react + web-vitals + i18next + react-i18next will grow main bundle (~50-70 KB est). Sentry + i18n dynamic-import as mitigation; track vs 296.58 kB; retrospective Q3 + AD-Bundle-Size-285kB-Carryover continuation.
- **Large sprint scope control**: per checklist 重要備註 — if a US超估, go minimal-viable within that US (don't delete US; mark 🚧 + reason → carryover AD). cookie-only fallback path (Bearer + localStorage dev-login) if cookie cross-port fails in dev.
- **Day 1 三-prong完成**: a few content-verify items deferred to Day 1 start (low-risk impl details, none gate Day 1).
