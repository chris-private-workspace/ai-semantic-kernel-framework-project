/**
 * File: frontend/src/features/tenant-settings/hooks/useRateLimitsUsage.ts
 * Purpose: TanStack Query polling hook for GET /admin/tenants/{id}/rate-limits/usage (Sprint 57.58 Track D).
 * Category: Frontend / tenant-settings / hooks
 * Scope: Phase 57 / Sprint 57.58 Track D (RateLimits RuntimeEnforcement — Live usage Card)
 *
 * Description:
 *   Polls the live Redis sliding-window counter every 5 seconds so the QuotasTab
 *   Live usage Card shows per-resource consumption before tenants hit 429 in
 *   production. `staleTime: 4000` lets TanStack auto-dedupe within a tab and
 *   keeps the cache warm between the 5s refetch ticks (no flicker). Polling
 *   cadence precedent: useApprovals (30_000) + useActiveLoops (10_000); this
 *   one is 5_000 per Sprint 57.58 plan §4.4.
 *
 * Created: 2026-05-28 (Sprint 57.58 Day 1 Track D)
 *
 * Modification History (newest-first):
 *   - 2026-05-28: Initial creation (Sprint 57.58 Day 1 Track D)
 *
 * Related:
 *   - ../services/tenantSettingsService.ts (fetchRateLimitsUsage)
 *   - ../components/tabs/QuotasTab.tsx (consumer — Live usage Card)
 *   - backend/src/api/v1/admin/tenants.py (RateLimitsUsageResponse source of truth)
 */

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { fetchRateLimitsUsage } from "../services/tenantSettingsService";
import type { RateLimitsUsageResponse } from "../types";

export const RATE_LIMITS_USAGE_QUERY_KEY_BASE = [
  "tenant-settings",
  "rate-limits-usage",
] as const;

export function useRateLimitsUsage(tenantId: string) {
  return useQuery<RateLimitsUsageResponse, Error>({
    queryKey: [...RATE_LIMITS_USAGE_QUERY_KEY_BASE, tenantId],
    queryFn: ({ signal }) => fetchRateLimitsUsage(tenantId, signal),
    enabled: Boolean(tenantId),
    refetchInterval: 5000, // 5-second live poll
    staleTime: 4000, // dedupe within tab between ticks
    placeholderData: keepPreviousData,
  });
}
