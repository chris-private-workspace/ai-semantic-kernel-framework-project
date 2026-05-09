/**
 * File: frontend/src/features/tenant-settings/hooks/useTenantSettingsSave.ts
 * Purpose: TanStack Query mutation hook for tenant settings PATCH (consumed by TenantSettingsEditForm).
 * Category: Frontend / tenant-settings / hooks
 * Scope: Phase 57 / Sprint 57.9 US-6 Day 4
 *
 * Description:
 *   Mirror useApprovalDecide pattern (Sprint 57.9 US-3). On `mutate()` success
 *   the hook invalidates `TENANT_SETTINGS_QUERY_KEY_BASE` so TenantSettingsView
 *   auto-refreshes with the latest server state. Mutation state (`isPending` /
 *   `error`) consumed by TenantSettingsEditForm for save-button disabled +
 *   error-banner rendering.
 *
 *   Replaces Sprint 57.3 store.save / saving / saveError pattern.
 *
 * Created: 2026-05-09 (Sprint 57.9 Day 4 US-6)
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Initial creation (Sprint 57.9 US-6)
 *
 * Related:
 *   - ../services/tenantSettingsService.ts (updateTenantSettings)
 *   - ./useTenantSettings.ts (TENANT_SETTINGS_QUERY_KEY_BASE single-source for invalidation)
 *   - ../components/TenantSettingsEditForm.tsx (consumer)
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { updateTenantSettings } from "../services/tenantSettingsService";
import type { TenantSettingsResponse, TenantUpdateRequest } from "../types";
import { TENANT_SETTINGS_QUERY_KEY_BASE } from "./useTenantSettings";

export interface SaveArgs {
  tenantId: string;
  payload: TenantUpdateRequest;
}

export function useTenantSettingsSave() {
  const qc = useQueryClient();
  return useMutation<TenantSettingsResponse, Error, SaveArgs>({
    mutationFn: ({ tenantId, payload }) => updateTenantSettings(tenantId, payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: TENANT_SETTINGS_QUERY_KEY_BASE });
    },
  });
}
