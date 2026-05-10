/**
 * File: frontend/tests/e2e/fixtures/auth-fixtures.ts
 * Purpose: Auth state seeder/clearer for e2e tests gated by <RequireAuth> / authStore.
 * Category: Frontend / e2e / fixtures
 * Scope: Phase 57 / Sprint 57.8 US-5 → Sprint 57.13 US-A1/A2 (authStore-based)
 *
 * Description:
 *   Sprint 57.13 moved the auth source of truth from a localStorage JWT to
 *   authStore (resolved on app mount via GET /api/v1/auth/me). E2e tests now
 *   make the gate pass by *mocking* /api/v1/auth/me — `seedAuthJwt` fulfils
 *   it with a fake {user, tenant, roles} payload; `clearAuthJwt` returns 401
 *   (the unauthenticated path → redirect to /auth/login).
 *
 *   `page.route` registered here in beforeEach is checked before later spec
 *   routes for the same URL (Playwright matches the most-recently-registered
 *   handler, but specs almost never override the /api/v1/auth/me route).
 *
 *   NOTE: tenant-scoped pages (cost-dashboard / sla-dashboard / tenant-settings)
 *   now read tenant_id from authStore.tenant.id, not the URL ?tenant_id=.
 *   Specs that mock per-tenant endpoints should mock the seeded tenant id
 *   (default below) or pass `tenantId` to override. Full e2e sweep: Sprint
 *   57.13 US-C1 (Day 9).
 *
 * Created: 2026-05-09 (Sprint 57.8 Day 3)
 * Last Modified: 2026-05-10
 *
 * Related:
 *   - frontend/src/features/auth/store/authStore.ts (bootstrap → /auth/me)
 *   - frontend/src/features/auth/components/RequireAuth.tsx (the gate)
 */

import type { Page } from "@playwright/test";

/** Default seeded tenant id (used by tenant-scoped pages reading authStore.tenant.id). */
export const E2E_TENANT_ID = "00000000-0000-0000-0000-0000000000e1";

interface SeedAuthOptions {
  tenantId?: string;
  tenantCode?: string;
  roles?: string[];
}

/**
 * Make the auth gate pass: mock GET /api/v1/auth/me with a fake authenticated
 * identity (default: a platform-admin user so all pages render). Call in
 * beforeEach BEFORE page.goto().
 */
export async function seedAuthJwt(page: Page, opts: SeedAuthOptions = {}): Promise<void> {
  const tenantId = opts.tenantId ?? E2E_TENANT_ID;
  const tenantCode = opts.tenantCode ?? "E2E";
  const roles = opts.roles ?? ["user", "admin", "platform_admin"];
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        user: {
          id: "00000000-0000-0000-0000-0000000000a1",
          email: "e2e@test.local",
          display_name: "E2E User",
        },
        tenant: { id: tenantId, name: "E2E Tenant", code: tenantCode },
        roles,
      }),
    }),
  );
}

/** Explicit unauthenticated path — /auth/me returns 401 → <RequireAuth> redirects to /auth/login. */
export async function clearAuthJwt(page: Page): Promise<void> {
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({ error: "Authorization Bearer token required" }),
    }),
  );
}
