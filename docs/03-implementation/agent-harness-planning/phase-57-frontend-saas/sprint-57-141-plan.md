# Sprint 57.141 Plan — pass^k reliability eval harness (research #2)

**Summary**: An evidence-first measurement-harness thin spike that gives V2 its first `pass^k` (repeat-k-runs) reliability eval — the axis `pass@1` / drive-through-once is blind to (τ-bench: GPT-4o pass@1 ~61% but pass^8 <25%). Closes `AD-Eval-PassK-Reliability-Harness` (research #2, canonical-order next after #6/#3/#8/#4/#1). Ships a pure-offline `scripts/benchmark_pass_k.py` (mirrors the proven `benchmark_judge.py`) measuring **4 axes** (user-picked): pass^k vs pass@1 · behavioral consistency · fault injection (λ) · perturbation (ε), with a **hybrid oracle** (rules-based first, LLMJudge for open-ended) over a multi-step-graded corpus. **Drive-through is MANDATORY** but is a real-Azure harness run producing a real verdict (offline/no-UI — the #135/#137/#138 "CATCH = the harness itself" pattern), NOT chat-v2 UI. Design note REQUIRED (spike sprint). NO migration / NO wire (stays 26) / NO frontend / NO `loop.py` edit.

**Status**: Approved-to-execute (user 2026-06-24: selected "下一步執行 #2"; AskUserQuestion → axes = all 4, oracle = hybrid rules+judge)
**Branch**: `feature/sprint-57-141-passk-reliability-harness`
**Base**: `main` HEAD `196d8892` (Sprint 57.140 task-primitive #333 merged)
**Slice**: closes `AD-Eval-PassK-Reliability-Harness` (research #2); standalone (net-new, no arc)
**Scope decisions**: (a) 4 axes pass^k + behavioral-consistency + λ-fault + ε-perturbation (user-picked over the recommended minimal 2-axis — defensible: the spike MEASURES λ/ε on V2's own loop, self-producing data vs trusting the 🔴 weak external citations) (b) hybrid oracle: rules-based exact/contains first, LLMJudge for open-ended (c) pure-offline harness mirroring `benchmark_judge.py` — zero src edit, zero wire/migration/frontend.

---

## 0. Background

### The gap (`AD-Eval-PassK-Reliability-Harness`, research #2)

The platform proves quality two ways today — **drive-through** (run once, can a human use it) + **5 A/B benchmarks** (two arms, one run each). **Neither measures repeatability**: run the SAME input k times — do all k pass? Research's headline finding is `reliability ≠ capability` and the two **diverge super-linearly with task length**, invisible to `pass@1` (τ-bench: GPT-4o retail pass@1 ~61% but **pass^8 <25%**).

### Why it matters (the missing capability)

A drive-through PASS is a `pass@1` sample. A feature that drives through cleanly may be <25% reliable across 8 repeats. The platform is **structurally blind to cross-run reliability** — exactly the "reliability science" axis research §4 theme 6 says must augment drive-through. And research §6 flags V2's trace-persistence as **one of the few cheap places to generate enterprise multi-tenant pass^k data** — a structural advantage left unused.

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `196d8892`) | Anchor |
|-------|--------------------------------------|--------|
| 5 benchmark scripts | ALL A/B two-arm, NONE repeat-k-run | `backend/scripts/benchmark_judge.py:171-187` (cheap vs strong) |
| harness scaffold | proven: load_cases→run→build_report→MD+JSON, real Azure | `benchmark_judge.py:109-349` |
| run-driving entry | `loop.run()` callable k times via built handler | `orchestrator_loop/loop.py:1942-1948` + `handler.py:280-348` |
| trace data source | `message_events` JSONB + `LoopCompleted` tokens + per-event `trace_id` | `infrastructure/db/models/sessions.py:224-268` + `event_wire_schema.py:66` |
| existing pass^k/consistency/fault | **NONE** (grep zero) — only test-only `FlakyTransientError` | `tests/.../test_loop_retry_integration.py:191` |

→ The fix builds a NEW offline harness that drives `loop.run()` k times per case, judges each via a hybrid oracle, and computes 4 reliability axes — reusing the benchmark scaffold + the existing verifiers, touching NO src.

### The design (offline harness: 3 new files, 0 src edit, 4 axes)

```
NEW scripts/benchmark_pass_k.py
    load_cases(YAML) -> list[PassKCase]                 # mirror benchmark_judge.load_cases
    run_case(handler_factory, case, k, *, fault_rate, rng) -> CaseRun
        # drive loop.run() k times; per run collect {passed, final_answer, tool_seq, stop_reason, tokens}
        # oracle: rules-based exact/contains (oracle_type=rules) | LLMJudgeVerifier (oracle_type=judge)
    _FaultInjectingChatClient(ChatClient)               # λ: wrap client, raise transient at fault_rate (rng-injectable)
    build_report(...) -> PassKReport                    # pure metrics:
        pass@1   = mean over cases of (passing runs / k)
        pass^k   = fraction of cases where ALL k runs passed   # the divergence headline
        behavioral_consistency = answer-identical rate + tool-seq-identical rate across k runs
        lambda_axis = pass^k(fault_rate=0) - pass^k(fault_rate=λ)        # resilience (Cat 8 retry recovers some)
        epsilon_axis = pass^k variance across input paraphrases          # wording sensitivity
        per_category (easy / multistep / tool_use)        # the divergence hypothesis test
    main()  argparse: --fixture --out --k(=5) --fault-rate(=0.2) --epsilon(flag)
NEW tests/fixtures/observability/pass_k_cases.yaml       # ~10-14 cases, difficulty-graded + perturbation variants
NEW tests/unit/scripts/test_benchmark_pass_k.py          # CI-safe: importlib + SpyLoop + SpyOracle, NO Azure, seeded rng
```

Why offline-online-generate (not offline-consume): prod has no naturally-repeated runs yet, so the harness GENERATES the k runs by calling `loop.run()` (mirrors `benchmark_judge` calling the judge). `_FaultInjectingChatClient` is defined IN the script (no src change). Randomness uses `random.Random` with an injectable seed so unit tests stay deterministic.

### Ground truth (recon head-start — code read on `main` HEAD `196d8892`; ALL re-verified §checklist 0.1)

- `backend/scripts/benchmark_judge.py:109-151` — `load_cases` YAML+schema+unique-id pattern to mirror
- `backend/scripts/benchmark_judge.py:278-295` — `build_azure_model_profile()` → `profile.cheap/.action`; `LLMJudgeVerifier(chat_client=..., temperature=0.0)` (the oracle for open-ended cases)
- `backend/tests/unit/scripts/test_benchmark_judge.py:19-45` — importlib file-path load idiom (CI-safe)
- `backend/tests/unit/scripts/test_benchmark_judge.py:103-120` — Spy verifier pattern (no Azure)
- `api/v1/chat/handler.py:280-348` — `build_real_llm_handler(...) → AgentLoopImpl`; env-validate `AZURE_OPENAI_*` `:325-332`
- `orchestrator_loop/loop.py:1942-1948` — `run(*, session_id, user_input, trace_context) → AsyncIterator[LoopEvent]`
- `agent_harness/verification/rules_based.py` + `llm_judge.py:57-121` — the two verifiers the hybrid oracle wraps
- `adapters/_base/` `ChatClient` ABC — what `_FaultInjectingChatClient` subclasses (LLM-neutral; NO `import openai`)

**Baselines (Sprint 57.140 closeout)**: pytest 2843+5skip · wire 26 · Vitest 920 · mockup 51 · mypy 0/380 · run_all 10/10. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — filled in §checklist 0.1)

- **D-chatclient-abc** — grep the real `ChatClient` ABC method signature (`chat`/`stream`?) so `_FaultInjectingChatClient` overrides correctly (Prong 2).
- **D-handler-factory-shape** — confirm `build_real_llm_handler` kwargs needed to drive a minimal run (db/session_id/tenant_id optional?) so the harness can build a handler without full DB (Prong 2).
- **D-verifier-ctor** — confirm `RulesBasedVerifier` + `LLMJudgeVerifier` ctor + `verify()` signature (does it take `state`?) for the oracle wrapper (Prong 2).
- **D-loop-run-noDB** — confirm `loop.run()` works without a message_store/db (offline harness may run DB-less; if not, harness needs a minimal in-memory path) (Prong 2 — scope risk).
- **D-fixture-dir** — `tests/fixtures/observability/` exists or NEW (Prong 1).
- **D-benchmark-marker** — confirm `@pytest.mark.benchmark` registered (pyproject/pytest.ini) for the real-Azure gate (Prong 1/2).

## 1. Sprint Goal

Ship a permanent, re-runnable `scripts/benchmark_pass_k.py` that, on real Azure, measures pass^k vs pass@1 + behavioral consistency + λ-fault + ε-perturbation over a difficulty-graded corpus, and produces a MD+JSON report — then DRIVE it on real Azure to obtain an honest verdict on **whether pass^k actually diverges from pass@1 in V2's own loop** (either direction is a valid verdict: divergence = a real reliability blind spot found; no divergence = V2 stable on this corpus, with corpus-difficulty noted). Proven by: CI-safe unit tests green (no Azure) + the mandatory real-Azure drive-through run + full gate sweep. Produces CHANGE-NNN + a spike design note (8-point gate).

## 2. User Stories

- **US-1** (pass^k core): 作為平台可靠性負責人，我希望對同一輸入重複跑 k 次量測 pass^k vs pass@1，以便看見 pass@1 隱藏的長程可靠性退化。
- **US-2** (behavioral consistency): 作為可靠性負責人，我希望即使 k 次全 pass 也能量測答案/tool-序列跨 run 一致性，以便偵測「agent 跟自己不同意」。
- **US-3** (fault injection λ): 作為可靠性負責人，我希望注入 infra fault（transient LLM error）量測 pass^k 退化，以便了解 Cat 8 retry 的容錯韌性。
- **US-4** (perturbation ε): 作為可靠性負責人，我希望對輸入 paraphrase 量測 pass^k 穩定性，以便了解對措辭的敏感度。
- **US-5** (hybrid oracle + graded corpus): 作為可靠性負責人，我希望 rules-based 優先 + judge 開放題判定 + 含難度梯度的 corpus，以便 pass^k 訊號誠實（封閉題零 judge noise）。
- **US-6** (verdict drive-through, MANDATORY): 作為可靠性負責人，我希望真 Azure 跑完產出誠實 verdict（pass^k 是否 < pass@1），以便 evidence-first 證明/證偽研究命題。
- **US-7** (closeout): CHANGE-NNN + design note (8-point gate) + calibration + navigators。

## 3. Technical Specifications

### 3.0 Architecture (offline harness; NO src edit / NO migration / NO wire / NO frontend)

```
NEW backend/scripts/benchmark_pass_k.py                       — 4-axis harness (load_cases / run_case / _FaultInjectingChatClient / build_report / main)
NEW backend/tests/fixtures/observability/pass_k_cases.yaml    — corpus (~10-14: easy/multistep/tool_use + ε perturbation variants)
NEW backend/tests/unit/scripts/test_benchmark_pass_k.py       — CI-safe unit (importlib + SpyLoop + SpyOracle + seeded rng, NO Azure)
UNTOUCHED orchestrator_loop/loop.py · api/v1/chat/handler.py · event_wire_schema.py (wire stays 26) · any migration · frontend
UNTOUCHED agent_harness/verification/{rules_based,llm_judge}.py (harness WRAPS, never edits)
```

### 3.1 Harness core (US-1/2) — `scripts/benchmark_pass_k.py`

- `PassKCase` frozen dataclass: `id, input, oracle_type ∈ {rules,judge}, expected (str|list[str]|None), category ∈ {easy,multistep,tool_use}, perturbations: list[str] = []`.
- `load_cases(path)`: YAML parse + schema validate (required keys, unique id, category enum, oracle_type enum, judge cases must have a non-empty `expected` criterion string OR fall back to output_quality) — mirror `benchmark_judge.load_cases:109-151`.
- `run_case(handler_factory, case, k, *, fault_rate, rng)`: for each of k runs, build a handler (optionally wrapping its ChatClient in `_FaultInjectingChatClient` when `fault_rate>0`), `await loop.run(...)`, drain events → capture `final_answer` (last `LLMResponded.content`), `tool_seq` (ordered `ToolCallRequest.name`), `stop_reason`, `tokens`; oracle-judge → `passed: bool`. Returns `CaseRun(passed: list[bool], answers, tool_seqs, tokens)`.

### 3.2 Hybrid oracle (US-5)

- `evaluate(case, answer, state) -> bool`: `oracle_type=="rules"` → normalized exact/contains match against `expected` (zero judge noise — for easy/closed-form); `oracle_type=="judge"` → `LLMJudgeVerifier(profile.cheap, template="output_quality"|"key_condition")` `.verify(answer, state)` → `.passed`. Judge-noise documented as a known caveat.

### 3.3 Fault axis λ (US-3)

- `_FaultInjectingChatClient(ChatClient)`: wraps an inner client; on each call, `rng.random() < fault_rate` → raise a transient error (the class the Cat 8 retry matrix classifies TRANSIENT) else delegate. `rng` injectable (`random.Random(seed)`) so unit tests are deterministic.
- λ metric: run the pass^k pass twice (`fault_rate=0` baseline vs `fault_rate=λ`), report `lambda_degradation = pass^k(0) − pass^k(λ)` (Cat 8 retry should recover some → degradation < raw fault rate).

### 3.4 Perturbation axis ε (US-4)

- For cases with `perturbations` (paraphrases of `input`), run pass^k for the original + each variant; report `epsilon_stability` = pass^k spread (max−min) across paraphrases per case + aggregate.

### 3.5 Report (US-1..4) — `build_report` + MD/JSON

- pure function → `PassKReport`: `pass_at_1`, `pass_k`, `divergence (=pass@1−pass^k)`, `answer_consistency`, `tool_seq_consistency`, `lambda_degradation`, `epsilon_stability`, `per_category: dict`, `total_tokens`, `total_runs`. Markdown (human verdict table) + JSON (tooling) → `backend/benchmark_reports/`. Mirror `benchmark_judge` `report_to_markdown:251-275` + JSON `:300-317`.

### 3.6 What is explicitly NOT done

- ❌ MAST 14-mode failure auto-classifier (no existing taxonomy; separate large item → `AD-Eval-MAST-Classifier-Phase58`).
- ❌ persistence-driven cross-tenant pass^k data pipeline (the harness GENERATES runs; reading them back from `message_events` is a noted optional extension, not in this slice → `AD-Eval-PassK-Persistence-Pipeline-Phase58`).
- ❌ wire event / chat-v2 dashboard (YAGNI — pass^k is a CI/offline metric).
- ❌ editing `llm_judge.py`/`rules_based.py` (harness WRAPS only).
- ❌ changing `loop.py` / `max_turns` (harness drives the loop as-is).

### 3.7 Validation (US-1..US-7)

Gates: mypy `src` 0/380 (harness is `scripts/`, also mypy-clean) · run_all 10/10 · pytest 2843+new (CI-safe unit, no Azure) · Vitest 920 (untouched) · mockup 51 (`diff` empty, untouched) · `npm run lint && npm run build` (NO `--silent`, FE untouched) · black/isort/flake8 clean · LLM-SDK-leak clean (the `_FaultInjectingChatClient` subclasses the ABC, no native import). Plus the §3.x drive-through (MANDATORY — real Azure harness run producing a real verdict).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/scripts/benchmark_pass_k.py` | NEW |
| 2 | `backend/tests/fixtures/observability/pass_k_cases.yaml` | NEW |
| 3 | `backend/tests/unit/scripts/test_benchmark_pass_k.py` | NEW |
| 4 | `claudedocs/4-changes/feature-changes/CHANGE-NNN-passk-reliability-harness.md` | NEW |
| 5 | `docs/03-implementation/agent-harness-planning/<doc-number>-passk-reliability-eval-design.md` | NEW (spike design note) |
| — | `orchestrator_loop/loop.py` · `handler.py` · `event_wire_schema.py` · verifiers · migrations · frontend | **UNTOUCHED** |

## 5. Acceptance Criteria

1. `scripts/benchmark_pass_k.py` loads the corpus, drives `loop.run()` k times/case, computes all 4 axes + per-category, writes MD+JSON.
2. Hybrid oracle: rules-based exact/contains for closed-form cases (deterministic), LLMJudge for open-ended; judge-noise caveat documented.
3. CI-safe unit tests green WITHOUT Azure (importlib + SpyLoop + SpyOracle + seeded rng); real-Azure path behind `@pytest.mark.benchmark` / env gate.
4. `_FaultInjectingChatClient` subclasses `ChatClient` ABC; LLM-SDK-leak lint clean (no native import).
5. **Drive-through PASS (MANDATORY, real Azure)** — a representative real-Azure run (cost-bounded k) exercises ALL 4 axes end-to-end + produces an honest verdict (pass^k vs pass@1 on the multistep cases, either direction); report + observed-vs-intended in progress.md. (Offline harness = the run IS the drive-through, #135/#137/#138 pattern; NOT chat-v2 UI; NOT gate-only.)
6. `AD-Eval-PassK-Reliability-Harness` CLOSED; CHANGE-NNN + spike design note (8-point gate); calibration recorded; navigators + next-phase-candidates updated (research #2 → DONE; next = #5).

## 6. Deliverables

- [ ] US-1 pass^k + pass@1 + divergence over k runs
- [ ] US-2 behavioral consistency (answer + tool-seq) across runs
- [ ] US-3 λ fault-injection degradation
- [ ] US-4 ε perturbation stability
- [ ] US-5 hybrid oracle + difficulty-graded corpus
- [ ] US-6 real-Azure drive-through verdict
- [ ] US-7 CHANGE-NNN + design note + calibration + navigators

## 7. Workload Calibration

- Scope class **NEW `passk-reliability-spike` 0.60** (1st data point; anchor `verification-trace-and-benchmark-spike` 0.60 (57.111) + the #136-139 measurement-harness spikes all 0.60 — same Cat-12/10 greenfield-benchmark-script + golden-fixture + `@pytest.mark.benchmark` shape; set 0.60 NOT higher because the 57.137 lesson holds — a >~3 hr real implementation core (4-axis computation + fault wrapper + corpus + CI tests) holds the spike multiplier; flag the 4-axis breadth as upper-edge risk → if ratio >1.20 re-point toward 0.75).
- **Agent-delegated: no** (parent-direct; harness design + oracle wiring + verdict interpretation are judgment-dense). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~11 hr (harness core+axes ~4.5 / corpus ~1 / oracle+fault wrapper ~1.5 / CI tests ~2 / drive-through ~1.5 / closeout+design-note ~0.5... ≈ recompute Day-4) → class-calibrated commit ~6.5 hr (mult 0.60). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **AP-4 (meaningless report)** — bad oracle / too-easy corpus → numbers lie | rules-based oracle first (zero noise) + corpus MUST include multistep/tool_use difficulty gradient; judge-noise documented (§3.2) |
| **Real-Azure cost** (4 axes × k × N most expensive spike yet) | k configurable; drive-through uses cost-bounded representative run (not full matrix); oracle judge on cheap tier |
| **D-loop-run-noDB** — harness may need DB to drive `loop.run()` | Day-0 Prong-2 resolves; if DB required, use a minimal in-memory message_store or a throwaway session (scope risk flagged) |
| **Risk Class B** (cross-platform mypy `unused-ignore`) | dual ignore code if the late-import / ABC subclass trips it |
| **Risk Class E** (stale backend masks behavior) | drive-through is a fresh `python` harness invocation (no long-running server), so the script loads `.env` + builds a fresh handler each run — clean by construction; still confirm `.env` Azure creds loaded |
| **λ fault randomness vs deterministic tests** | `_FaultInjectingChatClient` takes an injectable `rng` (`random.Random(seed)`) — unit tests deterministic, real run uses unseeded |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- MAST 14-mode failure classifier → `AD-Eval-MAST-Classifier-Phase58`
- persistence-driven cross-tenant pass^k data pipeline (read-back from `message_events`) → `AD-Eval-PassK-Persistence-Pipeline-Phase58`
- wire/UI dashboard for reliability metrics → deferred (YAGNI; CI/offline metric)
- research #5 OTel GenAI schema / #7 tool-desc lint → separate candidates (next per canonical order = #5)
