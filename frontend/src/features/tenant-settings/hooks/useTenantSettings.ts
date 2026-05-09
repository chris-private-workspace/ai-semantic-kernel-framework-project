/**
 * File: frontend/src/features/tenant-settings/hooks/useTenantSettings.ts
 * Purpose: TanStack Query hook for tenant settings GET (consumed by TenantSettingsView).
 * Category: Frontend / tenant-settings / hooks
 * Scope: Phase 57 / Sprint 57.9 US-6 Day 4
 *
 * Description:
 *   Mirror useCostSummary pattern. `enabled: Boolean(tenantId)` short-circuits
 *   the fetch when admin hasn't selected a tenant via URL ?tenant_id=.
 *
 * Created: 2026-05-09 (Sprint 57.9 Day 4 US-6)
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Initial creation (Sprint 57.9 US-6)
 *
 * Related:
 *   - ../services/tenantSettingsService.ts (fetchTenantSettings)
 *   - ./useTenantSettingsSave.ts (mutation; invalidates this query on success)
 *   - ../components/TenantSettingsView.tsx (consumer)
 */

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { fetchTenantSettings } from "../services/tenantSettingsService";
import type { TenantSettingsResponse } from "../types";

export const TENANT_SETTINGS_QUERY_KEY_BASE = ["tenant-settings", "detail"] as const;

export function useTenantSettings(tenantId: string) {
  return useQuery<TenantSettingsResponse, Error>({
    queryKey: [...TENANT_SETTINGS_QUERY_KEY_BASE, tenantId],
    queryFn: ({ signal }) => fetchTenantSettings(tenantId, signal),
    enabled: Boolean(tenantId),
    placeholderData: keepPreviousData,
  });
}
