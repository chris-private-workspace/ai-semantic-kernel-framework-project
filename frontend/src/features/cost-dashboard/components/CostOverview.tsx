/**
 * File: frontend/src/features/cost-dashboard/components/CostOverview.tsx
 * Purpose: Cost Dashboard top-level container — TanStack-driven cost summary view.
 * Category: Frontend / cost-dashboard / components
 * Scope: Phase 57 / Sprint 57.1 US-2 (initial) → Sprint 57.7 US-B3 (AppShell + Tailwind) → Sprint 57.9 US-6 Day 4 (TanStack)
 *
 * Description:
 *   Sprint 57.9 US-6 Day 4: replaced manual useEffect + loadData orchestration
 *   with `useCostSummary` TanStack Query hook (closes AD-Cost-Dashboard-UseQuery).
 *   Reads tenant_id from URL query string `?tenant_id=...` (admin-driven per
 *   D8 — backend enforces require_admin_platform_role); reads currentMonth
 *   from useCostStore (UI-only state).
 *
 *   Drops: useEffect dependency-tracking + setMonth invalidation; TanStack
 *   queryKey [tenantId, month] auto-refetches on either change.
 *
 * Created: 2026-05-06 (Sprint 57.1 Day 1)
 * Last Modified: 2026-05-09
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — migrate to useCostSummary TanStack hook (drop store loadData/data/loading/error)
 *   - 2026-05-10: Sprint 57.7 US-B3 — migrate to AppShell + Tailwind utility classes
 *   - 2026-05-06: Initial creation (Sprint 57.1 Day 1 / US-2 — Cost overview)
 */

import { useSearchParams } from "react-router-dom";

import { useCostSummary } from "../hooks/useCostSummary";
import { useCostStore } from "../store/costStore";
import { CostBreakdownTable } from "./CostBreakdownTable";

export function CostOverview() {
  const [searchParams] = useSearchParams();
  const tenantId = searchParams.get("tenant_id") ?? "";
  const currentMonth = useCostStore((s) => s.currentMonth);

  const { data, isLoading, error, refetch } = useCostSummary(tenantId, currentMonth);

  return (
    <div className="space-y-4">
      <header>
        <p className="text-sm text-muted-foreground">
          Per-tenant cost ledger summary. Backend enforces admin-platform role
          (Sprint 56.3 endpoint). 401/403 surfaces as error below.
        </p>
      </header>

      {!tenantId && (
        <p className="text-sm text-destructive">
          Missing{" "}
          <code className="rounded bg-muted px-1 py-0.5">?tenant_id=...</code>{" "}
          query parameter.
        </p>
      )}

      {isLoading && tenantId && (
        <p className="text-sm italic text-muted-foreground">
          Loading cost summary…
        </p>
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
          <p className="text-lg">
            <strong>Total cost ({data.month}):</strong> ${data.total_cost_usd}
          </p>
          <CostBreakdownTable data={data} />
        </>
      )}
    </div>
  );
}
