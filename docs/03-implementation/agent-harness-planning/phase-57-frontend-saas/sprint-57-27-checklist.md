# Sprint 57.27 — Checklist (AD-Mockup-Fidelity-Rebuild-Overview)

[Link to plan](./sprint-57-27-plan.md)

**Class**: `frontend-mockup-strict-rebuild` 0.60 (4th application; baseline KEEP per 3-sprint window rule)
**Workload**: Bottom-up ~6.5 hr → calibrated commit ~3.9 hr (multiplier 0.60)
**Day count**: 4 (Day 0 setup + 三-prong + Prong 5 / Day 1 page-head + KPI + Active Loops + HITL Queue / Day 2 Cost Burn + Providers + Incidents + Error Trend + Quick Actions / Day 3 i18n + integration + closeout)
**4th-data-point watch**: Day 3 retro Q2 records actual/committed ratio as the 4th `frontend-mockup-strict-rebuild` data point + the rich-dashboard sub-classification DECISION (per next-phase-candidates #41); KEEP 0.60 regardless

---

## Day 0 — Plan + Checklist + 三-prong + Prong 5 + DRIFT-REPORT skeleton (2026-05-21)

### 0.1 Plan + Checklist + Branch
- [x] **Plan drafted** at `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-27-plan.md`
  - DoD: 13-section structure mirror Sprint 57.25 (frontmatter + Sprint Goal / Background / User Stories / Technical Specs / File Change List / Acceptance Criteria / Deliverables / Dependencies & Risks / Workload / Sequencing)
  - Verify: file exists; sections present
- [x] **Checklist drafted** at `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-27-checklist.md`
  - DoD: Day 0-3 structure; per-task DoD + Verify command; sub-bullets 3-6 per task; final Day 6-step closeout (3.1-3.6)
  - Verify: this file exists
- [x] **Branch creation** from main `fb27df73`
  - DoD: `git checkout -b feature/sprint-57-27-overview-rebuild`
  - Verify: `git branch --show-current` → `feature/sprint-57-27-overview-rebuild`
- [x] **DRIFT-REPORT skeleton** at `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-27/artifacts/overview-rebuild/DRIFT-REPORT.md`
  - DoD: D1-D16 drift list table + 9-widget mockup-vs-production matrix skeleton + mockup ref resolution (`page-overview.jsx:74-379`)
  - Verify: file exists
- [x] **progress.md Day 0** at `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-27/progress.md` → 8 D-PRE findings catalogued
  - DoD: Day 0 entry with 三-prong findings + Prong 5 cross-ref + D-PRE findings
  - Verify: file exists

### 0.2 Day 0 三-prong (Prong 1 path + Prong 2 content + Prong 4 test selector)
- [x] **Prong 1 Path verify**: shared primitives + overview files exist as plan assumes → 7 primitives present; `features/overview/` dir ABSENT (D-PRE-1)
  - DoD: `components/ui/{CardShell,PageHead,BackendGapBanner}.tsx` + `components/charts/{Spark,StatCard,AreaChart,BarTrack}.tsx` all present (7 reuse targets)
  - DoD: `pages/overview/OverviewPage.tsx` present (728 lines, REWRITE target); `features/overview/` dir exists or needs creation (7 NEW component files)
  - Verify: `Glob` each path
- [x] **Prong 2 Content verify**: shared-primitive APIs serve overview needs → D-PRE-4 (PageHead no meta slot) / D-PRE-5 (CardShell title 14px) / D-PRE-6 (Loop type no agent/model)
  - DoD: read `PageHead` props — confirm title/subtitle/routePath/actions slots; check for a mono-meta slot (R1 — if absent, US-B1 decision = feature-scoped sibling line)
  - DoD: read `StatCard` props — confirm `spark` prop exists (Sprint 57.25 used it; R2)
  - DoD: read `CardShell` props — confirm `flush`/`dense` body variants
  - DoD: read `AreaChart` API — assess if it can express CostBurnChart budget-diagonal (R3 — default: keep CostBurnChart bespoke SVG)
  - DoD: read `useActiveLoops` return shape — confirm fields ActiveLoopsCard needs (agent/session/tenant/model/turns)
  - Verify: `Read` each primitive + hook; catalogue findings as D-PRE in progress.md
- [x] **Prong 4 Test selector verify**: existing overview specs + visual-regression baseline → D-PRE-2 / D-PRE-7
  - DoD: locate existing OverviewPage Vitest spec; note selectors that will break on extracted-component rewrite
  - DoD: D-PRE-2 — `/overview` is NOT in `visual-regression.spec.ts` (6-route list excludes it); rebuild will NOT trigger a 57.26-style CI failure; US-D3 may optionally add it
  - Verify: `Grep` overview spec + visual-regression.spec.ts

### 0.3 Day 0 Prong 5 audit cross-ref
- [x] **Prong 5**: Sprint 57.22 AUDIT-REPORT overview row → Unit 7 COSMETIC 60% 3-4hr; "Remove h1" action WRONG (D-PRE-8)
  - DoD: grep `claudedocs/4-changes/sprint-57-22-*/AUDIT-REPORT-COMPREHENSIVE.md` for the overview unit — confirm priority classification + estimate vs this sprint's scope
  - Verify: `Grep` AUDIT-REPORT; catalogue in progress.md Day 0

### 0.4 Day 0 commit
- [x] **Fold Sprint 57.26 checklist §3.4** [x] marks (Merge / Post-merge cleanup) per user decision 2026-05-21
  - DoD: `sprint-57-26-checklist.md` §3.4 last 2 items already `[x]` (done this session); confirm staged
- [x] **Day 0 commit** — plan + checklist + 三-prong + DRIFT skeleton + progress + 57.26 §3.4 fold
  - DoD: `git add` plan + checklist + DRIFT skeleton + progress.md + sprint-57-26-checklist.md
  - Commit message: `chore(sprint-57-27, Day 0): plan + checklist + 三-prong + DRIFT skeleton + 57.26 §3.4 fold`
  - Verify: `git log --oneline -1` → commit `43eedcee` (5 files)

---

## Day 1 — Group B (page-head + KPI row + Active Loops + HITL Queue) (2026-05-22)

### 1.1 US-B1 — page-head + KPI row 4-stat WITH sparklines
> 🚧 **DEFERRED to Day 3 OverviewPage assembly** — page-head + KPI row are in-page JSX inside `OverviewPage.tsx` (not standalone component files). Execution-order adjustment: standalone widget component files (`features/overview/components/*`) are built first (Day 1-2), then the `OverviewPage.tsx` final assembly (page-head + KPI + 9-widget grid) lands Day 3. Items kept `[ ]` per sacred rule.
- [ ] **Page-head** rebuilt per mockup `page-overview.jsx:74-87`
  - In-page title + subtitle + `/overview` route-pill + page-actions (Export outline + New Chat primary)
  - Mono `{tenant} · {role} · {clock}` meta line (D2; R1 decision — feature-scoped sibling unless PageHead has meta slot)
  - D1 closed: in-page title rendered; AppShellV2 topbar title decision (R7 — suppress duplicate or keep one)
  - DoD: page-head matches mockup at 1440×900
- [ ] **KPI row** 4× `<StatCard>` per mockup `:90-95`
  - Active Sessions (`14 loops`, +3↑) / HITL Pending (`3 approvals`, 1 critical↓) / Cost MTD (`$2,847` + sparkline) / SLA p95 (`1.84s` + sparkline)
  - D3 + D5 closed: Cost MTD + SLA p95 use `<StatCard spark>` + `<Spark>`; D10 stat delta arrow = SVG icon
  - `kpiSparklines.ts` fixture (2 spark arrays)
  - DoD: 4 stats render; 2 sparklines visible
- [ ] **Verify**: `npm run build` clean; page-head + KPI render at 1440×900

### 1.2 US-B2 — ActiveLoopsCard + HITLQueueCard
- [x] **ActiveLoopsCard** (NEW; `features/overview/components/ActiveLoopsCard.tsx`) — commit `9c4fd7f6`
  - 5-col loopRow per mockup `:99-141`; D4 layout closed; agent_name/model placeholder per D-PRE-6 (`AD-Loop-Session-Enrich-Phase58`); `MAX_TURNS=50` hardcoded (D15)
  - Preserves `useActiveLoops(10)` real data + loading/error/empty states
  - Uses `<CardShell>` (flush body)
  - DoD: real loop rows render; loading/error/empty states intact ✅
- [x] **HITLQueueCard** (NEW; `features/overview/components/HITLQueueCard.tsx`) — commit `9c4fd7f6`
  - 3 risk-tinted cards per mockup `:143-167`; D13 closed: critical tint matches mockup `oklch(.../0.08)`
  - `__fixtures__/hitlQueue.ts` fixture + `<BackendGapBanner>`
  - DoD: 3 cards render; critical card danger-tinted; banner visible ✅
- [ ] 🚧 **Verify**: ActiveLoops + HITL render in `grid2` 1.4fr/1fr layout — DEFERRED to Day 3 OverviewPage assembly (components built + imported; grid2 layout is an assembly-stage task)

### 1.3 Vitest — Day 1 components
- [x] **ActiveLoopsCard.test.tsx** — `tests/unit/features/overview/` (loading / error / empty / happy 5-col row) — commit `9c4fd7f6`
- [x] **HITLQueueCard.test.tsx** — `tests/unit/features/overview/` (3 cards / critical tint / BackendGapBanner) — commit `9c4fd7f6`
  - DoD: Vitest 430→437/437 passing (+7); no regression ✅
  - Verify: `npm run test` ✅ / `npm run lint` ✅ / `npm run build` ✅

### 1.4 Day 1 Playwright MCP pair-verify + commit
- [ ] 🚧 **Playwright MCP** pair-verify Day 1 widgets (mockup 8080 + production 3007 at 1440×900) — DEFERRED to Day 3: ActiveLoops + HITL are visible on `/overview` only after the OverviewPage assembly wires the grid2 layout; pair-verify the full page once Day 3 assembly completes
  - DoD: page-head + KPI + ActiveLoops + HITL screenshot compared; drift noted in DRIFT-REPORT
- [x] **Day 1 commit** (partial — Group B widgets) — commit `9c4fd7f6` (10 files +565/-171)
  - Commit message: `feat(frontend, sprint-57-27, Day 1, Group B): ActiveLoopsCard + HITLQueueCard + _primitives extract`
  - Scope: ActiveLoopsCard + HITLQueueCard + `_primitives.tsx` + `__fixtures__/hitlQueue.ts` + 2 Vitest specs; OverviewPage -170 lines (inline defs removed, new components imported); i18n EN+zh-TW +1 key. page-head + KPI (US-B1) deferred to Day 3 assembly.

---

## Day 2 — Group C (Cost Burn + Providers + Incidents + Error Trend + Quick Actions) (2026-05-23)

### 2.1 US-C1 — CostBurnChart + ErrorTrendChart
- [x] **CostBurnChart** (NEW; `features/overview/components/CostBurnChart.tsx`) — commit `2bd7c776`
  - SVG cumulative 30-day burn line + gradient area + budget diagonal + gridlines per mockup `:273-329`
  - D16 closed: x-axis labels (`day 1 / today / day 30`) + budget-line text label ✅
  - `costBurn.ts` fixture; bespoke SVG (R3 — not force-fit AreaChart) ✅
  - `<BackendGapBanner>` added (not in mockup; AP-2 honesty — fixture-backed per DRIFT-REPORT §4)
  - DoD: chart renders with axis labels + budget line ✅
- [x] **ErrorTrendChart** (NEW; `features/overview/components/ErrorTrendChart.tsx`) — commit `2bd7c776`
  - 24-bar histogram + tone-by-value per mockup `:331-379` ✅
  - D16 closed: x-axis labels (`-24h / -12h / now`) ✅
  - `errorTrend.ts` fixture ✅; `<BackendGapBanner>` added (AP-2 honesty, same rationale)
  - DoD: 24 bars render with axis labels ✅
- [x] **Verify**: both charts wired into OverviewPage `grid2eq` layout; build ✅

### 2.2 US-C2 — ProvidersCard + IncidentsCard
- [x] **ProvidersCard** (NEW; `features/overview/components/ProvidersCard.tsx`) — commit `2bd7c776`
  - 4-row trafficDot (green/amber/red glow) + mono name + p95 + calls per mockup `:180-199` ✅
  - `providers.ts` fixture + `<BackendGapBanner>` ✅ (glow uses `color-mix(in oklch …)` — functional equivalent of mockup `oklch(from …)`, wider browser support)
  - DoD: 4 rows render with trafficDot tones ✅
- [x] **IncidentsCard** (NEW; `features/overview/components/IncidentsCard.tsx`) — commit `2bd7c776`
  - 4-row RiskBadge + mono id + title + status Badge + since per mockup `:204-225` ✅
  - D11 closed: Badge 4px radius (not pill); D12 closed: RiskBadge `risk-*` token tone map ✅ (via shared `_primitives.tsx`)
  - `incidents.ts` fixture + `<BackendGapBanner>` ✅
  - DoD: 4 rows render; badges 4px square; RiskBadge tones correct ✅
- [x] **Verify**: Providers + Incidents wired into OverviewPage; build ✅

### 2.3 US-C3 — QuickActionsStrip
- [x] **QuickActionsStrip** (NEW; `features/overview/components/QuickActionsStrip.tsx`) — commit `2bd7c776`
  - 4 quickBtn (New Chat / Review governance / Tenants / Verification; icon + label + sub) per mockup `:236-266` ✅
  - Full-width flex row; each button navigates on click ✅
  - DoD: 4 buttons render; navigate works ✅
- [x] **Verify**: strip wired into OverviewPage below grids; build ✅

### 2.4 Vitest + Playwright + Day 2 commit
- [x] **Vitest specs** — CostBurnChart (4) + ErrorTrendChart (4) + ProvidersCard (4) + IncidentsCard (4) + QuickActionsStrip (4) — commit `2bd7c776`
  - DoD: Vitest 437 → 457 passing (+20); no regression ✅
- [ ] 🚧 **Playwright MCP** pair-verify Day 2 widgets — DEFERRED to Day 3 §3.3 full-page pair-verify (widgets visible on `/overview` only after Day 3 assembly polishes the grid layout to mockup fidelity; single full-page pass is more efficient than per-widget)
- [x] **Day 2 commit** — commit `2bd7c776` (17 files, +1164/-360)
  - Commit message: `feat(frontend, sprint-57-27, Day 2, Group C): CostBurnChart + ErrorTrendChart + ProvidersCard + IncidentsCard + QuickActionsStrip`

---

## Day 3 — Group D + closeout (2026-05-24)

### 3.1 US-D1 — i18n EN + zh-TW
- [x] **i18n keys** added to `frontend/src/i18n/locales/{en,zh-TW}/common.json` — commits `2bd7c776` (widget keys) + `dd405c6b` (page-head + KPI keys)
  - NEW keys: `overview.{title,subtitle,export,newChat}` + `overview.kpi.*` + `overview.{costBurn,errors,providers,incidents,quickActions}.*` + 4 BackendGapBanner reasons
  - DoD: EN + zh-TW parity; no missing-translation warnings on `npm run build` ✅
  - Verify: `npm run build` ✅

### 3.2 US-D2 — OverviewPage final assembly
- [x] **OverviewPage.tsx rewritten** — 728-line all-in-one → ~215-line assembly — commit `dd405c6b`
  - Imports 9 extracted widgets + shared primitives (PageHead / StatCard / Spark / CardShell); mockup-faithful grid layout (kpiRow gap-12 / grid2 1.4fr+1fr / grid2eq×2 / quick strip) ✅
  - Token drifts closed: D6 (radius 12px ✓) / D7 (card-head padding in CardShell) / D8 (card-title 12.5px — R9, shared CardShell) / D9 (stat padding in StatCard) / D14 (page mb-[14px] rhythm) ✅
  - AP-3 reversal COMPLETE: 0 inline `Card`/`Badge`/`Stat`/`RiskBadge` definitions remain ✅
  - page-head mono meta uses real `authStore` tenant + role (not mockup's hardcoded `acme-prod`); R7: no AppShellV2 pageTitle → no topbar duplicate
  - DoD: page assembles; all 9 widgets render ✅
- [x] **Existing OverviewPage spec adapted** — `tests/unit/pages/overview/OverviewPage.test.tsx` test 1 updated (in-page title vs `data-page-title` topbar) — commit `dd405c6b`
  - DoD: spec passes ✅ (6 tests intact)
- [x] **Verify**: `npm run lint && npm run build` clean ✅; Vitest 457/457

### 3.3 US-D3 — Vitest + Playwright + visual-regression
- [x] **Vitest 457** passing (430 baseline + 27 new — ActiveLoops/HITL Day 1 + 5 widgets Day 2) — no regression
  - Verify: `npm run test` ✅ 94 files / 457 tests
- [x] **Playwright MCP pair-verify** full page (mockup 8080 + production 3007 @ 1440×900) — commit pending
  - DoD: full-page screenshots `sprint-57-27-{mockup,prod}-overview.png` compared; verdict PARITY; 1 noted divergence (ActiveLoops live 404) logged in DRIFT-REPORT §3/§4
- [x] **visual-regression baseline regenerate** — N/A per D-PRE-2: `/overview` is NOT in `visual-regression.spec.ts` (6-route list excludes it); no baseline exists to regenerate; rebuild does not trigger a 57.26-style CI failure (R5 RESOLVED). Optional add of `/overview` to the spec deferred (out-of-scope; consider Ops Dashboards sprint).

### 3.4 DRIFT-REPORT verdict
- [x] **DRIFT-REPORT** §verdict for `/overview` = **PARITY**
  - DoD: D1-D14 + D16 closed; D17 accepted addition; D15 + ActiveLoops-404 carryover; per-widget A-I verdict recorded ✅
- [x] **Cosmetic regressions iterated** to parity — pair-verify found no cosmetic regression needing iteration; the 1 noted item (ActiveLoops live 404) is a backend-data carryover, not cosmetic

### 3.5 Retrospective + memory + closeout
- [x] **retrospective.md** Q1-Q7 + Q2 calibration (ratio ≈0.95, 4th data point) + Q2.1 #41 rich-dashboard sub-class DECISION = DROPPED
- [x] **memory snapshot** `memory/project_phase57_27_overview_rebuild.md` created + MEMORY.md +1 quality pointer
- [x] **`.claude/rules/sprint-workflow.md`** calibration matrix — `frontend-mockup-strict-rebuild` row +1 data point (57.27≈0.95, 4-pt mean 0.90, #41 DROPPED) + MHist entry
- [x] **`next-phase-candidates.md`** — added #43 AD-Overview-Backend-Extensions-Phase58 + #44 AD-CardShell-Title-Crossverify-cost-sla; resolved #41 (rich-dashboard sub-class DROPPED)
- [x] **CLAUDE.md** Current Sprint row + Last Updated footer (minimal touch per REFACTOR-001 §Sprint Closeout)

### 3.6 PR open + CI + merge
- [ ] **PR open** with body (Sprint 57.27 scope + 16-drift closure + 9 widget groups + AP-3 reversal + 4th-app calibration + visual-baseline regen note)
- [ ] **CI green**: all 6 required checks (visual-regression baseline pre-regenerated per 3.3)
- [ ] **Merge** (after CI green + user approval; squash per Sprint 57.23-57.26 pattern)
- [ ] **Post-merge cleanup**: local + remote feature branch delete + any throwaway visual-baseline branch delete

---

## Key Decisions Required During Sprint

| ID | Decision | When | Default |
|----|----------|------|---------|
| R1 | PageHead mono-meta slot — extend shared primitive vs feature-scoped sibling line | Day 1 (US-B1) | Feature-scoped sibling (Karpathy §2 — 1 consumer) |
| R3 | CostBurnChart — reuse `<AreaChart>` vs bespoke SVG | Day 0 Prong 2 / Day 2 | Bespoke feature-scoped SVG (mockup-direct port) |
| R7 | In-page title vs AppShellV2 topbar title | Day 1 (US-B1) | Render in-page per mockup; suppress topbar duplicate |
| — | Playwright e2e for `/overview` — add bootstrap spec vs defer | Day 3 | Defer unless quick (out-of-scope; consider Ops Dashboards sprint) |
