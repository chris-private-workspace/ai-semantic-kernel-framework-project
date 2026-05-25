/**
 * File: frontend/tests/unit/admin-tenants/AdminTenantsView.test.tsx
 * Purpose: Vitest coverage for AdminTenantsView — integration data-flow across 3 subcomponents.
 * Category: Frontend / Tests / admin-tenants / unit
 * Scope: Phase 57 / Sprint 57.43 Day 2 (mockup-fidelity rebuild Vitest coverage)
 *
 * Description:
 *   - Mounts TenantsPageHeader (title "Tenants" present)
 *   - Mounts TenantsStatsStrip ("Active tenants" / "Total seats" labels present)
 *   - Mounts TenantsTable ("All tenants" Card title + sample tenant rows present)
 *   - Stateless verification (no hooks, no useState / useEffect leakage)
 *
 * Created: 2026-05-25 (Sprint 57.43 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-05-25: Initial creation (Sprint 57.43 Day 2) — admin-tenants mockup-fidelity rebuild Vitest coverage
 *
 * Related:
 *   - frontend/src/features/admin-tenants/components/AdminTenantsView.tsx
 *   - sprint-57-43-plan.md §AC3
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AdminTenantsView } from "@/features/admin-tenants/components/AdminTenantsView";

describe("AdminTenantsView (Sprint 57.43)", () => {
  it("renders TenantsPageHeader with title 'Tenants'", () => {
    render(<AdminTenantsView />);
    // Page title may collide with sidebar nav label; use getAllByText per Sprint 57.41/42 cohort lesson
    const matches = screen.getAllByText("Tenants");
    expect(matches.length).toBeGreaterThanOrEqual(1);
  });

  it("renders TenantsPageHeader sub line + route-pill", () => {
    render(<AdminTenantsView />);
    expect(
      screen.getByText(
        /Multi-tenant lifecycle · RLS-isolated · feature flags \+ quotas per tenant/i,
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("/admin/tenants")).toBeInTheDocument();
  });

  it("renders TenantsStatsStrip with all 4 KPI labels", () => {
    render(<AdminTenantsView />);
    expect(screen.getByText("Active tenants")).toBeInTheDocument();
    expect(screen.getByText("Total seats")).toBeInTheDocument();
    expect(screen.getByText("Agents deployed")).toBeInTheDocument();
    expect(screen.getByText("Anomalies")).toBeInTheDocument();
  });

  it("renders TenantsTable with Card title 'All tenants'", () => {
    render(<AdminTenantsView />);
    expect(screen.getByText("All tenants")).toBeInTheDocument();
  });

  it("renders first and last fixture tenant rows", () => {
    render(<AdminTenantsView />);
    // First fixture entry
    expect(screen.getByText("acme-prod")).toBeInTheDocument();
    // Last fixture entry (name + id same for tenant_3kp9)
    const matches = screen.getAllByText("tenant_3kp9");
    expect(matches.length).toBeGreaterThanOrEqual(1);
  });

  it("renders AP-2 BackendGapBanner declaring backend wire deferred", () => {
    render(<AdminTenantsView />);
    const banner = screen.getByTestId("backend-gap-banner");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent(/Phase 58\+/);
  });

  it("is stateless (renders deterministically across multiple mounts)", () => {
    const { unmount: u1 } = render(<AdminTenantsView />);
    expect(screen.getByText("All tenants")).toBeInTheDocument();
    u1();
    render(<AdminTenantsView />);
    // Second mount renders the same content — no captured state from first mount
    expect(screen.getByText("All tenants")).toBeInTheDocument();
    expect(screen.getByText("Active tenants")).toBeInTheDocument();
  });
});
