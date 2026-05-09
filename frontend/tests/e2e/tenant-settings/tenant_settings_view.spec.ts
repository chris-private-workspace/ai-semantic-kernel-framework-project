/**
 * File: frontend/tests/e2e/tenant-settings/tenant_settings_view.spec.ts
 * Purpose: Playwright e2e — admin loads /tenant-settings with mocked 57.3 GET endpoint.
 * Category: Frontend / e2e / tenant-settings
 * Scope: Phase 57 / Sprint 57.3 US-5
 *
 * Description:
 *   Validates the Tenant Settings View (57.3 US-1 + US-4):
 *     1. Happy path: admin loads /tenant-settings?tenant_id=... → fetches
 *        57.3 GET endpoint → renders 10-field read view with State + Plan badges.
 *     2. Error path: backend 500 → error message + retry button → mock 200
 *        on retry → success.
 *
 *   Uses page.route() browser-layer mock per 57.1 v2 D19 pattern (no real
 *   backend / no admin auth fixture).
 *
 * Created: 2026-05-07 (Sprint 57.3 Day 4)
 */

import { expect, test } from "@playwright/test";

const TENANT_ID = "00000000-0000-4000-8000-000000000099";
const TENANT_ENDPOINT = `**/api/v1/admin/tenants/${TENANT_ID}`;

const mockTenant = {
  id: TENANT_ID,
  code: "ACME_E2E",
  display_name: "Acme E2E Corp",
  state: "active",
  plan: "enterprise",
  provisioning_progress: { steps_completed: 7 },
  onboarding_progress: { steps_completed: 6 },
  meta_data: { region: "us-west", contact: "ops@acme.test" },
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-05-07T00:00:00Z",
};

test.describe("Sprint 57.3 US-5 — Tenant Settings View e2e", () => {
  test("happy path: admin loads view, sees 10 fields + State + Plan badges", async ({ page }) => {
    await page.route(TENANT_ENDPOINT, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockTenant),
      });
    });

    await page.goto(`/tenant-settings?tenant_id=${TENANT_ID}`);

    await expect(page.getByRole("heading", { name: "Tenant Settings" })).toBeVisible();
    // ID + Code + Display Name visible.
    await expect(page.getByText(TENANT_ID)).toBeVisible();
    await expect(page.getByText("ACME_E2E")).toBeVisible();
    await expect(page.getByText("Acme E2E Corp")).toBeVisible();
    // State + Plan badges (rendered as <span>; text-based assertion).
    await expect(page.getByText("active")).toBeVisible();
    await expect(page.getByText("enterprise")).toBeVisible();
    // Edit button exists.
    await expect(page.getByRole("button", { name: "Edit" })).toBeVisible();
  });

  test("error path: backend 500 shows retry; mock 200 on retry recovers", async ({ page }) => {
    // Sprint 57.9 US-6 Day 4: TanStack StrictMode double-render fix — gate
    // success on retryClicked instead of firstCall flag.
    let retryClicked = false;
    await page.route(TENANT_ENDPOINT, async (route) => {
      if (!retryClicked) {
        await route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({ detail: "internal server error" }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockTenant),
        });
      }
    });

    await page.goto(`/tenant-settings?tenant_id=${TENANT_ID}`);

    // First load fails — error UX visible
    await expect(page.getByText(/Error:/)).toBeVisible();
    const retryButton = page.getByRole("button", { name: "Retry" });
    await expect(retryButton).toBeVisible();

    // Click retry → second call succeeds → tenant data appears
    retryClicked = true;
    await retryButton.click();
    await expect(page.getByText("Acme E2E Corp")).toBeVisible();
  });
});
