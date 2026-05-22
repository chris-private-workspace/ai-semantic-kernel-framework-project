/**
 * File: frontend/src/features/sla-dashboard/components/SLAOverview.tsx
 * Purpose: SLA Dashboard top-level container — mockup-fidelity rebuild (Sprint 57.25).
 * Category: Frontend / sla-dashboard / components
 * Scope: Phase 57 / Sprint 57.25 (Group B Day 1 + Group C Day 2 complete; 6 widget groups)
 *
 * Description:
 *   Sprint 57.25 Day 2 (this state): rebuild complete — assembles all 6
 *   mockup widget groups per reference/design-mockups/page-admin.jsx:31-199
 *   (SlaPage). Legacy 6-SLAMetricsCard block + violations Badge + SLA
 *   threshold constants removed (Karpathy §3 orphan delete; semantically
 *   replaced by SLOStatusCard per user Q3 alignment).
 *
 *   Final layout (mockup-faithful grid):
 *   - §1 page-head (PageHead + TimeRangeTabs + Refresh + Export stubs)
 *   - §2 4-stat sparkline grid (StatCard × 4 + Spark × 4 reused)
 *   - §3 + §4 main grid (1fr_360px responsive): LatencyChart 24h left +
 *     SLOStatusCard right per mockup line 61-99
 *   - §5 + §6 secondary grid (2-col): TopSlowOpsTable left +
 *     ErrorRateByServiceCard right per mockup line 103-153
 *
 *   3 BackendGapBanner instances per AP-2 honesty (LatencyChart 24h /
 *   cross-operation p99 / per-service error rate); AD-SLA-Dashboard-
 *   Backend-Extensions-Phase58 carryover documents per-field gap.
 *
 *   Backend reused: useSLAReport TanStack hook + GET /api/v1/sla-report
 *   (Sprint 57.9 US-6 Day 4 stable). MonthPicker preserved as auxiliary
 *   per user Q1 alignment with sibling note.
 *
 * Created: 2026-05-06 (Sprint 57.1 Day 2)
 * Last Modified: 2026-05-19
 *
 * Modification History (newest-first):
 *   - 2026-05-19: Sprint 57.25 Day 2 US-C1+C2+C3 — SLO status + slow ops table + error rate by service; orphan delete SLAMetricsCard (Karpathy §3); rebuild complete
 *   - 2026-05-19: Sprint 57.25 Day 1 US-B1+B2+B3 — PageHead + TimeRangeTabs + 4-stat sparkline + LatencyChart card (mockup rebuild start)
 *   - 2026-05-11: Sprint 57.16 — inline styles → Tailwind utility classes (AD-Inline-Style-Cleanup-Sweep-Round2)
 *   - 2026-05-10: Sprint 57.13 US-B2 — loading → <CardSkeleton>; error → <ErrorRetry>
 *   - 2026-05-10: Sprint 57.13 US-A2 — tenant_id from authStore.tenant.id
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — migrate to useSLAReport TanStack hook + Tailwind utilities
 *   - 2026-05-06: Initial creation (Sprint 57.1 Day 2 / US-3 — SLA overview)
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx:31-199 (SlaPage canonical mockup)
 *   - frontend/src/components/ui/PageHead.tsx + CardShell.tsx + BackendGapBanner.tsx (Sprint 57.24 v2 reused)
 *   - frontend/src/components/charts/{Spark, StatCard, BarTrack}.tsx (Sprint 57.24 v2 reused)
 *   - frontend/src/features/sla-dashboard/components/{TimeRangeTabs, LatencyChart, SLOStatusCard, TopSlowOpsTable, ErrorRateByServiceCard}.tsx (Sprint 57.25 NEW feature-scoped)
 *   - sprint-57-25-plan.md §Technical Specifications
 */

import { useTranslation } from "react-i18next";

import { Spark, StatCard } from "../../../components/charts";
import { CardSkeleton, ErrorRetry } from "../../../components/ui";
import { BackendGapBanner } from "../../../components/ui/BackendGapBanner";
import { Button } from "../../../components/ui/button";
import { CardShell } from "../../../components/ui/CardShell";
import { PageHead } from "../../../components/ui/PageHead";
import { useAuthStore } from "../../auth/store/authStore";
import { MonthPicker } from "../../cost-dashboard/components/MonthPicker";
import {
  SPARK_ERROR_BUDGET,
  SPARK_P50,
  SPARK_P95,
  SPARK_P99,
} from "../__fixtures__/statSparklines";
import { useSLAReport } from "../hooks/useSLAReport";
import { useSLAStore } from "../store/slaStore";
import { ErrorRateByServiceCard } from "./ErrorRateByServiceCard";
import { LatencyChart } from "./LatencyChart";
import { SLOStatusCard } from "./SLOStatusCard";
import { TimeRangeTabs } from "./TimeRangeTabs";
import { TopSlowOpsTable } from "./TopSlowOpsTable";

export function SLAOverview() {
  const { t } = useTranslation("common");
  const tenantId = useAuthStore((s) => s.tenant?.id ?? "");
  const currentMonth = useSLAStore((s) => s.currentMonth);
  const setMonth = useSLAStore((s) => s.setMonth);

  const { data, isLoading, isFetching, error, refetch } = useSLAReport(tenantId, currentMonth);

  // Sprint 57.25 Day 1 US-B2 — derive p99 stat value from real backend
  // when available, else fixture (matches mockup demo value 4.21s).
  const p99Seconds = data?.api_p99_ms != null ? (data.api_p99_ms / 1000).toFixed(2) : "4.21";

  return (
    <div className="space-y-4">
      {/* §1 page-head (US-B1). TimeRangeTabs visual-only; Refresh wires to
          useSLAReport.refetch; Export disabled stub per AP-2 honesty. */}
      <PageHead
        title={t("sla.pageTitle")}
        subtitle={t("sla.pageSub")}
        routePath="/sla-dashboard"
        actions={
          <>
            <TimeRangeTabs />
            <Button
              variant="outline"
              size="sm"
              onClick={() => void refetch()}
              disabled={isFetching || !tenantId}
              data-testid="sla-action-refresh"
            >
              {t("sla.action.refresh")}
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled
              title={t("sla.action.exportPending")}
              data-testid="sla-action-export"
            >
              {t("sla.action.export")}
            </Button>
          </>
        }
      />

      {/* MonthPicker auxiliary control (mockup doesn't show it; user Q1
          alignment keeps inline + sibling note). */}
      <div className="flex flex-wrap items-center gap-3">
        <MonthPicker value={currentMonth} onChange={setMonth} disabled={isFetching} />
        <span
          className="text-[11.5px] text-fg-muted"
          data-testid="sla-month-picker-aux-note"
        >
          {t("sla.monthPickerAuxiliary")}
        </span>
      </div>

      {!tenantId && (
        <p className="text-sm text-destructive">No tenant in your session.</p>
      )}

      {/* §2 4-stat sparkline grid (US-B2). p99 derives from real
          data.api_p99_ms when available; p50/p95/error_budget fully
          fixture per D-PRE-2. AP-2 honesty: LatencyChart banner below
          covers missing fields aggregate; per-card banners would be noisy. */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4" data-testid="sla-stat-grid">
        <StatCard
          label={t("sla.stat.p50")}
          value="284"
          unit="ms"
          delta="-18ms"
          deltaDir="up"
          spark={<Spark points={SPARK_P50} tone="var(--primary)" />}
        />
        <StatCard
          label={t("sla.stat.p95")}
          value="1.84"
          unit="s"
          delta="-180ms"
          deltaDir="up"
          spark={<Spark points={SPARK_P95} tone="var(--info)" />}
        />
        <StatCard
          label={t("sla.stat.p99")}
          value={p99Seconds}
          unit="s"
          delta="+0.30s"
          deltaDir="down"
          spark={<Spark points={SPARK_P99} tone="var(--warning)" />}
        />
        <StatCard
          label={t("sla.stat.errorBudget")}
          value="92.4"
          unit="%"
          delta="-1.2pp"
          deltaDir="down"
          spark={<Spark points={SPARK_ERROR_BUDGET} tone="var(--success)" />}
        />
      </div>

      {/* §3 LatencyChart 24h (US-B3) + §4 SLO status (US-C1). 1fr_360px
          responsive grid per mockup page-admin.jsx:61-99 grid-main 2-col. */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_360px]">
        <CardShell
          title={t("sla.latencyChart.title")}
          subtitle={t("sla.latencyChart.subtitle")}
          actions={
            <div
              className="flex items-center gap-3 text-[11px]"
              data-testid="sla-latency-chart-kbar"
            >
              <span className="inline-flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-primary" />
                {t("sla.latencyChart.badge.p50")}
              </span>
              <span className="inline-flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-info" />
                {t("sla.latencyChart.badge.p95")}
              </span>
              <span className="inline-flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-warning" />
                {t("sla.latencyChart.badge.p99")}
              </span>
            </div>
          }
        >
          <LatencyChart />
          <BackendGapBanner reason={t("sla.banner.latencyChart24h")} />
        </CardShell>
        <SLOStatusCard data={data ?? null} />
      </div>

      {/* §5 TopSlowOpsTable (US-C2) + §6 ErrorRateByServiceCard (US-C3).
          2-col grid per mockup page-admin.jsx:103-153. */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <TopSlowOpsTable />
        <ErrorRateByServiceCard />
      </div>

      {/* Loading + error states (preserved from Sprint 57.13 baseline). */}
      {isLoading && tenantId && <CardSkeleton count={3} />}

      {error && (
        <div role="alert">
          <ErrorRetry error={error} onRetry={() => void refetch()} />
        </div>
      )}
    </div>
  );
}
