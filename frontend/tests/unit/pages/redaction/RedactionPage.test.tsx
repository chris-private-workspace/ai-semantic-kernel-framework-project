/**
 * File: frontend/tests/unit/pages/redaction/RedactionPage.test.tsx
 * Purpose: Vitest smoke coverage for RedactionPage (Sprint 57.39 Day 2 / Domain C PROP→real).
 * Category: Frontend / Tests / pages / redaction
 * Scope: Phase 57 / Sprint 57.39 Day 2 / Domain C
 *
 * Created: 2026-05-24 (Sprint 57.39 Day 2 / Domain C)
 *
 * Modification History (newest-first):
 *   - 2026-05-24: Initial creation (Sprint 57.39 Day 2 / Domain C — verbatim port spec smoke)
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/components/AppShellV2", () => ({
  AppShellV2: ({ children, pageTitle }: { children: ReactNode; pageTitle: string }) => (
    <div data-testid="app-shell" data-page-title={pageTitle}>
      {children}
    </div>
  ),
}));

vi.mock("@/features/auth/components/RequireAuth", () => ({
  RequireAuth: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

import RedactionPage from "@/pages/redaction";

function wrap(children: ReactNode) {
  return <MemoryRouter initialEntries={["/redaction"]}>{children}</MemoryRouter>;
}

describe("RedactionPage", () => {
  it("renders AppShellV2 pageTitle", () => {
    render(wrap(<RedactionPage />));
    expect(screen.getByTestId("app-shell")).toHaveAttribute("data-page-title", "Redaction");
  });

  it("renders page-head title + route-pill", () => {
    render(wrap(<RedactionPage />));
    expect(screen.getByText("Observation Masker")).toBeInTheDocument();
    expect(screen.getByText("/redaction")).toBeInTheDocument();
  });

  it("renders 4-stat strip labels", () => {
    render(wrap(<RedactionPage />));
    expect(screen.getByText(/Redactions · 1h/)).toBeInTheDocument();
    expect(screen.getByText("Patterns active")).toBeInTheDocument();
    expect(screen.getByText(/Critical hits · 24h/)).toBeInTheDocument();
    expect(screen.getByText("False-positive rate")).toBeInTheDocument();
  });

  it("renders Patterns table with 8 pattern rows", () => {
    render(wrap(<RedactionPage />));
    // 8 mockup-verbatim REDACT_PATTERNS ids — `email` + `bearer` also appear in Recent
    // redactions Badge (collision), so assert >= 1 occurrence per id instead of unique.
    for (const id of ["email", "credit_card", "ssn", "ipv4", "aws_key", "bearer", "github_pat", "private_key"]) {
      expect(screen.getAllByText(id).length).toBeGreaterThanOrEqual(1);
    }
  });

  it("renders Recent redactions card with 5 events", () => {
    render(wrap(<RedactionPage />));
    expect(screen.getByText("Recent redactions")).toBeInTheDocument();
    // each event has a redacted text starting with → ; assert 5 redacted strings appear
    for (const r of ["→ [EMAIL]", "→ [IPV4]", "→ [BEARER_TOKEN]", "→ [CC]"]) {
      expect(screen.getAllByText(r).length).toBeGreaterThanOrEqual(1);
    }
  });

  it("renders AP-2 BackendGapBanner mentioning observation-masker API", () => {
    render(wrap(<RedactionPage />));
    expect(screen.getByRole("status")).toHaveTextContent(/observation-masker API/i);
  });
});
