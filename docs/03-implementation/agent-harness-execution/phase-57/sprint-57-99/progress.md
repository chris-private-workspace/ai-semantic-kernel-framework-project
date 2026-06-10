# Sprint 57.99 Progress — Verification-ESCALATE human-in-the-loop (A2)

**Plan**: [`sprint-57-99-plan.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-99-plan.md) · **Checklist**: [`sprint-57-99-checklist.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-99-checklist.md)
**Branch**: `feature/sprint-57-99-verification-escalate` (from `main` `be89d3ec` = A1 merged)
**Locked decisions** (AskUserQuestion 2026-06-10): APPROVE = **deliver the held failed answer (human overrides the judge)**; REJECT-with-note = **one human-coached turn, then terminal**; gating = **global settings toggle `chat_verification_escalate_on_max`, default OFF = A1 preserved**.

---

## Day 0 — Plan-vs-Repo Verify (2026-06-10)

An Explore "A2 verification-ESCALATE surface" recon ran first (mapped the 8-item surface + the realistic shape); a focused Day-0 grep then confirmed the load-bearing anchors on the A1-merged code. All anchors confirmed; all findings **reduce or confirm** scope (no expansion). **go/no-go = GO.**

### Prong 1 (path) + Prong 2 (content) — anchors confirmed (post-A1-merge)
- **The swap point** — `loop.py`: `if verdict.outcome == "failed_max":` `:2344` → `LoopCompleted(stop_reason=VERIFICATION_FAILED_STOP_REASON)` `:2346` (`VERIFICATION_FAILED_STOP_REASON = "verification_failed"` `:220`; the `_VerifyVerdict` failed_max return `:1688`). → A2 wraps `:2344-2346` in `if self._verification_escalate_on_max and not verification_escalated: → escalate; else → the A1 terminal`. **Confirmed exact.**
- **resume() kind dispatch is an `if/elif` chain** — `if kind == "input":` `:2856` / `elif kind == "between_turns":` `:2884` / `elif kind == "output":` `:2915` (→ `_replay_approved_output` `:2950`). → `elif kind == "verification":` is purely additive (D1 confirmed — no exhaustiveness consumer). **Confirmed.**
- **`_replay_approved_output`** `:3078` — the APPROVE path reuses this shape. **Confirmed.**
- **config** — `core/config/__init__.py`: `class Settings(BaseSettings)` `:28`; `chat_verification_mode: Literal["disabled","enabled"] = "enabled"` `:115`; `chat_verification_judge_template: str = "output_quality"` `:123`. → the new `chat_verification_escalate_on_max: bool = False` goes in the same Settings class near `:115-123` (the `chat_verification_*` cluster). **Confirmed.**
- The Explore recon's other anchors (carried into the plan §0, to re-confirm exactly at Day-1 as they are touched): `_emit_deferred_pause :1114-1165` (kinds tool/input/between_turns/output; output `response_snapshot`) · `_cat9_output_hitl_pause :1484-1604` (the A2 template) · `_replay_approved_output` snapshot fields `:3099-3105` · durable counter write `:3185-3186` + resume read (`metadata["verification_attempts"]`) · `ApprovalDecision.reason hitl.py:77` + `DecisionRequestBody.reason governance/router.py:106` · events `ApprovalRequested/Received events.py:400-408` · handler verification-mode threading `:265-270` + 3 builders.

### Prong 2.5 (drift) — confirmations
- **D1** — `resume()` kind dispatch is `if/elif` (`:2856`/`:2884`/`:2915`) → `elif kind == "verification":` additive, no enum/exhaustiveness break. *Confirmed.*
- **D2** — (Day-1) the held-answer snapshot field set (`_replay_approved_output :3099-3105`) must be in scope at the terminal `:2344`; if not, capture earlier in the turn. *To confirm Day-1.*
- **D3** — the REJECT bound: drive `_run_turns` with `verification_attempts=max` + `verification_escalated=True` so a 2nd fail → `failed_max` + already-escalated → terminal (not a 2nd escalate). The FAIL==max branch must read `verification_escalated`. *Design confirmed; wire Day-1.*
- **D4** — no new event (reuse `ApprovalRequested(HIGH)`/`ApprovalReceived`/`GuardrailTriggered`/`VerificationFailed` — the 57.93 precedent). *Confirmed.*

### Prong 3 (schema) — N/A
No DB/migration/ORM change (the durable `verification_escalated` bool rides the existing `state_snapshots` JSONB checkpoint metadata, the 57.98 precedent); no new event type (`check_event_schema_sync` unaffected); no new DTO (the reviewer note rides `ApprovalDecision.reason`). Confirmed no new table/column/event/DTO.

### Design-note decision
A2 = **feature-continuation** (the 4th pause leg — input/between-turns/output/verification — built from the same 57.91-93 primitive + the A1 gate) → **NO new design note** (`sprint-workflow.md §Step 5.5`, the 57.91-93/95/96 precedent). Record = CHANGE-066 + **update `25-verification-in-loop-design.md` §4** (A2 Open Invariant → SHIPPED) + 17.md (new resume kind).

### Strict-judge drive-through setup
Forcing a real verification fail for the Day-3 drive-through needs a strict judge template / a deliberately-hard prompt (the 57.98 carryover `strict-judge drive-through template`; a real gpt-5.2 answer passes the default `output_quality` judge first try). Day-3 approach: set a strict judge template (or a prompt the judge will reject) + `CHAT_VERIFICATION_ESCALATE_ON_MAX=true` on the drive-through backend; the cheap deployment (57.97) is set. If a real fail can't be forced cleanly, the escalate/approve/reject MECHANISM is unit-proven + the drive-through drives the toggle + the pause UI with a clearly-labelled forced-fail fixture.

### Drift findings (Day 0)
- **D-DAY0-1** — the swap point `:2344-2346` + the resume `if/elif` chain `:2856/2884/2915` are exactly as the plan assumed → A2 is a clean conditional-insert + additive `elif` (NO loop restructure). *Scope confirmed minimal.*
- **D-DAY0-2** — the config cluster `chat_verification_*` lives at `core/config/__init__.py:115-123` → the new toggle is a 1-line addition in the existing Settings class. *Confirmed straightforward.*
- (Day-1 will confirm D2 — the snapshot field set at the terminal — as `_cat10_verification_escalate_pause` is written.)

### Go/No-Go
**GO.** The recon + Day-0 grep confirm A2 is: a config toggle (1 line) + a new `_cat10_verification_escalate_pause` (mirror `_cat9_output_hitl_pause`) + a conditional at the FAIL==max terminal (`:2344`) + an additive `resume()` `elif kind == "verification":` + a durable `verification_escalated` bool (metadata, the 57.98 precedent). No new event/DB/DTO/migration/frontend. Scope shift vs plan ≈ 0%.

### Baseline (at branch creation)
- Branch `feature/sprint-57-99-verification-escalate` from `main` `be89d3ec` (A1 merged via PR #272)
- pytest collected = **2298** (`-m "not real_llm"`); `mypy src` = **0/353**; run_all 10/10 (to re-confirm at Day-0 commit)

---

## Day 1 — Config toggle + the escalate pause (US-1 / US-2) (2026-06-10)

Day-1 builds the run()-side of A2: the config toggle (US-1) + the escalate pause method
+ the conditional FAIL==max terminal + the durable `verification_escalated` flag (US-2).
The resume APPROVE/REJECT branches are Day-2. **Toggle defaults OFF → the A1 terminal is
byte-identical** (proven: 124 loop+verification+smoke tests green, zero regression).

### US-1 — the config toggle
- `core/config/__init__.py`: `chat_verification_escalate_on_max: bool = False` (env
  `CHAT_VERIFICATION_ESCALATE_ON_MAX`), in the `chat_verification_*` cluster after the
  judge template.
- `orchestrator_loop/loop.py` `__init__`: `verification_escalate_on_max: bool = False`
  (stored `self._verification_escalate_on_max`).
- `api/v1/chat/handler.py`: the main real_llm `AgentLoopImpl(...)` site reads
  `settings.chat_verification_escalate_on_max` + passes it into the ctor (after
  `verifier_registry=`). The echo-demo + child-loop sites are untouched (no registry →
  the escalate branch never runs there anyway).

### US-2 — the escalate pause + conditional terminal + durable flag
- NEW `_cat10_verification_escalate_pause()` (`loop.py`, mirrors `_cat9_output_hitl_pause`):
  builds a held-answer + verifier-reasons `response_snapshot` (the `_replay_approved_output`
  field set + `answer_text=parsed.text`), creates an `ApprovalRequest` (`kind="verification"`,
  `risk_level=HIGH`, the failed-verifier reasons in the payload), emits `ApprovalRequested(HIGH)`,
  builds `pending_approval{kind:"verification", response_snapshot}`, calls
  `_emit_deferred_pause(..., verification_escalated=True)`. Fail-closed paths (no-identity /
  persist-fail) fall back to the A1 `verification_failed` terminal (cannot offer a resumable
  pause).
- Conditional FAIL==max branch (the swap point): `if self._verification_escalate_on_max and
  not verification_escalated and self._hitl_manager and self._hitl_deferred and
  self._checkpointer and self._reducer:` → `_cat10_verification_escalate_pause(...)` → `return`;
  `else:` → the A1 `verification_failed` terminal (byte-identical). The snapshot is built from
  `metrics_acc` + `parsed.text`.
- Durable `verification_escalated`: threaded `_run_turns` param (`verification_escalated: bool =
  False`) + `_emit_deferred_pause` param + `_emit_state_checkpoint` writes
  `metadata["verification_escalated"]=True` when True (mirrors the 57.98
  `verification_attempts` metadata pattern — no migration). `run()` defaults False (fresh run);
  resume() (Day-2) reads it back so a REJECT continuation re-enters with the flag set → a 2nd
  failure takes the A1 terminal (the bound: exactly one human-coached turn).

### Tests (Day-1 — in `test_loop_pause_resume.py`, see D-DAY1-1)
- `test_verify_escalate_off_preserves_a1_terminal` — toggle OFF + 3 failing answers (max=2) →
  `verification_failed` terminal, NO `ApprovalRequested`, even WITH the full HITL wiring present
  (the toggle, not the wiring, gates it).
- `test_verify_escalate_on_max_pauses_for_human` — toggle ON + max-fail → `ApprovalRequested(HIGH)`
  + `LoopCompleted(awaiting_approval)` + a checkpoint carrying `pending_approval{kind:"verification",
  response_snapshot.answer_text="c is the held failed answer"}` + `metadata.verification_escalated
  is True`; NO `verification_failed` terminal.

### Gate
- mypy `src` **0/353**; `black`/`isort`/`flake8` (changed src + test) clean (2 E501 MHist trims —
  the 57.98 lesson applied); the full `test_loop_pause_resume.py` = **28 passed** (26 prior + 2 new);
  loop + verification + smoke regression = **124 passed** (zero regression → toggle-OFF byte-identical).

### Day-1 drift
- **D-DAY1-1** — the A2 escalate tests live in `test_loop_pause_resume.py` (NOT a separate NEW
  `test_loop_verification_escalate.py`). That file already has the exact fixtures the escalate +
  Day-2 resume tests need (the HITL-wired loop builder + `_FailingVerifier`/`_PassingVerifier` +
  `_vregistry` + `InMemoryCheckpointer`/`InMemoryReducer` + `SpyHITLManager` + the output-pause
  template). A new file would DUPLICATE all of it. The plan §4 explicitly allowed "if they fit the
  existing pause-resume fixtures" → they do. *Plan's "NEW file" preference superseded; no new file.*
- **D-DAY1-2** — `.env.example` (repo root) has NO `CHAT_VERIFICATION_*` entries (the sibling
  `chat_verification_mode` / `_judge_template` settings are documented only by their `Settings`
  defaults, not in `.env.example`). Adding a lone `CHAT_VERIFICATION_ESCALATE_ON_MAX` would be
  inconsistent. → skip the `.env.example` edit (match the existing convention; the `Settings`
  default False documents it). *Plan's `.env.example` item dropped per repo convention.*
- **D-DAY1-3** — `RiskLevel.HIGH.value` serializes as `"HIGH"` (uppercase), not `"high"` — caught
  by the escalate test assertion; fixed to the literal `"HIGH"`.

### Remaining (Day-2+)
- US-3 resume APPROVE → deliver the held failed answer (replay, not re-verified).
- US-4 resume REJECT-with-note → re-inject the note + one bounded human-coached turn → 2nd fail
  terminates (`verification_escalated` read back on resume).
- US-5 durable-flag-survives-resume test + no-new-event confirm.
- US-6 drive-through (strict-judge fail → escalate → approve + reject-coach).
- CHANGE-066 + 25.md §4 + 17.md (Day-3).

---

## Day 2 — Resume APPROVE / REJECT-with-note + the durable bound (US-3/US-4/US-5)

### What shipped
The `resume()` `kind` dispatch gained `elif kind == "verification":` (between the 57.93
`output` branch and the 57.88 `tool` `else`) — the run()-side escalate pause (Day-1) now has its
resume counterpart. Two human outcomes:

- **APPROVE (US-3)** — the human OVERRIDES the verifier. resume DELIVERS the held failed answer
  verbatim via the existing 57.93 `_replay_approved_output` (TERMINAL, no LLM re-call, NOT
  re-verified). The escalate-pause snapshot set the same `answer_text`/provider/model/token fields
  the output-pause replay reads, so the replay path is reused as-is — `return` before the shared
  `_run_turns` drive.
- **REJECT-with-note (US-4)** — re-inject `Message(role="user", "[Verification rejected by
  reviewer: {reason}. Please revise the answer.]")` and fall through to the shared `_run_turns`
  drive for EXACTLY ONE human-coached turn. The bound: `verification_attempts` is forced to
  `self._max_correction_attempts` + `verification_escalated=True`, so if the coached answer fails
  the gate AGAIN the swap-point guard `not verification_escalated` is False → the A1
  `verification_failed` terminal fires (no second pause).

### Durable flag (US-5)
- `resume()` rehydrates `verification_escalated = bool(metadata.get("verification_escalated",
  False))` at the top (mirrors the 57.98 `verification_attempts` read — rides metadata, no
  migration) and threads it into the shared `_run_turns` call. Absent on every other pause kind +
  on a fresh run() → False → byte-identical to A1.
- **No new event** — A2 reuses `ApprovalRequested`/`ApprovalReceived`/`GuardrailTriggered`/
  `LLMResponded`/`LoopCompleted`; `check_event_schema_sync` green WITH no new event class.

### Files (3)
- `src/agent_harness/orchestrator_loop/loop.py` — `resume()`: top-read of the durable flag + the
  `elif kind == "verification":` branch + `verification_escalated=` threaded into `_run_turns` +
  docstring kind-enumeration update + MHist 1-line.
- `tests/.../test_loop_pause_resume.py` — `_paused_state_verified` gains a `kind="verification"`
  branch (sets the durable flag); `_CapturingChatClient` (records `request.messages` to assert the
  note injection); 3 new resume tests.
- `docs/.../sprint-57-99-checklist.md` — Day-2 (2.1/2.2/2.3) + the §3.1 resume test items marked.

### Tests (3 new resume cases)
- `test_verify_escalate_resume_approve_delivers_held_answer` — APPROVE → held answer delivered,
  NO `VerificationPassed`/`Failed` (not re-verified), END_TURN, no `ApprovalRequested`.
- `test_verify_escalate_resume_reject_coaches_one_turn` — REJECT + PASSING coached turn → the note
  reaches `chat.seen_messages`, the revised answer is delivered + verified, END_TURN, no 2nd pause.
- `test_verify_escalate_reject_then_fail_binds_to_a1_terminal` — REJECT + FAILING coached turn (at
  attempt==max) → `verification_failed` terminal, NO 2nd `ApprovalRequested`, no new pause
  checkpoint (the durable flag is the bound, even with the toggle still ON).

### Gate
- mypy `src` **0/353** (gate authority; the test file's pre-existing line-154 `_dummy`
  `# type: ignore[unreachable]` flags only in a partial 2-file mypy run — it is outside the
  `mypy src` gate scope and is not my code).
- `black`/`isort`/`flake8` (changed src + test, FULL scope) clean.
- `test_loop_pause_resume.py` **31 passed** (28 prior + 3 new); loop + verification regression
  **126 passed**; `test_chat_verification_smoke.py` + cost-ledger **3 passed**. pytest collect
  **2303** (Day-0 baseline 2298 + 5 = 2 Day-1 escalate + 3 Day-2 resume; zero deletion).
- `run_all.py` **10/10** — AP-1 green (the escalate is a conditional `return` in the while-driven
  `_run_turns`; the reject continuation drives `_run_turns`), `check_event_schema_sync` green (no
  new event), LLM SDK leak 0.

### Day-2 drift
- **D-DAY2-1** — the REJECT branch sets BOTH `verification_attempts = self._max_correction_attempts`
  AND `verification_escalated = True` explicitly, even though the top metadata-read already supplies
  both (the escalate pause persisted attempts==max + the flag). Kept the explicit set: it makes the
  one-coached-turn bound airtight regardless of the persisted values (defensive + matches the
  documented decision), at the cost of one redundant line. The metadata top-read remains THE durable
  mechanism US-5 tests.

### Remaining (Day-3)
- US-6 drive-through (real UI + real backend + a strict judge: fail → escalate → APPROVE renders
  the held answer; a fresh fail → REJECT-with-note → one coached turn). Risk Class E clean restart;
  set `CHAT_VERIFICATION_ESCALATE_ON_MAX=true` + the strict judge for the drive-through backend.
- Full backend pytest sweep (NET delta documented).
- CHANGE-066 + `25-verification-in-loop-design.md` §4 (A2 Open Invariant → SHIPPED) + 17.md.

---
