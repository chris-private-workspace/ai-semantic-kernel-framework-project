/**
 * File: frontend/tests/unit/governance/ApprovalsStatsStrip.test.tsx
 * Purpose: Vitest coverage for ApprovalsStatsStrip — 4 KPI cards + AP-2 banner declaration.
 * Category: Frontend / Tests / governance / unit
 * Scope: Phase 57 / Sprint 57.40 Day 2 (mockup-fidelity rebuild)
 *
 * Description:
 *   - Active queue label + real count derived from approvals.length
 *   - 0 fallback when approvals is undefined
 *   - 3 fixture KPIs render labels (p50 / Approved · 24h / Rejected · 24h)
 *   - BackendGapBanner present declaring AP-2 fixture status
 *
 * Created: 2026-05-25 (Sprint 57.40 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-05-25: Initial creation (Sprint 57.40 Day 2)
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ApprovalsStatsStrip } from "@/features/governance/components/ApprovalsStatsStrip";
import type { ApprovalSummary } from "@/features/governance/types";

function makeApproval(id: string): ApprovalSummary {
  return {
    request_id: id,
    tenant_id: "22222222-2222-4222-8222-222222222222",
    session_id: "33333333-3333-4333-8333-333333333333",
    requester: "user-a",
    risk_level: "HIGH",
    payload: { tool_name: "salesforce_query" },
    sla_deadline: new Date(Date.now() + 60_000).toISOString(),
    context_snapshot: {},
  };
}

describe("ApprovalsStatsStrip (Sprint 57.40)", () => {
  it("renders 4 KPI labels in mockup order", () => {
    render(<ApprovalsStatsStrip approvals={[]} />);
    expect(screen.getByText("Active queue")).toBeInTheDocument();
    expect(screen.getByText("p50 approval time")).toBeInTheDocument();
    expect(screen.getByText("Approved · 24h")).toBeInTheDocument();
    expect(screen.getByText("Rejected · 24h")).toBeInTheDocument();
  });

  it("Active queue value derives from approvals.length", () => {
    render(
      <ApprovalsStatsStrip
        approvals={[makeApproval("a"), makeApproval("b"), makeApproval("c")]}
      />,
    );
    // Stat renders the value inside .stat-value tnum
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("Active queue value is 0 when approvals is undefined", () => {
    render(<ApprovalsStatsStrip approvals={undefined} />);
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("renders AP-2 BackendGapBanner declaring fixture-pending status", () => {
    render(<ApprovalsStatsStrip approvals={[]} />);
    const banner = screen.getByTestId("backend-gap-banner");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent(/p50 approval time/i);
    expect(banner).toHaveTextContent(/pending backend stats endpoint/i);
  });
});
