/**
 * File: frontend/src/features/tenant-settings/hooks/useFeatureFlagsSave.ts
 * Purpose: TanStack Query mutation hook for FeatureFlag overrides PUT (consumed by FeatureFlagsTab edit mode).
 * Category: Frontend / tenant-settings / hooks
 * Scope: Phase 57 / Sprint 57.55 Track B
 *
 * Description:
 *   Mirror useHITLPoliciesSave pattern (Sprint 57.54 Track B). On mutate() success
 *   the hook invalidates [...FEATURE_FLAGS_QUERY_KEY_BASE, tenantId] so
 *   FeatureFlagsTab auto-refreshes with the latest server state. Mutation state
 *   (isPending / error) consumed by FeatureFlagsTab edit mode for save-button
 *   disabled + inline-error rendering.
 *
 *   Sprint 57.55 Track B — closes AD-AgentFactor-Tier-3-Validation-Sprint-57.55.
 *
 * Created: 2026-05-27 (Sprint 57.55 Day 1)
 *
 * Modification History (newest-first):
 *   - 2026-05-27: Initial creation (Sprint 57.55 Day 1 Track B)
 *
 * Related:
 *   - ../services/tenantSettingsService.ts (saveFeatureFlagOverrides)
 *   - ./useFeatureFlags.ts (FEATURE_FLAGS_QUERY_KEY_BASE single-source)
 *   - ../components/tabs/FeatureFlagsTab.tsx (consumer)
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { saveFeatureFlagOverrides } from "../services/tenantSettingsService";
import type {
  FeatureFlagOverridesUpsertRequest,
  FeatureFlagOverridesUpsertResponse,
} from "../types";
import { FEATURE_FLAGS_QUERY_KEY_BASE } from "./useFeatureFlags";

export function useFeatureFlagsSave(tenantId: string) {
  const qc = useQueryClient();
  return useMutation<FeatureFlagOverridesUpsertResponse, Error, FeatureFlagOverridesUpsertRequest>({
    mutationFn: (payload) => saveFeatureFlagOverrides(tenantId, payload),
    onSuccess: () => {
      void qc.invalidateQueries({
        queryKey: [...FEATURE_FLAGS_QUERY_KEY_BASE, tenantId],
      });
    },
  });
}
