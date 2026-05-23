/**
 * File: frontend/scripts/sprint-57-32-day1-verify.mjs
 * Purpose: Sprint 57.32 Day 1 mini-verify — single /sla-dashboard screenshot
 *          confirming new verbatim page-head + .btn-group TimeRangeTabs + .grid-stats KPI row.
 * Category: Frontend / scripts (Sprint 57.32 Day 1)
 *
 * Usage: node scripts/sprint-57-32-day1-verify.mjs
 *
 * Created: 2026-05-23 (Sprint 57.32 Day 1 US-B mini-verify)
 */
import { chromium } from "playwright";
import path from "path";
import fs from "fs";

const BASE = "http://localhost:3007";
const VP = { width: 1440, height: 900 };
const OUT_DIR = path.resolve(
  `../claudedocs/4-changes/sprint-57-32-sla-dashboard-repoint/screenshots/day1`,
);
fs.mkdirSync(OUT_DIR, { recursive: true });

const AUTH_ME = {
  user: { id: "u-dev", email: "dev@ipa.local", display_name: "Dev User" },
  tenant: { id: "t-dev", name: "Dev Tenant", code: "DEV" },
  roles: ["admin"],
};

const SLA_REPORT = {
  tenant_id: "t-dev",
  month: "2026-05",
  availability_pct: 99.94,
  api_p99_ms: 920,
  loop_simple_p99_ms: 1840,
  loop_medium_p99_ms: 3200,
  loop_complex_p99_ms: 8400,
  hitl_queue_notif_p99_ms: 4100,
  violations_count: 2,
};

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: VP });
await ctx.route(/\/api\/v1\/auth\/me/, (r) =>
  r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(AUTH_ME) }),
);
await ctx.route(/\/api\/v1\//, (r) => {
  const url = r.request().url();
  if (/\/auth\/me/.test(url)) return r.fallback();
  if (/\/sla-report/.test(url)) {
    return r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(SLA_REPORT) });
  }
  return r.fulfill({ status: 200, contentType: "application/json", body: "[]" });
});

const page = await ctx.newPage();
console.log(`\n=== Sprint 57.32 Day 1 verify ===\n`);
await page.goto(`${BASE}/sla-dashboard`, { waitUntil: "domcontentloaded", timeout: 20000 });
await page.waitForTimeout(2500);

// Above-the-fold (page-head + KPI row)
await page.screenshot({ path: path.join(OUT_DIR, "day1-sla-dashboard-fold.png"), fullPage: false });
console.log(`  ✓ day1-sla-dashboard-fold.png (above-the-fold = page-head + KPI row)`);

// Full page for cross-verify with mockup
await page.screenshot({ path: path.join(OUT_DIR, "day1-sla-dashboard-full.png"), fullPage: true });
console.log(`  ✓ day1-sla-dashboard-full.png (full page)`);

await page.close();
await ctx.close();
await browser.close();

console.log(`\n=== done — 2 screenshots in screenshots/day1/ ===`);
