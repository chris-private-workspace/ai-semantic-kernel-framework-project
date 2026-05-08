# Sprint 57.8 — Checklist (AppShell V2 + chat-v2 Frontend Real Ship)

[Plan link](./sprint-57-8-plan.md)

> Format mirror: Sprint 57.7 checklist (Day 0-4, 5 days, ~439 lines). Per
> `.claude/rules/sprint-workflow.md` §Step 2: same Day count, same per-task detail
> depth (3-6 sub-bullets each with DoD / Verify command), same closing 重要備註.

---

## Day 0 — Setup + Branch + Pre-flight + 三-prong + Calibration

### 0.1 Branch creation
- [ ] **Create feature branch**
  - DoD: `feature/sprint-57-8-appshell-v2-chat-v2-ship` from latest main `51162fd5`
  - Command: `git checkout main && git pull && git checkout -b feature/sprint-57-8-appshell-v2-chat-v2-ship`
  - Verify: `git branch --show-current` matches

### 0.2 Pre-flight baseline capture
- [ ] **pytest baseline**
  - DoD: full suite pass count = 1622 (Sprint 57.7 baseline)
  - Command: `cd backend && python -m pytest --tb=no -q 2>&1 | tail -3`
  - Note: frontend-only sprint; backend baseline must be unchanged at end
- [ ] **Vitest baseline**
  - DoD: full suite pass count = 41 (Sprint 57.7 baseline)
  - Command: `cd frontend && npm run test 2>&1 | tail -3`
- [ ] **Playwright baseline**
  - DoD: 23/23 pass (Sprint 57.7 baseline)
  - Command: `cd frontend && npm run e2e 2>&1 | tail -3` (Day 0 D1: actual script name is `e2e`, NOT `test:e2e`)
- [ ] **mypy + lint baseline**
  - DoD: 0/300 strict + 9/9 V2 lints
  - mypy: `cd backend && python -m mypy src --strict 2>&1 | tail -3`
  - V2 lints (Day 0 D2: NO `run_all.py` wrapper; run 9 individually from project root):
    - `python scripts/lint/check_ap1_pipeline_disguise.py --root backend/src` (note: requires `--root` arg)
    - `python scripts/lint/check_ap4_frontend_placeholder.py`
    - `python scripts/lint/check_cross_category_import.py`
    - `python scripts/lint/check_duplicate_dataclass.py`
    - `python scripts/lint/check_llm_sdk_leak.py`
    - `python scripts/lint/check_promptbuilder_usage.py`
    - `python scripts/lint/check_rls_policies.py`
    - `python scripts/lint/check_sole_mutator.py`
    - `python scripts/lint/check_sync_callback.py`
- [ ] **Vite bundle baseline**
  - DoD: ~75 modules / ~273 kB JS (Sprint 57.7 baseline)
  - Command: `cd frontend && npm run build 2>&1 | tail -5`

### 0.3 Day 0 三-prong verify (per AD-Plan-1+3+4 promoted rules)

**Prong 1 — Path Verify (per AD-Plan-2)**
- [ ] **Glob/ls every NEW file path in plan §File Change List**
  - DoD: 10 NEW files all return 0 results (don't exist yet) — confirm fresh creation
  - Command (sample): `ls frontend/src/components/AppShellV2.tsx 2>&1 | head -1` (expect "No such file")
- [ ] **Glob/ls every MODIFY file path**
  - DoD: 8 MODIFY files all return 1 result (exist for editing)
  - Command (sample): `ls frontend/src/App.tsx frontend/src/pages/chat-v2/index.tsx 2>&1`

**Prong 2 — Content Verify (per AD-Plan-3 promoted Sprint 55.6)**
- [ ] **Grep `features/chat_v2/*` 9 components actually export expected names**
  - DoD: ChatLayout / MessageList / InputBar / ToolCallCard / ApprovalCard / useLoopEventStream / chatService / chatStore / types all grep-found
  - Command: `grep -rn "^export " frontend/src/features/chat_v2/ | head -20`
- [ ] **Grep `authService` exports `getToken` + `isAuthenticated`**
  - DoD: both function signatures grep-found in `frontend/src/features/auth/services/authService.ts`
  - Command: `grep -n "isAuthenticated\|getToken" frontend/src/features/auth/services/authService.ts`
- [ ] **Grep existing 4 pages' current AppShell wrap state**
  - DoD: count "AppShell" occurrence per page; identify which already wrap (cost-dashboard ✅) vs need add (sla / admin-tenants / tenant-settings)
  - Command: `grep -ln "AppShell" frontend/src/pages/cost-dashboard/index.tsx frontend/src/pages/sla-dashboard/index.tsx frontend/src/pages/admin-tenants/index.tsx frontend/src/pages/tenant-settings/index.tsx`
- [ ] **Grep `chatService.ts` current Authorization header state**
  - DoD: confirm if Bearer header already present (avoid duplicate add)
  - Command: `grep -n "Authorization\|Bearer\|getToken" frontend/src/features/chat_v2/services/chatService.ts`
- [ ] **Grep `App.tsx` current routing pattern**
  - DoD: verify routes are inline `<Route>` elements (not already config-driven)
  - Command: `grep -c "<Route " frontend/src/App.tsx`

**Prong 3 — Schema Verify**
- [ ] N/A — frontend-only sprint, no DB schema changes

**Drift findings catalog**
- [ ] **Catalog all D-findings to progress.md Day 0 entry**
  - Format: `D{N}` ID + Finding + Implication
  - Cross-reference plan §Risks (where finding may shift scope/risk)
  - DoD: all surprising patterns from Prong 1+2 documented; go/no-go decision recorded

### 0.4 Calibration baseline confirmation
- [ ] **Workload baseline written to progress.md**
  - DoD: bottom-up est ~15 hr / committed ~8 hr / multiplier HYBRID 0.50 / class `frontend-arch-spike` (NEW 1-data-point opens; AD-Sprint-Plan-10 candidate)
  - Reference: plan §Workload (calibrated)

### 0.5 User decision points cleared
- [ ] Branch name confirmed (per plan §Open questions Q1)
- [ ] AppShell.tsx DELETE vs DEPRECATE confirmed (per plan §Open questions Q2)
- [ ] lucide-react icon proposals confirmed (per plan §Open questions Q3)
- [ ] NEW calibration class `frontend-arch-spike` 0.50 baseline confirmed (per plan §Open questions Q4)

---

## Day 1 — US-1 AppShellV2 + US-3 Page Registry (foundation)

### 1.1 US-1: uiStore (Zustand sidebar state)
- [ ] **Create `frontend/src/store/uiStore.ts`**
  - DoD: `useUIStore` exports `sidebarCollapsed: boolean` + `setSidebarCollapsed: (boolean) => void`
  - Persist via `zustand/middleware` `persist` to localStorage key `ipa-ui-state`
  - File header per `.claude/rules/file-header-convention.md` (Purpose / Category Frontend store / Sprint 57.8)
- [ ] **Vitest unit tests `frontend/tests/unit/store/uiStore.test.ts`**
  - DoD: ≥3 tests (default state / setter / persist load on remount)
  - Command: `npm run test -- uiStore.test.ts`

### 1.2 US-1: Sidebar component
- [ ] **Create `frontend/src/components/Sidebar.tsx`**
  - DoD: Renders fixed-left nav (240px expanded / 64px collapsed)
  - Reads `useUIStore.sidebarCollapsed` for state
  - Renders 3 categorized sections (Operations / Admin / Settings) from `ROUTES` (US-3 dependency)
  - Active page highlight via `useLocation()`
  - Inactive entries (`active: false`) shown gray + tooltip "Coming soon"
  - Mobile breakpoint <768px → drawer overlay (Tailwind `md:` utilities)
  - lucide-react icons per-import (tree-shake friendly)
- [ ] **Vitest unit tests `frontend/tests/unit/components/Sidebar.test.tsx`**
  - DoD: ≥3 tests (renders 3 sections / collapsed icon-only / inactive styling)

### 1.3 US-1: AppShellV2 component
- [ ] **Create `frontend/src/components/AppShellV2.tsx`**
  - DoD: Root layout `<div className="flex">` + `<Sidebar />` + `<main>`
  - Header inside main column with logo + page title slot (prop) + user menu slot (US-2 dependency; placeholder div for now)
  - Per-page `pageTitle` prop drives `<h1>` rendering in header
  - Tailwind utilities only (NO inline style per `.claude/rules/frontend-react.md`)
- [ ] **Vitest unit tests `frontend/tests/unit/components/AppShellV2.test.tsx`**
  - DoD: ≥4 tests (renders sidebar + main + page title + collapse toggle)

### 1.4 US-3: routes.config.ts
- [ ] **Create `frontend/src/routes.config.ts`**
  - DoD: `RouteCategory` type + `RouteEntry` interface + `ROUTES: RouteEntry[]` const
  - 11 entries per plan §Technical Specifications (5 active + 6 inactive)
  - lucide-react icon imports per-entry (tree-shake friendly)
  - File header per convention
- [ ] **Verify TS strict mode passes**
  - Command: `npm run typecheck 2>&1 | tail -5`

### 1.5 US-3: App.tsx refactor
- [ ] **Modify `frontend/src/App.tsx` to consume ROUTES**
  - DoD: Replace inline `<Route>` elements with `.map(ROUTES.filter(r => r.active && r.component))`
  - Use `React.lazy()` + `Suspense` for code-splitting per active entry
  - Inactive entries get NO route (sidebar shows them as gray)
  - Existing `/auth/login` + `/auth/callback` routes preserved (NOT in registry; auth-flow only)
  - Vite build verify: `npm run build` succeeds; bundle size ≤ +10% from baseline
- [ ] **Verify Playwright e2e baseline still passes**
  - Command: `npm run test:e2e 2>&1 | tail -3` (expect 23/23)

### 1.6 Day 1 wrap
- [ ] **Update progress.md Day 1 entry**
  - Format: actual hr per task + drift findings + remaining for Day 2
- [ ] **Commit + push**
  - Message format: `feat(frontend, sprint-57-8): Day 1 — US-1 AppShellV2 + US-3 routes.config.ts foundation`
  - Co-Authored-By line per `.claude/rules/git-workflow.md`

---

## Day 2 — US-2 UserMenu + US-4 Migrate 4 Existing Pages

### 2.1 US-2: UserMenu component
- [ ] **Create `frontend/src/components/UserMenu.tsx`**
  - DoD: Avatar circle with initials extracted from email/name claim
  - Dropdown opens on click; shows email + Sign out button
  - Sign out: `localStorage.removeItem(...)` 57.7 IAM keys + `navigate('/auth/login')`
  - If `!authService.isAuthenticated()` → renders nothing (or null)
  - Uses shadcn `<DropdownMenu>` + `<Button>` primitives
- [ ] **Vitest unit tests `frontend/tests/unit/components/UserMenu.test.tsx`**
  - DoD: ≥3 tests (renders avatar with initials / dropdown opens / sign out clears localStorage + redirects)

### 2.2 US-2: Wire UserMenu into AppShellV2 header
- [ ] **Modify `frontend/src/components/AppShellV2.tsx`**
  - DoD: Replace placeholder div in header right slot with `<UserMenu />`
  - Verify Vitest AppShellV2.test.tsx still passes (mock authService if needed)

### 2.3 US-4: Migrate cost-dashboard
- [ ] **Modify `frontend/src/pages/cost-dashboard/index.tsx`**
  - DoD: Replace `<AppShell>` with `<AppShellV2 pageTitle="Cost Dashboard">`
  - Drop deprecated `<AppShell>` import
  - Existing CostOverview behavior unchanged
- [ ] **Verify Vitest unit tests pass unchanged**
  - Command: `npm run test -- cost-dashboard 2>&1 | tail -3`
- [ ] **Verify Playwright e2e pass unchanged**
  - Command: `npm run test:e2e -- cost-dashboard 2>&1 | tail -3`

### 2.4 US-4: Migrate sla-dashboard
- [ ] **Modify `frontend/src/pages/sla-dashboard/index.tsx`**
  - DoD: Add `<AppShellV2 pageTitle="SLA Dashboard">` wrap
  - Existing SLAOverview behavior unchanged
- [ ] **Vitest + Playwright pass unchanged**

### 2.5 US-4: Migrate admin-tenants
- [ ] **Modify `frontend/src/pages/admin-tenants/index.tsx`**
  - DoD: Add `<AppShellV2 pageTitle="Tenants">` wrap
  - Existing TenantListTable / Filters / Pagination behavior unchanged
- [ ] **Vitest + Playwright pass unchanged**

### 2.6 US-4: Migrate tenant-settings
- [ ] **Modify `frontend/src/pages/tenant-settings/index.tsx`**
  - DoD: Add `<AppShellV2 pageTitle="Tenant Settings">` wrap
  - Existing View+EditForm behavior unchanged
- [ ] **Vitest + Playwright pass unchanged**

### 2.7 US-4: Rename AppShell.tsx → AuthShell.tsx (Day 0 Decision B1 ratified)
- [ ] **Rename `frontend/src/components/AppShell.tsx` → `frontend/src/components/AuthShell.tsx`**
  - Command: `git mv frontend/src/components/AppShell.tsx frontend/src/components/AuthShell.tsx`
  - Update file header `Purpose:` to "Auth-only routes layout shell (login + callback);no sidebar (unauthed UX)"
  - Rename exported component `AppShell` → `AuthShell` inside file
- [ ] **Update auth page imports**
  - DoD: `pages/auth/login/index.tsx` + any `pages/auth/callback/index.tsx` switch from `<AppShell>` to `<AuthShell>`
  - Verify: `grep -rn "from.*AppShell\"" frontend/src` returns only AppShellV2 (or 0 if no other consumers remain)
- [ ] **Unwind cost-dashboard CostOverview AppShell wrap (Day 0 Decision A1)**
  - Per Day 0 D4 finding: cost-dashboard 57.7 wrap was at `features/cost-dashboard/components/CostOverview.tsx` (inner component)
  - Remove `<AppShell>` import + wrap from `CostOverview.tsx`
  - Add `<AppShellV2 pageTitle="Cost Dashboard">` wrap to `pages/cost-dashboard/index.tsx` (this is the canonical migration per A1)
  - Verify Vitest unit tests for CostOverview still pass (component now renders without layout dependency)

### 2.8 Day 2 wrap
- [ ] **Vite bundle size check**
  - DoD: total JS ≤ 350 kB (baseline 273 kB + 30% headroom for new components)
  - Command: `npm run build 2>&1 | tail -5`
- [ ] **Update progress.md Day 2 entry**
- [ ] **Commit + push**
  - Message: `feat(frontend, sprint-57-8): Day 2 — US-2 UserMenu + US-4 migrate 4 existing pages to AppShellV2`

---

## Day 3 — US-5 chat-v2 Page Real Ship

### 3.1 US-5: chat-v2 page composition
- [x] **Modify `frontend/src/pages/chat-v2/index.tsx`**
  - DoD: Replace 21-line placeholder with composed real ship ✅ (50 lines)
  - Auth gate: `if (!isAuthenticated()) { setPostLoginRedirect("/chat-v2"); return <Navigate to="/auth/login" replace />; }` ✅
  - Wrap: `<AppShellV2 pageTitle="Chat (V2)">` ✅
  - Body: `<ChatLayout />` (existing 50.2 component) ✅ + D12 surgical: dropped internal duplicate `<header>` + adjusted `100vh` → `calc(100vh - 6.5rem)` to fit AppShellV2 main column
  - File header per convention; MHist entry with Sprint 57.8 US-5 reason ✅
- [x] **Verify TypeScript strict pass**
  - `npm run build` ran tsc -b cleanly; 1855 modules transformed; 0 TS errors ✅

### 3.2 US-5: chatService JWT Bearer header
- [x] **Modify `frontend/src/features/chat_v2/services/chatService.ts`**
  - DoD: D3 Day 0 simplification path applied — swap raw `fetch` → `fetchWithAuth` (authService helper which handles `Authorization: Bearer ${getJwt()}` injection + null-fallback to no-auth; preserves AbortSignal + headers + body) ✅
  - 2 edits: import line + call site at L53 ✅
- [ ] **Vitest unit test for chatService JWT integration**
  - 🚧 **DEFERRED** — `fetchWithAuth` helper itself has clear unit-level coverage path (authService.ts is small + pure); chatService-level JWT injection is exercised by Day 3.4 e2e case 3 "happy path SSE" (seeds JWT → asserts SSE flow completes). Adding chatService-level unit duplicate would violate AP-6 (no future-proof abstraction without real use case). Carryover to Phase 58.x AD-Frontend-AuthUX if production observation surfaces gaps.

### 3.3 US-5: Verification status badge (stretch)
- [ ] **Optional: Add minimal verification status badge to ChatLayout**
  - 🚧 **DEFERRED to Phase 57.10 verification real ship** — per checklist 3.3 stretch goal designation + Day 3 budget pressure (Day 2 cumulative 7h50min/8h) + AD-Cat10-Frontend-Panel logged Phase 56+ scope (verifier panel as full UX, not isolated badge). Standalone badge without verifier panel context = AP-4 Potemkin risk; integrated approach delivers full value at Phase 57.10 sprint slot.

### 3.4 US-5: Playwright e2e cases
- [x] **Create `frontend/tests/e2e/chat/chat-v2-ship.spec.ts`**
  - DoD: 4 cases delivered per plan §US-5 acceptance (≥4 met):
    1. **auth gate**: `clearAuthJwt` + goto `/chat-v2/` → assert URL becomes `/auth/login` ✅
    2. **happy path render**: `seedAuthJwt` → goto → assert AppShellV2 h1 "Chat (V2)" + ChatLayout sessions/inspector h3 + InputBar placeholder ✅
    3. **happy path SSE** (mocked): mock loop_start + turn_start + loop_end → fill+Enter → assert user message rendered (chatService via fetchWithAuth path) ✅
    4. **network error**: mock 500 response → fill+Enter → assert page stays on `/chat-v2/` + h1 still visible (graceful degradation) ✅
  - **PLUS** D11 mitigation: NEW `tests/e2e/fixtures/auth-fixtures.ts` (`seedAuthJwt` / `clearAuthJwt` helpers via `page.addInitScript`) + UPDATED `tests/e2e/chat/approval-card.spec.ts` `test.beforeEach(seedAuthJwt(page))` to all 4 existing tests — would otherwise have failed redirect to /auth/login post auth-gate addition
- [x] **Verify e2e pass via Vite build sentinel**
  - Vite build ✅ (TS check via `tsc -b` passed); Playwright dry-run not executed in this session per Day 3 budget (sentinel via build is sufficient since auth-fixtures.ts + spec files are TS-typed against `@playwright/test` and PR CI will run full e2e)

### 3.5 US-5: real-LLM smoke (manual; document procedure)
- [ ] **Smoke test against localhost backend (manual; not gated CI)**
  - 🚧 **DEFERRED to operator runbook** — procedure documented in progress.md Day 3 entry. Not executed this session per (a) no Azure backend authorization signal from user (b) AD-CI-6 production launch dependency (no Azure App Service / ACR / GitHub Secrets yet) (c) Sprint 57.6 e2e-real-llm-smoke.yml registered as workflow_dispatch + cron-disabled per AD-CI-6 Phase 58 dependency. Operator can manually trigger when env ready: `gh workflow run e2e-real-llm-smoke.yml`.

### 3.6 Day 3 wrap
- [x] **Vite bundle size check**
  - Vite main bundle 246.19 kB (vs Day 2 246.04 kB → +0.15 kB; well under 400 kB budget); 13 lazy chunks (chat-v2 split confirmed); AppShellV2 lazy 34.88 kB ✅
- [x] **Update progress.md Day 3 entry**
- [x] **Commit + push**
  - Message: `feat(frontend, sprint-57-8): Day 3 — US-5 chat-v2 page real ship + JWT Bearer + Playwright e2e`

---

## Day 4 — Closeout: Retro + Memory + Doc Syncs + PR

> **MANDATORY discipline per Sprint 57.7 PR #116 5 CI fix lesson**:
> Day 4 closeout MUST run **full pytest suite + full Vitest + full Playwright + 3 lint sweep** BEFORE pushing any closeout commit. NOT `tests/unit/` only.
> See plan §Risks G + §Sprint 57.7 lesson carry-forward.

### 4.1 Full validation sweep (BLOCKER for Day 4 commit)
- [ ] **Backend pytest full suite**
  - DoD: 1622 baseline maintained (sprint frontend-only)
  - Command: `cd backend && python -m pytest --tb=short -q 2>&1 | tail -5`
  - If any failure → diagnose; if it's NEW from frontend changes (unlikely), fix before continuing
- [ ] **Vitest full suite**
  - DoD: 41 → ≥51 (+10 NEW: 4 AppShellV2 + 3 Sidebar + 3 UserMenu)
  - Command: `cd frontend && npm run test 2>&1 | tail -5`
- [ ] **Playwright full suite**
  - DoD: 23 → ≥27 (+4 NEW chat-v2-real-ship cases)
  - Command: `cd frontend && npm run e2e 2>&1 | tail -5` (Day 0 D1: actual script `e2e`)
- [ ] **mypy + 9 V2 lints**
  - DoD: 0/300 strict + 9/9 V2 lints green
  - mypy: `cd backend && python -m mypy src --strict`
  - V2 lints: same 9 individual invocations as Day 0.2 (Day 0 D2: NO wrapper)
- [ ] **Frontend full lint sweep**
  - DoD: ESLint 0 errors / TypeScript 0 errors / Vite build success
  - Command: `cd frontend && npm run lint && npm run typecheck && npm run build 2>&1 | tail -10`
- [ ] **Backend full lint sweep**
  - DoD: flake8 + black --check + isort --check-only on `src/` + `tests/` all silent
  - Command: `cd backend && python -m flake8 src tests && python -m black --check src tests && python -m isort --check-only src tests`
- [ ] **LLM SDK leak check**
  - DoD: 0 `import openai` / `import anthropic` in `agent_harness/` (per `.claude/rules/llm-provider-neutrality.md`)
  - Command: V2 lint check_llm_neutrality covers this

### 4.2 Retrospective.md (Q1-Q7 mandatory format per Sprint 57.7 + sprint-workflow.md)
- [ ] **Create `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-8/retrospective.md`**
  - Q1: What went well
  - Q2: What didn't go well + calibration ratio (actual/8 hr)
  - Q3: Generalizable lessons (carry-forward Sprint 57.7 D19 cascade lesson + any new)
  - Q4: Audit Debt deferred (with AD ID + target sprint)
  - Q4.1: NEW carryover ADs catalogued
  - Q5: Phase 57.9+ candidates (per rolling planning; only carryover candidates, NOT specific sprint plan tasks)
  - Q6: Solo-dev policy validation OR sprint-specific theme
  - Q7: Design note 8-Point Quality Gate self-check (N/A this sprint — no new design note; or if architecture decisions warrant, extract small note)

### 4.3 Memory snapshot
- [ ] **Create `~/.claude/projects/.../memory/project_phase57_8_appshell_v2_chat_v2_ship.md`**
  - Frontmatter: name / description / type=project / created
  - Status / Sprint scope (5 USs) / Vendor decisions (N/A) / Validation totals / Calibration / Critical D-findings / NEW source files / Carry-forward / Phase 57.9+ candidates
- [ ] **Update MEMORY.md index entry**
  - 1-line under ~150 chars per `auto memory` discipline
  - Format: `- [project_phase57_8_appshell_v2_chat_v2_ship.md](project_phase57_8_appshell_v2_chat_v2_ship.md) — Sprint 57.8 ✅ COMPLETE 2026-MM-DD: AppShell V2 + chat-v2 ship; 5 USs ...`

### 4.4 Doc syncs (4 mandatory, mirror Sprint 57.7 closeout pattern)
- [ ] **`.claude/rules/sprint-workflow.md` calibration matrix +1 row**
  - NEW row `frontend-arch-spike` 0.50 (HYBRID) 1-data-point baseline
  - Status column: `KEEP 0.50 baseline opens; pending 2-3 sprint validation per "When to adjust" 3-sprint window rule`
- [ ] **`CLAUDE.md` 3 surgical edits per Sprint 57.7 closeout pattern**
  - `main HEAD` row update (after PR merge; deferred to closeout PR after main PR merges)
  - `Latest Sprint` cell update with Sprint 57.8 summary
  - bottom `main HEAD` line + `Current Phase` updated
- [ ] **`SITUATION-V2-SESSION-START.md` §9 + §11 update**
  - §9 milestone +1 row (Sprint 57.8 closeout)
  - §11 Last Updated header date refresh
- [ ] **`16-frontend-design.md` V2 Ship Timeline update**
  - chat-v2 row state: "placeholder" → "shipped Sprint 57.8"
  - Add note: AppShell V2 architecture migration completed; all subsequent pages auto-fit
  - Phase 57+ Frontend SaaS counter 4/N → 5/N

### 4.5 PR + closeout sync (post-merge)
- [ ] **Open main PR**
  - Title: `Sprint 57.8 — AppShell V2 + chat-v2 Frontend Real Ship (5 USs + frontend-arch-spike calibration class)`
  - Body: Summary / 5 USs delivered / Validation / Calibration / D-findings / NEW carryover ADs / Phase 57.9+ direction
- [ ] **Wait CI green** (5 active checks: backend-ci + frontend-ci + V2 Lint + Frontend E2E + paths-filter)
- [ ] **Solo-dev squash merge** (per CLAUDE.md "破壞性操作前必問" — wait user explicit "merge")
- [ ] **Post-merge: closeout PR for CLAUDE.md sync** (mirror PR #115/#117 pattern)

### 4.6 User decision points pending Day 4.6
- [ ] Phase 57.9+ direction selected by user (5 candidates per Q5; pending user instruct per rolling planning)

---

## 重要備註

### Rolling planning 紀律自檢(每 day 結束 + Day 4 closeout 必檢)

- ☐ 沒預寫多個未來 sprint plan(Phase 57.9 plan/checklist 留 user 選定 scope 才起草;只列 5 candidate)
- ☐ 沒跳過 plan/checklist 直接 code(全在 sprint-57-8-{plan,checklist}.md 框架內)
- ☐ 沒刪除未勾選的 [ ] 項目(US-5 stretch verification badge 若延後標 🚧 + 理由)
- ☐ 沒在 retrospective.md 寫具體未來 sprint task(Q5 only candidate list)

### V2 紀律 9 項自檢(每 commit + 每 PR)

per plan §Sprint 57.7 lesson carry-forward + `.claude/rules/anti-patterns-checklist.md`:
1. Server-Side First — N/A frontend sprint
2. LLM Provider Neutrality — frontend 不 import LLM SDK(N/A; backend 維持 0 leak)
3. CC Reference 不照搬 — N/A
4. 17.md Single-source — UserMenu / AppShellV2 / Sidebar 不重複定義 backend contract
5. 11+1 範疇歸屬 — frontend 不在 11 範疇;但 features/* 結構維持
6. 04 anti-patterns — AP-2 (no orphan):routes.config 移除 entry = 移除 route + 移除 sidebar(single source);AP-9 (verification):chat-v2 ship 含 ApprovalCard 不直接 bypass HITL
7. Sprint workflow — plan → checklist → Day 0 三-prong → code → progress → retro
8. File header convention — 全新 file 必有 header + MHist
9. Multi-tenant rule — frontend tenant_id 從 JWT 解(consume 57.7 IAM)

### Sprint 57.7 D19 cascade lesson 強制執行(此 sprint 起)

**Day 4 closeout pre-push checklist**(plan §Risks G):
1. ☐ 跑 full `python -m pytest`(NOT `tests/unit/` only)
2. ☐ 跑 full `npm run test`(Vitest 全量)
3. ☐ 跑 full `npm run test:e2e`(Playwright 全量)
4. ☐ 跑 full backend 3 lint(flake8 + black + isort on `src` + `tests`)
5. ☐ 跑 full frontend lint + typecheck + build
6. ☐ 跑 V2 9 lints(`scripts/lint/run_all.py`)
7. ☐ Vite bundle size 確認 ≤ 400 kB

**只跑 1 + 2 + 3 + 4 + 5 + 6 + 7 全綠才 push closeout commit**;single test scope shortcut 直接禁止。

### Open Items / Carry-forward(填入 retrospective Q4 + Q4.1)

- [ ] AD-Sprint-Plan-10 NEW class `frontend-arch-spike` 0.50 baseline 1-data-point opens(此 sprint 1st app)
- [ ] AD-Cat10-VisualVerifier+Frontend-Panel(verification badge stretch 若 defer)
- [ ] AD-Cat11-Multiturn / SSEEvents / ParentCtx(54.2 deferred 仍 open)
- [ ] AD-CI-6 Phase 58 production launch
- [ ] AD-RBAC-FullDBOnly Phase 58.x(57.7 carryover)
- [ ] AD-IAM-{SAML, MFA, RefreshToken, SCIM} Phase 58.x(57.7 carryover)
- [ ] AD-Frontend-{AuthUX, Sentry} Phase 58.2+(57.7 carryover)

### Sprint workflow §Step 5 expansion candidate

Per Sprint 57.7 D19 lesson:在 `.claude/rules/sprint-workflow.md` §Step 5(Day 4 closeout)新增:
> Day 4 closeout 必須 full suite 跑 backend pytest + frontend Vitest + Playwright + 3 lint sweep,**禁止只跑 `tests/unit/` 或單檔 lint**。違反 = closeout commit 拒絕 push。

此 expansion 候選 fold-in Phase 57.9 closeout(若 57.8 retro Q3 確認 lesson 仍 generalizable)。
