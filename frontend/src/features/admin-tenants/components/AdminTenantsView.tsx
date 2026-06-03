/**
 * File: frontend/src/features/admin-tenants/components/AdminTenantsView.tsx
 * Purpose: Container mounting page header + stats strip + tenants table + Members drawer (Sprint 57.49).
 * Category: Frontend / admin-tenants / components
 * Scope: Phase 57 / Sprint 57.43 Day 1 + Sprint 57.49 Day 1 (Track B drawer mount)
 *
 * Description:
 *   Mounts TenantsPageHeader + TenantsStatsStrip + TenantsTable inside a single
 *   `<div>` matching mockup `page-admin.jsx` L334-409 TenantsPage outer wrapper.
 *
 *   Sprint 57.49 Track B addition: hosts `selectedTenantId` state + mounts
 *   `<TenantMembersDrawer>` overlay. Clicking a row in TenantsTable opens the
 *   drawer for that tenant; clicking the backdrop / Close button / pressing
 *   Escape sets selectedTenantId back to `null` (drawer unmounts).
 *
 * Key Components:
 *   - AdminTenantsView: page-level container w/ drawer state
 *
 * Created: 2026-05-25 (Sprint 57.43 Day 1)
 * Last Modified: 2026-06-03
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Sprint 57.74 — mount useAdminTenantsStats + thread fleet to strip + per-tenant map to table (A-6a stats wiring)
 *   - 2026-06-03: Sprint 57.73 — mount useAdminTenants + thread data/isLoading/isError/refetch to TenantsTable (A-6a real-data wiring)
 *   - 2026-05-26: Sprint 57.49 — add selectedTenantId state + TenantMembersDrawer mount (Track B)
 *   - 2026-05-25: Initial creation (Sprint 57.43 Day 1) — admin-tenants full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx L334-409 TenantsPage
 *   - ../hooks/useAdminTenants.ts (TanStack Query — real GET /api/v1/admin/tenants)
 *   - ../hooks/useAdminTenantsStats.ts (TanStack Query — real GET /api/v1/admin/tenants/stats)
 *   - ./{TenantsPageHeader,TenantsStatsStrip,TenantsTable,TenantMembersDrawer}.tsx
 */

import { useMemo, useState } from "react";

import { useAdminTenants } from "../hooks/useAdminTenants";
import { useAdminTenantsStats } from "../hooks/useAdminTenantsStats";
import { TenantMembersDrawer } from "./TenantMembersDrawer";
import { TenantsPageHeader } from "./TenantsPageHeader";
import { TenantsStatsStrip } from "./TenantsStatsStrip";
import { TenantsTable } from "./TenantsTable";

export function AdminTenantsView(): JSX.Element {
  const [selectedTenantId, setSelectedTenantId] = useState<string | null>(null);
  const { data, isLoading, isError, refetch } = useAdminTenants();
  const {
    data: stats,
    isLoading: statsLoading,
    isError: statsError,
  } = useAdminTenantsStats();

  // Reduce the per-tenant array into a lookup keyed by tenant id so the table
  // can resolve each row's agents/runs24 in O(1).
  const statsByTenant = useMemo(
    () =>
      (stats?.per_tenant ?? []).reduce<
        Record<string, { agents: number; runs24: number }>
      >((acc, s) => {
        acc[s.tenant_id] = { agents: s.agents, runs24: s.runs24 };
        return acc;
      }, {}),
    [stats?.per_tenant],
  );

  return (
    <div>
      <TenantsPageHeader />
      <TenantsStatsStrip
        fleet={stats?.fleet}
        isLoading={statsLoading}
        isError={statsError}
      />
      <TenantsTable
        tenants={data?.items ?? []}
        statsByTenant={statsByTenant}
        isLoading={isLoading}
        isError={isError}
        onRetry={() => void refetch()}
        onRowClick={setSelectedTenantId}
      />
      <TenantMembersDrawer
        tenantId={selectedTenantId}
        onClose={() => setSelectedTenantId(null)}
      />
    </div>
  );
}
