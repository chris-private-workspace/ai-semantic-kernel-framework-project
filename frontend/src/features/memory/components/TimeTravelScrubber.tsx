/* eslint-disable no-restricted-syntax -- mockup verbatim CSS literals; mockup-fidelity (Sprint 57.42). See reference/design-mockups/page-governance.jsx L600-656. */
/**
 * File: frontend/src/features/memory/components/TimeTravelScrubber.tsx
 * Purpose: Time-travel scrubber Card — range slider with real op markers + playback control + cursor display.
 * Category: Frontend / memory / components
 * Scope: Phase 57 / Sprint 57.42 Day 1 (mockup-fidelity rebuild) → 57.77 (real-data wire)
 *
 * Description:
 *   Verbatim port of `reference/design-mockups/page-governance.jsx:600-656`
 *   (`TimeTravelScrubber` component). Wraps in Card bodyClass="dense".
 *   Renders:
 *     - Replay 24h / Pause toggle button (outline → warning when playing)
 *     - Now ghost button (resets cursor to the latest op time)
 *     - Range slider (0..100) over the real op time domain [minMs, maxMs]
 *     - One marker per real op (WRITE/EVICT) positioned at the normalized
 *       (created_at_ms - minMs) / (maxMs - minMs) along the slider
 *     - Right cursor display: mono "now" (at maxMs) / HH:MM:SS at the cursor time
 *
 *   Sprint 57.77: marks + domain derive from useMemoryOps() (GET /memory/ops).
 *   `cursor` is an ms timestamp in [minMs, maxMs]; scrubbing maps the slider
 *   position → ms and calls onCursor(ms). The cursor really filters
 *   RecentMemoryOpsCard (browse-ops-timeline; honest, not state reconstruction).
 *   Empty ops (or a single op) → no marks + a subtle "no operations" hint
 *   (guards div-by-zero on the [minMs, maxMs] domain). Fixtures
 *   (MEMORY_OPS_TIMELINE / TIME_TRAVEL_MARKS) + the AP-2 banner removed — the
 *   backend producer (memory_ops) shipped Sprint 57.76.
 *
 *   Component stays pure controlled: cursor/onCursor/playing/onPlay are props;
 *   parent (MemoryView) owns the setInterval playback loop.
 *
 * Key Components:
 *   - TimeTravelScrubber: query-consuming, controlled component
 *
 * Created: 2026-05-25 (Sprint 57.42 Day 1)
 * Last Modified: 2026-06-04
 *
 * Modification History (newest-first):
 *   - 2026-06-04: Sprint 57.77 — marks from real ops (ms domain) + scrub→onCursor(ms); drop fixtures + AP-2 banner
 *   - 2026-06-03: Sprint 57.73 Track C — add AP-2 banner for deferred memory op-timeline feature (fixture markers)
 *   - 2026-05-25: Initial creation (Sprint 57.42 Day 1) — memory matrix full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-governance.jsx L600-656
 *   - ./MemoryView.tsx (parent — owns cursor + playing state + setInterval loop)
 *   - ../hooks/useMemoryOps.ts (server cache; dedup-shared with RecentMemoryOpsCard)
 *   - ../../../components/mockup-ui.tsx (Card + Button primitives)
 */

import { Button, Card } from "../../../components/mockup-ui";
import { useMemoryOps } from "../hooks/useMemoryOps";

export interface TimeTravelScrubberProps {
  /** Cursor time (ms). null = latest/all (renders as "now"). */
  cursor: number | null;
  onCursor: (next: number) => void;
  playing: boolean;
  onPlay: () => void;
}

function formatMs(ms: number): string {
  const d = new Date(ms);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

export function TimeTravelScrubber({
  cursor,
  onCursor,
  playing,
  onPlay,
}: TimeTravelScrubberProps): JSX.Element {
  const { data } = useMemoryOps();
  const ops = data?.ops ?? [];
  const times = ops.map((o) => o.created_at_ms);
  const minMs = times.length ? Math.min(...times) : 0;
  const maxMs = times.length ? Math.max(...times) : 0;
  // A real time domain needs ≥2 distinct timestamps; otherwise no marks (guards
  // div-by-zero on the [minMs, maxMs] normalization).
  const hasDomain = ops.length >= 2 && maxMs > minMs;

  const cursorMs = cursor ?? maxMs;
  const sliderValue = hasDomain ? ((cursorMs - minMs) / (maxMs - minMs)) * 100 : 100;
  const onSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!hasDomain) return;
    const frac = Number(e.target.value) / 100;
    onCursor(Math.round(minMs + frac * (maxMs - minMs)));
  };
  const atLatest = !hasDomain || cursorMs >= maxMs;

  return (
    <Card bodyClass="dense">
      <div className="row" style={{ gap: 12 }}>
        <Button
          variant={playing ? "warning" : "outline"}
          size="sm"
          icon={playing ? "pause" : "play"}
          onClick={onPlay}
        >
          {playing ? "Pause" : "Replay 24h"}
        </Button>
        <Button variant="ghost" size="sm" onClick={() => hasDomain && onCursor(maxMs)}>
          Now
        </Button>
        <div className="grow" style={{ position: "relative" }}>
          <div style={{ position: "relative", height: 36 }}>
            {/* Op markers behind slider (one per real op) */}
            <div style={{ position: "absolute", left: 0, right: 0, top: 14, height: 8 }}>
              {hasDomain &&
                ops.map((op, i) => {
                  const left = ((op.created_at_ms - minMs) / (maxMs - minMs)) * 100;
                  const color = op.op === "WRITE" ? "var(--memory)" : "var(--warning)";
                  return (
                    <div
                      key={i}
                      data-testid="memory-scrubber-mark"
                      title={`${op.op} · ${op.scope}.${op.key ?? ""}`}
                      style={{
                        position: "absolute",
                        left: `${left}%`,
                        width: 2,
                        height: 8,
                        background: color,
                        transform: "translateX(-50%)",
                        borderRadius: 1,
                      }}
                    />
                  );
                })}
            </div>
            <input
              type="range"
              min={0}
              max={100}
              step={0.5}
              value={sliderValue}
              onChange={onSliderChange}
              disabled={!hasDomain}
              aria-label="Time travel scrubber"
              style={{
                width: "100%",
                accentColor: "var(--primary)",
                position: "absolute",
                inset: 0,
              }}
            />
            {!hasDomain && (
              <div
                data-testid="memory-scrubber-empty"
                style={{
                  position: "absolute",
                  left: 0,
                  right: 0,
                  bottom: 0,
                  display: "flex",
                  justifyContent: "center",
                  pointerEvents: "none",
                }}
              >
                <span className="mono subtle" style={{ fontSize: 10 }}>
                  no operations
                </span>
              </div>
            )}
          </div>
        </div>
        <div className="col" style={{ gap: 2, minWidth: 100, textAlign: "right" }}>
          <span
            className="mono"
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: !atLatest ? "var(--warning)" : "var(--fg)",
            }}
          >
            {atLatest ? "now" : formatMs(cursorMs)}
          </span>
          <span className="mono subtle" style={{ fontSize: 10.5 }}>
            {hasDomain ? formatMs(maxMs) : "—"}
          </span>
        </div>
      </div>
    </Card>
  );
}
