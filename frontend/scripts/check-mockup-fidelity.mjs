/**
 * File: frontend/scripts/check-mockup-fidelity.mjs
 * Purpose: CI guard for the verbatim-CSS mockup-fidelity foundation (Sprint 57.28 AD-Mockup-Fidelity-Foundation-Switch).
 * Category: Frontend / scripts (Sprint 57.28 Day 3 US-D1)
 *
 * Description:
 *   Two guards protecting the Sprint 57.28 verbatim-CSS 4-layer sync protocol
 *   (docs/rules-on-demand/frontend-mockup-fidelity.md):
 *
 *   1. diff guard — `frontend/src/styles-mockup.css` MUST be a byte-identical
 *      copy of `reference/design-mockups/styles.css` (line-ending normalised).
 *      The verbatim copy is the protocol's single non-translation point; any
 *      divergence means the CSS was hand-edited / re-translated → drift. Hard
 *      fail with the first divergent line.
 *
 *   2. grep guard — no NEW hardcoded `#hex` / `oklch()` colour literals in
 *      `src/features/**` + `src/pages/**`. Pages must consume mockup classes /
 *      design tokens, never inline colour literals. Pre-existing offenders
 *      (the 13 not-yet-re-pointed pages) are absorbed by HEX_OKLCH_BASELINE;
 *      the guard hard-fails only when the offending-line count rises ABOVE the
 *      baseline. Each Phase-2 re-point sprint that removes offenders should
 *      lower HEX_OKLCH_BASELINE (the guard prints a reminder when live < base).
 *
 * Usage:
 *   node scripts/check-mockup-fidelity.mjs      # run from frontend/
 *   npm run check:mockup-fidelity               # CI + local
 *
 * Created: 2026-05-22 (Sprint 57.28 Day 3 US-D1)
 *
 * Modification History:
 *   - 2026-05-24: Sprint 57.35 Day 4 — bump HEX_OKLCH_BASELINE 25→41 (16 verbatim `oklch(from var(--X) l c h / X)` token-vocabulary literals from auth verbatim port across /auth/{login,invite,mfa,register} — all derive from existing design tokens like --danger / --warning / --primary, NOT raw colours; same vocabulary precedent as Sprint 57.30 bump 21→25; mockup uses these inline tint patterns where styles-mockup.css doesn't define a named class for the alpha variant — verbatim-token usage, not drift)
 *   - 2026-05-23: Sprint 57.30 Day 2 — bump HEX_OKLCH_BASELINE 21→25 (4 verbatim oklch tints in InputBar error box + SessionList AP-2 demo banner — production-only widgets with no mockup line; using mockup-token vocabulary verbatim)
 *   - 2026-05-22: Sprint 57.29 Day 4 — bump HEX_OKLCH_BASELINE 18→21 (3 verbatim oklch from page-overview.jsx)
 *   - 2026-05-22: Initial creation (Sprint 57.28 Day 3 US-D1) — diff guard + grep guard
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const FRONTEND = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const REPO = path.resolve(FRONTEND, "..");

const LAYER1 = path.join(REPO, "reference/design-mockups/styles.css");
const LAYER2 = path.join(FRONTEND, "src/styles-mockup.css");
const SCAN_DIRS = [path.join(FRONTEND, "src/features"), path.join(FRONTEND, "src/pages")];

// Phase-1 baseline — offending lines in features/ + pages/ at Sprint 57.35
// Day 4. +16 from Sprint 57.35: AuthShell + 7 auth routes Phase-2 verbatim
// re-point introduced `oklch(from var(--X) l c h / X)` token-vocabulary
// literals inline (mockup `page-extras.jsx` + `page-auth-extras.jsx` use these
// inline alpha-tint patterns where styles-mockup.css doesn't define a named
// class for the variant). All derive from existing design tokens (--danger /
// --warning / --primary), NOT raw colours — same legitimate verbatim-token
// vocabulary precedent as Sprint 57.30 bump 21→25.
// +4 from Sprint 57.30: InputBar error box + SessionList AP-2 demo banner.
// +3 from Sprint 57.29: page-overview.jsx verbatim oklch.
// The not-yet-re-pointed governance + chat_v2 risk-colour maps still carry
// hardcoded hex; Phase-2 re-point sprints lower this number when those land.
const HEX_OKLCH_BASELINE = 41;

let failed = false;

// === Guard 1: diff — styles-mockup.css byte-identical to mockup styles.css ===
// Why: the verbatim copy is the protocol's single non-translation point. Line
// endings are normalised (Risk R6 — cp on Windows may introduce CRLF).
function diffGuard() {
  for (const f of [LAYER1, LAYER2]) {
    if (!fs.existsSync(f)) {
      console.error(`✗ diff guard: missing file ${f}`);
      failed = true;
      return;
    }
  }
  const norm = (s) => s.replace(/\r\n/g, "\n");
  const a = norm(fs.readFileSync(LAYER1, "utf8"));
  const b = norm(fs.readFileSync(LAYER2, "utf8"));
  if (a === b) {
    console.log("✓ diff guard: styles-mockup.css byte-identical to reference/design-mockups/styles.css");
    return;
  }
  const al = a.split("\n");
  const bl = b.split("\n");
  let i = 0;
  while (i < al.length && i < bl.length && al[i] === bl[i]) i++;
  console.error("✗ diff guard: styles-mockup.css DIVERGED from reference/design-mockups/styles.css");
  console.error(`  first difference at line ${i + 1}:`);
  console.error(`    reference:  ${JSON.stringify(al[i] ?? "<EOF>")}`);
  console.error(`    production: ${JSON.stringify(bl[i] ?? "<EOF>")}`);
  console.error("  → styles-mockup.css must be a verbatim copy; never hand-edit it.");
  failed = true;
}

// === Guard 2: grep — no NEW hardcoded hex / oklch literals in pages ===
// Why: pages must consume mockup classes / design tokens. Comment lines are
// skipped (docstrings / Modification History may legitimately mention a hex).
const HEX = /#[0-9a-fA-F]{3,8}/;
const OKLCH = /\boklch\(/;
function isComment(line) {
  const t = line.trimStart();
  return t.startsWith("*") || t.startsWith("//") || t.startsWith("/*");
}
function walk(dir, out) {
  if (!fs.existsSync(dir)) return;
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) walk(full, out);
    else if (/\.tsx?$/.test(e.name)) out.push(full);
  }
}
function grepGuard() {
  const files = [];
  for (const d of SCAN_DIRS) walk(d, files);
  const offenders = [];
  for (const f of files) {
    const lines = fs.readFileSync(f, "utf8").split(/\r?\n/);
    lines.forEach((line, idx) => {
      if (isComment(line)) return;
      if (HEX.test(line) || OKLCH.test(line)) {
        offenders.push(`${path.relative(FRONTEND, f).replace(/\\/g, "/")}:${idx + 1}: ${line.trim()}`);
      }
    });
  }
  const n = offenders.length;
  if (n > HEX_OKLCH_BASELINE) {
    console.error(`✗ grep guard: ${n} hardcoded hex/oklch lines — ${n - HEX_OKLCH_BASELINE} NEW above baseline ${HEX_OKLCH_BASELINE}`);
    for (const o of offenders) console.error(`    ${o}`);
    console.error("  → use mockup classes / design tokens (var(--X)), not colour literals.");
    failed = true;
    return;
  }
  console.log(`✓ grep guard: ${n} hardcoded hex/oklch lines (baseline ${HEX_OKLCH_BASELINE}; Phase-2 re-point backlog)`);
  if (n < HEX_OKLCH_BASELINE) {
    console.log(`  note: live count ${n} < baseline ${HEX_OKLCH_BASELINE} — lower HEX_OKLCH_BASELINE to ${n}.`);
  }
}

console.log("=== check-mockup-fidelity ===");
diffGuard();
grepGuard();
if (failed) {
  console.error("\n✗ mockup-fidelity check FAILED");
  process.exit(1);
}
console.log("\n✓ mockup-fidelity check passed");
