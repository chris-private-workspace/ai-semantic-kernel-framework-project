/**
 * File: frontend/src/lib/queryClient.ts
 * Purpose: The single app-wide TanStack QueryClient — central place for default
 * options + a mutationCache.onError that surfaces failures as a toast.
 * Category: Frontend / lib (Sprint 57.13 US-B1 — Toast system)
 * Scope: Phase 57 / Sprint 57.13 US-B1
 *
 * Description:
 *   Extracted from main.tsx (Sprint 57.13 US-B1) so config lives in one place
 *   and the mutationCache can wire `onError → toastError`. Query failures are
 *   intentionally NOT toasted here — the dashboard pages (cost / sla /
 *   tenant-settings) render an inline error state + a "Retry" button (Sprint
 *   57.9 US-6), so a global toast would double-surface. Mutations (e.g.
 *   governance approve/decide) have no inline error slot, so they toast.
 *
 *   401 handling lives in authService.fetchWithAuth (the only layer that sees
 *   the raw status for *every* request — feature services rethrow as plain
 *   Error and lose the status code), so it isn't repeated here.
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 3)
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.13 US-B4 — mutationCache.onError also reportError(err, {source:"mutation"})
 *   - 2026-05-10: Initial creation (Sprint 57.13 Day 3)
 *
 * Related:
 *   - frontend/src/main.tsx (QueryClientProvider consumer)
 *   - frontend/src/lib/toast.ts (toastError + errorMessage)
 *   - frontend/src/lib/observability.ts (reportError)
 *   - frontend/src/features/auth/services/authService.ts (401 → redirect)
 */

import { MutationCache, QueryClient } from "@tanstack/react-query";

import { reportError } from "./observability";
import { errorMessage, toastError } from "./toast";

// staleTime 30s favours freshness over over-fetching for SaaS dashboards.
// retry:false aligns with the UX where 4xx/5xx surfaces immediately + a manual
// "Retry" button is provided per-page; avoids auto-retry storms against admin
// endpoints + matches the e2e contract that the first failure renders the
// error UX (Sprint 57.9 US-6 Day 4).
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      retry: false,
    },
    mutations: {
      retry: false,
    },
  },
  mutationCache: new MutationCache({
    onError: (err) => {
      toastError(errorMessage(err));
      reportError(err, { source: "mutation" });
    },
  }),
});
