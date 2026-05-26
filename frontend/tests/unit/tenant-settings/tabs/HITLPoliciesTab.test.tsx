/**
 * File: frontend/tests/unit/tenant-settings/tabs/HITLPoliciesTab.test.tsx
 * Purpose: Vitest coverage for HITLPoliciesTab — 4 risk-tier rows + Badge tone dispatch + AP-2 banner.
 * Category: Frontend / Tests / tenant-settings / unit / tabs
 * Scope: Phase 57 / Sprint 57.44 Day 2 (mockup-fidelity rebuild Vitest coverage)
 *
 * Description:
 *   - Renders "HITL policies" Card title + subtitle
 *   - Renders 4 risk-tier rows (critical / high / medium / low)
 *   - Each row has sev-dot sev-{level} class span
 *   - Badge tone dispatch: auto=success / ask_once=info / always_ask=warning
 *   - BackendGapBanner present
 *
 * Created: 2026-05-26 (Sprint 57.44 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-05-26: Initial creation (Sprint 57.44 Day 2) — tenant-settings mockup-fidelity rebuild Vitest coverage
 *
 * Related:
 *   - frontend/src/features/tenant-settings/components/tabs/HITLPoliciesTab.tsx
 *   - frontend/src/features/tenant-settings/_fixtures.ts (HITL_POLICIES = 4 entries)
 *   - sprint-57-44-plan.md §AC3
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { HITLPoliciesTab } from "@/features/tenant-settings/components/tabs/HITLPoliciesTab";
import { HITL_POLICIES } from "@/features/tenant-settings/_fixtures";

describe("HITLPoliciesTab (Sprint 57.44)", () => {
  it("renders Card title 'HITL policies' + subtitle", () => {
    render(<HITLPoliciesTab />);
    expect(screen.getByText("HITL policies")).toBeInTheDocument();
    expect(screen.getByText(/Per-tool · risk-tiered · escalation routing/)).toBeInTheDocument();
  });

  it("renders all 5 column headers", () => {
    render(<HITLPoliciesTab />);
    expect(screen.getByText("Risk tier")).toBeInTheDocument();
    expect(screen.getByText("Default policy")).toBeInTheDocument();
    expect(screen.getByText("SLA")).toBeInTheDocument();
    expect(screen.getByText("Approvers")).toBeInTheDocument();
    expect(screen.getByText("Off-platform")).toBeInTheDocument();
  });

  it("renders 4 risk-tier rows with sev-dot sev-{level} class", () => {
    const { container } = render(<HITLPoliciesTab />);
    expect(HITL_POLICIES).toHaveLength(4);
    for (const p of HITL_POLICIES) {
      const dot = container.querySelector(`.sev-dot.sev-${p.risk}`);
      expect(dot).not.toBeNull();
      // Risk label text rendered (capitalize via CSS, raw text unchanged)
      expect(screen.getByText(p.risk)).toBeInTheDocument();
    }
  });

  it("Badge tone dispatch: auto → success / ask_once → info / always_ask → warning", () => {
    render(<HITLPoliciesTab />);
    // critical = always_ask → warning
    const alwaysAskBadges = screen.getAllByText("always_ask");
    expect(alwaysAskBadges.length).toBe(2); // critical + high
    expect(alwaysAskBadges[0]!.className).toMatch(/warning/);

    // medium = ask_once → info
    const askOnceBadge = screen.getByText("ask_once");
    expect(askOnceBadge.className).toMatch(/info/);

    // low = auto → success
    const autoBadge = screen.getByText("auto");
    expect(autoBadge.className).toMatch(/success/);
  });

  it("renders AP-2 BackendGapBanner", () => {
    render(<HITLPoliciesTab />);
    const banner = screen.getByTestId("backend-gap-banner");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent(/Phase 58\+/);
    expect(banner).toHaveTextContent(/HITL/);
  });
});
