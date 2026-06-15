# Sprint 57.121 — Checklist (Skills slash-menu mockup + production re-point: the chat-v2 `/`-slash skill picker (`SkillSlashMenu.tsx`, 57.115) shipped greenfield with inline token-styles + "No mockup reference exists" — the one chat-v2 element with no `reference/design-mockups/` entry. This (1) AUTHORS it in the mockup (`page-chat.jsx` `SkillMenu` + `styles.css` `.skill-menu*`, CommandPalette-consistent) and (2) RE-POINTS production `SkillSlashMenu.tsx` to the classes (byte-identical CSS copy into `styles-mockup.css` + group header + kbd footer + drop the inline-style escape-hatch). Last Skills-epic item. NO backend/wire/codegen/migration. CHANGE-088)

[Plan](./sprint-57-121-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong; Prong-3 schema N/A — no table/migration/backend) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `8ed6a630`) — catalogued in progress.md ✅
- [x] **Prong 1 — path verify**: mockup #1/#2 present; production `styles-mockup.css` + `SkillSlashMenu.tsx` + `SkillSlashMenu.test.tsx` present; `CHANGE-088-*.md` free; NO design note
- [x] **Prong 2 — content verify** (drift findings → progress.md):
  - [x] **D-css-anchor**: `styles-mockup.css` composer block (917-937) BYTE-IDENTICAL to `reference/.../styles.css` PRE-edit (same content + line numbers) → byte-identical insert lands exactly; `diff` empty after the copy ✅
  - [x] **D-component-shape**: `SkillSlashMenu.tsx` inline `menuStyle`/`rowStyle` + `data-testid`s + `role`s + the `eslint-disable` header — preserved testids/roles, dropped inline+disable
  - [x] **D-inputbar-props**: `InputBar.tsx` renders `<SkillSlashMenu skills/activeIndex/onSelect/onHover>` — props unchanged → re-point internal, InputBar untouched
  - [x] **D-no-literal**: the `.skill-menu*` CSS is token-only → `HEX_OKLCH_BASELINE` 51 unchanged after the copy ✅
- [x] **Prong 3 — N/A** (no table/migration/ORM/backend)
- [x] **D-baselines**: FE Vitest 884 (57.120) · mockup gate RED on branch until Day 2.1 synced production (expected) · pytest 2648+5skip / wire 24 / mypy 0/371 / run_all 10/10 UNCHANGED expected (FE-only)
- [x] **Catalog drift**: all anchors confirmed-as-expected; no scope shift
- [x] **Go/no-go**: 🟢 **GO**

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-121-skills-slash-menu-mockup` (from `main` `8ed6a630`; carries the authored mockup changes)

---

## Day 1 — Mockup authoring (US-1) — DONE (the user-directed prerequisite + design-review checkpoint) ✅

### 1.1 `reference/design-mockups/styles.css` ✅
- [x] `.skill-menu` / `-list` / `-group` / `-item` / `-item.active` / `-name` / `-desc` / `-empty` / `-foot` (token-only: `var(--bg-1)`/`--border-strong`/`--radius-lg`/`var(--shadow)`/`--bg-hover`/`--fg-muted`; no hex/oklch literal) + `.composer-inner { position: relative }`. CommandPalette-consistent (subtle `--bg-hover` active, kbd footer)

### 1.2 `reference/design-mockups/page-chat.jsx` ✅
- [x] `SKILLS` (5 illustrative) + `SkillMenu` (`role=listbox`, group header + items + kbd footer, NO emoji) + interactive `Composer` (controlled `text` default `"/"`, slash parse `^\/(\S*)$`, ↑↓/↵/ESC filter)

### 1.3 Prototype verification ✅
- [x] `python -m http.server` (:8090) → `/chat-v2` → menu opens on `/`, lists 5 skills (`/code-review` active) + footer (↑↓/↵/ESC · 5 skills); `/su` filters to `/summarize` only (footer "1 skill" singular). 2 screenshots in `artifacts/`. User reviewed + approved → proceed to production port

---

## Day 2 — Production port: CSS byte-identical copy + component re-point + tests (US-2, US-3, US-4) ✅

### 2.1 CSS byte-identical copy (US-2) ✅
- [x] **`frontend/src/styles-mockup.css`** (EDIT): inserted the IDENTICAL `position: relative` into `.composer-inner` + the IDENTICAL `.skill-menu*` block after `.composer-tools`
  - DoD: ✅ `diff reference/design-mockups/styles.css frontend/src/styles-mockup.css` **empty (BYTE-IDENTICAL OK)**; `check:mockup-fidelity` 51 byte-identical

### 2.2 Component re-point (US-3) ✅
- [x] **`SkillSlashMenu.tsx`** (EDIT): dropped the `eslint-disable no-restricted-syntax` header + inline `menuStyle`/`rowStyle` + `CSSProperties` import; rendered `className="skill-menu"`/`-list`/`-group`("Skills")/`-item`(+`active`)/`-name`/`-desc`/`-empty` + a `.skill-menu-foot` kbd footer (↑↓/↵/ESC + `{n} skill{s}`, only when `skills.length>0`); KEPT `data-testid`s + `role=listbox`/`option` + `aria-selected` + the `onMouseDown` select. MHist + Last Modified
  - DoD: ✅ `npm run build` clean; `npm run lint` clean (NO unused-directive from the dropped disable; no residual inline style)

### 2.3 FE Vitest + gate sweep (US-4) ✅
- [x] **`SkillSlashMenu.test.tsx`** (EDIT +4): existing 4 pass (testid/aria-selected/onSelect/empty); added — `Skills` group header; footer ("2 skills" + ↑↓/↵/ESC hints); footer ABSENT on empty state; active row `.active` class. Targeted **8 passed**
- [x] Gate sweep: mypy `src` **0/371** (0 `.py`) · `run_all` **10/10** (count 24; event_schema_sync green) · `npm run lint` clean (no `--silent`) · `npm run build` ✅ · Vitest **888 (142 files)** (+4) · `check:mockup-fidelity` **51 byte-identical** · full pytest **2648+5skip UNCHANGED** · `InputBar.tsx`/`loop.py`/`events.py`/`sse.py`/`event_wire_schema`/codegen/migration UNTOUCHED
  - Verify: ✅ `diff` empty · `npx vitest run` (888) · `npm run lint && npm run build` · `check:mockup-fidelity` (51) · `run_all.py` (10/10)

---

## Day 3 — Drive-through (US-5) — real chat-v2 + real backend ✅

### 3.1 Restart / probe ✅
- [x] Backend :8000 + Vite :3007 (HMR'd) healthy (NO Risk-E restart — 0 `.py` delta). 57.120 JWT expired → re-dev-login jamie@acme.com / acme-prod / operator → `/chat-v2`, real_llm + idle (`slashEnabled`)

### 3.2 Drive-through (real chat-v2 composer) ✅
- [x] **Menu render + filter + select PASS**: `/` → menu in NEW mockup styling (panel + `Skills` group header + REAL bundled `/code-review`(active)/`/digest`/`/summarize` from `useChatSkills` w/ real descriptions + subtle `var(--bg-hover)` active + `.kbd` footer ↑↓/↵/ESC/**3 skills**); `/dig` → filter to ONLY `/digest` (footer "1 skill" singular); click `/digest` (via preserved `skill-slash-item-digest` testid) → `/digest ` filled + menu closed (force-load)
- [x] Each control driven (real skills + real render via mockup classes, not a fixture): observed-vs-intended + backend noted in progress.md; screenshot `artifacts/sprint-57-121-production-slash-menu.png` (+ 2 mockup-prototype). **AP-4 clear**
  - DoD: ✅ the menu renders + filters + selects live with the mockup styling; the chat-v2 mockup-fidelity gap closed

---

## Day 4 — CHANGE-088 + closeout (feature continuation — NO design note) ✅

### 4.1 CHANGE-088 ✅
- [x] **`claudedocs/4-changes/feature-changes/CHANGE-088-skills-slash-menu-mockup.md`** (1-page, incl. the mockup authoring + the drive-through)

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`mockup-author-and-port` 0.70 1st pt ~1.17 IN band) + progress.md final
- [x] Final gate sweep: mypy **0/371** (0 `.py`) · run_all **10/10** (count 24) · full pytest **2648+5skip UNCHANGED** · Vitest **888** (+4) · mockup **51 byte-identical**
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + memory subfile `project_phase57_121_skills_slash_menu_mockup.md` · next-phase-candidates (`AD-Skills-SlashMenu-Mockup` SHIPPED = **Skills epic COMPLETE**) · sprint-workflow matrix `mockup-author-and-port` 0.70 1st-point · AGENTS.md changelog (SkillMenu) · 17.md N/A
- [x] **Anti-pattern self-check** (retro Q5): AP-4 (menu live — drive-through) / AP-2 / AP-3 / AP-6 / mockup-fidelity → **0 violations**
- [ ] PR (push + open — user authorized "完整 sprint → PR"); CI → merge on green (gh-verified MERGED before main sync)
