# Sprint 57.154 Plan — A/B-measure combined-formation quality vs two focused calls

**Summary**: Sprint 57.152 combined the two post-send cheap-tier memory-formation calls (57.149 extract + 57.151 summarize) into ONE `chat()` via `MemoryFormationWorker`, shipping `chat_memory_combined_formation` default ON on the drive-through + the two-call env fallback alone. This sprint closes the 57.152 carryover `AD-Memory-Combined-Formation-AB-Quality` with the missing evidence: a real-Azure A/B harness measuring whether the combined prompt DEGRADES either half's quality (extracted user facts + session summary) vs the two focused separate calls. Key scope decision (user-picked via AskUserQuestion): a **Hybrid oracle** — deterministic keyword-coverage for facts + an LLM-judge for summary faithfulness (mirrors 57.141 hybrid + 57.138/153 judge). Backend-only measurement spike, ZERO src change baseline (drives the REAL `MemoryFormationWorker.form()` combined=True/False via capturing sinks — AP-10 safe); the only contingent src change is flipping the config default IF the A/B shows material quality regression (unlikely — 57.152 drive-through already proved the combined path forms both halves). NO user-facing surface → the real-Azure A/B IS the real-LLM verification (not gate-only); a design note (8-point gate) IS required (spike sprint).

**Status**: Approved-to-execute (user-picked `AD-Memory-Combined-Formation-AB-Quality` from the 57.153 closeout candidate list 2026-07-01; oracle methodology = Hybrid via AskUserQuestion 2026-07-01)
**Branch**: `feature/sprint-57-154-combined-formation-quality-ab`
**Base**: `main` HEAD `a0cf503a` (chore: flip Sprint 57.153 PR-pending → MERGED, PR #361)
**Slice**: closes `AD-Memory-Combined-Formation-AB-Quality` (57.152 carryover; the memory-formation arc's efficiency-validation slice — the arc 57.148→152 is functionally closed, this settles the combined-vs-separate quality question with numbers)
**Scope decisions**: (a) Hybrid oracle — deterministic facts coverage + LLM-judge summary faithfulness; (b) drive the REAL worker via capturing UserLayer/SummaryStore sinks (AP-10 safe, zero src change) NOT a re-implemented prompt; (c) two-sided verdict = KEEP combined default ON iff it does NOT materially regress facts-coverage OR summary-score vs separate (the efficiency win was established 57.152; the A/B only needs to prove no quality loss); (d) self-contained summary judge in the harness (NOT a new production `verification/templates/` file) to avoid an orphan production-selectable template.

---

## 0. Background

### The gap (`AD-Memory-Combined-Formation-AB-Quality`)

Sprint 57.152 shipped `MemoryFormationWorker` — one combined cheap-tier `chat()` returning both the durable-facts array AND the session-summary object — default ON, halving the per-send background token + latency vs the two focused 57.149/57.151 calls. But the 57.152 carryover notes the decision rested on the flag + a single drive-through: **no numbers proving the combined prompt does not DEGRADE either half's quality** vs asking each half in its own focused call.

### Why it matters (the missing capability)

Combining two focused prompts into one structured-JSON request is a classic quality-vs-cost trade: the model splits attention across two tasks, and the shared prompt is longer. If the combined prompt materially lowers fact coverage (misses durable facts a focused extractor would catch) or produces a shallower/less-faithful summary, the ~2× efficiency win is not worth it and the default should flip to the proven two-call path. Today that trade is unmeasured — an evidence gap on a default-ON path that runs after every chat send.

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `a0cf503a`) | Anchor |
|-------|--------------------------------------|--------|
| combined arm | ONE `chat()` over a shared prompt asking `facts[]` + `summary`/`key_decisions`/`unresolved_issues` | `memory/formation.py:151` `_form_combined` + `:221` `_build_prompt` |
| separate arm (facts) | a focused `chat()` asking only a `[{content,confidence}]` array | `memory/extraction.py:80` `extract_session_to_user` + `:55` `_EXTRACTION_PROMPT` |
| separate arm (summary) | a focused `chat()` asking only `{summary,key_decisions,unresolved_issues}` | `memory/session_summarizer.py:90` `summarize_and_store` + `:58` `_SUMMARY_PROMPT` |
| write sink (both arms) | `write_facts` → `UserLayer.write`; `store_summary` → `DBSessionSummaryStore.upsert_summary` | `extraction.py:116` / `session_summarizer.py:117` |
| the switch | `MemoryFormationWorker(..., combined=True/False)` selects the arm; nothing measures the delta | `formation.py:102` ctor `combined` |

→ The fix is a measurement harness that drives BOTH arms through the REAL worker (only capturing the terminal write) over a golden corpus, scores each arm's captured facts + summary with a Hybrid oracle, and emits a two-sided KEEP/FLIP verdict.

### The design (backend-only measurement spike: 1 harness + 1 corpus + 1 test file; zero src change baseline)

```
# Drive the REAL production formation path per arm; capture (not persist) the output; score it.
for case in corpus:
    worker_A = MemoryFormationWorker(cheap_client,
                 extractor=MemoryExtractor(cheap_client, CapturingUserLayer()),
                 summarizer=SessionSummarizer(cheap_client, CapturingSummaryStore()),
                 combined=True)                     # Arm A
    await worker_A.form(messages=case.conversation, session_id, tenant_id, user_id, known_facts=None)
    facts_A, summary_A = capturing sinks' recorded outputs
    # Arm B: identical but combined=False (the two-call path)

    facts_score  = deterministic keyword-coverage(emitted, case.expected_facts)   # rules half
    summary_score = llm_judge(case.conversation, summary_obj)                       # judge half (Hybrid)

report = two_sided_verdict(combined_scores, separate_scores)   # KEEP default ON iff no material regression
```

Why capturing sinks over reaching into private `_build_prompt`/`_parse_combined`: driving `form()` end-to-end (build → chat → parse → dispatch) with only the DB write swapped keeps the harness byte-faithful to production (AP-10 — no divergent re-implementation), and needs ZERO src change. Why a self-contained summary judge over reusing `LLMJudgeVerifier`: the production judge scores an agent OUTPUT against a trace-state; a summary-faithfulness rubric is a different shape, and adding a `summary_faithfulness.txt` to `verification/templates/` would create a production-selectable template no production path uses (orphan smell). The harness is under `backend/scripts/` (outside the AP-8 lint root + the templates dir) so a self-contained rubric via the ChatClient ABC is the honest, neutral fit.

### Ground truth (recon head-start — code read on `main` HEAD `a0cf503a`; ALL re-verified §checklist 0.1)

- `formation.py:115` `form(*, messages, session_id, tenant_id, user_id, known_facts, trace_context)` — the single entry both arms share; `combined` ctor flag picks `_form_combined` vs `_form_separate`.
- `formation.py:161` `_form_combined` gates `want_facts = extractor is not None and user_id is not None`; `want_summary = summarizer is not None` → the harness must wire BOTH collaborators + pass a non-None `user_id`.
- `extraction.py:145` `UserLayer.write(content=, tenant_id=, user_id=, time_scale=, confidence=, source=, trace_context=) -> UUID` — the capture seam for facts.
- `session_summarizer.py:134` `DBSessionSummaryStore.upsert_summary(session_id=, summary=, key_decisions=, unresolved_issues=)` — the capture seam for the summary.
- Both arms parse tolerantly (first JSON substring) → the harness scores whatever the worker actually captured, mirroring production exactly.
- 57.153 sibling `backend/scripts/benchmark_memory_grounded_judge.py` — the exact scaffold to mirror (dataclasses / `load_cases` / `run_arm` / `build_report` two-sided / `report_to_markdown` / lazy-Azure `_amain` / UTF-8 `main`).

**Baselines (57.153 closeout)**: pytest 3082 · wire 26 · Vitest 922 · mockup 51 · mypy 0/397 · run_all 11/11. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-fixture-dir** — grep/ls `backend/tests/fixtures/memory/` exists (else create); the 57.153 corpus lives under `tests/fixtures/verification/` — confirm the memory-formation corpus home.
- **D-capture-signatures** — read `UserLayer.write` + `DBSessionSummaryStore.upsert_summary` real signatures to build faithful capturing doubles (keyword args must match exactly).
- **D-ap8-scope** — confirm `backend/scripts/` is OUTSIDE the AP-8 lint root (57.153 D-ap8-harness established this) → no allowlist for the self-contained summary judge.
- **D-cheap-profile** — confirm `build_azure_model_profile().cheap` is the ChatClient the sibling harnesses use for the on-demand real run.
- **D-test-scripts-dir** — confirm `backend/tests/unit/scripts/` is the CI-safe home + the importlib-shadow pattern the sibling test uses.
- **D-change-designnote-free** — `CHANGE-121` + design note `57-*` are the next free numbers (120 / 56 highest).

## 1. Sprint Goal

Produce a real-Azure A/B verdict — with a permanent, CI-safe, importable harness + a difficulty-graded golden corpus — on whether `MemoryFormationWorker`'s combined single-call formation materially degrades either the extracted-facts quality (deterministic keyword coverage) or the session-summary quality (LLM-judge faithfulness) vs the two focused separate calls, and act on it: KEEP `chat_memory_combined_formation` default ON if there is no material regression, or flip the default to the proven two-call path if there is. Proven by: green gates (mypy/pytest/run_all/lint) on the harness + tests, and a real-Azure run of the REAL production formation path over the corpus emitting the A/B report (real LLM — NOT gate-only). Produces CHANGE-121 + design note `57-memory-combined-formation-quality-ab-design.md` (spike sprint, 8-point gate).

## 2. User Stories

- **US-1** (harness core): 作為 platform 維護者，我希望有一個可匯入、CI-safe 的 A/B harness 能用真 production 的 `MemoryFormationWorker.form()` 分別跑 combined 與 separate 兩臂並攔截其輸出，以便在不寫 DB、不重寫 prompt 的前提下忠實量測兩臂品質。
- **US-2** (Hybrid oracle + corpus): 作為 platform 維護者，我希望有確定性的 facts 覆蓋率評分 + LLM-judge 的 summary 忠實度評分，配上一份難度分級的黃金語料，以便「品質退化」有可量測、可重現的定義。
- **US-3** (two-sided verdict + tests): 作為 platform 維護者，我希望 harness 產出 two-sided KEEP/FLIP verdict 並有 ~13 個 spy-client CI 測試，以便 verdict 邏輯被鎖定且無 Azure 依賴即可回歸。
- **US-4** (real-Azure A/B run — real LLM, NOT gate-only): 作為 platform 維護者，我希望用真 Azure cheap-tier 跑完整語料得到 combined-vs-separate 的真實數字與 verdict，以便據此決定 `chat_memory_combined_formation` 的預設值（KEEP ON 或 flip）。
- **US-5** (closeout): 作為 platform 維護者，我希望 CHANGE-121 + design note 57 + retrospective + navigators 完成並關閉該 AD，以便下個 sprint 有乾淨基線。

## 3. Technical Specifications

### 3.0 Architecture (backend-only; NO migration / wire / frontend / loop.py; zero src change baseline)

```
NEW  backend/scripts/benchmark_combined_formation_quality.py    # A/B harness (mirror benchmark_memory_grounded_judge.py)
NEW  backend/tests/fixtures/memory/memory_formation_quality_cases.yaml   # ~10 difficulty-graded cases
NEW  backend/tests/unit/scripts/test_benchmark_combined_formation_quality.py  # ~13 CI-safe (spy client + capturing doubles)
EDIT (CONTINGENT ONLY) backend/src/core/config/__init__.py      # flip chat_memory_combined_formation default IF A/B shows material regression
UNTOUCHED  memory/formation.py · extraction.py · session_summarizer.py · loop.py · handler.py · router.py · migrations · wire(26) · frontend
```

### 3.1 Harness core (US-1) — `backend/scripts/benchmark_combined_formation_quality.py`

- Mirror the 57.153 scaffold: `@dataclass FormationCase` (id, conversation `list[{role,content}]`, expected_facts `list[list[str]]` keyword-groups, expected_summary_points `list[str]`, expects_facts `bool`), `@dataclass ArmScore` (arm, facts_coverage, facts_spurious_count, summary_score, n_facts_emitted, n_summary_stored), `@dataclass FormationReport` (per-arm means + deltas + `combined_recommended`).
- `load_cases(path)` — parse + schema-validate the golden YAML (dup-id guard, required keys, `expected` list types) — mirror `load_cases`.
- Capturing doubles: `_CapturingUserLayer.write(**kwargs) -> UUID` (record `(content, confidence)`, return `uuid4()`) + `_CapturingSummaryStore.upsert_summary(**kwargs)` (record the summary dict). Signatures match the real seams exactly (verified Day-0 D-capture-signatures).
- `run_arm(arm, cases, *, chat_client, judge_client)` — per case build a `MemoryFormationWorker(chat_client, extractor=MemoryExtractor(chat_client, CapturingUserLayer()), summarizer=SessionSummarizer(chat_client, CapturingSummaryStore()), combined=(arm=="combined"))`, `await worker.form(messages=…, session_id=uuid4(), tenant_id=uuid4(), user_id=uuid4(), known_facts=None)`, read the captured facts + summary, score with the oracle → aggregate an `ArmScore`.

### 3.2 Hybrid oracle + corpus (US-2)

- **facts (deterministic)** — `score_facts(emitted_contents, expected_keyword_groups) -> (coverage, spurious_count)`: `coverage` = fraction of expected groups where some emitted fact (normalized lower/whitespace) contains ALL the group's keywords; `spurious_count` = emitted facts matching NO expected group (a secondary signal, chiefly for `expects_facts: false` cases — the combined prompt must not hallucinate facts the focused extractor would not).
- **summary (LLM judge — Hybrid)** — `score_summary(judge_client, conversation, summary_obj) -> float` in `[0,1]`: a self-contained rubric prompt via the ChatClient ABC (cheap tier) asking the judge to score the summary's faithfulness + coverage of the conversation's topic/decisions/open-issues against `expected_summary_points`; tolerant numeric parse (0.0 on unparseable). Provider-neutral (ChatClient ABC only). CI: the spy judge returns scripted scores.
- **corpus** `memory_formation_quality_cases.yaml` — ~10 cases graded: clear multi-fact technical convos (name + stack + decisions), subtle/implicit-fact convos, a 0-durable-fact convo (arithmetic/chit-chat → tests spurious rate), a decisions-heavy convo (tests summary `key_decisions` capture), a long multi-turn convo (tests attention-split under load).

### 3.3 Two-sided verdict + tests (US-3)

- `build_report(combined, separate)` — `facts_coverage_delta = combined − separate`; `summary_score_delta = combined − separate`; `combined_recommended` = combined does NOT materially regress on EITHER axis (`facts_coverage_delta ≥ −Δ` AND `summary_score_delta ≥ −Δ`) AND does not materially inflate spurious facts (`spurious_delta ≤ +Δ_count`). `MATERIALITY_DELTA = 0.05` (mirror the sibling). The efficiency win was established 57.152 → the A/B's job is only to prove no material quality loss (no "improvement" axis needed).
- `report_to_markdown` + JSON dump to `benchmark_reports/` + lazy-Azure `_amain` + UTF-8 `main` — mirror the sibling.
- `test_benchmark_combined_formation_quality.py` (~13): `load_cases` happy/dup-id/missing-key/bad-type; `score_facts` full-coverage / partial / spurious; `score_summary` parse tolerance (spy); `run_arm` drives the real worker with a spy ChatClient + capturing doubles (asserts combined = 1 call, separate = 2 calls — the efficiency invariant); `build_report` two-sided verdict (no-regression → KEEP; facts-regression → FLIP; summary-regression → FLIP).

### 3.x What is explicitly NOT done

- NOT reusing `LLMJudgeVerifier` for the summary (would need an orphan production template) — self-contained rubric instead (§Scope decision d).
- NOT persisting to DB / touching `UserLayer` / `DBSessionSummaryStore` real impls — capturing doubles only.
- NOT changing `formation.py` / the two workers / the prompts — the A/B measures the SHIPPED prompts as-is.
- NOT flipping the config default unless the real-Azure A/B shows material regression (contingent, unlikely).
- NOT a chat-v2 UI drive-through (no new user-facing surface) — UNLESS the verdict flips the default (then a separate-path chat-v2 drive-through is added to confirm the two-call path still forms memory).

### 3.y Validation (US-1..US-5)

Gates: mypy `src` 0/397 · run_all 11/11 · pytest 3082 + ~13 · Vitest 922 (untouched) · mockup 51 (untouched) · black/isort/flake8 clean · LLM-SDK-leak clean. Plus the §3.2/US-4 real-Azure A/B run of the REAL production formation path (real LLM — the pure-backend equivalent of a drive-through; explicitly NOT gate-only).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/scripts/benchmark_combined_formation_quality.py` | NEW |
| 2 | `backend/tests/fixtures/memory/memory_formation_quality_cases.yaml` | NEW |
| 3 | `backend/tests/unit/scripts/test_benchmark_combined_formation_quality.py` | NEW |
| 4 | `backend/src/core/config/__init__.py` | EDIT **(CONTINGENT — only if A/B shows material regression → flip default)** |
| 5 | `claudedocs/4-changes/feature-changes/CHANGE-121-combined-formation-quality-ab.md` | NEW |
| 6 | `docs/03-implementation/agent-harness-planning/57-memory-combined-formation-quality-ab-design.md` | NEW (design note, 8-point gate) |
| — | `memory/formation.py` · `extraction.py` · `session_summarizer.py` · `loop.py` · `handler.py` · `router.py` · migrations · wire · frontend | **UNTOUCHED** |

## 5. Acceptance Criteria

1. The harness runs both arms through the REAL `MemoryFormationWorker.form()` (combined=True/False) capturing — not persisting — facts + summary; a unit test proves combined = 1 `chat()` call, separate = 2 (the efficiency invariant).
2. The Hybrid oracle scores facts (deterministic coverage + spurious count) + summary (LLM-judge faithfulness `[0,1]`) over a ~10-case difficulty-graded corpus.
3. `build_report` emits a two-sided KEEP/FLIP verdict; ~13 CI-safe spy tests lock the load / score / run / verdict logic (no Azure).
4. **Real-Azure A/B run (real LLM, real production formation path — NOT gate-only)** — combined-vs-separate numbers + verdict written to `benchmark_reports/`; the config default is set per the verdict (KEEP ON if no material regression). Report + observed-vs-intended in progress.md. (If the verdict FLIPS the default → add a chat-v2 drive-through of the separate path.)
5. `AD-Memory-Combined-Formation-AB-Quality` CLOSED; CHANGE-121 + design note 57 (8-point gate); calibration recorded (`memory-formation-combine-ab-spike` 0.60, 1st data point); navigators + next-phase-candidates updated.

## 6. Deliverables

- [ ] US-1 harness core (dataclasses + load_cases + capturing doubles + run_arm driving the real worker)
- [ ] US-2 Hybrid oracle (deterministic facts + LLM-judge summary) + ~10-case golden corpus
- [ ] US-3 two-sided `build_report` + `report_to_markdown` + ~13 CI-safe spy tests
- [ ] US-4 real-Azure A/B run + verdict + config default set per verdict
- [ ] US-5 CHANGE-121 + design note 57 + retrospective + navigators + AD closed

## 7. Workload Calibration

- Scope class **`memory-formation-combine-ab-spike` 0.60 (NEW class, 1st data point)** — a real-Azure A/B measurement-harness spike; anchored to `verification-context-hygiene-spike` 0.60 (57.136) + `verification-keycondition-spike` 0.60 (57.138) + `layered-compaction-spike` 0.60 (57.139) + the sibling `memory-formation-combine-spike` 0.60 (57.152). Same shape: a bounded harness + real-Azure A/B + golden fixture + CI-safe tests + a real-code core (harness ~280 lines + capturing doubles + Hybrid oracle + 10-case corpus + ~13 tests ≥~3.5 hr) that holds the 0.60 per the 57.137 lesson (a >~3 hr real implementation core holds the spike multiplier — NOT a tiny-code 0.85 re-point).
- **Agent-delegated: no** (parent-direct — the oracle design + verdict-logic nuance + honest-finding interpretation are best done parent-direct, as every benchmark sibling was). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~6.5 hr (harness ~2 · corpus ~1 · tests ~1.5 · real-Azure run + verdict ~1 · design note + closeout ~1) → class-calibrated commit ~3.9 hr (mult 0.60). Day-4 retro Q2 verifies; if ratio > 1.20 re-point toward 0.75 (the real-Azure staging + oracle-tuning is the variance risk).

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Oracle not discriminating enough to detect real degradation (facts coverage too coarse; summary judge too lenient) | Difficulty-graded corpus (clear / subtle / 0-fact / decisions-heavy / long); validate the oracle on the spy corpus (a scripted worse arm must score lower); report per-case scores in the design note for auditability |
| AP-10 Mock-vs-Real divergence (harness re-implements the prompt → measures the wrong thing) | Drive the REAL `MemoryFormationWorker.form()` + the two real workers; capture ONLY the terminal DB write (the sinks are the sole doubles); prompts/parse are production code |
| Real-Azure run non-determinism (single-run verdict variance) | `temperature=0.0` (formation is deterministic-ish); accept single-run verdicts as the sibling harnesses do; note run count in the report |
| Risk Class E (stale backend masks the run) — LOW here | The harness is a standalone script building its own Azure profile (no running-backend dependency); no `--reload` process involved. Just needs Azure env + a fresh `python scripts/…` invocation |
| Capturing-double signature drift vs the real seams | Day-0 D-capture-signatures reads `UserLayer.write` + `DBSessionSummaryStore.upsert_summary` real signatures before writing the doubles |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- Per-tenant combined/separate override — `AD-Memory-Combined-Formation-PerTenant-Phase58` (C3 config-tiering seam).
- A chat-v2 Inspector surface for "which formation path ran this send" — Phase58 observability carryover.
- Semantic near-dup dedup of the extracted facts (CARRY-026) — a different axis (57.150 shipped exact-normalized dedup).
- Extending the A/B to weaker models / harder corpora (the reflection-family caveat) — a follow-on if the strong-model verdict is inconclusive.
