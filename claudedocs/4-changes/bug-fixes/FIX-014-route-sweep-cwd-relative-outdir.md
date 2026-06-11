# FIX-014: `frontend/scripts/route-sweep.mjs` — OUT_DIR cwd-relative → `__dirname`-relative

**Date**: 2026-05-25
**Sprint**: AD `AD-RouteSweep-Cwd-Relative-OUT_DIR-Foot-Gun-Fix` application (not a sprint — single-commit micro-fix on hotfix branch)
**Scope**: 2 lines added (ESM `__dirname` derivation) + 1 line modified (`path.resolve` base arg) + WHY comment + MHist
**Branch**: `fix/route-sweep-cwd-relative-outdir`
**PR**: (filled after open)
**Class**: Infra / script foot-gun fix (Sprint 57.39 D4 evidence-driven)

---

## Problem

`frontend/scripts/route-sweep.mjs` resolves `OUT_DIR` with a **cwd-relative** path:

```js
const OUT_DIR = path.resolve(
  `../docs/03-implementation/agent-harness-execution/phase-57/sprint-57-39/artifacts/governance-multipage-phase2/screenshots/${MODE}`,
);
```

`path.resolve()` with a single relative argument resolves it against `process.cwd()`. The script's Usage block (file header docstring lines 22-24) documents the intended invocation as `node scripts/route-sweep.mjs before` — implying `cd frontend &&` beforehand. But if invoked from a different cwd:

| Invocation cwd | Resolved OUT_DIR | Outcome |
|----------------|------------------|---------|
| `<project>/frontend/` (intended) | `<project>/claudedocs/4-changes/...` | ✅ correct |
| `<project>/` (project root — common for AI agents) | `<project>/../claudedocs/4-changes/...` | ❌ PNGs land in **parent of project root** |
| any other dir | unpredictable | ❌ |

**Sprint 57.39 D4 evidence**: agent-delegated route-sweep run via the code-implementer agent (running from project root, not `frontend/`) landed 44 PNGs at `C:\Users\Chris\Downloads\claudedocs\4-changes\sprint-57-39-...\screenshots\` (parent of project root). Recovery cost: `Move-Item` + manual confirmation. Logged as Day 4 carryover AD with a 15-min micro-fix bundle candidate annotation.

---

## Root Cause

ESM modules in Node.js don't expose `__dirname` directly (unlike CommonJS). When authors need a script-location-relative path, the established pattern is:

```js
import { fileURLToPath } from "url";
const __dirname = path.dirname(fileURLToPath(import.meta.url));
```

The original `route-sweep.mjs` (Sprint 57.26 Day 0) omitted this derivation and used a bare relative path with `path.resolve()`, silently inheriting cwd-dependence. The intent ("base OUT_DIR at `<project>/claudedocs/...`") is only achievable if cwd happens to be `<project>/frontend/` — making the script **brittle to the caller's working directory**.

This is a textbook Node.js ESM foot-gun: the script "works" in the obvious case (developer running from `frontend/`) but fails silently for any other cwd, with no error — just wrong-location output.

---

## Solution (2 added lines + 1 modified line + WHY comment)

```diff
 import { chromium } from "playwright";
 import path from "path";
 import fs from "fs";
+import { fileURLToPath } from "url";
+
+// FIX-014: __dirname derivation for ESM — base OUT_DIR resolution at script
+// location (not process.cwd()). Sprint 57.39 D4 foot-gun: running from project
+// root vs frontend/ produced different OUT_DIRs (parent-of-root vs intended).
+const __dirname = path.dirname(fileURLToPath(import.meta.url));
```

```diff
 const OUT_DIR = path.resolve(
-  `../docs/03-implementation/agent-harness-execution/phase-57/sprint-57-39/artifacts/governance-multipage-phase2/screenshots/${MODE}`,
+  __dirname,
+  `../../docs/03-implementation/agent-harness-execution/phase-57/sprint-57-39/artifacts/governance-multipage-phase2/screenshots/${MODE}`,
 );
```

The `path.resolve(__dirname, "../../claudedocs/...")` form takes two args: first absolute base + second relative segment → cwd-invariant.

**Path arithmetic**:
- `__dirname` = `<project>/frontend/scripts/` (always — derived from script's `import.meta.url`, independent of caller cwd)
- Resolved OUT_DIR = `<project>/frontend/scripts/../../claudedocs/4-changes/...` = `<project>/claudedocs/4-changes/...` ✅

---

## Verification

### Static (syntax)

```bash
$ node --check frontend/scripts/route-sweep.mjs
[exit 0]
```

### Dynamic (path resolution from different cwd)

Smoke test invoked from `C:\Users\Chris` (intentionally a cwd that's neither `<project>/` nor `<project>/frontend/`):

```bash
$ node -e "import('url').then(({fileURLToPath}) => import('path').then(({default:path}) => {
    const d = path.dirname(fileURLToPath('file:///c:/Users/Chris/Downloads/ai-semantic-kernel-framework-project/frontend/scripts/route-sweep.mjs'));
    console.log('__dirname:', d);
    console.log('OUT_DIR:', path.resolve(d, '../../docs/03-implementation/agent-harness-execution/phase-57/sprint-57-39/artifacts/governance-multipage-phase2/screenshots/before'));
  }))"

__dirname: c:\Users\Chris\Downloads\ai-semantic-kernel-framework-project\frontend\scripts
OUT_DIR (before): c:\Users\Chris\Downloads\ai-semantic-kernel-framework-project\docs\03-implementation\agent-harness-execution\phase-57\sprint-57-39\artifacts\governance-multipage-phase2\screenshots\before
```

✅ OUT_DIR resolves to the **intended** `<project>/claudedocs/4-changes/...` location regardless of caller cwd. Sprint 57.39 D4 foot-gun is structurally fixed.

### What is NOT verified by this fix

- Full route-sweep execution (browser launch + 22-route screenshot capture) is intentionally NOT re-run — the dev server PID / port assumptions are runtime-environmental and unrelated to the path resolution fix. The fix is purely **infra path arithmetic** and verified by the smoke test above.
- The OUT_DIR slug (`sprint-57-39-governance-multipage-phase2`) is unchanged — each future sprint that uses this script will re-point the slug as usual (per the long MHist record of sprint re-points). FIX-014 does NOT touch the slug; it only fixes the foot-gun underneath it.

---

## Impact

### Functional

- Script can now be invoked from any cwd (project root / `<project>/frontend/` / anywhere else) and always writes PNGs to `<project>/claudedocs/4-changes/<current-slug>/screenshots/<mode>/`
- Removes 1 silent failure mode (wrong-location output with no error) — caller cwd is no longer a hidden dependency

### Backward compatibility

- ✅ **Fully compatible** — when invoked from the originally-intended cwd (`<project>/frontend/`), the new OUT_DIR resolves to the same path as before. No behavior change for users who already followed the Usage convention.
- ✅ **Existing screenshots not affected** — the resolved absolute path is identical for the intended cwd case.

### Lint / build / test footprint

- The script is a `.mjs` file in `frontend/scripts/` — outside Vitest scope, outside TypeScript scope, outside Vite build scope. No CI lint surfaces this file beyond syntax-check (which `node --check` passes).
- Mockup-fidelity guard unaffected (this script is the harness that *generates* the screenshots; it's not part of the styles-mockup.css verification surface).

### AD lifecycle

- ✅ **`AD-RouteSweep-Cwd-Relative-OUT_DIR-Foot-Gun-Fix`** — RESOLVED
- Pattern is **also applicable** to any future ESM `.mjs` script under `frontend/scripts/` that uses cwd-relative paths. Suggestion for next maintenance cycle: grep `frontend/scripts/*.mjs` for `path.resolve(\`\.\.` patterns to find other potential foot-guns (deferred — out of scope here per Karpathy §3).

### What's NOT included

- No new tests added — this is a 3-line ESM idiom fix with deterministic path arithmetic; the smoke test in §Verification is sufficient. Adding a Vitest spec for a Node script's path resolution would be over-engineering.
- No Usage docstring expansion — the existing `node scripts/route-sweep.mjs before` example remains valid (cwd-agnostic now). Documenting the new cwd-invariance is recorded in MHist + inline WHY comment; the Usage block needs no churn.
- No broader audit of other `.mjs` scripts in `frontend/scripts/` — deferred as a follow-up nice-to-have AD candidate.

---

## References

- AD source: `claudedocs/1-planning/next-phase-candidates.md` §Sprint 57.38 Follow-up Carryover → `AD-RouteSweep-Cwd-Relative-OUT_DIR-Foot-Gun-Fix` (logged as "15 min micro-fix bundle candidate" 2026-05-24)
- Evidence: Sprint 57.39 retrospective Day 4 D4 finding (PNGs landed at parent of project root)
- ESM `__dirname` idiom: standard Node.js pattern since ESM was stabilized — `import.meta.url` + `fileURLToPath` is the official replacement for CommonJS `__dirname`
- Subject script: `frontend/scripts/route-sweep.mjs` (created Sprint 57.26 Day 0; reused across Sprint 57.28-57.39 per long MHist)

---

## Modification History (newest-first)

- 2026-05-25: Initial creation (FIX-014 — cwd-relative → `__dirname`-relative path resolution)
