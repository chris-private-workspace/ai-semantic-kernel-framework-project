/**
 * File: frontend/tests/e2e/cost-dashboard/cost_dashboard.spec.ts
 * Purpose: Playwright e2e — admin loads /cost-dashboard with mocked 56.3 cost-summary endpoint.
 * Category: Frontend / e2e / cost-dashboard
 * Scope: Phase 57 / Sprint 57.1 US-5
 *
 * Description:
 *   Validates the Cost Dashboard (57.1 US-2):
 *     1. Happy path: admin loads /cost-dashboard?tenant_id=... → fetches
 *        56.3 cost-summary → renders MonthPicker + total + breakdown table.
 *     2. Error path: backend 500 → error message + retry button → mock 200
 *        → click retry → success.
 *
 *   Uses page.route() browser-layer mock per D19 (mirrors 53.6 governance
 *   approvals.spec.ts pattern; no real backend / no admin auth fixture).
 *
 * Created: 2026-05-06 (Sprint 57.1 Day 4)
 */

import { expect, test } from "@playwright/test";

const TENANT_ID = "00000000-0000-4000-8000-000000000099";
const COST_ENDPOINT = `**/api/v1/admin/tenants/${TENANT_ID}/cost-summary**`;

const mockCostSummary = {
  tenant_id: TENANT_ID,
  month: new Date().toISOString().substring(0, 7),
  total_cost_usd: "12.3456",
  by_type: {
    llm_input: {
      "azure_openai_gpt-5.4": { quantity: "10000", total_cost_usd: "10.0000", entry_count: 5 },
    },
    llm_output: {
      "azure_openai_gpt-5.4": { quantity: "1000", total_cost_usd: "2.0000", entry_count: 5 },
    },
    tool: {
      salesforce_query: { quantity: "10", total_cost_usd: "0.3456", entry_count: 10 },
    },
  },
};

test.describe("Sprint 57.1 US-5 — Cost Dashboard e2e", () => {
  test("happy path: admin loads dashboard, sees total + breakdown", async ({ page }) => {
    await page.route(COST_ENDPOINT, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockCostSummary),
      });
    });

    await page.goto(`/cost-dashboard?tenant_id=${TENANT_ID}`);

    await expect(page.getByRole("heading", { name: "Cost Dashboard" })).toBeVisible();
    await expect(page.getByLabel("Select month")).toBeVisible();
    // Total cost label + $amount live in same <p> but Playwright's getByText
    // resolves to the inner <strong> first; assert each visible separately.
    await expect(page.getByText(/Total cost/)).toBeVisible();
    await expect(page.getByText("$12.3456")).toBeVisible();

    // 3 breakdown rows: llm_input + llm_output + tool
    await expect(page.getByRole("row")).toHaveCount(4); // header + 3 data rows
    await expect(page.getByText("azure_openai_gpt-5.4").first()).toBeVisible();
    await expect(page.getByText("salesforce_query")).toBeVisible();
  });

  test("error path: backend 500 shows retry; mock 200 on retry recovers", async ({ page }) => {
    // Sprint 57.9 US-6 Day 4: TanStack Query under React 18 StrictMode may
    // fire the initial query twice (mount-unmount-mount dev double-render);
    // gate the success branch on an explicit retryClicked flag so the mock
    // returns 500 for ALL pre-click requests + 200 for any post-click request.
    let retryClicked = false;
    await page.route(COST_ENDPOINT, async (route) => {
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
          body: JSON.stringify(mockCostSummary),
        });
      }
    });

    await page.goto(`/cost-dashboard?tenant_id=${TENANT_ID}`);

    // First load fails — error UX visible
    await expect(page.getByText(/Error:/)).toBeVisible();
    const retryButton = page.getByRole("button", { name: "Retry" });
    await expect(retryButton).toBeVisible();

    // Click retry → second call succeeds → table appears
    retryClicked = true;
    await retryButton.click();
    await expect(page.getByText("$12.3456")).toBeVisible();
  });
});
