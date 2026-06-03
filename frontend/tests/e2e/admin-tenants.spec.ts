/**
 * File: frontend/tests/e2e/admin-tenants.spec.ts
 * Purpose: Hermetic Playwright e2e for the admin-tenants real-data wiring (Sprint 57.73 A-6a).
 * Category: Frontend / e2e / admin-tenants
 * Scope: Phase 57 / Sprint 57.73 (A-6a real-data wiring)
 *
 * Description:
 *   Mocks the backend calls the page makes — GET /api/v1/auth/me (so the
 *   authStore bootstraps an authenticated platform-admin and RequireAuth +
 *   role gate pass), GET /api/v1/admin/tenants (the list endpoint the
 *   TenantsTable consumes) and GET /api/v1/admin/tenants/stats (the Sprint
 *   57.74 fleet aggregate powering the strip + the agents/runs24 columns).
 *   Scenarios:
 *     1. happy   → real-shaped items render with mapped fields (name/code/plan)
 *     2. error   → 500 surfaces the inline error row + Retry affordance
 *     3. empty   → {items:[]} surfaces the empty-state row
 *     4. stats happy → strip shows real fleet values + table agents/runs24 filled
 *     5. stats error → 500 surfaces strip mockup-native error + table "—"
 *
 *   A dev token is seeded via addInitScript so fetchWithAuth attaches
 *   Authorization and the mocked /auth/me drives status=authenticated.
 *
 *   Route-order note: the `**\/tenants\/stats` route is registered AFTER the
 *   `**\/admin\/tenants` list route so the more-specific stats matcher wins
 *   for /tenants/stats (Playwright resolves overlapping routes last-registered
 *   first).
 *
 * Created: 2026-06-03 (Sprint 57.73)
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Sprint 57.74 — mock /admin/tenants/stats + stats happy/error scenarios (A-6a)
 *   - 2026-06-03: Initial creation (Sprint 57.73 A-6a) — admin-tenants real-data wiring e2e
 *
 * Related:
 *   - frontend/src/features/admin-tenants/components/{TenantsTable,TenantsStatsStrip}.tsx
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

// Sprint 57.74 — fleet aggregate powering the strip + the agents/runs24
// columns. ACME present in per_tenant (agents 5, runs24 1234); GLOBEX absent.
const STATS_PAYLOAD = {
  fleet: { active_tenants: 48, total_seats: 1284, agents_deployed: 612 },
  per_tenant: [
    { tenant_id: "00000000-0000-0000-0000-000000000001", agents: 5, runs24: 1234 },
  ],
  gapped: ["anomalies", "deltas"],
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

  // Register a default stats mock LAST (most-specific matcher wins for
  // /tenants/stats over the broad /admin/tenants** list matcher in each test).
  async function mockStats(
    page: import("@playwright/test").Page,
    { status = 200, body = STATS_PAYLOAD }: { status?: number; body?: unknown } = {},
  ): Promise<void> {
    await page.route("**/api/v1/admin/tenants/stats", (route) =>
      route.fulfill({
        status,
        contentType: "application/json",
        body: JSON.stringify(status === 200 ? body : { detail: "boom" }),
      }),
    );
  }

  test("happy: real tenant rows render with mapped fields", async ({ page }) => {
    await page.route("**/api/v1/admin/tenants**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(TENANTS_PAYLOAD),
      }),
    );
    await mockStats(page);

    await page.goto("/admin-tenants");

    await expect(page.getByText("All tenants")).toBeVisible();
    // name ← display_name, id ← code
    await expect(page.getByText("Acme Corp")).toBeVisible();
    await expect(page.getByText("ACME").first()).toBeVisible();
    await expect(page.getByText("Globex EU")).toBeVisible();
  });

  test("error: 500 surfaces inline error row + retry", async ({ page }) => {
    await page.route("**/api/v1/admin/tenants**", (route) =>
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "boom" }),
      }),
    );
    await mockStats(page);

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
    await mockStats(page);

    await page.goto("/admin-tenants");

    await expect(page.getByTestId("tenant-row-empty")).toBeVisible();
  });

  test("stats happy: strip shows real fleet values + table agents/runs24 filled", async ({
    page,
  }) => {
    await page.route("**/api/v1/admin/tenants**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(TENANTS_PAYLOAD),
      }),
    );
    await mockStats(page);

    await page.goto("/admin-tenants");

    // Strip real fleet values (total_seats number-formatted → "1,284").
    await expect(page.getByText("48").first()).toBeVisible();
    await expect(page.getByText("1,284")).toBeVisible();
    await expect(page.getByText("612")).toBeVisible();
    // ACME's agents/runs24 filled from the per-tenant map.
    await expect(page.getByText("5").first()).toBeVisible();
    await expect(page.getByText("1,234")).toBeVisible();
  });

  test("stats error: 500 surfaces strip mockup-native error (table cells '—')", async ({
    page,
  }) => {
    await page.route("**/api/v1/admin/tenants**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(TENANTS_PAYLOAD),
      }),
    );
    await mockStats(page, { status: 500 });

    await page.goto("/admin-tenants");

    // Rows still render (list call succeeded) but stats failed → strip values
    // + table agents/runs24 fall back to the subtle "—".
    await expect(page.getByText("Acme Corp")).toBeVisible();
    await expect(page.getByText("—").first()).toBeVisible();
  });
});
