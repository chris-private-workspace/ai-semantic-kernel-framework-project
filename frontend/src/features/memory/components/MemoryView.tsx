/* eslint-disable no-restricted-syntax -- mockup verbatim layout literals (height spacers between sections); mockup-fidelity (Sprint 57.42). See reference/design-mockups/page-governance.jsx L478-596. */
/**
 * File: frontend/src/features/memory/components/MemoryView.tsx
 * Purpose: Memory page container — assembles header + scrubber + matrix + 2-col bottom (RecentOps + GDPR) with cursor + playback state.
 * Category: Frontend / memory / components
 * Scope: Phase 57 / Sprint 57.42 Day 1 (mockup-fidelity rebuild)
 *
 * Description:
 *   Verbatim port of `reference/design-mockups/page-governance.jsx:462-597`
 *   MemoryPage component. Container owns local React state:
 *     - cursor: minutes ago (0 = now; -1440..0 range)
 *     - playing: boolean for replay playback
 *
 *   useEffect setInterval loop: when playing, decrement cursor by 30 every
 *   200ms; stop at -1440 (resets `playing` to false). Cleanup on unmount.
 *
 *   Render structure (mockup-faithful):
 *     <MemoryPageHeader ... />
 *     <TimeTravelScrubber ... />
 *     <div style={{ height: 14 }} />
 *     <MemoryMatrix />
 *     <div style={{ height: 16 }} />
 *     <div className="grid-main"><RecentMemoryOpsCard /><GdprErasureCard /></div>
 *
 *   Sprint 57.73 Track C: MemoryMatrix is now wired to the real /matrix aggregate
 *   and no longer consumes `cursor` (the cursor-aware entry filter was a
 *   fixture-only behavior). The cursor + scrubber remain (fixture op-timeline)
 *   but no longer filter the matrix.
 *
 * Key Components:
 *   - MemoryView: stateful container (cursor + playing)
 *
 * Created: 2026-05-25 (Sprint 57.42 Day 1)
 * Last Modified: 2026-06-03
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Sprint 57.73 Track C — MemoryMatrix no longer takes cursor (wired to real /matrix)
 *   - 2026-05-25: Initial creation (Sprint 57.42 Day 1) — memory matrix full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-governance.jsx L462-597 MemoryPage
 *   - ./MemoryPageHeader.tsx ./TimeTravelScrubber.tsx ./MemoryMatrix.tsx
 *     ./RecentMemoryOpsCard.tsx ./GdprErasureCard.tsx
 *   - ../../../pages/memory/index.tsx (parent — auth gate + AppShellV2 wrap)
 */

import { useEffect, useState } from "react";

import { GdprErasureCard } from "./GdprErasureCard";
import { MemoryMatrix } from "./MemoryMatrix";
import { MemoryPageHeader } from "./MemoryPageHeader";
import { RecentMemoryOpsCard } from "./RecentMemoryOpsCard";
import { TimeTravelScrubber } from "./TimeTravelScrubber";

export function MemoryView(): JSX.Element {
  const [cursor, setCursor] = useState(0);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      setCursor((c) => {
        if (c <= -1440) {
          setPlaying(false);
          return -1440;
        }
        return c - 30;
      });
    }, 200);
    return () => clearInterval(id);
  }, [playing]);

  return (
    <div>
      <MemoryPageHeader cursor={cursor} onResetCursor={() => setCursor(0)} />
      <TimeTravelScrubber
        cursor={cursor}
        onCursor={setCursor}
        playing={playing}
        onPlay={() => setPlaying((p) => !p)}
      />
      <div style={{ height: 14 }} />
      <MemoryMatrix />
      <div style={{ height: 16 }} />
      <div className="grid-main">
        <RecentMemoryOpsCard />
        <GdprErasureCard />
      </div>
    </div>
  );
}
