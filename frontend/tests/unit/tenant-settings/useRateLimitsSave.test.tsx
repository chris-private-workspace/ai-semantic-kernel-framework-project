/**
 * File: frontend/tests/unit/tenant-settings/useRateLimitsSave.test.tsx
 * Purpose: Vitest coverage for Sprint 57.57 useRateLimitsSave mutation hook.
 * Category: Frontend / Tests / tenant-settings / unit
 * Scope: Phase 57 / Sprint 57.57 Track B
 *
 * Description:
 *   Verifies useRateLimitsSave mutation hook:
 *   - mutationFn calls saveRateLimits(tenantId, payload)
 *   - onSuccess invalidates [...RATE_LIMITS_QUERY_KEY_BASE, tenantId]
 *   - onError propagates Error from service rejection
 *
 * Created: 2026-05-27 (Sprint 57.57 Day 1)
 *
 * Modification History (newest-first):
 *   - 2026-05-27: Initial creation (Sprint 57.57 Day 1 Track B)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, test, vi } from "vitest";

import * as svc from "@/features/tenant-settings/services/tenantSettingsService";
import { RATE_LIMITS_QUERY_KEY_BASE } from "@/features/tenant-settings/hooks/useRateLimits";
import { useRateLimitsSave } from "@/features/tenant-settings/hooks/useRateLimitsSave";
import type {
  RateLimitsUpsertRequest,
  RateLimitsUpsertResponse,
} from "@/features/tenant-settings/types";

const MOCK_PAYLOAD: RateLimitsUpsertRequest = {
  items: [
    { label: "API requests", value: "100/min" },
    { label: "Agent runs", value: "20/min" },
  ],
};

const MOCK_RESPONSE: RateLimitsUpsertResponse = {
  items: MOCK_PAYLOAD.items,
  total: 2,
  limit: 50,
  offset: 0,
};

function makeWrapper(): {
  qc: QueryClient;
  wrapper: ({ children }: { children: ReactNode }) => JSX.Element;
} {
  const qc = new QueryClient({
    defaultOptions: { mutations: { retry: false }, queries: { retry: false } },
  });
  return {
    qc,
    wrapper: ({ children }) => (
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    ),
  };
}

describe("Sprint 57.57 — useRateLimitsSave hook", () => {
  test("mutationFn invokes saveRateLimits(tenantId, payload) on mutate", async () => {
    const spy = vi.spyOn(svc, "saveRateLimits").mockResolvedValueOnce(MOCK_RESPONSE);
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useRateLimitsSave("tenant-x"), { wrapper });

    await act(async () => {
      result.current.mutate(MOCK_PAYLOAD);
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(spy).toHaveBeenCalledWith("tenant-x", MOCK_PAYLOAD);
    expect(result.current.data).toEqual(MOCK_RESPONSE);
  });

  test("onSuccess invalidates [...RATE_LIMITS_QUERY_KEY_BASE, tenantId]", async () => {
    vi.spyOn(svc, "saveRateLimits").mockResolvedValueOnce(MOCK_RESPONSE);
    const { qc, wrapper } = makeWrapper();
    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useRateLimitsSave("tenant-x"), { wrapper });

    await act(async () => {
      result.current.mutate(MOCK_PAYLOAD);
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: [...RATE_LIMITS_QUERY_KEY_BASE, "tenant-x"],
    });
  });

  test("propagates Error on service rejection", async () => {
    vi.spyOn(svc, "saveRateLimits").mockRejectedValueOnce(
      new Error("HTTP 422: items[].label required"),
    );
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useRateLimitsSave("tenant-x"), { wrapper });

    await act(async () => {
      result.current.mutate(MOCK_PAYLOAD);
    });
    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error?.message).toContain("label required");
  });
});
