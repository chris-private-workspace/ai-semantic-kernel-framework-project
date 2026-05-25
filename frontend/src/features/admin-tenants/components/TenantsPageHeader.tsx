/**
 * File: frontend/src/features/admin-tenants/components/TenantsPageHeader.tsx
 * Purpose: Verbatim port of admin tenants page header (title + sub + 2 actions).
 * Category: Frontend / admin-tenants / components
 * Scope: Phase 57 / Sprint 57.43 Day 1 (mockup-fidelity rebuild)
 *
 * Description:
 *   Verbatim port of mockup `page-admin.jsx` L336-348 — title "Tenants" + sub
 *   line with route-pill + 2 action buttons (Export outline+download icon /
 *   New tenant primary+plus icon). Both actions are AP-2 stubs (window.alert)
 *   pending backend endpoint implementation Phase 58+.
 *
 * Key Components:
 *   - TenantsPageHeader: stateless visual header component
 *
 * Created: 2026-05-25 (Sprint 57.43 Day 1)
 * Last Modified: 2026-05-25
 *
 * Modification History (newest-first):
 *   - 2026-05-25: Initial creation (Sprint 57.43 Day 1) — admin-tenants full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx L336-348
 *   - frontend/src/components/mockup-ui.tsx (Button primitive)
 */

import { Button } from "../../../components/mockup-ui";

export function TenantsPageHeader(): JSX.Element {
  const handleExport = (): void => {
    window.alert("Export: backend gap (Phase 58+) — admin tenant export endpoint pending");
  };
  const handleNewTenant = (): void => {
    window.alert("New tenant: backend gap (Phase 58+) — admin tenant create endpoint pending");
  };

  return (
    <div className="page-head">
      <div>
        <div className="page-title">Tenants</div>
        <div className="page-sub">
          Multi-tenant lifecycle · RLS-isolated · feature flags + quotas per tenant
          <span className="route-pill">/admin/tenants</span>
        </div>
      </div>
      <div className="page-actions">
        <Button variant="outline" size="sm" icon="download" onClick={handleExport}>
          Export
        </Button>
        <Button variant="primary" size="sm" icon="plus" onClick={handleNewTenant}>
          New tenant
        </Button>
      </div>
    </div>
  );
}
