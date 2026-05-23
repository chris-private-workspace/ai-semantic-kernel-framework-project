# Sprint 57.32 — Checklist

> Plan: [`sprint-57-32-plan.md`](./sprint-57-32-plan.md)
>
> AD-Sla-Dashboard-Verbatim-Repoint — 4th Phase-2 per-page verbatim-CSS re-point + 1st validation of lifted 0.50 baseline.
>
> Day 0-4; mirror 57.31 day structure (smaller scope; clean mockup mapping = 0 production-only widgets).

---

## Day 0 — Plan + Checklist + 三-prong + before-baseline

### 0.1 Plan + Checklist drafted

- [x] **Plan file** `sprint-57-32-plan.md` exists with 10 sections
- [x] **Checklist file** (this file) drafted mirroring Sprint 57.31 format

### 0.2 Day-0 三-prong verify

- [x] **Prong 1 — Path verify** — Glob batched: 7 production paths all present (1 page + 6 components); 3 NEW paths correctly absent. 0 path drift.
- [x] **Prong 2 — Content verify** — 4 findings catalogued in progress.md (D1 mockup SlaPage L32-198 + D2 R1-mitigated `.btn-group`/`.kbar` both present in styles-mockup.css L461/L1115 + D3 R3-mitigated LatencyChart SVG body aligned with mockup canonical + D4 7 component files structurally intact); all 🟢 GREEN
- [x] **Prong 3 — Schema verify**: N/A (frontend-only)
- [x] **Prong 4 — Visual baseline scope** — only `/sla-dashboard` baseline likely needs regen Day 4; same AD-CI-7 ff-merge workaround as 57.31

### 0.3 Before-baseline screenshot capture

- [x] **22 AppShellV2 + AuthShell + Home route screenshots** via `route-sweep.mjs before` mode — 22/22 ✓ captured to `claudedocs/4-changes/sprint-57-32-sla-dashboard-repoint/screenshots/before/`; route-sweep.mjs OUT_DIR re-pointed + MHist entry added
- [x] **sla-dashboard extras** — **skipped**: regular sweep capture suffices (no additional stateful UI requiring separate snapshots like cost-dashboard MonthPicker / table anomaly)
- [ ] **Day 0 commit** — single commit on `feature/sprint-57-32-sla-dashboard-repoint` branch (pending; next step)

---

## Day 1 — Group B (page-head + TimeRangeTabs + KPI row)

### 1.1 US-B1 — page-head + TimeRangeTabs verbatim re-point

- [ ] **Read mockup** `page-admin.jsx:34-52` (page-head + .btn-group time-range tabs)
- [ ] **Re-point** `pages/sla-dashboard/index.tsx`
  - Sub: drop `pageTitle="SLA Dashboard"` prop on AppShellV2 (avoid topbar duplicate per Sprint 57.31 pattern)
  - Sub: verbatim page-head with title + subtitle + `.route-pill /sla-dashboard` + actions composition
- [ ] **Re-point** `TimeRangeTabs.tsx`
  - Sub: `.btn-group` with 4 Button variants (1h ghost / 24h outline / 7d ghost / 30d ghost)
  - Sub: state-driven active variant (currently controlled by parent or local state — preserve logic)
  - Sub: include Refresh + Export Buttons inline with btn-group per mockup L49-50
- [ ] **Header MHist** updated (1-line per Sprint 55.3 char budget)
- [ ] **Verify**: Playwright shot `day1-sla-dashboard-head.png` showing new page-head matches mockup L34-52

### 1.2 US-B2 — SLAOverview grid-stats verbatim

- [ ] **Read mockup** `page-admin.jsx:54-59` (4-stat grid-stats KPI row)
- [ ] **Re-point** `SLAOverview.tsx`
  - Sub: `.grid-stats` 4-stat row
  - Sub: each Stat uses mockup-ui `<Stat>` primitive + `<Spark>` sparkline (reuse from Sprint 57.29; do NOT re-port primitive)
  - Sub: 4 stats: p50 latency (ms, primary tone) + p95 latency (s, info) + p99 latency (s, warning) + Error budget (%, success)
  - Sub: deltaDir per mockup ("up" / "down") with correct color semantics
- [ ] **Header MHist** updated
- [ ] **Verify**: Playwright shot `day1-sla-dashboard-fold.png` (full above-the-fold = page-head + KPI row)

### 1.3 Day 1 mini-verify

- [ ] All Day 1 files lint-clean
- [ ] Vitest re-run — 452 baseline maintained (or adapted spec count documented)
- [ ] Day 1 commit

---

## Day 2 — Group C (Latency + SLO row)

### 2.1 US-C1 — LatencyChart Card wrapper + .kbar verbatim

- [ ] **Read mockup** `page-admin.jsx:62-70` (Card wrapper + .kbar legend)
- [ ] **Re-point** `LatencyChart.tsx`
  - Sub: Card wrapper with title "Latency distribution" + subtitle "24h · all agents · p50 / p95 / p99"
  - Sub: `actions` prop = `.kbar` with 3 Badges (p50 primary-dot / p95 info-dot / p99 warning-dot)
  - Sub: SVG body verify no regression from Sprint 57.25 canonical (mockup L157-198)
  - Sub: data layer + 3 series rendering preserved
- [ ] **Header MHist** updated

### 2.2 US-C2 — SLOStatusCard 5-row .bar-track verbatim

- [ ] **Read mockup** `page-admin.jsx:72-98` (5-row SLO budget gauge)
- [ ] **Re-point** `SLOStatusCard.tsx`
  - Sub: `<Card title="SLO status" subtitle="Active SLO objectives">` wrapper
  - Sub: 5-row inner `.col` with gap 12
  - Sub: per row: `.spread` header (color dot ok/danger + name) + mono current/target right + `.bar-track` (width = `Math.min(100, used)`%, color = ok ? success : danger) + `subtle mono` budget-used label
  - Sub: 5 SLOs verbatim (Loop p95 < 2s / Tool success ≥ 99% / HITL response < 5m / Subagent depth ≤ 5 / Cost / run < $0.05)
- [ ] **Header MHist** updated

### 2.3 Day 2 mini-verify

- [ ] All Day 2 files lint-clean
- [ ] Playwright shot `day2-sla-dashboard-row1.png` (page + latency + SLO row)
- [ ] Day 2 commit

---

## Day 3 — Group D (Top slow + Error rate + Vitest)

### 3.1 US-D1 — TopSlowOpsTable verbatim

- [ ] **Read mockup** `page-admin.jsx:104-129` (.table 6-op)
- [ ] **Re-point** `TopSlowOpsTable.tsx`
  - Sub: `<Card title="Top slow operations" subtitle="p99 contributors · last 24h" bodyClass="flush">` wrapper
  - Sub: `<table className="table">` with header (Operation/Kind/p50/p95/p99/Calls; right-aligned numeric cols)
  - Sub: 6 op rows verbatim (tool.metrics.query / tool.k8s.set_env / loop.iteration / subagent.spawn / verification.run / memory.write)
  - Sub: Badge tone-by-kind dispatch (tool → tool / memory → memory / subagent → thinking / verify → success / loop → primary)
  - Sub: per-row mono tnum p50/p95 + p99 conditional color (> 3000ms → warning, else fg-muted) + calls subtle right-aligned
- [ ] **Header MHist** updated

### 3.2 US-D2 — ErrorRateByServiceCard verbatim

- [ ] **Read mockup** `page-admin.jsx:131-152` (6-row .bar-track)
- [ ] **Re-point** `ErrorRateByServiceCard.tsx`
  - Sub: `<Card title="Error rate by service" subtitle="Last hour">` wrapper
  - Sub: 6-row inner `.col` with gap 10
  - Sub: per row: `.spread` header (service name mono + rate % with > 0.5% conditional warning color) + `.bar-track` fill (width = `Math.min(100, rate × 50)`%, color = rate > 0.5 ? warning : success)
  - Sub: 6 services verbatim (inference.adapter / tool.runner / memory.store / audit.writer / subagent.scheduler / webhook.dispatcher)
- [ ] **Header MHist** updated

### 3.3 US-D3 — Vitest comprehensive

- [ ] Run full Vitest suite — expect 452 baseline (or adapt count if spec drift)
- [ ] If spec drift: identify which spec(s) test class names → adapt to verbatim DOM (likely 0 since Sprint 57.25 specs test data binding + testids, not class names per Sprint 57.31 precedent)
- [ ] Document any adaptations in progress.md Day 3

### 3.4 Day 3 mini-verify

- [ ] All Day 3 files lint-clean
- [ ] Playwright shot `day3-sla-dashboard-full.png` (full page above + below fold)
- [ ] Day 3 commit

---

## Day 4 — Group E (regression sweep + fidelity + closeout)

### 4.1 US-E1 — 22-route regression sweep

- [ ] **after-sweep** via `route-sweep.mjs after` — 22 PNG captured
- [ ] **Agent triage** — expect 18 🟢 PARITY + 1 🟢 PROP-stub + 0 🟡/🟠/🔴 + 3 ⚪ pre-existing fails (continuation of cleanest-yet pattern from 57.30-57.31)
- [ ] **REPOINT-REPORT.md** written (agent-produced)

### 4.2 US-E2 — /sla-dashboard fidelity verify

- [ ] **Step 1** styles.css ↔ styles-mockup.css diff → must remain empty (foundation untouched)
- [ ] **Step 2** mockup vs prod assessed via triage agent (read mockup file + Day 3 verify screenshots)
- [ ] **Step 3** representative mockup elements catalogued in REPOINT-REPORT.md (page-head + KPI + LatencyChart + SLOStatus + TopSlowOps + ErrorRateByService)
- [ ] **Step 4** drift verdict logged (target: **🟢 PARITY**)

### 4.3 US-E3 — Full gates

- [ ] tsc strict — only pre-existing TS6310 carryover (no new errors)
- [ ] ESLint exit 0
- [ ] Vitest baseline maintained (452 ± 5)
- [ ] Vite build successful
- [ ] check:mockup-fidelity 25/25 unchanged (no new oklch literals)
- [ ] Bundle size delta logged (expected ~0; no orphan cleanup this sprint)

### 4.4 US-E4 — Closeout

- [ ] **retrospective.md** Q1-Q7 written (Q7 N/A SKIP per Sprint 57.29-57.31 precedent; Q4 has baseline-lift 1st-data-point evaluation + RESOLUTION action)
- [ ] **Memory snapshot** `memory/project_phase57_32_sla_dashboard_repoint.md` NEW
- [ ] **MEMORY.md** pointer entry added (~250-300 char quality pointer per `.claude/rules/sprint-workflow.md §Sprint Closeout`)
- [ ] **CLAUDE.md** Current Sprint row + footer updated (minimal touch per `.claude/rules/sprint-workflow.md §Sprint Closeout — CLAUDE.md Update Policy`)
- [ ] **`sprint-workflow.md §Scope-class multiplier matrix`** updated — `frontend-verbatim-css-repoint` row now 4 data points + baseline-lift 1st-data-point validation result + MHist entry
- [ ] **`next-phase-candidates.md`** updated — update baseline-lift AD with 1st validation result; carryover open items refreshed
- [ ] **Day 4 commit** on `feature/sprint-57-32-sla-dashboard-repoint`
- [ ] **PR open** — `gh pr create` with body listing Sprint Goal + USs completed + 5 gates + bimodal/baseline-lift narrative + 22-route sweep summary
- [ ] **CI green → squash-merge** — if `/sla-dashboard` visual-regression baseline stale, expect manual ff-merge required (AD-CI-7-GHA-PR-Permission still open; same workaround as 57.31)

### 4.5 Sprint closeout self-check

- [ ] Sacred Rule check — 0 unchecked items deleted
- [ ] Acceptance Criteria — all 5 pass (PARITY + 0 catastrophic/structural + 5 gates green + baseline-lift validated + docs synced)
- [ ] Working tree clean post-merge — on main; only untracked older-sprint debug PNGs
- [ ] Branch deleted — `feature/sprint-57-32-sla-dashboard-repoint` deleted local + remote
