/**
 * File: frontend/src/features/subagents/hooks/useSubagents.ts
 * Purpose: TanStack Query hook for the subagents registry (Cat 11; agent_catalog list).
 * Category: Frontend / subagents / hooks
 * Scope: Phase 57 / Sprint 57.78 (re-point STUB → agent_catalog registry)
 *
 * Created: 2026-05-17 (Sprint 57.19 Day 4 / US-C3)
 *
 * Modification History (newest-first):
 *   - 2026-06-04: Sprint 57.78 — return SubagentsResponse; drop params; staleTime 30s (AD-Subagent-RealList)
 *   - 2026-05-17: Initial creation (Sprint 57.19 Day 4 / US-C3)
 *
 * Related:
 *   - ../services/subagentsService.ts
 *   - ../types.ts (SubagentsResponse)
 */

import { useQuery } from "@tanstack/react-query";

import { fetchSubagents } from "../services/subagentsService";
import type { SubagentsResponse } from "../types";

export const SUBAGENTS_LIST_QUERY_KEY = ["subagents", "list"] as const;

export function useSubagents() {
  return useQuery<SubagentsResponse, Error>({
    queryKey: SUBAGENTS_LIST_QUERY_KEY,
    queryFn: ({ signal }) => fetchSubagents(signal),
    staleTime: 30_000,
  });
}
