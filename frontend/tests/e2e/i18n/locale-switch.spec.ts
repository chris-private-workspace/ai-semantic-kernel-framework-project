/**
 * File: frontend/tests/e2e/i18n/locale-switch.spec.ts
 * Purpose: Playwright e2e — UserMenu locale switcher flips sidebar labels and persists across reload.
 * Category: Frontend / e2e / i18n
 * Scope: Phase 57 / Sprint 57.13 US-B5
 *
 * Description:
 *   Self-contained (no real backend): mocks GET /api/v1/auth/me → authenticated
 *   so <RequireAuth> renders the shell, and the cost-summary endpoint so the
 *   page doesn't error. Then:
 *     1. /cost-dashboard renders with English sidebar (browser default = en).
 *     2. Open UserMenu → click "繁體中文" → sidebar nav shows zh-TW labels.
 *     3. Reload → still zh-TW (localStorage `ipa-locale` persisted by the detector).
 *
 *   Mock pattern mirrors cost-dashboard/cost_dashboard.spec.ts (page.route()
 *   browser-layer interception per feedback_e2e_network_mocking_pattern.md).
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 7)
 */

import { expect, test } from "@playwright/test";

const TENANT_ID = "00000000-0000-4000-8000-000000000099";

const mockAuthMe = {
  user: { id: "11111111-1111-4111-8111-111111111111", email: "dev@local", display_name: "Dev User" },
  tenant: { id: TENANT_ID, name: "Dev Tenant", code: "dev" },
  roles: ["platform_admin"],
};

const mockCostSummary = {
  tenant_id: TENANT_ID,
  month: new Date().toISOString().substring(0, 7),
  total_cost_usd: "0.0000",
  by_type: { llm_input: {}, llm_output: {}, tool: {} },
};

test.describe("Sprint 57.13 US-B5 — i18n locale switch e2e", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(mockAuthMe) }),
    );
    await page.route("**/api/v1/admin/tenants/**/cost-summary**", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(mockCostSummary) }),
    );
  });

  test("switching to zh-TW translates the sidebar and survives reload", async ({ page }) => {
    await page.goto("/cost-dashboard");
    await expect(page.getByTestId("app-shell")).toBeVisible();

    // The sidebar is the only <aside> → role=complementary (stable across locales,
    // unlike its aria-label which itself gets translated).
    const sidebar = page.getByRole("complementary");
    await expect(sidebar.getByRole("link", { name: "Cost Dashboard" })).toBeVisible();

    // Open the user menu and pick Traditional Chinese (native label is locale-independent).
    await page.getByRole("button", { name: /user menu/i }).click();
    await page.getByRole("menuitem", { name: "繁體中文" }).click();

    // Sidebar nav now renders zh-TW labels.
    await expect(sidebar.getByRole("link", { name: "成本儀表板" })).toBeVisible();
    await expect(sidebar.getByRole("link", { name: "Cost Dashboard" })).toHaveCount(0);

    // Reload — the i18next detector reads localStorage `ipa-locale`, so still zh-TW.
    await page.reload();
    await expect(page.getByTestId("app-shell")).toBeVisible();
    await expect(
      page.getByRole("complementary").getByRole("link", { name: "成本儀表板" }),
    ).toBeVisible();
  });
});
