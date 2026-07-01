# Sprint 57.153 Progress — make the in-loop verification judge memory-aware

**Sprint**: 57.153 / **AD**: `AD-Verification-Judge-Memory-Inject-Blind` / **Base**: `main` `5bbf1a77`
**Branch**: `feature/sprint-57-153-verification-memory-grounding`

---

## Day 0 — Plan + Checklist + 三-prong verify — YYYY-MM-DD

### Accomplishments
- Scoping investigation (real code read): confirmed the two-fold blind-spot root cause — injected memory lives in the per-turn PromptBuilder artifact (system prompt) → `chat_messages`, NOT the `messages` accumulator (`loop.py:2377`); the verify gate's `trace_state` is built from `messages` (`loop.py:1737`); `build_trace_block` drops ALL system-role messages (`_trace.py:107`). Judge sees `{output}`+`{trace}` only (`llm_judge.py:139`).
- Wrote `sprint-57-153-plan.md` + `sprint-57-153-checklist.md` (frozen templates; short H1 + Summary block + §0 sub-headers).
- Branch created from `main` `5bbf1a77`.

### Day-0 三-prong drift findings (against `main` HEAD `5bbf1a77`)

| ID | Finding | Implication |
|----|---------|-------------|
| **D-memory-accesses-shape** | `builder.py:397-406` — `memory_accesses` entries are `{"scope","time_scale","key","summary"}`; `summary` is the MemoryHint's PII-safe capped summary (NOT raw content) | `build_memory_block` renders `[memory:{scope}] {summary}` (PII-safe by construction); read keys via `.get` defensively |
| **D-trace-state-fresh** | `loop.py:1737` — `_cat10_verify_gate` builds `trace_state` fresh per call (throwaway, not the persisted loop state) | Setting `injected_memory` on it needs NO Reducer → §Scope decision (a) holds |
| **D-loop-ctor-kwarg** | `handler.py:744-753` passes `verifier_registry=` / `verification_escalate_on_max=` / `correction_context_strategy=`; loop ctor takes `correction_context_strategy: str = "keep"` (`loop.py:396,467`) | Add `verification_memory_grounding=settings.chat_verification_memory_grounding` at the same site; mirror the ctor-kwarg pattern |
| **D-judge-template-only-2** | grep templates/: ONLY `output_quality.txt:16` + `key_condition.txt:35` have `{trace}`; the rest (safety_review/pii_leak_check/format_compliance/factual_consistency) are `{output}`-only Cat 9 fallbacks | Add `{memory}` to the 2 trace-aware templates; the `.replace("{memory}", …)` is a harmless no-op on the rest |
| **D-ap8-harness** | `check_promptbuilder_usage.py` is rooted at `backend/src/agent_harness/` (lines 5,12-13); `backend/scripts/` is OUTSIDE → new harness needs NO AP-8 allowlist. BONUS: `llm_judge.py` is ALREADY allowlisted (line 80) → the `_build_prompt` EDIT needs no allowlist change | No AP-8 allowlist touch this sprint |
| **D-judge-prompt-test** | `test_llm_judge.py:174-176` asserts via `in` substring (`"fact-checking judge" in sent_prompt`), NOT exact-equality; other tests use raw `"Judge: {output}"` (no `{trace}`/`{memory}`) | Adding the `{memory}` section + substitution does NOT break existing assertions |
| **D-lint-path** (NEW) | lint scripts live at repo-root `scripts/lint/` (NOT `backend/scripts/lint/`); benchmark scripts at `backend/scripts/`; `run_all.py` invoked `python scripts/lint/run_all.py` from repo root | Command-path correction for my own gate runs; NOT a scope shift |

### Baselines (re-verify before commit)
pytest 3053 · wire 26 · Vitest 922 · mockup 51 · mypy 0/397 · run_all 11/11

### Go/no-go
**GO** — scope-shift ~0%; all 6 planned drift checks + 1 bonus resolved pre-code; no plan §Technical Spec revision needed. Design = the direct parallel of 57.111 A3 (`{trace}`), now for `{memory}`.

### Remaining for Day 1
- US-1 `TransientState.injected_memory` field
- US-2 `build_memory_block` + `{memory}` substitution + 2 template edits

### Notes
- Doc numbering confirmed: design note → **56** (55 highest), CHANGE → **120** (119 highest).

---

## Day 1 — state field + memory block + judge {memory} — 2026-07-01

### Accomplishments
- US-1: `TransientState.injected_memory: str | None = None` (additive; docstring + MHist).
- US-2: `build_memory_block(accesses, *, char_budget)` in `_trace.py` (`[memory:{scope}] {summary}` capped; empty→""; keep-head drop-tail; defensive non-dict; env `CHAT_VERIFICATION_MEMORY_CHAR_BUDGET`). `LLMJudgeVerifier._build_prompt` substitutes `{memory}` from `state.transient.injected_memory` (no-op when absent/None). `output_quality.txt` + `key_condition.txt` gain a RETRIEVED MEMORY `{memory}` grounding section + "consistent = GROUNDED, still flag contradictions" instruction.
- Tests: 9 `build_memory_block` + 4 `{memory}` substitution. 2 E501 trimmed.
- Gate: black/isort/flake8 0 · mypy clean · 32 affected tests pass.

## Day 2 — loop wiring + config flag + handler — 2026-07-01

### Accomplishments
- US-3 loop: ctor kwarg `verification_memory_grounding: bool = True`; capture `turn_injected_memory` at the PromptBuilder build branch; `_cat10_verify_gate(*, injected_accesses=None)` renders `build_memory_block` (flag-gated) → `trace_state.transient.injected_memory`. MHist updated.
- US-3 config/handler: `chat_verification_memory_grounding: bool = True` (env `CHAT_VERIFICATION_MEMORY_GROUNDING`); handler wires it into the loop ctor.
- Tests: 3 gate-threading tests (`_CapturingVerifier` — ON renders block / OFF None / no-accesses None).
- **Stub-drift caught** (Risk Class — fake settings): `test_handler.py` SimpleNamespace fake settings lacked `chat_verification_memory_grounding` → 3 failures → added the field (mirrors the 57.136/57.99 stub-mirror pattern).
- **check_cross_category_import FAIL** → loop imported the PRIVATE `verification._trace`; re-exported `build_memory_block`+`build_trace_block` from `verification/__init__.py` + loop imports via the package → 11/11.

### Gate (Day 2 full)
mypy `src` 0/397 · run_all **11/11** · black/isort/flake8 clean · LLM-SDK-leak clean · 188 affected tests pass (verification 88 + loop 96 + handler 46 overlap). FE untouched (full pytest/Vitest at closeout).

### Remaining for Day 3
- US-4 A/B harness (`benchmark_memory_grounded_judge.py` + fixture + CI test) + real-Azure verdict
- US-5 drive-through (real chat-v2 + real Azure)

## Day 3 — A/B harness + drive-through — 2026-07-01

### US-4 A/B harness + real-Azure verdict
- `scripts/benchmark_memory_grounded_judge.py` (importable core + golden YAML + 13 CI-safe tests). Two arms (memory_aware vs bare) over a 10-case corpus (5 grounded-recall + 5 contradiction). Real production judge (`LLMJudgeVerifier` + output_quality, cheap tier).
- **Real Azure A/B (10 cases · 20 cheap-tier judge calls)** — `benchmark_reports/memory_grounded_judge_report.{md,json}`:
  - `grounded_recall_false_reject_rate`: bare **0%** → memory_aware **0%** (Δ 0)
  - `fabrication_catch_rate`: bare **0%** → memory_aware **100%** (Δ **+100pp**)
  - **verdict: KEEP memory-grounding default ON**
- **Honest finding**: a memory-blind `output_quality` judge is lenient enough ("when in doubt pass") that it does NOT false-reject grounded recalls in an isolated 1-turn corpus → the "blind judge rejects grounded recall" mode the drive-throughs saw at 57.149/152 is driven by ACCUMULATED cross-session memory creating a CONTRADICTION, not a clean grounded recall. The fix's deterministic, measurable value is **contradiction detection**: the memory-aware judge caught ALL 5 memory-contradicting answers (0→100%) that the blind judge missed, at ZERO false-reject cost. The verdict logic was corrected to a two-sided OR (ship if EITHER false-reject drops OR catch improves materially, AND neither regresses) mirroring `benchmark_correction_hygiene`.

### US-5 drive-through (real chat-v2 + real Azure gpt-5.2) — STRONG PASS
- **Risk Class E clean restart**: killed stale 57.152 backend PID 47908 (old code) via Win32_Process sweep → port 8000 free → fresh backend PID 49236 sole owner (new code, memory-grounding default ON); frontend vite :3007 untouched (node).
- **Leg 1** (session `ab497b91`, dev-login jamie@acme.com): "My name is Dana Okafor and I lead the Verification Loops category." → agent proactively `memory_write` ×2 (`User's name is Dana Okafor.` 0.95 / `User leads the Verification Loops category.` 0.9); final answer **Verification passed score 0.99**. Memory formation (57.148/149) live.
- **Leg 2** (NEW session `760d...`-style, 0-keyword recall "你知道我是誰嗎?我負責哪個範疇?"): the Loop trace shows the PromptBuilder injected the user-layer memory (4 `memory_accessed` reads incl. the NEW Dana facts AND the OLD 57.148 `User name is Chris.`/`Knowledge Connector` facts = an accumulated cross-session CONTRADICTION). The agent recalled: "you may be **Dana Okafor** (Verification Loops) OR **Chris** (Knowledge Connector) … which should I treat as authoritative?" → **Verification passed score 0.98**.
- **THE fix demonstrated**: the recall is GROUNDED in injected memory (both facts ARE in the user's durable memory) and the memory-aware in-loop judge PASSED it (0.98) — vs the pre-fix memory-BLIND judge (57.152 Leg-2) which rejected a memory-grounded recall as fabrication and coached it into a no-recall answer. The accumulated Dana+Chris contradiction reproduced the exact 57.152 scenario live; the fix delivered the grounded recall instead of erasing it (the agent even transparently surfaced the memory conflict). Screenshots: `artifacts/sprint-57-153-leg{1,2}-*.png`.

### Gate (Day 3)
flake8 0 · mypy `src` 0/397 (harness in scripts/ is outside the gate, mirrors benchmark_correction_hygiene) · 13 CI-safe harness tests pass · A/B real-Azure verdict KEEP-ON.

### Remaining for Day 4
- CHANGE-120 + design note 56 (8-point gate) + retrospective + calibration + navigators + AD CLOSE.

## Day 4 — CHANGE-120 + design note 56 + closeout — 2026-07-01

### Accomplishments
- `CHANGE-120-verification-memory-grounding.md` + design note `56-verification-memory-grounding-design.md` (8-point gate: §1 decision matrix TransientState-field-vs-ABC-kwarg / file:line per claim / verification commands / fixtures / open-invariant split / rollback = env flip / 17.md §1.1+§2.1 cross-ref).
- retrospective.md Q1-Q7 + calibration (NEW `verification-memory-grounding-spike` 0.60, 1st pt ratio ~1.0 IN band, KEEP).
- **Final gate sweep**: pytest **3082 passed / 6 skip (+29)** · mypy `src` **0/397** · run_all **11/11** · black/isort/flake8 clean · LLM-SDK-leak clean. FE untouched.
- Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (CLOSE `AD-Verification-Judge-Memory-Inject-Blind` + Phase58 carryovers) · sprint-workflow matrix (`verification-memory-grounding-spike` row).
- Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/11 → 0 violations; v2 lints 11/11.
