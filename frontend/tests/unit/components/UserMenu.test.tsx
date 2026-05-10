/**
 * File: frontend/tests/unit/components/UserMenu.test.tsx
 * Purpose: Vitest tests for UserMenu (auth-aware avatar dropdown — Radix DropdownMenu).
 * Category: Frontend / tests / unit / components
 * Scope: Phase 57 / Sprint 57.8 US-2 → Sprint 57.13 US-A1 (authStore) → Sprint 57.13 US-B3 (Radix)
 *
 * Created: 2026-05-10 (Sprint 57.8 Day 2)
 * Last Modified: 2026-05-10
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.13 US-B3 — Radix DropdownMenu (userEvent instead of fireEvent; role badge assertion)
 *   - 2026-05-10: Sprint 57.13 US-A1 — drive from authStore.user instead of a localStorage JWT; sign out → logout()
 *   - 2026-05-10: Initial creation (Sprint 57.8 US-2 — UserMenu Vitest)
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import { UserMenu } from "@/components/UserMenu";
import { logout } from "@/features/auth/services/authService";
import { useAuthStore } from "@/features/auth/store/authStore";

vi.mock("@/features/auth/services/authService", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/features/auth/services/authService")>();
  return { ...actual, logout: vi.fn() };
});

function setAuthed(
  user: { id: string; email: string; display_name: string | null },
  roles: string[] = ["user"],
): void {
  useAuthStore.setState({
    status: "authenticated",
    user,
    tenant: { id: "t-1", name: "Acme", code: "ACME" },
    roles,
  });
}

function setAnonymous(): void {
  useAuthStore.setState({ status: "anonymous", user: null, tenant: null, roles: [] });
}

const renderMenu = () =>
  render(
    <MemoryRouter>
      <UserMenu />
    </MemoryRouter>,
  );

describe("UserMenu", () => {
  beforeEach(() => {
    setAnonymous();
    vi.mocked(logout).mockClear();
  });

  afterEach(() => {
    useAuthStore.setState({ status: "unknown", user: null, tenant: null, roles: [] });
  });

  test("renders nothing when not authenticated", () => {
    const { container } = renderMenu();
    expect(container.firstChild).toBeNull();
  });

  test("renders avatar with display-name initial when authed", () => {
    setAuthed({ id: "u-1", email: "alice@example.com", display_name: "Alice Smith" });
    renderMenu();
    const button = screen.getByRole("button", { name: "User menu" });
    expect(button).toHaveTextContent("A"); // first char of display name, uppercase
    expect(button).toHaveAttribute("aria-haspopup", "menu");
    expect(button).toHaveAttribute("aria-expanded", "false");
  });

  test("falls back to email initial when display_name is null", () => {
    setAuthed({ id: "u-1", email: "bob@workos.com", display_name: null });
    renderMenu();
    expect(screen.getByRole("button", { name: "User menu" })).toHaveTextContent("B");
  });

  test("clicking avatar opens menu showing user + role badge + Sign out", async () => {
    const user = userEvent.setup();
    setAuthed({ id: "u-1", email: "bob@workos.com", display_name: "Bob" }, ["user", "admin"]);
    renderMenu();
    const button = screen.getByRole("button", { name: "User menu" });
    await user.click(button);

    expect(screen.getByText("Signed in as")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
    expect(screen.getByText("bob@workos.com")).toBeInTheDocument();
    expect(screen.getByText("admin")).toBeInTheDocument(); // role badge
    expect(screen.getByRole("menuitem", { name: /Sign out/ })).toBeInTheDocument();
    expect(button).toHaveAttribute("aria-expanded", "true");
  });

  test("clicking Sign out calls logout() and closes the menu", async () => {
    const user = userEvent.setup();
    setAuthed({ id: "u-1", email: "charlie@test.com", display_name: "Charlie" });
    renderMenu();

    const button = screen.getByRole("button", { name: "User menu" });
    await user.click(button);
    await user.click(screen.getByRole("menuitem", { name: /Sign out/ }));

    expect(vi.mocked(logout)).toHaveBeenCalledTimes(1);
    expect(button).toHaveAttribute("aria-expanded", "false");
  });
});
