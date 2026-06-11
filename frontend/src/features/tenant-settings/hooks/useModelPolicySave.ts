/**
 * File: frontend/src/features/tenant-settings/hooks/useModelPolicySave.ts
 * Purpose: TanStack mutation hook — PUT /admin/tenants/{id}/model-policy composite-replace.
 * Category: Frontend / tenant-settings / hooks
 * Scope: Phase 57 / Sprint 57.104 C1 (Model Policy tab write side)
 *
 * Description:
 *   Wraps `putModelPolicy` service func with TanStack `useMutation`. On success
 *   invalidates `[...MODEL_POLICY_QUERY_KEY_BASE, tenantId]` to trigger GET
 *   re-fetch with the saved (sparse) policy applied. Verbatim mirror of Sprint
 *   57.56 `useQuotasSave.ts` precedent.
 *
 * Created: 2026-06-11 (Sprint 57.104 C1)
 *
 * Modification History (newest-first):
 *   - 2026-06-11: Initial creation (Sprint 57.104 C1)
 *
 * Related:
 *   - ../services/tenantSettingsService.ts (putModelPolicy)
 *   - ./useModelPolicy.ts (MODEL_POLICY_QUERY_KEY_BASE)
 *   - ../components/tabs/ModelPolicyTab.tsx (consumer)
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { putModelPolicy } from "../services/tenantSettingsService";
import type { ModelPolicy } from "../types";
import { MODEL_POLICY_QUERY_KEY_BASE } from "./useModelPolicy";

export function useModelPolicySave(tenantId: string) {
  const qc = useQueryClient();
  return useMutation<ModelPolicy, Error, ModelPolicy>({
    mutationFn: (payload) => putModelPolicy(tenantId, payload),
    onSuccess: () => {
      void qc.invalidateQueries({
        queryKey: [...MODEL_POLICY_QUERY_KEY_BASE, tenantId],
      });
    },
  });
}
