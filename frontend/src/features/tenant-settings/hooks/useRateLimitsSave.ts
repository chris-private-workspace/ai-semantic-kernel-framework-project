/**
 * File: frontend/src/features/tenant-settings/hooks/useRateLimitsSave.ts
 * Purpose: TanStack mutation hook — PUT /admin/tenants/{id}/rate-limits items upsert.
 * Category: Frontend / tenant-settings / hooks
 * Scope: Phase 57 / Sprint 57.57 Track B (Phase 58.x portfolio FINAL 4/4)
 *
 * Description:
 *   Wraps `saveRateLimits` service func with TanStack `useMutation`. On
 *   success invalidates `[...RATE_LIMITS_QUERY_KEY_BASE, tenantId]` to
 *   trigger GET re-fetch with new item values applied. Verbatim mirror of
 *   Sprint 57.56 `useQuotasSave.ts` precedent.
 *
 * Created: 2026-05-27 (Sprint 57.57 Track B)
 *
 * Modification History (newest-first):
 *   - 2026-05-27: Initial creation (Sprint 57.57 Track B)
 *
 * Related:
 *   - ../services/tenantSettingsService.ts (saveRateLimits)
 *   - ./useRateLimits.ts (RATE_LIMITS_QUERY_KEY_BASE)
 *   - ../components/tabs/QuotasTab.tsx (consumer)
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { saveRateLimits } from "../services/tenantSettingsService";
import type {
  RateLimitsUpsertRequest,
  RateLimitsUpsertResponse,
} from "../types";
import { RATE_LIMITS_QUERY_KEY_BASE } from "./useRateLimits";

export function useRateLimitsSave(tenantId: string) {
  const qc = useQueryClient();
  return useMutation<RateLimitsUpsertResponse, Error, RateLimitsUpsertRequest>({
    mutationFn: (payload) => saveRateLimits(tenantId, payload),
    onSuccess: () => {
      void qc.invalidateQueries({
        queryKey: [...RATE_LIMITS_QUERY_KEY_BASE, tenantId],
      });
    },
  });
}
