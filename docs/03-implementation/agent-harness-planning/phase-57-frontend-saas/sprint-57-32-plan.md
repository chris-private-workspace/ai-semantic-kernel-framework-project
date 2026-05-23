# Sprint 57.32 — AD-Sla-Dashboard-Verbatim-Repoint

**File**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-32-plan.md`
**Purpose**: Plan for Sprint 57.32 — fourth Phase-2 per-page verbatim-CSS re-point (`/sla-dashboard`), continuing the Phase-2 epic after Sprint 57.29 (`/overview`), Sprint 57.30 (`/chat-v2`), and Sprint 57.31 (`/cost-dashboard`).
**Category**: Sprint planning / Phase 57+ Frontend SaaS
**Scope**: Phase 57+ Frontend SaaS — Phase-2 per-page re-point epic, 4th application
**Created**: 2026-05-23
**Last Modified**: 2026-05-23
**Status**: Draft → awaiting user approval

> **Modification History**
> - 2026-05-23: Initial draft (Sprint 57.32 Day 0) — sla-dashboard Phase-2 verbatim re-point per Sprint 57.31 retro Q5 recommendation (4th data point validates baseline 0.60→0.50 lift on rich-dashboard shape)

---

## Sprint Goal

Land the **fourth Phase-2 per-page verbatim-CSS re-point** on `/sla-dashboard` (operator-facing rich dashboard — daily latency / SLO / error-budget monitoring). This sprint provides the **1st validation data point for `AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift`** (Sprint 57.31 carryover) — same rich-dashboard shape as Sprint 57.29 `/overview` and Sprint 57.31 `/cost-dashboard`, on the freshly-lifted `frontend-verbatim-css-repoint` 0.50 baseline.

`/sla-dashboard` is a 7-file route (6 widget components + 1 page index): SLAOverview KPI row + LatencyChart + SLOStatusCard + TopSlowOpsTable + ErrorRateByServiceCard + TimeRangeTabs. Sprint 57.25 already did the **structural rebuild** under `frontend-mockup-strict-rebuild` 0.60 class (ratio 0.88 in-band lower edge; 3rd app in that class). Sprint 57.32 = verbatim CSS re-point on top of that rebuilt scaffolding — same method validated on `/overview` (57.29), `/chat-v2` (57.30), `/cost-dashboard` (57.31).

---

## Background

### Why Sprint 57.32 (this sprint)

Sprint 57.31 closed the 3rd Phase-2 per-page re-point on `/cost-dashboard` with PARITY verdict + RESOLVED the `AD-Sprint-Plan-frontend-verbatim-bimodal-watch` AD (Sprint 57.30 carryover): bimodal hypothesis WEAKENED + REJECTED (57.29 + 57.31 same rich-dashboard shape with vastly different ratios 1.0 vs 0.35 → shape NOT variance driver; driver = estimate generosity diminishing across class iteration as patterns mature). Action: `frontend-verbatim-css-repoint` baseline LIFTED **0.60 → 0.50**. NEW `AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift` opened to validate 0.50 across next 2-3 sprints.

Sprint 57.32 picks `/sla-dashboard` because:

1. **Baseline-lift 1st validation data point** — `/sla-dashboard` shares the rich-dashboard shape with Sprint 57.29 `/overview` + Sprint 57.31 `/cost-dashboard` (KPI stats row + chart cards + table cards). With baseline already lifted to 0.50, a ratio of 0.85-1.20 confirms the lift was calibrated correctly. A ratio < 0.7 suggests 0.50 still too generous → propose 0.40 next iteration. A ratio > 1.20 suggests 0.50 too aggressive → revert to 0.55 or 0.60. Per Sprint 57.31 retro Q5 explicit recommendation.

2. **User-value ROI** — `/sla-dashboard` is daily-used by operators monitoring latency (p50/p95/p99), SLO budget, top-slow-ops, error rates. PARITY upgrade meaningfully impacts production observability UX.

3. **Mockup source well-defined (NO production-only widgets)** — Day 0 Prong 2 confirms `/sla-dashboard` mockup lives at `reference/design-mockups/page-admin.jsx:32-198` (the `SlaPage` const + `LatencyChart` helper), co-located with CostPage in the admin-scope file. All 6 production components map 1:1 to mockup sections (no `production-only-by-design` widgets, no AP-2 BackendGapBanner needed — distinct from Sprint 57.31 cost-dashboard which had 3 production-only widgets MonthPicker/CostBreakdownTable/ProviderMixCard). Sprint 57.32 is therefore a **clean** rich-dashboard re-point — purest validation of the 0.50 baseline lift.

4. **Phase-1 alignment baseline already strong** — Sprint 57.25 rebuilt sla-dashboard with strict-rebuild approach using Sprint 57.24 v2 primitives (PageHead / Stat / Spark / CardShell / BarTrack / BackendGapBanner) + introduced NEW feature-scoped LatencyChart (Karpathy §2 inline). Phase-2 verbatim CSS re-point = swap any remaining translated-Tailwind or shadcn-default usage to mockup `.grid-stats` / `.grid-main` / `.bar-track` / `.table` / `.btn-group` / `.kbar` CSS class form.

### Mockup source mapping (Day 0 Prong 2 confirmed)

`page-admin.jsx:32-198`:

| Mockup line range | Mockup section | Production component |
|-------------------|----------------|----------------------|
| L34-52 | page-head (title + subtitle + `.route-pill` + `.btn-group` 1h/24h/7d/30d + Refresh + Export) | `pages/sla-dashboard/index.tsx` + `TimeRangeTabs.tsx` |
| L54-59 | grid-stats KPI row (4-stat: p50/p95/p99 latency + Error budget) | `SLAOverview.tsx` |
| L62-70 | grid-main row 1 LEFT — Latency distribution Card + `<LatencyChart />` + `.kbar` legend (p50/p95/p99 Badges) | `LatencyChart.tsx` (canonical SVG defined L157-198) |
| L72-98 | grid-main row 1 RIGHT — SLO status Card (5-row `.bar-track` budget gauge) | `SLOStatusCard.tsx` |
| L104-129 | grid-main row 2 LEFT — Top slow operations `.table` (6 ops with Badge tones per kind) | `TopSlowOpsTable.tsx` |
| L131-152 | grid-main row 2 RIGHT — Error rate by service Card (6-row `.bar-track`) | `ErrorRateByServiceCard.tsx` |

### Scope boundaries

**IN scope**:
- `/sla-dashboard` 7 production files re-point: `pages/sla-dashboard/index.tsx` + 6 components in `features/sla-dashboard/components/`.
- Any new mockup CSS classes needed (audit during Day 0 Prong 2; candidates: `.btn-group` + `.kbar` if absent from Sprint 57.28 foundation).
- 22-route regression sweep before/after + `/sla-dashboard` fidelity verification.

**OUT of scope**:
- The 10 remaining 🟡 AppShellV2 routes (orchestrator / loop-debug / memory / state-inspector / governance / verification / admin-tenants / tenant-settings / compaction / + 3 ⚪ crash-fix candidates).
- Backend extensions (SLA ingestion, p99 quantile sketch, SLO budget tracker — Sprint 56.3 SLA Monitor already shipped Phase 1).
- Sprint 57.30/57.31 carryover ADs except `AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift` (this sprint = 1st validation data point).

### Class baseline — `frontend-verbatim-css-repoint` 0.50 (4th application; 1st validation of lifted baseline)

4th application of the class baseline; 1st on the freshly-lifted 0.50. HYBRID weighted blend for Sprint 57.32:

| Component | Class | Multiplier | Weight |
|-----------|-------|------------|--------|
| Day-0 三-prong + before-baseline | `audit-cycle` | 0.85 | ~10% |
| 7 components re-point (4 widget cards + 1 table + 1 picker + 1 page) | `frontend-verbatim-css-repoint` | 0.50 | ~70% |
| 22-route sweep + fidelity verify | `frontend-verbatim-css-repoint` | 0.50 | ~10% |
| Closeout + retro + docs | `closeout` | 0.80 | ~10% |
| **HYBRID blended baseline** | | **≈ 0.55** | |

Bottom-up estimate: ~7 files × 1-2 hr each + Day 0 ~1.5 hr + Day 4 ~2 hr = **~10-15 hr**.
Calibrated commit: ~5-7.5 hr (multiplier ≈ 0.50 anchored to class baseline; HYBRID ≈ 0.55 if weighted exactly).

Per `AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift` (Sprint 57.31 NEW): this is the **1st validation data point** for the lifted 0.50 baseline. KEEP 0.50 this sprint per `When to adjust` 3-sprint window rule. After Sprint 57.32 closeout, evaluate:
- If ratio ≈ 0.85-1.20 → 0.50 lift CONFIRMED accurate (keep + accumulate evidence).
- If ratio ≈ 0.40-0.55 → 0.50 still too generous → propose 0.40 next iteration (consistent with Sprint 57.30+57.31 0.40 / 0.35 pattern).
- If ratio ≈ 0.60-0.85 → in-band lower edge; trend ok, keep 0.50.
- If ratio > 1.20 → over-corrected lift; revert toward 0.55-0.60.

### What is preserved (NOT changed)

- Sprint 57.25 sla-dashboard structural rebuild (7 reused Sprint 57.24 v2 primitives + 1 NEW feature-scoped LatencyChart).
- All component-logic layer: hooks, TanStack queries (`useSlaReport` / etc.), state, props, event handlers, a11y attrs, `data-testid`s.
- Backend integration (`slaService` / `/api/v1/sla-report`).
- All Sprint 57.25 Vitest specs that test logic / data binding / TanStack invalidation.
- `routes.config.ts` sla-dashboard entry.
- `frontend/src/components/mockup-ui.tsx` primitives (verbatim from Sprint 57.29-57.31; reuse only).

### What gets changed (this sprint scope)

**Day 1 — page-head + KPI row** (3 files):
- `pages/sla-dashboard/index.tsx` — drop `pageTitle` prop on AppShellV2 (avoid duplicate, per Sprint 57.31 pattern); verbatim page-head composition matching `page-admin.jsx:34-52` (title "SLA Dashboard" + subtitle + `.route-pill` + `.btn-group` time-range + Refresh + Export).
- `features/sla-dashboard/components/TimeRangeTabs.tsx` — `.btn-group` verbatim with 4 Button variants (1h ghost / 24h outline-active / 7d ghost / 30d ghost) matching `page-admin.jsx:43-48`.
- `features/sla-dashboard/components/SLAOverview.tsx` — `.grid-stats` 4-stat row verbatim matching `page-admin.jsx:54-59` (p50/p95/p99 latency + Error budget; with Spark + tone-coded delta).

**Day 2 — Latency + SLO row** (2 files):
- `features/sla-dashboard/components/LatencyChart.tsx` — verify Card wrapper + `.kbar` legend Badges (p50/p95/p99) verbatim per L62-70; SVG body already mockup-aligned from Sprint 57.25 (verify no regression).
- `features/sla-dashboard/components/SLOStatusCard.tsx` — 5-row `.bar-track` budget gauge verbatim per `page-admin.jsx:72-98` (with name + current/target mono + bar-track fill colored by `ok` flag + budget-used subtle).

**Day 3 — Top slow + Error rate row** (2 files):
- `features/sla-dashboard/components/TopSlowOpsTable.tsx` — `.table` 6-op verbatim per L104-129 (with Badge tones per kind tool/memory/subagent/verify/loop; right-aligned mono p50/p95/p99/Calls; p99 conditional color > 3000ms warning).
- `features/sla-dashboard/components/ErrorRateByServiceCard.tsx` — 6-row `.bar-track` verbatim per L131-152 (service name mono + rate percentage with > 0.5% conditional warning color; bar-track fill scaled `rate × 50`).

**Day 4 — Regression + fidelity verify + closeout**.

---

## User Stories

### Group A — Day 0 plan + 三-prong + before-baseline (PRE-WORK)

- **US-A1** (Plan + Checklist): As the AI, I draft Sprint 57.32 plan + checklist mirroring Sprint 57.31 format before any code runs. Acceptance: this file + `sprint-57-32-checklist.md` exist with full content.
- **US-A2** (Day-0 三-prong): As the AI, I run path-verify + content-verify + (no schema) on plan-time assertions; key Prong-2 grep checks: confirm mockup `SlaPage` location `page-admin.jsx:32-198`; verify `.btn-group` + `.kbar` classes presence in `styles-mockup.css`; confirm `LatencyChart.tsx` Sprint 57.25 SVG body still mockup-aligned (no regression since 57.25); verify Sprint 57.25 component file structure matches plan; verify TanStack hook integration patterns.
- **US-A3** (Before-baseline screenshots): Playwright capture 22 AppShellV2 routes via `route-sweep.mjs before` (OUT_DIR re-point to sprint-57-32-* dir) + `/sla-dashboard` time-range-tab-active state (showing 24h selected) before any code change.

### Group B — page-head + KPI row (Day 1)

- **US-B1** (page-head + TimeRangeTabs verbatim): As an operator on `/sla-dashboard`, the page-head matches mockup `page-admin.jsx:34-52` verbatim — title "SLA Dashboard" + subtitle "Range 12 · Observability · p50 / p95 / p99 latency + error budget" + `.route-pill /sla-dashboard` + actions (4-button `.btn-group` 1h/24h/7d/30d + Refresh + Export). Acceptance: `pages/sla-dashboard/index.tsx` page-head re-pointed; `TimeRangeTabs.tsx` `.btn-group` re-pointed; computed-style matches mockup.
- **US-B2** (SLAOverview grid-stats verbatim): As an operator, the 4 KPI cards match mockup `.grid-stats` shape — p50 latency (ms, tone primary) + p95 latency (s, tone info) + p99 latency (s, tone warning) + Error budget (%, tone success); each with mockup-ui `<Stat>` + `<Spark>` primitives. Acceptance: `SLAOverview.tsx` re-pointed using mockup-ui primitives (already verbatim from Sprint 57.29 — reuse, don't re-port).

### Group C — Latency + SLO row (Day 2)

- **US-C1** (LatencyChart verbatim): "Latency distribution" Card matches mockup `page-admin.jsx:62-70` — Card wrapper with subtitle "24h · all agents · p50 / p95 / p99" + `.kbar` legend with 3 Badges (p50 primary-dot / p95 info-dot / p99 warning-dot) + `<LatencyChart>` SVG body. Acceptance: `LatencyChart.tsx` Card wrapper + `.kbar` re-pointed; SVG verified no regression from Sprint 57.25.
- **US-C2** (SLOStatusCard verbatim): "SLO status" Card matches mockup `page-admin.jsx:72-98` — 5-row budget gauge (Loop p95 < 2s / Tool success ≥ 99% / HITL response < 5m / Subagent depth ≤ 5 / Cost / run < $0.05); each row with `.spread` header (color dot ok/danger + name + mono current/target) + `.bar-track` fill (width = used%, color = ok ? success : danger) + `subtle mono` budget-used label. Acceptance: re-pointed.

### Group D — Top slow + Error rate row (Day 3)

- **US-D1** (TopSlowOpsTable verbatim): "Top slow operations" Card matches mockup `page-admin.jsx:104-129` — `.table` with header (Operation/Kind/p50/p95/p99/Calls) + 6 op rows (tool.metrics.query / tool.k8s.set_env / loop.iteration / subagent.spawn / verification.run / memory.write); per-row Badge tone-by-kind (tool/memory/subagent/verify/loop); right-aligned mono tnum p50/p95/p99/Calls; p99 conditional color (> 3000ms warning). Acceptance: re-pointed.
- **US-D2** (ErrorRateByServiceCard verbatim): "Error rate by service" Card matches mockup `page-admin.jsx:131-152` — 6-row layout (inference.adapter / tool.runner / memory.store / audit.writer / subagent.scheduler / webhook.dispatcher); each with `.spread` header (service name mono + rate % with > 0.5% conditional warning color) + `.bar-track` fill (width = `rate × 50`%, color = rate > 0.5 ? warning : success). Acceptance: re-pointed.
- **US-D3** (Vitest comprehensive): All sla-dashboard Vitest specs pass; adapt any spec drift from translated DOM → verbatim DOM (likely small surface area since Sprint 57.25 specs already test data binding + testids, not class names — same pattern as Sprint 57.31).

### Group E — Regression sweep + fidelity verify + closeout (Day 4)

- **US-E1** (22-route sweep): 0 catastrophic / 0 structural; 3 ⚪ pre-existing fails (`/subagents` `/memory` `/verification`) classified explicitly NOT a regression.
- **US-E2** (`/sla-dashboard` fidelity verify): Mockup-vs-prod computed-style + Playwright; **🟢 PARITY** verdict logged in REPOINT-REPORT.md.
- **US-E3** (Full gates): tsc / lint / Vitest / Playwright / build / check:mockup-fidelity / route-sweep all green.
- **US-E4** (Closeout): retrospective.md Q1-Q7 + memory snapshot + CLAUDE.md / MEMORY.md / `sprint-workflow.md §Matrix` 4th-data-point row + `next-phase-candidates.md` + PR + merge + branch cleanup.

---

## Technical Specifications

### Verbatim re-point method (unchanged from Sprint 57.29-57.31)

For every component touched in Groups B-D:

1. Read mockup canonical source line range (`page-admin.jsx` SlaPage section).
2. Identify visual layer: CSS class names + inline-style literals.
3. Read production `.tsx`; identify translated-Tailwind / shadcn-default usage.
4. Re-point: replace translated Tailwind with mockup class names; replace shadcn defaults with mockup inline-style literals (copied byte-for-byte); preserve all component-logic layer.
5. Add file-level eslint-disable `no-restricted-syntax` with the standard verbatim escape-hatch comment IF inline-style literals are used.
6. Update file header MHist (1-line per Sprint 55.3 char budget rule).

### Reuse mockup-ui primitives (Karpathy §2 simplicity)

The Sprint 57.24 v2 + Sprint 57.29 verbatim primitive set (`PageHead` / `Stat` / `Spark` / `CardShell` / `BarTrack` / `BackendGapBanner` from `mockup-ui.tsx`) is already verbatim. Sprint 57.32 should **reuse them directly** — no re-porting needed for these primitives. Only the page-level composition + component-internal markup changes.

LatencyChart is **feature-scoped** (per Sprint 57.25 Karpathy §2 inline decision — single consumer, not promoted to mockup-ui); Sprint 57.32 keeps it feature-scoped.

### Class baseline 4th-data-point evaluation criteria (validates 0.50 lift)

After Day 4 closeout, compute `actual / committed` ratio:

| Range | Hypothesis test | Action |
|-------|----------------|--------|
| 0.85-1.20 | 0.50 lift CONFIRMED accurate | KEEP 0.50; accumulate evidence; close baseline-lift AD after 2-3 data points |
| 0.40-0.55 | 0.50 still too generous | Propose 0.40 next iteration (consistent with 57.30/57.31 pattern of 0.40/0.35) |
| 0.60-0.85 | In-band lower edge; trend ok | KEEP 0.50; mid-validation |
| > 1.20 | Over-corrected lift | Propose revert toward 0.55-0.60 |

---

## File Change List

### NEW files (3)

- `claudedocs/4-changes/sprint-57-32-sla-dashboard-repoint/screenshots/before/*.png` (NEW; 22 routes + 1-2 extras)
- `claudedocs/4-changes/sprint-57-32-sla-dashboard-repoint/screenshots/after/*.png` (NEW; matching pairs)
- `claudedocs/4-changes/sprint-57-32-sla-dashboard-repoint/REPOINT-REPORT.md` (NEW; final REPOINT-REPORT)

### MODIFIED files (~8-9)

Component re-point (Group B-D):
- `frontend/src/pages/sla-dashboard/index.tsx` (1).
- `frontend/src/features/sla-dashboard/components/TimeRangeTabs.tsx` (1).
- `frontend/src/features/sla-dashboard/components/SLAOverview.tsx` (1).
- `frontend/src/features/sla-dashboard/components/LatencyChart.tsx` (1).
- `frontend/src/features/sla-dashboard/components/SLOStatusCard.tsx` (1).
- `frontend/src/features/sla-dashboard/components/TopSlowOpsTable.tsx` (1).
- `frontend/src/features/sla-dashboard/components/ErrorRateByServiceCard.tsx` (1).

Optionally touched:
- `frontend/src/components/mockup-ui.tsx` (1; only if sla-dashboard needs NEW primitives not in 57.29-57.31 set — unlikely; verify Day 1).
- `frontend/scripts/route-sweep.mjs` (1; OUT_DIR re-point to sprint-57-32-* dir).
- `frontend/src/styles-mockup.css` — **NOT TOUCHED** (Sprint 57.28 byte-identical foundation; `diff` must remain empty). If `.btn-group` or `.kbar` absent, escalate to a separate foundation-correction sprint, NOT this one.

Day 4 docs / closeout:
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-32/progress.md` (NEW per-day file).
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-32/retrospective.md` (NEW Day 4).
- `CLAUDE.md` (Current Sprint row + footer).
- `memory/MEMORY.md` (pointer entry).
- `memory/project_phase57_32_sla_dashboard_repoint.md` (NEW snapshot).
- `.claude/rules/sprint-workflow.md` (`§Scope-class multiplier matrix` `frontend-verbatim-css-repoint` 4th-data-point row + baseline-lift 1st validation result).
- `claudedocs/1-planning/next-phase-candidates.md` (update `AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift` with 1st validation data point; carryover open items).
- `sprint-57-32-checklist.md` (per-day `[ ]` → `[x]`).

### DELETED files (0)

No file deletions expected.

### PRESERVED (not touched)

- `frontend/src/styles-mockup.css` (Sprint 57.28 byte-identical foundation; `diff` must remain empty).
- `frontend/src/components/AppShellV2.tsx` / `Sidebar.tsx` / `Topbar.tsx` / `UserMenu.tsx` (Sprint 57.29-57.30 re-point complete).
- `frontend/src/components/mockup-ui.tsx` primitives (Sprint 57.29 verbatim; reuse only).
- chat-v2 + overview + cost-dashboard + auth + sidebar components (Sprint 57.29-57.31 complete).
- All backend code.
- All other 10 🟡 routes.

---

## Acceptance Criteria

- [ ] `/sla-dashboard` mockup-vs-production fidelity = **PARITY** (computed-style identical on representative elements; 0 cosmetic / 0 structural drift).
- [ ] 22-route regression sweep: **0 catastrophic / 0 structural-regression**.
- [ ] All gates green: `tsc` 0 errors / lint 0 errors / Vitest **all-pass** (count baseline 452, expected ±5) / Playwright **all-pass** / `check:mockup-fidelity` baseline updated if new verbatim oklch literals introduced / Vite build successful.
- [ ] Baseline-lift 1st-data-point evaluation completed in retrospective Q4 with explicit action: confirm / lower / hold / revert.
- [ ] Retrospective.md Q1-Q7 + memory snapshot + docs sync + PR opened + CI green + squash-merged to main.

---

## Deliverables

- [ ] `/sla-dashboard` Phase-2 verbatim re-point (7 files).
- [ ] 22-route regression sweep with REPOINT-REPORT.md.
- [ ] `/sla-dashboard` fidelity verify with PARITY verdict.
- [ ] Baseline-lift 1st validation data point + class-baseline action.
- [ ] Full gates + closeout.

---

## Dependencies & Risks

### Dependencies

- Sprint 57.28 verbatim-CSS foundation (`styles-mockup.css` byte-identical) — MUST remain valid.
- Sprint 57.29 Phase-2 method validated on `/overview` (1st app).
- Sprint 57.30 Phase-2 method validated on `/chat-v2` (2nd app).
- Sprint 57.31 Phase-2 method validated on `/cost-dashboard` (3rd app) + baseline LIFTED 0.60 → 0.50.
- Sprint 57.25 sla-dashboard structural rebuild + 7 mockup-ui primitives + LatencyChart feature-scoped — kept as-is; only CSS layer re-pointed.

### Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|-----------|
| R1 | `styles-mockup.css` may lack `.btn-group` or `.kbar` classes (used in mockup SlaPage but possibly not extracted to foundation) | Medium | Low | Day 0 Prong 2 grep `styles-mockup.css` for both classes; if absent, escalate to a separate foundation sprint (do NOT modify foundation in this sprint per Sprint 57.28 byte-identical contract) |
| R2 | Sprint 57.25 sla-dashboard rebuild used some token-translated styles that DAY 0 may catch as needing re-point — increasing scope by 20%+ | Medium | Low | Day 0 Prong 2 catches this; if scope inflates, defer 1-2 components to Sprint 57.33; per `AD-Plan-1` audit-trail |
| R3 | LatencyChart SVG body drift since Sprint 57.25 (any incidental changes) | Low | Low | Day 0 Prong 2 reads current production SVG; if drift, re-align to mockup `page-admin.jsx:157-198` canonical |
| R4 | Baseline-lift 1st-data-point ratio could land in unexpected range, complicating baseline-lift validation decision | Low | Low | Use §Class baseline 4th-data-point evaluation criteria matrix; decision is mechanical not subjective |
| R5 | Visual-regression baseline staleness on 22 routes — but sla-dashboard shouldn't affect other routes since shell unchanged from Sprint 57.30 | Low | Low | Sprint 57.30+57.31 visual-regression CI passed clean on first run; expect same here; if `/sla-dashboard` baseline needs regen, expect `AD-CI-7-GHA-PR-Permission` manual ff-merge same as 57.31 |
| R6 | Pacing acceleration risk — 4th consecutive Phase-2 re-point may compress Day 1-3 into single batched delegation (like Sprint 57.31 Day 1 batched 7 files) which could obscure per-day calibration signal | Medium | Low | If Day 0 visual baseline shows production already very mockup-aligned (like 57.31 finding), document batched-delegation rationale in progress.md Day 1 §Plan-vs-execution adjustment (audit trail preserved); sprint-aggregate ratio still valid for 4th-data-point measurement |

### Common Risk Classes (per sprint-workflow.md §Common Risk Classes)

- **Class A — Paths-filter**: low risk; touches frontend heavily.
- **Class B + C**: N/A (frontend-only).
- **`AD-CI-7-GHA-PR-Permission`**: still open from Sprint 57.29 carryover; baseline-regen workflow auto-PR step fails. If `/sla-dashboard` baseline needs regen, expect manual ff-merge required (same workaround as Sprint 57.31).

---

## Workload

Bottom-up est ~10-15 hr → calibrated commit ~5-7.5 hr (HYBRID blended multiplier ≈ 0.55; anchored to class baseline 0.50).

| Group | Bottom-up | Notes |
|-------|-----------|-------|
| Group A (Day 0 plan + 三-prong + before-baseline) | ~1.5-2 hr | mirror 57.31 Day 0; faster (mockup well-mapped, no decision deferrals) |
| Group B (page-head + KPI row) | ~2-3 hr | 3 files (page + TimeRangeTabs + SLAOverview) |
| Group C (Latency + SLO row) | ~2-3 hr | 2 files |
| Group D (Top slow + Error rate + Vitest) | ~2-3 hr | 2 files + Vitest |
| Group E (Regression sweep + fidelity + closeout) | ~2-3 hr | mirror 57.31 Day 4 |
| **Total bottom-up** | **~10-15 hr** | |
| **HYBRID blended (class 0.50 + Day 0/4 mix)** | **~5-7.5 hr committed** | |

Day 4 retrospective Q2 must verify ratio + evaluate against baseline-lift validation criteria.

---

## Sequencing / Day plan

### Day 0 — Plan + Checklist + 三-prong + before-baseline

- Draft this plan + checklist.
- Day-0 三-prong (path + content + N/A schema + visual baseline strategy).
- Capture 22 before-baseline screenshots + 1-2 extras (sla-dashboard time-range-tab-active state).
- Drift findings catalogued.

### Day 1 — Group B (page-head + KPI row)

- US-B1: `pages/sla-dashboard/index.tsx` page-head + `TimeRangeTabs.tsx` `.btn-group` verbatim from `page-admin.jsx:34-52`.
- US-B2: `SLAOverview.tsx` KPI grid-stats verbatim from L54-59.
- End-of-Day-1 mini-verify: Playwright screenshot of `/sla-dashboard` showing new page-head + KPI row.

### Day 2 — Group C (Latency + SLO row)

- US-C1: `LatencyChart.tsx` Card wrapper + `.kbar` legend re-point (SVG body verify no regression).
- US-C2: `SLOStatusCard.tsx` 5-row `.bar-track` budget gauge re-point.

### Day 3 — Group D (Top slow + Error rate + Vitest)

- US-D1: `TopSlowOpsTable.tsx` `.table` re-point.
- US-D2: `ErrorRateByServiceCard.tsx` `.bar-track` re-point.
- US-D3: Vitest comprehensive re-run + spec drift adaptation if needed.

### Day 4 — Group E + closeout

- US-E1: 22-route after-sweep + agent triage.
- US-E2: `/sla-dashboard` fidelity verify (computed-style + Playwright + REPOINT-REPORT.md).
- US-E3: full gates.
- US-E4: retrospective.md Q1-Q7 + memory snapshot + doc syncs + PR opened + CI green → merge.
- Baseline-lift 1st-data-point validation logged in retro Q4 + `sprint-workflow.md §Matrix`.

---

## Related

- `sprint-57-31-plan.md` — immediate predecessor; same class + method + structure
- `sprint-57-25-plan.md` — sla-dashboard original strict-rebuild (Phase-1)
- `sprint-57-29-plan.md` — Phase-2 1st app `/overview` (same rich-dashboard shape)
- `sprint-57-30-plan.md` — Phase-2 2nd app `/chat-v2`
- `.claude/rules/sprint-workflow.md` §Scope-class multiplier matrix — `frontend-verbatim-css-repoint` baseline (0.50 lifted from 0.60 in 57.31)
- `.claude/rules/file-header-convention.md` — MHist 1-line max + char budget
- `docs/rules-on-demand/frontend-mockup-fidelity.md` — verbatim-CSS method (authoritative for any frontend sprint)
- `reference/design-mockups/page-admin.jsx:32-198` — SlaPage canonical visual source + LatencyChart helper
