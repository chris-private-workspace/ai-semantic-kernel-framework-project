/**
 * File: frontend/tests/unit/cost-dashboard/migrate.test.tsx
 * Purpose: Sprint 57.7 US-B3 → 57.8 US-4 architectural migration regression tests for CostOverview.
 * Category: Frontend / tests / unit / cost-dashboard
 * Scope: Phase 57 / Sprint 57.7 Day 3 Tier 3 → Sprint 57.8 US-4 (page-level wrap A1)
 *
 * Description:
 *   Sprint 57.8 A1 architectural change: AppShell wrap moved from
 *   CostOverview (inner component) → pages/cost-dashboard/index.tsx
 *   (page-level). CostOverview is now PURE BODY content with no layout
 *   dependency.
 *
 *   This test asserts the new architecture:
 *   1. CostOverview rendered alone produces NO brand link (no layout wrap)
 *   2. CostOverview rendered alone produces NO h1 (h1 = AppShellV2 pageTitle prop)
 *   3. CostOverview body has no inline `style` attributes (Tailwind only)
 *
 * Created: 2026-05-10 (Sprint 57.7 Day 3 Tier 3)
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.8 US-4 — rewrite for A1 architecture (CostOverview
 *     no longer wraps in AppShell + no longer renders h1; pages/index.tsx owns
 *     layout via AppShellV2 pageTitle slot)
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — wrap render in QueryClientProvider (CostOverview now consumes useCostSummary TanStack hook post-migration)
 *   - 2026-05-10: Initial creation (Sprint 57.7 Day 3 Tier 3)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { CostOverview } from "../../../src/features/cost-dashboard/components/CostOverview";

function renderInRouter(initialPath = "/cost-dashboard") {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[initialPath]}>
        <CostOverview />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("CostOverview — Sprint 57.7 US-B3 → 57.8 US-4 architectural migration", () => {
  it("renders pure body — NO layout wrap (no brand link, no h1) per A1 architecture", () => {
    renderInRouter();
    // Sprint 57.8 A1: AppShell wrap moved to pages/cost-dashboard/index.tsx;
    // CostOverview alone has no brand link footprint.
    expect(screen.queryByRole("link", { name: "IPA Platform" })).toBeNull();
    // h1 now provided by AppShellV2 pageTitle prop at page level; CostOverview
    // body emits no h1.
    expect(screen.queryByRole("heading", { level: 1 })).toBeNull();
  });

  it("body description paragraph rendered without inline style (Tailwind only)", () => {
    renderInRouter();
    // Description sentence (Sprint 57.13 US-A2 reworded to "for your tenant" —
    // tenant now comes from authStore, not a URL param).
    const desc = screen.getByText(/Cost ledger summary for your tenant/);
    expect(desc.getAttribute("style")).toBeNull();
    expect(desc.parentElement?.getAttribute("style")).toBeNull();
  });
});
