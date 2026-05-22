/**
 * File: frontend/tests/unit/features/overview/ActiveLoopsCard.test.tsx
 * Purpose: Vitest coverage for ActiveLoopsCard — loading / error / empty / happy 5-col row.
 * Category: Frontend / Tests / features / overview
 * Scope: Phase 57 / Sprint 57.27 Day 1 / US-B2
 *
 * Created: 2026-05-21 (Sprint 57.27 Day 1 / US-B2)
 *
 * Modification History (newest-first):
 *   - 2026-05-21: Initial creation (Sprint 57.27 Day 1) — adapted from OverviewPage.test.tsx
 */

import "@testing-library/jest-dom/vitest";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as loopsService from "@/features/loops/services/loopsService";

import { ActiveLoopsCard } from "@/features/overview/components/ActiveLoopsCard";

function wrap(children: ReactNode) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, refetchInterval: false } },
  });
  return (
    <QueryClientProvider client={client}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("ActiveLoopsCard", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders loading subtitle while the query is pending", () => {
    vi.spyOn(loopsService, "fetchLoops").mockReturnValue(new Promise(() => {}));
    render(wrap(<ActiveLoopsCard />));
    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("renders error banner when fetchLoops rejects", async () => {
    vi.spyOn(loopsService, "fetchLoops").mockRejectedValue(new Error("boom"));
    render(wrap(<ActiveLoopsCard />));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("boom");
    });
  });

  it("renders empty state when no active loops returned", async () => {
    vi.spyOn(loopsService, "fetchLoops").mockResolvedValue({
      items: [],
      next_cursor: null,
      page_size: 10,
    });
    render(wrap(<ActiveLoopsCard />));
    await waitFor(() => {
      expect(screen.getByText("No running loops right now.")).toBeInTheDocument();
    });
  });

  it("renders a happy-path 5-col loop row with status badge + session + tokens + turn", async () => {
    vi.spyOn(loopsService, "fetchLoops").mockResolvedValue({
      items: [
        {
          session_id: "11111111-2222-3333-4444-555555555555",
          status: "running",
          started_at_ms: Date.now() - 12_000,
          ended_at_ms: null,
          turn_count: 6,
          token_usage: 18420,
          total_cost_usd: "0.42",
        },
      ],
      next_cursor: null,
      page_size: 10,
    });
    render(wrap(<ActiveLoopsCard />));
    await waitFor(() => {
      expect(screen.getByText("11111111", { exact: false })).toBeInTheDocument();
    });
    expect(screen.getByText("running")).toBeInTheDocument();
    expect(screen.getByText(/18,420 tok/)).toBeInTheDocument();
    expect(screen.getByText("turn 6/50")).toBeInTheDocument();
  });
});
