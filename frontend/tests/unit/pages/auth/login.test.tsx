/**
 * File: frontend/tests/unit/pages/auth/login.test.tsx
 * Purpose: Unit test — LoginPage renders mockup-direct shape (3 SSO disabled + Continue button + dev link); WorkOS redirect.
 * Category: Frontend / tests / unit / pages / auth
 * Scope: Phase 57 / Sprint 57.13 US-A4 → Sprint 57.23 US-B2 (mockup-direct rewrite)
 *
 * Description:
 *   Sprint 57.23 US-B2 rewrite — DevLoginSection extracted to /auth/dev (see dev.test.tsx).
 *   This file now covers only the login page mockup-direct shape:
 *     1. Continue (primary) button rendered with WorkOS redirect on click
 *     2. 3 SSO outline buttons disabled with tooltip (AD-WorkOS-Multi-IdP-Phase58)
 *     3. Dev-login link to /auth/dev (extracted route)
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 2)
 * Last Modified: 2026-05-18
 *
 * Modification History:
 *   - 2026-05-18: Sprint 57.23 US-B2 — rewrite for mockup-direct shape; move DevLogin tests to dev.test.tsx
 *   - 2026-05-10: Sprint 57.13 US-B9 — add "no inline style" assertion
 *   - 2026-05-10: Initial creation (Sprint 57.13 Day 2 US-A4)
 */

import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useAuthStore } from "../../../../src/features/auth/store/authStore";
import LoginPage from "../../../../src/pages/auth/login";

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={["/auth/login"]}>
      <LoginPage />
    </MemoryRouter>,
  );
}

describe("LoginPage", () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    useAuthStore.setState({ status: "unknown", user: null, tenant: null, roles: [] });
    sessionStorage.clear();
    fetchSpy = vi.spyOn(global, "fetch");
  });

  afterEach(() => {
    fetchSpy.mockRestore();
    sessionStorage.clear();
    useAuthStore.setState({ status: "unknown", user: null, tenant: null, roles: [] });
  });

  it("renders Sign in heading + subtitle per mockup AuthLogin", () => {
    renderLogin();
    expect(screen.getByText("Sign in")).toBeInTheDocument();
    expect(screen.getByText(/Continue with SSO or your work email/i)).toBeInTheDocument();
  });

  it("renders 3 SSO outline buttons disabled (AD-WorkOS-Multi-IdP-Phase58 placeholders)", () => {
    renderLogin();
    const samlBtn = screen.getByRole("button", { name: /Continue with SAML SSO/i });
    const msftBtn = screen.getByRole("button", { name: /Continue with Microsoft/i });
    const googleBtn = screen.getByRole("button", { name: /Continue with Google Workspace/i });
    expect(samlBtn).toBeDisabled();
    expect(msftBtn).toBeDisabled();
    expect(googleBtn).toBeDisabled();
    expect(samlBtn).toHaveAttribute("aria-disabled", "true");
  });

  it("renders Continue primary button + dev-login link", () => {
    renderLogin();
    // Primary Continue button is the only enabled button (3 SSO buttons disabled)
    const continueBtn = screen.getByRole("button", { name: "Continue" });
    expect(continueBtn).toBeInTheDocument();
    expect(continueBtn).toBeEnabled();
    const devLink = screen.getByRole("link", { name: /Use dev-login/i });
    expect(devLink).toHaveAttribute("href", "/auth/dev");
  });

  it("does NOT render an <h1> (mockup intentional no-heading; Sprint 57.23 US-B2)", () => {
    renderLogin();
    expect(screen.queryByRole("heading", { level: 1 })).not.toBeInTheDocument();
  });
});
