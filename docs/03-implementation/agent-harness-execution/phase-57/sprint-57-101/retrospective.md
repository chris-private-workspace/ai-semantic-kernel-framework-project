# Sprint 57.101 Retrospective — between-turns message injection primitive (B1)

**Sprint**: 57.101 · **Closed**: 2026-06-11 · **Branch**: `feature/sprint-57-101-between-turns-injection`
**Scope class**: `loop-injection-primitive-spike` (NEW, mult 0.55) · `agent_factor` 1.0 (parent-direct)

---

## Q1. What was delivered?

The harness-deepening B1 slice: a chat-v2 user can send a supplementary instruction MID-RUN and the agent picks it up at the next turn boundary. Built as one reusable loop primitive (`MessageInbox`) so B2 TEAMMATE reuses the same drain seam.

- **Cat 1**: `MessageInbox` ABC (`_contracts/inbox.py`) + `_run_turns` drain seam (loop ctor `+message_inbox`).
- **Cat 12**: new `MessageInjected` wire event + codegen (count 23→24).
- **Cat 9**: each injected message runs the INPUT guardrail (`check_input`); a non-PASS injection is dropped + `GuardrailTriggered(input)`.
- **api**: module-level `InjectionRegistry` (tenant-scoped) + `QueueMessageInbox` + `POST /{id}/inject` (auth + active+owner gated).
- **Frontend**: composer usable mid-run (real_llm) → `inject()`; `message_injected` → `UserTurn(injected)` + tag.

## Q2. Estimate accuracy (calibration)

- Plan §Workload: bottom-up ~18.5 hr → class-calibrated commit ~10 hr (mult 0.55). Agent-delegated: **no** (parent-direct, `agent_factor` 1.0).
- Actual: AI-paced (not wall-clock measurable for an AI agent — recorded as estimate per the project's no-fabricated-metrics rule). The work matched the spec'd file list closely; the dominant real costs were exactly as predicted: the loop drain correctness (the D-DAY1-1 guardrail finding), the cross-request channel tenant-safety, the composer-mid-run UX (real_llm gating to avoid an echo dead-control), and the drive-through timing.
- **Calibration verdict**: `loop-injection-primitive-spike` 0.55 — 1st data point, KEEP pending 2-3 sprint validation. The slice was larger than 57.98-100 (a NEW Cat 1 contract + a NEW event TYPE + a module registry + a new API endpoint + the composer rework) but the 0.55 (cross-stack composition, like 57.96) fit because no single piece was deep — each layer was a thin, well-understood addition over the 57.88-99 pause/resume + 57.96 codegen machinery.

## Q3. What went well?

- **The Day-0 three-prong + the D-DAY1-1 catch**: reading the real `_cat9_between_turns_check` body (Prong 2 content-verify) disproved the proposal's "free between-turns guardrail check" assumption (it checks OUTPUTs, skips user inputs) BEFORE the drive-through. The fix (run `check_input` instead) was both more correct AND realized the DoD's guardrail-on-injected case. This is exactly what the content-verify prong is for.
- **The one-primitive-two-payoffs design held**: the `MessageInbox` ABC is genuinely reusable for B2 (not speculative — B2 is the next slice).
- **Codegen + parity discipline**: adding a NEW event type went cleanly through the 57.96 4-file codegen chain; the only count-bump touch points were caught by the parity test + `eventSchema.generated.test.ts`.
- **Drive-through PASS for BOTH DoD cases**, observed live with real Azure gpt-5.2 (not gate-only): the injection was acted-on (Case A) and guardrail-dropped (Case B).

## Q4. What to improve / lessons

- **Infra-down looked like a code hang (the big lesson)**: the dev infra (Docker Postgres/Redis/RabbitMQ) was DOWN at session start; the full-suite integration tests timed out ~104s/file on the dead DB, and two background full-runs I'd kicked off compounded it via DB contention — which read as a "hang" and sent me chasing a DB-corruption theory. The decisive diagnostic was the port check (`:5432 free` = infra down, not corrupt). **Lesson**: before reading a slow/failing integration suite as a code problem, run `docker compose ps` + a port check FIRST. Also: never kick off two full-suite runs concurrently (they contend on the test DB).
- **Don't kick off a second full pytest while one is running** — the contention made both crawl + masked the real (infra) cause.
- **Drive-through timing for a mid-run UI action against a real LLM**: a fast 2-turn run completes before a discrete Playwright inject can land. The reliable recipe: a forceful autonomous-multi-tool prompt (for runway) + inject IMMEDIATELY after send with no intermediate snapshot.

## Q5. Anti-pattern audit

- AP-1 (pipeline-not-loop): N/A — the drain is `for m in drained: append + yield` data-flow at the loop top; the loop stays `while True` driven by stop_reason (`check_ap1` green).
- AP-2 (no orphan): the inject endpoint + inbox are reachable from `router.py` + `handler.py`; `check_ap1`/`check_event_schema_sync` green.
- AP-4 (no Potemkin): the FE gates the Inject affordance to real_llm so there is no dead control in echo_demo; the drive-through proved the button has a real effect.
- AP-6 (no speculative abstraction): the `MessageInbox` ABC has a concrete B2 consumer (the next slice).
- AP-11 (no version suffix): none.

## Q6. Carryover

- **B2 TEAMMATE** — reuse the `MessageInbox` ABC: the child loop's inbox backed by the parent's mailbox channel (the next harness-deepening slice).
- Open invariants (design note 26 §4): echo-mode injection (intentionally unsupported), pause-on-injection (dropped, not paused — a follow-on), persistence (in-memory per-run), per-tenant injection policy (C3), optimistic FE echo (render-on-drain by design).

## Q7. Design Note Extract (spike sprint — required)

**File**: `docs/03-implementation/agent-harness-planning/26-between-turns-injection-design.md`
**Verified ratio (estimated)**: ≥ 95% (every invariant has a file:line + a pytest; the drive-through §2.6 is the one end-to-end case, now PASS).
**8-Point Quality Gate**:
- [x] 1. Section headers map to the US (drain seam / wire event / channel / endpoint / render / drive-through)
- [x] 2. Every claim has file:line (`loop.py` drain block, `injection_registry.py`, `event_wire_schema.py`, etc.)
- [x] 3. Decision matrices (module-registry vs per-request mailbox; INPUT-check vs between-turns-check D-DAY1-1; drop vs pause vs terminate)
- [x] 4. Verification commands (`pytest …test_inbox_drain.py::…`, etc.)
- [x] 5. Test fixture references (`ScriptedInbox`, `CapturingChatClient`, `BlockOnKeyword`)
- [x] 6. Open invariants分界 (§4 — B2 / echo / pause / persistence / policy / optimistic-echo deferred)
- [x] 7. Rollback path (`message_inbox=None` dormant default + revert the handler wiring line; ~30 min)
- [x] 8. 17.md cross-ref (`MessageInbox` §2.1 + `MessageInjected` §4.1)

**Reviewer pass**: self-review (parent-direct).
