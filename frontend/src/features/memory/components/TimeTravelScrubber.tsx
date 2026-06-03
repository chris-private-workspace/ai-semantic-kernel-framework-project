/* eslint-disable no-restricted-syntax -- mockup verbatim CSS literals; mockup-fidelity (Sprint 57.42). See reference/design-mockups/page-governance.jsx L600-656. */
/**
 * File: frontend/src/features/memory/components/TimeTravelScrubber.tsx
 * Purpose: Time-travel scrubber Card — 24h range slider with op markers + playback control + cursor display.
 * Category: Frontend / memory / components
 * Scope: Phase 57 / Sprint 57.42 Day 1 (mockup-fidelity rebuild)
 *
 * Description:
 *   Verbatim port of `reference/design-mockups/page-governance.jsx:600-656`
 *   (`TimeTravelScrubber` component). Wraps in Card bodyClass="dense".
 *   Renders:
 *     - Replay 24h / Pause toggle button (outline → warning when playing)
 *     - Now ghost button (resets cursor to 0)
 *     - Range slider mapped -1440..0 minutes via sliderValue formula
 *     - 12 op markers (WRITE/READ/EXPIRE) positioned at left%=(-t/1440)*100
 *     - 6 TIME_TRAVEL_MARKS labels (reversed; spread-between)
 *     - Right cursor display: mono "now" / "T-Xm" + relative time mono subtle
 *
 *   Component is pure controlled: cursor/onCursor/playing/onPlay are props.
 *   Parent (MemoryView) owns useEffect setInterval playback loop.
 *
 * Key Components:
 *   - TimeTravelScrubber: stateless, controlled component
 *
 * Created: 2026-05-25 (Sprint 57.42 Day 1)
 * Last Modified: 2026-06-03
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Sprint 57.73 Track C — add AP-2 banner for deferred memory op-timeline feature (fixture markers)
 *   - 2026-05-25: Initial creation (Sprint 57.42 Day 1) — memory matrix full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-governance.jsx L600-656
 *   - ./MemoryView.tsx (parent — owns cursor + playing state + setInterval loop)
 *   - ../_fixtures.ts (MEMORY_OPS_TIMELINE + TIME_TRAVEL_MARKS)
 *   - ../../../components/mockup-ui.tsx (Card + Button primitives)
 *   - ../../../components/ui/BackendGapBanner.tsx (AP-2 declaration)
 */

import { Button, Card } from "../../../components/mockup-ui";
import { BackendGapBanner } from "../../../components/ui/BackendGapBanner";
import { MEMORY_OPS_TIMELINE, TIME_TRAVEL_MARKS } from "../_fixtures";

export interface TimeTravelScrubberProps {
  cursor: number;
  onCursor: (next: number) => void;
  playing: boolean;
  onPlay: () => void;
}

export function TimeTravelScrubber({
  cursor,
  onCursor,
  playing,
  onPlay,
}: TimeTravelScrubberProps): JSX.Element {
  // Maps cursor (-1440..0) to slider value (0..100)
  const sliderValue = (cursor / -1440) * 100;
  const onSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onCursor(Math.round((-1440 * (Number(e.target.value) / 100)) / 5) * 5);
  };

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
        <Button variant="ghost" size="sm" onClick={() => onCursor(0)}>
          Now
        </Button>
        <div className="grow" style={{ position: "relative" }}>
          <div style={{ position: "relative", height: 36 }}>
            {/* Op markers behind slider */}
            <div style={{ position: "absolute", left: 0, right: 0, top: 14, height: 8 }}>
              {MEMORY_OPS_TIMELINE.map((op, i) => {
                const left = ((-op.t) / 1440) * 100;
                const color =
                  op.op === "WRITE"
                    ? "var(--memory)"
                    : op.op === "READ"
                      ? "var(--info)"
                      : "var(--warning)";
                return (
                  <div
                    key={i}
                    title={`${op.op} · ${op.scope}.${op.k}`}
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
              aria-label="Time travel scrubber"
              style={{
                width: "100%",
                accentColor: "var(--primary)",
                position: "absolute",
                inset: 0,
              }}
            />
            <div
              style={{
                position: "absolute",
                left: 0,
                right: 0,
                bottom: 0,
                display: "flex",
                justifyContent: "space-between",
                pointerEvents: "none",
              }}
            >
              {TIME_TRAVEL_MARKS.slice().reverse().map((m) => (
                <span key={m.t} className="mono subtle" style={{ fontSize: 10 }}>
                  {m.label}
                </span>
              ))}
            </div>
          </div>
        </div>
        <div className="col" style={{ gap: 2, minWidth: 100, textAlign: "right" }}>
          <span
            className="mono"
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: cursor < 0 ? "var(--warning)" : "var(--fg)",
            }}
          >
            {cursor === 0 ? "now" : `T-${Math.abs(cursor)}m`}
          </span>
          <span className="mono subtle" style={{ fontSize: 10.5 }}>
            {cursor === 0
              ? "10:42:28"
              : cursor > -60
                ? `~${10}:${String(42 - Math.abs(cursor)).padStart(2, "0")}`
                : cursor > -1440
                  ? `~${10 - Math.floor(Math.abs(cursor) / 60)}h ago`
                  : "yesterday"}
          </span>
        </div>
      </div>
      <BackendGapBanner reason="Memory operation history (per-op audit / version log) is a deferred backend feature — see AD-Memory-OpsHistory-Backend. The op markers + scrubber timeline are fixtures." />
    </Card>
  );
}
