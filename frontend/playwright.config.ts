/**
 * File: frontend/playwright.config.ts
 * Purpose: Playwright runner config for e2e specs (governance reviewer + chat ApprovalCard).
 * Category: Frontend / e2e
 * Scope: Phase 53 / Sprint 53.6 US-1
 *
 * Description:
 *   Wires Playwright to the Vite dev server (local) or `vite preview` server
 *   (CI). Targets headless Chromium only — Firefox/WebKit deferred to
 *   later sprints. Reporter is `list` locally and `list + html` on CI so
 *   failures upload an actionable report artifact via the GitHub workflow.
 *
 *   Sprint 53.6 ships 3 specs: smoke (US-1), governance approvals (US-2),
 *   chat ApprovalCard (US-3). All live under tests/e2e/.
 *
 * Created: 2026-05-04 (Sprint 53.6 Day 1)
 * Last Modified: 2026-05-04
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.13 US-B8 — expect.toHaveScreenshot config (animations off + small diff tolerance) for visual regression
 *   - 2026-05-04: Initial creation (Sprint 53.6 US-1)
 *
 * Related:
 *   - .github/workflows/playwright-e2e.yml
 *   - tests/e2e/smoke.spec.ts
 *   - tests/e2e/visual/visual-regression.spec.ts (consumes the toHaveScreenshot defaults)
 */

import { defineConfig, devices } from "@playwright/test";

const PORT = Number(process.env.E2E_PORT ?? 5173);
const BASE_URL = process.env.E2E_BASE_URL ?? `http://localhost:${PORT}`;
const IS_CI = Boolean(process.env.CI);

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  expect: {
    timeout: 5_000,
    // Visual regression (US-B8): disable animations + allow a tiny anti-aliasing
    // delta so font-hinting jitter doesn't cause flaky diffs.
    toHaveScreenshot: { animations: "disabled", maxDiffPixelRatio: 0.02 },
  },
  retries: IS_CI ? 2 : 0,
  workers: IS_CI ? 1 : undefined,
  reporter: IS_CI
    ? [["list"], ["html", { open: "never" }]]
    : [["list"]],
  use: {
    baseURL: BASE_URL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: IS_CI ? "retain-on-failure" : "off",
  },
  webServer: IS_CI
    ? {
        command: `npm run preview -- --port ${PORT} --strictPort`,
        port: PORT,
        reuseExistingServer: false,
        timeout: 60_000,
      }
    : {
        command: `npm run dev -- --port ${PORT} --strictPort`,
        port: PORT,
        reuseExistingServer: true,
        timeout: 60_000,
      },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
