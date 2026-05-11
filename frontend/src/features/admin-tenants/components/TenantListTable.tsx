/**
 * File: frontend/src/features/admin-tenants/components/TenantListTable.tsx
 * Purpose: Read-only table of tenants — Sprint 57.4 US-3.
 * Category: Frontend / admin-tenants / components
 * Scope: Phase 57 / Sprint 57.4 US-3
 *
 * Description:
 *   Renders TenantListItem[] from store as a table:
 *     Code | Display Name | State (badge) | Plan (badge) | Created | View
 *   View button navigates to /tenant-settings/?tenant_id={id} (consumes 57.3
 *   Tenant Settings page). Loading skeleton (5 placeholder rows) and empty
 *   state (with Reset Filters button) are rendered conditionally based on
 *   store flags.
 *
 *   Sprint 57.9 US-6 Day 4: items + loading now sourced from useAdminTenants
 *   TanStack hook (was store.items + store.loading); reset still calls
 *   store.reset (TanStack auto-refetches via queryKey change).
 *
 * Created: 2026-05-07 (Sprint 57.4 Day 3)
 * Last Modified: 2026-05-11
 *
 * Modification History (newest-first):
 *   - 2026-05-11: Sprint 57.15 — inline styles → Tailwind utility classes; badge colours via semantic tokens (AD-Inline-Style-Cleanup-Sweep)
 *   - 2026-05-10: Sprint 57.13 US-B2 — loading/empty now use components/ui (TableSkeleton/EmptyState/Button)
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — items+loading from useAdminTenants hook
 *   - 2026-05-07: Initial creation (Sprint 57.4 Day 3)
 *
 * Related:
 *   - ../hooks/useAdminTenants.ts (server cache post-migration)
 *   - ../store/adminTenantsStore.ts (UI-only query state post-migration)
 *   - ../types.ts (TenantState + TenantPlan badge color helpers)
 *   - ../../../components/ui (TableSkeleton / EmptyState / Button)
 */

import { useNavigate } from "react-router-dom";

import { Button, EmptyState, TableSkeleton } from "../../../components/ui";
import { cn } from "../../../lib/utils";
import { useAdminTenants } from "../hooks/useAdminTenants";
import { useAdminTenantsStore } from "../store/adminTenantsStore";
import { TenantPlan, TenantState, type TenantListItem } from "../types";

function stateBadgeClass(state: TenantState): string {
  switch (state) {
    case TenantState.ACTIVE:
      return "bg-success";
    case TenantState.PROVISIONING:
    case TenantState.REQUESTED:
      return "bg-warning";
    case TenantState.SUSPENDED:
    case TenantState.ARCHIVED:
    default:
      return "bg-muted-foreground";
  }
}

function planBadgeClass(plan: TenantPlan): string {
  return plan === TenantPlan.ENTERPRISE ? "bg-primary" : "bg-muted-foreground";
}

const BADGE_CLASS = "rounded px-2 py-0.5 text-sm whitespace-nowrap text-white";
const TH_CLASS = "border-b-2 border-border p-2 text-left font-semibold";
const TD_CLASS = "border-b border-border p-2";

interface RowProps {
  tenant: TenantListItem;
  onView: (id: string) => void;
}

function TenantRow({ tenant, onView }: RowProps): JSX.Element {
  return (
    <tr>
      <td className={cn(TD_CLASS, "font-mono")}>{tenant.code}</td>
      <td className={TD_CLASS}>{tenant.display_name}</td>
      <td className={TD_CLASS}>
        <span className={cn(BADGE_CLASS, stateBadgeClass(tenant.state))}>{tenant.state}</span>
      </td>
      <td className={TD_CLASS}>
        <span className={cn(BADGE_CLASS, planBadgeClass(tenant.plan))}>{tenant.plan}</span>
      </td>
      <td className={cn(TD_CLASS, "text-sm text-muted-foreground")}>{tenant.created_at}</td>
      <td className={TD_CLASS}>
        <button onClick={() => onView(tenant.id)}>View</button>
      </td>
    </tr>
  );
}

export function TenantListTable(): JSX.Element {
  const navigate = useNavigate();
  const reset = useAdminTenantsStore((s) => s.reset);
  const { data, isLoading } = useAdminTenants();
  const items = data?.items ?? [];

  const handleView = (id: string): void => {
    navigate(`/tenant-settings/?tenant_id=${encodeURIComponent(id)}`);
  };

  const handleReset = (): void => {
    reset();
    // TanStack auto-refetches via queryKey change after store.reset
  };

  if (isLoading) {
    return (
      <div role="status" aria-label="Loading tenants" className="p-4">
        <TableSkeleton rows={5} cols={6} />
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <EmptyState
        title="No tenants match current filter."
        action={
          <Button variant="outline" onClick={handleReset}>
            Reset Filters
          </Button>
        }
      />
    );
  }

  return (
    <table className="mt-2 w-full border-collapse">
      <thead>
        <tr>
          <th className={TH_CLASS}>Code</th>
          <th className={TH_CLASS}>Display Name</th>
          <th className={TH_CLASS}>State</th>
          <th className={TH_CLASS}>Plan</th>
          <th className={TH_CLASS}>Created</th>
          <th className={TH_CLASS}>Action</th>
        </tr>
      </thead>
      <tbody>
        {items.map((t) => (
          <TenantRow key={t.id} tenant={t} onView={handleView} />
        ))}
      </tbody>
    </table>
  );
}
