/**
 * File: frontend/tests/unit/tenant-settings/useQuotasSave.test.tsx
 * Purpose: Vitest coverage for Sprint 57.56 useQuotasSave mutation hook.
 * Category: Frontend / Tests / tenant-settings / unit
 * Scope: Phase 57 / Sprint 57.56 Track B
 *
 * Description:
 *   Verifies useQuotasSave mutation hook:
 *   - mutationFn calls saveQuotaOverrides(tenantId, payload)
 *   - onSuccess invalidates [...QUOTAS_QUERY_KEY_BASE, tenantId]
 *   - onError propagates Error from service rejection
 *
 * Created: 2026-05-27 (Sprint 57.56 Day 1)
 *
 * Modification History (newest-first):
 *   - 2026-05-27: Initial creation (Sprint 57.56 Day 1 Track B)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, test, vi } from "vitest";

import * as svc from "@/features/tenant-settings/services/tenantSettingsService";
import { QUOTAS_QUERY_KEY_BASE } from "@/features/tenant-settings/hooks/useQuotas";
import { useQuotasSave } from "@/features/tenant-settings/hooks/useQuotasSave";
import type {
  QuotaOverridesUpsertRequest,
  QuotaOverridesUpsertResponse,
} from "@/features/tenant-settings/types";

const MOCK_PAYLOAD: QuotaOverridesUpsertRequest = {
  overrides: { tokens_per_day: 20_000_000, cost_usd_per_day: 200 },
};

const MOCK_RESPONSE: QuotaOverridesUpsertResponse = {
  saved_overrides: MOCK_PAYLOAD.overrides,
  items: [
    {
      resource: "tokens_per_day",
      limit: 20_000_000,
      unit: "tokens",
      period: "day",
      current_usage: null,
    },
    {
      resource: "cost_usd_per_day",
      limit: 200,
      unit: "usd",
      period: "day",
      current_usage: null,
    },
  ],
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

describe("Sprint 57.56 — useQuotasSave hook", () => {
  test("mutationFn invokes saveQuotaOverrides(tenantId, payload) on mutate", async () => {
    const spy = vi.spyOn(svc, "saveQuotaOverrides").mockResolvedValueOnce(MOCK_RESPONSE);
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useQuotasSave("tenant-x"), { wrapper });

    await act(async () => {
      result.current.mutate(MOCK_PAYLOAD);
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(spy).toHaveBeenCalledWith("tenant-x", MOCK_PAYLOAD);
    expect(result.current.data).toEqual(MOCK_RESPONSE);
  });

  test("onSuccess invalidates [...QUOTAS_QUERY_KEY_BASE, tenantId]", async () => {
    vi.spyOn(svc, "saveQuotaOverrides").mockResolvedValueOnce(MOCK_RESPONSE);
    const { qc, wrapper } = makeWrapper();
    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useQuotasSave("tenant-x"), { wrapper });

    await act(async () => {
      result.current.mutate(MOCK_PAYLOAD);
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: [...QUOTAS_QUERY_KEY_BASE, "tenant-x"],
    });
  });

  test("propagates Error on service rejection", async () => {
    vi.spyOn(svc, "saveQuotaOverrides").mockRejectedValueOnce(
      new Error("HTTP 422: unknown resource"),
    );
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useQuotasSave("tenant-x"), { wrapper });

    await act(async () => {
      result.current.mutate(MOCK_PAYLOAD);
    });
    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error?.message).toContain("unknown resource");
  });
});
