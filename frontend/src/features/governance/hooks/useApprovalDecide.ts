/**
 * File: frontend/src/features/governance/hooks/useApprovalDecide.ts
 * Purpose: TanStack Query mutation hook for approval decision (consumed by DecisionModal).
 * Category: Frontend / governance / hooks
 * Scope: Phase 57 / Sprint 57.9 US-3 Day 2
 *
 * Description:
 *   Wraps `governanceService.decide` with:
 *   - `useMutation({ mutationFn, onSuccess })` for declarative mutation lifecycle
 *   - `onSuccess` invalidates `APPROVALS_QUERY_KEY` so the pending list auto-refetches
 *     after a decision (replaces Sprint 53.5 manual `await onSubmit + refresh()` pattern)
 *   - Mutation state (`isPending` / `error` / `data`) consumed by DecisionModal for
 *     button-disabled + error-banner rendering
 *
 *   Race protection: TanStack auto-handles concurrent mutations (each `mutate()` call
 *   gets its own promise; `isPending` reflects most recent). For rapid double-click
 *   of Approve, the first mutation completes and triggers invalidate; second mutation
 *   would hit the same endpoint but on an already-decided request_id (backend returns
 *   404/409 per state machine) — surfaced as `error` to user.
 *
 * Created: 2026-05-09 (Sprint 57.9 Day 2 US-3)
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Initial creation (Sprint 57.9 US-3)
 *
 * Related:
 *   - ../services/governanceService.ts (decide source)
 *   - ./useApprovals.ts (APPROVALS_QUERY_KEY single-source for invalidation)
 *   - ../components/DecisionModal.tsx (consumer)
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { governanceService } from "../services/governanceService";
import type { DecisionLabel, DecisionResponse } from "../types";
import { APPROVALS_QUERY_KEY } from "./useApprovals";

export interface DecideArgs {
  requestId: string;
  decision: DecisionLabel;
  reason?: string;
}

export function useApprovalDecide() {
  const qc = useQueryClient();
  return useMutation<DecisionResponse, Error, DecideArgs>({
    mutationFn: ({ requestId, decision, reason }) =>
      governanceService.decide(requestId, decision, reason),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: APPROVALS_QUERY_KEY });
    },
  });
}
