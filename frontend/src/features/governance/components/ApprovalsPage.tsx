/**
 * File: frontend/src/features/governance/components/ApprovalsPage.tsx
 * Purpose: Pending approvals page — TanStack-driven list + handles row click → DecisionModal.
 * Category: Frontend / governance / components
 * Scope: Phase 53 / Sprint 53.5 US-1 → Sprint 57.9 US-2 Day 1 (Tailwind) → Sprint 57.9 US-3 Day 2 (TanStack)
 *
 * Description:
 *   Sprint 57.9 US-3 Day 2: refactored from manual useState + useEffect +
 *   setInterval + AbortController boilerplate (Sprint 53.5) to consume the
 *   `useApprovals` TanStack Query hook (refetchInterval 30s preserved per
 *   single-source POLL_INTERVAL_MS in hook).
 *
 *   DecisionModal now self-contained via `useApprovalDecide` mutation hook
 *   (drops the legacy `onSubmit` callback prop wiring); ApprovalsPage only
 *   needs to hand DecisionModal the selected approval + an `onClose` to clear
 *   selection state.
 *
 * Created: 2026-05-04 (Sprint 53.5 Day 3)
 * Last Modified: 2026-05-09
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Sprint 57.9 US-3 Day 2 — drop manual polling/state, consume useApprovals hook
 *   - 2026-05-09: Sprint 57.9 US-2 Day 1 — Tailwind migration (drop inline styles)
 *   - 2026-05-04: Initial creation (Sprint 53.5 Day 3)
 *
 * Related:
 *   - ./ApprovalList.tsx
 *   - ./DecisionModal.tsx (self-contained mutation via useApprovalDecide)
 *   - ../hooks/useApprovals.ts (TanStack query)
 */

import { useState } from "react";

import { useApprovals } from "../hooks/useApprovals";
import type { ApprovalSummary } from "../types";
import { ApprovalList } from "./ApprovalList";
import { DecisionModal } from "./DecisionModal";

export function ApprovalsPage() {
  const { data: items = [], isLoading, error, refetch } = useApprovals();
  const [selected, setSelected] = useState<ApprovalSummary | null>(null);

  return (
    <div className="space-y-4">
      <div className="flex items-baseline justify-between">
        <h2 className="m-0 text-xl font-semibold">Pending Approvals</h2>
        <button
          type="button"
          onClick={() => void refetch()}
          disabled={isLoading}
          className="inline-flex items-center rounded-md border border-primary bg-background px-3 py-1.5 text-sm font-medium text-primary hover:bg-primary/10 disabled:opacity-50"
        >
          {isLoading ? "Refreshing…" : "Refresh"}
        </button>
      </div>

      {error && (
        <div
          role="alert"
          className="rounded-lg border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive"
        >
          Failed to load approvals: {error.message}
        </div>
      )}

      <ApprovalList approvals={items} onSelect={setSelected} />

      {selected && (
        <DecisionModal approval={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}
