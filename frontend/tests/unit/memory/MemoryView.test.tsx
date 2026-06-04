/**
 * File: frontend/tests/unit/memory/MemoryView.test.tsx
 * Purpose: Vitest integration coverage for MemoryView — assembles all 5 children; matrix/header wired to /matrix, ops/timeline still fixtures.
 * Category: Frontend / Tests / memory / unit
 * Scope: Phase 57 / Sprint 57.73 Track C (A-6b frontend half)
 *
 * Description:
 *   - Renders MemoryPageHeader (title "Memory Layers" + real /matrix total)
 *   - Renders TimeTravelScrubber (slider role + "Replay 24h" button — real ops)
 *   - Renders MemoryMatrix (5×3 grid headers — backend vocab permanent / quarterly / daily)
 *   - Renders RecentMemoryOpsCard (title "Recent memory ops" — real ops rows)
 *   - Renders GdprErasureCard (title "GDPR right-to-erasure")
 *   - Initial state cursor=null → MemoryPageHeader shows "Time travel" button
 *
 *   MemoryView now contains query-consuming children (MemoryMatrix +
 *   MemoryPageHeader call useMemoryMatrix; TimeTravelScrubber + RecentMemoryOpsCard
 *   call useMemoryOps); render under a QueryClientProvider with mocked
 *   memoryService.fetchMatrix + fetchOps.
 *
 * Created: 2026-05-25 (Sprint 57.42 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-06-04: Sprint 57.77 — mock fetchOps too; assert real op row renders; cursor=null init
 *   - 2026-06-03: Sprint 57.73 Track C — wrap in QueryClientProvider + mock /matrix; backend vocab headers; assert fixtures retained
 *   - 2026-05-25: Initial creation (Sprint 57.42 Day 2)
 */

import "@testing-library/jest-dom/vitest";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MemoryView } from "@/features/memory/components/MemoryView";
import { memoryService } from "@/features/memory/services/memoryService";
import type { MemoryMatrixResponse, MemoryOpsResponse } from "@/features/memory/types";

function renderWithClient(ui: ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

const SAMPLE: MemoryMatrixResponse = {
  cells: [
    { layer: "system", time_scale: "permanent", count: 1 },
    { layer: "tenant", time_scale: "permanent", count: 2 },
    { layer: "user", time_scale: "permanent", count: 1 },
    { layer: "user", time_scale: "quarterly", count: 1 },
    { layer: "user", time_scale: "daily", count: 2 },
  ],
  total: 7,
  gapped_layers: ["role", "session"],
};

const OPS_SAMPLE: MemoryOpsResponse = {
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
      key: "anomaly.token_spike",
      time_scale: null,
      value_snapshot: null,
      actor: null,
      created_at_ms: 1_700_000_001_000,
    },
  ],
  next_cursor: null,
};

describe("MemoryView (Sprint 57.77 real-data wire)", () => {
  beforeEach(() => {
    vi.spyOn(memoryService, "fetchMatrix").mockResolvedValue(SAMPLE);
    vi.spyOn(memoryService, "fetchOps").mockResolvedValue(OPS_SAMPLE);
  });

  it("integrates all 5 child components with cursor=null initial state", async () => {
    renderWithClient(<MemoryView />);

    // 1. MemoryPageHeader
    expect(screen.getByText("Memory Layers")).toBeInTheDocument();
    expect(screen.getByText("/memory")).toBeInTheDocument();
    // cursor=null init → headerCursor=null → "Time travel" button (NOT "Return to now")
    expect(screen.getByRole("button", { name: /^time travel$/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /return to now/i })).not.toBeInTheDocument();

    // 2. TimeTravelScrubber (real ops)
    expect(screen.getByRole("slider", { name: /time travel scrubber/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /replay 24h/i })).toBeInTheDocument();

    // 3. MemoryMatrix — backend vocab headers (after /matrix resolves)
    expect(await screen.findByText("permanent")).toBeInTheDocument();
    expect(screen.getByText("quarterly")).toBeInTheDocument();
    expect(screen.getByText("daily")).toBeInTheDocument();

    // 4. RecentMemoryOpsCard — real op row renders (after /ops resolves)
    expect(screen.getByText("Recent memory ops")).toBeInTheDocument();
    expect(await screen.findByText("preferences.rca_format")).toBeInTheDocument();

    // 5. GdprErasureCard
    expect(screen.getByText("GDPR right-to-erasure")).toBeInTheDocument();
  });
});
