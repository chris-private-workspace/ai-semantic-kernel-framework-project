/**
 * File: frontend/tests/unit/auth/authStore.test.ts
 * Purpose: Unit test for authStore — bootstrap (200 / 401 / network error) + clear.
 * Category: Frontend / tests / unit / auth
 * Scope: Phase 57 / Sprint 57.13 US-A1
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 1)
 * Last Modified: 2026-06-15 (Sprint 57.123 — /auth/me payload carries tenant.plan + tenant.region)
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useAuthStore } from "../../../src/features/auth/store/authStore";

const ME_PAYLOAD = {
  user: { id: "00000000-0000-0000-0000-0000000000a1", email: "alice@acme.test", display_name: "Alice" },
  // Sprint 57.123: /auth/me now returns plan + region (real Tenant cols).
  tenant: {
    id: "00000000-0000-0000-0000-0000000000b1",
    name: "Acme Corp",
    code: "ACME",
    plan: "enterprise",
    region: "ap-east-1",
  },
  roles: ["user", "admin"],
};

function resetStore(): void {
  useAuthStore.setState({ status: "unknown", user: null, tenant: null, roles: [] });
}

describe("authStore", () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    resetStore();
    fetchSpy = vi.spyOn(global, "fetch");
  });

  afterEach(() => {
    fetchSpy.mockRestore();
    resetStore();
  });

  it("starts in 'unknown' with empty identity", () => {
    const s = useAuthStore.getState();
    expect(s.status).toBe("unknown");
    expect(s.user).toBeNull();
    expect(s.tenant).toBeNull();
    expect(s.roles).toEqual([]);
  });

  it("bootstrap → 200 → 'authenticated' with the /auth/me payload", async () => {
    fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(ME_PAYLOAD), { status: 200 }));
    await useAuthStore.getState().bootstrap();
    const s = useAuthStore.getState();
    expect(s.status).toBe("authenticated");
    expect(s.user).toEqual(ME_PAYLOAD.user);
    expect(s.tenant).toEqual(ME_PAYLOAD.tenant);
    // Sprint 57.123: plan + region flow through to the store (chrome consumers).
    expect(s.tenant?.plan).toBe("enterprise");
    expect(s.tenant?.region).toBe("ap-east-1");
    expect(s.roles).toEqual(["user", "admin"]);
    // verifies it hit /auth/me with credentials included
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/auth/me");
    expect(init.credentials).toBe("include");
  });

  it("bootstrap → 401 → 'anonymous' with empty identity", async () => {
    fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify({ error: "x" }), { status: 401 }));
    await useAuthStore.getState().bootstrap();
    const s = useAuthStore.getState();
    expect(s.status).toBe("anonymous");
    expect(s.user).toBeNull();
    expect(s.tenant).toBeNull();
    expect(s.roles).toEqual([]);
  });

  it("bootstrap → network error → 'anonymous' (does not throw)", async () => {
    fetchSpy.mockRejectedValueOnce(new Error("network down"));
    await expect(useAuthStore.getState().bootstrap()).resolves.toBeUndefined();
    expect(useAuthStore.getState().status).toBe("anonymous");
  });

  it("clear → 'anonymous' + nulls (from authenticated)", () => {
    useAuthStore.setState({
      status: "authenticated",
      user: ME_PAYLOAD.user,
      tenant: ME_PAYLOAD.tenant,
      roles: ["user"],
    });
    useAuthStore.getState().clear();
    const s = useAuthStore.getState();
    expect(s.status).toBe("anonymous");
    expect(s.user).toBeNull();
    expect(s.tenant).toBeNull();
    expect(s.roles).toEqual([]);
  });
});
