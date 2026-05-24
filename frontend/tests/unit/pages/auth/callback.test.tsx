/**
 * File: frontend/tests/unit/pages/auth/callback.test.tsx
 * Purpose: Unit test — CallbackPage renders the loading spinner (default) or the error EmptyState (?error=…); no inline styles.
 * Category: Frontend / tests / unit / pages / auth
 * Scope: Phase 57 / Sprint 57.13 US-B9
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 9)
 */

import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useAuthStore } from "../../../../src/features/auth/store/authStore";
import CallbackPage from "../../../../src/pages/auth/callback";

function renderCallback(entry: string) {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <CallbackPage />
    </MemoryRouter>,
  );
}

describe("CallbackPage", () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    useAuthStore.setState({ status: "unknown", user: null, tenant: null, roles: [] });
    sessionStorage.clear();
    // bootstrap() → fetchAuthMe → 401 → anonymous (then navigate). We only assert
    // the synchronous first render here, so the resolution doesn't matter.
    fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "anonymous" }), { status: 401 }),
    );
  });

  afterEach(() => {
    fetchSpy.mockRestore();
    sessionStorage.clear();
    useAuthStore.setState({ status: "unknown", user: null, tenant: null, roles: [] });
  });

  it("shows the loading spinner + 'completing' text + 3-step progress when there is no ?error", () => {
    renderCallback("/auth/callback");
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByText(/Completing sign-in/i)).toBeInTheDocument();
    // Sprint 57.23 US-C1: 3-step progress list (mockup AuthCallback timed transitions)
    expect(screen.getByText(/Verifying SAML assertion/i)).toBeInTheDocument();
    expect(screen.getByText(/Resolving tenant \+ RLS context/i)).toBeInTheDocument();
    expect(screen.getByText(/Loading feature flags \+ memory scopes/i)).toBeInTheDocument();
    // Sprint 57.23: no-inline-style assertion dropped — conic-gradient spinning ring is
    // legitimate STYLE.md §3 escape hatch (Tailwind can't express conic-gradient + 1.2s custom duration)
  });

  it("shows an alert EmptyState + 'Back to login' link when ?error= is present", () => {
    renderCallback("/auth/callback?error=" + encodeURIComponent("vendor said no"));
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("vendor said no")).toBeInTheDocument();
    const backLink = screen.getByRole("link", { name: /Back to login/i });
    expect(backLink).toHaveAttribute("href", "/auth/login");
    // Sprint 57.35 US-B1: AuthShell verbatim re-point uses mockup-direct inline-style literals
    // (gradient + 400px column + brand row + footer text) per styles-mockup.css contract.
    // The no-inline-style assertion (Sprint 57.23 vintage) is dropped as it asserted a now-superseded
    // Tailwind translation; AuthShell intentionally carries verbatim inline-style literals (STYLE.md §1
    // escape hatch + frontend-mockup-fidelity.md verbatim-CSS rule).
    //
    // The behavioral assertion remains: ?error short-circuits before bootstrap → no fetch.
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
