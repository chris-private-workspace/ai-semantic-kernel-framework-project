/**
 * File: frontend/tests/unit/components/UserMenu.test.tsx
 * Purpose: Vitest tests for UserMenu (auth-aware avatar dropdown — Radix DropdownMenu).
 * Category: Frontend / tests / unit / components
 * Scope: Phase 57 / Sprint 57.8 US-2 → Sprint 57.13 US-A1 (authStore) → Sprint 57.13 US-B3 (Radix)
 *
 * Created: 2026-05-10 (Sprint 57.8 Day 2)
 * Last Modified: 2026-06-15
 *
 * Modification History:
 *   - 2026-06-15: Sprint 57.123 — current-tenant test (single real tenant; no globex-eu/initech-jp fixtures)
 *   - 2026-05-10: Sprint 57.13 US-B5 — locale switcher test (both locales + persist + changeLanguage)
 *   - 2026-05-10: Sprint 57.13 US-B3 — Radix DropdownMenu (userEvent instead of fireEvent; role badge assertion)
 *   - 2026-05-10: Sprint 57.13 US-A1 — drive from authStore.user instead of a localStorage JWT; sign out → logout()
 *   - 2026-05-10: Initial creation (Sprint 57.8 US-2 — UserMenu Vitest)
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import { ThemeProvider } from "@/components/ThemeProvider";
import { UserMenu } from "@/components/UserMenu";
import { logout } from "@/features/auth/services/authService";
import { useAuthStore } from "@/features/auth/store/authStore";
import i18n, { LOCALE_STORAGE_KEY } from "@/i18n";

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
    tenant: { id: "t-1", name: "Acme", code: "ACME", plan: "enterprise", region: "ap-east-1" },
    roles,
  });
}

function setAnonymous(): void {
  useAuthStore.setState({ status: "anonymous", user: null, tenant: null, roles: [] });
}

const renderMenu = () =>
  render(
    <MemoryRouter>
      <ThemeProvider>
        <UserMenu />
      </ThemeProvider>
    </MemoryRouter>,
  );

describe("UserMenu", () => {
  beforeEach(() => {
    setAnonymous();
    vi.mocked(logout).mockClear();
  });

  afterEach(async () => {
    useAuthStore.setState({ status: "unknown", user: null, tenant: null, roles: [] });
    // The locale-switcher test mutates the i18n singleton + localStorage; reset both
    // so test order doesn't leak (other UserMenu tests assert English aria-labels).
    localStorage.removeItem(LOCALE_STORAGE_KEY);
    await i18n.changeLanguage("en");
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

  test("shows the single real current tenant (name + region), not the 3-tenant fixture", async () => {
    const user = userEvent.setup();
    setAuthed({ id: "u-1", email: "dan@acme.com", display_name: "Dan" }, ["admin"]);
    renderMenu();
    await user.click(screen.getByRole("button", { name: "User menu" }));

    // The "Current tenant" section (relabelled from "Switch tenant") shows the
    // real authStore tenant — name + region from /auth/me.
    expect(screen.getByText("Current tenant")).toBeInTheDocument();
    const tenantRow = screen.getByTestId("usermenu-current-tenant");
    expect(tenantRow).toHaveTextContent("Acme");
    expect(tenantRow).toHaveTextContent("ap-east-1");
    expect(tenantRow).toHaveAttribute("aria-current", "true");

    // The old 3-tenant fixtures are gone.
    expect(screen.queryByText("globex-eu")).toBeNull();
    expect(screen.queryByText("initech-jp")).toBeNull();
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

  test("locale switcher offers both locales and persists the choice", async () => {
    const user = userEvent.setup();
    setAuthed({ id: "u-1", email: "dana@test.com", display_name: "Dana" });
    renderMenu();

    await user.click(screen.getByRole("button", { name: "User menu" }));
    // Both supported locales are offered as menu items (native labels).
    expect(screen.getByRole("menuitem", { name: "English" })).toBeInTheDocument();
    const zhItem = screen.getByRole("menuitem", { name: "繁體中文" });
    expect(zhItem).toBeInTheDocument();

    await user.click(zhItem);

    expect(localStorage.getItem(LOCALE_STORAGE_KEY)).toBe("zh-TW");
    expect(i18n.resolvedLanguage).toBe("zh-TW");
  });
});
