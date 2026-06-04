/**
 * File: frontend/src/features/memory/hooks/useMemoryOps.ts
 * Purpose: TanStack Query hook for the memory ops-history (GET /api/v1/memory/ops).
 * Category: Frontend / memory / hooks
 * Scope: Phase 57 / Sprint 57.77 (AD-Memory-OpsHistory-Backend frontend half)
 *
 * Description:
 *   Owns the server cache for the append-only memory ops log (WRITE/EVICT,
 *   user/tenant scope). Consumed by RecentMemoryOpsCard (table rows) and
 *   TimeTravelScrubber (marks derived from created_at_ms). React Query dedups
 *   the shared query key so both consumers issue a single request — same shape
 *   as MemoryMatrix + MemoryPageHeader sharing useMemoryMatrix. Mirrors
 *   useMemoryMatrix (Sprint 57.73) hook shape: stable queryKey + queryFn
 *   forwarding the AbortSignal.
 *
 * Created: 2026-06-04 (Sprint 57.77)
 *
 * Modification History (newest-first):
 *   - 2026-06-04: Initial creation (Sprint 57.77) — wire RecentOps + TimeTravel to GET /ops
 *
 * Related:
 *   - ../services/memoryService.ts (fetchOps)
 *   - ../types.ts (MemoryOpsResponse)
 *   - ../components/RecentMemoryOpsCard.tsx + TimeTravelScrubber.tsx (consumers)
 *   - ./useMemoryMatrix.ts (sibling pattern)
 */

import { useQuery } from "@tanstack/react-query";

import { memoryService } from "../services/memoryService";
import type { MemoryOpsResponse } from "../types";

export const MEMORY_OPS_QUERY_KEY = ["memory", "ops"] as const;

export function useMemoryOps() {
  return useQuery<MemoryOpsResponse, Error>({
    queryKey: MEMORY_OPS_QUERY_KEY,
    queryFn: ({ signal }) => memoryService.fetchOps(50, undefined, signal),
    staleTime: 30_000,
  });
}
