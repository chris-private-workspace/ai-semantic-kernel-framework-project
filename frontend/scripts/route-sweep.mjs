/**
 * File: frontend/scripts/route-sweep.mjs
 * Purpose: Standalone Playwright 1440×900 route-sweep harness for frontend
 *          foundation before/after regression evidence (reused across foundation sprints).
 * Category: Frontend / scripts (Sprint 57.26 Day 0; reused Sprint 57.28)
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
 *
 * Modification History:
 *   - 2026-05-24: Sprint 57.39 — re-point OUT_DIR to sprint-57-39-governance-multipage-phase2 (4-domain batched: /governance + /verification re-point + /redaction + /error-policy PROP→real; 1st deliberate-test of `-with-extras` 0.65 baseline post-57.38 split)
 *   - 2026-05-24: Sprint 57.38 — re-point OUT_DIR to sprint-57-38-class-split-subagents-fullbleed-audit (reused for 3-domain batched sprint: Domain A class-split decision meta + Domain B /subagents Phase-2 verbatim re-point -with-extras 5th app per Day 0 D5 reclass + Domain C AD-FullBleed-Pages-Audit FIX-010 follow-up)
 *   - 2026-05-24: Sprint 57.37 — re-point OUT_DIR to sprint-57-37-loop-debug-state-inspector (reused for 2-domain batched sprint: Domain A /loop-debug full rebuild + Domain B /state-inspector Phase-2 verbatim re-point; 8th+9th apps; closes Sprint 57.36 §Frontend Mockup-Fidelity Hard Constraint gap)
 *   - 2026-05-24: Sprint 57.36 — re-point OUT_DIR to sprint-57-36-loop-debug-repoint (reused for /loop-debug Phase-2 verbatim re-point sweep; 7th app of epic; 3rd non-rich-dashboard shape — single-file scope; discriminates bimodal-by-shape vs scale-overhead variance hypotheses)
 *   - 2026-05-24: Sprint 57.35 — re-point OUT_DIR to sprint-57-35-auth-repoint (reused for AuthShell + 7 /auth/* routes Phase-2 verbatim re-point; 2nd non-rich-dashboard shape; closes Sprint 57.23 vintage epic gap)
 *   - 2026-05-24: Sprint 57.34 — re-point OUT_DIR to sprint-57-34-orchestrator-repoint (reused for /orchestrator Phase-2 verbatim CSS re-point sweep; 1st non-rich-dashboard shape in epic)
 *   - 2026-05-24: Sprint 57.33 — re-point OUT_DIR to sprint-57-33-page-bug-fix (reused for 3-route crash-fix sweep: /subagents + /memory + /verification)
 *   - 2026-05-23: Sprint 57.32 — re-point OUT_DIR to sprint-57-32-sla-dashboard-repoint (reused for /sla-dashboard Phase-2 re-point sweep)
 *   - 2026-05-23: Sprint 57.31 — re-point OUT_DIR to sprint-57-31-cost-dashboard-repoint (reused for /cost-dashboard Phase-2 re-point sweep)
 *   - 2026-05-23: Sprint 57.30 — re-point OUT_DIR to sprint-57-30-chatv2-shell-repoint (reused for chat-v2 + shell hotfix sweep)
 *   - 2026-05-22: Sprint 57.29 — re-point OUT_DIR to sprint-57-29-overview-shell-repoint (reused for /overview + shell re-point sweep)
 *   - 2026-05-22: Sprint 57.28 — re-point OUT_DIR to sprint-57-28-mockup-fidelity-foundation (reused for verbatim-CSS foundation switch sweep)
 *   - 2026-05-21: Sprint 57.26 Day 2 — add endpoint-specific object mocks for
 *     cost-summary / sla-report so the rebuilt dashboards render real content
 *     (D-DAY1-1: the generic `[]` mock crashed their object-shaped data hooks)
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
  `../claudedocs/4-changes/sprint-57-39-governance-multipage-phase2/screenshots/${MODE}`,
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

// Object-shaped endpoint mocks (D-DAY1-1) — the generic `[]` mock crashes the
// rebuilt cost/sla dashboards whose data hooks expect an object payload.
// Shapes mirror frontend/src/features/{cost,sla}-dashboard/types.ts.
const COST_SUMMARY = {
  tenant_id: "t-dev",
  month: "2026-05",
  total_cost_usd: "2847.00",
  by_type: {
    inference: {
      "gpt-4.1": { quantity: "1240000", total_cost_usd: "1820.50", entry_count: 8400 },
      "claude-haiku-4-5": { quantity: "2100000", total_cost_usd: "640.20", entry_count: 12400 },
      "gpt-4.1-mini": { quantity: "480000", total_cost_usd: "92.40", entry_count: 4700 },
    },
    tool: {
      "k8s.exec": { quantity: "320", total_cost_usd: "118.30", entry_count: 320 },
      "http.fetch": { quantity: "1840", total_cost_usd: "44.10", entry_count: 1840 },
    },
    storage: {
      "memory.store": { quantity: "48000", total_cost_usd: "31.50", entry_count: 7800 },
    },
  },
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
    const url = r.request().url();
    if (/\/auth\/me/.test(url)) return r.fallback();
    const json = (obj) =>
      r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(obj) });
    if (/\/cost-summary/.test(url)) return json(COST_SUMMARY);
    if (/\/sla-report/.test(url)) return json(SLA_REPORT);
    // default — list-shaped endpoints tolerate an empty array
    return r.fulfill({ status: 200, contentType: "application/json", body: "[]" });
  });
  for (const [route, slug] of APPSHELL_ROUTES) await capture(ctx, route, slug);
  await ctx.close();
}

await browser.close();
const count = fs.readdirSync(OUT_DIR).filter((f) => f.endsWith(".png")).length;
console.log(`\n=== done — ${count} screenshots in screenshots/${MODE}/ ===`);
