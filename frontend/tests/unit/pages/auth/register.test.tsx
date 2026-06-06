/**
 * File: frontend/tests/unit/pages/auth/register.test.tsx
 * Purpose: Unit test — RegisterPage 4-step wizard stepper logic + real /tenants/register wiring.
 * Category: Frontend / tests / unit / pages / auth
 * Scope: Phase 57 / Sprint 57.23 US-C2 (wizard) → Sprint 57.87 (backend un-stub)
 *
 * Description:
 *   6 tests covering RegisterPage:
 *   1. Initial render at step 0 (Identity) — NO demo banner (Sprint 57.87 backend is live)
 *   2. Continue advances step 0 → 1 (Organization)
 *   3. Back retreats step 1 → 0
 *   4. Advances through all 4 steps to Confirm; Create workspace button on step 3
 *   5. Create workspace submit 409 → slug-taken error, no redirect (Sprint 57.87)
 *   6. Create workspace submit 201 → success, no error surfaced (Sprint 57.87)
 *
 * Created: 2026-05-18 (Sprint 57.23 US-C2)
 * Last Modified: 2026-06-06
 *
 * Modification History:
 *   - 2026-06-06: Sprint 57.87 — backend un-stub: drop demo-banner + 501-stub assertions;
 *     add 409 slug-taken + 201 success tests (POST /api/v1/tenants/register is now real)
 *   - 2026-05-18: Initial creation (Sprint 57.23 US-C2)
 *
 * Related:
 *   - frontend/src/pages/auth/register/index.tsx (page under test)
 *   - backend/src/api/v1/tenants.py (POST /api/v1/tenants/register)
 *   - reference/design-mockups/page-auth-extras.jsx:31-188 (AuthRegister mockup source)
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import RegisterPage from "../../../../src/pages/auth/register";

function renderRegister() {
  return render(
    <MemoryRouter initialEntries={["/auth/register"]}>
      <RegisterPage />
    </MemoryRouter>,
  );
}

function advanceToConfirm(): void {
  fireEvent.click(screen.getByRole("button", { name: /Continue/i })); // 0 → 1
  fireEvent.click(screen.getByRole("button", { name: /Continue/i })); // 1 → 2
  fireEvent.click(screen.getByRole("button", { name: /Continue/i })); // 2 → 3
}

describe("RegisterPage", () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    fetchSpy = vi.spyOn(global, "fetch");
  });

  afterEach(() => {
    fetchSpy.mockRestore();
  });

  it("renders at step 0 (Identity) without a demo banner (backend live)", () => {
    renderRegister();
    expect(screen.getByText("Create your workspace")).toBeInTheDocument();
    // Sprint 57.87 — the AP-2 demo / 501-stub banner is gone now the endpoint is real.
    expect(screen.queryByText(/Backend wire pending/i)).not.toBeInTheDocument();
    // Step 0 fields visible — mockup `.field-label` is a div; assert by visible label text.
    expect(screen.getByText(/Work email/i)).toBeInTheDocument();
    expect(screen.getByText(/Full name/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Continue/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Back/i })).not.toBeInTheDocument();
  });

  it("Continue advances step 0 → 1 (Organization)", () => {
    renderRegister();
    fireEvent.click(screen.getByRole("button", { name: /Continue/i }));
    expect(screen.getByText(/Company name/i)).toBeInTheDocument();
    expect(screen.getByText(/Tenant slug/i)).toBeInTheDocument();
    expect(screen.getByText(/^Region$/i)).toBeInTheDocument();
    expect(screen.getByText(/Team size/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Back/i })).toBeInTheDocument();
  });

  it("Back retreats step 1 → 0", () => {
    renderRegister();
    fireEvent.click(screen.getByRole("button", { name: /Continue/i }));
    fireEvent.click(screen.getByRole("button", { name: /Back/i }));
    expect(screen.getByText(/Work email/i)).toBeInTheDocument();
    expect(screen.queryByText(/Company name/i)).not.toBeInTheDocument();
  });

  it("Advances through all 4 steps to Confirm; Create workspace button on step 3", () => {
    renderRegister();
    advanceToConfirm();
    expect(screen.getByText(/Almost done/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Create workspace/i })).toBeInTheDocument();
  });

  it("Create workspace submit 409 → slug-taken error, no redirect", async () => {
    fetchSpy.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "that workspace URL is already taken" }), {
        status: 409,
      }),
    );
    renderRegister();
    advanceToConfirm();
    fireEvent.click(screen.getByRole("button", { name: /Create workspace/i }));

    await waitFor(() =>
      expect(screen.getByText(/workspace URL is already taken/i)).toBeInTheDocument(),
    );
    const url = fetchSpy.mock.calls[0]?.[0] as string;
    expect(url).toBe("/api/v1/tenants/register");
    const body = JSON.parse((fetchSpy.mock.calls[0]?.[1] as RequestInit).body as string);
    expect(body).toHaveProperty("tenant_slug");
    expect(body).toHaveProperty("company_name");
  });

  it("Create workspace submit 201 → success, no error surfaced", async () => {
    fetchSpy.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          tenant: { id: "t1", code: "acme", display_name: "Acme", state: "active" },
          user: { id: "u1", email: "f@acme.com", display_name: "Founder" },
        }),
        { status: 201 },
      ),
    );
    renderRegister();
    advanceToConfirm();
    fireEvent.click(screen.getByRole("button", { name: /Create workspace/i }));

    await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(1));
    // success path: no slug-taken / generic error is surfaced
    expect(screen.queryByText(/workspace URL is already taken/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Could not create your workspace/i)).not.toBeInTheDocument();
  });
});
