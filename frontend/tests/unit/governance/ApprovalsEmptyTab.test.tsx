/**
 * File: frontend/tests/unit/governance/ApprovalsEmptyTab.test.tsx
 * Purpose: Vitest coverage for ApprovalsEmptyTab — AP-2 banner placeholder for 4 non-active tabs.
 * Category: Frontend / Tests / governance / unit
 * Scope: Phase 57 / Sprint 57.40 Day 2 (mockup-fidelity rebuild)
 *
 * Description:
 *   - Card title reflects the selected tabId label
 *   - "Pending backend list / filter endpoint" subtitle present
 *   - BackendGapBanner (AP-2 declaration) present with tab-specific reason
 *   - Each of approved / rejected / expired / policies tab labels dispatched correctly
 *
 * Created: 2026-05-25 (Sprint 57.40 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-05-25: Initial creation (Sprint 57.40 Day 2)
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ApprovalsEmptyTab } from "@/features/governance/components/ApprovalsEmptyTab";

describe("ApprovalsEmptyTab (Sprint 57.40)", () => {
  it("renders Card title + subtitle + AP-2 banner for approved tab", () => {
    render(<ApprovalsEmptyTab tabId="approved" />);
    expect(screen.getByText("Approved")).toBeInTheDocument();
    expect(
      screen.getByText(/pending backend list \/ filter endpoint/i),
    ).toBeInTheDocument();
    const banner = screen.getByTestId("backend-gap-banner");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent(/tab "Approved"/i);
    expect(banner).toHaveTextContent(/phase 58\+/i);
  });

  it("dispatches correct label for each of the 4 non-active tab ids", () => {
    const cases: Array<["approved" | "rejected" | "expired" | "policies", string]> = [
      ["approved", "Approved"],
      ["rejected", "Rejected"],
      ["expired", "Expired"],
      ["policies", "Policies"],
    ];
    for (const [tabId, expectedLabel] of cases) {
      const { unmount } = render(<ApprovalsEmptyTab tabId={tabId} />);
      expect(screen.getByText(expectedLabel)).toBeInTheDocument();
      const banner = screen.getByTestId("backend-gap-banner");
      expect(banner).toHaveTextContent(new RegExp(`tab "${expectedLabel}"`, "i"));
      unmount();
    }
  });
});
