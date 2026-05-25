/**
 * File: frontend/src/features/governance/components/AuditChainBadge.tsx
 * Purpose: On-demand chain integrity badge — calls /audit/verify-chain and surfaces valid / broken / total.
 * Category: Frontend / governance / components
 * Scope: Phase 57 / Sprint 57.9 US-5 Day 3
 *
 * Description:
 *   Standalone badge consuming `auditService.verifyChain` (heavy backend
 *   operation per Sprint 53.5 US-6). NOT auto-fetched on mount — user must
 *   click Verify chain button to trigger (avoids accidental walk on every
 *   AuditLogViewer mount). Once invoked, displays:
 *   - Loading state ("Verifying…")
 *   - Success ✓ valid + total_entries
 *   - Failure ✗ broken_at_id + total_entries (red destructive variant)
 *   - HTTP error (e.g. 403 forbidden auditor RBAC) surfaced with auditor-role hint
 *
 *   Uses TanStack `useQuery` with `enabled: false` — manual trigger via
 *   `refetch()`. No `placeholderData` — we want explicit "no result yet" UX
 *   before first click rather than stale display.
 *
 *   Tailwind impl per Day 0 D-PRE-2 + Sprint 57.8 UserMenu YAGNI precedent
 *   (no shadcn `<Badge>` introduced).
 *
 * Created: 2026-05-09 (Sprint 57.9 Day 3 US-5)
 *
 * Modification History (newest-first):
 *   - 2026-05-25: FIX-017 — valid-state badge hex sentinels (#2e7d32) → var(--risk-low) tokens
 *   - 2026-05-09: Initial creation (Sprint 57.9 US-5)
 *
 * Related:
 *   - ../services/auditService.ts (verifyChain source)
 *   - ./AuditLogViewer.tsx (mounts this badge top-right per US-4 design)
 *   - ../types.ts (ChainVerifyResult)
 */

import { useQuery } from "@tanstack/react-query";

import { auditService } from "../services/auditService";
import type { ChainVerifyResult } from "../types";

export const CHAIN_VERIFY_QUERY_KEY = ["governance", "audit-chain-verify"] as const;

const BUTTON_BASE =
  "inline-flex items-center rounded-md border px-3 py-1.5 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed";

const BUTTON_IDLE = "border-primary bg-background text-primary hover:bg-primary/10";

export function AuditChainBadge() {
  const { data, error, isFetching, refetch, isFetched } = useQuery<ChainVerifyResult, Error>({
    queryKey: CHAIN_VERIFY_QUERY_KEY,
    queryFn: ({ signal }) => auditService.verifyChain(signal),
    enabled: false,
  });

  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        onClick={() => void refetch()}
        disabled={isFetching}
        className={`${BUTTON_BASE} ${BUTTON_IDLE}`}
      >
        {isFetching ? "Verifying…" : "Verify chain"}
      </button>

      {error && (
        <span
          role="alert"
          className="rounded-md bg-destructive/10 px-2 py-1 text-xs font-semibold text-destructive"
        >
          Verify failed: {error.message}
        </span>
      )}

      {!error && isFetched && data && data.valid && (
        <span
          role="status"
          className="rounded-md bg-[color:var(--risk-low)]/10 px-2 py-1 text-xs font-semibold text-[color:var(--risk-low)]"
        >
          ✓ Valid · {data.total_entries} entries
        </span>
      )}

      {!error && isFetched && data && !data.valid && (
        <span
          role="status"
          className="rounded-md bg-destructive/10 px-2 py-1 text-xs font-semibold text-destructive"
        >
          ✗ Broken at id={data.broken_at_id} · {data.total_entries} entries
        </span>
      )}
    </div>
  );
}
