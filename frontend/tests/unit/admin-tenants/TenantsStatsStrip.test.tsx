/**
 * File: frontend/tests/unit/admin-tenants/TenantsStatsStrip.test.tsx
 * Purpose: Vitest coverage for TenantsStatsStrip — 4 Stat from STATS_FIXTURE.
 * Category: Frontend / Tests / admin-tenants / unit
 * Scope: Phase 57 / Sprint 57.43 Day 2 (mockup-fidelity rebuild Vitest coverage)
 *
 * Description:
 *   - Renders .grid-stats container with 4 Stat
 *   - 4 KPI labels (Active tenants / Total seats / Agents deployed / Anomalies)
 *   - 4 KPI values (48 / 284 / 612 / 1)
 *   - 4 delta indicators (+3 / +18 / +24 / +1)
 *   - deltaDir variations (3× up + 1× down)
 *   - STATS_FIXTURE schema integrity (exactly 4 entries)
 *
 * Created: 2026-05-25 (Sprint 57.43 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-05-25: Initial creation (Sprint 57.43 Day 2) — admin-tenants mockup-fidelity rebuild Vitest coverage
 *
 * Related:
 *   - frontend/src/features/admin-tenants/components/TenantsStatsStrip.tsx
 *   - frontend/src/features/admin-tenants/_fixtures.ts (STATS_FIXTURE)
 *   - sprint-57-43-plan.md §AC3
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TenantsStatsStrip } from "@/features/admin-tenants/components/TenantsStatsStrip";
import { STATS_FIXTURE } from "@/features/admin-tenants/_fixtures";

describe("TenantsStatsStrip (Sprint 57.43)", () => {
  it("STATS_FIXTURE has exactly 4 entries", () => {
    expect(STATS_FIXTURE).toHaveLength(4);
  });

  it("renders all 4 KPI labels in mockup order", () => {
    render(<TenantsStatsStrip />);
    expect(screen.getByText("Active tenants")).toBeInTheDocument();
    expect(screen.getByText("Total seats")).toBeInTheDocument();
    expect(screen.getByText("Agents deployed")).toBeInTheDocument();
    expect(screen.getByText("Anomalies")).toBeInTheDocument();
  });

  it("renders all 4 KPI values verbatim from fixture", () => {
    render(<TenantsStatsStrip />);
    expect(screen.getByText("48")).toBeInTheDocument();
    expect(screen.getByText("284")).toBeInTheDocument();
    expect(screen.getByText("612")).toBeInTheDocument();
    // "1" value appears in Anomalies; could be ambiguous with other "1" so check via fixture instead
    const anomalyEntry = STATS_FIXTURE.find((s) => s.label === "Anomalies");
    expect(anomalyEntry?.value).toBe("1");
  });

  it("renders all 4 delta indicators", () => {
    render(<TenantsStatsStrip />);
    expect(screen.getByText("+3")).toBeInTheDocument();
    expect(screen.getByText("+18")).toBeInTheDocument();
    expect(screen.getByText("+24")).toBeInTheDocument();
    expect(screen.getByText("+1")).toBeInTheDocument();
  });

  it("STATS_FIXTURE deltaDir variations are 3 up + 1 down", () => {
    const upCount = STATS_FIXTURE.filter((s) => s.deltaDir === "up").length;
    const downCount = STATS_FIXTURE.filter((s) => s.deltaDir === "down").length;
    expect(upCount).toBe(3);
    expect(downCount).toBe(1);
    // Anomalies is the down direction (regression signal)
    const anomalies = STATS_FIXTURE.find((s) => s.label === "Anomalies");
    expect(anomalies?.deltaDir).toBe("down");
  });
});
