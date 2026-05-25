/**
 * File: frontend/src/features/verification/components/CorrectionTraceView.tsx
 * Purpose: Vertical timeline view for one session's correction trace (US-4 §3.2).
 * Category: Frontend / verification / components
 * Scope: Phase 57 / Sprint 57.11 Day 3 / US-4 §3.2
 *
 * Description:
 *   Reads `?session_id=...` from useSearchParams; calls useCorrectionTrace.
 *   Renders entries grouped by turn_index then sorted by correction_attempt
 *   (sort already done backend-side; frontend just chunks by turn_index for
 *   visual grouping).
 *
 *   Each entry card:
 *     - Pass/fail icon (✅ / ❌)
 *     - Verifier name + VerifierTypeBadge
 *     - Reason (failed) + Suggested correction (failed) + Score (when present)
 *     - Correction attempt indicator
 *     - Visual: passed = green left border, failed = red left border
 *
 *   Empty/missing states: 404 / null sessionId → "No correction trace..."
 *
 * Created: 2026-05-10 (Sprint 57.11 Day 3 §3.2)
 * Last Modified: 2026-05-25
 *
 * Modification History (newest-first):
 *   - 2026-05-25: FIX-015 — re-point shadcn-utility tokens (bg-card/text-muted-foreground/border-border/etc.) → mockup verbatim classes/vars
 *   - 2026-05-24: Sprint 57.33 Day 3 US-D2 — defensive ?? [] on entries (_groupByTurn input + .length; AD-Overview-PreExisting-Route-Crashes)
 *   - 2026-05-10: Initial creation (Sprint 57.11 Day 3 §3.2)
 *
 * Related:
 *   - ../hooks/useCorrectionTrace.ts
 *   - ./VerifierTypeBadge.tsx
 *   - ../types.ts
 */

import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";

import { Skeleton } from "../../../components/ui";
import { useCorrectionTrace } from "../hooks/useCorrectionTrace";
import type { VerificationLogItem } from "../types";
import { VerifierTypeBadge } from "./VerifierTypeBadge";

function _groupByTurn(entries: VerificationLogItem[]): Map<number, VerificationLogItem[]> {
  const out = new Map<number, VerificationLogItem[]>();
  for (const e of entries) {
    const arr = out.get(e.turn_index);
    if (arr === undefined) {
      out.set(e.turn_index, [e]);
    } else {
      arr.push(e);
    }
  }
  return out;
}

export function CorrectionTraceView(): JSX.Element {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get("session_id");
  const query = useCorrectionTrace(sessionId);

  const groupedByTurn = useMemo(() => {
    if (query.data === undefined) return new Map<number, VerificationLogItem[]>();
    // FIX-Sprint-57-33 US-D2: defensive ?? [] — backend may return {} without `entries`,
    // crashing _groupByTurn's for…of (AD-Overview-PreExisting-Route-Crashes).
    return _groupByTurn(query.data.entries ?? []);
  }, [query.data]);

  if (sessionId === null) {
    return (
      // eslint-disable-next-line no-restricted-syntax -- mockup verbatim layout (padding/text-align); mockup-fidelity (FIX-015)
      <div className="card" style={{ padding: 24, textAlign: "center" }} data-testid="trace-no-session">
        <p className="subtle text-sm">
          Select a session from the Recent tab to view its correction trace.
        </p>
      </div>
    );
  }

  if (query.isLoading) {
    return (
      <div className="space-y-3" data-testid="trace-loading">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-16" />
        ))}
      </div>
    );
  }

  if (query.isError) {
    const is404 = query.error.message.includes("No verification entries");
    return (
      <div
        className="card"
        // eslint-disable-next-line no-restricted-syntax -- mockup verbatim layout (padding/text-align); mockup-fidelity (FIX-015)
        style={{ padding: 24, textAlign: "center" }}
        data-testid={is404 ? "trace-empty" : "trace-error"}
      >
        <p className="subtle text-sm">
          {is404 ? `No correction trace for session ${sessionId.slice(0, 8)}…` : query.error.message}
        </p>
      </div>
    );
  }

  if (!query.isSuccess) return <div />;

  return (
    <div className="space-y-6" data-testid="correction-trace">
      <div className="subtle text-sm">
        Session <span className="mono">{sessionId.slice(0, 8)}…</span> /{" "}
        {(query.data.entries ?? []).length} entries
      </div>
      {Array.from(groupedByTurn.entries()).map(([turnIndex, entries]) => (
        <div key={turnIndex} data-testid={`turn-${turnIndex}`}>
          <h4 className="subtle mb-2 text-xs font-semibold uppercase tracking-wide">
            Turn {turnIndex}
          </h4>
          <ul className="space-y-2">
            {entries.map((entry) => {
              return (
                <li
                  key={entry.id}
                  className="card p-3"
                  // eslint-disable-next-line no-restricted-syntax -- mockup verbatim border-left + var(--success|--danger); mockup-fidelity (FIX-015)
                  style={{
                    borderLeft: `4px solid ${entry.passed ? "var(--success)" : "var(--danger)"}`,
                  }}
                  data-testid={`entry-${entry.id}`}
                >
                  <div className="row">
                    <span aria-hidden className="text-base">
                      {entry.passed ? "✅" : "❌"}
                    </span>
                    <span className="text-sm font-medium">{entry.verifier_name}</span>
                    <VerifierTypeBadge type={entry.verifier_type} />
                    {entry.correction_attempt > 0 && (
                      <span className="subtle text-xs">
                        (correction #{entry.correction_attempt})
                      </span>
                    )}
                  </div>
                  {!entry.passed && entry.reason && (
                    /* eslint-disable-next-line no-restricted-syntax -- mockup CSS var consumed from styles-mockup.css verbatim; mockup-fidelity (FIX-015) */
                    <p className="mt-1 text-xs" style={{ color: "var(--danger)" }}>
                      {entry.reason}
                    </p>
                  )}
                  {!entry.passed && entry.suggested_correction && (
                    <p className="subtle mt-1 text-xs">
                      Suggested: {entry.suggested_correction}
                    </p>
                  )}
                  {entry.score !== null && entry.score !== undefined && (
                    <p className="subtle mt-1 text-xs">
                      Score: {entry.score.toFixed(2)}
                    </p>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </div>
  );
}
