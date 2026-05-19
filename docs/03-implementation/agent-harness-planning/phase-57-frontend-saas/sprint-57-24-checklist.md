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
- [x] **`<PageHead>` component extracted to `components/ui/PageHead.tsx`** (40 lines reusable; 5 future consumers planned 57.25-57.28)
  - File: `frontend/src/components/ui/PageHead.tsx` (NEW)
  - DoD: 1440×900 visual matches mockup `page-admin.jsx:202-216` (PageHead title + subtitle + routePath inline pill + badges slot + actions slot)
  - i18n: `cost.pageTitle` / `cost.pageSub` / `cost.adminScope` / `cost.action.byTenant` / `cost.action.csv` / `cost.action.filterPending` / `cost.action.csvPending` ✅ EN + zh-TW parity
  - Vitest: `tests/unit/components/PageHead.test.tsx` 5/5 passed
- [x] **Admin Badge gates on `isPlatformAdmin`** (PLATFORM_ADMIN_ROLES = ["admin", "platform_admin"] from authStore.roles)
  - DoD: non-admin doesn't see admin Badge (tested via `data-testid="cost-admin-scope-badge"`)
- [x] **"By tenant" + "CSV" buttons stubs** (disabled + title tooltip pending backend per AP-2)
  - DoD: buttons render with disabled state + tooltip via title attribute ("Filter API pending Phase 58+" / "CSV export pending Phase 58+")

### 1.2 US-B2 4-stat sparkline grid
- [x] **`<Spark>` primitive** at `frontend/src/components/charts/Spark.tsx` (~25 lines pure SVG polyline; default width=90 height=26 matching mockup ui.jsx:115-121)
  - Props: `points: number[]`, `tone?: string=hsl(var(--primary))`, `width?: number=90`, `height?: number=26`
  - DoD: ✅ pure SVG single path with min/max normalization; empty points returns null
- [x] **`<StatCard>` primitive** at `frontend/src/components/charts/StatCard.tsx` (~55 lines mockup-direct port of ui.jsx:99-113 + styles.css:489-504)
  - Props: `label, value, unit?, delta?, deltaDir?: "up"|"down", spark?: ReactNode`
  - DoD: ✅ Tailwind translation of mockup .stat styles (rounded-[10px] / bg-bg-1 / px-4 py-3.5 / text-2xl font-semibold tracking-[-0.02em] tabular-nums); deltaDir semantic = "up=positive(success+ArrowUp) / down=negative(danger+ArrowDown)"; spark absolute-positioned bottom-right opacity-60 per mockup
- [x] **Charts barrel** `frontend/src/components/charts/index.ts` exports Spark + StatCard (AreaChart added Day 1.3)
- [x] **4 stat instances in CostOverview** in grid-cols-4:
  - Spend MTD: real `data.total_cost_usd` value (`$X,XXX` toLocaleString) + Spark fixture (tone memory)
  - Tokens MTD: fixture value `14.2 M` + Spark fixture (default tone)
  - Cost / run: fixture `$0.052` + Spark fixture (tone warning)
  - Cache hit rate: fixture `38 %` + Spark fixture (tone success)
  - DoD: ✅ 4 cards render in `grid grid-cols-4 gap-3` with `data-testid="cost-stat-grid"` anchor for Day 3 Playwright
- [x] **Vitest specs**: `Spark.test.tsx` (5 cases) + `StatCard.test.tsx` (6 cases) all pass; covers render / tone / width-height defaults / empty-points edge / delta tone semantic / spark slot / delta omitted

### 1.3 US-B3 `<AreaChart>` 30d Spend over time
- [x] **`<AreaChart>` primitive** at `frontend/src/components/charts/AreaChart.tsx` (~85 lines mockup-direct port of page-admin.jsx:5-29)
  - Props: `data: number[]`, `tone?: string=hsl(var(--primary))`, `height?: number=180`
  - DoD: ✅ pure SVG; gradient fill + line stroke + 3 horizontal grid lines (25/50/75% positions); viewBox + preserveAspectRatio="none" + className="w-full" + SVG `height` attribute (no inline style per STYLE.md §1); empty data returns null
- [x] **`<CardShell>` primitive** at `frontend/src/components/ui/CardShell.tsx` (~50 lines mockup-direct port of OverviewPage inline Card pattern)
  - Props: `title?, subtitle?, actions?, bodyClass?, children`
  - DoD: ✅ Tailwind translation of mockup Card shape (rounded-[12px] / border / bg-bg-1 / px-4 py-3 header / p-4 body default); header omitted when neither title nor actions present; reused by Day 2 widget cards
- [x] **`<BackendGapBanner>` primitive** at `frontend/src/components/ui/BackendGapBanner.tsx` (~15 lines)
  - Props: `reason: string`
  - DoD: ✅ role="note" + warning-tone styling (border-warning/40 / bg-warning/5 / text-warning) + ⚠️ icon; data-testid for test
- [x] **Spend over time card in CostOverview** assembled (CardShell + AreaChart + BackendGapBanner)
  - i18n keys: `cost.spendOverTime.{title, subtitle}` + `cost.banner.areaChart30d` ✅ EN + zh-TW parity
- [x] **Fixture** `frontend/src/features/cost-dashboard/__fixtures__/spendOverTime30d.ts` (30-day data array; mirrors mockup page-admin.jsx:227 demo values $80-$284)
- [x] **Vitest specs**: `AreaChart.test.tsx` (5 cases) + `CardShell.test.tsx` (5 CardShell + 2 BackendGapBanner cases); covers svg+paths / tone / gradient / height attribute / empty edge / title-subtitle / actions slot / body class / banner role + warning tone

### 1.4 Day 1 Playwright MCP retry + commit
- [ ] **Playwright MCP `browser_close` reset attempt** (post Group B implementation)
  - If success: capture 1440×900 mockup + production pair for §1 + §2 + §3 widgets
  - If still stuck: log Day 1 finding + code-level diff substitute
- [ ] **Day 1 commit** with Group B work
  - Commit message: `feat(cost-dashboard, sprint-57-24, Day 1, Group B): page-head + 4-stat sparkline + AreaChart + reusable chart primitives`

---

## Day 2 — Group C (2026-05-20)

### 2.1 US-C1 `<CategoryBarsCard>`
- [x] **Component** at `frontend/src/features/cost-dashboard/components/CategoryBarsCard.tsx` (~55 lines mockup-direct port of page-admin.jsx:230-252)
  - Props: NONE — consumes inline fixture (R3 mitigation: mockup 6-category taxonomy ≠ backend by_type 2-level shape; AD-Cost-Backend-Category-Taxonomy-Phase58 carryover)
  - DoD: ✅ 6 fixture rows (Inference input/output / Thinking tokens / Tool runs / Embeddings / Sandbox compute) × dot + name + $value + BarTrack; per-row tone color (thinking/primary/info/tool/memory/warning); BackendGapBanner declaring taxonomy gap
  - i18n: ✅ `cost.category.{title, subtitle, inferenceInput, inferenceOutput, thinkingTokens, toolRuns, embeddings, sandboxCompute}` + `cost.banner.categoryTaxonomy` × EN + zh-TW
- [x] **`<BarTrack>` primitive extracted** to `frontend/src/components/charts/BarTrack.tsx` (~40 lines) — NOT inline; shared with Day 2.2 + 2.3 + Sprint 57.25+ widgets per Karpathy §2 "extract on 2nd consumer" (3 confirmed consumers + ≥3 future)
  - Props: `pct, tone?, height?`; clamps pct to [0,100]; documented STYLE.md §3 escape hatch for dynamic width % + tone color (no Tailwind utility expresses runtime values cleanly)
- [x] **CostBreakdownTable decision**: KEEP as separate detail row below the new grid (raw backend `by_type` 2-level dict view; serves different audience than mockup-summary CategoryBarsCard)
  - Rationale documented inline in CostOverview comments + Day 2 progress entry
- [x] **Vitest spec** `CategoryBarsCard.test.tsx` (4 cases: 6 BarTracks render / title-subtitle / BackendGapBanner present / dollar values toLocaleString format)
- [x] **Prong 2 content verify on `data.by_type` shape**: COMPLETED — 2-level dict (cost_type → sub_type → AggregatedSlice); NO clean mapping to mockup 6-category taxonomy → fully-fixture path chosen per CLAUDE.md §Mockup-Fidelity backend-gap rule + AP-2 honesty banner

### 2.2 US-C2 `<TenantTopTable>` admin-scope
- [x] **Component** at `frontend/src/features/cost-dashboard/components/TenantTopTable.tsx` (~145 lines mockup-direct port of page-admin.jsx:258-293)
  - DoD: ✅ top-8 rows × avatar (rounded primary/15 + first-letter cap) + mono slug + optional anomaly Badge (danger tone + dot) + Plan Badge (shadcn outline variant) + Tokens (mono tnum subtle right) + Cost ($X mono tnum right) + Quota % (color-coded by pct threshold) + quota BarTrack (color-coded tone)
  - Fixture: ✅ `__fixtures__/tenantTop8.ts` (8 rows mirror mockup page-admin.jsx:263-270 data; 1 row alert=true `tenant_3kp9`)
  - Quota color logic (mockup page-admin.jsx:282-287 mirror): pct>100→danger / pct>80→warning / else→muted+success bar
- [x] **Admin scope gate via parent `isPlatformAdmin` check in CostOverview** — component itself is admin-agnostic for test reuse; CostOverview conditionally mounts `{isPlatformAdmin && <TenantTopTable />}`
- [x] **`<BackendGapBanner reason={t("cost.banner.crossTenant")} />`** rendered below table; AP-2 honesty marker
- [x] **i18n**: `cost.tenant.{title, subtitle, anomaly, col.tenant, col.plan, col.tokens, col.cost, col.quotaUsed}` + `cost.banner.crossTenant` × EN + zh-TW (9 keys × 2 locales)
- [x] **Vitest spec** `TenantTopTable.test.tsx` (6 cases: 8 rows render / title-subtitle / 1 anomaly Badge (alert=true) / pct>100 danger text class / 80<pct≤100 warning text class / cross-tenant banner present)

### 2.3 US-C3 `<ProviderMixCard>` admin-scope
- [x] **Component** at `frontend/src/features/cost-dashboard/components/ProviderMixCard.tsx` (~80 lines mockup-direct port of page-admin.jsx:295-317)
  - DoD: ✅ 4 fixture rows × dot (toneClass) + mono label + $cost·tokens + BarTrack (color tone); admin-only subtitle with Shield icon (lucide-react); separator + LLM-neutrality notice + BackendGapBanner
  - Fixture: ✅ `__fixtures__/providerMix.ts` (4 rows: provider-A/B/C/self-hosted; tones primary/thinking/tool/memory)
- [x] **LLM-neutrality redaction notice** mockup-faithful copy: "Provider identity is redacted in operator views to enforce LLM-neutrality. Switching providers does not change tool semantics." — `data-testid="provider-llm-neutrality-notice"` for test
- [x] **`<BackendGapBanner reason={t("cost.banner.crossProvider")} />`** AP-2 honesty marker; distinct from LLM-neutrality notice
- [x] **i18n**: `cost.provider.{title, subtitle, llmNeutralityNotice}` + `cost.banner.crossProvider` × EN + zh-TW (4 keys × 2 locales)
- [x] **Vitest spec** `ProviderMixCard.test.tsx` (5 cases: 4 BarTracks render / 4 provider labels / title + admin-only subtitle / LLM-neutrality notice / cross-provider banner)

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
