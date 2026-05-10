/**
 * File: frontend/src/features/cost-dashboard/components/CostOverview.tsx
 * Purpose: Cost Dashboard top-level container — TanStack-driven cost summary view.
 * Category: Frontend / cost-dashboard / components
 * Scope: Phase 57 / Sprint 57.1 US-2 (initial) → Sprint 57.7 US-B3 (AppShell + Tailwind) → Sprint 57.9 US-6 Day 4 (TanStack)
 *
 * Description:
 *   Sprint 57.9 US-6 Day 4: replaced manual useEffect + loadData orchestration
 *   with `useCostSummary` TanStack Query hook (closes AD-Cost-Dashboard-UseQuery).
 *   Sprint 57.13 US-A2: tenant_id now comes from the authenticated session
 *   (authStore.tenant.id) — the page is wrapped in <RequireAuth> so tenant is
 *   always set; backend (US-A3) lets a user see their own tenant's data.
 *   currentMonth comes from useCostStore (UI-only state).
 *
 * Created: 2026-05-06 (Sprint 57.1 Day 1)
 * Last Modified: 2026-05-10
 *
 * Modification History (newest-first):
 *   - 2026-05-10: Sprint 57.13 US-A2 — tenant_id from authStore.tenant.id (was URL ?tenant_id=)
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — migrate to useCostSummary TanStack hook (drop store loadData/data/loading/error)
 *   - 2026-05-10: Sprint 57.7 US-B3 — migrate to AppShell + Tailwind utility classes
 *   - 2026-05-06: Initial creation (Sprint 57.1 Day 1 / US-2 — Cost overview)
 */

import { useAuthStore } from "../../auth/store/authStore";
import { useCostSummary } from "../hooks/useCostSummary";
import { useCostStore } from "../store/costStore";
import { CostBreakdownTable } from "./CostBreakdownTable";

export function CostOverview() {
  const tenantId = useAuthStore((s) => s.tenant?.id ?? "");
  const currentMonth = useCostStore((s) => s.currentMonth);

  const { data, isLoading, error, refetch } = useCostSummary(tenantId, currentMonth);

  return (
    <div className="space-y-4">
      <header>
        <p className="text-sm text-muted-foreground">
          Cost ledger summary for your tenant.
        </p>
      </header>

      {!tenantId && (
        <p className="text-sm text-destructive">No tenant in your session.</p>
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
