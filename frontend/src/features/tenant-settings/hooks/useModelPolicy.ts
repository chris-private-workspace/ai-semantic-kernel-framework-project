/**
 * File: frontend/src/features/tenant-settings/hooks/useModelPolicy.ts
 * Purpose: TanStack Query hook for GET /admin/tenants/{id}/model-policy (Sprint 57.104 C1).
 * Category: Frontend / tenant-settings / hooks
 * Scope: Phase 57 / Sprint 57.104 C1 (Model Policy tab read side)
 *
 * Created: 2026-06-11 (Sprint 57.104 C1)
 *
 * Modification History (newest-first):
 *   - 2026-06-11: Initial creation (Sprint 57.104 C1)
 *
 * Related:
 *   - ../services/tenantSettingsService.ts (getModelPolicy)
 *   - ../components/tabs/ModelPolicyTab.tsx (consumer)
 */

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { getModelPolicy } from "../services/tenantSettingsService";
import type { ModelPolicy } from "../types";

export const MODEL_POLICY_QUERY_KEY_BASE = ["tenant-settings", "model-policy"] as const;

export function useModelPolicy(tenantId: string) {
  return useQuery<ModelPolicy, Error>({
    queryKey: [...MODEL_POLICY_QUERY_KEY_BASE, tenantId],
    queryFn: ({ signal }) => getModelPolicy(tenantId, signal),
    enabled: Boolean(tenantId),
    placeholderData: keepPreviousData,
  });
}
