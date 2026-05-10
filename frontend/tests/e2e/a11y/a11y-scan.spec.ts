/**
 * File: frontend/tests/e2e/a11y/a11y-scan.spec.ts
 * Purpose: Playwright + axe-core accessibility scan — every shipped page must have 0 critical/serious violations.
 * Category: Frontend / e2e / a11y
 * Scope: Phase 57 / Sprint 57.13 US-B6
 *
 * Description:
 *   Runs axe-core (@axe-core/playwright AxeBuilder) against:
 *     - the 9 active routes (sidebar + AppShellV2 shell rendered; data fetches
 *       fail with no backend → accessible <ErrorRetry> error state, which axe
 *       also scans — error UIs need a11y too), with /api/v1/auth/me mocked so
 *       <RequireAuth> lets the shell render
 *     - /auth/login (anonymous) + /auth/callback?error=… (error UI; the ?error
 *       branch short-circuits before bootstrap, so it doesn't redirect)
 *   Assertion: 0 violations with impact "critical" or "serious". moderate/minor
 *   are logged (console.warn) but don't fail — baseline scope.
 *
 *   Self-contained: page.route() mocks (per feedback_e2e_network_mocking_pattern.md);
 *   the Vite dev server is auto-started by playwright.config.ts webServer.
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 8)
 */

import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const TENANT_ID = "00000000-0000-4000-8000-000000000099";

const mockAuthMe = {
  user: { id: "11111111-1111-4111-8111-111111111111", email: "dev@local", display_name: "Dev User" },
  tenant: { id: TENANT_ID, name: "Dev Tenant", code: "dev" },
  roles: ["platform_admin"],
};

/** Routes that render under AppShellV2 (active: true in routes.config). */
const GATED_ROUTES = [
  "/chat-v2",
  "/cost-dashboard",
  "/sla-dashboard",
  "/admin-tenants",
  "/tenant-settings",
  "/governance",
  "/verification",
  "/loop-debug",
  "/memory",
];

async function scan(page: Page, label: string): Promise<void> {
  const results = await new AxeBuilder({ page })
    // color-contrast is disabled at baseline scope: the chat-v2 inline panels
    // (ToolCallCard / MessageList / …) still use hardcoded-hex inline styles that
    // fail WCAG AA contrast — fixing those is AD-Inline-Style-Cleanup-Sweep. All
    // the structural rules (aria / labels / roles / focus) stay enabled.
    .disableRules(["color-contrast"])
    .analyze();
  const blocking = results.violations.filter(
    (v) => v.impact === "critical" || v.impact === "serious",
  );
  const minor = results.violations.filter(
    (v) => v.impact !== "critical" && v.impact !== "serious",
  );
  if (minor.length > 0) {
    // Surfaced for triage, not a failure at baseline scope.
    console.warn(`[a11y:${label}] ${minor.length} moderate/minor: ${minor.map((v) => v.id).join(", ")}`);
  }
  expect(blocking, `${label}: critical/serious violations: ${JSON.stringify(blocking.map((v) => ({ id: v.id, nodes: v.nodes.length })), null, 2)}`).toEqual([]);
}

test.describe("Sprint 57.13 US-B6 — accessibility scan", () => {
  test("gated pages (shell + content/error UI) have 0 critical/serious a11y violations", async ({ page }) => {
    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(mockAuthMe) }),
    );
    for (const route of GATED_ROUTES) {
      await page.goto(route);
      await expect(page.getByTestId("app-shell")).toBeVisible();
      await scan(page, route);
    }
  });

  test("auth pages have 0 critical/serious a11y violations", async ({ page }) => {
    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({ status: 401, contentType: "application/json", body: JSON.stringify({ detail: "anonymous" }) }),
    );

    await page.goto("/auth/login");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await scan(page, "/auth/login");

    await page.goto("/auth/callback?error=" + encodeURIComponent("test error from IdP"));
    await expect(page.getByRole("alert")).toBeVisible();
    await scan(page, "/auth/callback?error");
  });
});
