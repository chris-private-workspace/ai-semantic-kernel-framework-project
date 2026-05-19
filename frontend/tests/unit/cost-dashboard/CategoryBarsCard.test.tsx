/**
 * File: frontend/tests/unit/cost-dashboard/CategoryBarsCard.test.tsx
 * Purpose: Vitest spec for <CategoryBarsCard> (Sprint 57.24 Day 2 US-C1).
 * Category: Frontend / tests / unit / cost-dashboard
 * Scope: Phase 57 / Sprint 57.24 Day 2 US-C1
 *
 * Modification History:
 *   - 2026-05-19: Initial creation (Sprint 57.24 Day 2 US-C1)
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CategoryBarsCard } from "@/features/cost-dashboard/components/CategoryBarsCard";

describe("<CategoryBarsCard>", () => {
  it("renders all 6 mockup categories", () => {
    render(<CategoryBarsCard />);
    const card = screen.getByTestId("category-bars-card");
    expect(card).toBeInTheDocument();
    // 6 fixture rows → 6 BarTracks
    const bars = screen.getAllByTestId("bar-track");
    expect(bars).toHaveLength(6);
  });

  it("renders title + subtitle from i18n", () => {
    render(<CategoryBarsCard />);
    expect(screen.getByText("Spend by category")).toBeInTheDocument();
    expect(screen.getByText(/Last 7 days/)).toBeInTheDocument();
  });

  it("renders a BackendGapBanner declaring category taxonomy gap (AP-2 honesty)", () => {
    render(<CategoryBarsCard />);
    expect(screen.getByTestId("backend-gap-banner")).toBeInTheDocument();
    expect(screen.getByTestId("backend-gap-banner")).toHaveTextContent(
      /taxonomy/i,
    );
  });

  it("renders dollar values formatted with toLocaleString", () => {
    render(<CategoryBarsCard />);
    // Fixture top row: $1,240 with thousands separator
    expect(screen.getByText("$1,240")).toBeInTheDocument();
  });
});
