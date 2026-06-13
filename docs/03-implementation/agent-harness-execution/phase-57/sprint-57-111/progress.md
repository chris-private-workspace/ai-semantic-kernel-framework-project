# Sprint 57.111 Progress — A3: trace-aware critique verifier + permanent cheap-judge accuracy benchmark

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-111-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-111-checklist.md)

**Slice**: A3 — the LAST harness-deepening slice (optional). Closes the 10-slice set. Two deliverables: (1) trace-aware critique verifier (the in-loop Cat 10 judge sees recent turns + tool errors); (2) a permanent, re-runnable cheap-judge accuracy benchmark (user picked the permanent-eval-harness shape, 2026-06-13).

---

## Day 0 — 2026-06-13 — Plan-vs-Repo three-prong verify + branch

Branch `feature/sprint-57-111-trace-aware-critique-benchmark` cut from `main` `37e90f06` (post-#285).

### Prong 3 — schema verify
N/A — no DB / no migration. The benchmark is a YAML golden fixture + a pytest test; `verification_log` is NOT used as the source (it has no ground-truth label column — D10). Recorded explicitly.

### Drift findings (D1–D11)

| ID | Finding | Implication |
|----|---------|-------------|
| **D1** | `state=cast(LoopState, None)` lives in **4** sites: the A1 in-loop gate `loop.py:1684` (US-1 target) + 3 Cat 9 fallback judge paths `verification/tools.py:98` / `cat9_mutator.py:102` / `cat9_fallback.py:127` (genuinely no loop state). | US-1 trace-awareness scopes to `loop.py:1684` ONLY. The back-compat `state=None → empty {trace}` is **load-bearing** for the 3 fallback sites (not hypothetical). Plan §3.1 + §8 confirmed. |
| **D2** (central design Q) | `_run_turns` (`loop.py:1968-1981`) has **NO `state: LoopState` object** in scope — only raw per-run locals (`messages: list[Message]` …). `run()` (:1868) creates `messages` + threads it; `resume()` (:3009) rehydrates `state.transient.messages` then threads `messages`. | The trace comes from the loop-local `messages`. The gate gains a `messages` param. Candidate answer is appended at `:2552` (only the "correct" branch) AFTER the gate → at gate time `messages` EXCLUDES the candidate (zero double-count). |
| **D3** (threading mechanism) | `LoopState(transient, durable, version)` is constructed inline in loop.py **3× already** (`compact_state` :2096-2113 / `build_state` :2206 / `snapshot_state` :3525) — `TransientState(messages=list(messages), current_turn=turn_count)` + `DurableState(session_id=…, tenant_id=self._tenant_id or session_id)` + `StateVersion(version=turn_count, …, created_at=datetime.now(), created_by_category="orchestrator_loop")`. | Building a minimal `trace_state` in the gate (mirroring `compact_state`) is the codebase **idiom**, not noise. **Decision**: widen `Verifier.verify` ABC `state: LoopState → LoopState \| None = None` (removes the 4-site `cast(LoopState, None)` type-lie — the 3 fallback sites pass `state=None`, the gate passes the real `trace_state`); the judge reads `state.transient.messages` only when non-None; RulesBasedVerifier signature widened (ignores state anyway). |
| **D4** (judge prompt) | `LLMJudgeVerifier._build_prompt(output)` (`llm_judge.py:112-120`) = `.replace("{output}", output)`; raw-template detection `if "{output}" in self._template_arg`; `verify` calls `_build_prompt(output)` @ :88. | Extend to `_build_prompt(output, state)` + `{trace}` substitution; `output_quality.txt` gains a `{trace}` section. Back-compat: no-`{trace}` templates `.replace` no-op; `{output}`-detection unaffected (templates keep `{output}`). |
| **D5** (marker) | `pyproject.toml:59` `addopts = "-v --strict-markers"`; markers :60-68 = unit/integration/contract/multi_tenant/anti_pattern/observability/slow. **NO `real_llm` marker** (recon phantom flag CONFIRMED). | MUST register `benchmark` marker in pyproject.toml:60-68 (else `--strict-markers` errors at collection). |
| **D6** (CI gate — **SCOPE REDUCTION**) | `backend-ci.yml:164` = `pytest -v --tb=short` (**NO `-m` filter**). Existing real-Azure tests use `pytestmark = pytest.mark.skipif(os.environ.get("RUN_AZURE_INTEGRATION") != "1", …)` (`test_integration.py:54`). | The benchmark guards with the SAME `RUN_AZURE_INTEGRATION` skipif (CI skips gracefully; on-demand `RUN_AZURE_INTEGRATION=1 pytest -m benchmark`). **Plan file #10 (`backend-ci.yml` EDIT) is DROPPED** — not needed. The marker is for selection + strict-markers; the skipif is the CI safety net. |
| **D7** (determinism) | `ChatRequest.temperature: float = 1.0` (`chat.py:116`) but `LLMJudgeVerifier` builds `ChatRequest(messages=[...])` (:89) WITHOUT temperature → judge runs at temp 1.0 (non-deterministic). | For a stable accuracy number, add an optional `temperature: float = 1.0` to `LLMJudgeVerifier.__init__` (production byte-identical; the benchmark constructs its judges with `temperature=0.0`). Small, justified judge change. Day-1. |
| **D8** (profile both tiers) | `build_azure_model_profile(policy=None) -> ModelProfile{action, cheap}` (`profile.py:57`). | The benchmark calls `build_azure_model_profile()` → `LLMJudgeVerifier(chat_client=profile.action, temperature=0)` (strong) + `LLMJudgeVerifier(chat_client=profile.cheap, temperature=0)` (cheap). |
| **D9** (design note 25 structure) | `25-verification-in-loop-design.md`: §0 Summary / §1 Decision Matrix / §2 Verified Invariants (2.1-2.5) / §3 Contracts / §4 Open Invariants (line **77** A3 `[ ]` + line **80** cheap-judge `[ ]`) / §5 Rollback / §6 References / MHist. | Closeout moves §4 lines 77+80 `[ ]` → SHIPPED + adds §2.6 trace-aware + §2.7 benchmark verdict (OR a focused note 26 — finalize per §5.5). |
| **D10** (Prong-3) | No DB / no migration. `verification_log` (`verification_log.py:80`) has no ground-truth label column → NOT the benchmark source. | Benchmark = curated YAML golden fixture. Schema-verify N/A. |
| **D11** (Prong-1 paths) | NEW files Glob-0: `verification/_trace.py` / `templates/forced_fail_trace.txt` / `tests/fixtures/verification/judge_benchmark.yaml` / `tests/benchmark/{__init__,test_judge_accuracy}.py`. `test_judge_accuracy` basename: 0 collisions across the test tree. Guardrails fixture precedent confirmed (`tests/fixtures/guardrails/*.yaml` ×4 — the shape to mirror). | Clean. |

**Baselines** (trust 57.110 closeout; re-verify when tests run Day 1): full pytest **2502+4skip** · wire count **24** · FE Vitest **837** · mockup-fidelity **51** · mypy **0/359**.

### Go/no-go: **GO**
Net scope shift < 20%: D6 REMOVES a file (`backend-ci.yml` not needed — scope reduction); D7 ADDS a tiny judge `temperature` param (in-scope, <5%); D3 widens the ABC `state: LoopState | None` (planned, removes a type-lie). No finding forces a loop.py logic rewrite — US-1 stays a threading + judge-prompt slice. Proceed to Day 1.

### Updated File Change List (post-Day-0)
- DROP #10 `backend-ci.yml` (D6 — skipif guard handles CI).
- CONFIRM #1 `loop.py` (gate: +`messages` param + build `trace_state` mirroring `compact_state` + forward `state=trace_state`; remove `cast(LoopState, None)` @ :1684).
- ADD to #3 `llm_judge.py`: optional `temperature` ctor param (D7) + `_build_prompt(output, state)` (D4).
- ADD `verification/_abc.py` + `verification/rules_based.py` + `verification/tools.py` + `cat9_mutator.py` + `cat9_fallback.py`: widen `state: LoopState | None = None` + drop the `cast` at the 3 fallback sites (D1/D3).

---

## Day 1 — 2026-06-13 — US-1 trace-aware critique verifier (backend)

**Shipped**: the in-loop Cat 10 judge is now trace-aware. The single load-bearing change is `loop.py:1684` `state=cast(LoopState, None)` → a real `trace_state` the gate builds from its `messages` (mirroring the Cat 4 `compact_state` idiom, D3). Around it:
- **`_trace.py` (NEW)** — `build_trace_block(messages, *, max_messages, char_budget)`: bounded (last N msgs / per-msg cap / total char budget; env overrides), provider-neutral, renders `[role] content` + annotates assistant tool calls so a `[tool] ERROR…` reads in context. The candidate answer is NOT in the trace (gate runs before the `:2552` append → no double-count).
- **`llm_judge.py`** — `_build_prompt(output, state)` substitutes `{trace}` from `state.transient.messages` (empty when `state is None`); + an optional `temperature` ctor param (D7 — the benchmark builds judges at 0.0; default 1.0 byte-identical).
- **`output_quality.txt`** — a `{trace}` section + a 4th "contradicts the trace" failure bullet; "MAY BE EMPTY" wording keeps the no-state path identical.
- **ABC widen (D3)** — `Verifier.verify` `state: LoopState | None = None` removes the 4-site `cast(LoopState, None)` type-lie; `rules_based` widened (string-only by design); the 3 Cat 9 fallback judge sites (`tools.py` / `cat9_mutator.py` / `cat9_fallback.py`) now pass `state=None` (back-compat empty trace — load-bearing for them per D1).

**Tests** +13 (CI-safe): `test_trace_block.py` ×8 + `test_llm_judge_trace.py` ×5. No `state is None` pin needed converting (the existing `_state()` helper already returns `cast(LoopState, None)` → exercises the back-compat path).

**Gates (Day-1 partial)**: mypy `src` **0/360** (was 359; +1 = `_trace.py`) · black/isort/flake8 0 · verification + guardrails + orchestrator_loop **617 passed** (+13, 0 del). `loop.py` diff = 1 call-site arg + 1 helper param + the `trace_state` build + the `cast` import removal — NO loop logic rewrite (data threaded in, reviewed line-by-line).

**Decision recorded**: trace knobs are module constants + env override inside `_trace.py`, NOT `core/config` Settings — they are verification-internal tuning, not tenant policy (per-tenant verification is C3, out of scope). Keeps `core/config` untouched.

## Day 2 — 2026-06-13 — US-2 permanent cheap-judge accuracy benchmark (backend)

**Shipped**: a permanent, re-runnable benchmark (user picked the eval-harness shape over a one-off).
- **`scripts/benchmark_judge.py` (NEW)** — the reusable logic (precedent `verify_audit_chain.py`): `BenchCase`/`JudgeRun`/`BenchReport` + `load_cases` (schema-validate) + `run_judge(judge, cases, *, with_trace)` (builds the trace `LoopState` per case so trace_dependent cases exercise US-1) + `build_report` (pure: accuracy-vs-label / cheap-vs-strong agreement / per-category / trace_delta) + `CHEAP_ACCURACY_FLOOR=0.70` (the tracked metric; floor on the unambiguous categories only — borderline excluded) + a `main()` CLI (`python scripts/benchmark_judge.py`).
- **`tests/fixtures/verification/judge_benchmark.yaml` (NEW)** — 28 hand-labeled cases: clear_pass ×8 / clear_fail ×8 / trace_dependent ×7 (5 fail-when-trace-disproves + 2 trace-consistent-pass) / borderline ×5.
- **`tests/benchmark/test_judge_accuracy.py` (NEW)** — the real-LLM wrapper (`@pytest.mark.benchmark` + `RUN_AZURE_INTEGRATION` skipif): builds the Azure profile, runs cheap + strong (temp 0) + cheap-no-trace, asserts the floor. Day-3 drives it for real.
- **`tests/unit/scripts/test_benchmark_judge.py` (NEW)** — 9 CI-safe logic tests (spy Verifier + synthetic JudgeRuns), NO real LLM.
- **`pyproject.toml`** — registered the `benchmark` marker (`--strict-markers` ON). **`.gitignore`** — `/backend/benchmark_reports/`.

**D12 (Day-2 finding — `scripts/` shadow)**: `from scripts.benchmark_judge import ...` works alone but FAILS at collection in the full suite — once the `tests.unit.scripts` package is imported it shadows top-level `scripts` (documented in `pyproject.toml:55` + `test_verify_audit_chain.py`). Fix: BOTH test files load `benchmark_judge.py` via `importlib.util.spec_from_file_location` (register in `sys.modules` before `exec_module` — Py3.12 dataclass resolution), the established codebase idiom.

**D6 confirmed (scope reduction)**: CI runs `pytest -v --tb=short` (no `-m` filter) → the benchmark gates via `RUN_AZURE_INTEGRATION` skipif (CI skips it for free); `backend-ci.yml` NOT edited.

**Gates (Day-2 partial)**: mypy `src` **0/360** (scripts not gated; logic covered by the 9 CI-safe tests) · black/isort/flake8 0 · `-m benchmark` selects exactly 1 · `-m "not benchmark"` deselects it · together **9 passed + 1 skipped**. loop.py / wire / codegen / DB UNTOUCHED.

## Day 3 — (pending)

## Day 4 — (pending)
