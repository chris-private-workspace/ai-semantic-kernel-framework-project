# Sprint 57.126 Retrospective — chat-v2 session history replay (arc slice 2/2: complete the backend transcript foundation + the frontend click→replay)

**Closed**: 2026-06-16 · **Branch**: `feature/sprint-57-126-chatv2-session-history-replay-frontend` · **Base**: `main` `c8a338c8` (post-#300, 57.125)

## Q1 — What shipped?

The user-facing payoff of the 2-sprint arc opened by 57.125 — clicking a historical chat-v2 session now LOADS + replays its conversation (`AD-ChatV2-Session-History-Replay-Phase58` CLOSED):
- **Backend** (`router.py`): `_max_main_seq` (seed `main_seq` from the session's MAX → globally monotonic per session across sends; fixes a latent 57.125 multi-turn collision) + persist the inbound user prompt as a `user_message` `message_events` row per send (persist-only, reuses `_persist_main_event`). So the single `/events` source replays a complete `user→agent→user→agent` conversation.
- **Frontend**: `fetchSessionEvents` service + `UserMessageEvent` (hand-written persist-only type) + `loadSessionHistory` store action (conversation-only reset → fetch → sort → replay through the EXISTING `mergeEvent` + a new `user_message` case) + the `SessionList` click rewire. ZERO new CSS; wire 24; no migration/codegen.

## Q2 — Estimate accuracy (calibration)

- **Scope class**: `chatv2-history-replay-fullstack` (NEW). Started **0.60** → **re-pointed 0.85** (1st data point).
- **Agent-delegated: no** (parent-direct; the user_message placement + the MAX-seed + the replay shape mapping + the reset-vs-`reset()` + race/live guards were precise hand-authored decisions). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~10.5 hr → class-calibrated commit ~6.3 hr (mult 0.60). **Actual ≈ 9 hr → ratio ~1.43 OVER band**. Re-point 0.60 → **0.85** per the **ceremony-not-code-accelerated insight** (57.120/57.122/57.123): a full-ceremony parent-direct sprint WITH a mandatory multi-step drive-through + a Day-0 dead-end re-scope (Option C investigated then proved non-viable) has a large fixed-cost the 0.60 wrongly assumed code-hour acceleration would absorb. The Day-0 investigation (2 AskUserQuestions + the deep persistence grep chain) was ~2-2.5 hr alone — but it PREVENTED building Option C wrong (a build-then-revert that would have cost more). KEEP 0.85 pending a 2nd full-stack-chatv2 data point.

## Q3 — What went well?

- **Day-0 三-prong caught a 57.125 design gap before any code** (the highest-value moment): the persisted `/events` has no user prompts (state_data excludes messages; messages table no writer; only HITL-pause metadata). A naive sprint would have shipped an agent-only replay (incomplete) or built Option C (interleave from `/state`) only to find `/state` is empty too. The two AskUserQuestions surfaced the genuine fork and settled Option B (complete the writer) — the correct, complete, single-source path.
- **Reuse-a-proven-pattern de-risked the backend**: `_persist_main_event` took a `{type,data}` dict as-is → the user_message persist was a 2-line addition (no new helper). The `applyPivot` HANDOFF helper was the exact template for the conversation-only reset.
- **The elegance held end-to-end**: persisting the user_message at seq 1 (before loop_start) meant the replay's UserTurn is pushed before loop_start → the 57.116/120 active_skill stamping reconstructs on replay too, for free.
- **Drive-through proved it live**: a fresh-store reload + click replayed the FULL conversation (both user prompts + agent turns + verification + trace); multi-turn seq stayed monotonic 1..34→1..51 across replay→continue. All gates green; one mid-sprint Vitest fix (mock call-history reset).

## Q4 — What to improve / lessons

- **The 0.60 first estimate under-priced the fixed-cost ceremony + the Day-0 investigation** — the ceremony-not-code-accelerated insight (57.120/122/123) applies to full-stack chat-v2 sprints too, not just tiny-code ones. A sprint with a mandatory multi-step drive-through + a real Day-0 fork should start ~0.85.
- **57.125's "Vitest 892" baseline was slightly stale** — the actual pre-sprint count was ~895 (final 904 = +9 net-new). Minor; cite the final number, not the delta against a remembered baseline.
- **Two consecutive sprints (57.125 + 57.126) found the 57.125 persistence design was built on an incorrect premise** (state_data has messages) — a reminder that a backend foundation sprint's "gate + probe" verification (single-send probe) can miss multi-turn / completeness gaps that only the consuming sprint's Day-0 surfaces. The arc structure (backend then frontend) worked BECAUSE the frontend Day-0 re-verified the foundation.

## Q5 — Anti-pattern self-check

- **AP-1** (no fake loop): replay reuses the real `mergeEvent` reducer (a genuine event→Turn fold), not a disguised pipeline. ✅
- **AP-3** (no scattering): the replay logic is in the store (`loadSessionHistory`); the writer is in the chat router beside the sidechain observer. ✅
- **AP-4** (no Potemkin): the replay renders REAL persisted data — proven by integration tests + Vitest + a live drive-through (the user prompts + agent turns reappear). NOT a dead control / fixture / mislabel. ✅
- **AP-6** (YAGNI): `user_message` is persist-only (NOT a speculative live wire event); no loading skeleton built (the mockup has none); volume-filter + retention deferred. ✅
- **AP-11** (no version suffix; no dead code): the `setActiveSessionId` action is still used elsewhere (the store API); the click just calls the richer action. ✅
- v2 lints **10/10** (`check_event_schema_sync` green → the persist-only type did not drift the wire schema). N/A: AP-2/5/7/8/9/10.

## Q6 — Carryover

- **Resume-path main-event persistence** (🟢, NEW) — the resume path (`router.py:1175` `loop.resume`) does NOT persist main events (pre-existing 57.125 gap); a session that ended via a HITL resume replays only up to the pause. A follow-on AD.
- **Live multi-turn context gap** (🟡, NEW — pre-existing, surfaced by the drive-through) — the backend does NOT rehydrate prior conversation messages for the live loop (state_data excludes messages), so a follow-up in the same session loses prior context (turn 2 lost "it"→Paris). This is a real product gap (multi-turn chat is effectively single-turn for context) — NOT replay-related, but worth a dedicated AD.
- `AD-ChatV2-Transcript-Volume-Filter` (🟢) + `AD-ChatV2-Transcript-Retention` (🟢, Phase 58+) — carried from 57.125.
- Inherited from 57.124: `AD-ExecutionContext-ExplicitApproval-Tidy` + C-class / chrome Potemkin + operator-portal audit backlog.

## Q7 — Gate summary

mypy `src` **0/370** · flake8/black/isort clean · run_all **10/10** (wire 24) · full pytest **2712 passed / 5 skipped** (+1) · Vitest **904 passed** (+9) · `diff styles-mockup.css` empty · mockup-fidelity **51** byte-identical · lint exit 0 · build ✅ · NO migration/codegen. **Drive-through PASS** (real UI + real backend + real Azure gpt-5.2; complete replay + continuation; 2 screenshots in `artifacts/`).

## Design Note Extract

N/A — feature continuation (the replay contract was fixed in design note 37 §4 by 57.125, amended here with the persist-only `user_message` row). NO new design note per the §5.5 spike-vs-continuation rule + the 57.120/123 precedent.
