# Sprint 57.15 Progress — AD-Inline-Style-Cleanup-Sweep

> Plan: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-15-plan.md`
> Checklist: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-15-checklist.md`
> Branch: `feature/sprint-57-15-inline-style-cleanup` (from main `c9d89ff3`)
> Calibration: `frontend-refactor-mechanical` HYBRID 0.50 (1st application) — bottom-up ~7.5-11.5 hr → committed ~4-6 hr — Day 0-3

---

## Day 0 — 2026-05-11 — Setup + branch + pre-flight + 三-prong + calibration

### Done
- Branch `feature/sprint-57-15-inline-style-cleanup` created from main `c9d89ff3` ✅
- Plan + checklist drafted (mirror 57.14 structure — Day 0-3, 4 USs A1/A2/B1/C1)
- Pre-flight baseline (sanity, mostly untouched this sprint): pytest 1676 pass+4 skip / mypy 0/306 / 9-9 V2 lints / Vitest 236 / Playwright 18 spec files (local Windows 40 pass + 7 skip; CI ubuntu 46 pass + 1 skip) / Vite main bundle 297.89 kB (gzip 95.27) / LLM SDK leak 0 / Chromium chromium-1217 installed / **`style={{` baseline = 80 occurrences across 14 files** (target → drop to only `eslint-disable`-annotated dynamic escapes)
- Calibration: NEW class `frontend-refactor-mechanical` HYBRID 0.50 (1st app, 1-data-point opens); HYBRID blend = US-A1+A2 mechanical-refactor ×0.40-0.45 ~0.70 weight + US-B1 ci-config+a11y ×0.55 ~0.15 + US-C1 closeout ×0.80 ~0.15 ≈ 0.48 ≈ 0.50 mid-band. Day 3 retro Q2 verify ratio.

### Day 0 三-prong verify (Prong 1 path + Prong 2 content; Prong 3 schema = N/A — 0 DB/migration/ORM/API touched)

**Prong 1 — Path Verify** ✅
- 14 src feature components exist (`grep -rn "style={{" frontend/src` → 14 files, 80 occurrences — see baseline above; the precise per-file count is in the plan §Background table)
- `frontend/eslint.config.js` ✅ (ESLint 9 flat config) / `frontend/tailwind.config.ts` ✅ (`.ts` not `.js` — minor path note) / `frontend/STYLE.md` ✅ / `frontend/CONVENTION.md` ✅
- `frontend/tests/e2e/a11y/a11y-scan.spec.ts` ✅ (has `.disableRules(["color-contrast"])` at L90) / `frontend/tests/e2e/visual/visual-regression.spec.ts` ✅ + `visual-regression.spec.ts-snapshots/` has all 6 `*-chromium-linux.png` (admin-tenants / app-shell / auth-login / cost-dashboard / governance / verification-recent — committed by 57.14 PR #135) ✅
- `docs/03-implementation/agent-harness-planning/16-frontend-design.md` ✅ (**path note**: it's at `agent-harness-planning/16-frontend-design.md`, NOT under `phase-57-frontend-saas/` — plan/checklist Related lines should reference the correct path)
- `.claude/rules/sprint-workflow.md` ✅

**Prong 2 — Content Verify** (drift findings → D-PRE table below)
- `eslint.config.js` plugins = `@typescript-eslint` / `react-hooks` / `react-refresh` / `jsx-a11y`. **`eslint-plugin-react` is NOT a dep** (only `eslint-plugin-react-hooks` + `eslint-plugin-react-refresh` in package.json) → `react/forbid-dom-props` / `react/forbid-component-props` UNAVAILABLE → **D-PRE-1**: use `no-restricted-syntax` with a `JSXAttribute[name.name='style']` selector instead (dep-free, plain-ESLint; escape hatch = `// eslint-disable-next-line no-restricted-syntax -- <reason>`). `no-restricted-syntax` is not currently configured → can be added cleanly.
- `a11y-scan.spec.ts` scans `GATED_ROUTES = [/chat-v2, /cost-dashboard, /sla-dashboard, /admin-tenants, /tenant-settings, /governance, /verification, /loop-debug, /memory]` via `mockApi(page, mockAuthMe)` (the 57.14 hermeticity helper: catch-all `**/api/v1/**` → 503, then `/auth/me` → 200) → the data-driven content of the migration-target components (`CostBreakdownTable` rows, `TenantList*` rows, `ApprovalList` items, `SLAMetricsCard`) renders as `<ErrorRetry>` not populated UI → **D-PRE-2**: re-enabling `color-contrast` may already be ≈green (the offenders the disable-comment names — chat-v2 `ToolCallCard`/`MessageList` panels — may not actually render under mockApi-503 either; the disable may be conservative). Verify in US-B1: re-enable → run → if green, the cleanup is still valuable (convention + the low-contrast hex IS in the source); if red, the offenders self-identify → confirm among the 14 files or log `AD-Color-Contrast-Round2`.
- `STYLE.md` already has §1 "Tailwind Utility-First" (with "Rules" + "Migration precedent Sprint 57.9 US-2") / §2 "Color Tokens" (incl. shadcn semantic tokens / "Preferred over arbitrary values" / "When arbitrary values are acceptable") / §3 "Risk Badge Palette" (with "Reference component" + "Future codification candidate") / §4 Typography / §5 Spacing / §6 Skeleton / §7 Empty State / §8 Error Retry → **D-PRE-3**: the §"Inline styles" guard content should *extend* §1 "Rules" (lint guard reference) + add an escape-hatch sub-section, NOT a new top-level §; and the `ApprovalCard` `riskColor` migration must ALIGN with §3 "Risk Badge Palette" (read §3 + its "Reference component" before mapping risk colours in US-A2).
- No vitest spec asserts `toHaveStyle(...)` / `.style` on the 14 components (`grep -rn "toHaveStyle\|\.style\b" frontend/src/features --include="*.test.tsx"` → 0 hits) → **D-PRE-4** 🟢: migration won't break unit tests via style-literal assertions (will still verify other assertions per-file in US-A2).
- 14 files' `style={{}}` rough static-vs-dynamic ratio (sampled `CostBreakdownTable` / `ApprovalCard` / `SubagentTree` / `TenantListPagination`): ~90% static (`padding`/`textAlign`/`color: "#hex"`/`borderBottom`/`fontStyle`/`width: "100%"`/`borderCollapse`/`marginTop`) → trivial Tailwind map; ~5-10 dynamic (`SubagentTree` `marginLeft: depth*12` / `ApprovalCard` `color: riskColor` / `SLAMetricsCard` bar widths) → CSS-custom-property or finite-class-set strategy.

**Prong 3 — Schema Verify**: N/A (0 DB / migration / ORM model / API endpoint touched this sprint).

### D-PRE drift catalog

| ID | Severity | Finding | Implication |
|----|----------|---------|-------------|
| D-PRE-1 | 🟡 (approach shift, ≤5% scope) | `eslint-plugin-react` not a dep → `react/forbid-dom-props` unavailable | Use `no-restricted-syntax` `JSXAttribute[name.name='style']` selector (dep-free); escape hatch `// eslint-disable-next-line no-restricted-syntax -- <reason>`. Plan §Technical Spec + §US-B1 + checklist 2.2 + §Risks updated to reflect this. Same goal ("no-inline-style lint guard"), different primitive — no scope change. |
| D-PRE-2 | 🟡 | a11y-scan uses `mockApi`-503 → data-driven migration targets render as `<ErrorRetry>` not populated UI; the `color-contrast` disable may be conservative | Re-enabling `color-contrast` may already be ≈green; verify in US-B1. If green → cleanup still valuable (convention + the hex IS in source). If red → offenders self-identify → confirm ⊆ 14 files or log `AD-Color-Contrast-Round2`. Plan §Risks already covers the "out-of-scope violation" case. |
| D-PRE-3 | 🟢 | `STYLE.md` already has §1 Rules / §2 Color Tokens / §3 Risk Badge Palette | §"Inline styles" guard → extend §1 Rules + add escape-hatch sub-section (not a new top-level §); `ApprovalCard` riskColor migration must align with §3 "Risk Badge Palette" + its "Reference component" — read §3 before US-A2 maps risk colours. |
| D-PRE-4 | 🟢 | No vitest asserts inline-style literals on the 14 components | Migration won't break unit tests via style assertions (Risk-matrix row "vitest asserts inline style literal" probability lowered to ~0; still verify other assertions per-file). |

**Go/no-go**: findings shift scope by < 5% (D-PRE-1 is an implementation-primitive swap, same deliverable; D-PRE-2/3/4 are de-risking / alignment notes) → **GO for Day 1**. Plan §Technical Spec + §US-B1 + §Risks + checklist 2.2 updated to use `no-restricted-syntax`; plan/checklist Related-line path for `16-frontend-design.md` corrected.

### Day 0 commit
- (pending) `chore(sprint-57-15, Day 0): plan + checklist + 三-prong baseline`

### Remaining for Day 1
- US-A1: per-file triage of all 14 files → migration table in this file (Day 1 entry)
- US-A2 start: chat-v2 5 files (`ApprovalCard` / `ToolCallCard` / `ChatLayout` / `MessageList` / `SubagentTree`) — the `color-contrast` re-enable prerequisite; `ApprovalCard` riskColor per STYLE.md §3

### Notes
- Tailwind config is `tailwind.config.ts` (not `.js`).
- `16-frontend-design.md` lives at `agent-harness-planning/16-frontend-design.md` (top level), not under `phase-57-frontend-saas/`.
