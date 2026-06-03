/**
 * File: frontend/tests/unit/admin-tenants/TenantsStatsStrip.test.tsx
 * Purpose: Vitest coverage for prop-driven TenantsStatsStrip — 3 real fleet stats + honest-gapped Anomalies/deltas + states.
 * Category: Frontend / Tests / admin-tenants / unit
 * Scope: Phase 57 / Sprint 57.43 Day 2 → Sprint 57.74 (real-data wiring)
 *
 * Description:
 *   Sprint 57.74 rewrote TenantsStatsStrip to consume a real `fleet` prop from
 *   GET /api/v1/admin/tenants/stats. Coverage:
 *   - seeded fleet → 3 real values render (number-formatted)
 *   - Anomalies → subtle "—" gap marker (NOT a fabricated number)
 *   - no trend arrow / delta rendered for any stat (no historical source)
 *   - AP-2 BackendGapBanner naming the Anomalies/deltas gap
 *   - isLoading → subtle "···" placeholders (no real numbers)
 *   - isError → subtle error placeholders (no real numbers)
 *   Sample fleet is defined inline (no _fixtures.ts coupling — STATS_FIXTURE removed).
 *
 * Created: 2026-05-25 (Sprint 57.43 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Sprint 57.74 — rewrite for props API (real fleet + honest-gapped Anomalies/deltas + states); drop STATS_FIXTURE coupling (A-6a)
 *   - 2026-05-25: Initial creation (Sprint 57.43 Day 2) — admin-tenants mockup-fidelity rebuild Vitest coverage
 *
 * Related:
 *   - frontend/src/features/admin-tenants/components/TenantsStatsStrip.tsx
 *   - frontend/src/features/admin-tenants/types.ts (FleetStats)
 *   - sprint-57-74-plan.md §AC US-3
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TenantsStatsStrip } from "@/features/admin-tenants/components/TenantsStatsStrip";
import type { FleetStats } from "@/features/admin-tenants/types";

// Inline sample fleet (task brief: no _fixtures.ts sample).
const SAMPLE_FLEET: FleetStats = {
  active_tenants: 48,
  total_seats: 1284,
  agents_deployed: 612,
};

describe("TenantsStatsStrip (Sprint 57.74 real-data)", () => {
  it("renders all 4 KPI labels in mockup order", () => {
    render(<TenantsStatsStrip fleet={SAMPLE_FLEET} />);
    expect(screen.getByText("Active tenants")).toBeInTheDocument();
    expect(screen.getByText("Total seats")).toBeInTheDocument();
    expect(screen.getByText("Agents deployed")).toBeInTheDocument();
    expect(screen.getByText("Anomalies")).toBeInTheDocument();
  });

  it("renders the 3 real fleet values (number-formatted)", () => {
    render(<TenantsStatsStrip fleet={SAMPLE_FLEET} />);
    expect(screen.getByText("48")).toBeInTheDocument();
    // total_seats number-formatted via toLocaleString → "1,284"
    expect(screen.getByText("1,284")).toBeInTheDocument();
    expect(screen.getByText("612")).toBeInTheDocument();
  });

  it("Anomalies shows a subtle '—' gap marker (NOT a fabricated number)", () => {
    render(<TenantsStatsStrip fleet={SAMPLE_FLEET} />);
    // Anomalies is the only gap value in the strip on success → exactly one "—".
    const dashes = screen.getAllByText("—");
    expect(dashes).toHaveLength(1);
    expect(dashes[0]).toHaveStyle({ color: "var(--fg-subtle)" });
  });

  it("renders no trend arrow / delta for any stat (honest gap)", () => {
    const { container } = render(<TenantsStatsStrip fleet={SAMPLE_FLEET} />);
    // The Stat primitive renders a `.stat-delta` span only when `delta` is set;
    // every stat omits delta → zero .stat-delta nodes.
    expect(container.querySelectorAll(".stat-delta")).toHaveLength(0);
  });

  it("renders the AP-2 BackendGapBanner naming the Anomalies/deltas gap", () => {
    render(<TenantsStatsStrip fleet={SAMPLE_FLEET} />);
    const banner = screen.getByTestId("backend-gap-banner");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent(/Anomalies stat \+ per-stat trend deltas/);
  });

  it("isLoading → subtle '···' placeholders (no real numbers)", () => {
    render(<TenantsStatsStrip isLoading />);
    expect(screen.getAllByText("···")).toHaveLength(3);
    expect(screen.queryByText("48")).not.toBeInTheDocument();
  });

  it("isError → subtle error placeholders (no real numbers)", () => {
    render(<TenantsStatsStrip isError />);
    // 3 real slots show error "—" + Anomalies gap "—" = 4 dashes; no numbers.
    expect(screen.getAllByText("—")).toHaveLength(4);
    expect(screen.queryByText("48")).not.toBeInTheDocument();
  });
});
