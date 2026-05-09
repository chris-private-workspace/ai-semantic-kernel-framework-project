/**
 * File: frontend/tests/unit/admin-tenants/TenantListPagination.test.tsx
 * Purpose: Unit test for TenantListPagination — Next click advances offset; Prev/Next edge-disable.
 * Category: Frontend / tests / unit / admin-tenants
 * Scope: Phase 57 / Sprint 57.4 US-4 → Sprint 57.9 US-6 Day 4 (TanStack hook source for total)
 *
 * Created: 2026-05-07 (Sprint 57.4 Day 3)
 * Last Modified: 2026-05-09
 *
 * Modification History:
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — wrap with QueryClientProvider; total now sourced from useAdminTenants hook (was store.total)
 *   - 2026-05-07: Initial creation (Sprint 57.4 Day 3)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { TenantListPagination } from "../../../src/features/admin-tenants/components/TenantListPagination";
import * as svc from "../../../src/features/admin-tenants/services/adminTenantsService";
import { useAdminTenantsStore } from "../../../src/features/admin-tenants/store/adminTenantsStore";

function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

describe("TenantListPagination (post-57.9 US-6 — total via hook)", () => {
  beforeEach(() => {
    useAdminTenantsStore.getState().reset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("Next click advances offset by limit (TanStack auto-refetches via key change)", async () => {
    vi.spyOn(svc, "listTenants").mockResolvedValue({
      items: [],
      total: 100,
      limit: 50,
      offset: 0,
    });

    const Wrapper = makeWrapper();
    render(
      <Wrapper>
        <TenantListPagination />
      </Wrapper>,
    );

    // Wait for hook's first fetch to populate total=100 → Next becomes enabled
    await waitFor(() => expect(screen.getByText("Next →")).not.toBeDisabled());

    fireEvent.click(screen.getByText("Next →"));
    expect(useAdminTenantsStore.getState().query.offset).toBe(50);
  });

  it("Prev disabled at offset=0 + Next disabled when total <= limit", async () => {
    vi.spyOn(svc, "listTenants").mockResolvedValue({
      items: [],
      total: 30,
      limit: 50,
      offset: 0,
    });

    const Wrapper = makeWrapper();
    render(
      <Wrapper>
        <TenantListPagination />
      </Wrapper>,
    );

    await waitFor(() => expect(screen.getByText(/1-30 of 30|0-0 of 30/)).toBeInTheDocument());
    expect(screen.getByText("← Prev")).toBeDisabled();
    expect(screen.getByText("Next →")).toBeDisabled();
  });
});
