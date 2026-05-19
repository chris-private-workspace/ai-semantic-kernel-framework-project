/**
 * File: frontend/tests/unit/components/AreaChart.test.tsx
 * Purpose: Vitest spec for <AreaChart> primitive (Sprint 57.24 US-B3).
 * Category: Frontend / tests / unit / components
 * Scope: Phase 57 / Sprint 57.24 Day 1 US-B3
 *
 * Modification History:
 *   - 2026-05-19: Initial creation (Sprint 57.24 Day 1 US-B3)
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AreaChart } from "@/components/charts/AreaChart";

describe("<AreaChart>", () => {
  it("renders an SVG with fill path + line path when given data", () => {
    render(<AreaChart data={[10, 20, 30, 40, 50]} />);
    const svg = screen.getByTestId("area-chart");
    expect(svg.tagName.toLowerCase()).toBe("svg");
    expect(screen.getByTestId("area-fill")).toBeInTheDocument();
    expect(screen.getByTestId("area-line")).toBeInTheDocument();
  });

  it("applies the tone prop as the line stroke color", () => {
    render(<AreaChart data={[1, 2, 3]} tone="hsl(var(--memory))" />);
    const line = screen.getByTestId("area-line");
    expect(line.getAttribute("stroke")).toBe("hsl(var(--memory))");
  });

  it("includes a gradient definition for area fill", () => {
    const { container } = render(<AreaChart data={[1, 2, 3]} />);
    const gradients = container.querySelectorAll("linearGradient");
    expect(gradients.length).toBeGreaterThan(0);
  });

  it("honours custom height via SVG height attribute (STYLE.md §1 — no inline style)", () => {
    render(<AreaChart data={[1, 2, 3]} height={240} />);
    const svg = screen.getByTestId("area-chart");
    expect(svg.getAttribute("height")).toBe("240");
    // viewBox should also reflect the height so the path stretches correctly
    expect(svg.getAttribute("viewBox")).toContain("240");
  });

  it("returns null when given an empty data array", () => {
    const { container } = render(<AreaChart data={[]} />);
    expect(container.firstChild).toBeNull();
  });
});
