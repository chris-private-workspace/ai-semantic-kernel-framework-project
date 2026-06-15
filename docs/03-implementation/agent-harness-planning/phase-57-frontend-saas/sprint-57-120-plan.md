# Sprint 57.120 Plan — Chat-v2 Inspector Turn-Metadata Wire (active-skill row): The chat-v2 Inspector "Turn" tab (`InspectorTurn.tsx`) shows 8 per-turn KV rows (stop_reason / duration / tokens.in/out/thinking / cost / trace_id / span_id) read from the last `AgentTurn`. Sprint 57.116 wired `loop_start.active_skill` onto the triggering `UserTurn` as a "⚡ {skill}" timeline chip — but the Inspector PANEL has no per-turn "active skill" row, so an operator inspecting a turn cannot see WHICH skill was force-loaded for it alongside its trace_id / tokens. This slice — the chosen thin vertical of `AD-ChatV2-Inspector-Turn-Metadata-Wire` (ISSUE-5, carried from the 2026-06-06 drive-through audit) — surfaces the EXISTING `active_skill` (already on the wire since 57.116, no backend/codegen change) as a new `active_skill` KV row in the Inspector Turn tab, by carrying it forward onto the `AgentTurn` at `turn_start` (the same cross-slice assembly point that already links `span_id`). PURE frontend + store: NO backend / NO migration / NO wire / NO codegen / NO new SSE event / NO new wire field (count 24 unchanged). The bundled-skill registry, `loop.py`, `events.py`, `sse.py`, `event_wire_schema` are all UNTOUCHED.

**Status**: Approved-to-execute (user 2026-06-15: "繼續執行 57.120 AD-ChatV2-Inspector-Turn-Metadata-Wire" — the 120 of the remaining 119✅/120/121; scope aligned via AskUserQuestion 2026-06-15: **Active-skill row 單列** over active-skill+model / a broader metadata sweep)
**Branch**: `feature/sprint-57-120-chatv2-inspector-turn-metadata-wire`
**Base**: `main` HEAD `9fa42d22` (post-#294 — Sprint 57.119 skills system visibility)
**Slice**: `AD-ChatV2-Inspector-Turn-Metadata-Wire` (ISSUE-5) — the **Inspector-panel active-skill metadata row**. The 57.116 user-turn chip and this Inspector-panel row are the two distinct affordances of the same AD; 57.116 chose the chip, this sprint surfaces the Inspector row. Reuses the 57.116 `loop_start.active_skill` wire field — NO new domain, NO new wire/codegen/backend → a **feature continuation** (NO design note, mirrors 57.116/117/119; unlike the spike sprints). CHANGE-087.
**Scope decisions** (per the AskUserQuestion alignment + thin-vertical discipline): (a) **Active-skill row ONLY** — one new `active_skill` KV row in the Inspector Turn tab (alongside trace_id / tokens). The user explicitly chose this over also surfacing `model` (a 2nd row) or a broader sweep (actual input_tokens / cached tokens) — those stay carried. (b) **Reuse the EXISTING wire field** — `active_skill` already rides `loop_start` since 57.116; this sprint adds NO new wire field, NO codegen regen, NO backend change. (c) **Carry-forward at `turn_start`** — the `AgentTurn` gains an optional `activeSkill` populated at `turn_start` from the most-recent NON-injected `UserTurn`'s `activeSkill` (the loop trigger; `loop_start` stamps it just before `turn_start`). This mirrors how `span_id` is already assembled at `turn_start` from the spans slice, and is robust to a mid-run `message_injected` (an injected user turn carries no skill and is skipped). (d) **Honest surface** — null/absent → render "—" (the existing KV placeholder idiom; no AP-4 fabrication). (e) **NO mockup-fidelity drift** — the new row reuses the existing private `KV` helper (`.spread`/`.subtle`/`.mono tnum` mockup classes) + the ⚡ chip idiom; NO new CSS, NO new HEX/oklch literal, `styles-mockup.css` UNTOUCHED → `check:mockup-fidelity` stays green.

---

## 0. Background

The chat-v2 Inspector (`frontend/src/features/chat_v2/components/inspector/`) is a 4-tab panel (Turn / Trace / Memory / Tree), all wired to live SSE-derived store slices (Sprints 57.21 / 57.72 / 57.75). The **Turn** tab (`InspectorTurn.tsx`, a verbatim mockup re-point of `page-chat.jsx` L392-432) picks the most-recent `AgentTurn` from `chatStore.turns` and renders 8 KV rows: `stop_reason` / `duration` / `tokens.in` / `tokens.out` / `tokens.thinking` / `cost` / `trace_id` / `span_id` — each from a real `AgentTurn` field, "—" when null (honest surface; `tokens.thinking` + `cost` are legitimately post-loop "—").

The `AgentTurn` (`types.ts:142-157`) is the denormalized per-turn metadata object, assembled across SSE events in `chatStore.mergeEvent`: created at `turn_start` (`chatStore.ts:400-424`) with `traceId` (from the frame) + `spanId` (looked up from the newest running `TURN` span in the spans slice — a cross-slice assembly already in place); `tokensIn` set at `llm_request`; `tokensOut` / blocks at `llm_response`; `stopReason` / `durationMs` at `loop_end`.

Sprint 57.116 wired `loop_start.active_skill` (a server-confirmed force-loaded skill name, or null) onto the triggering `UserTurn` (`types.ts:128-140` — `UserTurn.activeSkill?`) and chipped it on the timeline ("⚡ {skill}" via `.route-pill`, `UserTurn.tsx:60-71`). The Inspector PANEL was deliberately deferred as a separate slice (`AD-ChatV2-Inspector-Turn-Metadata-Wire`, also logged as ISSUE-5 in the 2026-06-06 drive-through audit). So today an operator inspecting a turn sees its trace_id / tokens but NOT which skill was force-loaded for it.

### Design decision (carry the EXISTING `loop_start.active_skill` (57.116) forward onto the `AgentTurn` at `turn_start` — from the most-recent non-injected `UserTurn` (the loop trigger) — and render it as a new `active_skill` KV row in `InspectorTurn.tsx`, alongside trace_id / span_id; NO new wire field / NO codegen / NO backend / NO migration)

- **US-1 is "the `AgentTurn` carries the active skill"** (store + type): `AgentTurn` (`types.ts`) gains an optional `activeSkill?: string` (mirrors `UserTurn.activeSkill?`). At `turn_start` (`chatStore.ts`), the new `AgentTurn` is stamped with the most-recent NON-injected `UserTurn`'s `activeSkill` (the loop trigger; `loop_start` set it just before). Skipping injected user turns (57.101 — they carry no skill) keeps a mid-run injection from clearing the loop's skill; a new loop's trigger turn has `activeSkill` undefined → no stale leak.
- **US-2 is "the Inspector shows it"** (frontend): `InspectorTurn.tsx` adds one `active_skill` KV row (reusing the private `KV` helper) after `cost` / before `trace_id` (so the config-metadata sits with stop_reason/tokens and the trace identifiers stay grouped at the bottom) — `lastAgent.activeSkill ? \`⚡ ${lastAgent.activeSkill}\` : "—"` (the ⚡ idiom matches the 57.116 chip; "—" when no skill, the existing placeholder).
- **US-3 is "tests"**: FE Vitest — the store stamps `AgentTurn.activeSkill` from the trigger user turn at `turn_start` (and skips an injected turn); `InspectorTurn` renders the `active_skill` row with "⚡ {skill}" when set and "—" when absent.
- **US-4 is "the drive-through"** (real chat-v2 + real backend + real LLM): force-load a skill via `/skill-name` in the chat composer → the user-turn chip appears (57.116) AND the Inspector Turn tab's new `active_skill` row shows "⚡ {skill}"; a plain message (no force-load) → the row shows "—". Screenshots + observed-vs-intended in progress.md.
- **Rejected / deferred** (per the AskUserQuestion): a per-turn `model` row (the 2nd-row option — `currentModel` is captured but only shown in the header badge; carried as a follow-on); the broader sweep (actual `input_tokens` vs the estimate, `cached_input_tokens`, `cache_hit_rate` — `AD-ChatV2-Inspector-Cost-InStream` / the 57.108 token carve-outs hold); any new wire field / codegen / backend / migration.

### Ground truth (Day-0 head-start — direct reads on `main` HEAD `9fa42d22`; ALL re-verified in the formal Day-0 三-prong §checklist 0.1)

**Frontend (US-1/US-2):**
- `frontend/src/features/chat_v2/types.ts`: `UserTurn` (`:128-140`, has `activeSkill?: string` `:139` from 57.116); `AgentTurn` (`:142-157`, fields role/id/at/stopReason/durationMs/blocks/(waiting?)/tokensIn/tokensOut/tokensThinking/costUsd/traceId/spanId — NO activeSkill). → add `activeSkill?: string` to `AgentTurn`.
- `frontend/src/features/chat_v2/store/chatStore.ts`: `loop_start` case (`:363-398`) stamps `active_skill` onto the last user turn; `turn_start` case (`:400-424`) builds `newAgentTurn` (links `spanId` from the newest running TURN span — the existing cross-slice assembly to mirror). → in `turn_start`, compute `triggerSkill = [...s.turns].reverse().find((t): t is UserTurn => t.role === "user" && !t.injected)?.activeSkill` and add `activeSkill: triggerSkill` to `newAgentTurn`. (Import/typing: `UserTurn` type may need importing in the store — Day-0 confirm.)
- `frontend/src/features/chat_v2/components/inspector/InspectorTurn.tsx`: reads `lastAgent` (`:120-121`); the 8 KV rows (`:167-181`) via the private `KV` helper (`:63-70`, `.spread`/`.subtle`/`.mono tnum`). → add `<KV k="active_skill" v={lastAgent.activeSkill ? \`⚡ ${lastAgent.activeSkill}\` : "—"} />` after the `cost` row (`:179`), before `trace_id` (`:180`). No new CSS, no inline-style literal (reuses `KV`).

**Tests + baselines:**
- FE: `ChatInspector.test.tsx` (the Inspector tab spec — Glob the basename Day-0) and/or a `chatStore` spec for the `turn_start` stamp — add the active-skill cases. Confirm Day-0 whether a `chatStore.test.ts` exists for the store-level assertion or whether to assert via the rendered `InspectorTurn`.
- **Baselines (57.119 closeout)**: full pytest **2648+5skip** (UNCHANGED — no backend) · wire count **24** · FE Vitest **879** (142 files) · mockup-fidelity **51** · mypy `src` **0/371** · run_all **10/10**. Re-verify Day-0.
- **No backend. No migration. No wire / codegen change (count 24). NO design note (feature continuation).** **CHANGE next free = 087** (086 = 57.119).

### STALE / drift anchors to re-confirm in the formal Day-0 三-prong (§ checklist 0.1)

(1) The exact `AgentTurn` field list + order (`types.ts:142-157`) — to place `activeSkill?` cleanly (mirror `UserTurn.activeSkill?` `:139`). (2) The `turn_start` `newAgentTurn` constructor (`chatStore.ts:400-424`) — the exact shape + whether `UserTurn` is already imported in the store (for the `t is UserTurn` narrowing). (3) The `loop_start` stamp logic (`chatStore.ts:372-396`) — confirm it stamps the LAST user turn and the truthy-guard, so the most-recent non-injected user turn carries the trigger skill at `turn_start` time. (4) `InspectorTurn.tsx` KV row block (`:167-181`) + the `KV` helper (`:63-70`) — confirm the insertion point + that the `eslint-disable no-restricted-syntax` header already covers the file (no new inline-style → no new lint). (5) The test basenames (`ChatInspector.test.tsx` + any `chatStore` spec) — Glob before any NEW file (the unique-basename lesson); confirm the existing InspectorTurn test idioms (data-testid `inspector-turn`). (6) The FE Vitest baseline (879 vs the actual at HEAD `9fa42d22`). (7) `check:mockup-fidelity` baseline 51 + `styles-mockup.css` byte-identity — confirm the new KV row introduces NO new HEX/oklch (the `HEX_OKLCH_BASELINE` count is unchanged). (8) Baselines re-verify (pytest 2648+5skip / wire 24 / Vitest 879 / mockup 51 / mypy 0/371 / run_all 10/10).

## 1. Sprint Goal

The chat-v2 Inspector Turn tab gains a per-turn **`active_skill`** KV row (alongside trace_id / span_id) showing the force-loaded skill ("⚡ {skill}") for the inspected turn, or "—" when none. Backed by carrying the EXISTING `loop_start.active_skill` (57.116) forward onto the `AgentTurn` at `turn_start` (from the most-recent non-injected `UserTurn`, the loop trigger — robust to mid-run injection) + one new KV row in `InspectorTurn.tsx`. Proven by a real chat-v2 drive-through (force-load → chip + Inspector row both show the skill; plain message → "—"). PURE frontend + store: NO backend / NO migration / NO wire (count 24) / NO codegen / NO new wire field. Mockup-fidelity holds (the row reuses the `KV` helper; no new CSS / HEX / oklch). Closes the Inspector-panel leg of `AD-ChatV2-Inspector-Turn-Metadata-Wire` (ISSUE-5); the `model` row + the token sweep stay carried. Feature continuation (NO design note). CHANGE-087.

## 2. User Stories

- **US-1**: 作為 chat-v2 store，我希望 `AgentTurn` 帶 active skill：`AgentTurn` 加 optional `activeSkill?: string`（鏡像 `UserTurn.activeSkill?`），並在 `turn_start` 從「最近 non-injected `UserTurn`」（loop 觸發者；`loop_start` 剛 stamp 它）carry-forward 到新 `AgentTurn`（與 `span_id` 同一 cross-slice 組裝點；跳過 injected user turn → mid-run injection 不清掉 loop 的 skill，新 loop 的觸發 turn 無 skill → 不殘留），以便 Inspector 能讀 `lastAgent.activeSkill`。
- **US-2**: 作為 operator，我希望 Inspector Turn tab 顯示 active skill：`InspectorTurn.tsx` 在 `cost` 後、`trace_id` 前加一個 `active_skill` KV 列（復用 `KV` helper），值為 `lastAgent.activeSkill ? "⚡ {skill}" : "—"`（⚡ 對齊 57.116 chip idiom；無 skill 顯示 "—" placeholder），以便 inspecting 一個 turn 時能看到它被 force-load 的 skill（alongside trace_id / tokens）。
- **US-3**: 作為 platform，我希望測試守住：FE Vitest — store 在 `turn_start` 從觸發 user turn stamp `AgentTurn.activeSkill`（且跳過 injected turn）；`InspectorTurn` 在 skill 存在時渲染 "⚡ {skill}"、不存在時 "—"，以便回歸受保護。
- **US-4**: 作為 reviewer，我希望真 drive-through（真 chat-v2 + 真 backend + 真 LLM）：在 composer `/skill-name` force-load 一個 skill → user-turn chip 出現（57.116）且 Inspector Turn tab 的新 `active_skill` 列顯示 "⚡ {skill}"；plain message（無 force-load）→ 列顯示 "—"；截圖 + observed-vs-intended（控件 live — 真 store 值真渲染，非 fixture）。

## 3. Technical Specifications

### 3.0 Architecture (carry the EXISTING `loop_start.active_skill` (57.116) → onto `AgentTurn.activeSkill` at `turn_start` → a new `active_skill` KV row in `InspectorTurn.tsx`; NO backend / NO migration / NO wire / NO codegen / NO new SSE event / NO new wire field / NO new table)

```
frontend/src/features/chat_v2/types.ts (EDIT): AgentTurn + activeSkill?: string
frontend/src/features/chat_v2/store/chatStore.ts (EDIT): turn_start — carry activeSkill from most-recent non-injected UserTurn
frontend/src/features/chat_v2/components/inspector/InspectorTurn.tsx (EDIT): + active_skill KV row (reuse KV helper; ⚡ idiom; "—" placeholder)
backend / agent_harness / loop.py / events.py / sse.py / event_wire_schema / codegen / migration / a new wire field: UNTOUCHED / NONE
```

### 3.1 The `AgentTurn.activeSkill` field + `turn_start` carry-forward (US-1)

- **`types.ts`**: `AgentTurn` += `activeSkill?: string` (optional; mirrors `UserTurn.activeSkill?` `:139`). A 1-line comment: the force-loaded skill for the loop this turn belongs to, carried from the trigger user turn at `turn_start`.
- **`chatStore.ts` `turn_start`** (`:400-424`): before building `newAgentTurn`, compute `const triggerSkill = [...s.turns].reverse().find((t): t is UserTurn => t.role === "user" && !t.injected)?.activeSkill;` and add `activeSkill: triggerSkill` to `newAgentTurn`. Why most-recent non-injected user turn: `loop_start` stamps the loop's trigger user turn just before `turn_start`; an injected (57.101) user turn carries no skill and must be skipped so a mid-run injection doesn't clear the loop's skill; a new loop whose trigger has no force-load → `activeSkill` undefined → no stale leak. (Day-0: confirm `UserTurn` is imported in the store for the `t is UserTurn` narrowing — `AgentTurn` already is.)

### 3.2 The Inspector `active_skill` KV row (US-2)

- **`InspectorTurn.tsx`** (`:167-181`): insert, after the `cost` KV (`:179`) and before `trace_id` (`:180`):
  `<KV k="active_skill" v={lastAgent.activeSkill ? \`⚡ ${lastAgent.activeSkill}\` : "—"} />`
  Reuses the private `KV` helper (`.spread`/`.subtle`; non-mono so the skill name reads as a label, matching the chip). The ⚡ matches the 57.116 user-turn chip (no new HEX/oklch — a unicode glyph in text). "—" is the existing null placeholder. No new inline-style → the file's `eslint-disable no-restricted-syntax` header is unaffected. `data-testid` is N/A (the KV helper has none; the test asserts on the visible "active_skill" label + value text, mirroring the existing KV assertions).

### 3.3 Drive-through (US-4) — real chat-v2 + real backend + real LLM

1. Real backend (Risk Class E clean restart from repo-root + `Win32_Process` orphan sweep + a startup probe; `--reload` orphan caution) + the running Vite (:3007) + a dev-login tenant with skills (e.g. acme-skills). Open chat-v2.
2. Force-load a skill: type `/` → pick (or type `/release-notes`) → send a message. Observe: the user-turn "⚡ {skill}" chip (57.116) AND open the Inspector → Turn tab → the new `active_skill` row shows "⚡ {skill}".
3. Send a plain message (no `/skill`) → the Inspector Turn tab's `active_skill` row shows "—". Confirm each is live (real store value, real render — not a fixture): screenshots + observed-vs-intended in progress.md.

### 3.4 What is explicitly NOT done

A per-turn `model` row (the AskUserQuestion's 2nd option — `currentModel` is captured but only in the header badge; carried); the broader sweep (actual `input_tokens` vs the `tokens_in` estimate, `cached_input_tokens`, `cache_hit_rate` — the 57.108 token carve-outs + `AD-ChatV2-Inspector-Cost-InStream` hold); any new wire field / codegen / backend / SSE / migration / new-table change; any `styles-mockup.css` edit (the row reuses existing classes).

### 3.5 Validation (US-1..US-4)

FE Vitest: the store stamps `AgentTurn.activeSkill` from the trigger user turn at `turn_start` (asserts the field after a `loop_start{active_skill}` → `turn_start` sequence) and skips an injected turn (an injected user turn between does not clear it); `InspectorTurn` renders the `active_skill` row "⚡ {skill}" when set and "—" when absent. Gates: mypy strict 0 (UNCHANGED — no backend) · run_all 10/10 (count 24, NO codegen change) · full pytest **2648+5skip UNCHANGED** (FE-only) · Vitest +M vs 879 · mockup-fidelity **51** holds (the row reuses the `KV` helper — no `styles-mockup.css` change, no new HEX/oklch) · `loop.py`/`events.py`/`sse.py`/`event_wire_schema`/codegen/migration UNTOUCHED · `npm run build` (tsc) passes (a non-required optional field on `AgentTurn` won't break event literals, but build verifies the store/render types).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `frontend/src/features/chat_v2/types.ts` | EDIT — `AgentTurn` += `activeSkill?: string` |
| 2 | `frontend/src/features/chat_v2/store/chatStore.ts` | EDIT — `turn_start` carry-forward `activeSkill` from the most-recent non-injected `UserTurn` |
| 3 | `frontend/src/features/chat_v2/components/inspector/InspectorTurn.tsx` | EDIT — `active_skill` KV row (reuse `KV` helper; ⚡ idiom; "—") |
| 4 | `frontend/src/features/chat_v2/components/inspector/ChatInspector.test.tsx` (and/or a `chatStore` spec) | EDIT — `active_skill` row render + store carry-forward cases — Glob basename Day-0 |
| 5 | `claudedocs/4-changes/feature-changes/CHANGE-087-chatv2-inspector-active-skill-row.md` | NEW — change record (incl. the drive-through) |
| — | backend / `agent_harness` / `loop.py` / `events.py` / `sse.py` / `event_wire_schema` / codegen / migration / a new wire field / a design note | **UNTOUCHED / NONE** |

## 5. Acceptance Criteria

1. `AgentTurn` carries an optional `activeSkill`; at `turn_start` it is set from the most-recent non-injected `UserTurn`'s `activeSkill` (the loop trigger), robust to a mid-run injected turn (skipped) and to a new no-skill loop (no stale leak).
2. The Inspector Turn tab renders a new `active_skill` KV row (after `cost`, before `trace_id`) showing "⚡ {skill}" when set and "—" when absent.
3. FE Vitest covers: the store carry-forward at `turn_start` (incl. the injected-turn skip), and the `InspectorTurn` row render (set + absent).
4. Gates: mypy strict 0 (unchanged) · run_all 10/10 (count 24, NO codegen change) · full pytest 2648+5skip UNCHANGED · Vitest +M vs 879 · mockup-fidelity 51 holds (no `styles-mockup.css` change, no new HEX/oklch) · `loop.py`/`events.py`/`sse.py`/`event_wire_schema`/codegen/migration UNTOUCHED · `npm run build` passes.
5. Real drive-through PASS: a `/skill-name` force-load → the Inspector Turn tab's `active_skill` row shows "⚡ {skill}" (and the 57.116 chip); a plain message → "—"; screenshots + observed-vs-intended (the row is live — real store value, real render, not a fixture).
6. The `AD-ChatV2-Inspector-Turn-Metadata-Wire` (ISSUE-5) Inspector-panel active-skill leg shipped; NO design note (feature continuation); CHANGE-087; calibration recorded (`chatv2-inspector-existing-field-surface` 0.55, 1st data point); the `model` row + the token sweep carried.

## 6. Deliverables

- [ ] US-1 `AgentTurn.activeSkill?` (types.ts) + `turn_start` carry-forward from the most-recent non-injected `UserTurn` (chatStore.ts)
- [ ] US-2 the `active_skill` KV row in `InspectorTurn.tsx` (reuse `KV`; ⚡ idiom; "—")
- [ ] US-3 FE Vitest (store carry-forward + injected-skip; row render set + absent)
- [ ] US-4 drive-through PASS (force-load → Inspector row "⚡ {skill}" + chip; plain → "—"; screenshots + observed-vs-intended)
- [ ] CHANGE-087 + closeout (retro Q1-Q7 + calibration + navigators + next-phase-candidates: `AD-ChatV2-Inspector-Turn-Metadata-Wire` Inspector-panel leg shipped, the `model` row + token sweep carried; 17.md N/A — FE-only, no new contract)

## 7. Workload Calibration

- Scope class **`chatv2-inspector-existing-field-surface` 0.55** (NEW, 1st data point; pending 2-3 sprint validation). Shape: surface an ALREADY-store-captured wire field (no new wire field / no codegen / no backend / no migration) in a NEW chat-v2 render location + a thin store carry-forward onto the per-turn aggregate. Kin to `frontend-feature-with-event-wire-addition` 0.55 (VALIDATED 3pt — 57.100/108/116) in work shape (store capture + render + the chat-v2 turn-model familiarity), but LIGHTER (no wire-field add, no codegen regen, no cross-stack parity) — offset by the carry-forward edge-case care (injected-turn skip / no-stale-leak) + the mockup-fidelity-aware row insertion. Set 0.55 to start (same as the kin family); if the 1st data point lands < 0.7, re-point toward 0.45 (the `frontend-page-bug-fix` FE-only-surfacing neighbour).
- **Agent-delegated: no** (parent-direct; a bounded 3-file FE change over a well-understood store + a drive-through that must show a live render — too small to delegate). `agent_factor` 1.0 → §Workload uses the 3-segment form (class multiplier only).
- Bottom-up est ~3.5 hr (`types.ts` AgentTurn field ~0.15 · `chatStore.ts` turn_start carry-forward + edge-case ~0.5 · `InspectorTurn.tsx` KV row ~0.25 · FE Vitest store + render ~0.85 · drive-through ~0.6 · CHANGE-087 + closeout ~1.15) → class-calibrated commit ~1.9 hr (mult 0.55). Day-4 retro Q2 verifies (1st `chatv2-inspector-existing-field-surface` data point; if ratio diverges > 30% note for the matrix).

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| The Inspector shows the LAST `AgentTurn`; if `activeSkill` were read from the "most-recent user turn" only at render, a new no-skill loop could show a stale skill | carry-forward at `turn_start` from the most-recent NON-injected `UserTurn` (the loop trigger): a new loop's trigger turn has `activeSkill` undefined → the new `AgentTurn` gets undefined → "—" (no leak); confirmed by a Vitest sequence test |
| A mid-run `message_injected` (57.101) pushes a no-skill user turn → could clear the loop's skill for subsequent turns | the carry-forward skips injected user turns (`!t.injected`) → the loop's trigger skill is retained across an injection; Vitest asserts the skip |
| `UserTurn` not imported in the store → the `t is UserTurn` narrowing fails to type | Day-0 confirm the store's imports; add `UserTurn` to the existing `types` import if absent (a 1-token import edit) |
| `InspectorTurn.tsx` is a verbatim mockup re-point → a new row could drift mockup-fidelity | the row reuses the existing private `KV` helper (`.spread`/`.subtle`) + a unicode ⚡ in text — NO `styles-mockup.css` edit, NO new HEX/oklch literal → `check:mockup-fidelity` (byte-identity + `HEX_OKLCH_BASELINE`) stays green; run it as a gate |
| Adding a field to `AgentTurn` could break event/turn literals (the 57.116 build-time lesson) | `activeSkill?` is OPTIONAL (not required) → existing `AgentTurn` literals (fixtures/tests) compile unchanged; still run `npm run build` (tsc), not only Vitest, per the 57.116 carryover |
| Risk Class E — a stale `--reload` backend / orphaned spawn-worker serves OLD code at the drive-through | clean no-reload restart from repo-root + `Win32_Process` PID/PPID/StartTime orphan sweep + a startup probe before driving (the 57.118 routine; the cheap path is the chat composer `/skill` — the same as 57.115/116 drive-throughs) |
| The FE Vitest baseline (879) may differ at HEAD `9fa42d22` | Day-0 re-run Vitest to capture the real baseline before adding tests (the +M is relative to it) |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- **A per-turn `model` KV row** (the AskUserQuestion's 2nd option — `currentModel` is captured in the store + shown in the header badge but not per-turn in the Inspector; a natural follow-on, carried under `AD-ChatV2-Inspector-Turn-Metadata-Wire`).
- **The broader metadata sweep** (actual `input_tokens` vs the `tokens_in` estimate, `cached_input_tokens`, `cache_hit_rate` — the 57.108 token carve-outs + `AD-ChatV2-Inspector-Cost-InStream` hold; cost/thinking stay honest "—" by design).
- Any new wire field / codegen / SSE / backend / migration / new-table change (count 24 unchanged).
- `AD-Skills-SlashMenu-Mockup` (57.121 — needs a mockup authored first) — the last remaining Skills-epic item, executed next in sequence.
