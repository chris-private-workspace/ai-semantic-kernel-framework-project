/**
 * File: frontend/tests/unit/tenant-settings/tabs/DangerZoneTab.test.tsx
 * Purpose: Vitest coverage for DangerZoneTab — 4 destructive op boxes + danger Button alerts.
 * Category: Frontend / Tests / tenant-settings / unit / tabs
 * Scope: Phase 57 / Sprint 57.44 Day 2 (mockup-fidelity rebuild Vitest coverage)
 *
 * Description:
 *   - Renders "Danger zone" Card title
 *   - Renders 4 sub-boxes (Suspend / Rotate / Tombstone / Delete)
 *   - Each sub-box has danger-tone left-border (inline style)
 *   - Each has danger Button (Suspend / Rotate / Tombstone / Delete)
 *   - Button click fires window.alert with backend gap message
 *   - NO BackendGapBanner (mockup pattern; the entire tab is AP-2 stub by design)
 *
 * Created: 2026-05-26 (Sprint 57.44 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-05-26: Initial creation (Sprint 57.44 Day 2) — tenant-settings mockup-fidelity rebuild Vitest coverage
 *
 * Related:
 *   - frontend/src/features/tenant-settings/components/tabs/DangerZoneTab.tsx
 *   - frontend/src/features/tenant-settings/_fixtures.ts (DANGER_OPS = 4 entries)
 *   - sprint-57-44-plan.md §AC3
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DangerZoneTab } from "@/features/tenant-settings/components/tabs/DangerZoneTab";
import { DANGER_OPS } from "@/features/tenant-settings/_fixtures";

describe("DangerZoneTab (Sprint 57.44)", () => {
  beforeEach(() => {
    vi.spyOn(window, "alert").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders Card title 'Danger zone'", () => {
    render(<DangerZoneTab />);
    expect(screen.getByText("Danger zone")).toBeInTheDocument();
  });

  it("renders all 4 sub-box titles (DANGER_OPS keys)", () => {
    render(<DangerZoneTab />);
    expect(DANGER_OPS).toHaveLength(4);
    for (const z of DANGER_OPS) {
      expect(screen.getByText(z.k)).toBeInTheDocument();
      expect(screen.getByText(z.v)).toBeInTheDocument();
    }
  });

  it("renders 4 danger Buttons (Suspend / Rotate / Tombstone / Delete)", () => {
    render(<DangerZoneTab />);
    expect(screen.getByRole("button", { name: /^suspend$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^rotate$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^tombstone$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^delete$/i })).toBeInTheDocument();
  });

  it("each sub-box has danger left-border style (inline border-left: 2px solid var(--danger))", () => {
    const { container } = render(<DangerZoneTab />);
    // The 4 sub-boxes are the direct children of the .col wrapper with inline border-left.
    // Filter all divs with inline borderLeft style containing --danger.
    const divs = Array.from(container.querySelectorAll("div")) as HTMLDivElement[];
    const dangerBoxes = divs.filter((d) => (d.style.borderLeft || "").includes("--danger"));
    expect(dangerBoxes.length).toBe(4);
  });

  it("clicking Delete button fires window.alert with backend gap message", async () => {
    const user = userEvent.setup();
    const alertSpy = vi.spyOn(window, "alert").mockImplementation(() => {});
    render(<DangerZoneTab />);
    await user.click(screen.getByRole("button", { name: /^delete$/i }));
    expect(alertSpy).toHaveBeenCalledTimes(1);
    expect(alertSpy.mock.calls[0]![0]).toMatch(/backend gap/i);
    expect(alertSpy.mock.calls[0]![0]).toMatch(/Phase 58\+/i);
    expect(alertSpy.mock.calls[0]![0]).toMatch(/Delete/);
  });

  it("does NOT render BackendGapBanner (entire tab is AP-2 stub by design)", () => {
    render(<DangerZoneTab />);
    expect(screen.queryByTestId("backend-gap-banner")).toBeNull();
  });
});
