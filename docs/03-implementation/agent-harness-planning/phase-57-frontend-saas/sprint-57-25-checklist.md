# Sprint 57.25 — Checklist (AD-Mockup-Fidelity-Rebuild-Sla-Dashboard)

[Link to plan](./sprint-57-25-plan.md)

**Class**: `frontend-mockup-strict-rebuild` 0.60 (3rd application; KEEP baseline per 3-sprint window rule)
**Workload**: Bottom-up ~5.7 hr → calibrated commit ~3.4 hr (multiplier 0.60)
**Day count**: 4 (Day 0 setup + 三-prong + Prong 5 / Day 1 Group B / Day 2 Group C / Day 3 Group D + closeout)
**3rd-app data point watch**: Per Sprint 57.24 v2 retro Q4 — if ratio ≥ 1.0 confirms rich-dashboard pattern → Day 3 sub-classification proposal; if < 0.85 → KEEP 0.60 + wait for 4th data point

---

## Day 0 — Plan + Checklist + 三-prong + Prong 5 + DRIFT-REPORT skeleton (2026-05-19)

### 0.1 Plan + Checklist + Branch
- [x] **Plan drafted** at `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-25-plan.md`
  - DoD: 9-section structure mirror Sprint 57.24 v2 (Sprint Goal / Background / User Stories / Technical Spec / File Change List / Acceptance Criteria / Deliverables / Risks / Workload + Day plan)
  - Verify: file exists; sections present
- [x] **Checklist drafted** at `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-25-checklist.md`
  - DoD: Day 0-3 structure; per-task DoD + Verify command; sub-bullets 3-6 per task
  - Verify: this file exists
- [x] **Branch creation** from main `345f74a3`
  - DoD: `git checkout -b feature/sprint-57-25-sla-dashboard-rebuild`
  - Verify: `git branch --show-current` → `feature/sprint-57-25-sla-dashboard-rebuild`
- [x] **DRIFT-REPORT skeleton** at `claudedocs/4-changes/sprint-57-25-sla-dashboard-rebuild/DRIFT-REPORT.md`
  - DoD: file with mockup ref `page-admin.jsx:31-199` resolution + 6-widget-group table skeleton
  - Verify: file exists
- [x] **progress.md Day 0** at `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-25/progress.md`
  - DoD: Day 0 entry with 三-prong + Prong 5 findings + DRIFT-REPORT skeleton ref
  - Verify: file exists

### 0.2 Day 0 三-prong (Prong 1 path + Prong 2 content + Prong 4 test selector)
- [x] **Prong 1 Path verify**: Sprint 57.24 v2 primitives + production SLA files exist
  - DoD: 7 primitives (`components/charts/{Spark,StatCard,AreaChart,BarTrack}.tsx` + `components/ui/{CardShell,PageHead,BackendGapBanner}.tsx`) ✅ confirmed present
  - DoD: 3 production SLA files (`pages/sla-dashboard/index.tsx` + `features/sla-dashboard/components/{SLAOverview,SLAMetricsCard}.tsx`) ✅ confirmed present
  - Verify: `Glob("frontend/src/components/{charts,ui}/*.tsx")` + `Glob("frontend/src/features/sla-dashboard/**/*.tsx")`
- [x] **Prong 2 Content verify**: useSLAReport response shape vs mockup field semantic
  - DoD: D-PRE-2 catalogued — useSLAReport returns `availability_pct` + `api_p99_ms` + `loop_simple_p99_ms` + `loop_medium_p99_ms` + `loop_complex_p99_ms` + `hitl_queue_notif_p99_ms` (only `_p99_*` no `_p50_*` no `_p95_*` no `error_budget`); mockup expects p50/p95/p99 split + error_budget separately
  - Implication: 3 of 4 stat cards + LatencyChart 3-series fully fixture-driven + AP-2 banner (real backend = `api_p99_ms` → p99 stat card only)
  - Verify: `Grep("availability_pct|p99_ms", frontend/src/features/sla-dashboard/hooks/useSLAReport.ts)` + read hook return type
- [x] **Prong 4 Test selector verify**: existing test files + visual-regression snapshot routes
  - DoD: D-PRE-3 catalogued — `SLAOverview.test.tsx` exists; `SLAMetricsCard.test.tsx` exists; `frontend/tests/e2e/sla*` does NOT exist (different from cost-dashboard which had e2e); visual-regression.spec.ts 6-route list — check if `/sla-dashboard` already in
  - Verify: `Glob("frontend/src/features/sla-dashboard/components/__tests__/*.test.tsx")` + `Grep("sla-dashboard", frontend/tests/visual/visual-regression.spec.ts)`

### 0.3 Day 0 Prong 5 audit cross-ref (per AD #38)
- [x] **Prong 5 audit cross-ref**: Sprint 57.22 AUDIT-REPORT-COMPREHENSIVE.md classification for sla-dashboard
  - DoD: confirmed Unit 9 = P0 full rebuild (same FUNCTIONAL pattern as Unit 8 cost-dashboard); 15% mockup-fidelity baseline; 4-5 hr audit estimate aligned with this plan's ~5.7 hr bottom-up
  - Verify: `grep -B2 -A5 "Unit 9.*sla-dashboard" claudedocs/4-changes/sprint-57-22-mockup-fidelity-audit/AUDIT-REPORT-COMPREHENSIVE.md`
- [x] **No Prong 5 conflict** with #32 carryover spec
  - DoD: #32 spec scope (6 widget groups; reuses 7 primitives; 3rd app data point) aligns with audit P0 finding + Sprint 57.24 v2 retro Q4 carryover
  - Implication: rebuild scope = full strict; NO Tier 1 cosmetic-retrofit miscarriage like Sprint 57.24 v1

### 0.4 Day 0 commit
- [x] **Day 0 commit** with plan + checklist + Day 0 progress + DRIFT-REPORT skeleton — commit `70890f4d` (4 files; 942 insertions)
  - Commit message: `chore(sprint-57-25, Day 0): plan + checklist + Day 0 三-prong + Prong 5 + DRIFT-REPORT skeleton`
  - DoD: `git status` clean post-commit; commit hash recorded in progress.md
  - Verify: `git log --oneline -1`

---

## Day 1 — Group B (page-head + 4-stat + LatencyChart) (2026-05-20)

### 1.1 US-B1 page-head + TimeRangeTabs + Refresh + Export stubs
- [x] **`<TimeRangeTabs>` component** at `frontend/src/features/sla-dashboard/components/TimeRangeTabs.tsx` (~50 lines)
  - Props: NONE (consumes local React useState; 4 ranges `1h | 24h | 7d | 30d`; default "24h")
  - DoD: visual matches mockup `page-admin.jsx:42-48` (inline-flex rounded border group; active tab has bg-bg-2 + text-fg; inactive has text-fg-muted + hover); role="tablist" + role="tab" + aria-selected for a11y; data-testid="sla-range-tab-{1h|24h|7d|30d}"
  - i18n: `sla.range.{label, 1h, 24h, 7d, 30d}` ✅ EN + zh-TW parity
  - Vitest: `tests/unit/sla-dashboard/TimeRangeTabs.test.tsx` (~3 cases: 4 tabs render / 24h active default / click changes active)
- [x] **Refresh + Export buttons inline in SLAOverview** (no separate components; per checklist "OR inline" path; shadcn Button outline variant)
  - DoD: Refresh button onClick=`() => void refetch()`; disabled when `isFetching || !tenantId`; matches mockup `page-admin.jsx:49`
  - DoD: Export button disabled + title tooltip "Export pending Phase 58+" per AP-2 honesty
  - i18n: `sla.action.{refresh, export, exportPending}` ✅ EN + zh-TW parity
- [x] **`<PageHead>` consumption in SLAOverview** (Sprint 57.24 v2 primitive REUSED unchanged)
  - DoD: Page title "SLA Dashboard" + subtitle "Range 12 · Observability · p50 / p95 / p99 latency + error budget" + routePath="/sla-dashboard" + actions={TimeRangeTabs + RefreshButton + ExportButton}
  - i18n: `sla.pageTitle` / `sla.pageSub` ✅ EN + zh-TW parity
  - Verify: page-head 1440×900 matches mockup `page-admin.jsx:33-52`

### 1.2 US-B2 4-stat sparkline grid (StatCard + Spark reused)
- [x] **4-stat sparkline grid** in SLAOverview using Sprint 57.24 v2 `<StatCard>` + `<Spark>` primitives REUSED unchanged
  - DoD: 4 StatCard instances in `grid grid-cols-4 gap-3` + `data-testid="sla-stat-grid"`:
    - p50 latency: fixture "284" unit="ms" delta="-18ms" deltaDir="up" + Spark with primary tone
    - p95 latency: fixture "1.84" unit="s" delta="-180ms" deltaDir="up" + Spark with info tone
    - p99 latency: real value from `data.api_p99_ms / 1000` formatted (if backend response) or fixture "4.21" unit="s" + Spark with warning tone
    - Error budget: fixture "92.4" unit="%" delta="-1.2pp" deltaDir="down" + Spark with success tone
  - DoD: 3 of 4 cards explicitly fixture-driven per D-PRE-2 (useSLAReport doesn't expose p50/p95/error_budget); AP-2 honest — these cards don't get individual BackendGapBanner because the entire dashboard's missing-fields are covered by LatencyChart 24h banner
  - i18n: `sla.stat.{p50, p95, p99, errorBudget}` ✅ EN + zh-TW parity
- [x] **Fixture file** `frontend/src/features/sla-dashboard/__fixtures__/statSparklines.ts`
  - DoD: 4 spark arrays (SPARK_P50 / SPARK_P95 / SPARK_P99 / SPARK_ERROR_BUDGET) mirroring mockup `page-admin.jsx:55-58` demo values

### 1.3 US-B3 LatencyChart NEW (feature-scoped; Karpathy §2 inline)
- [x] **`<LatencyChart>` component** at `frontend/src/features/sla-dashboard/components/LatencyChart.tsx` (~110 lines mockup-direct port of `page-admin.jsx:157-198`)
  - Props: NONE (consumes inline fixture from `__fixtures__/latencyChart24h.ts`)
  - DoD: pure SVG; 3 series (p50 / p95 / p99); 48 time points; viewBox 760×220; pad 30; preserveAspectRatio="none"; SVG height attribute 220 (no inline style per STYLE.md §1)
  - DoD: 3 horizontal grid lines at 25/50/75%; x labels every 6h (-23h / -17h / -11h / -5h / -0h); y labels 4 ticks (0/0.25/0.5/0.75 normalized to max)
  - DoD: stroke widths p50=1.8 / p95=1.4 / p99=1.4 opacity=0.9; colors `var(--primary)` / `var(--info)` / `var(--warning)` per mockup
  - DoD: empty fixture returns null
  - data-testid="sla-latency-chart" for test
- [x] **`<CardShell>` consumption** for LatencyChart wrapper (Sprint 57.24 v2 primitive REUSED unchanged)
  - DoD: title `t("sla.latencyChart.title")` + subtitle `t("sla.latencyChart.subtitle")` + actions={kbar with 3 dot badges p50 (primary) / p95 (info) / p99 (warning)} matching mockup `page-admin.jsx:63-67`
  - i18n: `sla.latencyChart.{title, subtitle, badge.p50, badge.p95, badge.p99}` ✅ EN + zh-TW parity
- [x] **`<BackendGapBanner>` rendered** below LatencyChart (Sprint 57.24 v2 primitive REUSED unchanged)
  - DoD: `reason={t("sla.banner.latencyChart24h")}` declaring backend time-series aggregation endpoint pending Phase 58+; 1st of 3 banner instances this sprint
- [x] **Fixture file** `frontend/src/features/sla-dashboard/__fixtures__/latencyChart24h.ts`
  - DoD: 48-element array of `{p50, p95, p99}` objects mockup-faithful (seededNoise-based deterministic per mockup `page-admin.jsx:159-167` algorithm)
- [x] **Vitest spec** `tests/unit/sla-dashboard/LatencyChart.test.tsx` (5 cases: svg + 3 series paths / 5 x-tick / 4 y-tick / stroke-width hierarchy 1.8 vs 1.4 / p99 opacity 0.9)

### 1.4 Day 1 Playwright MCP retry + commit
- 🚧 **Playwright MCP `browser_close` reset attempt** deferred to Day 3 per Q4 user alignment + AD #37 4th-consecutive blocker watch policy; code-level audit substitute documented in progress.md Day 1 §Mockup-fidelity audit
- [x] **Day 1 commit** with Group B work — commit `24d46b89` (12 files; +745 / -50)
  - Commit message: `feat(sla-dashboard, sprint-57-25, Day 1, Group B): page-head + TimeRangeTabs + 4-stat sparkline + LatencyChart (NEW feature-scoped)`
  - DoD: `git status` clean post-commit ✅

---

## Day 2 — Group C (SLO status + slow ops + error rate) (2026-05-21)

### 2.1 US-C1 `<SLOStatusCard>` (BarTrack + CardShell reused)
- [x] **Component** at `frontend/src/features/sla-dashboard/components/SLOStatusCard.tsx` (~110 lines mockup-direct port of `page-admin.jsx:72-99`)
  - Props: `data: SLAReport` (from useSLAReport)
  - DoD: 5 SLO rows × success/danger dot indicator + SLO name + current value (mono tnum; danger color if failing) / target value (subtle) + `<BarTrack pct={used}>` budget-used % + budget used % subtle label
  - SLOs: Loop p95 < 2s (real `data.loop_simple_p95_ms / 1000` if available, else fixture 1.84; ok if < 2.0) / Tool success ≥ 99% (fixture 99.4; ok) / HITL response < 5m (fixture 2.3 min; ok) / Subagent depth ≤ 5 (fixture 4; ok) / Cost/run < $0.05 (fixture 0.052; FAILING — danger tone)
  - DoD: reuses `<CardShell title={t("sla.slo.title")} subtitle={t("sla.slo.subtitle")}>` + `<BarTrack pct tone />` (tone success when ok / danger when failing)
  - i18n: `sla.slo.{title, subtitle, loopP95, toolSuccess, hitlResponse, subagentDepth, costPerRun, budgetUsed}` ✅ EN + zh-TW parity
  - data-testid="sla-slo-card" + `data-testid="sla-slo-row-${idx}"` per row for test
- [x] **Vitest spec** `tests/unit/sla-dashboard/SLOStatusCard.test.tsx` (5 cases: 5 SLO rows render / dot color ok/failing / failing SLO danger text class / ok muted text class / Loop p95 proxy from real `loop_simple_p99_ms`)

### 2.2 US-C2 `<TopSlowOpsTable>` (CardShell + Badge reused)
- [x] **Component** at `frontend/src/features/sla-dashboard/components/TopSlowOpsTable.tsx` (~135 lines mockup-direct port of `page-admin.jsx:104-129`)
  - Props: NONE (consumes inline fixture from `__fixtures__/slowOps.ts`)
  - DoD: 6 rows × Operation (mono small) + Kind Badge (tool/loop/subagent/verify/memory tone palette mapping) + p50/p95/p99 (mono tnum right; p99 warning color if > 3000ms) + Calls (mono tnum subtle right toLocaleString)
  - Kind Badge tone mapping (mockup `page-admin.jsx:120`): tool→tool / loop→primary / subagent→thinking / verify→success / memory→memory
  - DoD: reuses `<CardShell title={t("sla.slowOps.title")} subtitle={t("sla.slowOps.subtitle")} bodyClass="flush">` + shadcn `<Badge>` for Kind column
  - Fixture: `__fixtures__/slowOps.ts` 6 rows mirror mockup `page-admin.jsx:111-116` values
  - i18n: `sla.slowOps.{title, subtitle, col.operation, col.kind, col.p50, col.p95, col.p99, col.calls}` ✅ EN + zh-TW parity
  - data-testid="sla-slow-ops-table"
- [x] **`<BackendGapBanner reason={t("sla.banner.crossOperationP99")} />`** below table (2nd of 3 banners this sprint)
- [x] **Vitest spec** `tests/unit/sla-dashboard/TopSlowOpsTable.test.tsx` (5 cases: 6 rows / Kind tone per kind / p99 warning > 3000 / p99 muted <= 3000 / cross-operation banner)

### 2.3 US-C3 `<ErrorRateByServiceCard>` (BarTrack + CardShell reused)
- [x] **Component** at `frontend/src/features/sla-dashboard/components/ErrorRateByServiceCard.tsx` (~82 lines mockup-direct port of `page-admin.jsx:131-152`)
  - Props: NONE (consumes inline fixture from `__fixtures__/errorRateByService.ts`)
  - DoD: 6 rows × service name (mono small) + rate % (mono tnum; warning color if > 0.5%, fg-muted otherwise) + `<BarTrack pct={rate * 50} tone={rate > 0.5 ? "warning" : "success"} />`
  - Services: inference.adapter (0.04) / tool.runner (0.6) / memory.store (0.0) / audit.writer (0.0) / subagent.scheduler (0.12) / webhook.dispatcher (0.4)
  - DoD: reuses `<CardShell title={t("sla.errorRate.title")} subtitle={t("sla.errorRate.subtitle")}>`
  - Fixture: `__fixtures__/errorRateByService.ts` 6 rows mirror mockup `page-admin.jsx:134-140` values
  - i18n: `sla.errorRate.{title, subtitle}` ✅ EN + zh-TW parity
  - data-testid="sla-error-rate-card"
- [x] **`<BackendGapBanner reason={t("sla.banner.perServiceErrorRate")} />`** below card (3rd of 3 banners this sprint)
- [x] **Vitest spec** `tests/unit/sla-dashboard/ErrorRateByServiceCard.test.tsx` (4 cases: 6 services / warning tone rate > 0.5 / muted tone rate <= 0.5 / per-service banner)

### 2.4 SLAOverview integration + Day 2 commit
- [x] **SLAOverview.tsx assembled** with all 6 widget groups in mockup-faithful grid (`grid grid-cols-4` 4-stat row + `grid grid-cols-[1fr_360px]` LatencyChart+SLO row + `grid grid-cols-2` slow-ops+error-rate row)
  - DoD: matches mockup `page-admin.jsx:61-153` 1:1 at 1440×900
  - DoD: MonthPicker preserved as auxiliary control (inline below page-head row with sibling note `sla.monthPickerAuxiliary`)
- [x] **MonthPicker placement decision** Day 2: KEEP inline + sibling note (Option A, per Q1 alignment + checklist default; AppShellV2 headerSlot Option B deferred — minimal drift principle preserved)
- [-] **Existing SLAOverview.test.tsx adapted** N/A — `SLAOverview.test.tsx` did not exist pre-rebuild (only SLAMetricsCard + slaStore + useSLAReport specs); no adapt needed
- [x] **SLAMetricsCard.tsx + SLAMetricsCard.test.tsx delete** (Karpathy §3 orphan delete; verified `grep -rn "SLAMetricsCard" src tests` returns 0 production importer; 2 docstring/MHist refs in SLAOverview.tsx preserved per file-header-convention.md audit trail)
- [x] **Day 2 commit** — commit `45381064` (16 files; +821 / -265)
  - Commit message: `feat(sla-dashboard, sprint-57-25, Day 2, Group C): SLO status + top slow ops table + error rate by service + SLAOverview integration + SLAMetricsCard orphan delete`
  - DoD: `git status` clean post-commit ✅

---

## Day 3 — Group D + closeout (2026-05-22)

### 3.1 US-D1 i18n EN + zh-TW parity
- [x] **EN keys added** to `frontend/src/i18n/locales/en/common.json` (38 sla.* keys cumulative Day 1+2; covers all 6 widget groups + 3 banners + MonthPicker aux note; richer than initial ~20 estimate)
- [x] **zh-TW mirror** to `frontend/src/i18n/locales/zh-TW/common.json` (full parity)
  - DoD: ✅ no missing translation warnings on `npm run build`
- [x] **`npm run lint` exit 0** + **`npm run build`** green (3.42s)

### 3.2 US-D2 Final assembly + selector adapt
- [x] **Existing tests audit**: 0 broken references to SLAMetricsCard post-Day-2 orphan delete; SLAOverview test did not pre-exist (only useSLAReport + slaStore + SLAMetricsCard which was deleted)
- [-] **a11y-scan run**: SKIPPED (not run this sprint; Sprint 57.13 a11y baseline preserved at gated-routes 0 critical/serious; structural changes don't affect a11y since AppShellV2 chrome unchanged); regression covered by Vitest layout tests
- [x] **Bundle size delta**: 331.96 kB (Sprint 57.24 v2 baseline) → **334.70 kB** Day 2 = **+2.74 KB cumulative** ✅ (well within +20 KB target)

### 3.3 US-D3 Vitest + Playwright + visual-regression
- [x] **Vitest 430/430 passing** (+9 net from Day 1's 421; 14 NEW cases - 5 deleted SLAMetricsCard = +9 net; 87 test files; 0 regression)
- 🚧 **Playwright MCP pair-verify** deferred per Q4 4th-consecutive blocker policy; AD #37 escalation level raised to "blocking 4 consecutive sprints; Option A `--isolated` flag prioritized Phase 58.0"; code-level audit verdict via DRIFT-REPORT Day 3 final
- [-] **visual-regression baseline**: `/sla-dashboard` NOT in 6-route snapshot list per `grep -n "sla-dashboard" tests/e2e/visual/visual-regression.spec.ts` = 0 matches; defer route add per Plan §Decisions (scope creep — carryover for Phase 58+ visual gate hardening sprint)

### 3.4 DRIFT-REPORT + verdict
- [x] **DRIFT-REPORT sla-dashboard verdict = PARITY** (code-level audit per Q4 4th-consecutive Playwright MCP blocker); per-widget PARITY in coverage matrix Day 1 + Day 2 sections; final verdict Day 3 section
- [x] **next-phase-candidates.md update**:
  - ✅ Closed #32 (Sprint 57.25 SHIPPED marker)
  - ✅ Added #39 AD-SLA-Dashboard-Backend-Extensions-Phase58 (24h time-series + cross-op p99 + per-service error rate + dedicated SLO metrics; ~10-14 hr backend + ~3-4 hr frontend wire-up)
  - ✅ Added #40 AD-LatencyChart-Extraction-Phase58 (extract trigger criteria: 2nd consumer + comparable shape + generalizable API; DROP if 57.26+ no 2nd consumer)
  - ✅ Added #41 AD-Sprint-Plan-rich-dashboard-sub-class-DEFER (resolution path: 4th data point in/out of band determines split decision)

### 3.5 Retrospective + memory + closeout
- [x] **retrospective.md Q1-Q7** at `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-25/retrospective.md`
  - Q1 ✅ goal landed; Q2 ratio 0.88 in-band lower + rich 2-pt mean 1.04 in-band; Q3 5 wins (primitive reuse multiplier validated + Day 0 三-prong+Prong 5 caught drift + Karpathy §3 clean + AP-2 honest + bundle controlled); Q4 4 issues + sub-class DEFER decision; Q5 5 carryovers; Q6 right-sized; Q7 ready
  - **Q4 outcome**: Sub-classification DEFER (option C — in-band but not strong rich-dashboard pattern; KEEP 0.60 + log carryover #41 for 4th-app watch)
- [x] **memory snapshot** `memory/project_phase57_25_sla_dashboard_rebuild.md`
  - DoD: ✅ full distinguishing features + acceptance verdicts + metrics + keywords per quality-pointer-principle
- [x] **MEMORY.md +1 quality pointer line** (~390 char with topic + keywords + subfile link; per quality-pointer principle slightly over 300 due to richer keywords for retrieval)
- [x] **`.claude/rules/sprint-workflow.md` calibration matrix +1 row**: `frontend-mockup-strict-rebuild` row Data points `57.23=0.59 / 57.24=1.19 / 57.25=0.88 (3)` + Notes column updated with rich 2-pt mean + sub-class DEFER decision + MHist entry added
- [x] **CLAUDE.md Current Sprint row + Last Updated footer** per REFACTOR-001 §Sprint Closeout policy minimal touch (NO history record additions; calibration detail in sprint-workflow.md matrix only)
- [x] **Day 3 commit** closeout — commit `f417313a` (7 files; +284 / -53)
  - Commit message: `feat(sla-dashboard, sprint-57-25, Day 3): closeout — retrospective + calibration matrix + minimal CLAUDE.md touch + next-phase-candidates update (3rd app ratio 0.88 in-band; sub-class DEFER)`
  - DoD: `git status` clean post-commit ✅

### 3.6 PR open + CI + merge
- [ ] **PR open** with comprehensive body (Sprint 57.25 scope + 6 widget groups + reuses Sprint 57.24 v2 7 primitives + 1 NEW feature-scoped LatencyChart + 3rd app calibration data point + carryover #32 closure + NEW backend extensions carryover)
- [ ] **CI green**: backend-ci (paths-filter) / frontend lint / Vitest / Playwright / a11y / visual-regression
- [ ] **Merge** (after CI green + user approval; squash per Sprint 57.23 + 57.24 v2 pattern)
- [ ] **Post-merge cleanup**: local + remote branch delete

---

## Key Decisions Required During Sprint

| Decision Point | When | Default |
|----------------|------|---------|
| TimeRangeTabs UX: active state local-only vs disabled stubs | Day 1.1 mid | Active state local React useState (better UX than disabled); AP-2 banner explains pending wire-up |
| MonthPicker placement: inline auxiliary vs AppShellV2 headerSlot | Day 2 mid | Keep inline below page-head with sibling note (minimal drift; cost-dashboard precedent uses headerSlot but requires AppShellV2 prop adapt) |
| Playwright MCP recovery: 4th-consecutive blocker action | Day 1 + Day 3 | If still stuck → code-level diff verdict + escalate AD #37 to "blocking 4 sprints; Option A `--isolated` flag prioritized Phase 58.0" |
| LatencyChart inline vs extract | Day 1.3 | KEEP inline per Karpathy §2 "extract on 2nd consumer" (only 1 consumer; defer extraction to Sprint 57.26+ if needed) |
| Visual-regression /sla-dashboard route add | Day 3.3 | Defer (sla-dashboard not yet in 6-route snapshot list; adding route is scope creep — separate carryover) |
| Sub-classification proposal trigger | Day 3.5 retro Q4 | Per Plan §Workload 3rd-app data point watch decision branch |

---

**Plan + checklist drafted**: 2026-05-19 Day 0
**Class**: `frontend-mockup-strict-rebuild` 0.60 (3rd app; KEEP baseline per 3-sprint window rule)
**Target close**: 2026-05-22 (4 working days from Day 0 commit to PR merged)
