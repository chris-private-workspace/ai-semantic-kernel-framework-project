/**
 * File: frontend/tests/unit/features/overview/ProvidersCard.test.tsx
 * Purpose: Vitest coverage for ProvidersCard — 4 provider rows, traffic-dot tones, BackendGapBanner.
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

import { ProvidersCard } from "@/features/overview/components/ProvidersCard";

function wrap(children: ReactNode) {
  return <MemoryRouter>{children}</MemoryRouter>;
}

describe("ProvidersCard", () => {
  it("renders all 4 provider name rows", () => {
    render(wrap(<ProvidersCard />));
    expect(screen.getByText("claude-haiku-4-5")).toBeInTheDocument();
    expect(screen.getByText("gpt-4.1")).toBeInTheDocument();
    expect(screen.getByText("gpt-4.1-mini")).toBeInTheDocument();
    expect(screen.getByText("embedding-3-large")).toBeInTheDocument();
  });

  it("renders green, amber traffic-dot elements", () => {
    const { container } = render(wrap(<ProvidersCard />));
    const greenDot = container.querySelector("[data-testid='traffic-dot-green']");
    const amberDot = container.querySelector("[data-testid='traffic-dot-amber']");
    expect(greenDot).not.toBeNull();
    expect(amberDot).not.toBeNull();
  });

  it("renders p95 latency labels", () => {
    render(wrap(<ProvidersCard />));
    expect(screen.getByText("p95 1.8s")).toBeInTheDocument();
    expect(screen.getByText("p95 3.2s")).toBeInTheDocument();
  });

  it("renders a BackendGapBanner declaring fixture data", () => {
    render(wrap(<ProvidersCard />));
    expect(screen.getByTestId("backend-gap-banner")).toBeInTheDocument();
    expect(screen.getByTestId("backend-gap-banner")).toHaveTextContent(/fixture data/i);
  });
});
