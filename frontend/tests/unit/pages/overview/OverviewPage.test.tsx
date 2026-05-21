/**
 * File: frontend/tests/unit/pages/overview/OverviewPage.test.tsx
 * Purpose: Vitest coverage for OverviewPage (US-C1) — loading / error / empty / happy / nav.
 * Category: Frontend / Tests / pages / overview
 * Scope: Phase 57 / Sprint 57.19 Day 3 / US-C1
 *
 * Created: 2026-05-17 (Sprint 57.19 Day 3 / US-C1)
 *
 * Modification History (newest-first):
 *   - 2026-05-21: Sprint 57.27 Day 3 — adapt for R7 in-page PageHead title (no AppShellV2 pageTitle prop)
 *   - 2026-05-17: Initial creation (Sprint 57.19 Day 3 / US-C1)
 */

import "@testing-library/jest-dom/vitest";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as loopsService from "@/features/loops/services/loopsService";

vi.mock("@/components/AppShellV2", () => ({
  // R7: AppShellV2 no longer receives pageTitle for /overview — in-page PageHead is the title.
  AppShellV2: ({ children }: { children: ReactNode }) => (
    <div data-testid="app-shell">{children}</div>
  ),
}));

vi.mock("@/features/auth/components/RequireAuth", () => ({
  RequireAuth: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

import { OverviewPage } from "@/pages/overview/OverviewPage";

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

describe("OverviewPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders in-page title via PageHead (R7: no AppShellV2 topbar duplicate)", () => {
    vi.spyOn(loopsService, "fetchLoops").mockResolvedValue({
      items: [],
      next_cursor: null,
      page_size: 10,
    });
    render(wrap(<OverviewPage />));
    // Title is rendered in-page by <PageHead> — assert the heading text is present
    expect(screen.getByText("Overview")).toBeInTheDocument();
  });

  it("renders all 4 KPI cards", () => {
    vi.spyOn(loopsService, "fetchLoops").mockResolvedValue({
      items: [],
      next_cursor: null,
      page_size: 10,
    });
    render(wrap(<OverviewPage />));
    expect(screen.getByText("Active sessions")).toBeInTheDocument();
    expect(screen.getByText("HITL pending")).toBeInTheDocument();
    expect(screen.getByText("Cost (MTD)")).toBeInTheDocument();
    expect(screen.getByText("SLA p95")).toBeInTheDocument();
  });

  it("renders empty state when no active loops returned", async () => {
    vi.spyOn(loopsService, "fetchLoops").mockResolvedValue({
      items: [],
      next_cursor: null,
      page_size: 10,
    });
    render(wrap(<OverviewPage />));
    await waitFor(() => {
      expect(screen.getByText("No running loops right now.")).toBeInTheDocument();
    });
  });

  it("renders error banner when fetchLoops rejects", async () => {
    vi.spyOn(loopsService, "fetchLoops").mockRejectedValue(new Error("boom"));
    render(wrap(<OverviewPage />));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("boom");
    });
  });

  it("renders happy-path loop rows with status badge + session id + tokens", async () => {
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
    render(wrap(<OverviewPage />));
    await waitFor(() => {
      // ActiveLoopsCard (Sprint 57.27) renders session as the 8-char prefix
      // (no ellipsis) inside the 5-col loop row.
      expect(screen.getByText("11111111", { exact: false })).toBeInTheDocument();
    });
    expect(screen.getByText("running")).toBeInTheDocument();
    expect(screen.getByText(/18,420 tok/)).toBeInTheDocument();
  });

  it("renders all 4 quick-action buttons", () => {
    vi.spyOn(loopsService, "fetchLoops").mockResolvedValue({
      items: [],
      next_cursor: null,
      page_size: 10,
    });
    render(wrap(<OverviewPage />));
    expect(screen.getByText("New chat session")).toBeInTheDocument();
    expect(screen.getByText("Review approvals")).toBeInTheDocument();
    expect(screen.getByText("Tenants console")).toBeInTheDocument();
    expect(screen.getByText("Verification log")).toBeInTheDocument();
  });
});
