/**
 * File: frontend/src/features/tenant-settings/hooks/useQuotasSave.ts
 * Purpose: TanStack mutation hook — PUT /admin/tenants/{id}/quotas overrides upsert.
 * Category: Frontend / tenant-settings / hooks
 * Scope: Phase 57 / Sprint 57.56 Track B (Phase 58.x portfolio item 3/4)
 *
 * Description:
 *   Wraps `saveQuotaOverrides` service func with TanStack `useMutation`. On
 *   success invalidates `[...QUOTAS_QUERY_KEY_BASE, tenantId]` to trigger
 *   GET re-fetch with new override values applied. Verbatim mirror of Sprint
 *   57.55 `useFeatureFlagsSave.ts` precedent.
 *
 * Created: 2026-05-27 (Sprint 57.56 Track B)
 *
 * Modification History (newest-first):
 *   - 2026-05-27: Initial creation (Sprint 57.56 Track B)
 *
 * Related:
 *   - ../services/tenantSettingsService.ts (saveQuotaOverrides)
 *   - ./useQuotas.ts (QUOTAS_QUERY_KEY_BASE)
 *   - ../components/tabs/QuotasTab.tsx (consumer)
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { saveQuotaOverrides } from "../services/tenantSettingsService";
import type {
  QuotaOverridesUpsertRequest,
  QuotaOverridesUpsertResponse,
} from "../types";
import { QUOTAS_QUERY_KEY_BASE } from "./useQuotas";

export function useQuotasSave(tenantId: string) {
  const qc = useQueryClient();
  return useMutation<QuotaOverridesUpsertResponse, Error, QuotaOverridesUpsertRequest>({
    mutationFn: (payload) => saveQuotaOverrides(tenantId, payload),
    onSuccess: () => {
      void qc.invalidateQueries({
        queryKey: [...QUOTAS_QUERY_KEY_BASE, tenantId],
      });
    },
  });
}
