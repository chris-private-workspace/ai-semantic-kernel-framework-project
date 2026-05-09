/**
 * File: frontend/src/features/cost-dashboard/hooks/useCostSummary.ts
 * Purpose: TanStack Query hook for cost summary fetch (consumed by CostOverview).
 * Category: Frontend / cost-dashboard / hooks
 * Scope: Phase 57 / Sprint 57.9 US-6 Day 4
 *
 * Description:
 *   Replaces the loadData/data/loading/error orchestration that previously
 *   lived in `costStore.ts`. After Day 4 migration, store keeps UI-only state
 *   (currentMonth selection); this hook owns the server cache.
 *
 *   `enabled: Boolean(tenantId)` short-circuits the fetch when admin hasn't
 *   chosen a tenant yet (URL ?tenant_id=... missing) — avoids spurious 4xx.
 *   `placeholderData: keepPreviousData` smooths month switching (prior month's
 *   data stays visible while next loads).
 *
 *   Closes AD-Cost-Dashboard-UseQuery (Sprint 57.7 logged) — first non-governance
 *   TanStack consumer + 4-page batch via Day 4.
 *
 * Created: 2026-05-09 (Sprint 57.9 Day 4 US-6)
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Initial creation (Sprint 57.9 US-6 — closes AD-Cost-Dashboard-UseQuery)
 *
 * Related:
 *   - ../services/costService.ts (fetchCostSummary)
 *   - ../store/costStore.ts (UI-only state post-migration)
 *   - ../components/CostOverview.tsx (consumer)
 *   - ../types.ts (CostSummaryResponse)
 */

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { fetchCostSummary } from "../services/costService";
import type { CostSummaryResponse } from "../types";

export const COST_SUMMARY_QUERY_KEY_BASE = ["cost-dashboard", "summary"] as const;

export function useCostSummary(tenantId: string, month: string) {
  return useQuery<CostSummaryResponse, Error>({
    queryKey: [...COST_SUMMARY_QUERY_KEY_BASE, tenantId, month],
    queryFn: ({ signal }) => fetchCostSummary(tenantId, month, signal),
    enabled: Boolean(tenantId),
    placeholderData: keepPreviousData,
  });
}
