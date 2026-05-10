/**
 * File: frontend/src/pages/cost-dashboard/index.tsx
 * Purpose: Cost Dashboard page — wraps Routes in AppShellV2 (page-level layout per Day 0 A1).
 * Category: Frontend / pages / cost-dashboard
 * Scope: Phase 57 / Sprint 57.1 US-2 → 57.8 US-4 → Sprint 57.9 US-6 Day 4 (loading source migrated)
 *
 * Modification History (newest-first):
 *   - 2026-05-10: Sprint 57.13 US-A2 — wrap in <RequireAuth> (was ungated)
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — MonthPickerSlot consumes useIsFetching for loading state (store no longer holds loading)
 *   - 2026-05-10: Sprint 57.8 US-4 — page-level AppShellV2 wrap + MonthPickerSlot hoist
 *   - 2026-05-06: Initial creation (Sprint 57.1 Day 1 / US-2)
 */

import { useIsFetching } from "@tanstack/react-query";
import type { FC } from "react";
import { Route, Routes } from "react-router-dom";

import { AppShellV2 } from "../../components/AppShellV2";
import { RequireAuth } from "../../features/auth/components/RequireAuth";
import { CostOverview } from "../../features/cost-dashboard/components/CostOverview";
import { MonthPicker } from "../../features/cost-dashboard/components/MonthPicker";
import { COST_SUMMARY_QUERY_KEY_BASE } from "../../features/cost-dashboard/hooks/useCostSummary";
import { useCostStore } from "../../features/cost-dashboard/store/costStore";

const MonthPickerSlot: FC = () => {
  const currentMonth = useCostStore((s) => s.currentMonth);
  const setMonth = useCostStore((s) => s.setMonth);
  const fetchingCount = useIsFetching({ queryKey: COST_SUMMARY_QUERY_KEY_BASE });
  return <MonthPicker value={currentMonth} onChange={setMonth} disabled={fetchingCount > 0} />;
};

export default function CostDashboardPage() {
  return (
    <RequireAuth>
      <AppShellV2 pageTitle="Cost Dashboard" headerActions={<MonthPickerSlot />}>
        <Routes>
          <Route index element={<CostOverview />} />
        </Routes>
      </AppShellV2>
    </RequireAuth>
  );
}
