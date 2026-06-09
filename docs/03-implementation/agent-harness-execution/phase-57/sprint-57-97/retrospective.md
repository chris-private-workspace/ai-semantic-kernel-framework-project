# Sprint 57.97 Retrospective — Multi-model profile (cheap tier for verification)

**Plan**: [`sprint-57-97-plan.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-97-plan.md)
**Progress**: [`progress.md`](./progress.md)
**Change record**: `claudedocs/4-changes/feature-changes/CHANGE-064-multi-model-profile-verification.md`
**Design note**: `docs/03-implementation/agent-harness-planning/24-multi-model-profile-design.md`
**Dates**: 2026-06-09 (Day 0-3) ~ 2026-06-10 (Day 4 closeout)

---

## Q1. What did we deliver? (US-1..US-5)

| US | Deliverable | Status |
|----|-------------|--------|
| US-1 | thin provider-neutral `ModelProfile{action, cheap}` value object (`adapters/_base/model_profile.py`) + re-export + 17.md registration | ✅ |
| US-2 | `build_azure_model_profile` cheap builder + `AZURE_OPENAI_CHEAP_*` env + byte-identical unset-fallback + `.env.example` | ✅ |
| US-3 | verification (llm_judge) ← `profile.cheap`; loop + compactor + prompt + subagents ← `profile.action`; `loop.py` diff = 0 | ✅ |
| US-4 | cost attributed to cheap model (via `config/llm_pricing.yml` + `response.model` capture); `check_llm_sdk_leak` 0 | ✅ |
| US-5 | **drive-through PASS** — real Azure, verification on gpt-5.4-mini ~62% cheaper, cost_ledger-proven | ✅ |

Gate: mypy 0/353 · run_all 10/10 · black/isort/flake8 clean · pytest 2291 passed / 4 skipped (baseline 2283 → **+8**, 0 deletions).

## Q2. Estimate accuracy / calibration

- **Scope class**: `multi-model-profile-spike` (NEW, 0.55 mid-band) — **1st data point**.
- **Agent-delegated**: **no** (parent-direct — the cost-attribution correctness + the real-money drive-through cost-delta assertion are parent verification work) → `agent_factor = 1.0`; does NOT extend the agent-delegation streak.
- **Bottom-up est ~14 hr → class-calibrated commit ~7.5 hr (mult 0.55).**
- **Actual ≈ 7 hr** (estimated — not rigorously per-day-tracked, same caveat as Sprint 57.13/57.27; Day 3 drive-through absorbed an unplanned ~1 hr Risk-Class-E orphaned-worker hunt offset against thin code + thin tests).
- **Ratio actual/committed ≈ 0.93** ✅ in [0.85, 1.20] band. **Ratio actual/bottom-up ≈ 0.50** (bottom-up ~2× generous; the 0.55 multiplier landed within ~5%).
- **Verdict**: KEEP `multi-model-profile-spike` 0.55 baseline per `When to adjust` 3-sprint window rule (1-data-point insufficient for adjustment). Pending 2-3 sprint validation.

## Q3. What went well

- **Day-0 recon collapsed the scope correctly**: the Explore recon (file:line anchors) confirmed the seam was a construction-time DI swap, not an ABC change → `loop.py` diff = 0, no event/DB/migration. The premise "model is per-construction not per-call" was verified before any code (`chat_client.py:69-93` has no `model=` param).
- **D-DAY1-1 caught a footgun before it shipped**: the plan proposed `AZURE_OPENAI_CHEAP_PRICING_*` env vars; Day-1 content-grep revealed the cost-ledger prices via `config/llm_pricing.yml` (model-keyed), NOT the adapter config pricing — so those env vars would have been a silent no-op. Dropped them (Karpathy §2); anchored the drive-through proof on the cost_ledger sub_type model-attribution instead.
- **The fallback design (`cheap is action`)** made the feature safe to ship without a 2nd deployment + gave a clean soft-rollback path + a trivially testable identity invariant.
- **Drive-through delivered a real, quantified saving** (~62% cheaper verification, cost_ledger-proven) — not a paper claim.

## Q4. What to improve / lessons (carryover ADs)

- **Risk Class E is more insidious than documented** (D-DAY3-1): an orphaned `multiprocessing.spawn` `--reload` worker (child of a long-dead reloader) kept serving :8000 with old code + old env, and port-owner-based kills (`dev.py`/netstat/`taskkill /PID`) all missed it because the socket was attributed to the dead parent and the worker cmdline lacks "uvicorn". **Folded into `sprint-workflow.md §Risk Class E`** (the reliable check is `Get-CimInstance Win32_Process -Filter "Name='python.exe'"` by PID/PPID/StartTime, then `Stop-Process -Force` the orphans). This cost ~1 hr of false "the cheap routing is broken" debugging before the reproduce-script proved the code correct.
- **Carryover ADs (Open Invariants → `next-phase-candidates.md`)**: compaction/memory/thinking cheap-tier (the seam is built, follow-on adds a field); threading `ModelProfile` into the loop; per-tenant model policy (Config 分層, cc-parity §7.3); cheap-judge accuracy benchmark; non-Azure cheap-tier builders.

## Q5. Anti-Pattern Audit (11 points)
- AP-1 (pipeline-as-loop): N/A — no loop change (`loop.py` diff = 0).
- AP-2 (side-track): ✅ — `ModelProfile` is consumed on the main `build_real_llm_handler` path (traceable from the chat API).
- AP-3 (cross-dir scatter): ✅ — `ModelProfile` in `adapters/_base/` (home of `ChatClient`); builder in `adapters/azure_openai/`; wiring in `api/v1/chat/handler.py`. The value object PREVENTS scatter for future tiers.
- AP-4 (Potemkin): ✅ — real cost routing, drive-through-proven (cost_ledger sub_type shows the cheap model); not a stub.
- AP-5/6 (PoC accumulation / hybrid-bridge debt): ✅ — thin value object for a real current consumer; no speculative dispatcher (YAGNI).
- AP-7 (context rot): N/A.
- AP-8 (no central PromptBuilder): N/A.
- AP-9 (no verification): N/A (this sprint MOVES verification to a cheaper tier; it stays default-ON).
- AP-10 (mock vs real divergence): ✅ — the unset-fallback (`cheap is action`) means dev (no cheap deployment) and prod (cheap deployment) share the exact same code path; tests cover both.
- AP-11 (version suffix): ✅ — no `_v1`/`_v2` names.

## Q6. Design Note Extract (spike sprint — MANDATORY per Step 5.5)

**File**: `docs/03-implementation/agent-harness-planning/24-multi-model-profile-design.md`
**Verified ratio (estimated)**: ≥ 95% (every claim file:line-anchored; the only non-verified content is the fenced §4 Open Invariants).
**8-Point Quality Gate**:
- [x] 1. Section headers map to US-1..US-5
- [x] 2. file:line references for every claim
- [x] 3. Decision matrix (4-row: per-call / ABC-wrapper / thin value object / direct injection)
- [x] 4. Verification commands (pytest paths + drive-through reproduce step)
- [x] 5. Test fixture references (monkeypatch.setenv / cast placeholders / artifact PNG)
- [x] 6. Open invariants fenced from verified (§4)
- [x] 7. Rollback path (soft = unset env; hard = revert ~30 min)
- [x] 8. 17.md cross-ref (`ModelProfile` registered §2.1; `ChatClient` ABC unchanged)

**Reviewer pass**: self-review (solo-dev).

## Q7. Risk register review (vs plan §8)
- Cheap deployment availability → ✅ user provided gpt-5.4-mini.
- Cost computed centrally (mis-priced cheap judge) → resolved by D-DAY1-1 (yml-keyed + `response.model` capture; no wiring needed).
- Per-call model not observable → cost-ledger sub_type sufficient; span attr deferred (Open Invariant).
- Fallback not byte-identical → tested (`cheap is action` identity).
- Neutrality / SDK leak → `check_llm_sdk_leak` 0.
- **Risk Class E** → MATERIALIZED (D-DAY3-1); reinforced rule + lesson logged.

## Carryover (→ `claudedocs/1-planning/next-phase-candidates.md`)
1. Compaction cheap-tier (highest token-volume; needs long-conversation drive-through)
2. Memory-extraction cheap-tier
3. Thinking cheap-tier
4. Thread `ModelProfile` into the loop (in-loop per-phase selection)
5. Per-tenant model policy (Config 分層, cc-parity §7.3)
6. Cheap-judge accuracy benchmark
7. Non-Azure cheap-tier builder (Anthropic/OpenAI)

## Modification History
- 2026-06-10: Initial creation (Sprint 57.97 Day 4 closeout)
