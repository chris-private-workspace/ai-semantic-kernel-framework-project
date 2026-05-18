/**
 * File: frontend/tests/unit/pages/auth/expired.test.tsx
 * Purpose: Unit test — ExpiredPage fixture/param render + Sign-in-again navigate + Resume navigate with ?next forward.
 * Category: Frontend / tests / unit / pages / auth
 * Scope: Phase 57 / Sprint 57.23 US-D3 (NEW /auth/expired route)
 *
 * Description:
 *   3 tests covering Sprint 57.23 US-D3 ExpiredPage:
 *   1. Initial render with query params (?session_id + ?reason) honored; fixture fallback when absent
 *   2. "Sign in again" click navigates to /auth/login
 *   3. "Resume session" click navigates to /auth/callback?next=<encoded original path>
 *
 * Created: 2026-05-18 (Sprint 57.23 US-D3)
 *
 * Related:
 *   - frontend/src/pages/auth/expired/index.tsx (page under test)
 *   - reference/design-mockups/page-auth-extras.jsx:374-416 (AuthExpired mockup source)
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import ExpiredPage from "../../../../src/pages/auth/expired";

const navigateSpy = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useNavigate: () => navigateSpy,
  };
});

function renderExpired(searchString = "") {
  return render(
    <MemoryRouter initialEntries={[`/auth/expired${searchString}`]}>
      <ExpiredPage />
    </MemoryRouter>,
  );
}

describe("ExpiredPage", () => {
  beforeEach(() => {
    navigateSpy.mockClear();
  });

  afterEach(() => {
    // no-op
  });

  it("renders fixture metadata when no query params; query params honored when present", () => {
    // No params → fixture
    const { unmount } = renderExpired();
    expect(screen.getByText(/Your session expired/i)).toBeInTheDocument();
    expect(screen.getByText(/14h 02m ago/i)).toBeInTheDocument();
    expect(screen.getByText("sess_8a2f1c3")).toBeInTheDocument();
    expect(screen.getByText(/jwt_expired · 24h max/i)).toBeInTheDocument();
    unmount();

    // With params → param values displayed
    renderExpired("?session_id=sess_custom_123&reason=idle_timeout");
    expect(screen.getByText("sess_custom_123")).toBeInTheDocument();
    expect(screen.getByText(/idle_timeout/i)).toBeInTheDocument();
  });

  it("Sign in again click navigates to /auth/login", () => {
    renderExpired();
    fireEvent.click(screen.getByRole("button", { name: /Sign in again/i }));
    expect(navigateSpy).toHaveBeenCalledWith("/auth/login");
  });

  it("Resume session navigates to /auth/callback (no next) and /auth/callback?next=<encoded> (with next)", () => {
    const { unmount } = renderExpired();
    fireEvent.click(screen.getByRole("button", { name: /Resume session/i }));
    expect(navigateSpy).toHaveBeenCalledWith("/auth/callback");
    unmount();

    navigateSpy.mockClear();
    renderExpired("?next=%2Fchat-v2%2Fsession-abc");
    fireEvent.click(screen.getByRole("button", { name: /Resume session/i }));
    expect(navigateSpy).toHaveBeenCalledWith("/auth/callback?next=%2Fchat-v2%2Fsession-abc");
  });
});
