/**
 * File: frontend/tests/unit/components/Topbar.test.tsx
 * Purpose: Vitest tests for the Topbar tenant pill (real authStore tenant, not a fixture).
 * Category: Frontend / tests / unit / components
 * Scope: Phase 57 / Sprint 57.123 (NEW — AD-FE-Tenant-Display-Fixture-Phase58)
 *
 * Created: 2026-06-15 (Sprint 57.123)
 */

import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, test } from "vitest";

import { Topbar } from "@/components/layout/Topbar";
import { ThemeProvider } from "@/components/ThemeProvider";
import { useAuthStore } from "@/features/auth/store/authStore";

const noop = (): void => {};

const renderTopbar = () =>
  render(
    <MemoryRouter initialEntries={["/cost-dashboard"]}>
      <ThemeProvider>
        <Topbar onOpenPalette={noop} onToggleNotifs={noop} />
      </ThemeProvider>
    </MemoryRouter>,
  );

describe("Topbar tenant pill", () => {
  afterEach(() => {
    useAuthStore.setState({ status: "unknown", user: null, tenant: null, roles: [] });
  });

  test("renders the real authStore tenant name · role (not the 'acme-prod' fixture)", () => {
    useAuthStore.setState({
      status: "authenticated",
      user: { id: "u-1", email: "dan@acme.com", display_name: "Dan" },
      tenant: { id: "t-1", name: "Globex EU", code: "globex-eu", plan: "enterprise", region: "eu-west-1" },
      roles: ["admin"],
    });
    renderTopbar();
    expect(screen.getByText(/Globex EU · admin/)).toBeInTheDocument();
    expect(screen.queryByText(/acme-prod/)).toBeNull();
  });

  test("falls back to em-dash when tenant is null (pre-bootstrap)", () => {
    useAuthStore.setState({
      status: "authenticated",
      user: { id: "u-1", email: "x@y.z", display_name: null },
      tenant: null,
      roles: ["user"],
    });
    renderTopbar();
    expect(screen.getByText(/— · user/)).toBeInTheDocument();
  });
});
