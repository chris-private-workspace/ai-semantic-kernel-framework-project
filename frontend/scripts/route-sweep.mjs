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
 *   - 2026-05-26: Sprint 57.44 Day 0 — re-point OUT_DIR to sprint-57-44-tenant-settings-rebuild (single-domain rebuild: /tenant-settings 6-tab IA — General/FeatureFlags/Quotas/HITLPolicies/Members/DangerZone; closes last CATASTROPHIC verdict + 🎉 Phase-2 epic FULL CLEAN; 2nd validation sprint under agent_factor = 0.55 → MANDATORY tighten 0.55 → 0.45)
 *   - 2026-05-25: Sprint 57.43 Day 0 — re-point OUT_DIR to sprint-57-43-admin-tenants-rebuild (single-domain rebuild: /admin-tenants page-head + 4 KPI stats + 9-col tenants table; closes drift audit 2026-05-25 #1 priority CATASTROPHIC post Sprint 57.42 /memory close; 1st validation sprint under newly ACTIVATED agent_factor = 0.55)
 *   - 2026-05-25: Sprint 57.42 Day 0 — re-point OUT_DIR to sprint-57-42-memory-matrix-rebuild (single-domain rebuild: /memory Memory Layers 5x3 matrix + TimeTravelScrubber + bottom 2-col grid; closes drift audit 2026-05-25 #2 priority CATASTROPHIC)
 *   - 2026-05-25: Sprint 57.41 Day 2 D-DAY0-1 fix — add `/api/v1/verification/recent` specific mock returning {items, total, has_more, next_offset, page_size} VerificationLogPage envelope (default [] fallback would trip useVerificationRecent TanStack on `data.items === undefined`; 2nd application of envelope-mock convention, AD-RouteSweep-Envelope-Mock-Convention)
 *   - 2026-05-25: Sprint 57.40 Day 2 D-DAY0-1 fix — add `/governance/approvals` specific mock returning {items, total, has_more} PendingListResponse shape (default [] fallback tripped rebuilt ApprovalsPage TanStack)
 *   - 2026-05-25: Sprint 57.41 Day 0 — re-point OUT_DIR to sprint-57-41-verification-full-rebuild (single-domain rebuild: /verification recent view full mockup-fidelity rebuild; closes drift audit 2026-05-25 #2 priority CATASTROPHIC)
 *   - 2026-05-25: Sprint 57.40 Day 0 — re-point OUT_DIR to sprint-57-40-governance-full-rebuild (single-domain rebuild: /governance Approvals view full mockup-fidelity rebuild; closes drift audit 2026-05-25 #3 priority)
 *   - 2026-05-25: FIX-018 — APPSHELL_ROUTES auto-derived from routes.config.ts (closes AD-RouteSweep-Auto-Derive; eliminates FIX-016-class manual-sync gap)
 *   - 2026-05-25: FIX-016 — APPSHELL_ROUTES +/redaction +/error-policy (PROP→real coverage gap)
 *   - 2026-05-25: FIX-014 — OUT_DIR cwd-relative → __dirname-relative (Sprint 57.39 D4 foot-gun)
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
import { fileURLToPath } from "url";

// FIX-014: __dirname derivation for ESM — base OUT_DIR resolution at script
// location (not process.cwd()). Sprint 57.39 D4 foot-gun: running from project
// root vs frontend/ produced different OUT_DIRs (parent-of-root vs intended).
const __dirname = path.dirname(fileURLToPath(import.meta.url));

const MODE = process.argv[2] || "before";
const LIST_ONLY = process.argv.includes("--list-only");
if (!["before", "after"].includes(MODE)) {
  console.error(`unknown mode "${MODE}" — use: before | after [--list-only]`);
  process.exit(1);
}

// === FIX-018: auto-derive APPSHELL_ROUTES from routes.config.ts ===
// Why: prior to FIX-018, APPSHELL_ROUTES was hand-maintained. Each PROP→real
// promotion (e.g. Sprint 57.39 /redaction + /error-policy) silently went
// missing from the sweep until FIX-016 manually patched it. routes.config.ts
// is the single source of truth for the active page registry (App.tsx +
// Sidebar.tsx already consume it); the sweep should derive from the same.
// Logic:
//   - real pages = active=true && proposed!=true (15 routes as of FIX-018)
//   - PROP rep   = first proposed=true entry in declaration order (covers
//                  the shared ComingSoonPlaceholder shell once; the other
//                  ~11 PROPs all render the same shell, so 1 is enough)
//   - DRAFT (active=false && designed=true) excluded — no <Route> generated.
//   - slug       = path.slice(1).replace(/\//g, '-')  (e.g. /admin/pricing
//                  → admin-pricing); PROP rep slug = 'prop-stub-' + slug.
//
// Parser: regex against routes.config.ts text. Each RouteEntry block is a
// `{ ... }` with no nested braces (lazy(() => import(...)) uses parens only),
// so splitting on `},` boundaries is robust. If the regex finds 0 real
// entries (file structure changed), THROW — never silently emit an empty
// sweep list, per AD-Pre-Push-Lint-Silent-Suppression-Anti-Pattern lesson.
function deriveAppshellRoutes() {
  const configPath = path.resolve(__dirname, "../src/routes.config.ts");
  const text = fs.readFileSync(configPath, "utf8");
  const arrayMatch = text.match(/export const ROUTES\s*:\s*RouteEntry\[\]\s*=\s*\[([\s\S]+)\];?\s*$/m);
  if (!arrayMatch) {
    throw new Error(
      "route-sweep FIX-018: failed to locate `export const ROUTES: RouteEntry[] = [...]` in routes.config.ts — schema changed? update parser.",
    );
  }
  const body = arrayMatch[1];
  const blocks = body
    .split(/\}\s*,/)
    .map((b) => b + "}")
    .filter((b) => /\bpath:\s*"/.test(b) && /\bactive:\s*(true|false)/.test(b));
  const real = [];
  const propStubs = [];
  for (const block of blocks) {
    const pathMatch = block.match(/\bpath:\s*"([^"]+)"/);
    const activeMatch = block.match(/\bactive:\s*(true|false)/);
    if (!pathMatch || !activeMatch || activeMatch[1] !== "true") continue;
    const routePath = pathMatch[1];
    const slug = routePath.replace(/^\//, "").replace(/\//g, "-");
    if (/\bproposed:\s*true/.test(block)) {
      propStubs.push([routePath, `prop-stub-${slug}`]);
    } else {
      real.push([routePath, slug]);
    }
  }
  if (real.length === 0) {
    throw new Error(
      "route-sweep FIX-018: derived 0 real routes — routes.config.ts parse failed silently? CHECK schema before continuing (do NOT silent-pass).",
    );
  }
  const propRep = propStubs.length > 0 ? [propStubs[0]] : [];
  return { routes: [...real, ...propRep], realCount: real.length, propTotal: propStubs.length };
}

const BASE = "http://localhost:3007";
const VP = { width: 1440, height: 900 };
const OUT_DIR = path.resolve(
  __dirname,
  `../../claudedocs/4-changes/sprint-57-45-chatv2-inspector-tab-rename/screenshots/${MODE}`,
);

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

// AppShellV2 routes — auto-derived from routes.config.ts (FIX-018; closes
// AD-RouteSweep-Auto-Derive). Prior hand-maintained list had to be patched
// every PROP→real promotion (last patch: FIX-016 added /redaction +
// /error-policy after Sprint 57.39 silently shipped them). routes.config.ts
// is the single registry consumed by App.tsx + Sidebar.tsx; the sweep now
// shares it. Real-page count + PROP rep are logged below for greppable
// evidence; if the derivation drops to 0 real entries the script THROWS.
const { routes: APPSHELL_ROUTES, realCount: APPSHELL_REAL_COUNT, propTotal: APPSHELL_PROP_TOTAL } =
  deriveAppshellRoutes();

// --list-only short-circuit (FIX-018 Day 2 dry-run): print derived list +
// exit 0 without launching browser / creating OUT_DIR. Used to validate the
// auto-derive output matches the prior hand-maintained list byte-for-byte.
if (LIST_ONLY) {
  console.log(`\n=== route-sweep --list-only (FIX-018 auto-derive evidence) ===\n`);
  console.log(`PUBLIC_ROUTES (${PUBLIC_ROUTES.length}):`);
  for (const [route, slug] of PUBLIC_ROUTES) console.log(`  ${slug.padEnd(26)} ${route}`);
  console.log(
    `\nAPPSHELL_ROUTES (${APPSHELL_ROUTES.length} = ${APPSHELL_REAL_COUNT} real + 1 of ${APPSHELL_PROP_TOTAL} PROP rep):`,
  );
  for (const [route, slug] of APPSHELL_ROUTES) console.log(`  ${slug.padEnd(26)} ${route}`);
  process.exit(0);
}

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

// Sprint 57.40 D-DAY0-1 — `/governance/approvals` returns `PendingListResponse`
// shape `{items, total, has_more}` (see backend `api/v1/governance/router.py`).
// The default `[]` fallback tripped the rebuilt ApprovalsPage (TanStack threw
// "data is undefined" because `governanceService.listPending` reads
// `body.items`). The audit PNG captured 2026-05-25 showed the red error banner
// — that was a sweep-mock artifact, NOT a production bug. Dispatched inside
// the broad /api/v1/ handler alongside cost-summary / sla-report.
const APPROVALS_LIST = { items: [], total: 0, has_more: false };

// Sprint 57.41 D-DAY0-1 — `/verification/recent` returns `VerificationLogPage`
// shape `{items, total, has_more, next_offset, page_size}` (see backend
// `api/v1/verification.py:89-95`). The rebuilt VerificationRunsTable consumes
// `data.items` via the useVerificationRecent TanStack hook; the default `[]`
// fallback would trip on `data.items === undefined`. 2nd application of the
// envelope-mock convention after Sprint 57.40 (AD-RouteSweep-Envelope-Mock-Convention).
const VERIFICATION_RECENT = { items: [], total: 0, has_more: false, next_offset: null, page_size: 50 };

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

fs.mkdirSync(OUT_DIR, { recursive: true });
const browser = await chromium.launch({ headless: true });

console.log(`\n=== route-sweep [${MODE}] → ${OUT_DIR} ===`);
console.log(
  `    auto-derived: ${APPSHELL_REAL_COUNT} real AppShellV2 routes + 1 of ${APPSHELL_PROP_TOTAL} PROP rep (FIX-018)\n`,
);
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
    if (/\/governance\/approvals/.test(url)) return json(APPROVALS_LIST);
    if (/\/verification\/recent/.test(url)) return json(VERIFICATION_RECENT);
    // default — list-shaped endpoints tolerate an empty array
    return r.fulfill({ status: 200, contentType: "application/json", body: "[]" });
  });
  for (const [route, slug] of APPSHELL_ROUTES) await capture(ctx, route, slug);
  await ctx.close();
}

await browser.close();
const count = fs.readdirSync(OUT_DIR).filter((f) => f.endsWith(".png")).length;
console.log(`\n=== done — ${count} screenshots in screenshots/${MODE}/ ===`);
