# Sprint 57.24 — Progress

**Sprint**: AD-Mockup-Existing-Pages-Retrofit Tier 1 (6-Page Cosmetic Retrofit)
**Branch**: `feature/sprint-57-24-mockup-fidelity-retrofit-tier-1`
**Calibration**: `mockup-fidelity-retrofit` 0.55 NEW class 1st application
**Bottom-up**: ~10 hr → **Calibrated commit**: ~5.5 hr (4-day solo-dev sprint)

---

## Day 0 — 2026-05-19

### Today's Plan

1. Plan + checklist drafted (mirror Sprint 57.23 structure)
2. Branch creation from main `13663c8c`
3. Day 0 三-prong (Path + Content + Schema + Test Selector prongs)
4. Playwright MCP browser_close attempt (R3 mitigation)
5. If Playwright available: 12 baseline captures (6 mockup + 6 production pre-retrofit)
6. Catalog D-PRE drift findings

### Drift findings (D-PRE)

**D-PRE-1**: `/verification/recent` does NOT have a separate page file in production. `frontend/src/pages/verification/index.tsx` is the sole file; the `/verification/recent` route is handled via client-side redirect from within index.tsx (per Sprint 57.22 Unit 11 note "Redirected /verification → /verification/recent"). **Impact**: Sprint 57.24 scope effective page count = **5**, not 6 (collapse verification + verification/recent into 1 retrofit target). Bottom-up estimate adjustment: ~10 hr → ~9 hr; calibrated commit ~5.5 hr → ~5 hr.

**D-PRE-2**: Mockup files are domain-grouped, NOT page-named. Initial plan assumed `page-cost.jsx` / `page-sla.jsx` / `page-verification.jsx` / `page-tenants.jsx` / `page-tenant-settings.jsx` — none exist. Corrected references:
- `/cost-dashboard` → `reference/design-mockups/page-admin.jsx:200-321` (CostPage)
- `/sla-dashboard` → `reference/design-mockups/page-admin.jsx:31-199` (SlaPage)
- `/verification` (covers /verification/recent) → `reference/design-mockups/page-extras.jsx:817-927` (VerificationPage)
- `/admin/tenants` list → `reference/design-mockups/page-admin.jsx:322-410` (AdminTenants section)
- `/admin/tenants/settings` → `reference/design-mockups/page-admin.jsx:411+` (TenantSettings)

**D-PRE-3 (R1 mitigation confirm)**: Mockup `page-extras.jsx:928` has comment `// /feature-flags (lifted out of /tenant-settings)`. This suggests mockup intent **separates** the feature-flags tab out of tenant-settings into a standalone `/feature-flags` route. This is Sprint 57.22 Unit 31's architectural finding manifested concretely. **R1 escalation**:
- If retrofit only cosmetic (matching mockup tab visuals within current 6-tab structure) → Sprint 57.24 retrofit-only acceptable
- If structural (need to lift feature-flags tab out + create new `/feature-flags` route) → escalate to NEW AD-Tenant-Settings-Feature-Flags-Lift-Phase58 + Sprint 57.24 US-D2 cosmetic-only

**D-PRE-4 (path naming)**: Production route is `/admin/tenants/settings` (plural with slash); mockup uses `/admin/tenant-settings` (singular with hyphen) per `page-admin.jsx:411` comment. Naming-level drift only; route paths preserved as-is per V2 surgical-change discipline. No action.

### Prong 4 (Test selector verify) summary

- ✅ a11y-scan (`tests/e2e/a11y/a11y-scan.spec.ts:127`) uses `getByTestId("app-shell")` anchor for all 5 gated retrofit pages (L51-56 GATED_ROUTES array). **No selector drift risk** for Sprint 57.24 cosmetic retrofit (unless we remove the AppShellV2 `data-testid="app-shell"` anchor — which we won't, it's preserved).
- ⚠️ visual-regression (`tests/e2e/visual/visual-regression.spec.ts`) has 2 baselines for retrofit pages: `cost-dashboard.png` (L107-116) + `admin-tenants.png` (L133-137). **Expected drift** on retrofit; Day 3 handles via Sprint 57.14 visual-baseline workflow_dispatch + cherry-pick (parallel to Sprint 57.23 PR #156 recovery pattern).
- ℹ️ visual-regression does NOT cover `/sla-dashboard` / `/tenant-settings` / `/verification` — only 2 of 5 retrofit pages have visual baselines.
- ℹ️ Unit Vitest tests for sla-dashboard / verification / admin-tenants / tenant-settings are component-level (`SLAMetricsCard.test.tsx` / `CorrectionTraceView.test.tsx` / `adminTenantsStore.test.ts` / `tenantSettingsStore.test.ts` etc) — **no h1 anchor dependencies** that would break on cosmetic class swaps.

### Prong 2 (Content verify) — deferred to Day 1 per-page inventory

Per-page Tailwind class state inventory IS the Day 1 retrofit work itself (not pre-Day-1 verify). For Sprint 57.23 Prong 2 was about "claimed-but-unwired entry points" — that pattern doesn't apply to cosmetic retrofit. Catalog per-page class drift findings as they emerge during Day 1-2 retrofit task execution.

### Day 0 Actual Hours

- Plan + checklist + progress + DRIFT-REPORT skeleton + AD-Memory-Structural-Rebuild-Phase58 added: ~45 min
- Prong 1 (Path verify): ~15 min; 4 D-PRE findings catalogued
- Prong 4 (Test selector verify): ~15 min; no drift risk identified
- **Day 0 total ~1.25 hr** (vs informal target ~2 hr; ~38% under)

### R1 Mitigation Status

D-PRE-3 confirmed Sprint 57.22 Unit 31 architectural finding manifests concretely as `/feature-flags (lifted out of /tenant-settings)` per mockup `page-extras.jsx:928`. Day 1 R1 escalation check: read mockup `page-admin.jsx:411+` (TenantSettings) vs production `frontend/src/pages/tenant-settings/index.tsx` to determine:
- (a) feature-flags tab still IN production within 6-tab structure → retrofit-only suffices for Sprint 57.24
- (b) Sprint 57.24 must lift feature-flags tab OUT to new route → escalate to AD-Tenant-Settings-Feature-Flags-Lift-Phase58 + Sprint 57.24 US-D2 cosmetic-only

Default assumption: (a) until proven otherwise during Day 1 R1 check.

### Playwright MCP baseline captures

🚧 **Deferred to Day 1+** due to prior session browser-stuck state lingering (per Sprint 57.23 Day 4 R3 evidence). First Day 1 action: attempt `browser_close` to reset; if available, retroactively capture baselines.

---

## Day 1 — 2026-05-19 — 🛑 SPRINT ABORTED per §Step 2.5

### What happened

Day 1 first action: `browser_close` attempt → still browser-stuck (prior session lingering, same as Sprint 57.23 Day 4 evidence). Pivoted to R3 contingency (code-level audit + Tailwind iterate).

Per `.claude/rules/sprint-workflow.md` §Step 2.5 Day-0 verify methodology, opened Day 1 with code-level inventory of all 5 retrofit targets' inner components vs mockup widget structure. Finding emerged on first 2 pages (cost-dashboard + sla-dashboard) that production state is **structurally far thinner** than mockup, not cosmetic-class drift.

### D-STRUCTURAL findings (Day 1 reality check)

**D-STRUCTURAL-1**: `/cost-dashboard` production (`CostOverview.tsx` 68 lines) renders only `<p>` description + total cost text + `<CostBreakdownTable>` (5-col cost_type × sub_type rows). Mockup `CostPage` (page-admin.jsx:200-321, 121 lines) requires: page-head with route-pill + admin Badge + 4-stat grid with sparklines (Spend MTD / Tokens MTD / Cost-run / Cache hit) + AreaChart "Spend over time" 30d + "Spend by category" 6-row bars + "Spend by tenant" top-8 table + "Provider mix" 4-provider card with admin scope notice. **5/6 mockup widget groups are missing** — not Tailwind class drift, but structural widget absence. Tier 1 cosmetic-feasible premise invalid.

**D-STRUCTURAL-2**: `/sla-dashboard` production (`SLAOverview.tsx` 133 lines) has `MonthPicker` + violations badge + 6-card grid (Availability / API p99 / Loop simple/medium/complex / HITL queue notif). Mockup `SlaPage` (page-admin.jsx:31-199, 169 lines) requires: time-range btn-group (1h/24h/7d/30d) + Refresh + Export buttons + 4-stat grid with sparklines + LatencyChart 24h SVG (3-series p50/p95/p99) + 5-row SLO status card + Top slow operations table (6 ops × p50/p95/p99/calls) + Error rate by service card (6 services). **5/6 mockup widget groups missing**.

**D-STRUCTURAL-3** (already known per Sprint 57.22 audit Unit 31): `/tenant-settings` production (`TenantSettingsView.tsx`) has 6-tab structure; mockup `TenantSettings` (page-admin.jsx:411+) plus mockup comment in `page-extras.jsx:928` indicates `/feature-flags` lifted OUT of `/tenant-settings` into standalone route — architectural finding requires lift refactor, not cosmetic.

**D-STRUCTURAL-4 (verify deferred)**: `/admin/tenants` list production (`AdminTenantsPage.tsx`) has `TenantListFilters + TenantListTable + TenantListPagination` (role-gated). Mockup `AdminTenants` (page-admin.jsx:322-410, 88 lines) inner component verify pending.

**D-STRUCTURAL-5 (verify deferred)**: `/verification` production has 2-tab navigation + `VerificationList + CorrectionTraceView`. Mockup `VerificationPage` (page-extras.jsx:817-927, 110 lines) inner component verify pending.

### Pattern recognition

All inspected production pages exhibit the SAME pattern: thin real-data MVP shipping core backend integration + 1-3 functional widgets, vs mockup which is a "rich widget showcase" with 6-8 widget groups per page (KPI sparklines + multi-series charts + 多 table + side-cards). This is NOT Tailwind padding/radius/shadow drift; it's structural widget absence.

Sprint 57.22 audit (`AUDIT-REPORT.md`) had already classified Unit 1 (cost-dashboard) + Unit 2 (sla-dashboard) + Unit 31 (tenant-settings) as **P0 requiring full mockup-fidelity rebuild** in Phase 57.23+ epic. Sprint 57.24 plan's Tier 1 selection of these pages as "cosmetic retrofit" was an oversight against audit findings.

### Abort decision

Per `.claude/rules/sprint-workflow.md` §Step 2.5:
> **Findings shift scope by > 50% → abort sprint; redraft plan with reality baseline**

Day 1 finding shifts effective scope by **≈100%** (Tier 1 cosmetic-feasible premise → invalid for all 5 pages). User selected Option D (Abort + redraft) per Day 1 AskUserQuestion.

### Preservation policy

Per CLAUDE.md "Never Delete Docs" + V2 discipline:
- ✅ Day 0 + Day 1 progress.md entries preserved as historical audit trail
- ✅ DRIFT-REPORT skeleton updated with D-STRUCTURAL-1/2/3 confirmed findings
- ✅ Day 0 commit `5eb7ac84` preserved (plan + checklist + 三-prong + AD-Memory-Structural-Rebuild-Phase58 carryover)
- ⏳ Plan + checklist redraft pending user direction (audit-only / split-audit-first / pure-rebuild)
- ⏳ Class calibration pivot pending: `mockup-fidelity-retrofit` 0.55 → likely `frontend-mockup-fidelity-audit-tier-1` 0.85 (parallel Sprint 57.22 audit class) OR `frontend-mockup-strict-rebuild` 0.60 (parallel Sprint 57.23 rebuild class)

### Day 1 hours (Group A — abort + redraft)

- Production inventory (5 pages × inner components read): ~30 min
- AskUserQuestion + abort decision: ~10 min
- Documentation (progress entry + DRIFT-REPORT update + TaskUpdate): ~15 min
- Plan v2 + checklist v2 redraft (mirror Sprint 57.23 structure): ~45 min
- Day 1.0 commit `308ca93b` (atomic redraft commit): ~5 min
- **Day 1 abort + redraft subtotal ~1.75 hr**

### Day 1.1 US-B1 page-head + page-actions (Group B start)

**Output**:
- NEW `frontend/src/components/ui/PageHead.tsx` (40 lines reusable primitive; 5 future consumer paths planned 57.25-57.28)
- NEW `frontend/tests/unit/components/PageHead.test.tsx` (5 cases all pass: title+subtitle / routePath pill / badges slot / actions slot / actions omitted edge case)
- REWRITE-TOP `frontend/src/features/cost-dashboard/components/CostOverview.tsx` (added PageHead + admin scope gate + page-actions row; preserved Total cost + CostBreakdownTable below temporarily)
- UPDATE `frontend/src/i18n/locales/en/common.json` + `zh-TW/common.json` (+ cost.* namespace 7 keys × 2 locales)
- UPDATE `frontend/tests/unit/cost-dashboard/migrate.test.tsx` (selector adapt for new PageHead subtitle; preserve assertion intent "no inline style")

**Verification**:
- Vitest 374/374 全綠 (76 files; +5 from Sprint 57.23 close baseline 369)
- `npm run lint` exit 0 (0 errors / 0 warnings)
- `npm run build` 3.79s; main bundle 329.57 kB (+0.46 kB from 329.11 baseline — PageHead + i18n keys)

**DoD verified**:
- ✅ PageHead matches mockup `page-admin.jsx:202-216` shape (title + subtitle + routePath + admin badge + 2 buttons)
- ✅ Admin Badge gates on `isPlatformAdmin` (PLATFORM_ADMIN_ROLES `admin|platform_admin`)
- ✅ "By tenant" + "CSV" buttons render disabled + title tooltip per AP-2 honesty
- ✅ i18n EN + zh-TW parity (no missing translation warnings on build)
- ✅ data-testid anchors installed for Day 3 Playwright pair-verify

**Day 1.1 hours ~50 min**:
- PageHead component + spec: ~20 min
- CostOverview integration + i18n keys: ~15 min
- Test selector adapt + verify Vitest/lint/build: ~15 min

**Day 1 cumulative ~2.6 hr** (vs ~4.2 hr commit budget = ~62% consumed for ~25% Group B progress; on track)

### Day 1.2 US-B2 4-stat sparkline grid (Group B continued)

**Output**:
- NEW `frontend/src/components/charts/Spark.tsx` (~25 lines pure SVG polyline; mockup-direct port of ui.jsx:115-121)
- NEW `frontend/src/components/charts/StatCard.tsx` (~55 lines mockup-direct port of ui.jsx:99-113 + styles.css:489-504)
- NEW `frontend/src/components/charts/index.ts` (barrel — Spark + StatCard + types exports)
- NEW `frontend/tests/unit/components/Spark.test.tsx` (5 cases: render / tone / defaults / custom-dims / empty-edge)
- NEW `frontend/tests/unit/components/StatCard.test.tsx` (6 cases: label-value / unit / delta-up-success / delta-down-danger / spark-slot / omitted-delta)
- UPDATE `frontend/src/features/cost-dashboard/components/CostOverview.tsx` (add §2 4-stat sparkline grid below PageHead; Spend MTD value derives real `data.total_cost_usd`; other 3 stats fixture + sparkline fixtures inline `STAT_FIXTURES` const)
- UPDATE `frontend/src/i18n/locales/{en,zh-TW}/common.json` (+ cost.stat.{spendMtd, tokensMtd, costPerRun, cacheHit} × 2 locales = 8 new keys)

**Verification**:
- Vitest 385/385 全綠 (78 files; +11 from Day 1.1 baseline 374)
- `npm run lint` exit 0 (0 errors / 0 warnings)
- `npm run build` 3.60s; main bundle 329.76 kB (+0.19 from 329.57 Day 1.1 baseline)

**DoD verified**:
- ✅ Spark default width=90 height=26 matches mockup ui.jsx canonical
- ✅ Spark pure SVG (no chart lib); single path with min/max normalization
- ✅ StatCard Tailwind translation of mockup .stat styles (bg-bg-1 / border / px-4 py-3.5 / rounded-[10px])
- ✅ StatCard deltaDir semantic: "up"=success+ArrowUp / "down"=danger+ArrowDown (per mockup .stat-delta.up/.down CSS)
- ✅ StatCard spark slot absolute-positioned bottom-right opacity-60 per mockup .stat-spark CSS
- ✅ 4 stat instances in grid-cols-4 with data-testid anchor + tone colors matching mockup (Spend MTD memory / Tokens default / Cost-run warning / Cache hit success)
- ✅ Spend MTD value swaps to real data.total_cost_usd via toLocaleString when data loaded; "$—" placeholder otherwise
- ✅ i18n EN + zh-TW parity (cost.stat.*; no missing translation warnings on build)

**Day 1.2 hours ~40 min**:
- Spark + StatCard primitives + specs: ~20 min
- CostOverview integration + i18n + fixtures: ~10 min
- Verify Vitest/lint/build: ~10 min

**Day 1 cumulative ~3.3 hr** (vs ~4.2 hr commit budget = ~79% consumed for ~50% Group B progress; on track; US-B3 next)

### Day 1.3 US-B3 AreaChart + CardShell + BackendGapBanner + 30d Spend card (Group B complete)

**Output**:
- NEW `frontend/src/components/charts/AreaChart.tsx` (~85 lines mockup-direct port of page-admin.jsx:5-29 AreaChart helper)
- NEW `frontend/src/components/ui/CardShell.tsx` (~50 lines reusable card shell; mockup-direct port of OverviewPage inline Card pattern)
- NEW `frontend/src/components/ui/BackendGapBanner.tsx` (~15 lines warning-tone banner with role="note")
- NEW `frontend/src/features/cost-dashboard/__fixtures__/spendOverTime30d.ts` (30-day fixture array; mirrors mockup demo values)
- NEW `frontend/tests/unit/components/AreaChart.test.tsx` (5 cases)
- NEW `frontend/tests/unit/components/CardShell.test.tsx` (5 CardShell + 2 BackendGapBanner = 7 cases)
- UPDATE `frontend/src/components/charts/index.ts` (add AreaChart export)
- UPDATE `frontend/src/features/cost-dashboard/components/CostOverview.tsx` (add §3 30d Spend over time card; new imports)
- UPDATE `frontend/src/i18n/locales/{en,zh-TW}/common.json` (+ cost.spendOverTime.{title, subtitle} + cost.banner.areaChart30d = 3 keys × 2 locales)

**Verification**:
- Vitest 397/397 全綠 (80 files; +12 from Day 1.2 baseline 385: AreaChart 5 + CardShell 5 + BackendGapBanner 2)
- `npm run lint` exit 0 (fixed 1 STYLE.md §1 violation: replaced inline `style={{ height }}` with SVG `height` attribute)
- `npm run build` 3.41s; main bundle 330.14 kB (+0.38 from 329.76 Day 1.2 baseline)

**DoD verified**:
- ✅ AreaChart mockup-direct port (page-admin.jsx:5-29 spec): gradient fill + line stroke + 3 grid lines at 25/50/75% + viewBox + preserveAspectRatio="none"
- ✅ AreaChart STYLE.md §1 compliant (SVG `height` attribute instead of inline style)
- ✅ CardShell mockup-direct port (page-overview.jsx Card): rounded-[12px] + bg-bg-1 + border-b header + p-4 body; header omitted when no title/actions
- ✅ BackendGapBanner role="note" + warning-tone + ⚠️ icon for AP-2 honesty marker
- ✅ §3 30d Spend over time card assembled (CardShell wrapping AreaChart + BackendGapBanner)
- ✅ Fixture `SPEND_OVER_TIME_30D` 30-element array matches mockup demo values
- ✅ i18n EN + zh-TW parity (no missing translation warnings on build)

**Day 1.3 hours ~45 min**:
- AreaChart + CardShell + BackendGapBanner primitives + specs: ~25 min
- CostOverview integration + i18n + fixture: ~10 min
- Lint fix (inline style → SVG attribute) + re-verify: ~10 min

**Day 1 cumulative ~4.1 hr** (vs ~4.2 hr commit budget = ~98% consumed; **Group B 100% complete** 3/3 USs done; on calibration band)

---

## Day 2 — 2026-05-19 — Group C kickoff (over-budget acknowledged)

### Day 2 budget note

Day 1 consumed ~4.1 hr of the ~4.2 hr commit budget. Day 2 + Day 3 work
proceeds **over the planned commit ceiling**; calibration ratio will be
captured at Day 3 retrospective Q2. This is acceptable — Group B (Day 1)
included §1.0 abort + redraft overhead (~50 min) NOT in original plan
scope; treating effective Day 1 = ~3.2 hr in-scope, leaves ~1.0 hr
remaining for Group C+D.

### Day 2.1 US-C1 CategoryBarsCard + BarTrack primitive

**Prong 2 content verify (R3 mitigation, COMPLETED before US-C1 code)**:
- Read `frontend/src/features/cost-dashboard/types.ts` confirmed
  `by_type: Record<string, Record<string, AggregatedSlice>>` (2-level dict)
- Read mockup page-admin.jsx:230-252 confirmed 6 FLAT categories with
  fixed names + colors + percentages
- **D-Day2-1 drift finding**: mockup 6-category taxonomy DOES NOT 1:1 map
  to backend 2-level dict shape. Per CLAUDE.md §Mockup-Fidelity backend-
  gap rule, chose fully-fixture path + BackendGapBanner declaring
  taxonomy gap. Real backend `by_type` view continues to render below
  via existing CostBreakdownTable (separate raw-detail view).
- Logged AD-Cost-Backend-Category-Taxonomy-Phase58 for harmonization
  follow-up (added to next-phase-candidates.md Day 3 closeout).

**Output**:
- NEW `frontend/src/components/charts/BarTrack.tsx` (~40 lines reusable
  percentage-bar primitive; documented STYLE.md §3 escape hatch for
  dynamic width% + tone color)
- NEW `frontend/src/features/cost-dashboard/__fixtures__/categoryBreakdown.ts`
  (6 fixture rows mirroring mockup page-admin.jsx:232-238 demo values)
- NEW `frontend/src/features/cost-dashboard/components/CategoryBarsCard.tsx`
  (~55 lines mockup-direct port; CardShell + 6 rows × dot + name + $value
  + BarTrack + BackendGapBanner)
- NEW `frontend/tests/unit/cost-dashboard/CategoryBarsCard.test.tsx` (4
  cases: 6 BarTracks / title-subtitle / banner / toLocaleString format)
- UPDATE `frontend/src/components/charts/index.ts` (add BarTrack export)
- UPDATE `frontend/src/features/cost-dashboard/components/CostOverview.tsx`:
  - Imported CategoryBarsCard
  - Wrapped §3 (30d AreaChart) + §4 (CategoryBarsCard) into 2-col grid at
    lg breakpoint (`grid grid-cols-1 gap-3 lg:grid-cols-2`) per mockup
    page-admin.jsx:225 grid-main layout
- UPDATE i18n EN + zh-TW (+ cost.category.* 8 keys + cost.banner.categoryTaxonomy = 9 keys × 2 locales)

**CostBreakdownTable decision**: KEPT as separate detail row below the
new grid. Rationale: CategoryBarsCard is mockup-fidelity summary view
(6 flat categories); CostBreakdownTable is raw backend `by_type` 2-level
detail view. Both serve different audiences (executive summary vs
auditor / engineer detail). Keeping both honors AP-2 honesty (mockup
view alongside raw data so reviewers can validate).

**Verification**:
- Vitest 401/401 全綠 (81 files; +4 from Day 1.3 baseline 397)
- `npm run lint` exit 0 (BarTrack primitive uses 2 documented
  `eslint-disable-next-line no-restricted-syntax` for dynamic style;
  comments explain STYLE.md §3 rationale)
- `npm run build` 3.26s; main bundle 330.86 kB (+0.72 from 330.14 Day 1.3)

**DoD verified**:
- ✅ 6 mockup categories rendered with mockup-faithful tone colors
- ✅ BarTrack reusable primitive (3 consumers planned this sprint + ≥3
  future per 57.25-57.28; extraction justified per Karpathy §2)
- ✅ BackendGapBanner declares taxonomy gap (AP-2 honesty)
- ✅ CostOverview §3 + §4 wrapped in 2-col grid per mockup grid-main
- ✅ i18n EN + zh-TW parity (no missing translation warnings on build)

**Day 2.1 hours ~35 min**:
- Prong 2 content verify + D-Day2-1 logging: ~5 min
- BarTrack + CategoryBarsCard + fixture + spec: ~20 min
- CostOverview integration + i18n + verify: ~10 min

### Day 2.2 US-C2 TenantTopTable admin-scope

**Output**:
- NEW `frontend/src/features/cost-dashboard/__fixtures__/tenantTop8.ts` (8-row fixture mirroring mockup page-admin.jsx:263-270; 1 row `tenant_3kp9` alert=true + pct=320 over-quota)
- NEW `frontend/src/features/cost-dashboard/components/TenantTopTable.tsx` (~145 lines mockup-direct port of page-admin.jsx:258-293):
  - CardShell with `bodyClass=""` for flush table layout
  - `TenantRow` sub-component renders each row: avatar + slug + optional anomaly Badge + Plan Badge (shadcn outline) + Tokens (mono tnum subtle) + Cost ($X mono) + Quota % (color-coded text) + BarTrack (color-coded tone)
  - Helper functions `quotaBarTone(pct)` + `quotaTextClass(pct)` encapsulate per-pct color logic (>100 danger / >80 warning / else success+muted)
- NEW `frontend/tests/unit/cost-dashboard/TenantTopTable.test.tsx` (6 cases)
- UPDATE `frontend/src/features/cost-dashboard/components/CostOverview.tsx`:
  - Imported `TenantTopTable`
  - Added §5 admin-gated row: `{isPlatformAdmin && <TenantTopTable />}` BELOW the §3+§4 2-col grid
  - Component admin-agnostic + parent-gated design (per checklist note) keeps unit-test simple
- UPDATE i18n EN + zh-TW (+ cost.tenant.{title, subtitle, anomaly, col.*} 8 keys + cost.banner.crossTenant = 9 keys × 2 locales)

**Verification**:
- Vitest 407/407 全綠 (82 files; +6 from Day 2.1 baseline 401: 6 TenantTopTable cases)
- `npm run lint` exit 0
- `npm run build` 3.29s; main bundle 331.37 kB (+0.51 from 330.86 Day 2.1 baseline)

**DoD verified**:
- ✅ 8 fixture rows rendered with mockup-faithful tone palette
- ✅ Anomaly Badge appears ONLY on row with alert=true (1 row → tenant_3kp9)
- ✅ Over-quota (pct=320) uses danger text + danger bar tone
- ✅ Near-limit (pct=92 wonka-apac) uses warning text + warning bar tone
- ✅ Normal rows use muted text + success bar tone
- ✅ Admin scope gate at parent level (CostOverview); component itself admin-agnostic
- ✅ BackendGapBanner declares cross-tenant API gap (AP-2 honesty)
- ✅ i18n EN + zh-TW parity

**Day 2.2 hours ~25 min**:
- TenantTopTable + fixture + spec: ~15 min
- CostOverview integration + i18n + verify: ~10 min

---

---
