/**
 * File: frontend/tests/unit/pages/auth/register.test.tsx
 * Purpose: Unit test — RegisterPage 4-step wizard stepper logic + AP-2 demo banner + 501 stub error.
 * Category: Frontend / tests / unit / pages / auth
 * Scope: Phase 57 / Sprint 57.23 US-C2 (NEW 4-step wizard)
 *
 * Description:
 *   5 tests covering Sprint 57.23 US-C2 RegisterPage:
 *   1. Initial render at step 0 (Identity) + demo banner (AP-2 compliance)
 *   2. Continue button advances step 0 → 1 (Organization)
 *   3. Back button retreats step 1 → 0
 *   4. Step 3 (Confirm) submit calls POST /api/v1/tenants/register
 *   5. 501 backend stub surfaces errorStubbed message
 *
 * Created: 2026-05-18 (Sprint 57.23 US-C2)
 *
 * Related:
 *   - frontend/src/pages/auth/register/index.tsx (page under test)
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

describe("RegisterPage", () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    fetchSpy = vi.spyOn(global, "fetch");
  });

  afterEach(() => {
    fetchSpy.mockRestore();
  });

  it("renders at step 0 (Identity) with demo banner + stepper bar", () => {
    renderRegister();
    // Header
    expect(screen.getByText("Create your workspace")).toBeInTheDocument();
    // AP-2 demo banner
    expect(
      screen.getByText(/Backend wire pending Phase 58\+ IAM Block B/i),
    ).toBeInTheDocument();
    // Step 0 fields visible
    expect(screen.getByLabelText(/Work email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Full name/i)).toBeInTheDocument();
    // Continue (not Create) button on step 0
    expect(screen.getByRole("button", { name: /Continue/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Back/i })).not.toBeInTheDocument();
  });

  it("Continue advances step 0 → 1 (Organization)", () => {
    renderRegister();
    fireEvent.click(screen.getByRole("button", { name: /Continue/i }));
    // Step 1 fields visible
    expect(screen.getByLabelText(/Company name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Tenant slug/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Region/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Team size/i)).toBeInTheDocument();
    // Back button now visible (step > 0)
    expect(screen.getByRole("button", { name: /Back/i })).toBeInTheDocument();
  });

  it("Back retreats step 1 → 0", () => {
    renderRegister();
    fireEvent.click(screen.getByRole("button", { name: /Continue/i }));
    fireEvent.click(screen.getByRole("button", { name: /Back/i }));
    // Back to step 0
    expect(screen.getByLabelText(/Work email/i)).toBeInTheDocument();
    expect(screen.queryByLabelText(/Company name/i)).not.toBeInTheDocument();
  });

  it("Advances through all 4 steps to Confirm; Create workspace button on step 3", () => {
    renderRegister();
    fireEvent.click(screen.getByRole("button", { name: /Continue/i })); // 0 → 1
    fireEvent.click(screen.getByRole("button", { name: /Continue/i })); // 1 → 2
    fireEvent.click(screen.getByRole("button", { name: /Continue/i })); // 2 → 3
    expect(screen.getByText(/Almost done/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Create workspace/i })).toBeInTheDocument();
  });

  it("Create workspace submits POST /api/v1/tenants/register and surfaces 501 stub error", async () => {
    fetchSpy.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Not Implemented" }), { status: 501 }),
    );
    renderRegister();
    // Advance to step 3
    fireEvent.click(screen.getByRole("button", { name: /Continue/i }));
    fireEvent.click(screen.getByRole("button", { name: /Continue/i }));
    fireEvent.click(screen.getByRole("button", { name: /Continue/i }));
    // Submit
    fireEvent.click(screen.getByRole("button", { name: /Create workspace/i }));

    await waitFor(() =>
      expect(screen.getByText(/Backend register endpoint is stubbed \(501\)/i)).toBeInTheDocument(),
    );
    // Verify request shape
    const url = fetchSpy.mock.calls[0]?.[0] as string;
    expect(url).toBe("/api/v1/tenants/register");
  });
});
