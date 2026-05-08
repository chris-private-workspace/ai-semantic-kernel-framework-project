# Sprint 57.7 — IAM Foundation + Frontend Foundation 1/N spike (Tier 0 Block A + B)

> **Sprint Type**: Phase 57+ sixth sprint — **IAM Auth + Frontend Foundation spike** (Tier 0 Block A + B 第一波 per `claudedocs/1-planning/enterprise-saas-gap-analysis-20260508.md` §6 adjusted roadmap);Hosted IAM vendor route (per user 2026-05-08 decision);primary deliverable = OIDC PKCE working with 1 IdP (Entra) + DB-backed RBAC + Frontend foundation install + 1 page migrate + Day 4 design note `20-iam-deep-dive.md` (8-Point Quality Gate verified ratio ≥ 95%);secondary deliverable = AD-Reality 3a sessions/tool_calls observer wire (using US-A2 抽出的 user_id JWT extraction infra)
> **Owner Categories**: §Platform Layer (`platform_layer/identity/jwt.py` + `auth.py` + new `oidc.py` for OIDC PKCE + `rbac.py` for DB-backed RBAC) + §API Layer (new `api/v1/auth.py` router with login/callback/logout endpoints) + §Frontend Foundation (`frontend/package.json` Tailwind 4 + shadcn/ui + TanStack Query + RHF + Zod + react-error-boundary + Sonner install + `frontend/src/components/AppShell` layout + `frontend/src/pages/auth/{login,callback}` net-new + 1 ship page migrate) + §Cat 12 Observability (chat router 4-stream sessions+tool_calls observer wire — closes AD-Reality-3a per Sprint 57.6 deferred)
> **Phase**: 57 (Frontend SaaS — 6/N sprint;Phase 57+ Frontend SaaS counter advances 3/N → 4/N because B3 page migrate counts as frontend ship)
> **Workload**: 5 days (Day 0-4); bottom-up est ~25-33 hr (7 USs across IAM 3 + Frontend 3 + Reality 1 + Day 4 closeout extract) → calibrated commit **~15-20 hr** (HYBRID multiplier weighted blend ~0.60: IAM `mixed-greenfield` 0.60 + Frontend `medium-frontend` 0.65 + Reality `reality-gap-fix` 0.50;FIRST hybrid application — no precedent;1-data-point baseline opens for AD-Sprint-Plan-9 NEW class proposal `iam-frontend-spike` post-sprint)
> **Branch**: `feature/sprint-57-7-iam-frontend-foundation`
> **Plan Authority**: This document (per CLAUDE.md §Sprint Execution Workflow + sprint-workflow.md §Step 1)
> **Roadmap Source**: gap-analysis §6 adjusted roadmap 2026-05-08 (取消原 Phase 58.0 doc sprint;改為每個 spike sprint Day 4 closeout 抽 design note);user 2026-05-08 4 decisions locked: IAM 三項核心 only (SAML/MFA/Refresh deferred 58+) / Hosted vendor route (4-vendor matrix US-A1 → chosen vendor US-A2) / Frontend Block B + 1 page migrate / Day 4 only `20-iam-deep-dive.md` (Frontend doc 留 Phase 58.2+ extract)
> **AD logging (sub-scope)**: Closes AD-Reality-3a (sessions/tool_calls observer — using US-A2 user_id JWT extraction infra unblock per Sprint 57.6 Day 2 探勘 finding) + AD-Sprint-Plan-7 second data point (`reality-check` 0.85 baseline pending 2-3 sprint window — NOT applicable this sprint type) + opens AD-Sprint-Plan-9 NEW class proposal `iam-frontend-spike` (1-data-point baseline) + opens AD-IAM-Vendor-Lock-In risk register (Hosted route 後續 cost scale risk)

---

## Sprint Goal

Provide the **first IAM + Frontend Foundation Tier 0 spike** following Sprint 57.6 Reality Gap Fix by:

- **US-A1** (Block A — IAM vendor evaluation): Produce 4-vendor comparison matrix (WorkOS / Clerk / Auth0 / Supabase Auth) covering Cost (per MAU + per connection) / SCIM 2.0 / SAML 2.0 / OIDC PKCE / SDK quality (Python backend + React frontend) / SOC 2 Type II inheritance / vendor lock-in / migration off-ramp;output decision recommendation with 4 distinct rejection rationales (NOT「best practice」hand-wave)
- **US-A2** (Block A — OIDC PKCE wire with chosen vendor): Install chosen vendor SDK + connect 1 IdP (recommend Microsoft Entra ID per CLAUDE.md target market);wire backend `/api/v1/auth/{login,callback,logout}` 3 endpoints + frontend `/auth/login` + `/auth/callback` 2 routes;JWT issue with RS256 + JWKS validate (vendor manages JWKS endpoint);extract user_id from JWT in chat router → unblocks US-R1
- **US-A3** (Block A — DB-backed RBAC): Replace `auth.py:101+L107+L116` 3 hardcoded frozenset with `roles` + `user_roles` + `role_permissions` SQL lookup;preserve `_require_role()` API surface;1 endpoint demo (recommend extend admin tenants endpoint with per-tenant custom role check);per-tenant role isolation via tenant_id RLS
- **US-B1** (Block B — Frontend foundation install): Install `tailwindcss@4` + `@tailwindcss/postcss` + shadcn/ui CLI + initialize 5 base components (Button / Input / Card / Toast / Dialog) + `@tanstack/react-query@5` + `react-hook-form@7` + `zod@3` + `react-error-boundary@4` + `sonner@1` + Tailwind config + PostCSS config + shadcn `components.json`
- **US-B2** (Block B — AppShell + ErrorBoundary): NEW `frontend/src/components/AppShell.tsx` with header / nav / main / footer slot pattern + Light/Dark theme provider via Tailwind class strategy + Top-level `<ErrorBoundary fallback={...}>` wrapping all routes + Suspense boundary for lazy-loaded pages + Sonner `<Toaster />` mount
- **US-B3** (Block B — 1 ship page migrate): Migrate **cost-dashboard** (selected per smallest scope + already proven SSE/dashboard pattern) from inline `style={{}}` to AppShell + Tailwind classes + replace ad-hoc fetch with TanStack Query `useQuery({ queryKey: ['cost-summary', tenantId], ... })` to prove pattern reusability;preserve all existing 4 Vitest unit tests + 1 Playwright e2e (regression sentinel)
- **US-R1** (AD-Reality 3a — sessions/tool_calls observer wire): With user_id JWT extraction infra from US-A2, wire chat router LoopStarted observer → `SessionRepository.create_session(user_id, tenant_id)` INSERT to `sessions` table;wire ToolCallExecuted observer → `ToolCallRepository.create()` INSERT to `tool_calls` table;follows Sprint 57.6 best-effort try/except pattern;3-5 unit tests covering happy path + auth-missing graceful fallback + duplicate session prevention
- **Day 4 closeout add-on**:
  - Extract `docs/03-implementation/agent-harness-planning/20-iam-deep-dive.md` design note per `claudedocs/templates/spike-design-note-template.md` 8-Point Quality Gate (verified ratio ≥ 95%): vendor decision matrix + verified invariants (OIDC PKCE flow with file:line + RS256/JWKS validation with file:line + DB-backed RBAC SQL with file:line) + open invariants deferred (SAML 2.0 / MFA / Refresh rotation / SCIM provisioning) + rollback path + 17.md cross-reference
  - SITUATION-V2 §9 milestones add Sprint 57.7 entry with dual scoring (code-level + runtime-level)
  - CLAUDE.md sync (Latest Sprint 57.6 → 57.7 / main HEAD / Last Updated / Current Phase)
  - sprint-workflow.md §Workload Calibration matrix add `iam-frontend-spike` HYBRID class baseline 0.60 (1-data-point;pending 2-3 sprint validation per AD-Sprint-Plan-9)

Sprint 結束後:
- (a) **Vendor evaluation matrix completed** — 4-vendor 比較有 chosen vendor + 3 rejection rationale + cost projection 1 year @ 1000 tenants × 5 MAU
- (b) **OIDC PKCE flow works end-to-end with Entra ID** — `curl POST /api/v1/auth/login` → vendor SDK redirect → real Entra login → callback → JWT issued + decoded + RBAC enforced
- (c) **DB-backed RBAC enforced** — at least 1 endpoint (recommend admin tenants list) uses real DB role lookup;test verifies per-tenant role isolation
- (d) **Frontend foundation working** — `npm run build` Vite produces valid bundle with Tailwind utility classes + shadcn Button rendered + TanStack Query DevTools accessible in dev mode
- (e) **1 page migrated** — cost-dashboard renders inside AppShell with Tailwind styling + TanStack Query fetches cost-summary;5 existing tests still green + 2-3 NEW Vitest unit tests for AppShell + 1 Playwright e2e regression
- (f) **AD-Reality 3a closed** — chat session post-completion `sessions` table ≥ 1 row + `tool_calls` table ≥ 0 rows (≥ 1 if tool calls executed);3-5 unit tests cover observer wiring
- (g) **Design note `20-iam-deep-dive.md` published** — 8-Point Quality Gate self-checked + reviewer (user) approved + verified ratio ≥ 95% claim self-validated
- (h) **Documentation sync** — SITUATION-V2 + CLAUDE.md + sprint-workflow.md committed

**主流量驗收標準**:
- ✅ `python scripts/dev.py start` succeeds + frontend ↔ backend talk + can navigate `/auth/login` → vendor redirect → real Entra login → callback returns to `/auth/callback` → JWT stored + redirected to `/cost-dashboard`
- ✅ JWT extracted in chat router → `sessions.user_id` populated correctly
- ✅ `psql -c "SELECT count(*) FROM sessions WHERE user_id IS NOT NULL"` ≥ 1 after 1 chat session post-login
- ✅ `psql -c "SELECT count(*) FROM tool_calls"` ≥ 0 (≥ 1 if test triggers tool execution)
- ✅ `python -m pytest backend/tests/ -q` → ≥ +18 NEW tests (US-A2 6 + US-A3 4 + US-R1 5 + edge cases 3) → 1602 → ≥ 1620
- ✅ `cd frontend && npm run test` Vitest → ≥ +5 NEW tests (US-B2 AppShell 3 + US-B3 cost-dashboard migrated 2) → 35 → ≥ 40
- ✅ `cd frontend && npm run e2e` Playwright → ≥ +2 NEW e2e (US-A2 login flow happy path + US-B3 cost-dashboard regression) → 23 → ≥ 25
- ✅ `python scripts/lint/run_all.py` → 9/9 V2 lints green (NO regress)
- ✅ `grep -rn "import openai\|import anthropic" backend/src/agent_harness/ backend/src/platform_layer/identity/` → 0 (LLM neutrality preserved)
- ✅ `20-iam-deep-dive.md` exists at `docs/03-implementation/agent-harness-planning/` + 8-Point Quality Gate self-check pass

---

## Background

### V2 進度 (2026-05-09 IAM + Frontend Foundation 起點)

- **22/22 sprints (100%) main progress completed** + **Phase 56-58 SaaS Stage 1 3/3 ✅ CLOSED** + **Phase 57+ Frontend SaaS 3/N completed** (57.1 v2 + 57.3 + 57.4) + **Sprint 57.5 V2 Reality Check ✅ COMPLETE** + **Sprint 57.6 Reality Gap Fix ✅ COMPLETE** (PR #114 + #115)
- main HEAD: `d485b42d` (Sprint 57.6 closeout doc PR #115;newer than CLAUDE.md memory recorded `799ce14e`) — Day 0 ✅ verified
- pytest baseline 1602 / mypy --strict 0/295 source files / **9 V2 lints 9/9 green** (含 Sprint 57.6 NEW check_ap4_frontend_placeholder.py) / LLM SDK leak 0
- Vitest baseline 35 / Playwright e2e baseline 23
- Vite build 75 modules / 209.11 kB
- **17 cumulative D-findings** from Sprint 57.6 (11 Day 0 + 1 Day 1 + 3 Day 2 + 3 Day 3) + 28 D-findings from 57.5 = 45 cumulative
- **Dual scoring framework adopted** (Sprint 57.5 introduced + Sprint 57.6 SITUATION-V2 §9 enforced): code-level + runtime-level dual entries every future sprint

### 為什麼 Phase 57.7 是 IAM + Frontend Foundation spike (not feature work)

Per gap-analysis 2026-05-08 8-sub-agent audit + user 2026-05-08 decisions:

1. **V2 對業界 SaaS baseline 整體 ~30-40% 覆蓋率** (gap-analysis §0.1) — agent harness 11+1 範疇核心 ★★★★ (Cat 9 PII L5 / Audit Merkle / Cat 12 telemetry) 業界領先;**外圍 SaaS 商業化能力(IAM / DevOps生產化 / SRE / SOC 2 / Analytics / Public API / Commerce)約 30-40% baseline**
2. **Auth 是所有 SaaS 商業化的源頭瓶頸** (gap-analysis §2.1) — Auth 缺 → 無 demo 路徑給非 admin 用戶 → 4 ship pages (cost / SLA / tenant-settings / admin-tenants) 假設 token 自動存在 → AD-Reality-3a sessions infra block by missing user_id JWT extraction
3. **Frontend foundation 規劃 vs 實作 17/20 RED** (gap-analysis §1.1) — `16-frontend-design.md` 規劃 shadcn/ui + Tailwind + TanStack Query + RHF/Zod + i18next + axe-core,**全部沒裝**;後續每頁重造輪子 cost 高
4. **Buy-vs-Build IAM 偏向 Buy** (gap-analysis §5) — 自建 14 條 Tier 0+1 capability ~15-25 sprint (比 Phase 56-58 SaaS Stage 1 backend 整體還大);Hosted vendor 1-2 sprint 達 Tier 0 + Tier 1 大部分;V2 核心差異化是 agent harness 不是 IAM
5. **Doc-level rolling discipline 2026-05-08 強制** (CLAUDE.md §⛔ 禁止反模式 + sprint-workflow.md §Step 5.5) — 不預寫多份新規劃文件;每個 spike sprint Day 4 closeout 必須抽 1 份 design note (8-Point Quality Gate verified ratio ≥ 95%)

**IAM + Frontend Foundation Spike 性質區分**:
- 不是 reality check sprint (Sprint 57.5 已做)
- 不是 reality gap fix sprint (Sprint 57.6 已做;但 US-R1 含 1 個 fix as side-effect of US-A2)
- 不是 audit cycle bundle (audit cycle fold-in process AD;此 sprint 是 spike 探索)
- **是 spike sprint** — 主要 deliverable 是 IAM Tier 0 三項核心能力 verified + Frontend foundation install + Day 4 design note extract per 8-Point Quality Gate

### 既有結構 (Day 0 三-prong 探勘 v1 完成)

✅ **D-GREEN baseline confirmed**:

```
backend/src/platform_layer/identity/
├── __init__.py
├── jwt.py                      # ✅ JWTManager class L103 + encode L133 + decode L172 + verify L191
└── auth.py                     # ⚠️ 3× hardcoded frozenset RBAC at L101/L107/L116

backend/src/infrastructure/db/models/
├── identity.py                 # ✅ 4 ORM tables: User L158 + Role L202 + UserRole L233 + RolePermission L264
└── api_keys.py                 # ✅ ApiKey L70

backend/src/infrastructure/db/migrations/versions/
├── 0001_initial_identity.py    # ✅ users + roles + user_roles + role_permissions baseline
├── 0006_api_keys_rate_limits.py
└── ... (14 more migrations through 0016)
```

⚠️ **D-RED gaps identified — Phase 57.7 scope addresses**:

```
backend/src/api/v1/
└── (NO auth.py)                # ❌ US-A2 will create with login/callback/logout 3 endpoints

frontend/src/pages/
├── chat-v2/                    # 7 existing pages (chat-v2 / verification / governance / ...)
└── (NO auth/)                  # ❌ US-A2 will add login + callback routes

frontend/package.json
└── React 18 + Vite 5 + Zustand only  # ❌ US-B1 install Tailwind 4 + shadcn/ui + TanStack Query + RHF + Zod + Sonner + react-error-boundary
```

⏳ **D-DEFER-Day-1 schema verify** — column-level drift on `users` table for OIDC `external_id` field (TBD;may trigger Alembic 0017 migration scope addition ~1-2 hr)

### V2 紀律 9 項對齊確認

1. **Server-Side First** ✅ — IAM enforce on backend (JWT validate / RBAC SQL query);frontend 只 hold token + UI render
2. **LLM Provider Neutrality** ✅ — 此 sprint 不動 LLM 鏈路;US-A2 vendor SDK install 限制在 `platform_layer/identity/oidc.py` 不污染 agent_harness/
3. **CC Reference 不照搬** ✅ — IAM 自 Hosted vendor SaaS 借力,non-CC pattern
4. **17.md Single-source** ✅ — US-A2 NEW endpoints 屬 §API Layer;NEW classes (`OIDCFlow`, `RBACManager`) 屬 §Platform Layer;NO new cross-category contract added (auth flow 是 standalone vertical)
5. **11+1 範疇歸屬** ✅ — `platform_layer/identity/` 已 own;Frontend Foundation 是 §Frontend Layer;US-R1 改 chat router 屬 §Cat 12 Observability cross-cutting
6. **04 anti-patterns** ✅✅ — AP-2 (Side-track): vendor matrix US-A1 必有 3 rejection rationale + decision (NOT「best practice」hand-wave);AP-4 (Potemkin): US-A2 OIDC flow必須 working end-to-end with real Entra (NOT placeholder);AP-9 (Verification): Day 4 design note 8-Point Quality Gate enforces verified ratio ≥ 95%;AP-11 (No version suffix): 不 introduce `_v1` suffix
7. **Sprint workflow** ✅ — plan → checklist → Day 0 三-prong → Day 1-4 → progress + retro;本文件鏡射 57.6 plan 結構 (10 sections + metadata block;7 USs;Day 0-4 structure)
8. **File header convention** ✅ — 此 sprint 寫 substantial source code + frontend + 1 design note;全加 file header per convention;MHist entries ≤ 100 chars per E501 budget per AD-Lint-MHist-Verbosity
9. **Multi-tenant rule** ✅ — IAM 鐵律 #1+#2+#3 強化:`users.tenant_id` 必填 / DB-backed RBAC query 必加 `WHERE tenant_id = ?` / `Settings.jwt_secret` per-tenant key rotation deferred 58+

---

## User Stories

### US-A1: Block A — IAM Vendor Evaluation Matrix

**As** the V2 platform engineer
**I want** a 4-vendor comparison matrix (WorkOS / Clerk / Auth0 / Supabase Auth) with explicit chosen vendor + 3 rejection rationale + cost projection
**So that** Phase 57.7 US-A2 wire path is informed by Buy-vs-Build evidence (per gap-analysis §5) NOT「best practice」hand-wave

**Acceptance Criteria**:
- [ ] 4-row matrix table covering: Cost (per MAU + per connection) / SCIM 2.0 / SAML 2.0 / OIDC PKCE / Python SDK quality / React SDK quality / SOC 2 Type II inheritance / vendor lock-in evaluation / migration off-ramp
- [ ] Cost projection: 1 year @ 1000 tenants × 5 user = 5000 MAU for chosen vendor (USD estimate)
- [ ] 3 rejection rationale (specific reasons for non-chosen vendors)
- [ ] Decision rationale for chosen vendor (specific to V2 enterprise B2B target market;Taiwan/HK/EU optional)
- [ ] Migration off-ramp: 「if we want to leave this vendor in 2 years, what does it take」documented

**Day 4 design note section**: §1 Decision Matrix (8-Point Quality Gate #3 satisfied)

### US-A2: Block A — OIDC PKCE Flow with Chosen Vendor + 1 IdP (Entra)

**As** the V2 platform engineer
**I want** a working OIDC PKCE login flow via chosen vendor SDK + Microsoft Entra ID IdP
**So that** non-admin users can demo V2 + 4 ship pages have real authenticated sessions + AD-Reality-3a observer can extract user_id

**Acceptance Criteria**:
- [ ] Chosen vendor SDK installed (`backend/requirements.txt` add 1 dep + `frontend/package.json` add 1 dep)
- [ ] Backend `api/v1/auth.py` NEW router with 3 endpoints:
  - `GET /api/v1/auth/login?redirect_uri=...` → vendor SDK redirect to Entra
  - `GET /api/v1/auth/callback?code=...&state=...` → vendor SDK exchange + JWT issue
  - `POST /api/v1/auth/logout` → JWT invalidate + vendor SDK signout redirect
- [ ] Frontend `pages/auth/login/index.tsx` + `pages/auth/callback/index.tsx` 2 routes net-new (using basic React + react-router-dom v6;NOT yet AppShell since US-B2 not done concurrent)
- [ ] JWT issue with RS256 algorithm (asymmetric) + JWKS validation:
  - Vendor's `/.well-known/jwks.json` URL stored in `Settings.jwt_jwks_url`
  - `JWTManager.decode()` extended to fetch JWKS + verify against vendor public key OR vendor SDK provides `decode_with_jwks(token)` helper
  - **OR** if chosen vendor only supports HS256, document trade-off in design note + open invariant for Phase 58+ RS256 wire
- [ ] User upsert on first login: vendor's user_id (subject) → `users.external_id` column lookup;if missing → INSERT new `users` row with tenant_id from JWT custom claim
- [ ] **D-DEFER-Day-1**: if `users.external_id` column missing → Alembic 0017 migration adds VARCHAR(255) UNIQUE column + index
- [ ] 6+ unit tests:
  - 1 happy path login redirect
  - 1 happy path callback exchange + JWT issue
  - 1 happy path logout
  - 1 callback with bad state (CSRF protection)
  - 1 callback with bad code
  - 1 user upsert on first login

**Day 4 design note section**: §2.1 + §2.2 + §2.3 Verified Invariants (OIDC PKCE / RS256+JWKS / user upsert) — each with file:line + verification command (8-Point Quality Gate #2 + #4 satisfied)

### US-A3: Block A — DB-Backed RBAC

**As** the V2 platform engineer
**I want** `auth.py:101+L107+L116` 3 hardcoded frozenset RBAC replaced with `roles` + `user_roles` + `role_permissions` SQL lookup per-tenant
**So that** Tier 0 #5 blocker (gap-analysis §1.2) closed + per-tenant custom roles enabled (e.g. tenant A defines「reviewer」role w/ specific permissions)

**Acceptance Criteria**:
- [ ] NEW `platform_layer/identity/rbac.py` with `RBACManager` class:
  - `async def has_role(user_id: UUID, tenant_id: UUID, role_label: str) -> bool` — SQL JOIN query on user_roles + roles + tenant_id filter
  - `async def has_permission(user_id: UUID, tenant_id: UUID, action: str, resource: str) -> bool` — SQL JOIN on user_roles + role_permissions
- [ ] `auth.py:_require_role()` REWIRE to call `RBACManager.has_role()` instead of frozenset `in` check
- [ ] **Backwards compatible**: 3 helper functions (`require_audit_role` / `require_approver_role` / `require_admin_platform_role`) preserved API surface;internally call `_require_role()` → DB lookup
- [ ] 1 endpoint demo: `GET /api/v1/admin/tenants` (existing) verifies platform_admin role via DB lookup (NOT frozenset);test verifies per-tenant role isolation (admin in tenant A cannot platform_admin tenant B)
- [ ] 4+ unit tests:
  - 1 happy path: user has role → returns True
  - 1 happy path: user lacks role → returns False (raises 403)
  - 1 cross-tenant isolation: user with role in tenant A queried for tenant B → False
  - 1 backwards compat: existing `require_admin_platform_role` dependency still works post-rewire

**Day 4 design note section**: §2.4 Verified Invariant (DB-backed RBAC) — file:line for SQL query + verification command

### US-B1: Block B — Frontend Foundation Install

**As** the frontend engineer
**I want** Tailwind 4 + shadcn/ui CLI + 5 base components + TanStack Query 5 + RHF 7 + Zod 3 + react-error-boundary 4 + Sonner 1 installed and configured
**So that** Block B Foundation 1/N established (per gap-analysis §1.1 17/20 RED) + future pages stop reinventing wheels

**Acceptance Criteria**:
- [ ] `frontend/package.json` adds 8 deps:
  - `tailwindcss@^4.0.0` (dev)
  - `@tailwindcss/postcss` (dev)
  - `@tanstack/react-query@^5.0.0`
  - `@tanstack/react-query-devtools@^5.0.0` (dev)
  - `react-hook-form@^7.0.0`
  - `zod@^3.0.0`
  - `react-error-boundary@^4.0.0`
  - `sonner@^1.0.0`
- [ ] `frontend/tailwind.config.ts` + `frontend/postcss.config.cjs` configured;`src/index.css` adds `@tailwind base; @tailwind components; @tailwind utilities;`
- [ ] shadcn CLI initialized (`npx shadcn-ui@latest init`);`components.json` committed;`src/components/ui/` directory NEW
- [ ] 5 shadcn components added: Button / Input / Card / Toast (Sonner-backed) / Dialog
- [ ] `npm run build` succeeds + Vite bundle size delta < +50% (foundation install should not balloon bundle excessively;Tailwind purges unused)
- [ ] 0 NEW Vitest tests this US (foundation install verified via build success;US-B2 + US-B3 add component tests)

**Day 4 design note section**: NOT covered (Frontend doc deferred to Phase 58.2+ extract per user 2026-05-08 decision)

### US-B2: Block B — AppShell + ErrorBoundary + Theme

**As** the frontend engineer
**I want** a NEW `AppShell` layout component + theme provider + ErrorBoundary 階層 + Suspense boundary
**So that** Block B foundation has proven layout pattern + every page gets consistent header/nav/footer + errors don't whitescreen the app

**Acceptance Criteria**:
- [ ] NEW `frontend/src/components/AppShell.tsx`:
  - Props: `children` (main slot) + optional `headerActions` slot
  - Layout: header (logo + nav + headerActions) / main (children) / footer (copyright + version)
  - Tailwind utility classes (NO inline `style={{}}`)
- [ ] NEW `frontend/src/components/ThemeProvider.tsx`:
  - Light/Dark toggle stored in localStorage
  - Tailwind dark mode class strategy (`html.dark`)
- [ ] NEW `frontend/src/components/AppErrorBoundary.tsx`:
  - Wraps `<Outlet />` in router root
  - Fallback UI: friendly error message + reset button + sentry placeholder (Sentry deferred per user)
- [ ] `frontend/src/main.tsx` wires `<ThemeProvider><AppErrorBoundary><App /></AppErrorBoundary></ThemeProvider>` + `<Toaster richColors />` mount
- [ ] 3+ Vitest tests:
  - 1 AppShell renders children
  - 1 ThemeProvider toggle persists to localStorage
  - 1 ErrorBoundary catches thrown error + renders fallback

### US-B3: Block B — 1 Ship Page Migrate (cost-dashboard)

**As** the frontend engineer
**I want** the existing `cost-dashboard` page migrated from inline `style={{}}` to AppShell + Tailwind + TanStack Query
**So that** Block B foundation pattern is proven on a real page (not just demo) + future migrations have working reference

**Acceptance Criteria**:
- [ ] `frontend/src/pages/cost-dashboard/index.tsx` REFACTOR:
  - Wrap in `<AppShell>...</AppShell>`
  - Replace inline `style={{}}` with Tailwind utility classes
  - Replace ad-hoc `fetch` + `useEffect` data loading with `useQuery({ queryKey: ['cost-summary', tenantId], queryFn: ... })`
  - Use shadcn Card for 6 metric tiles
- [ ] All existing 4 Vitest unit tests still pass (regression sentinel — 0 test deletion per V2 紀律)
- [ ] All existing 1 Playwright e2e still passes (UI text contract preserved)
- [ ] 2+ NEW Vitest unit tests:
  - 1 TanStack Query loading state renders skeleton
  - 1 TanStack Query error state renders fallback
- [ ] **Page migrate counter**: `Phase 57+ Frontend SaaS counter advances 3/N → 4/N` (cost-dashboard now AppShell-compliant;3 remaining ship pages — sla / tenant-settings / admin-tenants — defer to Phase 58.2+ Frontend Pages 11 batch)

### US-R1: AD-Reality 3a — Sessions + Tool_Calls Observer Wire

**As** the V2 platform engineer
**I want** chat router LoopStarted observer → `SessionRepository.create_session(user_id, tenant_id)` INSERT + ToolCallExecuted observer → `ToolCallRepository.create()` INSERT
**So that** AD-Reality-3a (deferred Sprint 57.6 Day 2 探勘 due to missing user_id JWT extraction) is unblocked by US-A2's auth flow

**Acceptance Criteria**:
- [ ] `backend/src/api/v1/chat.py` LoopStarted observer hook calls `SessionRepository.create_session()`:
  - Extract `user_id` from JWT decoded by FastAPI dependency `Depends(get_current_user)` (NEW dep per US-A2)
  - INSERT row to `sessions` table with `(user_id, tenant_id, started_at)`;`Session.user_id` is NOT NULL FK to `users.id`
  - best-effort try/except (per Sprint 57.6 audit_log observer pattern;observer failure 不可 break SSE stream)
- [ ] `backend/src/api/v1/chat.py` ToolCallExecuted observer hook calls `ToolCallRepository.create()`:
  - INSERT row to `tool_calls` table with `(session_id, tool_name, tool_input_preview, status, duration_ms, result_preview)`
  - best-effort try/except
- [ ] 5+ unit tests:
  - 2 LoopStarted observer (happy path INSERT + auth missing graceful skip)
  - 2 ToolCallExecuted observer (happy path INSERT + duplicate skip via session_id+tool_call_id constraint)
  - 1 best-effort: observer raises exception → SSE stream uninterrupted (mock + assert)
- [ ] **AD-Reality-3a closed** (3-5 hr est per Sprint 57.6 Q5 retrospective deferred candidate);**3b/3c/3d still deferred** (deeper observer wiring for guardrail + verification audit;Phase 58+ TBD)

---

## Technical Specifications

### TS-1: IAM Hosted Vendor SDK Selection (constrains US-A1 + US-A2)

**Pre-evaluation context**: gap-analysis §5 Buy-vs-Build matrix recommends「自建 11+1 範疇 agent harness + 買 SaaS 商業化外圍能力」. IAM is non-differentiating for V2 (V2 賣 agent harness 不賣 IAM). Hosted route = ~6-8 hr Phase 57.7 spike vs Self-built ~6-8 hr same sprint but Phase 58+ ~15-25 sprint to reach Tier 0+1.

**4-vendor pre-screen** (US-A1 will deepen + verify):

| Vendor | B2B 強度 | Cost @ 5K MAU/yr | SCIM | SAML | Pre-screen |
|--------|---------|------------------|------|------|-----------|
| **WorkOS** | ★★★★ Best B2B | ~$500-2000/yr per connection | ✅ | ✅ | Strong candidate (Taiwan/HK target market) |
| **Clerk** | ★★ DX strong but PLG-focused | ~$1000-3000/yr (per MAU) | ⚠️ Add-on | ⚠️ Add-on | Mid candidate (frontend SDK best) |
| **Auth0** | ★★★ Mature but expensive | ~$2000-5000/yr (per MAU) | ✅ | ✅ | High cost concern |
| **Supabase Auth** | ★ OSS limited B2B | ~$0 (self-host) - $300/yr (cloud) | ⚠️ Limited | ⚠️ Limited | Low cost but feature-limited |

**US-A2 will commit to chosen vendor based on US-A1 matrix outcome**;recommended pre-bias = **WorkOS** (best B2B + Taiwan/HK enterprise SAML deals later)

### TS-2: OIDC PKCE Flow Sequence

```
1. User clicks "Login with Entra" on /auth/login page
2. Frontend POST GET /api/v1/auth/login?redirect_uri=/cost-dashboard
3. Backend vendor SDK generates state + code_verifier + code_challenge
4. Backend stores (state → code_verifier) in Redis (TTL 10 min) for callback retrieval
5. Backend redirects browser to vendor authorize URL with code_challenge + state
6. Vendor redirects to Entra ID login
7. User authenticates with Entra
8. Entra redirects to vendor callback (vendor SDK manages this)
9. Vendor redirects to V2 backend /api/v1/auth/callback?code=...&state=...
10. Backend retrieves code_verifier by state from Redis
11. Backend vendor SDK exchanges code + code_verifier → JWT (signed by vendor)
12. Backend extracts subject (Entra user_id) from JWT
13. Backend upsert `users` row: lookup by external_id (Entra subject);if missing → INSERT
14. Backend issues V2 JWT with sub=users.id + tenant_id + roles + RS256 signed
15. Backend redirects to frontend redirect_uri with V2 JWT in cookie OR query param
16. Frontend stores JWT in localStorage / sessionStorage / httpOnly cookie (TBD security model in design note)
17. Subsequent requests carry JWT in Authorization: Bearer header
```

### TS-3: DB-Backed RBAC Query Pattern

```sql
-- has_role(user_id, tenant_id, role_label) implementation:
SELECT EXISTS (
  SELECT 1
  FROM user_roles ur
  JOIN roles r ON ur.role_id = r.id
  WHERE ur.user_id = :user_id
    AND r.tenant_id = :tenant_id    -- per-tenant isolation
    AND r.label = :role_label
)
```

```sql
-- has_permission(user_id, tenant_id, action, resource):
SELECT EXISTS (
  SELECT 1
  FROM user_roles ur
  JOIN role_permissions rp ON ur.role_id = rp.role_id
  WHERE ur.user_id = :user_id
    AND ur.tenant_id = :tenant_id    -- via UserRole.tenant_id
    AND rp.action = :action
    AND rp.resource = :resource
)
```

**RLS interaction**: `roles` + `user_roles` + `role_permissions` tables already covered by Sprint 56.1 RLS hardening (Migration 0009);queries WHERE-clauses still pass tenant_id explicitly per `multi-tenant-data.md` 鐵律 #2 belt-and-suspenders.

### TS-4: Frontend Foundation File Layout

```
frontend/
├── tailwind.config.ts          # NEW (US-B1)
├── postcss.config.cjs          # NEW (US-B1)
├── components.json             # NEW (US-B1) — shadcn config
├── src/
│   ├── index.css              # MODIFIED (US-B1) — add @tailwind directives
│   ├── main.tsx               # MODIFIED (US-B2) — wrap in providers
│   ├── components/
│   │   ├── AppShell.tsx       # NEW (US-B2)
│   │   ├── ThemeProvider.tsx  # NEW (US-B2)
│   │   ├── AppErrorBoundary.tsx  # NEW (US-B2)
│   │   └── ui/                # NEW (US-B1) — shadcn-generated
│   │       ├── button.tsx
│   │       ├── input.tsx
│   │       ├── card.tsx
│   │       ├── dialog.tsx
│   │       └── (sonner Toaster wired in main.tsx)
│   └── pages/
│       ├── auth/              # NEW (US-A2)
│       │   ├── login/index.tsx
│       │   └── callback/index.tsx
│       └── cost-dashboard/index.tsx  # MODIFIED (US-B3) — AppShell + Tailwind + useQuery
```

### TS-5: AD-Reality-3a Observer Wire Pattern (extends Sprint 57.6 audit_log pattern)

```python
# Pseudocode for chat.py changes
async def chat_endpoint(..., user: User = Depends(get_current_user)):
    session_id = uuid4()
    try:
        # NEW US-R1: LoopStarted observer
        await session_repository.create_session(
            id=session_id,
            user_id=user.id,         # NEW: extracted from US-A2 JWT
            tenant_id=user.tenant_id,
            started_at=datetime.utcnow(),
        )
    except Exception as exc:
        logger.warning(f"sessions observer failed: {exc}", exc_info=True)
        # best-effort — proceed with chat

    async for event in agent_loop.stream(...):
        if event.type == ToolCallExecuted:
            try:
                # NEW US-R1: ToolCallExecuted observer
                await tool_call_repository.create(
                    session_id=session_id,
                    tool_name=event.tool_name,
                    tool_input_preview=event.input_preview,
                    status=event.status,
                    duration_ms=event.duration_ms,
                    result_preview=event.result_preview,
                )
            except Exception as exc:
                logger.warning(f"tool_calls observer failed: {exc}", exc_info=True)

        yield format_sse(event)
```

---

## File Change List

| Path | Status | Owner US | LOC est |
|------|--------|----------|---------|
| `backend/requirements.txt` | MODIFIED | US-A2 | +1 line (vendor SDK dep) |
| `backend/src/core/config.py` | MODIFIED | US-A2 | +5 lines (Settings: jwt_jwks_url + vendor_api_key + vendor_client_id) |
| `backend/src/platform_layer/identity/oidc.py` | NEW | US-A2 | ~150 lines |
| `backend/src/platform_layer/identity/rbac.py` | NEW | US-A3 | ~120 lines |
| `backend/src/platform_layer/identity/auth.py` | MODIFIED | US-A3 | -30 lines (frozenset removed) +20 lines (RBACManager call) |
| `backend/src/platform_layer/identity/jwt.py` | MODIFIED | US-A2 | +30 lines (JWKS validate path) |
| `backend/src/api/v1/auth.py` | NEW | US-A2 | ~180 lines (3 endpoints) |
| `backend/src/api/v1/chat.py` | MODIFIED | US-R1 | +30 lines (2 observer hooks) |
| `backend/src/infrastructure/db/repositories/session_repository.py` | NEW | US-R1 | ~80 lines |
| `backend/src/infrastructure/db/repositories/tool_call_repository.py` | NEW | US-R1 | ~80 lines |
| `backend/src/infrastructure/db/migrations/versions/0017_users_external_id.py` | NEW (conditional D8) | US-A2 | ~40 lines (if column missing) |
| `backend/tests/unit/platform_layer/identity/test_oidc.py` | NEW | US-A2 | ~120 lines (6 tests) |
| `backend/tests/unit/platform_layer/identity/test_rbac.py` | NEW | US-A3 | ~80 lines (4 tests) |
| `backend/tests/unit/api/v1/test_chat_observer_sessions.py` | NEW | US-R1 | ~120 lines (5 tests) |
| `backend/tests/integration/test_oidc_flow_e2e.py` | NEW | US-A2 | ~80 lines (1 e2e test with mocked vendor) |
| `frontend/package.json` | MODIFIED | US-B1 | +8 deps |
| `frontend/tailwind.config.ts` | NEW | US-B1 | ~30 lines |
| `frontend/postcss.config.cjs` | NEW | US-B1 | ~10 lines |
| `frontend/components.json` | NEW | US-B1 | ~25 lines (shadcn) |
| `frontend/src/index.css` | MODIFIED | US-B1 | +3 lines (@tailwind directives) |
| `frontend/src/main.tsx` | MODIFIED | US-B2 | +10 lines (providers wrap) |
| `frontend/src/components/AppShell.tsx` | NEW | US-B2 | ~80 lines |
| `frontend/src/components/ThemeProvider.tsx` | NEW | US-B2 | ~50 lines |
| `frontend/src/components/AppErrorBoundary.tsx` | NEW | US-B2 | ~40 lines |
| `frontend/src/components/ui/{button,input,card,dialog}.tsx` | NEW | US-B1 | ~200 lines total (shadcn-generated;mostly boilerplate) |
| `frontend/src/pages/auth/login/index.tsx` | NEW | US-A2 | ~60 lines |
| `frontend/src/pages/auth/callback/index.tsx` | NEW | US-A2 | ~70 lines |
| `frontend/src/pages/cost-dashboard/index.tsx` | MODIFIED | US-B3 | rewrite ~200 lines (style → Tailwind + useQuery) |
| `frontend/src/components/__tests__/AppShell.test.tsx` | NEW | US-B2 | ~50 lines (3 tests) |
| `frontend/src/pages/cost-dashboard/__tests__/migrate.test.tsx` | NEW | US-B3 | ~40 lines (2 tests) |
| `frontend/tests/e2e/auth-login-happy-path.spec.ts` | NEW | US-A2 | ~50 lines (1 e2e mocked vendor) |
| `frontend/tests/e2e/cost-dashboard-regression.spec.ts` | NEW | US-B3 | ~30 lines (1 e2e regression) |
| `docs/03-implementation/agent-harness-planning/20-iam-deep-dive.md` | NEW | Day 4 closeout | ~300-500 lines (8-Point Quality Gate) |
| `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md` | MODIFIED | Day 4 closeout | +30 lines (§9 Sprint 57.7 entry + §11 Last Updated) |
| `CLAUDE.md` | MODIFIED | Day 4 closeout | ~+30 lines (Latest Sprint + main HEAD + Last Updated) |
| `.claude/rules/sprint-workflow.md` | MODIFIED | Day 4 closeout | +5 lines (calibration matrix `iam-frontend-spike` 0.60 row) |

**Estimated total LOC delta**: ~+2200 source + ~+650 tests + ~+400 docs ≈ **~+3250 LOC**

---

## Acceptance Criteria

1. ✅ All 7 USs (A1+A2+A3+B1+B2+B3+R1) marked `[x]` in checklist
2. ✅ pytest: 1602 → ≥ 1620 (+18 minimum;US-A2 6 + US-A3 4 + US-R1 5 + edge cases 3)
3. ✅ mypy --strict: 0 errors / 295+ source files (NEW oidc.py + rbac.py + auth.py route + 2 repos add ~7 files → 302+)
4. ✅ V2 lints: 9/9 green (NO regress)
5. ✅ Vitest: 35 → ≥ 40 (+5 minimum)
6. ✅ Playwright e2e: 23 → ≥ 25 (+2 minimum)
7. ✅ Vite build: succeeds + bundle size delta < +50% (foundation install acceptable balloon)
8. ✅ LLM SDK leak: 0 in `agent_harness/` + `platform_layer/identity/`
9. ✅ Manual smoke: full OIDC flow with real Entra works (login → callback → JWT → cost-dashboard render)
10. ✅ DB persist: `sessions` ≥ 1 row + `tool_calls` ≥ 0 rows (≥ 1 if test triggers tool)
11. ✅ Day 4 design note `20-iam-deep-dive.md` published with 8-Point Quality Gate self-check pass
12. ✅ retrospective.md ≥ 250 lines covering Q1-Q6 + calibration ratio Q2

---

## Deliverables (checklist mapping)

- [ ] US-A1: 4-vendor matrix completed + chosen vendor + 3 rejection rationale (Day 1)
- [ ] US-A2: OIDC PKCE flow working with real Entra (Day 1-2)
- [ ] US-A3: DB-backed RBAC + 1 endpoint demo (Day 2)
- [ ] US-B1: Frontend foundation 8 deps installed + Tailwind/shadcn configured (Day 2)
- [ ] US-B2: AppShell + ThemeProvider + AppErrorBoundary + 3 Vitest (Day 2-3)
- [ ] US-B3: cost-dashboard migrate + 2 NEW Vitest + 1 e2e regression (Day 3)
- [ ] US-R1: AD-Reality 3a sessions+tool_calls observer + 5 unit tests (Day 3)
- [ ] Day 4 design note `20-iam-deep-dive.md` (8-Point Quality Gate) + retrospective + memory + sync PR

---

## Dependencies & Risks

### Dependencies

- **External**: Microsoft Entra ID tenant for testing OIDC flow (Day 1 setup;or use vendor's hosted test IdP if available)
- **Internal**: chosen vendor account creation (US-A1 outcome → US-A2 SDK install gating)
- **Internal**: `users.external_id` column verify (D8 deferred to Day 1 morning;may trigger Alembic 0017 ~1-2 hr add)

### Risk Class A — Hosted vendor account provisioning lag

**Symptom**: chosen vendor (likely WorkOS) requires 1-2 day account approval for B2B trial → blocks US-A2 wire on Day 1
**Workaround**: Day 1 morning kick off vendor signup parallel with US-A1 matrix work;if approval lags >1 day → fallback to **Self-built lite** (own OIDC PKCE + use `python-jose` + Entra direct OIDC discovery);US-A1 captured both routes
**Long-term**: vendor selection criteria includes「signup approval time」row in matrix

### Risk Class B — Vendor SDK breaks LLM neutrality

**Symptom**: vendor SDK transitively imports `openai` or `anthropic` or hardcoded LLM model name in some helper
**Workaround**: Day 1 grep `pip show <vendor-sdk>` deps + `python -c "import <vendor-sdk>; print(...)"` deps tree;if violation → quarantine import in `platform_layer/identity/oidc.py` only + add `# noqa: AP-2-vendor-isolated` comment
**Long-term**: V2 lint `check_neutrality.py` already enforces;check rejects in CI pre-merge

### Risk Class C — `users.external_id` column drift (Day 0 D8)

**Symptom**: `users` ORM at `identity.py:158` may not have `external_id VARCHAR UNIQUE` column → user upsert pattern in US-A2 fails
**Workaround**: Day 1 morning verify column existence via grep `external_id` in `identity.py`;if missing → `alembic revision --autogenerate` Migration 0017 + `alembic upgrade head` (~30 min add)
**Long-term**: addressed in 0017 migration + design note §3 Cross-Category Contracts

### Risk Class D — Frontend foundation balloon bundle size

**Symptom**: Tailwind 4 + shadcn + TanStack Query + RHF + Zod + Sonner + react-error-boundary install balloons bundle size beyond acceptable budget (target < 350 kB gzipped)
**Workaround**: US-B1 Vite build verifies bundle size delta;if > 50% balloon → adopt Tailwind purge config strict + shadcn tree-shake config;commit to bundle budget in design note
**Long-term**: Lighthouse CI deferred Phase 58.2+ Tier 1 will enforce performance budget gate

### Risk Class E — AppShell + cost-dashboard migrate breaks existing tests

**Symptom**: cost-dashboard migrate to AppShell changes DOM structure → Playwright e2e selectors break (recall Sprint 57.4 D14 strict-mode selector fix)
**Workaround**: US-B3 Day 3 rerun `npm run e2e` after migrate;if selectors break → update e2e selectors via `getByRole` / `getByText` strict + role attributes;**0 test deletion** per V2 紀律
**Long-term**: visual regression testing deferred Phase 58.2+

### Risk Class F — Calibration HYBRID 1st application

**Symptom**: Bottom-up est 25-33 hr × 0.60 blend = ~15-20 hr commit may underestimate IAM vendor SDK integration complexity (no 2-data-point baseline)
**Workaround**: Day 4 retro Q2 measure ratio carefully;if > 1.20 → AD-Sprint-Plan-9 propose lift to 0.75;if < 0.85 → propose lower to 0.50;1-data-point this sprint;need 2-3 sprint window before promotion
**Long-term**: scope-class refinement matrix per AD-Sprint-Plan-4

---

## Workload (calibrated)

| US | Bottom-up (hr) | Calibration class | Multiplier | Calibrated commit (hr) |
|-----|---------------|-------------------|-----------|------------------------|
| US-A1 vendor matrix | 3 | mixed-greenfield | 0.60 | 1.8 |
| US-A2 OIDC wire | 6-8 (avg 7) | mixed-greenfield | 0.60 | 4.2 |
| US-A3 DB-backed RBAC | 3-4 (avg 3.5) | mixed-greenfield | 0.60 | 2.1 |
| US-B1 frontend install | 3-4 (avg 3.5) | medium-frontend | 0.65 | 2.3 |
| US-B2 AppShell + ErrorBoundary | 2-3 (avg 2.5) | medium-frontend | 0.65 | 1.6 |
| US-B3 cost-dashboard migrate | 2-3 (avg 2.5) | medium-frontend | 0.65 | 1.6 |
| US-R1 AD-Reality 3a | 3-5 (avg 4) | reality-gap-fix | 0.50 | 2.0 |
| Day 4 closeout (design note + retro + memory + sync) | 3 | medium-backend | 0.80 | 2.4 |
| **Total** | **~26-33 hr** | **HYBRID weighted** | **~0.60** | **~18 hr commit** |

**Calibration trigger**: `iam-frontend-spike` HYBRID class baseline opens (1-data-point this sprint) → AD-Sprint-Plan-9 NEW;Day 4 retro Q2 verify ratio + decide promote / adjust / hold

**Day budget**:
- Day 0: ~2 hr (探勘 + plan + checklist) ✅ COMPLETE this session
- Day 1: ~5-6 hr (US-A1 vendor matrix + US-A2 backend OIDC wire start + US-A3 DB-backed RBAC start)
- Day 2: ~5-6 hr (US-A2 frontend auth + US-A3 finish + US-B1 frontend install)
- Day 3: ~4-5 hr (US-B2 AppShell + US-B3 migrate + US-R1 sessions/tool_calls observer)
- Day 4: ~3 hr (design note + retro + memory + sync PR)

---

**Plan version**: v1 draft 2026-05-09 (this session)
**Author**: laitim2001 + Claude Code (paired drafting)
**Reviewer (pending)**: laitim2001
**Next step after review**: branch creation `feature/sprint-57-7-iam-frontend-foundation` + commit Day 0 progress.md + plan + checklist + start Day 1
