/**
 * File: frontend/src/features/governance/hooks/useApprovals.ts
 * Purpose: TanStack Query hook for pending approvals list (consumed by ApprovalsPage).
 * Category: Frontend / governance / hooks
 * Scope: Phase 57 / Sprint 57.9 US-3 Day 2
 *
 * Description:
 *   First TanStack Query consumer in V2 frontend (Sprint 57.7 US-B2 wired
 *   <QueryClientProvider> in main.tsx; Sprint 57.7 deferred actual usage per
 *   AD-Cost-Dashboard-UseQuery — Sprint 57.9 closes via this hook + Day 4 4-page migration).
 *
 *   Wraps `governanceService.listPending` with:
 *   - `queryKey: APPROVALS_QUERY_KEY` (single-source export for invalidation reuse)
 *   - `refetchInterval: 30_000` (mirror Sprint 53.5 ApprovalsPage polling cadence;
 *     drops manual setInterval + AbortController boilerplate)
 *   - `signal` forwarded from TanStack to governanceService (auto-cancellation
 *     on stale query / unmount)
 *
 *   Replaces the manual useState + useEffect + setInterval + AbortController +
 *   useCallback pattern in Sprint 53.5 ApprovalsPage. Refactor lands Day 2 via
 *   ApprovalsPage drop of all that boilerplate.
 *
 * Created: 2026-05-09 (Sprint 57.9 Day 2 US-3)
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Initial creation (Sprint 57.9 US-3 — first TanStack Query in V2)
 *
 * Related:
 *   - ../services/governanceService.ts (listPending source)
 *   - ./useApprovalDecide.ts (mutation; invalidates this query on success)
 *   - ../components/ApprovalsPage.tsx (consumer)
 *   - main.tsx (QueryClientProvider with staleTime 30s + refetchOnWindowFocus false)
 */

import { useQuery } from "@tanstack/react-query";

import { governanceService } from "../services/governanceService";
import type { ApprovalSummary } from "../types";

/**
 * Single-source query key for governance approvals list. Exported so the
 * mutation hook (useApprovalDecide) can `qc.invalidateQueries({ queryKey: APPROVALS_QUERY_KEY })`
 * without duplicating the literal.
 */
export const APPROVALS_QUERY_KEY = ["governance", "approvals"] as const;

const POLL_INTERVAL_MS = 30_000;

export function useApprovals() {
  return useQuery<ApprovalSummary[], Error>({
    queryKey: APPROVALS_QUERY_KEY,
    queryFn: ({ signal }) => governanceService.listPending(signal),
    refetchInterval: POLL_INTERVAL_MS,
  });
}
