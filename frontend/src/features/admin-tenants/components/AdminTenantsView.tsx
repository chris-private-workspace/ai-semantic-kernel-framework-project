/**
 * File: frontend/src/features/admin-tenants/components/AdminTenantsView.tsx
 * Purpose: Container mounting the 3 verbatim-port subcomponents of /admin-tenants.
 * Category: Frontend / admin-tenants / components
 * Scope: Phase 57 / Sprint 57.43 Day 1 (mockup-fidelity rebuild)
 *
 * Description:
 *   Mounts TenantsPageHeader + TenantsStatsStrip + TenantsTable inside a single
 *   `<div>` matching mockup `page-admin.jsx` L334-409 TenantsPage outer wrapper.
 *   Stateless (no hooks) per D-DAY0-6 Option A fixture-first decision; backend
 *   wire and useAdminTenants hook re-introduction deferred Phase 58+.
 *
 * Key Components:
 *   - AdminTenantsView: page-level container
 *
 * Created: 2026-05-25 (Sprint 57.43 Day 1)
 * Last Modified: 2026-05-25
 *
 * Modification History (newest-first):
 *   - 2026-05-25: Initial creation (Sprint 57.43 Day 1) — admin-tenants full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx L334-409 TenantsPage
 *   - frontend/src/features/admin-tenants/components/{TenantsPageHeader,TenantsStatsStrip,TenantsTable}.tsx
 */

import { TenantsPageHeader } from "./TenantsPageHeader";
import { TenantsStatsStrip } from "./TenantsStatsStrip";
import { TenantsTable } from "./TenantsTable";

export function AdminTenantsView(): JSX.Element {
  return (
    <div>
      <TenantsPageHeader />
      <TenantsStatsStrip />
      <TenantsTable />
    </div>
  );
}
