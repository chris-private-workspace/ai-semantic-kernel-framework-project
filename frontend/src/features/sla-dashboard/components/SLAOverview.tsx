/**
 * File: frontend/src/features/sla-dashboard/components/SLAOverview.tsx
 * Purpose: SLA Dashboard top-level container — TanStack-driven SLA report view.
 * Category: Frontend / sla-dashboard / components
 * Scope: Phase 57 / Sprint 57.1 US-3 → Sprint 57.9 US-6 Day 4 (TanStack + Tailwind)
 *
 * Description:
 *   Sprint 57.9 US-6 Day 4: replaced manual useEffect + loadData orchestration
 *   with `useSLAReport` TanStack Query hook + dropped inline styles for
 *   Tailwind utilities (mirror governance/cost-dashboard refactor pattern).
 *
 *   Reads tenant_id from URL query (admin-driven per D8). MonthPicker stays
 *   in body (page index doesn't hoist it for sla-dashboard, unlike
 *   cost-dashboard). Threshold fallback to Standard 99.5% (per Day 0 D10 —
 *   frontend has no tenant.plan accessible). Latency thresholds use sensible
 *   defaults.
 *
 * Created: 2026-05-06 (Sprint 57.1 Day 2)
 * Last Modified: 2026-05-09
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — migrate to useSLAReport TanStack hook + Tailwind utilities (drop inline styles)
 *   - 2026-05-06: Initial creation (Sprint 57.1 Day 2 / US-3 — SLA overview)
 */

import { useSearchParams } from "react-router-dom";

import { MonthPicker } from "../../cost-dashboard/components/MonthPicker";
import { useSLAReport } from "../hooks/useSLAReport";
import { useSLAStore } from "../store/slaStore";
import { SLAMetricsCard } from "./SLAMetricsCard";

const AVAILABILITY_THRESHOLD_STANDARD = 99.5;

const API_P99_MAX_MS = 1000;
const LOOP_SIMPLE_P99_MAX_MS = 5000;
const LOOP_MEDIUM_P99_MAX_MS = 30000;
const LOOP_COMPLEX_P99_MAX_MS = 120000;
const HITL_QUEUE_NOTIF_P99_MAX_MS = 60000;

export function SLAOverview() {
  const [searchParams] = useSearchParams();
  const tenantId = searchParams.get("tenant_id") ?? "";
  const currentMonth = useSLAStore((s) => s.currentMonth);
  const setMonth = useSLAStore((s) => s.setMonth);

  const { data, isLoading, isFetching, error, refetch } = useSLAReport(tenantId, currentMonth);

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Per-tenant SLA report. Backend enforces admin-platform role
        (Sprint 56.3 endpoint). Threshold fallback to Standard 99.5%
        availability — Enterprise tier display deferred (Day 0 D — frontend
        has no tenant.plan access).
      </p>

      {!tenantId && (
        <p className="text-sm text-destructive">
          Missing{" "}
          <code className="rounded bg-muted px-1 py-0.5">?tenant_id=...</code>{" "}
          query parameter.
        </p>
      )}

      <div>
        <MonthPicker value={currentMonth} onChange={setMonth} disabled={isFetching} />
      </div>

      {isLoading && tenantId && (
        <p className="text-sm italic text-muted-foreground">Loading SLA report…</p>
      )}

      {error && (
        <div
          role="alert"
          className="rounded-lg border border-destructive/40 bg-destructive/5 p-4"
        >
          <p className="text-sm text-destructive">Error: {error.message}</p>
          <button
            onClick={() => void refetch()}
            className="mt-3 inline-flex items-center rounded-md border border-border bg-background px-3 py-1.5 text-sm font-medium hover:bg-muted"
          >
            Retry
          </button>
        </div>
      )}

      {data && !isLoading && !error && (
        <>
          <div>
            <span
              data-testid="violations-badge"
              className={
                data.violations_count > 0
                  ? "inline-block rounded-full bg-destructive/10 px-3 py-1.5 font-bold text-destructive"
                  : "inline-block rounded-full bg-[#e6f4ea] px-3 py-1.5 font-bold text-[#1a7f37]"
              }
            >
              Violations: {data.violations_count}
            </span>
          </div>

          <div className="flex flex-wrap gap-4">
            <SLAMetricsCard
              label="Availability"
              value={data.availability_pct}
              threshold={AVAILABILITY_THRESHOLD_STANDARD}
              unit="%"
              mode="gte"
            />
            <SLAMetricsCard
              label="API p99"
              value={data.api_p99_ms}
              threshold={API_P99_MAX_MS}
              unit="ms"
              mode="lte"
            />
            <SLAMetricsCard
              label="Loop simple p99"
              value={data.loop_simple_p99_ms}
              threshold={LOOP_SIMPLE_P99_MAX_MS}
              unit="ms"
              mode="lte"
            />
            <SLAMetricsCard
              label="Loop medium p99"
              value={data.loop_medium_p99_ms}
              threshold={LOOP_MEDIUM_P99_MAX_MS}
              unit="ms"
              mode="lte"
            />
            <SLAMetricsCard
              label="Loop complex p99"
              value={data.loop_complex_p99_ms}
              threshold={LOOP_COMPLEX_P99_MAX_MS}
              unit="ms"
              mode="lte"
            />
            <SLAMetricsCard
              label="HITL queue notif p99"
              value={data.hitl_queue_notif_p99_ms}
              threshold={HITL_QUEUE_NOTIF_P99_MAX_MS}
              unit="ms"
              mode="lte"
            />
          </div>
        </>
      )}
    </div>
  );
}
