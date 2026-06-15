# Sprint 57.120 — Checklist (Chat-v2 Inspector Turn-Metadata Wire (active-skill row): the chat-v2 Inspector "Turn" tab shows 8 per-turn KV rows but no "active skill" — 57.116 wired `loop_start.active_skill` onto the triggering `UserTurn` as a timeline chip only. This slice — the chosen thin vertical of `AD-ChatV2-Inspector-Turn-Metadata-Wire` (ISSUE-5) — surfaces the EXISTING `active_skill` as a new `active_skill` KV row in the Inspector Turn tab, by carrying it forward onto the `AgentTurn` at `turn_start` (the same point `span_id` is linked). PURE frontend + store: NO backend / NO migration / NO wire (count 24) / NO codegen / NO new wire field. Mockup-fidelity holds (reuse the `KV` helper). Feature continuation (NO design note); CHANGE-087)

[Plan](./sprint-57-120-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong; Prong-3 schema N/A — no table / migration / backend) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `9fa42d22`) — catalogued in progress.md ✅
- [x] **Prong 1 — path verify**: 3 EDIT targets present (`types.ts` / `chatStore.ts` / `InspectorTurn.tsx`); test homes (`tests/unit`, NOT co-located): `chatStore.activeSkill.test.ts` (the 57.116 store test — carry-forward) + `ChatInspector.test.tsx` (Inspector render); `CHANGE-087-*.md` free; NO design note
- [x] **Prong 2 — content verify** (drift findings → progress.md):
  - [x] **D-agentturn-shape**: `AgentTurn` (`types.ts:142-157`) has an `// Inspector Turn tab metadata` group (`:150-156`) + `UserTurn.activeSkill?` (`:139`, the mirror) — place `activeSkill?: string` in that group
  - [x] 🔧 **D-turnstart** (real drift, 1-token fix): `turn_start` (`chatStore.ts:400-424`) links `spanId` from the spans slice (the assembly idiom). **`UserTurn` is NOT imported** (`:66-80`) → add it for the `(t): t is UserTurn` narrowing
  - [x] **D-loopstart-stamp**: `loop_start` (`:372-396`) stamps the LAST user turn's `activeSkill` (truthy-guard) → the most-recent non-injected user turn carries the trigger skill at `turn_start`
  - [x] **D-inspectorturn-kv**: KV block (`:167-181`) + `KV` helper (`:63-70`) + `eslint-disable no-restricted-syntax` header (`:52`) — insert after `cost` (`:179`), before `trace_id` (`:180`); reuse `KV` → no new lint
  - [x] **D-fe-test-path**: confirmed `tests/unit` convention; `chatStore.activeSkill.test.ts` has `userTurn`/`agentTurn`/`loopStart`/`lastUser` + imports `UserTurn`; event shapes `turn_start:{trace_id?,turn_num}` / `message_injected:{trace_id?,text}`
- [x] **Prong 3 — N/A** (no new table / migration / ORM / backend — pure FE store + render)
- [x] **D-baselines**: at HEAD `9fa42d22` — FE Vitest **879 (142 files)** ✅ · mockup **51 byte-identical** ✅ · pytest 2648+5skip / wire 24 / mypy 0/371 / run_all 10/10 UNCHANGED expected (confirm at gate)
- [x] **Catalog drift**: 1 real drift (D-turnstart `UserTurn` import — non-scope-shifting); others confirmed-as-expected
- [x] **Go/no-go**: 🟢 **GO** — design holds end-to-end; no scope shift > 20%

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-120-chatv2-inspector-turn-metadata-wire` (from `main` `9fa42d22`)

---

## Day 1 — Frontend code: `AgentTurn.activeSkill` + `turn_start` carry-forward + Inspector KV row (US-1, US-2) ✅

### 1.1 `AgentTurn.activeSkill?` + `turn_start` carry-forward (US-1) ✅
- [x] **`frontend/src/features/chat_v2/types.ts`** (EDIT): `AgentTurn` += `activeSkill?: string` (mirror `UserTurn.activeSkill?` `:139`; 3-line WHY comment). MHist + Last Modified 2026-06-15
- [x] **`frontend/src/features/chat_v2/store/chatStore.ts`** (EDIT): in `turn_start`, `const triggerSkill = [...s.turns].reverse().find((t): t is UserTurn => t.role === "user" && !t.injected)?.activeSkill;` + `activeSkill: triggerSkill` on `newAgentTurn`; added `UserTurn` to the `../types` import (D-turnstart drift); WHY comment (trigger = most-recent non-injected; skip injected 57.101; no stale leak). MHist + Last Modified
  - DoD: ✅ `npm run build` (tsc) clean (✓ built in 3.50s) — `activeSkill?` optional → no `AgentTurn` literal breaks

### 1.2 The Inspector `active_skill` KV row (US-2) ✅
- [x] **`frontend/src/features/chat_v2/components/inspector/InspectorTurn.tsx`** (EDIT): after the `cost` KV, before `trace_id`: `<KV k="active_skill" v={lastAgent.activeSkill ? \`⚡ ${lastAgent.activeSkill}\` : "—"} />` (reuse `KV`; ⚡ = 57.116 chip idiom; "—" placeholder). MHist + Last Modified
  - DoD: ✅ no new inline-style (reuse `KV`) → no new `no-restricted-syntax`; build clean; mockup-fidelity 51 byte-identical (no `styles-mockup.css` change)

---

## Day 2 — FE Vitest + gate sweep (US-3) ✅

### 2.1 FE Vitest (US-3) ✅
- [x] **`frontend/tests/unit/chat_v2/chatStore.activeSkill.test.ts`** (EDIT +3): a new describe — `turn_start` carries the trigger user turn's `activeSkill` onto the new `AgentTurn`; an intervening `message_injected` (injected user turn) does NOT clear it on a later `turn_start`; a new no-skill loop's `turn_start` → `activeSkill` undefined (no leak from a prior skilled loop). Added `turnStart`/`messageInjected` factories + `lastAgent()` helper + `AgentTurn` import
- [x] **`frontend/tests/unit/chat_v2/components/inspector/ChatInspector.test.tsx`** (EDIT +2, 1 mod): the `active_skill` row renders "⚡ code-review" when set + "—" when the turn carries no skill (exactly 1 dash in the default populated turn); the null-placeholder dash count 6→7 (active_skill). `makeAgentTurn` already takes `Partial<AgentTurn>` → `activeSkill` override
  - DoD: ✅ targeted run **20 passed** (chatStore.activeSkill 7 + ChatInspector 13); the existing Inspector suite stays green

### 2.2 Gate sweep ✅
- [x] mypy `src` **0/371** (UNCHANGED — git diff confirms 0 `.py` files changed) · black/isort/flake8 N/A (no .py) · `run_all` **10/10** (count 24; `check_event_schema_sync` green = no wire change) · `npm run lint` clean (no `--silent`; no new errors — InspectorTurn reuses `KV`, no inline-style) · `npm run build` ✅ · Vitest **884 (142 files)** (+5 vs 879) · `check:mockup-fidelity` **51** (byte-identical `styles-mockup.css` + `HEX_OKLCH_BASELINE` unchanged) · full pytest **2648+5skip UNCHANGED** (FE-only, 0 `.py` delta) · `loop.py`/`events.py`/`sse.py`/`event_wire_schema`/codegen/migration UNTOUCHED
  - Verify: ✅ `npx vitest run` (884) · `npm run lint && npm run build` · `npm run check:mockup-fidelity` (51) · `python scripts/lint/run_all.py` (10/10)

---

## Day 3 — Drive-through (US-4) — real chat-v2 + real backend + real LLM ✅

### 3.1 Restart / probe ✅
- [x] Backend :8000 → 200 + Vite :3007 → 200 (Invoke-WebRequest; curl hook-blocked). NO Risk-Class-E restart needed — 0 `.py` delta this sprint → running 57.119 backend code == this branch's; the chip + row rendering live confirmed the backend emits `active_skill`. dev-login jamie@acme.com / acme-prod / operator → `/chat-v2`, real_llm (gpt-5.2). System-bundled `/code-review` resolves for acme-prod (57.113)

### 3.2 Drive-through (real chat-v2 composer + real backend + real LLM) ✅
- [x] **Leg A (force-load → Inspector row) PASS**: `/code-review please review: def add(a, b): return a - b` → Send → user-turn "⚡ code-review" chip (57.116) + a real code-review answer (Summary/Risks-table found the `a-b` bug/fixes, verification 0.99) AND **Inspector → Turn tab (Turn 1)**: the new **`active_skill: ⚡ code-review`** row, between `cost` and `trace_id` as designed (trace_id 2b6f96…). Screenshot `artifacts/sprint-57-120-legA-inspector-active-skill.png`
- [x] **Leg B (plain message → "—") PASS**: `what is 2 + 2?` → "2 + 2 = 4" → **Inspector → Turn tab (Turn 2)**: **`active_skill: —`** (a different trace 8f0ee1… — a new no-skill loop; the prior code-review did NOT leak). Screenshot `artifacts/sprint-57-120-legB-inspector-no-skill-dash.png`
- [x] Each control driven (real store value + real render, not a fixture): the row tracks the ACTUAL inspected turn (Turn 1 ⚡ code-review / Turn 2 —); the chip + the row agree. Observed-vs-intended + backend noted in progress.md; 2 screenshots in `artifacts/`. **AP-4 clear**
  - DoD: ✅ the Inspector `active_skill` row is live in both legs; the no-leak design proven live; screenshots captured

---

## Day 4 — CHANGE-087 + closeout (feature continuation — NO design note) ✅

### 4.1 CHANGE-087 ✅
- [x] **`claudedocs/4-changes/feature-changes/CHANGE-087-chatv2-inspector-active-skill-row.md`** (1-page, incl. the drive-through both legs)

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`chatv2-inspector-existing-field-surface` 0.55→0.85 re-pointed; 1st pt ratio ~1.6 OVER — tiny-code+full-ceremony insight) + progress.md final
- [x] Final gate sweep: mypy **0/371** (0 `.py`) · run_all **10/10** (count 24) · full pytest **2648+5skip UNCHANGED** · Vitest **884** (+5) · mockup **51** holds · `npm run build` ✅
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + memory subfile `project_phase57_120_chatv2_inspector_active_skill.md` · next-phase-candidates (Inspector-panel active-skill leg SHIPPED + `model` row + token sweep carried + 121 carried) · sprint-workflow matrix `chatv2-inspector-existing-field-surface` 0.85 1st-point · 17.md N/A (FE-only, no new contract)
- [x] **Anti-pattern self-check** (retro Q5): AP-4 (the row is live — drive-through both legs) / AP-2 / AP-3 / AP-6 / mockup-fidelity → **0 violations**
- [ ] PR (push + open on user authorization); CI → merge on green (gh-verified MERGED before main sync)
