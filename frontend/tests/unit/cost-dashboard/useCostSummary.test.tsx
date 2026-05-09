/**
 * File: frontend/tests/unit/cost-dashboard/useCostSummary.test.tsx
 * Purpose: Vitest tests for useCostSummary TanStack Query hook (Sprint 57.9 US-6).
 * Category: Frontend / tests / unit / cost-dashboard
 * Scope: Phase 57 / Sprint 57.9 US-6 Day 4
 *
 * Description:
 *   Mirrors useApprovals/useAuditLog test pattern (TanStack hook + delta
 *   assertions per D-PRE-10 lesson).
 *
 * Created: 2026-05-09 (Sprint 57.9 Day 4 US-6)
 *
 * Modification History:
 *   - 2026-05-09: Initial creation (Sprint 57.9 US-6 — closes AD-Cost-Dashboard-UseQuery)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, test, vi } from "vitest";

import * as costService from "@/features/cost-dashboard/services/costService";
import {
  COST_SUMMARY_QUERY_KEY_BASE,
  useCostSummary,
} from "@/features/cost-dashboard/hooks/useCostSummary";
import type { CostSummaryResponse } from "@/features/cost-dashboard/types";

function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

const SAMPLE_RESPONSE: CostSummaryResponse = {
  tenant_id: "11111111-1111-4111-8111-111111111111",
  month: "2026-05",
  total_cost_usd: "42.10",
  by_type: {},
};

describe("useCostSummary (Sprint 57.9 US-6)", () => {
  test("COST_SUMMARY_QUERY_KEY_BASE is single-source ['cost-dashboard', 'summary']", () => {
    expect(COST_SUMMARY_QUERY_KEY_BASE).toEqual(["cost-dashboard", "summary"]);
  });

  test("disabled when tenantId is empty (admin hasn't selected tenant)", async () => {
    const spy = vi.spyOn(costService, "fetchCostSummary").mockResolvedValue(SAMPLE_RESPONSE);

    const { result } = renderHook(() => useCostSummary("", "2026-05"), {
      wrapper: makeWrapper(),
    });

    // enabled:false short-circuits; isLoading should be false (TanStack v5 idle)
    await waitFor(() => expect(result.current.isFetching).toBe(false));
    expect(spy).not.toHaveBeenCalled();
    expect(result.current.data).toBeUndefined();
  });

  test("fetches when tenantId provided + returns data on success", async () => {
    const spy = vi.spyOn(costService, "fetchCostSummary").mockResolvedValueOnce(SAMPLE_RESPONSE);

    const { result } = renderHook(() => useCostSummary("tenant-uuid", "2026-05"), {
      wrapper: makeWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(spy).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual(SAMPLE_RESPONSE);
  });

  test("error state surfaces (HTTP 403 admin-platform RBAC simulation)", async () => {
    vi.spyOn(costService, "fetchCostSummary").mockRejectedValueOnce(
      new Error("HTTP 403: admin role required"),
    );

    const { result } = renderHook(() => useCostSummary("tenant-uuid", "2026-05"), {
      wrapper: makeWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe("HTTP 403: admin role required");
  });
});
