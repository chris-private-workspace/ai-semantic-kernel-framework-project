/**
 * File: frontend/tests/unit/features/overview/CostBurnChart.test.tsx
 * Purpose: Vitest coverage for CostBurnChart — SVG structure, legend row, BackendGapBanner.
 * Category: Frontend / Tests / features / overview
 * Scope: Phase 57 / Sprint 57.27 Day 2 / US-B3
 *
 * Created: 2026-05-21 (Sprint 57.27 Day 2 / US-B3)
 *
 * Modification History (newest-first):
 *   - 2026-05-21: Initial creation (Sprint 57.27 Day 2)
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { CostBurnChart } from "@/features/overview/components/CostBurnChart";

function wrap(children: ReactNode) {
  return <MemoryRouter>{children}</MemoryRouter>;
}

describe("CostBurnChart", () => {
  it("renders an SVG element", () => {
    const { container } = render(wrap(<CostBurnChart />));
    const svg = container.querySelector("svg");
    expect(svg).not.toBeNull();
  });

  it("renders the legend MTD and on-pace labels", () => {
    render(wrap(<CostBurnChart />));
    // MTD label (the span showing "$X MTD")
    expect(screen.getByText(/MTD/i)).toBeInTheDocument();
    // on-pace target label
    expect(screen.getByText(/on-pace target/i)).toBeInTheDocument();
  });

  it("renders the over-pace or under-pace trend indicator", () => {
    render(wrap(<CostBurnChart />));
    // either "over pace" or "under pace" must be present
    const overPace = screen.queryByText(/over pace/i);
    const underPace = screen.queryByText(/under pace/i);
    expect(overPace ?? underPace).not.toBeNull();
  });

  it("renders a BackendGapBanner declaring fixture data", () => {
    render(wrap(<CostBurnChart />));
    expect(screen.getByTestId("backend-gap-banner")).toBeInTheDocument();
    expect(screen.getByTestId("backend-gap-banner")).toHaveTextContent(/fixture data/i);
  });
});
