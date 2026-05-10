---
File: docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-13-plan.md
Purpose: Sprint 57.13 plan — Frontend Foundation 1/N Completion + Frontend↔Backend Wiring 全打通. Closes the entire "前端基礎建設 (Foundation 1/N)" gap list (auth flow end-to-end, 4-page auth gate, dev fake-login, connectivity smoke, Toast system, design-system component layer, Radix primitives, Sentry + Web Vitals observability, i18n zh-TW/en, a11y baseline, Lighthouse CI, visual regression, AuthShell + inline-style cleanup). Phase 57+ Frontend SaaS — Foundation completion sprint.
Category: Frontend / Backend (auth) / DevOps (CI) / Foundation
Scope: Phase 57 / Sprint 57.13

Description:
    Per user 2026-05-10 directive: "完全集中去處理所有關於 前端基礎建設 (Foundation 1/N)
    現況 的未處理/未準備的內容, 把前端架構完整地準備好, 不是馬虎地處理或簡化地開發"
    + "把前端和後端的連接全部打通, 這是最高首先的任務".

    This is an exceptionally large "Foundation" sprint (~15 USs / Day 0-9 / ~10 days)
    — comparable in scope to Sprint 49.1 (V2 skeleton). It is intentionally not split,
    per the user's "完全集中" instruction. The work is grouped:

    A. Frontend↔Backend Wiring 打通 (US-A1..A5) — the connectivity layer:
       - A1: OIDC auth flow end-to-end via cookie-only (backend middleware accepts
             v2_jwt cookie as fallback to Bearer header; NEW GET /api/v1/auth/me;
             frontend Zustand authStore; isAuthenticated() → authStore; callback page
             bootstraps via /auth/me; fix oidc_redirect_uri default).
       - A2: 4 currently-ungated pages (cost / sla / admin-tenants / tenant-settings)
             get isAuthenticated() gate + source tenant_id from authStore (not URL).
       - A3: backend cross-tenant hardening — admin {tenant_id} path endpoints assert
             path tenant_id == request.state.tenant_id unless caller is platform-admin.
       - A4: dev fake-login — POST /api/v1/auth/dev-login (Settings.env != "prod" gated,
             404 in prod) + login-page "Dev Login" section (import.meta.env.DEV gated).
       - A5: connectivity smoke — backend test_api_smoke.py hits every router; frontend
             real-backend connectivity.spec.ts (opt-in via env); .env.example WORKOS_*
             + dev setup note.

    B. Frontend Architecture 基建 (US-B1..B9) — the foundation layer:
       - B1: Toast/notification system — wire installed `sonner` (<Toaster> + useToast()
             + integrate into fetchWithAuth errors + QueryClient mutationCache onError).
       - B2: design-system components in components/ui/ — <Skeleton> <EmptyState>
             <ErrorRetry> <Card> <Button> <Badge>; refactor existing pages' copy-pasted
             skeleton/empty/retry blocks to use them.
       - B3: Radix-based primitives in components/ui/ — <Dialog> (wrap installed
             @radix-ui/react-dialog), <DropdownMenu> (add @radix-ui/react-dropdown-menu);
             refactor governance DecisionModal → <Dialog>; UserMenu → <DropdownMenu>.
       - B4: frontend observability — @sentry/react SDK + init (DSN from
             import.meta.env.VITE_SENTRY_DSN, no-op if absent) wired into AppErrorBoundary;
             web-vitals → NEW POST /api/v1/telemetry/frontend endpoint → Cat 12.
       - B5: i18n — i18next + react-i18next; frontend/src/i18n/ with en + zh-TW bundles;
             useTranslation() adoption in shell/sidebar/usermenu/auth pages + several
             feature pages; locale switcher in UserMenu; extraction script;
             CONVENTION.md §i18n addendum.
       - B6: a11y baseline — eslint-plugin-jsx-a11y recommended config in eslint.config.js
             (+ fix violations) + @axe-core/playwright → a11y-scan.spec.ts on all 9 pages
             + AuthShell, asserting 0 critical/serious.
       - B7: Lighthouse CI — @lhci/cli + lighthouserc.js (perf/a11y/best-practices/seo
             budgets) + GitHub Actions frontend-lighthouse.yml.
       - B8: visual regression — Playwright toHaveScreenshot() baselines for AppShell +
             login + 4 representative pages (visual-regression.spec.ts) + .gitattributes
             for snapshot PNGs + CI step.
       - B9: AuthShell + login/callback Tailwind migration + UserMenu real user +
             inline-style cleanup sweep (17 files identified by Explore).

    C. Closeout (US-C1) — routes.config wire (if needed) + full Playwright e2e + full
       validation sweep + retrospective Q1-Q7 + memory snapshot + doc syncs (CONVENTION.md
       updates / 16-frontend-design.md / sprint-workflow.md calibration / SITUATION +
       CLAUDE.md deferred post-merge) + PR.

    Deferred OUT of this sprint (explicitly): nothing from the Foundation 1/N gap list —
    this sprint clears it. (Heavier "polish" items like RUM session replay, exhaustive
    visual coverage, full i18n string extraction of every page are scoped minimal here
    and may be expanded in a follow-up; the foundation/wiring itself is complete.)

Created: 2026-05-10 (Sprint 57.13 drafting; user directive — full Foundation 1/N completion + frontend↔backend wiring)
Last Modified: 2026-05-10
Status: Closed (Day 9 closeout — 13/15 USs full + 2 minimal-viable; ratio ~0.95–1.0 in band; see retrospective.md)

Modification History (newest-first):
    - 2026-05-10: Day 9 closeout — sprint done; calibration `frontend-foundation-spike` 0.50 1st app ratio ~0.95–1.0 KEEP; carryovers in retrospective.md Q4
    - 2026-05-10: Initial creation (Sprint 57.13 — Frontend Foundation 1/N Completion + Frontend↔Backend Wiring 全打通; ~15 USs / Day 0-9)

Related:
    - sprint-57-12-plan.md (structural template per sprint-workflow.md §Step 1 — most recent completed sprint)
    - 16-frontend-design.md (frontend 12-page roadmap + Foundation requirements)
    - 20-iam-deep-dive.md (Sprint 57.7 IAM extract — §2.5 sessions/tool_calls observer; §4 open invariants: this sprint closes "Frontend auth UX polish" + "Sentry browser error tracking")
    - claudedocs/1-planning/enterprise-saas-gap-analysis-20260508.md §0.4 + §1.1 (Frontend 20 sub-domains; this sprint closes the Foundation subset)
    - frontend/CONVENTION.md + frontend/STYLE.md (existing codified conventions — this sprint extends §i18n + §design-system)
    - .claude/rules/frontend-react.md / file-header-convention.md / sprint-workflow.md / multi-tenant-data.md / anti-patterns-checklist.md
---

# Sprint 57.13 — Frontend Foundation 1/N Completion + Frontend↔Backend Wiring 全打通

## Sprint Goal

把「前端基礎建設 (Foundation 1/N)」現況清單上的**全部未處理項一次清掉**，並讓 **login → callback → authenticated session → 導覽全部 9 個 active 頁面 → 各頁打到真 backend 並正確回傳**這條主流量端到端跑通。完成後：(1) 真實 OIDC 登入流程不再 redirect loop；(2) 9 個 active 頁面全部 auth-gated 且讀 session tenant；(3) 開發者用 dev fake-login 即可測 auth-gated 頁面（免 WorkOS 帳號）；(4) Toast / Skeleton / EmptyState / ErrorRetry / Dialog / DropdownMenu 共用組件層就位；(5) Sentry + Web Vitals 前端可觀測；(6) i18n zh-TW/en 骨架；(7) a11y baseline (jsx-a11y + axe-core)；(8) Lighthouse CI；(9) visual regression baseline；(10) login/callback + 17 個 inline-style 檔案 Tailwind 化。

---

## Background

### 為什麼現在做 Foundation 完整化（user 直接指示）

Sprint 57.7 做了 "Frontend Foundation 1/N spike"（裝 Tailwind 4 + TanStack Query + AppShell V2 + routes.config single-source）+ 57.9 做 TanStack 4-page migration + 57.10 做 CONVENTION.md + STYLE.md codify。但 gap analysis §1.1 + §0.4 顯示 Foundation 仍有一大批未處理項（shadcn/設計系統組件層 / Sentry / i18next / Lighthouse CI / jsx-a11y + axe-core / visual regression / inline-style cleanup），**而且最關鍵的「前端後端連接打通」（真實 OIDC flow 因 cookie↔localStorage 不對盤而 redirect loop；4 個頁面無 auth gate）一直沒收口**。User 2026-05-10 指示：完全集中處理 Foundation 1/N 全部未處理內容 + 把前端後端連接全部打通，這是最高優先，不簡化。

### 連接打通的核心問題（為什麼是 cookie-only）

| 問題 | 現況 | 修法 |
|------|------|------|
| backend `/auth/callback` 設 httpOnly cookie `v2_jwt`，但前端 `isAuthenticated()` 讀 localStorage `v2_jwt` | httpOnly cookie JS 讀不到 → localStorage 永遠空 → auth-gated 頁面彈回 `/auth/login` → redirect loop | **cookie-only**：`fetchWithAuth` 已 `credentials:"include"` → cookie 自動帶；`tenant_context.py` middleware 新增「Bearer header 缺則讀 `v2_jwt` cookie」fallback；NEW `GET /api/v1/auth/me`（cookie 有效回 `{user, tenant, roles}`，否則 401）；前端 NEW Zustand `authStore`；`isAuthenticated()` → 查 authStore；App 掛載時 `bootstrapAuth()` 打 `/auth/me` 填 authStore；callback page → `bootstrapAuth()` → redirect |
| `oidc_redirect_uri` config default = `http://localhost:3005/auth/callback`（指向 frontend）但 backend 的 callback endpoint 在 `/api/v1/auth/callback` | WorkOS 把 user 送回 frontend page，但那 page 沒有 code exchange 邏輯（只有 `?token=` fallback，backend 不帶 token） | default 改 `http://localhost:8000/api/v1/auth/callback`（dev：vite proxy 不轉 `/auth/callback` 非 `/api` path，所以必須直指 backend port；prod：透過 reverse proxy `/api/v1/auth/callback`）；frontend `/auth/callback` page 角色改為「backend 302 回來的 landing → `bootstrapAuth()` → 導去原頁」 |
| `tenant_context.py` middleware 只讀 `Authorization: Bearer` header | dev fake-login / cookie flow 都無法走 | middleware 改：先看 Bearer header，沒有則看 `v2_jwt` cookie |
| 4 個頁面（cost / sla / admin-tenants / tenant-settings）無 `isAuthenticated()` gate；tenant_id 來自 URL `?tenant_id=...` 或 missing | 任何人開 URL 都進得去；admin `{tenant_id}` path endpoint 不檢查 path tenant 是否 = 認證 tenant | 加 `isAuthenticated()` gate；tenant_id 改讀 `authStore.tenant.id`；backend 加 cross-tenant 檢查（path tenant ≠ session tenant 且非 platform-admin → 403） |
| WorkOS 未配 → `/auth/login` 回 503；`.env.example` 沒列 `WORKOS_*` | 新環境無從得知要配；開發者測 auth-gated 頁面只能手動塞 localStorage | NEW `POST /api/v1/auth/dev-login`（`Settings.env != "prod"` gated）發 V2 JWT cookie 免 WorkOS；`.env.example` 補 `WORKOS_API_KEY` / `WORKOS_CLIENT_ID` / `OIDC_REDIRECT_URI` + dev setup 註解 |

### Foundation 組件層的「不馬虎」原則

- **不用 shadcn CLI**（避免 vendoring 整套 + 重排所有現有組件），但**建一個對等的 `components/ui/` 層**：用已裝的 `@radix-ui/react-dialog` + `@radix-ui/react-slot` + 新增 `@radix-ui/react-dropdown-menu` + `tailwind-merge`（已裝）+ `class-variance-authority`（需裝）做出 `<Dialog>` `<DropdownMenu>` `<Button>`（cva variants）`<Card>` `<Badge>` `<Skeleton>` `<EmptyState>` `<ErrorRetry>`。這是「shadcn-style hand-rolled UI primitives」——業界常見做法，比硬塞 shadcn CLI 更乾淨。
- **設計系統組件必須真的被現有頁面採用**（不是建了放著）：governance `DecisionModal` → `<Dialog>`；UserMenu → `<DropdownMenu>`；governance/verification/memory/admin-tenants/cost/sla 的 loading skeleton / empty state / error retry copy-paste 區塊 → 換成 `<Skeleton>` `<EmptyState>` `<ErrorRetry>`（消重複；per AP-3 反 scattering）。
- **Sentry 是 no-op-safe**：`VITE_SENTRY_DSN` 沒設時 SDK 不 init，零 runtime 影響；但 Web Vitals 報到 backend `/api/v1/telemetry/frontend` → Cat 12，所以**就算沒 Sentry 也有前端可觀測性**。
- **i18n 不求一次抽完所有 string**：建 i18next 骨架 + en/zh-TW bundle + shell/sidebar/usermenu/auth pages + 至少 2 個 feature page 採用 + locale switcher + extraction script + CONVENTION.md §i18n addendum；剩餘頁面的 string 抽取列入 follow-up（但**骨架與規範完整**，這是 Foundation 的定義）。
- **Lighthouse CI / visual regression 是 baseline 不是 gate**（先別當 hard CI gate，避免第一輪就紅；先 `continue-on-error` + 收基線，後續 sprint 再轉 gate）。

### 17.md / V2 紀律對齊

- `17-cross-category-interfaces.md`：NEW `GET /api/v1/auth/me` + `POST /api/v1/auth/dev-login` + `POST /api/v1/telemetry/frontend` 是新 API surface — 登記在 17.md（或如果 17.md 只管 agent harness 內部 contract，則在 plan §Tech Spec 標明 owner）。0 NEW agent-harness contract / ABC / LoopEvent / migration（除了可能一張 dev-user seed 不需要 migration）。
- Multi-tenant 鐵律：`/auth/me` + `/auth/dev-login` 都明確 tenant_id（dev-login 必帶 `tenant_code`，不存在 → 自動建 dev tenant 或 400）；4 頁 tenant_id 改讀 session（不再 URL 可偽造）；admin endpoint cross-tenant 檢查。
- LLM Provider Neutrality：N/A（這 sprint 不碰 `agent_harness/`）；`workos` 是 auth SDK 不是 LLM SDK，`@sentry/react` 是 obs SDK——都不違反 §原則 2。
- CC Reference 不照搬：N/A（前端 SaaS web app，不是 CC 移植）。

---

## User Stories

### Group A — Frontend↔Backend Wiring 打通

#### US-A1: OIDC auth flow 端到端（cookie-only）

**作為** 一個 enterprise 使用者，**我希望** 在 `/auth/login` 點登入 → 經 WorkOS 認證 → 自動回到平台且維持登入狀態能導覽各頁，**以便** 真的能用這個平台（不是 redirect loop）。

**Backend**:
- `platform_layer/middleware/tenant_context.py` — `TenantContextMiddleware`（或對應 dependency）改：JWT 來源優先 `Authorization: Bearer <token>`，缺則讀 `request.cookies.get("v2_jwt")`；其餘邏輯（decode / 401 / `request.state.{tenant_id,user_id,roles}`）不變。
- NEW `GET /api/v1/auth/me` — 走同一個 middleware（需有效 JWT，cookie 或 header）；回 `AuthMeResponse {user: {id, email, display_name}, tenant: {id, name, code}, roles: list[str]}`；middleware 已驗 JWT，handler 只從 `request.state` + DB 撈 user/tenant 詳情；無效 JWT → middleware 已回 401。
- `core/config/__init__.py` — `oidc_redirect_uri` default 改 `http://localhost:8000/api/v1/auth/callback`（dev 直指 backend port；註解說明 prod 走 reverse proxy）。
- `api/v1/auth.py` `/callback` — 維持設 `v2_jwt` cookie + 302，但 `final_redirect` 改成導去 frontend `/auth/callback?next=<原頁>`（讓 frontend callback page 接管 bootstrap + 最終導航），或直接導去原頁（二選一，Day 1 三-prong 後定；傾向導去 frontend `/auth/callback` 以便統一 bootstrap）。

**Frontend**:
- NEW `frontend/src/features/auth/store/authStore.ts` — Zustand store `{ status: "unknown" | "authenticated" | "anonymous", user: AuthUser | null, tenant: AuthTenant | null, roles: string[], bootstrap(): Promise<void>, clear(): void }`；`bootstrap()` 打 `/api/v1/auth/me` → 200 設 authenticated + payload / 401 設 anonymous。
- `frontend/src/features/auth/services/authService.ts` — 加 `fetchAuthMe()`；`isAuthenticated()` 改成「if authStore.status === 'unknown' → false（caller 應先 bootstrap）；else status === 'authenticated'」；保留 `fetchWithAuth` 的 `credentials:"include"`，Bearer-from-localStorage 改為**只在 localStorage 有 token 時才加**（dev fake-login 路徑會用；cookie 路徑不需要）；`logout()` 打 `/api/v1/auth/logout` + `authStore.clear()` + redirect。
- `frontend/src/App.tsx` — App 掛載時（或一個 `<AuthBootstrap>` wrapper）`useEffect(() => authStore.bootstrap(), [])`；在 `status === 'unknown'` 時顯示 loading spinner（避免 gate 在 bootstrap 完成前就誤判 anonymous → 閃 redirect）。
- `frontend/src/pages/auth/callback/index.tsx` — 改為：`useEffect`: 若 `?error=` → 顯示錯誤；否則 `await authStore.bootstrap()` → `navigate(searchParams.get("next") || consumePostLoginRedirect(), {replace:true})`；wrap 在 `<AuthShell>`（US-B9 一起做也行，但 callback 重寫在這裡）。
- 9 個 auth-gated 頁面的 gate（chat-v2 / governance / verification / loop-debug / memory 現有的 + cost / sla / admin-tenants / tenant-settings US-A2 加的）改成依 `authStore.status`（`unknown` → spinner；`anonymous` → `<Navigate to="/auth/login">` + `setPostLoginRedirect`；`authenticated` → render）。

**Tests**: backend `tests/integration/api/test_auth_me.py`（cookie 有效 → 200 + payload；無 cookie / 無 header → 401；過期 JWT → 401）；frontend `tests/unit/auth/authStore.test.ts`（bootstrap 200 → authenticated；401 → anonymous；clear → unknown→anonymous）+ `tests/unit/auth/isAuthenticated.test.ts`（status 對應）。

**驗收**: 起 backend（dev fake-login 或 mock /auth/me）→ 開 `/governance` 未登入 → 彈 `/auth/login`；登入（dev-login）後 → 自動回 `/governance` 且不再彈走；重整頁面 → 仍 authenticated（cookie 還在）。

#### US-A2: 4 個 ungated 頁面補 auth gate + tenant-from-session

**作為** 平台維運者，**我希望** cost-dashboard / sla-dashboard / admin-tenants / tenant-settings 也需要登入才能看，且看到的是我所屬 tenant 的資料（不是 URL 隨便填的 tenant），**以便** 不洩漏跨 tenant 資料。

- 4 個 `pages/*/index.tsx` — 加 `authStore.status` gate（同 US-A1 pattern）+ wrap `AppShellV2`（cost/sla/admin-tenants/tenant-settings 已 wrap，補 gate 即可）。
- cost-dashboard / sla-dashboard / tenant-settings — `tenant_id` 改從 `authStore.tenant.id` 取（移除 URL `?tenant_id=` 或 hardcoded）；service call 帶這個 id。
- admin-tenants list — 是 platform-admin scoped endpoint（`/api/v1/admin/tenants` 無 tenant_id），保持；但加 gate + 若 `roles` 不含 platform-admin → 顯示 `<EmptyState>` "需要平台管理員權限"（不直接 403 白屏）。
- `routes.config.ts` — 不需改（4 頁已 active）；但 CONVENTION.md 補一句「所有 active page 必須 auth-gated」。

**Tests**: frontend `tests/unit/pages/authGate.test.tsx`（4 頁各：status anonymous → Navigate；authenticated → render）+ Playwright `tests/e2e/auth/four-page-gate.spec.ts`（未 seed JWT 開 4 頁各彈 /auth/login；dev-login 後可進）。

#### US-A3: Backend cross-tenant hardening（admin {tenant_id} path endpoints）

**作為** 安全負責人，**我希望** `/api/v1/admin/tenants/{tenant_id}/...` 系列 endpoint 不信任 path 上的 tenant_id（除非 caller 是 platform-admin），**以便** 一般 admin 不能透過改 URL 看別 tenant。

- NEW dependency `require_tenant_match_or_platform_admin(tenant_id: UUID, request: Request)` in `platform_layer/middleware/tenant_context.py`（或 `api/_deps.py`）：若 `request.state.roles` 含 `platform_admin` → pass（可看任何 tenant）；否則 assert `tenant_id == request.state.tenant_id`，不符 → 403。
- `api/v1/admin/{tenants,cost_summary,sla_reports}.py` — 把 `{tenant_id}` path endpoint 的 dependency 從 `require_admin_platform_role`（或現況）改/加上 `require_tenant_match_or_platform_admin`。`GET /api/v1/admin/tenants`（list，無 tenant_id）保持 platform-admin only。
- 確認 RLS：這些 endpoint 若用 `get_db_session_with_tenant` 已有 RLS；若用裸 session，補 `SET LOCAL app.tenant_id`。

**Tests**: `tests/integration/api/test_admin_cross_tenant.py`（一般 admin 帶 tenant A JWT 打 tenant B 的 cost-summary → 403；platform-admin 打任何 tenant → 200；tenant A admin 打自己 tenant → 200）。

#### US-A4: Dev fake-login（免 WorkOS）

**作為** 開發者，**我希望** 在 dev 環境不用註冊 WorkOS 帳號就能登入測 auth-gated 頁面，**以便** 本地開發順暢。

- NEW `POST /api/v1/auth/dev-login?tenant_code=<code>&email=<email>` in `api/v1/auth.py`：`if Settings.env == "prod": raise HTTPException(404)`（prod 完全隱形）；resolve `tenant_code` → tenant（不存在 → 自動建一個 `name="Dev Tenant"` 或 400，傾向自動建以降低摩擦，但用一個固定 dev tenant code list 限制）；upsert dev user（`external_id=f"dev:{email}"`）；issue `v2_jwt` cookie（roles `["user", "admin", "platform_admin"]` 讓 dev 能測所有頁面）+ 回 `{ user, tenant, roles }` JSON（不 redirect，讓前端自己導）。
- Frontend `pages/auth/login/index.tsx` — `{import.meta.env.DEV && (<DevLoginSection />)}`：一個輸入 tenant_code（default `"dev"`）+ email（default `"dev@local"`）的小 form，submit → `POST /api/v1/auth/dev-login` → `await authStore.bootstrap()`（或直接用回的 payload 設 authStore）→ `navigate(consumePostLoginRedirect())`。Prod build (`import.meta.env.DEV === false`) 完全不 render 此區塊。
- `scripts/dev.py` 或 README — 註明「dev 不需 WorkOS；用 /auth/login 的 Dev Login 按鈕；或 `curl -X POST localhost:8000/api/v1/auth/dev-login?tenant_code=dev`」。

**Tests**: `tests/integration/api/test_dev_login.py`（env=dev → 200 + cookie set + tenant created；env=prod → 404；roles 含 platform_admin）+ Playwright `tests/e2e/auth/dev-login.spec.ts`（開 /auth/login → 點 Dev Login → 導到 cost-dashboard 且 authStore authenticated）。

#### US-A5: Connectivity smoke + .env.example

**作為** 維運者，**我希望** 有一個自動檢查確認「前端會打的每個 backend endpoint 都活著且回正確 shape」+ 新環境知道要配什麼，**以便** 連接斷掉時 CI 抓得到。

- NEW backend `tests/integration/api/test_api_smoke.py` — 用一個 dev JWT（透過 `JWTManager.encode` 直接造，roles platform_admin）打每個 registered router 的代表性 GET（`/api/v1/health`, `/api/v1/auth/me`, `/api/v1/admin/tenants`, `/api/v1/admin/tenants/{seed_tenant}/cost-summary?month=...`, `/api/v1/admin/tenants/{seed_tenant}/sla-report?month=...`, `/api/v1/audit/log`, `/api/v1/verification/recent`, `/api/v1/memory/recent?layer=user`, `/api/v1/governance/approvals`），assert status ∈ {200, 404}（404 OK = 無資料；不可 5xx / 401）+ 回應是合法 JSON。
- NEW frontend `tests/e2e/connectivity/connectivity.spec.ts` — `test.skip(!process.env.RUN_CONNECTIVITY, "real-backend only")`；流程：`POST /api/v1/auth/dev-login` → 逐一 `page.goto` 9 個 active 頁面 → assert 各頁的 root testid 出現且無 console error / no `[role=alert]` 含 "Error"。CI 預設不跑（需 backend + DB）；本地用 `RUN_CONNECTIVITY=1 npx playwright test connectivity` 手動跑。
- `.env.example`（root）+ `backend/.env.example`（若有）— 新增：`WORKOS_API_KEY=`（註解：dev 可留空，用 /auth/dev-login）/ `WORKOS_CLIENT_ID=` / `OIDC_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback` / `VITE_SENTRY_DSN=`（前端，留空 = Sentry 不 init）。README / SITUATION-6（service startup）補 dev 不需 WorkOS 的說明。

**驗收**: `cd backend && pytest tests/integration/api/test_api_smoke.py` green；`RUN_CONNECTIVITY=1 npx playwright test connectivity`（backend 跑時）green。

### Group B — Frontend Architecture 基建

#### US-B1: Toast / notification 系統（wire installed `sonner`）

**作為** 使用者，**我希望** 操作失敗時看到明確的提示（不是 silent 失敗），**以便** 知道發生什麼。

- `frontend/src/App.tsx`（或 `main.tsx`）— 掛 `<Toaster position="top-right" richColors />`（sonner，已裝）。
- NEW `frontend/src/lib/toast.ts` — `toastError(msg, opts?)` / `toastSuccess(msg)` / `toastInfo(msg)` 薄包 sonner（統一 duration / aria）。
- `frontend/src/features/auth/services/authService.ts` `fetchWithAuth` — 401 → `toastError("登入已過期，請重新登入")` + `authStore.clear()` + redirect `/auth/login`；其他非 2xx → 不在 fetchWithAuth toast（交給 caller / TanStack），但 throw Error with detail。
- NEW `frontend/src/lib/queryClient.ts` — 集中建 `QueryClient`，`mutationCache: new MutationCache({ onError: (err) => toastError(...) })`、`queryCache` `onError` 視情況（query error 通常頁面已有 ErrorRetry，可不 toast，避免吵）；`App.tsx` 用這個 client（取代散落的 inline `new QueryClient()`）。

**Tests**: `tests/unit/lib/toast.test.ts`（呼叫 sonner mock 確認）+ `tests/unit/lib/queryClient.test.ts`（mutation onError 觸發 toastError）+ Playwright `tests/e2e/toast/toast.spec.ts`（mock 一個 mutation 500 → 看到 toast）。

#### US-B2: 設計系統組件層（components/ui/ — Skeleton / EmptyState / ErrorRetry / Card / Button / Badge）

**作為** 前端開發者，**我希望** 有一套共用的 loading/empty/error/card/button/badge 組件，**以便** 不用每頁 copy-paste（per AP-3 反 scattering + STYLE.md §6-7 已文件化的 pattern）。

- NEW `frontend/src/components/ui/`:
  - `skeleton.tsx` — `<Skeleton className>` 基礎 + `<TableSkeleton rows={5} cols={n}>` + `<CardSkeleton count={3}>`（取自 STYLE.md §6）。
  - `empty-state.tsx` — `<EmptyState icon={LucideIcon} title message action={{label, onClick}}?>`（取自 STYLE.md §7 + verification/memory 現有的 empty + reset 按鈕）。
  - `error-retry.tsx` — `<ErrorRetry error message onRetry>` 內含 `retryClicked` StrictMode-safe state（取自 STYLE.md §7 完整 code + Sprint 57.9 D-PRE-15 lesson）。
  - `card.tsx` — `<Card> <CardHeader> <CardTitle> <CardContent> <CardFooter>`（Tailwind only）。
  - `button.tsx` — `<Button variant="primary"|"secondary"|"ghost"|"danger" size="sm"|"md"|"lg">` 用 `class-variance-authority`（需 `npm i class-variance-authority`）+ `tailwind-merge`（已裝）+ `@radix-ui/react-slot`（已裝，`asChild` 支援）。
  - `badge.tsx` — `<Badge variant="default"|"success"|"warning"|"danger"|"info">`（取代散落的 inline badge；含 STYLE.md §3 risk palette）。
  - `index.ts` — barrel export。
- **採用（消重複）**：refactor 至少這些頁面用上述組件取代 copy-paste：governance（ApprovalsPage / AuditLogViewer 的 skeleton + empty + retry）、verification（VerificationList / CorrectionTraceView）、memory（MemoryRecentList / MemoryByScopeBrowser）、admin-tenants（TenantListTable 的 skeleton/empty）、cost-dashboard / sla-dashboard（loading）。每 refactor 都跑該頁既有 Vitest 確認無 regression。
- CONVENTION.md — §design-system addendum：「loading/empty/error 必須用 `components/ui/`，禁止頁面內 copy-paste」。

**Tests**: `tests/unit/components/ui/*.test.tsx`（各組件 render + variant + ErrorRetry 的 retryClicked 行為）≥ 12 tests。

#### US-B3: Radix-based primitives（Dialog / DropdownMenu）+ refactor consumers

**作為** 前端開發者，**我希望** modal/dropdown 用 accessible 的 Radix primitives 包裝（focus trap / ESC / aria 自動處理），**以便** 不用手刻 a11y。

- NEW `frontend/src/components/ui/`:
  - `dialog.tsx` — wrap `@radix-ui/react-dialog`（已裝）：`<Dialog> <DialogTrigger> <DialogContent> <DialogHeader> <DialogTitle> <DialogDescription> <DialogFooter> <DialogClose>` + Tailwind 樣式 + overlay。
  - `dropdown-menu.tsx` — wrap `@radix-ui/react-dropdown-menu`（需 `npm i @radix-ui/react-dropdown-menu`）：`<DropdownMenu> <DropdownMenuTrigger> <DropdownMenuContent> <DropdownMenuItem> <DropdownMenuSeparator> <DropdownMenuLabel>`。
- **採用**：
  - governance `DecisionModal`（現在手刻）→ 用 `<Dialog>`（保留現有 API 形狀；內部換實作；跑 governance Vitest + e2e 確認 approval flow 不破）。
  - `components/UserMenu.tsx`（現在手刻 popover）→ 用 `<DropdownMenu>`（顯示 `authStore.user.email` + display_name + role badges + locale switcher（US-B5 加）+ Sign out）。
- `package.json` — `+@radix-ui/react-dropdown-menu` `+class-variance-authority`（B2 也要）。

**Tests**: `tests/unit/components/ui/dialog.test.tsx` + `dropdown-menu.test.tsx`（open/close/ESC/item click）+ governance e2e regression（DecisionModal flows 4/4）+ UserMenu unit（顯示 email / Sign out 呼叫 logout）。

#### US-B4: 前端可觀測性（Sentry SDK + Web Vitals + telemetry endpoint）

**作為** 維運者，**我希望** 前端 error + Web Vitals 有上報管道，**以便** 生產出問題時看得到。

- `package.json` — `+@sentry/react` `+web-vitals`。
- NEW `frontend/src/lib/observability.ts` — `initObservability()`：若 `import.meta.env.VITE_SENTRY_DSN` → `Sentry.init({ dsn, environment: import.meta.env.MODE, tracesSampleRate: 0.1, ... })`；否則 no-op（log 一行「Sentry disabled (no DSN)」）。`reportError(err, ctx?)` → Sentry.captureException（有 DSN）+ 永遠 `console.error`。`reportWebVitals()`：`onCLS/onFCP/onLCP/onINP/onTTFB(metric => fetch('/api/v1/telemetry/frontend', {method:'POST', body: JSON.stringify({name, value, id, rating, navigationType})}))`（fire-and-forget；fetch 失敗 swallow）。
- `frontend/src/main.tsx` — `initObservability()` + `reportWebVitals()` 開機呼叫。
- `frontend/src/components/AppErrorBoundary.tsx` — `onError` 改呼 `reportError(error, {componentStack})`（取代現有 placeholder）。
- `fetchWithAuth` / `toastError` — 5xx / network error 時也 `reportError`。
- NEW backend `api/v1/telemetry.py` — `POST /api/v1/telemetry/frontend`（**不需 auth** — 前端 unauthenticated 也可能有 web vitals；但 rate-limit-friendly，body 限 schema）；收 `{name, value, id, rating, navigationType, url?}` → 透過 Cat 12 telemetry（`observability` module 的現有 metric recorder / span）記一個 `frontend.web_vitals` metric（per metric name as label）+ `frontend.error` event（若是 error report，另一個 endpoint `POST /api/v1/telemetry/frontend-error` 收 `{message, stack, url, userAgent}`）。register router in `api/main.py`。
- `.env.example` — `VITE_SENTRY_DSN=`（已在 US-A5 列）；backend 無需 Sentry。

**Tests**: `tests/integration/api/test_telemetry_frontend.py`（POST web_vitals → 200 + metric recorded；POST error → 200）+ `tests/unit/lib/observability.test.ts`（no DSN → no Sentry.init；有 DSN → init 被呼；reportWebVitals 呼 fetch）。

#### US-B5: i18n（i18next + react-i18next，zh-TW + en）

**作為** 台/港使用者，**我希望** 介面能切繁中，**以便** 符合目標市場。

- `package.json` — `+i18next` `+react-i18next` `+i18next-browser-languagedetector` `+i18next-parser`（devDep，extraction）。
- NEW `frontend/src/i18n/`:
  - `index.ts` — `i18n.use(LanguageDetector).use(initReactI18next).init({ resources: { en, "zh-TW" }, fallbackLng: "en", detection: { order: ["localStorage", "navigator"], lookupLocalStorage: "ipa-locale" }, interpolation: { escapeValue: false } })`。
  - `locales/en/common.json` + `locales/zh-TW/common.json`（namespace `common` 先做：shell / sidebar nav labels / usermenu / auth pages / 通用按鈕 Save/Cancel/Retry/...）。
  - 後續可加 `locales/*/governance.json` 等 per-feature namespace（這 sprint 至少把 `common` + `auth` 兩個 namespace 做齊，feature namespace 留 placeholder + 1-2 個示範）。
- `frontend/src/main.tsx` — `import "./i18n"` before render。
- 採用：`AppShellV2` / `Sidebar`（nav labels — 但 nav label 來自 `routes.config.ts` 的 `name`，所以 `routes.config.ts` 的 `name` 改成 i18n key + Sidebar 用 `t(route.name)`，或 routes.config 加 `nameKey`）；`UserMenu`（含 locale switcher：en ⇄ 繁中，寫 `ipa-locale` localStorage + `i18n.changeLanguage`）；`pages/auth/login` + `pages/auth/callback`；至少 2 個 feature page（建議 cost-dashboard + verification）示範 `useTranslation`。
- CONVENTION.md — §i18n addendum：「user-facing string 必須走 `t()`；新 namespace 命名；extraction 用 `npm run i18n:extract`」。

**Tests**: `tests/unit/i18n/i18n.test.ts`（en/zh-TW bundle 有相同 key set；changeLanguage 生效）+ Playwright `tests/e2e/i18n/locale-switch.spec.ts`（切繁中 → sidebar label 變 + reload 後仍繁中）。

#### US-B6: a11y baseline（jsx-a11y + axe-core）

**作為** 採購方（EU EN 301 549 / WCAG 2.1 AA），**我希望** 介面有 a11y 檢查，**以便** 通過 procurement gate。

- `package.json` — `+eslint-plugin-jsx-a11y`（devDep）+ `+@axe-core/playwright`（devDep）。
- `frontend/eslint.config.js` — 加 `jsxA11y.configs.recommended`（或 strict）；跑 `npm run lint` → 修所有 surfaced violations（預期：login/callback 的 inline-style button 缺 type 已有、img alt、label htmlFor 等；US-B9 的 AuthShell 重寫一起修）。
- NEW `frontend/tests/e2e/a11y/a11y-scan.spec.ts` — 用 `AxeBuilder`：對 9 個 active 頁面（dev-login 後）+ `/auth/login` + `/auth/callback` 各跑 `axe.analyze()`，assert `violations.filter(v => ["critical","serious"].includes(v.impact)).length === 0`（moderate/minor 列 warning 不 fail，先 baseline）。
- CONVENTION.md — §a11y addendum。

**Tests**: 上述 a11y-scan.spec.ts 即是 test（≥ 11 個 page scan）。

#### US-B7: Lighthouse CI

**作為** 前端 lead，**我希望** 每個 PR 有 Lighthouse 報告（perf / a11y / best-practices / seo），**以便** 不退化。

- `package.json` — `+@lhci/cli`（devDep）+ script `"lhci": "lhci autorun"`。
- NEW `frontend/lighthouserc.js` — `{ ci: { collect: { staticDistDir: "./dist", url: ["http://localhost/", "http://localhost/cost-dashboard", ...重點頁], numberOfRuns: 1 }, assert: { assertions: { "categories:performance": ["warn", {minScore: 0.7}], "categories:accessibility": ["error", {minScore: 0.9}], "categories:best-practices": ["warn", {minScore: 0.8}], "first-contentful-paint": ["warn", {maxNumericValue: 2000}], "interactive": ["warn", {maxNumericValue: 4000}] } }, upload: { target: "temporary-public-storage" } } }`。注意：static dist 對 SPA 的 client-routed 頁可能要設 `staticDistDir` + `--collect.url` 用 `index.html`，或用 `startServerCommand: "npm run preview"`。Day 7 三-prong 試跑後定。
- NEW `.github/workflows/frontend-lighthouse.yml` — on PR touching `frontend/**`：`npm ci && npm run build && npx lhci autorun`；`continue-on-error: true`（先不當 hard gate，避免第一輪紅 block 自己；後續 sprint 轉 gate）。
- CONVENTION.md — §performance addendum（Web Vitals 預算 + Lighthouse 門檻）。

**Tests**: N/A（CI workflow；本地 `npm run build && npm run lhci` 跑通即驗收）。

#### US-B8: Visual regression baseline

**作為** 前端開發者，**我希望** 關鍵頁面有截圖基線，**以便** 不小心改壞版面時 e2e 抓得到。

- NEW `frontend/tests/e2e/visual/visual-regression.spec.ts` — 對 `AppShellV2`（空 main）+ `/auth/login` + 4 個代表頁（cost-dashboard / governance approvals tab / verification recent tab / admin-tenants list — 都用 mock 固定資料以求 deterministic）各 `await expect(page).toHaveScreenshot('<name>.png', { maxDiffPixelRatio: 0.02 })`。
- 第一次跑 `npx playwright test visual --update-snapshots` 產生 baseline PNG（commit 進 `tests/e2e/visual/visual-regression.spec.ts-snapshots/`）。
- `.gitattributes` — `*.png binary`（避免 line-ending mangling）。
- `playwright.config.ts` — 確認 `snapshotPathTemplate` / `expect.toHaveScreenshot` 設定（threshold / animations: "disabled"）。
- CI：visual spec 跑在 `chromium` only（跨 OS 渲染差異 → CI 用 Linux baseline；本地 Windows 跑可能差異 → 文件註明「baseline 是 CI Linux 產的；本地跑 visual 用 `--update-snapshots` 自己看 diff 不要 commit」）。或更簡單：visual spec 加 `test.skip(process.platform !== 'linux' && !process.env.CI)` —— Day 9 三-prong 後定。

**Tests**: 上述 visual-regression.spec.ts（≥ 6 截圖）。

#### US-B9: AuthShell + login/callback Tailwind 化 + UserMenu real user + inline-style cleanup sweep

**作為** 前端開發者，**我希望** 沒有 inline `style={{}}` 散落、login/callback 用 AuthShell + 設計系統組件、UserMenu 顯示真實登入者，**以便** codebase 一致（per `.claude/rules/frontend-react.md` Tailwind utility-first）。

- `pages/auth/login/index.tsx` — 重寫：`<AuthShell>` 內一個 `<Card>` 置中：logo / title (`t()`) / `<Button variant="primary">Login with Microsoft Entra</Button>`（onClick → `/api/v1/auth/login?redirect_to=...`）/ error `<EmptyState>`（若 `?error=`）/ `{import.meta.env.DEV && <DevLoginSection/>}`（US-A4）/ vendor footnote。去掉所有 inline style。
- `pages/auth/callback/index.tsx` — 重寫：`<AuthShell>` 內：loading `<Skeleton>`/spinner（bootstrap 中）/ error `<EmptyState action={{label:"Back to login", onClick: ...}}>`（若 `?error=`）；邏輯 = US-A1 的 bootstrap + navigate。去掉 inline style。
- `components/UserMenu.tsx` — 用 US-B3 的 `<DropdownMenu>`：trigger 顯示 avatar（initials from `authStore.user.display_name`）+ name；content 顯示 email + role `<Badge>`s + locale switcher（US-B5）+ `<DropdownMenuItem onSelect={logout}>Sign out</DropdownMenuItem>`。
- **Inline-style cleanup sweep** — Explore 識別的 17 個檔案（`SubagentTree.tsx` / `TenantSettingsView.tsx` / `TenantListPagination.tsx` / `TenantListTable.tsx` / `TenantListFilters.tsx` / `ChatLayout.tsx` / `SLAMetricsCard.tsx` / `MonthPicker.tsx` / `CostBreakdownTable.tsx` / `MessageList.tsx` / `ApprovalCard.tsx` / `ToolCallCard.tsx` + auth pages + admin-tenants index 等）→ 把 `style={{...}}` 換成 Tailwind utility class（surgical：只動 style，不改邏輯；per Karpathy「不順手改相鄰代碼」——但 inline style 就是這 US 的標的所以動）。每改一個檔跑該檔關聯 Vitest。
- `.claude/rules/frontend-react.md` / CONVENTION.md / STYLE.md — 確認「禁止 inline style」規則已有；若沒有，補一句。

**Tests**: `tests/unit/pages/auth/login.test.tsx` + `callback.test.tsx`（render AuthShell；DEV 模式顯示 DevLoginSection；error param 顯示 EmptyState）+ `tests/unit/components/UserMenu.test.tsx`（顯示 authStore.user；Sign out 呼 logout）+ grep 確認 `frontend/src` 無 `style={{` 殘留（一個 lint script 或 test）。

### Group C — Closeout

#### US-C1: routes.config wire（如需）+ Playwright e2e 全套 + 全 validation sweep + retrospective + memory + doc syncs + PR

- `routes.config.ts` — 這 sprint 不新增 page（除非 US 中決定加一個 `/auth/login` 之外的 auth 相關頁），預期不改；但確認 4 頁 gate + CONVENTION 規則一致。
- Playwright e2e 匯整：US-A1 auth flow / US-A2 four-page-gate / US-A4 dev-login / US-A5 connectivity（opt-in）/ US-B1 toast / US-B3 dialog+dropdown / US-B5 locale-switch / US-B6 a11y-scan / US-B8 visual — 全跑通。
- 全 validation sweep：pytest（baseline 1654 + 新增 backend tests，target +25-35）/ mypy --strict 0 / 9 V2 lints 9/9 / Vitest（baseline 168 + 新增，target +50-70）/ Playwright（baseline 37 + 新增，target +20-30）/ Vite build（main bundle size noted — 預期會漲，sonner 已裝、Radix dropdown + sentry + i18next + cva + axe 等；track vs 296.58 kB；可能需 code-split 緩解，列 retrospective Q3）/ ESLint silent（含新 jsx-a11y）/ backend black+isort+flake8 / LLM SDK leak 0。
- `retrospective.md` Q1-Q7（Q7 N/A SKIP — Foundation 完成 sprint，不是新領域 spike；但這是個大 sprint，retrospective 要認真寫 estimate accuracy + 各 US 實際 vs 預估）。
- memory snapshot `project_phase57_13_frontend_foundation_completion.md` + MEMORY.md index。
- doc syncs（in-sprint）：CONVENTION.md（§design-system / §i18n / §a11y / §performance / §auth-flow addenda — 把這 sprint 建的 pattern 文件化）+ STYLE.md（§design-system 組件對應）+ 16-frontend-design.md（V2 Ship Timeline — Foundation 1/N 標記 complete + 新增「auth flow端到端 / dev-login / Toast / 設計系統組件 / Sentry / i18n / a11y / Lighthouse / visual」清單）+ sprint-workflow.md（calibration matrix +1 NEW class `frontend-foundation-spike`）+ enterprise-saas-gap-analysis-20260508.md §0.4（Foundation 1/N → done）。
- doc syncs（deferred post-merge closeout PR）：CLAUDE.md（V2 status / main HEAD / Latest Sprint / Next Phase 候選）+ SITUATION-V2-SESSION-START.md（§9 milestone + Last Updated header）。
- PR open + closeout user decision points（bundle size delta / 任何 deferred 項 → carryover AD / calibration ratio / Lighthouse + visual 何時轉 hard gate）。

---

## Technical Specifications

### Auth flow 端到端（cookie-only）— sequence

```
1. 未登入 user 開 /governance
   → React: authStore.status === "unknown"（剛開機 bootstrap 中）→ 顯示 spinner
   → bootstrap() 打 GET /api/v1/auth/me → 401（無 cookie）→ authStore.status = "anonymous"
   → /governance gate: status === "anonymous" → setPostLoginRedirect("/governance") + <Navigate to="/auth/login">

2. /auth/login 點 "Login with Microsoft Entra"
   → window.location.href = /api/v1/auth/login?redirect_to=/governance
   → backend /auth/login: WorkOSOIDCFlow().initiate_login() → 302 to WorkOS authorize URL
     + set cookies: oidc_state / oidc_redirect_to(=/governance) / oidc_tenant_code(=default 或 user 選)

3. WorkOS hosted login → user 認證 → WorkOS 302 to OIDC_REDIRECT_URI
   = http://localhost:8000/api/v1/auth/callback?code=...&state=...

4. backend /auth/callback:
   → validate oidc_state cookie vs state param
   → resolve oidc_tenant_code cookie → tenants.id（不存在 → 400）
   → WorkOSOIDCFlow().exchange_callback(code, state, expected_state) → OIDCProfile
   → _upsert_user_from_oidc(profile, tenant_id, db) → users row
   → JWTManager().encode(sub=user.id, tenant_id, roles=["user"], extra={email, external_id}) → v2_jwt
   → set v2_jwt cookie (httpOnly, secure=Settings.cookie_secure, samesite=lax, max_age=jwt_expires_minutes*60)
   → 302 to <frontend>/auth/callback?next=/governance   ← (oidc_redirect_to cookie 的值放 next param)
     [decision: 也可直接 302 到 /governance；但走 frontend /auth/callback 統一 bootstrap 較乾淨]

5. frontend /auth/callback page:
   → useEffect: if ?error → show EmptyState; else
   → await authStore.bootstrap() → GET /api/v1/auth/me（cookie 帶上）→ 200 {user, tenant, roles} → status = "authenticated"
   → navigate(searchParams.get("next") || consumePostLoginRedirect(), { replace: true }) → /governance

6. /governance gate: status === "authenticated" → render <AppShellV2><GovernancePage/></AppShellV2>
   → GovernancePage 的 service call 用 fetchWithAuth → cookie 自動帶（credentials: "include"）→ middleware 讀 cookie → request.state.tenant_id → RLS

Dev fast-path (US-A4): 步驟 2-4 換成 /auth/login 的 DevLoginSection → POST /api/v1/auth/dev-login?tenant_code=dev
   → backend: env != prod check → upsert dev tenant + dev user → encode JWT roles=["user","admin","platform_admin"]
   → set v2_jwt cookie + return {user, tenant, roles} JSON
   → frontend: authStore 直接用 return payload 設 authenticated → navigate(consumePostLoginRedirect())
```

### `tenant_context.py` middleware 改動（最小）

```python
# 現況（pseudo）：
token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
if not token: raise HTTPException(401)
# 改成：
auth_header = request.headers.get("Authorization", "")
token = auth_header.removeprefix("Bearer ").strip() if auth_header.startswith("Bearer ") else ""
if not token:
    token = request.cookies.get("v2_jwt", "")   # NEW: cookie fallback
if not token: raise HTTPException(401)
# ... 其餘 decode / request.state 設定不變
```
注意：`/api/v1/auth/login` `/api/v1/auth/callback` `/api/v1/auth/dev-login` `/api/v1/telemetry/frontend*` `/api/v1/health` 必須在 middleware 的 **public path allowlist**（無需 JWT）；確認現有 allowlist 包含這些（Day 1 三-prong grep）。

### Backend NEW endpoints schema

- `GET /api/v1/auth/me` → 200 `{ "user": {"id": uuid, "email": str, "display_name": str|null}, "tenant": {"id": uuid, "name": str, "code": str}, "roles": [str] }` / 401（middleware）
- `POST /api/v1/auth/dev-login?tenant_code=str&email=str` → (env!=prod) 404 / 200 `{ "user": {...}, "tenant": {...}, "roles": ["user","admin","platform_admin"] }` + Set-Cookie v2_jwt
- `POST /api/v1/telemetry/frontend` (no auth) body `{ "name": str, "value": float, "id": str, "rating": str, "navigationType": str|null, "url": str|null }` → 200 `{}` (fire-and-forget metric record)
- `POST /api/v1/telemetry/frontend-error` (no auth) body `{ "message": str, "stack": str|null, "url": str|null, "user_agent": str|null }` → 200 `{}` (record as Cat 12 event)

### Calibration class

NEW class `frontend-foundation-spike` — HYBRID weighted blend over the 15 USs:
- Group A (A1-A5: auth wiring + dev-login + smoke) ≈ `backend-auth × 0.65` weight ~0.30 of sprint
- Group B (B1-B3: Toast + design-system + Radix) ≈ `frontend-arch-greenfield × 0.50` weight ~0.30
- Group B (B4-B8: Sentry + i18n + a11y + Lighthouse + visual) ≈ `frontend-infra-new × 0.45` weight ~0.25
- Group B (B9: AuthShell + inline cleanup) ≈ `frontend-pattern-reuse × 0.35` weight ~0.10
- Group C (C1 closeout) ≈ `closeout × 0.80` weight ~0.05
- Weighted blend ≈ **0.50** mid-band. Pending 2-3 future Foundation-style sprints to validate (likely none — Foundation is one-shot — so this may stay 1-data-point).

---

## File Change List

> 完整精確清單在 Day 0 三-prong 後於 checklist 落實；以下為 plan 層級概覽。

### NEW Backend
- `backend/src/api/v1/auth_me.py`（或加進 `auth.py` — Day 1 三-prong 後定；傾向加進 `auth.py` 同 router）— `GET /auth/me` + `POST /auth/dev-login`
- `backend/src/api/v1/telemetry.py` — `POST /telemetry/frontend` + `POST /telemetry/frontend-error`
- `backend/src/api/_deps.py`（若不存在則新建）或 `tenant_context.py` — `require_tenant_match_or_platform_admin` dependency
- `backend/tests/integration/api/test_auth_me.py` / `test_dev_login.py` / `test_admin_cross_tenant.py` / `test_telemetry_frontend.py` / `test_api_smoke.py`

### MODIFIED Backend
- `backend/src/platform_layer/middleware/tenant_context.py` — cookie fallback + public-path allowlist 確認 + `require_tenant_match_or_platform_admin`
- `backend/src/api/v1/auth.py` — `/me` + `/dev-login` endpoints + `/callback` final_redirect 改導 frontend `/auth/callback?next=`
- `backend/src/api/main.py` — register telemetry router
- `backend/src/api/v1/admin/{tenants,cost_summary,sla_reports}.py` — 套 `require_tenant_match_or_platform_admin` 在 `{tenant_id}` path endpoints
- `backend/src/core/config/__init__.py` — `oidc_redirect_uri` default → backend port；確認有 `env` / 新增 `cookie_secure: bool = False`（prod True）
- `.env.example`（root + `backend/.env.example` if exists）— WORKOS_* / OIDC_REDIRECT_URI / VITE_SENTRY_DSN

### NEW Frontend
- `frontend/src/features/auth/store/authStore.ts`
- `frontend/src/lib/{toast.ts, queryClient.ts, observability.ts}`
- `frontend/src/components/ui/{skeleton,empty-state,error-retry,card,button,badge,dialog,dropdown-menu,index}.tsx`
- `frontend/src/i18n/{index.ts, locales/en/{common,auth}.json, locales/zh-TW/{common,auth}.json}`
- `frontend/lighthouserc.js`
- `.github/workflows/frontend-lighthouse.yml`
- `frontend/.gitattributes`（`*.png binary`）— 或 repo root `.gitattributes` 補一行
- `frontend/tests/unit/auth/{authStore,isAuthenticated}.test.ts`
- `frontend/tests/unit/lib/{toast,queryClient,observability}.test.ts`
- `frontend/tests/unit/components/ui/*.test.tsx`（skeleton/empty-state/error-retry/card/button/badge/dialog/dropdown-menu）
- `frontend/tests/unit/components/UserMenu.test.tsx`
- `frontend/tests/unit/pages/{authGate.test.tsx, auth/login.test.tsx, auth/callback.test.tsx}`
- `frontend/tests/unit/i18n/i18n.test.ts`
- `frontend/tests/e2e/auth/{auth-flow,four-page-gate,dev-login}.spec.ts`
- `frontend/tests/e2e/toast/toast.spec.ts`
- `frontend/tests/e2e/i18n/locale-switch.spec.ts`
- `frontend/tests/e2e/a11y/a11y-scan.spec.ts`
- `frontend/tests/e2e/visual/visual-regression.spec.ts` + `-snapshots/*.png`
- `frontend/tests/e2e/connectivity/connectivity.spec.ts`

### MODIFIED Frontend
- `frontend/src/App.tsx` — `<AuthBootstrap>` wrapper + `<Toaster>` + use shared `queryClient` + auth routes 確認 AuthShell
- `frontend/src/main.tsx` — `initObservability()` + `reportWebVitals()` + `import "./i18n"`
- `frontend/src/features/auth/services/authService.ts` — `fetchAuthMe()` + `isAuthenticated()` 改 authStore + 401 → toast + clear + redirect
- `frontend/src/pages/auth/login/index.tsx` + `callback/index.tsx` — 重寫（AuthShell + Card + Button + EmptyState + DevLoginSection）
- `frontend/src/components/{AppErrorBoundary,UserMenu,AppShellV2,Sidebar}.tsx` — Sentry wire / DropdownMenu / i18n labels
- `frontend/src/pages/{cost-dashboard,sla-dashboard,admin-tenants,tenant-settings}/index.tsx` — auth gate + tenant-from-authStore
- `frontend/src/features/governance/components/DecisionModal.tsx` — 用 `<Dialog>`
- `frontend/src/features/{governance,verification,memory,admin-tenants,cost-dashboard,sla-dashboard}/components/*` — 採用 `<Skeleton>/<EmptyState>/<ErrorRetry>`（消重複）
- 17 個 inline-style 檔案 — Tailwind 化（清單見 US-B9）
- `frontend/eslint.config.js` — `+jsx-a11y`
- `frontend/package.json` — `+@radix-ui/react-dropdown-menu` `+class-variance-authority` `+@sentry/react` `+web-vitals` `+i18next` `+react-i18next` `+i18next-browser-languagedetector` `+i18next-parser`(dev) `+eslint-plugin-jsx-a11y`(dev) `+@axe-core/playwright`(dev) `+@lhci/cli`(dev) + scripts `i18n:extract` / `lhci`
- `frontend/playwright.config.ts` — visual snapshot 設定 / a11y test dir 確認
- `frontend/src/routes.config.ts` — `nameKey` for i18n（或 Sidebar `t()`）

### Doc syncs
- in-sprint: `frontend/CONVENTION.md`（5 addenda）/ `frontend/STYLE.md`（design-system）/ `16-frontend-design.md`（Foundation complete）/ `.claude/rules/sprint-workflow.md`（calibration +1 row）/ `.claude/rules/frontend-react.md`（如需補 inline-style 禁止）/ `claudedocs/1-planning/enterprise-saas-gap-analysis-20260508.md` §0.4（Foundation 1/N → done）
- post-merge: `CLAUDE.md` / `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md`

---

## Acceptance Criteria

### Functional
- [ ] (A1) 未登入開 auth-gated 頁面 → 彈 /auth/login；登入後 → 回原頁；reload 仍 authenticated（cookie）。`GET /auth/me` 回正確 payload；無 cookie → 401。`tenant_context` middleware 接受 cookie JWT。
- [ ] (A2) cost / sla / admin-tenants / tenant-settings 4 頁皆 auth-gated；tenant_id 來自 authStore（非 URL）；admin-tenants 無 platform_admin role 顯示 EmptyState 而非白屏。
- [ ] (A3) 一般 admin 帶 tenant A JWT 打 `/admin/tenants/{B}/cost-summary` → 403；platform_admin 打任何 tenant → 200。
- [ ] (A4) dev：`POST /auth/dev-login?tenant_code=dev` → 200 + cookie + roles 含 platform_admin；prod（env=prod）→ 404。`/auth/login` DEV 模式顯示 DevLoginSection；prod build 不顯示。
- [ ] (A5) `pytest test_api_smoke.py` green（每 router 代表 GET 非 5xx/401）；`.env.example` 含 WORKOS_* / OIDC_REDIRECT_URI / VITE_SENTRY_DSN。
- [ ] (B1) API mutation 失敗 → 看到 toast；`<Toaster>` 掛在 App；shared `queryClient`。
- [ ] (B2) `components/ui/` 有 Skeleton/EmptyState/ErrorRetry/Card/Button/Badge；governance/verification/memory/admin-tenants/cost/sla 至少各 1 處 copy-paste 區塊已換成共用組件；ErrorRetry retryClicked StrictMode-safe。
- [ ] (B3) `components/ui/` 有 Dialog/DropdownMenu（Radix-based）；DecisionModal 用 Dialog 且 approval flow 4/4 e2e 通過；UserMenu 用 DropdownMenu 顯示 authStore.user。
- [ ] (B4) `VITE_SENTRY_DSN` 設 → Sentry init；不設 → no-op（零 runtime 影響）。Web Vitals POST 到 `/api/v1/telemetry/frontend` → Cat 12 metric。AppErrorBoundary onError → reportError（取代 placeholder）。
- [ ] (B5) i18next 骨架 + en/zh-TW `common`+`auth` namespace；UserMenu locale switcher 切繁中 → sidebar nav label 變繁中 + reload 後仍繁中；CONVENTION.md §i18n。
- [ ] (B6) `npm run lint` 含 jsx-a11y 且 silent（violations 全修）；`a11y-scan.spec.ts` 對 ≥ 11 頁 axe scan 0 critical/serious。
- [ ] (B7) `npm run build && npx lhci autorun` 本地跑通；`.github/workflows/frontend-lighthouse.yml` 存在（continue-on-error）。
- [ ] (B8) `visual-regression.spec.ts` ≥ 6 截圖有 baseline；CI 跑 visual（chromium）。
- [ ] (B9) `frontend/src` 無 `style={{` 殘留（lint/test 確認）；login/callback 用 AuthShell + 設計系統組件；UserMenu 顯示真實 user。

### Non-functional
- pytest baseline 1654 → +25-35（新 backend tests）；mypy --strict 0/N；9 V2 lints 9/9；Vitest 168 → +50-70；Playwright 37 → +20-30；Vite build 成功（main bundle size noted，預期 ↑，列 retrospective Q3 + 視需要 code-split）；ESLint silent（含 jsx-a11y）；backend black+isort+flake8 clean；LLM SDK leak 0。
- 9 個 active 頁面 + auth pages 全部 render 無 console error（connectivity spec opt-in 驗證）。

### Sprint workflow discipline
- Phase README（無需，沿用 phase-57-frontend-saas）→ plan（本檔）→ checklist → Day 0 三-prong → code（Day 1-9）→ 每 day update checklist + progress.md → retrospective → PR。
- 三-prong（Day 0）：Prong 1 path verify（所有 NEW/MODIFIED 路徑）+ Prong 2 content verify（middleware allowlist / JWTManager API / RBACManager / Settings 欄位 / admin endpoint signatures / authService 現況 / vite port）+ Prong 3 schema verify（dev-login 是否需 migration — 預期不需，用既有 users/tenants/roles 表）。

### V2 紀律 9 項 self-check（each commit + PR）
1. Server-Side First — auth flow / tenant resolution / RLS 全 server-side；前端純 presentation
2. LLM Provider Neutrality — N/A（不碰 agent_harness）；workos/sentry 非 LLM SDK
3. CC Reference 不照搬 — N/A
4. 17.md Single-source — NEW `/auth/me` `/auth/dev-login` `/telemetry/frontend*` 登記 17.md（或標 owner）；0 NEW agent-harness contract/ABC/LoopEvent/migration
5. 11+1 範疇 — 本 sprint 主要在 platform_layer (identity/middleware) + api/v1 + frontend；Cat 12 (telemetry endpoint forward)；無跨範疇雜湊
6. 04 anti-patterns — AP-2 no orphan（NEW endpoints 都 wired + 有 consumer）/ AP-3 no scattering（設計系統組件集中 components/ui/，消頁面 copy-paste）/ AP-4 no Potemkin（每 NEW 組件有 test + 被現有頁面採用）/ AP-6 YAGNI（不裝 shadcn CLI、Lighthouse/visual 先 baseline 不 gate）
7. Sprint workflow — plan→checklist→三-prong→code→progress→retro，無跳步
8. File header convention — 所有 NEW 檔有 header + Category + MHist 1-line max
9. Multi-tenant rule — `/auth/me` `/auth/dev-login` 明確 tenant；4 頁 tenant-from-session；admin cross-tenant 檢查；RLS 確認

---

## Deliverables (checklist mapping)

- [ ] US-A1: cookie-fallback middleware + GET /auth/me + authStore + bootstrap + callback rewire + oidc_redirect_uri fix + tests
- [ ] US-A2: 4-page auth gate + tenant-from-authStore + tests
- [ ] US-A3: require_tenant_match_or_platform_admin + admin endpoints + tests
- [ ] US-A4: POST /auth/dev-login + login-page DevLoginSection + tests
- [ ] US-A5: test_api_smoke.py + connectivity.spec.ts(opt-in) + .env.example + setup doc
- [ ] US-B1: <Toaster> + lib/toast.ts + lib/queryClient.ts + fetchWithAuth/QueryClient onError + tests
- [ ] US-B2: components/ui/{skeleton,empty-state,error-retry,card,button,badge} + refactor 6 feature areas + tests
- [ ] US-B3: components/ui/{dialog,dropdown-menu} + DecisionModal→Dialog + UserMenu→DropdownMenu + tests
- [ ] US-B4: @sentry/react + web-vitals + lib/observability.ts + AppErrorBoundary wire + backend telemetry router + tests
- [ ] US-B5: i18next + react-i18next + i18n/ bundles + shell/usermenu/auth/2 feature pages adopt + locale switcher + extraction script + tests
- [ ] US-B6: jsx-a11y in eslint.config + fix violations + @axe-core/playwright + a11y-scan.spec.ts
- [ ] US-B7: @lhci/cli + lighthouserc.js + frontend-lighthouse.yml
- [ ] US-B8: visual-regression.spec.ts + baselines + .gitattributes + playwright config
- [ ] US-B9: AuthShell login/callback rewrite + UserMenu real user + inline-style sweep 17 files + no-inline-style check
- [ ] US-C1: routes wire(if needed) + full e2e + full validation sweep + retrospective + memory + 6 in-sprint doc syncs + PR (+ 2 deferred post-merge)

---

## Dependencies & Risks

### External dependencies (npm installs)
`@radix-ui/react-dropdown-menu` / `class-variance-authority` / `@sentry/react` / `web-vitals` / `i18next` / `react-i18next` / `i18next-browser-languagedetector` / `i18next-parser`(dev) / `eslint-plugin-jsx-a11y`(dev) / `@axe-core/playwright`(dev) / `@lhci/cli`(dev). 全部成熟 OSS、無 license 問題、無 V2 紀律衝突（非 LLM SDK）。Bundle 影響：sonner(已裝)~3KB / radix-dropdown ~10KB / sentry/react ~25KB(可 lazy) / web-vitals ~2KB / i18next+react-i18next ~25KB / cva ~1KB / a11y/lighthouse 全是 devDep（不進 bundle）。預估 main bundle +50-70KB → 視需要把 Sentry + i18n 做 dynamic import 緩解（列 retrospective Q3 / AD-Bundle-Size 延伸）。

### Risk matrix
| Risk | 機率 | 影響 | 緩解 |
|------|------|------|------|
| cookie-only flow 在 vite dev proxy 下 cross-origin cookie 問題（frontend :3007 ↔ backend :8000 不同 port） | 中 | 高（auth 跑不通）| Day 1 三-prong 先驗：vite proxy `/api` → :8000 同 origin 嗎？若 cookie 因 port 差被擋 → 改用 vite proxy 也轉 `/auth/callback`（非 `/api` path）+ `OIDC_REDIRECT_URI` 指向 frontend port 經 proxy 回 backend。最壞 fallback：dev 用 dev-login（不經 WorkOS redirect，直接同 origin POST），WorkOS redirect flow 留 staging/prod 驗 |
| middleware public-path allowlist 漏掉 `/auth/me`(需 JWT 但 401 不該是 redirect loop) / `/auth/dev-login`(不需 JWT) / `/telemetry/*`(不需 JWT) | 中 | 高 | Day 1 三-prong grep 現有 allowlist；`/auth/me` 是「需 JWT 但回 401 非異常」——middleware 對它正常運作即可（401 是預期）；`/auth/dev-login` + `/telemetry/*` 必須 allowlist |
| 17 個 inline-style 檔案 Tailwind 化引入視覺 regression | 中 | 中 | visual-regression.spec.ts（US-B8）先建 baseline，再做 inline cleanup（US-B9 在 Day 9，B8 也 Day 9 但先 B8 baseline 後 B9 cleanup → diff 抓到改壞）；每改一檔跑該檔 Vitest |
| Lighthouse CI 對 SPA client-routed 頁不易跑（staticDistDir 只有 index.html）| 中 | 低（continue-on-error）| Day 7 三-prong 試 `startServerCommand: npm run preview` + `url: [/, /cost-dashboard, ...]`；跑不通就只測 `/`（首頁）先 baseline |
| visual snapshot 跨 OS（本地 Windows vs CI Linux）渲染差異 → 一直 fail | 中 | 中 | baseline 只在 CI(Linux) 產；本地 visual spec `test.skip(process.platform !== 'linux' && !process.env.CI)`；文件註明 |
| sprint 太大（15 USs / 10 days）→ scope creep / 跑不完 | 高 | 中 | Day 0 plan 已切清楚每 US；若中途發現某 US 超估 → 該 US 內 minimal-viable（如 i18n 只做 common namespace、visual 只做 3 頁），但**不刪 US**（per sacred rule，未做標 🚧 + reason 留 carryover AD）；user 已知這是大 sprint |
| bundle size 漲太多（>350KB main）| 中 | 中 | Sentry + i18n dynamic import；retrospective Q3 量化 + 視需要起 follow-up optimization sprint |

### Roll-back plan
- 每 US 一個或多個 commit；若某 US 出問題可單獨 revert（feature branch）。
- Auth flow 改動（US-A1）是最關鍵——若 cookie-only 在 dev 跑不通，fallback：保留現有 Bearer-header flow + dev-login 直接寫 localStorage（不靠 cookie），`/auth/me` 接受 Bearer header；WorkOS 真實 redirect flow 標 carryover「需 staging 環境驗證」。即「連接打通」的核心（dev 能登入導覽各頁）仍達成，只是 WorkOS prod flow 延後。
- 整個 branch 在 PR 前都可 reset；merge 後若有問題開 hotfix PR。

---

## Workload (calibrated)

### Bottom-up estimate by US
| US | 估計 | 備註 |
|----|------|------|
| A1 | 5-6 hr | 最大單一 US — middleware + /auth/me + authStore + bootstrap + callback rewire + 9 頁 gate 改 + tests |
| A2 | 3-4 hr | 4 頁 gate + tenant-from-store + tests |
| A3 | 2-3 hr | dependency + 3 admin files + tests |
| A4 | 2-3 hr | dev-login endpoint + login-page section + tests |
| A5 | 2-3 hr | smoke test + connectivity spec + .env.example + doc |
| B1 | 2-3 hr | Toaster + toast lib + queryClient + onError wire + tests |
| B2 | 5-6 hr | 6 個 ui 組件 + refactor 6 feature areas + ≥12 tests |
| B3 | 3-4 hr | 2 個 Radix 組件 + DecisionModal + UserMenu refactor + tests |
| B4 | 3-4 hr | Sentry + web-vitals + observability lib + AppErrorBoundary + backend telemetry router + tests |
| B5 | 4-5 hr | i18next setup + 2 namespace bundles + shell/usermenu/auth/2-page adopt + locale switcher + extraction + tests |
| B6 | 2-3 hr | jsx-a11y config + fix violations + axe-core spec ≥11 pages |
| B7 | 2-3 hr | lhci + lighthouserc + workflow |
| B8 | 2-3 hr | visual spec + baselines + gitattributes + config |
| B9 | 4-5 hr | login/callback rewrite + UserMenu + 17-file inline cleanup + check |
| C1 | 3-4 hr | full e2e + validation sweep + retrospective + memory + 6 doc syncs + PR |
| **Bottom-up total** | **~49-65 hr** | |

### Calibrated commit
Class `frontend-foundation-spike` HYBRID 0.50 (1st application) → **49-65 hr × 0.50 ≈ 25-32 hr** committed. Day 0-9（10 days）。Day 4 retrospective Q2 驗 ratio；若 |delta| > 30% → 記 AD-Sprint-Plan-N。

> **這是大 sprint** — 比平常 5-day sprint 大 ~2x。User 2026-05-10 明確要求「完全集中、不簡化」，故不切分。若 user 後續要切，建議切點：A1-A5+B1+B9 為 57.13a（auth 打通 + 設計系統 + AuthShell），B2-B8 為 57.13b（組件層 refactor 採用 + 觀測 + i18n + a11y + CI + visual）。
