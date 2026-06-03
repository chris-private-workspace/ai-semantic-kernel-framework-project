/**
 * File: frontend/tests/unit/admin-tenants/TenantsTable.test.tsx
 * Purpose: Vitest coverage for prop-driven TenantsTable — real rows + field map + "—" gaps + loading/error/empty states.
 * Category: Frontend / Tests / admin-tenants / unit
 * Scope: Phase 57 / Sprint 57.43 Day 2 → Sprint 57.73 (real-data wiring)
 *
 * Description:
 *   Sprint 57.73 rewrote TenantsTable to consume real TenantListItem[] via props.
 *   Coverage:
 *   - real rows render with mapped fields (display_name / code / plan / region /
 *     seats / state / created date) + literal "—" for the unbacked agents/runs24
 *   - isLoading → mockup-native skeleton rows
 *   - isError → inline error row + retry button calls onRetry
 *   - empty (items.length === 0) → empty-state row
 *   - AP-2 BackendGapBanner naming the agents/runs24/stats gap
 *   Sample tenant rows are defined inline (not in _fixtures.ts) per task brief.
 *
 * Created: 2026-05-25 (Sprint 57.43 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Sprint 57.73 — rewrite for props API (real data + states); drop TENANTS_FIXTURE coupling (A-6a)
 *   - 2026-05-25: Initial creation (Sprint 57.43 Day 2) — admin-tenants mockup-fidelity rebuild Vitest coverage
 *
 * Related:
 *   - frontend/src/features/admin-tenants/components/TenantsTable.tsx
 *   - frontend/src/features/admin-tenants/types.ts (TenantListItem)
 *   - sprint-57-73-plan.md
 */

import "@testing-library/jest-dom/vitest";

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { TenantsTable } from "@/features/admin-tenants/components/TenantsTable";
import {
  TenantPlan,
  TenantState,
  type TenantListItem,
} from "@/features/admin-tenants/types";

// Inline sample rows (task brief: no _fixtures.ts sample tenant rows).
const SAMPLE_TENANTS: TenantListItem[] = [
  {
    id: "00000000-0000-0000-0000-000000000001",
    code: "ACME",
    display_name: "Acme Corp",
    state: TenantState.ACTIVE,
    plan: TenantPlan.ENTERPRISE,
    created_at: "2026-01-15T08:30:00Z",
    updated_at: "2026-05-07T00:00:00Z",
  },
  {
    id: "00000000-0000-0000-0000-000000000002",
    code: "GLOBEX",
    display_name: "Globex EU",
    state: TenantState.SUSPENDED,
    plan: TenantPlan.STANDARD,
    created_at: "2025-09-12T12:00:00Z",
    updated_at: "2026-05-07T00:00:00Z",
  },
];

describe("TenantsTable (Sprint 57.73 real-data)", () => {
  it("renders real rows with mapped fields + '—' for unbacked agents/runs24", () => {
    render(<TenantsTable tenants={SAMPLE_TENANTS} />);

    // name ← display_name, id ← code
    expect(screen.getByText("Acme Corp")).toBeInTheDocument();
    expect(screen.getByText("ACME")).toBeInTheDocument();
    expect(screen.getByText("Globex EU")).toBeInTheDocument();
    expect(screen.getByText("GLOBEX")).toBeInTheDocument();

    // plan badge (raw enum value rendered)
    const enterpriseBadge = screen.getByText(TenantPlan.ENTERPRISE);
    expect(enterpriseBadge.className).toMatch(/primary/);
    const standardBadge = screen.getByText(TenantPlan.STANDARD);
    expect(standardBadge.className).toMatch(/info/);

    // status ← state with tone dispatch
    const activeBadge = screen.getByText(TenantState.ACTIVE);
    expect(activeBadge.className).toMatch(/success/);
    expect(activeBadge.className).toMatch(/dot/);
    const suspendedBadge = screen.getByText(TenantState.SUSPENDED);
    expect(suspendedBadge.className).toMatch(/danger/);

    // created ← created_at sliced to YYYY-MM-DD
    expect(screen.getByText("2026-01-15")).toBeInTheDocument();
    expect(screen.getByText("2025-09-12")).toBeInTheDocument();

    // agents + runs24 unbacked → literal "—" (2 rows × 2 cols = 4 dashes)
    expect(screen.getAllByText("—")).toHaveLength(4);
  });

  it("isLoading → mockup-native skeleton rows (no real rows)", () => {
    render(<TenantsTable tenants={[]} isLoading />);
    expect(screen.getAllByTestId("tenant-row-skeleton")).toHaveLength(3);
    expect(screen.queryByText("Acme Corp")).not.toBeInTheDocument();
  });

  it("isError → inline error row + retry button calls onRetry", () => {
    const onRetry = vi.fn();
    render(<TenantsTable tenants={[]} isError onRetry={onRetry} />);
    expect(screen.getByTestId("tenant-row-error")).toBeInTheDocument();
    const retryBtn = screen.getByRole("button", { name: /Retry/ });
    fireEvent.click(retryBtn);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("empty (items.length === 0) → empty-state row", () => {
    render(<TenantsTable tenants={[]} />);
    expect(screen.getByTestId("tenant-row-empty")).toBeInTheDocument();
    expect(screen.getByText(/No tenants found/)).toBeInTheDocument();
  });

  it("renders Card title + toolbar + AP-2 BackendGapBanner naming the gap", () => {
    render(<TenantsTable tenants={SAMPLE_TENANTS} />);
    expect(screen.getByText("All tenants")).toBeInTheDocument();
    expect(screen.getByText(/Filter by name, id, region/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /plan: all/i })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /sort: runs \(24h\)/i }),
    ).toBeInTheDocument();

    const banner = screen.getByTestId("backend-gap-banner");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent(/Agents \/ 24h-runs/);
  });
});
