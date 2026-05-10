/**
 * File: frontend/src/pages/sla-dashboard/index.tsx
 * Purpose: SLA Dashboard page — wraps Routes in AppShellV2 (page-level layout per Day 0 A1).
 * Category: Frontend / pages / sla-dashboard
 * Scope: Phase 57 / Sprint 57.1 US-3 → 57.8 US-4 (page-level AppShellV2 migration)
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.13 US-A2 — wrap in <RequireAuth> (was ungated)
 *   - 2026-05-10: Sprint 57.8 US-4 — page-level AppShellV2 wrap
 *   - 2026-05-06: Initial creation (Sprint 57.1 Day 2 / US-3)
 */

import { Route, Routes } from "react-router-dom";

import { AppShellV2 } from "../../components/AppShellV2";
import { RequireAuth } from "../../features/auth/components/RequireAuth";
import { SLAOverview } from "../../features/sla-dashboard/components/SLAOverview";

export default function SLADashboardPage() {
  return (
    <RequireAuth>
      <AppShellV2 pageTitle="SLA Dashboard">
        <Routes>
          <Route index element={<SLAOverview />} />
        </Routes>
      </AppShellV2>
    </RequireAuth>
  );
}
