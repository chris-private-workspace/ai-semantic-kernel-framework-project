# CHANGE-120: Memory-aware in-loop verification judge

**Date**: 2026-07-01
**Sprint**: 57.153
**Scope**: 範疇 10 (Verification Loops) × 範疇 3 (Memory) × 範疇 1 (Orchestrator Loop) — backend-only

## Problem

The in-loop Cat 10 verification judge (57.98 A1 + 57.111 A3) saw only `{output}` + a `{trace}`
block built from the conversation accumulator `messages`. The memory injected by `DefaultPromptBuilder`
(57.148 `profile()` user facts + 57.151 `recent_sessions()` summaries) lives in the per-turn prompt
artifact (the system prompt), never in `messages`, and `build_trace_block` drops every system-role
message. So the judge was BLIND to the grounding the agent had: a memory-grounded recall — especially
a 0-keyword-overlap one ("你知道我是誰?" → "你是 Chris") — read as an unsupported/off-topic claim, and
the judge false-positive-REJECTed it, triggering a coached retry that produced a no-recall answer
(observed live at Sprint 57.149 + 57.152 Leg-2). This silently defeated the 57.148→152 memory-formation
arc on the verification path: the memory was injected, the agent recalled correctly, but the judge erased it.

## Root Cause

Two stacked facts (both re-verified Day-0, `main` `5bbf1a77`):
1. The injected memory is rendered into the per-turn `artifact` → `chat_messages` (`loop.py:2377`), NOT
   merged back into the `messages` accumulator the verify gate builds `trace_state` from (`loop.py:1737`).
2. `build_trace_block` explicitly drops all system-role messages (`_trace.py:107`).

So the judge prompt (`llm_judge.py:139`) substituted `{output}`+`{trace}` only — the memory the agent
was grounded in never reached it.

## Solution

The direct parallel of 57.111 A3 (which added `{trace}`): make the judge **memory-aware**.

- `TransientState.injected_memory: str | None` (new field, additive default-None) — carries the memory
  rendered into THIS turn's prompt. Set only on the gate's throwaway `trace_state` snapshot (no Reducer).
- `build_memory_block(accesses, *, char_budget)` (`verification/_trace.py`, sibling to `build_trace_block`)
  — renders the per-turn `memory_accesses` (`builder.py:397` — `{scope, summary}`, PII-safe capped) as
  bounded `[memory:{scope}] {summary}` lines; empty → `""`.
- `LLMJudgeVerifier._build_prompt` substitutes a new `{memory}` placeholder from
  `state.transient.injected_memory` (no-op when absent — same property as `{trace}`).
- `output_quality.txt` + `key_condition.txt` gain a RETRIEVED MEMORY `{memory}` section + the instruction
  "a statement consistent with the retrieved memory is GROUNDED — do NOT flag it as fabricated/off-topic
  merely because the trace doesn't mention it; still flag genuine contradictions."
- The loop captures `turn_injected_memory` at the PromptBuilder build branch and threads it into
  `_cat10_verify_gate(..., injected_accesses=)`, gated on a new ctor kwarg `verification_memory_grounding`
  (mirrors 57.136 `correction_context_strategy`), set from `settings.chat_verification_memory_grounding`
  (env `CHAT_VERIFICATION_MEMORY_GROUNDING`, default ON; `=false` → judge byte-identical to pre-57.153).

**Key design choice**: thread via a `TransientState` field, NOT a `Verifier.verify` ABC kwarg. The gate
already constructs a throwaway `trace_state`; a field touches 0 verifier impls + 0 test stubs (vs ~13 for
an ABC kwarg), and "what memory was injected this turn" is a legitimate transient fact.

`build_memory_block`+`build_trace_block` re-exported from `verification/__init__.py` (the loop imports the
package, not the private `_trace` — `check_cross_category_import` compliance).

Files: `_contracts/state.py` · `verification/_trace.py` · `verification/llm_judge.py` ·
`verification/__init__.py` · `verification/templates/{output_quality,key_condition}.txt` ·
`orchestrator_loop/loop.py` · `core/config/__init__.py` · `api/v1/chat/handler.py` +
`scripts/benchmark_memory_grounded_judge.py` + fixture + tests. NO migration / wire / frontend.

## Verification

- **Real-Azure A/B harness** (`benchmark_memory_grounded_judge.py`, 10 cases · 20 cheap-tier judge calls):
  `grounded_recall_false_reject_rate` bare 0% → memory 0%; `fabrication_catch_rate` bare **0% → memory 100%**
  (+100pp); **verdict KEEP default ON**. Honest finding: a memory-blind `output_quality` judge is lenient
  enough to PASS grounded recalls in isolation, so the fix's deterministic measurable value is
  **contradiction detection** (catching answers that contradict the user's durable memory) at zero
  false-reject cost.
- **Drive-through STRONG PASS** (real chat-v2 + real Azure gpt-5.2, fresh backend PID 49236): Leg 1
  jamie states "Dana Okafor / Verification Loops" → memory_write ×2 + verify 0.99; Leg 2 NEW session
  0-keyword "你知道我是誰?我負責哪個範疇?" → the agent recalled both grounded facts (the accumulated
  Dana + 57.148 Chris = a CONTRADICTION, surfaced transparently) and the memory-aware judge
  **VerificationPassed score 0.98** — the grounded recall was DELIVERED, vs the pre-fix blind judge
  (57.152 Leg-2) that rejected→no-recall. Screenshots in the sprint artifacts.
- Gates: mypy `src` 0/397 · run_all 11/11 · pytest (+38: 9 block + 4 substitution + 3 gate-threading +
  13 harness + handler-stub fixes) · black/isort/flake8 clean · LLM-SDK-leak clean.

## Impact

Backend-only. Closes `AD-Verification-Judge-Memory-Inject-Blind`. The in-loop judge no longer erases
memory-grounded recalls, and now catches answers that contradict the user's durable memory. Default ON
with a one-env-var revert (`CHAT_VERIFICATION_MEMORY_GROUNDING=false`). The read-path memory injection
(57.148/151) and the `Verifier.verify` ABC are untouched. Carryovers: `AD-Verification-Memory-Grounding-PerTenant-Phase58`
(C3 config-tiering) + `AD-Verification-Memory-Grounding-Inspector-Phase58` (a chat-v2 surface for "the
judge saw memory this turn").
