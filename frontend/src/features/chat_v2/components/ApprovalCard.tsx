/**
 * File: frontend/src/features/chat_v2/components/ApprovalCard.tsx
 * Purpose: Inline HITL approval card rendered in chat (Sprint 53.5 US-2).
 * Category: Frontend / chat_v2 / components
 * Scope: Phase 53 / Sprint 53.5 US-2
 *
 * Description:
 *   Displays an in-conversation card when the loop emits ApprovalRequested.
 *   Renders Approve / Reject quick buttons (calls governanceService.decide
 *   and optimistically updates the chat store) plus a deep link to the
 *   governance approvals page.
 *
 *   When ApprovalReceived arrives, the card transitions to a readonly view
 *   showing the reviewer outcome.
 *
 * Created: 2026-05-04 (Sprint 53.5 Day 4 US-2)
 * Last Modified: 2026-05-11
 *
 * Modification History:
 *   - 2026-05-11: Sprint 57.15 — inline styles → Tailwind utility classes; risk colours per STYLE.md §3 (AD-Inline-Style-Cleanup-Sweep)
 *   - 2026-05-04: Initial creation (Sprint 53.5 Day 4 US-2)
 *
 * Related:
 *   - ../store/chatStore.ts (approvals slice)
 *   - ../../governance/services/governanceService.ts (decide call)
 *   - frontend/STYLE.md §3 Risk Badge Palette
 */

import { useState } from "react";

import { cn } from "../../../lib/utils";
import { governanceService } from "../../governance/services/governanceService";
import type { DecisionLabel } from "../../governance/types";
import { useChatStore } from "../store/chatStore";

// Risk colour classes per STYLE.md §3 Risk Badge Palette (canonical 4-level).
const RISK_TEXT_CLASS: Record<string, string> = {
  LOW: "text-green-700",
  MEDIUM: "text-orange-600",
  HIGH: "text-orange-800",
  CRITICAL: "text-red-800",
};

// Decision badge background per outcome (semantic tokens — STYLE.md §2).
const DECISION_BADGE_CLASS: Record<string, string> = {
  APPROVED: "bg-success",
  REJECTED: "bg-danger",
  ESCALATED: "bg-warning",
};

type Props = {
  approvalRequestId: string;
};

export function ApprovalCard({ approvalRequestId }: Props) {
  const entry = useChatStore((s) => s.approvals[approvalRequestId]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!entry) return null;

  const submit = async (decision: DecisionLabel) => {
    setBusy(true);
    setError(null);
    try {
      await governanceService.decide(approvalRequestId, decision);
      // Optimistic: mark decision locally so UI updates even before
      // ApprovalReceived SSE arrives. The SSE event will overwrite if needed.
      useChatStore.setState((s) => ({
        approvals: {
          ...s.approvals,
          [approvalRequestId]: {
            ...s.approvals[approvalRequestId],
            decision: decision.toUpperCase(),
          },
        },
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const riskTextClass = RISK_TEXT_CLASS[entry.riskLevel] ?? "text-muted-foreground";
  const isPending = entry.decision === null;
  const decisionBadgeClass =
    DECISION_BADGE_CLASS[entry.decision ?? ""] ?? "bg-muted-foreground";

  return (
    <div
      className="my-2 rounded-md border border-warning bg-warning/10 px-4 py-3 text-[0.95rem]"
      role="region"
      aria-label="HITL approval"
    >
      <div className="mb-1.5 font-semibold">
        🔔 Approval requested —{" "}
        <span className={cn("font-bold", riskTextClass)}>{entry.riskLevel}</span> risk
      </div>
      <div className="text-sm text-muted-foreground">
        Request ID: <code>{approvalRequestId}</code>
      </div>

      {!isPending && (
        <div className="mt-2">
          Decision:{" "}
          <span
            className={cn(
              "inline-block rounded-full px-2 py-0.5 text-xs font-bold text-white",
              decisionBadgeClass,
            )}
          >
            {entry.decision}
          </span>
        </div>
      )}

      {error && (
        <div role="alert" className="mt-1.5 text-sm text-danger">
          {error}
        </div>
      )}

      {isPending && (
        <div className="mt-2 flex gap-1.5">
          <button
            type="button"
            className="cursor-pointer rounded border-0 bg-success px-3 py-1 text-sm font-semibold text-white"
            onClick={() => void submit("approved")}
            disabled={busy}
          >
            {busy ? "…" : "Approve"}
          </button>
          <button
            type="button"
            className="cursor-pointer rounded border-0 bg-danger px-3 py-1 text-sm font-semibold text-white"
            onClick={() => void submit("rejected")}
            disabled={busy}
          >
            {busy ? "…" : "Reject"}
          </button>
          <a
            href="/governance/approvals"
            className="rounded bg-transparent px-3 py-1 text-sm font-semibold text-primary underline"
          >
            Open governance page →
          </a>
        </div>
      )}
    </div>
  );
}
