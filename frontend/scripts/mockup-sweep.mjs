/**
 * File: frontend/scripts/mockup-sweep.mjs
 * Purpose: Standalone Playwright 1440×900 mockup screenshot harness — sibling
 *          of route-sweep.mjs but reads the mockup-side reference (mockup
 *          SPA with hash routing) instead of the production dev server.
 * Category: Frontend / scripts (2026-05-25 drift audit)
 *
 * Description:
 *   Loads reference/design-mockups/index.html via file:// URL, navigates
 *   to each hash route (#overview, #chat-v2, ...), waits for babel+react
 *   to render, screenshots 1440×900. Output to claudedocs/5-status/
 *   drift-audit-2026-05-25/screenshots/mockup/ so it sits next to the
 *   production after/ sweep for side-by-side compare.
 *
 *   AUTH_ROUTES in app.jsx use the non-slash form (`auth-login`,
 *   `auth-callback`, ...); production paths use `/auth/login`. The mapping
 *   below normalises both ends so filenames match for diff'ing.
 *
 * Usage:
 *   node scripts/mockup-sweep.mjs
 *
 * Created: 2026-05-25 (drift audit)
 */
import { chromium } from "playwright";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(__dirname, "../..");
const OUT_DIR = path.resolve(REPO, "claudedocs/5-status/drift-audit-2026-05-25/screenshots/mockup");
const VP = { width: 1440, height: 900 };
// Use http://localhost:8080 (python -m http.server) instead of file:// —
// babel-standalone fails to load unpkg CDN scripts under file:// (CORS / SRI),
// producing blank black PNGs. Per CLAUDE.md §Frontend Mockup-Fidelity
// `python -m http.server` is the canonical mockup serve method.
const BASE_URL = `http://localhost:8080/index.html`;

// Mockup hash route → production-equivalent slug (mirrors route-sweep.mjs slugs
// so PNG filenames line up for side-by-side compare).
const ROUTES = [
  // auth pages (rendered without app shell)
  ["auth-login", "auth-login"],
  ["auth-callback", "auth-callback"],
  ["auth-register", "auth-register"],
  ["auth-invite", "auth-invite"],
  ["auth-mfa", "auth-mfa"],
  ["auth-expired", "auth-expired"],
  ["auth-dev", "auth-dev"],
  // operations
  ["overview", "overview"],
  ["chat-v2", "chat-v2"],
  ["orchestrator", "orchestrator"],
  ["subagents", "subagents"],
  ["loop-debug", "loop-debug"],
  ["memory", "memory"],
  ["state-inspector", "state-inspector"],
  // governance
  ["governance", "governance"],
  ["verification", "verification"],
  ["redaction", "redaction"],
  ["error-policy", "error-policy"],
  // observability
  ["cost-dashboard", "cost-dashboard"],
  ["sla-dashboard", "sla-dashboard"],
  // admin
  ["admin-tenants", "admin-tenants"],
  ["tenant-settings", "tenant-settings"],
  // PROP rep
  ["compaction", "prop-stub-compaction"],
];

fs.mkdirSync(OUT_DIR, { recursive: true });
const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: VP });
const page = await ctx.newPage();

console.log(`\n=== mockup-sweep → ${OUT_DIR} ===`);
console.log(`    source: ${BASE_URL}\n`);

// Load index.html ONCE; subsequent navigations use location.hash so the SPA
// stays mounted (faster + same babel-compiled state).
await page.goto(BASE_URL, { waitUntil: "domcontentloaded", timeout: 30000 });
// Wait for babel to compile + React to mount before first nav (otherwise
// the first screenshot may catch an empty #root). Babel-standalone compile
// of ~15 JSX files takes 4-6s; 8s is conservative.
await page.waitForTimeout(8000);

for (const [hash, slug] of ROUTES) {
  try {
    await page.evaluate((h) => {
      window.location.hash = h;
    }, hash);
    await page.waitForTimeout(900);
    await page.screenshot({
      path: path.join(OUT_DIR, `${slug}.png`),
      fullPage: false,
    });
    console.log(`  ✓ ${slug.padEnd(26)} #${hash}`);
  } catch (err) {
    console.log(`  ✗ ${slug.padEnd(26)} #${hash} — ${String(err).substring(0, 80)}`);
  }
}

await ctx.close();
await browser.close();
const count = fs.readdirSync(OUT_DIR).filter((f) => f.endsWith(".png")).length;
console.log(`\n=== done — ${count} mockup screenshots in screenshots/mockup/ ===`);
