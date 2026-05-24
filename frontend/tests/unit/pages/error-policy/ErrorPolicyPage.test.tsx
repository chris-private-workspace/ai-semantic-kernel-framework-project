/**
 * File: frontend/tests/unit/pages/error-policy/ErrorPolicyPage.test.tsx
 * Purpose: Vitest smoke coverage for ErrorPolicyPage (Sprint 57.39 Day 2 / Domain D PROP→real).
 * Category: Frontend / Tests / pages / error-policy
 * Scope: Phase 57 / Sprint 57.39 Day 2 / Domain D
 *
 * Created: 2026-05-24 (Sprint 57.39 Day 2 / Domain D)
 *
 * Modification History (newest-first):
 *   - 2026-05-24: Initial creation (Sprint 57.39 Day 2 / Domain D — verbatim port spec smoke)
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

import ErrorPolicyPage from "@/pages/error-policy";

function wrap(children: ReactNode) {
  return <MemoryRouter initialEntries={["/error-policy"]}>{children}</MemoryRouter>;
}

describe("ErrorPolicyPage", () => {
  it("renders AppShellV2 pageTitle", () => {
    render(wrap(<ErrorPolicyPage />));
    expect(screen.getByTestId("app-shell")).toHaveAttribute("data-page-title", "Error Policy");
  });

  it("renders page-head title + route-pill", () => {
    render(wrap(<ErrorPolicyPage />));
    // mocked AppShellV2 puts pageTitle on data-page-title attr (not text content);
    // so "Error Policy" only appears once (the .page-title div).
    expect(screen.getByText("Error Policy")).toBeInTheDocument();
    expect(screen.getByText("/error-policy")).toBeInTheDocument();
  });

  it("renders 4-stat strip labels", () => {
    render(wrap(<ErrorPolicyPage />));
    expect(screen.getByText(/Errors · 1h/)).toBeInTheDocument();
    expect(screen.getByText("Auto-recovered")).toBeInTheDocument();
    expect(screen.getByText("Circuits open")).toBeInTheDocument();
    expect(screen.getByText("Budget burn")).toBeInTheDocument();
  });

  it("renders all 4 ERROR_CLASSES ids", () => {
    render(wrap(<ErrorPolicyPage />));
    for (const id of ["TRANSIENT", "LLM_RECOVERABLE", "HITL_RECOVERABLE", "FATAL"]) {
      expect(screen.getByText(id)).toBeInTheDocument();
    }
  });

  it("renders all 4 retry-budget row labels", () => {
    render(wrap(<ErrorPolicyPage />));
    expect(screen.getByText("Inference retries")).toBeInTheDocument();
    expect(screen.getByText("Tool retries")).toBeInTheDocument();
    expect(screen.getByText("Subagent re-spawns")).toBeInTheDocument();
    expect(screen.getByText("HITL re-prompts")).toBeInTheDocument();
  });

  it("renders Circuit breakers table with 6 adapters", () => {
    render(wrap(<ErrorPolicyPage />));
    for (const adapter of ["azure_openai", "anthropic", "vector_db", "tool.k8s", "tool.zendesk", "tool.slack"]) {
      expect(screen.getByText(adapter)).toBeInTheDocument();
    }
  });

  it("renders AP-2 BackendGapBanner mentioning /api/v1/error-policy", () => {
    render(wrap(<ErrorPolicyPage />));
    expect(screen.getByRole("status")).toHaveTextContent(/error-policy/i);
  });

  it("renders Force-close button only for the open adapter", () => {
    render(wrap(<ErrorPolicyPage />));
    // Only tool.zendesk has state="open"; should be the only Force-close button rendered.
    const forceCloseButtons = screen.getAllByText("Force close");
    expect(forceCloseButtons).toHaveLength(1);
  });
});
