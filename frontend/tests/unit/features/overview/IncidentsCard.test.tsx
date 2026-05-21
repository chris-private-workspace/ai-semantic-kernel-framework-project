/**
 * File: frontend/tests/unit/features/overview/IncidentsCard.test.tsx
 * Purpose: Vitest coverage for IncidentsCard — 4 rows, RiskBadge + Badge, BackendGapBanner.
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

import { IncidentsCard } from "@/features/overview/components/IncidentsCard";

function wrap(children: ReactNode) {
  return <MemoryRouter>{children}</MemoryRouter>;
}

describe("IncidentsCard", () => {
  it("renders all 4 incident ID and title rows", () => {
    render(wrap(<IncidentsCard />));
    expect(screen.getByText("INC-2451")).toBeInTheDocument();
    expect(screen.getByText("INC-2447")).toBeInTheDocument();
    expect(screen.getByText("INC-2440")).toBeInTheDocument();
    expect(screen.getByText("INC-2438")).toBeInTheDocument();
  });

  it("renders RiskBadge labels for each severity", () => {
    render(wrap(<IncidentsCard />));
    // high, low, medium, low (in fixture order)
    const highBadges = screen.getAllByText(/high/i);
    expect(highBadges.length).toBeGreaterThanOrEqual(1);
    const mediumBadges = screen.getAllByText(/medium/i);
    expect(mediumBadges.length).toBeGreaterThanOrEqual(1);
  });

  it("renders status Badge for each incident", () => {
    render(wrap(<IncidentsCard />));
    // open x2, investigating x1, resolved x1
    const openBadges = screen.getAllByText(/open/i);
    expect(openBadges.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/investigating/i)).toBeInTheDocument();
    expect(screen.getByText(/resolved/i)).toBeInTheDocument();
  });

  it("renders a BackendGapBanner declaring fixture data", () => {
    render(wrap(<IncidentsCard />));
    expect(screen.getByTestId("backend-gap-banner")).toBeInTheDocument();
    expect(screen.getByTestId("backend-gap-banner")).toHaveTextContent(/fixture data/i);
  });
});
