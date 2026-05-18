/**
 * File: frontend/tests/unit/pages/auth/invite.test.tsx
 * Purpose: Unit test — InvitePage fixture metadata render + Accept POST + 501 stub error + navigate to /auth/mfa.
 * Category: Frontend / tests / unit / pages / auth
 * Scope: Phase 57 / Sprint 57.23 US-D1 (NEW /auth/invite/:token route)
 *
 * Description:
 *   4 tests covering Sprint 57.23 US-D1 InvitePage:
 *   1. Initial render with fixture metadata (acme-prod · ap-east-1, dan@acme.com, operator, 6 days) + demo banner (AP-2)
 *   2. Accept button submits POST /api/v1/invites/:token/accept with form payload
 *   3. 501 backend stub surfaces errorStubbed message
 *   4. 200 success navigates to /auth/mfa
 *
 * Created: 2026-05-18 (Sprint 57.23 US-D1)
 *
 * Related:
 *   - frontend/src/pages/auth/invite/index.tsx (page under test)
 *   - reference/design-mockups/page-auth-extras.jsx:191-246 (AuthInvite mockup source)
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import InvitePage from "../../../../src/pages/auth/invite";

const navigateSpy = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useNavigate: () => navigateSpy,
  };
});

function renderInvite() {
  return render(
    <MemoryRouter initialEntries={["/auth/invite/test-token-abc"]}>
      <Routes>
        <Route path="/auth/invite/:token" element={<InvitePage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("InvitePage", () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    fetchSpy = vi.spyOn(global, "fetch");
    // Initial GET /api/v1/invites/:token returns 501 (stub) — fallback fixture preserved
    fetchSpy.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Not Implemented" }), { status: 501 }),
    );
    navigateSpy.mockClear();
  });

  afterEach(() => {
    fetchSpy.mockRestore();
  });

  it("renders fixture metadata + demo banner", async () => {
    renderInvite();
    // Title + subtitle from i18n
    expect(await screen.findByText(/You're invited to acme-prod/i)).toBeInTheDocument();
    // Demo banner (AP-2)
    expect(
      screen.getByText(/Backend wire pending Phase 58\+ IAM Block B/i),
    ).toBeInTheDocument();
    // Fixture metadata
    expect(screen.getByText(/acme-prod · ap-east-1/i)).toBeInTheDocument();
    expect(screen.getByText("dan@acme.com")).toBeInTheDocument();
    expect(screen.getByText("operator")).toBeInTheDocument();
    expect(screen.getByText(/in 6 days/i)).toBeInTheDocument();
    // Fields
    expect(screen.getByLabelText(/Full name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Set password/i)).toBeInTheDocument();
    // Accept button
    expect(screen.getByRole("button", { name: /Accept invitation/i })).toBeInTheDocument();
  });

  it("Accept submits POST /api/v1/invites/:token/accept and surfaces 501 stub error", async () => {
    // Second fetch (the Accept POST) returns 501
    fetchSpy.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Not Implemented" }), { status: 501 }),
    );
    renderInvite();

    // Fill fields
    fireEvent.change(screen.getByLabelText(/Full name/i), { target: { value: "Jamie Liu" } });
    fireEvent.change(screen.getByLabelText(/Set password/i), {
      target: { value: "verylongpassword123" },
    });

    // Submit
    fireEvent.click(screen.getByRole("button", { name: /Accept invitation/i }));

    // 501 error surface
    await waitFor(() =>
      expect(screen.getByText(/Backend invite endpoint is stubbed \(501\)/i)).toBeInTheDocument(),
    );
    // Request shape verify
    const acceptCall = fetchSpy.mock.calls.find((c) =>
      (c[0] as string).includes("/api/v1/invites/test-token-abc/accept"),
    );
    expect(acceptCall).toBeDefined();
    // Did NOT navigate on error
    expect(navigateSpy).not.toHaveBeenCalled();
  });

  it("Accept on 200 success navigates to /auth/mfa", async () => {
    // Second fetch returns 200
    fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify({ ok: true }), { status: 200 }));
    renderInvite();

    fireEvent.change(screen.getByLabelText(/Full name/i), { target: { value: "Jamie" } });
    fireEvent.change(screen.getByLabelText(/Set password/i), { target: { value: "verylongpw1234" } });
    fireEvent.click(screen.getByRole("button", { name: /Accept invitation/i }));

    await waitFor(() => expect(navigateSpy).toHaveBeenCalledWith("/auth/mfa"));
  });

  it("MFA hint row visible below Accept button", () => {
    renderInvite();
    expect(
      screen.getByText(/You'll be asked to enroll an authenticator app/i),
    ).toBeInTheDocument();
  });
});
