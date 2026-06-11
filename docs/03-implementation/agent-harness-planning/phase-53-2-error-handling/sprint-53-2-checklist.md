# Sprint 53.2 — Error Handling Checklist

**Plan**: [sprint-53-2-plan.md](./sprint-53-2-plan.md)
**Branch**: `feature/sprint-53-2-error-handling` (off main `aaa3dd75`)
**Duration**: 5 days (Day 0-4 standard layout)

---

## Day 0 — Setup + Cat 8 Baseline + 53.x Carryover Reproduce (est. 3-4 hours)

### 0.1 Branch + plan + checklist commit
- [x] **Verify on main + clean working tree** _(HEAD aaa3dd75; only untracked phase-53-2 docs dir)_
- [x] **Verify branch protection still enforced** _(enforce_admins=true / review_count=1 / 8 status_checks)_
- [x] **Create feature branch** _(feature/sprint-53-2-error-handling)_
- [x] **Verify phase folder structure exists** _(planning + execution dirs created)_
- [x] **Commit Day 0 docs (plan + checklist)** _(commit 6ed1583d, 1599 lines)_

### 0.2 GitHub issues 建立
- [x] **Create 7 GitHub issues #40-46 + #47** _(8 total: #40-47; all sprint-53-2 labelled)_
- [x] **Verify #38 status** _(was auto-CLOSED by 53.1 PR #39 ref; xfail still in code; **REOPENED** 2026-05-03 to track US-7)_

### 0.3 Cat 8 既有結構 + baseline 記錄
- [x] **Cat 8 stub structure inventory** _(__init__.py + _abc.py + README.md ONLY; NO _contracts/errors.py; NO tests dir — Day 1 creates both)_
- [x] **Cat 8 既有 tests dir** _(missing — to be created Day 1)_
- [x] **Reference points: 8 files (plan estimated 17; -53% drift acceptable)**
- [x] **pytest baseline** _(596 passed / 4 skipped / 1 xfailed in 21.68s)_
- [x] **mypy baseline** _(202 src files clean)_
- [x] **LLM SDK leak baseline** _(0 violations)_
- [x] **6 V2 lint scripts baseline** _(ap1_pipeline_disguise / cross_category_import / duplicate_dataclass / llm_sdk_leak / promptbuilder_usage / sync_callback — all green)_
- [x] **CI Pipeline workflow baseline (AD-CI-1 reproduce)** _(5/5 last main push events FAILED since d4ba89ef 2026-05-01)_

### 0.4 #38 reproduce
- [x] **Run flaky test_router in isolation** _(2 passed / 1 xpassed — XPASS in isolation)_
- [x] **Run flaky test in full suite** _(596 passed / 1 xfailed — confirmed order-dependent flakiness)_
- [x] **Capture suspect leak source** _(isolation XPASS / full-suite xfailed → fixture/registry leak from upstream tests; Day 4 will narrow down)_

### 0.5 AD-CI-1 診斷
- [x] **Inspect last failed CI Pipeline run** _(run id 25252677119; failing job=Build Docker Images, step=Build Backend Docker image)_
- [x] **Identify root cause** _(error: "failed to read dockerfile: open Dockerfile: no such file or directory" — backend/Dockerfile missing; per issue #31 deferred)_
- [x] **Fix strategy decided** _(Day 4 US-8: conditional skip "Build Docker Images" job in ci.yml until #31 lands real V2 Dockerfile; do NOT write Dockerfile in 53.2)_

### 0.6 53.1 closeout bookkeeping branch verify
- [x] **Fetch closeout branch** _(HEAD 41aec40f; 2 commits ahead of main)_
- [x] **Verify diff content preview** _(2 files / +14 / -8 lines: retrospective.md + checklist.md docs-only edits; no src/ changes)_

### 0.7 Day 0 progress.md
- [x] **Day 0 progress.md** _(written at docs/03-implementation/agent-harness-execution/phase-53-2/sprint-53-2-error-handling/progress.md)_

---

## Day 1 — US-1 ErrorPolicy + US-2 RetryPolicy + ErrorRetried Event (est. 6-7 hours)

### 1.1 Update _contracts/errors.py
- [x] **Add new exception classes** _(created `_contracts/errors.py` with ErrorContext + AuthenticationError + MissingDataError + ToolExecutionError; re-exported via _contracts/__init__.py)_

### 1.2 Create policy.py (renamed from classifier.py per stub)
- [x] **Write `DefaultErrorPolicy` class** _(implements existing `ErrorPolicy` ABC: classify + should_retry + backoff_seconds; registry pattern with MRO walk; stdlib-only defaults)_
- [x] **Update `error_handling/__init__.py`** _(re-exported DefaultErrorPolicy)_

### 1.3 Create test_policy.py
- [x] **Create test_policy.py** _(19 tests pass: 10 classify + 4 should_retry + 4 backoff_seconds + 1 import smoke; covers all 4 ErrorClass cases + MRO + register)_

### 1.4 US-2 ErrorRetried event
- [x] **`ErrorRetried` already exists in stub `_contracts/events.py`** _(fields: attempt / error_class / backoff_ms — sufficient for 53.2; no code change needed)_

### 1.5 US-2 Create retry.py
- [x] **Write `RetryConfig` + `RetryPolicyMatrix` classes** _(layer-2 separation: policy.py owns "should retry?", retry.py owns "with what config?"; from_yaml + compute_backoff helper; mypy strict clean)_

### 1.6 Create retry_policies.yaml
- [x] **Create config file** _(`backend/config/retry_policies.yaml` with 4 ErrorClass defaults + salesforce_query per-tool override)_

### 1.7 Create test_retry.py
- [x] **Create test_retry.py** _(15 tests pass: 4 defaults + 3 resolution + 3 from_yaml + 5 compute_backoff)_

### 1.8 Update __init__.py
- [x] **Re-export RetryConfig + RetryPolicyMatrix + compute_backoff** _(exported via `agent_harness.error_handling`)_

### 1.9 Day 1 sanity checks
- [x] **mypy strict 仍 clean** _(205 src files clean, was 202 → +3 new files: errors.py + policy.py + retry.py)_
- [x] **All 6 V2 lint scripts 仍綠** _(ap1 + cross_category + duplicate_dataclass + llm_sdk_leak + promptbuilder + sync_callback all green)_
- [x] **Full pytest 不退步** _(596 → **630 passed** / 4 skip / 1 xfail (#38) / 0 fail; +34 new tests)_
- [x] **Cat 8 coverage Day 1 partial** _(`__init__` + `_abc` + `policy` + `retry` = **100%** coverage; 103/103 stmts; target ≥ 80%)_
- [x] **black + isort + flake8 + ruff** _(all green; `pytest` unused import removed from test_policy.py)_

### 1.10 Day 1 commit + push + verify CI
- [x] **Commit US-1 + US-2** _(commit f87c4a2f, +875/-88 lines, 11 files)_
- [x] **Push to feature branch** _(74fce70d → f87c4a2f)_
- [x] **CI green on this branch** _(Backend CI success on 2f565b60 after isort fix; other 7 workflows trigger on PR open at Day 4)_
- [x] **Close GitHub issues #40 + #41** _(both closed with verification comments)_

### 1.11 Day 1 progress.md update
- [x] **Append Day 1 progress.md** _(Day 1 section written with drift table + sanity matrix)_

---

## Day 2 — US-3 CircuitBreaker + US-4 ErrorBudget (est. 6-7 hours)

### 2.1 Create circuit_breaker.py
- [x] **Write `CircuitState` enum + `CircuitBreakerStats` + `DefaultCircuitBreaker` class** _(per-resource state; CLOSED/OPEN/HALF_OPEN; async with asyncio.Lock; CircuitOpenError; ABC made async)_


### 2.2 Create test_circuit_breaker.py
- [x] **Create test_circuit_breaker.py** _(15 tests pass: 3 construction + 3 closed→open + 4 recovery + 1 isolation + 2 concurrency + 2 smoke)_


### 2.3 Adapter 整合
- [x] **Wrapper pattern instead of modifying ABC** _(created `adapters/_base/circuit_breaker_wrapper.py` — composition; ChatClient ABC stays neutral; existing adapters untouched)_

### 2.4 Adapter integration test
- [x] **Create test_circuit_breaker_integration.py** _(6 tests pass: success path 2 + failure recording 2 + circuit-open short-circuit 2; tests/integration/adapters/__init__.py removed to avoid namespace shadow)_

### 2.5 Create budget.py
- [x] **Write `BudgetStore` Protocol + `InMemoryBudgetStore` + `TenantErrorBudget` class** _(skip FATAL since=bug; daily/monthly TTL; multi-tenant isolation)_

### 2.6 Create _redis_store.py
- [x] **Write `RedisBudgetStore` impl** _(MULTI/EXEC pipeline INCR+EXPIRE atomic; TYPE_CHECKING import; Redis[bytes] generic typed)_

### 2.7 Create error_budgets.yaml
- [x] **Create config file** _(defaults 1000/20000 + per_tenant override placeholder)_

### 2.8 Create test_budget.py
- [x] **Create test_budget.py** _(11 tests pass: 4 InMemoryStore + 3 record + 3 is_exceeded + 1 multi-tenant isolation; uses InMemoryBudgetStore not fakeredis)_

### 2.9 Update __init__.py
- [x] **Re-export DefaultCircuitBreaker + CircuitOpenError + CircuitState + BudgetStore + InMemoryBudgetStore + TenantErrorBudget**

### 2.10 Day 2 sanity checks
- [x] **mypy strict 仍 clean** _(209 src files clean; +4 new files vs Day 1 baseline 205)_
- [x] **All 6 V2 lint scripts 仍綠** _(AP-8 added allowlist for circuit_breaker_wrapper.py — transparent decorator, prompts already built upstream)_
- [x] **Full pytest 不退步** _(630 → **662 passed** / 4 skip / 1 xfail / 0 fail; +32 new tests = 15 cb + 6 cb_integration + 11 budget)_
- [x] **Cat 8 coverage Day 2** _(error_handling 93% — 254 stmts; budget 100% / circuit_breaker 97% / policy 100% / retry 100%; _redis_store 0% — uncovered by design, no Redis in CI)_
- [x] **black/isort/flake8/ruff** _(all green after auto-format on 6 files)_

### 2.11 Day 2 commit + push + verify CI
- [x] **Commit US-3 + US-4 + AP-8 allowlist** _(8c00b413, +1264/-82, 14 files)_
- [x] **Push to feature branch** _(be39582d → 8c00b413)_
- [x] **Backend CI green on this branch** _(initial 8c00b413 fail mypy on Linux Redis[bytes]; fix 677cfcc6 dual `# type: ignore[type-arg, unused-ignore]` per code-quality.md cross-platform pattern; success ✅)_
- [x] **Close GitHub issues #42 + #43**

### 2.12 Day 2 progress.md update
- [x] **Append Day 2 progress.md**

---

## Day 3 — US-5 ErrorTerminator + US-6 AgentLoop Integration (上半) (est. 6-7 hours)

### 3.1 Add LoopTerminated event
- [x] **Add `LoopTerminated` to `_contracts/events.py`** _(frozen dataclass with reason/detail/last_state_version; re-exported via _contracts/__init__.py)_

### 3.2 Create terminator.py
- [x] **Write `TerminationReason` enum + `TerminationDecision` + `DefaultErrorTerminator` class** _(4 reasons: BUDGET_EXCEEDED/CIRCUIT_OPEN/FATAL_EXCEPTION/MAX_RETRIES_EXHAUSTED; non-Tripwire; sync ABC compat method + async evaluate() rich path)_

### 3.3 Create test_terminator.py
- [x] **Create test_terminator.py** _(13 tests pass: 4 sync ABC + 1 budget + 2 circuit + 1 fatal + 1 max-retries + 2 non-termination + 2 enum/boundary smoke)_

### 3.4 Cat 8 vs Cat 9 邊界守門
- [x] **Grep `Tripwire` strict check** _(0 hits for `import.*Tripwire\|class Tripwire\|= Tripwire\|Tripwire(`; only docstring/README mentions explaining boundary)_
- [x] **Update __init__.py** _(re-exported DefaultErrorTerminator + TerminationDecision + TerminationReason)_

### 3.5 US-6 AgentLoop integration (上半 — opt-in deps + helper)
- [x] **Add Cat 8 deps to `AgentLoop.__init__`** _(5 opt-in kwargs: error_policy / retry_policy / circuit_breaker / error_budget / error_terminator; preserved 51.x + 53.1 baseline)_
- [x] **Implement `_handle_tool_error` helper** _(classify → record budget → check terminator; returns (terminate, error_class, reason, detail) tuple; Day 4 wires into main loop; aliased Cat8TerminationReason to avoid collision with orchestrator_loop.termination.TerminationReason)_

### 3.6 Day 3 sanity (moved before commit)
- [x] **mypy --strict** _(210 src files clean, was 209 +1 terminator)_
- [x] **6 V2 lint scripts** _(all green)_
- [x] **Full pytest** _(662 → **675 passed** / 4 skip / 1 xfail / 0 fail; +13 new terminator tests)_
- [x] **black/isort/flake8/ruff** _(auto-applied formatters; all clean)_
- [x] **51.x + 53.1 baseline preserved** _(all integration tests still green)_

### 3.7 Day 3 commit + push (中間 push 取得 CI 反饋)
- [x] **Commit US-5 + US-6 partial** _(077865b4, +534/-57, 8 files)_
- [x] **Push + verify Backend CI green** _(success on 077865b4)_
- [x] **Close GitHub issue #44**

### 3.8 Day 3 progress.md update
- [x] **Append Day 3 progress.md** _(Day 3 section written: 4 deliverables + drift table + sanity matrix)_

---

## Day 4 — US-6 Lower Half + #38 + AD-CI-1 + 53.1 Closeout Bundle + Retrospective + PR (executed 2026-05-03)

> _All Day 4 work compressed into same calendar day. 9 USs + retrospective.md + PR open. Detail boxes below were retroactively documented post-execution._

- [x] **4.1 Wire `_handle_tool_error` into main loop** _(commit `1e782813`; both uncaught exception path + soft-failure ToolResult path)_
- [x] **4.2 Integration tests** _(4 scenarios pass: LLM_recoverable / FATAL_terminate / BUDGET_terminate / opt_out)_
- [x] **4.3 Commit US-6 + push + Backend CI green + close #45** _(success on `1e782813`)_
- [x] **4.4 US-7 #38 fix** _(commit `39bf8648` — asyncio.run() per call replaces fragile get_event_loop().run_until_complete; xfail count 1 → 0)_
- [x] **4.5 US-8 AD-CI-1 fix** _(commits `39bf8648` + `57cf923d` — hashFiles('backend/Dockerfile') guard auto-skips Build job until #31)_
- [x] **4.6 US-9 53.1 closeout bundle** _(merge commit `b4001430` brings 2 commits from `docs/sprint-53-1-closeout-bookkeeping`)_
- [x] **4.7 Sprint final verification** _(all grep evidence ✅ — see retrospective Q6)_
- [x] **4.8 retrospective.md** _(6 必答 + Audit Debt AD-Cat8-1~3 + AD-CI-2/3)_
- [ ] **4.9 PR open + normal merge** ← in progress

### 4.1 US-6 AgentLoop integration (下半 — wire helper into main loop)
- [ ] **Replace direct tool execution with `_execute_tool_with_error_handling`**
  - File: `backend/src/agent_harness/orchestrator_loop/loop.py`
  - 在主 loop 內 tool execution 點呼叫 helper
  - 處理 helper 返回的 `ToolResult | None`：None 代表 terminator 已 fire → break loop
  - DoD: 51.x + 53.1 baseline tests 不退步

### 4.2 US-6 Integration tests
- [ ] **Create test_loop_error_handling.py**
  - File: `backend/tests/integration/agent_harness/orchestrator_loop/test_loop_error_handling.py`
  - Tests:
    - `test_llm_recoverable_error_injects_error_result_into_messages`
    - `test_transient_error_retries_with_backoff_then_succeeds`
    - `test_max_retries_exhausted_triggers_terminator`
    - `test_circuit_open_triggers_terminator`
    - `test_budget_exceeded_triggers_terminator`
    - `test_fatal_unexpected_triggers_terminator_with_checkpoint`
  - DoD: ≥ 6 integration tests pass

### 4.3 US-6 commit + push + verify
- [ ] **Commit US-6 final**
  - Message: `feat(error-handling, sprint-53-2): US-6 AgentLoop tool-error chain (full integration)`
  - **Verify branch before commit**
- [ ] **Push + verify 8 workflow CI green**
- [ ] **Close GitHub issue #45**

### 4.4 US-7 #38 flaky test_router fix (AD-Cat7-2)
- [ ] **Apply fixture / DI registry fix per Day 0 reproduce findings**
  - 推測 fix 1: conftest.py 加 autouse fixture reset DI registry between tests
  - 推測 fix 2: `tests/unit/api/v1/chat/test_router.py` fixtures scope 改 function（從 session/module）
  - 推測 fix 3: 新 Cat 8 deps (RetryPolicy / CircuitBreaker / ErrorBudget) 確保 per-test instance（避免 global state leak）
  - DoD: fix 落地；mypy clean
- [ ] **Remove xfail decorator**
  - File: `backend/tests/unit/api/v1/chat/test_router.py::TestMultiTenantIsolation`
  - 移除 `@pytest.mark.xfail(reason="...", strict=False)` decorator + reason
  - DoD: 無 xfail decorator
- [ ] **Verify in isolation + full suite + random order**
  - `cd backend && python -m pytest tests/unit/api/v1/chat/test_router.py::TestMultiTenantIsolation -v`
  - `cd backend && python -m pytest tests/ --tb=no -q 2>&1 | tail -5`
  - `cd backend && python -m pytest tests/ --random-order 2>&1 | tail -5`（若已裝；否則加 to dev extras carryover）
  - DoD: 三種 run 都 pass；無 xfail
- [ ] **Close GitHub issue #38**
  - `gh issue close 38 --comment "Resolved by commit <hash>. Verified: full suite + random order pass."`

### 4.5 US-8 AD-CI-1 CI Pipeline push-to-main fix
- [ ] **Apply fix per Day 0 診斷 findings**
  - 推測 fix 1: ci.yml 修 push trigger 對齊 PR triggers
  - 推測 fix 2: alembic head conflict 修
  - 推測 fix 3: 加 setup script 補齊 push event 缺項
  - DoD: ci.yml / setup script 落地
- [ ] **Push to feature branch + verify ci.yml on push event green**
  - `gh run list --branch feature/sprint-53-2-error-handling --workflow ci.yml --limit 3`
  - DoD: latest run conclusion = success
- [ ] **Close GitHub issue #46**

### 4.6 US-9 53.1 closeout bookkeeping bundle
- [ ] **Merge `docs/sprint-53-1-closeout-bookkeeping` into 53.2 feature branch**
  - `git fetch origin docs/sprint-53-1-closeout-bookkeeping`
  - `git merge --no-ff origin/docs/sprint-53-1-closeout-bookkeeping -m "chore(closeout, sprint-53-1): bundle bookkeeping commits into 53.2"`
  - 或 cherry-pick：`git cherry-pick <commit-1-sha> <commit-2-sha>`
  - DoD: merge 無衝突；2 commits 在 feature branch
- [ ] **Verify content + push**
  - `git log --oneline -10`
  - `git push origin feature/sprint-53-2-error-handling`
  - DoD: closeout commits 可見；CI 綠
- [ ] **Close GitHub issue #47**

### 4.7 Sprint final verification
- [ ] **All 8 active CI workflow green on feature branch latest**
  - `gh run list --branch feature/sprint-53-2-error-handling --limit 8`
  - DoD: 全綠 on latest commit
- [ ] **pytest final baseline**
  - `cd backend && python -m pytest --tb=no -q 2>&1 | tail -5`
  - DoD: ≥ 615 PASS / 0 xfail（#38 已 reactivate）/ 4 skip / 0 fail
- [ ] **Cat 8 coverage final**
  - `cd backend && python -m pytest tests/ --cov=src/agent_harness/error_handling --cov-report=term 2>&1 | tail -10`
  - DoD: ≥ 80%
- [ ] **mypy strict + LLM SDK leak final**
  - DoD: 205+ src clean；LLM SDK leak = 0；6 V2 lints + black/isort/flake8/ruff green
- [ ] **Cat 8 vs Cat 9 邊界 grep evidence**
  - `grep -rn "Tripwire\|tripwire" backend/src/agent_harness/error_handling/`
  - DoD: 0 hits（per 17.md §6）
- [ ] **ErrorClassifier 真在 AgentLoop 用**
  - `grep -rn "error_classifier\.classify" backend/src/agent_harness/orchestrator_loop/`
  - DoD: ≥ 1 hit
- [ ] **CircuitBreaker 真在 Adapter 用**
  - `grep -rn "circuit_breaker\.is_open\|record_success\|record_failure" backend/src/adapters/`
  - DoD: ≥ 3 hits
- [ ] **ErrorTerminator 真在 AgentLoop 用**
  - `grep -rn "error_terminator\.should_terminate" backend/src/agent_harness/orchestrator_loop/`
  - DoD: ≥ 1 hit
- [ ] **AD-CI-1 fix 驗證**
  - `gh run list --workflow ci.yml --branch feature/sprint-53-2-error-handling --limit 3 --json conclusion`
  - DoD: 最近 3 run 全綠

### 4.8 Day 4 retrospective.md
- [ ] **Write retrospective.md**
  - Path: `docs/03-implementation/agent-harness-execution/phase-53-2/sprint-53-2-error-handling/retrospective.md`
  - 6 必答條 (per plan §Retrospective 必答)：
    1. 每個 US 真清了嗎？commit + verification + 8 active CI run id
    2. 跨切面紀律：admin-merge count（=0）/ temp-relax count（=0）/ Cat 8 coverage / Cat 8 vs Cat 9 grep evidence
    3. 砍 scope？（如 #38 / AD-CI-1 / closeout bundle 部分未解）
    4. GitHub issues #40-46 + #47 + #38 status table
    5. Audit Debt 累積？（如 ErrorBudget tenant override / Redis HA / per-tool circuit breaker discussion 等）
    6. 主流量整合驗收（ErrorClassifier 真用？RetryPolicy 真用？CircuitBreaker 在 Adapter 真接入？ErrorBudget 真用？ErrorTerminator 真用？LLM-recoverable 回注真實作？Cat 8 vs Cat 9 grep ＝ 0？coverage 真 ≥ 80%？）
  - DoD: 6 條全答 + 對齊 53.1 retrospective 結構

### 4.9 PR open + closeout
- [ ] **Push final commits**
  - `git push origin feature/sprint-53-2-error-handling`
- [ ] **Verify final CI green**
  - 8 workflow 全綠 on latest commit
- [ ] **Open PR**
  - Title: `feat(error-handling, sprint-53-2): Cat 8 Error Handling — ErrorClassifier + RetryPolicy + CircuitBreaker + ErrorBudget + ErrorTerminator + AgentLoop integration + #38 fix + AD-CI-1 fix + 53.1 closeout bundle`
  - Body 含：
    - Summary: 9 US ✅ + Cat 8 Level 4 達成 + #38 closed + AD-CI-1 closed + 53.1 closeout bundled
    - Each US verification 證據 (workflow run id + status)
    - GitHub issues #40-46 + #47 + #38 close URLs
    - Cat 8 coverage 數字
    - Cat 8 vs Cat 9 邊界 grep evidence (`Tripwire` in `error_handling/` = 0)
    - 53.1 closeout bundle 確認（2 commits merged）
    - Diff stat
  - DoD: PR opened；CI runs triggered
- [ ] **Wait for review approval (per branch protection)**
  - User reviews PR
  - DoD: 1 approval given (per protection rule required_approving_review_count=1)
- [ ] **Normal merge (NOT admin override, NOT temp-relax bootstrap)**
  - `gh pr merge <id> --merge` (or squash per project convention)
  - DoD: merge commit on main；branch protection enforce_admins=true 自動強制；無 bypass；**zero temp-relax**
- [ ] **Verify post-merge main CI green**
  - `gh run list --branch main --limit 8` 等 ~5 min
  - 8 workflow 全綠 on `main` HEAD
  - DoD: progress.md + retrospective.md §Q1 補上 main HEAD 的 run id；AD-CI-1 修復確認
- [ ] **Update memory**
  - V2 milestone: 14/22 sprints (64%)
  - Cat 8 Level 4 達成
  - phase 53.2 完成
  - #38 closure status
  - AD-CI-1 closure status
  - 53.1 closeout bookkeeping bundled

### 4.10 Cleanup
- [ ] **Delete local feature branch**
  - `git checkout main && git pull && git branch -d feature/sprint-53-2-error-handling`
  - DoD: branch removed local
- [ ] **Delete remote feature branch (if not auto-deleted)**
  - `git push origin --delete feature/sprint-53-2-error-handling`
- [ ] **Delete remote `docs/sprint-53-1-closeout-bookkeeping` branch**
  - `git push origin --delete docs/sprint-53-1-closeout-bookkeeping`
  - DoD: 53.1 closeout branch 已 cleanup（內容已 bundle 進 main）
- [ ] **Update `claudedocs/5-status/v2-audit-2026-04/V2-AUDIT-OPEN-ISSUES-20260501.md` if applicable**
  - Mark AD-Cat7-2 + AD-CI-1 closed by 53.2
  - DoD: §10 table updated（如有對應 entry）

---

## Verification Summary（Day 4 final 必填）

| Item | Status | Evidence |
|------|--------|----------|
| US-1 ErrorClassifier concrete impl | ⬜ | commit hash + coverage % |
| US-2 RetryPolicy matrix + ErrorRetried event | ⬜ | commit hash + YAML loaded test |
| US-3 CircuitBreaker per-provider | ⬜ | commit hash + adapter integration test pass |
| US-4 ErrorBudget per-tenant | ⬜ | commit hash + multi-tenant isolation test |
| US-5 ErrorTerminator | ⬜ | commit hash + 4 termination reasons unit tests |
| US-6 AgentLoop integration | ⬜ | grep error_classifier.classify ≥ 1 hit + integration test scenarios pass |
| US-7 #38 flaky test_router fix | ⬜ | xfail removed + random-order pass × 3 |
| US-8 AD-CI-1 CI Pipeline fix | ⬜ | ci.yml on push event green on main HEAD |
| US-9 53.1 closeout bookkeeping bundle | ⬜ | 2 commits merged + remote branch deleted |
| 8 active CI workflow green on main HEAD | ⬜ | 8 run ids |
| Cat 8 coverage ≥ 80% | ⬜ | pytest --cov output |
| pytest ≥ 615 PASS / 0 xfail / 0 fail | ⬜ | counts |
| mypy 205+ src clean | ⬜ | tail output |
| LLM SDK leak = 0 | ⬜ | tail output |
| 6 V2 lint scripts green | ⬜ | each exit 0 |
| Cat 8 vs Cat 9 邊界 (Tripwire in error_handling/) | ⬜ | grep = 0 hits |
| ErrorClassifier 真在 AgentLoop 用 | ⬜ | grep evidence |
| CircuitBreaker 真在 Adapter 用 | ⬜ | grep evidence (≥ 3 hits) |
| ErrorTerminator 真在 AgentLoop 用 | ⬜ | grep evidence |
| Sprint 53.2 PR normal merge (no admin, no temp-relax) | ⬜ | merge commit hash + protection status |
| V2 milestone 14/22 (64%) | ⬜ | memory + retrospective updated |

---

**權威排序**：本 checklist 對齊 [sprint-53-2-plan.md](./sprint-53-2-plan.md) Acceptance Criteria + Retrospective 必答 6 條。任何 Day 順序變動 / scope 砍必須在 progress.md + retrospective.md 透明列出（per 53.1 closeout 教訓 — branch protection enforce_admins=true 持續強制；本 sprint 必須 zero temp-relax）。
