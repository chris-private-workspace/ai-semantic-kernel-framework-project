/* eslint-disable no-restricted-syntax -- mockup verbatim CSS literals (header dot + gap indicator color); mockup-fidelity (Sprint 57.42 / 57.73). See reference/design-mockups/page-governance.jsx L501-552. */
/**
 * File: frontend/src/features/memory/components/MemoryMatrix.tsx
 * Purpose: 5×3 dual-axis Memory Layers matrix — header row + 5 layer rows × 3 time-scale count cells, wired to GET /matrix aggregate.
 * Category: Frontend / memory / components
 * Scope: Phase 57 / Sprint 57.73 Track C (A-6b frontend half)
 *
 * Description:
 *   Layout is the verbatim mockup grid from
 *   `reference/design-mockups/page-governance.jsx:501-552` (`.memory-matrix`):
 *   4-column × 6-row grid — header row (empty corner + 3 time-scale headers with
 *   colored dot + TTL subtitle) then 5 layer rows (label cell + 3 count cells).
 *
 *   Data is REAL (Sprint 57.73 Track C): consumes useMemoryMatrix() →
 *   GET /api/v1/memory/matrix. Per-cell count is looked up from the response
 *   `cells` (key `${layer}:${time_scale}`; absent pairs default to 0).
 *   Layers in `gapped_layers` (role + session — no backend query path) render a
 *   gap indicator ("n/a") across the row, NEVER a fabricated number.
 *
 *   The mockup's per-entry list + cursor-aware time-travel visibility filter were
 *   fixture-only behaviors; the real aggregate exposes only counts, so the cell
 *   body shows the count (no per-entry rows, no time-travel filtering). The
 *   time-travel scrubber widget remains (fixture-driven) but no longer filters
 *   this matrix.
 *
 * Key Components:
 *   - MemoryMatrix: query-consuming component (no props)
 *
 * Created: 2026-05-25 (Sprint 57.42 Day 1)
 * Last Modified: 2026-06-03
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Sprint 57.73 Track C — wire to useMemoryMatrix (real counts + gap indicator); drop cursor entry-filter
 *   - 2026-05-25: Initial creation (Sprint 57.42 Day 1) — memory matrix full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-governance.jsx L501-552
 *   - ./MemoryView.tsx (parent)
 *   - ../hooks/useMemoryMatrix.ts (server cache)
 *   - ../types.ts (MemoryLayer / MemoryTimeScale / MemoryMatrixResponse)
 *   - ../../../components/mockup-ui.tsx (Icon primitive)
 *   - ../../../components/ui/BackendGapBanner.tsx (AP-2 declaration)
 */

import { Icon } from "../../../components/mockup-ui";
import { BackendGapBanner } from "../../../components/ui/BackendGapBanner";
import { useMemoryMatrix } from "../hooks/useMemoryMatrix";
import type { MemoryLayer, MemoryMatrixResponse, MemoryTimeScale } from "../types";

// The 5 layer rows and 3 time-scale columns, in mockup order.
const LAYERS: MemoryLayer[] = ["system", "tenant", "role", "user", "session"];
const TIME_SCALES: MemoryTimeScale[] = ["permanent", "quarterly", "daily"];

function scaleDotColor(t: MemoryTimeScale): string {
  return t === "permanent" ? "var(--memory)" : t === "quarterly" ? "var(--info)" : "var(--tool)";
}

function scaleTtl(t: MemoryTimeScale): string {
  return t === "permanent" ? "TTL ∞" : t === "quarterly" ? "TTL 90d" : "TTL 24h";
}

/** Build a `${layer}:${time_scale}` → count lookup from the response cells. */
function buildLookup(data: MemoryMatrixResponse): Map<string, number> {
  const lookup = new Map<string, number>();
  for (const cell of data.cells) {
    lookup.set(`${cell.layer}:${cell.time_scale}`, cell.count);
  }
  return lookup;
}

function MatrixGrid({ data }: { data: MemoryMatrixResponse }): JSX.Element {
  const lookup = buildLookup(data);
  const gapped = new Set<MemoryLayer>(data.gapped_layers);

  return (
    <div className="memory-matrix">
      <div className="mm-cell mm-header"></div>
      {TIME_SCALES.map((t) => (
        <div key={t} className="mm-cell mm-header">
          <div className="row" style={{ gap: 6 }}>
            <span
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: scaleDotColor(t),
              }}
            />
            <span>{t}</span>
            <span className="subtle">·</span>
            <span className="subtle">{scaleTtl(t)}</span>
          </div>
        </div>
      ))}

      {LAYERS.map((layer) => {
        const isGapped = gapped.has(layer);
        // Row total: sum of the 3 wired cells (0 for gapped layers).
        const rowTotal = isGapped
          ? 0
          : TIME_SCALES.reduce((acc, t) => acc + (lookup.get(`${layer}:${t}`) ?? 0), 0);
        return (
          <div className="mm-row-group" key={layer} style={{ display: "contents" }}>
            <div className="mm-cell mm-scope">
              <div className="name">{layer}</div>
              <div className="sub">{isGapped ? "no backend path" : "live"}</div>
              <div className="row" style={{ gap: 6, marginTop: "auto", paddingTop: 8 }}>
                <Icon name="memory" size={12} style={{ color: "var(--memory)" }} />
                <span className="mono" style={{ fontSize: 10.5, color: "var(--fg-muted)" }}>
                  {isGapped ? "n/a" : rowTotal.toLocaleString()}
                </span>
              </div>
            </div>
            {TIME_SCALES.map((t) => {
              if (isGapped) {
                return (
                  <div key={t} className="mm-cell">
                    <div
                      className="subtle"
                      style={{ fontSize: 11, fontStyle: "italic", color: "var(--fg-subtle)" }}
                    >
                      n/a
                    </div>
                  </div>
                );
              }
              const count = lookup.get(`${layer}:${t}`) ?? 0;
              return (
                <div key={t} className="mm-cell">
                  {count === 0 ? (
                    <div className="subtle" style={{ fontSize: 11, fontStyle: "italic" }}>
                      — empty
                    </div>
                  ) : (
                    <div className="mm-entry">
                      <span className="k mono" style={{ fontSize: 13, fontWeight: 600 }}>
                        {count.toLocaleString()}
                      </span>{" "}
                      <span className="subtle">{count === 1 ? "entry" : "entries"}</span>
                    </div>
                  )}
                  <div className="count">
                    {count} {count === 1 ? "entry" : "entries"}
                  </div>
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}

export function MemoryMatrix(): JSX.Element {
  const { data, isLoading, isError, error, refetch } = useMemoryMatrix();

  if (isLoading) {
    return (
      <div className="memory-matrix-state subtle" role="status" style={{ padding: 24 }}>
        Loading memory matrix…
      </div>
    );
  }

  if (isError) {
    return (
      <div className="memory-matrix-state" role="alert" style={{ padding: 24 }}>
        <div style={{ color: "var(--danger)", marginBottom: 8 }}>
          Failed to load memory matrix{error?.message ? `: ${error.message}` : ""}
        </div>
        <button type="button" className="btn outline" data-size="sm" onClick={() => void refetch()}>
          Retry
        </button>
      </div>
    );
  }

  if (!data || data.total === 0) {
    return (
      <div className="memory-matrix-state subtle" style={{ padding: 24, fontStyle: "italic" }}>
        No memory entries
      </div>
    );
  }

  return (
    <>
      <MatrixGrid data={data} />
      <BackendGapBanner reason="system/tenant/user counts are live; role/session layers have no backend path yet (501)" />
    </>
  );
}
