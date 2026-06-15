/**
 * File: frontend/tests/unit/components/Sidebar.test.tsx
 * Purpose: Vitest tests for Sidebar nav (categorized + collapse + active highlight + inactive disabled).
 * Category: Frontend / tests / unit / components
 * Scope: Phase 57 / Sprint 57.8 US-1.2 Day 1
 *
 * Created: 2026-05-10 (Sprint 57.8 Day 1)
 * Last Modified: 2026-06-15
 *
 * Modification History:
 *   - 2026-06-15: Sprint 57.123 — tenant pill renders real authStore.tenant (not FIXTURE_TENANT)
 *   - 2026-05-16: Sprint 57.18 — 3 → 6 categories per routes.config 6-category refactor (US-C1)
 *   - 2026-05-10: Initial creation (Sprint 57.8 US-1.2 — Sidebar Vitest)
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, test } from "vitest";

import { Sidebar } from "@/components/Sidebar";
import { useAuthStore } from "@/features/auth/store/authStore";
import { useUIStore } from "@/store/uiStore";

const renderWithRoute = (initialPath = "/cost-dashboard") =>
  render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Sidebar />
    </MemoryRouter>,
  );

describe("Sidebar", () => {
  beforeEach(() => {
    useUIStore.setState({ sidebarCollapsed: false });
    localStorage.removeItem("ipa-ui-state");
  });

  afterEach(() => {
    useAuthStore.setState({ status: "unknown", user: null, tenant: null, roles: [] });
  });

  test("tenant pill renders the real authStore tenant (name + `code · Plan` meta), not a fixture", () => {
    useAuthStore.setState({
      status: "authenticated",
      user: { id: "u-1", email: "dan@acme.com", display_name: "Dan" },
      tenant: { id: "t-1", name: "Globex EU", code: "globex-eu", plan: "enterprise", region: "eu-west-1" },
      roles: ["admin"],
    });
    renderWithRoute();
    expect(screen.getByText("Globex EU")).toBeInTheDocument();
    expect(screen.getByText("globex-eu · Enterprise")).toBeInTheDocument();
    // The hardcoded FIXTURE_TENANT is gone.
    expect(screen.queryByText("acme-prod")).toBeNull();
    expect(screen.queryByText(/tenant_01h9a2/)).toBeNull();
  });

  test("renders 6 category headers (Operations / Business / Governance / Observability / Resources / Admin) when expanded", () => {
    renderWithRoute();
    expect(screen.getByText("Operations")).toBeInTheDocument();
    expect(screen.getByText("Business")).toBeInTheDocument();
    // Governance appears twice: category header + route entry (Governance page) — use getAllByText
    expect(screen.getAllByText("Governance").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("Observability")).toBeInTheDocument();
    expect(screen.getByText("Resources")).toBeInTheDocument();
    expect(screen.getByText("Admin")).toBeInTheDocument();
    // Settings category removed in Sprint 57.18 — profile + mfa moved to Admin
    expect(screen.queryByText("Settings")).toBeNull();
  });

  test("active route entry has aria-current page", () => {
    renderWithRoute("/cost-dashboard");
    const activeLink = screen.getByRole("link", { name: /Cost Dashboard/ });
    expect(activeLink).toHaveAttribute("aria-current", "page");
  });

  test("inactive entries (active: false) render as disabled span with Coming soon title", () => {
    renderWithRoute();
    // Audit Log is active=false in routes.config
    const auditLog = screen.getByText("Audit Log");
    // Should NOT be a Link (no <a> wrapper); parent should have aria-disabled
    expect(auditLog.closest("a")).toBeNull();
    expect(auditLog.closest('[aria-disabled="true"]')).not.toBeNull();
    expect(auditLog.closest('[title="Coming soon"]')).not.toBeNull();
  });

  test("collapse toggle flips sidebarCollapsed and hides labels", () => {
    renderWithRoute();
    // Default expanded: labels visible
    expect(screen.getByText("Cost Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Operations")).toBeInTheDocument();

    // Click toggle (aria-label "Collapse sidebar")
    const toggle = screen.getByRole("button", { name: "Collapse sidebar" });
    fireEvent.click(toggle);

    // After collapse: labels hidden, store state flipped
    expect(useUIStore.getState().sidebarCollapsed).toBe(true);
    expect(screen.queryByText("Operations")).toBeNull();
    expect(screen.queryByText("Cost Dashboard")).toBeNull();
  });
});
