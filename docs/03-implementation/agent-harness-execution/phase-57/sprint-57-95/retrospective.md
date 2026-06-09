# Sprint 57.95 Retrospective — Cat 11 Subagent SSE Relay (node-level)

**Sprint**: 57.95 (Cat 11 → Cat 12 subagent SSE relay, Scope A node-level)
**Closed**: 2026-06-09
**Branch**: `feature/sprint-57-95-subagent-sse-relay`
**Record**: CHANGE-062 (feature-continuation — NO design note)

---

## Q1 — What did we deliver?

The chat-v2 Inspector "Tree" tab now shows the FORK subagent node instead of "no subagents spawned this session" — closing `AD-Subagent-Child-Event-SSE-Relay` at the node level (the 2026-06-06 drive-through gap; 57.94's child ran headless). The chat subagent dispatcher now carries an `event_emitter`, so `SubagentSpawned`/`SubagentCompleted` reach the SSE stream.

- `_category_factories.py` + `handler.py` (`build_real_llm_handler` + `build_handler`) thread the emitter; `router.py` builds a per-request buffer + `_relay_subagent_event` closure + `_drain_subagent_frames` helper, and `_stream_loop_events` drains the buffer (per loop event + at end). Single asyncio task; no queue/lock.
- **No `LoopEvent` contract change** (`SubagentSpawned` already carries `parent_session_id`), **no frontend change** (chatStore + InspectorTree already consume), **`loop.py` UNCHANGED**.
- Gate: mypy `src --strict` 0/351 · pytest **2277** (+6) · run_all 10/10 · black/isort/flake8 clean · `loop.py` diff = 0.
- **Drive-through PASS** (real UI + fresh backend PID 50200 + real Azure gpt-5.2): Tree node `fork` · completed · 3,692 tokens · "subagent node is visible"; Trace shows the relayed `subagent_spawned`/`subagent_completed` frames.

## Q2 — Calibration

Scope class: **`subagent-sse-relay-wiring` (NEW, 0.55 mid-band) — 1st data point, pending 2-3 sprint validation**. Pure backend composition wiring (thread an unwired emitter + a buffer-drain bridge), NOT the `subagent-child-loop-spike` build shape (57.94) and NOT a `loop.py` refactor. **Agent-delegated: no** (parent-direct — the async-ordering correctness of the buffer-drain + the drive-through with the Tree-node assertion are parent work). `agent_factor = 1.0`.

> Bottom-up est ~7.5 hr → class-calibrated commit ~4 hr (mult 0.55) → **actual ≈ 3.5-4 hr (AI-cadence est) → actual/committed ≈ 0.9-1.0 (IN band)**.

- The Day-0 探勘 (Explore agent map + 3 read passes) was the highest-leverage spend: it found the relay chain already exists end-to-end and the carryover's premise ("needs a `LoopEvent` parent_session_id/depth field") is FALSE for node-level → scope collapsed to "wire one emitter + a buffer bridge". The wiring + tests were small once that was known; the drive-through (clean restart + Playwright) was the dominant cost.
- 1st data point → KEEP 0.55 pending validation (the directional signal: landed roughly on the calibrated commit; AI-cadence wall-clock imperfectly measured, `AD-Calibration-AgentDelegated-WallClock-Measure`).

## Q3 — What went well?

- **Day-0 探勘 corrected the scope before any code** (D4): the 57.94 design note + carryover both said node visibility needs a `LoopEvent` contract field. A read-only pass found `SubagentSpawned` (a subclass) already carries `parent_session_id` + the whole chain (dispatcher slot since 57.12, sse.py serialization, frontend consumers) already exists. Scope dropped from "contract change + frontend" to "wire one emitter". This is the `AskUserQuestion` scope-fork (A vs B) paying off — the user picked node-level, and Day-0 showed node-level is tiny.
- **The buffer-drain design avoided a concurrency trap**: the obvious approach (asyncio.Queue + background-task merge) has lifecycle + ordering hazards. Recognizing that the emitter append + the drain both run in `_stream_loop_events`'s single asyncio task → a plain list + drain-per-event suffices. Lower risk, no lock.
- **The drive-through was self-proving**: the Trace tab shows the `subagent_spawned`/`subagent_completed` frames, which are the dispatcher's events (not the tool result) — they appear ONLY because the emitter is wired. Before 57.95 they were dropped. So the Tree node + the Trace frames together are unambiguous proof, not just "the UI looks right".
- **Reused the existing harness**: `_StubLoop` + `_consume` from `test_chat_sla_recording.py` drove `_stream_loop_events` directly — no new fixture scaffolding for the buffer-drain test.

## Q4 — What to improve?

- **Risk Class E bit (cost ~5 min)**: `:8000` was owned by the stale 57.94 backend (reloader + spawn-worker), running the pre-57.95 unwired dispatcher. Caught proactively this time (checked the owner + killed the full python tree BEFORE driving), but it's the 5th consecutive sprint (57.91-95) where a stale `--reload` backend would have masked a startup-built fix. The standing fix (separate worktree per session, or always `dev.py restart` + verify owner before any drive) remains the cure.
- **A minor pre-existing frontend nuance surfaced**: the INLINE `SubagentForkBlock` shows `0t` while the Tree node + the `subagent_completed` frame correctly show 3,692 tokens. Out of this backend-only sprint's scope (the inline block's token field is a frontend dual-emit display detail), logged for a future frontend touch — NOT a 57.95 regression.

## Q5 — Action items / carryover

- Carryover (deferred, → `next-phase-candidates.md`): **Scope B** — child INNER turn-stream nesting (the Tree expanding to show the child's per-turn TAO loop; needs `LoopEvent` base `parent_session_id`/`depth` + `ForkExecutor` forwarding every child event + frontend nested render). `AD-Subagent-Child-Event-SSE-Relay` now node-level CLOSED, turn-stream REMAINS. Plus the inline ForkBlock `0t` token-display nuance; `AD-Subagent-Child-Span-Nesting`; TEAMMATE/HANDOFF real loops; failure policies.
- Calibration: record `subagent-sse-relay-wiring` 0.55 (1st data point) in `calibration-log.md §3` + propose in `sprint-workflow.md §Scope-class matrix`.

## Q6 — Anti-pattern / discipline self-check

- AP-1 (no pipeline-as-loop — the drain is a plain serialize-and-yield of buffered events; run_all confirms it's not flagged) ✅ · AP-4 (this REMOVES a Potemkin — the headless subagent now surfaces; the opposite of a structural-slot-without-content) ✅ · AP-8 (PromptBuilder untouched) ✅ · AP-10 (no mock/real divergence — the tests exercise the same drain path) ✅ · LLM neutrality (SDK leak 0; no adapter touched) ✅ · Multi-tenant (no new query; the relay carries the dispatcher's events as-is) ✅ · Sprint workflow (plan → checklist → Day-0 verify → code → test → drive-through → docs) ✅ · File-header MHist 1-line ✅ · Drive-Through Acceptance (real UI + backend + Azure, the Tree-populated assertion, not gate-only) ✅ · NO design note (feature-continuation per Step 5.5) ✅.

## Q7 — Verdict

Shipped + drive-through PASS. A small, surgical sprint: Day-0 探勘 collapsed the scope (the relay chain already existed; only the chat emitter was unwired), the buffer-drain bridge avoided a concurrency trap, and the drive-through proved the subagent node is now visible in the Tree (with the relayed SSE frames in the Trace as corroboration). `loop.py`-untouched, no contract/frontend change. Honest deferred boundary (Scope B child turn-stream nesting) documented. Push + PR pending user authorization.
