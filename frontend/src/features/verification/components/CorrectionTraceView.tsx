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
    return _groupByTurn(query.data.entries);
  }, [query.data]);

  if (sessionId === null) {
    return (
      <div
        className="rounded border border-border bg-card p-6 text-center"
        data-testid="trace-no-session"
      >
        <p className="text-sm text-muted-foreground">
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
        className="rounded border border-border bg-card p-6 text-center"
        data-testid={is404 ? "trace-empty" : "trace-error"}
      >
        <p className="text-sm text-muted-foreground">
          {is404 ? `No correction trace for session ${sessionId.slice(0, 8)}…` : query.error.message}
        </p>
      </div>
    );
  }

  if (!query.isSuccess) return <div />;

  return (
    <div className="space-y-6" data-testid="correction-trace">
      <div className="text-sm text-muted-foreground">
        Session <span className="font-mono">{sessionId.slice(0, 8)}…</span> /{" "}
        {query.data.entries.length} entries
      </div>
      {Array.from(groupedByTurn.entries()).map(([turnIndex, entries]) => (
        <div key={turnIndex} data-testid={`turn-${turnIndex}`}>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Turn {turnIndex}
          </h4>
          <ul className="space-y-2">
            {entries.map((entry) => {
              const borderClass = entry.passed
                ? "border-l-4 border-green-500"
                : "border-l-4 border-red-500";
              return (
                <li
                  key={entry.id}
                  className={`rounded bg-card p-3 ${borderClass}`}
                  data-testid={`entry-${entry.id}`}
                >
                  <div className="flex items-center gap-2">
                    <span aria-hidden className="text-base">
                      {entry.passed ? "✅" : "❌"}
                    </span>
                    <span className="text-sm font-medium">{entry.verifier_name}</span>
                    <VerifierTypeBadge type={entry.verifier_type} />
                    {entry.correction_attempt > 0 && (
                      <span className="text-xs text-muted-foreground">
                        (correction #{entry.correction_attempt})
                      </span>
                    )}
                  </div>
                  {!entry.passed && entry.reason && (
                    <p className="mt-1 text-xs text-red-700">{entry.reason}</p>
                  )}
                  {!entry.passed && entry.suggested_correction && (
                    <p className="mt-1 text-xs text-muted-foreground">
                      Suggested: {entry.suggested_correction}
                    </p>
                  )}
                  {entry.score !== null && entry.score !== undefined && (
                    <p className="mt-1 text-xs text-muted-foreground">
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
