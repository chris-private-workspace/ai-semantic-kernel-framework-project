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
- `96877e11` `chore(sprint-57-15, Day 0): plan + checklist + 三-prong baseline` ✅

### Notes
- Tailwind config is `tailwind.config.ts` (not `.js`).
- `16-frontend-design.md` lives at `agent-harness-planning/16-frontend-design.md` (top level), not under `phase-57-frontend-saas/`.

---

## Day 1 — 2026-05-11 — US-A1 triage (in progress) + ⚠️ scope finding

### Smoke probe (deferred 0.5 items)
- `npm run lint` → silent (0 warnings/errors) ✅ baseline confirmed
- (vitest + a11y-scan smoke run at migration start)

### US-A1 triage — chat-v2 / subagent group (5 files read: ApprovalCard / ToolCallCard / ChatLayout / MessageList / SubagentTree)

Read the 5 files. They do NOT use a handful of `style={{...}}` inline literals — they use the **`const styles: Record<string, CSSProperties> = {...}` stylesheet-object pattern** + helper functions returning `CSSProperties` (`ApprovalCard`: `cardStyle`/`headerStyle`/`buttonRow` consts + `buttonStyle(kind)` + `decisionBadgeStyle(decision)` + `RISK_COLOR` map; `ToolCallCard`: `styles` record (7 keys) + `badge(color)` + `statusColor(entry)`; `ChatLayout`: `styles` record (5 keys); `MessageList`: `styles` record (12 keys); `SubagentTree`: 1 `style={{ marginLeft: depth*12 }}`). So per file the real surface is much larger than the `style={{` grep suggested:

| File | `style={{` (grep) | ALL `style=` JSX attrs | + module-level stylesheets/helpers | hardcoded hex (a11y-relevant) |
|------|-------------------|------------------------|-----------------------------------|-------------------------------|
| `chat_v2/ApprovalCard.tsx` | 4 | **11** | `cardStyle` `headerStyle` `buttonRow` consts + `buttonStyle()` + `decisionBadgeStyle()` + `RISK_COLOR` | `#666` (low-contrast) + `#c62828` `#2e7d32` `#ed6c02` `#d84315` `#b71c1c` `#1976d2` `#fff8e1` etc. |
| `chat_v2/ToolCallCard.tsx` | 3 | **12** | `styles` record (7) + `badge()` + `statusColor()` | `#7c8696` `#3b4252` `#d8dde7` `#f4f6fa` `#5a78c8` `#c43d3d` `#2f9c59` etc. |
| `chat_v2/ChatLayout.tsx` | 2 | **8** | `styles` record (5) | `#e2e6ee` `#fbfbfd` `#3b4252` `#7c8696` `#5a6377` — also has `gridTemplateAreas` / `gridTemplateColumns: "240px 1fr 280px"` / `calc(100vh - 6.5rem)`. **⚠️ file header says "Phase 58+ Tailwind migration when sessions sidebar + inspector get real content from 51.x / 52.x"** — explicitly deferred. |
| `chat_v2/MessageList.tsx` | 2 | **8** | `styles` record (12) | `#5a78c8` `#fff` `#d8dde7` `#2c2c33` `#7c8696` `#9aa3b3` etc. |
| `chat_v2/InputBar.tsx` | 0 | **10** | (not yet read — all `style={objVar}`) | TBD — **⚠️ this file is NOT in the CLAUDE.md carryover list** but matches `style=` |
| `subagent/SubagentTree.tsx` | 1 | **1** | — | (none — only `marginLeft: depth*12` dynamic) |

### ⚠️ D-DAY1-1 — scope finding: the plan undercounted (>20% shift)

**Plan §Background said "80 `style={{}}` / 14 files".** Re-survey with `grep -rEn "style=\{" frontend/src --include="*.tsx"`: **15 files** (InputBar.tsx was missed — `chat_v2/components/InputBar.tsx`, 10 `style={objVar}` attrs) with **133 `style=` JSX attrs** (80 inline-literal + 53 `style={objVar}`/`style={fn()}`), plus ~6 module-level `Record<string, CSSProperties>` stylesheet objects + ~5 helper functions returning `CSSProperties` that must be deleted. The `no-restricted-syntax` `JSXAttribute[name.name='style']` guard flags ALL `style=` (whether the value is an inline object literal, a variable, or a fn call) — so to make the guard pass at `error` level, ALL 133 must be migrated (or carry `eslint-disable`).

Per-file `style=` attr counts (descending): TenantSettingsView 27 / TenantListTable 15 / CostBreakdownTable 14 / TenantSettingsEditForm 13 / ToolCallCard 12 / ApprovalCard 11 / InputBar 10 / ChatLayout 8 / MessageList 8 / TenantListFilters 5 / SLAMetricsCard 4 / MonthPicker 2 / TenantListPagination 2 / ApprovalList 1 / SubagentTree 1.

This is a **>20% scope shift** (66% more occurrences + 1 more file + the work-per-occurrence is higher for the chat-v2 stylesheet-object files than for 1-line literals) → per `.claude/rules/sprint-workflow.md` §Step 2.5 ("Findings shift scope by 20-50% → revise plan §Acceptance Criteria + §Workload, re-confirm with user") → **paused for a scope decision before migrating**. Plus the `ChatLayout.tsx` "Phase 58+ defer" header note is a per-file wrinkle.

**Scope options presented to user**:
- **(A) Full sweep** — 15 files / 133 `style=` attrs + stylesheets/helpers; guard `error` everywhere; extend Day 0-3 → Day 0-4; ~6-9 hr committed.
- **(B) Tiered (a11y + visual first, Round2 the rest)** — this sprint: the files that gate the `color-contrast` re-enable + the 3 visual baselines = `ApprovalCard` / `ToolCallCard` / `MessageList` / `SubagentTree` (chat-v2 a11y) + `CostBreakdownTable` / `MonthPicker` / `ApprovalList` / `TenantListTable` / `TenantListPagination` / `TenantListFilters` (visual snapshots + a11y) ≈ 10 files / ~70 attrs; defer `ChatLayout` (Phase-58 note) / `InputBar` / `TenantSettingsView` / `TenantSettingsEditForm` / `SLAMetricsCard` ≈ 5 files / ~63 attrs → `AD-Inline-Style-Cleanup-Sweep-Round2` with file-level `/* eslint-disable no-restricted-syntax -- AD-Inline-Style-Cleanup-Sweep-Round2 */` + reason; guard `error` for everything else; Day 0-3 holds; ~4-6 hr.

→ **user chose (B) Tiered** (2026-05-11). Revised scope:
- **This sprint (10 files)**: `ApprovalCard` / `ToolCallCard` / `MessageList` / `SubagentTree` (chat-v2 a11y prereq) + `CostBreakdownTable` / `MonthPicker` / `ApprovalList` / `TenantListTable` / `TenantListPagination` / `TenantListFilters` (3 visual snapshots + a11y). ≈ 70 `style=` attrs.
- **Deferred → `AD-Inline-Style-Cleanup-Sweep-Round2` (5 files)**: `ChatLayout` (header's Phase-58 defer note) / `InputBar` / `TenantSettingsView` (27) / `TenantSettingsEditForm` (13) / `SLAMetricsCard` (4). ≈ 63 `style=` attrs. These get a file-level `/* eslint-disable no-restricted-syntax -- AD-Inline-Style-Cleanup-Sweep-Round2: inline styles pending tiered migration */` at the top so the `error`-level guard passes for everything else. Logged in retrospective Q4.
- Guard `no-restricted-syntax` = `error`; `color-contrast` axe rule re-enabled; 3 visual baselines (cost-dashboard / governance / admin-tenants) refreshed via the 57.14 workflow. Day 0-3 holds; calibration unchanged (~4-6 hr committed).
- Plan §"Day 1 scope revision" + checklist §1.2/§2.1/§2.3 updated accordingly.

### US-A2 — chat-v2 / subagent migration (4 files: ApprovalCard / ToolCallCard / MessageList / SubagentTree) — DONE 2026-05-11

- **`SubagentTree.tsx`** — was already ~all-Tailwind; only `style={{ marginLeft: depth*12 }}` left → finite `DEPTH_INDENT = ["ml-0","ml-3","ml-6","ml-9","ml-12","ml-[60px]"]` literal-string array (Tailwind JIT sees them; depth bounded by `MAX_DEPTH=5`) + `className={cn("space-y-1", DEPTH_INDENT[depth] ?? "ml-[60px]")}` + `import { cn } from "../../../lib/utils"`. **No inline style left, no eslint-disable needed.** MHist +1.
- **`ApprovalCard.tsx`** — full rewrite (4 `style={{}}` + `cardStyle`/`headerStyle`/`buttonRow` consts + `buttonStyle(kind)` + `decisionBadgeStyle(decision)` + `RISK_COLOR` map all removed). New: `RISK_TEXT_CLASS` map per STYLE.md §3 (`text-green-700`/`text-orange-600`/`text-orange-800`/`text-red-800` for LOW/MEDIUM/HIGH/CRITICAL, fallback `text-muted-foreground`) + `DECISION_BADGE_CLASS` map (`bg-success`/`bg-danger`/`bg-warning`, fallback `bg-muted-foreground`); card `my-2 rounded-md border border-warning bg-warning/10 px-4 py-3 text-[0.95rem]`; header `mb-1.5 font-semibold`; risk span `cn("font-bold", riskTextClass)`; request-id `text-sm text-muted-foreground` (was `#666` low-contrast → now WCAG-AA token); decision badge `cn("inline-block rounded-full px-2 py-0.5 text-xs font-bold text-white", decisionBadgeClass)`; error alert `mt-1.5 text-sm text-danger`; buttons `cursor-pointer rounded border-0 bg-success/bg-danger px-3 py-1 text-sm font-semibold text-white` + link `bg-transparent text-primary underline`. MHist +1; header comment + Related updated. **No inline style left.**
- **`ToolCallCard.tsx`** — full rewrite (3 `style={{}}` + `styles` record (7 keys) + `badge(color)` + `statusColor(entry)` removed). `statusColor`→`statusBadge` returns `{label, cls}` (`bg-primary`/`bg-danger`/`bg-success`); card `overflow-hidden rounded-md border border-border bg-card font-mono text-[13px]`; header `flex cursor-pointer select-none items-center gap-2.5 border-b border-border bg-muted px-3 py-2`; tool name `font-semibold text-foreground`; "X ms" + chevron `text-[11px] text-muted-foreground`; badge `cn("ml-auto rounded px-2 py-0.5 text-[11px] uppercase tracking-wide text-white", status.cls)`; body `px-3.5 py-2.5`; labels `mb-1 text-[11px] text-muted-foreground` (+ `mt-2` for the Result/Error label); `pre` per STYLE.md §4 (`m-0 whitespace-pre-wrap break-words rounded border border-border bg-muted px-2 py-1.5`; `font-mono` inherited from card). MHist +1; stale "Tailwind retrofitted in Phase 53.4" header comment removed; Related += STYLE.md §4. **No inline style left.**
- **`MessageList.tsx`** — full rewrite (2 `style={{}}` + `styles` record (12 keys) removed). `BUBBLE_BASE` const `whitespace-pre-wrap break-words rounded-xl px-3.5 py-2.5 text-sm leading-normal`; user bubble `${BUBBLE_BASE} rounded-br bg-primary text-white` in `<div className="max-w-[min(720px,90%)] self-end">`; assistant bubble `${BUBBLE_BASE} rounded-bl border border-border bg-card text-foreground` in `<div className="max-w-[min(720px,90%)] w-[min(720px,90%)] self-start">`; thinking `mb-1.5 text-xs italic text-muted-foreground`; tool-calls `mt-2.5 flex flex-col gap-2`; list `flex flex-1 flex-col gap-4 overflow-y-auto p-6`; empty `p-8 text-center text-sm text-muted-foreground`. MHist +1. **No inline style left.**

**Verify**: `npm run lint` silent (incl `--report-unused-disable-directives` → no stale disables) ✅ / `npm run build` main bundle `index-FIvzMl_y.js` **297.89 kB gzip 95.27 — byte-identical to baseline** (removed inline-style objects ≈ neutral; Tailwind classes already in bundle) ✅ / `npm run test` (vitest) **57 files / 236 pass — unchanged** ✅ / `npm run e2e -- a11y/a11y-scan.spec.ts` → **2 passed** (chat-v2 in GATED_ROUTES; structural a11y rules unaffected; `color-contrast` still disabled — re-enable is §2.2/Day 2) ✅ / `git diff` only the 4 src files + docs; 0 component-logic change.

**Tailwind ↔ original equivalence notes** (for the Day 3 visual-baseline eyeball — none of these 4 are in a visual snapshot, but recording the mapping discipline): `p-2`=0.5rem, `px-3 py-2`=0.75/0.5rem, `gap-2.5`=0.625rem, `mt-2`=0.5rem, `mb-1.5`=0.375rem, `rounded`=0.25rem(4px), `rounded-md`=0.375rem(6px), `rounded-xl`=0.75rem(12px) — all byte-equivalent to the original literals. Colour changes (intentional, a11y): `#666`→`text-muted-foreground` (WCAG-AA), `#7c8696`→`text-muted-foreground`, `#3b4252`/`#2c2c33`→`text-foreground`, `#d8dde7`/`#ebeef4`→`border-border`, `#fff`→`bg-card`, `#f4f6fa`/`#f8fafc`→`bg-muted`, `#5a78c8`→`bg-primary`, `#2e7d32`/`#2f9c59`→`bg-success`, `#c62828`/`#c43d3d`→`bg-danger`/`text-danger`, `#ed6c02`→`border-warning`, `#fff8e1`→`bg-warning/10`, risk levels→§3 classes.

### Day 1 commit
- (pending) `refactor(sprint-57-15, Day 1): US-A1 scope revision (B-tiered) + US-A2 chat-v2/subagent inline styles → Tailwind`

### Remaining for Day 2
- US-A2 §2.1: 6 visual/a11y files — `CostBreakdownTable` / `MonthPicker` / `ApprovalList` / `TenantListTable` / `TenantListPagination` / `TenantListFilters` → Tailwind (these affect the cost-dashboard / governance / admin-tenants visual snapshots)
- §2.3: 5 Round2 files get a top-of-file `/* eslint-disable no-restricted-syntax -- AD-Inline-Style-Cleanup-Sweep-Round2: ... */` (`ChatLayout` / `InputBar` / `TenantSettingsView` / `TenantSettingsEditForm` / `SLAMetricsCard`)
- US-B1: `eslint.config.js` += `no-restricted-syntax` `JSXAttribute[name.name='style']` (`error`); `a11y-scan.spec.ts` remove `.disableRules(["color-contrast"])`; `STYLE.md` §1 extend + escape-hatch sub-§

---

## Day 2 — 2026-05-11 — US-A2 §2.1 (5 visual/a11y files) + §2.3 (5 Round2 disables) + US-B1 (guard + a11y re-enable + STYLE.md)

### US-A2 §2.1 — visual-snapshot + a11y files migrated (5 files; ApprovalList was a no-op)
- **`CostBreakdownTable.tsx`** (14 `style={{}}`) — `<p>` `italic text-muted-foreground` (`#666`→AA); `<table>` `mt-4 w-full border-collapse`; thead `border-b-2 border-border text-left`; cells `p-2`/`p-2 text-right`; rows `border-b border-border`. MHist +1. **The cost-dashboard visual snapshot renders this `<p>`** (mocked `by_type` is empty → `rows.length===0`) → its colour changes (`#666`→token) ⇒ cost-dashboard baseline will change.
- **`MonthPicker.tsx`** (2) — label `inline-flex items-center gap-2`; input `px-2 py-1` (= `padding 0.25rem 0.5rem` byte-equivalent → no pixel change); `fontFamily:"inherit"` dropped (already inherits). MHist +1.
- **`ApprovalList.tsx`** — **NO-OP**: the earlier grep "1" was the JSDoc text `style={{}}`; the file is fully Tailwind (57.9). Not touched. ⇒ **governance visual snapshot UNCHANGED**.
- **`TenantListTable.tsx`** (15 `style=` incl `style={objVar}` + `BADGE_STYLE`/`TH_STYLE`/`TD_STYLE` + `stateBadgeColor`/`planBadgeColor`) — `stateBadgeColor`→`stateBadgeClass` (`bg-success`/`bg-warning`/`bg-muted-foreground`); `planBadgeColor`→`planBadgeClass` (`bg-primary`/`bg-muted-foreground`); `BADGE_CLASS`="rounded px-2 py-0.5 text-sm whitespace-nowrap text-white" / `TH_CLASS`="border-b-2 border-border p-2 text-left font-semibold" / `TD_CLASS`="border-b border-border p-2"; `#666` date cell→`text-sm text-muted-foreground`; `cn()` for badge + TD; `import { cn }`. MHist +1. (Table itself not in the snapshot — mocked `items:[]`→`<EmptyState>`.)
- **`TenantListPagination.tsx`** (2 incl `ROW_STYLE`) — `mt-4 flex items-center gap-3 py-2`; `style={{ color:"#666", fontSize:"0.9rem" }}`→`text-sm text-muted-foreground`. MHist +1. **The "0-0 of 0" text IS in the admin-tenants snapshot** → colour changes.
- **`TenantListFilters.tsx`** (5 `style=` incl `ROW_STYLE`/`LABEL_STYLE`) — bar `flex flex-wrap items-end gap-3 rounded border border-border bg-muted/30 p-3` (`#fafafa`→`bg-muted/30`, `#ddd`→`border-border`); `LABEL_CLASS`="flex flex-col text-sm font-semibold text-muted-foreground" (`#444`→token per §2 "labels"); search `min-w-64`. MHist +1. **The filter bar IS in the admin-tenants snapshot** → bg/border colour changes. ⇒ admin-tenants baseline will change.
- 0 `tailwind.config.ts` change (every colour mapped to an existing token/shade). `grep -rEn "style=\{" frontend/src` → only the 5 Round2 files now.

### §2.3 — 5 Round2 files: top-of-file (line 1) `/* eslint-disable no-restricted-syntax -- AD-Inline-Style-Cleanup-Sweep-Round2: ... */`
- `ChatLayout.tsx` (reason: header notes Phase 58+ migration when sidebar/inspector get real content) / `InputBar.tsx` (chat-v2 batch) / `SLAMetricsCard.tsx` (incl dynamic bar widths → CSS-var in Round2) / `TenantSettingsEditForm.tsx` (tenant-settings batch) / `TenantSettingsView.tsx` (tenant-settings batch). No MHist change — the disable directive's `-- reason` IS the WHY note; these files are explicitly *not* being migrated.

### US-B1 — guard + color-contrast re-enable + STYLE.md
- `eslint.config.js` — NEW `"no-restricted-syntax": ["error", { selector: "JSXAttribute[name.name='style']", message: "..." }]` + header comment. (`react/forbid-dom-props` unavailable — `eslint-plugin-react` not a dep; D-PRE-1.)
- `a11y-scan.spec.ts` — `color-contrast` re-enabled for **8/9 gated routes + auth pages**; `/chat-v2` keeps it disabled (ChatLayout Round2 `#7c8696`-on-`#fbfbfd` ≈ 3.7:1 < AA). `scan(page, label, allowLowContrast=false)`; loop passes `route === "/chat-v2"`. MHist +1. **0 new out-of-scope violations on the other 8 routes** — the migration's tokens all pass AA. (`AD-Color-Contrast-Round2` subsumed by `AD-Inline-Style-Cleanup-Sweep-Round2` — migrating ChatLayout closes the `/chat-v2` gap.)
- `STYLE.md` — §1 "Rules" bullet → references the `no-restricted-syntax` guard; NEW "### Inline-style escape hatches (dynamic values)" sub-§ (finite class lookup w/ §3 cross-ref + `ApprovalCard`/`SubagentTree` examples / CSS custom property + arbitrary value / last-resort `eslint-disable` + reason / whole-legacy-file `/* eslint-disable */` → Round2). MHist += 57.15; `Last Modified` → 2026-05-11.

### Hotfix during verify (D-DAY2-1)
Full `npx playwright test` flagged `chat/approval-card.spec.ts:108` "CRITICAL → dark red" — asserts `getComputedStyle(riskTextSpan).color === "rgb(183,28,28)"` (= `#b71c1c`). The migration had used `text-red-800` (`#991b1b`). **Fix**: `ApprovalCard.tsx` `RISK_TEXT_CLASS` → `text-[#2e7d32]`/`text-[#ed6c02]`/`text-[#d84315]`/`text-[#b71c1c]` (canonical 53.5 hex via Tailwind arbitrary-value classes — matches `governance/components/ApprovalList.tsx`, the §3 reference component + the named "test sentinel"; STYLE.md §3 lists `text-[#hex]` as acceptable for the risk palette). Not "change the spec to pass" — the spec asserts the canonical palette and the canonical palette is now what's rendered. Re-verified: lint silent / build 297.89 kB / `approval-card.spec.ts` 4 pass / full e2e 40 pass 7 skip 0 fail.

### Verify (Day 2)
- `npm run lint` silent (0 error, incl `--report-unused-disable-directives` — the 5 Round2 file-level disables are *used*; the new rule fires only inside them) ✅
- `npm run build` main bundle **297.89 kB gzip 95.27 — unchanged** ✅
- `npm run test` (vitest) **57 files / 236 pass — unchanged** ✅
- `npm run e2e -- a11y/a11y-scan.spec.ts` → **2 passed** (color-contrast on for 8/9 routes; 0 new violations) ✅
- `npx playwright test` (full) → **40 passed / 7 skipped / 0 failed** (7 skip = 1 connectivity + 6 visual-regression opt-in on Windows) ✅
- `git diff --stat main..HEAD` (after Day 2 commit) — only `frontend/**` + `docs/**`; **0 `backend/` changes** ✅

### Day 2 commit
- `62cba647` `feat(sprint-57-15, Day 2): US-A2 §2.1 (5 visual/a11y files) + §2.3 (5 Round2 disables) + US-B1 (no-inline-style guard + color-contrast re-enabled 8/9 + STYLE.md)` ✅

---

## Day 3 — 2026-05-11 — US-C1: validation sweep + visual baseline workflow + retrospective + memory + doc syncs + PR

### Validation sweep
- `npm run lint` 0 error (incl new `no-restricted-syntax` guard + `--report-unused-disable-directives` — the 5 Round2 file-level disables are *used*) ✅
- `npm run build` main bundle **297.89 kB gzip 95.27 — byte-identical** ✅
- `npm run test` (vitest) **57 files / 236 pass — unchanged** ✅
- `npx playwright test` (full) **40 pass / 7 skip / 0 fail** ✅
- Backend: `git diff --stat main..HEAD` = **0 `backend/` changes** (only `frontend/**` + `docs/**`) → backend baselines unchanged (pytest 1676 pass+4 skip / mypy 0/306 / 9-9 V2 lints / 0 LLM SDK leak); not re-run ✅

### Visual baseline workflow (first real e2e use of the 57.14 mechanism)
- `git push -u origin feature/sprint-57-15-inline-style-cleanup` ✅ (the `push`-triggered `e2e` CI run got concurrency-cancelled — the PR's CI re-runs it)
- `gh workflow run "Playwright E2E" --ref feature/sprint-57-15-inline-style-cleanup` → `visual-baseline` job **run `25644392922`** ✅ — all steps green ("Generate / update visual baselines" + "Open a PR with the updated baselines (if changed)" + "Upload generated baselines as artifact")
- `gh run download 25644392922 -n visual-baselines` → `sha256sum` compare to the committed `*-chromium-linux.png` → **all 6 SAME** → the workflow's `git diff --cached --quiet` was true → it committed nothing / opened no `chore/visual-baselines-*` PR. **No baseline commit this sprint.**
- **Why 0 diffs**: the migrated components (`CostBreakdownTable` "No cost entries" `<p>`, `TenantListFilters` bar, `TenantListPagination` "0-0 of 0") aren't visible in any of the 6 snapshots — `visual-regression.spec.ts` screenshots immediately after `getByTestId("app-shell")` is visible, *before* the data fetch resolves → it captures the loading/`<TableSkeleton>` state (design-system, untouched). ⇒ the 57.14 `visual-baseline` workflow_dispatch path is validated working (it diffed → found nothing → did nothing — didn't blindly commit a re-render). No `AD-Visual-Baseline-Refresh-57.15` needed; companion follow-up (`waitForLoadState` in visual specs) noted in retro Q4, out of scope.

### Closeout deliverables
- NEW `retrospective.md` (Q1-Q7 + 8-point self-check + rolling-planning self-check) ✅
- NEW `memory/project_phase57_15_inline_style_cleanup.md` + `MEMORY.md` index +1 row ✅
- doc syncs: `16-frontend-design.md` V2 Ship Timeline +1 (12/N) ✅ / `.claude/rules/sprint-workflow.md` calibration matrix +1 row (`frontend-refactor-mechanical` 0.50 1-data-point ratio ~1.7 OVER band KEEP) + matrix MHist ✅ / `STYLE.md` §1 + escape-hatches sub-§ (done Day 2) ✅ / checklist + plan Status → Closed + MHist ✅
- Deferred post-merge (not in this PR): `CLAUDE.md` (main HEAD / Latest Sprint / Next Phase 候選 — remove `AD-Inline-Style-Cleanup-Sweep`, add `AD-Inline-Style-Cleanup-Sweep-Round2`; a11y color-contrast on for 8/9) + `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md` §第八部分

### Day 3 commit + PR
- `75e0f4e3` `chore(sprint-57-15, Day 3): retrospective + doc syncs + closeout` ✅
- **PR #137** opened (https://github.com/laitim2001/ai-semantic-kernel-framework-project/pull/137); CI pending (the `visual-baseline` job correctly `skipping` on PR events); merge deferred to user. + a `<bookkeeping>` commit fills PR# into checklist §3.7 + this file.

### Drift catalog (Day 1-3)
| ID | Severity | Finding | Resolution |
|----|----------|---------|------------|
| D-PRE-1 | 🟡 | `eslint-plugin-react` not a dep → `react/forbid-dom-props` unavailable | guard uses built-in `no-restricted-syntax` `JSXAttribute[name.name='style']` (dep-free) — same deliverable |
| D-PRE-2 | 🟡 | a11y-scan uses mockApi-503 → data-driven components render as `<ErrorRetry>` | color-contrast re-enable is partial — 8/9 routes (the data-driven targets aren't scanned anyway; `/chat-v2` is the only one with always-rendered low-contrast inline text = ChatLayout Round2) |
| D-PRE-3 | 🟢 | `STYLE.md` already has §1 Rules / §3 Risk Badge Palette | §1 extended (not new top-level §); `ApprovalCard` riskColor aligned with §3 |
| D-PRE-4 | 🟢 | 0 vitest asserts inline-style literals | true — but D-DAY2-1 found an *e2e* spec that does |
| D-DAY1-1 | 🟡 (>20% scope) | plan 80/14 vs reality 15 files / 133 `style=` attrs + ~6 stylesheets + ~5 helper fns | user chose (B) Tiered: 10 files this sprint, 5 → NEW `AD-Inline-Style-Cleanup-Sweep-Round2` (file-level disabled) |
| D-DAY1-2 | 🟢 | `ApprovalList.tsx` grep "1" was a false positive (JSDoc text) | no-op — already 57.9-Tailwind |
| D-DAY2-1 | 🟢 | `approval-card.spec.ts:108` asserts CRITICAL risk colour == `#b71c1c`; first cut used `text-red-800` (#991b1b) | `ApprovalCard` `RISK_TEXT_CLASS` → `text-[#hex]` (canonical 53.5 palette, matches `governance/ApprovalList.tsx` the §3 ref) — align spec target with the canonical palette, not change the spec |
