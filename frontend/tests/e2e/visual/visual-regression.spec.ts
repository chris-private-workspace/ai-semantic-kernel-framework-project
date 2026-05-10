/**
 * File: frontend/tests/e2e/visual/visual-regression.spec.ts
 * Purpose: Playwright screenshot diffs for the shell + login + 4 representative pages (catch unintended visual drift).
 * Category: Frontend / e2e / visual
 * Scope: Phase 57 / Sprint 57.13 US-B8
 *
 * Description:
 *   `expect(page).toHaveScreenshot(...)` against fixed-data renders of:
 *     1. AppShellV2 with an empty <main> (the shell chrome: sidebar + header + UserMenu)
 *     2. /auth/login (the rewritten AuthShell + Card)
 *     3. /cost-dashboard (mocked cost-summary)
 *     4. /governance (mocked approvals list)
 *     5. /verification/recent (mocked verification list)
 *     6. /admin-tenants (mocked tenants list)
 *   All data + /auth/me are page.route()-mocked so the renders are deterministic.
 *
 *   ⚠️ SKIPPED BY DEFAULT — `test.skip(!process.env.RUN_VISUAL, ...)`. Screenshot
 *   baselines (`*-snapshots/*.png`) must be generated on the CI runner (Linux
 *   Chromium), NOT a dev machine — font rendering / DPI differ, so locally-made
 *   baselines would all mismatch. To enable: on CI, run
 *   `RUN_VISUAL=1 npx playwright test visual --update-snapshots`, commit the
 *   generated `-snapshots/` dir + `.gitattributes` (`*.png binary`), then drop
 *   the skip. Tracked: AD-Visual-Baseline-Generation (carryover).
 *
 *   Mock pattern mirrors cost_dashboard.spec.ts (page.route() browser-layer).
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 9)
 */

import { expect, test, type Page } from "@playwright/test";

const RUN_VISUAL = Boolean(process.env.RUN_VISUAL);

const TENANT_ID = "00000000-0000-4000-8000-000000000099";

const mockAuthMe = {
  user: { id: "11111111-1111-4111-8111-111111111111", email: "dev@local", display_name: "Dev User" },
  tenant: { id: TENANT_ID, name: "Dev Tenant", code: "dev" },
  roles: ["platform_admin"],
};

const SHOT_OPTS = { fullPage: true as const, animations: "disabled" as const };

async function fulfillJson(page: Page, glob: string, body: unknown): Promise<void> {
  await page.route(glob, (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) }),
  );
}

test.describe("Sprint 57.13 US-B8 — visual regression", () => {
  test.skip(
    !RUN_VISUAL,
    "Visual baselines not committed yet — generate on CI (RUN_VISUAL=1 ... --update-snapshots) then drop this skip. See AD-Visual-Baseline-Generation.",
  );

  test.beforeEach(async ({ page }) => {
    await fulfillJson(page, "**/api/v1/auth/me", mockAuthMe);
  });

  test("AppShellV2 chrome (empty main)", async ({ page }) => {
    await page.goto("/loop-debug"); // a light gated page; we screenshot the shell, not its content
    await expect(page.getByTestId("app-shell")).toBeVisible();
    await expect(page).toHaveScreenshot("app-shell.png", SHOT_OPTS);
  });

  test("/auth/login", async ({ page }) => {
    await page.goto("/auth/login");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page).toHaveScreenshot("auth-login.png", SHOT_OPTS);
  });

  test("/cost-dashboard", async ({ page }) => {
    await fulfillJson(page, "**/api/v1/admin/tenants/**/cost-summary**", {
      tenant_id: TENANT_ID,
      month: "2026-05",
      total_cost_usd: "12.3456",
      by_type: { llm_input: {}, llm_output: {}, tool: {} },
    });
    await page.goto("/cost-dashboard");
    await expect(page.getByTestId("app-shell")).toBeVisible();
    await expect(page).toHaveScreenshot("cost-dashboard.png", SHOT_OPTS);
  });

  test("/governance", async ({ page }) => {
    await fulfillJson(page, "**/api/v1/governance/approvals**", { approvals: [] });
    await page.goto("/governance");
    await expect(page.getByTestId("app-shell")).toBeVisible();
    await expect(page).toHaveScreenshot("governance.png", SHOT_OPTS);
  });

  test("/verification/recent", async ({ page }) => {
    await fulfillJson(page, "**/api/v1/verification/recent**", { items: [] });
    await page.goto("/verification/recent");
    await expect(page.getByTestId("app-shell")).toBeVisible();
    await expect(page).toHaveScreenshot("verification-recent.png", SHOT_OPTS);
  });

  test("/admin-tenants", async ({ page }) => {
    await fulfillJson(page, "**/api/v1/admin/tenants**", { items: [], total: 0, page: 1, page_size: 20 });
    await page.goto("/admin-tenants");
    await expect(page.getByTestId("app-shell")).toBeVisible();
    await expect(page).toHaveScreenshot("admin-tenants.png", SHOT_OPTS);
  });
});
