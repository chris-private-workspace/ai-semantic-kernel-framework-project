# Sprint 57.24 v2 — Checklist (AD-Cost-Dashboard-Full-Mockup-Fidelity-Rebuild)

> **Scope Pivot (2026-05-19 Day 1)**: This checklist v2 supersedes v1 retrofit Tier 1 checklist. See `sprint-57-24-plan.md §0 Scope Pivot Notice` + `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-24/progress.md` Day 1 abort entry. v1 checklist items 1.1-3.x for retrofit work are DROPPED (replaced by rebuild scope below); Day 0 三-prong + DRIFT-REPORT skeleton items remain `[x]` completed.

[Link to plan](./sprint-57-24-plan.md)

**Class**: `frontend-mockup-strict-rebuild` 0.60 (2nd application; Sprint 57.23 was 1st)
**Workload**: Bottom-up ~7 hr → calibrated commit ~4.2 hr (multiplier 0.60)
**Day count**: 4 (Day 0 preserved + Day 1 redraft + Group B / Day 2 Group C / Day 3 Group D + closeout)

---

## Day 0 — PRESERVED (commit 5eb7ac84; 2026-05-19)

### 0.1 Plan v1 + checklist v1 + Day 0 skeletons
- [x] **Plan v1 + checklist v1 drafted** (cosmetic retrofit Tier 1 scope; ABORTED Day 1)
  - DoD: 9-section structure mirror Sprint 57.23
  - Commit: `5eb7ac84` `chore(sprint-57-24, Day 0)`
- [x] **Branch creation from main `13663c8c`**
  - DoD: `git branch --show-current` → `feature/sprint-57-24-mockup-fidelity-retrofit-tier-1`
- [x] **DRIFT-REPORT skeleton** (5-page table; repurposed cost-dashboard-only Day 1)
  - DoD: `claudedocs/4-changes/sprint-57-24-mockup-fidelity-retrofit-tier-1/DRIFT-REPORT-RETROFIT-TIER-1.md` exists
- [x] **next-phase-candidates.md +1 entry #31** (AD-Memory-Structural-Rebuild-Phase58 carryover)

### 0.2 Day 0 三-prong (Path + Test Selector)
- [x] **Prong 1 Path verify**: 5 retrofit targets confirmed existence
  - DoD: 4 D-PRE findings catalogued in progress.md Day 0
  - Verify: `Glob("frontend/src/pages/{cost-dashboard,sla-dashboard,verification,admin-tenants,tenant-settings}/**")`
- [x] **Prong 4 Test selector verify**: a11y-scan getByTestId("app-shell") + visual-regression baselines inventory
  - DoD: 2 baselines identified (cost-dashboard + admin-tenants) requiring Day 3 regenerate
- [-] **Prong 2 Content verify deferred to Day 1 per-page inventory** (Day 1 outcome: reality check found STRUCTURAL drift; abort triggered)

---

## Day 1 — Plan/Checklist Redraft + Group B (2026-05-19)

### 1.0 Plan v2 + checklist v2 + abort documentation (Day 1 first half)
- [x] **Day 1 reality check inventory** (production CostOverview + SLAOverview + admin-tenants + tenant-settings + verification inner components vs mockup)
  - DoD: D-STRUCTURAL-1 through D-STRUCTURAL-3 confirmed; D-STRUCTURAL-4 / D-STRUCTURAL-5 verify deferred (sufficient pattern signal)
- [x] **AskUserQuestion Option D — Abort + redraft**
  - Decision: D-3 Pure rebuild start; Sprint 57.24 v2 = `/cost-dashboard` rebuild only
- [x] **progress.md Day 1 entry** (abort rationale + preservation policy + D-STRUCTURAL findings)
- [x] **DRIFT-REPORT Day 1 entry** (preliminary verdicts: 3/5 STRUCTURAL; 2 pending)
- [x] **Plan v2 redraft** (this sprint scope = cost-dashboard rebuild; §0 Scope Pivot Notice preserved)
- [x] **Checklist v2 redraft** (this file)
- [ ] **Day 1 commit** (plan v2 + checklist v2 + Day 1 progress + DRIFT-REPORT update + redraft TaskCreate entries)
  - DoD: `git status` clean post-commit; commit message includes `Sprint 57.24 v2 redraft (D-Step 2.5 abort)`

### 1.1 US-B1 page-head + page-actions
- [ ] **`<PageHead>` component or inline section** rendering title + subtitle + route-pill + admin Badge + page-actions
  - File: `frontend/src/features/cost-dashboard/components/CostOverview.tsx` (or extracted `PageHead.tsx`)
  - DoD: 1440×900 visual matches mockup `page-admin.jsx:202-216`
  - i18n: `cost.pageTitle` / `cost.pageSub` / `cost.adminScope` / `cost.action.byTenant` / `cost.action.csv`
- [ ] **Admin Badge gates on `isPlatformAdmin`** (PLATFORM_ADMIN_ROLES from authStore.roles)
  - DoD: non-admin doesn't see admin Badge
- [ ] **"By tenant" + "CSV" buttons stubs** (onClick toast "Backend filter API pending" for now)
  - DoD: buttons render with icons + label per mockup

### 1.2 US-B2 4-stat sparkline grid
- [ ] **`<Spark>` primitive** at `frontend/src/components/charts/Spark.tsx`
  - Props: `points: number[]`, `tone?: string`, `width?: number=60`, `height?: number=24`
  - DoD: pure SVG polyline; ≤ 30 lines
- [ ] **`<StatCard>` primitive** at `frontend/src/components/charts/StatCard.tsx`
  - Props: `label, value, unit?, delta?, deltaDir?: "up"|"down", spark?: ReactNode`
  - DoD: ≤ 50 lines; Tailwind only (no inline styles)
- [ ] **Charts barrel** `frontend/src/components/charts/index.ts` re-exports Spark + StatCard + AreaChart
- [ ] **4 stat instances in CostOverview**:
  - Spend MTD: `data.total_cost_usd` (real) + Spark fixture
  - Tokens MTD: derive from `data.by_type` aggregation (if available) else fixture
  - Cost / run: fixture (no backend run-count yet)
  - Cache hit rate: fixture (no backend metric yet)
  - DoD: 4 cards render in grid-cols-4 at 1440×900
- [ ] **Vitest spec** `Spark.test.tsx` + `StatCard.test.tsx` (≥ 4 cases each: render / props / spark slot / delta direction)

### 1.3 US-B3 `<AreaChart>` 30d Spend over time
- [ ] **`<AreaChart>` primitive** at `frontend/src/components/charts/AreaChart.tsx`
  - Props: `data: number[]`, `tone?: string`, `height?: number=200`
  - DoD: pure SVG area path with optional fill gradient; ≤ 70 lines
- [ ] **`<CardShell>` primitive** at `frontend/src/components/ui/CardShell.tsx`
  - Props: `title, subtitle?, actions?, bodyClass?, children`
  - DoD: ≤ 40 lines; reused by category / tenant / provider cards Day 2
- [ ] **`<BackendGapBanner>` primitive** at `frontend/src/components/ui/BackendGapBanner.tsx`
  - Props: `reason: string`
  - DoD: warning-tone banner; ≤ 15 lines
- [ ] **Spend over time card in CostOverview** (CardShell + AreaChart + BackendGapBanner)
  - i18n: `cost.spendOverTime` / `cost.spendOverTimeSub` / `cost.banner.areaChart30d`
- [ ] **Fixture** `frontend/src/features/cost-dashboard/__fixtures__/spendOverTime30d.ts` (30-day data array)
- [ ] **Vitest spec** `AreaChart.test.tsx` + `CardShell.test.tsx` (≥ 3 cases each)

### 1.4 Day 1 Playwright MCP retry + commit
- [ ] **Playwright MCP `browser_close` reset attempt** (post Group B implementation)
  - If success: capture 1440×900 mockup + production pair for §1 + §2 + §3 widgets
  - If still stuck: log Day 1 finding + code-level diff substitute
- [ ] **Day 1 commit** with Group B work
  - Commit message: `feat(cost-dashboard, sprint-57-24, Day 1, Group B): page-head + 4-stat sparkline + AreaChart + reusable chart primitives`

---

## Day 2 — Group C (2026-05-20)

### 2.1 US-C1 `<CategoryBarsCard>`
- [ ] **Component** at `frontend/src/features/cost-dashboard/components/CategoryBarsCard.tsx`
  - Props: `byType: CostSummaryResponse["by_type"]`
  - DoD: 6 category bars (Inference input/output / Thinking tokens / Tool runs / Embeddings / Sandbox compute); real `data.by_type` for available categories + fixture rows for missing
  - i18n: `cost.category.inferenceInput` / `cost.category.inferenceOutput` / etc (6 keys)
- [ ] **`<BarTrack>` inline primitive in CategoryBarsCard** (or extract to charts if needed)
  - DoD: percentage bar with per-row color token
- [ ] **CostBreakdownTable decision**: embed body OR keep as separate detail row
  - DoD: documented in progress.md Day 2
- [ ] **Vitest spec** `CategoryBarsCard.test.tsx` (≥ 3 cases: rendering / real data / fixture fallback)
- [ ] **Prong 2 content verify on `data.by_type` shape** before commit (per Risk R3 mitigation)

### 2.2 US-C2 `<TenantTopTable>` admin-scope
- [ ] **Component** at `frontend/src/features/cost-dashboard/components/TenantTopTable.tsx`
  - DoD: top-8 tenant rows with avatar + slug + Plan Badge + Tokens + Cost + Quota used % + quota bar
  - Fixture: `__fixtures__/tenantTop8.ts` (8 tenant rows matching mockup data)
- [ ] **Admin scope gate via parent `isPlatformAdmin` check in CostOverview** (component itself doesn't need to know)
  - DoD: non-admin doesn't see component
- [ ] **`<BackendGapBanner reason="Backend cross-tenant API pending Phase 58+ AD-Cost-Dashboard-Backend-Extensions" />`**
- [ ] **i18n**: `cost.tenant.title` / `cost.tenant.col.*` (5 columns) / `cost.tenant.anomaly` / `cost.banner.crossTenant`
- [ ] **Vitest spec** `TenantTopTable.test.tsx` (≥ 4 cases: rendering / anomaly Badge / over-quota color / banner)

### 2.3 US-C3 `<ProviderMixCard>` admin-scope
- [ ] **Component** at `frontend/src/features/cost-dashboard/components/ProviderMixCard.tsx`
  - DoD: 4-provider rows (provider-A/B/C/self-hosted) × Tokens + Cost + Pct + bar
  - Fixture: `__fixtures__/providerMix.ts` (4 provider rows matching mockup)
- [ ] **LLM-neutrality redaction notice** ("Provider identity is redacted in operator views to enforce LLM-neutrality. Switching providers does not change tool semantics.") per mockup
- [ ] **`<BackendGapBanner reason="Backend cross-provider API pending Phase 58+ AD-Cost-Dashboard-Backend-Extensions" />`**
- [ ] **i18n**: `cost.provider.title` / `cost.provider.banner` / `cost.provider.llmNeutralityNotice` / `cost.banner.crossProvider`
- [ ] **Vitest spec** `ProviderMixCard.test.tsx` (≥ 3 cases: rendering / LLM-neutrality notice / banner)

### 2.4 CostOverview integration + Day 2 commit
- [ ] **CostOverview.tsx assembled** with all 6 widget groups in mockup-faithful grid (`grid-cols-4` 4-stat row + `grid-cols-2` main grids)
  - DoD: matches mockup `page-admin.jsx:225-318` 1:1 at 1440×900
- [ ] **Existing CostOverview.test.tsx adapted** for new layout selectors (preserve behavioral assertions: real data flows / admin scope gate)
- [ ] **Day 2 commit**
  - Commit message: `feat(cost-dashboard, sprint-57-24, Day 2, Group C): category bars + tenant top-8 + provider mix + admin scope gate`

---

## Day 3 — Group D + closeout (2026-05-21 or 22)

### 3.1 US-D1 i18n EN + zh-TW parity
- [ ] **EN keys added** to `frontend/src/i18n/locales/en/common.json` (~25 keys covering all 6 widget groups + banners)
- [ ] **zh-TW mirror** to `frontend/src/i18n/locales/zh-TW/common.json`
  - DoD: no missing translation warnings on `npm run build`
- [ ] **Verify**: `npm run lint` + render checks both locales

### 3.2 US-D2 Final assembly + selector adapt
- [ ] **Existing tests audit**: any spec depending on old CostOverview shape needs selector update
  - DoD: all referencing tests pass post-rewrite
- [ ] **a11y-scan**: confirm `/cost-dashboard` passes (getByTestId("app-shell") + new widgets WCAG compliant)
  - Color contrast checks on widget tone colors (Sprint 57.18 tokens)
- [ ] **Bundle size delta check**: `npm run build` + compare KB delta; target ≤ +30 KB

### 3.3 US-D3 Vitest + Playwright + visual-regression
- [ ] **Vitest 369+15 passing**
  - DoD: `npm run test` exits 0; new spec count ≥ 15
- [ ] **Playwright e2e cost-dashboard happy-path** passes (selector adapt for layout rewrite)
- [ ] **Playwright MCP pair-verify** (Day 3 attempt; if browser still stuck → code-level diff substitute + AD-Playwright-MCP-Recovery-Phase58 carryover)
  - Save screenshots to `claudedocs/4-changes/sprint-57-24-mockup-fidelity-retrofit-tier-1/screenshots/mockup/cost-dashboard.png` + `production/cost-dashboard.png`
- [ ] **visual-regression baseline regenerated** via workflow_dispatch + cherry-pick from `chore/visual-baselines-*` PR (parallel Sprint 57.23 PR #156 recovery pattern)

### 3.4 DRIFT-REPORT + verdict
- [ ] **DRIFT-REPORT cost-dashboard verdict = PARITY** (or COSMETIC with documented residual drift if Playwright unavailable)
- [ ] **Sprint 57.25-57.28 carryover**: 4 remaining pages (sla / tenants / verification / tenant-settings) catalog in next-phase-candidates.md as `AD-Mockup-Fidelity-Rebuild-Page-*-Phase58` (4 entries)

### 3.5 Retrospective + memory + closeout
- [ ] **retrospective.md Q1-Q7** at `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-24/retrospective.md`
  - Q1: Did sprint goal land?
  - Q2: Workload calibration ratio (actual / committed); class `frontend-mockup-strict-rebuild` 0.60 2nd app data point
  - Q3: What went well?
  - Q4: What didn't go well (Day 1 abort lesson + Playwright MCP recovery + class calibration)?
  - Q5: Carryover ADs
  - Q6: Reusable chart primitives — were extracts right-sized?
  - Q7: Sprint 57.25+ readiness check
- [ ] **memory snapshot** `memory/project_phase57_24_cost_dashboard_rebuild.md` (Sprint scope + key decisions + Day 1 abort + V2 rebuild + reusable charts + 4 carryover pages)
- [ ] **MEMORY.md +1 quality pointer line** (per REFACTOR-001 §MEMORY.md Update Policy)
- [ ] **`.claude/rules/sprint-workflow.md` calibration matrix +1 row**:
  - `frontend-mockup-strict-rebuild` 2nd application; data point Sprint 57.24=X.XX
  - 3-sprint window status: Sprint 57.23=0.59 + 57.24=X.XX (2 of 3); if both below band → AD-Sprint-Plan propose 0.60 → 0.40-0.45 lift parallel Sprint 57.16 mechanical-class rule
- [ ] **CLAUDE.md Current Sprint row + Last Updated footer** (per REFACTOR-001 §CLAUDE.md Update Policy minimal touch — NO new history record additions)
- [ ] **next-phase-candidates.md update**: +4 entries for Sprint 57.25-57.28 carryover pages + 1 entry for AD-Cost-Dashboard-Backend-Extensions-Phase58
- [ ] **Day 3 commit** closeout
  - Commit message: `chore(sprint-57-24, Day 3, closeout): retrospective + memory + calibration matrix + CLAUDE.md sync`

### 3.6 PR open + CI + merge
- [ ] **PR open** with comprehensive body (Sprint 57.24 v2 redraft context + 6 widget groups + reusable charts + carryover)
- [ ] **CI green**: backend-ci (paths-filter) / frontend lint / Vitest / Playwright / a11y / visual-regression
- [ ] **Merge** (after CI green + user approval)
- [ ] **Post-merge cleanup**: local + remote branch delete

---

## Key Decisions Required During Sprint

| Decision Point | When | Default |
|----------------|------|---------|
| CostBreakdownTable embed vs keep | Day 2.1 mid | Embed into CategoryBarsCard body for tighter mockup parity |
| Playwright MCP recovery | Day 1 + Day 3 | If still stuck Day 3 → AD-Playwright-MCP-Recovery-Phase58 + code-level diff verdict |
| `data.by_type` category mapping | Day 2.1 start (Prong 2 content verify) | Real data where available + fixture for missing categories |
| Reusable chart primitives over-engineering | Day 1.2-1.3 | Keep mockup-mirror minimal; defer abstractions to 57.25+ actual reuse demand |

---

**Plan + checklist v2 redrafted**: 2026-05-19 Day 1 (post-abort)
**Class**: `frontend-mockup-strict-rebuild` 0.60 (2nd app; KEEP baseline per 3-sprint window rule)
**Target close**: 2026-05-21 or 22 (3 working days from Day 1 redraft complete)
