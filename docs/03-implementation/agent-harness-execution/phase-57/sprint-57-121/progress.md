# Sprint 57.121 Progress — Skills slash-menu mockup + production re-point

**Plan**: [`sprint-57-121-plan.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-121-plan.md) · **Checklist**: [`sprint-57-121-checklist.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-121-checklist.md)
**Branch**: `feature/sprint-57-121-skills-slash-menu-mockup` (from `main` `8ed6a630`, post-#295)
**Slice**: `AD-Skills-SlashMenu-Mockup` (the LAST Skills-epic item). Author the slash menu in `reference/design-mockups/` + re-point production `SkillSlashMenu.tsx` to the mockup classes. NO backend / wire (count 24) / codegen / migration. CHANGE-088.

---

## Day 1 — Mockup authoring (US-1) — DONE (user-directed prerequisite + design-review checkpoint) — 2026-06-15

The user asked to "先 author 57.121 的 slash-menu mockup" before the implementation. Authored + verified + reviewed BEFORE this sprint's plan (the AGENTS.md design → approve → implement flow).

### Recon + design alignment
- The chat-v2 `/`-slash picker (`SkillSlashMenu.tsx`, 57.115) was greenfield inline-styled with a header "No mockup reference exists for this element" — the one chat-v2 element with no `reference/design-mockups/` entry. `styles.css` had NO menu/dropdown class (net-new authoring).
- The ⌘K `CommandPalette` (topbar-overlays.jsx) is the closest design-language precedent: panel + a subtle `var(--bg-hover)` active row + `.kbd` footer. AGENTS.md 鐵律: no emoji, token-only, named styles.
- **AskUserQuestion** (2026-06-15): visual direction → **CommandPalette-consistent** (over a leaner list / a bold-primary active row).

### Authored (`reference/design-mockups/`)
- **`styles.css`**: `.skill-menu` (`position:absolute; bottom:100%`, `var(--bg-1)`/`--border-strong`/`--radius-lg`/`var(--shadow)`) + `-list`/`-group`/`-item`/`-item.active`(`var(--bg-hover)`)/`-name`/`-desc`/`-empty`/`-foot`; `.composer-inner` += `position: relative`. Token-only — NO hex/oklch literal.
- **`page-chat.jsx`**: `SKILLS` (5 illustrative) + a `SkillMenu` component (`role=listbox`, group header + items + kbd footer, no emoji) + an interactive `Composer` (controlled `text` default `"/"`, slash parse `^\/(\S*)$`, ↑↓/↵/ESC filter) to make the prototype demonstrable.

### Prototype verification (`python -m http.server` :8090)
- `/chat-v2` → menu opens on `/`, lists 5 skills (`/code-review` active) + footer (↑↓ navigate / ↵ select / ESC close · 5 skills); typing `/su` filters to `/summarize` only (footer "1 skill", singular). Structure (snapshot) + visual (screenshot) + interactivity all correct. 2 screenshots in `artifacts/` (`-open` / `-viewport`).
- **User reviewed + approved** → "核可並實作 57.121" → proceed to the production port.

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch — 2026-06-15

### Branch
`git checkout -b feature/sprint-57-121-skills-slash-menu-mockup` from `main` `8ed6a630` (carries the authored mockup changes) ✅

### Prong 1 — Path verify ✅
Mockup #1/#2 already edited; production `styles-mockup.css` / `SkillSlashMenu.tsx` / `SkillSlashMenu.test.tsx` present; `CHANGE-088-*.md` free; NO design note.

### Prong 2 — Content verify (drift findings)
- **D-css-anchor** (confirmed): `frontend/src/styles-mockup.css` composer block (917-937) is BYTE-IDENTICAL to `reference/design-mockups/styles.css` PRE-edit (same content + line numbers — the byte-identity held before the mockup edit) → the byte-identical insert lands exactly at the same anchor.
- **D-component-shape** (confirmed): `SkillSlashMenu.tsx` inline `menuStyle`/`rowStyle` + `data-testid`s (`skill-slash-menu`/`-item-{name}`/`-empty`) + `role`s + the file-level `eslint-disable no-restricted-syntax` — preserved testids/roles on re-point, dropped inline + disable.
- **D-inputbar-props** (confirmed): `InputBar.tsx` owns `filteredSkills`/`activeIndex`/`showMenu`/keyboard (57.115) + renders `<SkillSlashMenu skills/activeIndex/onSelect/onHover>` — props unchanged → the re-point is internal, InputBar untouched.
- **D-no-literal** (confirmed): the authored `.skill-menu*` CSS is token-only → `HEX_OKLCH_BASELINE` 51 unchanged after the copy.

### Prong 3 — Schema verify: N/A (no table/migration/ORM/backend).

### D-baselines (at HEAD `8ed6a630`)
FE Vitest 884 (confirmed 57.120) · mockup 51 (the gate was RED on this branch after the reference edit until Day 2.1 synced production — expected). pytest 2648+5skip / wire 24 / mypy 0/371 / run_all 10/10 UNCHANGED expected (FE-only).

### Catalog drift / Go-no-go: 🟢 GO
All anchors confirmed; the byte-identical copy + the component re-point hold; no scope shift.

---

## Day 2 — Production port: CSS byte-identical copy + component re-point + tests — 2026-06-15

### CSS byte-identical copy (US-2)
- **`frontend/src/styles-mockup.css`**: inserted the IDENTICAL `position: relative` into `.composer-inner` + the IDENTICAL `.skill-menu*` block after `.composer-tools`.
- `diff reference/design-mockups/styles.css frontend/src/styles-mockup.css` → **empty (BYTE-IDENTICAL OK)** ✅. `check:mockup-fidelity` → byte-identical + **51** (no literal added).

### Component re-point (US-3)
- **`SkillSlashMenu.tsx`**: dropped the `eslint-disable no-restricted-syntax` header + the inline `menuStyle`/`rowStyle` + the `CSSProperties` import; rendered via `className="skill-menu"`/`-list`/`-group`("Skills")/`-item`(+`active`)/`-name`/`-desc`/`-empty` + a `.skill-menu-foot` kbd footer (↑↓ navigate / ↵ select / ESC close / `{n} skill{s}`, only when `skills.length>0`). Kept the `data-testid`s + `role=listbox`/`option` + `aria-selected` + the `onMouseDown` preventDefault select. Uses `.kbd` + `.grow` (both in styles-mockup.css). MHist + Last Modified 2026-06-15.

### Tests (US-4)
- **`SkillSlashMenu.test.tsx`** (+4): the existing 4 (testid /name+desc / aria-selected / onSelect / empty) still pass (structure preserved); added — the `Skills` group header; the footer (count "2 skills" + ↑↓/↵/ESC hints); the footer ABSENT on the empty state; the active row carries the `.active` class. Targeted run **8 passed**.

### Gates (all green)
- `npm run lint` clean (no `--silent`; **no unused-directive** — dropping the `eslint-disable` + going all-classes is clean; the only output is pre-existing jsx-ast-utils notes on OTHER files) · `npm run build` ✅ (3.35s) · `check:mockup-fidelity` **byte-identical + 51** · Vitest **888 (142 files)** (+4 vs 884) · backend `run_all` **10/10** (count 24, `check_event_schema_sync` green).
- **git diff scope**: production = `styles-mockup.css` + `SkillSlashMenu.tsx` + `SkillSlashMenu.test.tsx` (+ the mockup `reference/` 2 files); **0 `.py`** → mypy 0/371, pytest 2648+5skip, wire 24 UNCHANGED. `InputBar.tsx`/`loop.py`/`events.py`/`sse.py`/`event_wire_schema`/codegen/migration UNTOUCHED.

---

## Day 3 — Drive-through (US-5) — real chat-v2 + real backend — 2026-06-15

### Setup
Backend :8000 + Vite :3007 (HMR'd the re-pointed `SkillSlashMenu.tsx` + the synced `styles-mockup.css`). NO Risk-E restart (0 `.py` delta; the menu render needs no LLM call). The 57.120 session JWT had expired → re-dev-login jamie@acme.com / acme-prod / operator → `/chat-v2` (mode real_llm, idle → `slashEnabled`).

### Drive-through (real chat-v2 composer) — PASS ✅
- **Render**: typed `/` → the menu renders with the NEW mockup styling — a panel above the composer, a `Skills` group header, the **REAL bundled skills** from `useChatSkills` (`/code-review` active / `/digest` / `/summarize`, with the real backend descriptions incl. 57.118's "Compute the canonical SHA-256 digest by running this skill's bundled script."), a subtle `var(--bg-hover)` active row, a `.kbd` footer (↑↓ navigate / ↵ select / ESC close / **3 skills**).
- **Filter**: typed `dig` → `/dig` → the menu filtered to ONLY `/digest` (footer "1 skill", singular).
- **Select**: clicked `/digest` (via the preserved `data-testid="skill-slash-item-digest"`) → the textbox filled `/digest ` + the menu CLOSED (force-load token set; the InputBar's `onMouseDown` select fired without losing composer focus).
- Each control live (real skills from the backend, real render via the mockup classes — not a fixture). **AP-4 clear**. Screenshot `artifacts/sprint-57-121-production-slash-menu.png` (+ the 2 mockup-prototype screenshots).

### Observed vs intended
Intended: the greenfield inline-styled slash menu re-pointed to the mockup `.skill-menu*` classes (panel + group header + subtle active + kbd footer), behavior preserved. Observed: EXACTLY that — the production menu renders with the new design-system styling, filters, and selects, driven by the real skill catalog; the 57.115 testids/keyboard/force-load all intact. The one chat-v2 mockup-fidelity gap is closed.
