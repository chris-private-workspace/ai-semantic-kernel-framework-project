---
sprint: 57.24 (v2 — scope pivoted 2026-05-19)
phase: Phase 57+ Frontend SaaS 20/N (pending close)
title: AD-Cost-Dashboard-Full-Mockup-Fidelity-Rebuild — 1-Page Strict Rebuild (Frontend-Led)
class: frontend-mockup-strict-rebuild 0.60 (2nd application; HYBRID weighted blend; baseline KEEP from Sprint 57.23 1st app ratio 0.59)
duration_days: 4 (Day 0 三-prong PRESERVED from v1 / Day 1 page-head + 4-stat grid + AreaChart + reusable extracts / Day 2 category bars + tenant table + provider mix / Day 3 i18n + Vitest + Playwright + closeout)
related:
  - Sprint 57.22 AUDIT-REPORT-COMPREHENSIVE.md (Unit 1 cost-dashboard P0 — full rebuild)
  - Sprint 57.23 plan + retrospective (frontend-mockup-strict-rebuild 0.60 class 1st app)
  - Sprint 57.20 plan (Option W frontend-leads / backend-follows philosophy)
  - Sprint 57.24 v1 plan (retrofit; ABORTED Day 1 per §Step 2.5 — see docs/03-implementation/agent-harness-execution/phase-57/sprint-57-24/progress.md Day 1 entry)
  - CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint (2026-05-17)
  - reference/design-mockups/page-admin.jsx:200-321 (CostPage mockup)
  - reference/design-mockups/page-admin.jsx:1-30 (Spark + Stat + Card + AreaChart helper components)
  - .claude/rules/sprint-workflow.md §Scope-class multiplier matrix
  - .claude/rules/sprint-workflow.md §Step 2.5 (Day-0 verify; abort discipline)
  - 16-frontend-design.md §Cost Dashboard page
  - 17-cross-category-interfaces.md (no new contracts this sprint; frontend-only + fixture banners for backend-gap widgets)
---

# Sprint 57.24 v2 — AD-Cost-Dashboard-Full-Mockup-Fidelity-Rebuild

## §0 Scope Pivot Notice (2026-05-19 Day 1)

This is **Sprint 57.24 plan v2** — scope was pivoted on Day 1 from the v1 scope (5-page cosmetic retrofit Tier 1) to a single-page strict rebuild after Day 1 reality check invalidated the cosmetic-feasible premise.

**v1 scope** (drafted 2026-05-19 Day 0, ABORTED Day 1): retrofit 5 ship pages (cost-dashboard / sla-dashboard / verification / admin/tenants list / admin/tenants/settings) for mockup-fidelity cosmetic alignment under class `mockup-fidelity-retrofit` 0.55.

**v1 abort cause** (catalogued in `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-24/progress.md` Day 1 + `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-24/artifacts/mockup-fidelity-retrofit-tier-1/DRIFT-REPORT-RETROFIT-TIER-1.md` Day 1): Day 1 code-level inventory found 5/6 mockup widget groups absent on cost-dashboard + sla-dashboard production renders; tenant-settings already known structural per Sprint 57.22 Unit 31. Pattern is STRUCTURAL widget absence, not cosmetic Tailwind drift. Per §Step 2.5 «Findings shift scope by > 50% → abort sprint; redraft plan with reality baseline».

**v2 scope** (this plan, drafted Day 1 post-abort): rebuild ONLY `/cost-dashboard` to 1:1 mockup fidelity per `reference/design-mockups/page-admin.jsx:200-321`. Class pivots to `frontend-mockup-strict-rebuild` 0.60 (2nd application of NEW class introduced Sprint 57.23). Remaining 4 pages (sla-dashboard / verification / admin/tenants / tenant-settings) defer to Sprint 57.25-57.28 as separate rebuild sprints.

**Preserved from v1**:
- Branch `feature/sprint-57-24-mockup-fidelity-retrofit-tier-1` (name historical; not renamed per user direction)
- Day 0 commit `5eb7ac84` (plan v1 + checklist v1 + Day 0 三-prong + DRIFT-REPORT skeleton + AD-Memory-Structural-Rebuild-Phase58 carryover #31)
- Day 0 三-prong findings D-PRE-1 through D-PRE-4 (still valid drift catalog)
- Day 1 D-STRUCTURAL findings 1-3 (newly catalogued; feed Phase 58+ rebuild epic)
- progress.md Day 0 + Day 1 entries (historical audit trail)
- DRIFT-REPORT skeleton (repurposed as cost-dashboard-only DRIFT-REPORT going forward)

---

## Sprint Goal

Rebuild **`/cost-dashboard`** (the single Tier 1 P0 page chosen for Sprint 57.24 first rebuild) to **1:1 mockup fidelity** per mockup `reference/design-mockups/page-admin.jsx:200-321` (CostPage), extracting reusable presentation primitives (`<Spark>`, `<StatCard>`, `<AreaChart>`, `<CardShell>`) into `components/charts/` and `components/ui/` for Sprint 57.25+ reuse — **frontend-led**, backend gaps filled via fixture data + visible "backend wire pending" demo banners per AP-2 honesty.

**Two-line philosophy** (per Sprint 57.20 Option W carry-forward):

1. **Frontend leads** — Cost Dashboard rebuilt 1:1 from mockup; 6 widget groups all ship visually (page-head + 4-stat grid + 30d AreaChart + Spend-by-category bars + Spend-by-tenant top-8 table + Provider mix card); reusable chart primitives extracted for 57.25-57.28 inheritance
2. **Backend follows** — Existing `useCostSummary` hook + `GET /api/v1/cost-summary?tenant_id&month` data feeds widgets where possible (4-stat grid: derive from `data.total_cost_usd` + `data.by_type` aggregation; Spend-by-category: real `data.by_type` mapping); widgets requiring missing backend data (30d AreaChart historical / Spend-by-tenant cross-tenant admin / Provider mix cross-provider admin) ship with fixture + visible banner per CLAUDE.md §Mockup-Fidelity escape hatch + AP-2 honesty; backend gap work defer to Sprint 57.29+ as NEW AD-Cost-Dashboard-Backend-Extensions-Phase58

## Background

### Why Sprint 57.24 (this sprint)

Sprint 57.22 AUDIT-REPORT-COMPREHENSIVE.md classified `/cost-dashboard` as **Unit 1 P0** (full rebuild required). Per Day 1 reality check (see §0 Scope Pivot Notice + progress.md Day 1):

| Mockup widget group | Production state (Sprint 57.1 + 57.9 + 57.13) | Drift severity |
|---------------------|------------------------------------------------|----------------|
| 1. page-head (title + sub + route-pill + admin scope Badge) | ❌ Missing (only AppShellV2 chrome title) | STRUCTURAL |
| 2. page-actions (By tenant filter + CSV export buttons) | ❌ Missing | STRUCTURAL |
| 3. 4-stat sparkline grid (Spend MTD / Tokens MTD / Cost-run / Cache hit) | ❌ Missing | STRUCTURAL |
| 4. 30d AreaChart "Spend over time" stacked by category | ❌ Missing | STRUCTURAL |
| 5. "Spend by category" 6-bar breakdown card | ❌ Missing (data exists in `data.by_type` but no visual) | STRUCTURAL |
| 6. "Spend by tenant" top-8 admin-scope table | ❌ Missing (cross-tenant data; admin scope) | STRUCTURAL + backend gap |
| 7. "Provider mix" 4-provider admin-scope card | ❌ Missing (cross-provider data; admin scope) | STRUCTURAL + backend gap |
| ✅ Total cost + CostBreakdownTable (2-level by_type table) | ✅ Existing — REUSE / refactor into "Spend by category" body | preserve |

**Σ bottom-up**: ~6-8 hr (mid ~7 hr) before calibration
**Calibrated commit**: ~7 hr × 0.60 ≈ ~4.2 hr (Sprint 57.23 1st app ratio 0.59 baseline KEEP per `When to adjust` 3-sprint window rule)

### Q1 + Q2 decisions (2026-05-19 user alignment)

| # | Decision | Sprint 57.24 v2 implication |
|---|----------|------------------------------|
| Q1 | Abort v1 + redraft per §Step 2.5 (D option) | This plan v2 ships; v1 preserved as historical |
| Q2 | First rebuild page = `/cost-dashboard` (P1) | Sprint 57.24 v2 scope = cost-dashboard only; sla / tenants / verification / tenant-settings defer to 57.25-57.28 |

### What is preserved (NOT rewritten)

| Layer | Specific | Reuse mechanism |
|-------|----------|-----------------|
| Page wrapper | `frontend/src/pages/cost-dashboard/index.tsx` | Existing AppShellV2 wrap + RequireAuth + Routes + MonthPickerSlot preserved; only inner `CostOverview` content rewritten |
| Auth gate | `RequireAuth` wrapper + role check pattern | Unchanged; admin scope widgets gate via `useAuthStore.roles` check (matches `AdminTenantsPage` pattern) |
| Data fetching | `useCostSummary(tenantId, currentMonth)` TanStack hook | Unchanged; existing query key + URL preserved |
| MonthPicker | `MonthPickerSlot` in AppShellV2 headerActions | Unchanged |
| CostBreakdownTable | 2-level by_type rows; current Tailwind classes | REUSE — embed into "Spend by category" card body or refactor as `<CategoryBarsCard>` data feed |
| Backend `/api/v1/cost-summary` endpoint | Existing response shape | Unchanged; no new backend code this sprint |
| Vitest baseline | 369/369 (Sprint 57.23 close) | Adapt selectors for CostOverview rewrite (~5 spec updates); add NEW specs (~15-20 cases) for new widgets |

### What gets rewritten (this sprint scope)

| Layer | File | Approach |
|-------|------|----------|
| CostOverview | `frontend/src/features/cost-dashboard/components/CostOverview.tsx` | REWRITE in-place: 6-widget-group layout per mockup; preserve `useCostSummary` data hook; mockup `page-admin.jsx:200-321` 1:1 |
| page-head | (NEW inline section in CostOverview) | Page title "Cost Ledger" + subtitle + route-pill + admin scope Badge + page-actions (By tenant filter button + CSV export button stubs) |
| <Spark> | `frontend/src/components/charts/Spark.tsx` (NEW) | Inline mini-sparkline SVG component (points array → polyline); 4 stat cards consume; reusable for 57.25 sla-dashboard |
| <StatCard> | `frontend/src/components/charts/StatCard.tsx` (NEW) | label + value + unit + delta + deltaDir + spark slot per mockup `Stat` helper; reusable |
| <AreaChart> | `frontend/src/components/charts/AreaChart.tsx` (NEW) | 30-day stacked area SVG component (data array → path); reusable for 57.25+ |
| <CardShell> | `frontend/src/components/ui/CardShell.tsx` (NEW) | Card wrapper with title + subtitle + actions slot + body per mockup `Card` helper; reusable |
| <CategoryBarsCard> | `frontend/src/features/cost-dashboard/components/CategoryBarsCard.tsx` (NEW) | 6-bar breakdown card consuming `data.by_type`; reuses `<CardShell>` + `<BarTrack>` |
| <TenantTopTable> | `frontend/src/features/cost-dashboard/components/TenantTopTable.tsx` (NEW, admin-scope) | Top-8 tenant table; fixture data + "Backend cross-tenant API pending" banner |
| <ProviderMixCard> | `frontend/src/features/cost-dashboard/components/ProviderMixCard.tsx` (NEW, admin-scope) | 4-provider mix card; fixture data + "Backend cross-provider API pending" banner |
| i18n | `frontend/src/i18n/locales/{en,zh-TW}/common.json` (or `cost.json` new namespace) | +~25 keys (cost.pageTitle / cost.pageSub / cost.stat.* / cost.category.* / cost.tenant.* / cost.provider.* / cost.adminBanner) |
| Vitest specs | `CostOverview.test.tsx` + new NEW spec files | Spec rewrite + 4 NEW spec files (CategoryBarsCard / TenantTopTable / ProviderMixCard / charts primitives) |

### V2 紀律對齐 (per Sprint 57.21 + 57.23 pattern)

- **約束 1 單一範疇歸屬**: 純 frontend sprint; all changes in `frontend/src/pages/cost-dashboard/` + `frontend/src/features/cost-dashboard/` + `frontend/src/components/charts/` + `frontend/src/components/ui/` + i18n
- **約束 2 主流量驗證**: `/cost-dashboard` is core dashboard entry; Playwright MCP pair-verify required at Day 1 (page-head + 4-stat + AreaChart) + Day 2 (category + tenant + provider) + Day 3 closeout
- **約束 3 LLM Provider Neutrality**: 0 SDK import preserved
- **約束 4 Anti-Pattern checklist**:
  - **AP-2 (no Potemkin)**: TenantTopTable + ProviderMixCard ship fixture data BUT must visibly mark as "Backend cross-tenant API pending Phase 58+ AD-Cost-Dashboard-Backend-Extensions" + "Backend cross-provider API pending" demo banners — honor AP-2 honesty
  - AP-3 (cross-directory scattering): all changes stay in `cost-dashboard/components/` (feature-scope) + `components/charts/` (shared) + `components/ui/` (shared); no scattering
  - AP-4 (rename-only refactor): every rewrite delivers visible mockup-fidelity gain + reusable chart primitives downstream-consumable
- **約束 5 測試優先**: Vitest 369 baseline preserved; NEW specs ~15-20 cases (Spark + StatCard + CardShell + AreaChart primitives + CategoryBarsCard + TenantTopTable + ProviderMixCard rendering + admin scope gate); Playwright e2e cost-dashboard happy-path preserved (selector adapt for layout rewrite)

## User Stories

### Group A — Day 0 setup + 三-prong (PRESERVED from v1; marked COMPLETED)

**US-A1** [COMPLETED Day 0 — commit `5eb7ac84`]: As a Sprint 57.24 owner, I want plan/checklist landed + feature branch created + Day 0 三-prong drift findings catalogued + DRIFT-REPORT skeleton with mockup ref resolution so that Day 1+ work has a clear baseline.

> ✅ Done in v1; D-PRE-1 through D-PRE-4 catalogued in progress.md Day 0. D-STRUCTURAL-1 through D-STRUCTURAL-3 added Day 1 reality check. Plan v2 redraft (this document) completes the abort + redraft cycle.

### Group B — page-head + 4-stat grid + AreaChart + reusable extracts (Day 1)

**US-B1**: As an admin user viewing cost data, I want `/cost-dashboard` page-head rendering Title "Cost Ledger" + subtitle "Range 12 · Token + tool spend · admin-only provider breakdown" + `<route-pill>/cost-dashboard</route-pill>` + admin scope Badge ("admin scope") + page-actions row (2 outline buttons: "By tenant" filter icon + "CSV" export icon) per mockup `page-admin.jsx:202-216` so that page identity matches mockup at 1440×900.

**US-B2**: As an admin user, I want 4-stat sparkline grid rendering `<StatCard label value unit delta deltaDir spark />` for Spend MTD ($X,XXX from data.total_cost_usd; sparkline from historical fixture) / Tokens MTD (XX.XM unit from data.by_type aggregation; sparkline fixture) / Cost-run ($X.XXX derived as total_cost / run_count if available, else fixture; sparkline fixture) / Cache hit rate (XX% fixture for now; sparkline fixture) per mockup `page-admin.jsx:218-223` so that 4 KPI signals render at-a-glance.

**US-B3**: As an admin user, I want `<AreaChart>` rendering 30-day Spend over time (stacked by category per mockup; data fixture pending backend 30d history endpoint) inside a `<CardShell title="Spend over time" subtitle="Daily · 30 days · stacked by category">` per mockup `page-admin.jsx:226-228` so that historical trend visible; visible banner "Backend 30-day history API pending Phase 58+".

**US-B4** (reusable extracts): As Sprint 57.25+ owner, I want `<Spark>` + `<StatCard>` + `<AreaChart>` + `<CardShell>` extracted to `frontend/src/components/charts/` + `frontend/src/components/ui/` with documented props + Vitest specs so that 57.25 sla-dashboard rebuild + 57.26+ remaining pages can reuse without recreation.

### Group C — Spend-by-category + Spend-by-tenant + Provider mix (Day 2)

**US-C1**: As an admin user, I want `<CategoryBarsCard>` rendering "Spend by category" `<CardShell title subtitle="Last 7 days">` body with 6 category rows (Inference input/output / Thinking tokens / Tool runs / Embeddings / Sandbox compute) consuming `data.by_type` real data (fallback to mockup fixture for missing category rows) per mockup `page-admin.jsx:230-252` so that category breakdown visible; uses `<BarTrack>` primitive (extracted with charts) with per-category color token (var(--thinking) / --primary / --info / --tool / --memory / --warning per mockup).

**US-C2**: As a platform admin user, I want `<TenantTopTable>` rendering admin-scope top-8 tenant table (per mockup `page-admin.jsx:258-293`) with columns Tenant (avatar + slug + anomaly Badge) / Plan / Tokens / Cost / Quota used % / quota bar per mockup so that cross-tenant cost visibility ships; fixture data only (cross-tenant backend API pending); admin scope gate via `useAuthStore.roles.includes("admin"|"platform_admin")` (matches `AdminTenantsPage` PLATFORM_ADMIN_ROLES); non-admin users see "需要平台管理員權限" notice; visible "Backend cross-tenant API pending Phase 58+" demo banner.

**US-C3**: As a platform admin user, I want `<ProviderMixCard>` rendering admin-scope 4-provider mix (per mockup `page-admin.jsx:295-317`) with rows provider-A/B/C/self-hosted × Tokens + Cost + Pct + bar per mockup so that LLM provider cost split visible; fixture data only (cross-provider backend API pending); same admin scope gate as US-C2; visible "Backend cross-provider API pending" demo banner + mockup's LLM-neutrality redaction notice ("Provider identity is redacted in operator views").

### Group D — i18n + integration + Vitest + Playwright + closeout (Day 3)

**US-D1**: As a multilingual operator, I want `frontend/src/i18n/locales/{en,zh-TW}/common.json` (or new `cost.json` namespace if scope warrants) extended with ~25 NEW keys covering page-head copy + 4-stat labels + category names + tenant table column headers + provider mix copy + admin banner text + LLM-neutrality redaction notice so that all NEW widgets render in both EN and zh-TW.

**US-D2**: As a routing maintainer, I want CostOverview.tsx assembled with all 6 widget groups in mockup-faithful grid layout (`grid-stats` 4-col stat row + `grid-main` 2-col main row × 2 stacks per mockup `page-admin.jsx:225-318`) using Tailwind tokens from Sprint 57.18 wired set + arbitrary value escape hatches per STYLE.md §3 where Tailwind utility doesn't map cleanly (multi-column grid layouts; precision bar widths).

**US-D3**: As a Sprint 57.24 v2 owner, I want Vitest 369 baseline grown to 369+N (N≥15 covering 4 new chart primitives + 3 new feature components + CostOverview integration + admin scope gate + fixture banner rendering) without regression + Playwright e2e cost-dashboard happy-path preserved (selector adapt for layout rewrite; visual-regression baseline regenerated via workflow_dispatch + cherry-pick parallel Sprint 57.23 pattern) + commits + retrospective.md Q1-Q7 + memory snapshot `memory/project_phase57_24_cost_dashboard_rebuild.md` + MEMORY.md +1 line + `.claude/rules/sprint-workflow.md` calibration matrix +1 row for `frontend-mockup-strict-rebuild` 0.60 class 2nd app + CLAUDE.md Current Sprint row + Last Updated footer landed so that Sprint 57.24 v2 = COMPLETE and Phase 57+ Frontend 20/N opens cleanly.

## Technical Specifications

### CostOverview.tsx rewrite — 6-widget-group layout

```typescript
// AFTER (mockup-direct port, frontend-led)
import { useTranslation } from "react-i18next";
import { useAuthStore } from "../../auth/store/authStore";
import { useCostSummary } from "../hooks/useCostSummary";
import { useCostStore } from "../store/costStore";
import { CardSkeleton, ErrorRetry } from "../../../components/ui";
import { CardShell } from "../../../components/ui/CardShell";
import { StatCard } from "../../../components/charts/StatCard";
import { Spark } from "../../../components/charts/Spark";
import { AreaChart } from "../../../components/charts/AreaChart";
import { CategoryBarsCard } from "./CategoryBarsCard";
import { TenantTopTable } from "./TenantTopTable";
import { ProviderMixCard } from "./ProviderMixCard";

const PLATFORM_ADMIN_ROLES = ["admin", "platform_admin"];

export function CostOverview() {
  const { t } = useTranslation("common");
  const tenantId = useAuthStore((s) => s.tenant?.id ?? "");
  const roles = useAuthStore((s) => s.roles);
  const isPlatformAdmin = roles.some((r) => PLATFORM_ADMIN_ROLES.includes(r));
  const currentMonth = useCostStore((s) => s.currentMonth);

  const { data, isLoading, error, refetch } = useCostSummary(tenantId, currentMonth);

  // Loading / error / no-tenant guards (preserved from existing)
  if (!tenantId) return <p className="text-sm text-destructive">{t("common.noTenant")}</p>;
  if (isLoading) return <CardSkeleton count={3} />;
  if (error) return <ErrorRetry error={error} onRetry={() => void refetch()} />;
  if (!data) return null;

  return (
    <div className="space-y-4">
      {/* §1 page-head (US-B1) */}
      <PageHead
        title={t("cost.pageTitle")}
        subtitle={t("cost.pageSub")}
        routePath="/cost-dashboard"
        adminBadge={isPlatformAdmin ? t("cost.adminScope") : undefined}
        actions={<><FilterButton /><ExportCSVButton /></>}
      />

      {/* §2 4-stat sparkline grid (US-B2) */}
      <div className="grid grid-cols-4 gap-3">
        <StatCard label={t("cost.stat.spendMtd")} value={data.total_cost_usd} unit="$" delta={...} spark={<Spark points={[...]} />} />
        {/* ... 3 more stat cards */}
      </div>

      {/* §3 AreaChart "Spend over time" (US-B3) */}
      <CardShell title={t("cost.spendOverTime")} subtitle={t("cost.spendOverTimeSub")}>
        <AreaChart data={spendOverTime30dFixture} />
        <BackendGapBanner reason={t("cost.banner.areaChart30d")} />
      </CardShell>

      {/* §4 Spend-by-category bars (US-C1) */}
      <CategoryBarsCard byType={data.by_type} />

      {/* §5 + §6 admin-scope grid (US-C2 + US-C3) */}
      {isPlatformAdmin && (
        <div className="grid grid-cols-2 gap-4">
          <TenantTopTable />
          <ProviderMixCard />
        </div>
      )}
    </div>
  );
}
```

### Reusable chart primitives spec

| Primitive | Path | Props | Reuse target |
|-----------|------|-------|--------------|
| `<Spark>` | `frontend/src/components/charts/Spark.tsx` | `points: number[]`; `tone?: string`; `width?: number=60`; `height?: number=24` | 57.25 sla-dashboard 4-stat sparklines |
| `<StatCard>` | `frontend/src/components/charts/StatCard.tsx` | `label, value, unit?, delta?, deltaDir?: "up"|"down", spark?: ReactNode` | 57.25 sla-dashboard 4-stat grid |
| `<AreaChart>` | `frontend/src/components/charts/AreaChart.tsx` | `data: number[]`; `tone?: string`; `height?: number=200` | 57.25 sla-dashboard LatencyChart base; 57.26+ other dashboards |
| `<CardShell>` | `frontend/src/components/ui/CardShell.tsx` | `title, subtitle?, actions?, bodyClass?, children` | All future widget cards (sla / verification / tenants / settings) |

### Admin scope gate pattern (US-C2 + US-C3)

Mirror `AdminTenantsPage` pattern:
```typescript
const PLATFORM_ADMIN_ROLES = ["admin", "platform_admin"];
const isPlatformAdmin = roles.some((r) => PLATFORM_ADMIN_ROLES.includes(r));
// Render TenantTopTable + ProviderMixCard only if isPlatformAdmin; else hide silently (no error notice — these are admin-only enhancements, not core data)
```

### Fixture + backend-gap banner pattern (AP-2 honesty)

```typescript
// components/ui/BackendGapBanner.tsx (NEW small primitive)
export function BackendGapBanner({ reason }: { reason: string }) {
  return (
    <div className="mt-2 rounded-md border border-warning/40 bg-warning/5 px-3 py-2 text-xs text-warning">
      ⚠️ {reason}
    </div>
  );
}
```

Used in: `<AreaChart>` (30d history pending) / `<TenantTopTable>` (cross-tenant API pending) / `<ProviderMixCard>` (cross-provider API pending).

## File Change List

### NEW files (13)

1. `frontend/src/components/charts/Spark.tsx`
2. `frontend/src/components/charts/StatCard.tsx`
3. `frontend/src/components/charts/AreaChart.tsx`
4. `frontend/src/components/charts/index.ts` (barrel)
5. `frontend/src/components/ui/CardShell.tsx`
6. `frontend/src/components/ui/BackendGapBanner.tsx`
7. `frontend/src/features/cost-dashboard/components/CategoryBarsCard.tsx`
8. `frontend/src/features/cost-dashboard/components/TenantTopTable.tsx`
9. `frontend/src/features/cost-dashboard/components/ProviderMixCard.tsx`
10. `frontend/src/features/cost-dashboard/components/PageHead.tsx` (or inline; TBD Day 1)
11. `frontend/src/features/cost-dashboard/__fixtures__/spendOverTime30d.ts`
12. `frontend/src/features/cost-dashboard/__fixtures__/tenantTop8.ts`
13. `frontend/src/features/cost-dashboard/__fixtures__/providerMix.ts`

### NEW spec files (4-5; ≥15 cases)

1. `frontend/src/components/charts/__tests__/Spark.test.tsx`
2. `frontend/src/components/charts/__tests__/StatCard.test.tsx`
3. `frontend/src/components/charts/__tests__/AreaChart.test.tsx`
4. `frontend/src/components/ui/__tests__/CardShell.test.tsx`
5. `frontend/src/features/cost-dashboard/components/__tests__/CategoryBarsCard.test.tsx` + `TenantTopTable.test.tsx` + `ProviderMixCard.test.tsx` (3 in 1 group or split)

### REWRITTEN files (1)

1. `frontend/src/features/cost-dashboard/components/CostOverview.tsx` — full rewrite from 68-line MVP to ~150-line 6-widget-group layout

### MODIFIED files (2-3)

1. `frontend/src/i18n/locales/en/common.json` — +~25 keys
2. `frontend/src/i18n/locales/zh-TW/common.json` — +~25 keys (mirror)
3. `frontend/src/features/cost-dashboard/components/__tests__/CostOverview.test.tsx` — adapt selectors + cover 6 widget groups

### PRESERVED (not touched)

- `frontend/src/pages/cost-dashboard/index.tsx` — AppShellV2 wrapper
- `frontend/src/features/cost-dashboard/hooks/useCostSummary.ts` — TanStack hook
- `frontend/src/features/cost-dashboard/store/costStore.ts` — currentMonth state
- `frontend/src/features/cost-dashboard/components/MonthPicker.tsx` — header slot
- `frontend/src/features/cost-dashboard/components/CostBreakdownTable.tsx` — REUSED (embed into CategoryBarsCard body OR keep as-is and replace with CategoryBarsCard; decision Day 2)
- `backend/**` — 0 backend changes

## Acceptance Criteria

1. ✅ `/cost-dashboard` renders all 6 mockup widget groups at 1440×900 (page-head + 4-stat + AreaChart + category bars + tenant table + provider mix) per mockup `page-admin.jsx:200-321` 1:1
2. ✅ Admin scope gate works: non-admin users see only widgets 1-4 (no tenant table / provider mix); admin users see all 6
3. ✅ Real backend data flows: 4-stat grid Spend MTD from `data.total_cost_usd`; Spend-by-category bars from `data.by_type` aggregation
4. ✅ Backend-gap widgets ship with visible "Backend X pending Phase 58+" banner (AP-2 honesty preserved)
5. ✅ 4 reusable chart primitives (`<Spark>`, `<StatCard>`, `<AreaChart>`, `<CardShell>`) + 1 banner primitive (`<BackendGapBanner>`) extracted with Vitest specs
6. ✅ Vitest 369+N where N≥15 NEW cases; baseline preserved
7. ✅ Playwright e2e cost-dashboard happy-path passes; visual-regression baseline regenerated via workflow_dispatch + cherry-pick
8. ✅ Bundle KB delta ≤ +30 KB (charts primitives are lightweight; no chart lib import — pure SVG)
9. ✅ i18n EN + zh-TW parity for ~25 NEW keys; no missing translation warnings
10. ✅ a11y-scan passes for `/cost-dashboard`; getByTestId("app-shell") anchor preserved
11. ✅ DRIFT-REPORT verdict for `/cost-dashboard` = PARITY (Playwright MCP pair-verify at Day 1 + Day 2 + Day 3 closeout)
12. ✅ Commits + retrospective + memory + CLAUDE.md + sprint-workflow calibration matrix +1 row + PR landed

## Deliverables

- [ ] Plan v2 + checklist v2 redrafted (Day 1 post-abort)
- [ ] §0 Scope Pivot Notice preserves abort context (this document § §0)
- [ ] DRIFT-REPORT skeleton repurposed cost-dashboard-only
- [ ] 4 reusable chart primitives (Spark / StatCard / AreaChart / CardShell) + BackendGapBanner extracted
- [ ] 3 feature components (CategoryBarsCard / TenantTopTable / ProviderMixCard) + 3 fixtures landed
- [ ] CostOverview rewritten 6-widget-group layout; mockup parity at 1440×900
- [ ] Admin scope gate wired (PLATFORM_ADMIN_ROLES)
- [ ] Vitest ≥369+15 passing; Playwright e2e + a11y-scan + visual-regression baseline current
- [ ] i18n EN + zh-TW +~25 keys
- [ ] Playwright MCP pair-verify artifacts (mockup + production screenshots at 1440×900) saved to `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-24/artifacts/mockup-fidelity-retrofit-tier-1/screenshots/`
- [ ] Retrospective Q1-Q7 + memory snapshot + MEMORY.md +1 + sprint-workflow calibration matrix +1 row (2nd app of frontend-mockup-strict-rebuild 0.60 class) + CLAUDE.md Current Sprint row + Last Updated footer
- [ ] PR opened + CI green + merge + post-merge cleanup

## Dependencies & Risks

### Dependencies

- `useCostSummary` hook stable (Sprint 57.9 US-6 Day 4 close; no expected drift)
- `useAuthStore.roles` populated (Sprint 57.13 US-A2; preserved)
- Sprint 57.18 wired tokens (oklch indigo + warning + thinking + memory + tool + info + success) — D-PRE-2 finding all needed tokens present
- Sprint 57.23 visual-baseline workflow_dispatch + cherry-pick pattern (RECENT EVIDENCE: PR #156 recovery)

### Risks

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| **R1** | Playwright MCP browser still stuck from Sprint 57.23 + Day 0 attempts → no visual baselines possible | MEDIUM | Code-level diff vs mockup line-by-line as primary verify (per R3 contingency from v1); Playwright pair-verify deferred to Day 3 closeout; if still stuck, document in DRIFT-REPORT as "code-level audit only; visual screenshots pending session reset" + escalate to AD-Playwright-MCP-Recovery-Phase58 |
| **R2** | Reusable chart primitives over-engineered for cost-dashboard alone | LOW | Keep primitive API minimal (mockup `Spark` is ~10 lines; mirror); document downstream consumption (57.25 sla LatencyChart will extend AreaChart) |
| **R3** | `data.by_type` shape doesn't cleanly map to mockup 6-category split | MEDIUM | Day 2 Prong 2 content verify before US-C1 commit; if missing categories (e.g. mockup has "Thinking tokens" but backend lacks `thinking` type) → use fixture for missing rows + log AD-Cost-Backend-Category-Taxonomy-Phase58 |
| **R4** | Bundle size blow-up from 4 NEW chart components | LOW | All SVG-based; no chart lib import; expected ~5-10 KB per component; total ≤30 KB acceptable |
| **R5** | Admin scope gate edge case (non-admin user sees nothing where mockup shows widgets) | LOW | Render widgets 1-4 always (non-admin still sees core data); only widgets 5-6 (tenant table + provider mix) gated; matches existing AdminTenantsPage UX pattern |
| **R6** | Carryover: visual-baseline workflow_dispatch GHA PR-create permission already validated Sprint 57.23 (PR #156); preserve pattern + cherry-pick from `chore/visual-baselines-*` | LOW | Reuse Sprint 57.23 FIX-008 wiring (workflow_dispatch + opens-a-PR not pushes-to-protected-main) |

### Common Risk Classes (per sprint-workflow.md §Common Risk Classes)

- **Risk Class A** (paths-filter vs `required_status_checks`): N/A — no `.github/workflows/` changes expected; backend-ci paths-filter not triggered
- **Risk Class B** (cross-platform mypy unused-ignore): N/A — frontend-only
- **Risk Class C** (module-level singleton across test event loops): N/A — frontend Vitest

## Workload

| Group | Bottom-up est | Class haircut 0.60 | Day allocation |
|-------|---------------|--------------------|----------------|
| Group A (Day 0 三-prong) | 0 (PRESERVED from v1) | 0 | Day 0 (done) |
| Group B (page-head + 4-stat + AreaChart + reusable extracts) | ~3 hr | ~1.8 hr | Day 1 |
| Group C (category bars + tenant table + provider mix) | ~2.5 hr | ~1.5 hr | Day 2 |
| Group D (i18n + integration + Vitest + Playwright + closeout) | ~1.5 hr | ~0.9 hr | Day 3 |
| **Σ Bottom-up** | **~7 hr** | **~4.2 hr** | **3 working days** |

**Bottom-up est ~7 hr → calibrated commit ~4.2 hr (multiplier 0.60)**

Day 4 retrospective Q2: verify actual / committed ratio; expected range [0.85, 1.20] (band per `.claude/rules/sprint-workflow.md` §Workload Calibration). If outside band → log AD-Sprint-Plan-N for class baseline review.

Reference data point: Sprint 57.23 1st application of `frontend-mockup-strict-rebuild` 0.60 class produced ratio 0.59 (below band by 0.26); 2nd app (this sprint) provides validation toward 3-sprint window evidence for potential lift to 0.40-0.45 per AD-Sprint-Plan parallel to Sprint 57.16 AD-Sprint-Plan-13 mechanical-class rule.

## Sequencing / Day plan

### Day 0 — PRESERVED (commit 5eb7ac84; 2026-05-19)

- [x] Plan v1 + checklist v1 drafted (mirror Sprint 57.23 structure)
- [x] Branch creation from main `13663c8c`
- [x] Day 0 三-prong (Prong 1 path verify + Prong 4 test selector verify)
- [x] DRIFT-REPORT skeleton (5-page table; now repurposed cost-dashboard-only)
- [x] D-PRE-1 through D-PRE-4 catalogued in progress.md Day 0
- [x] AD-Memory-Structural-Rebuild-Phase58 #31 added to next-phase-candidates.md

### Day 1 — Plan/Checklist Redraft + Group B (2026-05-19 evening through 2026-05-20 if continued)

- [ ] §0 Scope Pivot Notice + plan v2 + checklist v2 redrafted (this work)
- [ ] D-STRUCTURAL-1 through D-STRUCTURAL-3 entered progress.md + DRIFT-REPORT Day 1
- [ ] US-B1 page-head + page-actions render
- [ ] US-B2 4-stat sparkline grid + `<StatCard>` + `<Spark>` primitives extracted
- [ ] US-B3 `<AreaChart>` primitive + 30d Spend over time card + BackendGapBanner
- [ ] US-B4 reusable chart primitives finalized + Vitest specs
- [ ] Playwright MCP retry (browser_close + reconnect attempt)

### Day 2 — Group C (2026-05-20 or 21)

- [ ] US-C1 `<CategoryBarsCard>` consuming `data.by_type`
- [ ] US-C2 `<TenantTopTable>` admin-scope + fixture + BackendGapBanner
- [ ] US-C3 `<ProviderMixCard>` admin-scope + fixture + BackendGapBanner + LLM-neutrality redaction notice
- [ ] CostOverview integration: assemble all 6 widget groups in mockup-faithful grid
- [ ] CostBreakdownTable decision (embed into CategoryBarsCard OR keep separate)

### Day 3 — Group D + closeout (2026-05-21 or 22)

- [ ] US-D1 i18n keys EN + zh-TW
- [ ] US-D2 CostOverview final assembly + selector adapt for existing tests
- [ ] US-D3 Vitest 369+15 passing
- [ ] Playwright MCP pair-verify pass (mockup port 8080 + production port 3007 at 1440×900); save artifacts to `claudedocs/4-changes/sprint-57-24-*/screenshots/`
- [ ] DRIFT-REPORT cost-dashboard verdict = PARITY
- [ ] visual-regression baseline regenerated (workflow_dispatch + cherry-pick)
- [ ] Retrospective Q1-Q7
- [ ] Memory snapshot `memory/project_phase57_24_cost_dashboard_rebuild.md` + MEMORY.md +1 line
- [ ] `.claude/rules/sprint-workflow.md` calibration matrix +1 row (frontend-mockup-strict-rebuild 0.60 class 2nd app data point)
- [ ] CLAUDE.md Current Sprint row + Last Updated footer (per REFACTOR-001 §Sprint Closeout policy minimal touch)
- [ ] PR open + CI green + merge

---

**Plan v2 drafted**: 2026-05-19 Day 1 (post-abort)
**Sprint duration target**: 3-4 working days from Day 1 plan/checklist redraft complete to PR merged
