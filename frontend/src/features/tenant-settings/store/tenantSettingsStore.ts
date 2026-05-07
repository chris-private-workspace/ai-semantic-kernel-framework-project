/**
 * File: frontend/src/features/tenant-settings/store/tenantSettingsStore.ts
 * Purpose: Zustand store for Tenant Settings state (read + edit lifecycle).
 * Category: Frontend / tenant-settings / store
 * Scope: Phase 57 / Sprint 57.3 US-3
 *
 * Description:
 *   Mirrors costStore.ts Zustand pattern + extends with saving + saveError
 *   state for PATCH endpoint. Optimistic update on save success (server
 *   response replaces local data); rollback by re-fetching on error if
 *   needed. State: tenantId / data / loading / error / saving / saveError.
 *
 * Created: 2026-05-07 (Sprint 57.3 Day 3)
 * Last Modified: 2026-05-07
 *
 * Modification History:
 *   - 2026-05-07: Initial creation (Sprint 57.3 Day 3 / US-3 — Tenant Settings store)
 *
 * Related:
 *   - ../services/tenantSettingsService.ts (fetchTenantSettings + updateTenantSettings)
 *   - ../types.ts (TenantSettingsResponse + TenantUpdateRequest)
 *   - frontend/src/features/cost-dashboard/store/costStore.ts (pattern reference)
 */

import { create } from "zustand";

import { fetchTenantSettings, updateTenantSettings } from "../services/tenantSettingsService";
import type { TenantSettingsResponse, TenantUpdateRequest } from "../types";

interface TenantSettingsState {
  tenantId: string | null;
  data: TenantSettingsResponse | null;
  loading: boolean;
  error: string | null;
  saving: boolean;
  saveError: string | null;
  setTenantId: (tenantId: string) => void;
  loadData: () => Promise<void>;
  save: (payload: TenantUpdateRequest) => Promise<void>;
  reset: () => void;
}

export const useTenantSettingsStore = create<TenantSettingsState>((set, get) => ({
  tenantId: null,
  data: null,
  loading: false,
  error: null,
  saving: false,
  saveError: null,
  setTenantId: (tenantId) => set({ tenantId, data: null, error: null }),
  loadData: async () => {
    const tenantId = get().tenantId;
    if (!tenantId) return;
    set({ loading: true, error: null });
    try {
      const data = await fetchTenantSettings(tenantId);
      set({ data, loading: false });
    } catch (err) {
      set({ error: (err as Error).message, loading: false });
    }
  },
  save: async (payload) => {
    const tenantId = get().tenantId;
    if (!tenantId) return;
    set({ saving: true, saveError: null });
    try {
      const data = await updateTenantSettings(tenantId, payload);
      set({ data, saving: false });
    } catch (err) {
      set({ saveError: (err as Error).message, saving: false });
    }
  },
  reset: () =>
    set({
      tenantId: null,
      data: null,
      loading: false,
      error: null,
      saving: false,
      saveError: null,
    }),
}));
