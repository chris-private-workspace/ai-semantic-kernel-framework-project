/* eslint-disable no-restricted-syntax -- mockup verbatim CSS literals + per-cell font-size + max-width clamp; mockup-fidelity (Sprint 57.42). See reference/design-mockups/page-governance.jsx L557-579. */
/**
 * File: frontend/src/features/memory/components/RecentMemoryOpsCard.tsx
 * Purpose: Recent memory ops sidebar Card — 6-col table (Op / Scope / Key / Value / By / When) wired to GET /memory/ops.
 * Category: Frontend / memory / components
 * Scope: Phase 57 / Sprint 57.42 Day 1 (mockup-fidelity rebuild) → 57.77 (real-data wire)
 *
 * Description:
 *   Verbatim port of `reference/design-mockups/page-governance.jsx:557-579`
 *   (Recent memory ops Card). Subtitle "Live · last 100"; bodyClass "flush";
 *   actions "View all" ghost Button. Table is 6-col:
 *     - Op: Badge tone="memory" (WRITE / EVICT)
 *     - Scope: mono fontSize 11
 *     - Key: mono fontSize 11.5 (— if null)
 *     - Value: subtle mono fontSize 11, maxWidth 240 with ellipsis (— if null)
 *     - By: mono fontSize 11 var(--fg-muted) (— if null)
 *     - When: subtle fontSize 11 (HH:MM:SS from created_at_ms, client-local)
 *
 *   Sprint 57.77: consumes useMemoryOps() (GET /api/v1/memory/ops). The optional
 *   `cursor` prop (ms) filters the visible rows to ops at/before the cursor time
 *   (TimeTravel scrub = browse-ops-timeline; honest, not state reconstruction).
 *   Mockup-native loading/error/empty states (single full-width row, NOT shadcn
 *   skeletons). Fixture (RECENT_MEMORY_OPS) + AP-2 gap banner removed — the
 *   backend producer (memory_ops) shipped Sprint 57.76.
 *
 * Key Components:
 *   - RecentMemoryOpsCard: query-consuming functional, props { cursor? }
 *   - formatMs: created_at_ms → HH:MM:SS (client-local)
 *
 * Created: 2026-05-25 (Sprint 57.42 Day 1)
 * Last Modified: 2026-06-04
 *
 * Modification History (newest-first):
 *   - 2026-06-04: Sprint 57.77 — wire useMemoryOps + cursor filter + states; drop fixture + AP-2 banner
 *   - 2026-06-03: Sprint 57.73 Track C — reword AP-2 banner to deferred ops-history feature (no backend producer)
 *   - 2026-05-25: Initial creation (Sprint 57.42 Day 1) — memory matrix full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-governance.jsx L557-579
 *   - ../hooks/useMemoryOps.ts (server cache; dedup-shared with TimeTravelScrubber)
 *   - ../../../components/mockup-ui.tsx (Card + Badge + Button primitives)
 */

import { Badge, Button, Card } from "../../../components/mockup-ui";
import { useMemoryOps } from "../hooks/useMemoryOps";

export interface RecentMemoryOpsCardProps {
  /** Time-travel cursor (ms). Rows with created_at_ms > cursor are hidden; null = show all. */
  cursor?: number | null;
}

/** created_at_ms → HH:MM:SS (client-local; an activity timeline matches the mockup's relative "When"). */
function formatMs(ms: number): string {
  const d = new Date(ms);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

const COLS = 6;

export function RecentMemoryOpsCard({ cursor = null }: RecentMemoryOpsCardProps): JSX.Element {
  const { data, isLoading, isError, error } = useMemoryOps();
  const ops = (data?.ops ?? []).filter((o) => cursor == null || o.created_at_ms <= cursor);

  return (
    <Card
      title="Recent memory ops"
      subtitle="Live · last 100"
      bodyClass="flush"
      actions={
        <Button variant="ghost" size="sm">
          View all
        </Button>
      }
    >
      <table className="table">
        <thead>
          <tr>
            <th>Op</th>
            <th>Scope</th>
            <th>Key</th>
            <th>Value</th>
            <th>By</th>
            <th>When</th>
          </tr>
        </thead>
        <tbody>
          {isLoading && (
            <tr data-testid="memory-ops-loading">
              <td className="subtle" colSpan={COLS} style={{ fontSize: 11.5 }}>
                Loading…
              </td>
            </tr>
          )}
          {!isLoading && isError && (
            <tr data-testid="memory-ops-error">
              <td className="subtle" colSpan={COLS} style={{ fontSize: 11.5 }}>
                {error?.message ?? "Failed to load memory operations."}
              </td>
            </tr>
          )}
          {!isLoading && !isError && ops.length === 0 && (
            <tr data-testid="memory-ops-empty">
              <td className="subtle" colSpan={COLS} style={{ fontSize: 11.5 }}>
                No memory operations recorded yet.
              </td>
            </tr>
          )}
          {!isLoading &&
            !isError &&
            ops.map((m, i) => (
              <tr key={i} data-testid={`memory-ops-row-${i}`}>
                <td>
                  <Badge tone="memory">{m.op}</Badge>
                </td>
                <td className="mono" style={{ fontSize: 11 }}>
                  {m.scope}
                </td>
                <td className="mono" style={{ fontSize: 11.5 }}>
                  {m.key ?? "—"}
                </td>
                <td
                  className="subtle mono"
                  style={{
                    fontSize: 11,
                    maxWidth: 240,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {m.value_snapshot ?? "—"}
                </td>
                <td className="mono" style={{ fontSize: 11, color: "var(--fg-muted)" }}>
                  {m.actor ?? "—"}
                </td>
                <td className="subtle" style={{ fontSize: 11 }}>
                  {formatMs(m.created_at_ms)}
                </td>
              </tr>
            ))}
        </tbody>
      </table>
    </Card>
  );
}
