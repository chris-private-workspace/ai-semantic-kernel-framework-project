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
      className="border-t border-border bg-muted/30 p-3"
      data-testid="verification-panel"
      aria-label="Verification panel"
    >
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        Verification ({verifications.length})
      </h3>
      <ul className="space-y-2">
        {verifications.map((ev, idx) => {
          const passed = ev.type === "verification_passed";
          const borderClass = passed
            ? "border-l-4 border-green-500"
            : "border-l-4 border-red-500";
          return (
            <li
              key={`${ev.type}-${idx}`}
              className={`flex items-start gap-2 rounded bg-background p-2 ${borderClass}`}
              data-testid={`verification-entry-${idx}`}
            >
              <span aria-hidden className="mt-0.5 text-base">
                {passed ? "✅" : "❌"}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{ev.data.verifier}</span>
                  <VerifierTypeBadge type={ev.data.verifier_type} />
                </div>
                {!passed && ev.data.reason && (
                  <p className="mt-1 text-xs text-red-700">{ev.data.reason}</p>
                )}
                {!passed && ev.data.suggested_correction && (
                  <p className="mt-1 text-xs text-muted-foreground">
                    Suggested: {ev.data.suggested_correction}
                  </p>
                )}
                {passed && ev.data.score !== null && ev.data.score !== undefined && (
                  <p className="mt-1 text-xs text-muted-foreground">
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
