/**
 * File: frontend/src/pages/admin-tenants/index.tsx
 * Purpose: Admin Tenants Console page (filters + table + pagination).
 * Category: Frontend / pages / admin-tenants
 * Scope: Phase 57 / Sprint 57.4 US-4 → 57.8 US-4 → Sprint 57.9 US-6 Day 4 (TanStack hook)
 *
 * Description:
 *   Sprint 57.9 US-6 Day 4: error sourced from useAdminTenants TanStack hook;
 *   removed manual `useEffect → loadData()` (TanStack auto-fetches on mount
 *   via queryKey). Children (TenantListFilters / TenantListPagination /
 *   TenantListTable) all consume the hook + store independently.
 *
 *   Backend enforces require_admin_platform_role; frontend lets 401/403
 *   surface as Error UX.
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — error+refetch from useAdminTenants hook (drop store loadData)
 *   - 2026-05-10: Sprint 57.8 US-4 — page-level AppShellV2 wrap; remove inline padding
 *
 * Created: 2026-05-07 (Sprint 57.4 Day 3)
 */

import { AppShellV2 } from "../../components/AppShellV2";
import { TenantListFilters } from "../../features/admin-tenants/components/TenantListFilters";
import { TenantListPagination } from "../../features/admin-tenants/components/TenantListPagination";
import { TenantListTable } from "../../features/admin-tenants/components/TenantListTable";
import { useAdminTenants } from "../../features/admin-tenants/hooks/useAdminTenants";

export function AdminTenantsPage(): JSX.Element {
  const { error, refetch } = useAdminTenants();

  return (
    <AppShellV2 pageTitle="Admin Tenants Console">
      <p className="mb-4 text-sm text-muted-foreground">
        Browse + filter all tenants. Backend enforces admin-platform role
        (Sprint 57.4 list endpoint). 401/403 surfaces as error below.
      </p>

      <TenantListFilters />

      {error && (
        <div
          style={{
            marginTop: "1rem",
            padding: "1rem",
            border: "1px solid #a00",
            color: "#a00",
          }}
        >
          <p>Error: {error.message}</p>
          <button onClick={() => void refetch()}>Retry</button>
        </div>
      )}

      <TenantListTable />
      <TenantListPagination />
    </AppShellV2>
  );
}

export default AdminTenantsPage;
