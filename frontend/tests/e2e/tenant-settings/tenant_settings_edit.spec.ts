/**
 * File: frontend/tests/e2e/tenant-settings/tenant_settings_edit.spec.ts
 * Purpose: Playwright e2e — admin edits tenant settings via 57.3 PATCH endpoint.
 * Category: Frontend / e2e / tenant-settings
 * Scope: Phase 57 / Sprint 57.3 US-5
 *
 * Description:
 *   Validates the Tenant Settings Edit Form (57.3 US-2 + US-4):
 *     1. Happy path: admin clicks Edit, modifies display_name, saves → PATCH
 *        endpoint returns updated tenant → UI shows new value in View mode.
 *     2. Invalid JSON path: admin edits meta_data textarea with malformed
 *        JSON → blur triggers validation → red error + Save button disabled.
 *
 *   Uses page.route() browser-layer mock per 57.1 v2 D19 pattern.
 *
 * Created: 2026-05-07 (Sprint 57.3 Day 4)
 */

import { expect, test } from "@playwright/test";

import { seedAuthJwt } from "../fixtures/auth-fixtures";

const TENANT_ID = "00000000-0000-4000-8000-000000000099";
const TENANT_ENDPOINT = `**/api/v1/admin/tenants/${TENANT_ID}`;

const initialTenant = {
  id: TENANT_ID,
  code: "ACME_E2E",
  display_name: "Acme E2E Corp",
  state: "active",
  plan: "enterprise",
  provisioning_progress: {},
  onboarding_progress: {},
  meta_data: { region: "us-west" },
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-05-07T00:00:00Z",
};

const renamedTenant = {
  ...initialTenant,
  display_name: "Renamed E2E Corp",
  updated_at: "2026-05-07T01:00:00Z",
};

test.describe("Sprint 57.3 US-5 — Tenant Settings Edit Form e2e", () => {
  // Sprint 57.13 US-A2: the page is <RequireAuth>-gated + reads authStore.tenant.id.
  test.beforeEach(async ({ page }) => {
    await seedAuthJwt(page, { tenantId: TENANT_ID });
  });

  test("happy path: edit display_name, save, see new value in View", async ({ page }) => {
    // Sprint 57.9 US-6 Day 4: post-mutation invalidation triggers a refetch
    // (useTenantSettingsSave.onSuccess invalidates TENANT_SETTINGS_QUERY_KEY_BASE),
    // so subsequent GETs after the PATCH must return the renamed tenant for
    // the View to reflect the change. Track patchSeen so:
    //   GET pre-PATCH → initialTenant
    //   PATCH → renamedTenant
    //   GET post-PATCH (invalidate refetch) → renamedTenant
    let patchSeen = false;
    await page.route(TENANT_ENDPOINT, async (route) => {
      const method = route.request().method();
      if (method === "PATCH") {
        patchSeen = true;
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(renamedTenant),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(patchSeen ? renamedTenant : initialTenant),
        });
      }
    });

    await page.goto(`/tenant-settings?tenant_id=${TENANT_ID}`);

    // Wait for view to render initial data.
    await expect(page.getByText("Acme E2E Corp")).toBeVisible();

    // Click Edit → switch to form
    await page.getByRole("button", { name: "Edit" }).click();

    // Edit display_name input (D13: use Playwright getByRole textbox.nth(0) — getByDisplayValue not in Playwright API).
    const input = page.getByRole("textbox").nth(0);
    await input.fill("Renamed E2E Corp");

    // Click Save → PATCH endpoint mocked to return renamedTenant + onDone() switches back to View.
    await page.getByRole("button", { name: "Save" }).click();

    // After save, View should render with new display_name (from PATCH response in store).
    await expect(page.getByText("Renamed E2E Corp")).toBeVisible();
  });

  test("invalid JSON in meta_data textarea shows error + disables Save", async ({ page }) => {
    await page.route(TENANT_ENDPOINT, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(initialTenant),
      });
    });

    await page.goto(`/tenant-settings?tenant_id=${TENANT_ID}`);
    await expect(page.getByText("Acme E2E Corp")).toBeVisible();

    await page.getByRole("button", { name: "Edit" }).click();

    // Find the meta_data textarea (only textarea on the form).
    const textarea = page.getByRole("textbox").nth(1); // first is display_name input, second is meta_data textarea
    await textarea.fill("{not valid json");
    await textarea.blur();

    // Invalid JSON message visible
    await expect(page.getByText(/Invalid JSON/)).toBeVisible();

    // Save button should be disabled when JSON is invalid.
    const saveBtn = page.getByRole("button", { name: "Save" });
    await expect(saveBtn).toBeDisabled();
  });
});
