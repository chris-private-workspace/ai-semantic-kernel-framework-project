/**
 * File: frontend/scripts/sprint-57-30-day1-verify.mjs
 * Purpose: Sprint 57.30 Day 1 — verify shots after US-B1+B2 (Radix-drop + avatar 26×26 trigger).
 *          Captures the 26×26 trigger and the dropdown-flush-to-topbar state for Day 1 closeout evidence.
 *          Standalone ad-hoc; deletable after Sprint 57.30 closeout.
 * Category: Frontend / scripts / sprint-57-30
 * Scope: Phase 57 / Sprint 57.30 Day 1 (POST US-B1+B2 verification)
 *
 * Usage: node scripts/sprint-57-30-day1-verify.mjs
 *
 * Created: 2026-05-23
 */
import { chromium } from "playwright";
import path from "path";
import fs from "fs";

const BASE = "http://localhost:3007";
const VP = { width: 1440, height: 900 };
const OUT_DIR = path.resolve(
  `../claudedocs/4-changes/sprint-57-30-chatv2-shell-repoint/screenshots/day1-verify`,
);
fs.mkdirSync(OUT_DIR, { recursive: true });

// Mock auth (same shape as sprint-57-30-day0-extras.mjs)
async function mockAuth(page) {
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        user: { id: "u1", email: "operator@acme-prod.test", display_name: "Jane Lai", roles: ["operator"] },
        tenant: { id: "t1", code: "acme-prod", name: "Acme Production", region: "ap-east-1" },
        roles: ["operator"],
      }),
    }),
  );
  await page.route("**/api/v1/**", (route) => {
    if (route.request().url().includes("/auth/me")) return route.fallback();
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

console.log(`=== sprint-57-30-day1-verify → ${OUT_DIR} ===\n`);

// 1) UserMenu trigger closed at /overview — verify .avatar class → 26×26 trigger
await page.goto(`${BASE}/overview`, { waitUntil: "networkidle" });
await page.waitForTimeout(500);
await page.screenshot({
  path: path.join(OUT_DIR, "day1-usermenu-trigger-26.png"),
  fullPage: false,
});
console.log("  ✓ day1-usermenu-trigger-26 (expect 26×26 .avatar class)");

// 2) UserMenu dropdown open at /overview — verify flush against topbar bottom edge
//    Trigger has className="avatar" + aria-label="User menu"; locate via aria-label
const avatar = page.locator(".topbar button.avatar").first();
const avatarCount = await avatar.count();
if (avatarCount > 0) {
  await avatar.click();
  await page.waitForTimeout(400);
  await page.screenshot({
    path: path.join(OUT_DIR, "day1-usermenu-flush.png"),
    fullPage: false,
  });
  console.log("  ✓ day1-usermenu-flush (expect panel at top:50 right:12 — flush to topbar bottom)");
} else {
  console.log("  ⚠ .topbar button.avatar not found — selector or auth gate issue");
}

await browser.close();
console.log("\n=== done ===");
