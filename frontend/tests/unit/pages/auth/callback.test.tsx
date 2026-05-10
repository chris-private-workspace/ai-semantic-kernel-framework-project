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

  it("shows the loading spinner + 'completing' text when there is no ?error", () => {
    const { container } = renderCallback("/auth/callback");
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByText(/Completing sign-in/i)).toBeInTheDocument();
    expect(container.querySelectorAll("[style]")).toHaveLength(0);
  });

  it("shows an alert EmptyState + 'Back to login' link when ?error= is present", () => {
    const { container } = renderCallback("/auth/callback?error=" + encodeURIComponent("vendor said no"));
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("vendor said no")).toBeInTheDocument();
    const backLink = screen.getByRole("link", { name: /Back to login/i });
    expect(backLink).toHaveAttribute("href", "/auth/login");
    expect(container.querySelectorAll("[style]")).toHaveLength(0);
    // ?error short-circuits before bootstrap → no fetch.
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
