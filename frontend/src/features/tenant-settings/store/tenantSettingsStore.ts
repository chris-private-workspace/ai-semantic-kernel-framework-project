/**
 * File: frontend/src/features/tenant-settings/store/tenantSettingsStore.ts
 * Purpose: Zustand store for Tenant Settings UI-only state (selected tenantId).
 * Category: Frontend / tenant-settings / store
 * Scope: Phase 57 / Sprint 57.3 US-3 → Sprint 57.9 US-6 Day 4 (UI-only reduction)
 *
 * Description:
 *   Sprint 57.9 US-6 Day 4: reduced from full data + save orchestration to
 *   UI-only state (tenantId selection). Server cache moved to
 *   `useTenantSettings` query hook + `useTenantSettingsSave` mutation hook.
 *
 *   Note: in current usage TenantSettingsView reads tenantId directly from
 *   `useSearchParams()` so this store is largely a placeholder for any
 *   future cross-component selection sharing. Kept minimal but present so
 *   tests + multi-component coordination remain straightforward.
 *
 * Created: 2026-05-07 (Sprint 57.3 Day 3)
 * Last Modified: 2026-05-09
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — reduce to UI-only (drop loadData/save/data/loading/error)
 *   - 2026-05-07: Initial creation (Sprint 57.3 Day 3)
 *
 * Related:
 *   - ../hooks/useTenantSettings.ts + useTenantSettingsSave.ts (server cache post-migration)
 */

import { create } from "zustand";

interface TenantSettingsState {
  tenantId: string | null;
  setTenantId: (tenantId: string | null) => void;
  reset: () => void;
}

export const useTenantSettingsStore = create<TenantSettingsState>((set) => ({
  tenantId: null,
  setTenantId: (tenantId) => set({ tenantId }),
  reset: () => set({ tenantId: null }),
}));
