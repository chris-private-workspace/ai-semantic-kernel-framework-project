/**
 * File: frontend/src/features/chat_v2/components/ApprovalCard.tsx
 * Purpose: Inline HITL approval fallback card — verbatim mockup re-point of .hitl-card family.
 * Category: Frontend / chat_v2 / components
 * Scope: Phase 57.30 Day 4 §D4 (AD-Mockup-Direct-Port-Round-2 chatv2 shell repoint)
 *
 * Description:
 *   Phase-1 dual-emit fallback widget: when SSE emits ApprovalRequested,
 *   chatStore.mergeEvent populates both (a) approvals dict (this widget
 *   consumes) and (b) HITLTurn in turns array (chat-inline; HITLTurn.tsx).
 *   This widget is the legacy Sprint 53.5 path preserved for compat;
 *   the canonical Phase-1 chat-inline render is HITLTurn.
 *
 *   Visual: verbatim mockup `.hitl-card` family classes (border + bar +
 *   meta + payload + actions) per styles-mockup.css L845-897 — matches
 *   HITLTurn re-point shape so two mount contexts share the mockup
 *   visual layer. Approve / Reject buttons use verbatim `.btn success` /
 *   `.btn danger` mockup classes (styles-mockup.css L458-459 / L454-455).
 *
 *   CRITICAL e2e contract preservation (approval-card.spec.ts):
 *   - role="region" aria-label="HITL approval" → preserved
 *   - Card contains approvalRequestId text → preserved
 *   - "HIGH"/"MEDIUM"/"CRITICAL" risk text → preserved via uppercase
 *     entry.riskLevel
 *   - "Decision" + "APPROVED"/"REJECTED" text → preserved via decided
 *     banner
 *   - CRITICAL risk text computed color === rgb(183, 28, 28) → preserved
 *     via inline-style RISK_TEXT_HEX literal lookup (token CSS var does
 *     NOT satisfy literal assertion — inline hex required, parallel to
 *     HITLTurn SEVERITY_BADGE_LITERAL_HEX)
 *   - <button name="Approve" />, <button name="Reject" /> → preserved
 *
 *   Sprint 57.30 Day 4: re-pointed from Tailwind utility translations
 *   (border-warning bg-warning/10 px-4 py-3 + cn() + arbitrary
 *   text-[#b71c1c] etc.) to verbatim mockup `.hitl-card` family +
 *   `.btn success`/`.btn danger` system. Risk text hex preserved as
 *   inline-style literal for e2e contract; all other colors via
 *   var(--*) tokens.
 *
 * Created: 2026-05-04 (Sprint 53.5 Day 4 US-2)
 * Last Modified: 2026-05-23
 *
 * Modification History (newest-first):
 *   - 2026-05-23: Sprint 57.30 Day 4 §D4 — verbatim re-point Tailwind → mockup .hitl-card family + .btn success/danger; preserve approval-card.spec.ts L70/L82/L121-128 contracts
 *   - 2026-05-17: Sprint 57.20 Day 3 US-D1 — token migration text-muted-foreground→text-fg-muted; bg-muted-foreground→bg-fg-muted for new shell mockup consistency
 *   - 2026-05-11: Sprint 57.15 — inline styles → Tailwind utility classes; risk colours per STYLE.md §3 (AD-Inline-Style-Cleanup-Sweep)
 *   - 2026-05-04: Initial creation (Sprint 53.5 Day 4 US-2)
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L270-313 (HITLTurn reference shape)
 *   - frontend/src/styles-mockup.css L845-897 (.hitl-card / .hitl-card-bar / .hitl-head / .hitl-meta / .hitl-actions)
 *   - frontend/src/styles-mockup.css L426-460 (.btn success/danger/ghost)
 *   - ../store/chatStore.ts (approvals slice — fallback dict)
 *   - ../../governance/services/governanceService.ts (decide call)
 *   - features/chat_v2/components/turns/HITLTurn.tsx (canonical Phase-1 chat-inline render)
 *   - tests/e2e/chat/approval-card.spec.ts (L70/L71/L82/L105/L121-128 selector + literal contracts)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: RISK_TEXT_HEX_LITERAL must
   use literal hex for getComputedStyle(risk-text).color === "rgb(183,28,28)" assertion
   (approval-card.spec.ts L128 CRITICAL contract). Token CSS var does NOT satisfy literal.
   All other styling via mockup CSS classes + var(--*) inline-style. */

import { useState } from "react";

import { governanceService } from "../../governance/services/governanceService";
import type { DecisionLabel } from "../../governance/types";
import { useChatStore } from "../store/chatStore";

// Risk text literal hex per STYLE.md §3 Risk Badge Palette — canonical 53.5
// hex matches HITLTurn.SEVERITY_BADGE_LITERAL_HEX. Inline-style required
// (CSS var does NOT satisfy approval-card.spec.ts L128 literal assertion).
const RISK_TEXT_HEX_LITERAL: Record<string, string> = {
  LOW: "#2e7d32",
  MEDIUM: "#ed6c02",
  HIGH: "#d84315",
  CRITICAL: "#b71c1c",
};

// Decision badge mockup class per outcome — uses .badge family (semantic tokens).
const DECISION_BADGE_CLASS: Record<string, string> = {
  APPROVED: "badge success",
  REJECTED: "badge danger",
  ESCALATED: "badge warning",
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

  const riskHex = RISK_TEXT_HEX_LITERAL[entry.riskLevel] ?? undefined;
  const isPending = entry.decision === null;
  const decisionBadgeClass =
    DECISION_BADGE_CLASS[entry.decision ?? ""] ?? "badge";

  return (
    <div
      className="hitl-card"
      role="region"
      aria-label="HITL approval"
    >
      <div className="hitl-card-bar" />
      <div className="hitl-head">
        <span>
          🔔 Approval requested —{" "}
          <span style={{ fontWeight: 700, color: riskHex }}>{entry.riskLevel}</span> risk
        </span>
      </div>
      <div className="hitl-meta">
        <span>
          Request ID: <code className="mono">{approvalRequestId}</code>
        </span>
      </div>

      {!isPending && (
        <div style={{ marginTop: 8, fontSize: 12 }}>
          Decision: <span className={decisionBadgeClass}>{entry.decision}</span>
        </div>
      )}

      {error && (
        <div
          role="alert"
          style={{ marginTop: 6, fontSize: 12, color: "var(--danger)" }}
        >
          {error}
        </div>
      )}

      {isPending && (
        <div className="hitl-actions" style={{ marginTop: 8 }}>
          <button
            type="button"
            className="btn success"
            data-size="sm"
            onClick={() => void submit("approved")}
            disabled={busy}
          >
            {busy ? "…" : "Approve"}
          </button>
          <button
            type="button"
            className="btn danger"
            data-size="sm"
            onClick={() => void submit("rejected")}
            disabled={busy}
          >
            {busy ? "…" : "Reject"}
          </button>
          <a
            href="/governance/approvals"
            className="btn ghost"
            data-size="sm"
            style={{ textDecoration: "none" }}
          >
            Open governance page →
          </a>
        </div>
      )}
    </div>
  );
}
