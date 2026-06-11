/**
 * File: frontend/src/features/chat_v2/components/turns/HITLTurn.tsx
 * Purpose: Renders HITL-role Turn — verbatim mockup re-point of L270-313 inline approval card.
 * Category: Frontend / chat_v2 / components / turns
 * Scope: Phase 57.21 (Day 2 — Option C cp+convert; AD-ChatV2-Full-Mockup-Fidelity Phase-1)
 *
 * Description:
 *   Per-turn shell with warning-tinted marker + head row "HITL approval
 *   required" + body renders inline rich approval card (severity-tinted
 *   border + bar + icon-ring + title + countdown + meta row + rationale
 *   + payload pre-block + 4 action buttons). Source: mockup
 *   reference/design-mockups/page-chat.jsx L270-313; styles
 *   styles-mockup.css L742-771 (.turn / .turn-rail / .turn-marker /
 *   .turn-head / .turn-body) + L845-897 (.hitl-card / .hitl-card-bar /
 *   .hitl-head .icon-ring / .hitl-meta / .hitl-payload / .hitl-actions /
 *   .hitl-countdown) + L426-460 (.btn primary/success/danger/outline/ghost
 *   variants) + L507-535 (.badge + .badge.warning).
 *
 *   Sprint 57.30 Day 3: re-pointed from translated-Tailwind utility classes
 *   to verbatim mockup `.turn` shell + `.hitl-card` + family classes +
 *   `.btn` button system. Severity bar/border/bg now CSS-owned via
 *   `[data-severity]` selectors in styles-mockup.css L854-867 (covers
 *   risk-critical + risk-high explicitly; risk-low / risk-medium fall back
 *   to base warning tones from .hitl-card — acceptable per mockup
 *   defaults). Marker warning override + role color inline-style
 *   preserved from mockup L273+L275 verbatim.
 *
 *   CRITICAL e2e contract preservation (approval-card.spec.ts):
 *   - L70 expects card text contains approval_id → preserved via
 *     "approval_id: {approvalRequestId}" mono row
 *   - L71 expects "HIGH" text in card → preserved via uppercase severity
 *   - L82+L105 expect "Decision" text + APPROVED/REJECTED → preserved via
 *     decided-state banner
 *   - L121-128 expects getComputedStyle(severity-badge).color ===
 *     "rgb(183,28,28)" for CRITICAL → preserved via inline-style literal
 *     hex (#b71c1c) in SEVERITY_BADGE_LITERAL_HEX. Token-based class
 *     (CSS var) does NOT satisfy this literal assertion.
 *   - data-testid hitl-card / approve-btn / reject-btn / hitl-decision
 *     preserved verbatim
 *
 *   Phase-1 behavioral preservation: only Approve & continue + Reject
 *   wire to governanceService.decide(APPROVED | REJECTED). "Approve with
 *   edits" + "Escalate to L2" 4-action UX deferred to Phase-2
 *   AD-ChatV2-HITL-FourAction-Phase2. SLA countdown + audit_id render
 *   placeholder "—" when fields null.
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 2 §2.1)
 *
 * Modification History (newest-first):
 *   - 2026-06-10: Sprint 57.100 — verification reject-with-note (coaching input + resume); kind-aware meta row
 *   - 2026-05-23: Sprint 57.30 Day 3 §D1 — verbatim re-point Tailwind → mockup .turn/.hitl-card/.btn + preserve SEVERITY_BADGE_LITERAL_HEX e2e contract
 *   - 2026-05-18: Sprint 57.21 Day 4 CI-FIX — render approval_id + SEVERITY_BADGE_LITERAL hex + hide buttons when decided (preserves approval-card.spec.ts L70+L108+L131/152 contracts)
 *   - 2026-05-17: Sprint 57.21 Day 4 D-DAY3-3 — add role="region" + aria-label="HITL approval" for e2e contract preservation (approval-card.spec.ts selector compatibility post-TurnList swap)
 *   - 2026-05-17: Initial extract from mockup L270-313 + Tailwind convert (Sprint 57.21 Day 2 §2.1)
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L270-313 (source JSX)
 *   - frontend/src/styles-mockup.css L845-897 (.hitl-card / .hitl-card-bar / .hitl-head / .hitl-meta / .hitl-payload / .hitl-actions / .hitl-countdown / .icon-ring)
 *   - frontend/src/styles-mockup.css L426-460 (.btn primary/success/danger/outline/ghost)
 *   - frontend/src/styles-mockup.css L742-771 (.turn shell)
 *   - ../../types.ts (HITLTurn + RiskSeverity types)
 *   - ../../../governance/services/governanceService.ts (decide POST)
 *   - tests/e2e/chat/approval-card.spec.ts (L70/L71/L82/L105/L121-128 selector + literal contracts)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: mockup page-chat.jsx L273
   (marker warning override) + L275 (role color: var(--warning)) + L287 (countdown color)
   + L291-294 (.row inline gap) + L296-298 (rationale inline-style font/color) + L306-308
   (audit_id row inline) all use inline-style. SEVERITY_BADGE_LITERAL_HEX must use literal
   hex so getComputedStyle(badge).color === "rgb(183,28,28)" (approval-card.spec.ts L128). */

import { Check, Clock, FileText, Shield, X } from "lucide-react";
import { useCallback, useState } from "react";

import { governanceService } from "../../../governance/services/governanceService";
import { useLoopEventStream } from "../../hooks/useLoopEventStream";
import { useChatStore } from "../../store/chatStore";
import type { HITLTurn as HITLTurnType, RiskSeverity } from "../../types";

// Severity badge text colour literal hex per STYLE.md §3 Risk Badge Palette —
// Sprint 57.15 colour-literal sentinel preserved for approval-card.spec.ts L128
// (CRITICAL → computed color === "rgb(183,28,28)"). Token-based class (CSS var)
// does NOT satisfy the literal assertion — inline-style hex required.
const SEVERITY_BADGE_LITERAL_HEX: Record<RiskSeverity, string> = {
  "risk-low": "#2e7d32",
  "risk-medium": "#ed6c02",
  "risk-high": "#d84315",
  "risk-critical": "#b71c1c",
};

// Severity tone for the small badge background tint — mockup uses RiskBadge
// component (L291 `<RiskBadge level="high" />`). The mockup CSS .badge.risk-X
// classes (styles-mockup.css L532-535) provide background + border tints.
const SEVERITY_BADGE_TONE: Record<RiskSeverity, string> = {
  "risk-low": "risk-low",
  "risk-medium": "risk-medium",
  "risk-high": "risk-high",
  "risk-critical": "risk-critical",
};

export function HITLTurn({ turn }: { turn: HITLTurnType }): JSX.Element {
  const [submitting, setSubmitting] = useState<"approve" | "reject" | null>(null);
  // Sprint 57.100: a verification-ESCALATE reject reveals a coaching-note input
  // (the backend coaches exactly one human-guided turn — A2). Other kinds reject
  // immediately (terminate — the tool never runs).
  const [showNoteInput, setShowNoteInput] = useState(false);
  const [rejectNote, setRejectNote] = useState("");
  const isVerification = turn.kind === "verification";
  const mergeEvent = useChatStore((s) => s.mergeEvent);
  // Sprint 57.88 (US-5): resume the deferred-paused loop after an approve.
  const { resume } = useLoopEventStream();

  const submitDecision = useCallback(
    async (decision: "approved" | "rejected", note?: string) => {
      if (turn.decision !== null) return;
      setSubmitting(decision === "approved" ? "approve" : "reject");
      try {
        await governanceService.decide(turn.approvalRequestId, decision, note);
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
        // Sprint 57.88 (US-5): durable HITL pause-resume. ONLY the deferred
        // pause flow (loop_end with stop_reason="awaiting_approval", SSE stream
        // already closed) needs a client-driven resume; the legacy BLOCKING
        // HITL flow (Sprint 53.5/53.6) continues server-side on the SAME open
        // stream, so it must NOT be resumed here (guarded on stopReason).
        // Sprint 57.100: APPROVE always resumes; a verification REJECT ALSO
        // resumes (the backend coaches one human-guided turn — A2). Other kinds'
        // reject leaves the loop terminated (the tool never runs).
        const shouldResume =
          decision === "approved" || (decision === "rejected" && isVerification);
        if (
          shouldResume &&
          useChatStore.getState().stopReason === "awaiting_approval"
        ) {
          await resume();
        }
      } finally {
        setSubmitting(null);
      }
    },
    [turn.approvalRequestId, turn.decision, mergeEvent, resume, isVerification],
  );

  const decided = turn.decision !== null;
  const severity = turn.severity;
  const countdownLabel = turn.countdownSec !== null ? `${turn.countdownSec}s` : "—";
  const severityLabel = severity.replace("risk-", "").toUpperCase();
  const badgeHex = SEVERITY_BADGE_LITERAL_HEX[severity];

  return (
    <div className="turn" data-role="hitl" role="region" aria-label="HITL approval">
      <div className="turn-rail" />
      <div
        className="turn-marker"
        style={{ background: "var(--warning)", borderColor: "var(--warning)" }}
      />
      <div className="turn-head">
        <span className="role" style={{ color: "var(--warning)" }}>
          HITL approval required
        </span>
        <span className="badge warning">always_ask</span>
        <span className="mono subtle">· {turn.at}</span>
      </div>
      <div className="turn-body">
        <div className="hitl-card" data-severity={severity} data-testid="hitl-card">
          <div className="hitl-card-bar" />
          <div className="hitl-head">
            <span className="icon-ring">
              <Shield size={13} />
            </span>
            <span style={{ flex: 1 }}>{turn.title}</span>
            <span className="hitl-countdown">
              <Clock size={11} />
              SLA <span style={{ color: "var(--warning)" }}>{countdownLabel}</span>
            </span>
          </div>
          <div className="hitl-meta">
            <span className="row" style={{ gap: 5 }}>
              severity:{" "}
              <span
                className={`badge ${SEVERITY_BADGE_TONE[severity]}`}
                style={{ color: badgeHex }}
              >
                {severityLabel}
              </span>
            </span>
            <span className="row" style={{ gap: 5 }}>
              {isVerification ? "kind:" : "tool:"}{" "}
              <span className="mono" style={{ color: "var(--tool)" }}>
                {isVerification ? "verification" : turn.tool}
              </span>
            </span>
            <span className="row" style={{ gap: 5 }}>
              policy: <span className="badge">always_ask</span>
            </span>
          </div>
          {turn.rationale !== "—" && (
            <div style={{ fontSize: 12.5, color: "var(--fg-muted)", marginBottom: 6 }}>
              <strong style={{ color: "var(--fg)", fontWeight: 600 }}>Rationale.</strong>{" "}
              {turn.rationale}
            </div>
          )}
          {turn.payload !== "—" && <div className="hitl-payload">{turn.payload}</div>}
          {!decided && (
            <>
              <div className="hitl-actions">
                <button
                  type="button"
                  aria-label="Approve"
                  disabled={submitting !== null}
                  onClick={() => submitDecision("approved")}
                  className="btn success"
                  data-size="sm"
                  data-testid="approve-btn"
                >
                  <Check size={12} />
                  Approve &amp; continue
                </button>
                <button
                  type="button"
                  aria-label="Reject"
                  disabled={submitting !== null}
                  // Sprint 57.100: a verification reject reveals the coaching-note
                  // input (the backend coaches one human-guided turn — A2);
                  // every other kind rejects immediately (terminate).
                  onClick={() =>
                    isVerification ? setShowNoteInput(true) : submitDecision("rejected")
                  }
                  className="btn danger"
                  data-size="sm"
                  data-testid="reject-btn"
                >
                  <X size={12} />
                  Reject
                </button>
                {/* "Approve with edits" + "Escalate to L2" 4-action UX deferred to
                    Phase-2 AD-ChatV2-HITL-FourAction-Phase2 — backend needs APPROVED_WITH_EDITS
                    variant + payload editor + escalate routing. Phase-1 ships canonical
                    2-action subset (matches Sprint 53.5 baseline + e2e contract). */}
                <span
                  className="row subtle"
                  style={{ marginLeft: "auto", fontSize: 11, gap: 5 }}
                >
                  <FileText size={12} />
                  <span className="mono">audit_id: —</span>
                </span>
              </div>
              {/* Sprint 57.100: verification-ESCALATE coaching note. No mockup
                  source for this element (page-chat.jsx L270-313 has no HITL note
                  input) → design-system vocab only (var(--*) tokens, no new
                  HEX/oklch). The note rides ApprovalDecision.reason → the backend
                  re-injects it as a user correction for one human-coached turn. */}
              {isVerification && showNoteInput && (
                <div style={{ marginTop: 8 }}>
                  <textarea
                    aria-label="Coaching note"
                    data-testid="reject-note"
                    value={rejectNote}
                    onChange={(e) => setRejectNote(e.target.value)}
                    placeholder="Coaching note for the agent (optional)…"
                    rows={2}
                    style={{
                      width: "100%",
                      boxSizing: "border-box",
                      fontFamily: "inherit",
                      fontSize: 12.5,
                      padding: "6px 8px",
                      borderRadius: "var(--radius-sm)",
                      border: "1px solid var(--border)",
                      background: "var(--bg-1)",
                      color: "var(--fg)",
                      resize: "vertical",
                      marginBottom: 6,
                    }}
                  />
                  <div className="hitl-actions">
                    <button
                      type="button"
                      aria-label="Reject with note"
                      disabled={submitting !== null}
                      onClick={() => submitDecision("rejected", rejectNote)}
                      className="btn danger"
                      data-size="sm"
                      data-testid="reject-confirm-btn"
                    >
                      <X size={12} />
                      Reject &amp; coach
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
          {/* approval_id always visible (e2e contract approval-card.spec.ts L70). */}
          <div
            className="row"
            style={{
              marginTop: 8,
              gap: 12,
              flexWrap: "wrap",
              fontSize: 11,
              color: "var(--fg-subtle)",
            }}
          >
            <span className="row" style={{ gap: 5 }}>
              <FileText size={12} />
              <span className="mono">approval_id: {turn.approvalRequestId}</span>
            </span>
          </div>
          {decided && (
            <div
              data-testid="hitl-decision"
              style={{
                marginTop: 10,
                padding: "6px 10px",
                borderRadius: "var(--radius-sm)",
                fontSize: 12,
                fontWeight: 500,
                background: "var(--bg-2)",
                color: "var(--fg)",
              }}
            >
              Decision: {turn.decision}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
