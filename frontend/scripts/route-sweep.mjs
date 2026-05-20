/**
 * File: frontend/scripts/route-sweep.mjs
 * Purpose: Standalone Playwright 1440×900 route-sweep harness for Sprint 57.26
 *          (AD-Foundation-Fidelity-Token-Correction) before/after regression evidence.
 * Category: Frontend / scripts (Sprint 57.26 Day 0)
 *
 * Description:
 *   Screenshots all ~22 representative production routes at 1440×900 into a
 *   mode-parametrised out-dir, so a before (Day 0) vs after (Day 2) diff and a
 *   vs-mockup comparison can be performed for the global foundation-token fix.
 *
 *   AppShellV2 (authed) routes are captured with a mocked GET /api/v1/auth/me
 *   so RequireAuth resolves to "authenticated"; other /api/v1 calls return an
 *   empty 200 so pages render without a live backend. AuthShell + Home routes
 *   need no mock.
 *
 *   Standalone Playwright (NOT the MCP server) — AD #37 the Playwright MCP has
 *   been a blocker for 4 consecutive sprints; the standalone driver is the
 *   Sprint 57.25-validated fallback.
 *
 * Usage:
 *   node scripts/route-sweep.mjs before    # Day 0 baseline
 *   node scripts/route-sweep.mjs after     # Day 2 post-correction
 *
 * Created: 2026-05-20 (Sprint 57.26 Day 0) — supersedes the temporary frontend/diagnose-render.mjs
 */
import { chromium } from "playwright";
import path from "path";
import fs from "fs";

const MODE = process.argv[2] || "before";
if (!["before", "after"].includes(MODE)) {
  console.error(`unknown mode "${MODE}" — use: before | after`);
  process.exit(1);
}

const BASE = "http://localhost:3007";
const VP = { width: 1440, height: 900 };
const OUT_DIR = path.resolve(
  `../claudedocs/4-changes/sprint-57-26-foundation-fidelity/screenshots/${MODE}`,
);
fs.mkdirSync(OUT_DIR, { recursive: true });

// Home + AuthShell routes — no auth mock needed (public).
const PUBLIC_ROUTES = [
  ["/", "home"],
  ["/auth/login", "auth-login"],
  ["/auth/callback", "auth-callback"],
  ["/auth/register", "auth-register"],
  ["/auth/invite/demo-token-123", "auth-invite"],
  ["/auth/mfa", "auth-mfa"],
  ["/auth/expired", "auth-expired"],
  ["/auth/dev", "auth-dev"],
];

// AppShellV2 routes — 13 real pages + 1 PROP stub representative (/compaction;
// the other 13 PROP stubs all render the same ComingSoonPlaceholder shell).
const APPSHELL_ROUTES = [
  ["/overview", "overview"],
  ["/chat-v2", "chat-v2"],
  ["/orchestrator", "orchestrator"],
  ["/subagents", "subagents"],
  ["/loop-debug", "loop-debug"],
  ["/memory", "memory"],
  ["/state-inspector", "state-inspector"],
  ["/governance", "governance"],
  ["/verification", "verification"],
  ["/cost-dashboard", "cost-dashboard"],
  ["/sla-dashboard", "sla-dashboard"],
  ["/admin-tenants", "admin-tenants"],
  ["/tenant-settings", "tenant-settings"],
  ["/compaction", "prop-stub-compaction"],
];

const AUTH_ME = {
  user: { id: "u-dev", email: "dev@ipa.local", display_name: "Dev User" },
  tenant: { id: "t-dev", name: "Dev Tenant", code: "DEV" },
  roles: ["admin"],
};

async function capture(ctx, route, slug) {
  const page = await ctx.newPage();
  try {
    await page.goto(`${BASE}${route}`, { waitUntil: "domcontentloaded", timeout: 20000 });
    await page.waitForTimeout(2200);
    await page.screenshot({ path: path.join(OUT_DIR, `${slug}.png`), fullPage: false });
    console.log(`  ✓ ${slug.padEnd(26)} ${route}`);
  } catch (err) {
    console.log(`  ✗ ${slug.padEnd(26)} ${route} — ${String(err).substring(0, 80)}`);
  } finally {
    await page.close();
  }
}

const browser = await chromium.launch({ headless: true });

console.log(`\n=== route-sweep [${MODE}] → ${OUT_DIR} ===\n`);
console.log("-- public (Home + AuthShell) --");
{
  const ctx = await browser.newContext({ viewport: VP });
  for (const [route, slug] of PUBLIC_ROUTES) await capture(ctx, route, slug);
  await ctx.close();
}

console.log("-- AppShellV2 (mocked auth) --");
{
  const ctx = await browser.newContext({ viewport: VP });
  await ctx.route(/\/api\/v1\/auth\/me/, (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(AUTH_ME) }),
  );
  await ctx.route(/\/api\/v1\//, (r) => {
    if (/\/auth\/me/.test(r.request().url())) return r.fallback();
    return r.fulfill({ status: 200, contentType: "application/json", body: "[]" });
  });
  for (const [route, slug] of APPSHELL_ROUTES) await capture(ctx, route, slug);
  await ctx.close();
}

await browser.close();
const count = fs.readdirSync(OUT_DIR).filter((f) => f.endsWith(".png")).length;
console.log(`\n=== done — ${count} screenshots in screenshots/${MODE}/ ===`);
