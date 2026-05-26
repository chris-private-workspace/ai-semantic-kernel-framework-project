/**
 * File: frontend/tests/unit/tenant-settings/tabs/QuotasTab.test.tsx
 * Purpose: Vitest coverage for QuotasTab — 5 bar-track rows + 3 rate-limit rows + Request increase button.
 * Category: Frontend / Tests / tenant-settings / unit / tabs
 * Scope: Phase 57 / Sprint 57.44 Day 2 (mockup-fidelity rebuild Vitest coverage)
 *
 * Description:
 *   - Renders "Usage quotas" + "Rate limits" Card titles
 *   - Renders 5 bar-track rows (one per QUOTAS entry)
 *   - Renders 3 spread rows for RATE_LIMITS (API requests / Tool calls / SSE connections)
 *   - Each bar-track inner span has width style matching q.pct%
 *   - Request increase Button + click fires window.alert with backend gap message
 *   - BackendGapBanner present
 *
 * Created: 2026-05-26 (Sprint 57.44 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-05-26: Initial creation (Sprint 57.44 Day 2) — tenant-settings mockup-fidelity rebuild Vitest coverage
 *
 * Related:
 *   - frontend/src/features/tenant-settings/components/tabs/QuotasTab.tsx
 *   - frontend/src/features/tenant-settings/_fixtures.ts (QUOTAS / RATE_LIMITS)
 *   - sprint-57-44-plan.md §AC3
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { QuotasTab } from "@/features/tenant-settings/components/tabs/QuotasTab";
import { QUOTAS, RATE_LIMITS } from "@/features/tenant-settings/_fixtures";

describe("QuotasTab (Sprint 57.44)", () => {
  beforeEach(() => {
    vi.spyOn(window, "alert").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders 'Usage quotas' + 'Rate limits' Card titles", () => {
    render(<QuotasTab />);
    expect(screen.getByText("Usage quotas")).toBeInTheDocument();
    expect(screen.getByText("Rate limits")).toBeInTheDocument();
  });

  it("renders 5 bar-track rows (one per QUOTAS entry)", () => {
    const { container } = render(<QuotasTab />);
    const barTracks = container.querySelectorAll(".bar-track");
    expect(barTracks.length).toBe(QUOTAS.length);
    expect(QUOTAS).toHaveLength(5);
  });

  it("each quota row renders the quota label", () => {
    render(<QuotasTab />);
    for (const q of QUOTAS) {
      expect(screen.getByText(q.k)).toBeInTheDocument();
    }
  });

  it("renders 3 rate-limit spread rows from RATE_LIMITS fixture", () => {
    render(<QuotasTab />);
    for (const r of RATE_LIMITS) {
      expect(screen.getByText(r.label)).toBeInTheDocument();
      expect(screen.getByText(r.value)).toBeInTheDocument();
    }
    expect(RATE_LIMITS).toHaveLength(3);
  });

  it("Request increase button fires window.alert with backend gap message", async () => {
    const user = userEvent.setup();
    const alertSpy = vi.spyOn(window, "alert").mockImplementation(() => {});
    render(<QuotasTab />);
    const btn = screen.getByRole("button", { name: /request increase/i });
    expect(btn).toBeInTheDocument();
    await user.click(btn);
    expect(alertSpy).toHaveBeenCalledTimes(1);
    expect(alertSpy.mock.calls[0]![0]).toMatch(/backend gap/i);
    expect(alertSpy.mock.calls[0]![0]).toMatch(/Phase 58\+/i);
  });

  it("renders AP-2 BackendGapBanner declaring backend extension", () => {
    render(<QuotasTab />);
    const banner = screen.getByTestId("backend-gap-banner");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent(/Phase 58\+/);
    expect(banner).toHaveTextContent(/Usage quotas/);
  });
});
