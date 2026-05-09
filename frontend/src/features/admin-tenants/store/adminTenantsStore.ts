/**
 * File: frontend/src/features/admin-tenants/store/adminTenantsStore.ts
 * Purpose: Zustand store for Admin Tenants Console UI-only state (filter + pagination query).
 * Category: Frontend / admin-tenants / store
 * Scope: Phase 57 / Sprint 57.4 US-2 → Sprint 57.9 US-6 Day 4 (UI-only reduction)
 *
 * Description:
 *   Sprint 57.9 US-6 Day 4: reduced from full data orchestration (loadData /
 *   items / total / loading / error) to UI-only filter+pagination query.
 *   Server cache moved to `useAdminTenants` TanStack Query hook (mirror
 *   cost-dashboard / sla-dashboard reduction).
 *
 *   Action setFilter still resets offset to 0 (filter change should restart
 *   pagination); setPagination changes limit/offset only.
 *
 * Created: 2026-05-07 (Sprint 57.4 Day 2)
 * Last Modified: 2026-05-09
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — reduce to UI-only (drop loadData/items/total/loading/error)
 *   - 2026-05-07: Initial creation (Sprint 57.4 Day 2)
 *
 * Related:
 *   - ../hooks/useAdminTenants.ts (server cache post-migration)
 *   - ../types.ts (TenantListQuery)
 */

import { create } from "zustand";

import type { TenantListQuery, TenantPlan, TenantState } from "../types";

const DEFAULT_QUERY: TenantListQuery = {
  state: undefined,
  plan: undefined,
  search: undefined,
  limit: 50,
  offset: 0,
};

interface FilterPartial {
  state?: TenantState;
  plan?: TenantPlan;
  search?: string;
}

interface PaginationPartial {
  limit?: number;
  offset?: number;
}

interface AdminTenantsState {
  query: TenantListQuery;
  setFilter: (partial: FilterPartial) => void;
  setPagination: (partial: PaginationPartial) => void;
  reset: () => void;
}

export const useAdminTenantsStore = create<AdminTenantsState>((set) => ({
  query: { ...DEFAULT_QUERY },
  setFilter: (partial) =>
    set((s) => ({
      query: {
        ...s.query,
        ...partial,
        offset: 0, // filter change resets pagination
      },
    })),
  setPagination: (partial) =>
    set((s) => ({
      query: { ...s.query, ...partial },
    })),
  reset: () =>
    set({
      query: { ...DEFAULT_QUERY },
    }),
}));
