/**
 * File: frontend/tests/unit/admin-tenants/adminTenantsService.test.ts
 * Purpose: Unit test for adminTenantsService — URL building + listTenants happy + error throw.
 * Category: Frontend / tests / unit / admin-tenants
 * Scope: Phase 57 / Sprint 57.4 US-2
 *
 * Created: 2026-05-07 (Sprint 57.4 Day 2)
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  buildListSearchParams,
  listTenants,
} from "../../../src/features/admin-tenants/services/adminTenantsService";
import {
  TenantPlan,
  TenantState,
  type TenantListQuery,
  type TenantListResponse,
} from "../../../src/features/admin-tenants/types";

const MOCK_RESPONSE: TenantListResponse = {
  items: [
    {
      id: "00000000-0000-0000-0000-000000000001",
      code: "ACME",
      display_name: "Acme Corp",
      state: TenantState.ACTIVE,
      plan: TenantPlan.ENTERPRISE,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-05-07T00:00:00Z",
    },
  ],
  total: 1,
  limit: 50,
  offset: 0,
};

describe("adminTenantsService", () => {
  describe("buildListSearchParams", () => {
    it("omits undefined optional filters and emits limit+offset", () => {
      const query: TenantListQuery = { limit: 50, offset: 0 };
      const params = buildListSearchParams(query);
      expect(params.has("state")).toBe(false);
      expect(params.has("plan")).toBe(false);
      expect(params.has("search")).toBe(false);
      expect(params.get("limit")).toBe("50");
      expect(params.get("offset")).toBe("0");
    });

    it("emits all filters when provided + skips empty search string", () => {
      const query: TenantListQuery = {
        state: TenantState.ACTIVE,
        plan: TenantPlan.ENTERPRISE,
        search: "ACME",
        limit: 25,
        offset: 25,
      };
      const params = buildListSearchParams(query);
      expect(params.get("state")).toBe("active");
      expect(params.get("plan")).toBe("enterprise");
      expect(params.get("search")).toBe("ACME");
      expect(params.get("limit")).toBe("25");
      expect(params.get("offset")).toBe("25");

      const emptySearch: TenantListQuery = {
        search: "",
        limit: 50,
        offset: 0,
      };
      expect(buildListSearchParams(emptySearch).has("search")).toBe(false);
    });
  });

  describe("listTenants", () => {
    let fetchSpy: ReturnType<typeof vi.spyOn>;

    beforeEach(() => {
      fetchSpy = vi.spyOn(global, "fetch");
    });

    afterEach(() => {
      fetchSpy.mockRestore();
    });

    it("calls fetch with correct URL + parses JSON response", async () => {
      fetchSpy.mockResolvedValueOnce(
        new Response(JSON.stringify(MOCK_RESPONSE), { status: 200 }),
      );
      const result = await listTenants({
        state: TenantState.ACTIVE,
        limit: 50,
        offset: 0,
      });
      const calledUrl = fetchSpy.mock.calls[0][0] as string;
      expect(calledUrl).toContain("/api/v1/admin/tenants?");
      expect(calledUrl).toContain("state=active");
      expect(calledUrl).toContain("limit=50");
      expect(result).toEqual(MOCK_RESPONSE);
    });

    it("throws Error with detail message on 403", async () => {
      fetchSpy.mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "forbidden" }), { status: 403 }),
      );
      await expect(
        listTenants({ limit: 50, offset: 0 }),
      ).rejects.toThrow("forbidden");
    });
  });
});
