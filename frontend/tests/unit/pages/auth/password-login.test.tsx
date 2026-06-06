/**
 * File: frontend/tests/unit/pages/auth/password-login.test.tsx
 * Purpose: Unit test — PasswordLoginPage wired to POST /auth/password-login (Sprint 57.86 US-4).
 * Category: Frontend / tests / unit / pages / auth
 * Scope: Phase 57 / Sprint 57.86 US-4
 *
 * Description:
 *   1. renders the tenant-code / email / password fields
 *   2. submit 200 → authStore.bootstrap() + navigate (post-login redirect)
 *   3. submit 401 → surfaces the single generic error, does NOT navigate
 *   4. empty-field guard → submit disabled, no fetch
 *
 * Created: 2026-06-06 (Sprint 57.86 US-4)
 *
 * Related:
 *   - frontend/src/pages/auth/password-login/index.tsx (page under test)
 *   - backend/src/api/v1/auth.py (POST /auth/password-login)
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import PasswordLoginPage from "../../../../src/pages/auth/password-login";

const navigateSpy = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useNavigate: () => navigateSpy,
  };
});

const bootstrapSpy = vi.fn().mockResolvedValue(undefined);
vi.mock("@/features/auth/store/authStore", () => ({
  useAuthStore: (selector: (s: { bootstrap: () => Promise<void> }) => unknown) =>
    selector({ bootstrap: bootstrapSpy }),
}));

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/auth/password-login"]}>
      <PasswordLoginPage />
    </MemoryRouter>,
  );
}

function fillForm(): void {
  const tenant = document.querySelector<HTMLInputElement>("#pwl-tenant");
  const email = document.querySelector<HTMLInputElement>("#pwl-email");
  const password = document.querySelector<HTMLInputElement>("#pwl-password");
  if (!tenant || !email || !password) throw new Error("password-login inputs not found");
  fireEvent.change(tenant, { target: { value: "acme-prod" } });
  fireEvent.change(email, { target: { value: "ok@acme.com" } });
  fireEvent.change(password, { target: { value: "rightpw123" } });
}

describe("PasswordLoginPage", () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    fetchSpy = vi.spyOn(global, "fetch");
    navigateSpy.mockClear();
    bootstrapSpy.mockClear();
  });

  afterEach(() => {
    fetchSpy.mockRestore();
  });

  it("renders the tenant-code / email / password fields", () => {
    renderPage();
    expect(screen.getByText("Sign in with password")).toBeInTheDocument();
    expect(document.querySelector("#pwl-tenant")).toBeTruthy();
    expect(document.querySelector("#pwl-email")).toBeTruthy();
    expect(document.querySelector("#pwl-password")).toBeTruthy();
  });

  it("submit 200 bootstraps and navigates", async () => {
    fetchSpy.mockResolvedValueOnce(
      jsonResponse({ user: { id: "u1", email: "ok@acme.com" }, tenant: {}, roles: ["user"] }),
    );
    renderPage();
    fillForm();
    fireEvent.click(screen.getByRole("button", { name: /Sign in/i }));

    await waitFor(() => expect(bootstrapSpy).toHaveBeenCalled());
    await waitFor(() => expect(navigateSpy).toHaveBeenCalled());
    const call = fetchSpy.mock.calls.find((c) =>
      (c[0] as string).includes("/api/v1/auth/password-login"),
    );
    expect(call).toBeDefined();
  });

  it("submit 401 surfaces a generic error and does not navigate", async () => {
    fetchSpy.mockResolvedValueOnce(jsonResponse({ detail: "Invalid credentials" }, 401));
    renderPage();
    fillForm();
    fireEvent.click(screen.getByRole("button", { name: /Sign in/i }));

    await waitFor(() => expect(screen.getByText(/Invalid credentials/i)).toBeInTheDocument());
    expect(navigateSpy).not.toHaveBeenCalled();
  });

  it("disables submit until all fields are filled (no fetch)", () => {
    renderPage();
    const btn = screen.getByRole("button", { name: /Sign in/i });
    expect(btn).toBeDisabled();
    fireEvent.click(btn);
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
