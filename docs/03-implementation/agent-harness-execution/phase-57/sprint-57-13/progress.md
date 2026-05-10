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

## Day 5 — US-B3 (Radix Dialog + DropdownMenu primitives + DecisionModal/UserMenu refactor) — `6bb4fdde`

### NEW `components/ui/` Radix wrappers (barrel `index.ts` updated)
- `dialog.tsx` — `Dialog`/`DialogTrigger`/`DialogClose`/`DialogPortal` (Radix re-exports) + `DialogOverlay` (dimmed backdrop) + `DialogContent` (portalled to `<body>`, centred panel, built-in X close button, `role="dialog"`) + `DialogHeader`/`DialogFooter` (layout) + `DialogTitle`/`DialogDescription` (Radix — accessible title/description). Controlled use: `<Dialog open onOpenChange={...}><DialogContent>…</DialogContent></Dialog>`. Radix supplies focus-trap + ESC + outside-click + aria wiring.
- `dropdown-menu.tsx` — `DropdownMenu`/`DropdownMenuTrigger`/`DropdownMenuPortal` (Radix) + `DropdownMenuContent` (portalled menu surface; `bg-background border shadow-md` — this app's tailwind.config has no `popover` token → D-DAY5-1) + `DropdownMenuItem` (`role="menuitem"` + `focus:bg-muted`) + `DropdownMenuSeparator` + `DropdownMenuLabel`. Radix supplies keyboard nav + focus + ESC/outside-click close + `role="menu"`.
- `package.json`: `+@radix-ui/react-dropdown-menu@^2.1.16` (`@radix-ui/react-dialog@^1.1.15` already present from 57.7 D-PRE-6).

### Consumer refactors
- **governance `DecisionModal`** — the hand-rolled `fixed inset-0 z-[100] … bg-black/45` overlay + inner `role="dialog"` panel with `onClick` outside-close + `stopPropagation` → `<Dialog open onOpenChange={(o) => { if (!o) onClose(); }}><DialogContent className="max-w-[720px] font-sans"><DialogHeader><DialogTitle>Review approval — {toolName}</DialogTitle></DialogHeader> … {reason textarea} … {error alert} … <DialogFooter>{Cancel | Escalate | Reject | Approve}</DialogFooter></DialogContent></Dialog>`. The API (`{ approval, onClose }`) and the parent's mount/unmount pattern are unchanged; the 4 action buttons keep their semantic colours (green/red/orange — `<Button>` variants don't carry those); `role="dialog"` + button accessible-names are preserved (so the approval-flow e2e selectors survive). **governance Vitest suite is green** (no DecisionModal vitest exists — only e2e). **The e2e `tests/e2e/governance/approvals.spec.ts` was NOT re-run this turn** (no backend server in this env) — folded into the US-C1 e2e sweep (which is already deferred for the auth-gate changes). D-DAY5-3.
- **`UserMenu`** — the custom popover (`useState(open)` + `useRef(wrapperRef)` + `useEffect` for outside-click + ESC + a manual `<div role="menu">`) → `<DropdownMenu><DropdownMenuTrigger aria-label="User menu" …>{initial}</DropdownMenuTrigger><DropdownMenuContent align="end"><DropdownMenuLabel>{Signed-in-as / name / email / role badges}</DropdownMenuLabel><DropdownMenuSeparator/><DropdownMenuItem onSelect={() => void logout()}>Sign out</DropdownMenuItem></DropdownMenuContent></DropdownMenu>`. The trigger keeps `aria-label="User menu"` + `aria-haspopup="menu"` (Radix sets the latter + `aria-expanded`). It now also renders `authStore.roles` as `<Badge variant="outline">` pills (was just name/email before). A locale-switcher item slot is reserved for US-B5 (i18n).

### Test infra
- `tests/unit/setup.ts` — added jsdom polyfills for Radix: `Element.prototype.{hasPointerCapture, setPointerCapture, releasePointerCapture, scrollIntoView}` + `globalThis.ResizeObserver`. Without these, opening a Radix menu/dialog under `@testing-library` throws (`target.hasPointerCapture is not a function` etc.). D-DAY5-2.
- `tests/unit/components/UserMenu.test.tsx` — rewritten: `@testing-library/user-event` instead of `fireEvent` (Radix dropdown needs real pointer-event sequencing to open); asserts the role-badge text + `aria-expanded` toggle on the trigger. Still 5 tests.
- NEW `tests/unit/components/ui/radix.test.tsx` — 9 tests: Dialog (closed → no `role="dialog"` / open → content+title+footer / `{Escape}` → `onOpenChange(false)` / X button → `onOpenChange(false)`); DropdownMenu (closed → no `role="menu"` / open → menu+label+menuitem / item click → `onSelect` + menu closes / `aria-expanded` toggles / works inside a stateful host that updates on item select).
- `CONVENTION.md` §10 — added "Modal dialog → `<Dialog>`" + "Dropdown/popover menu → `<DropdownMenu>`" rows + the Radix-in-jsdom test note (setup.ts polyfills + `user-event` not `fireEvent`).

### Drift findings (Day 5)
| ID | Finding | Implication |
|----|---------|-------------|
| D-DAY5-1 | This app's `tailwind.config.js` has no `popover` token (UserMenu's old custom popover used `bg-popover text-popover-foreground` — silently transparent) | `dropdown-menu.tsx` `DropdownMenuContent` uses `bg-background border border-border shadow-md` (tokens that exist). Pre-existing UserMenu transparency bug is moot now (replaced). Could add a `popover` token in a future polish. |
| D-DAY5-2 | jsdom implements none of Radix's pointer-capture / scrollIntoView / ResizeObserver — Radix primitives throw under `@testing-library` without polyfills | Added the 5 polyfills to `tests/unit/setup.ts` (one-time; benefits all future Radix usage). Tests of Radix primitives must use `@testing-library/user-event`, not `fireEvent`. |
| D-DAY5-3 | DecisionModal's e2e (`approvals.spec.ts`) can't be re-run here (no backend server); the Radix swap *should* be e2e-transparent (role="dialog" + button names + ESC/outside-click preserved) but isn't verified | 🚧 folded into the US-C1 e2e sweep (already deferred for the Day 1-2 auth-gate changes). |

### Verification (Day 5 aggregate)
- Frontend: `npm run lint` clean; `npm run build` ✅ — main `index-*.js` 243.89 kB gzip 77.33 (≈flat vs Day 4 243.86); **the `RequireAuth-*.js` lazy chunk grew 34.65 → 126.24 kB (gzip 11.56 → 41.04) — `@radix-ui/react-dialog` + `@radix-ui/react-dropdown-menu` land in that chunk** (governance/DecisionModal + AppShell/UserMenu pull them in). Lazy-loaded on first auth-gated route nav, so initial-load main bundle is unaffected — but flag for the AD-Bundle-Size watch. **`npm run test` → 54 files / 221 passed** (Day 4: 53/212; +1 file / +9 tests from `radix.test.tsx`). Pre-existing jsdom "Not implemented: navigation" + deliberate ErrorBoundary "kaboom" throw on stderr — not failures.
- Backend: untouched (no backend changes); `pytest` baseline 1670 + 4 skipped.
- Manual UI not run (no dev server boot).

---

## Day 6 — US-B4 (frontend observability: Sentry + Web Vitals + Cat 12 telemetry endpoint) — `a8b90ba4`

### Frontend
- **NEW `src/lib/observability.ts`** — three entry points:
  - `initObservability()` — called once at startup. If `import.meta.env.VITE_SENTRY_DSN` is set → `sentry = await import("@sentry/react"); sentry.init({ dsn, environment: import.meta.env.MODE, tracesSampleRate: 0.1 })`. No DSN → no-op. The dynamic import keeps the ~100 kB `@sentry/react` v10 bundle out of the main chunk (dev/CI ship nothing).
  - `reportError(err, ctx?)` — **always** `console.error(err, ctx)`; if Sentry is live → `captureException(err, { extra: ctx })`; **also** fire-and-forget beacon → `POST /api/v1/telemetry/frontend-error` (so the Cat 12 backend records the error regardless of Sentry). Never throws (every step is try/catch'd).
  - `reportWebVitals()` — `import("web-vitals").then(({ onCLS, onFCP, onLCP, onINP, onTTFB }) => …)` → each metric → beacon → `POST /api/v1/telemetry/frontend` with `{ name, value, id, rating, navigationType, url }`. `beacon()` uses `navigator.sendBeacon` (survives page unload), falls back to `fetch(..., { keepalive: true })`.
- **`main.tsx`** — `void initObservability(); reportWebVitals();` before `createRoot` (fire-and-forget; never blocks render).
- **`components/AppErrorBoundary.tsx`** — `onError={(error, info) => reportError(error, { componentStack: info.componentStack })}` (was a "Sentry … placeholder — Phase 58.2+" note in the docstring; now wired).
- **`features/auth/services/authService.ts` `fetchWithAuth`** — wrapped the `fetch` in try/catch: a network failure → `reportError(err, { url, kind: "network" })` then rethrow; a `res.status >= 500` → `reportError(new Error(\`HTTP \${status} from \${url}\`), { url, status })`. (5xx reporting is intentionally noisy-ish — it's the cheapest place that sees the raw status for every request.)
- **`lib/queryClient.ts` `mutationCache.onError`** — now also `reportError(err, { source: "mutation" })` alongside the existing `toastError`. (`toastError` itself stays a pure UI helper — error-sink wiring lives in `fetchWithAuth` + the mutation cache, not in the toast fn.)
- **`package.json`**: `+@sentry/react@^10.52.0` `+web-vitals@^5.2.0` — both **dynamic-imported**, so neither lands in the main bundle (separate chunks; loaded lazily on first error / first vital).

### Backend (範疇 12)
- **NEW `api/v1/telemetry.py`** — `POST /telemetry/frontend` (`WebVitalIn { name, value, id, rating?, navigationType?, url? }` — `navigationType` camelCase to match the web-vitals lib field name, `# noqa: N815`) → one structured JSON log line `event=frontend.web_vitals` with the metric fields as extras → **204 No Content** (the SPA / sendBeacon doesn't read the body). `POST /telemetry/frontend-error` (`FrontendErrorIn { message, stack?, url?, user_agent?, context? }`) → `event=frontend.error` (logged at `warning`) → 204. Anonymous — `/api/v1/telemetry` is already in `TenantContextMiddleware.EXEMPT_PATH_PREFIXES` (added 57.7 US-A1). Malformed bodies → 422 (Pydantic), never 500.
- **`api/main.py`** — `app.include_router(telemetry_router, prefix="/api/v1")`.
- **Cat 12 emit choice (D-DAY6-1)**: this app has **no app-level OpenTelemetry meter** anywhere in `src/` (only `setup_opentelemetry()` which auto-instruments FastAPI/SQLAlchemy/Redis). The established Cat-12 emit path here is the structured JSON logger (`configure_json_logging` at startup), which the OTel log pipeline picks up + `PIIRedactor` scrubs at the formatter. So the telemetry endpoints emit via `get_json_logger("frontend.telemetry").info/warning(event=…, extra={…})` — not a new `metrics.get_meter(...)` (which would be the only such usage in the codebase).

### Drift findings (Day 6)
| ID | Finding | Implication |
|----|---------|-------------|
| D-DAY6-1 | The backend has no app-level OTel meter pattern (`metrics.get_meter / create_counter / create_histogram`) anywhere in `src/` — only `setup_opentelemetry` auto-instrumentation | The telemetry endpoints emit Cat 12 data via the structured JSON logger (the established path here), not a bespoke new meter. A future polish could add a `frontend.web_vitals` histogram once the codebase grows an app-level meter convention. |
| D-DAY6-2 | `reportError` per the checklist spec is "Sentry + console.error" only — but the §6.2 backend `/frontend-error` endpoint would then have no producer (Potemkin) | `reportError` also fire-and-forget beacons to `/frontend-error` — minor deviation from the literal checklist that makes the endpoint actually used (AP-2 / AP-4). Noted. |
| D-DAY6-3 | The eslint config has no `no-console` rule, so `// eslint-disable-next-line no-console` comments are flagged as "unused disable directive" under `--report-unused-disable-directives` | Removed the two `eslint-disable no-console` comments from `observability.ts` (the `console.error` calls are intentional + not lint-flagged). |

### Verification (Day 6 aggregate)
- Frontend: `npm run lint` clean (after removing the 2 dead `eslint-disable no-console` directives); `npm run build` ✅ — main `index-*.js` **245.25 kB** gzip 77.85 (Day 5: 243.89 / 77.33 — **+1.36 kB**, the small static cost of `observability.ts` itself; `@sentry/react` + `web-vitals` are separate dynamic chunks, NOT in main). `RequireAuth` lazy chunk unchanged at 126.24 kB. **`npm run test` → 55 files / 226 passed** (Day 5: 54/221; +1 file / +5 tests from `observability.test.ts`). Pre-existing jsdom "Not implemented: navigation" + deliberate ErrorBoundary "kaboom" throw on stderr — not failures.
- Backend: `black`/`isort`/`flake8` clean on changed files (fixed 2 E501 — the main.py MHist line + a telemetry.py docstring line, trimmed); **`mypy src/ --strict` → 306 source files, no issues** (+1 file: `telemetry.py`); **9/9 V2 lints green** (`python scripts/lint/run_all.py` — must run from repo root, not `backend/`); **full `pytest -q` → 1676 passed + 4 skipped** (Day 3 baseline 1670+4; +6 from `test_telemetry_frontend.py`).
- Manual UI not run (no dev server boot). The Sentry path is untested end-to-end (no DSN in this env) — the unit test covers the no-DSN no-op + the beacon path; a real Sentry smoke is out of scope (would need a project DSN).

---

## Day 7 — US-B5 (i18n: i18next + react-i18next, zh-TW + en) — `890876f7`

### Setup (§7.1)
- **NEW `src/i18n/index.ts`** — `i18n.use(LanguageDetector).use(initReactI18next).init({ resources, fallbackLng:"en", supportedLngs:["en","zh-TW"], ns:["common","auth"], defaultNS:"common", detection:{ order:["localStorage","navigator"], lookupLocalStorage:"ipa-locale", caches:["localStorage"] }, interpolation:{ escapeValue:false }, react:{ useSuspense:false } })`. Resources are bundled JSON imports, so `init()` resolves synchronously → no `<Suspense>` boundary needed (and `useSuspense:false` makes it explicit). Exports `SUPPORTED_LOCALES` (`[{id:"en",label:"English"},{id:"zh-TW",label:"繁體中文"}]`), `LOCALE_STORAGE_KEY` (`"ipa-locale"`), `resources`.
- **NEW `src/i18n/locales/{en,zh-TW}/{common,auth}.json`** — `common`: `shell.*` (brand / primaryNavigation / mainNav / collapseSidebar / expandSidebar / comingSoon), `nav.*` (13 route labels + `nav.category.{operations,admin,settings}`), `userMenu.*` (label / options / signedInAs / signOut / language), `action.*` (retry / cancel / save / loading), `verification.tabsLabel` + `verification.tab.{recent,correctionTrace}`. `auth`: signInTitle / signInSubtitle / loginWithWorkOS / errorTitle / completing / backToLogin / `devSection.{heading,submit,submitting,errorDisabled,errorFailed("…({{status}})"),errorRequest}`.
- **`main.tsx`** — `import "./i18n"` before `createRoot`.
- **NEW root `i18next-parser.config.cjs`** + `package.json` script `"i18n:extract"` — `i18next-parser` scans `src/**` for `t(...)`, adds missing keys (en: key text as default; others: empty), `keepRemoved:true`. CommonJS (`.cjs`) on purpose since `package.json` is `"type":"module"`. NOT run in CI — dev convenience; the hand-maintained JSON is the source of truth. `i18next-parser@9` is npm-deprecated (suggests `i18next-cli`) but kept per checklist literal — fine for an extraction-only dev tool (D-DAY7-2).
- **`package.json`** — `+i18next@^26 +react-i18next@^17 +i18next-browser-languagedetector@^8` (deps) `+i18next-parser@^9` (dev). 6 + 162 packages added.

### Adoption (§7.2)
- **`routes.config.ts`** — `RouteEntry` gains required `nameKey: string` (i18n key resolved against `common` ns, e.g. `nav.costDashboard`); `name` stays as the English dev/debug fallback. All 13 entries populated (D-DAY7-1).
- **`Sidebar`** — `useTranslation("common")`; nav labels `t(entry.nameKey, entry.name)`; category headers `t(\`nav.category.${category}\`)`; aria-labels (`shell.primaryNavigation` / `shell.mainNav`) + "Coming soon" (`shell.comingSoon`) + collapse-toggle aria-label (`shell.expandSidebar`/`shell.collapseSidebar`) + brand (`shell.brand`) all via `t()`. Removed the module-const `CATEGORY_LABELS` map (D-DAY7-3). `AppShellV2` itself unchanged — its only string is the `pageTitle` prop, translated by the caller pages.
- **`UserMenu`** — filled the locale-switcher slot the Day 5 docstring reserved: a `<DropdownMenuSeparator>` + `<DropdownMenuLabel>Language</DropdownMenuLabel>` + one `<DropdownMenuItem>` per `SUPPORTED_LOCALES` (the active locale marked with `<Check size={14}>` + `aria-current`; inactive ones get `<Check className="invisible">` for alignment). `onSelect` → `localStorage.setItem("ipa-locale", id)` (try/catch for private-mode) + `void i18n.changeLanguage(id)` (the detector also caches via `caches:["localStorage"]`, so this is belt-and-braces). "Signed in as" / "Sign out" / both aria-labels via `t()` (D-DAY7-4).
- **`pages/auth/login` + `callback`** — every user-facing string via `t(..., {ns:"auth"})` incl. `devSection.errorFailed` interpolation (`{{status}}`). The `tenant_code` / `email` form-field labels are kept literal (technical identifiers matching backend query params — translating them would be confusing). **Inline styles NOT touched** — tailwind-ize + `<AuthShell>` wrap is explicitly US-B9 scope, and the docstrings already say so; bleeding it into Day 7 would be scope creep (D-DAY7-5).
- **2 feature-page demos** — `cost-dashboard/index.tsx`: `pageTitle={t("nav.costDashboard")}` (via `useTranslation("common")`). `verification/index.tsx`: `pageTitle={t("nav.verification")}` + tab labels `t("verification.tab.recent")` / `t("verification.tab.correctionTrace")` + tabs `aria-label={t("verification.tabsLabel")}`. (Both `pageTitle`s + the verification tabs render the same English text as before — so even the existing e2e specs that assert `"Cost Dashboard"` / `"Verification tabs"` keep passing; no NEW e2e breakage from i18n.)
- **`CONVENTION.md`** — new §11 i18n Convention (rules table: `t()` not literals / `nameKey` for nav / both-locale parity / interpolation / locale switcher; namespaces `common`+`auth`; extraction tool note; test reset rule for files that call `changeLanguage`).

### Tests (§7.3)
- **`tests/unit/setup.ts`** — `import "@/i18n"` so components using `useTranslation()` render real strings in unit tests, not raw keys. (Without it, `t("shell.primaryNavigation")` would return the key, breaking aria-label assertions; the `t(nameKey, name)` fallback covers nav labels but bare `t()` calls need a real i18n instance.) Verified: existing `Sidebar.test.tsx` (3 category headers / aria-current / "Coming soon" / "Collapse sidebar") + `AppShellV2.test.tsx` + `UserMenu.test.tsx` all still green.
- **NEW `tests/unit/i18n/i18n.test.ts`** (6 tests) — exactly the 2 supported locales; en ≡ zh-TW key parity per namespace (flatten + compare); every leaf is a non-empty string in both locales; `changeLanguage("en")`/`("zh-TW")` flips resolved translations (`nav.costDashboard` ⇄ "成本儀表板", `auth:loginWithWorkOS` ⇄ "使用 WorkOS 登入"); `devSection.errorFailed` interpolates `{{status}}`; unknown locale (`"fr"`) → en fallback. `afterAll` resets to `"en"`.
- **`tests/unit/components/UserMenu.test.tsx`** — +1 test ("locale switcher offers both locales and persists the choice": open menu → both `English` + `繁體中文` menuitems present → click `繁體中文` → `localStorage["ipa-locale"] === "zh-TW"` + `i18n.resolvedLanguage === "zh-TW"`). Added `afterEach` that clears `ipa-locale` + `await i18n.changeLanguage("en")` so the singleton + localStorage don't leak across the file's tests (the earlier English-aria-label assertions would otherwise break if this test ran first).
- **NEW `tests/e2e/i18n/locale-switch.spec.ts`** — self-contained (mocks `**/api/v1/auth/me` → authenticated `platform_admin` + `**/api/v1/admin/tenants/**/cost-summary**` → empty): `/cost-dashboard` renders → app-shell visible → sidebar shows `"Cost Dashboard"` (browser default = en) → open UserMenu → click `"繁體中文"` → sidebar `complementary` region now shows `"成本儀表板"` + no `"Cost Dashboard"` link → `page.reload()` → still `"成本儀表板"` (i18next detector reads `ipa-locale` from localStorage). Uses `getByRole("complementary")` to anchor the sidebar (its `aria-label` itself gets translated, so can't key on that). ⚠️ **Written but not executed in this session** (no dev server boot) → US-C1 e2e sweep runs + verifies it, alongside D-DAY5-3 (governance approvals e2e) + the Day 1-2 auth-gate e2e updates (D-DAY7-6).

### Drift findings (Day 7)
| ID | Finding | Implication |
|----|---------|-------------|
| D-DAY7-1 | `routes.config.ts` `RouteEntry` had `name: string` only — no i18n key field | Added required `nameKey: string`; `name` retained as dev/debug fallback (`t(nameKey, name)`). Sidebar is the sole consumer; App.tsx route gen unaffected (uses `path`/`component`). |
| D-DAY7-2 | `i18next-parser@9.4.0` is npm-deprecated (suggests `i18next-cli`) | Kept per checklist literal — it's an extraction-only dev tool (`npm run i18n:extract`), not in CI; the hand-maintained JSON is authoritative. Migrating to `i18next-cli` is a trivial future swap if desired. |
| D-DAY7-3 | `Sidebar.tsx` had a module-const `CATEGORY_LABELS: Record<RouteCategory,string>` | Removed; category headers now `t(\`nav.category.${category}\`)`. Single source = the JSON bundles. |
| D-DAY7-4 | `UserMenu` Day-5 docstring already reserved "A locale switcher item slot is reserved for US-B5 (i18n)" | Filled it now (per-locale menuitems + persist). No structural surprise. |
| D-DAY7-5 | `pages/auth/{login,callback}` carry inline `style={{…}}` blocks; their docstrings say "Tailwind-ize + `<AuthShell>` wrap: Sprint 57.13 US-B9" | Day 7 only extracts the *strings* (i18n). The styling refactor stays in US-B9 — touching it here would be scope bleed. The `tenant_code`/`email` form labels are also intentionally kept literal (API param names). |
| D-DAY7-6 | The new `locale-switch.spec.ts` (+ D-DAY5-3 governance e2e + Day 1-2 auth-gate e2e) can't be run here — no dev server / backend boot in this env | All deferred to US-C1's e2e sweep (which also re-verifies the Day 5 DecisionModal Radix swap). The locale test is self-contained (page.route mocks), so it's the lowest-risk of the deferred ones. |
| D-DAY7-7 | Main bundle jumped 245.25 → 304.37 kB (gzip 77.85 → 97.66; **+59 kB / +20 kB gzip**) — i18next core + react-i18next + the detector are in the *main* chunk, not a dynamic one | i18n must initialize before render (locale must be resolved before components mount), so it can't be dynamic-imported the way `@sentry/react`/`web-vitals` were (Day 6). Recorded against the AD-Bundle-Size carryover — a follow-up optimization sprint candidate, not a Day-7 blocker. The plan's §Risks anticipated this ("本 sprint 預期再漲"). |

### Verification (Day 7 aggregate)
- Frontend: `npm run lint` clean; `npm run build` ✅ — main `index-*.js` **304.37 kB** gzip **97.66** (Day 6: 245.25 / 77.85 — +59.12 kB / +19.81 kB gzip; D-DAY7-7). `RequireAuth` lazy chunk **127.00 kB** (Day 6: 126.24 — +0.76 kB, the small i18n-touch in `Sidebar`/`UserMenu` which are in that group). **`npm run test` → 56 files / 233 passed** (Day 6: 55/226; +1 file / +7 tests = 6 i18n.test.ts + 1 UserMenu.test.tsx). Deliberate ErrorBoundary "kaboom" + jsdom "navigation not implemented" on stderr — not failures.
- Backend: **untouched this day** (zero `.py` changes) — pytest baseline **1676 + 4 skip** holds, `mypy src --strict` 306 files clean holds, **9/9 V2 lints** green holds. (No re-run needed — surgical-change discipline; the prior-day verification is still current.)
- Manual UI not run (no dev server). Unit tests cover bundle parity (en ≡ zh-TW key sets), `changeLanguage` switching, interpolation, and the UserMenu switcher persist path; the e2e covers the full switch-and-reload flow but goes to US-C1 for execution.
- Mid-sprint note (Day 4 ratio check still holds): `frontend-foundation-spike` 0.50 1st app, committed ~25-32 hr; Days 0-7 done = 9/15 USs at 7/10 calendar days — pace tracking ~as projected; no `AD-Sprint-Plan-N` triggered.

---

## Day 8 — US-B6 (a11y baseline: jsx-a11y + axe-core) + US-B7 (Lighthouse CI) — `c3294318`

### US-B6 — accessibility (§8.1)
- **`eslint.config.js`** — added `eslint-plugin-jsx-a11y` to the flat config: `plugins: { ..., "jsx-a11y": jsxA11y }` + `rules: { ...jsxA11y.flatConfigs.recommended.rules, ...existing }`. Now a11y issues fail `npm run lint` (`--max-warnings 0`). First run surfaced **exactly 5 violations across 3 files** — all fixed (not silenced wholesale; only one targeted disable, with a reason):
  - `src/components/ui/card.tsx` — `CardTitle` is `<h3 ref className {...props}/>` (standard shadcn primitive; content comes from `children` at call sites). `jsx-a11y/heading-has-content` can't see content through the `{...props}` spread → false positive → `// eslint-disable-next-line jsx-a11y/heading-has-content` with a comment explaining why.
  - `src/features/chat_v2/components/ToolCallCard.tsx:91` — the collapse-header `<div role="button" aria-expanded onClick>` had no keyboard support (`jsx-a11y/click-events-have-key-events` + `interactive-supports-focus`). Fixed: added `tabIndex={0}` + `onKeyDown` (Enter/Space → `setOpen(v => !v)` + `preventDefault`). The div's inline styles are left alone — that cleanup is US-B9 scope.
  - `src/features/tenant-settings/components/TenantSettingsEditForm.tsx:84,102` — two `<label>`s with no associated control (`jsx-a11y/label-has-associated-control`). Fixed: added `htmlFor="tenant-settings-display-name"` / `id` on the `<input>` and `htmlFor="tenant-settings-meta-data"` / `id` on the `<textarea>`. Inline styles untouched (US-B9).
  - (The `pages/auth/login` dev-login form's `<label>tenant_code <input/></label>` did NOT trigger — nested-control association satisfies the rule. Lucide `<svg>` icons don't trigger anything — no jsx-a11y rule covers `<svg>`.)
- **NEW `tests/e2e/a11y/a11y-scan.spec.ts`** — `new AxeBuilder({ page }).analyze()` over: (1) the 9 active routes with `**/api/v1/auth/me` mocked → authenticated so `<RequireAuth>` renders the AppShellV2 shell; the page's own data fetches fail (no backend) → the accessible `<ErrorRetry>` (`role="alert"`, Day 4) error state, which axe also scans — error UIs need a11y too; (2) `/auth/login` with `/auth/me` → 401 (anonymous); (3) `/auth/callback?error=…` — the `?error` branch sets the error message and `return`s before the bootstrap effect, so it shows the error UI rather than redirecting. Assertion per page: **0 violations with impact `critical` or `serious`** (moderate/minor get `console.warn(...)` for triage — not a failure at baseline scope). Self-contained (`page.route()` mocks; vite dev server auto-started by `playwright.config.ts` webServer). ⚠️ **written, not executed here** (no dev server boot) → US-C1 e2e sweep runs it (`npx playwright test a11y`).
- **`CONVENTION.md`** — new §12 Accessibility Convention (rules table: clickable non-`<button>` → real button or `role+tabIndex+onKeyDown` / form field → `htmlFor`+`id` or nested / heading wrapper component → targeted disable OK / error region → `role="alert"` / decorative icon → leave; axe-core e2e scan note + "add new pages to the route list").

### US-B7 — Lighthouse CI (§8.2)
- **`package.json`** — `+eslint-plugin-jsx-a11y@^6.10.2` `+@axe-core/playwright@^4.11.3` `+@lhci/cli@^0.15.1` (all dev) + `"lhci": "lhci autorun"` script.
- **NEW `frontend/lighthouserc.cjs`** — `.cjs` on purpose (package.json is `"type":"module"`; LHCI loads config via `require()` — same reasoning as `i18next-parser.config.cjs`). `collect.startServerCommand: "npm run preview -- --port 4173 --strictPort"` (vite preview does SPA fallback — a bare static server would 404 `/auth/login`), `collect.url: ["http://localhost:4173/auth/login"]` (the one page that renders fully without auth/backend; auth-gated pages can't be Lighthouse'd without a backend → out of scope), `numberOfRuns: 1`, `chromeFlags: "--no-sandbox --headless=new"` (CI containers). `assert.assertions`: `categories:accessibility` **`error` ≥ 0.9** (hard gate) / `categories:performance` **`warn` ≥ 0.7** / `categories:best-practices` **`warn` ≥ 0.8** / `first-contentful-paint` `warn` ≤ 2000 ms / `interactive` `warn` ≤ 4000 ms (the perf budgets are warnings while the bundle is being trimmed — see AD-Bundle-Size). `upload.target: "temporary-public-storage"` (no token needed).
- **NEW `.github/workflows/frontend-lighthouse.yml`** — `on: pull_request: paths: [frontend/**, .github/workflows/frontend-lighthouse.yml]`; job runs `npm ci` → `npm run build` → `npm run lhci` (NOT `npx lhci` — there's an unrelated squatted `lhci` package on the registry; `npm run lhci` resolves `node_modules/.bin/lhci` from `@lhci/cli`); job-level `continue-on-error: true` (it's a budget *tripwire*, never a required check — no branch-protection interaction). Mirrors `frontend-ci.yml`'s checkout@v4 / setup-node@v4 node-20 / `defaults.run.working-directory: frontend`.
- **`.gitignore`** — added `frontend/.lighthouseci/` (the run output dir `lhci autorun` writes).
- **`CONVENTION.md`** — new §13 Performance / Lighthouse Convention (`.cjs` rationale / `npm run lhci` flow / a11y hard gate vs warn budgets / `continue-on-error` workflow / add new public pages to the url list).

### Drift findings (Day 8)
| ID | Finding | Implication |
|----|---------|-------------|
| D-DAY8-1 | jsx-a11y recommended surfaced only **5 violations** total (3 files), all genuinely fixable; the codebase was already mostly accessible | Fixed all 5 (1 targeted disable for the shadcn-wrapper false positive + 4 real fixes). No need to down-tune any rules — `--max-warnings 0` holds with the full recommended set. |
| D-DAY8-2 | `lighthouserc.js` (checklist literal) won't work — package.json is `"type":"module"` so a `.js` config is ESM and LHCI's `require()`-based loader can't read `module.exports` | Used `lighthouserc.cjs` (same precedent as `i18next-parser.config.cjs` on Day 7). `lhci healthcheck` confirms the config is found. |
| D-DAY8-3 | `npx lhci` (checklist literal in the workflow draft) is risky — there's an unrelated `lhci` package on npm that prints "Hello, this is AnupamAS01!" (got it briefly when I ran `npx lhci` from the wrong cwd) | Workflow + the script use `npm run lhci` which resolves the local `node_modules/.bin/lhci` from `@lhci/cli`. Never `npx lhci` directly. |

### Verification (Day 8 aggregate)
- Frontend: **`npm run lint` clean** with jsx-a11y recommended now enabled (0 violations after the 5 fixes); **`npm run build` ✅** — main `index-*.js` **304.37 kB** gzip 97.67 (Day 7: 304.37 / 97.66 — unchanged; the a11y fixes are byte-level: a few attrs + a comment), `RequireAuth` lazy chunk **127.00 kB** unchanged; **`npm run test` → 56 files / 233 passed** (unchanged from Day 7 — the 3 touched src files have no broken tests). `node_modules/.bin/lhci healthcheck` ✅; **local `npm run build && npm run lhci` autorun ✅** — `Checking assertions against 1 URL(s) … All results processed! … Uploading median LHR … success!` (one harmless "Timed out waiting for the server to start listening" warning — LHCI's stdout pattern didn't match `vite preview`'s, but Lighthouse ran against the live server fine; no assertion failures → exit 0). Cleaned up `.lighthouseci/` after.
- Backend: **untouched** (zero `.py` changes — Day 8 is eslint config + 3 a11y fixes + LHCI config + GH workflow + CONVENTION.md + .gitignore) — pytest baseline **1676 + 4 skip** holds, `mypy src --strict` 306 clean holds, **9/9 V2 lints** green holds.
- Not run here: the new `a11y-scan.spec.ts` (no dev-server boot) → US-C1 sweep; a real Lighthouse-on-PR (the workflow does it; verified locally that `lhci autorun` works end-to-end).
- Pace note: Days 0-8 done = 11/15 USs (A1-A5 + B1-B7) at 8/10 calendar days — `frontend-foundation-spike` 0.50 still tracking; no `AD-Sprint-Plan-N`.

---

## Day 9 — US-B8 (visual regression) + US-B9 (auth pages rewrite) + US-C1 (closeout) — code `8f7961dc`

### US-B8 — visual regression (§9.1)
- **NEW `tests/e2e/visual/visual-regression.spec.ts`** — `expect(page).toHaveScreenshot(name, { fullPage, animations:"disabled" })` × 6: AppShellV2 chrome (via `/loop-debug`, `/auth/me` mocked) + `/auth/login` + `/cost-dashboard` + `/governance` + `/verification/recent` + `/admin-tenants` (all with fixed-data `page.route()` mocks). **`test.skip(!process.env.RUN_VISUAL, …)`** — baselines (`*-snapshots/*.png`) MUST be generated on the CI Linux runner, not committed from a dev box (font rendering / DPI differ → all-mismatch). The infra is in place; baseline-gen + un-skip = `AD-Visual-Baseline-Generation` (carryover, retrospective Q4).
- **`playwright.config.ts`** — `expect.toHaveScreenshot: { animations:"disabled", maxDiffPixelRatio: 0.02 }`.
- **NEW `frontend/.gitattributes`** — `*.png binary` (for the future `-snapshots/`).

### US-B9 — auth pages rewrite + lazy-load (§9.2)
- **`pages/auth/login/index.tsx`** — rewritten: `<AuthShell>` + `<Card>`/`<CardHeader>`/`<CardContent>`; page-level `<h1>` (styled like CardTitle — the card *is* the whole page; gives every auth page an h1 for a11y); `<Button>` (default) for "Login with WorkOS", `<Button variant="secondary" size="sm">` for the dev-login submit; error banner = `role="alert"` div (`bg-destructive/10 border-destructive/40 text-destructive` + `<AlertTriangle>`); dev-login `<input>`s get `htmlFor`/`id` (`dev-login-tenant-code` / `dev-login-email`); `{import.meta.env.DEV && <DevLoginSection/>}`; **ALL inline `style={{}}` removed** — Tailwind only. i18n strings unchanged (US-B5).
- **`pages/auth/callback/index.tsx`** — rewritten: `<AuthShell>`; loading = `<div role="status"><Loader2 animate-spin/><p>{t("completing")}</p></div>`; error = `<div role="alert"><EmptyState icon={<AlertTriangle/>} title={t("errorTitle")} message={errorMessage} action={<Button asChild variant="outline"><Link to="/auth/login">{t("backToLogin")}</Link></Button>}/></div>` (the `<div role="alert">` wrapper because `<EmptyState>` is semantically a "no-data" panel, not an alert); bootstrap+navigate logic unchanged (US-A1); inline styles removed.
- **`App.tsx`** — `LoginPage` / `CallbackPage` now `const … = lazy(() => import(...))` (were static imports). They're inside the existing `<Suspense fallback={<PageLoading/>}>`. **This is the key bundle fix**: a barrel import (`import { Button } from "@/components/ui"`) from a *statically*-bundled page drags the *whole* `ui/` layer — incl. the `dialog`/`dropdown-menu` modules + their Radix deps — into `main` (a +120 kB regression on the first rewrite attempt). Lazy-loading the auth pages puts that cost in a lazy chunk → **main bundle 297.89 kB gzip 95.27**, ~flat vs the Day-0 baseline 296.58 kB; `RequireAuth` lazy chunk shrank 127→9 kB (Radix hoisted to shared chunks). So Day 9 net-*improved* the main bundle vs Day 7's 304 kB.
- **`UserMenu.tsx`** — no change (already `<DropdownMenu>` + role badges from Day 5, locale switcher from Day 7).
- **Inline-style cleanup sweep (broad — ~15 files)** — 🚧 deferred → `AD-Inline-Style-Cleanup-Sweep`. Did the auth pages (the highest-value — full of inline styles + the entry points). The rest (`SubagentTree` / `TenantSettingsView` / `TenantList{Pagination,Table,Filters}` / `ChatLayout` / `SLAMetricsCard` / `MonthPicker` / `CostBreakdownTable` / `MessageList` / `ApprovalCard` / `ToolCallCard` + admin-tenants index) still have `style={{}}` → Tailwind — mechanical bulk work, better as its own focused pass (sanctioned by checklist §"大 sprint scope 控管"). The `no-inline-style` lint/test guard waits for the sweep to complete (it'd fail now).
- Tests: `tests/unit/pages/auth/login.test.tsx` +1 ("page-level h1 + 0 `[style]` elements"); **NEW `tests/unit/pages/auth/callback.test.tsx`** (2 — loading spinner / error EmptyState + Back-to-login `<Link href="/auth/login">`; both assert 0 `[style]`).

### US-C1 — closeout (§9.3-§9.9)
- **`routes.config.ts`** — confirmed: 4 pages already `<RequireAuth>`-gated (Day 2) + `nameKey` populated (Day 7); 0 NEW page.
- **Full validation sweep** — frontend: `npm run lint` clean (jsx-a11y on) / `npm run build` ✅ main 297.89 kB / **`npm run test` → 57 files / 236 pass** (Day-0 baseline 168/45 → +68). Backend: **untouched since Day 6** (zero `.py` changes Days 7-9) → pytest baseline **1676+4** / mypy --strict 306 / 9-9 V2 lints / black+isort+flake8 / LLM SDK leak 0 — all hold; not re-run (surgical-change discipline; the user can run `cd backend && python -m pytest` to confirm before merge). **e2e (playwright a11y / visual / governance / chat-v2 / locale-switch / auth-gate) NOT run in the dev sessions** (no dev-server/backend boot) → CI (`playwright-e2e.yml`) + `AD-Frontend-E2E-Sweep` carryover; the spec code is all in place (5 NEW spec files).
- **`retrospective.md`** — NEW, Q1-Q7 (Q2: ratio ~0.95–1.0 in band — actual hours estimated, not rigorously per-day-tracked; Q6: KEEP `frontend-foundation-spike` 0.50; Q7: design note N/A SKIP — foundation-completion, not a new-domain spike). Q4 logs the carryover ADs (AD-Inline-Style-Cleanup-Sweep / AD-Visual-Baseline-Generation / AD-Frontend-E2E-Sweep + AD-Bundle-Size [downgraded optional] / AD-i18n-Feature-Namespaces / AD-WorkOS-Prod-Redirect-Flow / AD-Lighthouse-Visual-Hard-Gate / AD-Frontend-RUM-SessionReplay). Q4.1 = 5 closeout decision points (surfaced in the PR description).
- **memory snapshot** — NEW `memory/project_phase57_13_frontend_foundation_completion.md` + MEMORY.md index +1 row.
- **doc syncs** — `16-frontend-design.md` V2 Ship Timeline +1 entry ("Frontend Foundation 1/N COMPLETE" + delivered list + carryovers + 57.14+ candidates); `.claude/rules/sprint-workflow.md` calibration matrix +1 row (`frontend-foundation-spike` 0.50 1-data-point ~0.95–1.0 KEEP) + MHist entry; `gap-analysis §0.4` +1 row + Top-10 #1/#2/#3 updated (#3 → ✅ done, not "大致"); checklist + plan header MHist closeout entries. `CONVENTION.md §10-§13` / `STYLE.md §6-§8` / `frontend-react.md` L90 already cover the relevant rules — no new edits needed. `CLAUDE.md` + `SITUATION-V2-SESSION-START.md` → DEFERRED post-merge (per checklist plan).
- **17.md** — unchanged: **0 NEW agent_harness contract / ABC / LoopEvent / migration** this sprint; the 4 NEW api/v1 endpoints (`GET /auth/me`, `POST /auth/dev-login`, `POST /telemetry/frontend`, `POST /telemetry/frontend-error`) + `require_tenant_match_or_platform_admin` are HTTP-boundary code documented in their file headers — outside 17.md's scope.
- **PR** — branch pushed; PR opened with the V2-紀律-9 self-check + the 5 closeout decision points. **Squash merge NOT done in-session** — per the executing-actions-with-care policy, a merge to `main` is surfaced to the user for confirmation.

### Drift findings (Day 9)
| ID | Finding | Implication |
|----|---------|-------------|
| D-DAY9-1 | First auth-page rewrite used `import { Button } from "@/components/ui"` (the barrel) — `App.tsx` static-imports `LoginPage`, so Rollup pulled the whole `ui/` layer (incl. `dialog`/`dropdown-menu` + Radix) into `main` → +120 kB | Fixed by `React.lazy()`-ing the auth pages (kept the barrel import — the barrel side-effect goes into the lazy chunk, deduped against `RequireAuth`). Net result *better* than before. Lesson for CONVENTION §10: barrel re-exports are fine for lazy-loaded consumers; a barrel import from a statically-bundled module drags the whole layer. |
| D-DAY9-2 | `<EmptyState>` (Day 4) has no `role="alert"` — it's a "no-data" panel; the callback error page needs an alert region | Wrapped `<EmptyState>` in `<div role="alert">` on the callback error path (correct semantics; keeps the a11y-scan spec's `getByRole("alert")` valid). |
| D-DAY9-3 | Login `<CardTitle>` would render `<h3>`, not the page-level `<h1>` a login page should have | Used a styled `<h1>` (CardTitle classes) inside `<CardHeader>` instead of `<CardTitle>` — page-level h1 + card styling, no class duplication beyond the one className. |
| D-DAY9-4 | The broad inline-style sweep (~17 files) + visual baselines + e2e execution are too large / not-runnable-here to finish in Day 9 | Minimal-viable per checklist §"大 sprint scope 控管": auth pages done; the rest → 3 carryover ADs (AD-Inline-Style-Cleanup-Sweep / AD-Visual-Baseline-Generation / AD-Frontend-E2E-Sweep). 13/15 USs full + 2 minimal-viable. |

### Verification (Day 9 aggregate)
- Frontend: `npm run lint` clean (jsx-a11y recommended) / `npm run build` ✅ — main `index-*.js` **297.89 kB** gzip 95.27 (Day 7-8: 304.37 / 97.66 — **−6.5 kB / −2.4 kB gzip**; ~flat vs Day-0 baseline 296.58), `RequireAuth` lazy chunk **8.91 kB** (Day 8: 127.00 — Radix hoisted to shared chunks now that auth pages are lazy too) / **`npm run test` → 57 files / 236 passed** (Day 8: 56/233; +1 file / +3 tests = 1 login.test.tsx + 2 callback.test.tsx). Deliberate ErrorBoundary "kaboom" + jsdom "navigation not implemented" on stderr — not failures.
- Backend: **untouched since Day 6** — baselines hold (pytest 1676+4 / mypy --strict 306 / 9-9 V2 lints / black+isort+flake8 / LLM SDK leak 0).
- Not run here: the full backend `pytest` re-run (nothing changed; user can confirm) + the playwright e2e suite (no dev-server boot) → CI + `AD-Frontend-E2E-Sweep`.
- Calibration (Q6): `frontend-foundation-spike` 0.50, 1-data-point, ratio ~0.95–1.0 ✅ in [0.85, 1.20] → KEEP; recorded in sprint-workflow.md matrix.

---

## Remaining for Day 7-9

- [x] Day 3: US-A5 (connectivity smoke + .env.example) + US-B1 (Toast) — `e1c3f58e`
- [x] Day 4: US-B2 (design-system component layer + adopt across 6 feature areas) + mid-sprint ratio check — `02910cfe`
- [x] Day 5: US-B3 (Radix Dialog+DropdownMenu primitives + DecisionModal+UserMenu refactor) — `6bb4fdde`
- [x] Day 6: US-B4 (Sentry + Web Vitals + Cat 12 telemetry endpoint) — `a8b90ba4`
- [x] Day 7: US-B5 (i18n — i18next zh-TW/en + shell/usermenu/auth/2-page adoption + locale switcher) — `890876f7`
- [x] Day 8: US-B6 (a11y baseline — jsx-a11y + axe-core scan, 5 violations fixed) + US-B7 (Lighthouse CI — lighthouserc.cjs + GH workflow) — `c3294318`
- [x] Day 9: US-B8 (visual-regression spec — skipped pending CI baselines) + US-B9 (auth pages rewrite: AuthShell+Card+Button, Tailwind, lazy-loaded → main 297.89 kB ~flat) + US-C1 (closeout — retrospective.md / memory / doc syncs / PR) — `8f7961dc`(code) + docs
- **Sprint 57.13 status: 13/15 USs fully delivered + 2 minimal-viable** (US-B8 visual = spec written, baselines deferred; US-B9 inline-cleanup = auth pages done, broad ~15-file sweep deferred). PR opened end of Day 9; **squash-merge surfaced to user** (not done in-session).
- 🚧 Carryover ADs (live work — see retrospective.md Q4): **AD-Inline-Style-Cleanup-Sweep** (~15 files → Tailwind + add no-inline-style guard) / **AD-Visual-Baseline-Generation** (gen `*-snapshots/*.png` on CI Linux, commit, drop `test.skip`) / **AD-Frontend-E2E-Sweep** (run+verify governance / locale-switch / a11y-scan / auth-gate / chat-v2 e2e — consolidates D-DAY4-2 e2e + D-DAY5-3 + D-DAY7-6) / AD-Bundle-Size (downgraded **optional** — main flat vs baseline) / AD-i18n-Feature-Namespaces / AD-WorkOS-Prod-Redirect-Flow / AD-Lighthouse-Visual-Hard-Gate / AD-Frontend-RUM-SessionReplay. Also still open: D-DAY4-2 component-API change (`data-testid?`/`pending?` props on verification/memory/AuditLogViewer for full `<ErrorRetry>`/`<EmptyState>` adoption). 17.md registry: N/A — 0 NEW agent_harness contract this sprint (the 4 NEW api/v1 endpoints are HTTP-boundary, documented in file headers).

---

## Notes / Risks

- **D-PRE-8 is the key finding**: the auth flow being broken at the middleware-allowlist level confirms why the user couldn't log in. US-A1 fixes it (cookie fallback + EXEMPT_PATH_PREFIXES). Combined with the cookie↔localStorage fix (authStore + /auth/me), login → callback → authenticated → navigate becomes end-to-end functional.
- **Bundle size watch**: adding @radix-ui/react-dropdown-menu + @sentry/react + web-vitals + i18next + react-i18next will grow main bundle (~50-70 KB est). Sentry + i18n dynamic-import as mitigation; track vs 296.58 kB; retrospective Q3 + AD-Bundle-Size-285kB-Carryover continuation.
- **Large sprint scope control**: per checklist 重要備註 — if a US超估, go minimal-viable within that US (don't delete US; mark 🚧 + reason → carryover AD). cookie-only fallback path (Bearer + localStorage dev-login) if cookie cross-port fails in dev.
- **Day 1 三-prong完成**: a few content-verify items deferred to Day 1 start (low-risk impl details, none gate Day 1).
