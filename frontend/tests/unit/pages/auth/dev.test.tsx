/**
 * File: frontend/tests/unit/pages/auth/dev.test.tsx
 * Purpose: Unit test — DevLoginPage (extracted from login per Sprint 57.23 US-B3) POSTs /auth/dev-login + bootstraps authStore.
 * Category: Frontend / tests / unit / pages / auth
 * Scope: Phase 57 / Sprint 57.23 US-B3 (extracted DevLoginSection → /auth/dev)
 *
 * Description:
 *   3 tests covering Sprint 57.23 US-B3 DevLoginPage:
 *   1. Renders mockup AuthDev shape (warning card + identity/tenant/role + Continue-as button)
 *   2. Continue-as → POST /api/v1/auth/dev-login with selected identity + tenant → bootstrap authenticated
 *   3. 404 → "disabled in this environment" error surface (no state change)
 *
 * Created: 2026-05-18 (Sprint 57.23 US-B3)
 *
 * Related:
 *   - frontend/src/pages/auth/dev/index.tsx (page under test)
 *   - frontend/tests/unit/pages/auth/login.test.tsx (Sprint 57.23 sibling — DevLogin tests moved here)
 *   - reference/design-mockups/page-extras.jsx:109-152 (AuthDev mockup source)
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useAuthStore } from "../../../../src/features/auth/store/authStore";
import DevLoginPage from "../../../../src/pages/auth/dev";

function renderDev() {
  return render(
    <MemoryRouter initialEntries={["/auth/dev"]}>
      <DevLoginPage />
    </MemoryRouter>,
  );
}

describe("DevLoginPage", () => {
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

  it("renders mockup AuthDev shape (warning + identity/tenant/role + Continue-as)", () => {
    renderDev();
    // Warning card
    expect(screen.getByText(/Dev login — non-production only/i)).toBeInTheDocument();
    expect(screen.getByText(/Skips SAML \/ MFA/i)).toBeInTheDocument();
    // 3 fields — Sprint 57.35 verbatim re-point uses mockup `.field` + `.field-label` (div, not <label htmlFor>).
    // Assert by visible label text + control existence; semantically equivalent to prior getByLabelText contract.
    expect(screen.getByText(/Assume identity/i)).toBeInTheDocument();
    expect(screen.getByText(/^Tenant$/i)).toBeInTheDocument();
    expect(screen.getByText(/^Role$/i)).toBeInTheDocument();
    // The 2 selects are present
    expect(document.querySelectorAll("select").length).toBe(2);
    // Continue button shows selected identity email
    expect(screen.getByRole("button", { name: /Continue as jamie@acme.com/i })).toBeInTheDocument();
  });

  it("Continue-as: POSTs /auth/dev-login with selected tenant + email → bootstraps authStore to authenticated", async () => {
    fetchSpy
      // 1) POST /api/v1/auth/dev-login
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            user: { id: "u1", email: "jamie@acme.com", display_name: "jamie" },
            tenant: { id: "t1", name: "acme-prod", code: "acme-prod" },
            roles: ["operator"],
          }),
          { status: 200 },
        ),
      )
      // 2) GET /api/v1/auth/me (from bootstrap())
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            user: { id: "u1", email: "jamie@acme.com", display_name: "jamie" },
            tenant: { id: "t1", name: "acme-prod", code: "acme-prod" },
            roles: ["operator"],
          }),
          { status: 200 },
        ),
      );

    renderDev();
    fireEvent.click(screen.getByRole("button", { name: /Continue as jamie@acme.com/i }));

    await waitFor(() => expect(useAuthStore.getState().status).toBe("authenticated"));

    const firstUrl = fetchSpy.mock.calls[0]?.[0] as string;
    expect(firstUrl).toContain("/api/v1/auth/dev-login?");
    // Default selections: jamie@acme.com identity + acme-prod tenant
    expect(firstUrl).toContain("tenant_code=acme-prod");
    expect(firstUrl).toContain("email=jamie%40acme.com");
  });

  it("404 → 'disabled in this environment' error (no state change)", async () => {
    fetchSpy.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Not Found" }), { status: 404 }),
    );
    renderDev();
    fireEvent.click(screen.getByRole("button", { name: /Continue as jamie@acme.com/i }));
    await waitFor(() =>
      expect(screen.getByText(/disabled in this environment/i)).toBeInTheDocument(),
    );
    expect(useAuthStore.getState().status).toBe("unknown");
  });
});
