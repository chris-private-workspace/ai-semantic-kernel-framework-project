/**
 * File: frontend/src/features/sla-dashboard/store/slaStore.ts
 * Purpose: Zustand store for SLA Dashboard UI-only state (current month selection).
 * Category: Frontend / sla-dashboard / store
 * Scope: Phase 57 / Sprint 57.1 US-3 → Sprint 57.9 US-6 Day 4 (UI-only reduction)
 *
 * Description:
 *   Sprint 57.9 US-6 Day 4: reduced from full data orchestration to UI-only
 *   state (currentMonth + setMonth + reset). Server cache moved to
 *   `useSLAReport` TanStack Query hook (mirror cost-dashboard reduction).
 *
 * Created: 2026-05-06 (Sprint 57.1 Day 2)
 * Last Modified: 2026-05-09
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — reduce to UI-only (drop loadData/data/loading/error)
 *   - 2026-05-06: Initial creation (Sprint 57.1 Day 2 / US-3)
 *
 * Related:
 *   - ../hooks/useSLAReport.ts (server cache post-migration)
 */

import { create } from "zustand";

function defaultMonth(): string {
  return new Date().toISOString().substring(0, 7);
}

interface SLAState {
  currentMonth: string;
  setMonth: (month: string) => void;
  reset: () => void;
}

export const useSLAStore = create<SLAState>((set) => ({
  currentMonth: defaultMonth(),
  setMonth: (month) => set({ currentMonth: month }),
  reset: () => set({ currentMonth: defaultMonth() }),
}));
