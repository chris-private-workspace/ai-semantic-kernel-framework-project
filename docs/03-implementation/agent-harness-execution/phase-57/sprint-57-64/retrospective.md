# Sprint 57.64 Retrospective — Chat-Path Keystone Wiring

**Date**: 2026-06-01
**Sprint**: 57.64
**Scope**: Cat 5 PromptBuilder + Cat 3 memory tools + Cat 11 subagent tools (A-3a) injection into the production `real_llm` chat path; no `loop.py` edits
**Status**: Closed (with one deferred item: real_llm live e2e — confirmatory, blocked on out-of-scope A-5 SSE surfacing + Azure cost)

> Modification History
> - 2026-06-01: Initial creation (Sprint 57.64 closeout)

---

## Q1: What was delivered?

- **EDIT** `business_domain/_register_all.py` — `make_default_executor` opt-in deps (memory_retrieval + memory_layers + subagent_dispatcher + parent_session_id, all default None → byte-identical 55.2 registry when absent). Memory deps → `register_builtin_tools(...)` (REAL handlers). Dispatcher → `task_spawn` (FORK/TEAMMATE) + one `agent_researcher` AS_TOOL (HANDOFF excluded). NEW `_adapt_subagent_handler` Cat 11→Cat 2 bridge in the registration layer.
- **EDIT** `api/v1/chat/_category_factories.py` — 3 new LLM-neutral factories: `make_chat_prompt_builder` (Cat 5, keystone), `make_chat_memory_deps` (Cat 3), `make_chat_subagent_dispatcher` (Cat 11).
- **EDIT** `handler.py` — `build_real_llm_handler` injects `prompt_builder=` into `AgentLoopImpl`; threads memory deps + dispatcher + `user_id` into `make_default_executor`.
- **EDIT** `router.py` — thread `user_id`.
- **EDIT** `scripts/lint/check_promptbuilder_usage.py` — path-targeted AST positive check (AP-2 false-green → true-green).
- **EDIT** `17-cross-category-interfaces.md` — `task_spawn` risk_level (SEQUENTIAL/AUTO/MEDIUM); `SubagentResultReducer` resolved as **REUSE** (no new contract).
- **NEW** `test_chat_keystone_wiring.py` — 11 tests (Cat 5 ×3 + Cat 3 ×4 + Cat 11 ×3 + combined ×1).
- Docs: CHANGE-032, progress.md, this retrospective.

**Core thesis validated**: all three activate by api/factory-layer wiring alone — zero `loop.py` churn (every dep is a `is not None`-gated loop param). D3 drift (A-1/A-3a do NOT share `register_builtin_tools`) was caught Day 0 and A-3a budgeted a separate registration call.

## Q2: Estimate accuracy (calibration)

- Scope class: **medium-backend (0.80)**.
- **Agent-delegated: YES** — Day 1 + Day 2 implemented via 2 sequential `code-implementer` agents (≥ 80% of implementation), parent re-verified independently → **`agent_factor` `mechanical-greenfield-design-decisions` 0.65** (new factory + registration design + `SubagentResultReducer` decision = design decisions, not pure port).
- Plan §Workload: bottom-up ~13 hr → class-calibrated commit ~10.5 hr (mult 0.80) → agent-adjusted commit ~6.8 hr (× 0.65).
- **Actual**: NOT cleanly wall-clock-measurable — work spanned multiple interrupted sessions + a `/compact` between Day 2 and Day 3-4 closeout, with agent-delegated Day 1-2 (fast) and parent-direct Day 3-4 docs/test. **Low-confidence estimate** of focused time ≈ 5-8 hr → ratio actual/agent-adjusted ≈ 0.74-1.18 — straddling the `mechanical-greenfield-design-decisions` band, but **flagged low-confidence**; this single data point lacks a clean wall-clock measurement (same caveat as 57.63). **Do NOT use it to adjust 0.65.** See Q7.

## Q3: What went well?

- **Day-0 三-prong paid off (D3)**: caught that `register_builtin_tools` registers memory but NOT subagent tools BEFORE code → A-3a budgeted a separate `make_task_spawn_tool` registration instead of assuming a shared call. No mid-sprint scope surprise.
- **LLM-neutrality held cleanly**: all three factories live in the api layer (receive `ChatClient` ABC); `agent_harness/**` stayed SDK-free; `check_llm_sdk_leak` green throughout. The `_adapt_subagent_handler` bridge sits in the **registration layer**, keeping Cat 11 / Cat 2 owners decoupled (no cross-category hashing — AP-3).
- **Backward-compat by construction**: opt-in deps default None → the no-deps registry is byte-identical to 55.2 (echo + 18 business tools). Every existing chat test passed unchanged.
- **Agent delegation + independent re-verification**: Day 1 + Day 2 were code-implementer-delegated, but the parent re-ran tests + mypy + lints itself rather than trusting the agent's self-report — caught nothing broken, confirming the delegated output. Staged (Day 1 review → Day 2 review) kept checkpoints.
- **Combined test proves co-existence**: `test_combined_all_three_active_one_run` shows PromptBuilt + memory round-trip + FORK merge in ONE run, not just three isolated tests. Full suite green (**1934 passed / 4 skipped**).
- Closes two structural debts: the keystone AP-8 (no central PromptBuilder on chat path) and the AP-2 false-green lint.

## Q4: What to improve?

- **Flag intended simplifications in the plan, not at review**: three small shortcuts surfaced only at closeout — `TiktokenCounter` hard-codes `gpt-4o` (deployment is gpt-5.2), `make_chat_memory_deps(db)` accepts then discards `db` (session-scope only), and the AS_TOOL wrapper hard-codes a single `agent_researcher` role. These are acceptable for A-3a scope but should have been listed as explicit "known simplifications" in plan §Technical Spec / §Out of Scope so review isn't where they're discovered.
- **Sequence A-5 with keystones for external observability**: the real_llm live leg can't cleanly assert PromptBuilt at the HTTP layer because A-5 (LoopEvent→SSE surfacing) is out of scope — PromptBuilt is an in-process event. A future sequencing should pair the keystone with A-5 so "wired" is externally provable on the real path, not only via the in-process mock test.
- **Keep the re-verification discipline**: independently re-running delegated agents' tests/lints (not trusting self-report) was the right call and should remain standard for all delegated sprints.

## Q5: Anti-pattern audit (11 checks)

- AP-1 (Pipeline-as-Loop): N/A — reused `AgentLoopImpl` while-true; no new loop.
- AP-2 (side-track): ✅ — **closes** the AP-2 false-green lint (`check_promptbuilder_usage` now scans the chat call-site, true-green); all new code reachable from `router.py`.
- AP-3 (cross-dir scatter): ✅ — keystone factories in one `_category_factories.py`; the Cat 11→Cat 2 bridge sits in the registration layer (decoupled), not hashed across category dirs.
- AP-4 (Potemkin): ✅ — **closes** AP-4 instances: Cat 5 was always-fallback, Cat 3/11 absent. Memory uses the REAL handler (`is not memory_placeholder_handler` asserted); HANDOFF (the one remaining hollow stub) is EXCLUDED and kept gated with `HANDOFF_NOT_IMPLEMENTED` tests intact.
- AP-5 (PoC accumulation): N/A.
- AP-6 (hybrid bridge debt): ✅ — opt-in deps + factories serve the one production caller; no speculative abstraction.
- AP-7 (context rot): N/A — Cat 4 compactor injection was 57.63's point.
- AP-8 (no central PromptBuilder): ✅ — **this sprint's keystone CLOSES it**: the chat path now builds prompts through `DefaultPromptBuilder` instead of the naked fallback.
- AP-9 (no verification): N/A — Cat 10 was 57.63.
- AP-10 (mock vs real divergence): ✅ — cross-tenant isolation tested through the REAL memory handler logic (in-memory session scope; composite `(tenant_id, session_id)` key); subagent FORK merge tested through the real dispatcher.
- AP-11 (version suffix): ✅ — no `_v1`/`_v2` names.

## Q6: Carryover ADs

- **AD-Cat5-TiktokenCounter-Model-Hardcode**: `make_chat_prompt_builder` builds `TiktokenCounter(model="gpt-4o")` while the live deployment is gpt-5.2 — token counts may be off. Ties to FIX-024 pricing-config drift; fold into the billing-correctness bundle (B-7/B-8/C-15).
- **AD-Cat3-MemoryDeps-DB-Unused**: `make_chat_memory_deps(db)` accepts `db` then discards it (session-scope only for now). DB-backed scopes (tenant/user/role/system layers) need the `db` wired — future memory-depth sprint.
- **AD-Cat11-ASTool-SingleRole-Hardcode**: the AS_TOOL wrapper exposes a single hard-coded `agent_researcher` role; make role set config-driven in a future Cat 11 sprint.
- **AD-Cat5-3-11-RealLLM-E2E**: the real_llm live leg (PromptBuilt observable on the streaming HTTP path) is deferred — blocked on A-5 (events→SSE) being out of scope; supersedes 57.63's AD-Cat4-7-8-10-RealLLM-E2E for the keystone categories.
- **Remaining Area-A gaps (capstone)**: A-3b Cat 11 HANDOFF (hollow executor — design spike + 8-point design note); A-1 Tier2 (memory auto-inject) + A-2 Tier2 (prompt caching) — both touch `loop.py` → 候選 Sprint B; A-4 loop tracer / A-5 events→SSE / A-6 frontend real-data — independent sprints.
- **FIX-024** (real_llm cost_ledger Δ=0): un-billed gpt-5.2 calls; feeds the billing bundle.

## Q7: Calibration matrix update

- Record 1 data point: scope class `medium-backend` (0.80), `agent_factor = mechanical-greenfield-design-decisions 0.65` (agent-delegated: yes), ratio ≈ 0.74-1.18 **with a low-confidence wall-clock caveat** (multi-session interrupted + `/compact` mid-sprint). **Do NOT adjust the 0.65 sub-class baseline** on this point — measurement quality insufficient (same caveat class as 57.63's `agent_factor=1.0` point).
- Context for the `mechanical-greenfield-design-decisions` 0.65 watch (per `sprint-workflow.md §Active`): prior validations 57.56=1.02 (IN) + 57.57=1.15 (IN) + 57.61=0.74 (BELOW, backend-only) + 57.62=0.77 (BELOW, pair). The `AD-AgentFactor-DesignDecisions-Below-Band-Watch` rule (next clean point < 0.85 → tighten 0.65 → 0.55) needs a **clean** measurement; this caveated point does NOT count toward that trigger. Note as a caveated data point in the matrix `mechanical-greenfield-design-decisions` row.

## Closeout checklist

- [x] Plan + checklist exist (PR #225)
- [x] Day 0 三-prong verify (GO; D1-D8 re-confirmed, D3 drift folded)
- [x] Code: Cat 5 injection (keystone) + Cat 3 memory + Cat 11 A-3a (commits `487432a9` + `1701b4e4`)
- [x] Tests: 11 keystone (Cat 5 ×3 + Cat 3 ×4 + Cat 11 ×3 + combined ×1); full suite **1934 passed / 4 skipped**
- [x] mypy src **0/319** / 9-9 V2 lints green (SDK leak 0; check_promptbuilder_usage true-green)
- [x] progress.md (Day 0-4)
- [x] retrospective.md (this file)
- [x] CHANGE-032
- [x] Area-A capstone update (候選 Sprint A shipped; D3 runtime-confirmed)
- [ ] commit (Day 3+4) + push + PR — user-authorized
- [ ] 🚧 real_llm live e2e — deferred (confirmatory; A-5 out of scope + Azure cost + FIX-024 cost red)

---

(Filled per the Q1-Q7 + closeout structure mirrored from sprint-57-63/retrospective.md.)
