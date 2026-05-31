# Sprint 57.63 Plan — Production Chat-Path Category Activation (Cat 4 / 7 / 8 / 10)

**Purpose**: Wire the currently-Potemkin optional categories (Cat 4 Compaction, Cat 7 State/Checkpoint, Cat 8 Error/Retry) into the production `real_llm` chat path by injecting their dependencies into `build_real_llm_handler`, and make Cat 10 Verification substantive (currently default-disabled + no-op verifier). Prove each fires on the main flow via integration tests; validate with a `real_llm` e2e run.
**Category / Scope**: Cat 4 + Cat 7 + Cat 8 + Cat 10 activation on api/v1/chat boundary; Phase 57.63
**Created**: 2026-05-31
**Status**: Draft (pending user scope approval; code execution gated)
**Source**: `claudedocs/5-status/breadth-probe-20260531.md` §4 + §6 (handler-injection probe — committed `4d6e6d35`)

> **Modification History**
> - 2026-05-31: Initial creation — derived from breadth-probe §4.2 (production chat path activates only Cat 1/2/6/9/HITL; Cat 4/5/7/8 not injected, Cat 10 inert by default).

---

## 0. Background

The breadth probe (`breadth-probe-20260531.md` §4) confirmed via line-anchored evidence that `AgentLoopImpl.__init__` (`backend/src/agent_harness/orchestrator_loop/loop.py:184-263`) exposes every cross-category dependency as a keyword param defaulting to `None` (inactive when None), but the production chat handler `build_real_llm_handler` (`backend/src/api/v1/chat/handler.py:177-187`) injects only `chat_client / output_parser / tool_executor / tool_registry / system_prompt / max_turns / hitl_manager / guardrail_engine`. Result on the real chat flow:

- **Active**: Cat 1 (loop), Cat 2 (tools), Cat 6 (parser), Cat 9 (guardrail engine), HITL.
- **Potemkin / inactive**: Cat 4 compaction (loop.py:847 no-op), Cat 7 state/checkpoint (loop.py:994/1373/1381 skipped), Cat 8 error/retry (`_handle_tool_error` never fires), Cat 9 tripwire/audit/capability, Cat 12 loop-tracer (NoOpTracer).
- **Cat 10**: `run_with_verification` wrapper is always invoked (router.py:333) but `chat_verification_mode` defaults to `"disabled"` → transparent pass-through, and even `"enabled"` ships a no-op `RulesBasedVerifier(rules=[])`.

Loop integration for Cat 4/7/8/10 already exists and is gated on `is not None` — **injection alone activates them; no loop.py edits are needed** (Cat 11 HANDOFF is the exception and is OUT of this sprint — see `claudedocs/1-planning/cat11-handoff-scope-analysis-20260531.md`).

---

## 1. Sprint Goal

Activate Cat 4 / 7 / 8 on the production `real_llm` chat path by injecting their dependencies into `build_real_llm_handler`, and make Cat 10 verification substantive (enable mode + register a real verifier), with integration tests proving each category fires on the chat SSE flow (closing the Potemkin gap) and a `real_llm` e2e proving the activated flow end-to-end. LLM-provider neutrality preserved: all deps constructed at the api/adapter layer; `agent_harness/**` stays SDK-import-clean.

---

## 2. User Stories

- **US-1 (Cat 7 State/Checkpoint)** — As an operator, I want agent state checkpointed per turn on the production chat path, so conversations are durable/auditable. → inject `DefaultReducer()` + `DBCheckpointer(db, session_id=, tenant_id=)` (+ tenant_id).
- **US-2 (Cat 4 Compaction)** — As a platform owner, I want context compaction active on the chat path, so long conversations don't degrade (context rot, AP-7). → inject a `HybridCompactor`.
- **US-3 (Cat 8 Error/Retry)** — As an SRE, I want tool errors classified / retried / circuit-broken / budget-tracked on the chat path, so transient failures self-heal and runaway tenants are capped. → inject `DefaultErrorPolicy` + `RetryPolicyMatrix` + `DefaultCircuitBreaker` + `TenantErrorBudget` + `DefaultErrorTerminator`.
- **US-4 (Cat 10 Verification)** — As a quality owner, I want output verification active on the chat path with a substantive verifier. → enable `chat_verification_mode` + register a real `LLMJudgeVerifier` in `_verifier_factory`.
- **US-5 (Validation)** — As a reviewer, I want integration tests proving each category fires on the chat SSE path (+ multi-tenant scoping) and a `real_llm` e2e proving the activated flow, so "11+1 Level 4" is true at runtime, not just in isolated tests.

---

## 3. Technical Specifications

### 3.0 Dependency + ordering plumbing (prerequisite for US-1/3)
- Thread `tenant_id: UUID`, `db: AsyncSession`, `session_id: UUID` from `router.py` → `build_handler` (`handler.py:190-197`) → `build_real_llm_handler` (`handler.py:139-144`). None currently accept these.
- **Ordering fix**: `session_id` is generated at `router.py:219`, AFTER `build_handler` is called at `router.py:202`. The Checkpointer binding needs `session_id` → move `session_id` generation BEFORE `build_handler`, then pass it in. (Risk Class — see §8.)
- Available in router request scope (`router.py:131-142`, all `Depends`): `current_tenant`, `current_user`, `factory: ServiceFactory`, `db: AsyncSession`, `tracer`. `db` already threaded to `_stream_loop_events` (router.py:281/307).
- **No default factories exist** for Cat 4/7/8/10-verifier (all hand-constructed in tests). Add a single `backend/src/api/v1/chat/_category_factories.py` (api layer) to construct these from the adapter `ChatClient` + db + tenant_id + session_id (KISS; single responsibility). LLM-neutral: the adapter is passed as `ChatClient` ABC; no SDK import in `agent_harness/**`.

### 3.1 Cat 7 (US-1)
- `DefaultReducer()` — `state_mgmt/reducer.py:69`, zero deps.
- `DBCheckpointer(db_session, *, session_id, tenant_id)` — `state_mgmt/checkpointer.py:94,107`; DB-backed (`append_snapshot` + `StateSnapshot` ORM). One instance per (session, tenant).
- **All-or-nothing**: reducer + checkpointer + tenant_id must ALL be passed or the loop's Cat 7 path is no-op (loop.py:236-245). 17.md §2.1 Contracts: Reducer L134, Checkpointer L133.

### 3.2 Cat 4 (US-2)
- `HybridCompactor(*, structural: StructuralCompactor, semantic: SemanticCompactor, token_budget=100_000, token_threshold_ratio=0.75)` — `context_mgmt/compactor/hybrid.py:59`. ABC `_abc.py:47`; 17.md §2.1 Compactor L125.
- `SemanticCompactor` needs a `ChatClient` (LLM-neutral). `StructuralCompactor` rule-based.
- Token counting is real: `AzureOpenAIAdapter.count_tokens` (`adapters/azure_openai/adapter.py:341-356`, lazy `TiktokenCounter`). Compactor reads `state.transient.token_usage_so_far` (does not itself call count_tokens).
- **Day-0 verify**: exact `StructuralCompactor.__init__` + `SemanticCompactor.__init__` deps (flagged uncaptured in investigation).

### 3.3 Cat 8 (US-3)
- `DefaultErrorPolicy(*, max_attempts=3, backoff_base=1.0, backoff_max=30.0, jitter=True)` — `error_handling/policy.py:59,73`.
- `RetryPolicyMatrix(matrix=None)` / `RetryPolicyMatrix.from_yaml(path)` — `retry.py:85,94` (loop param `retry_policy`).
- `DefaultCircuitBreaker(*, threshold=5, recovery_timeout_seconds=60.0, half_open_max_calls=1)` — `circuit_breaker.py:84,96`.
- `TenantErrorBudget(store, *, max_per_day=1000, max_per_month=20000)` — `budget.py:108,126`; store = `InMemoryBudgetStore()` (`budget.py:69`, **chosen for this sprint**) or `RedisBudgetStore(client)` (`_redis_store.py:35,42`, deferred — no shared error-budget Redis client wired). tenant_id passed per-call, not at construction.
- `DefaultErrorTerminator(*, circuit_breaker=None, error_budget=None, max_retry_attempts=5)` — `terminator.py:69,83`. 17.md §2.1 ErrorPolicy L135; §6 ErrorTerminator boundary.

### 3.4 Cat 10 (US-4)
- `chat_verification_mode: Literal["disabled","enabled"] = "disabled"` — `core/config/__init__.py:112`.
- `LLMJudgeVerifier(*, chat_client, judge_template, name="llm_judge", tracer=None)` — `verification/llm_judge.py:53,56`; needs a `ChatClient` + a `judge_template` (loaded via `load_template()` from `verification/templates/`, or raw string with `{output}`). Fail-closed.
- `_verifier_factory.py` (`build_default_verifier_registry` L56-67 / `select_verifier_registry` L70): register a real `LLMJudgeVerifier` instead of the no-op `RulesBasedVerifier(rules=[])`. 17.md §2.1 Verifier L139.
- **Decision (confirm Day-0/scope)**: enable mode + verify **final output only** (not every turn) to control the extra LLM call's latency/cost.

---

## 4. File Change List

| File | Change |
|------|--------|
| `backend/src/api/v1/chat/_category_factories.py` | **NEW** — construct compactor / reducer / checkpointer / error_* from adapter ChatClient + db + tenant_id + session_id |
| `backend/src/api/v1/chat/handler.py` | thread `tenant_id`/`db`/`session_id` into `build_handler` + `build_real_llm_handler`; inject Cat 4/7/8 deps into `AgentLoopImpl(...)` |
| `backend/src/api/v1/chat/router.py` | move `session_id` generation before `build_handler`; pass `tenant_id`/`db`/`session_id` |
| `backend/src/api/v1/chat/_verifier_factory.py` | register real `LLMJudgeVerifier` (replace no-op default) |
| `backend/src/core/config/__init__.py` | `chat_verification_mode` default (if flipping to enabled) + judge-template setting |
| `backend/tests/integration/api/test_chat_category_activation_wiring.py` | **NEW** — assert StateCheckpointed (Cat 7) / ContextCompacted (Cat 4) / error classify-retry (Cat 8) / VerificationPassed-Failed (Cat 10) on chat SSE path + multi-tenant scoping |
| `backend/tests/integration/api/test_chat_e2e_real_llm.py` (or extend existing) | **NEW/extend** — `-m real_llm` e2e of the activated flow |
| `claudedocs/4-changes/feature-changes/CHANGE-0XX-chat-path-category-activation.md` | change record |

**No DB migration** (Cat 7 reuses existing `StateSnapshot` ORM / `append_snapshot`) — confirm Day-0 Prong-3.

---

## 5. Acceptance Criteria

- `build_real_llm_handler` injects `compactor`, `reducer`, `checkpointer`, `tenant_id`, `error_policy` (+ retry/circuit/budget/terminator); Cat 10 enabled with a real verifier.
- Integration tests prove on the chat SSE path: `StateCheckpointed` after turns (Cat 7); `ContextCompacted` when token budget exceeded (Cat 4); tool-error classification + retry on a failing tool (Cat 8); `VerificationPassed`/`VerificationFailed` with the real verifier (Cat 10). Checkpointer + error-budget scoped by `tenant_id` (cross-tenant isolation test).
- `real_llm` e2e: one benign multi-turn Azure run reaches END_TURN with `cost_ledger` rows (FIX-022) + `StateSnapshot` rows + verification events.
- All existing tests green; `mypy --strict` clean; 9/9 V2 lints (incl. **LLM SDK leak 0** — `agent_harness/**` no `import openai/anthropic`); frontend untouched.

---

## 6. Deliverables

- [ ] `_category_factories.py` (api-layer constructors, LLM-neutral)
- [ ] Cat 7 injected + tested on chat path
- [ ] Cat 4 injected + tested on chat path
- [ ] Cat 8 (5 deps) injected + tested on chat path
- [ ] Cat 10 enabled + real verifier registered + tested
- [ ] tenant_id/db/session_id threading + ordering fix
- [ ] integration test (4 categories + multi-tenant) + real_llm e2e
- [ ] CHANGE record + progress.md + retrospective.md

---

## 7. Workload Calibration

Scope class: `medium-backend` (0.80). **Agent-delegated: TBD-Day-1-decision** (resolve at Day 1 start).

> Bottom-up est ~14 hr → class-calibrated commit ~11 hr (mult 0.80) → agent-adjusted commit TBD (apply `agent_factor` sub-class per `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier` if Day-1 = `yes`).

---

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **Ordering bug**: `session_id` generated after `build_handler` (router.py:219 vs 202) | Move session_id generation before build_handler; Day-0 confirm no other consumer breaks |
| **Cat 7 all-or-nothing** (reducer+checkpointer+tenant_id) | Inject all three together; assert no-op if any missing in unit test |
| **InMemoryBudgetStore** is per-process (not cross-instance) | Accept for this sprint; `RedisBudgetStore` deferred until a shared error-budget Redis client is wired (NEW carryover AD) |
| **Cat 10 extra LLM call** (latency + cost per verification) | Verify final output only; mode-gated; document cost in CHANGE |
| **LLM-neutrality** (Risk: pulling SDK into agent_harness) | Construct SemanticCompactor/LLMJudgeVerifier with the adapter via `ChatClient` ABC at api layer; lint check_llm_sdk_leak gates |
| **Module-level singleton test isolation** (Risk Class C) | autouse reset fixtures per `.claude/rules/testing.md` §Module-level Singleton Reset |
| Day-0 unknowns: StructuralCompactor/SemanticCompactor ctors; StateSnapshot ORM presence; no-new-migration | Day-0 三-prong (Prong 1 path + Prong 2 content + Prong 3 schema) before Day 1 |

---

## 9. Out of Scope

- **Cat 11 HANDOFF** — wiring + the missing platform-level session-boot is a separate, larger effort. See `claudedocs/1-planning/cat11-handoff-scope-analysis-20260531.md`; recommend its own sprint.
- **Cat 5 PromptBuilder** + **Cat 9 tripwire/audit/capability** + **Cat 12 loop-tracer** on the chat path — not in this sprint (can be a follow-up activation sprint).
- **RedisBudgetStore** cross-instance error budget (deferred — needs shared Redis client).
