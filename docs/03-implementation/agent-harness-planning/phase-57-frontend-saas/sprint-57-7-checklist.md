# Sprint 57.7 — Checklist (IAM Foundation + Frontend Foundation 1/N spike)

> [Sprint Plan](./sprint-57-7-plan.md)

**Sprint Goal**: Tier 0 Block A (IAM Auth — vendor matrix + OIDC PKCE wire + DB-backed RBAC) + Block B (Frontend Foundation 1/N — Tailwind 4 + shadcn/ui + TanStack Query + RHF + Zod + ErrorBoundary + Sonner + AppShell + 1 page migrate) + AD-Reality 3a sessions/tool_calls observer wire (using US-A2 抽出的 user_id JWT extraction infra unblock);Day 4 extract `20-iam-deep-dive.md` design note per `claudedocs/templates/spike-design-note-template.md` 8-Point Quality Gate (verified ratio ≥ 95%);Hosted vendor route (per user 2026-05-08 decision);7 USs across IAM 3 + Frontend 3 + Reality 1。

---

## Day 0 — Setup + Branch + Pre-flight + 三-prong + Calibration

### 0.1 Branch + plan + checklist commit
- [ ] **Branch from main `d485b42d`**
  - DoD:`git checkout -b feature/sprint-57-7-iam-frontend-foundation`
  - Verify:`git branch --show-current` → `feature/sprint-57-7-iam-frontend-foundation`
  - Note: pre-existing main uncommitted state (sprint-workflow.md / CLAUDE.md / SITUATION-V2 modified + claudedocs/templates/ + enterprise-saas-gap-analysis-20260508.md untracked) — these are 2026-05-08 doc-level rolling updates;include in initial Sprint 57.7 commit per Day 0 D9 RECOMMEND
- [ ] **Commit plan + checklist + progress.md (Day 0) + pre-existing doc updates**
  - DoD:plan + checklist + progress.md + 5 doc files staged + committed with conventional message:`docs(plan, sprint-57-7): IAM Foundation + Frontend Foundation 1/N spike + bundle 2026-05-08 doc-level rolling updates`
  - Verify:`git log --oneline -1` shows commit;`git status --short` clean

### 0.2 Day-0 三-prong 探勘 v1 (per AD-Plan-1+2+3+4 promoted)
- [x] **Prong 1 Path Verify** ✅ (this session — see progress.md §0.2)
  - `backend/src/platform_layer/identity/{jwt.py, auth.py}` exists
  - `backend/src/infrastructure/db/models/{identity.py, api_keys.py}` exists
  - `backend/src/api/v1/auth*.py` NOT exists (US-A2 will create)
  - `frontend/src/pages/auth/` NOT exists (US-A2 will create)
  - 16 Alembic migrations through 0016
- [x] **Prong 2 Content Verify** ✅
  - `JWTManager.encode/decode/verify` plumbing at jwt.py L103-201
  - `_RESERVED_CLAIMS = frozenset({sub, tenant_id, roles, iat, exp})` at jwt.py L112 — OIDC claims via `extra` parameter
  - `auth.py:101+L107+L116` 3× hardcoded frozenset RBAC (RED CONFIRMED Tier 0 #5)
  - 0 LLM SDK leak in `platform_layer/identity/`
- [x] **Prong 3 Schema Verify** ✅ (5 ORM tables exist) + 1 deferred (D8 column-level drift Day 1 morning)
- [x] **Prong 4 Frontend Foundation Verify** ✅ (D7 RED CONFIRMED — package.json 0 of 8 deps)

### 0.3 Calibration multiplier pre-read (HYBRID first application)
- [ ] **`iam-frontend-spike` HYBRID 0.60 weighted blend 1st application (per AD-Sprint-Plan-9 NEW class proposal)**
  - Bottom-up est ~26-33 hr (7 USs + Day 4 closeout) — see plan §Workload table
  - Calibrated commit ~18 hr (weighted blend: IAM 3 USs × 0.60 + Frontend 3 USs × 0.65 + Reality 1 US × 0.50 + closeout × 0.80)
  - Day 4 retro Q2 verify:若 ratio in [0.85, 1.20] → 0.60 blend baseline validated;若 < 0.85 → AD-Sprint-Plan-9 propose lower 0.50 blend (vendor SDK saved more time);若 > 1.20 → AD-Sprint-Plan-9 propose lift 0.75 (OIDC integration deeper);1-data-point baseline this sprint;pending 2-3 sprint window evidence

### 0.4 Pre-flight verify (main green baseline)
- [ ] **Backend baselines (pre-sprint snapshot)**
  - `python -m pytest backend/tests/ -q --tb=no` → 1602 collected / 0 failures
  - `python -m mypy backend/src --strict` → 0 errors / 295 source files
  - `python scripts/lint/run_all.py` → 9 V2 lints 9/9 green
  - `grep -rn "import openai\|import anthropic" backend/src/agent_harness/ backend/src/platform_layer/identity/` → 0
  - Verify:All baselines documented in progress.md ✅
- [ ] **Frontend baselines (pre-sprint snapshot)**
  - `cd frontend && npm run lint` → clean
  - `cd frontend && npm run build` → success / 75 modules / 209.11 kB
  - `cd frontend && npm run test` → 35 unit tests pass
  - `cd frontend && npm run e2e -- --reporter=list` → 23 e2e tests pass
  - Verify:All baselines documented in progress.md ✅

### 0.5 Day 0 commit + push
- [x] **Catalogue D-findings + decide Day 1 scope** ✅ (this session — 9 D-findings catalogued in progress.md §0.5)
- [ ] **Day 0 commit + push**
  - DoD:plan + checklist + progress.md + pre-existing doc updates committed (combined with 0.1)
  - Verify:`git log --oneline -1` shows commit;`git push -u origin feature/sprint-57-7-iam-frontend-foundation`

---

## Day 1 — US-A1 Vendor Matrix + US-A2 OIDC Backend + US-A3 RBAC Start

### 1.1 D8 column-level schema verify (Day 0 deferred)
- [ ] **Verify `users.external_id` column for OIDC subject linking**
  - Read `backend/src/infrastructure/db/models/identity.py` User class
  - Grep `external_id` in identity.py + 0001_initial_identity.py
  - Decision:
    - 若 column 存在 → no migration needed;US-A2 user upsert pattern works
    - 若 column 缺 → US-A2 scope add Alembic 0017 migration `users_external_id` (~1-2 hr;VARCHAR(255) UNIQUE NOT NULL with default empty string for existing rows)
  - Document in progress.md Day 1 entry

### 1.2 US-A1 IAM Vendor Evaluation Matrix
- [ ] **Initiate vendor account signup (parallel with matrix work to mitigate Risk Class A)**
  - WorkOS B2B trial signup
  - Clerk dev account
  - Auth0 dev account (free tier)
  - Supabase Auth (self-host evaluation OR cloud free tier)
- [ ] **Build 4-vendor comparison matrix**
  - Cost (per MAU + per connection;1 year @ 5000 MAU projection)
  - SCIM 2.0 support (✅ / ⚠️ add-on / ❌)
  - SAML 2.0 support
  - OIDC PKCE support
  - Python backend SDK quality (latest version + GitHub stars + last release + maintainers count)
  - React frontend SDK quality
  - SOC 2 Type II inheritance (vendor's compliance docs)
  - Vendor lock-in evaluation (proprietary token format? data export?)
  - Migration off-ramp (「if we leave in 2 years, what does it take」)
  - Signup approval time (Risk Class A)
- [ ] **Document 3 rejection rationale** (specific reasons for non-chosen vendors;NOT「best practice」hand-wave per AP-2)
- [ ] **Document chosen vendor decision** with V2 enterprise B2B target market context (Taiwan/HK + EU optional)
- [ ] **Save matrix to** `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-7/iam-vendor-matrix.md` (intermediate artifact;Day 4 will fold into design note §1)

### 1.3 US-A2 OIDC Backend Wire (chosen vendor)
- [x] **Install chosen vendor SDK** ✅ Day 3
  - `backend/requirements.txt` already pinned `workos>=4.0,<6.0` Day 1
  - `pip install workos` succeeded (no req diff needed)
  - Verify:`python -c "from workos import WorkOSClient, AsyncWorkOSClient"` ✅
  - **AP-2 verify**: 0 transitive `openai` / `anthropic` in workos deps (Risk Class B clean)
- [ ] **`backend/src/core/config.py` Settings extend**
  - Add `jwt_jwks_url: str = ""` field
  - Add `vendor_api_key: str = ""` (read from env)
  - Add `vendor_client_id: str = ""` (read from env)
  - Add `oidc_redirect_uri: str = "http://localhost:3005/auth/callback"` (configurable)
  - Update `.env.example` with placeholder values
- [ ] **NEW `backend/src/platform_layer/identity/oidc.py`**
  - `OIDCFlow` class with methods:
    - `async def initiate_login(redirect_uri: str) -> tuple[str, str]` — returns (authorize_url, state) + stores code_verifier in Redis (TTL 10 min) keyed by state
    - `async def exchange_callback(code: str, state: str) -> dict` — retrieves code_verifier from Redis + vendor SDK exchange + returns vendor token + user info
    - `async def signout(token: str) -> str` — vendor SDK signout + returns redirect URL
  - File header per file-header-convention.md (Category: §Platform Layer / Identity)
- [ ] **`backend/src/platform_layer/identity/jwt.py` extend with JWKS validation**
  - NEW `async def decode_with_jwks(token: str, jwks_url: str) -> JWTClaims` method
  - Fetches JWKS from URL (with cache TTL 1 hour)
  - Verifies token signature against vendor's public key
  - Falls back to existing `decode()` for HS256 internal V2 JWT
  - **OR** if chosen vendor only supports HS256 → document trade-off in design note + open invariant
  - Update file header MHist: `2026-05-09: Sprint 57.7 — add JWKS validate path for OIDC vendor (closes US-A2 partial)`
- [ ] **NEW `backend/src/api/v1/auth.py`** with 3 endpoints:
  - `GET /api/v1/auth/login?redirect_uri=...` → `OIDCFlow.initiate_login()` + 302 redirect to vendor authorize URL
  - `GET /api/v1/auth/callback?code=...&state=...` → `OIDCFlow.exchange_callback()` + user upsert + V2 JWT issue + redirect to original `redirect_uri` with JWT (cookie or query param;security model in design note)
  - `POST /api/v1/auth/logout` → JWT invalidate + `OIDCFlow.signout()`
  - File header per convention (Category: §API Layer)
- [ ] **Wire `api/main.py` to register `auth.py` router**
  - Add `app.include_router(auth_router, prefix="/api/v1")`
- [ ] **NEW `backend/src/api/dependencies/auth.py` (or extend existing)**
  - `Depends(get_current_user)` extracts JWT from `Authorization: Bearer <token>` header
  - Decodes V2 JWT via `JWTManager.decode()`
  - Loads `User` row from DB by `users.id`
  - Returns `User` object with tenant_id + roles (used by US-R1 + US-A3)
- [x] **6+ unit tests** in `backend/tests/unit/platform_layer/identity/test_oidc.py` ✅ Day 3 (7 tests)
  - 1 initiate_login URL+state happy path (mock sync client)
  - 1 exchange_callback CSRF state mismatch raises OIDCStateError
  - 1 exchange_callback returns OIDCProfile on vendor success (mock async)
  - 1 callback endpoint missing tenant cookie → 400
  - 1 callback endpoint unknown tenant → 400 (DB lookup miss mocked)
  - 1 _upsert_user_from_oidc INSERTs new User on first login (mock AsyncSession)
  - **BONUS**: 1 vendor exception → OIDCExchangeError mapping
  - File header per convention ✅

### 1.4 US-A3 DB-backed RBAC start
- [ ] **NEW `backend/src/platform_layer/identity/rbac.py`**
  - `RBACManager` class with:
    - `async def has_role(user_id: UUID, tenant_id: UUID, role_label: str) -> bool` — SQL JOIN per TS-3
    - `async def has_permission(user_id: UUID, tenant_id: UUID, action: str, resource: str) -> bool` — SQL JOIN
  - File header per convention (Category: §Platform Layer / Identity)
- [ ] **MODIFY `backend/src/platform_layer/identity/auth.py`**
  - REMOVE 3 frozenset constants (`_AUDIT_ROLES` / `_APPROVER_ROLES` / `_ADMIN_PLATFORM_ROLES`)
  - REWIRE `_require_role()` to call `RBACManager.has_role()` with role_label
  - Preserve API surface of `require_audit_role` / `require_approver_role` / `require_admin_platform_role` — internally call `_require_role()`
  - Update file header MHist: `2026-05-09: Sprint 57.7 — replace 3 frozenset RBAC with DB-backed RBACManager (closes US-A3)`

### 1.5 Day 1 commit + push + progress.md
- [ ] **Commit Day 1 evidence**
  - Stage: requirements.txt + config.py + oidc.py + jwt.py + auth.py (router) + auth.py (dep) + rbac.py + auth.py (RBAC rewire) + test_oidc.py + iam-vendor-matrix.md + progress.md
  - Commit:`feat(identity, sprint-57-7): Day 1 US-A1 vendor matrix + US-A2 OIDC backend + US-A3 DB-backed RBAC start`
  - Verify:`git log main..HEAD --oneline` shows new commit;remote up-to-date

---

## Day 2 — US-A2 Frontend Auth + US-A3 finish + US-B1 Frontend Install

### 2.1 US-A2 Frontend Auth UX (basic React + react-router;NOT yet AppShell)
- [ ] **NEW `frontend/src/pages/auth/login/index.tsx`**
  - Render「Login with Microsoft Entra」button
  - On click → `window.location.href = '/api/v1/auth/login?redirect_uri=' + encodeURIComponent(currentPath)`
  - Display error message if `?error=...` query param (callback failure)
  - File header per convention
- [ ] **NEW `frontend/src/pages/auth/callback/index.tsx`**
  - On mount → extract JWT from URL query param OR cookie
  - Store JWT in `localStorage` (basic — security model TBD in design note;httpOnly cookie option for Phase 58+)
  - Redirect to original `redirect_uri` (or `/cost-dashboard` default)
  - Display loading spinner during JWT extract
  - File header per convention
- [ ] **MODIFY `frontend/src/App.tsx`**
  - Add 2 routes: `/auth/login` + `/auth/callback`
  - NO yet AppShell wrap (US-B2 will introduce later)
- [ ] **NEW `frontend/src/services/auth.ts`**
  - `getJwt(): string | null` — reads from localStorage
  - `setJwt(token: string): void`
  - `clearJwt(): void`
  - `isAuthenticated(): boolean`
- [ ] **MODIFY existing `frontend/src/services/*.ts`** API call helpers
  - Add `Authorization: Bearer <jwt>` header if `isAuthenticated()`
- [ ] **Manual verify OIDC flow end-to-end**
  - `python scripts/dev.py start` (backend + frontend)
  - Browser visit `http://localhost:3005/cost-dashboard` → redirected to login (TBD if this redirect logic added or just show empty page)
  - Click「Login with Entra」 → vendor redirect → real Entra auth
  - Callback → JWT in localStorage
  - Redirect to cost-dashboard with auth header
  - Verify in browser DevTools Network tab: `Authorization: Bearer eyJ...` present
  - Capture screenshot to progress.md

### 2.2 US-A3 DB-backed RBAC finish + endpoint demo
- [ ] **MODIFY `backend/src/api/v1/admin/tenants.py` GET endpoint**
  - Already uses `Depends(require_admin_platform_role)` — verify still works post-RBAC rewire
  - Add explicit per-tenant role isolation test scenario in unit test
- [ ] **4+ unit tests** in `backend/tests/unit/platform_layer/identity/test_rbac.py`:
  - 1 happy path: user has role → returns True
  - 1 happy path: user lacks role → returns False (raises 403)
  - 1 cross-tenant isolation: user with role in tenant A queried for tenant B → False
  - 1 backwards compat: existing `require_admin_platform_role` dependency still works post-rewire
  - File header per convention
- [ ] **Backend integration smoke**
  - `python -m pytest backend/tests/unit/platform_layer/identity/ -q` → 6 + 4 = 10+ tests pass
  - `python -m pytest backend/tests/integration/admin/ -q` → existing admin tenants tests still pass (regression)

### 2.3 US-B1 Frontend Foundation Install
- [ ] **`frontend/package.json` add 8 deps**
  - dependencies: `@tanstack/react-query@^5.0.0` + `react-hook-form@^7.0.0` + `zod@^3.0.0` + `react-error-boundary@^4.0.0` + `sonner@^1.0.0`
  - devDependencies: `tailwindcss@^4.0.0` + `@tailwindcss/postcss` + `@tanstack/react-query-devtools@^5.0.0`
  - Run `npm install`
- [ ] **NEW `frontend/tailwind.config.ts`**
  - Content paths: `["./index.html", "./src/**/*.{ts,tsx}"]`
  - Theme: extend with shadcn-compatible CSS variables
  - Dark mode: class strategy
- [ ] **NEW `frontend/postcss.config.cjs`**
  - Plugins: `'@tailwindcss/postcss': {}` + `autoprefixer: {}`
- [ ] **MODIFY `frontend/src/index.css`**
  - Add `@tailwind base;` + `@tailwind components;` + `@tailwind utilities;`
  - Define shadcn CSS variables (root + dark)
- [ ] **Initialize shadcn CLI**
  - `cd frontend && npx shadcn-ui@latest init` (interactive — accept defaults TypeScript + Default style + Slate base + RSC false)
  - `components.json` committed
- [ ] **Add 5 shadcn components**
  - `npx shadcn-ui@latest add button input card dialog`
  - Sonner Toaster used directly (not via shadcn)
  - Files appear at `frontend/src/components/ui/{button,input,card,dialog}.tsx`
- [ ] **`npm run build` verify**
  - Build succeeds
  - Bundle size delta: 209.11 kB → ≤ 314 kB (< +50% balloon per Risk Class D)
  - Capture build output to progress.md
- [ ] **`npm run lint` verify**
  - ESLint clean (0 warnings;shadcn boilerplate may need eslint-disable comments)

### 2.4 Day 2 commit + push + progress.md
- [ ] **Commit Day 2 evidence**
  - Stage: pages/auth/{login,callback}/index.tsx + App.tsx + services/auth.ts + services/*.ts (if modified) + test_rbac.py + package.json + tailwind.config.ts + postcss.config.cjs + components.json + index.css + components/ui/*.tsx + progress.md
  - Commit:`feat(frontend, sprint-57-7): Day 2 US-A2 frontend auth + US-A3 RBAC finish + US-B1 frontend foundation install`
  - Verify:`git log main..HEAD --oneline` shows new commit

---

## Day 3 — US-B2 AppShell + US-B3 Migrate + US-R1 Observer

### 3.1 US-B2 AppShell + ThemeProvider + AppErrorBoundary
- [ ] **NEW `frontend/src/components/AppShell.tsx`**
  - Props: `children` + optional `headerActions`
  - Layout: `<header>` (logo + nav links + headerActions) + `<main className="container mx-auto p-6">{children}</main>` + `<footer>` (copyright + version)
  - Tailwind utility classes throughout (NO inline style)
  - File header per convention
- [ ] **NEW `frontend/src/components/ThemeProvider.tsx`**
  - Context with `theme: 'light' | 'dark'` + `toggleTheme()`
  - Persists to localStorage
  - Applies/removes `dark` class on `html` element
- [ ] **NEW `frontend/src/components/AppErrorBoundary.tsx`**
  - Wraps `react-error-boundary.ErrorBoundary` with custom fallback
  - Fallback UI: Card with error message + Reset button + (placeholder for Sentry deferred)
- [ ] **MODIFY `frontend/src/main.tsx`**
  - Wrap App in: `<ThemeProvider><AppErrorBoundary><App /></AppErrorBoundary></ThemeProvider>`
  - Add `<Toaster richColors position="top-right" />` mount
  - Add TanStack Query: `<QueryClientProvider client={queryClient}>` wrap entire tree
- [ ] **3+ Vitest tests** in `frontend/src/components/__tests__/AppShell.test.tsx`:
  - 1 AppShell renders children inside main slot
  - 1 ThemeProvider toggle persists to localStorage
  - 1 AppErrorBoundary catches thrown error + renders fallback
  - File header per convention

### 3.2 US-B3 cost-dashboard migrate
- [ ] **REFACTOR `frontend/src/pages/cost-dashboard/index.tsx`**
  - Wrap in `<AppShell>...</AppShell>`
  - Replace inline `style={{}}` with Tailwind utility classes
  - Replace ad-hoc fetch with `useQuery({ queryKey: ['cost-summary', tenantId], queryFn: ... })`
  - Use shadcn Card for 6 metric tiles
  - Update file header MHist: `2026-05-10: Sprint 57.7 — migrate to AppShell + Tailwind + TanStack Query (closes US-B3)`
- [ ] **Verify existing tests still pass (regression sentinel)**
  - `cd frontend && npm run test -- cost-dashboard` → all 4 existing Vitest pass
  - `cd frontend && npm run e2e -- cost-dashboard` → 1 existing Playwright passes
  - **0 test deletion** per V2 紀律
- [ ] **2+ NEW Vitest tests** in `frontend/src/pages/cost-dashboard/__tests__/migrate.test.tsx`:
  - 1 TanStack Query loading state renders skeleton
  - 1 TanStack Query error state renders fallback
  - File header per convention
- [ ] **Bundle size re-verify**
  - `npm run build` after migrate
  - Delta from 75 modules / 209.11 kB → ~ +5-10 modules / +30-60 kB acceptable
  - Capture to progress.md

### 3.3 US-R1 AD-Reality 3a sessions/tool_calls observer wire
- [x] **NEW `backend/src/infrastructure/db/repositories/session_repository.py`** ✅ Day 3 Tier 2
  - `SessionRepository.create_session(session_id, user_id, tenant_id, title)` DAO
  - File header per convention ✅
- [x] **NEW `backend/src/infrastructure/db/repositories/tool_call_repository.py`** ✅ Day 3 Tier 2
  - `ToolCallRepository.create(session_id, tenant_id, tool_name, arguments, status, duration_ms, permission_check_passed)` DAO
  - File header per convention ✅
- [x] **MODIFY `api/v1/chat/router.py` LoopStarted observer** ✅ Day 3 Tier 2 (D19: existing user_id infra usable, no new dep needed)
  - Pre-stream Session INSERT with `Depends(get_current_user_id)` real user_id from JWT
  - Best-effort SAVEPOINT (`db.begin_nested()`) per Sprint 57.6 audit_log pattern
  - Env flag `SESSIONS_CHAT_OBSERVER` default true (production) / false (tests)
  - File header MHist updated ✅
- [x] **MODIFY `api/v1/chat/router.py` ToolCallExecuted observer** ✅ Day 3 Tier 2
  - On ToolCallExecuted event → ToolCallRepository.create
  - Best-effort SAVEPOINT + env flag `TOOL_CALLS_CHAT_OBSERVER`
- [x] **6 unit tests** ✅ Day 3 Tier 2 (target +5 ⏫ +20%)
  - `test_session_and_tool_call_repos.py`: 2 SessionRepository + 4 ToolCallRepository tests
  - Mocked AsyncSession matching test_oidc.py pattern
  - File header per convention ✅
- [ ] 🚧 **Manual verify DB persist end-to-end** DEFERRED Phase 58+ integration test
  - Reason: requires real Postgres + WorkOS B2B account approved + RLS context working;unit-level mocks already verify call contract
- [x] **AD-Reality-3a + AD-Reality-3b closed evidence captured in progress.md §3.6+§3.7** ✅

### 3.4 Backend smoke + frontend smoke
- [ ] **Backend full pytest run**
  - `python -m pytest backend/tests/ -q --tb=short`
  - Expected: 1602 → ≥ 1620 (+18 minimum)
  - 0 failures / 0 errors
- [ ] **Frontend full build + test run**
  - `cd frontend && npm run build` → success
  - `cd frontend && npm run test` → 35 → ≥ 40 unit tests pass
  - `cd frontend && npm run e2e` → 23 → ≥ 25 e2e tests pass
- [ ] **9 V2 lints final verify**
  - `python scripts/lint/run_all.py` → 9/9 green

### 3.5 Day 3 commit + push + progress.md
- [ ] **Commit Day 3 evidence**
  - Stage: AppShell.tsx + ThemeProvider.tsx + AppErrorBoundary.tsx + main.tsx + AppShell.test.tsx + cost-dashboard/index.tsx + migrate.test.tsx + session_repository.py + tool_call_repository.py + chat.py + test_chat_observer_sessions.py + progress.md
  - Commit:`feat(frontend+backend, sprint-57-7): Day 3 US-B2 AppShell + US-B3 cost-dashboard migrate + US-R1 sessions/tool_calls observer (closes AD-Reality-3a)`
  - Verify:`git log main..HEAD --oneline` shows new commit

---

## Day 4 — Day 4 Closeout: Design Note + Retro + PR

### 4.1 NEW `docs/03-implementation/agent-harness-planning/20-iam-deep-dive.md` design note
- [ ] **Author per `claudedocs/templates/spike-design-note-template.md` 8-Point Quality Gate**
  - Frontmatter (title / purpose / category / created / sprint_source / verified_ratio ≥ 95% / status: Active)
  - §0 Spike Summary (sprint scope / verified period / calibration ratio / verification counts)
  - §1 Decision Matrix (4-vendor comparison + chosen vendor + 3 rejection rationale + cost projection;fold in iam-vendor-matrix.md intermediate artifact from Day 1)
  - §2 Verified Invariants (each with `file:line` + verification command):
    - §2.1 OIDC PKCE Flow (file:line for `oidc.py:OIDCFlow.initiate_login` + `exchange_callback` + verification: `pytest test_oidc.py::test_callback_exchange`)
    - §2.2 RS256 + JWKS Validation (file:line for `jwt.py:decode_with_jwks` + verification command;OR document HS256 trade-off if vendor only supports HS256)
    - §2.3 User Upsert via external_id (file:line for upsert SQL + verification: `pytest test_oidc.py::test_user_upsert_first_login`)
    - §2.4 DB-Backed RBAC (file:line for `rbac.py:RBACManager.has_role` SQL JOIN + verification: `pytest test_rbac.py::test_cross_tenant_isolation`)
  - §3 Cross-Category Contracts (none — auth flow is standalone vertical;NO new 17.md contract added)
  - §4 Open Invariants (deferred to Phase XX.Y):
    - SAML 2.0 (Phase 58+ when $50K+ ACV deal)
    - MFA TOTP / Refresh Token Rotation (Phase 58+)
    - SCIM 2.0 provisioning (Phase 58+ when 100+ MAU tenant)
    - Frontend auth UX polish (sign-up flow / forgot password / MFA settings — Phase 58.2+ Frontend Pages 11)
    - Sentry frontend error tracking (Phase 58.2+ Tier 1)
  - §5 Rollback / Fallback (revert: `auth.py` route + `oidc.py` + `rbac.py` + `users.external_id` Alembic 0017 + frontend auth pages;estimated 1-2 days;sentinel: existing frozenset-RBAC backup branch tag `rbac-frozenset-pre-57.7`)
  - §6 References (sprint plan / retrospective / 17.md cross-ref absent confirmed / .claude/rules/multi-tenant-data.md)
  - §7 Modification History (1 entry: Initial extract from Sprint 57.7 closeout Day 4)
  - **Length target**: 200-500 lines (outcome, NOT cap;若真學到 500+ 行 verified content 就寫 500+)
- [ ] **8-Point Quality Gate self-check**
  - [ ] 1. Section header 對應 spike user story (US-A1/A2/A3 → §1/§2.x)
  - [ ] 2. 每個技術 claim 有 file:line
  - [ ] 3. Decision rationale 含比較矩陣 (§1 vendor matrix)
  - [ ] 4. Verification command reproducible (pytest commands per §2.x)
  - [ ] 5. Test fixture reference (test_oidc.py + test_rbac.py + test_chat_observer_sessions.py)
  - [ ] 6. Open invariant 明確分界 (§4 Deferred list)
  - [ ] 7. Rollback / fallback 路徑 (§5)
  - [ ] 8. Cross-reference 17.md single-source (§3 confirmed NO new contract)
- [ ] **User reviewer pass** — present design note draft;await approval before commit

### 4.2 Retrospective.md
- [ ] **Create `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-7/retrospective.md`**
  - Q1 What went well — IAM vendor matrix process / OIDC wire path 哪些 worked smoothly / Frontend foundation install 哪些 顯著 ROI
  - Q2 What didn't go well + calibration ratio:
    - Compute: actual_total_hr / committed_18_hr ratio
    - Document delta vs expected ≈ 1.0
    - 若 |delta| > 30% → log AD-Sprint-Plan-9 evidence (1-data-point insufficient for promotion;need 2-3 sprint window)
    - 若 ratio in [0.85, 1.20] → blend baseline 0.60 validated;mark calibration matrix entry「pending 2-3 sprint validation」
  - Q3 What we learned — Hosted vendor route validation / Tailwind 4 vs CSS-in-JS migration cost / OIDC PKCE complexity vs documentation
  - Q4 Audit Debt deferred — Top N findings carry-forward to Phase 57.x+ (e.g. SAML / MFA / Refresh / SCIM all deferred per spec;但 NEW finding may surface during Day 1-3 — catalogue here)
  - Q5 Next steps + Phase 57.8+ direction proposal:
    - Per gap-analysis §6 adjusted roadmap: Phase 57.8 = SOC 2 Readiness + SBOM Supply Chain (Block C + D);Phase 57.9 = Status Page + APAC Compliance (Block E + F);Phase 58.0+ = Tier 1 IaC + DR drill
    - 不寫具體 Phase 57.8 plan tasks per rolling planning 紀律;只列 candidate scope
    - 若 Day 4 user 想 pivot (e.g. 因 IAM 體驗 promotional pages 缺) → record alternative direction
  - Q6 Solo-dev policy validation
  - Q7 8-Point Quality Gate self-grade (verified ratio % + 8 gates pass count)
  - Verify:`wc -l retrospective.md` ≥ 250 lines

### 4.3 Memory snapshot + MEMORY.md index
- [ ] **Create `memory/project_phase57_7_iam_frontend_foundation.md`**
  - Same format as `project_phase57_6_reality_gap_fix.md` (≤ 80 lines per memory budget;若超過 200 chars per line → 拆 line)
  - Frontmatter (name / description / type / created)
  - Body sections: sprint scope / 7 USs closed / chosen vendor / pytest delta / Vitest delta / Playwright delta / calibration ratio / D-findings count / next phase candidate
- [ ] **Update MEMORY.md index** add 1 line entry
  - Format: `- [project_phase57_7_iam_frontend_foundation.md](project_phase57_7_iam_frontend_foundation.md) — Sprint 57.7 ✅ COMPLETE (YYYY-MM-DD): IAM Foundation + Frontend Foundation 1/N spike;...`
  - Keep entry < 200 chars

### 4.4 Doc closeout updates
- [ ] **MODIFY `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md` §9 milestones**
  - Add Sprint 57.7 entry above 57.6 with 7 USs closure summary
  - Dual scoring: code-level ★★★★ ~88% (post-IAM + foundation install) / runtime-level ★★★ ~70% (real OIDC working;some Sprint 58+ gaps remain SAML/MFA/Refresh)
  - §11 Last Updated header sync (Previous chain to 57.6)
- [ ] **MODIFY `CLAUDE.md`**
  - Latest Sprint (57.6 → 57.7 with 7 USs + AD-Reality-3a closure + AD-Sprint-Plan-9 NEW)
  - main HEAD (`d485b42d` → Sprint 57.7 merged commit hash)
  - Last Updated (with Previous chain to 57.6)
  - Current Phase (added Sprint 57.7 IAM + Frontend Foundation 1/N)
- [ ] **MODIFY `.claude/rules/sprint-workflow.md` §Workload Calibration matrix**
  - Add 1 NEW row:`iam-frontend-spike` 0.60 multiplier (HYBRID weighted blend;1-data-point baseline this Sprint 57.7;pending 2-3 sprint validation per AD-Sprint-Plan-9)
  - Update file header MHist (≤ 100 chars per E501 budget)

### 4.5 Open PR + CI green + solo-dev merge
- [ ] **Push branch + open PR**
  - Push:`git push origin feature/sprint-57-7-iam-frontend-foundation`
  - PR title:`Sprint 57.7 — IAM Foundation + Frontend Foundation 1/N spike (Tier 0 Block A + B + AD-Reality-3a)`
  - PR body:Sprint goal + 7 USs + AD-Reality-3a closure + AD-Sprint-Plan-9 NEW + acceptance + Phase 57.8+ TBD per user decision
  - Verify:5 active CI checks green;solo-dev policy review_count=0 satisfied
- [ ] **Squash merge to main**
  - DoD:GitHub UI squash + merge;branch deleted post-merge
  - Verify:main HEAD updated

### 4.6 User decision interaction (Phase 57.8+ direction)
- [ ] **Present Sprint 57.7 closure summary + Phase 57.8+ direction question**
  - Direction options (per gap-analysis §6 adjusted roadmap):
    - (a) Phase 57.8 SOC 2 Readiness + SBOM Supply Chain spike (~12-15 hr;Block C + D;EU CRA 2026 Sep deadline)
    - (b) Phase 57.8 Status Page + APAC Compliance spike (~10-12 hr;Block E + F;target market mandatory)
    - (c) Phase 58.0+ Tier 1 IaC + DR drill (~15-20 hr;production launch readiness)
    - (d) Pivot to existing Phase 57.x feature ship (chat-v2 / governance / verification real ship now that auth working)
    - (e) Pivot to Frontend Pages 11 (User Profile / MFA Settings / Billing / etc — Phase 58.2+)
  - Per rolling planning 紀律:不預寫 Phase 57.8 plan;等 user 明確選定 scope 才起草

---

## 重要備註

- **此 sprint 寫 substantial source code** — Day 1 + Day 2 + Day 3 全寫 production code (US-A2 OIDC backend + frontend / US-A3 RBAC manager + rewire / US-B1 frontend deps install + config / US-B2 AppShell + providers / US-B3 cost-dashboard refactor / US-R1 chat router observer + 2 repos);Day 4 純 doc + design note extract
- **Phase 57+ Frontend SaaS counter advances 3/N → 4/N** — cost-dashboard now AppShell-compliant counts as ship advance;3 remaining ship pages (sla / tenant-settings / admin-tenants) defer to Phase 58.2+ Frontend Pages 11 batch migrate
- **若 Day 1 vendor account approval lag > 1 day → fallback Self-built Lite path** (Risk Class A) — own OIDC PKCE + python-jose + Entra direct OIDC discovery;US-A1 matrix已 captured both routes
- **誠實 over completeness** — Day 4 design note 8-Point Quality Gate verified ratio ≥ 95% 是 quality gate;若某 invariant 沒驗證到位就明確標 deferred到 §4 (NOT 偽裝 verified)
- **不殺 node 流程** — 啟動 backend uvicorn / frontend vite 後保留 running (per CLAUDE.md global rule;node 流程同時跑 claude code)
- **此 sprint 是 Phase 57.7 first calibration HYBRID class** — `iam-frontend-spike` 0.60 blend 1-data-point baseline opens AD-Sprint-Plan-9;Day 4 retro Q2 careful measure
- **Doc-level rolling discipline 嚴守** — Day 4 ONLY extract `20-iam-deep-dive.md` (per user 2026-05-08 Q4 decision);Frontend doc 留 Phase 58.2+ extract;NOT pre-write 18/19/21/22/23/24/25
- **AD-Reality 3a closure** — sessions + tool_calls observer wire (3b/3c/3d guardrail+verification audit observer 仍 deferred Phase 58+)
