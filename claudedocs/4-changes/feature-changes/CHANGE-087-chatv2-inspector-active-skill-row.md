# CHANGE-087: Chat-v2 Inspector Turn tab — active_skill metadata row

**Date**: 2026-06-15
**Sprint**: 57.120
**Scope**: Frontend / chat_v2 (store + Inspector render) — pure FE, no backend
**Slice**: `AD-ChatV2-Inspector-Turn-Metadata-Wire` (ISSUE-5) — the Inspector-panel active-skill row (the Skills epic's remaining items: this 120, then 121 `AD-Skills-SlashMenu-Mockup`)

## Problem

The chat-v2 Inspector "Turn" tab (`InspectorTurn.tsx`) shows 8 per-turn KV rows (stop_reason / duration / tokens.in/out/thinking / cost / trace_id / span_id) read from the last `AgentTurn`. Sprint 57.116 wired `loop_start.active_skill` (a server-confirmed force-loaded skill name) onto the triggering `UserTurn` as a "⚡ {skill}" timeline chip — but the Inspector PANEL had no per-turn "active skill" row, so an operator inspecting a turn could not see WHICH skill was force-loaded for it alongside its trace_id / tokens. Carried from the 2026-06-06 drive-through audit as ISSUE-5.

## Root Cause / Gap

`active_skill` was already on the wire (57.116 `loop_start.active_skill`) and captured in the store onto the `UserTurn`, but the Inspector Turn tab reads the `AgentTurn`, which carried no skill field. The metadata existed; it just wasn't surfaced in the per-turn Inspector view. The fix is a pure FE store + render addition — NO new wire field, NO codegen, NO backend.

## Solution

Carry the existing `loop_start.active_skill` forward onto the `AgentTurn` at `turn_start` (the same cross-slice assembly point that already links `span_id`), and render it as a new `active_skill` KV row.

- **`types.ts`**: `AgentTurn` += optional `activeSkill?: string` (mirrors `UserTurn.activeSkill?`).
- **`chatStore.ts`** (`turn_start` case): added `UserTurn` to the `../types` import; computed `triggerSkill = [...s.turns].reverse().find((t): t is UserTurn => t.role === "user" && !t.injected)?.activeSkill` and stamped `activeSkill: triggerSkill` on the new `AgentTurn`. The most-recent NON-injected user turn is the loop trigger (`loop_start` stamped it just before); skipping a 57.101 injected mid-run user turn keeps an injection from clearing the loop's skill, and a new no-skill loop's trigger has `activeSkill` undefined → no stale leak from a prior skilled loop.
- **`InspectorTurn.tsx`**: a new `<KV k="active_skill" v={lastAgent.activeSkill ? \`⚡ ${lastAgent.activeSkill}\` : "—"} />` after `cost`, before `trace_id` (reuses the private `KV` helper; ⚡ matches the 57.116 chip; "—" placeholder when absent).

**Mockup-fidelity**: `InspectorTurn.tsx` is a verbatim mockup re-point; the new row reuses the existing `KV` helper (`.spread`/`.subtle`) — NO `styles-mockup.css` change, NO new HEX/oklch literal. `check:mockup-fidelity` stays byte-identical + 51.

**Out of scope** (per the AskUserQuestion alignment): a per-turn `model` KV row (carried); the broader token sweep (actual `input_tokens` vs the estimate, `cached_input_tokens`, `cache_hit_rate` — carried); any new wire field / codegen / backend / migration.

## Files

| File | Change |
|------|--------|
| `frontend/src/features/chat_v2/types.ts` | `AgentTurn` += `activeSkill?: string` |
| `frontend/src/features/chat_v2/store/chatStore.ts` | `turn_start` carry-forward from the most-recent non-injected `UserTurn`; +`UserTurn` import |
| `frontend/src/features/chat_v2/components/inspector/InspectorTurn.tsx` | `active_skill` KV row (reuse `KV`; ⚡; "—") |
| `frontend/tests/unit/chat_v2/chatStore.activeSkill.test.ts` | +3 (carry-forward / injected-skip / no-leak) |
| `frontend/tests/unit/chat_v2/components/inspector/ChatInspector.test.tsx` | +2 (⚡ set / "—" absent); null-dash count 6→7 |

## Verification

- **Gates**: `npm run build` (tsc) ✅ · Vitest **884 (142 files)** (+5 vs 879) · `npm run lint` clean (InspectorTurn reuses `KV` → no inline-style) · `check:mockup-fidelity` **51 byte-identical** · backend `run_all` **10/10** (count 24; `check_event_schema_sync` green = no wire change). git diff: 5 files, ALL FE, **0 `.py`** → mypy `src` 0/371, pytest 2648+5skip, wire 24 definitionally UNCHANGED; `loop.py`/`events.py`/`sse.py`/`event_wire_schema`/codegen/migration UNTOUCHED.
- **Drive-through** (real chat-v2 + real backend + real LLM gpt-5.2, acme-prod, both legs PASS):
  - **Leg A**: `/code-review …` → user-turn "⚡ code-review" chip + a real code-review answer (found the `a-b` bug, verification 0.99) AND Inspector Turn tab (Turn 1) shows the new `active_skill: ⚡ code-review` row between `cost` and `trace_id`.
  - **Leg B**: a plain "what is 2 + 2?" → Inspector Turn tab (Turn 2) shows `active_skill: —` (a new no-skill loop; the prior code-review did NOT leak — the no-leak design, proven live).
  - Each control live (real store value, real render — the row tracks the actual force-load; the chip + the row agree). AP-4 clear. Screenshots: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-120/artifacts/sprint-57-120-leg{A,B}-*.png`.

## Impact

Frontend-only (chat-v2 Inspector). The Inspector Turn tab now surfaces the force-loaded skill per turn. Closes the Inspector-panel leg of `AD-ChatV2-Inspector-Turn-Metadata-Wire` (ISSUE-5). The `model` row + the token sweep stay carried. No backend / DB / wire / API surface change.
