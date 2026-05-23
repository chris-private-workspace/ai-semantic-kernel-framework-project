# Sprint 57.31 — Checklist

> Plan: [`sprint-57-31-plan.md`](./sprint-57-31-plan.md)
>
> AD-Cost-Dashboard-Verbatim-Repoint — 3rd Phase-2 per-page verbatim-CSS re-point.
>
> Day 0-4; mirror 57.30 day structure (smaller scope = 5 days instead of 6).

---

## Day 0 — Plan + Checklist + 三-prong + before-baseline

### 0.1 Plan + Checklist drafted

- [x] **Plan file** `sprint-57-31-plan.md` exists with 11 sections
- [x] **Checklist file** (this file) drafted mirroring Sprint 57.30 format

### 0.2 Day-0 三-prong verify

- [ ] **Prong 1 — Path verify** (all §File Change List paths in real repo)
  - Sub: `Glob` 7 production file paths → expect 7 matches
  - Sub: `Glob` 3 NEW paths (REPOINT-REPORT.md + screenshot dirs) → expect 0 matches
  - DoD: 0 path drift OR drift findings catalogued as `D{N}`
- [ ] **Prong 2 — Content verify** (plan-time factual assertions in real code)
  - Sub: confirm mockup `CostPage` at `page-admin.jsx:201`
  - Sub: identify exact mockup line ranges for each of: page-head / `.grid-stats` KPI row / `.grid-main` chart row 1 / `.grid-main` table row (+ optional 4th section)
  - Sub: `grep -n "ProviderMixCard\|MonthPicker\|CostBreakdownTable" reference/design-mockups/` → verify if mockup has equivalents (if not, plan AP-2 BackendGapBanner OR production-only annotation)
  - Sub: `grep -n "grid-stats\|grid-main\|bar-track\|table" frontend/src/styles-mockup.css` → verify mockup CSS classes ready
  - Sub: read Sprint 57.24 v2 progress.md briefly to recall what cost-dashboard's current Phase-1 state is
  - DoD: ≥3 content-verify findings in progress.md Day 0
- [ ] **Prong 3 — Schema verify**: N/A (frontend-only)
- [ ] **Prong 4 — Visual baseline scope**: identify if any 22 routes' visual-regression baselines could go stale on Sprint 57.31 cost-dashboard changes (likely only `/cost-dashboard` itself); decide upfront vs Day 4 regen

### 0.3 Before-baseline screenshot capture

- [ ] **22 AppShellV2 route screenshots** via `route-sweep.mjs before` mode
  - Sub: update `route-sweep.mjs` OUT_DIR + MHist entry to point to sprint-57-31-* dir
  - DoD: 22 PNG in `claudedocs/4-changes/sprint-57-31-cost-dashboard-repoint/screenshots/before/`
- [ ] **cost-dashboard extras** (Playwright via `sprint-57-31-day0-extras.mjs` modeled after 57.30 day0-extras)
  - Sub: `/cost-dashboard` default state (MonthPicker closed, table without sort/filter)
  - Sub: `/cost-dashboard` table-with-anomaly-row visible (mockup shows `wonka-apac` + `tenant_3kp9` anomaly badges)
  - DoD: 2 PNG in `screenshots/before/`
- [ ] **Day 0 commit**

---

## Day 1 — Group B (page-head + KPI row)

### 1.1 US-B1 — page-head verbatim re-point — ✅ done (batched Day 1)

- [x] **Read mockup** `page-admin.jsx:203-219` + production index.tsx
- [x] **Re-point** `pages/cost-dashboard/index.tsx` — drop `pageTitle` prop on AppShellV2 (avoid duplicate); +6/-5
- [x] **Header MHist** updated

### 1.2 US-B2 — KPI grid-stats verbatim — ✅ done (batched Day 1)

- [x] **Read mockup** `page-admin.jsx:221-225` + production CostOverview.tsx
- [x] **Re-point** `CostOverview.tsx` — verbatim inline `.page-head` + `.grid-stats` + `.grid-main`; mockup-ui Stat/Spark/Card/Button/Badge primitives; +146/-118
- [x] **Header MHist** updated

### 1.3 Day 1 mini-verify

- [x] Playwright 3 shots (`day1-cost-dashboard-full.png` + `day1-cost-dashboard-fold.png` + `day1-cost-dashboard-table-anomaly.png`) → PARITY visual confirmed
- [ ] Day 1 commit (pending — covers all 7 files batched per Day 0 visual finding adjustment)

---

## Day 2 — Subsumed into Day 1 batched delegation (per Day 0 visual finding)

Day 2 + Day 3 work all done in Day 1 batched delegation. Rationale: Day 0 baseline showed production cost-dashboard already very mockup-aligned from Sprint 57.24 v2 strict rebuild; batching 7 files in one agent delegation more efficient than 3 daily delegations.

- [x] **US-C1 CategoryBarsCard** — mockup-ui Card + `.col`/`.spread`/`.bar-track` verbatim; +64/-37
- [x] **US-C2 ProviderMixCard** — mockup-ui Card/Icon + `.col`/`.spread`/`.bar-track`/`.thin-rule`/`.subtle` verbatim per `page-admin.jsx:295-318`; +91/-59
- [x] **US-C3 MonthPicker** — production-only filter UI; mockup token vocabulary (var(--*) inline); no AP-2 banner; +44/-13

---

## Day 3 — Subsumed into Day 1 batched delegation

- [x] **US-D1 CostBreakdownTable** — Decision (c) production-only-by-design (real backend `by_type` 2-level drill-down for current tenant); mockup `.table`/`.mono`/`.tnum`/`.subtle` vocabulary; no AP-2 banner (real backend data, no gap); +66/-39
- [x] **US-D2 TenantTopTable** — mockup-ui Card/Badge + `.table`/`.row`/`.mono`/`.tnum`/`.subtle`/`.bar-track` verbatim per `page-admin.jsx:253-294`; preserved `text-danger`/`-warning` Tailwind classnames alongside inline-style color for Vitest contract continuity; +138/-94
- [x] **US-D3 Vitest comprehensive** — 452/452 (no spec drift; testid + class-membership contracts preserved)

---

## Day 4 — Group E (regression sweep + fidelity + closeout)

### 4.1 US-E1 — 22-route regression sweep

- [x] **after-sweep** via `route-sweep.mjs after` — 22 PNG captured
- [x] **Agent triage** — 18 🟢 PARITY + 1 🟢 PROP-stub + 0 🟡/🟠/🔴 + 3 ⚪ pre-existing fails (cleanest yet)
- [x] **REPOINT-REPORT.md** written (agent-produced)

### 4.2 US-E2 — /cost-dashboard fidelity verify

- [x] **Step 1** styles.css ↔ styles-mockup.css diff → empty (foundation untouched)
- [x] **Step 2** mockup vs prod assessed via triage agent (read mockup file structure + Day 1 verify screenshots)
- [x] **Step 3** 12 visible mockup elements catalogued in REPOINT-REPORT.md
- [x] **Step 4** drift verdict **🟢 PARITY** logged

### 4.3 US-E3 — Full gates

- [x] tsc strict — only pre-existing TS6310 carryover
- [x] ESLint exit 0
- [x] Vitest 452/452 (unchanged baseline; 0 spec drift)
- [x] Vite build 3.14s; bundle 336.80 kB (unchanged from Sprint 57.30 post-cleanup)
- [x] check:mockup-fidelity 25/25 unchanged (no new oklch literals)
- [x] Bundle size delta logged: 0 change (no orphan cleanup this sprint)

### 4.4 US-E4 — Closeout

- [x] **retrospective.md** Q1-Q6 written (Q7 N/A SKIP per Sprint 57.29-57.30 precedent; Q4 has bimodal-watch 3rd-data-point evaluation + RESOLUTION action)
- [x] **Memory snapshot** `memory/project_phase57_31_cost_dashboard_repoint.md` NEW
- [x] **MEMORY.md** pointer entry added
- [x] **CLAUDE.md** Current Sprint row + footer updated (minimal touch)
- [x] **`sprint-workflow.md §Scope-class multiplier matrix`** updated — `frontend-verbatim-css-repoint` row now 3 data points + baseline LIFTED 0.60→0.50 + MHist entry; `AD-Sprint-Plan-frontend-verbatim-bimodal-watch` CLOSED in row text
- [x] **`next-phase-candidates.md`** updated — bimodal-watch CLOSED, replaced by baseline-lift AD; +2 NEW carryover (baseline-lift + CostBreakdownTable-Backend-Tenant-Scope); 3 production-only widget patterns documented
- [ ] **Day 4 commit** — pending (next step)
- [ ] **PR open** — pending Day 4 commit
- [ ] **CI green → squash-merge** — pending PR

### 4.5 Sprint closeout self-check

- [x] Sacred Rule check — 0 unchecked items deleted
- [x] Acceptance Criteria — all pass (PARITY verdict + 0 catastrophic/structural + 5 gates green + bimodal-watch resolved + docs synced)
- [ ] Working tree clean post-merge — pending
- [ ] Branch deleted — pending
