/**
 * File: frontend/tests/unit/tenant-settings/useTenantSettings.test.tsx
 * Purpose: Vitest tests for useTenantSettings + useTenantSettingsSave (Sprint 57.9 US-6).
 * Category: Frontend / tests / unit / tenant-settings
 * Scope: Phase 57 / Sprint 57.9 US-6 Day 4
 *
 * Created: 2026-05-09 (Sprint 57.9 Day 4 US-6)
 *
 * Modification History:
 *   - 2026-05-09: Initial creation (Sprint 57.9 US-6)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, test, vi } from "vitest";

import * as svc from "@/features/tenant-settings/services/tenantSettingsService";
import {
  TENANT_SETTINGS_QUERY_KEY_BASE,
  useTenantSettings,
} from "@/features/tenant-settings/hooks/useTenantSettings";
import { useTenantSettingsSave } from "@/features/tenant-settings/hooks/useTenantSettingsSave";
import {
  TenantPlan,
  TenantState,
  type TenantSettingsResponse,
} from "@/features/tenant-settings/types";

function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

const SAMPLE: TenantSettingsResponse = {
  id: "00000000-0000-0000-0000-000000000001",
  code: "ACME",
  display_name: "Acme Corp",
  state: TenantState.ACTIVE,
  plan: TenantPlan.ENTERPRISE,
  provisioning_progress: {},
  onboarding_progress: {},
  meta_data: {},
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-05-07T00:00:00Z",
};

describe("useTenantSettings (Sprint 57.9 US-6)", () => {
  test("TENANT_SETTINGS_QUERY_KEY_BASE is single-source ['tenant-settings', 'detail']", () => {
    expect(TENANT_SETTINGS_QUERY_KEY_BASE).toEqual(["tenant-settings", "detail"]);
  });

  test("disabled when tenantId is empty", async () => {
    const spy = vi.spyOn(svc, "fetchTenantSettings").mockResolvedValue(SAMPLE);

    const { result } = renderHook(() => useTenantSettings(""), {
      wrapper: makeWrapper(),
    });

    await waitFor(() => expect(result.current.isFetching).toBe(false));
    expect(spy).not.toHaveBeenCalled();
    expect(result.current.data).toBeUndefined();
  });

  test("fetches when tenantId provided + returns data on success", async () => {
    const spy = vi.spyOn(svc, "fetchTenantSettings").mockResolvedValueOnce(SAMPLE);

    const { result } = renderHook(() => useTenantSettings("tenant-uuid"), {
      wrapper: makeWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(spy).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual(SAMPLE);
  });
});

describe("useTenantSettingsSave (Sprint 57.9 US-6)", () => {
  test("mutate success calls updateTenantSettings with correct args", async () => {
    const updated = { ...SAMPLE, display_name: "Renamed" };
    const spy = vi.spyOn(svc, "updateTenantSettings").mockResolvedValueOnce(updated);

    const { result } = renderHook(() => useTenantSettingsSave(), {
      wrapper: makeWrapper(),
    });

    result.current.mutate({ tenantId: "tenant-uuid", payload: { display_name: "Renamed" } });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(spy).toHaveBeenCalledWith("tenant-uuid", { display_name: "Renamed" });
    expect(result.current.data).toEqual(updated);
  });

  test("mutate error exposes error state without invalidate effect on caller", async () => {
    vi.spyOn(svc, "updateTenantSettings").mockRejectedValueOnce(new Error("HTTP 422: invalid"));

    const { result } = renderHook(() => useTenantSettingsSave(), {
      wrapper: makeWrapper(),
    });

    result.current.mutate({ tenantId: "tenant-uuid", payload: { display_name: "" } });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe("HTTP 422: invalid");
  });
});
