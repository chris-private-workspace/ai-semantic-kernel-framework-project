/**
 * File: frontend/src/pages/admin-tenants/index.tsx
 * Purpose: Admin Tenants Console page (filters + table + pagination).
 * Category: Frontend / pages / admin-tenants
 * Scope: Phase 57 / Sprint 57.4 US-4
 *
 * Description:
 *   Loads on mount + on store query change. URL query string sync deferred
 *   per AP-6 (will land alongside multi-page filter shareability when a
 *   real need surfaces; this sprint ships in-memory filter state only).
 *
 *   Backend enforces require_admin_platform_role; frontend lets 401/403
 *   surface as Error UX (Home Link always visible per 57.1 D10 Option C).
 *
 * Created: 2026-05-07 (Sprint 57.4 Day 3)
 */

import { useEffect } from "react";

import { TenantListFilters } from "../../features/admin-tenants/components/TenantListFilters";
import { TenantListPagination } from "../../features/admin-tenants/components/TenantListPagination";
import { TenantListTable } from "../../features/admin-tenants/components/TenantListTable";
import { useAdminTenantsStore } from "../../features/admin-tenants/store/adminTenantsStore";

export function AdminTenantsPage(): JSX.Element {
  const { error, loadData } = useAdminTenantsStore();

  useEffect(() => {
    void loadData();
  }, [loadData]);

  return (
    <div style={{ padding: "2rem", fontFamily: "system-ui, sans-serif" }}>
      <h1>Admin Tenants Console</h1>
      <p style={{ color: "#666", fontSize: "0.9rem" }}>
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
          <p>Error: {error}</p>
          <button onClick={() => void loadData()}>Retry</button>
        </div>
      )}

      <TenantListTable />
      <TenantListPagination />
    </div>
  );
}

export default AdminTenantsPage;
