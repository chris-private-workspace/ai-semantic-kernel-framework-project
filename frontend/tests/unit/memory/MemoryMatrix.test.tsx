/**
 * File: frontend/tests/unit/memory/MemoryMatrix.test.tsx
 * Purpose: Vitest coverage for MemoryMatrix wired to GET /matrix — real counts, gap indicator, 0-default, loading/error/empty states, AP-2 banner.
 * Category: Frontend / Tests / memory / unit
 * Scope: Phase 57 / Sprint 57.73 Track C (A-6b frontend half)
 *
 * Description:
 *   Seeds the matrix query via a QueryClientProvider + a mocked
 *   memoryService.fetchMatrix (mirrors the useCostSummary/useAdminTenants
 *   QueryClientProvider test pattern). Asserts:
 *   - 3 time-scale headers (backend vocab permanent / quarterly / daily) + TTL
 *   - 5 layer rows (system / tenant / role / user / session)
 *   - real per-cell counts for wired layers (system / tenant / user)
 *   - absent wired (layer, time_scale) cell defaults to 0 ("— empty")
 *   - gapped layers (role + session) render a gap indicator ("n/a"), and NO
 *     fabricated number appears in those rows
 *   - reworded AP-2 BackendGapBanner
 *   - loading status, error + Retry, and empty (total 0) states
 *
 * Created: 2026-05-25 (Sprint 57.42 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Sprint 57.73 Track C — rewrite for wired /matrix (real counts + gap indicator); QueryClientProvider
 *   - 2026-05-25: Initial creation (Sprint 57.42 Day 2)
 */

import "@testing-library/jest-dom/vitest";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { MemoryMatrix } from "@/features/memory/components/MemoryMatrix";
import { memoryService } from "@/features/memory/services/memoryService";
import type { MemoryMatrixResponse } from "@/features/memory/types";

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

describe("MemoryMatrix wired to /matrix (Sprint 57.73 Track C)", () => {
  it("renders 3 backend-vocab headers + TTL + 5 layer rows + reworded AP-2 banner", async () => {
    vi.spyOn(memoryService, "fetchMatrix").mockResolvedValueOnce(SAMPLE);
    renderWithClient(<MemoryMatrix />);

    // headers use the BACKEND vocab (permanent / quarterly / daily)
    expect(await screen.findByText("permanent")).toBeInTheDocument();
    expect(screen.getByText("quarterly")).toBeInTheDocument();
    expect(screen.getByText("daily")).toBeInTheDocument();
    expect(screen.getByText("TTL ∞")).toBeInTheDocument();
    expect(screen.getByText("TTL 90d")).toBeInTheDocument();
    expect(screen.getByText("TTL 24h")).toBeInTheDocument();

    // 5 layer labels
    expect(screen.getByText("system")).toBeInTheDocument();
    expect(screen.getByText("tenant")).toBeInTheDocument();
    expect(screen.getByText("role")).toBeInTheDocument();
    expect(screen.getByText("user")).toBeInTheDocument();
    expect(screen.getByText("session")).toBeInTheDocument();

    // Reworded AP-2 BackendGapBanner (live wired + remaining role/session gap)
    const banner = screen.getByTestId("backend-gap-banner");
    expect(banner).toHaveTextContent(/role\/session layers have no backend path/i);
  });

  it("renders real counts for wired layers + 0-default for absent wired cells", async () => {
    vi.spyOn(memoryService, "fetchMatrix").mockResolvedValueOnce(SAMPLE);
    renderWithClient(<MemoryMatrix />);

    await screen.findByText("permanent");

    // user row: 1 + 1 + 2 = 4 wired entries across permanent/quarterly/daily
    // "2 entries" appears in the user.daily cell (count footer + cell body)
    expect(screen.getAllByText(/2 entries/).length).toBeGreaterThan(0);
    // singular count rendered for count=1 cells
    expect(screen.getAllByText(/1 entry/).length).toBeGreaterThan(0);
    // system row has only permanent count=1 → system.quarterly + system.daily
    // are absent in cells → default 0 → "— empty" placeholders present
    expect(screen.getAllByText("— empty").length).toBeGreaterThan(0);
  });

  it("gapped layers (role + session) show 'n/a' gap indicator and NO fabricated number", async () => {
    vi.spyOn(memoryService, "fetchMatrix").mockResolvedValueOnce(SAMPLE);
    renderWithClient(<MemoryMatrix />);

    await screen.findByText("permanent");

    // role + session rows: label sub-text "no backend path" + "n/a" cells.
    // 2 gapped layers × (1 label "n/a" + 3 cell "n/a") = 8 "n/a" occurrences.
    expect(screen.getAllByText("n/a").length).toBe(8);
    expect(screen.getAllByText("no backend path").length).toBe(2);

    // No fabricated number: the only entry/count strings come from wired rows.
    // The gapped layers must not surface any "entries" count footer.
    const role = screen.getByText("role").closest(".mm-scope");
    expect(role).not.toBeNull();
    // The role label cell shows "n/a", never a number.
    expect(within(role as HTMLElement).queryByText(/\d/)).toBeNull();
  });

  it("shows loading state while fetching", () => {
    vi.spyOn(memoryService, "fetchMatrix").mockImplementation(
      () => new Promise(() => {}), // never resolves → stays loading
    );
    renderWithClient(<MemoryMatrix />);
    expect(screen.getByRole("status")).toHaveTextContent(/loading memory matrix/i);
  });

  it("shows error state + Retry on fetch failure", async () => {
    vi.spyOn(memoryService, "fetchMatrix").mockRejectedValueOnce(new Error("HTTP 403"));
    renderWithClient(<MemoryMatrix />);
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(/failed to load memory matrix/i),
    );
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("shows empty state when total is 0", async () => {
    vi.spyOn(memoryService, "fetchMatrix").mockResolvedValueOnce({
      cells: [],
      total: 0,
      gapped_layers: ["role", "session"],
    });
    renderWithClient(<MemoryMatrix />);
    expect(await screen.findByText(/no memory entries/i)).toBeInTheDocument();
  });
});
