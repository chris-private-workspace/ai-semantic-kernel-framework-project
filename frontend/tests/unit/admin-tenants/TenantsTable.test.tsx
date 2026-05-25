/**
 * File: frontend/tests/unit/admin-tenants/TenantsTable.test.tsx
 * Purpose: Vitest coverage for TenantsTable — Card + 9-col table + Badge tone dispatch + AP-2 banner.
 * Category: Frontend / Tests / admin-tenants / unit
 * Scope: Phase 57 / Sprint 57.43 Day 2 (mockup-fidelity rebuild Vitest coverage)
 *
 * Description:
 *   - Card title "All tenants" + subtitle "48 active · 3 anomalies in last 24h"
 *   - 8 column header labels (Tenant / Plan / Region / Seats / Agents / Runs · 24h / Status / Created)
 *   - 8 tenant rows present (acme-prod / globex-eu / initech-jp / umbrella-us /
 *     wonka-apac / stark-prod / wayne-corp / tenant_3kp9)
 *   - Plan Badge tone dispatch (Enterprise=primary / Pro=info / Starter no tone)
 *   - Status Badge tone dispatch (active=success / anomaly=danger / quota-warn=warning)
 *   - Toolbar: cmdk visual stub + 2 ghost buttons (Plan: all / Sort: runs (24h))
 *   - AP-2 BackendGapBanner present
 *
 * Created: 2026-05-25 (Sprint 57.43 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-05-25: Initial creation (Sprint 57.43 Day 2) — admin-tenants mockup-fidelity rebuild Vitest coverage
 *
 * Related:
 *   - frontend/src/features/admin-tenants/components/TenantsTable.tsx
 *   - frontend/src/features/admin-tenants/_fixtures.ts (TENANTS_FIXTURE, TABLE_SUBTITLE)
 *   - sprint-57-43-plan.md §AC3
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TenantsTable } from "@/features/admin-tenants/components/TenantsTable";
import {
  TABLE_SUBTITLE,
  TENANTS_FIXTURE,
} from "@/features/admin-tenants/_fixtures";

describe("TenantsTable (Sprint 57.43)", () => {
  it("renders Card title 'All tenants' + subtitle", () => {
    render(<TenantsTable />);
    expect(screen.getByText("All tenants")).toBeInTheDocument();
    expect(screen.getByText(TABLE_SUBTITLE)).toBeInTheDocument();
    expect(TABLE_SUBTITLE).toBe("48 active · 3 anomalies in last 24h");
  });

  it("renders all 8 labeled column headers (9th col is dots placeholder)", () => {
    render(<TenantsTable />);
    expect(screen.getByText("Tenant")).toBeInTheDocument();
    expect(screen.getByText("Plan")).toBeInTheDocument();
    expect(screen.getByText("Region")).toBeInTheDocument();
    expect(screen.getByText("Seats")).toBeInTheDocument();
    expect(screen.getByText("Agents")).toBeInTheDocument();
    expect(screen.getByText("Runs · 24h")).toBeInTheDocument();
    expect(screen.getByText("Status")).toBeInTheDocument();
    expect(screen.getByText("Created")).toBeInTheDocument();
  });

  it("renders all 8 tenant rows from TENANTS_FIXTURE", () => {
    render(<TenantsTable />);
    const names = [
      "acme-prod",
      "globex-eu",
      "initech-jp",
      "umbrella-us",
      "wonka-apac",
      "stark-prod",
      "wayne-corp",
      "tenant_3kp9",
    ];
    for (const name of names) {
      const matches = screen.getAllByText(name);
      expect(matches.length).toBeGreaterThanOrEqual(1);
    }
    expect(TENANTS_FIXTURE).toHaveLength(8);
  });

  it("Plan Badge tone dispatch: Enterprise → primary, Pro → info, Starter → (no tone)", () => {
    render(<TenantsTable />);
    // Enterprise count from fixture
    const enterpriseEntries = TENANTS_FIXTURE.filter((t) => t.plan === "Enterprise");
    const enterpriseBadges = screen.getAllByText("Enterprise");
    expect(enterpriseBadges.length).toBe(enterpriseEntries.length);
    expect(enterpriseBadges[0]!.className).toMatch(/primary/);

    // Pro count from fixture
    const proEntries = TENANTS_FIXTURE.filter((t) => t.plan === "Pro");
    const proBadges = screen.getAllByText("Pro");
    expect(proBadges.length).toBe(proEntries.length);
    expect(proBadges[0]!.className).toMatch(/info/);

    // Starter count from fixture (no tone applied)
    const starterEntries = TENANTS_FIXTURE.filter((t) => t.plan === "Starter");
    const starterBadges = screen.getAllByText("Starter");
    expect(starterBadges.length).toBe(starterEntries.length);
    // Starter has no tone — Badge class is "badge   " with empty tone
    expect(starterBadges[0]!.className).not.toMatch(/(primary|info|success|warning|danger)/);
  });

  it("Status Badge tone dispatch: active → success, anomaly → danger, quota-warn → warning", () => {
    render(<TenantsTable />);
    // active (multiple rows)
    const activeBadges = screen.getAllByText("active");
    expect(activeBadges.length).toBeGreaterThanOrEqual(1);
    expect(activeBadges[0]!.className).toMatch(/success/);
    expect(activeBadges[0]!.className).toMatch(/dot/);

    // anomaly (tenant_3kp9)
    const anomalyBadges = screen.getAllByText("anomaly");
    expect(anomalyBadges.length).toBe(1);
    expect(anomalyBadges[0]!.className).toMatch(/danger/);

    // quota-warn (wonka-apac)
    const quotaBadges = screen.getAllByText("quota-warn");
    expect(quotaBadges.length).toBe(1);
    expect(quotaBadges[0]!.className).toMatch(/warning/);
  });

  it("renders Card-internal toolbar with cmdk stub + 2 ghost buttons", () => {
    render(<TenantsTable />);
    expect(screen.getByText(/Filter by name, id, region/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /plan: all/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sort: runs \(24h\)/i })).toBeInTheDocument();
  });

  it("renders AP-2 BackendGapBanner declaring schema gap", () => {
    render(<TenantsTable />);
    const banner = screen.getByTestId("backend-gap-banner");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent(/Phase 58\+/);
    expect(banner).toHaveTextContent(/TenantListItem/);
  });

  it("Runs · 24h column displays toLocaleString-formatted numbers", () => {
    render(<TenantsTable />);
    // acme-prod runs24 = 14820 → "14,820" with comma separator
    expect(screen.getByText("14,820")).toBeInTheDocument();
    // initech-jp runs24 = 18420 → "18,420"
    expect(screen.getByText("18,420")).toBeInTheDocument();
  });
});
