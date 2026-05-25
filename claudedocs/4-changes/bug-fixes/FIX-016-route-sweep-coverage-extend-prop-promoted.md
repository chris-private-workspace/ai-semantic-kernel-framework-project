# FIX-016: `frontend/scripts/route-sweep.mjs` — APPSHELL_ROUTES coverage extend (PROP→real promoted pages)

**Date**: 2026-05-25
**Sprint**: AD `AD-RouteSweep-Coverage-Extend-PROP-Promoted-Pages` application (not a sprint — single-commit micro-fix on hotfix branch; #3 of 4-AD sequence per user authorization)
**Scope**: 2 NEW APPSHELL_ROUTES entries (`/redaction` + `/error-policy`) + comment refresh (13→15 real / 13→11 PROP rep) + MHist
**Branch**: `fix/route-sweep-coverage-extend`
**PR**: (filled after open)
**Class**: Infra / script coverage gap fix (Sprint 57.39 D-DAY2.5-1 evidence-driven)

---

## Problem

`frontend/scripts/route-sweep.mjs` hardcodes `APPSHELL_ROUTES` as a 14-entry tuple list (13 real pages + 1 PROP stub representative `/compaction`). Sprint 57.39 promoted `/redaction` + `/error-policy` from PROP stubs to real implementations (Domain C + D of the 4-domain batched sprint), but the sweep clamp was NOT updated — so the **Day 2.5 after baseline sweep** had no before/after PNG evidence for the 2 newly-promoted routes. Logged as Sprint 57.39 D-DAY2.5-1 drift finding.

The current state vs reality:

| Source | Real route count | Coverage gap |
|--------|------------------|--------------|
| `routes.config.ts` `ROUTES.filter(r => r.active && !r.proposed && r.component)` | 15 | — |
| `route-sweep.mjs` `APPSHELL_ROUTES` | 13 | **missing /redaction + /error-policy** |

This is a **coverage drift** between two single-source-of-truth files for the same conceptual "active production routes" list.

---

## Root Cause

Sprint 57.18 (`AD-Mockup-Integration-Foundation`) introduced the 3-state route convention (active / proposed PROP / designed DRAFT) and made `routes.config.ts` the single-source registry consumed by `App.tsx`, `Sidebar.tsx`, and `ComingSoonPlaceholder.tsx`. But `route-sweep.mjs` — created later (Sprint 57.26 Day 0) — uses an INDEPENDENT hardcoded list without any sync mechanism with `routes.config.ts`.

When any future sprint promotes a PROP route to real, `route-sweep.mjs` silently misses it. The script "works" (no error, just incomplete coverage) — a textbook silent-drift gap.

Long-term, the right fix is **auto-derive APPSHELL_ROUTES from routes.config.ts** so the registry stays in sync automatically. But that requires either:
- TS-from-MJS module import (needs `tsx` / `ts-node`)
- Text-parsing `routes.config.ts` with regex (fragile)
- Pre-build extraction step (adds build complexity)

For the immediate FIX-016 scope, **Option A (manual additions)** is preferred per Karpathy §2 (Simplicity First) — closes the Sprint 57.39 gap with minimal change. Auto-derive deferred as `AD-RouteSweep-Auto-Derive` follow-up candidate.

---

## Solution (Option A — 2 NEW entries + comment refresh)

```diff
- // AppShellV2 routes — 13 real pages + 1 PROP stub representative (/compaction;
- // the other 13 PROP stubs all render the same ComingSoonPlaceholder shell).
+ // AppShellV2 routes — 15 real pages + 1 PROP stub representative (/compaction;
+ // the other 11 PROP stubs all render the same ComingSoonPlaceholder shell).
+ // FIX-016: +/redaction +/error-policy (Sprint 57.39 PROP→real promotion gap;
+ // previously stuck at 13 real + missed Sprint 57.39 deliberate-test PNG evidence).
+ // Future auto-derive from routes.config.ts is AD-RouteSweep-Auto-Derive candidate.
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
+   ["/redaction", "redaction"],
+   ["/error-policy", "error-policy"],
    ["/cost-dashboard", "cost-dashboard"],
    ["/sla-dashboard", "sla-dashboard"],
    ["/admin-tenants", "admin-tenants"],
    ["/tenant-settings", "tenant-settings"],
    ["/compaction", "prop-stub-compaction"],
  ];
```

New entries placed **after `/verification`** (Governance group continuation per `routes.config.ts` category ordering), **before `/cost-dashboard`** (Observability group start).

Comment refresh:
- "13 real" → "15 real" (matches new APPSHELL_ROUTES length 16 = 15 real + 1 PROP)
- "other 13 PROP stubs" → "other 11 PROP stubs" (matches current `routes.config.ts` proposed count: 12 total proposed routes − 1 representative `/compaction` = 11 others)

---

## Verification

| Check | Result |
|-------|--------|
| `node --check frontend/scripts/route-sweep.mjs` | ✅ syntax OK |
| `npm run lint` (frontend; non-silent — lesson from FIX-015 CI fail) | ✅ 0 errors (script `.mjs` not in eslint `src` scope; only upstream `jsx-ast-utils` warnings — unchanged) |

**Why no dynamic run**: a full route-sweep execution requires the frontend dev server + browser launch + 24 screenshot captures (~30-60 sec wall-clock). The fix is purely a data-list extension with no runtime logic change. Static syntax check + path arithmetic verification (FIX-014 already covered) is sufficient. Future sprints that use the script will exercise the new entries naturally.

**Why no other validation suites run**: the script is a `.mjs` file in `frontend/scripts/` — outside Vitest scope, outside TypeScript scope, outside Vite build scope (per FIX-014 doc). Local Vitest/build/mockup-fidelity runs are unaffected by this change.

---

## Impact

### Coverage

- **APPSHELL_ROUTES**: 14 entries → 16 entries (+2)
- **Real-route coverage**: 13 → 15 (now matches `routes.config.ts` reality)
- **PROP-stub representative**: 1 (unchanged — `/compaction`; the other 11 PROPs still all render identical `ComingSoonPlaceholder` shell)

### Future sprint impact

- Sprint 57.40+ route-sweep runs will now capture `/redaction` + `/error-policy` in both `before/` and `after/` directories
- PROP→real promotion sprints can now produce visual evidence without needing to also remember to update `route-sweep.mjs` (for the routes already in the list)
- **Still requires manual update** for FUTURE PROP→real promotions — that's the `AD-RouteSweep-Auto-Derive` follow-up scope

### AD lifecycle

- ✅ **`AD-RouteSweep-Coverage-Extend-PROP-Promoted-Pages`** — RESOLVED (Option A applied)
- 🆕 **`AD-RouteSweep-Auto-Derive`** (NEW carryover) — automate APPSHELL_ROUTES derivation from `routes.config.ts` to prevent future drift; needs decision between (a) tsx/ts-node dependency, (b) text-parse regex, (c) build-step extraction. Estimated ~2-3 hr. Class: `frontend-refactor-mechanical` 0.80 candidate.

### Backward compatibility

- ✅ Fully compatible — existing route-sweep invocations continue to work; the 2 new routes are simply additional screenshots taken
- No script signature / arg / cwd / output-dir change (FIX-014 invariance preserved)

### What's NOT included

- Auto-derive from `routes.config.ts` (deferred as new AD per above)
- No update to existing PROP stub representative (`/compaction` is still the chosen rep — alternative would be more PROP samples but the principle "all PROPs share the same `ComingSoonPlaceholder` shell" makes 1 rep sufficient)
- No script BASE URL update (kept `http://localhost:3007` — sprint-specific dev server choice, unrelated to this fix)

---

## References

- AD source: `claudedocs/1-planning/next-phase-candidates.md` §Sprint 57.39 Carryover #49
- Evidence: Sprint 57.39 retrospective Day 2.5 D-DAY2.5-1 finding
- Related single-source registry: `frontend/src/routes.config.ts` (consumed by App.tsx + Sidebar.tsx + ComingSoonPlaceholder.tsx)
- Related infra: FIX-014 (`frontend/scripts/route-sweep.mjs` cwd-relative → __dirname-relative)
- Future automation candidate: `AD-RouteSweep-Auto-Derive` (logged in this FIX's carryover section)

---

## Modification History (newest-first)

- 2026-05-25: Initial creation (FIX-016 — APPSHELL_ROUTES +/redaction +/error-policy + comment refresh)
