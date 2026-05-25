# Sprint 57.43 — AD-AdminTenants-Tenants-Table-Rebuild — Checklist

> [Sprint plan](./sprint-57-43-plan.md)
>
> **Branch**: `feature/sprint-57-43-admin-tenants-rebuild`
> **Class**: `frontend-mockup-strict-rebuild` 0.60 (9th data point; 1st validation under `agent_factor = 0.55` ACTIVATED 2026-05-25)
> **Mirror template**: Sprint 57.42 checklist (Day 0/1/2/2.5/3 structure)

---

## Day 0 — Three-Prong Verify + Baselines

### 0.1 Plan + checklist draft commit
- [ ] **Commit plan + checklist drafts**
  - DoD: `git log --oneline -1` shows commit subject `chore(plan): Sprint 57.43 plan + checklist draft (Day 0)` and includes only `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-43-plan.md` + `sprint-57-43-checklist.md`
  - Verify: `git diff main --stat` shows 2 NEW files

### 0.2 Prong 1 — Path verify (per `.claude/rules/sprint-workflow.md §Step 2.5 Prong 1`)
- [ ] **Verify file paths in plan §4 File Change List are correct**
  - DoD: For each path in §4, run Glob; expect 0 results for NEW, 1 result for MODIFIED/DELETED
  - Verify: `Glob frontend/src/features/admin-tenants/components/AdminTenantsView.tsx` returns 0 (NEW)
  - Verify: `Glob frontend/src/pages/admin-tenants/index.tsx` returns 1 (MODIFIED)
  - Verify: `Glob frontend/src/features/admin-tenants/components/TenantList*.tsx` returns 3 (DELETED targets)
- [ ] **Verify mockup excerpt location**
  - DoD: `reference/design-mockups/page-admin.jsx` line 322-410 contains `TenantsPage` function + `TENANTS = [...]` fixture
  - Verify: `Grep "TenantsPage\|TENANTS = \[" reference/design-mockups/page-admin.jsx` returns 2 hits

### 0.3 Prong 2 — Content verify (per `.claude/rules/sprint-workflow.md §Step 2.5 Prong 2`)
- [ ] **Verify `useTenantList` hook exists + signature (plan §1.2)**
  - DoD: Hook file exists at expected location; signature returns `{ data, isLoading, error }` shape
  - Verify: `Grep "export.*useTenantList\|function useTenantList" frontend/src/features/admin-tenants/`
- [ ] **Verify `tenantService` exists + GET list method (plan §1.2)**
  - DoD: Service has `listTenants()` or equivalent method calling `GET /api/v1/admin/tenants`
  - Verify: `Grep "listTenants\|getTenants\|admin/tenants" frontend/src/features/admin-tenants/services/`
- [ ] **Verify `types.ts` Tenant interface shape (plan §1.2)**
  - DoD: Tenant type has at minimum `id` / `display_name` / `plan` / `state` / `created_at`
  - Verify: Read `frontend/src/features/admin-tenants/types.ts` (cap 50 lines)

### 0.4 Prong 2.5 — Child component tree depth audit (per `.claude/rules/sprint-workflow.md §Step 2.5 Prong 2.5` AD-Plan-5 fold-in)
- [ ] **Enumerate child component tree depth=2 from `pages/admin-tenants/index.tsx`**
  - DoD: List all `import.*@/features/admin-tenants` consumers; identify shadcn-utility token residue / inline style escape comments / outer wrapper artifact / fullBleed drop sites
  - Verify: `Grep -n "import.*@/features/admin-tenants" frontend/src/pages/admin-tenants/index.tsx`
- [ ] **Per child file anti-pattern grep**
  - DoD: For each enumerated child, grep for `bg-card|text-foreground|border-border|bg-muted|text-muted-foreground|style={{` patterns
  - Verify: `Grep "bg-card\|text-foreground\|border-border" frontend/src/features/admin-tenants/components/` — non-zero indicates token residue (FIX-012/015 precedent)

### 0.5 Prong 3 — Schema verify (per `.claude/rules/sprint-workflow.md §Step 2.5 Prong 3`)
- [ ] **Verify backend `GET /api/v1/admin/tenants` response schema vs mockup row shape**
  - DoD: List response fields; map to mockup columns TENANT/PLAN/REGION/SEATS/AGENTS/RUNS/STATUS/CREATED
  - Verify: `Grep "tenant_list_response\|class TenantListResponse\|@router.get" backend/src/api/v1/admin/tenants.py`
- [ ] **Detect schema gaps (mockup columns not in backend response)**
  - DoD: Catalog gaps (e.g. backend may not return `agents` count / `runs` count); plan §1.4 fallback decision verified
  - Verify: Catalog in progress.md Day 0 entry as `D-DAY0-N` findings

### 0.6 Mockup excerpt Read for Day 1 components
- [ ] **Read mockup `page-admin.jsx:322-410 TenantsPage` excerpt for component decomposition**
  - DoD: Confirm 4 components per plan §3.1 (TenantsPageHeader / TenantsStatsStrip / TenantsTable / AdminTenantsView); confirm line counts
  - Verify: Read `reference/design-mockups/page-admin.jsx` offset=320 limit=100

### 0.7 Before-sweep + baselines
- [ ] **Update route-sweep.mjs OUT_DIR to sprint slug**
  - DoD: `route-sweep.mjs` OUT_DIR re-points to `claudedocs/4-changes/sprint-57-43-admin-tenants-rebuild/screenshots/{before,after}/`
  - Verify: `Grep "sprint-57-4" frontend/scripts/route-sweep.mjs` shows `sprint-57-43-admin-tenants-rebuild`
- [ ] **Run 24-route before-sweep (24 PNGs to before/)**
  - DoD: 24 PNG files exist at `claudedocs/4-changes/sprint-57-43-admin-tenants-rebuild/screenshots/before/`
  - Verify: `Glob claudedocs/4-changes/sprint-57-43-admin-tenants-rebuild/screenshots/before/*.png` returns 24
- [ ] **Baseline records**
  - DoD: Day 0 progress.md notes Vitest baseline (486 passing), HEX_OKLCH_BASELINE current value, mockup-fidelity guard exit 0, route-sweep before-shape baseline
  - Verify: `(cd frontend && npm run test --silent 2>&1 | tail -5)` shows passing count 486

### 0.8 Drift findings catalog + go/no-go
- [ ] **Catalog Day 0 D-DAY0-N findings in progress.md**
  - DoD: All Prong 1+2+2.5+3 findings logged with severity (GREEN/YELLOW/RED); plan §Risks updated if scope shift > 20%
  - Verify: progress.md Day 0 entry has `## Drift findings (Day 0)` header with D-DAY0-1, D-DAY0-2, ... format
- [ ] **Day 0 closeout commit**
  - DoD: `git log --oneline -1` shows commit subject `chore(plan): Sprint 57.43 Day 0 — 3-prong + 24-PNG before + baselines`
  - Verify: `git diff main --stat` shows progress.md + route-sweep.mjs + 24 PNGs

---

## Day 1 — NEW Components + Page Restructure + Orphan Delete (code-implementer agent-delegated)

### 1.1 NEW component: `AdminTenantsView` (container)
- [ ] **Create `AdminTenantsView.tsx` (~85 lines)**
  - DoD: Mounts TenantsPageHeader + TenantsStatsStrip + TenantsTable; calls `useTenantList()` (Option B per §1.4) OR fallback fixtures (Option A); passes data to children
  - Verify: TypeScript strict 0 errors; component file header convention compliant (Purpose/Category/Scope per `.claude/rules/file-header-convention.md`)

### 1.2 NEW component: `TenantsPageHeader` (.page-head)
- [ ] **Create `TenantsPageHeader.tsx` (~80 lines)**
  - DoD: Verbatim port `page-admin.jsx:336-355` mockup `.page-head` — title "Tenants" + sub "Multi-tenant orchestration" + route-pill `/admin/tenants` + 3 actions (Invite / Search / New tenant — Day 1 AP-2 stubs `window.alert(...)`)
  - Verify: Browser DOM contains `<div class="page-head">` + 3 `<button>` (i18n keys per existing convention)

### 1.3 NEW component: `TenantsStatsStrip` (4 KPI strip)
- [ ] **Create `TenantsStatsStrip.tsx` (~75 lines)**
  - DoD: 4 KPI Card per mockup `page-admin.jsx:357-380` — Active tenants / Total seats / Agents / Anomalies; KPI compute from `useTenantList()` data (active = tenants.filter(state="active").length; total seats = tenants.sum(seats); agents/anomalies — AP-2 banner if backend missing)
  - Verify: Renders 4 `<Card>` with KPI labels + numeric values

### 1.4 NEW component: `TenantsTable` (9-col table)
- [ ] **Create `TenantsTable.tsx` (~155 lines)**
  - DoD: Verbatim port `page-admin.jsx:381-410` mockup `<table className="table">` 9-col schema (TENANT/PLAN/REGION/SEATS/AGENTS/RUNS/STATUS/CREATED + ⋯ actions); status Badge tone dispatch (active=primary / paused=warning / trial=memory); rows map `tenants.map(t => <tr>...)`
  - Verify: Browser DOM contains `<table>` with 9-col `<thead>` + N-row `<tbody>`

### 1.5 NEW: `_fixtures.ts` (fallback per §1.4 Option B)
- [ ] **Create `_fixtures.ts` (~30 lines)**
  - DoD: Verbatim port `page-admin.jsx:323-333` TENANTS const + KPI compute helpers; used only when Day 0 Prong 3 reveals backend schema gap
  - Verify: Exports `TENANTS_FIXTURE` array of 9 entries + helper functions

### 1.6 Page restructure (`pages/admin-tenants/index.tsx`)
- [ ] **Restructure `pages/admin-tenants/index.tsx` to single `<AdminTenantsView />` mount**
  - DoD: Preserves `<RequireAuth>` + `<AppShellV2 pageTitle={t("nav.adminTenants")}>` wrap; replaces inner content with `<AdminTenantsView />`; outer Routes unchanged
  - Verify: File ~30-40 lines (down from current ~70+); no `<TenantListFilters>` / `<TenantListTable>` / `<TenantListPagination>` imports

### 1.7 Orphan delete (Karpathy §3) — 3 vintage components
- [ ] **Delete `TenantListFilters.tsx` + `TenantListTable.tsx` + `TenantListPagination.tsx`**
  - DoD: 3 files removed via `git rm`; 0 remaining imports anywhere (`grep -rn "TenantListFilters\|TenantListTable\|TenantListPagination" frontend/src/` returns 0)
  - Verify: `git status --short` shows 3 D entries

### 1.8 Orphan delete — associated Vitest specs
- [ ] **Delete Vitest specs for retired components (TBD Day 0 grep count)**
  - DoD: For each deleted component, corresponding `*.test.tsx` removed; co-located with parent delete in same commit (per Sprint 57.42 Lesson 2)
  - Verify: `git status --short` D-count matches

### 1.9 Orphan delete — e2e if exists
- [ ] **Check + delete e2e `admin-tenants-page.spec.ts` if exists**
  - DoD: If file exists at `frontend/e2e/` → delete; if not → note in progress.md
  - Verify: `Glob frontend/e2e/admin-tenants*.ts` returns 0 (post-delete) or N/A

### 1.10 Day 1 closeout commit
- [ ] **Commit Day 1 (NEW + MODIFIED + DELETED via code-implementer agent)**
  - DoD: `git log --oneline -1` shows commit subject `feat(frontend, sprint-57-43): Day 1 — 4 NEW components + fixtures + page restructure + 3 orphan delete (code-implementer agent)`
  - Verify: `git diff main --stat` shows NET +~230 lines per plan §4 estimate; LLM SDK leak grep 0

---

## Day 2 — Vitest Specs + Audit Report PARITY (code-implementer agent-delegated)

### 2.1 Vitest spec NEW files
- [ ] **Create Vitest spec for `AdminTenantsView` (~5-8 tests; integration data-flow)**
  - DoD: Mock `useTenantList()`; renders TenantsPageHeader + TenantsStatsStrip + TenantsTable; tests data flow + loading state + error state
  - Verify: `(cd frontend && npx vitest run tests/unit/admin-tenants/AdminTenantsView)` passes
- [ ] **Create Vitest spec for `TenantsPageHeader` (~3-5 tests)**
  - DoD: Renders title/sub/route-pill/3 actions; AP-2 click handler firings
  - Verify: vitest pass
- [ ] **Create Vitest spec for `TenantsStatsStrip` (~4-6 tests)**
  - DoD: Renders 4 KPI Card; KPI compute correctness (active count / total seats / agents / anomalies); AP-2 banner conditional
  - Verify: vitest pass
- [ ] **Create Vitest spec for `TenantsTable` (~5-8 tests)**
  - DoD: Renders 9-col header; renders N rows; status Badge tone dispatch; empty state (if no tenants); `getAllByText` pattern for ambiguous strings (per Sprint 57.42 Lesson 5)
  - Verify: vitest pass
- [ ] **Vitest baseline progression**
  - DoD: Vitest count 486 → ≥ 490 (AC3 minimum +4; target +8 per plan §3.7)
  - Verify: `(cd frontend && npm run test --silent 2>&1 | tail -3)` shows new passing count

### 2.2 Audit report PARITY update
- [ ] **Update `claudedocs/5-status/drift-audit-2026-05-25/audit-report.md` 8 edits per Sprint 57.40-42 pattern**
  - DoD: row 21 verdict 🔴 → ✅ PARITY; summary `19→20 PARITY / 2→1 CATASTROPHIC remaining`; Key findings post-57.43 paragraph; Effort estimate strike row 113 (`/admin-tenants rebuild`); Recommendations renumber (post-57.43); Carryover #1 CLOSED; footer status updated
  - Verify: `Grep "admin-tenants" claudedocs/5-status/drift-audit-2026-05-25/audit-report.md` shows updated verdict markers

### 2.3 Day 2 closeout commit
- [ ] **Commit Day 2 (Vitest specs + audit PARITY via code-implementer agent)**
  - DoD: `git log --oneline -1` shows commit subject `test(frontend, sprint-57-43): Day 2 — N NEW Vitest specs + audit report PARITY (code-implementer agent)`
  - Verify: `git diff HEAD~1 --stat` shows NEW spec files + audit-report.md edits

---

## Day 2.5 — After Sweep + 3-Way Evidence Pair

### 2.5.1 After-sweep run
- [ ] **Run 24-route after-sweep**
  - DoD: 24 PNG files at `claudedocs/4-changes/sprint-57-43-admin-tenants-rebuild/screenshots/after/`
  - Verify: `Glob claudedocs/4-changes/sprint-57-43-admin-tenants-rebuild/screenshots/after/*.png` returns 24

### 2.5.2 sha256 diff vs before
- [ ] **Compute before/after sha256 diff per route**
  - DoD: 24 routes classified IDENTICAL / CHANGED; only `/admin-tenants` intentional CHANGED; ≤ 3 sub-300-byte noise routes; 0 unintended regressions
  - Verify: progress.md Day 2.5 entry has sweep table with byte-diff column

### 2.5.3 3-way evidence pair staging
- [ ] **Stage BEFORE / AFTER / MOCKUP screenshots at `before-after/` subfolder**
  - DoD: 3 PNG files (admin-tenants-before.png / admin-tenants-after.png / admin-tenants-mockup.png) staged for retrospective evidence
  - Verify: `Glob claudedocs/4-changes/sprint-57-43-admin-tenants-rebuild/before-after/*.png` returns 3
- [ ] **AFTER / MOCKUP byte ratio**
  - DoD: AFTER bytes ≥ 75% of MOCKUP bytes (structural PARITY threshold per Sprint 57.40-42 pattern; Sprint 57.42 achieved 92%)
  - Verify: progress.md Day 2.5 entry records BEFORE / AFTER / MOCKUP KB sizes + ratio

### 2.5.4 Day 2.5 closeout commit
- [ ] **Commit Day 2.5 (after sweep + 3-way evidence)**
  - DoD: `git log --oneline -1` shows commit subject `chore(sweep, sprint-57-43): Day 2.5 — after sweep + 3-way evidence pair`
  - Verify: `git diff HEAD~1 --stat` shows 24 PNG additions + 3 evidence pair PNGs

---

## Day 3 — Retro Q1-Q7 + Matrix MHist + Memory + Closeout

### 3.1 Retrospective Q1-Q7 per 6-question format
- [ ] **Write `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-43/retrospective.md`**
  - DoD: 7 questions answered per Sprint 57.42 retrospective.md template (Q1 What went well / Q2 What didn't go well + Calibration / Q3 Lessons / Q4 Audit debt deferred / Q5 Next steps / Q6 Verbatim-CSS protocol / Q7 Solo-dev policy)
  - Q2 MUST record: `actual/bottom-up` ratio + `actual/committed-with-agent-factor` ratio + **`agent-delegated: yes`** tag (per `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier` tracking discipline)
  - Verify: File exists; Q2 has 3-line tracking record

### 3.2 Matrix MHist entry + `agent_factor` 1st validation note
- [ ] **Update `.claude/rules/sprint-workflow.md` matrix MHist + §Active Agent Delegation Factor Modifier**
  - DoD: New MHist entry at top of matrix MHist list (newest-first); `frontend-mockup-strict-rebuild` row Status column updated with 9th data point ratio; §Active block "Activation history" appends 1st validation result; rollback rule status tracked
  - Verify: `Grep "57.43" .claude/rules/sprint-workflow.md` shows ratio entries

### 3.3 Memory subfile + MEMORY.md update
- [ ] **Create `memory/project_phase57_43_admin_tenants_rebuild.md`**
  - DoD: Subfile per Sprint 57.42 template (Goal / Shipped / Calibration ratio / Phase-2 epic progress / Sweep evidence / D-DAY-X drift findings / Anomalies / Lessons / Commits / Related)
  - Verify: File exists at global memory path
- [ ] **Update `memory/MEMORY.md` with Sprint 57.43 quality pointer entry**
  - DoD: Pointer entry ~250-300 char (per Sprint Closeout policy quality pointer principle); subfile link + 1-sentence topic + keywords
  - Verify: MEMORY.md has new entry above Sprint 57.42 entry (newest-first)

### 3.4 CLAUDE.md sync (optional per Sprint Closeout policy)
- [ ] **Update CLAUDE.md `Current Sprint` row + `Last Updated` footer (navigator-level only)**
  - DoD: Only timeless milestone updates allowed; NO sprint-by-sprint history table cell additions (per REFACTOR-001 + §Sprint Closeout policy)
  - Verify: `git diff CLAUDE.md` shows ≤ 2 line changes (Current Sprint + Last Updated)

### 3.5 Day 3 closeout commit + push + PR
- [ ] **Commit Day 3 closeout**
  - DoD: `git log --oneline -1` shows commit subject `chore(sprint-57-43): Day 3 closeout — retro Q1-Q7 + matrix MHist + memory + agent_factor 0.55 1st validation`
  - Verify: `git diff HEAD~1 --stat` shows retrospective.md + sprint-workflow.md + memory files + CLAUDE.md
- [ ] **Push + open PR**
  - DoD: Branch pushed; PR opened against main with title `feat(frontend, sprint-57-43): /admin-tenants Tenants table full mockup-fidelity rebuild (closes drift audit 2026-05-25 #1 priority CATASTROPHIC)` + co-author footer
  - Verify: `gh pr view --json url --jq .url` returns PR URL
- [ ] **CI green confirmation**
  - DoD: 5 required CI checks all green (Backend E2E + Frontend E2E chromium + Lint+Type+Test PG16 + v2-lints + + Frontend E2E Tests if it triggers)
  - Verify: `gh pr checks --watch=$false` shows all `success`
- [ ] **Local cleanup post-merge**
  - DoD: After user merges → `git checkout main && git pull --ff-only && git branch -D feature/sprint-57-43-admin-tenants-rebuild`
  - Verify: `git branch` shows only main

---

## Pre-Commit Self-Check (per `.claude/rules/sprint-workflow.md §Before Commit Checklist`)

Before each Day's commit:

- [ ] **Backend lint (if backend touched — Sprint 57.43 is frontend-only; skip)**
  - `(cd backend && black . && isort . && flake8 . && mypy .)`
- [ ] **V2 architecture lints (if backend touched — skip)**
  - `python scripts/lint/run_all.py`
- [ ] **Frontend lint + build (Sprint 57.43 every Day 1+)**
  - `(cd frontend && npm run lint && npm run build)` — **MUST run WITHOUT `--silent`** (per AD-Pre-Push-Lint-Silent-Suppression-Anti-Pattern; redirect with `2>&1 | tail -20` if noise too much)
- [ ] **Frontend Vitest (Sprint 57.43 every Day 2+)**
  - `(cd frontend && npm run test)`
- [ ] **Mockup-fidelity guard (Day 1+ when components change)**
  - `(cd frontend && node scripts/check-mockup-fidelity.mjs)` exit 0
- [ ] **No prohibited imports** (LLM SDK leak in `agent_harness/**` — N/A frontend-only)
- [ ] **File header convention** (NEW files have Purpose/Category/Scope/MHist per `.claude/rules/file-header-convention.md`)
- [ ] **MHist entries ≤ 100 chars per line** (E501 budget)
- [ ] **Anti-patterns checklist 11 points** (per `.claude/rules/anti-patterns-checklist.md` PR template)

---

## Acceptance criteria verification (Day 3 closeout)

Map to plan §5:

- [ ] **AC1**: 4 NEW components render per mockup; mockup-fidelity guard exit 0; HEX_OKLCH_BASELINE ≤ +2 bump
- [ ] **AC2**: `/admin-tenants` drift audit verdict 🔴 → ✅ PARITY; summary 19→20 PARITY / 2→1 CATASTROPHIC
- [ ] **AC3**: Vitest 486 → ≥ 490 (target +8) all GREEN
- [ ] **AC4**: 24-route sweep 0 unintended regressions; only `/admin-tenants` intentional; ≤ 3 sub-300-byte noise
- [ ] **AC5**: 3-way evidence pair AFTER ≥ 75% of MOCKUP size
- [ ] **AC6**: Karpathy §3 orphan delete completed (3 Sprint 57.4 vintage components + specs + e2e if exists)
- [ ] **AC7**: Backend GET wire (Option B §1.4) OR fallback Option A + Phase 58+ AD
- [ ] **AC8**: Retro Q2 records `agent-delegated: yes` + `actual/committed-with-agent-factor` ratio (1st validation under `agent_factor = 0.55`)

---

**Modification History (newest-first)**:
- 2026-05-25: Initial creation (Sprint 57.43 Day 0 checklist draft) — mirror Sprint 57.42 Day 0/1/2/2.5/3 structure
