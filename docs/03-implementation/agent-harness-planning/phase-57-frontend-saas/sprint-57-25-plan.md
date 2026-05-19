---
sprint: 57.25
phase: Phase 57+ Frontend SaaS 21/N (pending close)
title: AD-Mockup-Fidelity-Rebuild-Sla-Dashboard — 1-Page Strict Rebuild (Frontend-Led)
class: frontend-mockup-strict-rebuild 0.60 (3rd application; baseline KEEP per 3-sprint window rule; sub-classification decision pending this sprint's ratio per Sprint 57.24 v2 retrospective Q4)
duration_days: 4 (Day 0 setup + 三-prong + Prong 5 / Day 1 page-head + 4-stat + LatencyChart / Day 2 SLO status + slow-ops table + error-rate / Day 3 i18n + integration + closeout)
related:
  - Sprint 57.22 AUDIT-REPORT-COMPREHENSIVE.md (Unit 9 sla-dashboard P0 — full rebuild, same FUNCTIONAL pattern as Unit 8 cost-dashboard)
  - Sprint 57.24 v2 plan + retrospective (frontend-mockup-strict-rebuild 0.60 class 2nd app; 7 reusable primitives extracted)
  - Sprint 57.23 plan + retrospective (frontend-mockup-strict-rebuild 0.60 class 1st app; ratio 0.59)
  - Sprint 57.20 plan (Option W frontend-leads / backend-follows philosophy)
  - CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint (2026-05-17)
  - reference/design-mockups/page-admin.jsx:31-199 (SlaPage mockup + LatencyChart helper)
  - .claude/rules/sprint-workflow.md §Scope-class multiplier matrix
  - .claude/rules/sprint-workflow.md §Step 2.5 (Day-0 verify; Prong 5 audit cross-ref AD #38)
  - claudedocs/1-planning/next-phase-candidates.md #32 (AD-Mockup-Fidelity-Rebuild-Sla-Dashboard-Phase58 carryover spec)
  - 16-frontend-design.md §SLA Dashboard page
  - 17-cross-category-interfaces.md (no new contracts this sprint; frontend-only + fixture banners for backend-gap widgets)
---

# Sprint 57.25 — AD-Mockup-Fidelity-Rebuild-Sla-Dashboard

## Sprint Goal

Rebuild **`/sla-dashboard`** to **1:1 mockup fidelity** per mockup `reference/design-mockups/page-admin.jsx:31-199` (SlaPage), reusing all 7 reusable presentation primitives extracted in Sprint 57.24 v2 (`<Spark>` / `<StatCard>` / `<AreaChart>` / `<BarTrack>` / `<CardShell>` / `<PageHead>` / `<BackendGapBanner>`) plus 1 NEW feature-scoped `<LatencyChart>` (3-series multi-line; inline per Karpathy §2 "extract on 2nd consumer") — **frontend-led**, backend gaps filled via fixture data + visible "backend wire pending" demo banners per AP-2 honesty.

**Two-line philosophy** (per Sprint 57.20 Option W carry-forward):

1. **Frontend leads** — SLA Dashboard rebuilt 1:1 from mockup; 6 widget groups ship visually (page-head with 4-button time-range tabs + Refresh + Export / 4-stat sparkline / 24h LatencyChart 3-series SVG / 5-row SLO status card / Top slow ops table / Error rate by service); reuses all 7 Sprint 57.24 v2 primitives + 1 NEW feature-scoped LatencyChart
2. **Backend follows** — Existing `useSLAReport` hook + `GET /api/v1/sla-report` data feeds 4-stat grid partially (availability + p99 from `api_p99_ms` / `loop_*_p99_ms` — but mockup p50/p95/p99 latency split + error budget % not in backend response → fixture for those + AP-2 banner); LatencyChart 24h time-series + SLO status + slow ops table + error rate by service all require backend SSE/aggregation endpoints (NOT in scope) → fixture data + visible banner per CLAUDE.md §Mockup-Fidelity escape hatch + AP-2 honesty; backend gap work folds into NEW AD-SLA-Dashboard-Backend-Extensions-Phase58 carryover

## Background

### Why Sprint 57.25 (this sprint)

Sprint 57.22 AUDIT-REPORT-COMPREHENSIVE.md classified `/sla-dashboard` as **Unit 9 P0** (full rebuild required; same FUNCTIONAL pattern as Unit 8 cost-dashboard, 15% mockup fidelity, 4-5 hr estimate). Per `next-phase-candidates.md` #32 (added Sprint 57.24 v2 closeout 2026-05-19), Sprint 57.25 is the explicit Sprint 57.25 candidate for this rebuild.

| Mockup widget group | Production state (Sprint 57.1 + 57.9 + 57.13 + 57.16) | Drift severity |
|---------------------|--------------------------------------------------------|----------------|
| 1. page-head (title + sub + route-pill + 4-button time-range tabs + Refresh + Export) | ❌ Missing (only AppShellV2 chrome title + plaintext "SLA report for your tenant..." paragraph) | STRUCTURAL |
| 2. 4-stat sparkline grid (p50 latency / p95 latency / p99 latency / Error budget) | ❌ Missing (production renders 6 `<SLAMetricsCard>` instances with different field semantic) | STRUCTURAL |
| 3. 24h LatencyChart 3-series SVG (p50 / p95 / p99 over 48 time points) | ❌ Missing (production has no chart at all) | STRUCTURAL |
| 4. 5-row SLO status card (Loop p95 / Tool success / HITL response / Subagent depth / Cost/run + bar-track + budget used %) | ❌ Missing (production has flat 6-card MetricsCard layout) | STRUCTURAL |
| 5. Top slow operations table (6-row × Operation + Kind Badge + p50/p95/p99/Calls) | ❌ Missing | STRUCTURAL + backend gap |
| 6. Error rate by service card (6-row × service + rate + bar-track) | ❌ Missing | STRUCTURAL + backend gap |
| ✅ `useSLAReport` hook + `<SLAMetricsCard>` 3-state PASS/FAIL/noData logic + threshold constants | ✅ Existing — REUSE partial values (availability_pct / api_p99_ms maps to mockup p99) + reuse SLA_STATE 3-tone palette wisdom into SLO status card | preserve where applicable |

**Σ bottom-up**: ~5-6 hr (mid ~5.5 hr) before calibration
**Calibrated commit**: ~5.5 hr × 0.60 ≈ ~3.3 hr (KEEP class baseline per 3-sprint window rule)

### Class baseline + sub-classification watch (Sprint 57.24 v2 retro Q4 carryover)

This sprint is the **3rd application of `frontend-mockup-strict-rebuild` 0.60 class**. The 2-data-point history shows bimodal pattern:

| Sprint | Scope shape | actual/committed ratio | actual/bottom-up ratio |
|--------|-------------|-----------------------:|------------------------:|
| 57.23 (1st app) | Auth flow — 7 small routes (login / SSO / mfa / register / invite / callback / expired) | 0.59 (below band by 0.26) | 0.36 |
| 57.24 v2 (2nd app) | 1 rich dashboard — cost-dashboard with 6 widget groups + 7 primitives extraction | 1.19 (top of band) | 0.71 |
| 57.25 (this; 3rd app) | 1 rich dashboard — sla-dashboard with 6 widget groups + 1 NEW LatencyChart | **TBD; predicted ~1.0-1.2 if "rich-dashboard" pattern holds** | TBD |

**Class baseline KEEP 0.60** per `When to adjust` 3-sprint window rule. If Sprint 57.25 ratio ≥ 1.0 (confirming "rich-dashboard" pattern), Day 3 retrospective Q4 should propose **sub-classification split**:
- `frontend-mockup-strict-rebuild-auth-flow` (small-route shape) → 0.55 (lower haircut; aligned with 57.23 evidence)
- `frontend-mockup-strict-rebuild-dashboard-rich` (rich-dashboard shape) → 0.65 (higher haircut; aligned with 57.24+57.25 evidence)

If Sprint 57.25 ratio < 0.85 (rejoining 57.23 below-band pattern), KEEP 0.60 baseline and wait for 4th data point.

### What is preserved (NOT rewritten)

| Layer | Specific | Reuse mechanism |
|-------|----------|-----------------|
| Page wrapper | `frontend/src/pages/sla-dashboard/index.tsx` | Existing AppShellV2 wrap + RequireAuth + Routes preserved; only inner `SLAOverview` content rewritten; AppShellV2 may optionally gain `headerSlot={<MonthPickerSlot/>}` mirroring cost-dashboard pattern (Day 1 decision) |
| Auth gate | `RequireAuth` wrapper | Unchanged |
| Data fetching | `useSLAReport(tenantId, currentMonth)` TanStack hook | Unchanged; existing query key + URL preserved |
| Sprint 57.24 v2 primitives | `components/charts/{Spark, StatCard, AreaChart, BarTrack}` + `components/ui/{CardShell, PageHead, BackendGapBanner}` | All 7 imported and reused; no API changes |
| SLA threshold constants | `AVAILABILITY_THRESHOLD_STANDARD` + `API_P99_MAX_MS` + `LOOP_*_P99_MAX_MS` + `HITL_QUEUE_NOTIF_P99_MAX_MS` | Reused inside SLO status card for current vs target comparison |
| `<SLAMetricsCard>` 3-state palette wisdom | Tailwind tokens `text-success` / `text-danger` / `text-muted-foreground` | Lifted into SLO status card status indicators (mockup uses `var(--success)` / `var(--danger)` dot colors) |
| Backend `/api/v1/sla-report` endpoint | Existing response shape | Unchanged; no new backend code this sprint |
| Vitest baseline | 412/412 (Sprint 57.24 v2 close) | Adapt 2 specs (SLAOverview + SLAMetricsCard) for full rewrite; add NEW specs ~12-15 cases for new widgets + LatencyChart primitive |

### What gets rewritten (this sprint scope)

| Layer | File | Approach |
|-------|------|----------|
| SLAOverview | `frontend/src/features/sla-dashboard/components/SLAOverview.tsx` | REWRITE in-place: 6-widget-group layout per mockup; preserve `useSLAReport` data hook; mockup `page-admin.jsx:32-155` 1:1 |
| LatencyChart | `frontend/src/features/sla-dashboard/components/LatencyChart.tsx` (NEW; feature-scoped) | 3-series SVG (p50/p95/p99); 48 data points; axis labels + grid; ~85 lines mockup-direct port of `page-admin.jsx:157-198`; inline because only 1 consumer (SLA dashboard); Sprint 57.26+ may extract if 2nd consumer arises |
| SLOStatusCard | `frontend/src/features/sla-dashboard/components/SLOStatusCard.tsx` (NEW; feature-scoped) | 5-row SLO objectives display; consumes threshold constants + useSLAReport data; reuses `<BarTrack>` + `<CardShell>` |
| TopSlowOpsTable | `frontend/src/features/sla-dashboard/components/TopSlowOpsTable.tsx` (NEW; feature-scoped) | 6-row table mockup-direct port; fixture data + `<BackendGapBanner>` |
| ErrorRateByServiceCard | `frontend/src/features/sla-dashboard/components/ErrorRateByServiceCard.tsx` (NEW; feature-scoped) | 6-row card with `<BarTrack>` per service; fixture data + `<BackendGapBanner>` |
| TimeRangeTabs | `frontend/src/features/sla-dashboard/components/TimeRangeTabs.tsx` (NEW; feature-scoped) | 4-button group (1h / 24h-active-default / 7d / 30d) with local React state; visual-only this sprint; consumed in page-head actions; banner explains pending wire-up |
| Fixtures | `frontend/src/features/sla-dashboard/__fixtures__/{latencyChart24h, slowOps, errorRateByService, statSparklines}.ts` | NEW; mirror mockup demo values |
| i18n | `frontend/src/i18n/locales/{en,zh-TW}/common.json` | +~20 keys (sla.pageTitle / sla.pageSub / sla.range.{1h,24h,7d,30d} / sla.stat.* / sla.slo.* / sla.slowOps.* / sla.errorRate.* / sla.banner.*) |
| Vitest specs | `SLAOverview.test.tsx` (existing; adapt) + `LatencyChart.test.tsx` + `SLOStatusCard.test.tsx` + `TopSlowOpsTable.test.tsx` + `ErrorRateByServiceCard.test.tsx` + `TimeRangeTabs.test.tsx` (NEW) | 12-15 NEW cases + 2 adapt |

### V2 紀律對齐 (per Sprint 57.24 v2 pattern)

- **約束 1 單一範疇歸屬**: 純 frontend sprint; all changes in `frontend/src/pages/sla-dashboard/` + `frontend/src/features/sla-dashboard/` + i18n
- **約束 2 主流量驗證**: `/sla-dashboard` is core dashboard entry; Playwright MCP pair-verify attempted at Day 1 (page-head + 4-stat + LatencyChart) + Day 2 (SLO + slow-ops + error-rate) + Day 3 closeout; if MCP still stuck (4th-consecutive blocker per AD #37) → code-level audit substitute
- **約束 3 LLM Provider Neutrality**: 0 SDK import preserved (frontend-only sprint)
- **約束 4 Anti-Pattern checklist**:
  - **AP-2 (no Potemkin)**: TopSlowOpsTable + ErrorRateByServiceCard + LatencyChart 24h history all ship fixture data BUT visibly mark as "Backend X API pending Phase 58+" per AP-2 honesty (3 BackendGapBanner usages expected; matches Sprint 57.24 v2 pattern of 3 banners)
  - AP-3 (cross-directory scattering): all changes stay in `features/sla-dashboard/` (feature-scope) — NO new primitives extracted to `components/charts/` or `components/ui/` this sprint (LatencyChart kept inline per Karpathy §2)
  - AP-4 (rename-only refactor): every rewrite delivers visible mockup-fidelity gain; SLAMetricsCard is REPLACED by 4-stat grid + SLO status card (not renamed); existing SLAMetricsCard.tsx deleted post-rewrite verify per Karpathy §3 orphan delete
- **約束 5 測試優先**: Vitest 412 baseline preserved; NEW specs ~12-15 cases; Playwright e2e for sla-dashboard NOT existing — Day 3 closeout decision whether to add bootstrap e2e or skip (out-of-scope; consider Sprint 57.29+ Ops Dashboards remaining); a11y-scan baseline preserved

## User Stories

### Group A — Day 0 setup + 三-prong + Prong 5 (PRE-WORK)

**US-A1**: As a Sprint 57.25 owner, I want plan + checklist landed + feature branch created from main `345f74a3` + Day 0 三-prong (Prong 1 path + Prong 2 content + Prong 4 test selector) + Prong 5 audit cross-ref (per AD #38) findings catalogued in progress.md Day 0 + DRIFT-REPORT skeleton with mockup ref resolution + AD-SLA-Dashboard-Backend-Extensions-Phase58 carryover added to next-phase-candidates.md so that Day 1+ work has a clear baseline and 3rd-app class baseline data point reference is locked in.

### Group B — page-head + 4-stat grid + LatencyChart (Day 1)

**US-B1**: As an operator viewing SLA data, I want `/sla-dashboard` page-head rendering Title "SLA Dashboard" + subtitle "Range 12 · Observability · p50 / p95 / p99 latency + error budget" + `<route-pill>/sla-dashboard</route-pill>` + page-actions row (4-button time-range tab group [1h / 24h-active-default / 7d / 30d] + Refresh button + Export button) per mockup `page-admin.jsx:33-52` so that page identity matches mockup at 1440×900. Time range tab state managed by local React useState (default "24h"); Refresh + Export buttons render as stubs with title tooltip per AP-2 honesty.

**US-B2**: As an operator, I want 4-stat sparkline grid rendering `<StatCard label value unit delta deltaDir spark />` for **p50 latency** (284ms / fixture; sparkline fixture; mockup-faithful since useSLAReport returns no p50 split) / **p95 latency** (1.84s / fixture from useSLAReport.api_p95_ms if available, else mockup fixture) / **p99 latency** (4.21s / real from useSLAReport.api_p99_ms; spark fixture) / **Error budget** (92.4% / fixture; mockup-faithful since not in backend response) per mockup `page-admin.jsx:54-59` so that 4 KPI signals render at-a-glance. Stat cards reuse Sprint 57.24 v2 `<StatCard>` + `<Spark>` primitives unchanged.

**US-B3**: As an operator, I want NEW feature-scoped `<LatencyChart>` rendering 24h latency distribution as 3-series (p50 / p95 / p99) multi-line SVG with axis labels (x: -23h..-0h every 6h; y: max..0 4 ticks) + grid lines (25/50/75%) per mockup `page-admin.jsx:157-198` inside a `<CardShell title="Latency distribution" subtitle="24h · all agents · p50 / p95 / p99" actions={kbar badges p50/p95/p99 dots}>` so that historical latency distribution trend visible. Fixture data (48 time points; mockup-faithful demo curve); visible `<BackendGapBanner reason={sla.banner.latencyChart24h}>` below card explaining backend time-series aggregation endpoint pending Phase 58+. LatencyChart kept inline in `features/sla-dashboard/components/` per Karpathy §2 (not extracted to `components/charts/`); Sprint 57.26+ extraction decision deferred.

### Group C — SLO status + slow ops + error rate (Day 2)

**US-C1**: As an operator, I want `<SLOStatusCard>` rendering "SLO status" subtitle "Active SLO objectives" body with 5 SLO rows (Loop p95 < 2s / Tool success ≥ 99% / HITL response < 5m / Subagent depth ≤ 5 / Cost / run < $0.05) per mockup `page-admin.jsx:72-99` so that SLO objectives compliance visible. Each row: success/danger dot indicator + SLO name + current value (mono tnum; danger color if failing) / target value (subtle) + `<BarTrack>` budget-used % + budget used % subtle label. Use threshold constants from existing SLAOverview (AVAILABILITY_THRESHOLD_STANDARD / API_P99_MAX_MS / LOOP_*_P99_MAX_MS / HITL_QUEUE_NOTIF_P99_MAX_MS) where applicable + mockup fixtures for SLOs not yet backed by threshold constants (Cost/run; Subagent depth).

**US-C2**: As an operator, I want `<TopSlowOpsTable>` rendering 6-row table (per mockup `page-admin.jsx:104-129`) with columns Operation (mono small) + Kind Badge (tool/loop/subagent/verify/memory tone palette) + p50/p95/p99 (mono tnum right; p99 warning color if > 3000ms) + Calls (mono tnum subtle right toLocaleString) so that top latency contributors visible. Fixture data (6 mockup-faithful rows); `<BackendGapBanner reason={sla.banner.crossOperationP99}>` below table; reuses `<CardShell>` + `<Badge>` (shadcn).

**US-C3**: As an operator, I want `<ErrorRateByServiceCard>` rendering 6-row card (per mockup `page-admin.jsx:131-152`) with rows inference.adapter / tool.runner / memory.store / audit.writer / subagent.scheduler / webhook.dispatcher × service name (mono small) + rate % (mono tnum; warning color if > 0.5%) + `<BarTrack>` per service (width = rate × 50; warning tone if > 0.5%, success otherwise) so that per-service error rate visible. Fixture data (6 mockup-faithful values); `<BackendGapBanner reason={sla.banner.perServiceErrorRate}>` below card.

### Group D — i18n + integration + Vitest + Playwright + closeout (Day 3)

**US-D1**: As a multilingual operator, I want `frontend/src/i18n/locales/{en,zh-TW}/common.json` extended with ~20 NEW keys covering page-head copy + range tab labels + 4-stat labels + SLO row names + slow-ops column headers + error-rate service labels + 3× BackendGapBanner reasons + LatencyChart card title/subtitle so that all NEW widgets render in both EN and zh-TW.

**US-D2**: As a routing maintainer, I want SLAOverview.tsx assembled with all 6 widget groups in mockup-faithful grid layout (`grid-cols-4` 4-stat row + `grid-cols-2` main grids × 2 stacks per mockup `page-admin.jsx:61-153`) using Tailwind tokens from Sprint 57.18 wired set + arbitrary value escape hatches per STYLE.md §3 where Tailwind utility doesn't map cleanly (multi-column grid layouts; precision bar widths). MonthPicker preserved as auxiliary control (mockup doesn't show it but production users depend on month-level data; AP-2 banner explains range-tabs pending; MonthPicker location TBD Day 2 — likely AppShellV2 headerSlot mirroring cost-dashboard pattern).

**US-D3**: As a Sprint 57.25 owner, I want Vitest 412 baseline grown to 412+N (N≥12 covering LatencyChart + SLOStatusCard + TopSlowOpsTable + ErrorRateByServiceCard + TimeRangeTabs + SLAOverview integration) without regression + Playwright MCP pair-verify attempted (4th-consecutive blocker possible per AD #37; code-level audit fallback) + visual-regression baseline regenerated via workflow_dispatch + cherry-pick (parallel Sprint 57.23 PR #156 + 57.24 v2 PR #157 pattern; sla-dashboard route may need adding to visual-regression.spec.ts 6-route snapshot list if not yet present) + commits + retrospective.md Q1-Q7 with calibration ratio analysis + sub-classification proposal if pattern confirmed + memory snapshot `memory/project_phase57_25_sla_dashboard_rebuild.md` + MEMORY.md +1 line + `.claude/rules/sprint-workflow.md` calibration matrix +1 row for `frontend-mockup-strict-rebuild` 0.60 class 3rd app + CLAUDE.md Current Sprint row + Last Updated footer landed so that Sprint 57.25 = COMPLETE and Phase 57+ Frontend 21/N opens cleanly.

## Technical Specifications

### SLAOverview.tsx rewrite — 6-widget-group layout

```typescript
// AFTER (mockup-direct port; frontend-led; reuses 7 Sprint 57.24 v2 primitives + 1 NEW feature-scoped LatencyChart)
import { useTranslation } from "react-i18next";
import { CardSkeleton, ErrorRetry } from "../../../components/ui";
import { PageHead } from "../../../components/ui/PageHead";
import { BackendGapBanner } from "../../../components/ui/BackendGapBanner";
import { CardShell } from "../../../components/ui/CardShell";
import { StatCard } from "../../../components/charts/StatCard";
import { Spark } from "../../../components/charts/Spark";
import { useAuthStore } from "../../auth/store/authStore";
import { useSLAReport } from "../hooks/useSLAReport";
import { useSLAStore } from "../store/slaStore";
import { LatencyChart } from "./LatencyChart";
import { SLOStatusCard } from "./SLOStatusCard";
import { TopSlowOpsTable } from "./TopSlowOpsTable";
import { ErrorRateByServiceCard } from "./ErrorRateByServiceCard";
import { TimeRangeTabs } from "./TimeRangeTabs";
import { MonthPicker } from "../../cost-dashboard/components/MonthPicker";
import { sparkP50, sparkP95, sparkP99, sparkErrorBudget } from "../__fixtures__/statSparklines";

export function SLAOverview() {
  const { t } = useTranslation("common");
  const tenantId = useAuthStore((s) => s.tenant?.id ?? "");
  const currentMonth = useSLAStore((s) => s.currentMonth);
  const setMonth = useSLAStore((s) => s.setMonth);

  const { data, isLoading, isFetching, error, refetch } = useSLAReport(tenantId, currentMonth);

  if (!tenantId) return <p className="text-sm text-destructive">{t("common.noTenant")}</p>;
  if (isLoading) return <CardSkeleton count={3} />;
  if (error) return <ErrorRetry error={error} onRetry={() => void refetch()} />;
  if (!data) return null;

  return (
    <div className="space-y-4">
      {/* §1 page-head (US-B1) */}
      <PageHead
        title={t("sla.pageTitle")}
        subtitle={t("sla.pageSub")}
        routePath="/sla-dashboard"
        actions={
          <>
            <TimeRangeTabs />
            <RefreshButton onClick={() => void refetch()} disabled={isFetching} />
            <ExportButton />
          </>
        }
      />

      {/* MonthPicker preserved as auxiliary (mockup doesn't show; AP-2 banner explains range-tabs pending) */}
      <div className="flex items-center gap-3">
        <MonthPicker value={currentMonth} onChange={setMonth} disabled={isFetching} />
        <span className="text-xs text-fg-muted">{t("sla.banner.monthPickerAuxiliary")}</span>
      </div>

      {/* §2 4-stat sparkline grid (US-B2) */}
      <div className="grid grid-cols-4 gap-3" data-testid="sla-stat-grid">
        <StatCard label={t("sla.stat.p50")} value="284" unit="ms" delta="-18ms" deltaDir="up" spark={<Spark points={sparkP50} tone="hsl(var(--primary))" />} />
        <StatCard label={t("sla.stat.p95")} value="1.84" unit="s" delta="-180ms" deltaDir="up" spark={<Spark points={sparkP95} tone="hsl(var(--info))" />} />
        <StatCard label={t("sla.stat.p99")} value="4.21" unit="s" delta="+0.30s" deltaDir="down" spark={<Spark points={sparkP99} tone="hsl(var(--warning))" />} />
        <StatCard label={t("sla.stat.errorBudget")} value="92.4" unit="%" delta="-1.2pp" deltaDir="down" spark={<Spark points={sparkErrorBudget} tone="hsl(var(--success))" />} />
      </div>

      {/* §3 LatencyChart 24h + §4 SLO status (US-B3 + US-C1) */}
      <div className="grid grid-cols-[1fr_360px] gap-4">
        <CardShell title={t("sla.latencyChart.title")} subtitle={t("sla.latencyChart.subtitle")} actions={<LatencyKbar />}>
          <LatencyChart />
          <BackendGapBanner reason={t("sla.banner.latencyChart24h")} />
        </CardShell>
        <SLOStatusCard data={data} />
      </div>

      {/* §5 + §6 Slow ops + error rate (US-C2 + US-C3) */}
      <div className="grid grid-cols-2 gap-4">
        <TopSlowOpsTable />
        <ErrorRateByServiceCard />
      </div>
    </div>
  );
}
```

### LatencyChart primitive spec (NEW; feature-scoped; not extracted)

| Aspect | Decision |
|--------|----------|
| Path | `frontend/src/features/sla-dashboard/components/LatencyChart.tsx` (feature-scoped) |
| API | No props (consumes inline fixture from `__fixtures__/latencyChart24h.ts`); ~85 lines mockup-direct port of `page-admin.jsx:157-198` |
| SVG dimensions | viewBox 760×220; pad 30; preserveAspectRatio="none"; className="w-full" + style {height: 220} |
| Series | 3 lines (p50 primary stroke 1.8 / p95 info stroke 1.4 / p99 warning stroke 1.4 opacity 0.9) |
| Grid | 3 horizontal lines at 25/50/75% positions |
| Axis | x labels at i=0,12,24,36,47 → "-23h" / "-17h" / "-11h" / "-5h" / "-0h" (every 6h); y labels at 4 ticks 0/0.25/0.5/0.75 normalized to max |
| Colors | `var(--primary)` / `var(--info)` / `var(--warning)` per mockup |
| Karpathy §2 | NOT extracted to `components/charts/` (only 1 consumer); Sprint 57.26+ revisit if 2nd consumer arises |

### Reused Sprint 57.24 v2 primitives (no API change)

| Primitive | Path | Sprint 57.25 usage |
|-----------|------|-------------------|
| `<Spark>` | `components/charts/Spark.tsx` | 4-stat grid sparklines (p50/p95/p99/error-budget) |
| `<StatCard>` | `components/charts/StatCard.tsx` | 4-stat grid main cards |
| `<AreaChart>` | `components/charts/AreaChart.tsx` | NOT USED this sprint (mockup uses multi-line LatencyChart, not area) |
| `<BarTrack>` | `components/charts/BarTrack.tsx` | SLO status budget-used bars (5) + ErrorRateByServiceCard service bars (6) |
| `<CardShell>` | `components/ui/CardShell.tsx` | LatencyChart wrapper + SLOStatusCard + TopSlowOpsTable + ErrorRateByServiceCard |
| `<PageHead>` | `components/ui/PageHead.tsx` | Page header (title + subtitle + routePath pill + actions slot) |
| `<BackendGapBanner>` | `components/ui/BackendGapBanner.tsx` | 3 instances (LatencyChart 24h + cross-operation p99 + per-service error rate) |

### TimeRangeTabs primitive spec (NEW; feature-scoped; visual-only this sprint)

```typescript
// frontend/src/features/sla-dashboard/components/TimeRangeTabs.tsx (~50 lines)
import { useState } from "react";
import { useTranslation } from "react-i18next";

type Range = "1h" | "24h" | "7d" | "30d";

export function TimeRangeTabs() {
  const { t } = useTranslation("common");
  const [active, setActive] = useState<Range>("24h");
  const ranges: Range[] = ["1h", "24h", "7d", "30d"];
  return (
    <div role="tablist" aria-label={t("sla.range.label")} className="inline-flex rounded-md border border-border bg-bg-1 p-0.5">
      {ranges.map((r) => (
        <button
          key={r}
          role="tab"
          aria-selected={active === r}
          onClick={() => setActive(r)}
          className={active === r ? "rounded-sm bg-bg-2 px-3 py-1 text-xs font-medium text-fg" : "rounded-sm px-3 py-1 text-xs text-fg-muted hover:text-fg"}
          data-testid={`sla-range-tab-${r}`}
        >
          {t(`sla.range.${r}`)}
        </button>
      ))}
    </div>
  );
}
```

Behavior: visual-only; active state local; clicking doesn't refetch data (refetch wire-up pending backend time-range aggregation endpoint; documented inline via AP-2 banner sibling component in §3 LatencyChart card).

### SLOStatusCard structure (NEW; feature-scoped)

```typescript
// frontend/src/features/sla-dashboard/components/SLOStatusCard.tsx (~110 lines)
interface SLOStatusCardProps {
  data: SLAReport;
}

const SLOS = [
  { name: "Loop p95 < 2s", target: 2.0, mode: "lte", field: "loop_simple_p95_ms", divideBy: 1000, unit: "" },
  { name: "Tool success ≥ 99%", target: 99, mode: "gte", fixedValue: 99.4 /* fixture */, unit: "" },
  { name: "HITL response < 5m", target: 5, mode: "lte", fixedValue: 2.3 /* fixture (min) */, unit: "" },
  { name: "Subagent depth ≤ 5", target: 5, mode: "lte", fixedValue: 4 /* fixture */, unit: "" },
  { name: "Cost / run < $0.05", target: 0.05, mode: "lte", fixedValue: 0.052 /* fixture (failing) */, unit: "" },
] as const;
// Per-row: success/danger dot + name + current/target (mono tnum; danger color if failing) + BarTrack budget-used % + budget used % subtle
```

Reuses `<CardShell>` + `<BarTrack>` + Tailwind tokens `text-success` / `text-danger` / `text-fg-muted`. AP-2 honesty: 4 of 5 SLO values are fixture (backend doesn't track Tool success / HITL response / Subagent depth / Cost-per-run dedicated metrics yet); the card itself ships without BackendGapBanner because the SLO logic is functional and reuses existing thresholds — but a single sibling note explains 4 of 5 are placeholder values pending dedicated metrics.

### TopSlowOpsTable structure (NEW; feature-scoped)

6-row table mockup-direct port; uses shadcn `<Table>` primitive (if present) or plain Tailwind `<table>` with mockup-faithful styling. Kind Badge tones map to mockup's tone palette: tool→tool / loop→primary / subagent→thinking / verify→success / memory→memory. p99 column color-code: > 3000ms → warning; else fg-muted.

```typescript
const SLOW_OPS = [
  { name: "tool.metrics.query", k: "tool", p50: 180, p95: 1900, p99: 4400, calls: 2840 },
  { name: "tool.k8s.set_env", k: "tool", p50: 920, p95: 2800, p99: 5200, calls: 18 },
  { name: "loop.iteration", k: "loop", p50: 290, p95: 1820, p99: 4100, calls: 14820 },
  { name: "subagent.spawn", k: "subagent", p50: 12, p95: 38, p99: 220, calls: 412 },
  { name: "verification.run", k: "verify", p50: 18, p95: 84, p99: 180, calls: 9200 },
  { name: "memory.write", k: "memory", p50: 4, p95: 12, p99: 38, calls: 7820 },
];
```

### ErrorRateByServiceCard structure (NEW; feature-scoped)

```typescript
const ERROR_RATES = [
  { name: "inference.adapter", rate: 0.04 },
  { name: "tool.runner", rate: 0.6 },
  { name: "memory.store", rate: 0.0 },
  { name: "audit.writer", rate: 0.0 },
  { name: "subagent.scheduler", rate: 0.12 },
  { name: "webhook.dispatcher", rate: 0.4 },
];
// Per row: service name (mono small) + rate % (mono tnum; warning if > 0.5%) + <BarTrack pct={rate * 50} tone={rate > 0.5 ? "warning" : "success"} />
```

## File Change List

### NEW files (~10)

1. `frontend/src/features/sla-dashboard/components/LatencyChart.tsx` (~85 lines)
2. `frontend/src/features/sla-dashboard/components/SLOStatusCard.tsx` (~110 lines)
3. `frontend/src/features/sla-dashboard/components/TopSlowOpsTable.tsx` (~95 lines)
4. `frontend/src/features/sla-dashboard/components/ErrorRateByServiceCard.tsx` (~70 lines)
5. `frontend/src/features/sla-dashboard/components/TimeRangeTabs.tsx` (~50 lines)
6. `frontend/src/features/sla-dashboard/components/RefreshButton.tsx` + `ExportButton.tsx` (small stubs ~25 lines each; or inline if not reused)
7. `frontend/src/features/sla-dashboard/__fixtures__/latencyChart24h.ts` (48 time points × p50/p95/p99)
8. `frontend/src/features/sla-dashboard/__fixtures__/slowOps.ts` (6 rows)
9. `frontend/src/features/sla-dashboard/__fixtures__/errorRateByService.ts` (6 rows)
10. `frontend/src/features/sla-dashboard/__fixtures__/statSparklines.ts` (4 spark arrays: p50/p95/p99/errorBudget)

### NEW spec files (≥5)

1. `frontend/tests/unit/sla-dashboard/LatencyChart.test.tsx` (~4 cases: svg path renders / 3 series present / axis labels present / empty fixture edge)
2. `frontend/tests/unit/sla-dashboard/SLOStatusCard.test.tsx` (~5 cases: 5 SLO rows / success-danger dot color / failing SLO has danger text class / BarTrack budget-used % present / target value mono tnum)
3. `frontend/tests/unit/sla-dashboard/TopSlowOpsTable.test.tsx` (~4 cases: 6 rows / Kind Badge tone per kind / p99 warning color when > 3000ms / BackendGapBanner present)
4. `frontend/tests/unit/sla-dashboard/ErrorRateByServiceCard.test.tsx` (~3 cases: 6 services / warning tone when rate > 0.5 / BackendGapBanner present)
5. `frontend/tests/unit/sla-dashboard/TimeRangeTabs.test.tsx` (~3 cases: 4 tabs render / 24h active default / click changes active)

### REWRITTEN files (1)

1. `frontend/src/features/sla-dashboard/components/SLAOverview.tsx` — full rewrite from current 133-line MetricsCard layout to ~120-line 6-widget-group layout

### DELETED files (1)

1. `frontend/src/features/sla-dashboard/components/SLAMetricsCard.tsx` — orphan post-rewrite (no production importer); Karpathy §3 orphan delete

### MODIFIED files (3)

1. `frontend/src/i18n/locales/en/common.json` — +~20 keys (`sla.pageTitle` / `sla.pageSub` / `sla.range.{label, 1h, 24h, 7d, 30d}` / `sla.stat.{p50, p95, p99, errorBudget}` / `sla.latencyChart.{title, subtitle}` / `sla.slo.{title, subtitle, slos.*, budgetUsed}` / `sla.slowOps.{title, subtitle}` / `sla.errorRate.{title, subtitle}` / `sla.banner.{latencyChart24h, crossOperationP99, perServiceErrorRate, monthPickerAuxiliary}` / `sla.action.{refresh, export}`)
2. `frontend/src/i18n/locales/zh-TW/common.json` — +~20 keys (mirror parity)
3. `frontend/src/features/sla-dashboard/components/__tests__/SLAOverview.test.tsx` — adapt selectors for new 6-widget layout (preserve hook + tenant gate + no-tenant guard assertions; drop legacy SLAMetricsCard assertions)

### PRESERVED (not touched)

- `frontend/src/pages/sla-dashboard/index.tsx` — AppShellV2 wrapper (may optionally gain `headerSlot` prop Day 1 decision — TBD)
- `frontend/src/features/sla-dashboard/hooks/useSLAReport.ts` — TanStack hook
- `frontend/src/features/sla-dashboard/store/slaStore.ts` — currentMonth state
- Sprint 57.24 v2 primitives (`components/charts/{Spark,StatCard,AreaChart,BarTrack}` + `components/ui/{CardShell,PageHead,BackendGapBanner}`) — reused unchanged
- `backend/**` — 0 backend changes

## Acceptance Criteria

1. ✅ `/sla-dashboard` renders all 6 mockup widget groups at 1440×900 (page-head with time-range tabs + 4-stat sparkline + LatencyChart 24h + SLO status 5-row + Top slow ops table 6-row + Error rate by service 6-row) per mockup `page-admin.jsx:32-155` 1:1
2. ✅ Reuses all 7 Sprint 57.24 v2 primitives without API changes; 0 new shared primitives added (LatencyChart kept inline feature-scoped per Karpathy §2)
3. ✅ Real backend data flows where applicable: useSLAReport.api_p99_ms feeds p99 StatCard value; loop_*_p99_ms feeds SLO status Loop p95 row threshold check; remaining mockup fields (p50 / p95 / error budget / 24h time-series / SLO 4-of-5 / slow ops / error rates) ship as fixture with AP-2 banner per CLAUDE.md §Mockup-Fidelity escape hatch
4. ✅ Backend-gap widgets ship with 3 visible `<BackendGapBanner>` instances (LatencyChart 24h history / cross-operation p99 / per-service error rate) declaring AD-SLA-Dashboard-Backend-Extensions-Phase58 carryover
5. ✅ TimeRangeTabs visual-only (local React state); MonthPicker preserved as auxiliary control with sibling note
6. ✅ Vitest 412+N where N≥12 NEW cases; baseline preserved; 2 existing specs adapted (SLAOverview.test.tsx + SLAMetricsCard.test.tsx deletion / replacement)
7. ✅ Playwright e2e for sla-dashboard NOT created this sprint (out-of-scope; defer to Sprint 57.29+ Ops Dashboards remaining); a11y-scan passes for `/sla-dashboard` (gated routes 0 critical/serious violations)
8. ✅ Bundle KB delta ≤ +20 KB (charts primitives already shipped Sprint 57.24 v2; only NEW LatencyChart + SLOStatusCard + 3 small components + i18n; expected ~10-15 KB net)
9. ✅ i18n EN + zh-TW parity for ~20 NEW keys; no missing translation warnings on `npm run build`
10. ✅ DRIFT-REPORT verdict for `/sla-dashboard` = PARITY (code-level audit if Playwright MCP 4th-consecutive blocker per AD #37; visual-regression baseline regen pending CI loop per Sprint 57.23 + 57.24 v2 pattern)
11. ✅ Commits + retrospective Q1-Q7 with calibration ratio analysis + sub-classification proposal if pattern confirmed + memory snapshot + MEMORY.md +1 quality pointer line + sprint-workflow.md calibration matrix +1 row (3rd app of frontend-mockup-strict-rebuild 0.60 class) + CLAUDE.md Current Sprint row + Last Updated footer + PR landed
12. ✅ Karpathy §3 orphan delete: SLAMetricsCard.tsx deleted post-rewrite (verify `grep -rn "SLAMetricsCard" frontend/src` returns 0 production importer; only deletion-itself git diff entry remains)

## Deliverables

- [ ] Plan + checklist drafted (this sprint Day 0)
- [ ] DRIFT-REPORT skeleton at `claudedocs/4-changes/sprint-57-25-sla-dashboard-rebuild/DRIFT-REPORT.md` with mockup ref resolution
- [ ] AD-SLA-Dashboard-Backend-Extensions-Phase58 carryover added to `next-phase-candidates.md` (Day 3 closeout) — parallel to AD #36 cost-dashboard backend extensions
- [ ] 1 NEW LatencyChart feature-scoped primitive (inline; not extracted)
- [ ] 4 NEW widget components (SLOStatusCard / TopSlowOpsTable / ErrorRateByServiceCard / TimeRangeTabs) + 2 small button stubs (Refresh / Export)
- [ ] 4 NEW fixtures (latencyChart24h / slowOps / errorRateByService / statSparklines)
- [ ] SLAOverview rewritten 6-widget-group layout; mockup parity at 1440×900
- [ ] SLAMetricsCard.tsx + its test spec deleted (Karpathy §3 orphan delete)
- [ ] Vitest ≥412+12 passing; existing SLAOverview.test.tsx adapted
- [ ] i18n EN + zh-TW +~20 keys
- [ ] Playwright MCP pair-verify attempted (4th-consecutive blocker possible); code-level audit fallback
- [ ] Retrospective Q1-Q7 + calibration ratio analysis (3rd app data point) + sub-classification proposal if pattern confirmed + memory snapshot + MEMORY.md +1 + sprint-workflow calibration matrix +1 row + CLAUDE.md minimal touch + next-phase-candidates.md update
- [ ] PR opened + CI green + merge + post-merge cleanup

## Dependencies & Risks

### Dependencies

- Sprint 57.24 v2 7 primitives stable + present (verified Day 0 Prong 1: ✅ all present)
- `useSLAReport` hook stable (Sprint 57.13 baseline; no expected drift)
- `useAuthStore.tenant.id` populated (Sprint 57.13 US-A2; preserved)
- Sprint 57.18 wired tokens (oklch indigo + warning + thinking + memory + tool + info + success) — D-PRE-1 finding all needed tokens present
- Sprint 57.23 visual-baseline workflow_dispatch + cherry-pick pattern (RECENT EVIDENCE: PR #156 + PR #157 recovery; 4-step manual workaround documented)

### Risks

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| **R1** | Playwright MCP 4th-consecutive blocker (Sprint 57.22 + 57.23 + 57.24 v2 + now 57.25) — AD #37 escalation level | HIGH | Code-level audit + Vitest spec coverage primary verify; visual-regression baseline regen via CI workflow_dispatch + cherry-pick fallback; if 4th consecutive → strongly recommend AD #37 Option A (`--isolated` flag) prioritized Phase 58.0 |
| **R2** | `useSLAReport` response field mismatch with mockup field semantic (availability_pct + api_p99_ms + loop_*_p99_ms vs mockup p50/p95/p99 latency + error budget) | MEDIUM | Day 0 Prong 2 content verify catalogued; fixture-driven path chosen for missing fields + AP-2 honesty banner; AD-SLA-Dashboard-Backend-Extensions-Phase58 carryover documents per-field mapping gap |
| **R3** | NEW LatencyChart 3-series component complexity (axis labels + grid + 3 series + 48 data points) underestimated | MEDIUM | Mockup `page-admin.jsx:157-198` is ~40 lines target; ~85 lines budgeted with TypeScript types + comments; Vitest tests narrow (svg renders / 3 paths present / axis tick count); Day 1 commit incremental |
| **R4** | TimeRangeTabs visual-only UX confusing (4 buttons that change active state but don't refetch) | LOW | Pair with sibling AP-2 banner explanation; alternative: render disabled state with tooltip; pick TBD Day 1 |
| **R5** | MonthPicker placement — mockup doesn't show it but production functionality needed | LOW | Keep MonthPicker as auxiliary inline below page-head row with sibling note; Day 2 decision whether to move to AppShellV2 headerSlot or remove entirely |
| **R6** | Bundle size blow-up from NEW feature-scoped components | LOW | All SVG-based (LatencyChart) + table/list-based (others); no chart lib import; expected ~10-15 KB net delta |
| **R7** | Existing SLAOverview.test.tsx + SLAMetricsCard.test.tsx selectors break post-rewrite | LOW | Adapt SLAOverview.test.tsx; delete SLAMetricsCard.test.tsx with component; CI Vitest stage catches regressions |
| **R8** | Sprint 57.25 ratio outlier breaks 3rd-app sub-classification decision | LOW | Per Sprint 57.24 v2 retro Q4 + sprint-workflow calibration matrix `When to adjust` 3-sprint window rule, sub-class proposal requires consistent pattern across 3+ data points; Sprint 57.25 ratio fed into Day 3 retro Q4 analysis; if pattern inconclusive → KEEP 0.60 baseline + wait for 4th data point |

### Common Risk Classes (per sprint-workflow.md §Common Risk Classes)

- **Risk Class A** (paths-filter vs `required_status_checks`): N/A — no `.github/workflows/` changes expected; backend-ci paths-filter not triggered
- **Risk Class B** (cross-platform mypy unused-ignore): N/A — frontend-only
- **Risk Class C** (module-level singleton across test event loops): N/A — frontend Vitest

## Workload

| Group | Bottom-up est | Class haircut 0.60 | Day allocation |
|-------|---------------|--------------------|----------------|
| Group A (Day 0 setup + 三-prong + Prong 5) | ~0.5 hr | ~0.3 hr | Day 0 |
| Group B (page-head + 4-stat + LatencyChart) | ~2.5 hr | ~1.5 hr | Day 1 |
| Group C (SLO status + slow ops + error rate) | ~2.0 hr | ~1.2 hr | Day 2 |
| Group D (i18n + integration + Vitest + closeout) | ~0.7 hr | ~0.4 hr | Day 3 |
| **Σ Bottom-up** | **~5.7 hr** | **~3.4 hr** | **4 working days (Day 0-3)** |

**Bottom-up est ~5.7 hr → calibrated commit ~3.4 hr (multiplier 0.60)**

Day 3 retrospective Q2: verify actual / committed ratio; expected range [0.85, 1.20] per band; expected reading ~1.0-1.2 if rich-dashboard sub-pattern holds (per Sprint 57.24 v2 pattern). If outside band → log AD-Sprint-Plan-N for class baseline review.

**3rd app data point watch** (per Sprint 57.24 v2 retro Q4 carryover):
- 57.23 ratio 0.59 (small-route shape; below band)
- 57.24 v2 ratio 1.19 (rich-dashboard shape; top of band)
- 57.25 ratio TBD — if ≥ 1.0 (rich-dashboard pattern confirmed) → Day 3 retro Q4 propose sub-class split (`-auth-flow` 0.55 + `-dashboard-rich` 0.65)
- If 57.25 ratio < 0.85 (rejoining 57.23 pattern) → KEEP 0.60 baseline and wait for 4th data point

## Sequencing / Day plan

### Day 0 — Plan + Checklist + 三-prong + Prong 5 + DRIFT-REPORT skeleton

- [ ] Plan + checklist drafted (mirror Sprint 57.24 v2 structure)
- [ ] Branch creation from main `345f74a3` (post-Sprint 57.24 v2 squash merge)
- [ ] Day 0 三-prong (Prong 1 path verify + Prong 2 content verify on useSLAReport response shape + Prong 4 test selector verify on existing SLAOverview.test.tsx + SLAMetricsCard.test.tsx + visual-regression.spec.ts 6-route snapshot list)
- [ ] Day 0 Prong 5 audit cross-ref (per AD #38): grep Sprint 57.22 AUDIT-REPORT for sla-dashboard P0 status → confirmed Unit 9 P0 full rebuild
- [ ] DRIFT-REPORT skeleton at `claudedocs/4-changes/sprint-57-25-sla-dashboard-rebuild/DRIFT-REPORT.md` with mockup ref resolution
- [ ] D-PRE-1 through D-PRE-4 catalogued in progress.md Day 0

### Day 1 — Group B (page-head + 4-stat + LatencyChart)

- [ ] US-B1 page-head + TimeRangeTabs + Refresh + Export stub buttons
- [ ] US-B2 4-stat sparkline grid (reuses StatCard + Spark)
- [ ] US-B3 LatencyChart NEW feature-scoped component + 24h fixture + CardShell + BackendGapBanner
- [ ] Vitest specs for LatencyChart (~4 cases) + TimeRangeTabs (~3 cases)
- [ ] Playwright MCP retry (browser_close + reconnect attempt; AD #37 4th-consecutive blocker watch)

### Day 2 — Group C (SLO + slow ops + error rate)

- [ ] US-C1 SLOStatusCard with 5 SLO rows (reuses BarTrack + CardShell + threshold constants from existing SLAOverview)
- [ ] US-C2 TopSlowOpsTable 6-row + fixture + Kind Badge tones + p99 warning color + BackendGapBanner
- [ ] US-C3 ErrorRateByServiceCard 6-row + fixture + BarTrack per service + BackendGapBanner
- [ ] Vitest specs for 3 components (~12 cases total)

### Day 3 — Group D + closeout

- [ ] US-D1 i18n EN + zh-TW (~20 keys)
- [ ] US-D2 SLAOverview final assembly + MonthPicker placement decision + selector adapt for existing SLAOverview.test.tsx
- [ ] SLAMetricsCard.tsx + spec delete (Karpathy §3 orphan delete)
- [ ] US-D3 Vitest 412+12 passing
- [ ] Playwright MCP pair-verify (mockup port 8080 + production port 3007 at 1440×900) — if 4th-consecutive blocker, document + code-level audit + AD #37 escalation
- [ ] visual-regression baseline regenerate (workflow_dispatch + cherry-pick; check if sla-dashboard already in 6-route snapshot list, add if not)
- [ ] DRIFT-REPORT sla-dashboard verdict = PARITY
- [ ] Retrospective.md Q1-Q7 + Q2 calibration ratio analysis + Q4 sub-classification proposal if pattern confirmed
- [ ] Memory snapshot `memory/project_phase57_25_sla_dashboard_rebuild.md` + MEMORY.md +1 quality pointer line
- [ ] `.claude/rules/sprint-workflow.md` calibration matrix +1 row (frontend-mockup-strict-rebuild 0.60 class 3rd app data point) + MHist
- [ ] `claudedocs/1-planning/next-phase-candidates.md` update (close #32 + add AD-SLA-Dashboard-Backend-Extensions-Phase58 carryover)
- [ ] CLAUDE.md Current Sprint row + Last Updated footer (per REFACTOR-001 §Sprint Closeout policy minimal touch)
- [ ] PR open + CI green + merge

---

**Plan drafted**: 2026-05-19 Day 0
**Sprint duration target**: 4 working days from Day 0 plan/checklist commit to PR merged
**Class**: `frontend-mockup-strict-rebuild` 0.60 (3rd application; baseline KEEP per 3-sprint window rule)
