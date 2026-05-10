/**
 * File: frontend/tests/unit/pages/auth/login.test.tsx
 * Purpose: Unit test — LoginPage renders the WorkOS button + (DEV) dev fake-login form; no inline styles.
 * Category: Frontend / tests / unit / pages / auth
 * Scope: Phase 57 / Sprint 57.13 US-A4 → US-B9 (AuthShell rewrite — Tailwind-only assertion)
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 2)
 * Last Modified: 2026-05-10
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.13 US-B9 — add "no inline style" assertion (page rewritten to <AuthShell>+<Card>+<Button>, Tailwind only)
 *   - 2026-05-10: Initial creation (Sprint 57.13 Day 2 US-A4)
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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

  it("renders the WorkOS login button", () => {
    renderLogin();
    expect(screen.getByRole("button", { name: /Login with WorkOS/i })).toBeInTheDocument();
  });

  it("renders a page-level <h1> and uses no inline styles (US-B9 — AuthShell + Tailwind)", () => {
    const { container } = renderLogin();
    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    expect(container.querySelectorAll("[style]")).toHaveLength(0);
  });

  it("renders the dev fake-login form in DEV builds (import.meta.env.DEV)", () => {
    renderLogin();
    expect(screen.getByText(/Dev fake-login/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Dev Login$/i })).toBeInTheDocument();
  });

  it("Dev Login: POSTs /auth/dev-login then bootstraps authStore to authenticated", async () => {
    fetchSpy
      // 1) POST /api/v1/auth/dev-login
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            user: { id: "u1", email: "dev@local", display_name: "dev" },
            tenant: { id: "t1", name: "Dev Tenant (dev)", code: "dev" },
            roles: ["user", "admin", "platform_admin"],
          }),
          { status: 200 },
        ),
      )
      // 2) GET /api/v1/auth/me (from bootstrap())
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            user: { id: "u1", email: "dev@local", display_name: "dev" },
            tenant: { id: "t1", name: "Dev Tenant (dev)", code: "dev" },
            roles: ["user", "admin", "platform_admin"],
          }),
          { status: 200 },
        ),
      );

    renderLogin();
    fireEvent.click(screen.getByRole("button", { name: /^Dev Login$/i }));

    await waitFor(() => expect(useAuthStore.getState().status).toBe("authenticated"));
    expect(useAuthStore.getState().roles).toContain("platform_admin");

    const firstUrl = fetchSpy.mock.calls[0]?.[0] as string;
    expect(firstUrl).toContain("/api/v1/auth/dev-login?");
    expect(firstUrl).toContain("tenant_code=dev");
    expect(firstUrl).toContain("email=dev%40local");
  });

  it("Dev Login: 404 surfaces a 'disabled in this environment' message", async () => {
    fetchSpy.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Not Found" }), { status: 404 }),
    );
    renderLogin();
    fireEvent.click(screen.getByRole("button", { name: /^Dev Login$/i }));
    await waitFor(() =>
      expect(screen.getByText(/disabled in this environment/i)).toBeInTheDocument(),
    );
    expect(useAuthStore.getState().status).toBe("unknown");
  });
});
