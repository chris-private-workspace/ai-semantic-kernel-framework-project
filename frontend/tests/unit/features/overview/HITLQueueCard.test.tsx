/**
 * File: frontend/tests/unit/features/overview/HITLQueueCard.test.tsx
 * Purpose: Vitest coverage for HITLQueueCard — 3 cards / critical tint / BackendGapBanner.
 * Category: Frontend / Tests / features / overview
 * Scope: Phase 57 / Sprint 57.27 Day 1 / US-B2
 *
 * Created: 2026-05-21 (Sprint 57.27 Day 1 / US-B2)
 *
 * Modification History (newest-first):
 *   - 2026-05-22: Sprint 57.29 US-C2 — assert verbatim critical marker (re-point dropped bg-danger/8 Tailwind)
 *   - 2026-05-21: Initial creation (Sprint 57.27 Day 1)
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { HITLQueueCard } from "@/features/overview/components/HITLQueueCard";

function wrap(children: ReactNode) {
  return <MemoryRouter>{children}</MemoryRouter>;
}

describe("HITLQueueCard", () => {
  it("renders all 3 fixture approval cards", () => {
    render(wrap(<HITLQueueCard />));
    expect(screen.getByText("salesforce_update — refund $4,820")).toBeInTheDocument();
    expect(
      screen.getByText("email_send — refund confirmation to 14 customers"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("servicenow_create_ticket — P1 incident escalation"),
    ).toBeInTheDocument();
  });

  it("marks the critical-risk approval card distinctly", () => {
    render(wrap(<HITLQueueCard />));
    const criticalCard = screen
      .getByText("servicenow_create_ticket — P1 incident escalation")
      .closest("button");
    expect(criticalCard).not.toBeNull();
    // Verbatim re-point (Sprint 57.29): the critical card carries the mockup's
    // inline oklch danger tint (background + border from var(--danger)) — a
    // visual-layer literal, not a Tailwind class. The critical RiskBadge
    // (`.sev-critical`) structurally marks the card; the pixel-level tint is
    // verified by the Day-5 Playwright fidelity sweep (jsdom does not render oklch).
    expect(criticalCard?.querySelector(".sev-critical")).not.toBeNull();
    const normalCard = screen
      .getByText("salesforce_update — refund $4,820")
      .closest("button");
    expect(normalCard?.querySelector(".sev-critical")).toBeNull();
  });

  it("renders a BackendGapBanner declaring the fixture data", () => {
    render(wrap(<HITLQueueCard />));
    expect(screen.getByTestId("backend-gap-banner")).toBeInTheDocument();
    expect(screen.getByTestId("backend-gap-banner")).toHaveTextContent(
      /fixture data/i,
    );
  });
});
