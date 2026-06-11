# Sprint 57.30 — AD-Chatv2-Verbatim-Repoint + Shell-Hotfix-UserMenu-Avatar

**File**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-30-plan.md`
**Purpose**: Plan for Sprint 57.30 — second Phase-2 per-page verbatim-CSS re-point (`/chat-v2`) + bundle the carryover shell hotfix (UserMenu Radix-drop + topbar avatar 36→26 split + topbar icon audit) that 57.29 left as `AD-UserMenu-Mockup-Structural-Deltas`.
**Category**: Sprint planning / Phase 57+ Frontend SaaS
**Scope**: Phase 57+ Frontend SaaS — Phase-2 per-page re-point epic, 2nd application
**Created**: 2026-05-23
**Last Modified**: 2026-05-23
**Status**: Draft → awaiting user approval

> **Modification History**
> - 2026-05-23: Initial draft (Sprint 57.30 Day 0) — Shell hotfix + chat-v2 verbatim re-point (Option B per user selection 2026-05-23)

---

## Sprint Goal

Land the **second Phase-2 per-page verbatim-CSS re-point** on `/chat-v2` (Operator chat — the product's flagship route) and **clear the carryover shell-hotfix debt** (`AD-UserMenu-Mockup-Structural-Deltas` + topbar avatar 36→26 split + topbar icon audit) that Sprint 57.29 left open.

`/chat-v2` is the highest-complexity AppShellV2 route (19 production .tsx, 3-col shell + Inspector 4-tab + Turn Block Model from Sprint 57.21 Phase-1). The structure stays; only the CSS / inline-style literals are re-pointed to consume mockup `page-chat.jsx` + `styles-mockup.css` verbatim — same method validated on `/overview` in Sprint 57.29.

The shell hotfix is folded in (not split into a separate sprint) because (a) it's small (~3-4 hr), (b) the UserMenu Radix-drop touches the same shell `/chat-v2` consumes through `<AppShellV2>`, and (c) it un-blocks every future Phase-2 page (the drift is in the global shell, not per-page).

---

## Background

### Why Sprint 57.30 (this sprint)

Sprint 57.29 closed the **first Phase-2 per-page verbatim-CSS re-point** on `/overview` with PARITY verdict and 0 catastrophic / 0 structural regression across the 22-route sweep, validating the method (verbatim copy mockup CSS class names + inline-style literals; preserve component-logic layer). The retrospective opened 4 carryover ADs:

- **`AD-UserMenu-Mockup-Structural-Deltas`** — UserMenu dropdown drops down with a visible gap from the topbar instead of flush (mockup `top: 50` is 2px from `topbar` height `48`). Root cause: Sprint 57.13 US-B3 swapped the mockup `useDismiss` popover for Radix `<DropdownMenu>` for "free focus trap / keyboard nav"; Radix's floating-ui portal positioning overrides the verbatim `position: absolute; top: 50; right: 12` styles, so the dropdown anchors to the avatar-button bottom edge (~y=37) + Radix `sideOffset` ≈ 4px, landing **below** the topbar bottom edge (y=48) → visible "drop down" gap.
- **`AD-Inline-Style-Rule-vs-Verbatim-Method`** — escape-hatch lint rule conflicts with mockup-fidelity verbatim policy.
- **`AD-MockupFidelity-Guard-TokenRelative-Oklch`** — CI check-mockup-fidelity guard token tolerance.
- **`AD-Overview-PreExisting-Route-Crashes`** — 3 routes (`/subagents` `/memory` `/verification`) crash with pre-existing content bugs; not 57.29 regressions.

User audit 2026-05-23 also surfaced a second drift `AD-UserMenu-Mockup-Structural-Deltas` did not catalogue: the topbar **trigger avatar** is 36×36 px (production reuses `avatarStyle` for both the trigger button and the in-panel identity card avatar), but mockup `styles.css:387-394 .avatar` is **26×26 px**; identity-card avatar in mockup `topbar-overlays.jsx:347-360` is **36×36 px**. Production conflates the two — they share one style object.

Per the Phase-2 epic plan (`claudedocs/1-planning/next-phase-candidates.md`), `/chat-v2` is next: the product's flagship page, structurally most complex, highest visual-fidelity ROI. Sprint 57.21 already did the **Phase-1 structural rewrite** (Turn Block Model + 3-col shell + Inspector 4-tab + Composer scaffolding); Phase-2 is the verbatim CSS re-point on top of that scaffolding.

### Why bundle shell hotfix + chat-v2 page re-point in one sprint (Option B, user-approved 2026-05-23)

User selected Option B (Shell hotfix + 1 page re-point) out of 4 scope options (vs. hotfix-only / hotfix + page + crash fix / hotfix-only minimal). Rationale:

- Shell hotfix is global — it un-blocks every future Phase-2 page (the UserMenu drift surfaces on every page that consumes `<AppShellV2>`, not just `/chat-v2`).
- Doing shell first in Day 1 → chat-v2 starts Day 2 with the corrected shell → fidelity verification at Day 5 measures the page on top of a corrected baseline (no "shell drift contamination" in the chat-v2 PARITY verdict).
- Bundling avoids a tiny ~3-4 hr standalone hotfix sprint with its own Day-0/closeout overhead (~50% of the actual code time would be ceremonial).
- Crash routes deferred — they are pre-existing content bugs unrelated to shell or chat-v2 re-point; should be a separate "page-bug-fix" class sprint with different calibration (likely `frontend-mockup-strict-rebuild` 0.60 or new `frontend-page-bug-fix` 0.45).

### Scope boundaries

**IN scope**:
- Shell hotfix Group B (UserMenu Radix-drop verbatim + topbar avatar trigger 36→26 + topbar icon audit + Vitest fixup).
- `/chat-v2` Phase-2 verbatim-CSS re-point: 19 production `.tsx` files in `frontend/src/features/chat_v2/components/` + `frontend/src/pages/chat-v2/index.tsx`.
- `mockup-ui.tsx` extension only if new primitives are needed by chat-v2 (e.g. `Composer` icons, `Inspector` tab pills) — verbatim from mockup `ui.jsx` / `page-chat.jsx`.
- 22-route regression sweep before/after + `/chat-v2` fidelity verification (computed-style + Playwright screenshot).

**OUT of scope**:
- Pre-existing crash routes (`/subagents` `/memory` `/verification`) — `AD-Overview-PreExisting-Route-Crashes` deferred to Sprint 57.31+ as a separate page-bug-fix sprint.
- Other 12 🟡 AppShellV2 routes (`orchestrator` / `loop-debug` / `state-inspector` / `cost-dashboard` / `sla-dashboard` / `admin-tenants` / `tenant-settings` / `compaction` / etc.) — per rolling planning, picked next sprint.
- Backend extension (e.g. real `/api/v1/loops` / tenant-switch API / chat session APIs) — fixture data kept where mockup uses fixture; production data path stays as Sprint 57.21 wired.
- `AD-Inline-Style-Rule-vs-Verbatim-Method` rule rewrite — deferred (lint rule policy iteration; not blocking).
- `AD-MockupFidelity-Guard-TokenRelative-Oklch` — deferred (CI guard tuning; not blocking).
- `AD-CI-7-GHA-PR-Permission` (baseline-regen workflow auto-PR step) — deferred to a separate infra sprint or repo-setting change.

### Class baseline — REUSE `frontend-verbatim-css-repoint` 0.60 (2nd application)

`frontend-verbatim-css-repoint` opened Sprint 57.29 (1st application, ratio ≈ 1.0 in [0.85, 1.20] band, 1-data-point baseline). Per `When to adjust` 3-sprint window rule, this is the **2nd application** — KEEP 0.60 baseline. Sprint 57.30 = the 2nd data point; aggregate window window opens after Sprint 57.31+ if a 3rd Phase-2 per-page re-point ships.

HYBRID weighted blend for Sprint 57.30 (the bundled scope makes the class blend a mix):

| Component | Class | Multiplier | Weight |
|-----------|-------|------------|--------|
| Day-0 三-prong + before-baseline | `audit-cycle` | 0.85 | ~10% |
| UserMenu Radix-drop verbatim (Group B) | `frontend-refactor-mechanical` | 0.45 | ~10% |
| Topbar avatar/icon audit + fixup (Group B) | `frontend-foundation-token-correction` | 0.55 | ~10% |
| chat-v2 19 components re-point (Group C+D) | `frontend-verbatim-css-repoint` | 0.60 | ~50% |
| 22-route sweep + chat-v2 fidelity verify (Group E) | `frontend-verbatim-css-repoint` | 0.50 | ~10% |
| Closeout + retro + docs | `closeout` | 0.80 | ~10% |
| **HYBRID blended baseline** | | **≈ 0.60** | |

Bottom-up estimate ~17-21 hr; calibrated commit ≈ **10-12 hr** (multiplier ≈ 0.55-0.60 blended).

### What is preserved (NOT changed)

- Sprint 57.21 Phase-1 Turn Block Model discriminated union (`UserTurn` | `AgentTurn` | `HITLTurn`) + chatStore `mergeEvent` reducer + SSE pipeline.
- 3-col shell composition (`ChatLayout` 3-col grid; `SessionList` left rail; `TurnList` center; `ChatInspector` right rail) — only the CSS / inline-style is re-pointed.
- Inspector 4-tab structure (`Overview` / `State` / `Tools` / `Verification`) — content delivery preserved; only the chrome is re-pointed.
- Block scaffolding (`ThinkingBlock` / `ToolBlock` / `VerificationBlock` / `SubagentForkBlock` / `Block` base) — Sprint 57.21 architecture, kept.
- `ApprovalCard` HITL flow + governance integration.
- `Composer` + `InputBar` keyboard handlers + auto-resize behaviour.
- All Sprint 57.21 Vitest specs that test logic / block routing / Turn discriminated union behaviour.
- 22-route AppShellV2 entries in `routes.config.ts`.
- All backend integration (`chatService` / `loopService` / `useLoopStream` SSE / `/api/v1/chat` POST).

### What gets changed (this sprint scope)

**Group B — Shell hotfix (Day 1)**:
- `UserMenu.tsx` — drop `<DropdownMenu>` Radix wrapper; port mockup `topbar-overlays.jsx` `useDismiss` hook verbatim + `<div data-topbar-overlay>` panel; preserve all keyboard interaction we still need (ESC close, click-outside close) inside the verbatim hook.
- `UserMenu.tsx` — separate the **trigger avatar** (26×26 from mockup `.avatar` class) from the in-panel **identity-card avatar** (36×36 from mockup `topbar-overlays.jsx:347`). Production conflates them today.
- `Topbar.tsx` — audit all topbar icon sizes against mockup; verify `Icon size=` literals match mockup `ui.jsx` Icon component defaults.
- `Topbar.test.tsx` / `UserMenu.test.tsx` — adapt assertions to new structure (assert `.avatar` 26×26 trigger + Radix-free dropdown semantics).

**Group C — chat-v2 shell + composer (Day 2)**:
- `pages/chat-v2/index.tsx` — re-point page-head + layout wrap to verbatim mockup `page-chat.jsx` structure.
- `features/chat_v2/components/ChatLayout.tsx` — 3-col grid verbatim from mockup `page-chat.jsx` outer layout.
- `features/chat_v2/components/ChatHeader.tsx` — re-point header bar to mockup verbatim.
- `features/chat_v2/components/SessionList.tsx` — left-rail session list verbatim from mockup.
- `features/chat_v2/components/Composer.tsx` + `InputBar.tsx` — composer container + input verbatim from mockup.

**Group D — chat-v2 turns + blocks + inspector (Day 3-4)**:
- `features/chat_v2/components/TurnList.tsx` — turn list scroll container verbatim.
- `features/chat_v2/components/turns/AgentTurn.tsx` / `UserTurn.tsx` / `HITLTurn.tsx` — turn frames verbatim from mockup turn shapes.
- `features/chat_v2/components/blocks/*.tsx` (5 files) — block visual layer verbatim.
- `features/chat_v2/components/inspector/ChatInspector.tsx` + `InspectorTurn.tsx` + `ComingSoonInspectorTab.tsx` — 4-tab chrome + inspector content verbatim.
- `features/chat_v2/components/ApprovalCard.tsx` — HITL approval visual layer verbatim.

**Group E — Regression + fidelity verify + closeout (Day 5)**:
- `route-sweep.mjs` 22-route before/after sweep.
- `/chat-v2` fidelity verification — mockup-vs-prod computed-style + Playwright screenshot (1440×900).
- Vitest / Playwright / `tsc` / lint / `check:mockup-fidelity` / build full gate.
- Retrospective + memory snapshot + doc syncs (CLAUDE.md / MEMORY.md / `sprint-workflow.md §Scope-class multiplier matrix` / `next-phase-candidates.md`).

---

## User Stories

### Group A — Day 0 plan + 三-prong + before-baseline (PRE-WORK)

- **US-A1** (Plan + Checklist): As the AI, I draft Sprint 57.30 plan + checklist mirroring Sprint 57.29 format (11 sections, Day 0-5, 5 user-story groups A-E) before any code runs, so the sprint contract is explicit. Acceptance: this file + `sprint-57-30-checklist.md` exist with full content.
- **US-A2** (Day-0 三-prong): As the AI, I run path-verify + content-verify + (no schema) on plan-time assertions, so reality drift is caught at <30 min cost before Day 1 code. Acceptance: Day-0 grep findings catalogued in `progress.md` under "Drift findings" with `D{N}` IDs.
- **US-A3** (Before-baseline screenshots): As the AI, I capture Playwright screenshots of all 22 AppShellV2 routes + `/chat-v2` (Inspector closed + open) + UserMenu open (avatar trigger + dropdown) **before** any code change, so the after-baseline regression diff has a clean reference. Acceptance: before-state screenshots in `claudedocs/4-changes/sprint-57-30-*/screenshots/before/`.

### Group B — Shell hotfix (Day 1)

- **US-B1** (UserMenu Radix-drop verbatim): As an operator, I see the UserMenu dropdown flush against the topbar bottom edge (no gap) when I click my avatar, so the visual matches the mockup canonical. Acceptance: UserMenu drops `<DropdownMenu>` Radix wrapper; ports `useDismiss` hook verbatim from mockup `topbar-overlays.jsx:9-27`; uses `position: absolute; top: 50; right: 12` from `panelStyle`; ESC + click-outside still close the panel; keyboard `Tab` navigates inside the panel (manual verify).
- **US-B2** (Topbar avatar trigger 26→26): As an operator, the avatar circle in the topbar is the mockup-correct 26×26 px size, not the inflated 36×36 px. Acceptance: `Topbar.tsx` UserMenu trigger renders an avatar with `width: 26; height: 26; font-size: 10.5` (mockup `.avatar` class); the in-panel identity-card avatar keeps `36×36` (mockup `topbar-overlays.jsx:347`); the two avatars use distinct style objects in `UserMenu.tsx`.
- **US-B3** (Topbar icon size audit): As the AI, I audit all topbar `Icon size=` literals against mockup `topbar-overlays.jsx` + `shell.jsx` Topbar section; correct any drift. Acceptance: audit findings in `progress.md` Day 1; corrections committed; mockup `Icon` sizes match (locale/theme/bell/⌘K).
- **US-B4** (Topbar + UserMenu Vitest fixup): As a developer, the Vitest spec for `UserMenu` + `Topbar` + any shell consumer asserts the new structure correctly. Acceptance: all existing chat-v2 / overview / shell Vitest specs pass after Group B changes; new spec for avatar size split if needed.

### Group C — chat-v2 shell + composer (Day 2)

- **US-C1** (ChatLayout 3-col): As an operator on `/chat-v2`, the 3-col layout (session list | turn list | inspector) matches mockup `page-chat.jsx` grid template + gap + min/max widths verbatim. Acceptance: `ChatLayout.tsx` renders the mockup grid; computed-style matches.
- **US-C2** (ChatHeader + SessionList + Composer + InputBar): As an operator, the chat header bar, session list rail, composer container, and input bar match the mockup verbatim (class names + inline-style literals copied byte-for-byte). Acceptance: 4 files re-pointed; Vitest passes; `check:mockup-fidelity` baseline updated if new oklch literals.

### Group D — chat-v2 turns + blocks + inspector (Day 3-4)

- **US-D1** (TurnList + 3 turn shapes): As an operator, the turn list scroller + UserTurn / AgentTurn / HITLTurn frames match mockup verbatim. Acceptance: 4 files re-pointed; all Sprint 57.21 Turn Block Model behaviour preserved (no regression in discriminated-union routing).
- **US-D2** (5 blocks): As an operator, the 5 block components (Block / ThinkingBlock / ToolBlock / VerificationBlock / SubagentForkBlock) render with mockup-canonical CSS. Acceptance: 5 files re-pointed; all Sprint 57.21 block routing tests pass.
- **US-D3** (Inspector 4-tab + InspectorTurn + ComingSoonInspectorTab): As an operator, the right-rail Inspector chrome (4-tab navigator + content panel + coming-soon placeholder) matches mockup verbatim. Acceptance: 3 files re-pointed; all 4 tabs render; tab-switch behaviour preserved.
- **US-D4** (ApprovalCard): As an operator awaiting HITL approval on a turn, the approval card visual matches the mockup HITL approval shape verbatim. Acceptance: `ApprovalCard.tsx` re-pointed; the approve/deny/escalate buttons keep their behaviour.

### Group E — Regression sweep + fidelity verify + closeout (Day 5)

- **US-E1** (22-route regression sweep): As the AI, I run `route-sweep.mjs` before/after on 22 routes + diff screenshots, so we can declare "0 catastrophic / 0 structural regression" with evidence. Acceptance: sweep produces 22 before + 22 after screenshots; agent triage classifies each route; 0 catastrophic, 0 structural-regression.
- **US-E2** (chat-v2 fidelity verify): As the AI, I run Playwright + computed-style diff comparing mockup-vs-prod `/chat-v2` at 1440×900, so the PARITY verdict is grounded in measurement, not eye. Acceptance: REPOINT-REPORT.md captures the verdict with computed-style measurements + screenshots.
- **US-E3** (Full gates): As the AI, I run all gates (tsc / lint / Vitest / Playwright / build / `check:mockup-fidelity` / route-sweep) before PR. Acceptance: all gates green; Vitest count + build size delta logged.
- **US-E4** (Closeout: retro + memory + docs): As the AI, I write retrospective.md Q1-Q7 + memory snapshot + sync CLAUDE.md Current Sprint row + MEMORY.md pointer + `sprint-workflow.md §Scope-class multiplier matrix` 2nd-data-point row + `next-phase-candidates.md` carryover ADs. Acceptance: all docs synced; PR opened; merged after CI green.

---

## Technical Specifications

### Verbatim re-point method (the rule this sprint applies, unchanged from Sprint 57.29)

For every component touched in Groups B-D:

1. Read the mockup canonical source line range (`reference/design-mockups/page-chat.jsx` / `topbar-overlays.jsx` / `styles.css`).
2. Identify the visual layer: CSS class names (consumed from `styles-mockup.css` which is byte-identical to mockup `styles.css`) + inline-style literals.
3. Read the production `.tsx` for the same component; identify translated-Tailwind / shadcn-default usage that violates the verbatim rule.
4. Re-point: replace translated Tailwind with mockup class names; replace shadcn defaults with mockup inline-style literals (copied byte-for-byte); preserve all component-logic layer (hooks / state / props / event handlers / a11y attrs).
5. Add file-level eslint-disable `no-restricted-syntax` with the standard verbatim escape-hatch comment.
6. Update file header MHist (1-line per Sprint 55.3 char budget rule).

### US-B1 — UserMenu Radix-drop verbatim port

Source: `reference/design-mockups/topbar-overlays.jsx:9-27` (`useDismiss` hook) + `:331-441` (UserMenu panel structure).

Port plan:
- Add `useDismiss` hook to `frontend/src/components/UserMenu.tsx` (or extract to `frontend/src/hooks/useDismiss.ts` if reused by `CommandPalette` / `NotificationsPanel`; Sprint 57.19 ports of those used Radix `<Dialog>` — check if they should also be Radix-dropped — defer to scope).
- Drop `<DropdownMenu>` / `<DropdownMenuTrigger>` / `<DropdownMenuContent>` imports.
- Render avatar trigger as `<button className="avatar" type="button" ref={anchorRef} onClick={() => setOpen(o => !o)}>`.
- Render panel conditionally `{open && <div data-topbar-overlay style={panelStyle}>...</div>}`.
- `useDismiss(open, () => setOpen(false), anchorRef)` for ESC + click-outside.
- Keyboard `Tab` cycles within panel: native browser focus order works for `<button>` + `<a>` items; if Radix's free `Tab`-trap behaviour was load-bearing, add manual focus management (likely not needed — mockup ships without it).

Loss vs Radix: free `aria-activedescendant` keyboard nav (arrow keys), focus trap, `aria-haspopup` semantics. Gain: pixel-perfect verbatim parity + closes `AD-UserMenu-Mockup-Structural-Deltas` clean. Trade-off accepted because mockup mockup is the canonical UX spec.

### US-B2 — Avatar size split

Today `UserMenu.tsx:75-80` `avatarStyle` is **36×36** and used at both `<DropdownMenuTrigger>` `<button style={avatarStyle}>` (line 147) **and** inside the dropdown identity card (line 161). Split into two:

```tsx
const triggerAvatarStyle: CSSProperties = {
  // Mockup .avatar class (styles.css:387-394) — used as topbar trigger
  width: 26, height: 26, borderRadius: "50%",
  background: "linear-gradient(135deg, oklch(0.7 0.14 30), oklch(0.6 0.16 350))",
  display: "flex", alignItems: "center", justifyContent: "center",
  fontSize: 10.5, color: "white", fontWeight: 600,
  border: "1px solid var(--border)", flexShrink: 0,
};

const identityAvatarStyle: CSSProperties = {
  // Mockup topbar-overlays.jsx:347-360 — bigger avatar inside the dropdown identity card
  width: 36, height: 36, borderRadius: "50%",
  background: "linear-gradient(135deg, oklch(0.7 0.14 30), oklch(0.6 0.16 350))",
  color: "white", fontSize: 13, fontWeight: 600,
  display: "flex", alignItems: "center", justifyContent: "center",
};
```

Better still — use the `.avatar` CSS class for the trigger (it's already in `styles-mockup.css`); only the identity-card avatar needs inline style.

### US-B3 — Topbar icon size audit

Compare current `Topbar.tsx` Icon sizes against mockup:

| Element | Production size | Mockup size (per `topbar-overlays.jsx` / `ui.jsx`) | Action |
|---------|-----------------|----------------------------------------------------|--------|
| `Icon name="search"` (⌘K) | 13 | TBD (verify) | audit |
| `Icon name="globe"` (locale) | 12 | TBD | audit |
| `Icon name={theme}` (sun/moon) | 14 | TBD | audit |
| `Icon name="bell"` | 14 | TBD | audit |
| Avatar trigger | 36×36 ❌ | 26×26 ✅ | fix (US-B2) |

Day 0 三-prong Prong 2 (content verify) catalogues the exact mockup Icon sizes per element; Day 1 fixes any drift discovered.

### US-C1 — ChatLayout 3-col grid

Source: `reference/design-mockups/page-chat.jsx` outer grid (line range TBD Day 0 prong).

Port plan:
- Replace ChatLayout's translated-Tailwind `grid grid-cols-[...]` with verbatim inline-style or mockup class.
- Grid template: 3 cols (session-rail width / 1fr center / inspector-rail width when open).
- Gap + min/max widths verbatim from mockup.

### US-C2 / D1 / D2 / D3 / D4 — per-component re-point

Each component follows the same 6-step verbatim re-point method above. Per-component mockup source line ranges catalogued in checklist Day 2-4.

### US-E2 — chat-v2 fidelity verification (Mockup-Fidelity DoD)

Per `docs/rules-on-demand/frontend-mockup-fidelity.md` 4-step DoD:

1. `diff reference/design-mockups/styles.css frontend/src/styles-mockup.css` → must be empty (no Sprint 57.30 change to foundation).
2. Playwright screenshot mockup (via `python -m http.server`) vs `/chat-v2` production at 1440×900.
3. Computed-style measurement on representative elements + page-level dimensions, item-by-item.
4. Drift classification + parity verdict logged to `progress.md` Day 5 + REPOINT-REPORT.md.

### route-sweep.mjs reuse

Reuse the same harness from Sprint 57.26-57.29 (`scripts/visual/route-sweep.mjs`). Before-baseline runs **before any code change in Day 0**; after-baseline runs Day 5. Agent triage categorises each route as PARITY / acceptable-cosmetic / catastrophic / structural-regression.

---

## File Change List

### NEW files (~1 + screenshots)

- `frontend/src/hooks/useDismiss.ts` (NEW) — only if extracted from `UserMenu.tsx` for reuse; if not extracted, the hook lives inside `UserMenu.tsx` and this entry drops.
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-30/artifacts/chatv2-shell-repoint/screenshots/before/*.png` (NEW; 22 routes + 5-6 UserMenu states + chat-v2 inspector states).
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-30/artifacts/chatv2-shell-repoint/screenshots/after/*.png` (NEW; matching pairs).
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-30/artifacts/chatv2-shell-repoint/REPOINT-REPORT.md` (NEW; final REPOINT-REPORT mirroring Sprint 57.29 format).

### MODIFIED files (~22-23)

Shell hotfix (Group B):
- `frontend/src/components/UserMenu.tsx` — Radix-drop + avatar split.
- `frontend/src/components/layout/Topbar.tsx` — icon-size audit corrections.
- `frontend/tests/unit/components/UserMenu.test.tsx` (or wherever the UserMenu spec lives) — adapt to Radix-free structure.
- `frontend/tests/unit/components/layout/Topbar.test.tsx` (if exists; otherwise N/A) — adapt to icon-size corrections.

chat-v2 page re-point (Group C+D):
- `frontend/src/pages/chat-v2/index.tsx` (1).
- `frontend/src/features/chat_v2/components/ChatLayout.tsx` (1).
- `frontend/src/features/chat_v2/components/ChatHeader.tsx` (1).
- `frontend/src/features/chat_v2/components/SessionList.tsx` (1).
- `frontend/src/features/chat_v2/components/Composer.tsx` (1).
- `frontend/src/features/chat_v2/components/InputBar.tsx` (1).
- `frontend/src/features/chat_v2/components/TurnList.tsx` (1).
- `frontend/src/features/chat_v2/components/turns/UserTurn.tsx` (1).
- `frontend/src/features/chat_v2/components/turns/AgentTurn.tsx` (1).
- `frontend/src/features/chat_v2/components/turns/HITLTurn.tsx` (1).
- `frontend/src/features/chat_v2/components/blocks/Block.tsx` (1).
- `frontend/src/features/chat_v2/components/blocks/ThinkingBlock.tsx` (1).
- `frontend/src/features/chat_v2/components/blocks/ToolBlock.tsx` (1).
- `frontend/src/features/chat_v2/components/blocks/VerificationBlock.tsx` (1).
- `frontend/src/features/chat_v2/components/blocks/SubagentForkBlock.tsx` (1).
- `frontend/src/features/chat_v2/components/inspector/ChatInspector.tsx` (1).
- `frontend/src/features/chat_v2/components/inspector/InspectorTurn.tsx` (1).
- `frontend/src/features/chat_v2/components/inspector/ComingSoonInspectorTab.tsx` (1).
- `frontend/src/features/chat_v2/components/ApprovalCard.tsx` (1).
- `frontend/src/components/mockup-ui.tsx` (1; only if new primitives needed by chat-v2).

Vitest specs touched (likely ~3-5):
- `frontend/tests/unit/features/chat-v2/**/*.test.tsx` — adapt assertions if structural class names change.

Day 5 docs / closeout:
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-30/progress.md` (NEW per-day file).
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-30/retrospective.md` (NEW Day 5).
- `CLAUDE.md` (Current Sprint row + footer).
- `memory/MEMORY.md` (pointer entry).
- `memory/project_phase57_30_chatv2_shell_repoint.md` (NEW snapshot).
- `.claude/rules/sprint-workflow.md` (`§Scope-class multiplier matrix` `frontend-verbatim-css-repoint` 2nd-data-point row).
- `claudedocs/1-planning/next-phase-candidates.md` (close 1+ carryover ADs; add any new ones).
- `sprint-57-30-checklist.md` (per-day `[ ]` → `[x]`).

### DELETED files (0)

No file deletions expected. (Sprint 57.29 deleted `_primitives.tsx` orphan; Sprint 57.30 doesn't anticipate orphans because chat-v2 already uses its own `features/chat_v2/components/` tree with no parallel `_primitives` to clean.)

### PRESERVED (not touched)

- `frontend/src/styles-mockup.css` (Sprint 57.28 byte-identical foundation; `diff` must remain empty).
- `frontend/src/components/AppShellV2.tsx`, `Sidebar.tsx` (Sprint 57.29 re-point complete; not touched unless icon audit reveals a regression to Sidebar — unlikely).
- `frontend/src/components/topbar/CommandPalette.tsx`, `NotificationsPanel.tsx` (Sprint 57.19 ports; Radix-drop deferred unless `useDismiss` extraction touches them).
- `frontend/src/components/mockup-ui.tsx` Spark / Stat / Card / Button / Icon / Badge / SevDot / RiskBadge primitives (Sprint 57.29 verbatim; only **add** new primitives if chat-v2 needs them — do not modify existing).
- All backend code (FastAPI / DB / SSE / etc.).
- All other 12 🟡 routes not in chat-v2 scope.

---

## Acceptance Criteria

- [ ] `/chat-v2` mockup-vs-production fidelity = **PARITY** (computed-style identical on representative elements; 0 cosmetic / 0 structural drift on agent triage of Playwright screenshot).
- [ ] UserMenu dropdown opens flush against topbar bottom edge (no visible gap; `top: 50` from container = `topbar` height 48 + 2px); ESC + click-outside still close.
- [ ] Topbar avatar trigger renders 26×26 px (mockup `.avatar` class); in-panel identity-card avatar renders 36×36 px (mockup `topbar-overlays.jsx:347`); the two use distinct style sources.
- [ ] Topbar icon sizes match mockup verbatim (audit findings closed in Day 1 commit).
- [ ] 22-route regression sweep: **0 catastrophic / 0 structural-regression**; any 🟡 acceptable-cosmetic transitions documented with reason.
- [ ] All gates green: `tsc` 0 errors / lint 0 errors / Vitest **all-pass** (count baseline 457, expected ±10) / Playwright **all-pass** / `check:mockup-fidelity` baseline updated if new oklch literals introduced / Vite build successful / LLM-SDK leak 0.
- [ ] No new ADs blocking the sprint; all carryover ADs from Sprint 57.29 either closed in this sprint or explicitly deferred to `next-phase-candidates.md`.
- [ ] Retrospective.md Q1-Q7 + memory snapshot + CLAUDE.md / MEMORY.md / `sprint-workflow.md §Matrix` 2nd-data-point row all synced + PR opened + CI green + merged.

---

## Deliverables

- [ ] Shell hotfix: `AD-UserMenu-Mockup-Structural-Deltas` closed (US-B1).
- [ ] Avatar trigger 26→26 split: US-B2 closed.
- [ ] Topbar icon audit + fixup: US-B3 closed.
- [ ] Vitest spec adaptations: US-B4 closed.
- [ ] `/chat-v2` Phase-2 verbatim CSS re-point: US-C1 / C2 / D1 / D2 / D3 / D4 closed.
- [ ] 22-route regression sweep: US-E1 closed with REPOINT-REPORT.md.
- [ ] `/chat-v2` fidelity verify: US-E2 closed with PARITY verdict.
- [ ] Full gates: US-E3 closed.
- [ ] Closeout: US-E4 closed.

---

## Dependencies & Risks

### Dependencies

- Sprint 57.28 verbatim-CSS foundation (`styles-mockup.css` byte-identical to mockup `styles.css`) — **MUST remain valid** (Day 0 三-prong Prong 1 verifies the diff is empty).
- Sprint 57.29 Phase-2 method validated on `/overview` — method baseline accepted.
- Sprint 57.21 Phase-1 chat-v2 structural rewrite (Turn Block Model + 3-col shell + Inspector 4-tab + Composer) — structural scaffolding accepted; Sprint 57.30 only re-points CSS.
- `mockup-ui.tsx` Sprint 57.29 verbatim primitive set (`Icon` / `Button` / `Card` / `Stat` / `Spark` / `Badge` / `SevDot` / `RiskBadge`) — reused; extended only if chat-v2 needs new primitives (e.g. Composer-specific icon set).

### Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|-----------|
| R1 | UserMenu Radix-drop loses load-bearing focus-trap / arrow-key nav behaviour | Medium | Medium | Test manually Day 1; if regression surfaces, add custom focus management inside the `useDismiss` panel (small surface area). Acceptable: mockup ships without arrow-key nav by design. |
| R2 | chat-v2 19 components is the largest single-page re-point scope to date (vs 7 widgets in 57.29 `/overview`) — scope creep into Day 6 | Medium | Medium | Bottom-up estimate 17-21 hr × 0.60 = ~11-13 hr committed; Day 0 三-prong should catch any plan-vs-repo gap that inflates this 20%+. If Day 3 shows scope is exceeding day-by-day, defer Group D part (e.g. ApprovalCard) to next sprint. |
| R3 | `useDismiss` extraction touches `CommandPalette` + `NotificationsPanel` if those also use Radix today | Low | Low | Day 0 三-prong verifies; if those also Radix-coupled, scope a separate Sprint 57.31 follow-up; current sprint only touches UserMenu. |
| R4 | Vitest specs assume Radix `<DropdownMenu>` DOM structure (`role="menu"`, etc.) — many fails on Radix-drop | Medium | Low | Day 1 last task: run Vitest after UserMenu refactor; adapt assertions to verbatim `<div data-topbar-overlay>` semantics. |
| R5 | Visual-regression baseline staleness on routes 57.29 last touched — pre-existing 4 routes baseline-regen need to repeat | Medium | Low | Day 0 三-prong Prong-Visual: pre-list affected routes; trigger baseline-regen workflow upfront or accept Day 5 baseline regen overhead. |
| R6 | `AD-Overview-PreExisting-Route-Crashes` 3 routes (`/subagents` `/memory` `/verification`) — if Sprint 57.30 sweep catches them as "regression", false positive could derail PARITY verdict | Low | Low | Per US-E1, explicitly classify those 3 routes as **pre-existing fail** (before == after baseline); they are not Sprint 57.30 regressions. |
| R7 | `/chat-v2` has live SSE chat behaviour; re-point shouldn't change runtime semantics, but CSS change could accidentally hide a tooltip / focus ring / etc. | Medium | Low | Day 4 Vitest + Playwright covers Sprint 57.21 behavioural specs; manual smoke on Day 5 before closeout. |

### Common Risk Classes (per sprint-workflow.md §Common Risk Classes)

- **Class B — Cross-platform `mypy --strict` `unused-ignore`**: N/A this sprint (frontend only).
- **Class C — Module-level singleton across test event loops**: N/A this sprint (frontend Vitest).
- **Class A — Paths-filter vs `required_status_checks`**: low risk; touches `frontend/` heavily, so backend-ci paths-filter triggers normally.
- **`AD-CI-7-GHA-PR-Permission`**: Sprint 57.29 carryover; visual-regression baseline-regen workflow auto-PR step still fails; Day 5 expects to manually ff-merge baseline-regen commit again (same workaround as Sprint 57.29).

---

## Workload

Bottom-up est ~17-21 hr → calibrated commit ~10-12 hr (HYBRID blended multiplier ≈ 0.55-0.60).

| Group | Bottom-up | Notes |
|-------|-----------|-------|
| Group A (Day 0 plan + 三-prong + before-baseline) | ~2 hr | mirror 57.29 Day 0 |
| Group B (Shell hotfix UserMenu + avatar + icon audit + Vitest) | ~3-4 hr | mechanical refactor + audit |
| Group C (chat-v2 shell + composer 6 files) | ~4-5 hr | 6 components |
| Group D (chat-v2 turns + blocks + inspector + ApprovalCard 13 files) | ~6-8 hr | 13 components (most numerous) |
| Group E (Regression sweep + chat-v2 fidelity + Vitest + closeout) | ~2-3 hr | mirror 57.29 Day 5 |
| **Total bottom-up** | **~17-22 hr** | |
| **HYBRID blended** | **~0.60 (≈10-13 hr committed)** | per matrix above |

Day 4 retrospective Q2 must verify ratio in [0.85, 1.20] band; if `actual / committed > 1.20`, log `AD-Sprint-Plan-N` to revisit `frontend-verbatim-css-repoint` baseline for the 3rd data point.

---

## Sequencing / Day plan

### Day 0 — Plan + Checklist + 三-prong + before-baseline

- Draft this plan + checklist.
- Day-0 三-prong:
  - Prong 1 path-verify: confirm all 22 file paths in §File Change List exist (or `Glob` returns 0 for new files).
  - Prong 2 content-verify: grep for plan-time assertions (e.g. "Radix `<DropdownMenu>` used in UserMenu only — not CommandPalette / NotificationsPanel"; "chat-v2 has 19 .tsx in features/chat_v2/components/"; "mockup `page-chat.jsx` line count 533").
  - Prong 3 schema-verify: N/A (frontend only, no DB).
  - Prong 4 visual-baseline: identify routes whose Sprint 57.29 baseline may go stale on Sprint 57.30 shell-hotfix.
- Capture before-baseline screenshots: 22 routes + UserMenu states + chat-v2 inspector states.
- Drift findings catalogued in `progress.md` with `D{N}` IDs.

### Day 1 — Group B (Shell hotfix)

- US-B1: UserMenu Radix-drop + verbatim useDismiss port.
- US-B2: avatar trigger 36→26 split.
- US-B3: topbar icon size audit + fix.
- US-B4: Vitest adapt to Radix-free structure.
- End-of-Day-1 mini-verify: `/chat-v2` + `/overview` + 3-4 other shell-consuming routes Playwright spot-check (UserMenu opens flush; avatar 26×26; bell ring still works; ⌘K still works).

### Day 2 — Group C (chat-v2 shell + composer)

- US-C1: ChatLayout 3-col grid verbatim.
- US-C2: ChatHeader + SessionList + Composer + InputBar verbatim.
- End-of-Day-2 mini-verify: `/chat-v2` mounts, sessions visible, composer renders, no Vitest regression.

### Day 3 — Group D first half (turns + 3 blocks)

- US-D1: TurnList + 3 turn shapes (UserTurn / AgentTurn / HITLTurn).
- US-D2 first half: Block base + ThinkingBlock + ToolBlock.

### Day 4 — Group D second half (Inspector + remaining blocks + ApprovalCard)

- US-D2 second half: VerificationBlock + SubagentForkBlock.
- US-D3: ChatInspector + InspectorTurn + ComingSoonInspectorTab.
- US-D4: ApprovalCard.
- Vitest re-run after all chat-v2 components done; fix any spec drift.

### Day 5 — Group E + closeout

- US-E1: 22-route regression sweep before/after + agent triage.
- US-E2: `/chat-v2` fidelity verify (computed-style + Playwright + REPOINT-REPORT.md).
- US-E3: full gates run (tsc / lint / Vitest / Playwright / build / `check:mockup-fidelity` / route-sweep).
- US-E4: retrospective.md Q1-Q7 + memory snapshot + doc syncs + PR opened.
