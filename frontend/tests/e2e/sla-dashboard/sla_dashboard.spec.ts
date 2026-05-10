/**
 * File: frontend/tests/e2e/sla-dashboard/sla_dashboard.spec.ts
 * Purpose: Playwright e2e — admin loads /sla-dashboard with mocked 56.3 sla-report endpoint.
 * Category: Frontend / e2e / sla-dashboard
 * Scope: Phase 57 / Sprint 57.1 US-5
 *
 * Description:
 *   Validates the SLA Dashboard (57.1 US-3):
 *     1. Happy path: admin loads /sla-dashboard?tenant_id=... → fetches
 *        56.3 sla-report → renders MonthPicker + violations badge + 6 metric cards.
 *     2. Error path: backend 500 → error message + retry button → mock 200
 *        → click retry → success.
 *
 *   Uses page.route() browser-layer mock per D19 (mirrors cost_dashboard.spec.ts).
 *
 * Created: 2026-05-06 (Sprint 57.1 Day 4)
 */

import { expect, test } from "@playwright/test";

import { seedAuthJwt } from "../fixtures/auth-fixtures";

const TENANT_ID = "00000000-0000-4000-8000-000000000099";
const SLA_ENDPOINT = `**/api/v1/admin/tenants/${TENANT_ID}/sla-report**`;

const mockSLAReport = {
  tenant_id: TENANT_ID,
  month: new Date().toISOString().substring(0, 7),
  availability_pct: 99.7,
  api_p99_ms: 850,
  loop_simple_p99_ms: 4200,
  loop_medium_p99_ms: 28000,
  loop_complex_p99_ms: 110000,
  hitl_queue_notif_p99_ms: 45000,
  violations_count: 0,
};

test.describe("Sprint 57.1 US-5 — SLA Dashboard e2e", () => {
  // Sprint 57.13 US-A2: the page is <RequireAuth>-gated + reads authStore.tenant.id.
  test.beforeEach(async ({ page }) => {
    await seedAuthJwt(page, { tenantId: TENANT_ID });
  });

  test("happy path: admin loads dashboard, sees violations badge + 6 metric cards", async ({ page }) => {
    await page.route(SLA_ENDPOINT, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockSLAReport),
      });
    });

    await page.goto(`/sla-dashboard?tenant_id=${TENANT_ID}`);

    await expect(page.getByRole("heading", { name: "SLA Dashboard" })).toBeVisible();
    await expect(page.getByLabel("Select month")).toBeVisible();
    await expect(page.getByTestId("violations-badge")).toContainText("Violations: 0");

    // 6 metric cards via data-testid
    await expect(page.getByTestId("sla-card-availability")).toBeVisible();
    await expect(page.getByTestId("sla-card-api-p99")).toBeVisible();
    await expect(page.getByTestId("sla-card-loop-simple-p99")).toBeVisible();
    await expect(page.getByTestId("sla-card-loop-medium-p99")).toBeVisible();
    await expect(page.getByTestId("sla-card-loop-complex-p99")).toBeVisible();
    await expect(page.getByTestId("sla-card-hitl-queue-notif-p99")).toBeVisible();

    // Availability is 99.7% which passes Standard 99.5% threshold
    await expect(page.getByTestId("sla-card-availability")).toContainText("PASS");
  });

  test("error path: backend 500 shows retry; mock 200 on retry recovers", async ({ page }) => {
    // Sprint 57.9 US-6 Day 4: TanStack StrictMode double-render fix — gate
    // success on retryClicked instead of firstCall flag (mirror cost-dashboard).
    let retryClicked = false;
    await page.route(SLA_ENDPOINT, async (route) => {
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
          body: JSON.stringify(mockSLAReport),
        });
      }
    });

    await page.goto(`/sla-dashboard?tenant_id=${TENANT_ID}`);

    await expect(page.getByText(/Error:/)).toBeVisible();
    const retryButton = page.getByRole("button", { name: "Retry" });
    await expect(retryButton).toBeVisible();

    retryClicked = true;
    await retryButton.click();
    await expect(page.getByTestId("violations-badge")).toContainText("Violations: 0");
  });
});
