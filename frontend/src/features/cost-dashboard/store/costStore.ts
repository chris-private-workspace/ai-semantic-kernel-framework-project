/**
 * File: frontend/src/features/cost-dashboard/store/costStore.ts
 * Purpose: Zustand store for Cost Dashboard UI-only state (current month selection).
 * Category: Frontend / cost-dashboard / store
 * Scope: Phase 57 / Sprint 57.1 US-2 → Sprint 57.9 US-6 Day 4 (UI-only reduction)
 *
 * Description:
 *   Sprint 57.9 US-6 Day 4: reduced from full data orchestration (loadData /
 *   data / loading / error) to UI-only state (currentMonth + setMonth + reset).
 *   Server cache moved to `useCostSummary` TanStack Query hook (closes
 *   AD-Cost-Dashboard-UseQuery from Sprint 57.7). This separation lets the
 *   page-level MonthPickerSlot stay un-changed while CostOverview consumes
 *   the hook directly for data/loading/error.
 *
 * Created: 2026-05-06 (Sprint 57.1 Day 1)
 * Last Modified: 2026-05-09
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — reduce to UI-only (drop loadData/data/loading/error)
 *   - 2026-05-06: Initial creation (Sprint 57.1 Day 1 / US-2 — Cost Dashboard store)
 *
 * Related:
 *   - ../hooks/useCostSummary.ts (server cache post-migration)
 *   - frontend/src/features/governance/components/ApprovalsPage.tsx (Day 2 reduction precedent)
 */

import { create } from "zustand";

function defaultMonth(): string {
  return new Date().toISOString().substring(0, 7);
}

interface CostState {
  currentMonth: string;
  setMonth: (month: string) => void;
  reset: () => void;
}

export const useCostStore = create<CostState>((set) => ({
  currentMonth: defaultMonth(),
  setMonth: (month) => set({ currentMonth: month }),
  reset: () => set({ currentMonth: defaultMonth() }),
}));
