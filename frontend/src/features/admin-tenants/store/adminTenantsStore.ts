/**
 * File: frontend/src/features/admin-tenants/store/adminTenantsStore.ts
 * Purpose: Zustand store for Admin Tenants Console list state (filters + pagination + items).
 * Category: Frontend / admin-tenants / store
 * Scope: Phase 57 / Sprint 57.4 US-2
 *
 * Description:
 *   Mirrors 57.3 tenantSettingsStore Zustand pattern. State holds:
 *     - query  TenantListQuery with state/plan/search filters + limit+offset
 *     - items  current page TenantListItem[] from server
 *     - total  total count for pagination indicator
 *     - loading/error  fetch lifecycle flags
 *
 *   Action setFilter resets offset to 0 (filter change should restart
 *   pagination); setPagination changes limit/offset only.
 *
 * Created: 2026-05-07 (Sprint 57.4 Day 2)
 *
 * Related:
 *   - ../services/adminTenantsService.ts (listTenants)
 *   - ../types.ts (TenantListQuery + TenantListItem)
 *   - ../../tenant-settings/store/tenantSettingsStore.ts (pattern reference)
 */

import { create } from "zustand";

import { listTenants } from "../services/adminTenantsService";
import type {
  TenantListItem,
  TenantListQuery,
  TenantPlan,
  TenantState,
} from "../types";

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
  items: TenantListItem[];
  total: number;
  loading: boolean;
  error: string | null;
  setFilter: (partial: FilterPartial) => void;
  setPagination: (partial: PaginationPartial) => void;
  loadData: () => Promise<void>;
  reset: () => void;
}

export const useAdminTenantsStore = create<AdminTenantsState>((set, get) => ({
  query: { ...DEFAULT_QUERY },
  items: [],
  total: 0,
  loading: false,
  error: null,
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
  loadData: async () => {
    set({ loading: true, error: null });
    try {
      const data = await listTenants(get().query);
      set({ items: data.items, total: data.total, loading: false });
    } catch (err) {
      set({ error: (err as Error).message, loading: false, items: [], total: 0 });
    }
  },
  reset: () =>
    set({
      query: { ...DEFAULT_QUERY },
      items: [],
      total: 0,
      loading: false,
      error: null,
    }),
}));
