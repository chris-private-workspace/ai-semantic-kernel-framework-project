# Sprint 57.63 Checklist — Production Chat-Path Category Activation (Cat 4 / 7 / 8 / 10)

**Plan**: [`sprint-57-63-plan.md`](./sprint-57-63-plan.md)
**Created**: 2026-05-31
**Status**: Draft (code gated on scope approval)

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify (per `.claude/rules/sprint-workflow.md §Step 2.5`)
- [x] **Prong 1 (path)**: `_category_factories.py` does NOT exist; `handler.py` / `router.py` / `_verifier_factory.py` / `core/config/__init__.py` exist
  - Verify: `Glob backend/src/api/v1/chat/_category_factories.py` → 0 results
- [x] **Prong 2 (content)**: capture verbatim `StructuralCompactor.__init__` + `SemanticCompactor.__init__` (deps); confirm `chat_verification_mode` field (config:112); confirm `_verifier_factory` no-op default; confirm `AgentLoopImpl.__init__` param names (loop.py:184-263)
  - Verify: `grep -n "def __init__" backend/src/agent_harness/context_mgmt/compactor/structural.py backend/src/agent_harness/context_mgmt/compactor/semantic.py`
- [x] **Prong 3 (schema)**: confirm `StateSnapshot` ORM + `append_snapshot` exist; confirm **NO new migration** needed (Cat 7 reuses existing table)
  - Verify: `grep -rn "class StateSnapshot\|def append_snapshot" backend/src/infrastructure/db/`
- [x] Catalogue drift findings (D0-N) in progress.md; go/no-go for Day 1

### 0.2 Branch + decisions
- [x] Create branch `feature/sprint-57-63-chat-path-category-activation` from main
- [x] Confirm scope decisions: Cat 10 verify-final-only vs per-turn; Cat 8 budget = InMemory; Agent-delegated yes/no (Workload 4-segment)

---

## Day 1 — Plumbing + Cat 7 + Cat 4

### 1.1 Dependency + ordering plumbing
- [x] Move `session_id` generation before `build_handler` (router.py); thread `tenant_id`/`db`/`session_id` → `build_handler` → `build_real_llm_handler`
  - DoD: signatures updated; existing chat tests still pass
  - Verify: `pytest tests/integration/api/test_chat_e2e.py -q`
- [x] Create `_category_factories.py` (api-layer constructors; adapter passed as `ChatClient`)
  - DoD: mypy strict clean; no SDK import
  - Verify: `python scripts/lint/run_all.py` (check_llm_sdk_leak green)

### 1.2 Cat 7 injection
- [x] Inject `DefaultReducer()` + `DBCheckpointer(db, session_id=, tenant_id=)` into `build_real_llm_handler`
  - DoD: all-three-or-no-op honored
- [ ] Integration test: `StateCheckpointed` emitted on chat SSE path after a turn; cross-tenant isolation
  - Verify: `pytest tests/integration/api/test_chat_category_activation_wiring.py -k cat7 -q`

### 1.3 Cat 4 injection
- [x] Construct `HybridCompactor(structural, semantic=SemanticCompactor(chat_client))`; inject
  - DoD: uses Day-0-confirmed ctor deps
- [ ] Integration test: `ContextCompacted` emitted when token budget exceeded
  - Verify: `pytest tests/integration/api/test_chat_category_activation_wiring.py -k cat4 -q`

---

## Day 2 — Cat 8 + Cat 10

### 2.1 Cat 8 injection (5 deps)
- [x] Inject `DefaultErrorPolicy()` + `RetryPolicyMatrix()` + `DefaultCircuitBreaker()` + `TenantErrorBudget(InMemoryBudgetStore())` + `DefaultErrorTerminator(circuit_breaker=, error_budget=)`
- [ ] Integration test: a failing tool triggers classify → retry → (budget/circuit) on chat path
  - Verify: `pytest tests/integration/api/test_chat_category_activation_wiring.py -k cat8 -q`

### 2.2 Cat 10 enable
- [x] Register real `LLMJudgeVerifier(chat_client, judge_template)` — via NEW `make_chat_verifier_registry` (approach A: built in build_real_llm_handler with the loop's adapter, threaded to router); `chat_verification_mode` kept default `disabled` (safe rollout) + new `chat_verification_judge_template="safety_review"` setting. final-output-only. Source mypy/flake8/9-lints green; 50 unit tests pass. (Integration proof BLOCKED on Docker — Day 3)
- [ ] Integration test: `VerificationPassed`/`VerificationFailed` emitted with the real verifier
  - Verify: `pytest tests/integration/api/test_chat_category_activation_wiring.py -k cat10 -q`

---

## Day 3 — Cross-cutting Tests + real_llm e2e

- [ ] Combined integration test: all 4 categories active in one chat SSE run + multi-tenant scoping (checkpointer + budget per tenant)
- [ ] `real_llm` e2e (`-m real_llm`): benign multi-turn Azure run → END_TURN with `cost_ledger` rows + `StateSnapshot` rows + verification events
  - Verify: `pytest -m real_llm tests/integration/api/test_chat_e2e_real_llm.py -q`
- [ ] Confirm LLM SDK leak 0 + mypy strict + 9/9 V2 lints

---

## Day 4 — Closeout

- [ ] Full validation sweep: `pytest` (all) / `mypy --strict` / `python scripts/lint/run_all.py` / frontend untouched / LLM SDK leak 0
- [ ] `claudedocs/4-changes/feature-changes/CHANGE-0XX-chat-path-category-activation.md`
- [ ] progress.md (Day 0-4 actuals) + retrospective.md (Q1-Q7)
- [ ] Calibration: record `medium-backend` ratio + agent_factor (if delegated) in `.claude/rules/sprint-workflow.md §Scope-class multiplier matrix`
- [ ] Update breadth-probe doc §4.1/§5 verdict (Cat 4/7/8/10 now active on chat path) — close the Potemkin finding
- [ ] PR (no push without authorization)
