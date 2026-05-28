/**
 * File: frontend/tests/unit/tenant-settings/useRateLimitsUsage.test.tsx
 * Purpose: Vitest coverage for Sprint 57.58 useRateLimitsUsage polling query hook.
 * Category: Frontend / Tests / tenant-settings / unit
 * Scope: Phase 57 / Sprint 57.58 Track D
 *
 * Description:
 *   Verifies useRateLimitsUsage query hook:
 *   - queryFn calls fetchRateLimitsUsage(tenantId) on initial mount
 *   - 5-second refetchInterval triggers a second fetch (fake timers)
 *   - error from service rejection surfaces as isError
 *
 * Created: 2026-05-28 (Sprint 57.58 Day 1 Track D)
 *
 * Modification History (newest-first):
 *   - 2026-05-28: Initial creation (Sprint 57.58 Day 1 Track D)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, test, vi } from "vitest";

import * as svc from "@/features/tenant-settings/services/tenantSettingsService";
import { useRateLimitsUsage } from "@/features/tenant-settings/hooks/useRateLimitsUsage";
import type { RateLimitsUsageResponse } from "@/features/tenant-settings/types";

const MOCK_RESPONSE: RateLimitsUsageResponse = {
  items: [
    { resource: "api_requests", window: 60, limit: 100, current: 30, reset_at: 1_900_000_060 },
    { resource: "tool_calls", window: 60, limit: 100, current: 95, reset_at: 1_900_000_058 },
  ],
};

function makeWrapper(): {
  qc: QueryClient;
  wrapper: ({ children }: { children: ReactNode }) => JSX.Element;
} {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return {
    qc,
    wrapper: ({ children }) => (
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    ),
  };
}

describe("Sprint 57.58 — useRateLimitsUsage hook", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  test("queryFn invokes fetchRateLimitsUsage(tenantId) on initial mount", async () => {
    const spy = vi
      .spyOn(svc, "fetchRateLimitsUsage")
      .mockResolvedValue(MOCK_RESPONSE);
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useRateLimitsUsage("tenant-x"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(spy).toHaveBeenCalledWith("tenant-x", expect.anything());
    expect(result.current.data).toEqual(MOCK_RESPONSE);
  });

  test("5-second refetchInterval triggers a polling refetch", async () => {
    vi.useFakeTimers();
    const spy = vi
      .spyOn(svc, "fetchRateLimitsUsage")
      .mockResolvedValue(MOCK_RESPONSE);
    const { wrapper } = makeWrapper();
    renderHook(() => useRateLimitsUsage("tenant-x"), { wrapper });

    // Initial fetch resolves.
    await vi.waitFor(() => expect(spy).toHaveBeenCalledTimes(1));

    // Advance past the 5s refetchInterval → second poll fires.
    await vi.advanceTimersByTimeAsync(5000);
    await vi.waitFor(() => expect(spy.mock.calls.length).toBeGreaterThanOrEqual(2));
  });

  test("propagates Error on service rejection", async () => {
    vi.spyOn(svc, "fetchRateLimitsUsage").mockRejectedValue(
      new Error("HTTP 404: tenant not found"),
    );
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useRateLimitsUsage("tenant-x"), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toContain("tenant not found");
  });
});
