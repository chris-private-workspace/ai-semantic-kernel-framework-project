/**
 * File: frontend/scripts/sprint-57-31-day1-verify.mjs
 * Purpose: Sprint 57.31 Day 1 — verify shots after /cost-dashboard 7-file verbatim re-point.
 *          Captures full page + an anomaly row visibility shot for Day 1 closeout evidence.
 *          Standalone ad-hoc; deletable after Sprint 57.31 closeout.
 * Category: Frontend / scripts / sprint-57-31
 * Scope: Phase 57 / Sprint 57.31 Day 1 (POST verbatim re-point verification)
 *
 * Usage: node scripts/sprint-57-31-day1-verify.mjs
 *
 * Created: 2026-05-23
 */
import { chromium } from "playwright";
import path from "path";
import fs from "fs";

const BASE = "http://localhost:3007";
const VP = { width: 1440, height: 900 };
const OUT_DIR = path.resolve(
  `../claudedocs/4-changes/sprint-57-31-cost-dashboard-repoint/screenshots/day1-verify`,
);
fs.mkdirSync(OUT_DIR, { recursive: true });

// Mock auth — platform_admin so admin-scope widgets mount (TenantTopTable + ProviderMixCard)
async function mockAuth(page) {
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        user: {
          id: "u1",
          email: "admin@acme-prod.test",
          display_name: "Pat Admin",
          roles: ["platform_admin"],
        },
        tenant: {
          id: "00000000-0000-4000-8000-000000000099",
          code: "acme-prod",
          name: "Acme Production",
          region: "ap-east-1",
        },
        roles: ["platform_admin"],
      }),
    }),
  );
  // Mock cost-summary so the bottom CostBreakdownTable renders real-shape data
  await page.route(
    "**/api/v1/admin/tenants/*/cost-summary**",
    (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          tenant_id: "00000000-0000-4000-8000-000000000099",
          month: new Date().toISOString().substring(0, 7),
          total_cost_usd: "12.3456",
          by_type: {
            llm_input: {
              "azure_openai_gpt-5.4": {
                quantity: "10000",
                total_cost_usd: "10.0000",
                entry_count: 5,
              },
            },
            llm_output: {
              "azure_openai_gpt-5.4": {
                quantity: "1000",
                total_cost_usd: "2.0000",
                entry_count: 5,
              },
            },
            tool: {
              salesforce_query: {
                quantity: "10",
                total_cost_usd: "0.3456",
                entry_count: 10,
              },
            },
          },
        }),
      }),
  );
  // Pass-through for anything else (200 empty)
  await page.route("**/api/v1/**", (route) => {
    const url = route.request().url();
    if (url.includes("/auth/me") || url.includes("/cost-summary")) {
      return route.fallback();
    }
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({}),
    });
  });
}

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: VP });
const page = await ctx.newPage();
await mockAuth(page);

console.log(`=== sprint-57-31-day1-verify → ${OUT_DIR} ===\n`);

// 1) Full-page /cost-dashboard shot after Day 1 re-point
await page.goto(`${BASE}/cost-dashboard`, { waitUntil: "networkidle" });
await page.waitForTimeout(800);
await page.screenshot({
  path: path.join(OUT_DIR, "day1-cost-dashboard-full.png"),
  fullPage: true,
});
console.log(
  "  ✓ day1-cost-dashboard-full (expect .page-head + .grid-stats 4-stat + .grid-main rows + admin widgets)",
);

// 2) Viewport shot focused on header / KPI area (above the fold)
await page.screenshot({
  path: path.join(OUT_DIR, "day1-cost-dashboard-fold.png"),
  fullPage: false,
});
console.log(
  "  ✓ day1-cost-dashboard-fold (expect mockup .page-head + grid-stats above the fold)",
);

// 3) TenantTopTable anomaly badge visibility (wonka-apac warning + tenant_3kp9 over-quota)
const anomalyBadge = page.locator('[data-testid="tenant-anomaly-badge"]').first();
const anomalyCount = await anomalyBadge.count();
if (anomalyCount > 0) {
  await anomalyBadge.scrollIntoViewIfNeeded();
  await page.waitForTimeout(300);
  await page.screenshot({
    path: path.join(OUT_DIR, "day1-cost-dashboard-table-anomaly.png"),
    fullPage: false,
  });
  console.log(
    "  ✓ day1-cost-dashboard-table-anomaly (expect tenant_3kp9 anomaly Badge dot + 320% over-quota)",
  );
} else {
  console.log("  ⚠ [tenant-anomaly-badge] not found — admin gate or fixture missing");
}

await browser.close();
console.log("\n=== done ===");
