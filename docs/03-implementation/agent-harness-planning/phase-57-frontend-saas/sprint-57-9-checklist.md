# Sprint 57.9 — Checklist (Governance Real Ship + TanStack Query 4-page Migration)

[Plan link](./sprint-57-9-plan.md)

> Format mirror: Sprint 57.8 checklist (Day 0-4, 5 days, ~388 lines). Per
> `.claude/rules/sprint-workflow.md` §Step 2: same Day count, same per-task detail
> depth (3-6 sub-bullets each with DoD / Verify command), same closing 重要備註.

---

## Day 0 — Setup + Branch + Pre-flight + 三-prong + Calibration

### 0.1 Branch creation
- [x] **Create feature branch** ✅
  - DoD: `feature/sprint-57-9-governance-ship-tquery-migration` from latest main `caf95706`
  - Command: `git checkout main && git pull && git checkout -b feature/sprint-57-9-governance-ship-tquery-migration`
  - Verify: `git branch --show-current` matches ✅

### 0.2 Pre-flight baseline capture
- [x] **pytest baseline** ✅ post D-PRE-1 cleanup
  - DoD: full suite pass count = 1622 (Sprint 57.8 baseline; 1618 passed + 4 skipped) — **post-cleanup matches** (initial -3 D13-class pollution)
- [x] **Vitest baseline** ✅
  - DoD: 57/57 (19 files / 2.54s) — matches
- [x] **Playwright baseline** ✅
  - DoD: 27/27 (7.6s) — matches
- [x] **mypy + lint baseline** ✅
  - mypy: 0/300 source files — matches
  - 9 V2 lints: 9/9 green (4.19s via `python scripts/lint/run_all.py`)
- [x] **Vite bundle baseline** ✅
  - 246.19 kB main + 13 lazy chunks (AppShellV2 lazy 34.88 kB) — matches

### 0.3 Day 0 三-prong verify (per AD-Plan-1+3+4 promoted rules)

**Prong 1 — Path Verify (per AD-Plan-2)**
- [ ] **Glob/ls every NEW file path in plan §File Change List**
  - DoD: 16 NEW files all return 0 results (don't exist yet) — confirm fresh creation
  - Sample: `ls frontend/src/features/governance/hooks/useApprovals.ts 2>&1 | head -1` (expect "No such file")
  - Sample: `ls frontend/src/features/cost-dashboard/hooks/useCostSummary.ts 2>&1 | head -1`
- [ ] **Glob/ls every MODIFY file path**
  - DoD: 15 MODIFY files all return 1 result (exist for editing)
  - Sample: `ls frontend/src/pages/governance/index.tsx frontend/src/features/governance/services/governanceService.ts 2>&1`
- [ ] **Verify admin-tenants page actual file location (Risk I)**
  - DoD: identify the canonical file holding admin-tenants list/filter/pagination (could be `pages/admin-tenants/index.tsx` OR `features/admin-tenants/components/AdminTenantsPage.tsx`)
  - Command: `find frontend/src -path "*admin-tenants*" -name "*.tsx" | head -10`
  - Document path in plan §File Change List MODIFY row "TBD via Day 0"

**Prong 2 — Content Verify (per AD-Plan-3 promoted Sprint 55.6)**
- [ ] **Grep `features/governance/` 5 existing files actually export expected names**
  - DoD: ApprovalsPage / ApprovalList / DecisionModal / governanceService all grep-found
  - Command: `grep -rn "^export " frontend/src/features/governance/ | head -10`
- [ ] **Grep `authService` exports `isAuthenticated` + `setPostLoginRedirect` + `fetchWithAuth`**
  - DoD: all 3 function signatures grep-found in `frontend/src/features/auth/services/authService.ts`
  - Command: `grep -n "isAuthenticated\|setPostLoginRedirect\|fetchWithAuth" frontend/src/features/auth/services/authService.ts`
- [ ] **Grep main.tsx QueryClient setup intact (no regression from 57.8)**
  - DoD: `<QueryClientProvider client={queryClient}>` wrap present
  - Command: `grep -n "QueryClientProvider\|QueryClient" frontend/src/main.tsx`
- [ ] **Grep governanceService.ts current fetch pattern (Risk D — claims mismatch detect)**
  - DoD: confirm raw `fetch` (not yet `fetchWithAuth`); identify Authorization header handling
  - Command: `grep -n "fetch\|fetchWithAuth\|Authorization" frontend/src/features/governance/services/governanceService.ts`
- [ ] **Grep IAM JWT claim shape (Risk D)**
  - DoD: confirm `_to_internal_jwt` claims output includes `tenant_id` + `roles`; verify backend `require_approver_role` / `require_audit_role` checks expected claims
  - Backend: `grep -n "require_approver_role\|require_audit_role\|roles\b" backend/src/platform_layer/identity/auth.py`
  - Frontend: `grep -n "_to_internal_jwt\|claims\|roles" backend/src/api/v1/auth/oidc.py 2>/dev/null` (Sprint 57.7 OIDC)
- [ ] **Grep `routes.config.ts` governance entry current state**
  - DoD: confirm `name: "Governance"` exists with `active: false` + `category: "admin"` + icon `ShieldCheck`
  - Command: `grep -n "Governance\|governance" frontend/src/routes.config.ts`
- [ ] **Grep 4 page services current fetch pattern (US-6 baseline)**
  - DoD: confirm direct `fetch` not yet TanStack; identify any partial migrations
  - Command: `grep -n "fetch\|useQuery\|useMutation" frontend/src/features/cost-dashboard/services/costService.ts frontend/src/features/sla-dashboard/services/slaService.ts frontend/src/features/admin-tenants/services/adminTenantsService.ts frontend/src/features/tenant-settings/services/tenantSettingsService.ts`
- [ ] **Grep Zustand store current state surface (US-6 baseline)**
  - DoD: identify which stores hold server state (data/loading/error) vs UI-only state (filter/draft)
  - Command: `grep -A 3 "interface.*State\b" frontend/src/features/cost-dashboard/store/costStore.ts frontend/src/features/sla-dashboard/store/slaStore.ts frontend/src/features/admin-tenants/store/adminTenantsStore.ts frontend/src/features/tenant-settings/store/tenantSettingsStore.ts | head -40`
- [ ] **Grep shadcn `<Dialog>` usage existing (Risk C — bundle weight)**
  - DoD: count Dialog imports across frontend; if 0 elsewhere, prefer Tailwind Modal impl
  - Command: `grep -rln "from.*shadcn.*dialog\|@/components/ui/dialog" frontend/src/`

**Prong 3 — Schema Verify**
- [ ] N/A — frontend-only sprint, no DB schema changes

**Drift findings catalog**
- [x] **Catalog all D-findings to progress.md Day 0 entry** ✅
  - 7 D-findings catalogued (D-PRE-1 RED resolved + D-PRE-2..6 GREEN + D-PRE-5 YELLOW)
  - Risk D resolution: 57.7 IAM `roles` claim ↔ 53.5 backend `_require_role` JWT consumption MATCH ✅
  - go/no-go: ✅ GO Day 1 (D-PRE-1 RED was Sprint 57.8 carryover not regression; baseline restored to 1622)

### 0.4 Calibration baseline confirmation
- [x] **Workload baseline written to progress.md** ✅
  - bottom-up est ~22 hr / committed ~10.5 hr / multiplier HYBRID 0.50 / class `frontend-feature-with-migration` (NEW 1-data-point opens; AD-Sprint-Plan-10 extension)

### 0.5 User decision points cleared (pre-confirmed via plan Q1-Q4)
- [x] Branch name confirmed: `feature/sprint-57-9-governance-ship-tquery-migration` (Q1 select A)
- [x] Audit log viewer scope confirmed: filter form + paginated table (Q2 select A)
- [x] Tab UX confirmed: URL-based 2 sub-routes (Q3 select A)
- [x] NEW calibration class `frontend-feature-with-migration` 0.50 baseline confirmed (Q4 select A)
- [ ] shadcn `<Dialog>` decision pending Day 0 Prong 2 bundle-weight grep (default Tailwind per YAGNI)

---

## Day 1 — US-1 AppShellV2 + Auth Gate + Tabs + US-2 Tailwind Migration

### 1.1 US-1: Pages governance/index.tsx composition
- [x] **Modify `frontend/src/pages/governance/index.tsx`** ✅
  - 40-line placeholder → 70-line composed real ship; auth gate + AppShellV2 + 2-tab nav + nested Routes
  - File header MHist updated with Sprint 57.9 US-1 Day 1 entry
- [x] **Verify TypeScript strict pass** ✅
  - `tsc -b` 0 errors; AuditLogViewer stub created (Day 1 import-resolver enabler; Day 3 US-4 real impl)

### 1.2 US-1: routes.config.ts update
- [x] **Modify `frontend/src/routes.config.ts`** ✅
  - governance `active: false` → `active: true` + `component: lazy(() => import("./pages/governance"))`
  - File header active count 5→6 + new MHist entry
- [x] **Modify `frontend/src/App.tsx` (BONUS — D-PRE-8 NEW)** ✅
  - Removed legacy direct `import GovernancePage from "./pages/governance"` (L35) + `<Route path="/governance/*" element={<GovernancePage />} />` (L93)
  - Single-source restored per in-code direction L91-93; verification still placeholder for Phase 57.10
  - File header MHist updated

### 1.3 US-2: ApprovalsPage Tailwind migration
- [x] **Modify `frontend/src/features/governance/components/ApprovalsPage.tsx`** ✅
  - 121 → 99 lines; drop pageStyle/headerRow/buttonStyle const objects
  - Tailwind: `space-y-4` container + `flex items-baseline justify-between` header + cost-dashboard error pattern
  - Behavior preserved (polling 30s + AbortController; US-3 Day 2 will refactor to TanStack hooks)

### 1.4 US-2: ApprovalList Tailwind migration
- [x] **Modify `frontend/src/features/governance/components/ApprovalList.tsx`** ✅
  - 115 → 91 lines; drop tableStyle/thStyle/tdStyle/RISK_COLOR/inline button-style
  - Risk palette preserved via arbitrary-value classes `text-[#2e7d32]/2/3/4` (regression sentinel)

### 1.5 US-2: DecisionModal Tailwind migration
- [x] **Modify `frontend/src/features/governance/components/DecisionModal.tsx`** ✅
  - 192 → 159 lines; drop overlayStyle/dialogStyle/header/fieldRow/labelStyle/reasonBox/buttonRow/buttonStyle()
  - Tailwind impl per Day 0 D-PRE-2 + Sprint 57.8 UserMenu YAGNI precedent (no shadcn `<Dialog>`)
  - 4 button kinds via BUTTON_BASE + BUTTON_KIND records with arbitrary-value palette preservation

### 1.6 Day 1 wrap
- [x] **Vite bundle size check** ✅
  - main JS **240.30 kB** (-5.89 kB vs baseline 246.19 kB) — governance lazy-load > legacy direct-import; 17% under 280 kB budget
- [x] **Update progress.md Day 1 entry** ✅
- [x] **Commit + push** (executed below)

---

## Day 2 — US-3 TanStack Governance Hooks + Refactor

### 2.1 US-3: governanceService fetchWithAuth swap ✅
- [x] **Modify `frontend/src/features/governance/services/governanceService.ts`**
  - 2 fetch sites swapped → fetchWithAuth (mirror Sprint 57.8 D3 chatService pattern)

### 2.2 US-3: useApprovals hook ✅
- [x] **Create `frontend/src/features/governance/hooks/useApprovals.ts`** — APPROVALS_QUERY_KEY single-source export + useQuery refetchInterval 30_000
- [x] **Vitest test** — 4 tests pass (1 bonus: APPROVALS_QUERY_KEY single-source assertion)

### 2.3 US-3: useApprovalDecide mutation hook ✅
- [x] **Create `frontend/src/features/governance/hooks/useApprovalDecide.ts`** — useMutation + onSuccess invalidates APPROVALS_QUERY_KEY
- [x] **Vitest test** — 3 tests pass (mutate success+invalidate / error / isPending lifecycle)

### 2.4 US-3: ApprovalsPage refactor ✅
- [x] **Modify `frontend/src/features/governance/components/ApprovalsPage.tsx`** — 99 → 64 lines (drop 10 imports/symbols including useState/useRef/useCallback/useEffect/setInterval/AbortController)

### 2.5 US-3: DecisionModal refactor ✅
- [x] **Modify `frontend/src/features/governance/components/DecisionModal.tsx`** — 159 → 142 lines (drop onSubmit prop entirely + busy/error useState; consume useApprovalDecide mutation hook)

### 2.6 Day 2 wrap ✅
- [x] **Vite bundle size check** — main JS 240.75 kB (+0.45 kB vs Day 1; under 280 kB budget by 39 kB); governance lazy 18.75 kB NEW
- [x] **Update progress.md Day 2 entry**
- [x] **Commit + push** (executed below — D-PRE-10 fix included in same Day 2 commit)

---

## Day 3 — US-4 Audit Log Viewer + US-5 Chain Verify Badge

### 3.1 US-4: auditService.ts NEW ✅
- [x] **Create `frontend/src/features/governance/services/auditService.ts`**
  - DoD: 2 functions:
    - `fetchAuditLog(filter: AuditLogFilter): Promise<AuditLogPage>` consuming GET `/api/v1/audit/log` with query params ✅
    - `verifyChain(): Promise<ChainVerifyResult>` consuming GET `/api/v1/audit/verify-chain` ✅
  - Both use `fetchWithAuth` for IAM JWT ✅
  - URLSearchParams for filter (omit-undefined helper; mirror Sprint 57.4 buildListSearchParams pattern) ✅
  - File header per convention ✅
- [x] **Modify `frontend/src/features/governance/types.ts`**
  - DoD: extend with `AuditLogFilter` + `AuditLogEntry` (12 fields) + `AuditLogPage` + `ChainVerifyResult` ✅

### 3.2 US-4: useAuditLog hook ✅
- [x] **Create `frontend/src/features/governance/hooks/useAuditLog.ts`**
  - DoD: `useQuery({ queryKey: [...AUDIT_LOG_QUERY_KEY_BASE, filter], ... })` + `placeholderData: keepPreviousData` ✅
  - File header per convention ✅
- [x] **Vitest unit test `frontend/tests/unit/governance/useAuditLog.test.tsx`** — 4 tests (key / fetch / error / refetch delta) ✅

### 3.3 US-4: AuditLogViewer component ✅
- [x] **Create `frontend/src/features/governance/components/AuditLogViewer.tsx`**
  - DoD: filter form (4 fields: operation / resource_type / user_id / from_ts datetime-local) with draft-vs-committed pattern ✅
  - State: `[filter, setFilter] = useState({ offset: 0, page_size: 50 })`; Apply promotes draft → filter ✅
  - Paginated table 6 columns (id / timestamp / operation / resource / user / hash) + 5-row loading skeleton + empty-state Reset Filters ✅
  - Next/Prev pagination footer with edge-disable + range indicator + has_more hint ✅
  - Tailwind utilities only ✅
  - File header per convention ✅
- [x] **Vitest unit test `frontend/tests/unit/governance/AuditLogViewer.test.tsx`** — 3 tests (filter inputs + chain badge / empty state / one-row + pagination) ✅

### 3.4 US-5: AuditChainBadge component ✅
- [x] **Create `frontend/src/features/governance/components/AuditChainBadge.tsx`**
  - DoD: `useQuery({ queryKey: CHAIN_VERIFY_QUERY_KEY, queryFn: ..., enabled: false })` — manual trigger via Verify chain button ✅
  - 4 states: idle / Verifying / ✓ Valid · N entries / ✗ Broken at id=X · N entries / ❌ Verify failed (alert) ✅
  - Tailwind badge styling (no inline) ✅
  - File header per convention ✅
- [x] **Wire AuditChainBadge into AuditLogViewer header** — top-right of title row ✅
- [x] **Vitest unit test `frontend/tests/unit/governance/AuditChainBadge.test.tsx`** — 4 tests (idle / valid / broken / error) ✅

### 3.5 US-1 stub fixup (post-US-4 complete) ✅
- [x] **AuditLogViewer.tsx Day 1 stub replaced with real impl** — `pages/governance/index.tsx` import resolves to real US-4 component; TypeScript strict pass ✅

### 3.6 Day 3 wrap ✅
- [x] **Vite bundle size check** — main JS 240.78 kB (under 290 kB budget by 49 kB; +0.03 kB vs Day 2) ✅
- [x] **Vitest 64 → 75 (+11; target ≥+6 hit 183%)** ✅
- [x] **tsc strict 0 errors** (TS6310 pre-existing AD-Frontend-Tsconfig D24 carryover unchanged) ✅
- [x] **Update progress.md Day 3 entry** ✅
- [x] **Commit + push**
  - Message: `feat(frontend, sprint-57-9): Day 3 — US-4 AuditLogViewer + auditService + useAuditLog + US-5 AuditChainBadge`

---

## Day 4 — US-6 4-page TanStack Migration + Closeout

> **MANDATORY discipline per Sprint 57.7 + 57.8 lessons (PR #116 + #118 carry-forward)**:
> Day 4 closeout MUST run **full pytest suite + full Vitest + full Playwright + 9 V2 lints + 3 backend lint sweep** BEFORE pushing any closeout commit. NOT subset.
> See plan §Risks H + §Sprint 57.7+57.8 lesson carry-forward.

### 4.1 US-6: 4-page TanStack hook creation ✅
- [x] **4 hook files created** — `useCostSummary` / `useSLAReport` / `useAdminTenants` / `useTenantSettings` + bonus `useTenantSettingsSave` mutation hook (5 NEW hooks total) ✅
  - All single-source `*_QUERY_KEY_BASE` exports ✅
  - All consume `fetchWithAuth` via swapped services ✅
  - Day 4 D-PRE-13 lesson: hook test pattern reuse from Day 2/3 → 0 brittle-test fix needed ✅
  - File headers per convention with US-6 MHist ✅

### 4.2 US-6: 4-page component refactor ✅
- [x] **CostOverview.tsx** — drop useEffect+loadData; use `useCostSummary({tenantId, currentMonth})`; `error.message`+`refetch()` retry path ✅
- [x] **SLAOverview.tsx** — same pattern + Tailwind migration (drop ALL inline styles) + violations badge `data-testid` preserved ✅
- [x] **admin-tenants page + 3 children** — TenantListFilters / TenantListPagination / TenantListTable each consume `useAdminTenants` hook + store query state ✅
- [x] **TenantSettingsView.tsx** — `useTenantSettings(tenantId)` hook ✅
- [x] **TenantSettingsEditForm.tsx** — NEW `tenantId` prop + `useTenantSettingsSave` mutation hook (drop store.save) ✅

### 4.3 US-6: 4 Zustand store reductions ✅
- [x] **4 stores reduced to UI-only state** ✅
  - costStore: `currentMonth + setMonth + reset` only (dropped data/loading/error/loadData) ✅
  - slaStore: `currentMonth + setMonth + reset` only ✅
  - adminTenantsStore: `query (filter+pagination) + setFilter + setPagination + reset` only (dropped items/total/loading/error/loadData) ✅
  - tenantSettingsStore: `tenantId + setTenantId + reset` only (dropped data/saving/saveError/loadData/save) ✅
  - Each store MHist entry with Sprint 57.9 US-6 reason ✅
  - Store API surface tests assert dropped keys NOT present (regression sentinel) ✅

### 4.4 Full validation sweep (BLOCKER for Day 4 commit) ✅
- [x] **Backend pytest full suite** — **1622 collected** baseline maintained (no backend changes this sprint) ✅
- [x] **Vitest full suite** — 75 → **93** in 3.65s (**+18**, target ≥+8 hit **225%**) ✅
- [x] **Playwright full suite** — **27/27 passed** in 7.3s (was 27 baseline; 5 governance auth-gate fixed via seedAuthJwt + 4 StrictMode-aware mock retries fixed via retryClicked flag) ✅
- [x] **9 V2 lints** — 9/9 green in 1.00s ✅
- [x] **Frontend full lint sweep** — ESLint silent + tsc strict 0 errors + Vite build clean (240.86 kB main; under 290 kB budget by 49 kB) ✅
- [x] **Backend full lint sweep** — flake8 silent + black --check 300 files clean ✅
- [x] **LLM SDK leak check** — 0 leaks (check_llm_sdk_leak.py) ✅

### 4.5 US-6 stretch: Playwright e2e cases NEW (governance-real-ship.spec.ts) 🚧 DEFERRED
- [ ] **Create `frontend/tests/e2e/governance/governance-real-ship.spec.ts`** 🚧 DEFERRED to Phase 57.10+ — Day 4 budget consumed by 4-page migration test fixups (StrictMode mock + auth gate seed); existing 27 Playwright e2e cover governance approvals reviewer flow (5 cases via Sprint 53.6) which now run authenticated post-Day 4 fix. AD-Governance-RealShip-E2E logged for follow-up sprint.

### 4.6 Retrospective.md (Q1-Q7 mandatory format per Sprint 57.7+57.8 + sprint-workflow.md) ✅
- [x] **Create `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-9/retrospective.md`** ✅
  - Q1 What went well: existing 53.5 components rich reuse / TanStack 4-page closure / 6 USs delivered
  - Q2 calibration ratio: actual_hr / 10.5 commit = ratio (target [0.85, 1.20] band)
  - Q3 lessons: governance HITL ship is V2 core differentiation visible / TanStack migration = mechanical pattern reuse confirmation / NEW class `frontend-feature-with-migration` 1st-app data point
  - Q4 audit debt: closures (AD-Cost-Dashboard-UseQuery + AD-Front-1 partial via TanStack interim) + new ADs if any
  - Q5 Phase 57.10+ candidates: verification real ship (~10-12 hr — same pattern reuse) / 5 deferred pages from 16.md V2 Ship Timeline / SOC 2 + SBOM ~12-15 hr / Status Page + APAC ~10-12 hr / Tier 1 IaC ~15-20 hr
  - Q6 solo-dev policy held; 5 active CI checks
  - Q7 N/A SKIP — feature ship sprint NOT spike (no design note required)

### 4.7 Memory snapshot ✅
- [x] **Created `~/.claude/projects/.../memory/project_phase57_9_governance_ship.md`** (~80 lines) ✅
- [x] **Updated MEMORY.md index entry** with 57.9 entry after 57.8 (chronological) ✅

### 4.8 Doc syncs (3/4; CLAUDE.md deferred to post-merge closeout PR per 57.7+57.8 pattern) ✅
- [x] **`.claude/rules/sprint-workflow.md` calibration matrix +1 row** — NEW row `frontend-feature-with-migration` 0.50 HYBRID 1-data-point baseline ratio 1.00 bullseye + Modification History entry ✅
- [ ] **`CLAUDE.md` 3 surgical edits** 🚧 DEFERRED to post-merge closeout PR — Per Sprint 57.7+57.8 pattern (PR #115/#117/#119 mirror): main HEAD row needs merged commit SHA which is unknown until PR merges → all 3 CLAUDE.md edits bundled in post-merge closeout PR
- [x] **`SITUATION-V2-SESSION-START.md` §9 + §11 update** ✅
  - §9 milestone +1 row Sprint 57.9 entry inserted before 57.8 row (newest-first) ✅
  - §11 Last Updated header refreshed; Previous = 57.8 + 57.7 demoted ✅
- [x] **`16-frontend-design.md` V2 Ship Timeline update** ✅
  - "5 已 ship pages" → **"6 已 ship pages"** (governance promoted from "2 priority") ✅
  - "2 priority Phase 57.9+ ship" → **"1 priority Phase 57.10 ship"** (governance closed; verification remaining) ✅
  - Sprint slot mapping: Phase 57.9 ✅ DONE entry added with calibration 1.00 bullseye notation ✅
  - Modification History entry added; Reality framing notes Sprint 57.9 closes AD-Cost-Dashboard-UseQuery via 4-page TanStack migration ✅

### 4.9 PR + closeout sync (post-merge)
- [ ] **Open main PR** 🚧 PENDING USER INSTRUCT
  - Per CLAUDE.md "破壞性操作前必問" + rolling planning gate
  - Draft prepared: Title `Sprint 57.9 — Governance Real Ship + TanStack Query 4-page Migration (6 USs + frontend-feature-with-migration calibration class)`
- [ ] **Wait CI green** 🚧 PENDING — after PR open
- [ ] **Solo-dev squash merge** 🚧 PENDING — wait user explicit "merge"
- [ ] **Post-merge: closeout PR for CLAUDE.md sync** 🚧 PENDING — mirror PR #115/#117/#119 pattern

### 4.10 User decision points pending Day 4.6
- [ ] **Phase 57.10+ direction** 🚧 PENDING USER INSTRUCT
  - Top candidates per Q5 retrospective: verification real ship (highest ROI — same pattern reuse as 57.9) / 5 deferred pages from 16.md / SOC 2 / Status Page / Tier 1 IaC

---

## 重要備註

### Rolling planning 紀律自檢(每 day 結束 + Day 4 closeout 必檢)

- ☐ 沒預寫多個未來 sprint plan(Phase 57.10 plan/checklist 留 user 選定 scope 才起草;只列 5 candidate)
- ☐ 沒跳過 plan/checklist 直接 code(全在 sprint-57-9-{plan,checklist}.md 框架內)
- ☐ 沒刪除未勾選的 [ ] 項目(US-1 stub fix 若延後 + reason)
- ☐ 沒在 retrospective.md 寫具體未來 sprint task(Q5 only candidate list)

### V2 紀律 9 項自檢(每 commit + 每 PR)

per plan §Sprint 57.7+57.8 lesson carry-forward + `.claude/rules/anti-patterns-checklist.md`:
1. Server-Side First — N/A frontend sprint
2. LLM Provider Neutrality — frontend 不 import LLM SDK(N/A; backend 維持 0 leak)
3. CC Reference 不照搬 — N/A
4. 17.md Single-source — useApprovals queryKey APPROVALS_QUERY_KEY single-source export;auditService 不重複 backend contract
5. 11+1 範疇歸屬 — frontend 不在 11 範疇;features/* 結構維持
6. 04 anti-patterns — AP-2 (no orphan):routes.config.ts governance entry active 後 pages/governance 必 reachable;AP-9 (verification):governance ship 含 ApprovalCard pipeline 不 bypass HITL;AP-3 (no scattering):governance components 集中 features/governance/
7. Sprint workflow — plan → checklist → Day 0 三-prong → code → progress → retro
8. File header convention — 全新 file 必有 header + MHist;1-line max per MHist entry
9. Multi-tenant rule — frontend tenant_id 從 JWT 解(consume 57.7 IAM);backend governance/audit endpoints enforce via require_approver_role / require_audit_role + get_current_tenant

### Sprint 57.7 D19 + 57.8 D13 cascade lesson 強制執行(此 sprint 必行)

**Day 4 closeout pre-push checklist**(plan §Risks H):
1. ☐ 跑 full `python -m pytest`(NOT `tests/unit/` only)
2. ☐ 跑 full `npm run test`(Vitest 全量)
3. ☐ 跑 full `npm run e2e`(Playwright 全量)
4. ☐ 跑 full backend 3 lint(flake8 + black + isort on `src` + `tests`)
5. ☐ 跑 full frontend lint + typecheck + build
6. ☐ 跑 V2 9 lints(`scripts/lint/run_all.py`)
7. ☐ Vite bundle size 確認 ≤ 290 kB main
8. ☐ Pre-existing dev DB pollution check (Sprint 57.8 D13 carry-forward)

**只跑 1+2+3+4+5+6+7+8 全綠才 push closeout commit**;single test scope shortcut 禁止。

### Open Items / Carry-forward(填入 retrospective Q4 + Q4.1)

- [ ] AD-Sprint-Plan-10 NEW class `frontend-feature-with-migration` 0.50 baseline 1-data-point opens(此 sprint 1st app)
- [ ] AD-Front-1 polling-vs-SSE: TanStack refetchInterval = interim solution; SSE upgrade 仍 candidate Phase 58.x carryover
- [ ] AD-Cat10-VisualVerifier+Frontend-Panel(verification real ship Phase 57.10 候選)
- [ ] AD-Cat11-Multiturn / SSEEvents / ParentCtx(54.2 deferred 仍 open Phase 56+)
- [ ] AD-CI-6 Phase 58 production launch
- [ ] AD-RBAC-FullDBOnly Phase 58.x(57.7 carryover)
- [ ] AD-IAM-{SAML, MFA, RefreshToken, SCIM} Phase 58.x(57.7 carryover)
- [ ] AD-Frontend-{AuthUX, Sentry} Phase 58.2+(57.7 carryover)
- [ ] AD-Frontend-h1-Convention(57.8 carryover)
- [ ] AD-Test-Tenant-Code-Pollution(57.8 carryover)
- [ ] AD-Plan-3-h1-Grep meta-rule(57.8 carryover)
- [ ] AD-Cost-Dashboard-ChildrenTailwind(57.8 carryover — admin-tenants error block batch)

### Sprint workflow §Step 5 expansion candidate

Per Sprint 57.7 D19 + 57.8 D13 lessons:在 `.claude/rules/sprint-workflow.md` §Step 5(Day 4 closeout)新增:
> Day 4 closeout 必須 full suite 跑 backend pytest + frontend Vitest + Playwright + 3 lint sweep + V2 9 lints,**禁止只跑 `tests/unit/` 或單檔 lint**;另須檢查 dev DB pre-existing pollution。違反 = closeout commit 拒絕 push。

此 expansion 候選 fold-in Phase 57.10 closeout(若 57.9 retro Q3 確認 lesson 仍 generalizable)。
