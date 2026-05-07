/**
 * File: frontend/tests/unit/tenant-settings/tenantSettingsStore.test.ts
 * Purpose: Unit test for tenantSettingsStore — loadData + save action transitions.
 * Category: Frontend / tests / unit / tenant-settings
 * Scope: Phase 57 / Sprint 57.3 US-3
 *
 * Created: 2026-05-07 (Sprint 57.3 Day 3)
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import * as svc from "../../../src/features/tenant-settings/services/tenantSettingsService";
import { useTenantSettingsStore } from "../../../src/features/tenant-settings/store/tenantSettingsStore";
import {
  TenantPlan,
  TenantState,
  type TenantSettingsResponse,
} from "../../../src/features/tenant-settings/types";

const MOCK_DATA: TenantSettingsResponse = {
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

describe("tenantSettingsStore", () => {
  beforeEach(() => {
    useTenantSettingsStore.getState().reset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("loadData success transitions: setTenantId → loadData → data populated", async () => {
    vi.spyOn(svc, "fetchTenantSettings").mockResolvedValueOnce(MOCK_DATA);

    useTenantSettingsStore.getState().setTenantId("tenant-uuid");
    expect(useTenantSettingsStore.getState().tenantId).toBe("tenant-uuid");

    await useTenantSettingsStore.getState().loadData();
    const state = useTenantSettingsStore.getState();
    expect(state.loading).toBe(false);
    expect(state.data).toEqual(MOCK_DATA);
    expect(state.error).toBeNull();
  });

  it("save success: optimistic update → data replaced from server response", async () => {
    const updated = { ...MOCK_DATA, display_name: "Renamed" };
    vi.spyOn(svc, "updateTenantSettings").mockResolvedValueOnce(updated);

    useTenantSettingsStore.setState({ tenantId: "tenant-uuid", data: MOCK_DATA });
    await useTenantSettingsStore.getState().save({ display_name: "Renamed" });

    const state = useTenantSettingsStore.getState();
    expect(state.saving).toBe(false);
    expect(state.saveError).toBeNull();
    expect(state.data?.display_name).toBe("Renamed");
  });
});
