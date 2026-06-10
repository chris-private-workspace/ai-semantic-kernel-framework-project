# Sprint 57.98 Progress — Verification into the loop (A1)

**Plan**: [`sprint-57-98-plan.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-98-plan.md) · **Checklist**: [`sprint-57-98-checklist.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-98-checklist.md)
**Branch**: `feature/sprint-57-98-verification-in-loop` (from `main` `84389e91`)
**Locked decisions** (AskUserQuestion 2026-06-10): gate order = **guardrail → verification**; attempt counter = **durable (checkpoint)**; max-after terminal = **stop_reason="verification_failed"** (A1 default; ESCALATE→A2 deferred).

---

## Day 0 — Plan-vs-Repo Verify (2026-06-10)

Two read-only Explore recons ran (the §0 head-start "verification-into-loop surface" map + a focused 7-question Day-0 confirmation). All proposal §1 anchors confirmed; all findings **reduce or confirm** scope (no expansion). **go/no-go = GO.**

### Prong 1 (path) — anchors confirmed
- Wrapper `verification/correction_loop.py`: `run_with_verification` `:83-91` (max=2 `:90`) · intercept `LoopCompleted` `:141-144` · `_build_correction_input` `:321-337` · terminal `:229-239` (`VERIFICATION_FAILED_STOP_REASON :80`) · verifier call `:168-171`
- Router `api/v1/chat/router.py`: import `:96` · main wrap `:432-439` · `_stream_resume_events :813-835` · `loop.resume() :827` (un-wrapped — the hole) · endpoint `:838-892` · tuple unpack `:241` · plumbing `:349`
- Handler `api/v1/chat/handler.py`: `build_handler` returns `tuple[AgentLoopImpl, VerifierRegistry|None]` `:257` · registry built `:488-495` (`make_chat_verifier_registry(profile.cheap,…) :492-494`)
- Loop `orchestrator_loop/loop.py`: `_run_turns :1621` · parse `:2012` · output-guardrail pre-gate `:2014-2023` · `_cat9_output_check :1090-1176` · `_cat9_output_escalate_pause :1371-1399` · `_emit_deferred_pause :1039-1088` · `__init__ :311-351` (no verifier param) · action call `:1954` · `resume() :2486-2520` drives `_run_turns :2512` · `_replay_approved_output :2805-2856`
- State `_contracts/state.py`: `LoopState :79-85` · `DurableState :66-76` (no `verification_attempts`)
- Events `_contracts/events.py`: `VerificationPassed :319-329` · `VerificationFailed :332-343` (`correction_attempt :343`) — wire-ready

### Prong 2 (content) + Prong 2.5 (reducer / drift) — 7 confirmations
- **Q1 reducer** (`state_mgmt/reducer.py:141-166`): `_merge_durable` = dict-patch keys + kwargs rebuild; add `verification_attempts` via scalar-replace (mirror `last_checkpoint_version :160`); increment via `reducer.merge(state, {"durable": {"verification_attempts": n}}, source_category=…)`. No action dataclass.
- **Q2 replay** (`loop.py:2833-2856`): `_replay_approved_output` re-emits `LLMResponded`/`Thinking`/`LoopCompleted` DIRECTLY from snapshot — does NOT route through parse→gate. → human-approved replay is NOT re-verified **by code-path isolation** (no explicit skip flag needed).
- **Q3 is_final_answer** (`loop.py:2026-2027`): `should_terminate_by_stop_reason(response) or classify_output(response) == OutputType.FINAL` — reuse verbatim to gate the verify check.
- **Q4 verification_log** (`correction_loop.py:246-318`): `_persist_verification_event()` → `VerificationLogRepository.insert(...)` `:295`, called per-verifier `:204`. Migrate this call into the gate (same granularity). `test_correction_loop_persist.py` asserts `passed/reason/suggested_correction/correction_attempt`.
- **Q5 correction role** (`correction_loop.py:321-337`): plain string concat passed as `user_input` → implicit `user` role. Migrate as `Message(role="user", content=correction_block)`.
- **Q6 stop_reason** (`events.py:128` + `termination.py:52-65`): `stop_reason: str` (NOT enum); `TerminationReason` has no `VERIFICATION_FAILED`; no consumer switches on the string. → emit raw `LoopCompleted(stop_reason="verification_failed")`, **no enum change**.
- **Q7 tuple** (`handler.py:257` + `router.py:241`): router is the SOLE unpacker of the registry. → drop the 2nd tuple element, return `AgentLoopImpl` alone, update the router unpack; no test unpacks it.

### Prong 3 (schema) — N/A
No DB/migration/ORM change (durable field rides the existing `state_snapshots` JSONB checkpoint); no new event type (`VerificationPassed/Failed` already wire-serialized → `check_event_schema_sync` unaffected). Confirmed no new table/column/event.

### Design-note number
`Glob 2*-*.md` → highest = **24** (multi-model-profile); next free = **25** → `25-verification-in-loop-design.md`. (Note: a pre-existing duplicate `20-iam-deep-dive` + `20-subagent-child-loop-design` both use 20 — not this sprint's concern.)

### Drift findings (Day 0)
- **D-DAY0-1** — `_replay_approved_output` re-emits directly (Q2) → the "replay-not-reverified" requirement is satisfied **by code-path isolation**; the plan's conditional "add an explicit skip" is NOT needed. *Scope ↓.* (Keep the assertion test.)
- **D-DAY0-2** — `build_handler` returns a tuple, router sole unpacker (Q7) → resolve the plan's open "decide whether the tuple keeps the registry": **drop it, return `AgentLoopImpl` alone**; update `router.py:241` unpack. *Resolved.*
- **D-DAY0-3** — reducer is dict-patch `_merge_durable`, no action dataclass (Q1) → durable counter increment is a one-line merge-key addition. *Confirmed straightforward.*
- **D-DAY0-4** — `stop_reason` raw string, no enum, not switched-on (Q6) → terminal needs no `TerminationReason` change. *Confirmed plan default.*
- **D-DAY0-5** — correction feedback role = `user` (Q5). *Confirmed.*
- **D-DAY0-6** — `is_final_answer` predicate reusable verbatim (Q3). *Confirmed.*
- **D-DAY0-7** — verification_log writer = `_persist_verification_event` → migrate into the gate (Q4). *Confirmed sub-task (DRIFT 4 from §0).*

### Go/No-Go
**GO.** The gate move is clean: one ctor-param coupling (Q7 resolved), the reducer/replay/predicate/stop_reason/role are all confirmed-simple, and every Day-0 finding reduces or confirms scope. Scope shift vs plan ≈ 0% (D-DAY0-1 slightly reduces work). Proceeding to Day 1.

### Baseline (at branch creation)
- Branch `feature/sprint-57-98-verification-in-loop` from `main` `84389e91`
- pytest collected = **2295** (2291 passed + 4 skipped, 57.97-merged); `mypy src` = **0/353**; `run_all` 10/10

---

## Day 1 — Loop ctor verifier + in-loop gate (US-1 / US-2) (2026-06-10)

Added the in-loop Cat 10 verification gate; **production path still uses the wrapper** (the registry is not yet passed to the loop ctor — that is Day-2), so the gate is DORMANT in production → main flow byte-identical, regression green.

### Done
- **US-1 — loop ctor** (`loop.py`): `AgentLoopImpl.__init__` gains `verifier_registry: "VerifierRegistry | None" = None` + `max_correction_attempts: int = 2` (stored). `VerifierRegistry` imported under `TYPE_CHECKING` (the `verification` package __init__ re-exports `run_with_verification` → imports `orchestrator_loop` → a module-level import would cycle); the gate duck-types `get_all()`/`len()`; persistence is lazy-imported.
- **US-2 — the gate** (`loop.py`): NEW `_VerifyVerdict` dataclass + `_build_correction_block()` + `_cat10_verify_gate()` (runs the registry's verifiers, collects VerificationPassed/Failed events, persists each, accumulates judge tokens) + integration in `_run_turns` AFTER `_cat9_output_check` and BEFORE the stop_reason/FINAL terminator (locked guardrail→verification order), gated on `is_final_answer AND verifier_registry`. PASS → deliver (judge tokens stamped on the END_TURN terminators); FAIL<max → append the failed assistant answer + a `user` correction Message + `verification_attempts++` + `turn_count++` + `continue` (the in-loop critique); FAIL==max → `LoopCompleted(stop_reason="verification_failed")`. `VERIFICATION_FAILED_STOP_REASON` defined in loop.py.
- **verification_log persistence**: extracted to NEW `verification/persistence.py::persist_verification_event` (Sprint 57.11 logic verbatim); the gate lazy-imports it. `correction_loop.py` untouched Day-1 (transient dup, removed with the wrapper Day-2).
- **Tests**: NEW `test_loop_verification_gate.py` (4 tests): pass-delivers / fail-then-pass-reinjects-as-new-turn (asserts the correction text reaches the 2nd chat request + the failed answer is in context) / fail-at-max→verification_failed / no-registry→skipped (byte-identical).

### Gate
- NEW gate tests **4/4 pass**; regression `tests/unit/agent_harness/{orchestrator_loop,verification}` + `test_chat_verification_smoke` + `test_verification` = **132 passed** (gate dormant → zero behavior change).
- `mypy src` **0/354** (353 + persistence.py); black/isort/flake8 (changed src + new test) clean. (Single-file `mypy <test>` reports import-untyped artifacts — a known single-file-mode limitation; `mypy src` is the authoritative source gate, and the test is flake8-clean.)

### Day-1 notes / drift
- **D-DAY1-1** — `verification_attempts` is a `_run_turns` LOCAL (param, default 0) this day; the DURABLE-across-pause persistence (DurableState/metadata + checkpoint + between-turns/output pause forwarding + resume read) is Day-2 (US-3), matching the checklist split. The gate's within-run max logic is fully working + tested today.
- **D-DAY1-2** — `correction_attempt` on the `VerificationFailed` event is 0-indexed (the first failure = attempt 0), matching the retired wrapper's `_persist` semantics (the proposal's "attempt=1" wording was loose). Tests assert `correction_attempt == 0` on the first failure.
- **D-DAY1-3** — judge-token accounting across a mid-correction pause is deferred (an Open Invariant for the design note): within a non-paused run the verif tokens accumulate + stamp the terminal LoopCompleted correctly; a rare pause-mid-correction may under-count (no LoopCompleted fires until resume). The `verification_attempts` counter IS made durable Day-2; the judge-token cross-pause accounting is documented, not fixed in A1.

### Remaining (Day-2+)
- US-3 durable `verification_attempts` (metadata + checkpoint + pause forwarding + resume read) → survives pause→resume mid-correction.
- US-4 resume coverage assertion + `_replay_approved_output` not-re-verified test (Day-0 Q2 confirmed it re-emits directly → no skip flag needed).
- US-5 wrapper retire: handler ctor injection + router wrapper delete + `correction_loop.py` removal + `__init__` re-export + convert `test_correction_loop*.py`.
- US-6 drive-through (fail-then-pass in-loop + resume verified).

---
