/**
 * File: frontend/tests/unit/memory/RecentMemoryOpsCard.test.tsx
 * Purpose: Vitest coverage for RecentMemoryOpsCard — Card title + 6-col table headers + 5 fixture rows + Op Badge tone dispatch + AP-2 banner.
 * Category: Frontend / Tests / memory / unit
 * Scope: Phase 57 / Sprint 57.42 Day 2 (memory matrix full mockup-fidelity rebuild)
 *
 * Description:
 *   - Card title "Recent memory ops" + subtitle "Live · last 100"
 *   - 6 table headers (Op / Scope / Key / Value / By / When)
 *   - 5 fixture rows (3 op types: WRITE × 2 / READ × 2 / EXPIRE × 1)
 *   - First fixture row content rendered (scope / key / value / by / at)
 *   - AP-2 BackendGapBanner declared inside Card for deferred ops timeline endpoint
 *
 * Created: 2026-05-25 (Sprint 57.42 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Sprint 57.73 Track C — update AP-2 banner assertion to reworded deferred-feature text
 *   - 2026-05-25: Initial creation (Sprint 57.42 Day 2)
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RecentMemoryOpsCard } from "@/features/memory/components/RecentMemoryOpsCard";

describe("RecentMemoryOpsCard (Sprint 57.42)", () => {
  it("renders Card title + 6-col table headers + 5 fixture rows + AP-2 banner", () => {
    render(<RecentMemoryOpsCard />);

    // Card title + subtitle
    expect(screen.getByText("Recent memory ops")).toBeInTheDocument();
    expect(screen.getByText("Live · last 100")).toBeInTheDocument();

    // 6 column headers in mockup order
    expect(screen.getByText("Op")).toBeInTheDocument();
    expect(screen.getByText("Scope")).toBeInTheDocument();
    expect(screen.getByText("Key")).toBeInTheDocument();
    expect(screen.getByText("Value")).toBeInTheDocument();
    expect(screen.getByText("By")).toBeInTheDocument();
    expect(screen.getByText("When")).toBeInTheDocument();

    // First fixture row content (RECENT_MEMORY_OPS[0])
    expect(screen.getByText("session.sess_4tk2p")).toBeInTheDocument();
    expect(screen.getByText("root_cause")).toBeInTheDocument();
    expect(screen.getByText("pgbouncer pool too small")).toBeInTheDocument();
    expect(screen.getAllByText("incident-responder").length).toBeGreaterThan(0);
    expect(screen.getByText("10:42:27")).toBeInTheDocument();

    // Op Badge tone dispatch — 3 op types render across 5 rows
    expect(screen.getAllByText("WRITE").length).toBe(2);
    expect(screen.getAllByText("READ").length).toBe(2);
    expect(screen.getAllByText("EXPIRE").length).toBe(1);

    // AP-2 BackendGapBanner declared inside Card (reworded Sprint 57.73 Track C
    // to deferred ops-history feature — memory writes emit zero audit rows)
    const banner = screen.getByTestId("backend-gap-banner");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent(/deferred backend feature/i);
  });
});
