/**
 * File: frontend/src/features/memory/components/MemoryRecentList.tsx
 * Purpose: Paginated memory entry table with layer dropdown filter (US-5 recent tab).
 * Category: Frontend / memory / components
 * Scope: Phase 57 / Sprint 57.12 Day 2-3 / US-5
 *
 * Description:
 *   Composed UI mirroring VerificationList.tsx (Sprint 57.11) pattern:
 *     - Layer dropdown (system / tenant / user — the 3 wired layers; role +
 *       session shown disabled with "(Phase 58+)" suffix)
 *     - Paginated table: 50 rows; columns: layer (MemoryScopeBadge) / scope_id
 *       truncated / key / content truncated 80 + tooltip / created_at / expires_at
 *     - Loading skeleton (5-row)
 *     - Error retry UX with retryClicked flag (Sprint 57.9 D-PRE-15 lesson —
 *       StrictMode-safe; flag reset on layer change)
 *     - Empty state
 *     - Prev / Next pagination footer
 *
 *   Note: layer is mandatory in the backend /recent endpoint (single layer
 *   per request), so the dropdown has no "Any" option — defaults to "user".
 *
 * Created: 2026-05-10 (Sprint 57.12 Day 2-3 / US-5)
 *
 * Related:
 *   - ../hooks/useMemoryRecent.ts
 *   - ./MemoryScopeBadge.tsx
 *   - ../types.ts
 *   - frontend/src/features/verification/components/VerificationList.tsx (sibling pattern)
 */

import { useMemo, useState } from "react";

import { Skeleton } from "../../../components/ui";
import { useMemoryRecent } from "../hooks/useMemoryRecent";
import type { MemoryLayer, MemoryRecentFilter } from "../types";
import { MemoryScopeBadge } from "./MemoryScopeBadge";

const PAGE_SIZE = 50;
const CONTENT_SNIPPET_MAX = 80;

/** Layers wired in Sprint 57.12 (backend returns 501 for role + session). */
const WIRED_LAYERS: MemoryLayer[] = ["system", "tenant", "user"];
const PHASE58_LAYERS: MemoryLayer[] = ["role", "session"];

function _truncate(text: string | null, max: number): string {
  if (text === null) return "";
  if (text.length <= max) return text;
  return `${text.slice(0, max)}…`;
}

export function MemoryRecentList(): JSX.Element {
  const [layer, setLayer] = useState<MemoryLayer>("user");
  const [offset, setOffset] = useState(0);
  const [retryClicked, setRetryClicked] = useState(false);

  const filter = useMemo<MemoryRecentFilter>(
    () => ({ layer, limit: PAGE_SIZE, offset }),
    [layer, offset],
  );
  const query = useMemoryRecent(filter);

  function handleLayerChange(next: MemoryLayer) {
    setLayer(next);
    setOffset(0);
    setRetryClicked(false);
  }

  function handleRetry() {
    setRetryClicked(true);
    void query.refetch();
  }

  return (
    <div className="space-y-4" data-testid="memory-recent-list">
      <div className="flex flex-wrap items-end gap-3 rounded border border-border bg-card p-3">
        <label className="flex flex-col text-sm">
          <span className="mb-1 text-xs font-medium text-muted-foreground">Layer</span>
          <select
            value={layer}
            onChange={(e) => handleLayerChange(e.target.value as MemoryLayer)}
            className="rounded border border-input bg-background px-2 py-1 text-sm"
            data-testid="filter-layer"
          >
            {WIRED_LAYERS.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
            {PHASE58_LAYERS.map((l) => (
              <option key={l} value={l} disabled>
                {l} (Phase 58+)
              </option>
            ))}
          </select>
        </label>
      </div>

      {query.isLoading && (
        <div className="space-y-2" data-testid="loading-skeleton">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-10" />
          ))}
        </div>
      )}

      {query.isError && (
        <div className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-800">
          <p>Error: {query.error.message}</p>
          <button
            type="button"
            onClick={handleRetry}
            className="mt-2 rounded bg-red-600 px-2 py-1 text-xs font-medium text-white"
            data-testid="error-retry"
          >
            Retry{retryClicked ? "ing..." : ""}
          </button>
        </div>
      )}

      {query.isSuccess && query.data.items.length === 0 && (
        <div className="rounded border border-border bg-card p-6 text-center">
          <p className="text-sm text-muted-foreground">No memory entries in this layer.</p>
        </div>
      )}

      {query.isSuccess && query.data.items.length > 0 && (
        <>
          <div className="overflow-x-auto rounded border border-border">
            <table className="min-w-full text-sm" data-testid="memory-table">
              <thead className="bg-muted text-left text-xs uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th className="px-3 py-2">Layer</th>
                  <th className="px-3 py-2">Scope ID</th>
                  <th className="px-3 py-2">Key</th>
                  <th className="px-3 py-2">Content</th>
                  <th className="px-3 py-2">Created</th>
                  <th className="px-3 py-2">Expires</th>
                </tr>
              </thead>
              <tbody>
                {query.data.items.map((item) => (
                  <tr
                    key={item.id}
                    className="border-t border-border hover:bg-muted/30"
                    data-testid={`memory-row-${item.id}`}
                  >
                    <td className="px-3 py-2">
                      <MemoryScopeBadge layer={item.layer} />
                    </td>
                    <td className="px-3 py-2 font-mono text-xs">
                      {item.scope_id ? `${item.scope_id.slice(0, 8)}…` : "—"}
                    </td>
                    <td className="px-3 py-2 text-xs">{item.key ?? "—"}</td>
                    <td className="px-3 py-2 text-xs text-muted-foreground" title={item.content}>
                      {_truncate(item.content, CONTENT_SNIPPET_MAX)}
                    </td>
                    <td className="px-3 py-2 text-xs text-muted-foreground">
                      {new Date(item.created_at_ms).toLocaleString()}
                    </td>
                    <td className="px-3 py-2 text-xs text-muted-foreground">
                      {item.expires_at_ms ? new Date(item.expires_at_ms).toLocaleDateString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              Showing {offset + 1}–{offset + query.data.items.length} of {query.data.total}
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                className="rounded border border-input bg-background px-3 py-1 text-xs disabled:opacity-50"
                data-testid="pagination-prev"
              >
                Prev
              </button>
              <button
                type="button"
                disabled={!query.data.has_more}
                onClick={() => setOffset(offset + PAGE_SIZE)}
                className="rounded border border-input bg-background px-3 py-1 text-xs disabled:opacity-50"
                data-testid="pagination-next"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
