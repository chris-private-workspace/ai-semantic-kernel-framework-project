/**
 * File: frontend/src/features/memory/components/MemoryPageHeader.tsx
 * Purpose: Memory page header — title / sub / route pill / time-travel cursor badge / 3 action buttons.
 * Category: Frontend / memory / components
 * Scope: Phase 57 / Sprint 57.42 Day 1 (mockup-fidelity rebuild)
 *
 * Description:
 *   Verbatim port of `reference/design-mockups/page-governance.jsx:480-495`
 *   (`.page-head` section of MemoryPage). Title "Memory Layers" + sub
 *   "Dual-axis · 5 scope × 3 time scale" + `/memory` route pill + entries count
 *   + conditional time-travel info Badge when cursor != null + 3 action buttons
 *   (Time travel / Return to now toggle + Export AP-2 + New entry AP-2).
 *
 *   The Time-travel button toggles variant outline ↔ warning based on cursor;
 *   onClick resets cursor to null (returns to "now"). The cursor is a ms
 *   timestamp (Sprint 57.77; was a fixture minute-offset); the Badge shows the
 *   scrubbed op time HH:MM:SS, matching the TimeTravelScrubber cursor display.
 *   Export + New entry are visual-only AP-2 stubs.
 *
 *   Entries count is REAL (Sprint 57.73 Track C): consumes useMemoryMatrix()
 *   → matrix `total`. React Query dedups the shared key so this issues no extra
 *   request beyond MemoryMatrix's. While loading the count is hidden (a subtle
 *   "…" placeholder, never a fabricated number).
 *
 * Key Components:
 *   - MemoryPageHeader: query-consuming functional, props { cursor, onResetCursor }
 *
 * Created: 2026-05-25 (Sprint 57.42 Day 1)
 * Last Modified: 2026-06-04
 *
 * Modification History (newest-first):
 *   - 2026-06-04: Sprint 57.77 — cursor ms|null (was minute-offset); time-travel Badge shows HH:MM:SS
 *   - 2026-06-03: Sprint 57.73 Track C — entries count from useMemoryMatrix total (drop TOTAL_ENTRIES fixture)
 *   - 2026-05-25: Initial creation (Sprint 57.42 Day 1) — memory matrix full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-governance.jsx L480-495
 *   - ./MemoryView.tsx (parent — owns cursor state)
 *   - ../hooks/useMemoryMatrix.ts (server cache; dedup-shared with MemoryMatrix)
 *   - ../../../components/mockup-ui.tsx (Button + Badge primitives)
 */

import { Badge, Button } from "../../../components/mockup-ui";
import { useMemoryMatrix } from "../hooks/useMemoryMatrix";

export interface MemoryPageHeaderProps {
  /** Time-travel cursor (ms). null = at latest/now; non-null = scrubbed to a past op time. */
  cursor: number | null;
  onResetCursor: () => void;
}

/** created_at_ms → HH:MM:SS (client-local; matches the TimeTravelScrubber cursor display). */
function formatMs(ms: number): string {
  const d = new Date(ms);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

export function MemoryPageHeader({ cursor, onResetCursor }: MemoryPageHeaderProps): JSX.Element {
  const { data } = useMemoryMatrix();
  const entriesLabel = data ? `${data.total.toLocaleString()} entries` : "… entries";
  const isTimeTravel = cursor != null;
  const onExport = () => {
    window.alert("Export: backend gap (Phase 58+) — memory export endpoint pending");
  };
  const onNewEntry = () => {
    window.alert("New entry: backend gap (Phase 58+) — memory POST endpoint pending");
  };
  return (
    <div className="page-head">
      <div>
        <div className="page-title">Memory Layers</div>
        <div className="page-sub">
          Dual-axis · 5 scope × 3 time scale
          <span className="route-pill">/memory</span>
          <span className="mono subtle">· {entriesLabel}</span>
          {isTimeTravel && (
            <Badge tone="info" dot>
              time-travel · {formatMs(cursor)}
            </Badge>
          )}
        </div>
      </div>
      <div className="page-actions">
        <Button
          variant={isTimeTravel ? "warning" : "outline"}
          size="sm"
          icon="clock"
          onClick={onResetCursor}
        >
          {isTimeTravel ? "Return to now" : "Time travel"}
        </Button>
        <Button variant="outline" size="sm" icon="download" onClick={onExport}>
          Export
        </Button>
        <Button variant="primary" size="sm" icon="plus" onClick={onNewEntry}>
          New entry
        </Button>
      </div>
    </div>
  );
}
