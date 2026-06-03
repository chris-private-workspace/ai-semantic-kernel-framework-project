/**
 * File: frontend/tests/unit/memory/MemoryPageHeader.test.tsx
 * Purpose: Vitest coverage for MemoryPageHeader — title / sub / route-pill / REAL entries total (from /matrix) / cursor-aware Badge + button swap.
 * Category: Frontend / Tests / memory / unit
 * Scope: Phase 57 / Sprint 57.73 Track C (A-6b frontend half)
 *
 * Description:
 *   - Renders "Memory Layers" title + sub "Dual-axis · 5 scope × 3 time scale"
 *     + `.route-pill` "/memory"
 *   - Entries count is REAL: from useMemoryMatrix() total (seeded via mocked
 *     memoryService.fetchMatrix + QueryClientProvider)
 *   - Loading → subtle "… entries" placeholder (never a fabricated number)
 *   - cursor < 0 renders conditional time-travel Badge + "Return to now" button
 *   - cursor === 0 hides Badge + shows "Time travel" button label
 *
 * Created: 2026-05-25 (Sprint 57.42 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Sprint 57.73 Track C — entries count from real /matrix total; QueryClientProvider; drop entriesTotal prop
 *   - 2026-05-25: Initial creation (Sprint 57.42 Day 2)
 */

import "@testing-library/jest-dom/vitest";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { MemoryPageHeader } from "@/features/memory/components/MemoryPageHeader";
import { memoryService } from "@/features/memory/services/memoryService";
import type { MemoryMatrixResponse } from "@/features/memory/types";

function renderWithClient(ui: ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

const SAMPLE: MemoryMatrixResponse = {
  cells: [{ layer: "tenant", time_scale: "permanent", count: 7 }],
  total: 7,
  gapped_layers: ["role", "session"],
};

describe("MemoryPageHeader (Sprint 57.73 Track C)", () => {
  it("renders title, sub-text, /memory route pill, REAL entries total, and 3 action buttons (cursor=0)", async () => {
    vi.spyOn(memoryService, "fetchMatrix").mockResolvedValueOnce(SAMPLE);
    renderWithClient(<MemoryPageHeader cursor={0} onResetCursor={vi.fn()} />);

    expect(screen.getByText("Memory Layers")).toBeInTheDocument();
    expect(screen.getByText(/Dual-axis · 5 scope × 3 time scale/)).toBeInTheDocument();
    expect(screen.getByText("/memory")).toBeInTheDocument();
    // real total from /matrix (after fetch resolves)
    expect(await screen.findByText(/7 entries/)).toBeInTheDocument();

    // cursor=0 → "Time travel" button label (no "Return to now")
    expect(screen.getByRole("button", { name: /time travel/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /return to now/i })).not.toBeInTheDocument();
    // AP-2 visual-only stub buttons
    expect(screen.getByRole("button", { name: /export/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /new entry/i })).toBeInTheDocument();
  });

  it("shows '… entries' placeholder while the matrix total is loading (no fabricated number)", () => {
    vi.spyOn(memoryService, "fetchMatrix").mockImplementation(() => new Promise(() => {}));
    renderWithClient(<MemoryPageHeader cursor={0} onResetCursor={vi.fn()} />);
    expect(screen.getByText(/… entries/)).toBeInTheDocument();
  });

  it("cursor<0 swaps button to 'Return to now' and renders time-travel Badge with absolute minutes", async () => {
    vi.spyOn(memoryService, "fetchMatrix").mockResolvedValueOnce(SAMPLE);
    renderWithClient(<MemoryPageHeader cursor={-42} onResetCursor={vi.fn()} />);

    expect(screen.getByRole("button", { name: /return to now/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^time travel$/i })).not.toBeInTheDocument();
    expect(screen.getByText(/time-travel · 42m ago/i)).toBeInTheDocument();
  });
});
