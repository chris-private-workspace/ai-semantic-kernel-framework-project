/**
 * File: frontend/src/features/governance/components/AuditLogViewer.tsx
 * Purpose: Audit log paginated viewer — filter form (4 fields) + paginated table + AuditChainBadge.
 * Category: Frontend / governance / components
 * Scope: Phase 57 / Sprint 57.9 US-4 Day 3 (full impl; stub created Day 1 for Routes import)
 *
 * Description:
 *   Real implementation replacing Sprint 57.9 Day 1 stub.
 *
 *   Layout:
 *   - Header row: title + <AuditChainBadge /> (US-5; manual Verify chain trigger)
 *   - Filter form: operation / resource_type / user_id / from_ts_ms (datetime-local)
 *     + Apply / Reset buttons. Form-state lives locally (`draft`); only "Apply"
 *     promotes draft → committed `filter` state which drives `useAuditLog`.
 *     This avoids one fetch per keystroke (mirror Sprint 57.4 admin-tenants
 *     no-debounce pattern per AP-6).
 *   - Paginated table: columns = id / timestamp / operation / resource / user /
 *     hash. Empty state with Reset Filters action. Loading skeleton 5 rows.
 *   - Pagination footer: Prev / Next + range indicator. Edge-disable based on
 *     offset + has_more.
 *
 *   The `from_ts_ms` field uses `<input type="datetime-local">` (browser-native
 *   picker; simpler than introducing a date-picker dep per YAGNI). `to_ts_ms`
 *   omitted from UI per minimal-form scope — `from` covers most "show me what
 *   happened since X" queries; range can be added Phase 58+ via
 *   AD-AuditLog-Range deferred.
 *
 *   Tailwind impl per Day 0 D-PRE-2 + Sprint 57.8 UserMenu YAGNI precedent.
 *   No shadcn `<Form>` / `<Input>` / `<Table>` — native HTML keeps the
 *   dependency footprint flat.
 *
 * Created: 2026-05-09 (Sprint 57.9 Day 1 stub) → full impl 2026-05-09 (Day 3)
 * Last Modified: 2026-05-25
 *
 * Modification History (newest-first):
 *   - 2026-05-25: FIX-015 — re-point shadcn-utility tokens (bg-card/text-foreground/border-border/etc.) → mockup verbatim classes/vars
 *   - 2026-05-09: Sprint 57.9 US-4 Day 3 — replace stub with filter form + paginated table + chain badge mount
 *   - 2026-05-09: Initial creation as Day 1 stub (Sprint 57.9 US-1 enabler)
 *
 * Related:
 *   - sprint-57-9-plan.md §US-4 / §US-5
 *   - ../hooks/useAuditLog.ts (TanStack query)
 *   - ./AuditChainBadge.tsx (US-5)
 *   - ../types.ts (AuditLogFilter / AuditLogEntry)
 */

import { useState } from "react";

import { Skeleton } from "../../../components/ui";
import { useAuditLog } from "../hooks/useAuditLog";
import type { AuditLogFilter } from "../types";
import { AuditChainBadge } from "./AuditChainBadge";

const PAGE_SIZE = 50;

const EMPTY_FILTER: AuditLogFilter = {
  offset: 0,
  page_size: PAGE_SIZE,
};

function _formatTs(timestampMs: number): string {
  return new Date(timestampMs).toLocaleString();
}

function _shortHash(hash: string): string {
  if (!hash) return "—";
  return hash.length <= 12 ? hash : `${hash.slice(0, 8)}…${hash.slice(-4)}`;
}

function _datetimeLocalToMs(value: string): number | undefined {
  if (!value) return undefined;
  const ms = new Date(value).getTime();
  return Number.isNaN(ms) ? undefined : ms;
}

export function AuditLogViewer() {
  const [draft, setDraft] = useState<AuditLogFilter>(EMPTY_FILTER);
  const [filter, setFilter] = useState<AuditLogFilter>(EMPTY_FILTER);
  const [draftFromLocal, setDraftFromLocal] = useState<string>("");

  const { data, isLoading, error, refetch, isFetching } = useAuditLog(filter);

  const apply = () => {
    setFilter({
      ...draft,
      from_ts_ms: _datetimeLocalToMs(draftFromLocal),
      offset: 0, // reset page when filter changes
      page_size: PAGE_SIZE,
    });
  };

  const reset = () => {
    setDraft(EMPTY_FILTER);
    setDraftFromLocal("");
    setFilter(EMPTY_FILTER);
  };

  const goPrev = () => {
    if ((filter.offset ?? 0) <= 0) return;
    setFilter({ ...filter, offset: Math.max(0, (filter.offset ?? 0) - PAGE_SIZE) });
  };

  const goNext = () => {
    if (!data?.has_more || data.next_offset === null) return;
    setFilter({ ...filter, offset: data.next_offset ?? (filter.offset ?? 0) + PAGE_SIZE });
  };

  const items = data?.items ?? [];
  const offset = filter.offset ?? 0;
  const rangeStart = items.length === 0 ? 0 : offset + 1;
  const rangeEnd = offset + items.length;
  const hasMore = data?.has_more ?? false;

  return (
    <div className="space-y-4">
      <div className="spread">
        <h2 className="m-0 text-xl font-semibold">Audit Log</h2>
        <AuditChainBadge />
      </div>

      {/* Filter form */}
      {/* eslint-disable-next-line no-restricted-syntax -- mockup CSS var consumed from styles-mockup.css verbatim; mockup-fidelity (FIX-015) */}
      <div className="card" style={{ padding: 16 }}>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-4">
          <label className="field">
            <span className="field-label">Operation</span>
            <input
              type="text"
              className="input"
              value={draft.operation ?? ""}
              onChange={(e) => setDraft({ ...draft, operation: e.target.value })}
              placeholder="e.g. tool_executed"
            />
          </label>
          <label className="field">
            <span className="field-label">Resource type</span>
            <input
              type="text"
              className="input"
              value={draft.resource_type ?? ""}
              onChange={(e) => setDraft({ ...draft, resource_type: e.target.value })}
              placeholder="e.g. tool / approval"
            />
          </label>
          <label className="field">
            <span className="field-label">User ID (UUID)</span>
            <input
              type="text"
              className="input"
              value={draft.user_id ?? ""}
              onChange={(e) => setDraft({ ...draft, user_id: e.target.value })}
              placeholder="optional"
            />
          </label>
          <label className="field">
            <span className="field-label">From (timestamp)</span>
            <input
              type="datetime-local"
              className="input"
              value={draftFromLocal}
              onChange={(e) => setDraftFromLocal(e.target.value)}
            />
          </label>
        </div>
        <div className="mt-3 flex justify-end gap-2">
          <button type="button" onClick={reset} className="btn outline">
            Reset
          </button>
          <button type="button" onClick={apply} className="btn primary">
            Apply
          </button>
          <button
            type="button"
            onClick={() => void refetch()}
            disabled={isFetching}
            className="btn outline"
          >
            {isFetching ? "Refreshing…" : "Refresh"}
          </button>
        </div>
      </div>

      {error && (
        <div
          role="alert"
          className="card"
          // eslint-disable-next-line no-restricted-syntax -- mockup CSS var consumed from styles-mockup.css verbatim; mockup-fidelity (FIX-015)
          style={{
            padding: 12,
            borderColor: "oklch(from var(--danger) l c h / 0.4)",
            background: "oklch(from var(--danger) l c h / 0.08)",
            color: "var(--danger)",
            fontSize: 13,
          }}
        >
          Failed to load audit log: {error.message}
        </div>
      )}

      {/* Table */}
      {/* eslint-disable-next-line no-restricted-syntax -- mockup CSS var consumed from styles-mockup.css verbatim; mockup-fidelity (FIX-015) */}
      <div className="card" style={{ padding: 0, overflowX: "auto" }}>
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Timestamp</th>
              <th>Operation</th>
              <th>Resource</th>
              <th>User</th>
              <th>Hash</th>
            </tr>
          </thead>
          <tbody>
            {isLoading &&
              [0, 1, 2, 3, 4].map((i) => (
                <tr key={`skeleton-${i}`}>
                  <td colSpan={6}>
                    <Skeleton className="h-4 w-full" />
                  </td>
                </tr>
              ))}

            {!isLoading && items.length === 0 && (
              <tr>
                {/* eslint-disable-next-line no-restricted-syntax -- mockup verbatim layout (text-align/padding); mockup-fidelity (FIX-015) */}
                <td colSpan={6} className="subtle" style={{ textAlign: "center", padding: "24px 12px" }}>
                  No audit log entries match the current filter.{" "}
                  <button
                    type="button"
                    onClick={reset}
                    className="font-semibold hover:underline"
                    // eslint-disable-next-line no-restricted-syntax -- mockup CSS var consumed from styles-mockup.css verbatim; mockup-fidelity (FIX-015)
                    style={{ color: "var(--primary)", background: "transparent", border: 0, cursor: "pointer" }}
                  >
                    Reset filters
                  </button>
                </td>
              </tr>
            )}

            {!isLoading &&
              items.map((entry) => (
                <tr key={entry.id}>
                  <td className="mono">{entry.id}</td>
                  <td>{_formatTs(entry.timestamp_ms)}</td>
                  <td>{entry.operation}</td>
                  <td>
                    {entry.resource_type}
                    {entry.resource_id && (
                      /* eslint-disable-next-line no-restricted-syntax -- mockup verbatim font-size (11px); mockup-fidelity (FIX-015) */
                      <span className="subtle ml-1" style={{ fontSize: 11 }}>
                        ({entry.resource_id})
                      </span>
                    )}
                  </td>
                  {/* eslint-disable-next-line no-restricted-syntax -- mockup verbatim font-size (11px); mockup-fidelity (FIX-015) */}
                  <td className="mono" style={{ fontSize: 11 }}>
                    {entry.user_id ?? <span className="subtle">—</span>}
                  </td>
                  {/* eslint-disable-next-line no-restricted-syntax -- mockup verbatim font-size (11px); mockup-fidelity (FIX-015) */}
                  <td className="mono" style={{ fontSize: 11 }}>
                    {_shortHash(entry.current_log_hash)}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {/* Pagination footer */}
      {/* eslint-disable-next-line no-restricted-syntax -- mockup verbatim font-size (13px); mockup-fidelity (FIX-015) */}
      <div className="spread subtle" style={{ fontSize: 13 }}>
        <span>
          {items.length === 0 ? "No entries" : `Showing ${rangeStart}–${rangeEnd}`}
          {hasMore && <span className="ml-1">(more available)</span>}
        </span>
        {/* eslint-disable-next-line no-restricted-syntax -- mockup verbatim gap (8px); mockup-fidelity (FIX-015) */}
        <div className="row" style={{ gap: 8 }}>
          <button
            type="button"
            onClick={goPrev}
            disabled={offset <= 0 || isFetching}
            className="btn outline"
          >
            Prev
          </button>
          <button
            type="button"
            onClick={goNext}
            disabled={!hasMore || isFetching}
            className="btn outline"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
