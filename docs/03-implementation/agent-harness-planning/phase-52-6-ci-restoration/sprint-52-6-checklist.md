# Sprint 52.6 — CI Infra Restoration Checklist

**Plan**: [sprint-52-6-plan.md](./sprint-52-6-plan.md)
**Branch**: `feature/sprint-52-6-ci-restoration` (off main `0ec64c77`)
**Duration**: 5 days (Day 0-4 standard layout)

---

## Day 0 — Setup + Reproduce CI Failures (est. 2 hours)

### 0.1 Branch + plan + checklist commit
- [ ] **Verify on main + clean working tree**
  - `git checkout main && git pull && git status --short`
  - DoD: HEAD `0ec64c77`（or newer if main moved）+ working tree empty
- [ ] **Create feature branch**
  - `git checkout -b feature/sprint-52-6-ci-restoration`
  - DoD: `git branch --show-current` returns `feature/sprint-52-6-ci-restoration`
- [ ] **Verify phase folder structure exists**
  - planning: `docs/03-implementation/agent-harness-planning/phase-52-6-ci-restoration/sprint-52-6-{plan,checklist}.md`
  - execution: `docs/03-implementation/agent-harness-execution/phase-52-6/sprint-52-6-ci-restoration/`
  - DoD: `ls` confirms both
- [ ] **Commit Day 0 docs (plan + checklist)**
  - Files: this plan + this checklist
  - Commit message: `docs(ci-restoration, sprint-52-6): Day 0 plan + checklist`
  - **Verify branch before commit**: `git branch --show-current`
  - DoD: `git log -1` shows Day 0 commit on feature branch

### 0.2 GitHub issues 建立
- [ ] **Create 5 GitHub issues #21-25**
  - `gh issue create --title "[Sprint 52.6 / US-1] Black formatting fix on main" --label audit-carryover,sprint-52-6 --body "..."`（5 issues 模仿 52.5 #11-18 格式 — title + body 包含 plan link + DoD）
  - DoD: `gh issue list -l sprint-52-6 -s open` returns 5 rows; URLs 列入 progress.md

### 0.3 Reproduce 4 workflow failures locally
- [ ] **US-1 Black violation list**
  - `cd backend && black --check src tests 2>&1 | head -50 > /tmp/black-violations.txt`
  - DoD: 違反檔案數 + 行數記錄到 progress.md（預期 < 20 file）
- [ ] **US-2 Lint 2 violation list**
  - `python scripts/lint/check_cross_category_import.py --root backend/src/agent_harness 2>&1 | head -30 > /tmp/lint2-violations.txt`
  - DoD: 違反 import 列表記錄到 progress.md；分 Type A（真違反）vs Type B（合理跨範疇）
- [ ] **US-3 E2E latest failure log**
  - `gh run view 25223942660 --log-failed 2>&1 | head -200 > /tmp/e2e-fail.log`
  - DoD: root cause 推斷記錄到 progress.md（Playwright install 缺 / stale spec / env var）
- [ ] **US-4 AP-8 lint script status check**
  - `ls scripts/check_promptbuilder_usage.py scripts/lint/check_promptbuilder_usage.py 2>&1`
  - DoD: 確認當前路徑 `scripts/check_promptbuilder_usage.py`（非 `scripts/lint/`），需 git mv

### 0.4 Pre-existing baseline 記錄
- [ ] **pytest baseline**
  - `cd backend && python -m pytest --tb=no -q 2>&1 | tail -5`
  - DoD: `493 PASS / 1 skipped / 2 pre-existing` recorded（or actual main HEAD baseline if drifted）
- [ ] **mypy baseline**
  - `cd backend && mypy --strict src 2>&1 | tail -3`
  - DoD: 200 src files clean recorded
- [ ] **LLM SDK leak baseline**
  - `python scripts/lint/check_llm_sdk_leak.py --root backend/src 2>&1 | tail -2`
  - DoD: 0 violations recorded

### 0.5 Day 0 progress.md
- [ ] **Day 0 progress.md**
  - Path: `docs/03-implementation/agent-harness-execution/phase-52-6/sprint-52-6-ci-restoration/progress.md`
  - Sections: Day 0 setup / Reproduced failures (4 workflow root causes) / Baseline metrics / Remaining for Day 1
  - DoD: 5 GitHub issue URLs + 4 violation summary 已列

---

## Day 1 — US-1 Black + US-6 Collection Fix (est. 4-5 hours)

### 1.1 Apply Black auto-format
- [ ] **Run black on backend src**
  - `cd backend && black src 2>&1 | tail -5`
  - DoD: "X files reformatted" output；no error
- [ ] **Run black on backend tests**
  - `cd backend && black tests 2>&1 | tail -5`
  - DoD: same
- [ ] **Run black --check confirm**
  - `cd backend && black --check src tests`
  - DoD: exit 0；"All done!" output

### 1.2 Sanity checks
- [ ] **mypy strict 200 src 仍 clean**
  - `cd backend && mypy --strict src 2>&1 | tail -3`
  - DoD: same baseline as Day 0.4
- [ ] **pytest baseline 不退步**
  - `cd backend && python -m pytest --tb=no -q 2>&1 | tail -5`
  - DoD: 493 PASS / 2 pre-existing CARRY-035（或 Day 0.4 baseline 數字）
- [ ] **Diff stat 預期僅格式化**
  - `git diff --stat src tests | tail -10`
  - DoD: 改動行數合理；spot-check 3 random files 確認僅 whitespace / line break

### 1.3 Day 1 commit + push + verify CI
- [ ] **Commit Black fix**
  - Stage: `git add backend/src backend/tests`
  - Message: `style(backend, sprint-52-6): US-1 apply black formatting (CI infra restoration)`
  - **Verify branch before commit**: `git branch --show-current`
- [ ] **Push to feature branch**
  - `git push origin feature/sprint-52-6-ci-restoration`
- [ ] **Verify backend-ci.yml + ci.yml Black step 綠 on this branch**
  - `gh run list --branch feature/sprint-52-6-ci-restoration --limit 5`
  - 等 ~3 min for CI；`gh run view <id> --json jobs -q '.jobs[].steps[] | select(.name | contains("Black"))'`
  - DoD: backend-ci.yml + ci.yml 的 Black step 都顯示 success
- [ ] **Close GitHub issue #21**
  - `gh issue close 21 --comment "Resolved by commit <hash>. Verified: black --check exit 0; backend-ci.yml + ci.yml Black step green on feature branch run <id>."`

### 1.4 US-6 collection fix
- [ ] **Apply Option I — pyproject.toml pythonpath**
  - Edit `backend/pyproject.toml`：在 `[tool.pytest.ini_options]` 加 `pythonpath = ["."]`
  - DoD: line `pythonpath = ["."]` exists under section
- [ ] **Verify `backend/scripts/__init__.py` exists**
  - From Day 0.4 untracked file or create: `touch backend/scripts/__init__.py`
  - DoD: file exists + 0 bytes
- [ ] **Verify pytest collection passes**
  - `cd backend && python -m pytest tests/unit/scripts/test_verify_audit_chain.py --collect-only 2>&1 | tail -5`
  - DoD: exit 0 + "9 tests collected"（or whatever the file's actual test count）
- [ ] **Verify full pytest still works**
  - `cd backend && python -m pytest --tb=no -q 2>&1 | tail -5`
  - DoD: 553 PASS / 14 FAIL / 4 skipped / **0 collection error**（tests now reachable）
- [ ] **If Option I fails**: fallback to Option II（test file importlib.util refactor）or Option III（rename test dir）
  - Audit Debt 記錄 + 改 plan §Tech Spec §US-6
- [ ] **Commit US-6**
  - Stage: `git add backend/pyproject.toml backend/scripts/__init__.py`
  - Message: `fix(scripts, sprint-52-6): US-6 unblock test_verify_audit_chain collection (52.5 carryover)`
  - **Verify branch before commit**
- [ ] **Push to feature branch**
  - `git push origin feature/sprint-52-6-ci-restoration`
- [ ] **Verify ci.yml「Run tests with coverage」step**（仍會 fail 14 個 — 期待，US-7 處理）
  - `gh run view <id> --json jobs -q '.jobs[].steps[] | select(.name | contains("Run tests"))'`
  - DoD: collection error 消失（其他 14 fail 仍有，待 US-7）
- [ ] **Close GitHub issue #26**
  - `gh issue close 26 --comment "Resolved by commit <hash>. Verified: pytest --collect-only on test_verify_audit_chain.py exit 0; 14 pre-existing test failures still need US-7 xfail triage."`

### 1.5 Day 1 progress.md update
- [ ] **Append Day 1 progress.md**
  - Sections: Today's accomplishments (US-1 ✅ + US-6 ✅) / CI verification run ids / Remaining for Day 2

---

## Day 2 — US-2 Lint 2 Fix + US-4 AP-8 Wire (est. 4-6 hours)

### 2.1 US-2 Lint 2 violator categorization
- [ ] **Re-run lint with verbose**
  - `python scripts/lint/check_cross_category_import.py --root backend/src/agent_harness --verbose 2>&1 | tee /tmp/lint2-detail.txt`
  - DoD: 每個違反 import 帶來源檔 + import target
- [ ] **Categorize Type A vs Type B**
  - Type A 真違反：`from agent_harness.<other>.<private>` → 直接 import 私有模組
  - Type B 合理跨範疇：透過 ABC / contracts 但 lint 誤判
  - DoD: progress.md 列每個違反屬 A or B + 修補策略

### 2.2 US-2 Type A fix（真違反）
- [ ] **改走 `agent_harness._contracts/` 公開介面**
  - 對每個 Type A 違反：判斷該 type 是否已在 `_contracts/__init__.py` 暴露
  - 若已 → 改 import path（`from agent_harness._contracts import X`）
  - 若沒 → add re-export 到 `agent_harness/_contracts/__init__.py`
  - DoD: Type A 違反數 = 0；違反者 import path 變 `_contracts/`

### 2.3 US-2 Type B fix（誤判）
- [ ] **若 lint script 支援 allowlist**
  - 加 owner allowlist comment：`# allow-cross-category: <reason>` (per script convention)
  - 否則：考慮將該 ABC / type 移到 `_contracts/`（**只在 < 3 處違反時**；多處則進 53.x architectural review）
- [ ] **若 Type B > 5 違反**
  - **降規模**：retrospective Audit Debt 記錄 + 53.x architectural review issue
  - 本 sprint 暫加 lint allowlist with TODO comment
  - DoD: lint exit 0；Audit Debt 列出待 53.x 處理項

### 2.4 US-2 verify
- [ ] **Local lint exit 0**
  - `python scripts/lint/check_cross_category_import.py --root backend/src/agent_harness`
- [ ] **mypy + pytest 仍 baseline**
  - 同 1.2

### 2.5 US-4 AP-8 wire to lint.yml
- [ ] **git mv `scripts/check_promptbuilder_usage.py` → `scripts/lint/check_promptbuilder_usage.py`**
  - `git mv scripts/check_promptbuilder_usage.py scripts/lint/check_promptbuilder_usage.py`
  - DoD: file in new location；git tracking preserved
- [ ] **Update unit test import path（如有）**
  - 找 `backend/tests/unit/scripts/lint/test_promptbuilder_usage_lint.py`（or wherever it is）
  - 確認 import path 引用新位置（如 lint script 是用 subprocess 跑就無需改）
- [ ] **Add Lint 6 step to `.github/workflows/lint.yml`**
  - 加在 Lint 5 之後：
    ```yaml
    - name: Lint 6 — AP-8 PromptBuilder usage (no bare messages list)
      run: python scripts/lint/check_promptbuilder_usage.py --root backend/src
    ```
  - DoD: lint.yml 步驟數 = 7（Lint 1-6 + unit test）
- [ ] **Local AP-8 lint exit 0**
  - `python scripts/lint/check_promptbuilder_usage.py --root backend/src`
  - DoD: exit 0（per 52.2 Day 4 verify, main 已 clean）

### 2.6 Day 2 commit + push + verify CI
- [ ] **Commit US-2 + US-4**
  - Stage: `git add backend/src/agent_harness scripts/lint .github/workflows/lint.yml`（加上 unit test import update if applicable）
  - Message: `fix(agent-harness, sprint-52-6): US-2 + US-4 cross-category imports + AP-8 lint wire`
  - **Verify branch before commit**
- [ ] **Push**
- [ ] **Verify lint.yml all 6 steps green**
  - `gh run view <new-id> --json jobs -q '.jobs[].steps[] | select(.name | contains("Lint"))'`
  - DoD: Lint 1-6 + unit test 全 success
- [ ] **Close GitHub issues #22 + #24**
  - `gh issue close 22 --comment "..."`；`gh issue close 24 --comment "..."`

### 2.7 Day 2 progress.md update

---

## Day 3 — US-3 Playwright + E2E + US-7 xfail Triage (est. 5-7 hours)

### 3.1 Diagnose Playwright failure root cause
- [ ] **Read fail log**
  - 從 `/tmp/e2e-fail.log`（Day 0.3 抓的）+ 必要時 `gh run view <e2e-id> --log` 重抓
  - DoD: progress.md 記錄 root cause（pick one or more）：
    - (a) browser binary 缺 → workflow 加 `npx playwright install --with-deps`
    - (b) stale spec → frontend pages 演進後 selector 失效
    - (c) ENV var 缺 → BACKEND_URL / BASE_URL
    - (d) flaky timing → retry config
- [ ] **Reproduce locally**
  - `cd frontend && npx playwright install chromium`（如缺）
  - `cd frontend && npm run test:e2e 2>&1 | tee /tmp/e2e-local.log`
  - DoD: local 跑出與 CI 相同 fail（confirms diagnosis）

### 3.2 Fix workflow infra
- [ ] **Edit `.github/workflows/e2e-tests.yml`**
  - 加 `- run: cd frontend && npx playwright install --with-deps chromium`（在 npm install 之後 / E2E 之前）
  - 視 root cause 加 ENV var
  - DoD: workflow YAML valid（`gh workflow view e2e-tests.yml` parses OK）

### 3.3 Fix or skip stale specs
- [ ] **List E2E specs**
  - `ls frontend/tests/e2e/` 或 `frontend/e2e/`（看 playwright.config.ts testDir）
  - DoD: spec 清單記錄
- [ ] **Per spec 決策**：fix or `test.skip`
  - **Fix**：spec 對應 frontend page 仍存在 → 修 selector
  - **Skip**：spec 對應已刪 / 重命名 page → `test.skip("Sprint 52.6: stale after frontend evolution; reactivate in 53.x")` + 列入 retrospective Audit Debt
  - **降規模門檻**：如 fix 工作量 > 半天，全部 skip + 留 1 個 smoke spec（chat-v2 page render）
  - DoD: `cd frontend && npm run test:e2e` exit 0（all pass + skipped 列原因）

### 3.4 Day 3 commit + push + verify CI
- [ ] **Commit US-3**
  - Stage: `git add .github/workflows/e2e-tests.yml frontend/`
  - Message: `fix(e2e, sprint-52-6): US-3 Playwright install + stale spec handling`
  - **Verify branch before commit**
- [ ] **Push**
- [ ] **Verify e2e-tests.yml green on this branch**
  - `gh run view <new-id> --json jobs -q '.jobs[].steps[] | {name, conclusion}'`
  - DoD: Playwright + E2E + Check results 三步全 success
- [ ] **Close GitHub issue #23**
  - `gh issue close 23 --comment "..."`（含 skipped spec 列表 + 53.x reactivate plan）

### 3.5 US-7 xfail triage 14 pre-existing failures
- [ ] **For each of 6 test files, add `@pytest.mark.xfail(strict=True, reason="...")`**：
  - `tests/e2e/test_lead_then_verify_workflow.py` × 2 tests
    - Reason: `"Sprint 51.2 demo affected by 52.x changes; reactivate per #27 in 53.1"`
  - `tests/integration/agent_harness/tools/test_builtin_tools.py` × 2 tests（CARRY-035）
    - Reason: `"CARRY-035 (52.2 retrospective AI-11); reactivate per #27 in 53.1"`
  - `tests/integration/memory/test_memory_tools_integration.py` × 6 tests
    - Reason: `"52.5 P0 #18 ExecutionContext refactor mismatch; reactivate per #27 in 53.1"`
  - `tests/integration/memory/test_tenant_isolation.py` × 2 tests
    - Reason: `"52.5 P0 #11/#18 multi-tenant + ExecutionContext; reactivate per #27 in 53.1"`
  - `tests/integration/orchestrator_loop/test_cancellation_safety.py` × 1 test
    - Reason: `"52.5 orchestrator drift; reactivate per #27 in 53.1"`
  - `tests/unit/api/v1/chat/test_router.py::TestMultiTenantIsolation` × 1 test
    - Reason: `"52.5 P0 #11 multi-tenant; reactivate per #27 in 53.1"`
  - DoD: 14 tests 全加 `@pytest.mark.xfail(strict=True, reason="...")` decorator；不改 source code
- [ ] **Verify pytest exit 0**
  - `cd backend && python -m pytest --tb=no -q 2>&1 | tail -8`
  - DoD: `XX passed, 14 xfailed, X skipped` + exit 0
- [ ] **Strict=True sanity**
  - 隨選 1 個 xfail test 暫時加 `assert True` 看是否 XPASS（test framework warning）
  - 然後 revert 確保標記為 xfail
  - DoD: pytest output 顯示 "x" 標記符
- [ ] **Verify mypy + LLM SDK leak 不退步**
  - 同 Day 0.4 baselines

### 3.6 Day 3 commit + push + verify CI
- [ ] **Commit US-3 + US-7**
  - Stage: `git add .github/workflows/e2e-tests.yml frontend/ backend/tests/`
  - Message: `fix(ci, sprint-52-6): US-3 + US-7 — Playwright config + xfail triage 14 pre-existing failures`
  - **Verify branch before commit**
- [ ] **Push**
- [ ] **Verify e2e-tests.yml + ci.yml「Run tests with coverage」green**
  - `gh run view <id> --json jobs -q '.jobs[].steps[] | select(.conclusion != null) | {name, conclusion}'`
  - DoD: e2e-tests.yml 3 step success + ci.yml「Run tests with coverage」success（with xfail）+「Check results」success
- [ ] **Close GitHub issue #23**
  - `gh issue close 23 --comment "..."`（含 skipped spec 列表）
- [ ] **Update GitHub issue #27 with reactivation plan**
  - `gh issue edit 27 --body "Updated <date>: 14 pre-existing failures xfailed in PR <hash>. Reactivation plan for 53.1: ..."`
  - **Don't close** #27（53.1 reactivate 才 close）

### 3.7 Day 3 progress.md update

---

## Day 4 — US-5 Branch Protection + Retrospective + Closeout (est. 3-4 hours)

### 4.1 US-5 Branch protection rule setup
- [ ] **Confirm current state**
  - `gh api repos/laitim2001/ai-semantic-kernel-framework-project/branches/main/protection 2>&1 | head -20`
  - DoD: 確認 protection 不存在 / 不完整（如 admin bypass enabled）
- [ ] **Set branch protection via GitHub UI or `gh api`**
  - GitHub UI：Settings → Branches → Add rule for `main`
  - 必選 status checks：V2 Lint / Backend CI / CI Pipeline / E2E Tests / Frontend CI
  - 必選 options：require up-to-date / require PR review (1 approval) / restrict push / no force push / no delete
  - **關鍵**：Allow administrators to bypass = ❌
  - DoD: 設定後 `gh api .../branches/main/protection` 回傳完整配置
- [ ] **Verify lockdown via dummy red PR**
  - Create test branch with intentional black violation：`git checkout -b test/branch-protection-verify-52-6`
  - Push + open PR；4 workflow 應該紅
  - 嘗試 admin merge → **應該被擋**
  - DoD: screenshot or `gh api` response 證明 admin 無法 bypass red CI；PR 關閉，test branch 刪除

### 4.2 13.md doc 更新
- [ ] **Edit `docs/03-implementation/agent-harness-planning/13-deployment-and-devops.md`**
  - 加 §Branch Protection 章節：
    - 設定的 status checks 清單
    - 設定的 options（review / up-to-date / no force push / no admin bypass）
    - 為何需要（避免 admin-merge norm；52.5 §AD-2 教訓）
    - `gh api` 等價設定命令（reproducibility）
  - DoD: 章節新增；目錄連結更新（如 13.md 有 TOC）

### 4.3 Sprint final verification
- [ ] **All 4 workflow + Frontend CI green on feature branch latest run**
  - `gh run list --branch feature/sprint-52-6-ci-restoration --limit 6`
  - DoD: V2 Lint + Backend CI + CI Pipeline + E2E Tests + Frontend CI 全綠
- [ ] **No admin-merge usage in this sprint**
  - 本 sprint 內所有 commit 走正常 push（無 PR merge bypass — 因為 PR 開到 Day 4 末才 merge）
- [ ] **pytest + mypy + LLM SDK leak baselines 不退步**
  - 同 Day 0.4 baseline；任何退步必須在 retrospective 解釋

### 4.4 Day 4 retrospective.md
- [ ] **Write retrospective.md**
  - Path: `docs/03-implementation/agent-harness-execution/phase-52-6/sprint-52-6-ci-restoration/retrospective.md`
  - 6 必答條（per plan §Retrospective 必答）：
    1. 每個 US 真清了嗎？commit + verification（含 main HEAD CI run id 待 PR merge 後補）
    2. 跨切面紀律：admin-merge count（=0）/ silent skip count（E2E）/ Potemkin 修補（AP-8 wire 完成）
    3. 砍 scope？（如 US-2 Type B / US-3 E2E spec 降規模）
    4. GitHub issues #21-25 全 close 表格
    5. Audit Debt 累積？（53.x 處理項列出）
    6. 主流量整合驗收（4 workflow 真執行 / branch protection 真擋 admin / AP-8 真跑 / E2E 真跑）
  - DoD: 6 條全答 + 對齐 52.5 retrospective 章節結構

### 4.5 Phase folder rolling 更新
- [ ] **No phase README needed**
  - phase-52-6 同 phase-52-5 為 single-sprint phase；無需 README
- [ ] **Update `06-phase-roadmap.md` 如必要**
  - 視內容；如 roadmap 沒列 52.6（rolling planning 屬性），不強制更新；retrospective 中提及

### 4.6 PR open + closeout
- [ ] **Push final commits**
  - `git push origin feature/sprint-52-6-ci-restoration`
- [ ] **Verify final CI green**
  - 4 workflow + Frontend CI 全綠 on latest commit
- [ ] **Open PR**
  - Title: `feat(ci-restoration, sprint-52-6): CI infra restoration — AD-5 (4 workflow + branch protection)`
  - Body 含：
    - Summary：5 US ✅ + AD-5 closure
    - Each US verification 證據（workflow run id + status）
    - GitHub issues #21-25 close URL
    - Branch protection screenshot or `gh api` response
    - Diff stat
  - DoD: PR opened；CI runs triggered
- [ ] **Wait for review approval（per branch protection rule）**
  - User reviews PR
  - DoD: 1 approval given
- [ ] **Normal merge（NOT admin-merge）**
  - `gh pr merge <id> --merge`（or squash per project convention）
  - DoD: merge commit on main；branch protection rule 沒被 bypass
- [ ] **Verify post-merge main CI green**
  - `gh run list --branch main --limit 6` 等 ~5 min
  - 4 workflow + Frontend CI 全綠 on `main` HEAD（**這是 AD-5 closure 的關鍵證據**）
  - DoD: progress.md + retrospective.md §Q1 補上 main HEAD 的 run id
- [ ] **Update memory: V2 milestone 12/22 sprints + AD-5 closed**

### 4.7 Cleanup
- [ ] **Delete local feature branch**
  - `git checkout main && git pull && git branch -d feature/sprint-52-6-ci-restoration`
  - DoD: branch removed local
- [ ] **Delete remote feature branch（if not auto-deleted）**
  - `git push origin --delete feature/sprint-52-6-ci-restoration`
- [ ] **Update `claudedocs/5-status/v2-audit-2026-04/V2-AUDIT-OPEN-ISSUES-20260501.md` §AD-5**
  - Mark AD-5 ✅ Closed by Sprint 52.6（commit hash + PR url）
  - DoD: §10 table updated

---

## Verification Summary（Day 4 final 必填）

| Item | Status | Evidence |
|------|--------|----------|
| US-1 Black on main | ⬜ | run id |
| US-2 Lint 2 on main | ⬜ | run id |
| US-3 E2E on main | ⬜ | run id（含 skipped spec count）|
| US-4 AP-8 (Lint 6) on main | ⬜ | run id |
| US-5 Branch protection on main | ⬜ | `gh api` response |
| US-6 collection error gone | ⬜ | pytest collection output |
| US-7 14 xfail decorations + #27 umbrella | ⬜ | xfail count + #27 url |
| 4 workflow + Frontend CI 全綠 on main HEAD | ⬜ | 5 run ids |
| Branch protection 真擋 admin-merge | ⬜ | dummy PR test result |
| pytest exit 0（539 PASS / 14 xfail / 4 skipped / 0 fail） | ⬜ | counts |
| mypy 200 src clean | ⬜ | tail output |
| LLM SDK leak = 0 | ⬜ | tail output |
| Sprint 52.6 PR 走正常 merge（no admin） | ⬜ | merge commit hash |

---

**權威排序**：本 checklist 對齐 [sprint-52-6-plan.md](./sprint-52-6-plan.md) Acceptance Criteria + Retrospective 必答 6 條。任何 Day 順序變動 / scope 砍必須在 progress.md + retrospective.md 透明列出（per 52.5 §AD-2 教訓）。
