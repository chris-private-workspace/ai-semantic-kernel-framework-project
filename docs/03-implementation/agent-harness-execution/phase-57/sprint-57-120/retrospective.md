# Sprint 57.120 Retrospective — Chat-v2 Inspector Turn-Metadata Wire (active-skill row)

**Closed**: 2026-06-15 · **Branch**: `feature/sprint-57-120-chatv2-inspector-turn-metadata-wire` (from `main` `9fa42d22`) · **Slice**: `AD-ChatV2-Inspector-Turn-Metadata-Wire` (ISSUE-5) · CHANGE-087 · NO design note (feature continuation)

## Q1 — What was delivered?

The chat-v2 Inspector "Turn" tab gained a per-turn **`active_skill`** KV row (between `cost` and `trace_id`) showing the force-loaded skill ("⚡ {skill}") for the inspected turn, or "—" when none. Pure FE + store: the existing `loop_start.active_skill` (57.116, already on the wire) is carried forward onto the `AgentTurn` at `turn_start` (from the most-recent non-injected `UserTurn`, the loop trigger), and rendered via the existing `KV` helper. NO backend / migration / wire (count 24) / codegen / new wire field. 5 files, ALL FE (3 src + 2 test). Both drive-through legs PASS.

## Q2 — Estimate accuracy / calibration

- **Scope class**: `chatv2-inspector-existing-field-surface` (NEW, 1st data point). Agent-delegated: **no** (parent-direct; `agent_factor` 1.0 → 3-segment form).
- Bottom-up est ~3.5 hr → class-calibrated commit ~1.9 hr (mult 0.55) → **actual ~3.0 hr** → **ratio actual/committed ≈ 1.6 (OVER band, > 1.20)**.
- **Why over**: the code was trivial (3 one-to-few-line edits + 5 test cases reusing existing factories); the sprint cost was DOMINATED by the fixed-cost ceremony (plan mirroring 57.119 + checklist + Day-0 三-prong + drive-through + CHANGE-087 + retro + navigators). The 0.55 multiplier was borrowed from the `frontend-feature-with-event-wire-addition` family (0.55, VALIDATED), but THAT family has real code-hours (a wire field + codegen + cross-stack parity) for the haircut to bite on. Here there is almost no code to haircut — the ceremony is the work, and ceremony is not code-accelerated. So 0.55 under-committed.
- **Action**: **re-point `chatv2-inspector-existing-field-surface` 0.55 → 0.85** (ceremony-dominated, tiny-code, parent-direct FE surfacing — the haircut barely applies). KEEP 0.85 pending 2-3 sprint validation. Single-over-point caution: per the matrix rollback rule a single ratio > 1.20 re-points conservatively (toward 0.85), not back to 1.0; if a 2nd `*-existing-field-surface` lands < 0.7 at 0.85, lower again.
- **Calibration insight (generalizable)**: for a TINY-CODE + FULL-CEREMONY sprint, the calibration multiplier should approach ~0.85-1.0 regardless of the FE family it resembles — the per-class multipliers in the 0.45-0.65 band assume the bottom-up has enough code-hours that the AI/agent acceleration haircut is meaningful. When the code is ~10 lines and the ceremony is the dominant cost, there is little to haircut.

## Q3 — What went well?

- **Idiom-fit design**: the codebase already assembles `AgentTurn` at `turn_start` from cross-slice lookups (`span_id` from the spans slice). Adding the `activeSkill` carry-forward at the same point — and reading `lastAgent.activeSkill` in the Inspector — fit the existing pattern exactly (the AD's "alongside trace_id / tokens" framing matched the implementation literally).
- **Reuse over reinvention**: `active_skill` already on the wire (57.116) → 0 backend / codegen / migration. The Inspector row reused the private `KV` helper → 0 new CSS / HEX / oklch → mockup-fidelity held byte-identical.
- **Day-0 三-prong caught the one real drift** (`UserTurn` not imported in the store) before Day 1 — a 1-token fix, no mid-sprint surprise. The existing `chatStore.activeSkill.test.ts` (57.116) was the perfect home for the carry-forward tests (factories + `UserTurn` import already there).
- **57.116 build-time lesson applied**: ran `npm run build` (tsc) BEFORE Vitest; `activeSkill?` is optional so no `AgentTurn` literal broke (the 57.116 required-field break did not recur).
- **Drive-through first-try PASS, both legs** — and Leg B doubled as a LIVE proof of the no-leak design (Turn 1 ⚡ code-review, Turn 2 — across two real loops).

## Q4 — What to improve / lessons

- **Calibration-class selection**: don't borrow a multiplier from a same-domain family without checking the code-vs-ceremony ratio. A wire-addition sprint and an existing-field-surface sprint look similar but have very different code-hour profiles → different effective multipliers (see Q2).
- **No backend restart for FE-only drive-throughs**: confirmed the routine — a 0-`.py`-delta sprint can drive-through against the already-running backend (no Risk-Class-E dance) once a quick probe + the live chip/row render confirm the backend emits the needed field. Saved the orphan-worker sweep.
- **Playwright `.fill()` vs the slash menu**: `.fill()` doesn't trigger the per-char slash-menu, but the InputBar's send-time leading-`/skill`-token parse (57.115) still force-loaded correctly — good to know the force-load path is menu-independent.

## Q5 — Anti-pattern self-check

- **AP-4 (Potemkin)**: ✅ clear — the `active_skill` row is a LIVE store value (Turn 1 ⚡ code-review / Turn 2 — across two real loops, the chip + the row agree), proven by the drive-through, not a fixture/dead control/mislabel.
- **AP-2 (side-track)**: ✅ — reachable from the main chat flow (the Inspector on `/chat-v2`); no orphan code.
- **AP-3 (cross-dir scatter)**: ✅ — all changes within `frontend/src/features/chat_v2/` (the chat-v2 feature).
- **AP-6 (speculative abstraction)**: ✅ — no new abstraction; reused the existing `KV` helper + the `turn_start` assembly point + the 57.116 wire field. The `model` row + token sweep were explicitly NOT built (carried).
- **Mockup-fidelity**: ✅ — `styles-mockup.css` byte-identical, 51 HEX/oklch baseline unchanged (reused `KV`).
- **0 violations.**

## Q6 — Carryover

- `AD-ChatV2-Inspector-Turn-Metadata-Wire` (ISSUE-5) Inspector-panel active-skill leg **SHIPPED**. Still carried under the same AD: a per-turn **`model` KV row** (the AskUserQuestion's 2nd option — `currentModel` is captured + in the header badge but not per-turn) + the broader **token sweep** (actual `input_tokens` vs the estimate, `cached_input_tokens`, `cache_hit_rate` — the 57.108 carve-outs + `AD-ChatV2-Inspector-Cost-InStream` hold).
- Remaining Skills-epic item: `AD-Skills-SlashMenu-Mockup` (57.121 — ⚠️ needs a mockup authored first).
- 17.md: N/A (FE-only; no new cross-category contract).

## Q7 — Gate summary

mypy `src` 0/371 (UNCHANGED — 0 `.py`) · run_all 10/10 (count 24; `check_event_schema_sync` green) · `npm run build` ✅ · Vitest 884 (142 files) (+5 vs 879) · `npm run lint` clean · `check:mockup-fidelity` 51 byte-identical · full pytest 2648+5skip UNCHANGED · `loop.py`/`events.py`/`sse.py`/`event_wire_schema`/codegen/migration UNTOUCHED · drive-through both legs PASS (real chat-v2 + gpt-5.2).

## Design Note Extract

N/A — feature continuation (the slice extends the 57.116 wire field + the chat-v2 store/Inspector; no new domain / execution / security model). NO design note (mirrors 57.116/117/119).
