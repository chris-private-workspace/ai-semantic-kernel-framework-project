/**
 * File: frontend/tests/e2e/connectivity/connectivity.spec.ts
 * Purpose: Opt-in end-to-end connectivity smoke — real backend + real dev-login,
 * then visit every active page and assert the shell renders without console errors.
 * Category: Frontend / e2e / connectivity (Sprint 57.13 US-A5)
 * Scope: Phase 57 / Sprint 57.13 / Day 3 / US-A5
 *
 * Description:
 *   Unlike the rest of the e2e suite (which mocks /api/v1/* at page.route()),
 *   this spec hits a *live* backend so it can prove the full auth + page-load
 *   path actually works front-to-back. It is therefore opt-in: it is skipped
 *   unless RUN_CONNECTIVITY is set in the environment, so CI / `npm run test:e2e`
 *   stay hermetic.
 *
 *   Run it manually after `python scripts/dev.py start` (backend on :8000,
 *   frontend on :3007 via playwright.config webServer or already running):
 *
 *       RUN_CONNECTIVITY=1 npm run test:e2e -- connectivity
 *
 *   Flow: POST /api/v1/auth/dev-login (sets the v2_jwt cookie on the browser
 *   context) → for each of the 9 active routes: page.goto, assert we landed on
 *   the page (not bounced to /auth/login), assert <div data-testid="app-shell">
 *   rendered, assert zero console.error.
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 3)
 *
 * Related:
 *   - backend/src/api/v1/auth.py (POST /auth/dev-login)
 *   - frontend/src/routes.config.ts (active page list — keep in sync)
 *   - frontend/src/components/AppShellV2.tsx (data-testid="app-shell")
 *   - frontend/tests/e2e/smoke.spec.ts (hermetic bootstrap smoke — always runs)
 */

import { expect, test } from "@playwright/test";

// Active pages per routes.config.ts (active: true). Keep in sync when a page ships.
const ACTIVE_ROUTES = [
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

test.describe("Sprint 57.13 US-A5 — full-stack connectivity (opt-in)", () => {
  test.skip(!process.env.RUN_CONNECTIVITY, "Set RUN_CONNECTIVITY=1 to run against a live backend");

  test("dev-login then every active page renders without console errors", async ({ page }) => {
    // 1) Authenticate via dev fake-login — sets v2_jwt cookie on the context.
    const loginResp = await page.request.post("/api/v1/auth/dev-login");
    expect(loginResp.ok(), `dev-login failed: ${loginResp.status()}`).toBeTruthy();

    // 2) Walk every active page.
    for (const path of ACTIVE_ROUTES) {
      const consoleErrors: string[] = [];
      const onConsole = (msg: { type: () => string; text: () => string }) => {
        if (msg.type() === "error") consoleErrors.push(msg.text());
      };
      page.on("console", onConsole);

      await page.goto(path, { waitUntil: "networkidle" });

      // Not bounced to /auth/login → the auth cookie was accepted.
      expect(page.url(), `${path} redirected to login`).not.toContain("/auth/login");
      // The authenticated shell rendered.
      await expect(page.locator('[data-testid="app-shell"]'), `${path} shell missing`).toBeVisible();
      // No console errors on load.
      expect(consoleErrors, `${path} console errors: ${consoleErrors.join(" | ")}`).toHaveLength(0);

      page.off("console", onConsole);
    }
  });
});
