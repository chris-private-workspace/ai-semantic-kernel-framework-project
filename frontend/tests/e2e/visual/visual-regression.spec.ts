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
 *   RUNS ONLY ON THE LINUX RUNNER (or with RUN_VISUAL=1) — the guard runs iff
 *   either (a) the committed `visual-regression.spec.ts-snapshots/*-chromium-linux.png`
 *   baselines exist AND `process.platform === "linux"` (= the CI runner), or
 *   (b) `RUN_VISUAL=1` is set (the regeneration path / WSL). Screenshot baselines
 *   must be generated on the Linux runner, NOT a dev machine — font rendering /
 *   DPI differ, so locally-made (Windows/macOS) baselines would all mismatch; only
 *   the linux ones are committed, so a Windows/macOS dev run skips this spec. To regenerate after a UI change that
 *   legitimately moves the screenshots: run the `visual-baseline` job in
 *   .github/workflows/playwright-e2e.yml (Actions → "Playwright E2E" → Run
 *   workflow) — it runs `RUN_VISUAL=1 playwright test visual --update-snapshots`
 *   on ubuntu-latest and opens a `chore/visual-baselines-<run_id>` PR with the
 *   updated `-snapshots/` dir; merge it and this spec keeps running on every
 *   push/PR. Tracked: AD-Visual-Baseline-Generation (Sprint 57.14 landed the
 *   mechanism; FIX-007 fixed the `git add` glob, FIX-008 the protected-main push).
 *
 *   Mock pattern mirrors cost_dashboard.spec.ts (page.route() browser-layer).
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 9)
 * Last Modified: 2026-05-10
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.14 post-merge — visual-baseline job opens a PR (was: direct push to protected main, FIX-008); doc prose synced
 *   - 2026-05-10: Sprint 57.14 US-B1 — skip guard auto-un-skips once the -snapshots/ dir is committed (or RUN_VISUAL); CONVENTION.md §e2e + the visual-baseline CI job own the regeneration
 *   - 2026-05-10: Initial creation (Sprint 57.13 Day 9)
 */

import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { expect, test, type Page } from "@playwright/test";

// Playwright stores baselines next to the spec in `<spec-filename>-snapshots/`
// with OS-tagged names (`*-chromium-linux.png`). We only commit the *linux*
// baselines (generated on the CI Linux runner — see the `visual-baseline` job),
// so this spec only runs when (a) those baselines exist AND we're on linux
// (= the CI runner; a Windows/macOS dev would have no matching `*-win32.png` and
// the test would write+fail), or (b) `RUN_VISUAL=1` is set explicitly (WSL /
// the regeneration job). Until the linux baselines land it skips, so push/PR
// e2e is never red on a missing baseline.
const SNAPSHOTS_DIR = join(dirname(fileURLToPath(import.meta.url)), "visual-regression.spec.ts-snapshots");
const HAS_LINUX_BASELINES = existsSync(SNAPSHOTS_DIR) && process.platform === "linux";
const RUN_VISUAL = HAS_LINUX_BASELINES || Boolean(process.env.RUN_VISUAL);

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
    "Visual regression: skipped here. Runs on the CI Linux runner (where the committed " +
      "`*-chromium-linux.png` baselines match). Locally on Windows/macOS it's skipped (the baselines " +
      "are linux-only); use `RUN_VISUAL=1 npm run e2e -- visual` on WSL/Linux. To regenerate baselines " +
      "after a UI change: run the `visual-baseline` workflow_dispatch job (it opens a PR). " +
      "See AD-Visual-Baseline-Generation + frontend/CONVENTION.md §8.",
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
    // Sprint 57.23 US-B2 rewrite intentionally removed the <h1>"IPA Platform V2 — Sign In"</h1>
    // per mockup `page-extras.jsx:27-57` (heading-less card design). Anchor via AuthShell
    // `data-testid="auth-shell"` — consistent with app-shell anchor pattern at L93.
    // (Baseline auth-login-chromium-linux.png regenerated by Sprint 57.14 visual-baseline workflow_dispatch.)
    await expect(page.getByTestId("auth-shell")).toBeVisible();
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
