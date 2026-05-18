/**
 * File: frontend/src/features/chat_v2/components/turns/HITLTurn.tsx
 * Purpose: Renders HITL-role Turn — rich inline approval card per mockup L270-313.
 * Category: Frontend / chat_v2 / components / turns
 * Scope: Phase 57.21 (Day 2 — Option C cp+convert; AD-ChatV2-Full-Mockup-Fidelity Phase-1)
 *
 * Description:
 *   Per-turn shell with warning-tinted marker + head row "HITL approval
 *   required" + body renders inline rich approval card (severity-tinted
 *   border + bar + icon-ring + title + countdown + meta row + rationale
 *   + payload pre-block + 4 action buttons). Source: mockup
 *   reference/design-mockups/page-chat.jsx L270-313; styles
 *   reference/design-mockups/styles.css L845-897.
 *
 *   Phase-1 behavioral preservation: only Approve & continue + Reject
 *   wire to governanceService.decide(APPROVED | REJECTED). Approve with
 *   edits + Escalate to L2 render as disabled with tooltip indicating
 *   Sprint 57.22+ AD-ChatV2-HITL-FourAction-Phase2 carryover. SLA
 *   countdown + audit_id render placeholder "—" when fields null
 *   (backend SSE doesn't emit these yet — same epic deferral).
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 2 §2.1)
 *
 * Modification History (newest-first):
 *   - 2026-05-18: Sprint 57.21 Day 4 CI-FIX — render approval_id + SEVERITY_BADGE_LITERAL hex + hide buttons when decided (preserves approval-card.spec.ts L70+L108+L131/152 contracts)
 *   - 2026-05-17: Sprint 57.21 Day 4 D-DAY3-3 — add role="region" + aria-label="HITL approval" for e2e contract preservation (approval-card.spec.ts selector compatibility post-TurnList swap)
 *   - 2026-05-17: Initial extract from mockup L270-313 + Tailwind convert (Sprint 57.21 Day 2 §2.1)
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L270-313 (source JSX)
 *   - reference/design-mockups/styles.css L845-897 (hitl-card / hitl-head / hitl-meta / hitl-payload / hitl-actions)
 *   - ../../types.ts (HITLTurn + RiskSeverity types)
 *   - ../../../governance/services/governanceService.ts (decide POST)
 */

import { Check, Clock, FileText, Shield, X } from "lucide-react";
import { useCallback, useState } from "react";

import { governanceService } from "../../../governance/services/governanceService";
import { useChatStore } from "../../store/chatStore";
import type { HITLTurn as HITLTurnType, RiskSeverity } from "../../types";

const SEVERITY_BAR_CLASS: Record<RiskSeverity, string> = {
  "risk-low": "bg-risk-low",
  "risk-medium": "bg-risk-medium",
  "risk-high": "bg-risk-high",
  "risk-critical": "bg-risk-critical",
};

const SEVERITY_BORDER_CLASS: Record<RiskSeverity, string> = {
  "risk-low": "border-risk-low/60",
  "risk-medium": "border-risk-medium/60",
  "risk-high": "border-risk-high/60",
  "risk-critical": "border-risk-critical/60",
};

const SEVERITY_BG_CLASS: Record<RiskSeverity, string> = {
  "risk-low": "bg-risk-low/8",
  "risk-medium": "bg-risk-medium/8",
  "risk-high": "bg-risk-high/8",
  "risk-critical": "bg-risk-critical/10",
};

const SEVERITY_TEXT_CLASS: Record<RiskSeverity, string> = {
  "risk-low": "text-risk-low",
  "risk-medium": "text-risk-medium",
  "risk-high": "text-risk-high",
  "risk-critical": "text-risk-critical",
};

// Severity badge text colour literal hex per STYLE.md §3 Risk Badge Palette —
// Sprint 57.15 colour-literal sentinel preserved for approval-card.spec.ts L108
// (CRITICAL → computed color === "rgb(183,28,28)"). Token-based class
// `text-risk-critical` (CSS var) does NOT satisfy the literal assertion.
const SEVERITY_BADGE_LITERAL: Record<RiskSeverity, string> = {
  "risk-low": "text-[#2e7d32]",
  "risk-medium": "text-[#ed6c02]",
  "risk-high": "text-[#d84315]",
  "risk-critical": "text-[#b71c1c]",
};

export function HITLTurn({ turn }: { turn: HITLTurnType }): JSX.Element {
  const [submitting, setSubmitting] = useState<"approve" | "reject" | null>(null);
  const mergeEvent = useChatStore((s) => s.mergeEvent);

  const submitDecision = useCallback(
    async (decision: "approved" | "rejected") => {
      if (turn.decision !== null) return;
      setSubmitting(decision === "approved" ? "approve" : "reject");
      try {
        await governanceService.decide(turn.approvalRequestId, decision);
        // Optimistic update: chatStore.mergeEvent will overwrite when
        // ApprovalReceived SSE arrives. Force-set uppercase form here
        // (backend canonical wire format) so UI reflects immediately
        // without waiting for SSE round-trip.
        mergeEvent({
          type: "approval_received",
          data: {
            approval_request_id: turn.approvalRequestId,
            decision: decision.toUpperCase(),
          },
        });
      } finally {
        setSubmitting(null);
      }
    },
    [turn.approvalRequestId, turn.decision, mergeEvent],
  );

  const decided = turn.decision !== null;
  const severity = turn.severity;
  const countdownLabel = turn.countdownSec !== null ? `${turn.countdownSec}s` : "—";

  return (
    <div
      className="relative border-b border-border bg-bg px-6 py-3.5"
      data-role="hitl"
      role="region"
      aria-label="HITL approval"
    >
      <div className="absolute bottom-0 left-[10px] top-0 w-px bg-border" />
      <div className="absolute left-[6px] top-[18px] h-[9px] w-[9px] rounded-full border-2 border-warning bg-warning" />
      <div className="mb-2 flex items-center gap-2 pl-[22px] text-[11px] text-fg-muted">
        <span className="text-xs font-semibold text-warning">HITL approval required</span>
        <span className="rounded border border-warning/40 bg-warning/15 px-1.5 py-px font-mono text-[10.5px] text-warning">
          always_ask
        </span>
        <span className="font-mono text-fg-subtle">· {turn.at}</span>
      </div>
      <div className="pl-[22px]">
        <div
          className={`relative my-2 overflow-hidden rounded-md border-[1.5px] p-3.5 ${SEVERITY_BORDER_CLASS[severity]} ${SEVERITY_BG_CLASS[severity]}`}
          data-severity={severity}
          data-testid="hitl-card"
        >
          <div className={`absolute bottom-0 left-0 top-0 w-[3px] ${SEVERITY_BAR_CLASS[severity]}`} />
          <div className="mb-1 flex items-center gap-2 text-[13px] font-semibold">
            <span
              className={`flex h-[22px] w-[22px] items-center justify-center rounded-full ${SEVERITY_BG_CLASS[severity]} ${SEVERITY_TEXT_CLASS[severity]}`}
            >
              <Shield size={13} />
            </span>
            <span className="flex-1">{turn.title}</span>
            <span className="ml-auto flex items-center gap-1 font-mono text-[11px] text-fg-muted">
              <Clock size={11} />
              SLA <span className={SEVERITY_TEXT_CLASS[severity]}>{countdownLabel}</span>
            </span>
          </div>
          <div className="mb-2.5 flex flex-wrap gap-3 text-[11.5px] text-fg-muted">
            <span className="flex items-center gap-1.5">
              severity:{" "}
              <span className={`rounded px-1.5 py-px font-mono text-[10.5px] ${SEVERITY_BG_CLASS[severity]} ${SEVERITY_BADGE_LITERAL[severity]}`}>
                {severity.replace("risk-", "").toUpperCase()}
              </span>
            </span>
            <span className="flex items-center gap-1.5">
              tool: <span className="font-mono text-tool">{turn.tool}</span>
            </span>
            <span className="flex items-center gap-1.5">
              policy:{" "}
              <span className="rounded border border-border bg-bg-2 px-1.5 py-px font-mono text-[10.5px] text-fg-muted">
                always_ask
              </span>
            </span>
          </div>
          {turn.rationale !== "—" && (
            <div className="mb-1.5 text-[12.5px] text-fg-muted">
              <strong className="font-semibold text-fg">Rationale.</strong> {turn.rationale}
            </div>
          )}
          {turn.payload !== "—" && (
            <pre className="my-2 max-h-[120px] overflow-y-auto whitespace-pre-wrap rounded-md border border-border bg-bg-1 p-2.5 font-mono text-[11px]">
              {turn.payload}
            </pre>
          )}
          {!decided && (
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                aria-label="Approve"
                disabled={submitting !== null}
                onClick={() => submitDecision("approved")}
                className="inline-flex items-center gap-1.5 rounded-md bg-success px-3 py-1.5 text-xs font-medium text-white shadow-sm transition hover:bg-success/90 disabled:cursor-not-allowed disabled:opacity-60"
                data-testid="approve-btn"
              >
                <Check size={12} />
                Approve &amp; continue
              </button>
              <button
                type="button"
                aria-label="Reject"
                disabled={submitting !== null}
                onClick={() => submitDecision("rejected")}
                className="inline-flex items-center gap-1.5 rounded-md bg-risk-critical px-3 py-1.5 text-xs font-medium text-white shadow-sm transition hover:bg-risk-critical/90 disabled:cursor-not-allowed disabled:opacity-60"
                data-testid="reject-btn"
              >
                <X size={12} />
                Reject
              </button>
              {/* "Approve with edits" + "Escalate to L2" 4-action UX deferred to
                  Phase-2 AD-ChatV2-HITL-FourAction-Phase2 — backend needs APPROVED_WITH_EDITS
                  variant + payload editor + escalate routing. Phase-1 ships canonical
                  2-action subset (matches Sprint 53.5 baseline + e2e contract). */}
            </div>
          )}
          {/* approval_id always visible (e2e contract approval-card.spec.ts L70);
              audit_id placeholder until Phase-2 AD-ChatV2-HITL-FourAction-Phase2. */}
          <div className="mt-2 flex flex-wrap items-center gap-3 text-[11px] text-fg-subtle">
            <span className="flex items-center gap-1.5">
              <FileText size={12} />
              <span className="font-mono">approval_id: {turn.approvalRequestId}</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="font-mono">audit_id: —</span>
            </span>
          </div>
          {decided && (
            <div
              className={`mt-2.5 rounded-md px-2.5 py-1.5 text-xs font-medium ${SEVERITY_BG_CLASS[severity]} ${SEVERITY_TEXT_CLASS[severity]}`}
              data-testid="hitl-decision"
            >
              Decision: {turn.decision}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
