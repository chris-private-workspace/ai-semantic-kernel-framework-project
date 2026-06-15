# Sprint 57.121 Retrospective — Skills slash-menu mockup + production re-point

**Closed**: 2026-06-15 · **Branch**: `feature/sprint-57-121-skills-slash-menu-mockup` (from `main` `8ed6a630`) · **Slice**: `AD-Skills-SlashMenu-Mockup` (the LAST Skills-epic item) · CHANGE-088 · NO design note (feature continuation)

## Q1 — What was delivered?

The chat-v2 `/`-slash skill picker got a `reference/design-mockups/` source of truth + a production re-point. (1) Authored the slash menu in the mockup (`page-chat.jsx` `SkillMenu` + `styles.css` `.skill-menu*` classes, CommandPalette-consistent, user-approved). (2) Re-pointed production `SkillSlashMenu.tsx` from greenfield inline token-styles to the mockup classes (byte-identical CSS copy into `styles-mockup.css` + a `Skills` group header + a `.kbd` footer + the `eslint-disable no-restricted-syntax` escape-hatch dropped). 5 production+mockup files, ALL FE, **0 `.py`**. Drive-through PASS. **This closes the Skills epic** (57.113-121).

## Q2 — Estimate accuracy / calibration

- **Scope class**: `mockup-author-and-port` (NEW, 1st data point). Agent-delegated: **no** (parent-direct; the authoring needed live prototype iteration + the port is a bounded component; `agent_factor` 1.0 → 3-segment form).
- Bottom-up est ~5.5 hr → class-calibrated commit ~3.85 hr (mult 0.70) → **actual ~4.5 hr** → **ratio actual/committed ≈ 1.17 (IN band, ≤ 1.20)**.
- **KEEP 0.70** (1st data point IN band; pending 2-3 sprint validation). The 0.70 was deliberately set above a pure `frontend-verbatim-css-repoint -with-extras` 0.65 because this sprint ALSO authored a net-new mockup (no prior visual to copy → real design + prototype-verification work) AND per the 57.120 ceremony-aware insight (tiny/bounded-code + full-ceremony sprints undershoot a low multiplier). The 1.17 confirms the higher multiplier was the right call — a pure 0.65 would have over-committed (~3.6 hr → ratio ~1.25, slightly over).
- **Cross-sprint note**: 57.120 (`chatv2-inspector-existing-field-surface`) re-pointed 0.55→0.85 for the same reason (ceremony not code-accelerated). This sprint's 0.70 landing IN band is consistent evidence that mockup/FE-surface sprints with a real-but-bounded code core sit in the ~0.65-0.85 range, not the 0.45-0.55 of the pure repoint family.

## Q3 — What went well?

- **The two-layer mockup model worked exactly as designed**: author the visual in `reference/` (CSS + JSX), copy the CSS byte-identical into production, re-point the component to the classes. The `diff` was empty on the first copy (the Day-0 D-css-anchor check confirmed the composer block was byte-identical pre-edit, so the insert landed exactly).
- **CommandPalette as the design-language anchor**: the mockup had no slash-menu precedent, but the ⌘K CommandPalette gave a ready design vocabulary (panel + subtle `--bg-hover` active + `.kbd` footer) → token-only, no new literal, mockup-fidelity 51 held.
- **The re-point removed an escape-hatch** (the `eslint-disable no-restricted-syntax` + all inline styles) — a net reduction in fidelity debt, not just a lateral move. The `--report-unused-disable-directives` lint confirmed the drop was clean.
- **The design-review checkpoint** (author mockup → screenshot → user approves → implement) prevented committing a CI-breaking partial change (a reference-only edit fails the byte-identity gate); the mockup was held local until the production port paired with it.
- **Drive-through first-try PASS** with REAL skills (the production menu shows the live `useChatSkills` catalog — `/code-review`/`/digest`/`/summarize` with real descriptions, not the mockup's illustrative 5).
- **Skills epic completed** (9 sprints, 57.113-121) — every cc-parity Skills gap is now shipped + drive-through-verified.

## Q4 — What to improve / lessons

- **Mockup authoring + production port can't be split across PRs** (the byte-identity gate couples them). The clean pattern: author + review the mockup as a LOCAL change, then implement the production port in the SAME PR. Worth remembering for future mockup-gap sprints (e.g. if any other greenfield element surfaces).
- **`.fill()` vs the slash-trigger**: the production InputBar parses the leading `/` on change; in Playwright, `pressSequentially` (slowly) appends char-by-char (good for the filter test), while `.fill()` replaces — use `pressSequentially` when building up a query incrementally.
- **Session JWT expiry**: the 57.120 browser session had expired (~1 hr); a re-dev-login was needed. Expected for back-to-back drive-throughs across a long session.

## Q5 — Anti-pattern self-check

- **AP-4 (Potemkin)**: ✅ clear — the menu is live (real `useChatSkills` skills, real render via the mockup classes, filter + select work), proven by the drive-through, not a fixture.
- **AP-2 (side-track)**: ✅ — reachable from the main chat flow (the composer `/` on `/chat-v2`); the new `.skill-menu` CSS is consumed by the re-pointed component (not inert).
- **AP-3 (cross-dir scatter)**: ✅ — production changes within `frontend/src/features/chat_v2/` + the global `styles-mockup.css`; the mockup within `reference/design-mockups/`.
- **AP-6 (speculative abstraction)**: ✅ — no new abstraction; reused the CommandPalette design vocabulary + the existing InputBar filter/keyboard. The interactive-Composer-port + the InputBar inline-`position:relative` cleanup were explicitly NOT done (out of scope).
- **Mockup-fidelity**: ✅ — `styles-mockup.css` byte-identical to `reference/design-mockups/styles.css`, 51 HEX/oklch baseline unchanged (token-only authored CSS), the inline-style escape-hatch removed.
- **0 violations.**

## Q6 — Carryover

- `AD-Skills-SlashMenu-Mockup` SHIPPED → **the Skills epic is COMPLETE** (no further Skills ADs). The remaining Skills carryovers are all explicitly-deferred larger slices, not epic-blocking: `AD-Skills-Authoring-UI` (versioning + hot-reload + disable-toggle legs), `AD-Skills-Bundled-Scripts` (tenant-authored leg), `AD-Config-Cache-MultiWorker-Invalidation`, per-tenant-configurable quota.
- The `AD-ChatV2-Inspector-Turn-Metadata-Wire` `model` row + token sweep (from 57.120) stay carried.
- Tiny tidy (noted, not pursued): the InputBar's now-redundant inline `position: relative` on `.composer-inner` (the class provides it).
- 17.md: N/A (FE-only; no new cross-category contract).

## Q7 — Gate summary

mypy `src` 0/371 (UNCHANGED — 0 `.py`) · run_all 10/10 (count 24; `check_event_schema_sync` green) · `diff` empty (byte-identical) · `check:mockup-fidelity` 51 · `npm run build` ✅ · Vitest 888 (142 files) (+4 vs 884) · `npm run lint` clean (no unused-directive) · full pytest 2648+5skip UNCHANGED · `InputBar.tsx`/`loop.py`/`events.py`/`sse.py`/`event_wire_schema`/codegen/migration UNTOUCHED · drive-through PASS (real chat-v2 + real skills).

## Design Note Extract

N/A — feature continuation (a mockup-fidelity re-point of an existing 57.115 element; no new domain / execution / security model). NO design note (mirrors 57.116/117/119/120).
