/**
 * File: frontend/src/features/sla-dashboard/hooks/useSLAReport.ts
 * Purpose: TanStack Query hook for SLA report fetch (consumed by SLAOverview).
 * Category: Frontend / sla-dashboard / hooks
 * Scope: Phase 57 / Sprint 57.9 US-6 Day 4
 *
 * Description:
 *   Mirror useCostSummary pattern. Replaces slaStore loadData orchestration.
 *
 * Created: 2026-05-09 (Sprint 57.9 Day 4 US-6)
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Initial creation (Sprint 57.9 US-6)
 *
 * Related:
 *   - ../services/slaService.ts (fetchSLAReport)
 *   - ../store/slaStore.ts (UI-only state post-migration)
 *   - ../components/SLAOverview.tsx (consumer)
 */

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { fetchSLAReport } from "../services/slaService";
import type { SLAReportResponse } from "../types";

export const SLA_REPORT_QUERY_KEY_BASE = ["sla-dashboard", "report"] as const;

export function useSLAReport(tenantId: string, month: string) {
  return useQuery<SLAReportResponse, Error>({
    queryKey: [...SLA_REPORT_QUERY_KEY_BASE, tenantId, month],
    queryFn: ({ signal }) => fetchSLAReport(tenantId, month, signal),
    enabled: Boolean(tenantId),
    placeholderData: keepPreviousData,
  });
}
