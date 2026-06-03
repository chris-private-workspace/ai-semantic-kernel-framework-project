/**
 * File: frontend/tests/e2e/admin-tenants.spec.ts
 * Purpose: Hermetic Playwright e2e for the admin-tenants real-data wiring (Sprint 57.73 A-6a).
 * Category: Frontend / e2e / admin-tenants
 * Scope: Phase 57 / Sprint 57.73 (A-6a real-data wiring)
 *
 * Description:
 *   Mocks the two backend calls the page makes — GET /api/v1/auth/me (so the
 *   authStore bootstraps an authenticated platform-admin and RequireAuth +
 *   role gate pass) and GET /api/v1/admin/tenants** (the list endpoint the
 *   TenantsTable now consumes). Three scenarios:
 *     1. happy   → real-shaped items render with mapped fields (name/code/plan)
 *     2. error   → 500 surfaces the inline error row + Retry affordance
 *     3. empty   → {items:[]} surfaces the empty-state row
 *
 *   A dev token is seeded via addInitScript so fetchWithAuth attaches
 *   Authorization and the mocked /auth/me drives status=authenticated.
 *
 * Created: 2026-06-03 (Sprint 57.73)
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Initial creation (Sprint 57.73 A-6a) — admin-tenants real-data wiring e2e
 *
 * Related:
 *   - frontend/src/features/admin-tenants/components/TenantsTable.tsx
 *   - frontend/src/features/auth/services/authService.ts (GET /auth/me bootstrap)
 *   - playwright.config.ts (webServer + baseURL)
 */

import { expect, test } from "@playwright/test";

const ADMIN_ME = {
  user: { id: "u-admin", email: "admin@example.test", display_name: "Admin" },
  tenant: { id: "t-1", name: "Acme", code: "ACME" },
  roles: ["platform_admin"],
};

const TENANTS_PAYLOAD = {
  items: [
    {
      id: "00000000-0000-0000-0000-000000000001",
      code: "ACME",
      display_name: "Acme Corp",
      state: "active",
      plan: "enterprise",
      region: "ap-east-1",
      locale: "zh-TW",
      retention_days: 90,
      sso_enabled: true,
      seats: 12,
      created_at: "2026-01-15T08:30:00Z",
      updated_at: "2026-05-07T00:00:00Z",
    },
    {
      id: "00000000-0000-0000-0000-000000000002",
      code: "GLOBEX",
      display_name: "Globex EU",
      state: "suspended",
      plan: "standard",
      region: "eu-west-1",
      locale: "en-GB",
      retention_days: 30,
      sso_enabled: false,
      seats: 6,
      created_at: "2025-09-12T12:00:00Z",
      updated_at: "2026-05-07T00:00:00Z",
    },
  ],
  total: 2,
  limit: 50,
  offset: 0,
};

test.describe("Sprint 57.73 admin-tenants real-data wiring", () => {
  test.beforeEach(async ({ page }) => {
    // Seed dev token so fetchWithAuth attaches Authorization (no /auth/login bounce).
    await page.addInitScript(() => {
      window.localStorage.setItem("v2_jwt", "e2e-fake-token");
    });
    // Authenticated platform-admin so RequireAuth + role gate render the view.
    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(ADMIN_ME),
      }),
    );
  });

  test("happy: real tenant rows render with mapped fields", async ({ page }) => {
    await page.route("**/api/v1/admin/tenants**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(TENANTS_PAYLOAD),
      }),
    );

    await page.goto("/admin-tenants");

    await expect(page.getByText("All tenants")).toBeVisible();
    // name ← display_name, id ← code
    await expect(page.getByText("Acme Corp")).toBeVisible();
    await expect(page.getByText("ACME").first()).toBeVisible();
    await expect(page.getByText("Globex EU")).toBeVisible();
    // unbacked agents/runs24 → literal "—"
    await expect(page.getByText("—").first()).toBeVisible();
  });

  test("error: 500 surfaces inline error row + retry", async ({ page }) => {
    await page.route("**/api/v1/admin/tenants**", (route) =>
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "boom" }),
      }),
    );

    await page.goto("/admin-tenants");

    await expect(page.getByTestId("tenant-row-error")).toBeVisible();
    await expect(page.getByRole("button", { name: /Retry/ })).toBeVisible();
  });

  test("empty: no items surfaces empty-state row", async ({ page }) => {
    await page.route("**/api/v1/admin/tenants**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0, limit: 50, offset: 0 }),
      }),
    );

    await page.goto("/admin-tenants");

    await expect(page.getByTestId("tenant-row-empty")).toBeVisible();
  });
});
