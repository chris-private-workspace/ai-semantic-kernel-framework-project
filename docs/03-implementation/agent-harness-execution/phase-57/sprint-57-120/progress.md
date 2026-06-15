# Sprint 57.120 Progress — Chat-v2 Inspector Turn-Metadata Wire (active-skill row)

**Plan**: [`sprint-57-120-plan.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-120-plan.md) · **Checklist**: [`sprint-57-120-checklist.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-120-checklist.md)
**Branch**: `feature/sprint-57-120-chatv2-inspector-turn-metadata-wire` (from `main` `9fa42d22`, post-#294)
**Slice**: `AD-ChatV2-Inspector-Turn-Metadata-Wire` (ISSUE-5) — the Inspector-panel active-skill metadata row. Pure FE + store; reuses the 57.116 `loop_start.active_skill` wire field. NO backend / migration / wire (count 24) / codegen. CHANGE-087.

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch — 2026-06-15

### Branch
`git checkout -b feature/sprint-57-120-chatv2-inspector-turn-metadata-wire` from `main` `9fa42d22` ✅

### Prong 1 — Path verify ✅
- `frontend/src/features/chat_v2/types.ts` (EDIT) — present; `AgentTurn` `:142-157`, `UserTurn.activeSkill?` `:139` ✅
- `frontend/src/features/chat_v2/store/chatStore.ts` (EDIT) — present; `turn_start` `:400-424`, `loop_start` `:363-398` ✅
- `frontend/src/features/chat_v2/components/inspector/InspectorTurn.tsx` (EDIT) — present; KV block `:167-181`, `KV` helper `:63-70`, `eslint-disable no-restricted-syntax` header `:52` ✅
- Test homes (Glob — `tests/unit` convention, NOT co-located): `frontend/tests/unit/chat_v2/chatStore.activeSkill.test.ts` (the 57.116 store test — the natural home for the carry-forward) + `frontend/tests/unit/chat_v2/components/inspector/ChatInspector.test.tsx` (the Inspector render test — `makeAgentTurn` factory + KV assertions) ✅
- `claudedocs/4-changes/feature-changes/CHANGE-087-*.md` free; NO design note (feature continuation) ✅

### Prong 2 — Content verify (drift findings)
- **D-agentturn-shape** (confirmed): `AgentTurn` (`types.ts:142-157`) has a `// Inspector Turn tab metadata` group (`:150-156`: tokensIn/out/thinking/costUsd/traceId/spanId) → `activeSkill?: string` fits there (mirror `UserTurn.activeSkill?` `:139`).
- 🔧 **D-turnstart** (real drift — 1-token fix, non-scope-shifting): `turn_start` (`chatStore.ts:400-424`) builds `newAgentTurn` linking `spanId` from the newest running TURN span (the cross-slice assembly idiom to mirror). **`UserTurn` is NOT imported in the store** (`:66-80` imports `AgentTurn`/`Block`/`HITLTurn`/`Turn`/… but not `UserTurn`) → must add `UserTurn` to the `../types` import for the `(t): t is UserTurn` narrowing. (The `loop_start` case at `:389-390` accesses `t.activeSkill` only inside a `t.role === "user"` guard — discriminated-union narrowing — so it needs no import; the `.find` type-guard predicate does.)
- **D-loopstart-stamp** (confirmed): `loop_start` (`:372-396`) stamps the LAST user turn's `activeSkill` with a truthy-guard (a null never overwrites) → at `turn_start` time the most-recent non-injected user turn carries the trigger skill.
- **D-inspectorturn-kv** (confirmed): insert the row after the `cost` KV (`:179`), before `trace_id` (`:180`); reuse the private `KV` helper (`.spread`/`.subtle`, non-mono) → no new inline-style → the file's `eslint-disable no-restricted-syntax` header is unaffected.
- **D-fe-test-path** (confirmed — the 57.119 lesson): tests live under `frontend/tests/unit/chat_v2/...` (NOT co-located). `chatStore.activeSkill.test.ts` already has `userTurn`/`agentTurn`/`loopStart`/`lastUser` factories + imports `UserTurn` (extend it). Event shapes (from `generated/loopEvents.generated.ts`): `turn_start: {trace_id?, turn_num}`, `message_injected: {trace_id?, text}`.

### Prong 3 — Schema verify: N/A
No new table / migration / ORM / backend — pure FE store + render.

### D-baselines (at HEAD `9fa42d22`)
- FE Vitest: **879 passed (142 files)** ✅ (matches the 57.119 closeout baseline)
- mockup-fidelity: **byte-identical `styles-mockup.css` + 51 hardcoded hex/oklch lines** ✅
- pytest 2648+5skip / wire 24 / mypy `src` 0/371 / run_all 10/10 — UNCHANGED expected (FE-only); confirm at gate.

### Catalog drift
1 real drift (**D-turnstart**: `UserTurn` not imported → a 1-token import edit, non-scope-shifting). All other Prong-2 anchors confirmed as the plan assumed.

### Go/no-go: 🟢 GO
The design holds end-to-end: `loop_start.active_skill` (57.116, on the wire) → carry-forward onto `AgentTurn.activeSkill` at `turn_start` from the most-recent non-injected `UserTurn` → a new `active_skill` KV row in `InspectorTurn.tsx` (reuse `KV`, no mockup-fidelity drift). No scope shift > 20%.

---

## Day 1-2 — FE code + Vitest + gate sweep — 2026-06-15

### Code (3 src files, all FE; ~0.7 hr actual vs ~0.9 hr est)
- **`types.ts`**: `AgentTurn` += `activeSkill?: string` (in the `// Inspector Turn tab metadata` group, mirrors `UserTurn.activeSkill?`).
- **`chatStore.ts`**: added `UserTurn` to the `../types` import (D-turnstart drift fix); in `turn_start`, `const triggerSkill = [...s.turns].reverse().find((t): t is UserTurn => t.role === "user" && !t.injected)?.activeSkill;` + `activeSkill: triggerSkill` on `newAgentTurn` (a 6-line WHY comment — most-recent non-injected user turn = the loop trigger; skip injected 57.101; no stale leak).
- **`InspectorTurn.tsx`**: `<KV k="active_skill" v={lastAgent.activeSkill ? \`⚡ ${lastAgent.activeSkill}\` : "—"} />` after `cost`, before `trace_id` (reuse `KV`; ⚡ = 57.116 chip idiom).
- All 3 MHist + Last Modified 2026-06-15.

### Tests (2 files, +5 Vitest; ~0.7 hr actual vs ~0.85 hr est)
- **`chatStore.activeSkill.test.ts`** (+3): the carry-forward (`loop_start{skill}`→`turn_start` → `AgentTurn.activeSkill`), the injected-skip (a `message_injected` between two `turn_start`s doesn't clear the skill), the no-leak (a new `loop_start(null)` loop → undefined). +`turnStart`/`messageInjected` factories + `lastAgent()` + `AgentTurn` import.
- **`ChatInspector.test.tsx`** (+2, 1 mod): the row "⚡ code-review" when set; "—" + exactly-1-dash when no skill; the null-placeholder dash count 6→7.

### Build-time lesson check (57.116 carryover)
`npm run build` (tsc) ran BEFORE Vitest — `activeSkill?` is OPTIONAL so no `AgentTurn` literal/fixture broke (the 57.116 required-field break did not recur). Clean ✓.

### Gates (all green)
- `npm run build` ✅ (✓ built 3.50s) · Vitest **884 (142 files)** (+5 vs 879) · `npm run lint` clean (no new errors; InspectorTurn reuses `KV` → no inline-style) · `check:mockup-fidelity` **51 byte-identical** (no `styles-mockup.css` change, no new HEX/oklch) · backend `run_all` **10/10** (count 24; `check_event_schema_sync` green = no wire change).
- **git diff scope**: 5 files, ALL FE (3 src + 2 test), **0 `.py`** → mypy `src` 0/371, pytest 2648+5skip, wire 24 all definitionally UNCHANGED. `loop.py`/`events.py`/`sse.py`/`event_wire_schema`/codegen/migration UNTOUCHED.

---

## Day 3 — Drive-through (real chat-v2 + real backend + real LLM) — 2026-06-15

### Setup
- Backend :8000 → 200, Vite :3007 → 200 (Invoke-WebRequest probe; curl blocked by a sandbox hook). The backend is 57.119 code (post-57.116 → emits `loop_start.active_skill`); this sprint has 0 `.py` changes so the running backend code == this branch's backend. Vite HMR'd the 3 changed FE files. NO Risk-Class-E restart needed (no backend code delta) — verified the chip + row rendered live (proof the running backend emits active_skill).
- dev-login (`/auth/dev`) jamie@acme.com / acme-prod / operator → `/chat-v2`. Mode = real_llm (gpt-5.2). Note: the dev-login tenant dropdown has no acme-skills, but the SYSTEM-bundled skills (code-review/summarize/digest, 57.113/118) resolve for every tenant → `/code-review` force-loads on acme-prod.

### Leg A (force-load → Inspector active_skill row) — PASS ✅
- Typed `/code-review please review: def add(a, b): return a - b` → Send. The `/code-review` leading token was stripped (user turn shows only "please review: …") and force-loaded the skill.
- **User turn**: a "⚡ code-review" chip (the 57.116 affordance, `title="Skill: code-review"`). **Agent turn** (gpt-5.2, real): a real code-review — `## Summary` (subtracts instead of adds; one correctness bug) + a `## Risks` table (High: returns `a - b` not `a + b`) + `## Suggested fixes` (`return a + b`). Verification passed 0.99.
- **Inspector → Turn tab (Turn 1 · end_turn)**: the NEW **`active_skill: ⚡ code-review`** row, positioned exactly between `cost` (—) and `trace_id` (2b6f96019dd74f4992fdeaa16a4a16be) as designed. tokens.in 2,725 / tokens.out 106 / span_id a7cd45486285e875.
- Screenshot: `artifacts/sprint-57-120-legA-inspector-active-skill.png`.

### Leg B (plain message → "—", no leak) — PASS ✅
- Typed `what is 2 + 2?` (no `/skill`) → Send → agent "2 + 2 = 4" (verification 0.99).
- **Inspector → Turn tab (Turn 2 · end_turn)**: the **`active_skill: —`** row (the placeholder). trace_id 8f0ee150273f40d0a7a608ee28467ac5 (a DIFFERENT trace — a new loop) / tokens.in 2,427 / tokens.out 11.
- This proves BOTH (a) the row tracks the ACTUAL inspected turn (Turn 1 = ⚡ code-review, Turn 2 = —) — live, not a fixture; and (b) the **no-leak** design — the prior code-review loop did NOT bleed into the new no-skill loop's turn (the Vitest no-leak case, proven live).
- Screenshot: `artifacts/sprint-57-120-legB-inspector-no-skill-dash.png`.

### Observed vs intended
Intended: surface the force-loaded skill as a per-turn Inspector row (alongside trace_id/tokens), "—" when none. Observed: EXACTLY that — Turn 1 "⚡ code-review", Turn 2 "—", both from the real store value populated by the carry-forward at `turn_start`, rendered in the real Inspector. Every control live (the row value changes with the actual force-load; the user-turn chip + the Inspector row agree). **AP-4 clear** — no dead control, no fixture, no mislabel.
