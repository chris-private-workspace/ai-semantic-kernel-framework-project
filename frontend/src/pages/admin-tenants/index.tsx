/**
 * File: frontend/src/pages/admin-tenants/index.tsx
 * Purpose: Admin Tenants Console page — auth gate + platform-admin role gate + mockup-fidelity view.
 * Category: Frontend / pages / admin-tenants
 * Scope: Phase 57 / Sprint 57.43 Day 1 (full mockup-fidelity rebuild)
 *
 * Description:
 *   GET /api/v1/admin/tenants is platform-admin-only (no tenant scope).
 *   Sprint 57.43 Day 1 rebuilds the body verbatim from mockup `page-admin.jsx`
 *   L334-409 — replaces the prior TenantListFilters/Table/Pagination triad
 *   (which used shadcn-utility tokens diverging from mockup fidelity) with
 *   the AdminTenantsView container (3 verbatim-port subcomponents driven by
 *   _fixtures.ts per D-DAY0-6 Option A). useAdminTenants hook unmounted in
 *   this rebuild; backend wire deferred Phase 58+ via AP-2 BackendGapBanner.
 *
 * Modification History (newest-first):
 *   - 2026-05-25: Sprint 57.43 Day 1 — full mockup-fidelity rebuild (AdminTenantsView replaces filters/table/pagination triad)
 *   - 2026-05-10: Sprint 57.13 US-A2 — <RequireAuth> + platform-admin role gate (AdminTenantsContent split)
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — error+refetch from useAdminTenants hook (drop store loadData)
 *   - 2026-05-10: Sprint 57.8 US-4 — page-level AppShellV2 wrap; remove inline padding
 *
 * Created: 2026-05-07 (Sprint 57.4 Day 3)
 */

import { AppShellV2 } from "../../components/AppShellV2";
import { Card } from "../../components/mockup-ui";
import { AdminTenantsView } from "../../features/admin-tenants/components/AdminTenantsView";
import { RequireAuth } from "../../features/auth/components/RequireAuth";
import { useAuthStore } from "../../features/auth/store/authStore";

// Mirrors backend _ADMIN_PLATFORM_ROLES (platform_layer/identity/auth.py).
const PLATFORM_ADMIN_ROLES = ["admin", "platform_admin"];

export function AdminTenantsPage(): JSX.Element {
  const roles = useAuthStore((s) => s.roles);
  const isPlatformAdmin = roles.some((r) => PLATFORM_ADMIN_ROLES.includes(r));

  return (
    <RequireAuth>
      <AppShellV2 pageTitle="Admin Tenants Console">
        {isPlatformAdmin ? (
          <AdminTenantsView />
        ) : (
          <Card title="需要平台管理員權限">
            <div className="subtle">
              你的帳號沒有平台管理員（platform admin）角色，因此無法檢視所有租戶。
              如需存取，請聯絡平台管理員。
            </div>
          </Card>
        )}
      </AppShellV2>
    </RequireAuth>
  );
}

export default AdminTenantsPage;
