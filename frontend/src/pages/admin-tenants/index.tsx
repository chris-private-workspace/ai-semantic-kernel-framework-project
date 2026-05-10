/**
 * File: frontend/src/pages/admin-tenants/index.tsx
 * Purpose: Admin Tenants Console page — auth gate + platform-admin role gate + filters/table/pagination.
 * Category: Frontend / pages / admin-tenants
 * Scope: Phase 57 / Sprint 57.4 US-4 → 57.8 US-4 → 57.9 US-6 → Sprint 57.13 US-A2 (auth + role gate)
 *
 * Description:
 *   GET /api/v1/admin/tenants is platform-admin-only (no tenant scope).
 *   Sprint 57.13 US-A2: wrap in <RequireAuth> and, when the authenticated
 *   user lacks a platform-admin role, render a "needs permission" notice
 *   instead of mounting the data hook (which would just 403). The data
 *   children live in <AdminTenantsContent> so their hooks only run when
 *   the role check passes.
 *
 * Modification History (newest-first):
 *   - 2026-05-10: Sprint 57.13 US-A2 — <RequireAuth> + platform-admin role gate (AdminTenantsContent split)
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
import { RequireAuth } from "../../features/auth/components/RequireAuth";
import { useAuthStore } from "../../features/auth/store/authStore";

// Mirrors backend _ADMIN_PLATFORM_ROLES (platform_layer/identity/auth.py).
const PLATFORM_ADMIN_ROLES = ["admin", "platform_admin"];

function AdminTenantsContent(): JSX.Element {
  const { error, refetch } = useAdminTenants();
  return (
    <>
      <p className="mb-4 text-sm text-muted-foreground">
        Browse + filter all tenants (platform-admin scope).
      </p>
      <TenantListFilters />
      {error && (
        <div className="mt-4 rounded-md border border-destructive/40 p-4 text-sm text-destructive">
          <p>Error: {error.message}</p>
          <button
            type="button"
            onClick={() => void refetch()}
            className="mt-2 rounded border border-destructive/40 px-2 py-1"
          >
            Retry
          </button>
        </div>
      )}
      <TenantListTable />
      <TenantListPagination />
    </>
  );
}

export function AdminTenantsPage(): JSX.Element {
  const roles = useAuthStore((s) => s.roles);
  const isPlatformAdmin = roles.some((r) => PLATFORM_ADMIN_ROLES.includes(r));

  return (
    <RequireAuth>
      <AppShellV2 pageTitle="Admin Tenants Console">
        {isPlatformAdmin ? (
          <AdminTenantsContent />
        ) : (
          <div className="rounded-md border border-border bg-muted/30 p-6 text-sm text-muted-foreground">
            <p className="font-medium text-foreground">需要平台管理員權限</p>
            <p className="mt-1">
              你的帳號沒有平台管理員（platform admin）角色，因此無法檢視所有租戶。
              如需存取，請聯絡平台管理員。
            </p>
          </div>
        )}
      </AppShellV2>
    </RequireAuth>
  );
}

export default AdminTenantsPage;
