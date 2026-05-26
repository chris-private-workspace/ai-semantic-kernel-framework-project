/**
 * File: frontend/tests/unit/tenant-settings/tabs/FeatureFlagsTab.test.tsx
 * Purpose: Vitest coverage for FeatureFlagsTab — 8 flag rows + Switch/numeric dispatch + AP-2 banner.
 * Category: Frontend / Tests / tenant-settings / unit / tabs
 * Scope: Phase 57 / Sprint 57.44 Day 2 (mockup-fidelity rebuild Vitest coverage)
 *
 * Description:
 *   - Renders "Feature flags" Card title + subtitle "Tenant-scoped overrides"
 *   - Renders 8 flag rows (FEATURE_FLAGS keys)
 *   - Boolean rows render <Switch role="switch">; numeric rows (ctl="num") render mono <input>
 *   - 4-column table headers rendered
 *   - BackendGapBanner present
 *
 * Created: 2026-05-26 (Sprint 57.44 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-05-26: Initial creation (Sprint 57.44 Day 2) — tenant-settings mockup-fidelity rebuild Vitest coverage
 *
 * Related:
 *   - frontend/src/features/tenant-settings/components/tabs/FeatureFlagsTab.tsx
 *   - frontend/src/features/tenant-settings/_fixtures.ts (FEATURE_FLAGS = 8 entries; 2 numeric)
 *   - sprint-57-44-plan.md §AC3
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FeatureFlagsTab } from "@/features/tenant-settings/components/tabs/FeatureFlagsTab";
import { FEATURE_FLAGS } from "@/features/tenant-settings/_fixtures";

describe("FeatureFlagsTab (Sprint 57.44)", () => {
  it("renders Card title 'Feature flags' + subtitle", () => {
    render(<FeatureFlagsTab />);
    expect(screen.getByText("Feature flags")).toBeInTheDocument();
    expect(screen.getByText(/Tenant-scoped overrides/)).toBeInTheDocument();
  });

  it("renders all 4 column headers", () => {
    render(<FeatureFlagsTab />);
    expect(screen.getByText("Flag")).toBeInTheDocument();
    expect(screen.getByText("Description")).toBeInTheDocument();
    expect(screen.getByText("Default")).toBeInTheDocument();
    expect(screen.getByText("Tenant override")).toBeInTheDocument();
  });

  it("renders all 8 flag-key mono cells from FEATURE_FLAGS fixture", () => {
    render(<FeatureFlagsTab />);
    for (const f of FEATURE_FLAGS) {
      expect(screen.getByText(f.k)).toBeInTheDocument();
    }
    expect(FEATURE_FLAGS).toHaveLength(8);
  });

  it("renders <Switch role='switch'> for boolean rows + mono <input> for numeric (ctl='num') rows", () => {
    const { container } = render(<FeatureFlagsTab />);
    const switches = container.querySelectorAll("[role='switch']");
    const numericFlags = FEATURE_FLAGS.filter((f) => f.ctl === "num");
    const booleanFlags = FEATURE_FLAGS.filter((f) => f.ctl !== "num");
    expect(switches.length).toBe(booleanFlags.length);

    // Numeric flags render <input class="input mono"> in tenant override column
    // Two numeric rows: subagent.max_depth (def=5) + loop.max_iterations (def=30)
    expect(numericFlags.length).toBe(2);
    // Find numeric input values 5 + 30 via container queryByDisplayValue equivalent
    const inputs = container.querySelectorAll("input.input.mono") as NodeListOf<HTMLInputElement>;
    // 2 numeric inputs expected
    expect(inputs.length).toBeGreaterThanOrEqual(2);
    const values = Array.from(inputs).map((i) => i.defaultValue);
    expect(values).toContain("5");
    expect(values).toContain("30");
  });

  it("renders AP-2 BackendGapBanner", () => {
    render(<FeatureFlagsTab />);
    const banner = screen.getByTestId("backend-gap-banner");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent(/Phase 58\+/);
    expect(banner).toHaveTextContent(/Feature flag/);
  });
});
