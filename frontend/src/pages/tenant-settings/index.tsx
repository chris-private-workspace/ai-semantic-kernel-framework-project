/**
 * File: frontend/src/pages/tenant-settings/index.tsx
 * Purpose: Tenant Settings page — wraps Routes in AppShellV2 (page-level layout per Day 0 A1).
 * Category: Frontend / pages / tenant-settings
 * Scope: Phase 57 / Sprint 57.3 US-5 → 57.8 US-4 (page-level AppShellV2 migration)
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.13 US-A2 — wrap in <RequireAuth> (was ungated)
 *   - 2026-05-10: Sprint 57.8 US-4 — page-level AppShellV2 wrap
 *   - 2026-05-07: Initial creation (Sprint 57.3 Day 3 / US-5 — Tenant Settings page wrapper)
 */

import { Route, Routes } from "react-router-dom";

import { AppShellV2 } from "../../components/AppShellV2";
import { RequireAuth } from "../../features/auth/components/RequireAuth";
import { TenantSettingsView } from "../../features/tenant-settings/components/TenantSettingsView";

export default function TenantSettingsPage() {
  return (
    <RequireAuth>
      <AppShellV2 pageTitle="Tenant Settings">
        <Routes>
          <Route index element={<TenantSettingsView />} />
        </Routes>
      </AppShellV2>
    </RequireAuth>
  );
}
