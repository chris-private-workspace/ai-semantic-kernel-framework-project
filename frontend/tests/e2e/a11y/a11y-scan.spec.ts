/**
 * File: frontend/tests/e2e/a11y/a11y-scan.spec.ts
 * Purpose: Playwright + axe-core accessibility scan — every shipped page must have 0 critical/serious violations.
 * Category: Frontend / e2e / a11y
 * Scope: Phase 57 / Sprint 57.13 US-B6
 *
 * Description:
 *   Runs axe-core (@axe-core/playwright AxeBuilder) against:
 *     - the 9 active routes (sidebar + AppShellV2 shell rendered; data fetches
 *       are mocked to 503 → accessible <ErrorRetry> error state, which axe also
 *       scans — error UIs need a11y too), with /api/v1/auth/me mocked so
 *       <RequireAuth> lets the shell render
 *     - /auth/login (anonymous) + /auth/callback?error=… (error UI; the ?error
 *       branch short-circuits before bootstrap, so it doesn't redirect)
 *   Assertion: 0 violations with impact "critical" or "serious". moderate/minor
 *   are logged (console.warn) but don't fail — baseline scope.
 *
 *   Self-contained: page.route() mocks (per feedback_e2e_network_mocking_pattern.md).
 *   Every /api/v1/** request is intercepted — /auth/me to 200, everything else to
 *   503 — so the test is hermetic whether or not a real backend happens to be
 *   reachable on :8000. (Originally only /auth/me was mocked, so data endpoints
 *   went through the Vite proxy; when a backend was running it returned 401 →
 *   fetchWithAuth's handleAuthExpired → window.location='/auth/login' → the shell
 *   never rendered. Sprint 57.14 AD-Frontend-E2E-Sweep made it hermetic.)
 *   The Vite dev server is auto-started by playwright.config.ts webServer.
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 8)
 * Last Modified: 2026-05-11
 *
 * Modification History (newest-first):
 *   - 2026-05-11: Sprint 57.16 — /chat-v2 color-contrast re-enabled (ChatLayout + InputBar migrated to AA tokens); all 9 gated routes + auth pages now full axe rule set (AD-Inline-Style-Cleanup-Sweep-Round2)
 *   - 2026-05-11: Sprint 57.15 — color-contrast re-enabled for every route except /chat-v2 (ChatLayout placeholder text still hardcoded-hex inline, deferred to AD-Inline-Style-Cleanup-Sweep-Round2)
 *   - 2026-05-10: Sprint 57.14 US-A2 — mock all /api/v1/** (data → 503) so the gated-pages scan is hermetic regardless of a running backend; wait for networkidle before axe to avoid mid-scan navigation
 *   - 2026-05-10: Initial creation (Sprint 57.13 Day 8)
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

/**
 * Make the test hermetic: every /api/v1/** request is intercepted.
 * `/auth/me` gets the supplied identity (200) or null (401); all other API
 * calls (the pages' data fetches) get a deterministic 503 → the page renders
 * its <ErrorRetry> state (which axe also scans), and crucially never a 401 —
 * a 401 would trip fetchWithAuth's handleAuthExpired() → window.location to
 * /auth/login, so the shell would never render. Register the catch-all FIRST
 * and the /auth/me handler SECOND so the more-specific (last-registered) one
 * wins for /auth/me and the catch-all covers everything else.
 */
async function mockApi(page: Page, authMe: object | null): Promise<void> {
  await page.route("**/api/v1/**", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ detail: "service unavailable (e2e mock)" }),
    }),
  );
  await page.route("**/api/v1/auth/me", (route) =>
    authMe
      ? route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(authMe) })
      : route.fulfill({ status: 401, contentType: "application/json", body: JSON.stringify({ detail: "anonymous" }) }),
  );
}

async function scan(page: Page, label: string): Promise<void> {
  // Sprint 57.16 (AD-Inline-Style-Cleanup-Sweep-Round2): /chat-v2 no longer
  // needs the color-contrast escape hatch — ChatLayout + InputBar were
  // migrated from inline `#7c8696` hex to `text-muted-foreground` (≈ 4.6:1 on
  // bg-muted; ≈ 4.9:1 on white — AA-compliant). All 9 gated routes + the auth
  // pages now run the full axe rule set with no per-route disable.
  const builder = new AxeBuilder({ page });
  const results = await builder.analyze();
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
    await mockApi(page, mockAuthMe);
    for (const route of GATED_ROUTES) {
      await page.goto(route);
      await expect(page.getByTestId("app-shell")).toBeVisible();
      // Let any client-side redirect (e.g. /verification → /verification/recent)
      // + the page's mocked data fetches settle before axe injects/evaluates —
      // otherwise "Execution context was destroyed, most likely because of a
      // navigation" if the SPA route changes mid-scan.
      await page.waitForLoadState("networkidle");
      // Sprint 57.16: all 9 gated routes (incl /chat-v2) run the full axe
      // rule set — no per-route disable.
      await scan(page, route);
    }
  });

  test("auth pages have 0 critical/serious a11y violations", async ({ page }) => {
    await mockApi(page, null);

    await page.goto("/auth/login");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await page.waitForLoadState("networkidle");
    await scan(page, "/auth/login");

    await page.goto("/auth/callback?error=" + encodeURIComponent("test error from IdP"));
    await expect(page.getByRole("alert")).toBeVisible();
    await page.waitForLoadState("networkidle");
    await scan(page, "/auth/callback?error");
  });
});
