/**
 * File: frontend/scripts/sprint-57-30-day2-verify.mjs
 * Purpose: Sprint 57.30 Day 2 — verify shots after US-C1+C2 (chat-v2 shell + composer verbatim CSS re-point).
 *          Captures /chat-v2 default 3-col state + data-list="hidden" + data-insp="hidden" toggle states
 *          for Day 2 closeout evidence (parallel to Sprint 57.29 Day 2 /overview verify).
 *          Standalone ad-hoc; deletable after Sprint 57.30 closeout.
 * Category: Frontend / scripts / sprint-57-30
 * Scope: Phase 57 / Sprint 57.30 Day 2 (POST US-C1+C2 verification)
 *
 * Usage: node scripts/sprint-57-30-day2-verify.mjs
 *
 * Created: 2026-05-23
 */
import { chromium } from "playwright";
import path from "path";
import fs from "fs";

const BASE = "http://localhost:3007";
const VP = { width: 1440, height: 900 };
const OUT_DIR = path.resolve(
  `../claudedocs/4-changes/sprint-57-30-chatv2-shell-repoint/screenshots/day2-verify`,
);
fs.mkdirSync(OUT_DIR, { recursive: true });

// Mock auth (same shape as sprint-57-30-day1-verify.mjs)
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

console.log(`=== sprint-57-30-day2-verify → ${OUT_DIR} ===\n`);

// 1) Default state — 3-col chat-shell + session list + header + empty stream + composer
await page.goto(`${BASE}/chat-v2`, { waitUntil: "networkidle" });
await page.waitForTimeout(800);
await page.screenshot({
  path: path.join(OUT_DIR, "day2-chatv2-shell.png"),
  fullPage: false,
});
console.log("  ✓ day2-chatv2-shell (expect 3-col .chat-shell + SessionList + ChatHeader + empty stream + InputBar composer)");

// 2) data-list="hidden" — collapse session list via ChatHeader left toggle
const listToggle = page.getByTestId("chat-header-toggle-list");
const listToggleCount = await listToggle.count();
if (listToggleCount > 0) {
  await listToggle.click();
  await page.waitForTimeout(400);
  await page.screenshot({
    path: path.join(OUT_DIR, "day2-chatv2-list-hidden.png"),
    fullPage: false,
  });
  console.log("  ✓ day2-chatv2-list-hidden (expect .chat-shell[data-list='hidden'] — SessionList grid column → 0)");
  // Reset
  await listToggle.click();
  await page.waitForTimeout(200);
} else {
  console.log("  ⚠ chat-header-toggle-list not found — selector or auth gate issue");
}

// 3) data-insp="hidden" — collapse inspector via ChatHeader right toggle
const inspToggle = page.getByTestId("chat-header-toggle-inspector");
const inspToggleCount = await inspToggle.count();
if (inspToggleCount > 0) {
  await inspToggle.click();
  await page.waitForTimeout(400);
  await page.screenshot({
    path: path.join(OUT_DIR, "day2-chatv2-insp-hidden.png"),
    fullPage: false,
  });
  console.log("  ✓ day2-chatv2-insp-hidden (expect .chat-shell[data-insp='hidden'] — ChatInspector grid column → 0)");
} else {
  console.log("  ⚠ chat-header-toggle-inspector not found — selector or auth gate issue");
}

await browser.close();
console.log("\n=== done ===");
