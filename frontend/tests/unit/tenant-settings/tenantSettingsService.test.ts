/**
 * File: frontend/tests/unit/tenant-settings/tenantSettingsService.test.ts
 * Purpose: Unit test for tenantSettingsService — fetch + update URL building + error throw.
 * Category: Frontend / tests / unit / tenant-settings
 * Scope: Phase 57 / Sprint 57.3 US-3
 *
 * Created: 2026-05-07 (Sprint 57.3 Day 3)
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  fetchTenantSettings,
  updateTenantSettings,
} from "../../../src/features/tenant-settings/services/tenantSettingsService";
import {
  TenantPlan,
  TenantState,
  type TenantSettingsResponse,
} from "../../../src/features/tenant-settings/types";

const MOCK_RESPONSE: TenantSettingsResponse = {
  id: "00000000-0000-0000-0000-000000000001",
  code: "ACME",
  display_name: "Acme Corp",
  state: TenantState.ACTIVE,
  plan: TenantPlan.ENTERPRISE,
  provisioning_progress: {},
  onboarding_progress: {},
  meta_data: { region: "us-west" },
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-05-07T00:00:00Z",
};

describe("tenantSettingsService", () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    fetchSpy = vi.spyOn(global, "fetch");
  });

  afterEach(() => {
    fetchSpy.mockRestore();
  });

  describe("fetchTenantSettings", () => {
    it("builds correct URL + returns parsed JSON on 200", async () => {
      fetchSpy.mockResolvedValueOnce(
        new Response(JSON.stringify(MOCK_RESPONSE), { status: 200 }),
      );

      const result = await fetchTenantSettings("tenant-uuid");
      expect(fetchSpy).toHaveBeenCalledWith(
        "/api/v1/admin/tenants/tenant-uuid",
        { credentials: "include" },
      );
      expect(result).toEqual(MOCK_RESPONSE);
    });

    it("throws Error with detail message on 500", async () => {
      fetchSpy.mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "internal server error" }), { status: 500 }),
      );

      await expect(fetchTenantSettings("tenant-uuid")).rejects.toThrow("internal server error");
    });
  });

  describe("updateTenantSettings", () => {
    it("sends PATCH with correct body + returns updated TenantSettingsResponse", async () => {
      const updated = { ...MOCK_RESPONSE, display_name: "Renamed Corp" };
      fetchSpy.mockResolvedValueOnce(
        new Response(JSON.stringify(updated), { status: 200 }),
      );

      const result = await updateTenantSettings("tenant-uuid", { display_name: "Renamed Corp" });
      expect(fetchSpy).toHaveBeenCalledWith(
        "/api/v1/admin/tenants/tenant-uuid",
        {
          method: "PATCH",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ display_name: "Renamed Corp" }),
        },
      );
      expect(result.display_name).toBe("Renamed Corp");
    });
  });
});
