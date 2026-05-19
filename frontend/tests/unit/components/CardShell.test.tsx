/**
 * File: frontend/tests/unit/components/CardShell.test.tsx
 * Purpose: Vitest spec for <CardShell> primitive (Sprint 57.24 US-B3).
 * Category: Frontend / tests / unit / components
 * Scope: Phase 57 / Sprint 57.24 Day 1 US-B3
 *
 * Modification History:
 *   - 2026-05-19: Initial creation (Sprint 57.24 Day 1 US-B3)
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CardShell } from "@/components/ui/CardShell";
import { BackendGapBanner } from "@/components/ui/BackendGapBanner";

describe("<CardShell>", () => {
  it("renders required children body", () => {
    render(
      <CardShell>
        <div data-testid="body-child">body</div>
      </CardShell>,
    );
    expect(screen.getByTestId("body-child")).toBeInTheDocument();
  });

  it("renders header row with title + subtitle when provided", () => {
    render(
      <CardShell title="Spend over time" subtitle="Daily · 30 days">
        <div>body</div>
      </CardShell>,
    );
    expect(screen.getByText("Spend over time")).toBeInTheDocument();
    expect(screen.getByText("Daily · 30 days")).toBeInTheDocument();
  });

  it("renders actions slot in header row", () => {
    render(
      <CardShell title="t" actions={<button type="button">Detail</button>}>
        <div>body</div>
      </CardShell>,
    );
    expect(screen.getByRole("button", { name: "Detail" })).toBeInTheDocument();
  });

  it("omits header row when neither title nor actions provided", () => {
    render(
      <CardShell>
        <div data-testid="body-child">body</div>
      </CardShell>,
    );
    const shell = screen.getByTestId("card-shell");
    // Only 1 direct child (body) — no header sibling
    expect(shell.children).toHaveLength(1);
  });

  it("honours bodyClass override", () => {
    const { container } = render(
      <CardShell title="t" bodyClass="custom-body-padding">
        <div>body</div>
      </CardShell>,
    );
    const body = container.querySelector(".custom-body-padding");
    expect(body).toBeInTheDocument();
  });
});

describe("<BackendGapBanner>", () => {
  it("renders the reason text inside a role=note element", () => {
    render(<BackendGapBanner reason="Backend 30-day API pending Phase 58+" />);
    const banner = screen.getByTestId("backend-gap-banner");
    expect(banner.getAttribute("role")).toBe("note");
    expect(banner).toHaveTextContent("Backend 30-day API pending Phase 58+");
  });

  it("applies warning tone styling classes", () => {
    render(<BackendGapBanner reason="x" />);
    const banner = screen.getByTestId("backend-gap-banner");
    expect(banner.className).toContain("text-warning");
    expect(banner.className).toContain("border-warning");
  });
});
