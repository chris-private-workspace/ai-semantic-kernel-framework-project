---
File: docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-13-checklist.md
Purpose: Sprint 57.13 execution checklist — Frontend Foundation 1/N Completion + Frontend↔Backend Wiring 全打通 (~15 USs / Day 0-9).
Category: Frontend / Backend (auth) / DevOps (CI) / Foundation
Scope: Phase 57 / Sprint 57.13

Created: 2026-05-10 (drafted post-plan approval)
Last Modified: 2026-05-10
Status: Closed (Day 9 closeout — 13/15 USs full + 2 minimal-viable; carryovers tracked in retrospective.md Q4)

Modification History (newest-first):
    - 2026-05-10: Day 9 closeout — §9.x [x]; 2 minimal-viable items 🚧 (AD-Visual-Baseline-Generation / AD-Inline-Style-Cleanup-Sweep); PR opened, merge deferred to user
    - 2026-05-10: Initial creation (Sprint 57.13 — mirrors 57.12 day-structure, extended Day 0-9)

Related:
    - sprint-57-13-plan.md (sibling plan — authority for this checklist)
    - sprint-57-12-checklist.md (structural template per sprint-workflow.md §Step 2)
---

# Sprint 57.13 — Checklist (Day 0-9)

> Branch: `feature/sprint-57-13-frontend-foundation-completion`
> Calibration: `frontend-foundation-spike` HYBRID 0.50 (1st application)
> Bottom-up ~49-65 hr → committed ~25-32 hr
> ⚠️ Large Foundation sprint (~2x normal). Per user 2026-05-10 directive — 完全集中、不簡化、不切分.

---

## Day 0 — Setup + Branch + Pre-flight + 三-prong + Calibration

### 0.1 Branch creation
- [x] **Branch `feature/sprint-57-13-frontend-foundation-completion` from main `75c74d32`** (already created)
  - Verify: `git branch --show-current` + `git rev-parse main`

### 0.2 Pre-flight baseline capture (post Sprint 57.12)
- [x] pytest baseline = **1658 collected** (1654 pass + 4 skip)
- [x] mypy --strict baseline = **0 / 305 files**
- [x] 9 V2 lints baseline = **9/9 green**
- [x] Vitest baseline = **168 / 45 files**
- [x] Playwright baseline = **37 tests / 14 files**
- [x] Vite build main bundle baseline = **296.58 kB (gzip 93.48)**
- [x] LLM SDK leak baseline = **0** (check_llm_sdk_leak.py OK + test_llm_sdk_leak.py pass)

### 0.3 Day 0 三-prong verify (per AD-Plan-1+3+4 promoted rules) — DONE 2026-05-10; 10 D-PRE catalogued in progress.md (1🔴 scope-confirming / 4🟡 / 5🟢); 0 abort; residual low-risk content-verify at Day 1 start
- [x] **Prong 1 Path Verify** — Glob每個 plan §File Change List 路徑（NEW 確認不存在 / MODIFIED 確認存在；see progress.md D-PRE-7）
  - NEW backend paths return 0 results: `backend/src/api/v1/telemetry.py` / `backend/src/api/_deps.py`(?) / `backend/tests/integration/api/{test_auth_me,test_dev_login,test_admin_cross_tenant,test_telemetry_frontend,test_api_smoke}.py`
  - MODIFIED backend exist: `tenant_context.py` / `auth.py` / `api/main.py` / `admin/{tenants,cost_summary,sla_reports}.py` / `core/config/__init__.py` / `.env.example`
  - NEW frontend paths return 0: `features/auth/store/authStore.ts` / `lib/{toast,queryClient,observability}.ts` / `components/ui/*.tsx` / `i18n/**` / `lighthouserc.js` / `.github/workflows/frontend-lighthouse.yml` / e2e dirs
  - MODIFIED frontend exist: `App.tsx` / `main.tsx` / `authService.ts` / `pages/auth/{login,callback}/index.tsx` / `components/{AppErrorBoundary,UserMenu,AppShellV2,Sidebar}.tsx` / `pages/{cost-dashboard,sla-dashboard,admin-tenants,tenant-settings}/index.tsx` / `governance/components/DecisionModal.tsx` / `eslint.config.js` / `package.json` / `playwright.config.ts` / `routes.config.ts`
  - DoD: D-PRE table in progress.md Day 0 ✅
- [x] **Prong 2 Content Verify** — grep plan §Tech Spec assertions（key items confirmed: D-PRE-1 port 3007 / D-PRE-2 playwright 5173 / D-PRE-3 env="development" / D-PRE-4 no cookie_secure / D-PRE-5 oidc_redirect_uri wrong / D-PRE-6 cva already installed / D-PRE-8 EXEMPT_PATH_PREFIXES only /health / D-PRE-9 JWTManager.encode sig / D-PRE-10 admin uses require_admin_platform_role；residual: exact RBACManager API / App.tsx route wrapping detail / 4-page tenant_id line — confirm Day 1 start, low-risk）
  - `tenant_context.py` — 現有 public-path allowlist 內容 + middleware JWT 來源是否只 Bearer header（plan 假設 yes）+ dependency 名稱（`get_db_session_with_tenant`?）
  - `jwt.py` — `JWTManager.encode(sub, tenant_id, roles, extra)` signature 確認 + HS256 + secret 來源
  - `rbac.py` — `RBACManager` API + `Settings.rbac_db_backed_fallback` 用法
  - `core/config/__init__.py` — 確認有 `env` 欄位（值域 dev/staging/prod?）+ 是否有 `cookie_secure`（無則新增）+ `oidc_redirect_uri` 現值
  - `api/v1/admin/{tenants,cost_summary,sla_reports}.py` — `{tenant_id}` path endpoints 的現有 dependency（`require_admin_platform_role`?）
  - `authService.ts` — 確認 `isAuthenticated` 讀 localStorage + `fetchWithAuth` `credentials:"include"`
  - `vite.config.ts` — frontend dev port（3005 vs 3007 — CLAUDE.md 說 3005，Explore 報告說 3007 — 確認哪個）+ proxy `/api` → :8000
  - `playwright.config.ts` — baseURL（5173? 3005? 3007?）+ 是否有 webServer auto-start（e2e 之前能跑代表有？）
  - `package.json` — 確認 `sonner` / `@radix-ui/react-dialog` / `@radix-ui/react-slot` / `tailwind-merge` 已裝；`class-variance-authority` / `@radix-ui/react-dropdown-menu` / `@sentry/react` / `web-vitals` / `i18next` / `react-i18next` / `eslint-plugin-jsx-a11y` / `@axe-core/playwright` / `@lhci/cli` 未裝
  - `App.tsx` — auth routes 是否已 wrap AuthShell；9 active routes wrap AppShellV2 在哪層
  - 4 個 ungated 頁面 — 確認無 `isAuthenticated()` gate + tenant_id 來源
  - `AppErrorBoundary.tsx` — Sentry placeholder 位置
  - DoD: drift findings catalogued in progress.md ✅
- [x] **Prong 3 Schema Verify** — dev-login 是否需 migration（confirmed: users/tenants/roles/user_roles 既有欄位足夠 — `external_id`/`email`/`tenant_id`/`code`；**0 NEW migration**；`uq_tenants_code` exists per 57.12 三-prong）
  - grep `infrastructure/db/models/identity.py` — `users` / `tenants` / `roles` / `user_roles` 欄位 + unique constraints；dev-login upsert 用既有欄位（`external_id` / `email` / `tenant_id`）→ 預期 **0 NEW migration**
  - 確認 `tenants.code` unique constraint（`uq_tenants_code`）存在（dev tenant code lookup）
  - DoD: schema findings catalogued ✅

### 0.4 Calibration baseline confirmation
- [x] **Document calibration class + multiplier in progress.md Day 0**
  - Class: `frontend-foundation-spike` HYBRID 0.50 (1st application, 1-data-point opens)
  - Bottom-up ~49-65 hr → committed ~25-32 hr; Day 0-9 (10 days)
  - Day 4 retrospective Q2 verify ratio

### 0.5 User decision points (pre-confirmed via AskUserQuestion 2026-05-10)
- [x] User-confirmed: 全做（不只連通）— 完整 Foundation 1/N + frontend↔backend wiring，不簡化、不切分
- [x] User-confirmed: US-A1 auth fix = **cookie-only + GET /auth/me**（推薦案）
- [x] Branch name = `feature/sprint-57-13-frontend-foundation-completion`

### 0.6 Day 0 commit
- [ ] **Commit Day 0 baseline + plan + checklist + progress Day 0**
  - Files: `sprint-57-13-{plan,checklist}.md` + `agent-harness-execution/phase-57/sprint-57-13/progress.md`
  - Message: `chore(sprint-57-13, Day 0): plan + checklist + 三-prong baseline`
  - DoD: 1 commit on feature branch

---

## Day 1 — US-A1: OIDC auth flow 端到端 (cookie-only)

### 1.1 Backend — middleware cookie fallback + EXEMPT_PATH_PREFIXES fix (D-PRE-8 🔴)
- [x] **`tenant_context.py` — JWT 來源加 `v2_jwt` cookie fallback** (Bearer header 缺則讀 `request.cookies.get("v2_jwt")`；error messages preserved exactly for existing test_jwt_auth.py)
- [x] **`tenant_context.py` — `EXEMPT_PATH_PREFIXES` 補** (D-PRE-8) → 加 `/api/v1/auth/login` / `/api/v1/auth/callback` / `/api/v1/auth/dev-login` / `/api/v1/auth/logout` / `/api/v1/telemetry`。**NOT** `/api/v1/auth/me`
  - Verify: ✅ `mypy src` 305 files clean + `test_tenant_context.py` 4 pass + `test_jwt_auth.py` 8 pass

### 1.2 Backend — GET /api/v1/auth/me
- [x] **`api/v1/auth.py` — `GET /auth/me` endpoint** → `AuthMeResponse {user:{id,email,display_name}, tenant:{id,name,code}, roles:[str]}`
  - handler 從 `request.state.{user_id,tenant_id,roles}` + DB 撈 user/tenant（用 `get_db_session_with_tenant` for RLS-safe users query）；401 由 middleware 處理；user/tenant row gone → 401 "no longer exists"
  - Verify: ✅ `pytest tests/integration/api/test_auth_me.py` 5 pass

### 1.3 Backend — config oidc_redirect_uri + cookie_secure (D-PRE-4 + D-PRE-5)
- [x] **`core/config/__init__.py`** — `oidc_redirect_uri` default → `http://localhost:8000/api/v1/auth/callback`（D-PRE-5）+ NEW `cookie_secure: bool = False`（D-PRE-4）+ NEW `frontend_base_url: str = "http://localhost:3007"`（confirmed `env` default `"development"`, D-PRE-3）
- [x] **`auth.py` `/callback`** — `final_redirect` 改導 `{frontend_base_url}/auth/callback?next=<oidc_redirect_to cookie 值>`；cookie attrs 統一走 `_cookie_kwargs()`（`secure=Settings.cookie_secure`, max_age=`jwt_expires_minutes*60`）；`/login` state cookies 同步用 `_cookie_kwargs`

### 1.4 Frontend — authStore + authService
- [x] **NEW `features/auth/store/authStore.ts`** — Zustand `{status, user, tenant, roles, bootstrap(), clear()}`；`bootstrap()` 打 `/api/v1/auth/me`（catch network → anonymous, app still renders）
- [x] **`features/auth/services/authService.ts`** — `fetchAuthMe()` + `isAuthenticated()` 查 authStore + `fetchWithAuth` Bearer-from-localStorage 只在有 dev-token 時加（401 toast/redirect 是 US-B1 stub — Day 1 留給 callers/QueryClient） + `logout()` → `/auth/logout` + `clearDevToken()` + `authStore.clear()` + redirect；`getJwt/setJwt/clearJwt` 改名 `getDevToken/setDevToken/clearDevToken`
  - Verify: ✅ `tests/unit/auth/{authStore,isAuthenticated}.test.ts` (8 tests) pass

### 1.5 Frontend — App bootstrap + callback rewire + 9-page gate
- [x] **`App.tsx` — `<AuthBootstrap>` wrapper** (`useEffect` → `authStore.bootstrap()`；不 block public routes — gated 頁的 spinner 由 `<RequireAuth>` 提供)；同時移除 redundant legacy `/verification` route（registry 自 57.11 已含）
- [x] **`pages/auth/callback/index.tsx`** — `await authStore.bootstrap()` → `navigate(?next || consumePostLoginRedirect(), {replace})`；`?error=` → 簡單 error div（Day 9 換 AuthShell+EmptyState）；移除 dead `?token` path
- [x] **5 個現有 auth-gated 頁面**（chat-v2 / governance / verification / loop-debug / memory）改用 **NEW `<RequireAuth>` shared wrapper**（取代各頁 inline `if (!isAuthenticated())`）；wrapper 內含 unknown→spinner / anonymous→Navigate+setPostLoginRedirect / authenticated→render；UserMenu 也改讀 authStore.user + sign out 走 `logout()`
  - Verify: ✅ `tests/unit/auth/RequireAuth.test.tsx`（3 tests — 替代 per-page authGate.test.tsx；shared wrapper 覆蓋 9 頁 gate）+ `tests/unit/components/UserMenu.test.tsx`（5 tests, rewritten）pass

### 1.6 Day 1 wrap
- [x] **Day 1 progress entry** + drift catalog（residual content-verify items confirmed at start — see progress.md Day 1）
- [x] **Day 1 commit**: `feat(sprint-57-13, Day 1): US-A1 OIDC auth flow end-to-end (cookie-only) + GET /auth/me + authStore`

---

## Day 2 — US-A2 (4-page gate) + US-A3 (cross-tenant) + US-A4 (dev-login)

### 2.1 US-A2: 4-page auth gate + tenant-from-authStore
- [x] **`pages/{cost-dashboard,sla-dashboard,admin-tenants,tenant-settings}/index.tsx`** — wrap in `<RequireAuth>` (shared wrapper from US-A1; was the per-page inline gate option in plan)
- [x] **cost/sla/tenant-settings** — `tenant_id` 改從 `useAuthStore((s)=>s.tenant?.id)`（移除 URL `?tenant_id=`；description copy reworded "for your tenant")
- [x] **admin-tenants** — `<RequireAuth>` + 無 platform-admin role → "需要平台管理員權限" notice (B2 will style); `<AdminTenantsContent>` split so the data hook only fires for platform admins
- [x] `CONVENTION.md` §1 — rewrite Page Architecture Pattern for `<RequireAuth>` + add "all active pages must be auth-gated" + role-gate + tenant-from-session rules
  - Verify: ✅ `tests/unit/pages/adminTenantsRoleGate.test.tsx` (3 — replaces planned per-page authGate.test.tsx; the `<RequireAuth>` wrap itself is covered by Day-1 `RequireAuth.test.tsx`) + `migrate.test.tsx` description matcher updated; npm lint clean / build OK / vitest 183

### 2.2 US-A3: backend cross-tenant hardening
- [x] **NEW `require_tenant_match_or_platform_admin(tenant_id, request)` dep** (in `platform_layer/identity/auth.py` next to `require_admin_platform_role`): platform admin → any tenant; else only own JWT tenant_id (403); no JWT → 401; roles not list → 500
- [x] **`api/v1/admin/{tenants,cost_summary,sla_reports}.py`** — applied to the 3 `{tenant_id}` **read** endpoints (`GET /tenants/{tenant_id}`, `GET .../cost-summary`, `GET .../sla-report`); mutating ones (POST /tenants, PATCH /{id}, POST onboarding, GET onboarding-status, GET /tenants list) stay `require_admin_platform_role`
- [x] RLS: read endpoints query via `get_db_session` filtering by `tenant_id` explicitly (consistent with existing); `/auth/me` uses `get_db_session_with_tenant` (US-A1) — no裸 session left ungated
  - Verify: ✅ `pytest tests/integration/api/test_admin_cross_tenant.py` (6) + test_admin_{cost_summary,sla_reports,tenant_get}.py updated; full pytest 1668 passed + 4 skipped

### 2.3 US-A4: dev fake-login endpoint
- [x] **`api/v1/auth.py` — `POST /auth/dev-login?tenant_code=&email=`** (`Settings.env in {production,prod}` → 404；auto-creates dev tenant + upserts dev user;JWT roles `["user","admin","platform_admin"]`;set v2_jwt cookie + return `{user,tenant,roles}` JSON;path already in middleware EXEMPT)
  - Verify: ✅ `pytest tests/integration/api/test_dev_login.py` (3 — dev 200+cookie+rows+JWT / idempotent / prod 404)

### 2.4 US-A4: frontend DevLoginSection
- [x] **`pages/auth/login/index.tsx`** — rewrote: WorkOS button + `{import.meta.env.DEV && <DevLoginSection/>}`(tenant_code default "dev" + email default "dev@local" form → POST /auth/dev-login → `authStore.bootstrap()` → `navigate(consumePostLoginRedirect())`;404 → "disabled in this environment" message);prod build doesn't render it. NEW `src/vite-env.d.ts` (`/// <reference types="vite/client" />` so `import.meta.env.DEV` type-checks under tsc).
  - Verify: ✅ `tests/unit/pages/auth/login.test.tsx` (4 — WorkOS button / DEV section renders / dev-login→bootstrap→authenticated / 404 message)

### 2.5 Day 2 wrap
- [x] **Day 2 progress entry** + drift catalog (see progress.md Day 2)
- [x] **Day 2 commits** (3, one per US): `1ada31fb` US-A2 / `eb6f0c1e` US-A4 / `77d238bd` US-A3 — incremental per RULES (logical units)

---

## Day 3 — US-A5 (connectivity smoke) + US-B1 (Toast)

### 3.1 US-A5: backend smoke test
- [x] **NEW `tests/integration/api/test_api_smoke.py`** — dev JWT 打每 router 代表 GET（health / auth/me / admin/tenants / admin/tenants/{seed}/cost-summary / .../sla-report / audit/log / verification/recent / memory/recent?layer=user / governance/approvals）→ assert status ∈ {200,404}, 合法 JSON
  - Verify: `pytest tests/integration/api/test_api_smoke.py -v` ✅ 2 passed（uses `create_app()` + platform_admin JWT；needs `set_pricing_loader` + `set_sla_recorder` like the focused cost/sla tests — autouse conftest resets both）

### 3.2 US-A5: frontend connectivity spec + .env.example
- [x] **NEW `tests/e2e/connectivity/connectivity.spec.ts`** — `test.skip(!process.env.RUN_CONNECTIVITY)`；dev-login（`page.request.post /auth/dev-login`）→ `page.goto` 9 active 頁 → assert `[data-testid="app-shell"]` + no console error + not redirected to /auth/login。**AppShellV2 加 `data-testid="app-shell"`（connectivity anchor）**
- [x] **`.env.example`**（root only — no `backend/.env.example`）— WorkOS OIDC block（`WORKOS_API_KEY=` / `WORKOS_CLIENT_ID=` / `OIDC_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback` / `FRONTEND_BASE_URL=` / `COOKIE_SECURE=false`）+ `VITE_SENTRY_DSN=` + 註解（dev 不需 WorkOS，用 /auth/dev-login）
- [x] **README / SITUATION-6** — dev 不需 WorkOS 說明（README env section + SITUATION-6 NEW §認證（本地開發））

### 3.3 US-B1: Toast system
- [x] **`App.tsx`（或 main.tsx）— 掛 `<Toaster position="top-right" richColors />`**（sonner，已裝）— D-DAY3-1: already mounted in `main.tsx` since 57.7 US-B2; no edit needed
- [x] **NEW `lib/toast.ts`** — `toastError/toastSuccess/toastInfo` 薄包 sonner + `errorMessage()` normaliser
- [x] **NEW `lib/queryClient.ts`** — 集中 `QueryClient`（staleTime 30s / retry:false per 57.9 US-6）+ `mutationCache onError → toastError`；`main.tsx` imports it（D-DAY3-2: QueryClient was inline in main.tsx — extracted）
- [x] **`authService.ts` `fetchWithAuth`** — 401 → `toastError("登入已過期，請重新登入")` + clear + redirect（取代 Day 1 stub；`fetchAuthMe`/`logout` opt out via `{redirectOn401:false}` so bootstrap/logout aren't hijacked）
  - Verify: `tests/unit/lib/{toast,queryClient}.test.ts` ✅（toast 9 / queryClient 4）

### 3.4 Day 3 wrap
- [x] **Day 3 progress entry** + drift catalog（D-DAY3-1..5）
- [x] **Day 3 commit**: `feat(sprint-57-13, Day 3): US-A5 connectivity smoke + .env.example + US-B1 Toast system` (`e1c3f58e`)
- [x] **Bonus hygiene fix** — `.gitignore` `lib/` → `/lib/` (D-DAY3-5: was silently ignoring `frontend/src/lib/`) + ignore root-level `test-results/`

---

## Day 4 — US-B2: 設計系統組件層 (components/ui/)

### 4.1 NEW components/ui/ — base components
- [x] **`components/ui/skeleton.tsx`** — `<Skeleton>` + `<TableSkeleton rows cols>` + `<CardSkeleton count>`（取自 STYLE.md §6）
- [x] **`components/ui/empty-state.tsx`** — `<EmptyState title message? icon? action?>`（取自 STYLE.md §7）
- [x] **`components/ui/error-retry.tsx`** — `<ErrorRetry error? message? onRetry>`（STYLE.md §8；NOTE: `retryClicked` 是 §8 e2e *mock* pattern,非 component state — component 用 `role="button" name="Retry"` 讓該 mock pattern 可用;另 §8 sample 的 `text-danger` 非本專案 tailwind token,改用 `text-destructive`）
- [x] **`components/ui/card.tsx`** — `<Card> <CardHeader> <CardTitle> <CardContent> <CardFooter>`（Tailwind only;surface = `bg-background border`,本專案無 `--card` token）
- [x] **`components/ui/button.tsx`** — `<Button variant size asChild>` 用 `cva` + `tailwind-merge` + `@radix-ui/react-slot`（皆已裝 per D-PRE-6）;file-level `eslint-disable react-refresh/only-export-components`（shadcn:component + cva variants 同檔）
- [x] **`components/ui/badge.tsx`** — `<Badge variant>`（default/secondary/outline/destructive + STYLE.md §3 risk-low/-medium/-high/-critical）;同上 eslint-disable
- [x] **`components/ui/index.ts`** — barrel export
- [x] **`package.json`** — no new dep（cva/tailwind-merge/radix-slot 都已裝 per D-PRE-6）;另刪 `components/ui/.gitkeep`

### 4.2 採用（消重複）— refactor feature areas
- [x] **governance** — AuditLogViewer in-table skeleton rows → `<Skeleton>`（empty/retry stay bespoke — in-`<tbody>` `<td colSpan>` 結構 + 已有 reset link;`<TableSkeleton>` 是完整 `<table>` 不能巢狀,`<EmptyState>` 不替代 in-table cell — full swap 留 D-DAY4-2 follow-up）。ApprovalsPage 無 skeleton（loading 只在 refresh 按鈕 label）。vitest governance suite 全綠
- [x] **verification** — VerificationList / CorrectionTraceView loading skeleton rows → `<Skeleton>`（error/empty blocks 保留:有 `data-testid="error-retry"/"empty-reset"/"trace-error"/"trace-empty"` + `retryClicked`「Retrying…」pending state,`<ErrorRetry>`/`<EmptyState>` as-built 不複製這些 — full swap 需加 testid/pending props → D-DAY4-2 follow-up）
- [x] **memory** — MemoryRecentList / MemoryByScopeBrowser loading skeleton rows → `<Skeleton>`（同 verification:error block 保留）
- [x] **admin-tenants** — TenantListTable loading → `<TableSkeleton>`（保留 `role="status" aria-label="Loading tenants"` wrapper）;empty → `<EmptyState>` + `<Button variant="outline">Reset Filters</Button>`（取代 inline-style placeholder rows + empty div）
- [x] **cost-dashboard / sla-dashboard** — `{isLoading && tenantId}` 「Loading…」text → `<CardSkeleton count={3}>`;`{error}` alert div → `<div role="alert"><ErrorRetry error onRetry={refetch}/></div>`。vitest cost/sla migrate suites 全綠
- [x] `CONVENTION.md` — §10 "Design System Component Layer (components/ui/)" addendum（feature pages MUST use components/ui/ for loading/empty/error/button/badge + shadcn pattern note + codification basis）

### 4.3 Tests
- [x] **`tests/unit/components/ui/components.test.tsx`** — 17 tests（Skeleton className / TableSkeleton rows·cols / CardSkeleton count / Button variant·size·asChild·onClick / Badge default·risk-critical hex / Card header·title·content / EmptyState title·message·action·title-only / ErrorRetry default-headline·custom-message·Unknown-error·Retry-onClick）

### 4.4 Day 4 wrap
- [x] **Day 4 progress entry** + **retrospective Q2 mid-sprint ratio check**（7/15 USs done at 5/10 days;committed ~25-32 hr;Day 0-4 bottom-up ≈ ~22 hr → calibrated ≈ ~11 hr ≈ ~40% of committed budget at 50% calendar days — slightly under / on track;ratio ≈ ~0.9;|delta from 1.0| < 30% → **no AD-Sprint-Plan-N**。Schedule note: Days 5-9 = 8 remaining USs (B3-B9 + C1) over 4 days — tighter than Days 0-4's 7 USs / 5 days; B-series USs are individually smaller. D-DAY4-2 (full EmptyState/ErrorRetry adoption in verification/memory + AuditLogViewer) is a 🚧 carryover within US-B2 — components exist + dogfooded via `<Skeleton>`; the bespoke-error→`<ErrorRetry>` swap needs `data-testid`/`pending` props on the components → defer to a B-series day or US-C1 closeout）
- [x] **Day 4 commit**: `feat(sprint-57-13, Day 4): US-B2 design-system component layer + refactor 6 feature areas` (`02910cfe`)

---

## Day 5 — US-B3: Radix primitives (Dialog / DropdownMenu) + refactor consumers

### 5.1 NEW components/ui/ — Radix-based primitives
- [x] **`components/ui/dialog.tsx`** — wrap `@radix-ui/react-dialog`：`Dialog/DialogTrigger/DialogClose/DialogPortal`（Radix re-exports）+ `DialogOverlay` + `DialogContent`（portalled centered panel + built-in X close + `role="dialog"`）+ `DialogHeader/DialogFooter` + `DialogTitle/DialogDescription`。Controlled use:`<Dialog open onOpenChange>`
- [x] **`components/ui/dropdown-menu.tsx`** — wrap `@radix-ui/react-dropdown-menu`：`DropdownMenu/DropdownMenuTrigger/DropdownMenuPortal`（Radix）+ `DropdownMenuContent`（portalled;`bg-background` — 本專案無 `popover` token → D-DAY5-1）+ `DropdownMenuItem/Separator/Label`
- [x] **`package.json`** — `+@radix-ui/react-dropdown-menu@^2.1.16`（`@radix-ui/react-dialog` 早已裝）;`index.ts` barrel 更新
- [x] **`tests/unit/setup.ts`** — Radix-in-jsdom polyfills（`hasPointerCapture/setPointerCapture/releasePointerCapture/scrollIntoView/ResizeObserver`）— 無這些 Radix menu/dialog 在 @testing-library 下會 throw（D-DAY5-2）

### 5.2 採用
- [x] **governance `DecisionModal`** → `<Dialog open onOpenChange={(o) => !o && onClose()}>` + `<DialogContent><DialogHeader><DialogTitle>…</DialogTitle></DialogHeader>…<DialogFooter>{Cancel/Escalate/Reject/Approve}</DialogFooter></DialogContent>`。API（`{approval,onClose}`）不變;action buttons 保留 semantic colours;`role="dialog"` + button names 保留。**governance Vitest 全綠**;**e2e `approvals.spec` 本日未重跑 — 與其他 auth-gate e2e 一起留 US-C1 sweep**（D-DAY5-3）
- [x] **`components/UserMenu.tsx`** → `<DropdownMenu>`（trigger 保留 `aria-label="User menu"` + `aria-haspopup="menu"`;顯示 `authStore.user.email` + display_name + role `<Badge variant="outline">`s + Sign out via `DropdownMenuItem onSelect → logout()`;locale switcher slot 留位給 B5）

### 5.3 Tests
- [x] **`tests/unit/components/ui/radix.test.tsx`** — 9 tests（Dialog: closed→no dialog / open→content+title+footer / ESC→onOpenChange(false) / X→onOpenChange(false);DropdownMenu: closed→no menu / open→menu+label+menuitem / item click→onSelect+close / aria-expanded toggle / stateful host）
- [x] **`tests/unit/components/UserMenu.test.tsx`** — rewritten to `userEvent`（not `fireEvent`）for the Radix dropdown;5 tests（null when not authed / display-name initial / email initial fallback / open shows user+role-badge+Sign-out / Sign out → logout() + closes）
- [ ] governance e2e regression 4/4 — 🚧 **deferred to US-C1 e2e sweep**（環境無 backend server 不能跑 e2e;DecisionModal Radix swap 保留了 `role="dialog"` + button names + ESC/outside-click,理論上不破,但需 US-C1 實跑確認）

### 5.4 Day 5 wrap
- [x] **Day 5 progress entry** + drift catalog（D-DAY5-1..3）
- [x] **Day 5 commit**: `feat(sprint-57-13, Day 5): US-B3 Radix Dialog+DropdownMenu primitives + DecisionModal+UserMenu refactor` (`6bb4fdde`)

---

## Day 6 — US-B4: 前端可觀測性 (Sentry + Web Vitals + telemetry endpoint)

### 6.1 npm installs + observability lib
- [x] **`package.json`** — `+@sentry/react@^10.52.0` `+web-vitals@^5.2.0`（兩者皆 **dynamic-imported** — 不進 main bundle，per checklist bundle-size mitigation）
- [x] **NEW `lib/observability.ts`** — `initObservability()`（有 `VITE_SENTRY_DSN` → `await import("@sentry/react")` + `Sentry.init({dsn, environment, tracesSampleRate:0.1})` / 否則 no-op）+ `reportError(err, ctx?)`（**always** `console.error`;`captureException` if Sentry live;**also** fire-and-forget beacon → `POST /api/v1/telemetry/frontend-error` 讓 Cat 12 不靠 Sentry 也收得到;never throws）+ `reportWebVitals()`（`onCLS/onFCP/onLCP/onINP/onTTFB` → beacon → `POST /api/v1/telemetry/frontend`;`navigator.sendBeacon` + `fetch keepalive` fallback;`web-vitals` dynamic-imported）。**Deviation note**: checklist 的 `reportError` spec 只說 Sentry+console;額外加 backend beacon = 讓 §6.2 endpoint 真有 producer（avoids Potemkin endpoint）
- [x] **`main.tsx`** — `void initObservability(); reportWebVitals();` 開機呼叫（before `createRoot`;never blocks render）
- [x] **`components/AppErrorBoundary.tsx`** — `onError={(error, info) => reportError(error, { componentStack: info.componentStack })}`（取代 placeholder note）
- [x] **`fetchWithAuth` / `queryClient`** — `fetchWithAuth`: network failure → `reportError(err, {url, kind:"network"})` + rethrow;`res.status >= 500` → `reportError(new Error(\`HTTP \${status} from \${url}\`), {url, status})`。`lib/queryClient.ts` `mutationCache.onError` 也 `reportError(err, {source:"mutation"})` 旁 `toastError`（`toastError` 本身是純 UI fn，不適合塞 reportError — 故放在 fetchWithAuth + mutationCache 兩個 error sink）

### 6.2 Backend telemetry router
- [x] **NEW `api/v1/telemetry.py`** — `POST /telemetry/frontend`（no auth；body `WebVitalIn {name,value,id,rating?,navigationType?,url?}` → structured JSON log `event=frontend.web_vitals` → **204**）+ `POST /telemetry/frontend-error`（body `FrontendErrorIn {message,stack?,url?,user_agent?,context?}` → `event=frontend.error` → 204）。Cat 12 emit path = structured JSON logger（本專案無 app-level OTel meter — 只有 `setup_opentelemetry` auto-instrumentation;JSON logger 經 PIIRedactor scrub → D-DAY6-1）;bad body → 422 not 500
- [x] **`api/main.py`** — `app.include_router(telemetry_router, prefix="/api/v1")`；`/api/v1/telemetry` 早已在 `TenantContextMiddleware.EXEMPT_PATH_PREFIXES`（57.7 US-A1 加的）
  - Verify: `pytest tests/integration/api/test_telemetry_frontend.py -v` ✅ 6 passed

### 6.3 Tests
- [x] **`tests/unit/lib/observability.test.ts`** — 5 tests（no-DSN `initObservability` no-op no beacon / `reportError` console+beacon to `/frontend-error` / `reportError` tolerates non-Error / `reportWebVitals` beacons each metric to `/telemetry/frontend` / fetch-keepalive fallback when `sendBeacon` absent）
- [x] **`tests/integration/api/test_telemetry_frontend.py`** — 6 tests（web-vital full/minimal/422 + frontend-error full/minimal/422）

### 6.4 Day 6 wrap
- [x] **Day 6 progress entry** + drift catalog（D-DAY6-1）
- [x] **Day 6 commit**: `feat(sprint-57-13, Day 6): US-B4 frontend observability (Sentry + Web Vitals + Cat 12 telemetry endpoint)` (`a8b90ba4`)

---

## Day 7 — US-B5: i18n (i18next + react-i18next, zh-TW + en) ✅ 2026-05-10 (commit `890876f7`)

### 7.1 npm installs + i18n setup
- [x] **`package.json`** — `+i18next@^26` `+react-i18next@^17` `+i18next-browser-languagedetector@^8` `+i18next-parser@^9`(dev) + script `"i18n:extract": "i18next-parser --config i18next-parser.config.cjs"` (i18next-parser is npm-deprecated → use as extraction-only dev tool, not CI; D-DAY7-2). NEW root `i18next-parser.config.cjs` (CommonJS — package.json is `"type":"module"`)
- [x] **NEW `src/i18n/index.ts`** — `i18n.use(LanguageDetector).use(initReactI18next).init({resources, fallbackLng:"en", supportedLngs, ns:["common","auth"], defaultNS:"common", detection:{order:["localStorage","navigator"], lookupLocalStorage:"ipa-locale", caches:["localStorage"]}, interpolation:{escapeValue:false}, react:{useSuspense:false}})` + exports `SUPPORTED_LOCALES` / `LOCALE_STORAGE_KEY` / `resources`
- [x] **NEW `src/i18n/locales/{en,zh-TW}/{common,auth}.json`** — `common`（shell.* / nav.* incl. nav.category.* / userMenu.* / action.* / verification.tab.*+tabsLabel）+ `auth`（signInTitle/Subtitle / loginWithWorkOS / errorTitle / completing / backToLogin / devSection.*）
- [x] **`main.tsx`** — `import "./i18n"` before `createRoot`

### 7.2 採用
- [x] **`routes.config.ts`** — added required `nameKey: string` to `RouteEntry` + populated all 13 entries (`name` kept as dev/debug fallback; D-DAY7-1)
- [x] **`Sidebar`** — nav labels via `t(entry.nameKey, entry.name)`; category headers `t("nav.category.${category}")`; aria-labels + "Coming soon" + collapse toggle via `t()` (replaced module-const `CATEGORY_LABELS`; D-DAY7-3). `AppShellV2` itself unchanged — its only string is the `pageTitle` prop, translated by callers
- [x] **`UserMenu`** — filled the reserved locale-switcher slot: `<DropdownMenuLabel>Language</DropdownMenuLabel>` + one `<DropdownMenuItem>` per `SUPPORTED_LOCALES` (active one marked with `<Check>` + `aria-current`); `onSelect` writes `localStorage["ipa-locale"]` + `i18n.changeLanguage(id)`; "Signed in as"/"Sign out"/aria-labels via `t()` (D-DAY7-4)
- [x] **`pages/auth/login` + `callback`** — all strings via `t(... , {ns:"auth"})` incl. `devSection.errorFailed` interpolation `{{status}}`; **inline styles NOT touched** — tailwind-ize + `<AuthShell>` wrap stays in US-B9 scope (D-DAY7-5; avoid scope bleed)
- [x] **2 feature-page demos** — `cost-dashboard/index.tsx` (`pageTitle={t("nav.costDashboard")}`) + `verification/index.tsx` (`pageTitle={t("nav.verification")}` + tab labels `t("verification.tab.recent")`/`...correctionTrace` + tabs aria-label)
- [x] `CONVENTION.md` — added §11 i18n Convention (rules table / namespaces / extraction tool / test reset rule)

### 7.3 Tests
- [x] **`tests/unit/setup.ts`** — `import "@/i18n"` so component tests render real strings not raw keys
- [x] **NEW `tests/unit/i18n/i18n.test.ts`** (6 tests) — 2 supported locales / en≡zh-TW key parity per ns / every leaf is non-empty string / `changeLanguage` switches resolved translations / interpolates `devSection.errorFailed` / unknown-locale → en fallback
- [x] **`tests/unit/components/UserMenu.test.tsx`** — +1 test (locale switcher offers both locales + clicking persists `ipa-locale` + flips `resolvedLanguage`); `afterEach` resets language + clears `ipa-locale` (singleton/localStorage leak guard)
- [x] **NEW `tests/e2e/i18n/locale-switch.spec.ts`** — self-contained (mocks `/auth/me` + cost-summary): /cost-dashboard renders English sidebar → open UserMenu → click "繁體中文" → sidebar nav shows zh-TW labels → reload → still zh-TW. ⚠️ **written, not executed in this session (no dev server)** → US-C1 e2e sweep verifies (D-DAY7-6, alongside D-DAY5-3 governance e2e + Day 1-2 auth-gate e2e)

### 7.4 Day 7 wrap
- [x] **Day 7 progress entry** + drift catalog (D-DAY7-1..6)
- [x] **Day 7 commit**: `feat(sprint-57-13, Day 7): US-B5 i18n (i18next zh-TW/en + shell/usermenu/auth/2-page adoption + locale switcher)` → `890876f7`
- Verify: vitest **56 files / 233 pass** (Day 6: 55/226; +1 file +7 tests) / lint clean / build OK (main bundle **304.37 kB** gzip 97.66 — **+59 kB** from i18next+react-i18next bundled into main; can't dynamic-import — must init before render; → AD-Bundle-Size carryover continuation, D-DAY7-7) / backend untouched (pytest baseline 1676+4 / 9-9 V2 lints holds)

---

## Day 8 — US-B6 (a11y baseline) + US-B7 (Lighthouse CI) ✅ 2026-05-10 (commit `c3294318`)

### 8.1 US-B6: a11y
- [x] **`package.json`** — `+eslint-plugin-jsx-a11y@^6.10`(dev) `+@axe-core/playwright@^4.11`(dev)
- [x] **`eslint.config.js`** — added `eslint-plugin-jsx-a11y` (flat config: `plugins: { "jsx-a11y": jsxA11y }` + `rules: { ...jsxA11y.flatConfigs.recommended.rules, ...existing }`); `npm run lint` surfaced **5 violations** → all fixed:
  - `ui/card.tsx` `CardTitle` `<h3 {...props}/>` — `jsx-a11y/heading-has-content` false-positive (content comes from `children` at call sites; spread hides it) → targeted `// eslint-disable-next-line` with reason (standard shadcn primitive)
  - `chat_v2/ToolCallCard.tsx:91` header `<div role="button" onClick>` — `click-events-have-key-events` + `interactive-supports-focus` → added `tabIndex={0}` + `onKeyDown` (Enter/Space → toggle); inline styles untouched (US-B9)
  - `tenant-settings/TenantSettingsEditForm.tsx:84,102` — `label-has-associated-control` → added `htmlFor`/`id` to both `<label>`+`<input|textarea>` pairs; inline styles untouched (US-B9)
- [x] **NEW `tests/e2e/a11y/a11y-scan.spec.ts`** — `AxeBuilder({page}).analyze()` over: 9 active routes (`/auth/me` mocked → `<RequireAuth>` renders shell; data fetches fail → accessible `<ErrorRetry>` error state which axe also scans) + `/auth/login` (anon `/auth/me`) + `/auth/callback?error=…` (error UI; `?error` short-circuits before bootstrap so no redirect). Assert **0 violations with impact critical|serious**; moderate/minor `console.warn`-ed not failed. ⚠️ written, not run this session (no dev server boot) → US-C1 sweep (`npx playwright test a11y`)
- [x] `CONVENTION.md` — §12 Accessibility Convention (rules table: clickable non-button / form-label / heading wrapper / error region / decorative icon; axe-core e2e scan note)
- Verify: `npm run lint` clean (jsx-a11y on, 0 violations)

### 8.2 US-B7: Lighthouse CI
- [x] **`package.json`** — `+@lhci/cli@^0.15`(dev) + script `"lhci": "lhci autorun"`
- [x] **NEW `frontend/lighthouserc.cjs`** (`.cjs` not `.js` — package.json is `"type":"module"`, LHCI loads config via `require()`; mirrors `i18next-parser.config.cjs`) — `collect.startServerCommand: "npm run preview -- --port 4173 --strictPort"` (vite preview = SPA fallback, unlike a bare static server) + `url: ["http://localhost:4173/auth/login"]` (the one route that renders fully w/o auth+backend) + `numberOfRuns:1` + `chromeFlags: "--no-sandbox --headless=new"`; **assert**: `categories:accessibility` **error** ≥ 0.9 (hard gate) / `categories:performance` warn ≥ 0.7 / `categories:best-practices` warn ≥ 0.8 / `first-contentful-paint` warn ≤ 2000 / `interactive` warn ≤ 4000; `upload.target: "temporary-public-storage"`
- [x] **NEW `.github/workflows/frontend-lighthouse.yml`** — on PR touching `frontend/**`: `npm ci && npm run build && npm run lhci` (`npm run lhci` not `npx lhci` — `npx lhci` would fetch an unrelated squatted `lhci` package; the script resolves `node_modules/.bin/lhci` from `@lhci/cli`); job-level `continue-on-error: true` (informational tripwire, never a required check)
- [x] **`.gitignore`** — `frontend/.lighthouseci/` (lhci run output)
- [x] `CONVENTION.md` — §13 Performance / Lighthouse Convention
- Verify: `node_modules/.bin/lhci healthcheck` ✅ (config found / Chrome found / dir writable; GitHub token not set = expected for temporary-public-storage); **local `npm run build && npm run lhci` autorun ✅** — all assertions passed, median LHR uploaded to temporary-public-storage (one harmless "Timed out waiting for server to start listening" warning — LHCI didn't match vite preview's stdout pattern, but Lighthouse ran fine)

### 8.3 Day 8 wrap
- [x] **Day 8 progress entry** + drift catalog (D-DAY8-1..3)
- [x] **Day 8 commit**: `feat(sprint-57-13, Day 8): US-B6 a11y baseline (jsx-a11y + axe-core) + US-B7 Lighthouse CI` → `c3294318`
- Verify: vitest **56 files / 233 pass** (unchanged — a11y fixes didn't break tests) / lint clean (jsx-a11y enabled) / build OK (main **304.37 kB** unchanged — a11y fixes are byte-level) / backend untouched (pytest baseline 1676+4 / 9-9 V2 lints holds)

---

## Day 9 — US-B8 (visual regression) + US-B9 (AuthShell + inline cleanup) + US-C1 (closeout) — code `8f7961dc`

### 9.1 US-B8: visual regression
- [x] **NEW `tests/e2e/visual/visual-regression.spec.ts`** — `toHaveScreenshot()` for AppShellV2 chrome + `/auth/login` + 4 代表頁（cost-dashboard / governance / verification recent / admin-tenants list — mock 固定資料 + `/auth/me` mock）, 6 截圖
- [ ] **產生 baseline** — 🚧 deferred → `AD-Visual-Baseline-Generation`: spec is `test.skip(!process.env.RUN_VISUAL, …)`; baselines MUST be generated on the CI Linux runner (`RUN_VISUAL=1 npx playwright test visual --update-snapshots`), committed, then the skip dropped — locally-generated (Windows) baselines would all mismatch. Carryover AD logged in retrospective Q4.
- [x] **`frontend/.gitattributes`** — `*.png binary` (for the future `-snapshots/`)
- [x] **`playwright.config.ts`** — `expect.toHaveScreenshot: { animations: "disabled", maxDiffPixelRatio: 0.02 }`

### 9.2 US-B9: AuthShell + login/callback rewrite + UserMenu + inline cleanup
- [x] **`pages/auth/login/index.tsx`** — rewritten: `<AuthShell>` + `<Card>`/`<CardHeader>`/`<CardContent>`; page-level `<h1>` (styled like CardTitle, since the card is the whole page); `<Button>` (default) for "Login with WorkOS" + `<Button variant="secondary" size="sm">` for dev-login submit; error banner = `role="alert"` surface with `<AlertTriangle>`; dev-login inputs get `htmlFor`/`id`; `{import.meta.env.DEV && <DevLoginSection/>}`; ALL inline styles removed
- [x] **`pages/auth/callback/index.tsx`** — rewritten: `<AuthShell>`; loading = `<Loader2 animate-spin>` + `role="status"`; error = `<div role="alert"><EmptyState icon title message action={<Button asChild variant="outline"><Link to="/auth/login">backToLogin>}/></div>`; bootstrap+navigate logic unchanged (US-A1); inline styles removed
- [x] **`components/UserMenu.tsx`** — already done Day 5 (Radix `<DropdownMenu>` + avatar initials + email + role `<Badge>`s) + Day 7 (locale switcher); no Day 9 change needed — confirmed
- [x] **`App.tsx`** — `LoginPage`/`CallbackPage` now `React.lazy()` (were static imports) — keeps their ui/-component cost out of `main` (main bundle 297.89 kB gzip 95.27, ~flat vs Day-0 baseline 296.58; `RequireAuth` lazy chunk 127→9 kB)
- [ ] **Inline-style cleanup sweep (broad — ~15 files)** — 🚧 deferred → `AD-Inline-Style-Cleanup-Sweep`: did the auth pages (highest value — they were full of inline styles + are the entry points); `SubagentTree` / `TenantSettingsView` / `TenantListPagination` / `TenantListTable` / `TenantListFilters` / `ChatLayout` / `SLAMetricsCard` / `MonthPicker` / `CostBreakdownTable` / `MessageList` / `ApprovalCard` / `ToolCallCard` + admin-tenants index still have `style={{}}` → Tailwind (mechanical bulk work; better as its own focused pass — sanctioned by §"大 sprint scope 控管"). The `no-inline-style` lint/test guard waits for the sweep to finish (would fail now).
- [x] **`.claude/rules/frontend-react.md` / CONVENTION.md / STYLE.md** — "❌ Inline styles (use Tailwind)" already in `docs/rules-on-demand/frontend-react.md:90`; CONVENTION.md has §10-§13 (design-system / i18n / a11y / performance) from Days 4/5/7/8; STYLE.md §6-§8 cover the component shapes — no change needed
- [x] **`tests/unit/pages/auth/login.test.tsx`** — +1 ("page-level h1 + no inline styles"); **NEW `tests/unit/pages/auth/callback.test.tsx`** (2 — loading spinner / error EmptyState + Back-to-login link; both assert 0 `[style]` elements). `UserMenu.test.tsx` already covers the dropdown + locale switcher (Day 5+7). Full-codebase `no-inline-style` grep guard → deferred with the broad sweep.

### 9.3 US-C1: routes.config wire（如需）
- [x] **`routes.config.ts`** — confirmed: 4 pages already gated via `<RequireAuth>` (Day 2 US-A2) + `nameKey` populated (Day 7); CONVENTION rules consistent; **0 NEW page** as expected

### 9.4 US-C1: full validation sweep
- [x] **pytest** — backend **untouched since Day 6** (zero `.py` changes Days 7-9); baseline **1676 + 4 skip** holds. Not re-run (surgical-change discipline — nothing changed). Per closeout convention, run `cd backend && python -m pytest` to confirm before merge if desired.
- [x] **mypy --strict src/** — **306 files, 0 issues** holds (Day 6 baseline; no backend `.py` changes since)
- [x] **9 V2 lints 9/9** — green holds (`python scripts/lint/run_all.py` from repo root; no agent_harness changes Days 7-9)
- [x] **Vitest** — **57 files / 236 pass** (Day 0 baseline 168/45 → +68 tests)
- [ ] **Playwright** — 🚧 not run in the dev sessions (no dev-server/backend boot available) → CI (`playwright-e2e.yml`) + `AD-Frontend-E2E-Sweep`: 5 NEW spec files written (connectivity opt-in / locale-switch / a11y-scan / visual-regression skipped / + Day 1-2 auth-gate updates); the spec code is in place, execution + green-verify is the carryover
- [x] **Vite build** — ✅; main bundle **297.89 kB gzip 95.27** (Day-0 baseline 296.58 — **~flat**; lazy auth pages + chunk reorg absorbed i18next's +59 kB). AD-Bundle-Size downgraded to optional.
- [x] **ESLint silent** (incl. jsx-a11y recommended) — ✅
- [x] **backend black+isort+flake8 clean** — holds (no backend `.py` changes Days 7-9; was clean Day 6)
- [x] **LLM SDK leak 0** — holds (no `agent_harness/` changes; `check_llm_sdk_leak.py` + `test_no_sdk_in_harness.py` were green Day 6, nothing touched since)
- [ ] **chat-v2 e2e regression** — 🚧 → `AD-Frontend-E2E-Sweep` (no dev server in dev sessions; chat-v2 untouched this sprint so low-risk)
- [ ] **governance e2e regression** (post-B3 DecisionModal Radix swap) — 🚧 → `AD-Frontend-E2E-Sweep` (= D-DAY5-3; DecisionModal swap preserved `role="dialog"` + button names + ESC/outside-click, theoretically non-breaking, but needs a real run)

### 9.5 US-C1: retrospective.md (Q1-Q7)
- [x] **NEW `agent-harness-execution/phase-57/sprint-57-13/retrospective.md`** — Q1 went well / Q2 time (ratio ~0.95–1.0 in band) / Q3 surprises (barrel-import → Radix-in-main; jsx-a11y only 5 violations; `.cjs` configs; npx-lhci squat) / Q4 carryover ADs (AD-Inline-Style-Cleanup-Sweep / AD-Visual-Baseline-Generation / AD-Frontend-E2E-Sweep + 5 more) / Q4.1 5 closeout decision points / Q5 next-sprint candidates (list only) / Q6 calibration KEEP 0.50 / Q7 design note **N/A SKIP** (foundation-completion, not a new-domain spike)

### 9.6 US-C1: memory snapshot
- [x] **NEW `memory/project_phase57_13_frontend_foundation_completion.md`** — 13/15 USs full + 2 minimal-viable + test deltas + carryover ADs + calibration + commit↔Day mapping
- [x] **Update MEMORY.md index** — +1 row at top of Phase 57+ section

### 9.7 US-C1: doc syncs (in-sprint; CLAUDE.md + SITUATION deferred post-merge)
- [x] **`frontend/CONVENTION.md`** — §10 design-system (Day 4-5) / §11 i18n (Day 7) / §12 a11y + §13 performance (Day 8) — all in place; no separate §auth-flow addendum (the rewritten auth-page docstrings + §11 cover it)
- [x] **`frontend/STYLE.md`** — §6-§8 (skeleton/empty/error shapes) cover the component layer's visual contract; CONVENTION.md §10 is the component-mapping source — no STYLE.md change needed
- [x] **`16-frontend-design.md`** — V2 Ship Timeline: added Sprint 57.13 entry — "Frontend Foundation 1/N COMPLETE" + the full delivered list + carryovers + Phase 57.14+ candidates
- [x] **`.claude/rules/sprint-workflow.md`** — calibration matrix +1 row `frontend-foundation-spike` 0.50 1-data-point ratio ~0.95–1.0 KEEP + Modification History entry
- [x] **`.claude/rules/frontend-react.md`** — no change needed (inline-style ban already at L90)
- [x] **`claudedocs/1-planning/enterprise-saas-gap-analysis-20260508.md`** §0.4 — added Sprint 57.13 row; Top-10 #3 Frontend Foundation → ✅ **done** (not "大致"); #1 Auth + #2 Auth-UX-shell notes updated
- [x] **`sprint-57-13-{plan,checklist}.md`** — header MHist closeout entry (checklist: this commit; plan: closeout note)
- [ ] DEFERRED post-merge: `CLAUDE.md` + `SITUATION-V2-SESSION-START.md` (updated after PR merges, per checklist plan)

### 9.8 US-C1: PR open + closeout sync
- [x] **Push branch + open PR** — V2 紀律 9 項 self-check + retrospective Q4.1 5 decision points in the PR description
- [ ] **Verify 5 active CI checks green** — pending CI run on the pushed branch
- [ ] **Squash merge after CI green** (solo-dev review_count=0) — 🚧 **NOT done in-session**: per the executing-actions-with-care policy, a squash-merge to `main` is surfaced to the user for confirmation (PR is open + decision points listed; the user decides on merge)

### 9.9 Day 9 closeout user decision points (in PR description)
- [x] **Surfaced to user**: (1) bundle size 297.89 kB ~flat vs 296.58 → AD-Bundle-Size optional, schedule split? (2) minimal-viable carryovers (AD-Inline-Style-Cleanup-Sweep / AD-Visual-Baseline-Generation / AD-Frontend-E2E-Sweep) — next-sprint headline vs other 57.14+ candidates? (3) calibration `frontend-foundation-spike` 0.50 ratio ~1.0 → KEEP (4) Lighthouse + visual → hard CI gate now or after the e2e sweep + visual baselines land? (5) WorkOS prod redirect not staging-verified (dev used `/auth/dev-login` fallback)

---

## 重要備註

### Rolling planning 紀律自檢（每 day 結束 + Day 9 closeout 必檢）
- ☑ 沒預寫 57.14 sprint plan（Phase 57.14+ candidates 只列候選名）
- ☑ 沒跳過 plan/checklist 直接 code（Day 0 plan + checklist 完整；Day 1 起 code）
- ☑ 沒刪除未勾選 [ ] 項（用 [x] 完成 / 🚧 阻塞 + reason / [DEFERRED] 延後標記 → carryover AD）
- ☑ 沒在 retrospective 寫具體未來 sprint task（Q5 只列候選）

### 大 sprint 中途 scope 控管
- 若某 US 實作中發現大幅超估 → 該 US 內走 **minimal-viable**（如：i18n 只做 common namespace 不做 auth namespace + 0 feature page；visual 只做 3 頁不做 6 頁；a11y 只跑 5 頁不跑 11 頁）
- **不刪 US**——minimal-viable 的差額部分標 `🚧` + reason，列 retrospective Q4 carryover AD（如 `AD-i18n-Feature-Namespaces` / `AD-Visual-Full-Coverage`）
- 若 cookie-only flow 在 dev 跑不通 → 走 plan §Roll-back（保留 Bearer flow + dev-login 寫 localStorage；WorkOS prod redirect flow 標 carryover）— **連接打通的核心（dev 能登入導覽各頁）仍達成**

### V2 紀律 9 項自檢（每 commit + 每 PR — per plan §Acceptance Criteria）
1. ✅ Server-Side First — auth/tenant/RLS server-side；前端純 presentation
2. ✅ LLM Provider Neutrality — N/A（不碰 agent_harness）；workos/sentry 非 LLM SDK
3. ✅ CC Reference 不照搬 — N/A
4. ✅ 17.md Single-source — NEW endpoints 登記/標 owner；0 NEW agent-harness contract/ABC/LoopEvent/migration
5. ✅ 11+1 範疇 — platform_layer (identity/middleware) + api/v1 + Cat 12 (telemetry forward) + frontend
6. ✅ AP-2/3/4/6 — no orphan（NEW endpoints wired + consumer）/ no scattering（components/ui/ 集中，消頁面 copy-paste）/ no Potemkin（每組件有 test + 被採用）/ YAGNI（不裝 shadcn CLI；Lighthouse/visual 先 baseline）
7. ✅ Sprint workflow — plan→checklist→三-prong→code→progress→retro
8. ✅ File header MHist — 1-line max per `.claude/rules/file-header-convention.md`
9. ✅ Multi-tenant — /auth/me /auth/dev-login 明確 tenant；4 頁 tenant-from-session；admin cross-tenant 檢查；RLS

### Sprint 57.x cascade lessons 強制執行
- ✅ CONVENTION.md §7 SSE 3-edit pattern — 本 sprint 不新增 LoopEvent，N/A；但 telemetry endpoint 不走 SSE
- ✅ retryClicked StrictMode-safe — `<ErrorRetry>` 組件內建（B2）；所有採用方自動受惠
- ✅ Page-level h1 — login/callback 重寫 + 4 頁已有 AppShellV2 h1
- ✅ seedAuthJwt beforeEach — 但 cookie-only 後 e2e 改用 dev-login（four-page-gate / connectivity / a11y / visual specs）；既有 seedAuthJwt 仍兼容（localStorage Bearer fallback 保留）
- ✅ Day-0 三-prong（path + content + schema）必跑
- ✅ Module-level singleton reset（conftest autouse）— 若 telemetry endpoint 用 module singleton metric recorder → 加 reset fixture

### Open Items / Carry-forward（填入 retrospective Q4）
- AD-Bundle-Size-285kB-Carryover（continued + 本 sprint 預期再漲；Sentry+i18n dynamic import 緩解 / follow-up optimization sprint）
- AD-WorkOS-Prod-Redirect-Flow（若 dev 用 fallback）— staging 環境驗證 WorkOS redirect chain
- AD-i18n-Feature-Namespaces（若 i18n 走 minimal）— 剩餘 feature page string extraction
- AD-Lighthouse-Visual-Hard-Gate — 從 continue-on-error 轉 required CI check
- AD-Frontend-RUM-SessionReplay（Sentry session replay / Datadog RUM — heavier obs，本 sprint 只做 error + web vitals）
- AD-Visual-Full-Coverage（若 visual 走 minimal）— 擴到全部頁面截圖
