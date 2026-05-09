/**
 * File: frontend/src/features/governance/components/DecisionModal.tsx
 * Purpose: Modal dialog with Approve / Reject / Escalate buttons + reason input — TanStack-driven mutation.
 * Category: Frontend / governance / components
 * Scope: Phase 53 / Sprint 53.5 US-1 → Sprint 57.9 US-2 Day 1 (Tailwind) → Sprint 57.9 US-3 Day 2 (TanStack)
 *
 * Description:
 *   Click-outside-to-close overlay + dialog with approval details, reason
 *   textarea, and 4 action buttons (Cancel / Escalate / Reject / Approve).
 *
 *   Sprint 57.9 US-3 Day 2: dropped legacy `onSubmit` callback prop — modal is
 *   now self-contained via `useApprovalDecide` mutation hook. On `mutate()`
 *   success the hook invalidates `APPROVALS_QUERY_KEY` (refreshes the list)
 *   and the modal calls `onClose()`. `isPending` from the mutation drives the
 *   busy / disabled state on action buttons; `error` from the mutation is
 *   surfaced inline.
 *
 *   Tailwind impl per Day 0 D-PRE-2 + Sprint 57.8 UserMenu YAGNI precedent.
 *
 * Created: 2026-05-04 (Sprint 53.5 Day 3)
 * Last Modified: 2026-05-09
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Sprint 57.9 US-3 Day 2 — drop onSubmit prop + useState/setBusy/setError → useApprovalDecide mutation
 *   - 2026-05-09: Sprint 57.9 US-2 Day 1 — Tailwind migration (drop inline styles)
 *   - 2026-05-04: Initial creation (Sprint 53.5 Day 3)
 *
 * Related:
 *   - ./ApprovalsPage.tsx (parent — passes approval + onClose only post-57.9-US-3)
 *   - ../hooks/useApprovalDecide.ts (TanStack mutation hook)
 */

import { useState } from "react";

import { useApprovalDecide } from "../hooks/useApprovalDecide";
import type { ApprovalSummary, DecisionLabel } from "../types";

type Props = {
  approval: ApprovalSummary;
  onClose: () => void;
};

const BUTTON_BASE =
  "rounded px-4 py-2 text-[0.95rem] font-semibold disabled:opacity-50 disabled:cursor-not-allowed";

const BUTTON_KIND: Record<"approve" | "reject" | "escalate" | "cancel", string> = {
  approve: "bg-[#2e7d32] text-white hover:bg-[#256a29]",
  reject: "bg-[#c62828] text-white hover:bg-[#b22222]",
  escalate: "bg-[#ed6c02] text-white hover:bg-[#d46002]",
  cancel: "bg-[#e0e0e0] text-[#333] hover:bg-[#d0d0d0]",
};

export function DecisionModal({ approval, onClose }: Props) {
  const [reason, setReason] = useState("");
  const decideM = useApprovalDecide();

  const submit = (decision: DecisionLabel) => {
    decideM.mutate(
      {
        requestId: approval.request_id,
        decision,
        reason: reason.trim() || undefined,
      },
      { onSuccess: onClose },
    );
  };

  const toolName = approval.payload.tool_name ?? "(unknown tool)";
  const summary = approval.payload.summary ?? approval.payload.reason ?? "";
  const busy = decideM.isPending;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/45"
      onClick={onClose}
      role="presentation"
    >
      <div
        className="min-w-[480px] max-w-[720px] rounded-lg bg-card p-6 font-sans shadow-2xl"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
      >
        <h3 className="m-0 mb-3 text-xl font-semibold">Review approval — {toolName}</h3>

        <div className="my-1.5 flex gap-2 text-[0.95rem]">
          <span className="min-w-[110px] font-semibold text-foreground/70">Request ID:</span>
          <code>{approval.request_id}</code>
        </div>
        <div className="my-1.5 flex gap-2 text-[0.95rem]">
          <span className="min-w-[110px] font-semibold text-foreground/70">Risk:</span>
          <span>{approval.risk_level}</span>
        </div>
        <div className="my-1.5 flex gap-2 text-[0.95rem]">
          <span className="min-w-[110px] font-semibold text-foreground/70">Requester:</span>
          <span>{approval.requester}</span>
        </div>
        <div className="my-1.5 flex gap-2 text-[0.95rem]">
          <span className="min-w-[110px] font-semibold text-foreground/70">SLA deadline:</span>
          <span>{new Date(approval.sla_deadline).toLocaleString()}</span>
        </div>
        {summary && (
          <div className="my-1.5 flex gap-2 text-[0.95rem]">
            <span className="min-w-[110px] font-semibold text-foreground/70">Reason:</span>
            <span>{summary}</span>
          </div>
        )}
        {approval.payload.tool_arguments && (
          <div className="my-1.5 flex gap-2 text-[0.95rem]">
            <span className="min-w-[110px] font-semibold text-foreground/70">Arguments:</span>
            <pre className="m-0 rounded bg-muted p-1.5 text-[0.85rem]">
              {JSON.stringify(approval.payload.tool_arguments, null, 2)}
            </pre>
          </div>
        )}

        <label className="mt-4 block text-[0.95rem] font-semibold">
          Reviewer reason (optional):
          <textarea
            className="mt-2 min-h-[80px] w-full resize-y rounded border border-border p-2 font-inherit text-[0.95rem]"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Optional context for the audit log"
            disabled={busy}
          />
        </label>

        {decideM.error && (
          <div role="alert" className="mt-2 text-[0.9rem] text-[#c62828]">
            {decideM.error.message}
          </div>
        )}

        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            className={`${BUTTON_BASE} ${BUTTON_KIND.cancel}`}
            onClick={onClose}
            disabled={busy}
          >
            Cancel
          </button>
          <button
            type="button"
            className={`${BUTTON_BASE} ${BUTTON_KIND.escalate}`}
            onClick={() => submit("escalated")}
            disabled={busy}
          >
            Escalate
          </button>
          <button
            type="button"
            className={`${BUTTON_BASE} ${BUTTON_KIND.reject}`}
            onClick={() => submit("rejected")}
            disabled={busy}
          >
            Reject
          </button>
          <button
            type="button"
            className={`${BUTTON_BASE} ${BUTTON_KIND.approve}`}
            onClick={() => submit("approved")}
            disabled={busy}
          >
            Approve
          </button>
        </div>
      </div>
    </div>
  );
}
