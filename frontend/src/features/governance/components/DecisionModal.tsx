/**
 * File: frontend/src/features/governance/components/DecisionModal.tsx
 * Purpose: Modal dialog with Approve / Reject / Escalate buttons + reason input — TanStack-driven mutation.
 * Category: Frontend / governance / components
 * Scope: Phase 53 / Sprint 53.5 US-1 → Sprint 57.9 US-2/3 (Tailwind + TanStack) → Sprint 57.13 US-B3 (Radix Dialog)
 *
 * Description:
 *   Self-contained approval-review dialog. Mounted/unmounted by ApprovalsPage
 *   (`{selected && <DecisionModal approval onClose />}`), so it drives Radix in
 *   controlled mode: `<Dialog open onOpenChange={(o) => !o && onClose()}>`. Shows
 *   approval details + a reason textarea + 4 actions (Cancel / Escalate / Reject /
 *   Approve). On `mutate()` success `useApprovalDecide` invalidates the approvals
 *   query and the modal closes; `isPending` drives the busy state; `error` is
 *   surfaced inline.
 *
 *   Sprint 57.13 US-B3: replaced the hand-rolled overlay + stopPropagation panel
 *   with components/ui <Dialog> (Radix) — focus trap, ESC, outside-click close,
 *   and aria title/dialog wiring come for free. The action buttons keep their
 *   semantic colours (green/red/orange) — `<Button>` variants don't carry those.
 *
 * Created: 2026-05-04 (Sprint 53.5 Day 3)
 * Last Modified: 2026-05-25
 *
 * Modification History (newest-first):
 *   - 2026-05-25: FIX-015 — re-point shadcn-utility tokens (bg-muted/text-foreground/border-border/etc.) → mockup verbatim classes/vars
 *   - 2026-05-10: Sprint 57.13 US-B3 — overlay+panel → components/ui <Dialog> (Radix)
 *   - 2026-05-09: Sprint 57.9 US-3 Day 2 — drop onSubmit prop + useState/setBusy/setError → useApprovalDecide mutation
 *   - 2026-05-09: Sprint 57.9 US-2 Day 1 — Tailwind migration (drop inline styles)
 *   - 2026-05-04: Initial creation (Sprint 53.5 Day 3)
 *
 * Related:
 *   - ./ApprovalsPage.tsx (parent — mounts/unmounts; passes approval + onClose)
 *   - ../hooks/useApprovalDecide.ts (TanStack mutation hook)
 *   - ../../../components/ui/dialog.tsx (Radix Dialog wrapper)
 */

import { useState } from "react";

import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "../../../components/ui";
import { useApprovalDecide } from "../hooks/useApprovalDecide";
import type { ApprovalSummary, DecisionLabel } from "../types";

type Props = {
  approval: ApprovalSummary;
  onClose: () => void;
};

const BUTTON_KIND: Record<"approve" | "reject" | "escalate" | "cancel", string> = {
  approve: "btn success",
  reject: "btn danger",
  escalate: "btn warning",
  cancel: "btn outline",
};

const ROW = "my-1.5 flex gap-2 text-[0.95rem]";
const ROW_LABEL = "min-w-[110px] font-semibold";

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
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent className="max-w-[720px] font-sans">
        <DialogHeader>
          <DialogTitle>Review approval — {toolName}</DialogTitle>
        </DialogHeader>

        <div>
          <div className={ROW}>
            <span className={ROW_LABEL}>Request ID:</span>
            <code>{approval.request_id}</code>
          </div>
          <div className={ROW}>
            <span className={ROW_LABEL}>Risk:</span>
            <span>{approval.risk_level}</span>
          </div>
          <div className={ROW}>
            <span className={ROW_LABEL}>Requester:</span>
            <span>{approval.requester}</span>
          </div>
          <div className={ROW}>
            <span className={ROW_LABEL}>SLA deadline:</span>
            <span>{new Date(approval.sla_deadline).toLocaleString()}</span>
          </div>
          {summary && (
            <div className={ROW}>
              <span className={ROW_LABEL}>Reason:</span>
              <span>{summary}</span>
            </div>
          )}
          {approval.payload.tool_arguments && (
            <div className={ROW}>
              <span className={ROW_LABEL}>Arguments:</span>
              <pre
                className="m-0 p-1.5 text-[0.85rem]"
                style={{
                  background: "var(--bg-2)",
                  border: "1px solid var(--border)",
                  borderRadius: 6,
                  fontFamily: "var(--font-mono)",
                }}
              >
                {JSON.stringify(approval.payload.tool_arguments, null, 2)}
              </pre>
            </div>
          )}
        </div>

        <label className="block text-[0.95rem] font-semibold">
          Reviewer reason (optional):
          <textarea
            className="textarea mt-2 w-full"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Optional context for the audit log"
            disabled={busy}
          />
        </label>

        {decideM.error && (
          <div role="alert" className="text-[0.9rem]" style={{ color: "var(--danger)" }}>
            {decideM.error.message}
          </div>
        )}

        <DialogFooter>
          <button
            type="button"
            className={BUTTON_KIND.cancel}
            onClick={onClose}
            disabled={busy}
          >
            Cancel
          </button>
          <button
            type="button"
            className={BUTTON_KIND.escalate}
            onClick={() => submit("escalated")}
            disabled={busy}
          >
            Escalate
          </button>
          <button
            type="button"
            className={BUTTON_KIND.reject}
            onClick={() => submit("rejected")}
            disabled={busy}
          >
            Reject
          </button>
          <button
            type="button"
            className={BUTTON_KIND.approve}
            onClick={() => submit("approved")}
            disabled={busy}
          >
            Approve
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
