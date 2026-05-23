/**
 * File: frontend/scripts/sprint-57-30-day0-extras.mjs
 * Purpose: Sprint 57.30 Day 0 — extra before-baseline screenshots not covered by route-sweep:
 *          UserMenu closed (avatar 36×36 drift evidence), UserMenu open (dropdown gap drift evidence),
 *          chat-v2 inspector closed + open. Standalone ad-hoc; deletable after Sprint 57.30 closeout.
 * Category: Frontend / scripts / sprint-57-30
 * Scope: Phase 57 / Sprint 57.30 Day 0 (PRE-WORK before any code change)
 *
 * Usage: node scripts/sprint-57-30-day0-extras.mjs
 *
 * Created: 2026-05-23
 */
import { chromium } from "playwright";
import path from "path";
import fs from "fs";

const BASE = "http://localhost:3007";
const VP = { width: 1440, height: 900 };
const OUT_DIR = path.resolve(
  `../claudedocs/4-changes/sprint-57-30-chatv2-shell-repoint/screenshots/before`,
);
fs.mkdirSync(OUT_DIR, { recursive: true });

// Mock auth (same shape as route-sweep.mjs)
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
  // Empty 200 for everything else under /api/v1 so pages render without backend
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

console.log(`=== sprint-57-30-day0-extras → ${OUT_DIR} ===\n`);

// 1) UserMenu — avatar closed at /overview (baseline drift: 36×36 inflated trigger)
await page.goto(`${BASE}/overview`, { waitUntil: "networkidle" });
await page.waitForTimeout(500);
await page.screenshot({
  path: path.join(OUT_DIR, "extra-usermenu-closed-overview.png"),
  fullPage: false,
});
console.log("  ✓ extra-usermenu-closed-overview");

// 2) UserMenu — dropdown open at /overview (baseline drift: gap below topbar bottom)
//    Click the avatar button (last button in .topbar; uses inline avatarStyle today)
const avatar = page.locator(".topbar button").filter({ hasText: /^[A-Z]$/ }).first();
if (await avatar.count()) {
  await avatar.click();
  await page.waitForTimeout(400);
  await page.screenshot({
    path: path.join(OUT_DIR, "extra-usermenu-open-overview.png"),
    fullPage: false,
  });
  console.log("  ✓ extra-usermenu-open-overview (showing drift gap below topbar)");
} else {
  console.log("  ⚠ avatar trigger not found by [A-Z] text — skipped");
}

// 3) chat-v2 inspector closed
const page2 = await ctx.newPage();
await mockAuth(page2);
await page2.goto(`${BASE}/chat-v2`, { waitUntil: "networkidle" });
await page2.waitForTimeout(800);
await page2.screenshot({
  path: path.join(OUT_DIR, "extra-chatv2-inspector-default.png"),
  fullPage: false,
});
console.log("  ✓ extra-chatv2-inspector-default");

// 4) chat-v2 try to toggle inspector (best-effort; may already be open by default)
const inspectorToggle = page2.locator('button[aria-label*="inspector" i], button[title*="inspector" i]').first();
if (await inspectorToggle.count()) {
  await inspectorToggle.click();
  await page2.waitForTimeout(400);
  await page2.screenshot({
    path: path.join(OUT_DIR, "extra-chatv2-inspector-toggled.png"),
    fullPage: false,
  });
  console.log("  ✓ extra-chatv2-inspector-toggled");
} else {
  console.log("  ⚠ inspector toggle button not found — skipped (default-state already captured)");
}

await browser.close();
console.log("\n=== done ===");
