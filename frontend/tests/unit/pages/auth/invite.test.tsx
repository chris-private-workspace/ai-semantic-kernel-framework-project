/**
 * File: frontend/tests/unit/pages/auth/invite.test.tsx
 * Purpose: Unit test — InvitePage wired to the real invites backend (Sprint 57.85 US-5).
 * Category: Frontend / tests / unit / pages / auth
 * Scope: Phase 57 / Sprint 57.23 US-D1 (NEW route) → Sprint 57.85 US-5 (backend wire)
 *
 * Description:
 *   Rewritten for Sprint 57.85 US-5 (the invites backend now exists; fixture + AP-2
 *   banner removed):
 *   1. GET 200 → renders the real metadata (no fixture, no demo banner)
 *   2. Accept POST 200 → navigate to /auth/mfa
 *   3. Accept failure (410) → surfaces acceptError, no navigate
 *   4. GET 404 → invalid state, no accept form
 *   5. GET 410 → expired/used state, no accept form
 *
 * Created: 2026-05-18 (Sprint 57.23 US-D1)
 * Last Modified: 2026-06-06
 *
 * Related:
 *   - frontend/src/pages/auth/invite/index.tsx (page under test)
 *   - backend/src/api/v1/invites.py (GET /invites/{token} + POST /accept)
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

const META = {
  tenant: "Acme Corp",
  invitedBy: "dan@acme.com",
  role: "Operator",
  expiresIn: "6 days",
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

function renderInvite() {
  return render(
    <MemoryRouter initialEntries={["/auth/invite/test-token-abc"]}>
      <Routes>
        <Route path="/auth/invite/:token" element={<InvitePage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("InvitePage (wired)", () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    fetchSpy = vi.spyOn(global, "fetch");
    navigateSpy.mockClear();
  });

  afterEach(() => {
    fetchSpy.mockRestore();
  });

  it("renders real invite metadata (no fixture, no demo banner)", async () => {
    fetchSpy.mockResolvedValueOnce(jsonResponse(META));
    renderInvite();

    expect(await screen.findByText("Acme Corp")).toBeInTheDocument();
    expect(screen.getByText("dan@acme.com")).toBeInTheDocument();
    expect(screen.getByText("Operator")).toBeInTheDocument();
    expect(screen.getByText("6 days")).toBeInTheDocument();
    // the AP-2 demo banner is gone
    expect(screen.queryByText(/Backend wire pending/i)).not.toBeInTheDocument();
    // accept form present
    expect(screen.getByRole("button", { name: /Accept invitation/i })).toBeInTheDocument();
  });

  it("accept POST 200 navigates to /auth/mfa", async () => {
    fetchSpy.mockResolvedValueOnce(jsonResponse(META)); // GET metadata
    fetchSpy.mockResolvedValueOnce(jsonResponse({ ok: true, user_id: "u1" })); // accept
    renderInvite();
    await screen.findByText("Acme Corp");

    const nameInput = document.querySelector<HTMLInputElement>("#inv-name");
    const passwordInput = document.querySelector<HTMLInputElement>("#inv-password");
    if (!nameInput || !passwordInput) throw new Error("Invite form inputs not found");
    fireEvent.change(nameInput, { target: { value: "Jamie Liu" } });
    fireEvent.change(passwordInput, { target: { value: "verylongpassword123" } });
    fireEvent.click(screen.getByRole("button", { name: /Accept invitation/i }));

    await waitFor(() => expect(navigateSpy).toHaveBeenCalledWith("/auth/mfa"));
    const acceptCall = fetchSpy.mock.calls.find((c) =>
      (c[0] as string).includes("/api/v1/invites/test-token-abc/accept"),
    );
    expect(acceptCall).toBeDefined();
  });

  it("accept failure (410) surfaces an error and does not navigate", async () => {
    fetchSpy.mockResolvedValueOnce(jsonResponse(META)); // GET metadata
    fetchSpy.mockResolvedValueOnce(jsonResponse({ detail: "gone" }, 410)); // accept fails
    renderInvite();
    await screen.findByText("Acme Corp");

    const nameInput = document.querySelector<HTMLInputElement>("#inv-name");
    const passwordInput = document.querySelector<HTMLInputElement>("#inv-password");
    if (!nameInput || !passwordInput) throw new Error("Invite form inputs not found");
    fireEvent.change(nameInput, { target: { value: "Jamie" } });
    fireEvent.change(passwordInput, { target: { value: "verylongpw1234" } });
    fireEvent.click(screen.getByRole("button", { name: /Accept invitation/i }));

    await waitFor(() =>
      expect(screen.getByText(/Could not accept the invitation/i)).toBeInTheDocument(),
    );
    expect(navigateSpy).not.toHaveBeenCalled();
  });

  it("GET 404 shows the invalid state with no accept form", async () => {
    fetchSpy.mockResolvedValueOnce(jsonResponse({ detail: "not found" }, 404));
    renderInvite();

    expect(await screen.findByText(/This invite link is invalid/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Accept invitation/i })).not.toBeInTheDocument();
  });

  it("GET 410 shows the expired/used state with no accept form", async () => {
    fetchSpy.mockResolvedValueOnce(jsonResponse({ detail: "gone" }, 410));
    renderInvite();

    expect(
      await screen.findByText(/This invite has expired or already been used/i),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Accept invitation/i })).not.toBeInTheDocument();
  });
});
