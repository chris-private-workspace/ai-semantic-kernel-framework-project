/**
 * File: frontend/src/features/tenant-settings/hooks/useRateLimitsAlerts.ts
 * Purpose: TanStack Query polling hook for GET /admin/tenants/{id}/rate-limits/alerts (Sprint 57.62 US-3).
 * Category: Frontend / tenant-settings / hooks
 * Scope: Phase 57 / Sprint 57.62 (RateLimits Alerting — Recent alerts surface)
 *
 * Description:
 *   Polls the recent 80%-threshold rate-limit alert log every 15 seconds so the
 *   QuotasTab "Recent alerts" Card surfaces breaches captured at the enforcement
 *   point — even when no admin was watching the Live usage Card. The poll cadence
 *   is 15s (vs useRateLimitsUsage's 5s) because alerts are durable, deduplicated
 *   records — not the sub-5s-critical live counter. `staleTime: 14000` dedupes
 *   within a tab between the 15s refetch ticks (no flicker).
 *
 * Created: 2026-05-29 (Sprint 57.62 US-3 Track B)
 *
 * Modification History (newest-first):
 *   - 2026-05-29: Initial creation (Sprint 57.62 US-3 Track B)
 *
 * Related:
 *   - ../services/tenantSettingsService.ts (fetchRateLimitsAlerts)
 *   - ../components/tabs/QuotasTab.tsx (consumer — Recent alerts Card)
 *   - backend/src/api/v1/admin/tenants.py (RateLimitAlertsResponse source of truth)
 */

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { fetchRateLimitsAlerts } from "../services/tenantSettingsService";
import type { RateLimitAlertsResponse } from "../types";

export const RATE_LIMITS_ALERTS_QUERY_KEY_BASE = [
  "tenant-settings",
  "rate-limits-alerts",
] as const;

export function useRateLimitsAlerts(tenantId: string) {
  return useQuery<RateLimitAlertsResponse, Error>({
    queryKey: [...RATE_LIMITS_ALERTS_QUERY_KEY_BASE, tenantId],
    queryFn: ({ signal }) => fetchRateLimitsAlerts(tenantId, undefined, signal),
    enabled: Boolean(tenantId),
    refetchInterval: 15000, // 15-second poll (alerts less time-critical than live usage)
    staleTime: 14000, // dedupe within tab between ticks
    placeholderData: keepPreviousData,
  });
}
