/* eslint-disable no-restricted-syntax -- mockup verbatim layout literals (height spacers between sections); mockup-fidelity (Sprint 57.42). See reference/design-mockups/page-governance.jsx L478-596. */
/**
 * File: frontend/src/features/memory/components/MemoryView.tsx
 * Purpose: Memory page container — assembles header + scrubber + matrix + 2-col bottom (RecentOps + GDPR) with cursor + playback state.
 * Category: Frontend / memory / components
 * Scope: Phase 57 / Sprint 57.42 Day 1 (mockup-fidelity rebuild) → 57.77 (real-data wire)
 *
 * Description:
 *   Verbatim port of `reference/design-mockups/page-governance.jsx:462-597`
 *   MemoryPage component. Container owns local React state:
 *     - cursor: ms timestamp of the time-travel position; null = latest/all
 *     - playing: boolean for replay playback
 *
 *   Sprint 57.77: cursor is now a ms timestamp (was fixture minute-offset). The
 *   scrubber + RecentOps derive their op time domain from useMemoryOps (React
 *   Query dedups the shared key, so this container reads the same cached page to
 *   bound playback). The playback setInterval advances cursor across the real op
 *   time range [minMs, maxMs]; it pauses + resets cursor to null at the end. The
 *   cursor flows into RecentMemoryOpsCard to filter ops to created_at_ms ≤ cursor
 *   (browse-ops-timeline; honest, not point-in-time state reconstruction). With
 *   0/1 ops, play is a no-op (no domain to animate).
 *
 *   Render structure (mockup-faithful, unchanged mount order):
 *     <MemoryPageHeader ... />
 *     <TimeTravelScrubber ... />
 *     <div style={{ height: 14 }} />
 *     <MemoryMatrix />
 *     <div style={{ height: 16 }} />
 *     <div className="grid-main"><RecentMemoryOpsCard /><GdprErasureCard /></div>
 *
 * Key Components:
 *   - MemoryView: stateful container (cursor: ms | null + playing)
 *
 * Created: 2026-05-25 (Sprint 57.42 Day 1)
 * Last Modified: 2026-06-04
 *
 * Modification History (newest-first):
 *   - 2026-06-04: Sprint 57.77 — cursor is ms (null=latest); playback advances over real op time range
 *   - 2026-06-03: Sprint 57.73 Track C — MemoryMatrix no longer takes cursor (wired to real /matrix)
 *   - 2026-05-25: Initial creation (Sprint 57.42 Day 1) — memory matrix full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-governance.jsx L462-597 MemoryPage
 *   - ./MemoryPageHeader.tsx ./TimeTravelScrubber.tsx ./MemoryMatrix.tsx
 *     ./RecentMemoryOpsCard.tsx ./GdprErasureCard.tsx
 *   - ../hooks/useMemoryOps.ts (shared op time domain for playback bounds)
 *   - ../../../pages/memory/index.tsx (parent — auth gate + AppShellV2 wrap)
 */

import { useEffect, useState } from "react";

import { GdprErasureCard } from "./GdprErasureCard";
import { MemoryMatrix } from "./MemoryMatrix";
import { MemoryPageHeader } from "./MemoryPageHeader";
import { RecentMemoryOpsCard } from "./RecentMemoryOpsCard";
import { TimeTravelScrubber } from "./TimeTravelScrubber";
import { useMemoryOps } from "../hooks/useMemoryOps";

// Playback steps across the op time range in this many frames (one tick / 200ms).
const PLAYBACK_FRAMES = 48;

export function MemoryView(): JSX.Element {
  const [cursor, setCursor] = useState<number | null>(null);
  const [playing, setPlaying] = useState(false);

  const { data } = useMemoryOps();
  const times = (data?.ops ?? []).map((o) => o.created_at_ms);
  const minMs = times.length ? Math.min(...times) : 0;
  const maxMs = times.length ? Math.max(...times) : 0;
  const hasDomain = times.length >= 2 && maxMs > minMs;

  useEffect(() => {
    if (!playing) return;
    if (!hasDomain) {
      // No range to animate — play is a no-op on an empty/single-op timeline.
      setPlaying(false);
      return;
    }
    const step = (maxMs - minMs) / PLAYBACK_FRAMES;
    const id = setInterval(() => {
      setCursor((c) => {
        const next = (c ?? minMs) + step;
        if (next >= maxMs) {
          setPlaying(false);
          return null; // reset to latest/all at the end of the range
        }
        return next;
      });
    }, 200);
    return () => clearInterval(id);
  }, [playing, hasDomain, minMs, maxMs]);

  // Header time-travel state is "active" only when scrubbed to a real PAST op
  // time (cursor set AND strictly before the latest op). cursor == maxMs (the
  // "Now" button) or null both read as "at latest" → header shows "Time travel".
  const headerCursor = hasDomain && cursor != null && cursor < maxMs ? cursor : null;

  return (
    <div>
      <MemoryPageHeader cursor={headerCursor} onResetCursor={() => setCursor(null)} />
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
        <RecentMemoryOpsCard cursor={cursor} />
        <GdprErasureCard />
      </div>
    </div>
  );
}
