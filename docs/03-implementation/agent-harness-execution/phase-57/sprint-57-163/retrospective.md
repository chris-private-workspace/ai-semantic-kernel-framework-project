# Sprint 57.163 Retrospective — Tool-error reflection rare-path verify + weaker-model A/B

**Closed**: 2026-07-09 · **Branch**: `feature/sprint-57-163-tool-reflection-evidence` · **CHANGE-130** · NO design note

## Q1 — What shipped

Closed 2 Tool-range (Cat 2) evidence carryovers from Sprint 57.144:
- **③1 rare-path verify**: an integration fault-inject test (`_RaisingExecutor` → `loop.py:3068` branch, lever ON/OFF) proving the rare reflection wiring; honestly labelled **gate-only** (the branch is near-unreachable on the 主流量 per Day-0) + a reality finding + a follow-on AD.
- **③4 weaker-model A/B**: a `--answerer-tier {action,cheap}` knob (`select_answerer` helper) + one real-Azure cheap-tier run.
- ③1-fix: `_error_taxonomy.py:36` stale cross-ref (3023-3030 → 3068-3086).

**KEY finding — reflection is tier-dependent**: strong tier +0.00% (57.144, keep OFF) vs weak tier **+12.5%** at **−6.8 tokens** (this sprint). Refines the 57.144 blanket "keep OFF" — reflection helps where the model is weaker.

## Q2 — Estimate accuracy / calibration

- Scope class **NEW `tool-reflection-drivethrough-evidence-spike` 0.60** (anchored to 57.144 `tool-reflection-and-lint-spike` 0.60 + the `verification-*` / `guardrail-restrict-spike` 0.60 evidence-first family).
- **Agent-delegated: no** (parent-direct — the Day-0 re-scope judgement + reading the A/B verdict need the parent in the loop). `agent_factor` 1.0 → 3-segment.
- Bottom-up ~5 hr → class-calibrated commit ~3 hr (mult 0.60). **Actual ~3 hr equiv → ratio ~1.0, IN band → KEEP 0.60 (1st data point)**. The Day-0 re-scope dropped ~1 hr of UI drive-through staging but added the re-scope decision + a ~4-file 方案-A alignment pass; net ~on budget. The real-code core (knob + `select_answerer` + 2 test files + docstring) was ~2-2.5 hr, so — unlike the 57.120 ceremony-not-code-accelerated re-points — the 0.60 spike multiplier held (57.137 lesson). If a 2nd `tool-reflection-drivethrough-evidence-spike` diverges > 30% from 0.60, re-point.

## Q3 — What went well / key lesson

- **Day-0 三-prong paid off big (D-executor-self-raise)**: reading `executor.execute()` before writing code revealed the rare path is near-unreachable in production (executor turns every failure into a `ToolResult`). Caught the un-doable drive-through BEFORE committing to it → re-scoped honestly rather than faking a Potemkin drive-through. This is exactly the Drive-Through-Acceptance discipline working (don't claim usability for a branch a human can't reach).
- **The weaker-model A/B produced a genuinely new, actionable finding** (tier-dependent reflection), not just a confirmation — the ③4 knob was worth building.
- Honest gate-only labelling of ③1 (integration test + reality finding, NOT a drive-through) respects the constraint's pure-backend exemption.

## Q4 — What to improve next

- The A/B is 8-case single-run → directional only. Adopt 57.154's `--runs N` averaging pattern before any evidence is used to flip a real default (logged as `AD-Tool-Reflection-PerTier-Default` prerequisite).
- 2 progress/plan Edit mismatches this sprint (em-dash / "path" word) cost re-reads — copy exact surrounding text for long-string Edits.

## Q5 — Anti-pattern self-check

- AP-2 (side-track): benchmark reachable via `main` + CI unit tests; integration test via pytest — ✅
- AP-4 (Potemkin): the rare branch is honestly gate-only + reality-finding-labelled — the anti-Potemkin move (NOT claimed as a drive-through) — ✅
- AP-8 (PromptBuilder): N/A (no prompt assembly changed) — ✅
- AP-10 (mock/real divergence): the A/B uses the PRODUCTION `classify_tool_error`/`render_reflection` + real Azure; the integration test's `FakeChatClient` is a standard test double — ✅
- AP-11 (version suffix): none — ✅
- v2 lints 11/11.

## Q6 — Carryover

- `AD-Tool-Reflection-RarePath-Near-Dead-Evaluate` — is the near-unreachable rare branch worth keeping, or should the executor expose a real self-raise → reflected-observation path?
- `AD-Tool-Reflection-PerTier-Default` — default ON for weaker/cheap-tier answerers (evidence: +12.5%), OFF for strong; or a per-tenant/per-profile reflection policy on the C3 seam. Needs a larger corpus / multi-run first.
- Tool range still open: ③2 `AD-Tool-Description-AutoFix`, ③3 `AD-Tool-Error-Taxonomy-UI`.

## Q7 — Gate summary

mypy `src` 400/0 · v2 lints 11/11 · black/isort/flake8 clean · pytest **3230 passed, 5 skipped, 0 fail** (+6: 4 knob unit + 2 rare-path integration) · A/B real-Azure cheap arm +12.5%. NO migration/wire/codegen/frontend.
