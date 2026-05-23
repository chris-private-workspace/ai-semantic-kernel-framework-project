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

### 1.1 US-B1 — page-head verbatim re-point

- [ ] **Read mockup** `page-admin.jsx:203-219` CostPage page-head + audit production `pages/cost-dashboard/index.tsx`
- [ ] **Re-point** `pages/cost-dashboard/index.tsx` page-head: title "Cost Ledger" + subtitle "Range 12 · Token + tool spend · admin-only provider breakdown" + `.route-pill /cost-dashboard` + `<Badge tone="warning">admin scope</Badge>` + actions (By tenant filter + CSV export); preserve AppShellV2 wrap, RequireAuth, page-level hooks
- [ ] **Header MHist** update (1-line ≤100 chars)

### 1.2 US-B2 — KPI grid-stats verbatim

- [ ] **Read mockup** `page-admin.jsx:221-225` `.grid-stats` 4-stat row + audit production `CostOverview.tsx`
- [ ] **Re-point** `CostOverview.tsx` to verbatim `.grid-stats` div + 4 `<Stat>` cards (Spend MTD + Tokens MTD + Cost per run + Cache hit rate) using existing mockup-ui `<Stat>` + `<Spark>` primitives (Sprint 57.29 verbatim — reuse, do NOT re-port)
- [ ] **Header MHist** update

### 1.3 Day 1 mini-verify

- [ ] Playwright screenshot `/cost-dashboard` showing new page-head + KPI row → `screenshots/day1-verify/`
- [ ] Day 1 commit

---

## Day 2 — Group C (chart cards row)

### 2.1 US-C1 — CategoryBarsCard verbatim

- [ ] **Read mockup** `page-admin.jsx:228-251` 6-row `.bar-track` category list
- [ ] **Re-point** `CategoryBarsCard.tsx` — 6 rows with color dot + name + cost + `.bar-track` pct fill verbatim
- [ ] **Header MHist** update

### 2.2 US-C2 — ProviderMixCard verbatim (or production-only)

- [ ] **Day 0 Prong 2** result determines: mockup has equivalent OR mark production-only
- [ ] **Re-point** OR **annotate** with `BackendGapBanner` + verbatim token vocabulary
- [ ] **Header MHist** update

### 2.3 US-C3 — MonthPicker verbatim (or production-only)

- [ ] **Day 0 Prong 2** result determines treatment
- [ ] **Re-point** OR **annotate** as production-only with mockup-token vocabulary
- [ ] **Header MHist** update

### 2.4 Day 2 mini-verify + commit

- [ ] Playwright screenshot `/cost-dashboard` showing chart row + production widgets
- [ ] Day 2 commit

---

## Day 3 — Group D (table cards + Vitest)

### 3.1 US-D1 — CostBreakdownTable verbatim

- [ ] **Day 0 Prong 2** finalizes mockup line range (potentially `page-admin.jsx:295+` after TenantTopTable)
- [ ] **Re-point** to `.table` + cells + per-row visual treatment verbatim
- [ ] **Header MHist** update

### 3.2 US-D2 — TenantTopTable verbatim

- [ ] **Read mockup** `page-admin.jsx:259-294` TenantTopTable section
- [ ] **Re-point** `TenantTopTable.tsx` — `.table` + 8-row body + plan `<Badge>` + tokens + cost + quota% color-coded text + `.bar-track` quota fill + anomaly `<Badge tone="danger" dot>` verbatim
- [ ] **Header MHist** update

### 3.3 US-D3 — Vitest comprehensive

- [ ] `npm run test -- cost-dashboard` → all pass
- [ ] Adapt any spec drift from translated DOM → verbatim DOM
- [ ] Day 3 commit

---

## Day 4 — Group E (regression sweep + fidelity + closeout)

### 4.1 US-E1 — 22-route regression sweep

- [ ] **after-sweep** via `route-sweep.mjs after`
- [ ] **Agent triage** classify all 22; expect 1 🟢 PARITY (/cost-dashboard) + 21 🟢 PARITY or 🟡 minor + 0 🟠/🔴; 3 ⚪ pre-existing fails classified explicitly NOT regression
- [ ] **REPOINT-REPORT.md** written

### 4.2 US-E2 — /cost-dashboard fidelity verify

- [ ] **Step 1** styles.css diff empty
- [ ] **Step 2** mockup vs prod Playwright 1440×900
- [ ] **Step 3** computed-style 10+ representative elements
- [ ] **Step 4** drift verdict logged; ideally PARITY

### 4.3 US-E3 — Full gates

- [ ] tsc strict (only pre-existing TS6310 carryover)
- [ ] ESLint exit 0
- [ ] Vitest all-pass; count delta logged
- [ ] Vite build successful
- [ ] check:mockup-fidelity baseline updated if new oklch literals introduced
- [ ] Bundle size delta logged (expected small; no orphan cleanup planned this sprint)

### 4.4 US-E4 — Closeout

- [ ] **retrospective.md** Q1-Q7 written (Q4 must include bimodal-watch 3rd-data-point evaluation + class action per §Class baseline 3rd-data-point evaluation criteria matrix)
- [ ] **Memory snapshot** `memory/project_phase57_31_cost_dashboard_repoint.md` NEW
- [ ] **MEMORY.md** pointer entry
- [ ] **CLAUDE.md** Current Sprint row + footer
- [ ] **`sprint-workflow.md §Scope-class multiplier matrix`** updated — `frontend-verbatim-css-repoint` 3rd-data-point row; CLOSE OR UPDATE `AD-Sprint-Plan-frontend-verbatim-bimodal-watch` per evaluation
- [ ] **`next-phase-candidates.md`** updated — close bimodal-watch AD if resolved; add any new carryover ADs
- [ ] **Day 4 commit** + **PR open** + **CI green → squash-merge** + branch cleanup

### 4.5 Sprint closeout self-check

- [ ] Sacred Rule check — 0 unchecked items deleted
- [ ] Acceptance Criteria — all pass
- [ ] Working tree clean post-merge
- [ ] Branch deleted
