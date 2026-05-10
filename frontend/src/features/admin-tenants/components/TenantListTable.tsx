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
 *   Mirrors inline-style pattern from 57.3 TenantSettingsView (no Tailwind).
 *
 *   Sprint 57.9 US-6 Day 4: items + loading now sourced from useAdminTenants
 *   TanStack hook (was store.items + store.loading); reset still calls
 *   store.reset (TanStack auto-refetches via queryKey change).
 *
 * Created: 2026-05-07 (Sprint 57.4 Day 3)
 * Last Modified: 2026-05-09
 *
 * Modification History (newest-first):
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
import { useAdminTenants } from "../hooks/useAdminTenants";
import { useAdminTenantsStore } from "../store/adminTenantsStore";
import { TenantPlan, TenantState, type TenantListItem } from "../types";

function stateBadgeColor(state: TenantState): string {
  switch (state) {
    case TenantState.ACTIVE:
      return "#0a0";
    case TenantState.PROVISIONING:
    case TenantState.REQUESTED:
      return "#a80";
    case TenantState.SUSPENDED:
    case TenantState.ARCHIVED:
      return "#888";
    default:
      return "#666";
  }
}

function planBadgeColor(plan: TenantPlan): string {
  return plan === TenantPlan.ENTERPRISE ? "#06c" : "#888";
}

const BADGE_STYLE: React.CSSProperties = {
  padding: "0.15rem 0.5rem",
  borderRadius: "0.25rem",
  color: "white",
  fontSize: "0.85rem",
  whiteSpace: "nowrap",
};

const TH_STYLE: React.CSSProperties = {
  textAlign: "left",
  borderBottom: "2px solid #ccc",
  padding: "0.5rem",
  fontWeight: 600,
};

const TD_STYLE: React.CSSProperties = {
  borderBottom: "1px solid #eee",
  padding: "0.5rem",
};

interface RowProps {
  tenant: TenantListItem;
  onView: (id: string) => void;
}

function TenantRow({ tenant, onView }: RowProps): JSX.Element {
  return (
    <tr>
      <td style={{ ...TD_STYLE, fontFamily: "monospace" }}>{tenant.code}</td>
      <td style={TD_STYLE}>{tenant.display_name}</td>
      <td style={TD_STYLE}>
        <span style={{ ...BADGE_STYLE, background: stateBadgeColor(tenant.state) }}>
          {tenant.state}
        </span>
      </td>
      <td style={TD_STYLE}>
        <span style={{ ...BADGE_STYLE, background: planBadgeColor(tenant.plan) }}>
          {tenant.plan}
        </span>
      </td>
      <td style={{ ...TD_STYLE, fontSize: "0.85rem", color: "#666" }}>
        {tenant.created_at}
      </td>
      <td style={TD_STYLE}>
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
    <table style={{ width: "100%", borderCollapse: "collapse", marginTop: "0.5rem" }}>
      <thead>
        <tr>
          <th style={TH_STYLE}>Code</th>
          <th style={TH_STYLE}>Display Name</th>
          <th style={TH_STYLE}>State</th>
          <th style={TH_STYLE}>Plan</th>
          <th style={TH_STYLE}>Created</th>
          <th style={TH_STYLE}>Action</th>
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
