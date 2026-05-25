# Sprint 57.43 — AD-AdminTenants-Tenants-Table-Rebuild

**Phase**: 57 (Frontend SaaS)
**Sprint id**: 57.43
**Drafted**: 2026-05-25 (Day 0)
**Branch**: `feature/sprint-57-43-admin-tenants-rebuild`
**Class**: `frontend-mockup-strict-rebuild` 0.60 (9th data point; 8-pt mean 0.71 at lower band edge per Sprint 57.42 retro — `When to adjust` lower-trigger had MET — but per `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier` ACTIVATED 2026-05-25, the systematic below-band signal is now attributed to agent-delegation factor not class drift → KEEP 0.60 class baseline + apply `agent_factor = 0.55` orthogonally). **1st validation sprint under newly ACTIVATED `agent_factor` modifier.**
**Mirror template**: Sprint 57.42 plan (§ structure 0-9, 9 main sections; 4-day Day-numbering Day 0/1/2/2.5/3).

---

## 0. Sprint Goal

Single-domain sprint to **fully rebuild `/admin-tenants` from mockup `page-admin.jsx:322-410 TenantsPage`** (Tenants `.page-head` + 4 KPI strip (Active tenants / Total seats / Agents / Anomalies) + 9-col tenants table with 9 fixture rows: TENANT/PLAN/REGION/SEATS/AGENTS/RUNS/STATUS/CREATED + ⋯ actions). Resolves the 2026-05-25 22-page drift audit's now-#1 priority CATASTROPHIC verdict on `/admin-tenants` (post Sprint 57.42 `/memory` rebuild, this is the 4th of 5 original CATASTROPHIC routes; ~12-15 hr est per `AD-AdminTenants-Tenants-Table-Rebuild`). Production currently shows only filter form (State/Plan/Search) + "No tenants match current filter" empty state + "0-0 of 0" pagination — 9 of mockup's 9 fixture rows + 4 KPIs entirely absent. Backend GET list endpoint already wired (Sprint 57.4 closed 2026-05-07).

### Drift audit context

Per `claudedocs/5-status/drift-audit-2026-05-25/audit-report.md` row 21:

- **Mockup design** (`reference/design-mockups/page-admin.jsx:322-410 TenantsPage`, ~90 lines incl. `TENANTS = [...]` fixture array line 323-333): `.page-head` (Tenants title + sub + `/admin/tenants` route-pill + actions) + 4 KPI strip (Active tenants / Total seats / Agents / Anomalies) + `<table className="table">` 9-col (TENANT/PLAN/REGION/SEATS/AGENTS/RUNS/STATUS/CREATED + actions ⋯) with `TENANTS.map(t => ...)` 9 fixture rows.
- **Production reality** (`frontend/src/pages/admin-tenants/index.tsx` Sprint 57.4 vintage + 3 components `TenantListFilters` / `TenantListTable` / `TenantListPagination`): only filter form (State / Plan / Search) + table with empty state "No tenants match current filter" + pagination "0-0 of 0". No `.page-head` proper (only `AppShellV2 pageTitle="Tenants"` chrome). No 4 KPI strip. No mockup 9-col schema. Backend GET list endpoint already exists from Sprint 57.4 (consumed by `useTenantList()` hook).

### Outer scope decision (Day 0 final)

Mockup is single-page (no outer tabs). Production is also single-page (no outer tabs). **No outer-tab disposition decision needed** (unlike Sprint 57.40 audit-log preserve / 57.41 timeline preserve / 57.42 §1.4 Option B 2-tab DROP precedent).

Mockup omits filter form; production has Filters (State/Plan/Search). Per Karpathy §3 + AP-2 retire decision §1.4: production-only Filters bar will be retired in the rebuild + carryover AD opened for Phase 58+ if admin-level filtering required.

---

## 1. Background

### 1.1 Why a strict-rebuild not a verbatim-css-repoint

Production `/admin-tenants` is Sprint 57.4 vintage shadcn-utility — Sprint 57.39 Phase-2 epic targeted /governance + /verification + /redaction + /error-policy and didn't include admin-tenants. The remaining drift is fundamentally structural:

- No `.page-head` mockup vocabulary (production uses `AppShellV2 pageTitle` chrome only)
- No 4 KPI strip (mockup-distinct ops dashboard)
- Table schema entirely different (current: Filters → empty table → Pagination; mockup: direct 4 KPI + 9-col table without filter form)
- Production backend GET list returns Tenant objects but UI renders empty state because page logic discards them when filter form is in default state

These cannot be added via a CSS swap — they require new React components with mockup schema mapping (TenantsPageHeader, TenantsStatsStrip×4 KPI, TenantsTable 9-col) + retire of Sprint 57.4 vintage Filters/Pagination components. Hence `frontend-mockup-strict-rebuild` 0.60 class (9th application — same class as Sprint 57.23/57.24v2/57.25/57.27/57.37A/57.40/57.41/57.42).

### 1.2 What stays unchanged (preserved wiring)

| Layer | Preserved | Source |
|-------|-----------|--------|
| Auth gate | `<RequireAuth>` wrap | `frontend/src/pages/admin-tenants/index.tsx` (current) → new keeps wrap |
| Shell wrap | `<AppShellV2 pageTitle={t("nav.adminTenants")}>` | same → preserved with same page title (Day 0 Prong 2 verify exact key) |
| Backend GET list endpoint | `GET /api/v1/admin/tenants` (Sprint 57.4 wired; 9-test coverage) | Day 0 Prong 3 Schema verify column shape |
| `useTenantList` TanStack hook | Day 0 Prong 2 confirm exists; reused if response shape compatible with mockup row schema (TENANT/PLAN/REGION/SEATS/AGENTS/RUNS/STATUS/CREATED) — feeds `<TenantsTable>` real-data path | `frontend/src/features/admin-tenants/hooks/useTenantList.ts` (TBD Day 0 confirm) |
| `tenantService` | Day 0 Prong 2 confirm; reused for table real-data path | `frontend/src/features/admin-tenants/services/tenantService.ts` (TBD Day 0) |
| `types.ts` `Tenant` interface | Reused if shape compatible | `frontend/src/features/admin-tenants/types.ts` |
| URL/path | `/admin-tenants` route in `routes.config.ts` | no change |
| Sidebar nav | nav entry `/admin-tenants` | no change |

### 1.3 What changes (rebuild scope)

| Layer | Old | New (per mockup) |
|-------|-----|------------------|
| `/admin-tenants` route content | TenantListFilters + TenantListTable (empty) + TenantListPagination | Single `<AdminTenantsView />` (no nested) |
| Page intro | (none — only AppShell pageTitle chrome) | `.page-head` (Tenants title + sub "Multi-tenant orchestration" + `/admin/tenants` route-pill + 3 actions Invite / Search / New tenant) |
| 4 KPI strip | (none) | `<TenantsStatsStrip>` 4 KPI Card (Active tenants / Total seats / Agents / Anomalies) |
| 9-col table | TenantListTable empty schema | `<TenantsTable>` 9-col mockup schema (TENANT/PLAN/REGION/SEATS/AGENTS/RUNS/STATUS/CREATED + ⋯) — real-data via `useTenantList()` per §1.4 Option B OR fixture-fallback Option A |
| Filters bar (State/Plan/Search) | `TenantListFilters.tsx` | **Retired** per Karpathy §3 — mockup omits filter form (admin-level filtering deferred to Phase 58+ + AD opened) |
| Pagination ("0-0 of 0") | `TenantListPagination.tsx` | **Retired** per Karpathy §3 — mockup shows direct rows (no pagination); admin-level pagination deferred to Phase 58+ if tenant count > 100 |
| Empty state ("No tenants match current filter") | `TenantListTable` empty branch | **Removed** — Real backend data wired direct OR fixture if Day 0 Prong 3 reveals schema gap |
| `TenantListTable.tsx` | Sprint 57.4 vintage 4-col table | **Deleted** per Karpathy §3 — replaced by `TenantsTable` 9-col |

### 1.4 Backend wiring decision (Day 0 final)

**Mockup** is fixture-only (9 hardcoded TENANTS const at `page-admin.jsx:323-333`). **Production** has backend GET list endpoint wired since Sprint 57.4. Two options:

- **Option A**: Use fixture (`_fixtures.ts`) verbatim from mockup; AP-2 banner declares deferred backend wire. Same pattern as Sprint 57.40/41/42 (rebuild fixture-first; backend wire as Phase 58+ if needed).
- **Option B** (selected): Wire to backend GET list endpoint immediately via `useTenantList` hook (Sprint 57.4 already exists). Mockup 9 fixture rows replaced with live data. Fallback to fixture (Option A) only if Day 0 Prong 3 Schema verify reveals response shape mismatch (e.g. mockup KPI counts `agents` / `anomalies` not in backend response).

**Selected: B**. Reasoning: backend list endpoint exists from Sprint 57.4 (US-1 GET + 9 tests). Sprint 57.42 retro Q3 Lesson: backend-wire is mockup-faithful when endpoint exists; fixture-first only when backend gap. AP-2 banner used only for fields backend doesn't yet expose (e.g. KPI strip metrics derived client-side from list length + per-tenant fields).

**Risk mitigation**: Day 0 Prong 3 Schema verify `tenant_list_response` envelope shape matches mockup TENANT row schema. If schema mismatch (e.g. backend returns `seats_purchased` but mockup column is `SEATS`) → field mapping helper in adapter; if backend missing fields (e.g. `agents` count not in response) → AP-2 banner + Phase 58+ extension AD.

### 1.5 Class baseline + 1st validation under `agent_factor = 0.55` (ACTIVATED 2026-05-25)

`frontend-mockup-strict-rebuild` 0.60 (9th application). Effective ratio under newly ACTIVATED `agent_factor = 0.55`: **0.60 × 0.55 = 0.33 expected**.

| Sprint | Page | Ratio (actual/committed) | agent_factor | Notes |
|--------|------|--------------------------|--------------|-------|
| 57.23 | auth flow rebuild (7 routes) | 0.59 | 1.0 (pre-activation) | 1st app below band 0.26 |
| 57.24 v2 | cost-dashboard rebuild | 1.19 | 1.0 | 2nd app top of band |
| 57.25 | sla-dashboard rebuild | 0.88 | 1.0 | 3rd app in band |
| 57.27 | overview rebuild | ≈0.95 | 1.0 | 4th app in band |
| 57.37A | loop-debug rebuild | ≈1.18 | 1.0 | 5th app top of band |
| 57.40 | governance rebuild | ≈0.36 | 1.0 (agent-delegated; modifier not yet activated) | 6th app below band |
| 57.41 | verification rebuild | ≈0.18 | 1.0 (agent-delegated; modifier not yet activated) | 7th app below band |
| 57.42 | memory rebuild | ≈0.33 | 1.0 (agent-delegated; modifier proposal) | 8th app below band (activation criteria MET) |
| **57.43** | **admin-tenants rebuild** | **TBD** | **0.55 (ACTIVATED 2026-05-25)** | **9th app — 1st validation under modifier** |

If Sprint 57.43 `actual/committed-with-agent-factor` lands in [0.85, 1.20] band → modifier validated; KEEP 0.55 per 3-sprint window rule. If < 0.7 → 1st rollback-trigger data point (need 2 sprints < 0.7 to tighten to 0.45). If > 1.20 → 1st upper rollback-trigger (single-data-point caution → KEEP 0.55 still per `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier rollback rule`).

---

## 2. User Stories

**US-1**: As a tenant admin, I want to see `/admin-tenants` with mockup-faithful Tenants `.page-head` + 4 KPI overview + 9-col tenants table so that I can monitor tenant fleet at a glance per mockup design (resolves drift audit row 21 🔴 CATASTROPHIC verdict).

**US-2**: As a frontend engineer, I want the production `/admin-tenants` to consume backend GET list endpoint (Sprint 57.4 already wired) via `useTenantList()` so that real tenant data renders in mockup-shape and the Phase-2 epic CATASTROPHIC count drops 2 → 1 (only `/tenant-settings` remaining).

**US-3**: As a project maintainer, I want Sprint 57.43 retro Q2 to record `agent-delegated: yes` + `actual/committed-with-agent-factor` ratio as 1st validation data point under newly ACTIVATED `agent_factor = 0.55` per `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier`, so that the modifier's 3-sprint rollback window opens with traceable evidence.

---

## 3. Technical Specifications

### 3.1 Component decomposition (per mockup `page-admin.jsx:322-410`)

| Component | Location | Lines (est) | Mockup ref |
|-----------|----------|-------------|------------|
| `AdminTenantsView` | `features/admin-tenants/components/AdminTenantsView.tsx` | ~85 | container (mounts header + stats + table; `useTenantList()` data flow) |
| `TenantsPageHeader` | `features/admin-tenants/components/TenantsPageHeader.tsx` | ~80 | `.page-head` line 336-355 — title + sub + route-pill + 3 actions (Invite / Search / New tenant; AP-2 stubs Day 1) |
| `TenantsStatsStrip` | `features/admin-tenants/components/TenantsStatsStrip.tsx` | ~75 | 4 KPI line 357-380 — Active tenants / Total seats / Agents / Anomalies (compute from `useTenantList()` data + AP-2 banner for backend-missing fields like `anomalies`) |
| `TenantsTable` | `features/admin-tenants/components/TenantsTable.tsx` | ~155 | 9-col table line 381-410 — header row + 9 row `TENANTS.map(t => ...)`; status Badge tone dispatch (active/paused/trial) |

(Approximate per audit-report quote; Day 0 Prong 2 will read mockup excerpt to confirm exact line counts + props shape.)

### 3.2 Fixture port

`features/admin-tenants/_fixtures.ts` ~30 lines: verbatim TENANTS const + KPI calc helpers (Active/Seats/Agents/Anomalies). Used only when Day 0 Prong 3 reveals backend schema gap (per §1.4 Option B fallback).

### 3.3 Backend wire (Option B per §1.4)

`<AdminTenantsView>` calls `useTenantList()` (Sprint 57.4 existing hook); passes result to `<TenantsStatsStrip>` (KPI compute) + `<TenantsTable>` (row map). If backend response shape mismatch with mockup row schema → adapter function in `AdminTenantsView` maps backend `Tenant` → mockup row shape.

### 3.4 Orphan delete (per Karpathy §3)

- `TenantListFilters.tsx` (Sprint 57.4 vintage; Filters bar retired)
- `TenantListPagination.tsx` (Pagination retired)
- `TenantListTable.tsx` (Sprint 57.4 vintage 4-col schema; replaced by `TenantsTable` 9-col)
- Associated Vitest specs (TBD Day 0 grep count — estimated ~3 spec files)
- Associated e2e specs (TBD Day 0 grep — if `admin-tenants-page.spec.ts` exists)

### 3.5 Page restructure

`pages/admin-tenants/index.tsx` restructured to mount `<AdminTenantsView />` only; outer Routes / Auth wrap / AppShellV2 unchanged (matches Sprint 57.42 §1.4 Option B page-restructure pattern).

### 3.6 Verbatim-CSS protocol

HEX_OKLCH_BASELINE estimated +0-2 bump (consistent with Sprint 57.40-42 pattern; verbatim-CSS protocol +0 actual when components use `var(--*)` refs only). 4 NEW components should reuse existing mockup-ui primitives (Card / Badge / Button / Icon — post 57.40+41+42 critical-mass). 0 new primitive lifts predicted.

### 3.7 Vitest spec additions

Estimate +4-8 NEW spec files (consistent with Sprint 57.40 +15 / 57.41 +9 / 57.42 +12 cohort; slightly smaller component count → smaller minimum). Each NEW component gets dedicated spec; 1 integration spec for `<AdminTenantsView>` data flow.

### 3.8 Audit report update

`claudedocs/5-status/drift-audit-2026-05-25/audit-report.md` 8 edits per Sprint 57.40-42 pattern: row 21 verdict 🔴 → ✅ PARITY + summary 19→20 PARITY / 2→1 CATASTROPHIC + Key findings post-57.43 paragraph + Effort estimate strike (`/admin-tenants rebuild` line 113) + Recommendations renumber + Carryover #1 CLOSED + footer status + (optional 8th edit per closeout precedent).

### 3.9 route-sweep before/after

`frontend/scripts/route-sweep.mjs` re-point OUT_DIR to `sprint-57-43-admin-tenants-rebuild` slug. Day 0 + Day 2.5 sweep before/after with sha256 diff per Sprint 57.40-42 precedent. 24-route sweep (16 derived from `routes.config.ts` + extras) — `/admin-tenants` is the expected CHANGED route.

---

## 4. File Change List

### NEW files (4 components + 1 fixtures + ~4-8 Vitest)

- `frontend/src/features/admin-tenants/components/AdminTenantsView.tsx`
- `frontend/src/features/admin-tenants/components/TenantsPageHeader.tsx`
- `frontend/src/features/admin-tenants/components/TenantsStatsStrip.tsx`
- `frontend/src/features/admin-tenants/components/TenantsTable.tsx`
- `frontend/src/features/admin-tenants/_fixtures.ts` (fallback per §1.4 Option B)
- `frontend/tests/unit/admin-tenants/AdminTenantsView.test.tsx`
- `frontend/tests/unit/admin-tenants/TenantsPageHeader.test.tsx`
- `frontend/tests/unit/admin-tenants/TenantsStatsStrip.test.tsx`
- `frontend/tests/unit/admin-tenants/TenantsTable.test.tsx`
- (optional) `frontend/tests/unit/admin-tenants/_fixtures.test.tsx` (if KPI compute helpers warrant)

### MODIFIED files

- `frontend/src/pages/admin-tenants/index.tsx` (restructure to single `<AdminTenantsView />` mount; preserves auth + shell wrap)
- `frontend/scripts/route-sweep.mjs` (re-point OUT_DIR to sprint-57-43-admin-tenants-rebuild slug; Day 2.5)
- `claudedocs/5-status/drift-audit-2026-05-25/audit-report.md` (8 edits per Sprint 57.40-42 pattern)
- `.claude/rules/sprint-workflow.md` (matrix MHist + `agent_factor` 1st validation note in §Active block; Day 3 closeout)

### DELETED files (Karpathy §3 orphan delete)

- `frontend/src/features/admin-tenants/components/TenantListFilters.tsx`
- `frontend/src/features/admin-tenants/components/TenantListTable.tsx`
- `frontend/src/features/admin-tenants/components/TenantListPagination.tsx`
- Associated Vitest specs (TBD Day 0 grep ~3 files)
- Associated e2e if exists (TBD Day 0 grep)

**Net Day 1 delta estimate**: +~510 / -~280 ≈ **NET +230 lines** (smaller than 57.42's NET -154 since fewer components + less orphan-delete; admin-tenants has 3 vintage components vs 57.42's 11 orphans).

---

## 5. Acceptance Criteria

- **AC1**: All 4 NEW components render per mockup excerpts (`page-admin.jsx:336-410`). Mockup-fidelity guard exit 0 (HEX_OKLCH_BASELINE ≤ +2 bump per §3.6 estimate).
- **AC2**: `/admin-tenants` drift audit verdict 🔴 → ✅ PARITY (audit-report.md row 21 update); summary 19→20 PARITY / 2→1 CATASTROPHIC remaining.
- **AC3**: Vitest 486 → ≥ 490 (+4 minimum, +8 target — within 57.40-42 cohort range +9 to +15). All GREEN.
- **AC4**: 24-route sweep 0 unintended regressions; only `/admin-tenants` intentional CHANGED; ≤ 3 sub-300-byte noise (consistent with Sprint 57.40-42 envelope).
- **AC5**: 3-way evidence pair (BEFORE / AFTER / MOCKUP) staged in `claudedocs/4-changes/sprint-57-43-admin-tenants-rebuild/before-after/`. AFTER ≥ 75% of MOCKUP size (structural fidelity threshold per Sprint 57.40-42 pattern).
- **AC6**: Karpathy §3 orphan delete completed (3 Sprint 57.4 vintage components + associated specs + e2e if exists).
- **AC7**: Backend GET wire (Option B §1.4) verified — `useTenantList()` consumed by `<AdminTenantsView>` (OR fallback Option A fixture-first if Day 0 Schema verify reveals mismatch + Phase 58+ AD opened).
- **AC8**: Sprint plan §Workload retro records `agent-delegated: yes` + `actual/committed-with-agent-factor` ratio as 1st validation data point under newly ACTIVATED `agent_factor = 0.55` per `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier`.

---

## 6. Deliverables

- [ ] **US-1**: TenantsPageHeader + TenantsStatsStrip + TenantsTable + AdminTenantsView render per mockup (Day 1 agent-delegated code-implementer)
- [ ] **US-2**: Backend GET wire via `useTenantList()` (Option B §1.4); Phase-2 epic CATASTROPHIC count 2 → 1
- [ ] **US-3**: Retro Q2 records 1st validation data point under `agent_factor = 0.55`; matrix MHist entry + `agent_factor` validation note in §Active block

---

## 7. Dependencies & Risks

### Dependencies

- **Backend GET list endpoint** `GET /api/v1/admin/tenants` (Sprint 57.4 wired; 9-test coverage). Day 0 Prong 3 Schema verify response shape.
- **`useTenantList`** TanStack hook (Sprint 57.4). Day 0 Prong 2 confirm exists + signature.
- **mockup-ui primitives** (Card / Badge / Button / Icon / Field — post 57.40+41+42 critical-mass; 0 new primitive lifts predicted).
- **routes.config.ts** entry for `/admin-tenants` (existing; no change).

### Risks

| Risk class | Mitigation |
|------------|------------|
| Backend response schema vs mockup TENANT row schema mismatch (e.g. `created_at` ISO format vs mockup display; `agents` count not in response) | **Day 0 Prong 3 Schema verify CONFIRMED gap (D-DAY0-6 🔴 RED)**: backend `TenantListItem` lacks `seats / region / agents / runs24 / status` (5 of 9 mockup columns); `AD-AdminTenants-Backend-Schema-Extension` elevated 🟡 → 🔴 BLOCKING. **§1.4 Option A fixture-first LOCKED IN** (was conditional; now selected). Backend wire deferred to Phase 58+; Day 1 components consume `_fixtures.ts` only. See `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-43/progress.md` §Day 0 D-DAY0-6 for full schema gap analysis. |
| 1st `agent_factor 0.55` validation ratio drifts > 1.20 or < 0.7 | Per `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier rollback rule`: single-data-point caution KEEP 0.55 this sprint; 2 sprints < 0.7 → tighten to 0.45; ≥ 2 sprints > 1.20 → drop modifier. Day 4 retro records validation outcome. |
| Karpathy §3 orphan delete catches consumers (e.g. e2e spec, external doc) | Day 0 Prong 1 + Day 1 grep before delete; carryover AD if doc references found (similar to Sprint 57.42 D-DAY1-3 types.ts MHist refresh) |
| Phase-2 epic post Sprint 57.43 still has 1 CATASTROPHIC `/tenant-settings` (15-20 hr, largest remaining scope) | Sprint 57.44 plan candidate; sprint sequencing per rolling planning §6 |

---

## 8. Workload Calibration (four-segment form per Sprint 57.43+ `agent_factor` activation)

**Bottom-up est ~12-15 hr → class-calibrated commit ~7.5-9 hr (mult 0.60) → agent-adjusted commit ~4-5 hr (agent_factor 0.55)**

Class: `frontend-mockup-strict-rebuild` 0.60 (9th data point)
agent_factor: 0.55 (1st validation data point under ACTIVATED 2026-05-25 modifier per `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier`)
**agent-delegated: yes** (per Day 0 strategic confirmation 2026-05-25 — Day 1 NEW components + Day 2 Vitest specs via code-implementer agent, consistent with Sprint 57.40/41/42 cohort)

**Per-day breakdown** (approximate):
- Day 0: ~50 min (3-prong + before sweep + baselines)
- Day 1: ~60-90 min (4 NEW components + fixtures + page restructure + orphan-delete 3 vintage components via code-implementer agent)
- Day 2: ~30-45 min (4-8 Vitest specs + audit report PARITY update via code-implementer agent)
- Day 2.5: ~15 min (after sweep + 3-way evidence pair assembly)
- Day 3: ~30-40 min (retro Q1-Q7 + matrix MHist + memory subfile + closeout commits)

**Total target**: ~4-5 hr (within agent-adjusted commit envelope).

### Day 4 retrospective Q2 must record (per `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier` tracking discipline):

1. `actual/bottom-up` ratio (existing)
2. `actual/committed-with-agent-factor` ratio (new committed = X × 0.60 × 0.55)
3. **`agent-delegated: yes`** (explicit tag — 1st data point under newly activated modifier)

If `actual/committed-with-agent-factor` ratio in [0.85, 1.20] band → modifier validated; KEEP 0.55. If outside band → record observation; rollback rule applies per 3-sprint window (single-data-point caution).

---

## 9. Carryover Audit Debt (anticipated; finalized at Day 3 retro)

| AD | Description | Target |
|----|-------------|--------|
| `AD-AdminTenants-Filter-Form-Phase58-Migrate` | Sprint 57.43 retires Filters bar (State/Plan/Search) per Karpathy §3 (mockup omits). Phase 58+ admin-level filtering on `/admin-tenants/admin` separate route OR collapsible `<details>` panel | Phase 58+ |
| `AD-AdminTenants-Pagination-Phase58-Migrate` | Sprint 57.43 retires pagination per Karpathy §3 (mockup shows direct 9 rows). Phase 58+ if tenant count > 100 | Phase 58+ |
| `AD-AdminTenants-Backend-Schema-Extension` | If Day 0 Prong 3 reveals backend schema gap (e.g. `agents` count / `anomalies` count fields missing) → backend extension required for full KPI compute | Phase 58+ |
| `AD-AdminTenants-New-Tenant-Modal-Phase58` | Mockup `.page-head` "New tenant" action is Sprint 57.43 AP-2 stub (`window.alert`) | Phase 58+ |
| `AD-AdminTenants-Invite-Modal-Phase58` | Mockup `.page-head` "Invite" action is Sprint 57.43 AP-2 stub | Phase 58+ |
| `AD-AdminTenants-Search-Header-Action-Phase58` | Mockup `.page-head` "Search" icon-button is Sprint 57.43 AP-2 stub (Filters bar retired; this is a quick-search overlay UI) | Phase 58+ |
| `AD-AdminTenants-Row-Actions-Phase58` | Mockup table row ⋯ kebab action menu Sprint 57.43 AP-2 stub | Phase 58+ |
| `AD-TenantSettings-6-Tab-Rebuild` (carried) | Last remaining CATASTROPHIC post Sprint 57.43; ~15-20 hr; mockup `page-admin.jsx:411+ TenantSettings`. Sprint 57.44 candidate. | Sprint 57.44 |

---

**Modification History (newest-first)**:
- 2026-05-25: Initial creation (Sprint 57.43 Day 0 plan draft) — single-domain admin-tenants rebuild; 1st validation under `agent_factor = 0.55`
