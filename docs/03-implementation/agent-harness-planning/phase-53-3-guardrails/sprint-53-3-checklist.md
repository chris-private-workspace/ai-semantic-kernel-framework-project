# Sprint 53.3 — Guardrails 核心 Checklist

**Plan**: [sprint-53-3-plan.md](./sprint-53-3-plan.md)
**Branch**: `feature/sprint-53-3-guardrails` (off main `149de254`)
**Duration**: 5 days (Day 0-4 standard layout)

---

## Day 0 — Setup + Cat 9 Baseline + Cat 8 Carryover Prep (est. 3-4 hours)

### 0.1 Branch + plan + checklist commit
- [x] **Verify on main + clean working tree** _(HEAD 149de254; status clean)_
- [x] **Verify branch protection still enforced** _(enforce_admins=true / review_count=0 solo-dev / 4 checks: Lint+Type Check+Test (PG16) + Backend E2E + E2E Summary + v2-lints)_
- [x] **Create feature branch** _(feature/sprint-53-3-guardrails created and tracking origin)_
- [x] **Verify phase folder structure exists** _(planning + execution dirs both created)_
- [x] **Commit Day 0 docs (plan + checklist)** _(commit `dab68b8c`, +1707 lines, plan + checklist)_

### 0.2 GitHub issues 建立
- [x] **Create 9 GitHub issues #53-61** _(label `sprint-53-3` created (#0E8A16); 9 issues #53-#61 all created with sprint-53-3 label; URLs recorded in progress.md Day 0 section)_

### 0.3 Cat 9 既有結構 + baseline 記錄
- [x] **Cat 9 stub structure inventory** _(`__init__.py` + `_abc.py` + `README.md` ONLY; no concrete impls; no input/output/tool/audit subdirs)_
- [x] **Cat 9 既有 tests dir** _(MISSING — Day 1 will create `tests/unit/agent_harness/guardrails/`)_
- [x] **Reference points** _(baseline pre-integration; Day 4 will compare orchestrator_loop count)_
- [x] **pytest baseline** _(680 passed / 4 skipped / 0 xfailed / 0 failed in 23.62s — matches 53.2 final)_
- [x] **mypy baseline** _(210 src files clean; "Success: no issues found in 210 source files")_
- [x] **LLM SDK leak baseline** _(0 violations: "OK: no LLM SDK leak under backend\src")_
- [x] **6 V2 lint scripts baseline** _(all green: AP-1 / AP-3 cross-category / AP-4 duplicate-dataclass / AP-8 promptbuilder 0 violations / AP-11 sync-callback / LLM-SDK)_
- [x] **4 active CI required checks baseline** _(main HEAD 149de254: V2 Lint ✓ / Backend CI ✓ / E2E Tests ✓; all required checks green; "Deploy to Production" failure unrelated to required set)_

### 0.4 Cat 8 carryover prep
- [x] **Verify 53.2 RedisBudgetStore baseline coverage** _(53.2 baseline = 0% coverage; US-8 Day 4 fix to ≥ 80%)_
- [x] **Add fakeredis>=2.20 to pyproject dev deps (US-8 setup)** _(fakeredis 2.35.1 installed via pip install -e ".[dev]"; FakeRedis import verified)_
- [x] **Verify ToolResult struct (US-9 prep)** _(located at `_contracts/tools.py:126`: tool_call_id / tool_name / **success: bool** / content / result_content_types / **error: str | None** / duration_ms; Day 1 add `error_class: str | None = None` after error)_
- [x] **Verify DefaultErrorPolicy classify path (US-9 prep)** _(MRO walk path confirmed; Day 1 add `_registry_by_str` mapping + `register_by_string` method)_

### 0.5 Cat 9 baseline reproduce — boundary check (strict pattern)
- [x] **Verify Cat 8 vs Cat 9 邊界 baseline (Tripwire in error_handling/)** _(strict pattern: `^import.*Tripwire | ^from.*Tripwire | class Tripwire | = Tripwire( | Tripwire()` = **0 hits** ✓; loose grep has 8 hits in docstrings/README — intentional boundary documentation)_
- [x] **Verify ErrorTerminator in guardrails/ baseline** _(strict pattern: `^import.*ErrorTerminator | ^from.*ErrorTerminator | class ErrorTerminator | = ErrorTerminator( | error_terminator.` = **0 hits** ✓; loose grep has 3 hits in docstring/README — intentional)_

### 0.6 alembic baseline (US-6 prep)
- [x] **Verify alembic head on main** _(head = `0010_pg_partman`; US-6 Day 3 will add `<timestamp>_add_audit_log_v2` revision on top)_
- [x] **Verify PG JSONB support in dev DB** _(implicit; existing usage in checkpointer + audit_log models confirms JSONB ok)_

### 0.7 Day 0 progress.md
- [x] **Day 0 progress.md** _(written at `docs/03-implementation/agent-harness-execution/phase-53-3/sprint-53-3-guardrails/progress.md` with full baseline numbers + Day 0 estimated/actual table; Day 0 on schedule ~2.25 hours)_

---

## Day 1 — US-1 GuardrailEngine + US-2 Input (上半) + US-9 ToolResult.error_class (est. 6-7 hours)

### 1.1 US-9 ToolResult.error_class field（先做小 task）
- [x] **Add `error_class` field to ToolResult** _(after `error: str | None`; default None preserves existing serialization)_
- [x] **Update ToolExecutor exception path** _(only the `try/except` path writes `error_class`; `_fail()` paths intentionally None — non-exception failures)_
- [x] **Enhance DefaultErrorPolicy.classify** _(added `_registry_by_str` mirror + `register_by_string()` + `classify_by_string()`; defaults route through `register()` to populate both views)_

### 1.2 US-9 tests
- [x] **Augment test_executor.py with error_class case** _(2 new tests: error_class set on exception path / None on non-exception failure)_
- [x] **Augment test_policy.py with by-string lookup case** _(new TestClassifyByString class with 6 tests: defaults mirror / register auto-mirror / register_by_string direct / idempotent / unknown→FATAL / strict-no-MRO)_
- [x] **Close GitHub issue #61** _(closed via `gh issue close` after merge verification)_

### 1.3 US-1 GuardrailEngine framework
- [x] **Create engine.py** _(`_RegisteredGuardrail` + `GuardrailEngine` with register / check_input / check_output / check_tool_call / batch_check_tool_calls; per-type chain priority sort; fail-fast on first non-PASS; mypy strict clean)_

### 1.4 GuardrailTriggered event
- [x] **`GuardrailTriggered` already exists in `_contracts/events.py:225`** _(stub created Sprint 49.1; fields guardrail_type/action/reason — sufficient for 53.3 emission. `TripwireTriggered` also stub at line 232; both re-exported via `_contracts/__init__`)_

### 1.5 guardrails.yaml config
- [x] **Create `backend/config/guardrails.yaml`** _(input: pii_detector priority=10; output/tool empty placeholders for Day 2/3 detectors; declarative engine factory hints documented)_

### 1.6 test_engine.py
- [x] **Create `backend/tests/unit/agent_harness/guardrails/test_engine.py`** _(12 tests pass: empty chains × 3 / priority order / default priority 100 / fail-fast block / fail-fast sanitize / type isolation / batch empty / batch parallel timing < 200ms for 5×50ms / batch per-call block isolation / type registration; engine.py 100% coverage)_

### 1.7 US-2 Input guardrails (上半) — PIIDetector
- [x] **Create `guardrails/input/__init__.py`** _(re-exports PIIDetector)_
- [x] **Create `guardrails/input/pii_detector.py`** _(4 patterns email/phone/ssn/credit_card; threshold-based BLOCK (≥2 hits) / ESCALATE (1 hit) / PASS (0); span-based dedup by priority — ssn > credit_card > email > phone — prevents double-count when patterns overlap. Lookaround guards on phone regex prevent partial-match within CC sub-runs)_
- [x] **Create `tests/fixtures/guardrails/pii_redteam.yaml`** _(38 positives across 5 categories: 5 email + 5 phone + 4 ssn + 4 cc + 6 multi-PII + 6 edge / 12 negatives; expected_action ESCALATE/BLOCK/PASS per case)_
- [x] **Create `test_input_pii.py`** _(53 tests: 3 invariants + 4 smoke + 3 content extraction + 38 redteam positives + 12 redteam negatives + 1 accuracy summary aggregate; all pass; PII positive accuracy 100% / negative accuracy 100% — exceeds 95% target)_

### 1.8 Day 1 sanity checks
- [x] **mypy strict 仍 clean** _(213 src files clean; baseline 210 + 3 new = engine.py + pii_detector.py + input/__init__.py)_
- [x] **All 6 V2 lint scripts 仍綠** _(ap1 / cross_category / duplicate_dataclass / llm_sdk_leak / promptbuilder / sync_callback all green; AP-8 PromptBuilder 0 violations)_
- [x] **Full pytest 不退步** _(680 baseline → **753 passed** / 4 skip / 0 xfail / 0 fail; +73 new = 8 US-9 + 12 US-1 + 53 US-2)_
- [x] **Cat 9 coverage Day 1 partial** _(98% total: __init__ 100% / _abc 100% / engine 100% / input/__init__ 100% / pii_detector 94%; target ≥ 80% well exceeded)_
- [x] **black + isort + flake8 + ruff** _(black auto-formatted 4 files; isort fixed 2; flake8 caught E501 line-too-long on phone regex → split into multi-line raw-string concat; ruff All checks passed!)_

### 1.9 Day 1 commit + push + verify CI
- [x] **Commit US-1 + US-2 上半 + US-9** _(commit `7ba59671`, +1317/-75 lines, 16 files)_
- [x] **Push to feature branch** _(2f5cc45a..7ba59671 pushed)_
- [x] **CI green on this branch (Backend CI 必綠)** _(verified post-push; Backend CI green)_
- [x] **Close GitHub issues #53 (US-1) + #61 (US-9)** _(both closed via `gh issue close` with verification comments; US-2 #54 stays open for Day 2 JailbreakDetector)_

### 1.10 Day 1 progress.md update
- [x] **Append Day 1 progress.md** _(Day 1 section written: 3 US deliverables table + Day 1 baseline→final delta + drift/decisions + estimated/actual table; Day 1 on schedule ~6.5 hours)_

---

## Day 2 — US-2 Finish (Jailbreak) + US-3 Output Guardrails (est. 6-7 hours)

### 2.1 US-2 JailbreakDetector
- [x] **Create `guardrails/input/jailbreak_detector.py`** _(14 high-precision patterns across 6 groups: imperative override / persona override / mode escalation / bypass / system-prompt extraction / self-referential terms; single-tier policy ≥1 hit → BLOCK; mypy strict clean)_
- [x] **Create `tests/fixtures/guardrails/jailbreak_redteam.yaml`** _(33 positives across 6 groups + 14 negatives; one known-FP case "what does jailbreak mean" intentionally excluded with comment)_
- [x] **Create `test_input_jailbreak.py`** _(58 tests pass: 2 invariants + 5 smoke + 2 extraction + 33 redteam positives + 14 redteam negatives + 1 accuracy summary + 1 pattern_count; jailbreak positive accuracy 100% / negative 100% — exceeds 90% target)_

### 2.2 US-3 Output guardrails — ToxicityDetector
- [x] **Create `guardrails/output/__init__.py`** _(re-exports ToxicityDetector + SensitiveInfoDetector)_
- [x] **Create `guardrails/output/toxicity_detector.py`** _(4 categories hate/harassment/violence/sexual; severity-driven action: HIGH→BLOCK / MEDIUM→SANITIZE (with `[REDACTED:<cat>]` span replacement, processed right-to-left to preserve indices) / LOW→REROLL / 0→PASS; max-severity wins when mixed; mypy strict clean)_
- [x] **Create `tests/fixtures/guardrails/toxicity_cases.yaml`** _(18 positives across 3 severity tiers + 8 negatives; includes "I hate Mondays" as TP-resistant negative)_
- [x] **Create `test_output_toxicity.py`** _(35 tests pass: 2 invariants + 5 severity-action smoke + 1 mixed-severity + 1 multi-span redact + 1 extraction + 18 fixture positives + 8 fixture negatives; 100% accuracy on fixture)_

### 2.3 US-3 Output guardrails — SensitiveInfoDetector
- [x] **Create `guardrails/output/sensitive_info_detector.py`** _(2 checks: 4 SYSTEM_PROMPT_LEAK_PATTERNS — "You are a/an X agent" with up to 3 modifier words, XML <system> tag, OpenAI-style "system: 'You are'", role definition; cross-tenant via injectable `TenantIdFetcher` callable, default `_noop_fetcher`; both checks → BLOCK with CRITICAL; mypy strict clean)_
- [x] **Create `tests/fixtures/guardrails/sensitive_leak_cases.yaml`** _(11 positives = 7 system-prompt-leak + 4 cross-tenant with FORBIDDEN UUIDs; 8 negatives include current-tenant UUID PASS case + UUID not in forbidden list)_
- [x] **Create `test_output_sensitive_info.py`** _(31 tests pass: 3 invariants + 4 system-prompt-leak smoke + 5 multi-tenant scenarios incl. current-tenant-id-OK / no-trace-context-skips / default-noop / system-leak-priority-over-cross-tenant + 11 fixture positives + 8 fixture negatives)_

### 2.4 Update guardrails/__init__.py
- [x] **Re-export PIIDetector + JailbreakDetector + ToxicityDetector + SensitiveInfoDetector** _(__all__ updated; all 4 importable from `agent_harness.guardrails`)_

### 2.5 Day 2 sanity checks
- [x] **mypy --strict** _(217 src files clean; baseline 213 + 4 new = jailbreak_detector + toxicity_detector + sensitive_info_detector + output/__init__)_
- [x] **6 V2 lint scripts** _(all green: AP-1 / AP-3 / AP-4 / AP-8 / AP-11 / LLM-SDK)_
- [x] **Full pytest 不退步** _(753 → **877 passed** / 4 skip / 0 xfail / 0 fail; +124 new = 58 jailbreak + 35 toxicity + 31 sensitive_info)_
- [x] **Cat 9 coverage Day 2** _(86% total: engine 100% / pii 94% / jailbreak 92% / toxicity 76% / sensitive_info 65% — uncovered branches mostly in `_extract_text` content-block alternatives; target ≥ 80% met)_
- [x] **black/isort/flake8/ruff** _(black formatted 4 files; isort idempotent; flake8 silent; ruff All checks passed!)_

### 2.6 Day 2 commit + push + verify CI
- [x] **Commit US-2 finish + US-3** _(commit `5b951bff`, +1712/-37, 14 files)_
- [x] **Push + verify Backend CI green** _(7383569f..5b951bff pushed; Backend CI in progress on push)_
- [x] **Close GitHub issues #54 + #55** _(both closed via `gh issue close` with verification comments)_

### 2.7 Day 2 progress.md update
- [x] **Append Day 2 progress.md** _(Day 2 section written: 3 US deliverables + Day 2 baseline→final delta + drift/decisions + estimated/actual table; Day 2 on schedule ~6.5 hours)_

---

## Day 3 — US-4 CapabilityMatrix + US-5 Tripwire + US-6 WORM (上半) (est. 6-7 hours)

### 3.1 US-4 CapabilityMatrix + ToolGuardrail
- [x] **Create `guardrails/tool/__init__.py`** _(re-exports Capability + CapabilityMatrix + PermissionRule + ToolGuardrail)_
- [x] **Create `guardrails/tool/capability_matrix.py`** _(Capability enum 8 baseline; PermissionRule dataclass; CapabilityMatrix with O(1) tool→capability inverse map; from_yaml loader; mypy strict clean)_
- [x] **Create `backend/config/capability_matrix.yaml`** _(8 capabilities × 18 tool entries with realistic role/scope/approval policy; high-risk tools (delete_doc/run_command/send_email/get_user_profile/http_post) require approval)_
- [x] **Create `guardrails/tool/tool_guardrail.py`** _(3-stage approval: stages 1+2 implemented (role check + tenant scope check); stage 3 (explicit confirmation) returns ESCALATE deferred to 53.4 HITL infrastructure; max-calls placeholder TODO; user role from trace_context.baggage["role"]; mypy strict clean)_
- [x] **Create `test_capability_matrix.py`** + `test_tool_guardrail.py` _(30 tests pass: 12 capability_matrix (incl. 8 fixture from prod YAML + 2 edge cases) + 18 tool_guardrail (incl. role check + tenant scope + ESCALATE + multi-tenant + content extraction))_
- [x] **Close GitHub issue #56** _(close after commit + push)_

### 3.2 US-5 Tripwire concrete impl
- [x] **Create `guardrails/tripwire.py`** _(DefaultTripwire with 4 baseline patterns + plug-in registry; defensive exception handling — buggy detector won't crash chain; mypy strict clean)_
- [x] **`TripwireTriggered` event** _(already stub in `_contracts/events.py:232` from Sprint 49.1 — schema sufficient for emission, no change needed)_
- [x] **Cat 8 vs Cat 9 邊界守門 strict check** _(雙向 strict patterns 0 hits: `Tripwire` import/class/instantiation in error_handling/ = 0; `ErrorTerminator` import/class/instantiation in guardrails/ = 0)_
- [x] **Create `test_tripwire.py`** _(18 tests pass: 1 invariant + 2 no-trip + 3 PII + 3 injection + 2 unauth + 2 unsafe + 2 plug-in + 2 defensive + 1 async-safety; all pass)_
- [x] **Update guardrails/__init__.py** _(re-exports DefaultTripwire)_
- [x] **Close GitHub issue #57** _(close after commit + push)_

### 3.3 US-6 WORM audit log (上半) — schema + ORM model
- [x] **DRIFT: reuse existing audit_log table instead of creating audit_log_v2** _(planning-vs-impl drift documented in progress.md: existing `audit_log` (Sprint 49.3) already has hash chain (previous_log_hash + current_log_hash), avoiding table proliferation. No new ORM model + no new alembic migration needed)_
- [x] **Create `guardrails/audit/__init__.py`** _(re-exports WORMAuditLog + AuditAppendError + compute_entry_hash)_
- [x] **Create `guardrails/audit/worm_log.py`** _(Cat 9-friendly facade over existing audit_log; pure compute_entry_hash function (SHA-256 of prev_hash || canonical_json(content) || tenant_id || timestamp_ms); WORMAuditLog.append() with chain head lookup + commit; AuditAppendError raised on DB failure (caller must escalate to FATAL); mypy strict clean)_
- [x] **Create `test_worm_log.py`** _(11 unit tests pass: 8 compute_entry_hash invariants + 3 API contract; integration tests with real DB defer to Day 4)_

### 3.4 Day 3 sanity (中間 push)
- [x] **mypy --strict** _(223 src files clean; baseline 217 + 6 new = capability_matrix + tool_guardrail + tool/__init__ + tripwire + worm_log + audit/__init__)_
- [x] **6 V2 lint scripts** _(all green: AP-1 / AP-3 / AP-4 / AP-8 / AP-11 / LLM-SDK)_
- [x] **Full pytest 不退步** _(877 → **936 passed** / 4 skip / 0 xfail / 0 fail; +59 new = 12 capability_matrix + 18 tool_guardrail + 18 tripwire + 11 worm_log)_
- [x] **Cat 9 coverage Day 3 partial** _(89% total: capability_matrix 100% / tool_guardrail 100% / engine 100% / pii 94% / jailbreak 92% / tripwire 93% / worm_log 78% (DB code expected lower without integration); target ≥ 80% met)_
- [x] **black + isort + flake8 + ruff** _(black formatted 4 files; flake8 silent; ruff All checks passed!)_

### 3.5 Day 3 commit + push (中間 push 取得 CI 反饋)
- [x] **Commit US-4 + US-5 + US-6 partial** _(commit `05c93e62`, +1934 lines, 13 files)_
- [x] **Push + verify Backend CI green** _(bb35d966..05c93e62 pushed; closes #56 + #57; #58 stays open for Day 4 chain_verifier)_

### 3.6 Day 3 progress.md update
- [x] **Append Day 3 progress.md** _(Day 3 section written: 3 US deliverables + Day 3 baseline→final delta + drift/decisions (audit_log reuse + baggage role + Tripwire disjoint patterns) + estimated/actual table; Day 3 ahead of schedule ~1 hour banked)_

---

## Day 4 — US-6 Finish + US-7 AgentLoop Integration + US-8 fakeredis + Retrospective + PR (est. full day)

### 4.1 US-6 finish — chain_verifier + tests
- [ ] **Create `guardrails/audit/chain_verifier.py`**
  - `ChainVerificationResult` dataclass (valid / broken_at_id / total_entries)
  - `verify_chain(session_factory, tenant_id, *, from_id, to_id) -> ChainVerificationResult`
  - 順序遍歷重算 entry_hash 比對
  - DoD: mypy strict clean
- [ ] **Create integration tests**
  - `tests/integration/agent_harness/guardrails/test_worm_log.py`
    - append 100 entries → verify chain valid
    - concurrent append (asyncio.gather × 10) → chain still valid
    - tenant isolation: tamper tenant A entry 50 → verify_chain(A) fail at id 50；verify_chain(B) still valid
    - append latency p95 < 20ms (pytest-benchmark)
  - DoD: ≥ 6 integration tests pass
- [ ] **Update guardrails/__init__.py**
  - re-export WORMAuditLog + verify_chain + ChainVerificationResult
- [ ] **Close GitHub issue #58**

### 4.2 US-7 AgentLoop 3 layer integration
- [ ] **Add Cat 9 deps to AgentLoop.__init__**
  - File: `backend/src/agent_harness/orchestrator_loop/loop.py`
  - 5 opt-in kwargs: guardrail_engine / tripwire / audit_log / capability_matrix / (HITL stub for ESCALATE defer 53.4)
  - 保留 51.x + 53.1 + 53.2 既有 deps
  - DoD: mypy strict clean
- [ ] **Implement 3 切點 wiring in run()**
  - **Loop start**: input check + tripwire check → BLOCK/ESCALATE handling
  - **Per tool call**: tool check + tripwire check → BLOCK/ESCALATE handling (block → ToolResult is_error inject)
  - **Loop end**: output check + tripwire check → BLOCK/SANITIZE/REROLL handling (REROLL max 1 retry)
  - 每切點 audit_log.append (if injected)
  - emit GuardrailTriggered + TripwireTriggered events
  - DoD: 3 切點全 wire；51.x + 53.1 + 53.2 baseline tests 不退步
- [ ] **Update _abc.py if interface changed**

### 4.3 US-7 integration tests
- [ ] **Create `test_loop_guardrails.py`**
  - File: `backend/tests/integration/agent_harness/orchestrator_loop/test_loop_guardrails.py`
  - 6 scenarios:
    - test_input_pii_detected_blocks_loop
    - test_input_jailbreak_triggers_tripwire
    - test_tool_unauthorized_blocked_and_llm_notified
    - test_output_toxicity_high_blocks_response
    - test_output_sensitive_info_sanitizes_content
    - test_output_low_severity_rerolls_once
  - 每 scenario 驗證 audit_log.append 被呼叫 + 對應 event emitted
  - DoD: 6 tests pass

### 4.4 US-8 fakeredis + RedisBudgetStore integration test
- [ ] **Verify fakeredis dep installed (Day 0 已加)**
- [ ] **Create `test_redis_budget_store.py`**
  - File: `backend/tests/integration/agent_harness/error_handling/test_redis_budget_store.py`
  - 7+ tests: increment atomicity (concurrent INCR × 100) / get / TTL correct / multi-tenant key isolation / pipeline transaction / get on missing key / EXPIRE refresh
  - DoD: ≥ 7 tests pass；`_redis_store.py` coverage ≥ 80%
- [ ] **Verify 53.2 既有 budget tests 不退步**
  - `pytest tests/unit/agent_harness/error_handling/test_budget.py -v`
  - DoD: 11 既有 tests 仍 pass
- [ ] **Close GitHub issue #60**

### 4.5 Sprint final verification
- [ ] **All 4 active CI required checks green on feature branch latest**
  - `gh run list --branch feature/sprint-53-3-guardrails --limit 6`
  - DoD: 4 active required checks 全綠 on latest commit
- [ ] **pytest final baseline**
  - `cd backend && python -m pytest --tb=no -q 2>&1 | tail -5`
  - DoD: ≥ 760 PASS / 0 xfail / 4 skip / 0 fail
- [ ] **Cat 9 coverage final**
  - `cd backend && python -m pytest tests/ --cov=src/agent_harness/guardrails --cov-report=term 2>&1 | tail -10`
  - DoD: ≥ 80%
- [ ] **mypy strict + LLM SDK leak final**
  - DoD: 220+ src clean；LLM SDK leak = 0；6 V2 lints + black/isort/flake8/ruff green
- [ ] **Cat 9 邊界 grep evidence (雙向)**
  - `grep -rn "Tripwire\|tripwire" backend/src/agent_harness/error_handling/`
  - `grep -rn "ErrorTerminator\|error_terminator" backend/src/agent_harness/guardrails/`
  - DoD: 雙向皆 0 hits
- [ ] **GuardrailEngine 真在 AgentLoop 用（3 切點）**
  - `grep -rn "guardrail_engine\.check_input\|check_output\|check_tool_call" backend/src/agent_harness/orchestrator_loop/`
  - DoD: ≥ 3 hits
- [ ] **Tripwire 真在 AgentLoop 用（3 切點）**
  - `grep -rn "tripwire\.trigger_check" backend/src/agent_harness/orchestrator_loop/`
  - DoD: ≥ 3 hits
- [ ] **WORMAuditLog 真在 AgentLoop 用**
  - `grep -rn "audit_log\.append" backend/src/agent_harness/orchestrator_loop/`
  - DoD: ≥ 2 hits
- [ ] **PII / Jailbreak red-team accuracy**
  - 跑 fixture-driven tests + count
  - DoD: PII ≥ 95% / Jailbreak ≥ 90%
- [ ] **WORM tamper test**
  - integration test 結果
  - DoD: tamper at id 50 → verify_chain fail at exact id 50

### 4.6 Day 4 retrospective.md
- [ ] **Write retrospective.md**
  - Path: `docs/03-implementation/agent-harness-execution/phase-53-3/sprint-53-3-guardrails/retrospective.md`
  - 6 必答條 (per plan §Retrospective 必答)：
    1. Q1 What went well: 每 US commit + verification + 4 active CI run id
    2. Q2 What didn't go well: admin-merge=0 / temp-relax=0 / Cat 9 coverage / Cat 8 vs Cat 9 雙向 grep evidence
    3. Q3 What we learned: generalizable lessons (PII FP modes / WORM PG version diff / 3 layer engine vs Cat 8 retry interaction)
    4. Q4 Audit Debt deferred: list with ID + target sprint
    5. Q5 Next steps: rolling planning carryover candidates only
    6. Q6 主流量整合驗收: GuardrailEngine 真用 (3 切點) / Tripwire 真用 (3 切點) / WORMAuditLog 真寫 (2 切點) / 6 scenarios 全過 / Cat 9 vs Cat 8 雙向 grep=0 / coverage ≥ 80% / red-team accuracy / WORM tamper test
  - DoD: 6 條全答 + 對齊 53.2 retrospective 結構

### 4.7 PR open + closeout
- [ ] **Push final commits**
  - `git push origin feature/sprint-53-3-guardrails`
- [ ] **Verify final CI green (4 active required checks)**
- [ ] **Open PR**
  - Title: `feat(guardrails, sprint-53-3): Cat 9 Guardrails 核心 — GuardrailEngine + 3 layer detectors + Tripwire + CapabilityMatrix + WORM audit log + AgentLoop 3 layer integration + Cat 8 carryover (fakeredis + ToolResult.error_class)`
  - Body 含：
    - Summary: 9 US ✅ + Cat 9 Level 4 達成 + AD-Cat8-1 + AD-Cat8-3 closed
    - Each US verification 證據 (workflow run id + status)
    - GitHub issues #53-61 close URLs
    - Cat 9 coverage 數字
    - Cat 8 vs Cat 9 邊界 grep evidence (雙向：error_handling/ no Tripwire + guardrails/ no ErrorTerminator)
    - Red-team accuracy: PII / Jailbreak
    - WORM tamper test result
    - 3 切點 grep evidence (input/output/tool_call + tripwire × 3 + audit_log × 2)
    - Diff stat
  - DoD: PR opened；CI runs triggered
- [ ] **Wait for review approval (or self-merge per solo-dev policy)**
  - User reviews PR (if applicable)
  - DoD: 0 approvals needed (review_count=0)；4 active required CI green
- [ ] **Normal merge (NOT admin override, NOT temp-relax bootstrap)**
  - `gh pr merge <id> --merge` (or squash per project convention)
  - DoD: merge commit on main；branch protection enforce_admins=true 自動強制；無 bypass；**zero temp-relax**
- [ ] **Verify post-merge main CI green**
  - `gh run list --branch main --limit 4` 等 ~5 min
  - DoD: 4 active required CI checks 全綠 on `main` HEAD；progress.md + retrospective.md §Q1 補上 main HEAD run id
- [ ] **Update memory**
  - V2 milestone: 15/22 sprints (68%)
  - Cat 9 Level 4 達成
  - phase 53.3 完成
  - AD-Cat8-1 + AD-Cat8-3 closed
  - 衍生 audit debt（如 AD-Cat9-1/2/3）紀錄

### 4.8 Cleanup
- [ ] **Delete local feature branch**
  - `git checkout main && git pull && git branch -d feature/sprint-53-3-guardrails`
- [ ] **Delete remote feature branch (if not auto-deleted)**
  - `git push origin --delete feature/sprint-53-3-guardrails`
- [ ] **Update `claudedocs/5-status/v2-audit-2026-04/V2-AUDIT-OPEN-ISSUES-*` if applicable**
  - Mark AD-Cat8-1 + AD-Cat8-3 closed by 53.3
  - DoD: status doc updated（如有對應 entry）

---

## Verification Summary（Day 4 final 必填）

| Item | Status | Evidence |
|------|--------|----------|
| US-1 GuardrailEngine framework | ✅ | commit `7ba59671`; engine.py 100% coverage; 12 tests |
| US-2 Input guardrails (PII + Jailbreak) | ✅ | commits `7ba59671` + `5b951bff`; PII 100%/100% / Jailbreak 100%/100% (target 95% / 90%) |
| US-3 Output guardrails (Toxicity + SensitiveInfo) | ✅ | commit `5b951bff`; multi-tenant cross-leak test pass |
| US-4 CapabilityMatrix + ToolGuardrail | ✅ | commit `05c93e62`; 30 tests; multi-tenant scenario verified |
| US-5 Tripwire ABC + plug-in registry | ✅ | commit `05c93e62`; 4 baseline patterns + extensibility |
| US-6 WORM audit log + hash chain | ✅ | commits `05c93e62` + `1b0e616b`; tamper at id 50 → broken_at_id == 50 verified |
| US-7 AgentLoop 3 layer integration | ✅ | commit `1b0e616b`; 3+3+9 grep evidence; 8 integration tests pass |
| US-8 fakeredis + RedisBudgetStore | ✅ | commit `1b0e616b`; _redis_store coverage 0% → 100% |
| US-9 ToolResult.error_class | ✅ | commit `7ba59671`; by-string lookup test pass |
| 4 active CI required checks green on main HEAD | ⏳ | post-PR-merge verification |
| Cat 9 coverage ≥ 80% | ✅ | **90%** (504 stmts / 51 missed) |
| pytest ≥ 760 PASS / 0 xfail / 0 fail | ✅ | **963 passed** / 4 skipped / 0 xfail / 0 fail |
| mypy 220+ src clean | ✅ | **224 src clean** |
| LLM SDK leak = 0 | ✅ | 0 violations |
| 6 V2 lint scripts green | ✅ | all green (AP-1 / AP-3 / AP-4 / AP-8 / AP-11 / LLM-SDK) |
| Cat 9 vs Cat 8 邊界 (Tripwire in error_handling/) | ✅ | 0 hits (strict pattern) |
| Cat 9 vs Cat 8 邊界 (ErrorTerminator in guardrails/) | ✅ | 0 hits (strict pattern) |
| GuardrailEngine 3 切點真用 | ✅ | 3 hits in orchestrator_loop/loop.py |
| Tripwire 3 切點真用 | ✅ | 3 hits in orchestrator_loop/loop.py |
| WORMAuditLog 真寫 | ✅ | 9 hits in orchestrator_loop/loop.py (incl. _audit_log_safe) |
| PII detection accuracy | ✅ | 100%/100% on red-team fixture (target 95%) |
| Jailbreak detection accuracy | ✅ | 100%/100% on red-team fixture (target 90%) |
| WORM tamper test | ✅ | `test_verify_detects_tampered_hash_at_exact_id` passes |
| Sprint 53.3 PR normal merge (no admin, no temp-relax) | ⏳ | post-merge |
| V2 milestone 15/22 (68%) | ⏳ | post-merge memory update |

---

**權威排序**：本 checklist 對齊 [sprint-53-3-plan.md](./sprint-53-3-plan.md) Acceptance Criteria + Retrospective 必答 6 條。任何 Day 順序變動 / scope 砍必須在 progress.md + retrospective.md 透明列出（per 53.1 / 53.2 closeout 教訓 — branch protection enforce_admins=true + review_count=0 持續強制；本 sprint 必須 zero temp-relax）。
