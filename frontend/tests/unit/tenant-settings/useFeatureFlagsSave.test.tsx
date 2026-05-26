/**
 * File: frontend/tests/unit/tenant-settings/useFeatureFlagsSave.test.tsx
 * Purpose: Vitest coverage for Sprint 57.55 useFeatureFlagsSave mutation hook.
 * Category: Frontend / Tests / tenant-settings / unit
 * Scope: Phase 57 / Sprint 57.55 Track B
 *
 * Description:
 *   Verifies useFeatureFlagsSave mutation hook:
 *   - mutationFn calls saveFeatureFlagOverrides(tenantId, payload)
 *   - onSuccess invalidates [...FEATURE_FLAGS_QUERY_KEY_BASE, tenantId]
 *   - onError propagates Error from service rejection
 *
 * Created: 2026-05-27 (Sprint 57.55 Day 1)
 *
 * Modification History (newest-first):
 *   - 2026-05-27: Initial creation (Sprint 57.55 Day 1 Track B)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, test, vi } from "vitest";

import * as svc from "@/features/tenant-settings/services/tenantSettingsService";
import { FEATURE_FLAGS_QUERY_KEY_BASE } from "@/features/tenant-settings/hooks/useFeatureFlags";
import { useFeatureFlagsSave } from "@/features/tenant-settings/hooks/useFeatureFlagsSave";
import type {
  FeatureFlagOverridesUpsertRequest,
  FeatureFlagOverridesUpsertResponse,
} from "@/features/tenant-settings/types";

const MOCK_PAYLOAD: FeatureFlagOverridesUpsertRequest = {
  overrides: { "subagent.fork.enabled": true, "tool.sandbox_full": false },
};

const MOCK_RESPONSE: FeatureFlagOverridesUpsertResponse = {
  saved_overrides: MOCK_PAYLOAD.overrides,
  items: [
    {
      name: "subagent.fork.enabled",
      value: true,
      default_enabled: false,
      overridden: true,
      description: "Allow concurrent fork mode",
      updated_at: "2026-05-27T00:00:00Z",
    },
    {
      name: "tool.sandbox_full",
      value: false,
      default_enabled: true,
      overridden: true,
      description: "Permit FULL_SANDBOX tool runs",
      updated_at: "2026-05-27T00:00:00Z",
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

describe("Sprint 57.55 — useFeatureFlagsSave hook", () => {
  test("mutationFn invokes saveFeatureFlagOverrides(tenantId, payload) on mutate", async () => {
    const spy = vi.spyOn(svc, "saveFeatureFlagOverrides").mockResolvedValueOnce(MOCK_RESPONSE);
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useFeatureFlagsSave("tenant-x"), { wrapper });

    await act(async () => {
      result.current.mutate(MOCK_PAYLOAD);
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(spy).toHaveBeenCalledWith("tenant-x", MOCK_PAYLOAD);
    expect(result.current.data).toEqual(MOCK_RESPONSE);
  });

  test("onSuccess invalidates [...FEATURE_FLAGS_QUERY_KEY_BASE, tenantId]", async () => {
    vi.spyOn(svc, "saveFeatureFlagOverrides").mockResolvedValueOnce(MOCK_RESPONSE);
    const { qc, wrapper } = makeWrapper();
    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useFeatureFlagsSave("tenant-x"), { wrapper });

    await act(async () => {
      result.current.mutate(MOCK_PAYLOAD);
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: [...FEATURE_FLAGS_QUERY_KEY_BASE, "tenant-x"],
    });
  });

  test("propagates Error on service rejection", async () => {
    vi.spyOn(svc, "saveFeatureFlagOverrides").mockRejectedValueOnce(
      new Error("HTTP 422: unknown flag name"),
    );
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useFeatureFlagsSave("tenant-x"), { wrapper });

    await act(async () => {
      result.current.mutate(MOCK_PAYLOAD);
    });
    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error?.message).toContain("unknown flag name");
  });
});
