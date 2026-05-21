/**
 * File: frontend/tests/unit/features/overview/ErrorTrendChart.test.tsx
 * Purpose: Vitest coverage for ErrorTrendChart — 24 bars, legend row, BackendGapBanner.
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

import { ErrorTrendChart } from "@/features/overview/components/ErrorTrendChart";

function wrap(children: ReactNode) {
  return <MemoryRouter>{children}</MemoryRouter>;
}

describe("ErrorTrendChart", () => {
  it("renders 24 SVG rect bars", () => {
    const { container } = render(wrap(<ErrorTrendChart />));
    const rects = container.querySelectorAll("rect");
    expect(rects.length).toBe(24);
  });

  it("renders the errors · 24h label", () => {
    render(wrap(<ErrorTrendChart />));
    expect(screen.getByText(/errors · 24h/i)).toBeInTheDocument();
  });

  it("renders the peak / hour label", () => {
    render(wrap(<ErrorTrendChart />));
    expect(screen.getByText(/peak \/ hour/i)).toBeInTheDocument();
  });

  it("renders a BackendGapBanner declaring fixture data", () => {
    render(wrap(<ErrorTrendChart />));
    expect(screen.getByTestId("backend-gap-banner")).toBeInTheDocument();
    expect(screen.getByTestId("backend-gap-banner")).toHaveTextContent(/fixture data/i);
  });
});
