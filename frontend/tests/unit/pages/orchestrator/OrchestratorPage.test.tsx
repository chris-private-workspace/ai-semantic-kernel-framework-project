/**
 * File: frontend/tests/unit/pages/orchestrator/OrchestratorPage.test.tsx
 * Purpose: Vitest coverage for OrchestratorPage (US-C2) — page chrome + 6 tabs + tab switching.
 * Category: Frontend / Tests / pages / orchestrator
 * Scope: Phase 57 / Sprint 57.19 Day 3 / US-C2
 *
 * Created: 2026-05-17 (Sprint 57.19 Day 3 / US-C2)
 *
 * Modification History (newest-first):
 *   - 2026-06-07: FIX-031 — assert dead action buttons disclose backend gap via alert
 *   - 2026-06-07: FIX-029 — assert page-level BackendGapBanner renders (AP-4 honesty)
 *   - 2026-05-17: Initial creation (Sprint 57.19 Day 3 / US-C2)
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

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

import { OrchestratorPage } from "@/pages/orchestrator/OrchestratorPage";

function wrap(children: ReactNode) {
  return <MemoryRouter>{children}</MemoryRouter>;
}

describe("OrchestratorPage", () => {
  it("renders AppShellV2 pageTitle", () => {
    render(wrap(<OrchestratorPage />));
    expect(screen.getByTestId("app-shell")).toHaveAttribute("data-page-title", "Orchestrator");
  });

  it("renders all 6 tab labels in the tablist", () => {
    render(wrap(<OrchestratorPage />));
    const tablist = screen.getByRole("tablist", { name: /Orchestrator tabs/i });
    expect(tablist).toBeInTheDocument();
    for (const label of ["Config", "System Prompt", "Tools", "Subagents", "Budgets", "Policies"]) {
      expect(screen.getByRole("tab", { name: new RegExp(label, "i") })).toBeInTheDocument();
    }
  });

  it("renders all 4 KPI cards", () => {
    render(wrap(<OrchestratorPage />));
    expect(screen.getByText("Sessions · 24h")).toBeInTheDocument();
    expect(screen.getByText("Avg loop turns")).toBeInTheDocument();
    expect(screen.getByText("Subagent spawns · 24h")).toBeInTheDocument();
    expect(screen.getByText("p95 session")).toBeInTheDocument();
  });

  it("defaults to Config tab and shows its body", () => {
    render(wrap(<OrchestratorPage />));
    expect(screen.getByText("Core settings")).toBeInTheDocument();
    const configTab = screen.getByRole("tab", { name: /^Config$/i });
    expect(configTab).toHaveAttribute("aria-selected", "true");
  });

  it("switches to Budgets tab and reveals budgets body", async () => {
    const user = userEvent.setup();
    render(wrap(<OrchestratorPage />));
    await user.click(screen.getByRole("tab", { name: /^Budgets$/i }));
    expect(screen.getByText("Loop budgets")).toBeInTheDocument();
    expect(screen.getByText("Termination conditions")).toBeInTheDocument();
  });

  it("switches to Tools tab and shows tool registry table", async () => {
    const user = userEvent.setup();
    render(wrap(<OrchestratorPage />));
    await user.click(screen.getByRole("tab", { name: /^Tools/i }));
    expect(screen.getByText("incidents.list")).toBeInTheDocument();
    expect(screen.getByText("k8s.rollback")).toBeInTheDocument();
  });

  it("renders orchestrator header chrome (name + version + live)", () => {
    render(wrap(<OrchestratorPage />));
    expect(screen.getByText("orchestrator-main")).toBeInTheDocument();
    expect(screen.getByText("v3.4.1")).toBeInTheDocument();
    expect(screen.getByText("live")).toBeInTheDocument();
  });

  it("renders the AP-4 backend-gap honesty banner (whole surface is fixture)", () => {
    // FIX-029: the lone full-impl Potemkin page now carries the same
    // BackendGapBanner every other fixture-backed page uses, so operators
    // aren't misled into thinking config / Deploy are wired.
    render(wrap(<OrchestratorPage />));
    const banner = screen.getByTestId("backend-gap-banner");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent(/non-functional/i);
  });

  // FIX-031: the header action buttons have no backend yet. Rather than silently
  // doing nothing (AP-4 dead control), each discloses the gap via window.alert.
  it("dead action buttons (Deploy / View repo) disclose the backend gap via alert (FIX-031)", async () => {
    const user = userEvent.setup();
    const alertSpy = vi.spyOn(window, "alert").mockImplementation(() => undefined);
    render(wrap(<OrchestratorPage />));

    await user.click(screen.getByRole("button", { name: /^Deploy$/i }));
    expect(alertSpy).toHaveBeenLastCalledWith(
      expect.stringContaining("Deploy: backend gap (Phase 58+)"),
    );

    await user.click(screen.getByRole("button", { name: /View in repo/i }));
    expect(alertSpy).toHaveBeenLastCalledWith(
      expect.stringContaining("View repo: backend gap (Phase 58+)"),
    );

    alertSpy.mockRestore();
  });
});
