/**
 * File: frontend/tests/unit/memory/TimeTravelScrubber.test.tsx
 * Purpose: Vitest coverage for TimeTravelScrubber — marks from real ops, empty→no marks+hint, scrub fires onCursor(ms).
 * Category: Frontend / Tests / memory / unit
 * Scope: Phase 57 / Sprint 57.42 Day 2 → 57.77 (real-data wire)
 *
 * Description:
 *   Sprint 57.77 rewrite (was fixture-minute slider mapping): mocks useMemoryOps
 *   and asserts the wired behavior —
 *     - one mark per op when ops ≥ 2 (real created_at_ms domain)
 *     - empty ops → no marks + the subtle "no operations" hint + disabled slider
 *     - scrubbing the slider fires onCursor with a ms timestamp in [minMs, maxMs]
 *     - playing=true swaps the button label to "Pause"
 *
 *   setInterval playback lives in MemoryView (parent), NOT here — component is
 *   pure controlled.
 *
 * Created: 2026-05-25 (Sprint 57.42 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-06-04: Sprint 57.77 — rewrite for real-data wire (marks from ops; empty hint; scrub→onCursor ms)
 *   - 2026-05-25: Initial creation (Sprint 57.42 Day 2)
 */

import "@testing-library/jest-dom/vitest";

import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TimeTravelScrubber } from "@/features/memory/components/TimeTravelScrubber";
import * as hook from "@/features/memory/hooks/useMemoryOps";
import type { MemoryOpsResponse } from "@/features/memory/types";

type HookReturn = ReturnType<typeof hook.useMemoryOps>;

const MIN = 1_700_000_000_000;
const MAX = 1_700_000_010_000;
const OPS: MemoryOpsResponse = {
  ops: [
    { op: "WRITE", scope: "user", key: "a", time_scale: null, value_snapshot: "x", actor: null, created_at_ms: MAX },
    { op: "EVICT", scope: "tenant", key: "b", time_scale: null, value_snapshot: null, actor: null, created_at_ms: 1_700_000_005_000 },
    { op: "WRITE", scope: "user", key: "c", time_scale: null, value_snapshot: "y", actor: null, created_at_ms: MIN },
  ],
  next_cursor: null,
};

function mockHook(data: MemoryOpsResponse | undefined): void {
  vi.spyOn(hook, "useMemoryOps").mockReturnValue({
    data,
    isLoading: false,
    isError: false,
    error: null,
  } as HookReturn);
}

describe("TimeTravelScrubber (Sprint 57.77 real-data wire)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders one mark per op when ops ≥ 2", () => {
    mockHook(OPS);
    render(<TimeTravelScrubber cursor={null} onCursor={vi.fn()} playing={false} onPlay={vi.fn()} />);
    expect(screen.getAllByTestId("memory-scrubber-mark").length).toBe(OPS.ops.length);
  });

  it("empty ops → no marks + 'no operations' hint + disabled slider", () => {
    mockHook({ ops: [], next_cursor: null });
    render(<TimeTravelScrubber cursor={null} onCursor={vi.fn()} playing={false} onPlay={vi.fn()} />);
    expect(screen.queryAllByTestId("memory-scrubber-mark").length).toBe(0);
    expect(screen.getByTestId("memory-scrubber-empty")).toBeInTheDocument();
    expect(screen.getByText("no operations")).toBeInTheDocument();
    const slider = screen.getByRole("slider", { name: /time travel scrubber/i }) as HTMLInputElement;
    expect(slider).toBeDisabled();
  });

  it("scrubbing fires onCursor with a ms timestamp in [minMs, maxMs]", () => {
    const onCursor = vi.fn();
    mockHook(OPS);
    render(<TimeTravelScrubber cursor={null} onCursor={onCursor} playing={false} onPlay={vi.fn()} />);
    const slider = screen.getByRole("slider", { name: /time travel scrubber/i });
    fireEvent.change(slider, { target: { value: "50" } });
    expect(onCursor).toHaveBeenCalledTimes(1);
    const arg = onCursor.mock.calls[0][0] as number;
    expect(arg).toBeGreaterThanOrEqual(MIN);
    expect(arg).toBeLessThanOrEqual(MAX);
    // 50% of [MIN, MAX] → the midpoint.
    expect(arg).toBe((MIN + MAX) / 2);
  });

  it("playing=true swaps button label to 'Pause'", () => {
    mockHook(OPS);
    render(<TimeTravelScrubber cursor={null} onCursor={vi.fn()} playing={true} onPlay={vi.fn()} />);
    expect(screen.getByRole("button", { name: /^pause$/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /replay 24h/i })).not.toBeInTheDocument();
  });
});
