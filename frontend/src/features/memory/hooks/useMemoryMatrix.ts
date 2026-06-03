/**
 * File: frontend/src/features/memory/hooks/useMemoryMatrix.ts
 * Purpose: TanStack Query hook for the Memory 5×3 matrix aggregate (GET /api/v1/memory/matrix).
 * Category: Frontend / memory / hooks
 * Scope: Phase 57 / Sprint 57.73 Track C (A-6b frontend half)
 *
 * Description:
 *   Owns the server cache for the dual-axis Memory Layers matrix. Consumed by
 *   MemoryMatrix (cell counts + gap indicator) and MemoryPageHeader (total).
 *   React Query dedups the shared query key so both consumers issue a single
 *   request. Mirrors useCostSummary (Sprint 57.9) hook shape: stable queryKey
 *   base + queryFn forwarding the AbortSignal.
 *
 * Created: 2026-06-03 (Sprint 57.73 Track C)
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Initial creation (Sprint 57.73 Track C) — wire matrix + header to GET /matrix
 *
 * Related:
 *   - ../services/memoryService.ts (fetchMatrix)
 *   - ../types.ts (MemoryMatrixResponse)
 *   - ../components/MemoryMatrix.tsx + MemoryPageHeader.tsx (consumers)
 *   - ../../cost-dashboard/hooks/useCostSummary.ts (sibling pattern)
 */

import { useQuery } from "@tanstack/react-query";

import { memoryService } from "../services/memoryService";
import type { MemoryMatrixResponse } from "../types";

export const MEMORY_MATRIX_QUERY_KEY = ["memory", "matrix"] as const;

export function useMemoryMatrix() {
  return useQuery<MemoryMatrixResponse, Error>({
    queryKey: MEMORY_MATRIX_QUERY_KEY,
    queryFn: ({ signal }) => memoryService.fetchMatrix(signal),
    staleTime: 30_000,
  });
}
