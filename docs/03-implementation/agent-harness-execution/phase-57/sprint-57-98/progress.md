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

## Day 2 — Durable counter + resume/replay + wrapper retire (US-3/US-4/US-5) (2026-06-10)

The production-path flip + wrapper retirement. The Cat 10 gate is now LIVE on the
main chat flow (registry injected into the loop ctor); the `run_with_verification`
wrapper is deleted. **Final gate**: `mypy src` **0/353** · run_all **10/10** ·
**full backend pytest 2290 passed + 4 skipped** (`-m "not real_llm"`, 108.5s; NET
−5 vs baseline = test consolidation, no coverage loss — see §Test conversions) ·
black/isort/flake8 clean.

### US-3 — durable `verification_attempts` (survives pause→resume mid-correction)
- **D-DAY2-1 (design pivot)**: Day-0 Prong 2.5 D1 locked a `DurableState.verification_attempts`
  scalar field + a Reducer patch. Day-2 grep of `state_mgmt/checkpointer.py` found
  `_serialize_state_for_db` (:217) + `_deserialize_state_from_db` (:243) are **explicit
  field allowlists** — a new `DurableState` scalar would NOT round-trip without editing
  BOTH (+ README). The 57.88 `pending_approval` precedent rides `metadata` (already
  round-tripped verbatim). → **carry the counter in `metadata["verification_attempts"]`**
  (lower blast radius, proven round-trip, zero serializer/migration change). Still the
  locked "durable (checkpoint)" decision. The checklist 2.1 "DurableState field + Reducer"
  sub-items are SUPERSEDED (🚧, not done as written; same goal delivered via metadata).
- `loop.py` threading: `_emit_state_checkpoint` + `_emit_deferred_pause` gain a
  `verification_attempts: int = 0` param (stored in metadata only when > 0). Threaded
  through the 3 pause chains that can fire mid-correction: between-turns
  (`_cat9_between_turns_check`→`_hitl_pause`), output-escalate
  (`_cat9_output_escalate_pause`→`_hitl_pause`), tool-HITL
  (`_cat9_tool_check`→`_cat9_hitl_branch`). The input-ESCALATE chain rides the default 0
  (always pre-turn). `resume()` reads `state.durable.metadata.get("verification_attempts", 0)`
  → passes to `_run_turns`; `run()` passes 0 (fresh-run reset is the default — D2).

### US-4 — resume coverage + replay-not-reverified
- **Resume coverage**: NO new code — `resume()` drives the shared `_run_turns`, and
  `build_real_llm_handler` now injects the registry into the loop ctor → a resumed
  continuation's final answer is verified by the SAME in-loop gate as a fresh run.
  This CLOSES the pre-57.98 hole (the wrapper only wrapped the chat `run()`, never
  `resume()`). Documented in `platform_layer/resume/service.py` (was "verification is
  the wrapper's concern, registry discarded" → now "injected; resumed answer verified").
- **Replay-not-reverified**: Day-0 Prong 2c confirmed `_replay_approved_output` re-emits
  the snapshot DIRECTLY (no parse→gate) → satisfied by code-path isolation, no skip flag.

### US-5 — wrapper retired + flow rewired
- `handler.py`: build the verifier registry BEFORE the loop, inject
  `verifier_registry=registry` into the `AgentLoopImpl(...)` ctor; all 3 builders
  (`build_echo_demo_handler` / `build_real_llm_handler` / `build_handler`) now return
  the wired `AgentLoopImpl` ALONE (tuple dropped).
- `router.py`: `loop = build_handler(...)` (no unpack); `_stream_loop_events` drops the
  `verifier_registry` param + plumbing; the wrapper call → `async for event in loop.run(...)`;
  removed the `run_with_verification` import. Resume path already calls `loop.resume()`
  directly → covered for free.
- `verification/correction_loop.py` **DELETED** (git rm); `verification/__init__.py` drops
  the `run_with_verification` + `VERIFICATION_FAILED_STOP_REASON` re-exports.

### D-DAY2-2 — Day-0 Q7 undercount (build_handler had MANY more unpackers)
Day-0 Q7 claimed "the router is the SOLE tuple-unpacker." FALSE. mypy + grep surfaced
unpackers in **production** (`platform_layer/resume/service.py`) AND 7 test files
(`test_handler.py`, `test_chat_hitl_production_wiring.py` ×6, `test_chat_category_activation_wiring.py` ×8,
`test_chat_keystone_wiring.py` ×6, `test_chat_tier2_wiring.py` ×8, `test_chat_verification_smoke.py`,
`test_audit_log_observer.py`, `test_chat_e2e.py`). All converted: `loop, _ = build_…` →
`loop = build_…`; registry-asserting sites read `loop._verifier_registry`. The 2 patch-target
tests (`test_audit_log_observer.py` / `test_chat_e2e.py`) re-pointed from patching
`router.run_with_verification` to a fake loop / `build_handler` whose `run()` yields the sequence.

### D-DAY2-3 — cross-category lint resolved BY the wrapper deletion
`check_cross_category_import` flagged loop.py's `verification.registry` (TYPE_CHECKING) +
`verification.persistence` (lazy) as private cross-category imports. Day-1 imported the
private submodules to dodge the `__init__`→`run_with_verification`→`orchestrator_loop`
cycle. With the wrapper deleted that cycle is GONE → switched both to the PACKAGE import
`agent_harness.verification` (re-exported `persist_verification_event` in `__init__`) →
run_all 10/10.

### Test conversions (Never-Delete via git mv)
- `git mv test_correction_loop.py → test_inloop_gate_tokens.py` — rewritten to drive
  `AgentLoopImpl` in-loop gate (5 judge-token cases + non-final-skip; richer FakeChatClient
  with tool-use + clamp).
- `git mv test_correction_loop_persist.py → test_inloop_gate_persist.py` — rewritten to
  drive the loop + patch `persistence.persist_verification_event` / `.get_session_factory`.
- `test_loop_verification_gate.py` (Day-1) gains `test_gate_skipped_when_empty_registry`.
- Stale-docstring sweep (Prong-2 rule): `verification_log` model+repo, `core/config`,
  `cat9_mutator`, `tools`, `sse.py`, `resume/service.py`, `test_chat_handoff`,
  `test_chat_verification_smoke` — all "run_with_verification wrapper" refs → in-loop gate.

### D-DAY2-4 — gate now LIVE perturbs mock-loop wiring tests (the BIG one)
The full integration sweep first ran **20 minutes / 4 failed** (keystone + tier2). Root
cause: `chat_verification_mode` defaults to **"enabled"** → `build_real_llm_handler` now
injects a REAL `LLMJudgeVerifier` into the loop ctor. The keystone/tier2 wiring tests
build that handler with FAKE Azure env, swap `loop._chat_client` for a mock, and drive
`loop.run()` to a FINAL answer — which now fires the in-loop gate. The verifier's OWN
ChatClient is the fake-Azure adapter (NOT the swapped mock) → a real fake-endpoint network
call that RETRIES (the 20-min runtime) + perturbs the mock-response sequence (extra
correction turn → tier2's last-request assertion fails). Pre-57.98 these tests DISCARDED
the returned registry, so `loop.run()` never verified. **Fix**: set
`CHAT_VERIFICATION_MODE=disabled` in both `_set_fake_azure` helpers (+ a post-setenv
`get_settings.cache_clear()` to beat the conftest re-cache race) → gate dormant → the loop
drives exactly as pre-57.98. **19 passed in 4.06s** (from 20 min). These suites test
category/memory wiring, NOT verification (which is covered by the gate + smoke + inloop suites).

### D-DAY2-5 — persist patch target follows the package import (D-DAY2-3 fallout)
After D-DAY2-3 switched the gate's lazy persist import to the PACKAGE
(`from agent_harness.verification import persist_verification_event`), the converted
persist test's `monkeypatch.setattr("…verification.persistence.persist_verification_event")`
no longer intercepted the gate (which now resolves the name on the PACKAGE namespace).
**Fix**: patch `agent_harness.verification.persist_verification_event` (the package
re-export). `test_persist_failure_silent` is unchanged (it patches
`persistence.get_session_factory`, which the real fn still looks up on its own module).

### Remaining (Day-3+)
- US-6 drive-through (fail-then-pass in-loop correction + resume-verified, real UI + Azure).
- CHANGE-065 + 17.md verifier-flow update (Day-3).
- Day-4 design note `25-verification-in-loop-design.md` (8-pt gate) + closeout.

---
