/**
 * File: frontend/tests/unit/governance/ApprovalsFilterTabs.test.tsx
 * Purpose: Vitest coverage for ApprovalsFilterTabs — 5 tab labels + Active real count + onChange dispatch.
 * Category: Frontend / Tests / governance / unit
 * Scope: Phase 57 / Sprint 57.40 Day 2 (mockup-fidelity rebuild)
 *
 * Description:
 *   - 5 tabs render with mockup-verbatim labels (Active / Approved / Rejected / Expired / Policies)
 *   - "Active" count is approvalsCount prop (real); other counts (184/6/2) are fixture
 *   - "Policies" has no count
 *   - Clicking a tab calls onChange with that tab's id (string union narrowed)
 *
 * Created: 2026-05-25 (Sprint 57.40 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-05-25: Initial creation (Sprint 57.40 Day 2)
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApprovalsFilterTabs } from "@/features/governance/components/ApprovalsFilterTabs";

describe("ApprovalsFilterTabs (Sprint 57.40)", () => {
  it("renders all 5 tabs with mockup-verbatim labels", () => {
    render(
      <ApprovalsFilterTabs value="active" onChange={vi.fn()} approvalsCount={2} />,
    );
    const tabs = screen.getAllByRole("tab");
    expect(tabs).toHaveLength(5);
    expect(screen.getByRole("tab", { name: /active/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /approved/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /rejected/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /expired/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /policies/i })).toBeInTheDocument();
  });

  it("Active tab count derives from approvalsCount prop (real)", () => {
    render(
      <ApprovalsFilterTabs value="active" onChange={vi.fn()} approvalsCount={7} />,
    );
    const activeTab = screen.getByRole("tab", { name: /active/i });
    // Tabs renders count inside <span class="tab-count">
    expect(activeTab).toHaveTextContent("7");
    // Fixture counts for 3 other countable tabs
    expect(screen.getByRole("tab", { name: /approved/i })).toHaveTextContent("184");
    expect(screen.getByRole("tab", { name: /rejected/i })).toHaveTextContent("6");
    expect(screen.getByRole("tab", { name: /expired/i })).toHaveTextContent("2");
  });

  it("Active tab is aria-selected when value='active'", () => {
    render(
      <ApprovalsFilterTabs value="active" onChange={vi.fn()} approvalsCount={3} />,
    );
    expect(screen.getByRole("tab", { name: /active/i })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByRole("tab", { name: /approved/i })).toHaveAttribute(
      "aria-selected",
      "false",
    );
  });

  it("clicking a non-active tab calls onChange with that tab id", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <ApprovalsFilterTabs value="active" onChange={onChange} approvalsCount={0} />,
    );
    await user.click(screen.getByRole("tab", { name: /approved/i }));
    expect(onChange).toHaveBeenCalledWith("approved");
    await user.click(screen.getByRole("tab", { name: /policies/i }));
    expect(onChange).toHaveBeenCalledWith("policies");
    expect(onChange).toHaveBeenCalledTimes(2);
  });
});
