/**
 * File: frontend/tests/unit/governance/useApprovals.test.tsx
 * Purpose: Vitest tests for useApprovals TanStack Query hook (Sprint 57.9 US-3).
 * Category: Frontend / tests / unit / governance
 * Scope: Phase 57 / Sprint 57.9 US-3 Day 2
 *
 * Description:
 *   First TanStack hook test in V2 frontend. Establishes pattern for
 *   subsequent hooks (useApprovalDecide / useAuditLog / 4-page Day 4 hooks):
 *   - QueryClient per-test (retry: false to fail-fast on mock errors)
 *   - JSX wrapper exposing QueryClientProvider
 *   - vi.spyOn the service layer; assert hook state via renderHook + waitFor
 *
 * Created: 2026-05-09 (Sprint 57.9 Day 2)
 *
 * Modification History:
 *   - 2026-05-09: Initial creation (Sprint 57.9 US-3 — first TanStack hook test)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, test, vi } from "vitest";

import { governanceService } from "@/features/governance/services/governanceService";
import { APPROVALS_QUERY_KEY, useApprovals } from "@/features/governance/hooks/useApprovals";
import type { ApprovalSummary } from "@/features/governance/types";

function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

const SAMPLE_APPROVAL: ApprovalSummary = {
  request_id: "11111111-1111-4111-8111-111111111111",
  tenant_id: "22222222-2222-4222-8222-222222222222",
  session_id: "33333333-3333-4333-8333-333333333333",
  requester: "user-a",
  risk_level: "HIGH",
  payload: { tool_name: "salesforce_query", reason: "PII access" },
  sla_deadline: new Date(Date.now() + 60_000).toISOString(),
  context_snapshot: {},
};

describe("useApprovals (Sprint 57.9 US-3)", () => {
  test("APPROVALS_QUERY_KEY is single-source ['governance', 'approvals']", () => {
    expect(APPROVALS_QUERY_KEY).toEqual(["governance", "approvals"]);
  });

  test("initial fetch returns approvals on success", async () => {
    const spy = vi
      .spyOn(governanceService, "listPending")
      .mockResolvedValueOnce([SAMPLE_APPROVAL]);

    const { result } = renderHook(() => useApprovals(), { wrapper: makeWrapper() });

    expect(result.current.isLoading).toBe(true);
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(spy).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual([SAMPLE_APPROVAL]);
    expect(result.current.error).toBeNull();
  });

  test("error state surfaces when service throws", async () => {
    vi.spyOn(governanceService, "listPending").mockRejectedValueOnce(
      new Error("HTTP 500: backend down"),
    );

    const { result } = renderHook(() => useApprovals(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe("HTTP 500: backend down");
    expect(result.current.data).toBeUndefined();
  });

  test("refetch() triggers an additional service call", async () => {
    // Use mockResolvedValue (not Once) — TanStack v5 may make internal mount-time
    // refetches (network status / focus checks); brittle to assert exact pre-refetch
    // count. Test intent: refetch() must produce >0 additional service calls.
    const spy = vi.spyOn(governanceService, "listPending").mockResolvedValue([SAMPLE_APPROVAL]);

    const { result } = renderHook(() => useApprovals(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    const callsBefore = spy.mock.calls.length;

    await result.current.refetch();
    expect(spy.mock.calls.length).toBeGreaterThan(callsBefore);
    expect(result.current.data).toEqual([SAMPLE_APPROVAL]);
  });
});
