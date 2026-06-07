/**
 * File: frontend/tests/unit/pages/subagents/SubagentsPage.test.tsx
 * Purpose: Vitest coverage for SubagentsPage wired to the real agent_catalog registry.
 * Category: Frontend / Tests / pages / subagents
 * Scope: Phase 57 / Sprint 57.78 (re-point STUB → agent_catalog registry)
 *
 * Created: 2026-05-17 (Sprint 57.19 Day 4 / US-C3)
 *
 * Modification History (newest-first):
 *   - 2026-06-07: FIX-031 — assert dead action controls disclose backend gap via alert
 *   - 2026-06-04: Sprint 57.78 — rewrite for real SubagentSpec items + honest-gap usage + loading/empty (AD-Subagent-RealList)
 *   - 2026-05-24: Sprint 57.33 Day 1 US-B2 — defensive spec: page survives backend payload with `items: undefined`
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
import type { SubagentSpec, SubagentsResponse } from "@/features/subagents/types";

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

const GAPPED = ["calls_24h", "p95_latency", "success_rate", "avg_tokens", "top_orchestrator"];

const ITEMS: SubagentSpec[] = [
  {
    key: "researcher",
    name: "Researcher",
    model: "claude-sonnet-4-5",
    allowed_modes: ["handoff", "as_tool"],
    status: "live",
    system_prompt: "Investigate and gather evidence.",
    budget: { max_tokens: 8000, max_duration: 240, max_concurrent: 4, max_depth: 2 },
    tools: ["log.tail", "metrics.query"],
  },
  {
    key: "reviewer",
    name: "Reviewer",
    model: null,
    allowed_modes: ["fork", "teammate"],
    status: "staging",
    system_prompt: "Review the produced artifact.",
    budget: null,
    tools: [],
  },
];

function mockSubagents(resp: SubagentsResponse): void {
  vi.spyOn(subagentsService, "fetchSubagents").mockResolvedValue(resp);
}

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

async function renderResolved(resp: SubagentsResponse): Promise<void> {
  mockSubagents(resp);
  render(wrap(<SubagentsPage />));
  // Wait for the first real row to appear (query resolves async). The first
  // item's key shows in BOTH the table row AND the detail header (default
  // selection), so use getAllByText.
  await waitFor(() => {
    expect(screen.getAllByText(resp.items[0]?.key ?? "researcher").length).toBeGreaterThan(0);
  });
}

describe("SubagentsPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders AppShellV2 pageTitle", () => {
    mockSubagents({ items: [], gapped: GAPPED });
    render(wrap(<SubagentsPage />));
    expect(screen.getByTestId("app-shell")).toHaveAttribute("data-page-title", "Subagents");
  });

  it("renders all 4 mode KPI cards", () => {
    mockSubagents({ items: [], gapped: GAPPED });
    render(wrap(<SubagentsPage />));
    for (const mode of ["fork", "as_tool", "teammate", "handoff"]) {
      expect(screen.getByText(mode, { selector: "div" })).toBeInTheDocument();
    }
  });

  it("renders real catalog rows (role / status)", async () => {
    await renderResolved({ items: ITEMS, gapped: GAPPED });
    // researcher is the default selection → appears in row + detail header.
    expect(screen.getAllByText("researcher").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("reviewer")).toBeInTheDocument();
    expect(screen.getByText("live")).toBeInTheDocument();
    expect(screen.getByText("staging")).toBeInTheDocument();
  });

  it("renders the real model and '—' for a null model", async () => {
    await renderResolved({ items: ITEMS, gapped: GAPPED });
    // researcher has a real model — appears in its table cell + the detail
    // spec-tab <option> (default selection), so use getAllByText.
    expect(screen.getAllByText("claude-sonnet-4-5").length).toBeGreaterThanOrEqual(1);
    // reviewer's null model + both usage cells render the honest-gap "—"
    expect(screen.getAllByText("—").length).toBeGreaterThanOrEqual(1);
  });

  it("derives KPI counts from allowed_modes", async () => {
    await renderResolved({ items: ITEMS, gapped: GAPPED });
    // fork:1 (reviewer), as_tool:1 (researcher), teammate:1 (reviewer), handoff:1 (researcher)
    const statValues = screen.getAllByText("1", { selector: ".stat-value" });
    expect(statValues.length).toBe(4);
  });

  it("page-head count reflects real item count", async () => {
    await renderResolved({ items: ITEMS, gapped: GAPPED });
    expect(screen.getByText(/^· 2/)).toBeInTheDocument();
  });

  it("shows the loading row while the query is pending", () => {
    vi.spyOn(subagentsService, "fetchSubagents").mockReturnValue(
      new Promise<SubagentsResponse>(() => undefined),
    );
    render(wrap(<SubagentsPage />));
    expect(screen.getByTestId("subagent-row-loading")).toBeInTheDocument();
  });

  it("shows the empty-state row when there are no subagents", async () => {
    mockSubagents({ items: [], gapped: GAPPED });
    render(wrap(<SubagentsPage />));
    await waitFor(() => {
      expect(screen.getByTestId("subagent-row-empty")).toBeInTheDocument();
    });
  });

  it("defaults to the first item in the detail card", async () => {
    await renderResolved({ items: ITEMS, gapped: GAPPED });
    // researcher appears in both the table row and the detail card header
    const roleEls = screen.getAllByText("researcher");
    expect(roleEls.length).toBeGreaterThanOrEqual(2);
  });

  it("clicking a row updates the selected detail card", async () => {
    const user = userEvent.setup();
    await renderResolved({ items: ITEMS, gapped: GAPPED });
    await user.click(screen.getByText("reviewer"));
    const reviewerEls = screen.getAllByText("reviewer");
    expect(reviewerEls.length).toBeGreaterThanOrEqual(2);
  });

  it("switches to the budget tab and reveals the worktree-absent note", async () => {
    const user = userEvent.setup();
    await renderResolved({ items: ITEMS, gapped: GAPPED });
    await user.click(screen.getByRole("tab", { name: /Budget/i }));
    expect(screen.getByText("Max tokens")).toBeInTheDocument();
    expect(screen.getByText(/Worktree mode is intentionally/i)).toBeInTheDocument();
  });

  it("tools tab shows the empty state when the selected spec has no tools", async () => {
    const user = userEvent.setup();
    // reviewer (tools: []) is the only item so it is the default selection
    await renderResolved({ items: [ITEMS[1]], gapped: GAPPED });
    await user.click(screen.getByRole("tab", { name: /Tools/i }));
    expect(screen.getByText(/No tools attached/i)).toBeInTheDocument();
  });

  it("stats tab honest-gaps all usage metrics to '—'", async () => {
    const user = userEvent.setup();
    await renderResolved({ items: ITEMS, gapped: GAPPED });
    await user.click(screen.getByRole("tab", { name: /Stats/i }));
    // 5 usage metric rows all render the gap placeholder; no fabricated numbers
    expect(screen.getByText(/Success rate/i)).toBeInTheDocument();
    expect(screen.queryByText("99.2%")).not.toBeInTheDocument();
    expect(screen.queryByText("2,840")).not.toBeInTheDocument();
    expect(screen.getAllByText("—").length).toBeGreaterThanOrEqual(5);
  });

  // Sprint 57.33 US-B2: regression guard for AD-Overview-PreExisting-Route-Crashes —
  // the page must survive a backend payload where the `items` field is
  // missing/undefined. Prior code did `data.items.length` which crashed with
  // "Cannot read properties of undefined (reading 'length')"; the fix uses
  // `data?.items ?? []`. This spec asserts no throw + KPI cards still render.
  it("survives backend payload with items field missing (defensive guard)", async () => {
    vi.spyOn(subagentsService, "fetchSubagents").mockResolvedValue({
      gapped: GAPPED,
    } as unknown as Awaited<ReturnType<typeof subagentsService.fetchSubagents>>);
    expect(() => render(wrap(<SubagentsPage />))).not.toThrow();
    // KPI cards render from the static MODE_KPI_META even with no items.
    expect(screen.getByText("fork", { selector: "div" })).toBeInTheDocument();
    // Once resolved with no items, the empty-state row appears.
    await waitFor(() => {
      expect(screen.getByTestId("subagent-row-empty")).toBeInTheDocument();
    });
  });

  // FIX-031: the registry action controls have no backend yet. Rather than
  // silently doing nothing (AP-4 dead control), each discloses the gap via
  // window.alert on click. Assert the disclosure fires for all three.
  it("dead action controls disclose the backend gap via alert (FIX-031)", async () => {
    const user = userEvent.setup();
    const alertSpy = vi.spyOn(window, "alert").mockImplementation(() => undefined);
    await renderResolved({ items: ITEMS, gapped: GAPPED });

    await user.click(screen.getByRole("button", { name: /Sync from repo/i }));
    expect(alertSpy).toHaveBeenLastCalledWith(
      expect.stringContaining("Sync from repo: backend gap (Phase 58+)"),
    );

    await user.click(screen.getByRole("button", { name: /New subagent/i }));
    expect(alertSpy).toHaveBeenLastCalledWith(
      expect.stringContaining("New subagent: backend gap (Phase 58+)"),
    );

    // researcher is the default detail selection → its "Test invoke" is present.
    await user.click(screen.getByRole("button", { name: /Test invoke/i }));
    expect(alertSpy).toHaveBeenLastCalledWith(
      expect.stringContaining("Test invoke: backend gap (Phase 58+)"),
    );
  });
});
