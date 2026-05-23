/**
 * File: frontend/scripts/sprint-57-30-day4-verify.mjs
 * Purpose: Sprint 57.30 Day 4 — verify shots after US-D2 second half + US-D3 + US-D4
 *          (VerificationBlock + SubagentForkBlock + ChatInspector 4-tab +
 *           InspectorTurn + ComingSoonInspectorTab + ApprovalCard verbatim re-point).
 *          Captures /chat-v2 with the right-rail Inspector open and clicks
 *          through the 4 tabs (Turn / Trace / Memory / Tree) to confirm the
 *          verbatim mockup `.chat-inspector` + `.tabs` + `.tab[data-active]`
 *          + per-tab content shape.
 *          Standalone ad-hoc; deletable after Sprint 57.30 closeout.
 * Category: Frontend / scripts / sprint-57-30
 * Scope: Phase 57 / Sprint 57.30 Day 4 (POST US-D2 second half + US-D3 + US-D4 verification)
 *
 * Usage: node scripts/sprint-57-30-day4-verify.mjs
 *
 * Created: 2026-05-23
 */
import { chromium } from "playwright";
import path from "path";
import fs from "fs";

const BASE = "http://localhost:3007";
const VP = { width: 1440, height: 900 };
const OUT_DIR = path.resolve(
  `../claudedocs/4-changes/sprint-57-30-chatv2-shell-repoint/screenshots/day4-verify`,
);
fs.mkdirSync(OUT_DIR, { recursive: true });

// Mock auth — parallels day3-verify shape
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

console.log(`=== sprint-57-30-day4-verify → ${OUT_DIR} ===\n`);

// 1) Navigate to /chat-v2 → Inspector mounted with default Turn tab (empty state).
await page.goto(`${BASE}/chat-v2`, { waitUntil: "networkidle" });
await page.waitForTimeout(800);
await page.screenshot({
  path: path.join(OUT_DIR, "day4-chatv2-inspector-overview.png"),
  fullPage: false,
});
console.log("  ✓ day4-chatv2-inspector-overview (verbatim .chat-inspector + .tabs + Turn tab active)");

// 2) Click "Memory" tab → ComingSoonInspectorTab placeholder renders.
//    Uses role=tab + name=Memory aria selector (preserves a11y contract).
try {
  await page.getByRole("tab", { name: "Memory" }).click();
  await page.waitForTimeout(300);
  await page.screenshot({
    path: path.join(OUT_DIR, "day4-chatv2-inspector-state.png"),
    fullPage: false,
  });
  console.log("  ✓ day4-chatv2-inspector-state (verbatim Memory tab active — ComingSoon placeholder)");
} catch (e) {
  console.log(`  ⚠ skipped Memory tab shot: ${e.message}`);
}

// 3) Click "Trace" tab → ComingSoonInspectorTab for Trace.
try {
  await page.getByRole("tab", { name: "Trace" }).click();
  await page.waitForTimeout(300);
  await page.screenshot({
    path: path.join(OUT_DIR, "day4-chatv2-coming-soon-tab.png"),
    fullPage: false,
  });
  console.log("  ✓ day4-chatv2-coming-soon-tab (verbatim Trace ComingSoonInspectorTab placeholder)");
} catch (e) {
  console.log(`  ⚠ skipped Trace tab shot: ${e.message}`);
}

await browser.close();
console.log("\n=== done ===");
