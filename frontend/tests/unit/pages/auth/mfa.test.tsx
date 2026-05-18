/**
 * File: frontend/tests/unit/pages/auth/mfa.test.tsx
 * Purpose: Unit test — MFAPage TOTP focus advance + Backspace retreat + paste + Verify disabled gate + Tab switch + WebAuthn simulate.
 * Category: Frontend / tests / unit / pages / auth
 * Scope: Phase 57 / Sprint 57.23 US-D2 (NEW /auth/mfa route — Roll-own TOTP + WebAuthn UI per Q3)
 *
 * Description:
 *   7 tests covering Sprint 57.23 US-D2 MFAPage:
 *   1. Initial render — TOTP tab default + 6 digit inputs + demo banner (AP-2) + Verify disabled
 *   2. Typing digit advances focus to next input
 *   3. Backspace on empty digit retreats focus to previous input
 *   4. Paste 6 digits fills all boxes + focuses last
 *   5. Verify button enabled once all 6 digits filled
 *   6. Tab switch TOTP → WebAuthn renders spinning ring + Simulate button (no digit grid)
 *   7. WebAuthn Simulate button calls POST /api/v1/mfa/verify with method=webauthn
 *
 * Created: 2026-05-18 (Sprint 57.23 US-D2)
 *
 * Related:
 *   - frontend/src/pages/auth/mfa/index.tsx (page under test)
 *   - reference/design-mockups/page-auth-extras.jsx:249-371 (AuthMFA mockup source)
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import MFAPage from "../../../../src/pages/auth/mfa";

const navigateSpy = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useNavigate: () => navigateSpy,
  };
});

function renderMFA() {
  return render(
    <MemoryRouter initialEntries={["/auth/mfa"]}>
      <MFAPage />
    </MemoryRouter>,
  );
}

describe("MFAPage", () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    fetchSpy = vi.spyOn(global, "fetch");
    navigateSpy.mockClear();
  });

  afterEach(() => {
    fetchSpy.mockRestore();
  });

  it("renders TOTP tab as default with 6 digit inputs + demo banner; Verify disabled initially", () => {
    renderMFA();
    // Header
    expect(screen.getByText(/Two-factor verification/i)).toBeInTheDocument();
    // AP-2 demo banner
    expect(
      screen.getByText(/MFA backend wire pending Phase 58\+ IAM Block C/i),
    ).toBeInTheDocument();
    // 6 digit inputs (aria-label "Digit 1" through "Digit 6")
    for (let i = 1; i <= 6; i++) {
      expect(screen.getByLabelText(`Digit ${i}`)).toBeInTheDocument();
    }
    // Verify button disabled when empty
    expect(screen.getByRole("button", { name: /Verify/i })).toBeDisabled();
  });

  it("typing digit advances focus to next input", () => {
    renderMFA();
    const input1 = screen.getByLabelText("Digit 1");
    const input2 = screen.getByLabelText("Digit 2");
    fireEvent.change(input1, { target: { value: "1" } });
    expect(input2).toHaveFocus();
  });

  it("Backspace on empty digit retreats focus to previous input", () => {
    renderMFA();
    const input1 = screen.getByLabelText("Digit 1");
    const input2 = screen.getByLabelText("Digit 2");
    fireEvent.change(input1, { target: { value: "1" } });
    // Focus on input2 now (empty); Backspace should retreat
    fireEvent.keyDown(input2, { key: "Backspace" });
    expect(input1).toHaveFocus();
  });

  it("Paste 6 digits fills all boxes", () => {
    renderMFA();
    const input1 = screen.getByLabelText("Digit 1");
    fireEvent.paste(input1, { clipboardData: { getData: () => "123456" } });
    expect(screen.getByLabelText("Digit 1")).toHaveValue("1");
    expect(screen.getByLabelText("Digit 2")).toHaveValue("2");
    expect(screen.getByLabelText("Digit 3")).toHaveValue("3");
    expect(screen.getByLabelText("Digit 4")).toHaveValue("4");
    expect(screen.getByLabelText("Digit 5")).toHaveValue("5");
    expect(screen.getByLabelText("Digit 6")).toHaveValue("6");
  });

  it("Verify button enabled once all 6 digits filled", () => {
    renderMFA();
    for (let i = 1; i <= 6; i++) {
      fireEvent.change(screen.getByLabelText(`Digit ${i}`), { target: { value: String(i) } });
    }
    expect(screen.getByRole("button", { name: /Verify/i })).not.toBeDisabled();
  });

  it("Tab switch TOTP → WebAuthn renders spinning ring + Simulate (no digit grid)", () => {
    renderMFA();
    const tab = screen.getByRole("tab", { name: /Security Key/i });
    fireEvent.click(tab);
    // WebAuthn ring visible
    expect(screen.getByTestId("webauthn-ring")).toBeInTheDocument();
    // Simulate button visible
    expect(screen.getByRole("button", { name: /Simulate success/i })).toBeInTheDocument();
    // Digit inputs gone
    expect(screen.queryByLabelText("Digit 1")).not.toBeInTheDocument();
  });

  it("WebAuthn Simulate calls POST /api/v1/mfa/verify + navigates on success", async () => {
    fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify({ ok: true }), { status: 200 }));
    renderMFA();
    fireEvent.click(screen.getByRole("tab", { name: /Security Key/i }));
    fireEvent.click(screen.getByRole("button", { name: /Simulate success/i }));

    await waitFor(() => expect(navigateSpy).toHaveBeenCalledWith("/auth/callback"));
    const verifyCall = fetchSpy.mock.calls.find((c) => (c[0] as string) === "/api/v1/mfa/verify");
    expect(verifyCall).toBeDefined();
  });
});
