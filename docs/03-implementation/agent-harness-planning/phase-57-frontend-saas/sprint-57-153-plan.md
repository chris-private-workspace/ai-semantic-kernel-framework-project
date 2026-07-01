# Sprint 57.153 Plan — make the in-loop verification judge memory-aware

**Summary**: The in-loop Cat 10 verification judge (57.98 A1 + 57.111 A3) sees `{output}` + a `{trace}` block built ONLY from the conversation accumulator `messages`, which never contains the `profile()`/`recent_sessions()`-injected memory (it lives in the per-turn PromptBuilder artifact = the system prompt, and `build_trace_block` drops all system-role messages anyway). So when the agent correctly recalls a fact grounded in injected memory — especially a 0-keyword-overlap recall like "你是誰" → "你是 Chris" — the judge has no visible evidence for the claim and false-positive-REJECTs it as unsupported/off-topic, triggering a coached retry that produces a no-recall answer (observed at Sprint 57.149 + 57.152 Leg-2). This sprint closes `AD-Verification-Judge-Memory-Inject-Blind` by making the judge memory-aware — the exact parallel of 57.111 A3 (which added `{trace}`): a new `TransientState.injected_memory` field + a `build_memory_block` helper + a `{memory}` judge-template placeholder + an instruction that a statement consistent with injected memory is GROUNDED (not fabrication), threaded loop → gate, gated by a new default-ON env lever. An evidence-first real-Azure A/B harness (`benchmark_memory_grounded_judge.py`, mirrors `benchmark_correction_hygiene.py`) measures that memory-grounding lowers the grounded-recall false-positive-reject rate WITHOUT degrading genuine-fabrication catch — the verdict that justifies default-ON. **Drive-through MANDATORY** (user-facing recall path). **Design note required** (spike sprint → note 56).

**Status**: Approved-to-execute (user picked direction 2 — `AD-Verification-Judge-Memory-Inject-Blind` — from the Sprint 57.152 closeout candidate list, 2026-07-01)
**Branch**: `feature/sprint-57-153-verification-memory-grounding`
**Base**: `main` HEAD `5bbf1a77` (chore flip Sprint 57.152 PR-pending → MERGED, #359)
**Slice**: standalone memory×verification cross-category fix (closes `AD-Verification-Judge-Memory-Inject-Blind`, logged 57.149 carryover, re-confirmed 57.152 Leg-2)
**Scope decisions**: (a) thread injected memory via a NEW `TransientState.injected_memory` field (NOT a `Verifier.verify` ABC kwarg — the gate already builds a throwaway `trace_state`; a field touches 0 verifier impls + 0 test stubs vs ~13 for an ABC kwarg, and "what memory was injected this turn" is a legitimate transient fact); (b) new `{memory}` judge-template placeholder + `build_memory_block` helper = the direct parallel of the 57.111 A3 `{trace}` mechanism; (c) source the memory from the per-turn `artifact.layer_metadata["memory_accesses"]` the loop ALREADY iterates (no extra search); (d) env lever `chat_verification_memory_grounding` default ON (this is a confirmed broken-UX fix, not a "might-help" — the A/B harness CONFIRMS no fabrication-catch regression; flip to opt-in only if it regresses); (e) backend-only, NO migration / wire / frontend / loop-loop-structure change.

---

## 0. Background

### The gap (`AD-Verification-Judge-Memory-Inject-Blind`)

- The in-loop Cat 10 judge (57.98 A1) verifies the FINAL candidate answer; 57.111 A3 made it trace-aware by passing `state` and rendering a `{trace}` block.
- But the judge's `{trace}` is built from the loop's `messages` accumulator (user/assistant/tool turns). The memory injected by `DefaultPromptBuilder.build()` (the 57.148 `profile()` user facts + 57.151 `recent_sessions()` summaries) is rendered into the per-turn **artifact** (the system prompt), assigned to `chat_messages` for the LLM call — and **never merged back into `messages`**.
- Even if it were, `build_trace_block` explicitly **drops every system-role message**.
- Net: the judge sees the recall answer + the recent conversation turns, but **never the memory the agent was grounded in**.

### Why it matters (the missing capability)

A grounded recall with no keyword overlap with the visible trace (the canonical "你知道我是誰?" → "你是 Chris" case) reads to the judge as an unsupported / off-topic claim → false-positive REJECT → the in-loop correction turn coaches "that wasn't supported" → the retry produces a **no-recall** answer. This silently defeats the entire 57.148→152 memory-formation arc on the verification path: the memory IS injected and the agent DOES recall, but the judge erases it. Observed live at Sprint 57.149 + 57.152 Leg-2.

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `5bbf1a77`) | Anchor |
|-------|-------------------------------------|--------|
| Memory injection | `profile()`+`recent_sessions()` rendered INTO the per-turn artifact → `chat_messages = list(artifact.messages)`; the loop's `messages` accumulator is NOT updated with it | `loop.py:2377` |
| Memory source | the injected hints ARE surfaced as `artifact.layer_metadata["memory_accesses"]` (scope/key/summary/time_scale) — the loop already iterates them for the Inspector Memory tab | `loop.py:2406` |
| Verify trace_state | built from `messages` (no injected memory) | `loop.py:1737` |
| Trace block | drops ALL system-role messages | `_trace.py:107` |
| Judge prompt | substitutes `{output}` + `{trace}` only — no memory placeholder | `llm_judge.py:139` / `output_quality.txt:16` |

→ The fix must give the judge the per-turn injected-memory content as legitimate grounding evidence, framed so a recall consistent with it is NOT flagged as fabrication.

### The design (backend-only: 1 state field + 1 block helper + 1 judge placeholder + 2 template edits + loop thread + env lever + A/B harness)

```
# Cat 7 contract  (state.py)
TransientState += injected_memory: str | None = None        # additive, default None → all existing constructions byte-identical

# Cat 10 helper   (_trace.py — sibling to build_trace_block)
build_memory_block(accesses: list[dict], *, char_budget) -> str   # render scope/summary lines; "" when empty → no-op like {trace}

# Cat 10 judge    (llm_judge.py)
_build_prompt(): ... .replace("{memory}", (state.transient.injected_memory or "") if state else "")

# Cat 10 templates (output_quality.txt + key_condition.txt)
+ "RETRIEVED MEMORY (facts injected into the agent's context from the user's durable memory; MAY BE EMPTY):
   --- {memory} --- A statement consistent with the retrieved memory above is GROUNDED — do NOT flag it as
   fabricated / unsupported / off-topic on the ground that the trace doesn't mention it."

# Cat 1 loop      (loop.py)
turn_injected_memory = artifact.layer_metadata.get("memory_accesses", [])   # captured at the build branch (~2406)
verdict = await self._cat10_verify_gate(..., injected_memory=(build_memory_block(turn_injected_memory)
                                                              if self._verification_memory_grounding else ""))
# _cat10_verify_gate sets trace_state.transient.injected_memory = injected_memory

# config + handler
chat_verification_memory_grounding: bool = True   (env CHAT_VERIFICATION_MEMORY_GROUNDING)
loop ctor kwarg verification_memory_grounding: bool = True   ← set from settings (mirrors 57.136 correction_context_strategy)

# evidence-first
scripts/benchmark_memory_grounded_judge.py + fixtures/verification/memory_grounded_judge_cases.yaml + CI test
```

Why this design over an ABC kwarg: `Verifier.verify(*, output, state, trace_context)` is a 17.md §2.1 contract; adding `injected_memory` there would touch the ABC + RulesBasedVerifier + LLMJudgeVerifier + ~13 test stubs that override `verify`. The gate already constructs a fresh throwaway `trace_state` (it is NOT the persisted loop state, so setting a field on it does not violate the Reducer-only-mutator rule), so carrying the memory on `TransientState` — exactly where `messages` (the other judge input) already lives — touches 0 verifier impls and 0 test stubs.

### Ground truth (recon head-start — code read on `main` HEAD `5bbf1a77`; ALL re-verified §checklist 0.1)

- `loop.py:1737` — `_cat10_verify_gate` builds `trace_state = LoopState(transient=TransientState(messages=list(messages), current_turn=turn_count), ...)`.
- `loop.py:2406` — `for _acc in artifact.layer_metadata.get("memory_accesses", []):` already iterated (MemoryAccessed emit); `_acc` has `scope`/`key`/`summary`/`time_scale`.
- `loop.py:2645` — the `_cat10_verify_gate(...)` call site (same turn iteration, after the build branch → a local captured at ~2406 is visible here).
- `loop.py:396,467` — `correction_context_strategy: str = "keep"` ctor kwarg precedent (57.136) for the new `verification_memory_grounding` kwarg.
- `_trace.py:82` — `build_trace_block(messages, *, max_messages, char_budget)` sibling shape for `build_memory_block`.
- `llm_judge.py:139` — `return template_text.replace("{output}", output).replace("{trace}", trace_block)`.
- `_category_factories.py:499` — `make_chat_verifier_registry` registers the `LLMJudgeVerifier(judge_template=...)`; no change needed (the verifier reads memory from `state`).
- `config/__init__.py:153` — `chat_verification_correction_strategy` env-lever precedent block.

**Baselines (57.152 closeout)**: pytest 3053 · wire 26 · Vitest 922 · mockup 51 · mypy 0/397 · run_all 11/11. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-memory-accesses-shape** — grep `loop.py` ~2406 + the PromptBuilder to confirm `memory_accesses` entries have `scope`+`summary` keys (the block fields) and that summaries are PII-capped → implication: `build_memory_block` field selection.
- **D-trace-state-fresh** — confirm `_cat10_verify_gate`'s `trace_state` is a throwaway (not the persisted loop state) so setting `injected_memory` on it doesn't need the Reducer → implication: §Scope decision (a) holds.
- **D-loop-ctor-kwarg** — confirm the loop ctor + the handler loop-construction site take new kwargs the way 57.136 `correction_context_strategy` did → implication: §3.3 wiring path.
- **D-judge-template-only-2** — confirm `output_quality.txt` + `key_condition.txt` are the only chat-path judge templates with `{trace}` (others are Cat 9 detector fallbacks) → implication: 2 template edits, `{memory}` `.replace` is a harmless no-op on the rest.
- **D-ap8-harness** — confirm `scripts/` is outside the `check_promptbuilder_usage` lint root (so the harness needs NO AP-8 allowlist, unlike 57.152 `formation.py` which is under `agent_harness/`).

## 1. Sprint Goal

Make the in-loop Cat 10 judge memory-aware so a recall grounded in injected memory is no longer false-positive-REJECTed. PROVEN by (1) the green gate set; (2) a real-Azure A/B harness verdict showing the grounded-recall false-positive-reject rate drops with memory-grounding ON while genuine-fabrication catch does not degrade; (3) the MANDATORY drive-through — a real chat-v2 new session asking a 0-keyword-overlap identity question recalls the prior-session fact and the in-loop judge PASSES it (no REJECT → no coached no-recall answer), vs the pre-fix REJECT. Produces CHANGE-120 + design note 56.

## 2. User Stories

- **US-1** (Cat 7 state): 作為 verification 範疇，我希望 `TransientState` 能攜帶「本輪注入的記憶」，以便 judge 能在不改 `Verifier.verify` ABC 的前提下讀到 grounding。
- **US-2** (Cat 10 judge): 作為 in-loop judge，我希望 prompt 有一個 `{memory}` grounding 區塊 + 「與注入記憶一致 = grounded」指示，以便不再把 grounded recall 誤判為 fabrication。
- **US-3** (Cat 1 loop wiring): 作為 orchestrator loop，我希望在 PromptBuilder build 時捕捉本輪 `memory_accesses` 並（經 default-ON env lever）注入 verify gate 的 `trace_state`，以便 judge 拿到真實 grounding。
- **US-4** (Cat 10 evidence): 作為 evidence-first 紀律，我希望一個 real-Azure A/B harness 量測 memory-grounding 降低 grounded-recall 假陽性 reject 且不降低真 fabrication 偵測率，以便佐證 default-ON。
- **US-5** (drive-through, MANDATORY): 作為使用者，我希望新 session 問 0-keyword 身分問題時，agent 的 grounded recall 被 in-loop judge 放行（不再被 coached 成 no-recall），以便記憶真的可用。
- **US-6** (closeout): 作為維護者，我希望 CHANGE-120 + design note 56 + calibration + navigators 完成，以便 `AD-Verification-Judge-Memory-Inject-Blind` 正式關閉。

## 3. Technical Specifications

### 3.0 Architecture (backend-only; NO migration / wire(26) / frontend / loop-structure change)

```
EDIT  agent_harness/_contracts/state.py          — TransientState += injected_memory: str | None = None
EDIT  agent_harness/verification/_trace.py        — NEW build_memory_block(accesses, *, char_budget)
EDIT  agent_harness/verification/llm_judge.py      — _build_prompt substitutes {memory} from state.transient.injected_memory
EDIT  agent_harness/verification/templates/output_quality.txt  — + RETRIEVED MEMORY {memory} section + grounding instruction
EDIT  agent_harness/verification/templates/key_condition.txt   — same {memory} section
EDIT  agent_harness/orchestrator_loop/loop.py      — capture memory_accesses @build; thread injected_memory→_cat10_verify_gate (flag-gated); set trace_state field; new ctor kwarg
EDIT  core/config/__init__.py                      — chat_verification_memory_grounding: bool = True (env CHAT_VERIFICATION_MEMORY_GROUNDING)
EDIT  api/v1/chat/handler.py                        — pass verification_memory_grounding=settings.* into the loop ctor
NEW   scripts/benchmark_memory_grounded_judge.py   — real-Azure A/B (with vs without {memory})
NEW   tests/fixtures/verification/memory_grounded_judge_cases.yaml — golden corpus (grounded + ungrounded cases)
NEW   tests/unit/scripts/test_benchmark_memory_grounded_judge.py    — CI-safe (MockChatClient + spy)
EDIT  tests/unit/agent_harness/verification/test_llm_judge.py (or sibling) — {memory} substitution
EDIT  tests/unit/agent_harness/verification/<trace test> — build_memory_block bounds/empty/render
EDIT  tests/unit/agent_harness/orchestrator_loop/test_loop_verification_gate.py — gate threads injected_memory to trace_state
UNTOUCHED  _abc.py / rules_based.py / registry.py — NO Verifier.verify ABC change (§Scope decision a)
UNTOUCHED  _category_factories.make_chat_verifier_registry — verifier reads memory from state, not ctor
```

### 3.1 Cat 7 state field (US-1) — `_contracts/state.py`

- Add `injected_memory: str | None = None` to `TransientState` (after `token_usage_so_far`). Additive default-None → every existing `TransientState(...)` construction is byte-identical. Update the class docstring Key Components line + 17.md §1.1 mention (additive note, no contract break).

### 3.2 Cat 10 judge + block (US-2) — `_trace.py` / `llm_judge.py` / templates

- `build_memory_block(accesses, *, char_budget=None)` in `_trace.py` (sibling to `build_trace_block`): render each access as `[memory:{scope}] {summary}` (one capped line), bounded by a char budget (env `CHAT_VERIFICATION_MEMORY_CHAR_BUDGET`, default reuse the trace budget constant family). Empty list / budget 0 → `""` (no-op, byte-identical to absent).
- `LLMJudgeVerifier._build_prompt`: add `.replace("{memory}", state.transient.injected_memory if state else "")` — guard `state is None` (Cat 9 fallback paths) and `injected_memory is None` → `""`. A template without `{memory}` is a byte-identical no-op (same property as `{trace}`).
- `output_quality.txt` + `key_condition.txt`: add a RETRIEVED MEMORY `{memory}` section + the instruction "A statement consistent with the retrieved memory above is GROUNDED — do NOT flag it as fabricated/unsupported/off-topic merely because the conversation trace doesn't mention it. (Still flag genuine contradictions of the memory.)". Keep "MAY BE EMPTY → judge normally" so the lever-OFF (empty) path reads cleanly.

### 3.3 Cat 1 loop wiring (US-3) — `loop.py`

- Initialize `turn_injected_memory: list[Any] = []` before the PromptBuilder branch; in the `for _acc in artifact.layer_metadata.get("memory_accesses", [])` region (~2406) capture `turn_injected_memory = list(artifact.layer_metadata.get("memory_accesses", []))` (the echo/naked-fallback path leaves it `[]`).
- At the `_cat10_verify_gate(...)` call (~2645) pass `injected_memory=(build_memory_block(turn_injected_memory) if self._verification_memory_grounding else "")`.
- `_cat10_verify_gate(*, ..., injected_memory: str = "")` sets `injected_memory=injected_memory` on the `TransientState(...)` it builds for `trace_state`.
- New loop ctor kwarg `verification_memory_grounding: bool = True` (store as `self._verification_memory_grounding`), mirroring `correction_context_strategy`. Default True keeps a non-handler caller (tests) memory-aware unless they opt out.

### 3.4 config + handler (US-3) — `core/config/__init__.py` / `api/v1/chat/handler.py`

- `chat_verification_memory_grounding: bool = True` with the env `CHAT_VERIFICATION_MEMORY_GROUNDING` + a docstring block mirroring `chat_verification_correction_strategy` (what it does, why default ON, how to revert).
- handler: at the loop-construction site (where `correction_context_strategy=`/`verifier_registry=` are passed) add `verification_memory_grounding=settings.chat_verification_memory_grounding`.

### 3.5 Evidence-first A/B harness (US-4) — `scripts/benchmark_memory_grounded_judge.py`

- Mirror `benchmark_correction_hygiene.py`: importable core (`load_cases` / `build_judge_prompt(case, grounded: bool)` / `run_arm` / `build_report` / `main`) + a golden YAML corpus. Each case: `{injected_memory: [facts], user_question, candidate_answer, expected: grounded_recall|genuine_fabrication}`.
- Two arms over the SAME corpus: **memory-aware** (judge gets the `{memory}` block) vs **bare** (empty `{memory}`, pre-fix). Metrics: `grounded_recall_false_reject_rate` (a grounded recall wrongly REJECTED — expect DOWN with memory) + `fabrication_catch_rate` (a genuine fabrication correctly REJECTED — expect NOT degraded). Verdict: memory-grounding KEEP-default-ON iff false-reject drops AND fabrication-catch does not regress materially (≥5pp threshold like the sibling).
- Real Azure on demand (`RUN_AZURE_INTEGRATION=1`), CI-safe MockChatClient + spy in the unit test.

### 3.x What is explicitly NOT done

- NOT changing the `Verifier.verify` ABC (§Scope decision a).
- NOT making memory grounding per-tenant (that is a C3-class config-tiering concern → carryover, mirrors the 57.111 A3 `{trace}` knobs staying module-level).
- NOT touching the read path's memory injection itself (57.148/151 unchanged) — only what the JUDGE sees.
- NOT adding a wire event / Inspector surface for "judge saw memory" (→ Phase 58 carryover).

### 3.y Validation (US-1..US-6)

Gates: mypy `src` 0/397(+) · run_all 11/11 · pytest 3053+ · Vitest 922 (unchanged — backend-only) · mockup 51 (`diff` empty — FE untouched) · black/isort/flake8 clean · LLM-SDK-leak clean. Plus the §3.5 A/B verdict + the US-5 drive-through (MANDATORY).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/agent_harness/_contracts/state.py` | EDIT (TransientState field) |
| 2 | `backend/src/agent_harness/verification/_trace.py` | EDIT (build_memory_block) |
| 3 | `backend/src/agent_harness/verification/llm_judge.py` | EDIT ({memory} substitution) |
| 4 | `backend/src/agent_harness/verification/templates/output_quality.txt` | EDIT ({memory} section) |
| 5 | `backend/src/agent_harness/verification/templates/key_condition.txt` | EDIT ({memory} section) |
| 6 | `backend/src/agent_harness/orchestrator_loop/loop.py` | EDIT (capture + thread + ctor kwarg) |
| 7 | `backend/src/core/config/__init__.py` | EDIT (env lever) |
| 8 | `backend/src/api/v1/chat/handler.py` | EDIT (wire flag into loop ctor) |
| 9 | `backend/scripts/benchmark_memory_grounded_judge.py` | NEW (A/B harness) |
| 10 | `backend/tests/fixtures/verification/memory_grounded_judge_cases.yaml` | NEW (golden corpus) |
| 11 | `backend/tests/unit/scripts/test_benchmark_memory_grounded_judge.py` | NEW (CI-safe) |
| 12 | `backend/tests/unit/agent_harness/verification/test_llm_judge.py` | EDIT ({memory} substitution) |
| 13 | `backend/tests/unit/agent_harness/verification/<build_memory_block test>` | NEW/EDIT |
| 14 | `backend/tests/unit/agent_harness/orchestrator_loop/test_loop_verification_gate.py` | EDIT (gate threads injected_memory) |
| 15 | `claudedocs/4-changes/feature-changes/CHANGE-120-verification-memory-grounding.md` | NEW |
| 16 | `docs/03-implementation/agent-harness-planning/56-verification-memory-grounding-design.md` | NEW (design note) |
| — | `backend/src/agent_harness/verification/_abc.py` | **UNTOUCHED** (no ABC change) |
| — | `backend/src/agent_harness/verification/rules_based.py` | **UNTOUCHED** |
| — | `backend/src/api/v1/chat/_category_factories.py` | **UNTOUCHED** |
| — | (no migration / no wire schema / no frontend) | **UNTOUCHED** |

## 5. Acceptance Criteria

1. `TransientState.injected_memory` field added; all existing constructions byte-identical (default None); mypy clean.
2. `build_memory_block` renders bounded `[memory:{scope}] {summary}` lines; empty → `""`; unit-tested.
3. `LLMJudgeVerifier` substitutes `{memory}`; a template without `{memory}` is byte-identical; the 2 chat-path templates carry the grounding section + instruction.
4. The loop captures per-turn `memory_accesses` + threads them (flag-gated) into the verify gate's `trace_state`; `verification_memory_grounding=False` → judge prompt byte-identical to pre-fix.
5. The A/B harness produces a verdict: grounded-recall false-positive-reject rate DOWN with memory-grounding, genuine-fabrication catch NOT materially degraded (real Azure, on demand; CI-safe unit test green).
6. **Drive-through PASS (MANDATORY, real UI + backend + LLM)** — a real chat-v2 NEW session asking a 0-keyword identity question recalls the prior-session fact AND the in-loop judge PASSES it (VerificationPassed, no correction turn, no no-recall answer), vs the documented pre-fix REJECT; screenshot + observed-vs-intended in progress.md. (NOT gate-only.)
7. `AD-Verification-Judge-Memory-Inject-Blind` CLOSED; CHANGE-120 + design note 56 (8-point gate); calibration recorded (`verification-memory-grounding-spike` 0.60); navigators + next-phase-candidates updated.

## 6. Deliverables

- [ ] US-1 `TransientState.injected_memory` field
- [ ] US-2 `build_memory_block` + `{memory}` substitution + 2 template edits
- [ ] US-3 loop capture + thread + ctor kwarg + config lever + handler wire
- [ ] US-4 `benchmark_memory_grounded_judge.py` + fixture + CI test + real-Azure A/B verdict
- [ ] US-5 drive-through PASS (real chat-v2 + real Azure)
- [ ] US-6 CHANGE-120 + design note 56 + calibration + navigators + AD CLOSED

## 7. Workload Calibration

- Scope class **NEW `verification-memory-grounding-spike` 0.60** (anchored to `verification-context-hygiene-spike` 0.60 (57.136) + `verification-keycondition-spike` 0.60 (57.138) — same Cat 10 verification spike shape: a bounded judge-context change + an env lever + a real-Azure A/B harness + a real-code core (state field + block helper + judge + 2 templates + loop thread + harness + tests, ≥~3.5 hr) that holds the 0.60 per the 57.137 lesson, NOT a tiny-code 0.85 re-point. 1st data point — KEEP pending 2-3 sprint validation; if it lands > 1.20, re-point toward 0.75 (the drive-through staging — a 2-session 0-keyword recall under the in-loop judge — is the variance risk)).
- **Agent-delegated: no** (parent-direct — a cross-category loop.py-core + contract touch with a non-trivial drive-through; `agent_factor` 1.0 → 3-segment form).
- Bottom-up est ~6 hr (US-1 ~0.3 / US-2 ~1.2 / US-3 ~1.3 / US-4 harness+fixture+tests ~1.7 / US-5 drive-through ~1.0 / US-6 closeout ~0.5) → class-calibrated commit ~3.6 hr (mult 0.60). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Memory-grounding makes the judge TOO lenient (passes genuine fabrications "because memory said so") | The A/B harness explicitly measures `fabrication_catch_rate` on ungrounded cases; the template instruction keeps "still flag genuine contradictions"; if catch regresses ≥5pp → flip the lever to opt-in (default OFF) at closeout. |
| Stale long-running `--reload` backend masks the flag/ctor wiring (Risk Class E) | Day-3 clean restart: kill ALL stale uvicorn + spawn-worker orphans (Win32_Process PID/PPID/StartTime sweep), confirm sole :8000 owner, capture startup log; the flag is read at handler/loop construction = startup-ish. Do NOT kill node. |
| `memory_accesses` shape drift (keys differ from scope/summary) | Day-0 Prong 2 grep `loop.py` ~2406 + the PromptBuilder layer_metadata population; `build_memory_block` reads keys defensively (`.get`). |
| The in-loop judge REJECT is non-deterministic at real LLM (the drive-through trigger may not reliably fire pre-fix) | Stage the drive-through with the 0-keyword identity case proven to REJECT at 57.149/152; if the pre-fix REJECT won't reproduce live, fall back to the A/B harness's deterministic grounded-recall case as the primary evidence + document honestly (AD-DriveThrough-Deterministic-Tool-Trigger precedent). |
| Test stub drift if any verifier test asserts `_build_prompt` output exactly | Day-0 grep test_llm_judge for hard-coded prompt assertions; update to expect the `{memory}` section. |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- Per-tenant memory-grounding policy → carryover `AD-Verification-Memory-Grounding-PerTenant-Phase58` (C3 config-tiering).
- A chat-v2 Inspector surface / wire event for "the judge saw memory this turn" → carryover `AD-Verification-Memory-Grounding-Inspector-Phase58`.
- Semantic relevance ranking of which injected memories the judge sees (CARRY-026 semantic axis).
- The cross-sprint `dan` identity-conflict accumulation observed at 57.152 Leg-2 (a memory-dedup/recency concern, not a judge concern) → already tracked under the memory-formation arc carryovers.
