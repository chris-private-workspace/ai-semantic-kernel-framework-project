/**
 * File: frontend/src/features/governance/components/ApprovalList.tsx
 * Purpose: Tabular list of pending approvals; row click → DecisionModal.
 * Category: Frontend / governance / components
 * Scope: Phase 53 / Sprint 53.5 US-1 → Sprint 57.9 US-2 Day 1 (Tailwind migration)
 *
 * Description:
 *   Renders pending approvals as table; tool / risk / requester / reason / time-left / action.
 *   Click "Review" → onSelect callback (parent opens DecisionModal).
 *
 *   Sprint 57.9 US-2 Day 1: inline `style={{}}` migrated to Tailwind utility classes.
 *   Risk badge palette preserved via arbitrary-value Tailwind classes
 *   (text-[#hex]) — regression sentinel for any test asserting computed color.
 *
 * Created: 2026-05-04 (Sprint 53.5 Day 3)
 * Last Modified: 2026-05-25
 *
 * Modification History (newest-first):
 *   - 2026-05-25: FIX-015 — re-point shadcn-utility tokens (bg-muted/border-border/etc.) → mockup verbatim classes/vars
 *   - 2026-05-09: Sprint 57.9 US-2 Day 1 — Tailwind migration (drop inline styles)
 *   - 2026-05-04: Initial creation (Sprint 53.5 Day 3)
 *
 * Related:
 *   - ./ApprovalsPage.tsx (parent owns state + fetch)
 */

import type { ApprovalSummary, RiskLevelLabel } from "../types";

type Props = {
  approvals: ApprovalSummary[];
  onSelect: (approval: ApprovalSummary) => void;
};

// Preserve exact 53.5 palette via Tailwind arbitrary-value class (test sentinel).
const RISK_COLOR_CLASS: Record<RiskLevelLabel, string> = {
  LOW: "text-[#2e7d32]",
  MEDIUM: "text-[#ed6c02]",
  HIGH: "text-[#d84315]",
  CRITICAL: "text-[#b71c1c]",
};

function formatAge(sla: string): string {
  const ms = new Date(sla).getTime() - Date.now();
  if (Number.isNaN(ms)) return "—";
  const minutes = Math.round(ms / 60_000);
  if (minutes < 0) return "expired";
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.round(minutes / 60);
  return `${hours}h`;
}

export function ApprovalList({ approvals, onSelect }: Props) {
  if (approvals.length === 0) {
    return <p className="subtle my-4 italic">No pending approvals.</p>;
  }
  return (
    <table className="table">
      <thead>
        <tr>
          <th>Tool</th>
          <th>Risk</th>
          <th>Requester</th>
          <th>Reason</th>
          <th>Time left</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        {approvals.map((approval) => {
          const toolName = approval.payload.tool_name ?? "(unknown)";
          const reason = approval.payload.reason ?? "";
          return (
            <tr key={approval.request_id}>
              <td>{toolName}</td>
              <td>
                <span className={`font-semibold ${RISK_COLOR_CLASS[approval.risk_level]}`}>
                  {approval.risk_level}
                </span>
              </td>
              <td>{approval.requester}</td>
              <td>{reason}</td>
              <td>{formatAge(approval.sla_deadline)}</td>
              <td>
                <button
                  type="button"
                  onClick={() => onSelect(approval)}
                  className="btn outline"
                >
                  Review
                </button>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
