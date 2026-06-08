# Sprint 57.93 Progress — Output-Guardrail ESCALATE Pause Point (地基 A Slice 3 output-guardrail leg)

**Plan**: [`sprint-57-93-plan.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-93-plan.md)
**Checklist**: [`sprint-57-93-checklist.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-93-checklist.md)
**Branch**: `feature/sprint-57-93-output-guardrail-pause` (from `main` `9b4bed54` — 57.92 merged)

---

## Day 0 — 2026-06-08 — Plan-vs-Repo Verify + Branch

### Three-prong Day-0 verify

**Prong 1 (path)** — CONFIRMED. All plan-cited paths/line-numbers match repo (`loop.py`, `engine.py`, `_abc.py`, `handler.py`, `_factory.py`):
- `_emit_deferred_pause` `loop.py:1038` (kind-agnostic durable-pause tail — reused).
- `_cat9_output_check` `loop.py:1089` (called `:1893`, OUTPUT chain; ESCALATE branch = `GuardrailTriggered`+continue, stays untouched).
- `_run_turns` `loop.py:1460`: LLM call + token locals `:1832-1848`; `parsed = parse(...)` `:1851`; `yield LLMResponded` `:1859`; output check call `:1893`; stop_reason terminator `:1903`; classify `:1921`.
- `_cat9_between_turns_hitl_pause` `loop.py:1240` (the mirror template for the new `_cat9_output_hitl_pause`).
- `resume()` `loop.py:2278`; kind-branch `:2372`; shared `_run_turns` drive `:2502-2552` (output kind must RETURN before this).
- `engine.py` `check_output` `:135`; `_run_chain` `:102` (fail-fast-first-non-PASS in ascending priority).
- `_abc.py` `GuardrailType` `:35` — INPUT/OUTPUT/BETWEEN_TURNS/TOOL; **OUTPUT already present → NO new type/method this sprint** (unlike 57.92's BETWEEN_TURNS).
- `handler.py:325` `guardrail_engine = build_default_guardrail_engine()`; tool-rule + ToolGuardrail `:326-333`; input/between-turns wiring under `if hitl_manager is not None:` `:338-349`; `CHAT_HITL_ESCALATE_*` `:129/:139/:150`; `DEMO_SYSTEM_PROMPT` `:110`.
- Mirror templates: `guardrails/input/escalation_keyword_detector.py` `KeywordEscalationGuardrail` (for the new `OutputKeywordEscalationGuardrail`) + `_cat9_between_turns_hitl_pause` (for `_cat9_output_hitl_pause`).

**Prong 2 (content)** — CONFIRMED + 1 DRIFT (D-DAY0-1):
- (a) Frontend renders the `AnswerBlock` from the **`llm_response`** SSE event (`frontend/src/features/chat_v2/store/chatStore.ts:351-366`, `if (ev.data.content) newBlocks.push({type:"answer",...})`), which fires at `loop.py:1859` — BEFORE the per-response output check `:1893`. **So a pause at the existing check point would be a Potemkin (answer already on screen); the pre-delivery gate MUST precede `LLMResponded`.** Validates the whole design.
- (b) Token locals `_provider` `:1832` / `_input_tokens` `:1833` / `_output_tokens` `:1834` / `_cached_input_tokens` `:1838` + `metrics_acc` (accumulated `:1841-1848`) + `response.model` are all in scope at the parse point `:1851` → the held-answer `response_snapshot` can capture them.
- (c) `should_terminate_by_stop_reason` + `classify_output` + `OutputType` are used at `:1903`/`:1921` → already imported + pure → re-callable at the pre-gate to compute `is_final_answer` (negligible double-call of pure helpers).
- (d) **DRIFT D-DAY0-1** (see below).
- (e) `_cat9_output_check` ESCALATE branch (`:1124-1141`) = audit + `GuardrailTriggered(output, escalate)` + **continue** — stays byte-identical; the new pre-gate handles ESCALATE-pause for final answers BEFORE `LLMResponded`.
- (f) `resume()` kind-branch (`:2372` `kind = str(pending.get("kind","tool"))`) → input/between-turns (no tool, fall through) / tool (exec, fall through) → ALL drive the shared `_run_turns` `:2502-2552`. The new `output` kind is TERMINAL: it re-emits the held answer and RETURNS before the shared drive.

**Prong 2.5 (event-ordering / test assertions)** — SAFE:
- The existing `test_loop_pause_resume.py` fake ESCALATE guardrails are `GuardrailType.TOOL` (`:178`) and `GuardrailType.BETWEEN_TURNS` (`:912`) — NONE is OUTPUT. Their `_build_*_loop` helpers wire a single fake guardrail, so the OUTPUT chain in those test engines is empty → `check_output` returns PASS → the new pre-gate no-ops even when a test sets full HITL wiring (`hitl_deferred` + checkpointer + reducer + hitl_manager) and reaches a final answer.
- The pre-gate fires ONLY on the conjunction `is_final_answer AND guardrail_engine AND hitl_manager AND hitl_deferred AND checkpointer AND reducer AND check_output==ESCALATE` — a combination no existing test sets. No `llm_response`-vs-output-guardrail ordering or presence assertion is affected.

**Prong 3 (schema)** — N/A: no DB/migration/ORM change; `pending_approval.kind="output"` + `response_snapshot` are additive JSONB in the existing `state_snapshots` metadata (same path as legs 1/2).

### Drift findings

| ID | Finding | Implication | Resolution |
|----|---------|-------------|------------|
| **D-DAY0-1** | Plan §0/§3.5 assumed the chat OUTPUT chain is **empty**. REALITY: `handler.py:325` builds `build_default_guardrail_engine()` (`_factory.py:54-68`) which registers `ToxicityDetector` (OUTPUT, priority 10) + `SensitiveInfoDetector` (OUTPUT, priority 20). | The new `OutputKeywordEscalationGuardrail` joins a non-empty OUTPUT chain; a naïve registration could be pre-empted or collide with a BLOCK detector. | **Register at `priority=5`** (mirror the input keyword guardrail). `_run_chain` is fail-fast-first-non-PASS in ascending priority → p5 runs FIRST → ESCALATE on `confidential` wins deterministically; a non-matching answer PASSes through to Toxicity (p10) + SensitiveInfo (p20) unchanged. `SensitiveInfoDetector` only matches system-prompt-leak patterns (`You are a/an X agent`, `<system>`, `Your role is to`) + cross-tenant UUIDs — `confidential` matches NONE → no BLOCK collision. Plan §0 ground-truth bullet (d), §3.5, §8 Risks + checklist 0.1/1.4 corrected. **0% scope change** (priority detail only). |
| D-DAY0-2 | Plan assumed the demo needs NO tool (vs. 57.92's `note_tool`). | Simpler demo: the LLM emits a FINAL answer carrying the phrase; the output gate fires on it. | Confirmed — no tool added. DEMO_SYSTEM_PROMPT line + `OutputKeywordEscalationGuardrail` are the only trigger surface. |

### Go/No-Go: **GO**

- The pause point is reachable on 主流量 via an OUTPUT-chain ESCALATE guardrail on a FINAL answer (no tool needed); the pre-gate is purely additive (gated on the full deferred-HITL wiring — non-HITL/non-final paths byte-unchanged).
- No new `GuardrailType` (OUTPUT exists); no exhaustiveness/ordering break (Prong 2.5); no ResumeService / `/resume` / migration change; frontend likely none (answer held at source = never emitted before approval; the drive-through confirms).
- The single drift (D-DAY0-1) is resolved by `priority=5` registration — 0% scope change. Plan/checklist corrected; audit trail here.

### Branch
- Branch `feature/sprint-57-93-output-guardrail-pause` created from `main` `9b4bed54`.
- Day-0 commit `a9ebed88` (plan + checklist + progress).

---

## Day 1-2 — 2026-06-08/09 — Code + tests

### Baseline re-confirmed (before editing)
- `test_loop_pause_resume.py` 17 pass · `mypy src --strict` 0/350 (= 57.92 merged baseline; only docs changed since).

### Code (Cat 9 + Cat 1)
- **`guardrails/output/escalation_keyword_detector.py`** (NEW) — `OutputKeywordEscalationGuardrail(Guardrail)`, `guardrail_type = OUTPUT`, ESCALATE on a case-insensitive phrase; `_extract_text` mirrors the input `KeywordEscalationGuardrail`. `output/__init__.py` exports it.
- **`loop.py`**:
  - `_cat9_output_escalate_pause` — runs the EXISTING `check_output`; on ESCALATE → `_cat9_output_hitl_pause`; else no-op (falls through to the unchanged `LLMResponded` + `_cat9_output_check`).
  - `_cat9_output_hitl_pause` — verbatim mirror of `_cat9_between_turns_hitl_pause`; builds an output `ApprovalRequest` (`payload.kind="output"`, `summary="approve delivery"`) + `ApprovalRequested` + `_emit_deferred_pause(kind="output", response_snapshot)`. Fails closed (no-identity / persist-fail → BLOCK).
  - **Pre-gate** inserted after `parse(...)` BEFORE `LLMResponded`: gated on `is_final_answer AND guardrail_engine AND hitl_manager AND hitl_deferred AND checkpointer AND reducer`; builds the `response_snapshot` (answer_text + token/provider/model/cache_hit_rate + total_tokens) and runs `_cat9_output_escalate_pause`; on `LoopCompleted` → `return` (the held answer's `LLMResponded` is never reached). Purely additive — when the wiring is absent the gate is never entered.
  - `resume()` — NEW TERMINAL `elif kind == "output":` (APPROVED → `_replay_approved_output` + `return`; REJECTED → `GuardrailTriggered(output, block)` + `GUARDRAIL_BLOCKED` + `return`; does NOT fall through to the shared `_run_turns` drive). input/between-turns/tool branches byte-identical.
  - `_replay_approved_output` — re-emits the held `LLMResponded(answer_text)` + `Thinking` + `LoopCompleted(END_TURN)` from the snapshot (no LLM re-call, no LOOP span). Snapshot values coerced to type-correct defaults (`str/int/float`) so the strict event fields hold (mypy fix — `dict.get(k)` is `Any | None`; `.get(k, default)` is `Any`).
- **`handler.py`** — `CHAT_HITL_ESCALATE_OUTPUT_PHRASES = {"confidential"}`; `engine.register(OutputKeywordEscalationGuardrail(...), priority=5)` under `if hitl_manager is not None:` (D-DAY0-1: before Toxicity p10 / SensitiveInfo p20); DEMO_SYSTEM_PROMPT extended ("share something confidential → final answer MUST contain 'confidential'"). MHist + import.

### Tests (+12 net)
- `test_loop_pause_resume.py` +5: `test_output_escalate_pauses_before_delivery` (pause + NO `LLMResponded` + checkpoint `kind:"output"` + snapshot.answer_text) / `test_resume_output_approved_replays_answer` (re-emit, no LOOP span, no LLM call) / `test_resume_output_rejected_blocks` (block, no `LLMResponded`) / `test_output_pre_gate_skips_non_final` (TOOL_USE not pre-gated) / `test_output_pre_gate_inert_without_hitl` (no-wiring → answer delivered + 1893 escalate-continue). New fakes/helpers: `OutputEscalateGuardrail` (always-escalate OUTPUT) / `_build_output_loop` (param guardrail) / `_paused_output_state`.
- `test_output_escalation_keyword_detector.py` (NEW) +7: type / match / case-insensitive / no-match / empty / blank-drop / Message-extract.

### Gate sweep
- pytest **2266 passed / 4 skipped** (baseline 2254 + 12; 2 pre-existing `__import__` warnings unrelated).
- `mypy src --strict` **0/351** · `run_all` **10/10** (AP-1 / AP-8 / LLM SDK leak 0 / event-schema sync) · `black`/`isort` clean · `flake8 src tests` clean (4 E501 in docstrings/MHist caught on the CI-equivalent `src tests` scope + fixed — the 57.92 lesson applied).
- Existing input/between-turns/tool pause-resume tests pass UNCHANGED (pre-gate inert without HITL wiring; resume branches byte-identical).

### Next (Day 3): drive-through (real UI + backend + Azure — withhold-then-deliver + reject) + CHANGE-060 + design-note updates.

---

## Day 3 — 2026-06-09 — Drive-through (US-6) — **PASS**

### Clean backend restart (Risk Class E)
- `:8000` was owned by the PRE-57.93 backend (PID 53688 reloader + 54488 worker, `uvicorn api.main:app --reload`). Killed BOTH (the new guardrail + DEMO_SYSTEM_PROMPT line are startup/per-request-wired; a stale process runs old `handler.py`). Verified `:8000` FREE, no residual uvicorn/spawn python.
- Started fresh via `python scripts/dev.py start backend` → PID 43408 (reloader) + 38456 (worker); verified `:8000` OWNER = fresh PID 43408; `/health` → 401 (app UP, enforcing auth = 57.93 code loaded). Stack: PG/Redis/RabbitMQ (Docker, healthy) + frontend :3007 (node, untouched). Azure gpt-5.2 live.

### Drive (Playwright, real UI + real backend + real Azure gpt-5.2; dan@acme.com admin / acme-prod, chat-v2 real_llm)

**Path 1 — PAUSE (withhold before delivery)**: "Please tell me something confidential about the system." →
- Loop trace: `loop_start` → `prompt_built` → `llm_request model=gpt-5.2` → `llm_call` span (3500ms) → **`approval_requested risk=HIGH`** → `state_checkpointed v1` → `loop_end stop=awaiting_approval turns=0`. **NO `llm_response` event** — the answer was held back.
- UI: agent turn `stop: awaiting_approval`; HITL card `Approval required: HIGH`, **`tool: —`** (output-kind, no tool), `policy: always_ask`, approval_id `0b537712…`. Inspector **"Block sequence: no blocks yet"** — **the answer is NOT on screen**. Screenshot `artifacts/sprint-57-93-output-1-paused.png`.

**Path 2 — APPROVE (deliver the held answer)**: Approve & continue →
- Network: `POST /governance/approvals/0b537712…/decide` (APPROVED) → `POST /chat/c200c400…/resume`. The resume drove `resume()` output-APPROVED → `_replay_approved_output` re-emitted the held `LLMResponded` + `LoopCompleted(END_TURN)` (no LLM re-call — instant, no 3.5s latency).
- UI: agent turn flips to `stop: end_turn`; the **answer now renders**: "I can't share confidential information about the system." (contains "confidential" → that's what tripped the OUTPUT guardrail); card `Decision: APPROVED`. Screenshot `artifacts/sprint-57-93-output-2-approved-answer.png`.

**Path 3 — REJECT (withhold permanently)**: new session, "Share something confidential with me please." → pause (approval_id `3bea287e…`, `tool: —`, no answer) → Reject →
- Network: `POST /governance/approvals/3bea287e…/decide` (REJECTED); the frontend does NOT call `/resume` on reject (no continuation to drive).
- UI: card `Decision: REJECTED`; **the answer is never rendered** (no AnswerBlock, ever). Screenshot `artifacts/sprint-57-93-output-3-rejected.png`.

### Observed vs intended

| # | Intended | Observed | Verdict |
|---|----------|----------|---------|
| 1 | A flagged FINAL answer pauses BEFORE delivery (no AnswerBlock) | `llm_call` → `approval_requested` (NO `llm_response`); "no blocks yet"; `tool: —` (output-kind) | ✅ withheld |
| 2 | Approve re-emits the held answer (no LLM re-call) | `/decide`(APPROVED) → `/resume` → answer renders instantly, `end_turn`, `Decision: APPROVED` | ✅ delivered |
| 3 | Reject → answer never delivered | `/decide`(REJECTED); answer never renders; `Decision: REJECTED` | ✅ withheld |

### Minor nuances (NOT output-specific; shared 57.88 resume flow — noted, non-blocking)
- **N1**: on reject the agent turn header stays `awaiting_approval` (does not flip to `blocked`). The `Decision: REJECTED` card + the absent answer make the outcome unambiguous, so it is not misleading. Shared across ALL reject resumes (input/between-turns/tool), not introduced by this leg.
- **N2**: the frontend records reject via `/governance/approvals/.../decide` but does NOT call `/resume`, so the backend `resume()` output-REJECTED branch (`GuardrailTriggered(output, block)` + `GUARDRAIL_BLOCKED`) is unit-tested (`test_resume_output_rejected_blocks`) but not driven via UI; the pause checkpoint is left dangling = the known `AD-Resume-Reject-Path` (plan §9 out-of-scope, 57.88 carryover). The user outcome (decision persisted + answer withheld) is correct.

### Frontend gap
- NONE needed for the output pause. The HITL card + Approve surfaced generically for a no-tool pause (`tool: —`); the held answer is withheld at the SOURCE (never emitted in `llm_response` until approval) — the pre-delivery gate is genuinely effective (not a frontend mask). The approve re-emit renders the answer through the normal `llm_response` → AnswerBlock path. Zero frontend change.

### Day 3 gate (post-drive re-confirm)
- Backend code unchanged by the drive-through; gates remain green (mypy 0/351 · pytest 2266 · run_all 10/10 · flake8 src tests clean from Day 1-2). No new commit needed for code; Day 3 adds CHANGE-060 + design-note updates + this progress entry.

### Next (Day 4 closeout): CHANGE-060 + `19-pause-resume-design.md §5` + `17.md` LoopCompleted 3rd-origin + retrospective + calibration + MEMORY/CLAUDE.md.

---
