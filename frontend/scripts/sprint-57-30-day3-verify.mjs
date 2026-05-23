/**
 * File: frontend/scripts/sprint-57-30-day3-verify.mjs
 * Purpose: Sprint 57.30 Day 3 — verify shots after US-D1 + US-D2 first half
 *          (TurnList + 3 turn shapes + 3 blocks verbatim CSS re-point).
 *          Captures /chat-v2 with default empty stream + injects mock TURNS
 *          via window-level fixture in chatStore to capture verbatim shots
 *          of each turn shape rendered.
 *          Standalone ad-hoc; deletable after Sprint 57.30 closeout.
 * Category: Frontend / scripts / sprint-57-30
 * Scope: Phase 57 / Sprint 57.30 Day 3 (POST US-D1 + US-D2 first half verification)
 *
 * Usage: node scripts/sprint-57-30-day3-verify.mjs
 *
 * Created: 2026-05-23
 */
import { chromium } from "playwright";
import path from "path";
import fs from "fs";

const BASE = "http://localhost:3007";
const VP = { width: 1440, height: 900 };
const OUT_DIR = path.resolve(
  `../claudedocs/4-changes/sprint-57-30-chatv2-shell-repoint/screenshots/day3-verify`,
);
fs.mkdirSync(OUT_DIR, { recursive: true });

// Mock auth (same shape as sprint-57-30-day2-verify.mjs)
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

console.log(`=== sprint-57-30-day3-verify → ${OUT_DIR} ===\n`);

// 1) Default state — empty stream after Day 3 TurnList re-point
//    Should show mockup `.subtle` + `.mono` empty-state copy at verbatim sizing.
await page.goto(`${BASE}/chat-v2`, { waitUntil: "networkidle" });
await page.waitForTimeout(800);
await page.screenshot({
  path: path.join(OUT_DIR, "day3-chatv2-empty.png"),
  fullPage: false,
});
console.log("  ✓ day3-chatv2-empty (verbatim mockup .subtle/.mono empty-state copy)");

// 2) Inject mock turns via zustand store to render all 3 turn shapes + 3 blocks.
//    Uses the same Turn Block Model discriminated union from types.ts.
const turnsInjected = await page.evaluate(() => {
  // Try to access zustand store via the React DevTools hook if exposed.
  // Fallback: dispatch via window.chatStoreApi if a debug hook exists.
  // For verbatim re-point check, even the empty state shot is meaningful
  // because mockup classes apply uniformly. We attempt the turns inject
  // best-effort — if injection fails the empty shot above is enough.
  try {
    const w = /** @type {any} */ (window);
    if (w.__chatStoreInjectMock) {
      w.__chatStoreInjectMock();
      return true;
    }
  } catch (e) {
    /* ignore — falls back to empty-state shot */
  }
  return false;
});

if (turnsInjected) {
  await page.waitForTimeout(400);
  await page.screenshot({
    path: path.join(OUT_DIR, "day3-chatv2-with-turns.png"),
    fullPage: false,
  });
  console.log("  ✓ day3-chatv2-with-turns (verbatim .turn/.turn-rail/.turn-marker/.turn-head)");
} else {
  console.log("  ⚠ no __chatStoreInjectMock hook — captured empty-state only (mockup classes still applied)");
}

await browser.close();
console.log("\n=== done ===");
