/**
 * File: frontend/src/features/subagents/hooks/useSubagents.ts
 * Purpose: TanStack Query hook for subagents list (Cat 11; US-C3 consumer).
 * Category: Frontend / subagents / hooks
 * Scope: Phase 57 / Sprint 57.19 Day 4 / US-C3
 *
 * Created: 2026-05-17 (Sprint 57.19 Day 4 / US-C3)
 *
 * Modification History (newest-first):
 *   - 2026-05-17: Initial creation (Sprint 57.19 Day 4 / US-C3)
 *
 * Related:
 *   - ../services/subagentsService.ts
 *   - ../types.ts (SubagentsPage)
 */

import { useQuery } from "@tanstack/react-query";

import { fetchSubagents, type FetchSubagentsParams } from "../services/subagentsService";
import type { SubagentsPage } from "../types";

export const SUBAGENTS_LIST_QUERY_KEY_BASE = ["subagents", "list"] as const;

export function useSubagents(params: FetchSubagentsParams = {}) {
  return useQuery<SubagentsPage, Error>({
    queryKey: [...SUBAGENTS_LIST_QUERY_KEY_BASE, params.mode ?? "all", params.cursor ?? null, params.limit ?? 50],
    queryFn: ({ signal }) => fetchSubagents(params, signal),
    staleTime: 5_000,
  });
}
