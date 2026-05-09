/**
 * File: frontend/tests/unit/governance/useApprovalDecide.test.tsx
 * Purpose: Vitest tests for useApprovalDecide TanStack Query mutation hook (Sprint 57.9 US-3).
 * Category: Frontend / tests / unit / governance
 * Scope: Phase 57 / Sprint 57.9 US-3 Day 2
 *
 * Created: 2026-05-09 (Sprint 57.9 Day 2)
 *
 * Modification History:
 *   - 2026-05-09: Initial creation (Sprint 57.9 US-3)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, test, vi } from "vitest";

import { governanceService } from "@/features/governance/services/governanceService";
import { useApprovalDecide } from "@/features/governance/hooks/useApprovalDecide";
import { APPROVALS_QUERY_KEY } from "@/features/governance/hooks/useApprovals";

function makeWrapperWithClient() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
  return { qc, wrapper };
}

const REQUEST_ID = "11111111-1111-4111-8111-111111111111";

describe("useApprovalDecide (Sprint 57.9 US-3)", () => {
  test("mutate success → calls service with correct args + invalidates approvals query", async () => {
    const decideSpy = vi.spyOn(governanceService, "decide").mockResolvedValueOnce({
      request_id: REQUEST_ID,
      decision: "approved",
      reviewer: "user-b",
    });
    const { qc, wrapper } = makeWrapperWithClient();
    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useApprovalDecide(), { wrapper });

    result.current.mutate({
      requestId: REQUEST_ID,
      decision: "approved",
      reason: "Looks safe.",
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(decideSpy).toHaveBeenCalledWith(REQUEST_ID, "approved", "Looks safe.");
    expect(result.current.data?.decision).toBe("approved");
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: APPROVALS_QUERY_KEY });
  });

  test("mutate error → exposes error state without invalidate", async () => {
    vi.spyOn(governanceService, "decide").mockRejectedValueOnce(new Error("HTTP 409: state conflict"));
    const { qc, wrapper } = makeWrapperWithClient();
    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useApprovalDecide(), { wrapper });

    result.current.mutate({ requestId: REQUEST_ID, decision: "rejected" });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe("HTTP 409: state conflict");
    expect(invalidateSpy).not.toHaveBeenCalled();
  });

  test("isPending toggles during mutation lifecycle", async () => {
    let resolveDecide: (() => void) | null = null;
    vi.spyOn(governanceService, "decide").mockImplementationOnce(
      () =>
        new Promise<never>((_, reject) => {
          resolveDecide = () => reject(new Error("late"));
        }),
    );
    const { wrapper } = makeWrapperWithClient();

    const { result } = renderHook(() => useApprovalDecide(), { wrapper });

    expect(result.current.isPending).toBe(false);
    result.current.mutate({ requestId: REQUEST_ID, decision: "escalated" });
    await waitFor(() => expect(result.current.isPending).toBe(true));

    resolveDecide?.();
    await waitFor(() => expect(result.current.isPending).toBe(false));
    expect(result.current.isError).toBe(true);
  });
});
