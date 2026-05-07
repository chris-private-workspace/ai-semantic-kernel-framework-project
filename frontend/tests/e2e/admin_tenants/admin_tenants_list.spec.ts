/**
 * File: frontend/tests/e2e/admin_tenants/admin_tenants_list.spec.ts
 * Purpose: Playwright e2e — admin tenants console list view (Sprint 57.4 US-5).
 * Category: Frontend / e2e / admin_tenants
 * Scope: Phase 57 / Sprint 57.4 US-5
 *
 * Description:
 *   Validates the Admin Tenants Console list page (57.4 US-1..US-4):
 *     1. Happy path: load page → table renders with mocked rows.
 *     2. Filter: select state=ACTIVE → second GET fired with state filter.
 *     3. Click View → navigates to /tenant-settings/?tenant_id=...
 *     4. Empty state: backend returns items=[] → "No tenants match" + Reset.
 *
 *   Uses page.route() browser-layer mock per 57.1 v2 D19 + 57.3 D13 pattern.
 *
 * Created: 2026-05-07 (Sprint 57.4 Day 4)
 */

import { expect, test } from "@playwright/test";

const TENANT_LIST_ENDPOINT = "**/api/v1/admin/tenants?**";
const TENANT_GET_ENDPOINT = "**/api/v1/admin/tenants/**";

const baseTenantA = {
  id: "00000000-0000-4000-8000-0000000000a1",
  code: "ACME_E2E",
  display_name: "Acme E2E Corp",
  state: "active",
  plan: "enterprise",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-05-07T00:00:00Z",
};

const baseTenantB = {
  id: "00000000-0000-4000-8000-0000000000b2",
  code: "REQ_PENDING",
  display_name: "Requested Pending",
  state: "requested",
  plan: "enterprise",
  created_at: "2026-02-01T00:00:00Z",
  updated_at: "2026-05-07T00:00:00Z",
};

test.describe("Sprint 57.4 US-5 — Admin Tenants Console list e2e", () => {
  test("happy path: page renders mocked rows + state badges", async ({ page }) => {
    await page.route(TENANT_LIST_ENDPOINT, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [baseTenantA, baseTenantB],
          total: 2,
          limit: 50,
          offset: 0,
        }),
      });
    });

    await page.goto("/admin-tenants");

    await expect(page.getByRole("heading", { name: "Admin Tenants Console" })).toBeVisible();
    await expect(page.getByText("ACME_E2E")).toBeVisible();
    await expect(page.getByText("REQ_PENDING")).toBeVisible();
    // Badges are <span> elements. The state dropdown also has lowercase
    // option values, so disambiguate via the table cell role + first match.
    await expect(page.locator("td span").filter({ hasText: "active" })).toBeVisible();
    await expect(page.locator("td span").filter({ hasText: "requested" })).toBeVisible();
  });

  test("filter: select state=ACTIVE triggers second GET with state filter", async ({ page }) => {
    let lastRequestUrl = "";
    await page.route(TENANT_LIST_ENDPOINT, async (route) => {
      lastRequestUrl = route.request().url();
      const url = new URL(lastRequestUrl);
      const stateFilter = url.searchParams.get("state");
      const items = stateFilter === "active" ? [baseTenantA] : [baseTenantA, baseTenantB];
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items,
          total: items.length,
          limit: 50,
          offset: 0,
        }),
      });
    });

    await page.goto("/admin-tenants");
    await expect(page.getByText("REQ_PENDING")).toBeVisible();

    // First select is the State dropdown.
    const stateSelect = page.getByRole("combobox").nth(0);
    await stateSelect.selectOption("active");
    await page.getByRole("button", { name: "Apply" }).click();

    await expect.poll(() => lastRequestUrl).toContain("state=active");
    await expect(page.getByText("REQ_PENDING")).not.toBeVisible();
    await expect(page.getByText("ACME_E2E")).toBeVisible();
  });

  test("click View navigates to /tenant-settings/?tenant_id=...", async ({ page }) => {
    await page.route(TENANT_LIST_ENDPOINT, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [baseTenantA],
          total: 1,
          limit: 50,
          offset: 0,
        }),
      });
    });

    // Mock the GET /{id} so the destination page also responds (otherwise
    // tenant-settings page would show error from real backend miss).
    await page.route(TENANT_GET_ENDPOINT, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ...baseTenantA,
          provisioning_progress: {},
          onboarding_progress: {},
          meta_data: {},
        }),
      });
    });

    await page.goto("/admin-tenants");
    await expect(page.getByText("ACME_E2E")).toBeVisible();

    await page.getByRole("button", { name: "View" }).click();

    await expect(page).toHaveURL(/\/tenant-settings\/?\?tenant_id=/);
    await expect(page.getByRole("heading", { name: "Tenant Settings" })).toBeVisible();
  });

  test("empty state: items=[] shows No tenants match + Reset Filters button", async ({ page }) => {
    await page.route(TENANT_LIST_ENDPOINT, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [],
          total: 0,
          limit: 50,
          offset: 0,
        }),
      });
    });

    await page.goto("/admin-tenants");
    await expect(page.getByText(/No tenants match/)).toBeVisible();
    await expect(page.getByRole("button", { name: "Reset Filters" })).toBeVisible();
  });
});
