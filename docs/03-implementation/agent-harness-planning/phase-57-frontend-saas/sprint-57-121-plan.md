# Sprint 57.121 Plan — Skills slash-menu mockup + production re-point (`AD-Skills-SlashMenu-Mockup`): The chat-v2 `/`-slash skill picker (`SkillSlashMenu.tsx`, Sprint 57.115) shipped as a GREENFIELD component with inline token-styles + a header comment "No mockup reference exists for this element" — the one chat-v2 element with NO entry in `reference/design-mockups/` (the canonical visual source of truth). This violates the Mockup-Fidelity Hard Constraint (every FE page/element must follow `reference/design-mockups/`). This sprint (1) AUTHORS the slash-menu in the mockup (`page-chat.jsx` `SkillMenu` + `styles.css` `.skill-menu*` classes, CommandPalette-consistent design, user-approved via AskUserQuestion 2026-06-15) and (2) RE-POINTS the production `SkillSlashMenu.tsx` from inline token-styles to the new mockup classes (byte-identical CSS copy into `styles-mockup.css` + add the mockup's group header + kbd footer + drop the inline-style escape-hatch). The last Skills-epic item. NO backend / wire / codegen / migration. CHANGE-088.

**Status**: Approved-to-execute (user 2026-06-15: authored the mockup → reviewed → "核可並實作 57.121（完整 sprint）"; the last of the remaining Skills ADs after 120✅; scope/visual aligned via AskUserQuestion 2026-06-15: **CommandPalette-consistent** over a leaner list / a bold-primary active row)
**Branch**: `feature/sprint-57-121-skills-slash-menu-mockup`
**Base**: `main` HEAD `8ed6a630` (post-#295 — Sprint 57.120 Inspector active_skill row)
**Slice**: `AD-Skills-SlashMenu-Mockup` (the last Skills-epic item). 57.115 shipped the `/skill-name` slash picker as a greenfield inline-styled component; this rounds out the Skills epic by giving it a mockup source of truth + re-pointing production to it. NO new domain / wire / backend → a **feature continuation** (NO design note, mirrors 57.116/117/119/120). CHANGE-088.
**Scope decisions** (per the AskUserQuestion + the Mockup-Fidelity Hard Constraint): (a) **Author the mockup first** — the slash menu had no `reference/design-mockups/` entry; the mockup (`page-chat.jsx` `SkillMenu` + `styles.css` `.skill-menu*`) becomes the canonical visual, authored + verified + user-reviewed BEFORE the production port (the AGENTS.md design→approve→implement flow). DONE before this plan (the user-directed prerequisite step). (b) **CommandPalette-consistent design** — panel `var(--bg-1)`/`--border-strong`/`--radius-lg`/`var(--shadow)`, a subtle `var(--bg-hover)` active row (NOT the 57.115 component's bold `var(--primary)`), a `Skills` group header, a `.kbd` footer (↑↓ navigate / ↵ select / ESC close / N skills). Token-only, NO hex/oklch literal (HEX_OKLCH baseline stays 51). NO emoji (the mockup 鐵律). (c) **Production re-point = CSS verbatim copy + component class swap** — the new `.skill-menu*` classes copied byte-identical into `frontend/src/styles-mockup.css` (restores the `check:mockup-fidelity` byte-identity) + `SkillSlashMenu.tsx` swapped from inline `menuStyle`/`rowStyle` to `className`s (keeping the 57.115 `data-testid`s + the InputBar's filter/keyboard untouched) + the group header + footer added + the file's `eslint-disable no-restricted-syntax` header DROPPED (no inline styles remain). (d) **InputBar untouched** — it already owns the filter / activeIndex / keyboard (57.115) and already renders the menu; the production interactivity is NOT re-ported (the mockup's interactive Composer is prototype-only). (e) **NO backend / wire / codegen / migration / new SSE event.**

---

## 0. Background

Sprint 57.115 shipped the `/skill-name` slash-command: typing `/` in the chat-v2 composer opens a filtered, keyboard-navigable skill picker (`SkillSlashMenu.tsx`); selecting (or typing `/name `) force-loads the skill. The InputBar (`InputBar.tsx`) owns the filter (`filteredSkills`), the `activeIndex`, and the keyboard (↑/↓/Enter/Esc); `SkillSlashMenu` is presentational — it renders the already-filtered skills, highlights `activeIndex` (`aria-selected`), and reports select/hover.

`SkillSlashMenu.tsx` was authored GREENFIELD with a header comment "No mockup reference exists for this element → inline styles use the mockup token vocabulary (the InputBar production-only-widget precedent)" + a file-level `eslint-disable no-restricted-syntax`. It is the ONE chat-v2 element with no `reference/design-mockups/` entry. The Mockup-Fidelity Hard Constraint (CLAUDE.md) requires every FE page/element to follow `reference/design-mockups/` (the canonical visual source of truth, `styles.css` copied byte-identical into `frontend/src/styles-mockup.css`). `AD-Skills-SlashMenu-Mockup` (carried since 57.115) asks to close this gap: author the mockup, then re-point production to it.

### Design decision (author the slash menu in `reference/design-mockups/` (`page-chat.jsx` `SkillMenu` + `styles.css` `.skill-menu*` classes, CommandPalette-consistent) → copy the `.skill-menu*` CSS byte-identical into `frontend/src/styles-mockup.css` → re-point `SkillSlashMenu.tsx` from inline token-styles to the mockup classes + add the group header + kbd footer; NO backend / wire / codegen / migration)

- **US-1 is "the mockup exists"** (`reference/design-mockups/`) — DONE (the user-directed prerequisite, reviewed + approved): `styles.css` gains `.skill-menu` / `-list` / `-group` / `-item` / `-item.active` / `-name` / `-desc` / `-empty` / `-foot` (token-only, no literals) + `.composer-inner { position: relative }`; `page-chat.jsx` gains `SKILLS` (5 illustrative skills) + a `SkillMenu` component + an interactive Composer (`/`-trigger, ↑↓/↵/ESC, filter) so the prototype demonstrates it. Verified live (`python -m http.server`): the menu opens on `/`, lists the skills + footer, filters on type, the count updates. CommandPalette-consistent, NO emoji.
- **US-2 is "production CSS matches the mockup byte-identical"** (`frontend/src/styles-mockup.css`) — apply the SAME `.composer-inner { position: relative }` + `.skill-menu*` block to `styles-mockup.css` so `diff reference/design-mockups/styles.css frontend/src/styles-mockup.css` is empty again (the verbatim-copy layer). No hex/oklch literal → `HEX_OKLCH_BASELINE` stays 51.
- **US-3 is "the production component uses the mockup classes"** (`SkillSlashMenu.tsx`) — swap the inline `menuStyle` / `rowStyle` for `className="skill-menu"` / `"skill-menu-item"` (+ `active`) / `"skill-menu-name"` / `"skill-menu-desc"` / `"skill-menu-empty"`; ADD the `Skills` group header + the `.skill-menu-foot` kbd footer (↑↓ navigate / ↵ select / ESC close / N skills) to match the mockup; KEEP the 57.115 `data-testid`s (`skill-slash-menu` / `skill-slash-item-{name}` / `skill-slash-empty`) + the `role="listbox"` / `role="option"` / `aria-selected`; DROP the file's `eslint-disable no-restricted-syntax` (no inline styles remain). InputBar untouched (it owns the filter/keyboard + already renders the menu).
- **US-4 is "tests"**: `SkillSlashMenu.test.tsx` — the existing 4 (render /name + description / aria-selected / onSelect on click / empty-state) still pass (structure preserved); ADD: the `Skills` group header renders; the footer renders with the count ("N skills") + kbd hints; the footer is absent on the empty state; the active row carries the `.active` class.
- **US-5 is "the drive-through"** (real chat-v2 + real backend): type `/` in the composer → the menu renders with the new styling (panel + group header + subtle active row + kbd footer); filter on type; select a skill → force-load. Screenshots + observed-vs-intended.
- **Rejected / deferred**: re-porting the mockup's interactive Composer to production (the InputBar already owns it — 57.115); changing the InputBar's filter/keyboard; the leaner-list / bold-primary visual variants (the AskUserQuestion chose CommandPalette-consistent); any backend / wire / codegen / migration / new SSE event.

### Ground truth (Day-0 head-start — direct reads on `main` HEAD `8ed6a630` + the authored mockup; ALL re-verified in the formal Day-0 三-prong §checklist 0.1)

**Mockup (US-1, DONE):**
- `reference/design-mockups/styles.css`: `.skill-menu*` block (after `.composer-tools`) + `position: relative` on `.composer-inner` (after `.composer {` block ~L919). Token-only.
- `reference/design-mockups/page-chat.jsx`: `SKILLS` + `SkillMenu` + interactive `Composer` (controlled `text`, slash parse `^\/(\S*)$`, ↑↓/↵/ESC).

**Production (US-2/US-3/US-4):**
- `frontend/src/styles-mockup.css`: must receive the IDENTICAL `.composer-inner { position: relative }` + `.skill-menu*` edits (Day-0: grep the `.composer-tools` / `.composer-inner` anchors to confirm they match reference's pre-edit state so the byte-identical insert lands cleanly).
- `frontend/src/features/chat_v2/components/SkillSlashMenu.tsx` (greenfield, 57.115): inline `menuStyle` (`:39-53`) + per-row `rowStyle` (`:79-88`); `data-testid` `skill-slash-menu`/`skill-slash-item-{name}`/`skill-slash-empty`; `role="listbox"`/`option`; the file-level `eslint-disable no-restricted-syntax` (`:1`). → re-point to classes + add header/footer + drop the disable.
- `frontend/src/features/chat_v2/components/InputBar.tsx`: owns `filteredSkills` / `activeIndex` / `showMenu` / keyboard (`:88-161`); renders `<SkillSlashMenu skills={filteredSkills} activeIndex={...} onSelect onHover />`; composer-inner has an inline `position: relative` (`:248`) — now redundant (the class provides it) but harmless; leave untouched (minimal scope).
- `frontend/tests/unit/chat_v2/SkillSlashMenu.test.tsx` (4 tests): testid-based; structure-preserving re-point keeps them green; add group/footer cases.

**Baselines (57.120 closeout)**: full pytest **2648+5skip** · wire **24** · FE Vitest **884** (142 files) · mockup-fidelity **51** (byte-identical) · mypy `src` **0/371** · run_all **10/10**. Re-verify Day-0.
- **No backend. No migration. No wire / codegen (count 24). NO design note (feature continuation).** **CHANGE next free = 088** (087 = 57.120).

### STALE / drift anchors to re-confirm in the formal Day-0 三-prong (§ checklist 0.1)

(1) `frontend/src/styles-mockup.css` `.composer-inner` / `.composer-tools` blocks match `reference/design-mockups/styles.css` PRE-edit (so the byte-identical insert is exact) — grep both. (2) `SkillSlashMenu.tsx` exact inline-style shape + the `data-testid`s + the `role`s (to preserve on re-point). (3) `InputBar.tsx` renders `SkillSlashMenu` with `skills`/`activeIndex`/`onSelect`/`onHover` (confirm the props are unchanged → the component re-point is internal). (4) `SkillSlashMenu.test.tsx` testids (`skill-slash-item-{name}` / `skill-slash-empty`) — preserve. (5) `check:mockup-fidelity` after the CSS sync — `diff` empty + `HEX_OKLCH_BASELINE` 51 unchanged (the new CSS has no literals). (6) The FE Vitest baseline (884). (7) Baselines re-verify (pytest 2648+5skip / wire 24 / Vitest 884 / mockup 51 / mypy 0/371 / run_all 10/10).

## 1. Sprint Goal

The chat-v2 `/`-slash skill picker gains a `reference/design-mockups/` source of truth (a CommandPalette-consistent `SkillMenu` in `page-chat.jsx` + `.skill-menu*` classes in `styles.css`, user-approved) and the production `SkillSlashMenu.tsx` is re-pointed from inline token-styles to those classes (byte-identical CSS copy into `styles-mockup.css` + a `Skills` group header + a `.kbd` footer + the inline-style escape-hatch dropped). Closes the one chat-v2 mockup-fidelity gap (`AD-Skills-SlashMenu-Mockup`) + the Skills epic. Proven by a real chat-v2 drive-through. NO backend / wire (count 24) / codegen / migration. Mockup-fidelity byte-identical + 51 holds. Feature continuation (NO design note). CHANGE-088.

## 2. User Stories

- **US-1**: 作為 designer，我希望 slash menu 有 mockup 真相來源（DONE）：`reference/design-mockups/styles.css` 加 `.skill-menu*`（token-only）+ `page-chat.jsx` 加 `SkillMenu` + 互動 Composer，CommandPalette-consistent、無 emoji，於 prototype 驗證可開/filter，以便 production 有 fidelity 依據。
- **US-2**: 作為 platform，我希望 production CSS 與 mockup byte-identical：把 `.composer-inner{position:relative}` + `.skill-menu*` block 原樣複製進 `frontend/src/styles-mockup.css`，使 `diff` 為空、`HEX_OKLCH_BASELINE` 維持 51，以便 `check:mockup-fidelity` 綠。
- **US-3**: 作為 frontend，我希望 `SkillSlashMenu.tsx` 用 mockup class：inline `menuStyle`/`rowStyle` → `className`（`skill-menu`/`-item`(+active)/`-name`/`-desc`/`-empty`）+ 加 `Skills` group header + `.skill-menu-foot` kbd footer（↑↓/↵/ESC/N skills）+ 保留 57.115 的 `data-testid`/`role`/`aria-selected` + 移除 file 級 `eslint-disable no-restricted-syntax`（無 inline style 殘留），以便 fidelity + 清掉 escape-hatch。
- **US-4**: 作為 platform，我希望測試守住：`SkillSlashMenu.test.tsx` 既有 4 仍過（結構保留）+ 新增 group header / footer(count + kbd) / empty 無 footer / active class，以便回歸受保護。
- **US-5**: 作為 reviewer，我希望真 drive-through（真 chat-v2 + 真 backend）：composer 打 `/` → menu 以新樣式渲染（panel + group header + subtle active + kbd footer）→ 打字 filter → 選 skill 觸發 force-load；截圖 + observed-vs-intended。

## 3. Technical Specifications

### 3.0 Architecture (author the slash menu in `reference/design-mockups/` → copy `.skill-menu*` CSS byte-identical into `frontend/src/styles-mockup.css` → re-point `SkillSlashMenu.tsx` to the classes + add group header / footer; NO backend / wire / codegen / migration / new SSE event)

```
reference/design-mockups/styles.css (DONE): + .skill-menu* + .composer-inner{position:relative}
reference/design-mockups/page-chat.jsx (DONE): + SKILLS + SkillMenu + interactive Composer (prototype demo)
frontend/src/styles-mockup.css (EDIT): + .skill-menu* + .composer-inner{position:relative}  ← byte-identical copy
frontend/src/features/chat_v2/components/SkillSlashMenu.tsx (EDIT): inline-styles → mockup classes + group header + kbd footer + drop eslint-disable
frontend/tests/unit/chat_v2/SkillSlashMenu.test.tsx (EDIT): keep 4 + add group/footer/empty/active cases
InputBar.tsx / loop.py / events.py / sse.py / event_wire_schema / codegen / migration: UNTOUCHED / NONE
```

### 3.1 Mockup authoring (US-1, DONE)

`styles.css` `.skill-menu` (`position:absolute; bottom:100%`, `var(--bg-1)`/`--border-strong`/`--radius-lg`/`var(--shadow)`) + `-list` (scroll, padding 4) + `-group` (uppercase mono `--fg-subtle`) + `-item` (column, `--radius-sm`) + `-item.active` (`var(--bg-hover)`) + `-name` (mono 13 500 `--fg`) + `-desc` (11 `--fg-muted`) + `-empty` (centered `--fg-subtle`) + `-foot` (kbd row, `--border` top). `.composer-inner` += `position: relative` (anchor). `page-chat.jsx` `SKILLS` (5) + `SkillMenu` (`role=listbox`, group + items + footer) + interactive `Composer` (controlled `text` default `"/"`, slash parse, ↑↓/↵/ESC).

### 3.2 Production CSS byte-identical copy (US-2)

`frontend/src/styles-mockup.css`: insert the IDENTICAL `position: relative` line into `.composer-inner` + the IDENTICAL `.skill-menu*` block after `.composer-tools`. Verify `diff reference/design-mockups/styles.css frontend/src/styles-mockup.css` is empty + `HEX_OKLCH_BASELINE` 51 unchanged (no literals in the new CSS).

### 3.3 Production component re-point (US-3)

`SkillSlashMenu.tsx`: drop the `eslint-disable no-restricted-syntax` header + the inline `menuStyle` / `rowStyle` + the `CSSProperties` import; render:
- `<div className="skill-menu" data-testid="skill-slash-menu" role="listbox" aria-label="Skills">`
  - `<div className="skill-menu-list">`
    - empty: `<div className="skill-menu-empty" data-testid="skill-slash-empty">No matching skills</div>`
    - else: `<div className="skill-menu-group">Skills</div>` + per skill `<div className={"skill-menu-item" + (active?" active":"")} role="option" aria-selected={active} tabIndex={-1} data-testid={\`skill-slash-item-${name}\`} onMouseDown={…onSelect} onMouseEnter={…onHover}>` with `<span className="skill-menu-name">/{name}</span>` + `<span className="skill-menu-desc">{description}</span>`
  - footer (only when `skills.length > 0`): `<div className="skill-menu-foot">` with `<span><span className="kbd">↑↓</span> navigate</span>` / `↵ select` / `ESC close` / `<span className="grow" />` / `<span>{skills.length} skill{s}</span>`
- Keep the `onMouseDown` preventDefault (select without losing composer focus — 57.115). InputBar untouched.

### 3.4 Drive-through (US-5) — real chat-v2 + real backend

1. Real backend (:8000) + Vite (:3007, HMR'd) + dev-login (acme-prod). Open chat-v2.
2. Type `/` → the menu renders with the new styling: a panel above the composer, a `Skills` group header, the real bundled skills (`/code-review` / `/summarize` / `/digest`) with subtle `var(--bg-hover)` active highlight, a `.kbd` footer (↑↓ navigate / ↵ select / ESC close / N skills). Type to filter; ↑↓ to move; Enter / click to select → the `/skill ` is filled (force-load). Screenshots + observed-vs-intended in progress.md.

### 3.5 What is explicitly NOT done

Re-porting the mockup's interactive Composer to production (the InputBar owns it — 57.115); changing the InputBar filter/keyboard; removing InputBar's redundant inline `position: relative` (harmless, out of scope); the leaner-list / bold-primary visual variants; any backend / wire / codegen / migration / new SSE event / new table.

### 3.6 Validation (US-1..US-5)

Mockup verified live (prototype). Production: `check:mockup-fidelity` byte-identical + 51; `SkillSlashMenu.test.tsx` (existing 4 + new group/footer/empty/active). Gates: mypy strict 0 (UNCHANGED — no backend) · run_all 10/10 (count 24) · full pytest **2648+5skip UNCHANGED** · Vitest +M vs 884 · mockup-fidelity **51 byte-identical** · `npm run lint` (the dropped `eslint-disable` must not leave an unused-directive — the re-point removes ALL inline styles) · `npm run build` · `loop.py`/`events.py`/`sse.py`/`event_wire_schema`/codegen/migration UNTOUCHED.

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `reference/design-mockups/styles.css` | EDIT (DONE) — `.skill-menu*` + `.composer-inner{position:relative}` |
| 2 | `reference/design-mockups/page-chat.jsx` | EDIT (DONE) — `SKILLS` + `SkillMenu` + interactive Composer (prototype) |
| 3 | `frontend/src/styles-mockup.css` | EDIT — byte-identical copy of #1 (`.skill-menu*` + `.composer-inner{position:relative}`) |
| 4 | `frontend/src/features/chat_v2/components/SkillSlashMenu.tsx` | EDIT — inline-styles → mockup classes + group header + kbd footer + drop `eslint-disable` |
| 5 | `frontend/tests/unit/chat_v2/SkillSlashMenu.test.tsx` | EDIT — keep 4 + add group / footer / empty-no-footer / active cases |
| 6 | `claudedocs/4-changes/feature-changes/CHANGE-088-skills-slash-menu-mockup.md` | NEW — change record (incl. the drive-through) |
| — | `InputBar.tsx` / `loop.py` / `events.py` / `sse.py` / `event_wire_schema` / codegen / migration / a design note | **UNTOUCHED / NONE** |

## 5. Acceptance Criteria

1. The slash menu exists in `reference/design-mockups/` (`page-chat.jsx` `SkillMenu` + `styles.css` `.skill-menu*`), CommandPalette-consistent, token-only, no emoji, verified live in the prototype.
2. `frontend/src/styles-mockup.css` is byte-identical to `reference/design-mockups/styles.css` (the `.skill-menu*` + `position:relative` copied); `HEX_OKLCH_BASELINE` 51 unchanged.
3. `SkillSlashMenu.tsx` renders via the mockup classes (no inline styles, no `eslint-disable`), with a `Skills` group header + a `.kbd` footer, preserving the 57.115 `data-testid`s / `role`s / `aria-selected` + the `onMouseDown` select.
4. `SkillSlashMenu.test.tsx` covers the existing 4 + the group header / footer (count + kbd) / empty-no-footer / active class.
5. Gates: mypy 0 (unchanged) · run_all 10/10 (count 24) · full pytest 2648+5skip UNCHANGED · Vitest +M · mockup-fidelity 51 byte-identical · lint clean (no unused-directive from the dropped disable) · `loop.py`/`events.py`/`sse.py`/`event_wire_schema`/codegen/migration UNTOUCHED.
6. Real drive-through PASS: the chat-v2 `/` menu renders with the new styling (panel + group header + subtle active + kbd footer), filters, selects → force-load; screenshots + observed-vs-intended (live — real skills, real render).
7. `AD-Skills-SlashMenu-Mockup` shipped (the last Skills-epic item); NO design note (feature continuation); CHANGE-088; calibration recorded (`mockup-author-and-port` 0.70, 1st data point).

## 6. Deliverables

- [ ] US-1 (DONE) mockup authored (`reference/` `styles.css` `.skill-menu*` + `page-chat.jsx` `SkillMenu` + interactive Composer) + verified live
- [ ] US-2 `styles-mockup.css` byte-identical copy (`diff` empty, 51 unchanged)
- [ ] US-3 `SkillSlashMenu.tsx` re-point (classes + group header + footer + drop eslint-disable)
- [ ] US-4 `SkillSlashMenu.test.tsx` (4 + group / footer / empty / active)
- [ ] US-5 drive-through PASS (`/` menu new styling + filter + select; screenshots + observed-vs-intended)
- [ ] CHANGE-088 + closeout (retro Q1-Q7 + calibration + navigators + next-phase-candidates: `AD-Skills-SlashMenu-Mockup` shipped = Skills epic COMPLETE; 17.md N/A — FE-only, no new contract)

## 7. Workload Calibration

- Scope class **`mockup-author-and-port` 0.70** (NEW, 1st data point; pending 2-3 sprint validation). Shape: author a NET-NEW mockup element (`reference/` styles.css + page-chat.jsx, no prior visual) + verbatim CSS copy into production + a bounded component re-point (inline→classes + a group header/footer + drop the escape-hatch) + tests + drive-through. More than a pure `frontend-verbatim-css-repoint -with-extras` 0.65 (the authoring half — a net-new design + prototype verification — has no prior source to copy), but the component is small (~120 lines) + the CSS ~40 lines. Set 0.70 (between the repoint family + the 57.120 ceremony-aware insight that tiny-code + full-ceremony sprints undershoot a low multiplier). If the 1st point lands > 1.20, re-point toward 0.85.
- **Agent-delegated: no** (parent-direct; the authoring needed live prototype iteration + the port is a bounded component + a drive-through that must show live render). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~5.5 hr (mockup authoring [done] `styles.css` ~0.5 + `page-chat.jsx` ~0.75 + prototype verify ~0.4 · CSS sync ~0.25 · `SkillSlashMenu.tsx` re-point ~0.6 · Vitest ~0.5 · drive-through ~0.6 · CHANGE-088 + closeout ~1.4 + plan/checklist ~0.5) → class-calibrated commit ~3.85 hr (mult 0.70). Day-4 retro Q2 verifies (1st `mockup-author-and-port` data point).

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Committing the reference/ mockup change ALONE breaks `check:mockup-fidelity` byte-identity (reference diverges from production) | this sprint pairs the reference change WITH the production `styles-mockup.css` byte-identical copy in the SAME PR (US-2) → `diff` empty → green. (This is why the mockup change was held local pending this implementation.) |
| The byte-identical insert into `styles-mockup.css` lands at a slightly different anchor than reference → `diff` non-empty | Day-0: grep BOTH files' `.composer-inner` / `.composer-tools` blocks to confirm they match pre-edit; insert at the identical anchor; run `diff` immediately after |
| The new `.skill-menu` CSS introduces a hex/oklch literal → `HEX_OKLCH_BASELINE` 51 bump | the authored CSS is token-only (`var(--bg-1)`/`--bg-hover`/`--shadow`/etc.) — no literal; confirm via the `check:mockup-fidelity` grep guard (stays 51) |
| Dropping the file-level `eslint-disable no-restricted-syntax` leaves an unused-directive OR a residual inline style trips `no-restricted-syntax` | the re-point removes ALL inline styles (everything goes to classes) → the disable is both unnecessary AND must be removed (an unused-directive fails `--report-unused-disable-directives`); run `npm run lint` (no `--silent`) to confirm |
| The re-point changes the DOM structure → the 57.115 tests break | preserve the `data-testid`s (`skill-slash-menu`/`skill-slash-item-{name}`/`skill-slash-empty`) + `role`/`aria-selected`; the group header + footer are ADDITIVE (new testids); run the suite |
| Risk Class E — a stale `--reload` backend at the drive-through | NO backend code change this sprint (0 `.py`) → the running backend serves current; a quick probe + the live menu render confirms; the cheap path is the chat composer `/` (no LLM call needed to see the menu) |
| The FE Vitest baseline (884) may differ at HEAD `8ed6a630` | Day-0 re-run Vitest to capture the real baseline |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- **Re-porting the mockup's interactive Composer to production** (the InputBar already owns the filter/keyboard — 57.115; the mockup's interactivity is prototype-only).
- **Removing InputBar's redundant inline `position: relative`** (the class now provides it; harmless, out of scope — a future tidy).
- **The leaner-list / bold-primary visual variants** (the AskUserQuestion chose CommandPalette-consistent).
- Any backend / wire / codegen / SSE / migration / new-table change (count 24 unchanged).
- This is the LAST Skills-epic item — no further Skills ADs after this (the epic completes).
