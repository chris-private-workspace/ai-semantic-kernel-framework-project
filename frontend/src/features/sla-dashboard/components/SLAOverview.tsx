/**
 * File: frontend/src/features/sla-dashboard/components/SLAOverview.tsx
 * Purpose: SLA Dashboard top-level container — Phase-2 verbatim-CSS re-point (Sprint 57.32).
 * Category: Frontend / sla-dashboard / components
 * Scope: Phase 57 / Sprint 57.32 Day 1 US-B1+B2 (Phase-2 verbatim re-point on Sprint 57.25 strict-rebuild scaffolding)
 *
 * Description:
 *   Sprint 57.32 Day 1 (this state): Phase-2 verbatim CSS re-point. The
 *   Sprint 57.25 strict-rebuild composition is preserved; the visual
 *   layer is swapped from translated-Tailwind (grid grid-cols-* / etc.)
 *   to mockup `.page-head` + `.grid-stats` + `.grid-main` + `.kbar` CSS
 *   classes; the primitive wrappers swap from components/ui/{PageHead,
 *   StatCard, CardShell} to components/mockup-ui/{Stat, Spark, Card,
 *   Button, Badge} (verbatim from Sprint 57.29 mockup-ui foundation).
 *
 *   Final layout (mockup-faithful, verbatim per page-admin.jsx:32-198 SlaPage):
 *   - §1 page-head (.page-head + .page-actions inline; TimeRangeTabs +
 *     Refresh + Export buttons)
 *   - §2 .grid-stats 4-stat sparkline grid (Stat × 4 + Spark × 4)
 *   - §3 + §4 .grid-main row 1 (LatencyChart 24h Card LEFT + SLOStatusCard RIGHT)
 *   - §5 + §6 .grid-main row 2 (TopSlowOpsTable LEFT + ErrorRateByServiceCard RIGHT)
 *
 *   3 BackendGapBanner instances preserved per AP-2 honesty
 *   (AD-SLA-Dashboard-Backend-Extensions-Phase58 carryover).
 *
 *   Backend reused: useSLAReport TanStack hook + GET /api/v1/sla-report
 *   (Sprint 57.9 US-6 stable). MonthPicker auxiliary preserved per Sprint
 *   57.25 user Q1 alignment.
 *
 * Created: 2026-05-06 (Sprint 57.1 Day 2)
 * Last Modified: 2026-05-23
 *
 * Modification History (newest-first):
 *   - 2026-05-23: Sprint 57.32 Day 1 US-B1+B2 — verbatim CSS re-point: .page-head + .grid-stats + .grid-main + .kbar + mockup-ui primitives
 *   - 2026-05-19: Sprint 57.25 Day 2 US-C1+C2+C3 — SLO status + slow ops table + error rate by service; orphan delete SLAMetricsCard (Karpathy §3); rebuild complete
 *   - 2026-05-19: Sprint 57.25 Day 1 US-B1+B2+B3 — PageHead + TimeRangeTabs + 4-stat sparkline + LatencyChart card (mockup rebuild start)
 *   - 2026-05-11: Sprint 57.16 — inline styles → Tailwind utility classes (AD-Inline-Style-Cleanup-Sweep-Round2)
 *   - 2026-05-10: Sprint 57.13 US-B2 — loading → <CardSkeleton>; error → <ErrorRetry>
 *   - 2026-05-10: Sprint 57.13 US-A2 — tenant_id from authStore.tenant.id
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — migrate to useSLAReport TanStack hook + Tailwind utilities
 *   - 2026-05-06: Initial creation (Sprint 57.1 Day 2 / US-3 — SLA overview)
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx:32-198 (SlaPage canonical mockup)
 *   - frontend/src/styles-mockup.css (mockup CSS foundation — .grid-stats / .grid-main / .page-head / .kbar / .btn-group)
 *   - frontend/src/components/mockup-ui.tsx (Stat / Spark / Card / Button / Badge primitives — Sprint 57.29 verbatim)
 *   - frontend/src/features/sla-dashboard/components/{TimeRangeTabs, LatencyChart, SLOStatusCard, TopSlowOpsTable, ErrorRateByServiceCard}.tsx
 *   - sprint-57-32-plan.md §US-B1+B2
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline style literals are copied byte-for-byte from mockup page-admin.jsx layout consts per Sprint 57.32 Day 1 US-B1+B2 verbatim escape-hatch (same pattern as Sprint 57.31 CostOverview). */

import type { CSSProperties } from "react";
import { useTranslation } from "react-i18next";

import { Badge, Button, Card, Spark, Stat } from "../../../components/mockup-ui";
import { CardSkeleton, ErrorRetry } from "../../../components/ui";
import { BackendGapBanner } from "../../../components/ui/BackendGapBanner";
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

// Verbatim from page-admin.jsx grid layout (sections 54 / 61 / 103) — section
// layout consts reused by the page below; matches Sprint 57.29 OverviewPage +
// Sprint 57.31 CostOverview pattern.
const layoutStyles = {
  page: { padding: 18 } satisfies CSSProperties,
  gridStats: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: 12,
    marginBottom: 14,
  } satisfies CSSProperties,
  gridMainRow1: {
    display: "grid",
    gridTemplateColumns: "1fr 360px",
    gap: 14,
    marginBottom: 14,
  } satisfies CSSProperties,
  gridMainRow2: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 14,
    marginBottom: 14,
  } satisfies CSSProperties,
  monthPickerRow: {
    display: "flex",
    flexWrap: "wrap" as const,
    alignItems: "center",
    gap: 12,
    marginBottom: 14,
  } satisfies CSSProperties,
  monthPickerNote: { fontSize: 11.5, color: "var(--fg-muted)" } satisfies CSSProperties,
  noTenant: { fontSize: 13, color: "var(--danger)", marginBottom: 14 } satisfies CSSProperties,
};

export function SLAOverview() {
  const { t } = useTranslation("common");
  const tenantId = useAuthStore((s) => s.tenant?.id ?? "");
  const currentMonth = useSLAStore((s) => s.currentMonth);
  const setMonth = useSLAStore((s) => s.setMonth);

  const { data, isLoading, isFetching, error, refetch } = useSLAReport(tenantId, currentMonth);

  // p99 stat value derives from real backend when available, else fixture
  // (matches mockup demo value 4.21s).
  const p99Seconds = data?.api_p99_ms != null ? (data.api_p99_ms / 1000).toFixed(2) : "4.21";

  return (
    <div style={layoutStyles.page}>
      {/* ── §1 page-head (verbatim from page-admin.jsx:34-52) ──
          TimeRangeTabs is .btn-group visual-only; Refresh wires to
          useSLAReport.refetch; Export disabled stub per AP-2 honesty. */}
      <div className="page-head">
        <div>
          <div className="page-title">{t("sla.pageTitle")}</div>
          <div className="page-sub">
            {t("sla.pageSub")}
            <span className="route-pill">/sla-dashboard</span>
          </div>
        </div>
        <div className="page-actions">
          <TimeRangeTabs />
          <Button
            variant="outline"
            size="sm"
            icon="refresh"
            onClick={() => void refetch()}
            disabled={isFetching || !tenantId}
            data-testid="sla-action-refresh"
          >
            {t("sla.action.refresh")}
          </Button>
          <Button
            variant="outline"
            size="sm"
            icon="download"
            disabled
            title={t("sla.action.exportPending")}
            data-testid="sla-action-export"
          >
            {t("sla.action.export")}
          </Button>
        </div>
      </div>

      {/* MonthPicker auxiliary control (mockup doesn't show it; Sprint 57.25
          user Q1 alignment keeps inline + sibling note as a production-only
          UI affordance — same pattern as Sprint 57.31 MonthPicker treatment). */}
      <div style={layoutStyles.monthPickerRow}>
        <MonthPicker value={currentMonth} onChange={setMonth} disabled={isFetching} />
        <span style={layoutStyles.monthPickerNote} data-testid="sla-month-picker-aux-note">
          {t("sla.monthPickerAuxiliary")}
        </span>
      </div>

      {!tenantId && (
        <p style={layoutStyles.noTenant}>No tenant in your session.</p>
      )}

      {/* ── §2 .grid-stats 4-stat sparkline row (verbatim from page-admin.jsx:54-59) ──
          p99 derives from real data.api_p99_ms when available; p50/p95/error_budget
          fully fixture per D-PRE-2. AP-2 honesty: LatencyChart banner below
          covers missing fields aggregate; per-card banners would be noisy. */}
      <div style={layoutStyles.gridStats} data-testid="sla-stat-grid">
        <Stat
          label={t("sla.stat.p50")}
          value="284"
          unit="ms"
          delta="-18ms"
          deltaDir="up"
          spark={<Spark points={SPARK_P50} tone="var(--primary)" />}
        />
        <Stat
          label={t("sla.stat.p95")}
          value="1.84"
          unit="s"
          delta="-180ms"
          deltaDir="up"
          spark={<Spark points={SPARK_P95} tone="var(--info)" />}
        />
        <Stat
          label={t("sla.stat.p99")}
          value={p99Seconds}
          unit="s"
          delta="+0.30s"
          deltaDir="down"
          spark={<Spark points={SPARK_P99} tone="var(--warning)" />}
        />
        <Stat
          label={t("sla.stat.errorBudget")}
          value="92.4"
          unit="%"
          delta="-1.2pp"
          deltaDir="down"
          spark={<Spark points={SPARK_ERROR_BUDGET} tone="var(--success)" />}
        />
      </div>

      {/* ── §3 + §4 .grid-main row 1 (verbatim from page-admin.jsx:61-99) ──
          LatencyChart 24h LEFT (with .kbar legend in actions) + SLOStatusCard RIGHT. */}
      <div style={layoutStyles.gridMainRow1}>
        <Card
          title={t("sla.latencyChart.title")}
          subtitle={t("sla.latencyChart.subtitle")}
          actions={
            <div className="kbar" data-testid="sla-latency-chart-kbar">
              <Badge tone="primary" dot>{t("sla.latencyChart.badge.p50")}</Badge>
              <Badge tone="info" dot>{t("sla.latencyChart.badge.p95")}</Badge>
              <Badge tone="warning" dot>{t("sla.latencyChart.badge.p99")}</Badge>
            </div>
          }
        >
          <LatencyChart />
          <BackendGapBanner reason={t("sla.banner.latencyChart24h")} />
        </Card>
        <SLOStatusCard data={data ?? null} />
      </div>

      {/* ── §5 + §6 .grid-main row 2 (verbatim from page-admin.jsx:103-153) ──
          TopSlowOpsTable LEFT + ErrorRateByServiceCard RIGHT. */}
      <div style={layoutStyles.gridMainRow2}>
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
