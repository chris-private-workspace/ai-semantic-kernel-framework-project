/**
 * File: frontend/src/pages/tenant-settings/index.tsx
 * Purpose: Tenant Settings page wrapper — wildcard route per 57.1 v2 cost-dashboard pattern.
 * Category: Frontend / pages / tenant-settings
 * Scope: Phase 57 / Sprint 57.3 US-5
 *
 * Created: 2026-05-07 (Sprint 57.3 Day 3)
 * Last Modified: 2026-05-07
 *
 * Modification History:
 *   - 2026-05-07: Initial creation (Sprint 57.3 Day 3 / US-5 — Tenant Settings page wrapper)
 */

import { Route, Routes } from "react-router-dom";

import { TenantSettingsView } from "../../features/tenant-settings/components/TenantSettingsView";

export default function TenantSettingsPage() {
  return (
    <Routes>
      <Route index element={<TenantSettingsView />} />
    </Routes>
  );
}
