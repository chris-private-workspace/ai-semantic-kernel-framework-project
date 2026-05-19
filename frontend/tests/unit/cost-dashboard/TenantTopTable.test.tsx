/**
 * File: frontend/tests/unit/cost-dashboard/TenantTopTable.test.tsx
 * Purpose: Vitest spec for <TenantTopTable> (Sprint 57.24 Day 2 US-C2).
 * Category: Frontend / tests / unit / cost-dashboard
 * Scope: Phase 57 / Sprint 57.24 Day 2 US-C2
 *
 * Modification History:
 *   - 2026-05-19: Initial creation (Sprint 57.24 Day 2 US-C2)
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TenantTopTable } from "@/features/cost-dashboard/components/TenantTopTable";

describe("<TenantTopTable>", () => {
  it("renders all 8 fixture tenant rows", () => {
    render(<TenantTopTable />);
    expect(screen.getAllByTestId("tenant-row")).toHaveLength(8);
  });

  it("renders title + subtitle from i18n", () => {
    render(<TenantTopTable />);
    expect(screen.getByText("Spend by tenant")).toBeInTheDocument();
    expect(screen.getByText(/MTD/)).toBeInTheDocument();
  });

  it("renders anomaly Badge only on rows with alert=true", () => {
    render(<TenantTopTable />);
    // Fixture has exactly 1 row with alert=true (tenant_3kp9)
    const badges = screen.getAllByTestId("tenant-anomaly-badge");
    expect(badges).toHaveLength(1);
  });

  it("colors quota % with danger tone when pct > 100 (over-quota)", () => {
    render(<TenantTopTable />);
    // tenant_3kp9 has pct=320 → text-danger
    const pcts = screen.getAllByTestId("tenant-quota-pct");
    const overQuota = pcts.find((el) => el.textContent === "320%");
    expect(overQuota).toBeDefined();
    expect(overQuota?.className).toContain("text-danger");
  });

  it("colors quota % with warning tone when 80 < pct <= 100 (near-limit)", () => {
    render(<TenantTopTable />);
    // wonka-apac has pct=92 → text-warning
    const pcts = screen.getAllByTestId("tenant-quota-pct");
    const nearLimit = pcts.find((el) => el.textContent === "92%");
    expect(nearLimit).toBeDefined();
    expect(nearLimit?.className).toContain("text-warning");
  });

  it("renders BackendGapBanner declaring cross-tenant API gap (AP-2 honesty)", () => {
    render(<TenantTopTable />);
    const banner = screen.getByTestId("backend-gap-banner");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent(/cross-tenant/i);
  });
});
