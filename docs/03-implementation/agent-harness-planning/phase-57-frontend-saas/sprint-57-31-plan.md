# Sprint 57.31 — AD-Cost-Dashboard-Verbatim-Repoint

**File**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-31-plan.md`
**Purpose**: Plan for Sprint 57.31 — third Phase-2 per-page verbatim-CSS re-point (`/cost-dashboard`), continuing the Phase-2 epic after Sprint 57.29 (`/overview`) and Sprint 57.30 (`/chat-v2`).
**Category**: Sprint planning / Phase 57+ Frontend SaaS
**Scope**: Phase 57+ Frontend SaaS — Phase-2 per-page re-point epic, 3rd application
**Created**: 2026-05-23
**Last Modified**: 2026-05-23
**Status**: Draft → awaiting user approval

> **Modification History**
> - 2026-05-23: Initial draft (Sprint 57.31 Day 0) — cost-dashboard Phase-2 verbatim re-point per user selection 2026-05-23

---

## Sprint Goal

Land the **third Phase-2 per-page verbatim-CSS re-point** on `/cost-dashboard` (operator-facing rich dashboard — daily cost / token / SLO monitoring). This sprint provides the **3rd data point for `AD-Sprint-Plan-frontend-verbatim-bimodal-watch`** (Sprint 57.30 carryover) — same rich-dashboard shape as Sprint 57.29 `/overview` but distinct sprint to test whether the 57.29 ≈1.0 / 57.30 ≈0.40 spread is bimodal or sampling noise.

`/cost-dashboard` is a 7-file route (6 widget components + 1 page index): CostOverview KPI row + CategoryBarsCard / ProviderMixCard charts + CostBreakdownTable / TenantTopTable + MonthPicker filter. Sprint 57.24 v2 already did the **structural rebuild** under `frontend-mockup-strict-rebuild` 0.60 class (ratio 1.19 top of band). Sprint 57.31 = verbatim CSS re-point on top of that rebuilt scaffolding — same method validated on `/overview` (57.29) and `/chat-v2` (57.30).

---

## Background

### Why Sprint 57.31 (this sprint)

Sprint 57.30 closed the 2nd Phase-2 per-page re-point on `/chat-v2` with PARITY verdict + Day 5 orphan cleanup bonus (-116.87 KB bundle from Radix DropdownMenu drop). The retrospective Q2 flagged a **calibration anomaly**: `frontend-verbatim-css-repoint` 0.60 baseline 2-data-point showed 57.29 ≈1.0 (in band middle) vs 57.30 ≈0.40 (below band by 0.45) — 2-pt mean 0.70 lower edge of band. Sprint 57.30 retro Q4 logged `AD-Sprint-Plan-frontend-verbatim-bimodal-watch` to track the 3rd data point.

Sprint 57.31 picks `/cost-dashboard` because:

1. **Bimodal hypothesis test** — `/cost-dashboard` shares the rich-dashboard shape with Sprint 57.29 `/overview` (KPI stats + chart cards + table card). If 57.29's high ratio (≈1.0) was driven by "rich-dashboard shape", 57.31 should land near 1.0 too — confirming bimodal. If 57.31 lands near 0.40-0.50 (like 57.30), the bimodal hypothesis weakens and the 0.60 baseline is simply too generous for the entire `frontend-verbatim-css-repoint` class regardless of page shape. Either outcome is informative.

2. **User-value ROI** — `/cost-dashboard` is daily-used by operators monitoring spend / token / quota. PARITY upgrade meaningfully impacts the production UX.

3. **Phase-1 alignment baseline already strong** — Sprint 57.24 v2 rebuilt cost-dashboard with strict-rebuild approach using Sprint 57.24 v2 primitives (PageHead / Stat / CardShell / AreaChart / BarTrack / Spark / BackendGapBanner). Phase-2 verbatim CSS re-point = swap any remaining translated-Tailwind or shadcn-default usage to mockup `.grid-stats` / `.grid-main` / `.bar-track` / `.table` CSS class form.

4. **Mockup source consolidation pattern (NEW finding from Day 0 探勘 2026-05-23)** — `/cost-dashboard` mockup lives at `reference/design-mockups/page-admin.jsx:201` (the `CostPage` const), NOT a dedicated `page-cost.jsx` file. This is a structural divergence from `/overview` (`page-overview.jsx`) and `/chat-v2` (`page-chat.jsx`). The mockup author co-located admin-scope pages (admin / cost / tenants / models / etc.) in one file. The verbatim port treats `CostPage` as the canonical visual source — line range `page-admin.jsx:201-…`.

### Scope boundaries

**IN scope**:
- `/cost-dashboard` 7 production files re-point: `pages/cost-dashboard/index.tsx` + 6 components in `features/cost-dashboard/components/` (CostOverview / CategoryBarsCard / ProviderMixCard / CostBreakdownTable / TenantTopTable / MonthPicker).
- Any new mockup CSS classes needed (audit during Day 0 Prong 2; likely all present in `styles-mockup.css` from Sprint 57.28 byte-identical foundation).
- 22-route regression sweep before/after + `/cost-dashboard` fidelity verification.

**OUT of scope**:
- The 11 remaining 🟡 AppShellV2 routes (orchestrator / loop-debug / memory / state-inspector / governance / verification / sla-dashboard / admin-tenants / tenant-settings / compaction / + 3 ⚪ crash-fix candidates).
- Backend extensions (cost data ingestion, ledger schema, monthly cron, etc. — Sprint 56.3 SLA + Cost Ledger already shipped Phase 1).
- Sprint 57.30 carryover ADs except `AD-Sprint-Plan-frontend-verbatim-bimodal-watch` (this sprint feeds the 3rd data point).

### Class baseline — REUSE `frontend-verbatim-css-repoint` 0.60 (3rd application)

3rd application of the class baseline. HYBRID weighted blend for Sprint 57.31:

| Component | Class | Multiplier | Weight |
|-----------|-------|------------|--------|
| Day-0 三-prong + before-baseline | `audit-cycle` | 0.85 | ~10% |
| 7 components re-point (4 widget cards + 1 table + 1 picker + 1 page) | `frontend-verbatim-css-repoint` | 0.50-0.60 | ~70% |
| 22-route sweep + fidelity verify | `frontend-verbatim-css-repoint` | 0.50 | ~10% |
| Closeout + retro + docs | `closeout` | 0.80 | ~10% |
| **HYBRID blended baseline** | | **≈ 0.55-0.60** | |

Bottom-up estimate: ~7 files × 1-2 hr each + Day 0 ~2 hr + Day 4 ~2 hr = **~12-18 hr**.
Calibrated commit: ~7-10 hr (multiplier ≈ 0.55-0.60 blended).

Per `AD-Sprint-Plan-frontend-verbatim-bimodal-watch`: this is the 3rd data point. KEEP 0.60 baseline this sprint per `When to adjust` 3-sprint window rule. After Sprint 57.31 closeout, evaluate:
- If ratio ≈ 0.80-1.10 → bimodal CONFIRMED (rich-dashboard upper band); propose class split.
- If ratio ≈ 0.40-0.55 → bimodal WEAKENS; propose lowering baseline 0.60→0.50.
- If ratio ≈ 0.60-0.75 → in-band, no change needed.

### What is preserved (NOT changed)

- Sprint 57.24 v2 cost-dashboard structural rebuild (PageHead / Stat / CardShell / AreaChart / BarTrack / Spark / BackendGapBanner mockup-ui primitives).
- All component-logic layer: hooks, TanStack queries (`useCostMtd` / `useCostBreakdown` / `useTenantTop` / etc.), state, props, event handlers, a11y attrs, `data-testid`s.
- Backend integration (`costService` / `/api/v1/cost-summary` / `/api/v1/cost-ledger`).
- All Sprint 57.24 v2 Vitest specs that test logic / data binding / TanStack invalidation.
- `routes.config.ts` cost-dashboard entry.

### What gets changed (this sprint scope)

**Day 1 — page-head + KPI row** (2 files):
- `pages/cost-dashboard/index.tsx` — page-head verbatim re-point matching `page-admin.jsx:203-219` CostPage page-head (title "Cost Ledger" / subtitle + `.route-pill` + `<Badge tone="warning">admin scope</Badge>` + page-actions: By tenant + CSV).
- `features/cost-dashboard/components/CostOverview.tsx` — 4-stat `.grid-stats` row verbatim re-point matching mockup KPI shape (Spend MTD / Tokens MTD / Cost per run / Cache hit rate).

**Day 2 — chart cards row** (3 files):
- `features/cost-dashboard/components/CategoryBarsCard.tsx` — "Spend by category" 6-row `.bar-track` verbatim re-point.
- `features/cost-dashboard/components/ProviderMixCard.tsx` — provider mix card (mockup may have this as `.grid-main` widget; verify Day 0 Prong 2 vs mockup line range).
- `features/cost-dashboard/components/MonthPicker.tsx` — filter pill (small file; verify mockup MonthPicker location).

**Day 3 — table cards** (2 files):
- `features/cost-dashboard/components/CostBreakdownTable.tsx` — `.table` verbatim re-point + per-row badges + `.bar-track` for quota%.
- `features/cost-dashboard/components/TenantTopTable.tsx` — "Spend by tenant" `.table` MTD top-8 verbatim re-point matching mockup `page-admin.jsx:259-294` shape.

**Day 4 — Regression + fidelity verify + closeout**.

---

## User Stories

### Group A — Day 0 plan + 三-prong + before-baseline (PRE-WORK)

- **US-A1** (Plan + Checklist): As the AI, I draft Sprint 57.31 plan + checklist mirroring Sprint 57.30 format before any code runs. Acceptance: this file + `sprint-57-31-checklist.md` exist with full content.
- **US-A2** (Day-0 三-prong): As the AI, I run path-verify + content-verify + (no schema) on plan-time assertions; key Prong-2 grep checks: confirm mockup `CostPage` location in `page-admin.jsx:201+`; identify exact mockup line ranges for KPI stats / chart cards / tables; check `styles-mockup.css` has `.grid-stats` / `.grid-main` / `.bar-track` / `.table` classes; verify Sprint 57.24 v2 cost-dashboard component file structure matches plan.
- **US-A3** (Before-baseline screenshots): Playwright capture 22 AppShellV2 routes + `/cost-dashboard` filter-open state + table-anomaly-row state before any code change.

### Group B — page-head + KPI row (Day 1)

- **US-B1** (page-head verbatim): As an operator on `/cost-dashboard`, the page-head matches mockup `page-admin.jsx:203-219` verbatim — title "Cost Ledger" + subtitle "Range 12 · …" + `.route-pill /cost-dashboard` + `<Badge tone="warning">admin scope</Badge>` + actions (By tenant filter button + CSV export). Acceptance: `pages/cost-dashboard/index.tsx` page-head re-pointed; computed-style matches mockup.
- **US-B2** (KPI grid-stats verbatim): As an operator, the 4 KPI cards (Spend MTD / Tokens MTD / Cost per run / Cache hit rate) match mockup `.grid-stats` shape — each with `<Stat>` primitive + sparkline + tone-coded delta. Acceptance: `CostOverview.tsx` re-pointed using mockup-ui `<Stat>` + `<Spark>` primitives (already verbatim from Sprint 57.29 — reuse, don't re-port).

### Group C — chart cards row (Day 2)

- **US-C1** (CategoryBarsCard verbatim): "Spend by category" 6-row vertical bar list matches mockup `page-admin.jsx:228-251` — each row with color dot + name + cost + `.bar-track` pct fill. Acceptance: `CategoryBarsCard.tsx` re-pointed.
- **US-C2** (ProviderMixCard verbatim): Provider mix breakdown matches mockup canonical (Day 0 to identify exact mockup line range or treat as production-only if mockup has no equivalent — confirm AP-2 BackendGapBanner appropriate). Acceptance: `ProviderMixCard.tsx` re-pointed OR backend-gap-banner annotated.
- **US-C3** (MonthPicker verbatim): Month filter pill matches mockup convention (small file; verify mockup design — if mockup uses inline-style + `.btn ghost`, port verbatim; if no mockup equivalent, document as production-only). Acceptance: `MonthPicker.tsx` re-pointed.

### Group D — table cards (Day 3)

- **US-D1** (CostBreakdownTable verbatim): Cost breakdown matches mockup `.table` semantic + per-row visual treatment. Acceptance: re-pointed.
- **US-D2** (TenantTopTable verbatim): "Spend by tenant" top-8 table matches mockup `page-admin.jsx:259-294` — `.table` + `.row` cells + plan `<Badge>` + token + cost + quota% color-coded text + `.bar-track` quota fill + anomaly `<Badge tone="danger" dot>`. Acceptance: re-pointed.
- **US-D3** (Vitest comprehensive): All cost-dashboard Vitest specs pass; adapt any spec drift from translated DOM → verbatim DOM (likely small surface area since Sprint 57.24 v2 specs already test data binding + testids, not class names).

### Group E — Regression sweep + fidelity verify + closeout (Day 4)

- **US-E1** (22-route sweep): 0 catastrophic / 0 structural; 3 ⚪ pre-existing fails (`/subagents` `/memory` `/verification`) classified explicitly NOT a regression.
- **US-E2** (`/cost-dashboard` fidelity verify): Mockup-vs-prod computed-style + Playwright; **🟢 PARITY** verdict logged in REPOINT-REPORT.md.
- **US-E3** (Full gates): tsc / lint / Vitest / Playwright / build / check:mockup-fidelity / route-sweep all green.
- **US-E4** (Closeout): retrospective.md Q1-Q7 + memory snapshot + CLAUDE.md / MEMORY.md / `sprint-workflow.md §Matrix` 3rd-data-point row + `next-phase-candidates.md` + PR + merge + branch cleanup.

---

## Technical Specifications

### Verbatim re-point method (unchanged from Sprint 57.29-57.30)

For every component touched in Groups B-D:

1. Read mockup canonical source line range (`page-admin.jsx` CostPage section).
2. Identify visual layer: CSS class names + inline-style literals.
3. Read production `.tsx`; identify translated-Tailwind / shadcn-default usage.
4. Re-point: replace translated Tailwind with mockup class names; replace shadcn defaults with mockup inline-style literals (copied byte-for-byte); preserve all component-logic layer.
5. Add file-level eslint-disable `no-restricted-syntax` with the standard verbatim escape-hatch comment IF inline-style literals are used.
6. Update file header MHist (1-line per Sprint 55.3 char budget rule).

### Mockup source mapping (Day 0 Prong 2 to confirm exact line ranges)

| Component | Mockup source | Notes |
|-----------|---------------|-------|
| `pages/cost-dashboard/index.tsx` page-head | `page-admin.jsx:203-219` | Title + subtitle + `.route-pill` + `admin scope` Badge + actions |
| `CostOverview.tsx` KPI row | `page-admin.jsx:221-225` | 4-stat `.grid-stats` |
| `CategoryBarsCard.tsx` | `page-admin.jsx:228-251` | 6-row `.bar-track` |
| `ProviderMixCard.tsx` | TBD Day 0 Prong 2 | Verify mockup line range OR mark production-only |
| `MonthPicker.tsx` | TBD Day 0 Prong 2 | Verify mockup line range OR mark production-only |
| `CostBreakdownTable.tsx` | TBD Day 0 Prong 2 | Possibly merged with TenantTopTable in mockup |
| `TenantTopTable.tsx` | `page-admin.jsx:255-294` | `.table` + per-row badges + quota `.bar-track` |

### Reuse mockup-ui primitives (Karpathy §2 simplicity)

The Sprint 57.24 v2 + Sprint 57.29 verbatim primitive set (`PageHead` / `Stat` / `CardShell` / `AreaChart` / `BarTrack` / `Spark` / `BackendGapBanner` from `mockup-ui.tsx`) is already verbatim. Sprint 57.31 should **reuse them directly** — no re-porting needed for these primitives. Only the page-level composition + component-internal markup changes.

### Class baseline 3rd-data-point evaluation criteria

After Day 4 closeout, compute `actual / committed` ratio:

| Range | Hypothesis test | Action |
|-------|----------------|--------|
| 0.85-1.20 | Bimodal CONFIRMED (rich-dashboard ≈ 1.0) | Propose split into `-rich-dashboard` (0.65) vs `-structural-heavy` (0.45) |
| 0.40-0.55 | Bimodal WEAKENS; baseline too generous overall | Propose lower baseline 0.60→0.50 (next 2 sprints validation) |
| 0.60-0.85 | In-band; no class change | KEEP 0.60 baseline |
| > 1.20 | Over band; rare case | Investigate Day 0 estimate accuracy + bottom-up generosity |

---

## File Change List

### NEW files (0 — all components already exist)

- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-31/artifacts/cost-dashboard-repoint/screenshots/before/*.png` (NEW; 22 routes + 1-2 extras)
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-31/artifacts/cost-dashboard-repoint/screenshots/after/*.png` (NEW; matching pairs)
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-31/artifacts/cost-dashboard-repoint/REPOINT-REPORT.md` (NEW; final REPOINT-REPORT)

### MODIFIED files (~9-10)

Component re-point (Group B-D):
- `frontend/src/pages/cost-dashboard/index.tsx` (1).
- `frontend/src/features/cost-dashboard/components/CostOverview.tsx` (1).
- `frontend/src/features/cost-dashboard/components/CategoryBarsCard.tsx` (1).
- `frontend/src/features/cost-dashboard/components/ProviderMixCard.tsx` (1).
- `frontend/src/features/cost-dashboard/components/MonthPicker.tsx` (1).
- `frontend/src/features/cost-dashboard/components/CostBreakdownTable.tsx` (1).
- `frontend/src/features/cost-dashboard/components/TenantTopTable.tsx` (1).

Optionally touched:
- `frontend/src/components/mockup-ui.tsx` (1; only if cost-dashboard needs NEW primitives not in 57.29 set — unlikely; verify Day 1).
- `frontend/scripts/route-sweep.mjs` (1; OUT_DIR re-point to sprint-57-31-* dir).

Day 4 docs / closeout:
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-31/progress.md` (NEW per-day file).
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-31/retrospective.md` (NEW Day 4).
- `CLAUDE.md` (Current Sprint row + footer).
- `memory/MEMORY.md` (pointer entry).
- `memory/project_phase57_31_cost_dashboard_repoint.md` (NEW snapshot).
- `.claude/rules/sprint-workflow.md` (`§Scope-class multiplier matrix` `frontend-verbatim-css-repoint` 3rd-data-point row + bimodal hypothesis evaluation result).
- `claudedocs/1-planning/next-phase-candidates.md` (close `AD-Sprint-Plan-frontend-verbatim-bimodal-watch` per the 3rd-data-point evaluation; possibly add new class-split AD).
- `sprint-57-31-checklist.md` (per-day `[ ]` → `[x]`).

### DELETED files (0)

No file deletions expected.

### PRESERVED (not touched)

- `frontend/src/styles-mockup.css` (Sprint 57.28 byte-identical foundation; `diff` must remain empty).
- `frontend/src/components/AppShellV2.tsx` / `Sidebar.tsx` / `Topbar.tsx` / `UserMenu.tsx` (Sprint 57.29-57.30 re-point complete).
- `frontend/src/components/mockup-ui.tsx` primitives (Sprint 57.29 verbatim; reuse only).
- chat-v2 + overview + auth + sidebar components (Sprint 57.29-57.30 complete).
- All backend code.
- All other 11 🟡 routes.

---

## Acceptance Criteria

- [ ] `/cost-dashboard` mockup-vs-production fidelity = **PARITY** (computed-style identical on representative elements; 0 cosmetic / 0 structural drift).
- [ ] 22-route regression sweep: **0 catastrophic / 0 structural-regression**.
- [ ] All gates green: `tsc` 0 errors / lint 0 errors / Vitest **all-pass** (count baseline 452, expected ±5) / Playwright **all-pass** / `check:mockup-fidelity` baseline updated if new verbatim oklch literals introduced / Vite build successful.
- [ ] Bimodal-watch 3rd-data-point evaluation completed in retrospective Q4 with explicit action: confirm split / weaken / no-change.
- [ ] Retrospective.md Q1-Q7 + memory snapshot + docs sync + PR opened + CI green + squash-merged to main.

---

## Deliverables

- [ ] `/cost-dashboard` Phase-2 verbatim re-point (7 files).
- [ ] 22-route regression sweep with REPOINT-REPORT.md.
- [ ] `/cost-dashboard` fidelity verify with PARITY verdict.
- [ ] Bimodal hypothesis 3rd-data-point evaluation + class-baseline action.
- [ ] Full gates + closeout.

---

## Dependencies & Risks

### Dependencies

- Sprint 57.28 verbatim-CSS foundation (`styles-mockup.css` byte-identical) — MUST remain valid.
- Sprint 57.29 Phase-2 method validated on `/overview` (1st app).
- Sprint 57.30 Phase-2 method validated on `/chat-v2` (2nd app).
- Sprint 57.24 v2 cost-dashboard structural rebuild + 7 mockup-ui primitives — kept as-is; only CSS layer re-pointed.

### Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|-----------|
| R1 | Mockup `CostPage` section in `page-admin.jsx:201` may have less detail than dedicated mockup pages; some production components (ProviderMixCard / MonthPicker / CostBreakdownTable) may not have mockup equivalents | Medium | Low | Day 0 Prong 2 verifies each component's mockup line range; if mockup-absent, annotate with AP-2 BackendGapBanner OR document as production-only verbatim-token-vocabulary widgets (Sprint 57.30 InputBar pattern) |
| R2 | Sprint 57.24 v2 cost-dashboard rebuild used some token-translated styles that DAY 0 may catch as needing re-point — increasing scope by 20%+ | Medium | Low | Day 0 Prong 2 catches this; if scope inflates, defer 1-2 components to Sprint 57.32; per `AD-Plan-1` audit-trail |
| R3 | TanStack query hook drift between Sprint 57.24 v2 and current production state | Low | Low | Day 0 Prong 2 grep TanStack hook usage; if drift discovered, log finding in `progress.md` |
| R4 | `frontend-verbatim-css-repoint` 3rd-data-point ratio could land in unexpected range, complicating class-split decision | Medium | Low | Use the §Class baseline 3rd-data-point evaluation criteria matrix; decision is mechanical not subjective |
| R5 | Visual-regression baseline staleness on 22 routes — but cost-dashboard shouldn't affect other routes since shell unchanged | Low | Low | Sprint 57.30 visual-regression CI passed clean on first run; expect same here |

### Common Risk Classes (per sprint-workflow.md §Common Risk Classes)

- **Class A — Paths-filter**: low risk; touches frontend heavily.
- **Class B + C**: N/A (frontend-only).
- **`AD-CI-7-GHA-PR-Permission`**: still open from Sprint 57.29 carryover; baseline-regen workflow auto-PR step fails. Sprint 57.30 didn't need it (baselines stayed valid). Sprint 57.31 expected same.

---

## Workload

Bottom-up est ~12-18 hr → calibrated commit ~7-10 hr (HYBRID blended multiplier ≈ 0.55-0.60).

| Group | Bottom-up | Notes |
|-------|-----------|-------|
| Group A (Day 0 plan + 三-prong + before-baseline) | ~1.5-2 hr | mirror 57.30 Day 0 |
| Group B (page-head + KPI row) | ~2-3 hr | 2 files |
| Group C (chart cards row) | ~3-4 hr | 3 files |
| Group D (table cards + Vitest) | ~3-5 hr | 2 files + Vitest |
| Group E (Regression sweep + fidelity + closeout) | ~2-3 hr | mirror 57.30 Day 5 |
| **Total bottom-up** | **~12-18 hr** | |
| **HYBRID blended** | **~0.55-0.60 (≈7-10 hr committed)** | |

Day 4 retrospective Q2 must verify ratio + evaluate against bimodal-watch criteria.

---

## Sequencing / Day plan

### Day 0 — Plan + Checklist + 三-prong + before-baseline

- Draft this plan + checklist.
- Day-0 三-prong (path + content + N/A schema + visual baseline strategy).
- Capture 22 before-baseline screenshots + 1-2 extras (cost-dashboard MonthPicker open / table anomaly row).
- Drift findings catalogued.

### Day 1 — Group B (page-head + KPI row)

- US-B1: `pages/cost-dashboard/index.tsx` page-head verbatim from `page-admin.jsx:203-219`.
- US-B2: `CostOverview.tsx` KPI grid-stats verbatim.
- End-of-Day-1 mini-verify: Playwright screenshot of `/cost-dashboard` showing new page-head + KPI row.

### Day 2 — Group C (chart cards row)

- US-C1: `CategoryBarsCard.tsx` re-point.
- US-C2: `ProviderMixCard.tsx` re-point (mockup-line-confirmed or AP-2 banner).
- US-C3: `MonthPicker.tsx` re-point (mockup-line-confirmed or production-only documented).

### Day 3 — Group D (table cards + Vitest)

- US-D1: `CostBreakdownTable.tsx` re-point.
- US-D2: `TenantTopTable.tsx` re-point.
- US-D3: Vitest comprehensive re-run + spec drift adaptation if needed.

### Day 4 — Group E + closeout

- US-E1: 22-route after-sweep + agent triage.
- US-E2: `/cost-dashboard` fidelity verify (computed-style + Playwright + REPOINT-REPORT.md).
- US-E3: full gates.
- US-E4: retrospective.md Q1-Q7 + memory snapshot + doc syncs + PR opened + CI green → merge.
- Class baseline 3rd-data-point evaluation logged in retro Q4 + `sprint-workflow.md §Matrix`.
