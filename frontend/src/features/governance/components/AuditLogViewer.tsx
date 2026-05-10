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
 * Last Modified: 2026-05-09
 *
 * Modification History (newest-first):
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
      <div className="flex items-baseline justify-between">
        <h2 className="m-0 text-xl font-semibold">Audit Log</h2>
        <AuditChainBadge />
      </div>

      {/* Filter form */}
      <div className="rounded-lg border border-border bg-card p-4">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-4">
          <label className="flex flex-col text-sm font-medium">
            Operation
            <input
              type="text"
              className="mt-1 rounded border border-border bg-background px-2 py-1.5 text-sm"
              value={draft.operation ?? ""}
              onChange={(e) => setDraft({ ...draft, operation: e.target.value })}
              placeholder="e.g. tool_executed"
            />
          </label>
          <label className="flex flex-col text-sm font-medium">
            Resource type
            <input
              type="text"
              className="mt-1 rounded border border-border bg-background px-2 py-1.5 text-sm"
              value={draft.resource_type ?? ""}
              onChange={(e) => setDraft({ ...draft, resource_type: e.target.value })}
              placeholder="e.g. tool / approval"
            />
          </label>
          <label className="flex flex-col text-sm font-medium">
            User ID (UUID)
            <input
              type="text"
              className="mt-1 rounded border border-border bg-background px-2 py-1.5 text-sm"
              value={draft.user_id ?? ""}
              onChange={(e) => setDraft({ ...draft, user_id: e.target.value })}
              placeholder="optional"
            />
          </label>
          <label className="flex flex-col text-sm font-medium">
            From (timestamp)
            <input
              type="datetime-local"
              className="mt-1 rounded border border-border bg-background px-2 py-1.5 text-sm"
              value={draftFromLocal}
              onChange={(e) => setDraftFromLocal(e.target.value)}
            />
          </label>
        </div>
        <div className="mt-3 flex justify-end gap-2">
          <button
            type="button"
            onClick={reset}
            className="rounded-md border border-border bg-background px-3 py-1.5 text-sm font-medium hover:bg-muted"
          >
            Reset
          </button>
          <button
            type="button"
            onClick={apply}
            className="rounded-md border border-primary bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Apply
          </button>
          <button
            type="button"
            onClick={() => void refetch()}
            disabled={isFetching}
            className="rounded-md border border-primary bg-background px-3 py-1.5 text-sm font-medium text-primary hover:bg-primary/10 disabled:opacity-50"
          >
            {isFetching ? "Refreshing…" : "Refresh"}
          </button>
        </div>
      </div>

      {error && (
        <div
          role="alert"
          className="rounded-lg border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive"
        >
          Failed to load audit log: {error.message}
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-sm">
          <thead className="bg-muted text-left text-xs font-semibold uppercase text-muted-foreground">
            <tr>
              <th className="px-3 py-2">ID</th>
              <th className="px-3 py-2">Timestamp</th>
              <th className="px-3 py-2">Operation</th>
              <th className="px-3 py-2">Resource</th>
              <th className="px-3 py-2">User</th>
              <th className="px-3 py-2">Hash</th>
            </tr>
          </thead>
          <tbody>
            {isLoading &&
              [0, 1, 2, 3, 4].map((i) => (
                <tr key={`skeleton-${i}`} className="border-t border-border">
                  <td colSpan={6} className="px-3 py-3">
                    <Skeleton className="h-4 w-full" />
                  </td>
                </tr>
              ))}

            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={6} className="px-3 py-6 text-center text-muted-foreground">
                  No audit log entries match the current filter.{" "}
                  <button
                    type="button"
                    onClick={reset}
                    className="font-semibold text-primary hover:underline"
                  >
                    Reset filters
                  </button>
                </td>
              </tr>
            )}

            {!isLoading &&
              items.map((entry) => (
                <tr key={entry.id} className="border-t border-border hover:bg-muted/30">
                  <td className="px-3 py-2 font-mono">{entry.id}</td>
                  <td className="px-3 py-2">{_formatTs(entry.timestamp_ms)}</td>
                  <td className="px-3 py-2">{entry.operation}</td>
                  <td className="px-3 py-2">
                    {entry.resource_type}
                    {entry.resource_id && (
                      <span className="ml-1 text-xs text-muted-foreground">
                        ({entry.resource_id})
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 font-mono text-xs">
                    {entry.user_id ?? <span className="text-muted-foreground">—</span>}
                  </td>
                  <td className="px-3 py-2 font-mono text-xs">
                    {_shortHash(entry.current_log_hash)}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {/* Pagination footer */}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          {items.length === 0 ? "No entries" : `Showing ${rangeStart}–${rangeEnd}`}
          {hasMore && <span className="ml-1">(more available)</span>}
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={goPrev}
            disabled={offset <= 0 || isFetching}
            className="rounded-md border border-border bg-background px-3 py-1 text-sm font-medium hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Prev
          </button>
          <button
            type="button"
            onClick={goNext}
            disabled={!hasMore || isFetching}
            className="rounded-md border border-border bg-background px-3 py-1 text-sm font-medium hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
