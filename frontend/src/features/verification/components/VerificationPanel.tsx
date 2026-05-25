/**
 * File: frontend/src/features/verification/components/VerificationPanel.tsx
 * Purpose: Inline verification events panel for chat-v2 (US-5 Sprint 57.11 Day 3 §3.5).
 * Category: Frontend / verification / components
 * Scope: Phase 57 / Sprint 57.11 Day 3 / US-5
 *
 * Description:
 *   Subscribes to chatStore.verifications array and renders compact cards for
 *   each VerificationPassed / VerificationFailed event:
 *     - Failed: red left border + reason snippet + suggested_correction
 *     - Passed: green left border + score (when present)
 *     - Both: VerifierTypeBadge + verifier name
 *
 *   Hidden when verifications.length === 0 (no empty card; conditional render
 *   at top — preserves chat-v2 layout when verification not active).
 *
 * Created: 2026-05-10 (Sprint 57.11 Day 3 / US-5)
 * Last Modified: 2026-05-25
 *
 * Modification History (newest-first):
 *   - 2026-05-25: FIX-015 — re-point shadcn-utility tokens (bg-muted/text-muted-foreground/border-border/etc.) → mockup verbatim classes/vars
 *   - 2026-05-10: Initial creation (Sprint 57.11 Day 3 / US-5)
 *
 * Related:
 *   - ../../chat_v2/store/chatStore.ts (verifications + appendVerification)
 *   - ../types.ts (VerificationEvent discriminated union)
 *   - ./VerifierTypeBadge.tsx (shared with US-4 list)
 */

import { useChatStore } from "../../chat_v2/store/chatStore";
import { VerifierTypeBadge } from "./VerifierTypeBadge";

export function VerificationPanel(): JSX.Element | null {
  const verifications = useChatStore((s) => s.verifications);
  if (verifications.length === 0) return null;

  return (
    <div
      className="p-3"
      // eslint-disable-next-line no-restricted-syntax -- mockup CSS var consumed from styles-mockup.css verbatim; mockup-fidelity (FIX-015)
      style={{ borderTop: "1px solid var(--border)", background: "var(--bg-2)" }}
      data-testid="verification-panel"
      aria-label="Verification panel"
    >
      <h3 className="subtle mb-2 text-xs font-semibold uppercase tracking-wide">
        Verification ({verifications.length})
      </h3>
      <ul className="space-y-2">
        {verifications.map((ev, idx) => {
          const passed = ev.type === "verification_passed";
          return (
            <li
              key={`${ev.type}-${idx}`}
              className="card flex items-start gap-2 p-2"
              // eslint-disable-next-line no-restricted-syntax -- mockup verbatim border-left + var(--success|--danger); mockup-fidelity (FIX-015)
              style={{
                borderLeft: `4px solid ${passed ? "var(--success)" : "var(--danger)"}`,
              }}
              data-testid={`verification-entry-${idx}`}
            >
              <span aria-hidden className="mt-0.5 text-base">
                {passed ? "✅" : "❌"}
              </span>
              <div className="min-w-0 flex-1">
                <div className="row">
                  <span className="text-sm font-medium">{ev.data.verifier}</span>
                  <VerifierTypeBadge type={ev.data.verifier_type} />
                </div>
                {!passed && ev.data.reason && (
                  /* eslint-disable-next-line no-restricted-syntax -- mockup CSS var consumed from styles-mockup.css verbatim; mockup-fidelity (FIX-015) */
                  <p className="mt-1 text-xs" style={{ color: "var(--danger)" }}>
                    {ev.data.reason}
                  </p>
                )}
                {!passed && ev.data.suggested_correction && (
                  <p className="subtle mt-1 text-xs">
                    Suggested: {ev.data.suggested_correction}
                  </p>
                )}
                {passed && ev.data.score !== null && ev.data.score !== undefined && (
                  <p className="subtle mt-1 text-xs">
                    Score: {ev.data.score.toFixed(2)}
                  </p>
                )}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
