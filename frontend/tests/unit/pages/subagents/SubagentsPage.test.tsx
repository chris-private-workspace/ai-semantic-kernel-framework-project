/**
 * File: frontend/tests/unit/pages/subagents/SubagentsPage.test.tsx
 * Purpose: Vitest coverage for SubagentsPage (US-C3) — KPI / list / row select + tab switch / carryover banner.
 * Category: Frontend / Tests / pages / subagents
 * Scope: Phase 57 / Sprint 57.19 Day 4 / US-C3
 *
 * Created: 2026-05-17 (Sprint 57.19 Day 4 / US-C3)
 *
 * Modification History (newest-first):
 *   - 2026-05-17: Initial creation (Sprint 57.19 Day 4 / US-C3)
 */

import "@testing-library/jest-dom/vitest";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as subagentsService from "@/features/subagents/services/subagentsService";

vi.mock("@/components/AppShellV2", () => ({
  AppShellV2: ({ children, pageTitle }: { children: ReactNode; pageTitle: string }) => (
    <div data-testid="app-shell" data-page-title={pageTitle}>
      {children}
    </div>
  ),
}));

vi.mock("@/features/auth/components/RequireAuth", () => ({
  RequireAuth: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

import { SubagentsPage } from "@/pages/subagents/SubagentsPage";

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

describe("SubagentsPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders AppShellV2 pageTitle", () => {
    vi.spyOn(subagentsService, "fetchSubagents").mockResolvedValue({
      items: [],
      next_cursor: null,
      page_size: 50,
      not_implemented_reason: null,
    });
    render(wrap(<SubagentsPage />));
    expect(screen.getByTestId("app-shell")).toHaveAttribute("data-page-title", "Subagents");
  });

  it("renders all 4 mode KPI cards", () => {
    vi.spyOn(subagentsService, "fetchSubagents").mockResolvedValue({
      items: [],
      next_cursor: null,
      page_size: 50,
      not_implemented_reason: null,
    });
    render(wrap(<SubagentsPage />));
    for (const mode of ["fork", "as_tool", "teammate", "handoff"]) {
      expect(screen.getByText(mode, { selector: "div" })).toBeInTheDocument();
    }
  });

  it("renders 8 fixture rows in the registry table", () => {
    vi.spyOn(subagentsService, "fetchSubagents").mockResolvedValue({
      items: [],
      next_cursor: null,
      page_size: 50,
      not_implemented_reason: null,
    });
    render(wrap(<SubagentsPage />));
    expect(screen.getByText("log-scanner")).toBeInTheDocument();
    expect(screen.getByText("summarizer")).toBeInTheDocument();
  });

  it("renders carryover banner when backend returns not_implemented_reason", async () => {
    vi.spyOn(subagentsService, "fetchSubagents").mockResolvedValue({
      items: [],
      next_cursor: null,
      page_size: 50,
      not_implemented_reason: "Subagent invocations are not yet persisted.",
    });
    render(wrap(<SubagentsPage />));
    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(/not yet persisted/i);
    });
  });

  it("defaults to compliance-auditor in detail card", () => {
    vi.spyOn(subagentsService, "fetchSubagents").mockResolvedValue({
      items: [],
      next_cursor: null,
      page_size: 50,
      not_implemented_reason: null,
    });
    render(wrap(<SubagentsPage />));
    // role in detail card header (mono font, semibold) — multiple matches expected (also in table); use getAllByText
    const roleEls = screen.getAllByText("compliance-auditor");
    expect(roleEls.length).toBeGreaterThanOrEqual(2);
  });

  it("clicking a row updates selected detail card", async () => {
    const user = userEvent.setup();
    vi.spyOn(subagentsService, "fetchSubagents").mockResolvedValue({
      items: [],
      next_cursor: null,
      page_size: 50,
      not_implemented_reason: null,
    });
    render(wrap(<SubagentsPage />));
    // click "log-scanner" row in list → detail header text content updates
    await user.click(screen.getByText("log-scanner"));
    // now both occurrences exist (table + detail header)
    const logEls = screen.getAllByText("log-scanner");
    expect(logEls.length).toBeGreaterThanOrEqual(2);
  });

  it("switches to budget tab and reveals max-tokens / worktree absent note", async () => {
    const user = userEvent.setup();
    vi.spyOn(subagentsService, "fetchSubagents").mockResolvedValue({
      items: [],
      next_cursor: null,
      page_size: 50,
      not_implemented_reason: null,
    });
    render(wrap(<SubagentsPage />));
    await user.click(screen.getByRole("tab", { name: /Budget/i }));
    expect(screen.getByText("Max tokens")).toBeInTheDocument();
    expect(screen.getByText(/Worktree mode is intentionally/i)).toBeInTheDocument();
  });
});
