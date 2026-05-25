/**
 * File: frontend/tests/unit/admin-tenants/TenantsPageHeader.test.tsx
 * Purpose: Vitest coverage for TenantsPageHeader — title + sub + 2 AP-2 alert stub actions.
 * Category: Frontend / Tests / admin-tenants / unit
 * Scope: Phase 57 / Sprint 57.43 Day 2 (mockup-fidelity rebuild Vitest coverage)
 *
 * Description:
 *   - Renders .page-head with title "Tenants" + sub line + route-pill /admin/tenants
 *   - Renders Export + New tenant action buttons
 *   - Export onClick fires window.alert with backend gap message
 *   - New tenant onClick fires window.alert with backend gap message
 *
 * Created: 2026-05-25 (Sprint 57.43 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-05-25: Initial creation (Sprint 57.43 Day 2) — admin-tenants mockup-fidelity rebuild Vitest coverage
 *
 * Related:
 *   - frontend/src/features/admin-tenants/components/TenantsPageHeader.tsx
 *   - sprint-57-43-plan.md §AC3
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { TenantsPageHeader } from "@/features/admin-tenants/components/TenantsPageHeader";

describe("TenantsPageHeader (Sprint 57.43)", () => {
  beforeEach(() => {
    vi.spyOn(window, "alert").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders page title 'Tenants'", () => {
    render(<TenantsPageHeader />);
    expect(screen.getByText("Tenants")).toBeInTheDocument();
  });

  it("renders page sub line + route-pill", () => {
    render(<TenantsPageHeader />);
    expect(
      screen.getByText(
        /Multi-tenant lifecycle · RLS-isolated · feature flags \+ quotas per tenant/i,
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("/admin/tenants")).toBeInTheDocument();
  });

  it("renders Export and 'New tenant' action buttons", () => {
    render(<TenantsPageHeader />);
    expect(screen.getByRole("button", { name: /^export$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /new tenant/i })).toBeInTheDocument();
  });

  it("Export click fires window.alert with backend gap message", async () => {
    const user = userEvent.setup();
    const alertSpy = vi.spyOn(window, "alert").mockImplementation(() => {});
    render(<TenantsPageHeader />);
    await user.click(screen.getByRole("button", { name: /^export$/i }));
    expect(alertSpy).toHaveBeenCalledTimes(1);
    expect(alertSpy.mock.calls[0]![0]).toMatch(/backend gap/i);
    expect(alertSpy.mock.calls[0]![0]).toMatch(/Phase 58\+/i);
  });

  it("'New tenant' click fires window.alert with backend gap message", async () => {
    const user = userEvent.setup();
    const alertSpy = vi.spyOn(window, "alert").mockImplementation(() => {});
    render(<TenantsPageHeader />);
    await user.click(screen.getByRole("button", { name: /new tenant/i }));
    expect(alertSpy).toHaveBeenCalledTimes(1);
    expect(alertSpy.mock.calls[0]![0]).toMatch(/backend gap/i);
    expect(alertSpy.mock.calls[0]![0]).toMatch(/Phase 58\+/i);
  });
});
