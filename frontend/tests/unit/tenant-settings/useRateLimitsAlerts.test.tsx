/**
 * File: frontend/tests/unit/tenant-settings/useRateLimitsAlerts.test.tsx
 * Purpose: Vitest coverage for Sprint 57.62 useRateLimitsAlerts polling query hook.
 * Category: Frontend / Tests / tenant-settings / unit
 * Scope: Phase 57 / Sprint 57.62 US-3 Track B
 *
 * Description:
 *   Verifies useRateLimitsAlerts query hook:
 *   - queryFn calls fetchRateLimitsAlerts(tenantId) on initial mount
 *   - 15-second refetchInterval triggers a second fetch (fake timers)
 *   - error from service rejection surfaces as isError
 *   - empty list resolves successfully
 *
 * Created: 2026-05-29 (Sprint 57.62 US-3 Track B)
 *
 * Modification History (newest-first):
 *   - 2026-05-29: Initial creation (Sprint 57.62 US-3 Track B)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, test, vi } from "vitest";

import * as svc from "@/features/tenant-settings/services/tenantSettingsService";
import { useRateLimitsAlerts } from "@/features/tenant-settings/hooks/useRateLimitsAlerts";
import type { RateLimitAlertsResponse } from "@/features/tenant-settings/types";

const MOCK_RESPONSE: RateLimitAlertsResponse = {
  items: [
    {
      resource: "api_requests",
      window: "min",
      threshold_pct: 80,
      actual_pct: 92,
      used: 92,
      quota: 100,
      severity: "warning",
      window_start: "2026-05-29T10:00:00Z",
      triggered_at: "2026-05-29T10:00:05Z",
    },
    {
      resource: "tool_calls",
      window: "min",
      threshold_pct: 80,
      actual_pct: 100,
      used: 100,
      quota: 100,
      severity: "critical",
      window_start: "2026-05-29T09:59:00Z",
      triggered_at: "2026-05-29T09:59:30Z",
    },
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

describe("Sprint 57.62 — useRateLimitsAlerts hook", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  test("queryFn invokes fetchRateLimitsAlerts(tenantId) on initial mount", async () => {
    const spy = vi
      .spyOn(svc, "fetchRateLimitsAlerts")
      .mockResolvedValue(MOCK_RESPONSE);
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useRateLimitsAlerts("tenant-x"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // tenantId first arg; limit undefined (backend default 20); signal last.
    expect(spy).toHaveBeenCalledWith("tenant-x", undefined, expect.anything());
    expect(result.current.data).toEqual(MOCK_RESPONSE);
  });

  test("resolves an empty alerts list successfully", async () => {
    vi.spyOn(svc, "fetchRateLimitsAlerts").mockResolvedValue({ items: [] });
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useRateLimitsAlerts("tenant-x"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.items).toEqual([]);
  });

  test("15-second refetchInterval triggers a polling refetch", async () => {
    vi.useFakeTimers();
    const spy = vi
      .spyOn(svc, "fetchRateLimitsAlerts")
      .mockResolvedValue(MOCK_RESPONSE);
    const { wrapper } = makeWrapper();
    renderHook(() => useRateLimitsAlerts("tenant-x"), { wrapper });

    // Initial fetch resolves.
    await vi.waitFor(() => expect(spy).toHaveBeenCalledTimes(1));

    // Advance past the 15s refetchInterval → second poll fires.
    await vi.advanceTimersByTimeAsync(15000);
    await vi.waitFor(() => expect(spy.mock.calls.length).toBeGreaterThanOrEqual(2));
  });

  test("propagates Error on service rejection", async () => {
    vi.spyOn(svc, "fetchRateLimitsAlerts").mockRejectedValue(
      new Error("HTTP 404: tenant not found"),
    );
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useRateLimitsAlerts("tenant-x"), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toContain("tenant not found");
  });
});
