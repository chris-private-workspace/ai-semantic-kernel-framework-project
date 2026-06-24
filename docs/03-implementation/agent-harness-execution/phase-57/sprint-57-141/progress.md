# Sprint 57.141 Progress — pass^k reliability eval harness (research #2)

**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-141-plan.md`
**Branch**: `feature/sprint-57-141-passk-reliability-harness` (from `main` `196d8892`)
**Closes**: `AD-Eval-PassK-Reliability-Harness` (research #2)

---

## Day 0 — 2026-06-24 — Plan-vs-Repo Verify (三-prong) + Branch

### Branch
- `git checkout -b feature/sprint-57-141-passk-reliability-harness` from `main` `196d8892` ✓

### Prong 1 — path verify (GREEN)
- `backend/scripts/benchmark_pass_k.py` — FREE (NEW) ✓
- `backend/tests/fixtures/observability/` — does NOT exist → NEW dir (D-fixture-dir) ✓
- `backend/tests/unit/scripts/test_benchmark_pass_k.py` — FREE (scripts test dir exists, 5 benchmark tests present) ✓
- Next change record = **CHANGE-108** (107 = latest task-primitive) ✓
- Next spike design note = **45** (44 = latest task-primitive) ✓

### Prong 2 — content verify (GREEN; drift catalog below)

| D-row | Finding | Implication |
|-------|---------|-------------|
| **D-loop-run-noDB** ✅ GREEN (the key scope risk) | `AgentLoopImpl.__init__` (`loop.py:318-397`) requires ONLY `chat_client`/`output_parser`/`tool_executor`/`tool_registry`; `message_store`/`checkpointer`/`reducer`/`tenant_id`/`compactor`/`prompt_builder` ALL `\| None = None`. `run()` (`loop.py:1942-1960`): `message_store is None → prior_messages = []`. | **loop.run() is offline-drivable with NO DB/migration/session** → harness self-contained. Scope NOT shifted (confirmed the plan's offline assumption). |
| **D-verifier-ctor** ✅ GREEN + scope ↓ | `LLMJudgeVerifier(*, chat_client, judge_template, name, tracer, temperature=1.0)` (`llm_judge.py:60`); `verify(*, output, state=None, trace_context=None) → VerificationResult.passed` (`:87`). `RulesBasedVerifier(rules: list[Rule], ...)` (`rules_based.py:40`) is a format/regex `Rule`-list abstraction. | judge oracle = `LLMJudgeVerifier(profile.cheap, "output_quality")`. **rules oracle = inline normalized exact/contains (NOT RulesBasedVerifier)** — drops a dependency, scope slightly ↓. (§3.2 adjusted: rules path is a plain string compare.) |
| **D-chatclient-abc** ✅ GREEN | `ChatClient(ABC)` (`chat_client.py:63`) has 5 abstract: `chat(request, *, cache_breakpoints, trace_context) → ChatResponse` (:69), `stream` (:79), `count_tokens` (:97), `get_pricing` (:112), `supports_feature` (:121). | `_FaultInjectingChatClient` must implement ALL 5: delegate count_tokens/get_pricing/supports_feature/stream to inner; override `chat` to raise transient at `fault_rate` else delegate. |
| **D-handler-factory-shape** ✅ GREEN | `build_real_llm_handler(...)` builds the client internally from `model_policy → profile.action`; takes NO `chat_client` param. | For λ the harness CANNOT inject a client via the factory → **direct-construct `AgentLoopImpl`** with `_FaultInjectingChatClient(profile.action)` + the 4 required deps (same loop shape across baseline/fault arms). Use `build_azure_model_profile()` for the real client (mirror `benchmark_judge.py:281-289`). |
| **D-benchmark-marker** ✅ GREEN | `benchmark` marker registered: `pyproject.toml:68` "real-LLM ... needs RUN_AZURE_INTEGRATION=1 + AZURE_OPENAI_*". | real-Azure path behind `@pytest.mark.benchmark` + `RUN_AZURE_INTEGRATION=1` env gate; CI-safe unit tests use importlib + spies. |
| **D-faultclient-leak** ✅ GREEN | `_FaultInjectingChatClient` subclasses `adapters._base.chat_client.ChatClient` (no `import openai`/`anthropic`). | LLM-SDK-leak lint clean. |

### Prong 3 — schema verify
- **N/A** — offline harness, NO DB table / migration / ORM column.

### D-baselines (from Sprint 57.140 closeout; full re-verify at Day-2 gate)
- pytest 2843+5skip · wire 26 (confirmed `event_wire_schema.py`) · Vitest 920 · mockup 51 · mypy 0/380 · run_all 10/10. (FE/mockup untouched this sprint → those stay; pytest +new CI-safe unit at Day 2.)

### Go/no-go
- **GO** — all D-rows GREEN; scope NOT shifted (slightly ↓: rules oracle is a plain compare, loop is DB-less). Direct-construct `AgentLoopImpl` is the harness's loop factory (D-handler-factory-shape) — a Day-1 implementation detail, not a scope change.

### Plan adjustments (per §Risks, not silent rewrite)
- §3.2 rules oracle: inline normalized exact/contains (NOT `RulesBasedVerifier`) — per D-verifier-ctor.
- §3.1/§3.3 loop factory: `_build_loop(chat_client)` direct-constructs `AgentLoopImpl` (DB-less), `run_case` wraps the client in `_FaultInjectingChatClient` when `fault_rate>0` — per D-handler-factory-shape (the factory takes no client param).

---

## Day 1-2 — 2026-06-24 — Harness core + 4 axes + corpus + CI tests

### Built (3 NEW files, 0 src edit)
- `backend/scripts/benchmark_pass_k.py` — the 4-axis harness:
  - `load_cases` (schema-validated YAML) · `PassKCase`/`RunOutcome`/`CaseRuns`/`PassKReport` dataclasses
  - `_FaultInjectingChatClient(ChatClient)` — 6-method ABC delegate + `chat` raises `InjectedFault` at `fault_rate` (rng-injectable) [λ]
  - `evaluate()` hybrid oracle — rules inline normalized contains/exact | `LLMJudgeVerifier(profile.cheap, per-case-criterion raw template)` for judge cases
  - `run_case()` — drives `AgentLoopImpl.run()` k times DB-less; `_extract()` pulls answer (last LLMResponded.content) / tool_seq / tokens (LoopCompleted) / stop_reason / terminated; escaped fault → failed run
  - `build_report()` — pure: pass@1 / pass^k / divergence / answer+tool-seq consistency / λ degradation / ε instability / per-category / tokens
  - `report_to_markdown` + JSON · `main()` argparse (`--k --fault-rate --epsilon`) + UTF-8 stdout · `_amain` lazy Azure import
- `backend/tests/fixtures/observability/pass_k_cases.yaml` — 12 cases (5 easy + 7 multistep; 10 rules + 2 judge; 2 with ε perturbations); `tool_use` deferred (DB-free robustness)
- `backend/tests/unit/scripts/test_benchmark_pass_k.py` — 17 CI-safe tests (importlib idiom + spy ChatClient 6-method + seeded rng + synthetic CaseRuns + monkeypatched executor driving a real AgentLoopImpl offline)

### Decisions (Day 1-2)
- **λ injection point** = chat client (universal; every case hits the LLM), loop uses DEFAULT error handling → baseline/fault arms differ ONLY by the wrapper = cleanest A/B; measures the real production loop's resilience as-is (escaped fault counts as a failed run). Custom transient-classifying policy deferred (would measure retry-specific recovery; a follow-up).
- **judge oracle** = per-case raw template embedding the correctness criterion + `{output}`, instructing `{"passed": bool}` JSON (what `LLMJudgeVerifier._parse_response` reads) → real correctness checks, not generic quality.
- **tool_use category** = schema-supported but deferred from the shipped corpus (needs mock-tool determinism; keeps the harness DB-free). Corpus = reasoning-only easy+multistep.

### Gates (Day 1-2)
- pass^k unit tests: **17/17 pass** (incl. `test_run_case_drives_loop_offline` — spy client drives a REAL AgentLoopImpl, proving the harness is correctly wired to the loop, no Azure)
- `mypy src/ --strict`: **Success, 380 files, 0 errors** (gate GREEN; harness in scripts/ doesn't affect it; harness type-resolves clean vs src except the `yaml` stub note — identical to `benchmark_judge.py`)
- black/isort/flake8: **clean** (fixed 4 E501 in docstring/markdown lines)
- v2 lint tests (`tests/unit/scripts/lint/` + `test_lint_rule.py`): **21 pass** (incl. `test_llm_sdk_leak` 3 — `_FaultInjectingChatClient` neutrality confirmed)
- backend full pytest: **2859 passed + 5 skip** (133s; 2843 baseline + 17 new = 2860). The 1 "fail" = pre-existing `AD-Billing-Outbox-Drain-Test-Flake` (Risk Class C isolation flake) — **passes in isolation** (re-ran → 1 passed); zero src/billing edit this sprint, not caused here.
- Vitest / mockup / build: UNTOUCHED (no frontend this sprint)

### Drift (Day 1-2)
- **D-runall-stale-path** — CLAUDE.md + `sprint-workflow.md` reference `python scripts/lint/run_all.py` which does NOT exist; the v2 lints are pytest tests under `tests/unit/scripts/lint/`. Stale-doc carryover (NOT this sprint's fix; candidate AD).

---

## Day 3 — 2026-06-24 — Real-Azure drive-through verdict (MANDATORY DoD)

Offline measurement harness → the real-Azure run IS the drive-through (#135/#137/#138 "CATCH = the harness itself", no UI). Standalone script reading root `.env` (gpt-5.2); NO backend server needed.

### Smoke (k=1, ~14 calls) — wiring proven
- Real Azure drove all 12 cases; rules + judge oracle both worked; report generated; tokens counted (13821). End-to-end harness↔loop wiring confirmed before the full spend.

### Full bounded 4-axis run (`--k 3 --fault-rate 0.2 --epsilon`)
- **12 cases · k=3 · 90 runs · 94,373 tokens** · real Azure gpt-5.2. Report → `artifacts/passk-drivethrough-verdict.{md,json}`.

| Axis | Result | Reading |
|------|--------|---------|
| **pass@1 / pass^k** | 100% / 100% · divergence **+0.00%** | On this reasoning corpus at k=3, V2 is fully reliable across repeats. **Honest verdict: NO divergence here** — the corpus (easy/multistep reasoning, no tools, k=3) does NOT stress the regime where research saw pass^8<25% (τ-bench = tool-heavy multi-turn agentic). The harness is correct; the corpus is too easy to surface divergence. |
| **behavioral consistency** | answer **75%** · tool-seq **100%** | ⭐ **KEY finding**: even at pass^k=100%, **3/12 cases gave non-identical answers across the 3 runs** — "passes consistently but phrases differently". This is the "agent disagrees with itself" axis — invisible to pass@1/pass^k. Real signal the harness surfaced. (tool-seq 100% ∵ reasoning cases use no tools.) |
| **λ fault injection (0.2)** | pass^k drop **50%** (100%→50%) | ⭐ **KEY finding**: a 20% LLM-call fault rate halves pass^k → the loop's DEFAULT error handling does NOT auto-retry chat-level faults → a faulted call fails the run. Real resilience number → hardening opportunity (chat-level retry). |
| **ε perturbation** | instability **0.00%** (2 cases) | pass^k held across all paraphrases → V2 robust to wording variation on these cases. Honest good-news. |

### Verdict (honest, evidence-first)
- **The research's pass^k<pass@1 divergence was NOT reproduced on V2's own loop with this reasoning corpus at k=3** — V2 is perfectly reliable here. This is a VALID verdict (either direction was acceptable per the plan): it says "the divergence regime needs a harder/longer/tool-using corpus + higher k" — the corpus is the limiting factor, not the harness (smoke + 90 runs prove the harness drives V2's real loop correctly).
- **Two real reliability signals invisible to pass@1 DID surface**: (1) 25% answer-phrasing inconsistency at 100% pass^k; (2) 50% pass^k collapse under a 20% LLM-fault rate (no chat-level retry). These are the harness's payoff.
- **AP-4 check**: NOT a Potemkin report — all numbers from real Azure runs, rules oracle deterministic (zero judge noise on 10/12 cases), corpus has a real difficulty gradient. The "100% pass^k" is honest (gpt-5.2 IS reliable on these tasks), not an artifact of a rigged oracle.

### Follow-on candidates (from the verdict)
- `AD-Eval-PassK-Harder-Corpus-Phase58` — add tool-heavy / longer multi-turn cases + k≥5 to stress the divergence regime the research flagged.
- `AD-Loop-ChatLevel-Retry-Phase58` — the λ axis showed no chat-call retry; evaluate a transient-classified chat retry (Cat 8) to lift λ resilience.
- `AD-Eval-Answer-Consistency-Surface-Phase58` — the 25% answer-inconsistency is worth surfacing per-case (which 3 cases? semantic vs cosmetic difference?).
