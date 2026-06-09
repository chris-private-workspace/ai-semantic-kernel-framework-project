# Sprint 57.96 Retrospective — Cat 11 Subagent child turn-stream nesting (Scope B)

**Sprint**: 57.96 (Cat 11 Scope B — the Inspector Tree node expands to the child's per-turn TAO loop)
**Closed**: 2026-06-09
**Branch**: `feature/sprint-57-96-subagent-child-turnstream`
**Record**: CHANGE-063 (feature-continuation — NO design note)

---

## Q1 — What did we deliver?

The chat-v2 Inspector "Tree" subagent node now **expands** to show the child loop's per-turn TAO loop (the child's `TurnStarted` / `LLMResponded` / `ToolCall*`), closing the remaining (turn-stream) half of `AD-Subagent-Child-Event-SSE-Relay`. 57.94 built the real child loop; 57.95 made the node visible (collapsed); 57.96 expands it.

- Backend: NEW `SubagentChildEvent(subagent_id, inner)` wrapper (`events.py`) + `sse.py` serializer → wire type `subagent_child` (`{subagent_id, inner_type, inner}`; inner re-serialized via its own branch) + `event_wire_schema` 22→23 + codegen regen + `ForkExecutor._drive` forwards the TAO subset (tagged) via the dispatcher's `_emit_safely`. **`loop.py`/`router.py`/`LoopEvent` base UNCHANGED.**
- Frontend: `SubagentNode.childEvents` + `chatStore` `subagent_child` routing by `subagent_id` + `InspectorTree` nested per-turn rows (mockup `.subagent-row`/`.indent` vocabulary).
- Gate: mypy 0/351 · pytest **2283 (+6)** · run_all 10/10 (incl `check_event_schema_sync`) · Vitest **777 (+7)** · build/lint/mockup-fidelity (baseline 53) · `loop.py`+`router.py` diff = 0.
- **Drive-through PASS** (real UI + fresh backend PID 41464 + real Azure gpt-5.2): a `task_spawn` whose child calls `echo_tool` → the Tree node expands to `turn 0 / LLM / → echo_tool() / ← echo_tool · child turn-stream visible / turn 1 / LLM · child turn-stream visible`; the Trace shows the relayed `subagent_child` wire frames; the parent answers "The child returned: `child turn-stream visible`".

## Q2 — Calibration

Scope class: **`subagent-child-turnstream-nesting` (NEW, 0.55 mid-band) — 1st data point, pending 2-3 sprint validation**. A multi-layer feature extension (NEW contract event type + executor forward + frontend data model + store routing + nested render), distinct from `subagent-sse-relay-wiring` (57.95, pure backend composition wiring) and `subagent-child-loop-spike` (57.94, child-loop build). **Agent-delegated: no** (parent-direct — the contract event type + the `subagent_id` tagging correctness + the drive-through nested-Tree assertion are parent verification work). `agent_factor = 1.0`.

> Bottom-up est ~12 hr → class-calibrated commit ~6.5 hr (mult 0.55) → **actual ≈ 6-7 hr (AI-cadence est) → actual/committed ≈ 0.9-1.1 (IN band)**.

- The Day-0 Explore map was again the highest-leverage spend: it found the router relay is ALREADY generic (zero router change) + `sse.py` already serializes the inner TAO types + `InspectorTree` is already recursive → the real work collapsed to "a wrapper type + one serializer + one executor forward + one store case + one render row". The codegen-chain discovery (`event_wire_schema` → codegen → generated FE artifacts + lint #10 + 2 parity tests) was the only non-obvious cost.
- 1st data point → KEEP 0.55 pending validation.

## Q3 — What went well?

- **The wrapper-event decision (locked Day-0 via AskUserQuestion) paid off exactly as predicted**: because `SubagentChildEvent` IS a `LoopEvent`, it rode the existing 57.95 emitter + the already-generic router buffer-drain with ZERO router/loop change. The whole "timing bridge" was inherited free; the diff stayed surgical (events.py + sse.py + fork.py + dispatcher.py + 3 FE files + the codegen registry).
- **`_emit_safely` as the executor emitter avoided both a try/except and an `__init__` ordering trap**: passing the dispatcher's bound `_emit_safely` (not the raw emitter) means the child-event forward is best-effort-isolated for free AND reads the live `_event_emitter` at call time (set after `self._fork` is constructed) → no reordering. AS_TOOL sharing `self._fork` then inherits the forwarding with no extra code.
- **The Day-0 codegen-chain discovery prevented a mid-sprint surprise**: the new wire type touches a 4-file chain (registry → codegen → 2 generated FE artifacts → lint #10) + 2 parity tests (backend + frontend twin). Finding this at Day-1 (not Day-3 CI) meant the codegen regen + both parity-count updates landed in the same commit.
- **The drive-through was self-proving on TWO independent surfaces**: the Tree node expansion (the feature) AND the relayed `subagent_child` wire frames in the Trace (the exact serializer shape `{subagent_id, inner_type, inner}`, impossible pre-57.96 since the child events were discarded). Either alone is suggestive; together they're unambiguous.

## Q4 — What to improve?

- **Risk Class E bit hard (cost ~5 min)**: uvicorn `--reload` RESPAWNS the worker if the worker is killed first — so the reloader must die first. The first kill attempt killed the worker (20360) → the reloader (50200) respawned a new worker (70560) → :8000 stayed owned. Killing the reloader first then the orphan worker freed it. This is the 6th consecutive sprint (57.91-96) where a stale `--reload` backend interfered. The standing cure (separate worktree per session, or always kill the reloader-first tree) remains.
- **The 57.12 emission test broke on a fixed-index assumption** (`emitter.events[1]`): once the child loop forwards TAO events, they interleave between Spawned and Completed, so the Completed is no longer at index 1. Fixed by locating it by type. Lesson for future event-stream additions: tests that index into an emitter's captured-event list by position are fragile when a new event source interleaves — prefer filter-by-type.

## Q5 — Action items / carryover

- Carryover (deferred, → `next-phase-candidates.md`): **recursion depth > 1** (child-of-child turn-stream — needs a 2nd level of `subagent_id` routing + nested-of-nested render) · **full-fidelity child events** (the non-TAO events, deliberately excluded) · **inline `SubagentForkBlock` `0t`** (turn-count, separate component) · **TEAMMATE / HANDOFF real loops** · `AD-Subagent-Child-Span-Nesting` · failure policies.
- Calibration: record `subagent-child-turnstream-nesting` 0.55 (1st data point) in `calibration-log.md §3` + `sprint-workflow.md §Scope-class matrix`.

## Q6 — Anti-pattern / discipline self-check

- AP-1 (the forward is an `isinstance`-gated `await emitter()` inside the EXISTING drain `async for` — no new loop driving; run_all confirms not flagged) ✅ · AP-4 (this REMOVES a Potemkin — the collapsed node now expands to real child telemetry) ✅ · AP-8 (PromptBuilder untouched) ✅ · AP-10 (no mock/real divergence — the tests exercise the same forward path; drive-through on real Azure) ✅ · LLM neutrality (SDK leak 0; no adapter touched) ✅ · Multi-tenant (no new query; the wrapper carries the child's events as-is) ✅ · Sprint workflow (plan → checklist → Day-0 Explore verify → code → test → drive-through → docs) ✅ · File-header MHist 1-line ✅ · Drive-Through Acceptance (real UI + backend + Azure; the Tree-expanded assertion + the Trace frames, not gate-only) ✅ · NO design note (feature-continuation per Step 5.5) ✅ · 17.md event registered (mandatory for a new event type) ✅.

## Q7 — Verdict

Shipped + drive-through PASS. The wrapper-event design (locked Day-0) kept the blast radius minimal — `loop.py`/`router.py`/`LoopEvent`-base untouched — while the Tree node now expands to the child's per-turn TAO loop end-to-end on real Azure, with the relayed `subagent_child` wire frames in the Trace as independent corroboration. Honest deferred boundary (recursion depth > 1, full-fidelity events, TEAMMATE/HANDOFF) documented. Push + PR pending user authorization.
