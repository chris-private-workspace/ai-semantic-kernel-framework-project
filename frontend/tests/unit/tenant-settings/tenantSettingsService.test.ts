/**
 * File: frontend/tests/unit/tenant-settings/tenantSettingsService.test.ts
 * Purpose: Unit test for tenantSettingsService — fetch + update URL building + error throw.
 * Category: Frontend / tests / unit / tenant-settings
 * Scope: Phase 57 / Sprint 57.3 US-3
 *
 * Created: 2026-05-07 (Sprint 57.3 Day 3)
 *
 * Modification History (newest-first):
 *   - 2026-05-28: Sprint 57.58 — +2 fetchRateLimitsUsage GET tests
 *   - 2026-05-27: Sprint 57.57 — +2 saveRateLimits PUT tests
 *   - 2026-05-27: Sprint 57.56 — +2 saveQuotaOverrides PUT tests
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  fetchFeatureFlags,
  fetchHITLPolicies,
  fetchQuotas,
  fetchRateLimits,
  fetchRateLimitsUsage,
  fetchTenantIdentity,
  fetchTenantMembers,
  fetchTenantSettings,
  saveFeatureFlagOverrides,
  saveHITLPolicies,
  saveQuotaOverrides,
  saveRateLimits,
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
  meta_data: { region_legacy: "us-west" },
  // Sprint 57.46 — SaaS settings extension
  region: "americas",
  locale: "en-US",
  retention_days: 180,
  sso_enabled: false,
  seats: 4,
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
      // Post-57.9 US-6: fetchWithAuth always sets credentials:"include" + Headers;
      // URL contract unchanged.
      expect(fetchSpy).toHaveBeenCalledWith(
        "/api/v1/admin/tenants/tenant-uuid",
        expect.objectContaining({ credentials: "include" }),
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
      // Post-57.9 US-6: fetchWithAuth wraps method+body+headers; assert key
      // contract fields with objectContaining (Headers normalized to Headers
      // object internally → tests can't compare instance equality cleanly).
      expect(fetchSpy).toHaveBeenCalledWith(
        "/api/v1/admin/tenants/tenant-uuid",
        expect.objectContaining({
          method: "PATCH",
          credentials: "include",
          body: JSON.stringify({ display_name: "Renamed Corp" }),
        }),
      );
      expect(result.display_name).toBe("Renamed Corp");
    });
  });

  /* === Sprint 57.49 — 5 sub-resource list endpoints === */

  describe("fetchTenantMembers (Sprint 57.49)", () => {
    it("builds correct URL with no query-string when limit/offset omitted", async () => {
      const payload = { items: [], total: 0, limit: 50, offset: 0 };
      fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(payload), { status: 200 }));
      await fetchTenantMembers("tenant-x");
      expect(fetchSpy).toHaveBeenCalledWith(
        "/api/v1/admin/tenants/tenant-x/members",
        expect.objectContaining({ method: "GET", credentials: "include" }),
      );
    });

    it("appends limit/offset query params when provided", async () => {
      const payload = { items: [], total: 0, limit: 10, offset: 20 };
      fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(payload), { status: 200 }));
      await fetchTenantMembers("tenant-x", 10, 20);
      expect(fetchSpy).toHaveBeenCalledWith(
        "/api/v1/admin/tenants/tenant-x/members?limit=10&offset=20",
        expect.objectContaining({ method: "GET" }),
      );
    });
  });

  describe("fetchHITLPolicies (Sprint 57.49)", () => {
    it("builds correct URL for /hitl-policies", async () => {
      const payload = { items: [], total: 0, limit: 50, offset: 0 };
      fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(payload), { status: 200 }));
      await fetchHITLPolicies("tenant-x");
      expect(fetchSpy).toHaveBeenCalledWith(
        "/api/v1/admin/tenants/tenant-x/hitl-policies",
        expect.objectContaining({ method: "GET" }),
      );
    });
  });

  describe("fetchFeatureFlags (Sprint 57.49)", () => {
    it("builds correct URL for /feature-flags", async () => {
      const payload = { items: [], total: 0, limit: 50, offset: 0 };
      fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(payload), { status: 200 }));
      await fetchFeatureFlags("tenant-x");
      expect(fetchSpy).toHaveBeenCalledWith(
        "/api/v1/admin/tenants/tenant-x/feature-flags",
        expect.objectContaining({ method: "GET" }),
      );
    });
  });

  describe("fetchQuotas (Sprint 57.49)", () => {
    it("builds correct URL for /quotas", async () => {
      const payload = { items: [], total: 0, limit: 50, offset: 0 };
      fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(payload), { status: 200 }));
      await fetchQuotas("tenant-x");
      expect(fetchSpy).toHaveBeenCalledWith(
        "/api/v1/admin/tenants/tenant-x/quotas",
        expect.objectContaining({ method: "GET" }),
      );
    });
  });

  describe("fetchRateLimits (Sprint 57.49)", () => {
    it("builds correct URL for /rate-limits", async () => {
      const payload = { items: [], total: 0, limit: 50, offset: 0 };
      fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(payload), { status: 200 }));
      await fetchRateLimits("tenant-x");
      expect(fetchSpy).toHaveBeenCalledWith(
        "/api/v1/admin/tenants/tenant-x/rate-limits",
        expect.objectContaining({ method: "GET" }),
      );
    });

    it("throws Error on non-2xx response", async () => {
      fetchSpy.mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "tenant not found" }), { status: 404 }),
      );
      await expect(fetchRateLimits("tenant-x")).rejects.toThrow("tenant not found");
    });
  });

  /* === Sprint 57.54 Track B — saveHITLPolicies PUT === */

  describe("saveHITLPolicies (Sprint 57.54)", () => {
    it("sends PUT with correct URL + JSON body", async () => {
      const payload = {
        auto_approve_max_risk: "LOW" as const,
        require_approval_min_risk: "MEDIUM" as const,
        reviewer_groups_by_risk: { HIGH: ["@platform-l1"] },
        sla_seconds_by_risk: { HIGH: 900 },
      };
      const responseBody = {
        saved_policy: payload,
        items: [
          { risk: "HIGH", policy: "always_ask", sla_seconds: 900, reviewers: "@platform-l1" },
        ],
      };
      fetchSpy.mockResolvedValueOnce(
        new Response(JSON.stringify(responseBody), { status: 200 }),
      );

      const result = await saveHITLPolicies("tenant-x", payload);
      expect(fetchSpy).toHaveBeenCalledWith(
        "/api/v1/admin/tenants/tenant-x/hitl-policies",
        expect.objectContaining({
          method: "PUT",
          credentials: "include",
          body: JSON.stringify(payload),
        }),
      );
      expect(result).toEqual(responseBody);
    });

    it("throws Error with detail message on 422 validation failure", async () => {
      fetchSpy.mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "invalid risk level" }), { status: 422 }),
      );
      await expect(
        saveHITLPolicies("tenant-x", {
          auto_approve_max_risk: "LOW",
          require_approval_min_risk: "MEDIUM",
          reviewer_groups_by_risk: {},
          sla_seconds_by_risk: {},
        }),
      ).rejects.toThrow("invalid risk level");
    });
  });

  /* === Sprint 57.55 Track B — saveFeatureFlagOverrides PUT === */

  describe("saveFeatureFlagOverrides (Sprint 57.55)", () => {
    it("sends PUT with correct URL + JSON body", async () => {
      const payload = {
        overrides: { "subagent.fork.enabled": true, "tool.sandbox_full": false },
      };
      const responseBody = {
        saved_overrides: payload.overrides,
        items: [
          {
            name: "subagent.fork.enabled",
            value: true,
            default_enabled: false,
            overridden: true,
            description: null,
            updated_at: "2026-05-27T00:00:00Z",
          },
        ],
      };
      fetchSpy.mockResolvedValueOnce(
        new Response(JSON.stringify(responseBody), { status: 200 }),
      );

      const result = await saveFeatureFlagOverrides("tenant-x", payload);
      expect(fetchSpy).toHaveBeenCalledWith(
        "/api/v1/admin/tenants/tenant-x/feature-flags",
        expect.objectContaining({
          method: "PUT",
          credentials: "include",
          body: JSON.stringify(payload),
        }),
      );
      expect(result).toEqual(responseBody);
    });

    it("throws Error with detail message on 422 unknown flag", async () => {
      fetchSpy.mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "unknown flag name: bogus.flag" }), { status: 422 }),
      );
      await expect(
        saveFeatureFlagOverrides("tenant-x", { overrides: { "bogus.flag": true } }),
      ).rejects.toThrow("unknown flag name");
    });
  });

  /* === Sprint 57.56 Track B — saveQuotaOverrides PUT === */

  describe("saveQuotaOverrides (Sprint 57.56)", () => {
    it("sends PUT with correct URL + JSON body", async () => {
      const payload = {
        overrides: { tokens_per_day: 20_000_000, cost_usd_per_day: 200 },
      };
      const responseBody = {
        saved_overrides: payload.overrides,
        items: [
          {
            resource: "tokens_per_day",
            limit: 20_000_000,
            unit: "tokens",
            period: "day",
            current_usage: null,
          },
        ],
      };
      fetchSpy.mockResolvedValueOnce(
        new Response(JSON.stringify(responseBody), { status: 200 }),
      );

      const result = await saveQuotaOverrides("tenant-x", payload);
      expect(fetchSpy).toHaveBeenCalledWith(
        "/api/v1/admin/tenants/tenant-x/quotas",
        expect.objectContaining({
          method: "PUT",
          credentials: "include",
          body: JSON.stringify(payload),
        }),
      );
      expect(result).toEqual(responseBody);
    });

    it("throws Error with detail message on 422 unknown resource", async () => {
      fetchSpy.mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "unknown resource name: bogus_resource" }), { status: 422 }),
      );
      await expect(
        saveQuotaOverrides("tenant-x", { overrides: { bogus_resource: 100 } }),
      ).rejects.toThrow("unknown resource");
    });
  });

  /* === Sprint 57.57 Track B — saveRateLimits PUT === */

  describe("saveRateLimits (Sprint 57.57)", () => {
    it("sends PUT with correct URL + JSON body", async () => {
      const payload = {
        items: [
          { label: "API requests", value: "100/min" },
          { label: "Agent runs", value: "20/min" },
        ],
      };
      const responseBody = {
        items: payload.items,
        total: 2,
        limit: 50,
        offset: 0,
      };
      fetchSpy.mockResolvedValueOnce(
        new Response(JSON.stringify(responseBody), { status: 200 }),
      );

      const result = await saveRateLimits("tenant-x", payload);
      expect(fetchSpy).toHaveBeenCalledWith(
        "/api/v1/admin/tenants/tenant-x/rate-limits",
        expect.objectContaining({
          method: "PUT",
          credentials: "include",
          body: JSON.stringify(payload),
        }),
      );
      expect(result).toEqual(responseBody);
    });

    it("throws Error with detail message on 422 invalid item", async () => {
      fetchSpy.mockResolvedValueOnce(
        new Response(
          JSON.stringify({ detail: "items[].label required" }),
          { status: 422 },
        ),
      );
      await expect(
        saveRateLimits("tenant-x", { items: [{ label: "", value: "100/min" }] }),
      ).rejects.toThrow("label required");
    });
  });

  /* === Sprint 57.58 Track D — fetchRateLimitsUsage GET === */

  describe("fetchRateLimitsUsage (Sprint 57.58)", () => {
    it("builds correct URL for /rate-limits/usage (no query-string) + returns parsed items", async () => {
      const payload = {
        items: [
          { resource: "api_requests", window: 60, limit: 100, current: 30, reset_at: 1_900_000_060 },
        ],
      };
      fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(payload), { status: 200 }));
      const result = await fetchRateLimitsUsage("tenant-x");
      expect(fetchSpy).toHaveBeenCalledWith(
        "/api/v1/admin/tenants/tenant-x/rate-limits/usage",
        expect.objectContaining({ method: "GET", credentials: "include" }),
      );
      expect(result).toEqual(payload);
    });

    it("throws Error with detail message on 404", async () => {
      fetchSpy.mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "tenant not found" }), { status: 404 }),
      );
      await expect(fetchRateLimitsUsage("tenant-x")).rejects.toThrow("tenant not found");
    });
  });

  /* === Sprint 57.50 — Identity single-record endpoint === */

  describe("fetchTenantIdentity (Sprint 57.50)", () => {
    it("builds correct URL for /identity (no query-string)", async () => {
      const payload = {
        provider: "SAML 2.0 · WorkOS",
        scim_enabled: true,
        allowed_domains: ["acme.com", "acme.io"],
        mfa_required: true,
      };
      fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(payload), { status: 200 }));
      const result = await fetchTenantIdentity("tenant-x");
      expect(fetchSpy).toHaveBeenCalledWith(
        "/api/v1/admin/tenants/tenant-x/identity",
        expect.objectContaining({ method: "GET", credentials: "include" }),
      );
      expect(result).toEqual(payload);
    });

    it("throws Error on non-2xx response", async () => {
      fetchSpy.mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "tenant not found" }), { status: 404 }),
      );
      await expect(fetchTenantIdentity("tenant-x")).rejects.toThrow("tenant not found");
    });
  });
});
