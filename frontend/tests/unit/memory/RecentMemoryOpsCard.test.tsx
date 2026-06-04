/**
 * File: frontend/tests/unit/memory/RecentMemoryOpsCard.test.tsx
 * Purpose: Vitest coverage for RecentMemoryOpsCard — real ops rows, null→"—", cursor filter, loading/error/empty states.
 * Category: Frontend / Tests / memory / unit
 * Scope: Phase 57 / Sprint 57.42 Day 2 → 57.77 (real-data wire)
 *
 * Description:
 *   Sprint 57.77 rewrite (was fixture-row assertions): mocks useMemoryOps and
 *   asserts the wired behavior —
 *     - real rows render (op badge / scope / key / value / actor / When)
 *     - null fields render the "—" placeholder
 *     - the cursor prop drops ops with created_at_ms > cursor (scrub filter)
 *     - loading / error / empty states render the mockup-native single rows
 *
 * Created: 2026-05-25 (Sprint 57.42 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-06-04: Sprint 57.77 — rewrite for real-data wire (mock useMemoryOps; rows/null/cursor/states)
 *   - 2026-06-03: Sprint 57.73 Track C — update AP-2 banner assertion to reworded deferred-feature text
 *   - 2026-05-25: Initial creation (Sprint 57.42 Day 2)
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RecentMemoryOpsCard } from "@/features/memory/components/RecentMemoryOpsCard";
import * as hook from "@/features/memory/hooks/useMemoryOps";
import type { MemoryOpsResponse } from "@/features/memory/types";

type HookReturn = ReturnType<typeof hook.useMemoryOps>;

const OPS: MemoryOpsResponse = {
  ops: [
    {
      op: "WRITE",
      scope: "user",
      key: "preferences.rca_format",
      time_scale: "permanent",
      value_snapshot: "5-whys + timeline",
      actor: "incident-responder",
      created_at_ms: 1_700_000_002_000,
    },
    {
      op: "EVICT",
      scope: "tenant",
      key: null,
      time_scale: null,
      value_snapshot: null,
      actor: null,
      created_at_ms: 1_700_000_001_000,
    },
  ],
  next_cursor: null,
};

function mockHook(partial: Partial<HookReturn>): void {
  vi.spyOn(hook, "useMemoryOps").mockReturnValue({
    data: undefined,
    isLoading: false,
    isError: false,
    error: null,
    ...partial,
  } as HookReturn);
}

describe("RecentMemoryOpsCard (Sprint 57.77 real-data wire)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders Card title + 6-col headers + real op rows", () => {
    mockHook({ data: OPS });
    render(<RecentMemoryOpsCard />);

    expect(screen.getByText("Recent memory ops")).toBeInTheDocument();
    expect(screen.getByText("Op")).toBeInTheDocument();
    expect(screen.getByText("When")).toBeInTheDocument();

    expect(screen.getByText("WRITE")).toBeInTheDocument();
    expect(screen.getByText("EVICT")).toBeInTheDocument();
    expect(screen.getByText("preferences.rca_format")).toBeInTheDocument();
    expect(screen.getByText("5-whys + timeline")).toBeInTheDocument();
    expect(screen.getByText("incident-responder")).toBeInTheDocument();
  });

  it("renders '—' for null key / value / actor fields", () => {
    mockHook({ data: { ops: [OPS.ops[1]], next_cursor: null } });
    render(<RecentMemoryOpsCard />);
    // EVICT row has null key + value_snapshot + actor → three "—" cells.
    expect(screen.getAllByText("—").length).toBeGreaterThanOrEqual(3);
  });

  it("cursor prop drops ops newer than the cursor time", () => {
    mockHook({ data: OPS });
    // cursor = the older op's time → the newer WRITE (…002_000) is filtered out.
    render(<RecentMemoryOpsCard cursor={1_700_000_001_000} />);
    expect(screen.queryByText("WRITE")).not.toBeInTheDocument();
    expect(screen.getByText("EVICT")).toBeInTheDocument();
  });

  it("renders loading state", () => {
    mockHook({ isLoading: true });
    render(<RecentMemoryOpsCard />);
    expect(screen.getByTestId("memory-ops-loading")).toBeInTheDocument();
    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("renders error state with the error message", () => {
    mockHook({ isError: true, error: new Error("auditor role required") });
    render(<RecentMemoryOpsCard />);
    expect(screen.getByTestId("memory-ops-error")).toBeInTheDocument();
    expect(screen.getByText("auditor role required")).toBeInTheDocument();
  });

  it("renders empty state when there are no ops", () => {
    mockHook({ data: { ops: [], next_cursor: null } });
    render(<RecentMemoryOpsCard />);
    expect(screen.getByTestId("memory-ops-empty")).toBeInTheDocument();
    expect(screen.getByText("No memory operations recorded yet.")).toBeInTheDocument();
  });
});
