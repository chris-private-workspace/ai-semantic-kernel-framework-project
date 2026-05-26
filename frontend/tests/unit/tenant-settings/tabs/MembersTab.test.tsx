/**
 * File: frontend/tests/unit/tenant-settings/tabs/MembersTab.test.tsx
 * Purpose: Vitest coverage for MembersTab — 8 members + avatar gradient + role Badge tone + Invite action.
 * Category: Frontend / Tests / tenant-settings / unit / tabs
 * Scope: Phase 57 / Sprint 57.44 Day 2 (mockup-fidelity rebuild Vitest coverage)
 *
 * Description:
 *   - Renders "Members" Card title + subtitle "8 active · 0 invitations"
 *   - Renders Invite button + click fires window.alert with backend gap message
 *   - Renders 8 member rows (one per MEMBERS entry)
 *   - Each row has avatar span with linear-gradient style
 *   - Role Badge tone dispatch: admin=primary / compliance=memory / operator=no tone
 *   - BackendGapBanner present
 *
 * Created: 2026-05-26 (Sprint 57.44 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-05-26: Initial creation (Sprint 57.44 Day 2) — tenant-settings mockup-fidelity rebuild Vitest coverage
 *
 * Related:
 *   - frontend/src/features/tenant-settings/components/tabs/MembersTab.tsx
 *   - frontend/src/features/tenant-settings/_fixtures.ts (MEMBERS = 8 entries)
 *   - sprint-57-44-plan.md §AC3
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { MembersTab } from "@/features/tenant-settings/components/tabs/MembersTab";
import { MEMBERS } from "@/features/tenant-settings/_fixtures";

describe("MembersTab (Sprint 57.44)", () => {
  beforeEach(() => {
    vi.spyOn(window, "alert").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders Card title 'Members' + subtitle '8 active · 0 invitations'", () => {
    render(<MembersTab />);
    expect(screen.getByText("Members")).toBeInTheDocument();
    expect(screen.getByText(/8 active · 0 invitations/)).toBeInTheDocument();
  });

  it("renders Invite button + click fires window.alert with backend gap message", async () => {
    const user = userEvent.setup();
    const alertSpy = vi.spyOn(window, "alert").mockImplementation(() => {});
    render(<MembersTab />);
    const btn = screen.getByRole("button", { name: /invite/i });
    expect(btn).toBeInTheDocument();
    await user.click(btn);
    expect(alertSpy).toHaveBeenCalledTimes(1);
    expect(alertSpy.mock.calls[0]![0]).toMatch(/backend gap/i);
    expect(alertSpy.mock.calls[0]![0]).toMatch(/Phase 58\+/i);
  });

  it("renders 8 member rows from MEMBERS fixture (unique names)", () => {
    render(<MembersTab />);
    expect(MEMBERS).toHaveLength(8);
    for (const m of MEMBERS) {
      expect(screen.getByText(m.n)).toBeInTheDocument();
      expect(screen.getByText(m.e)).toBeInTheDocument();
    }
  });

  it("renders 8 avatar spans with linear-gradient style", () => {
    const { container } = render(<MembersTab />);
    // Avatar span is the first span inside each .row > td > .row div in member cell.
    // Each avatar uses inline style.background containing 'linear-gradient'.
    const allSpans = container.querySelectorAll("td span") as NodeListOf<HTMLSpanElement>;
    const avatarSpans = Array.from(allSpans).filter((s) =>
      (s.style.background || "").includes("linear-gradient"),
    );
    expect(avatarSpans.length).toBe(8);
  });

  it("Role Badge tone dispatch: admin → primary / compliance → memory / operator → no tone", () => {
    render(<MembersTab />);
    // 2 admins + 5 operators + 1 compliance in MEMBERS fixture
    const adminBadges = screen.getAllByText("admin");
    expect(adminBadges.length).toBe(2);
    expect(adminBadges[0]!.className).toMatch(/primary/);

    const complianceBadge = screen.getByText("compliance");
    expect(complianceBadge.className).toMatch(/memory/);

    const operatorBadges = screen.getAllByText("operator");
    expect(operatorBadges.length).toBe(5);
    // operator has empty tone — no primary/info/success/warning/danger/memory token
    expect(operatorBadges[0]!.className).not.toMatch(/(primary|info|success|warning|danger|memory)/);
  });

  it("renders AP-2 BackendGapBanner", () => {
    render(<MembersTab />);
    const banner = screen.getByTestId("backend-gap-banner");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent(/Phase 58\+/);
    expect(banner).toHaveTextContent(/Member roster/);
  });
});
