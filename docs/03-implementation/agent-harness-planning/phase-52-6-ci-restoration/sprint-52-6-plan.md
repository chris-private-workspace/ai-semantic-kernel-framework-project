# Sprint 52.6 — CI Infra Restoration (Audit Debt AD-5)

**Phase**: phase-52-6-ci-restoration
**Sprint**: 52.6
**Duration**: 5 days (Day 0-4 standard layout)
**Status**: TODO → IN PROGRESS → DONE
**Created**: 2026-05-02
**Owner**: User-spawned cleanup session 2026-05-02+
**Branch**: feature/sprint-52-6-ci-restoration (off main `0ec64c77`)

---

## Sprint Goal

修復 V2-AUDIT-OPEN-ISSUES-20260501.md §AD-5「CI infra 100% fail rate on main」— 4 GitHub Actions workflow（V2 Lint / Backend CI / CI Pipeline / E2E Tests）連續 3 runs 全失敗。**在 Phase 53.1 啟動前**讓 main branch CI 全綠 + branch protection rule 落地，避免 admin-merge 成為 V2 開發 norm。

---

## Background

V2 Verification Audit（2026-05-01 closeout）在 §10 §AD-5 記錄：

> **CI infra 100% fail rate on main**: backend-ci.yml, ci.yml, e2e-tests.yml, lint.yml all failed last 3 runs each. Sprint 52.5 PR #19 fixed mypy+lint scope but CI infra (lint.yml needs sqlalchemy install, e2e needs Playwright setup, etc.) is broken at workflow-level. Admin-merge bypassed. New cleanup sprint: 'CI infra restoration'. Estimated 3-5 days.

**Sprint 52.6 啟動前 reproduce on main HEAD `0ec64c77`** 確認真實 failure 點（`gh run view`）：

| Workflow | File | Failed Step（最新 main run）| 性質 |
|----------|------|---------------------------|------|
| V2 Lint | `lint.yml` | Lint 2 — no private cross-category imports | 規則違反 |
| Backend CI | `backend-ci.yml` | Black (code formatting) | 格式化 |
| CI Pipeline | `ci.yml` | Run Black + Run tests with coverage + Check results | 格式化 + test 執行 |
| E2E Tests | `e2e-tests.yml` | Run Playwright tests + Run E2E tests + Check results | Playwright runner |
| Frontend CI | `frontend-ci.yml` | (n/a — last run SUCCESS) | 不在 scope |

**根因假設**（Day 0 將驗證）：
1. **Black**：Sprint 52.2 (PR #20) + Sprint 52.5 (PR #19) merge 期間，未跑 `black --check` pre-commit；admin-merge 略過 CI gate；累積 unformatted code 進入 main
2. **Lint 2**：Sprint 52.2 PromptBuilder 引入 `from agent_harness.<other>` 私有 import（or Sprint 52.5 chat handler / sandbox 重寫過程引入）；need Day 0 reproduce 才能定位
3. **Playwright**：E2E workflow 缺 `npx playwright install --with-deps` step；或測試 fixture import broken；Sprint 49.1 frontend skeleton 後 frontend pages 持續演進，E2E spec 未跟上
4. **AP-8 lint not wired**：Sprint 52.2 Day 4 新增 `scripts/check_promptbuilder_usage.py` 但**沒有加入** `lint.yml` 的 6 個 lint rule（仍是 Lint 1-5）；rule 存在但 CI 不執行 = AP-4 Potemkin

**衍生 process 問題**（Sprint 52.5 retrospective §AD-2 已記）：
- `main` 沒有 branch protection rule → admin-merge 是 fallback path
- 52.5 PR #19 + 52.2 PR #20 都使用 admin-merge（因 CI 紅）→ 形成 precedent
- 本 sprint 必須 + Phase 53 啟動前修，否則 53.1 + 53.2 + ... 將繼續 admin-merge

詳見：
- `claudedocs/5-status/v2-audit-2026-04/V2-AUDIT-OPEN-ISSUES-20260501.md` §AD-5（真相 entry）
- `docs/03-implementation/agent-harness-execution/phase-52-5/sprint-52-5-audit-carryover/retrospective.md` §Q5 §AD-2（admin-merge precedent）
- `docs/03-implementation/agent-harness-execution/phase-52/sprint-52-2/retrospective.md` §AI-15（branch protection rule TODO）

---

## User Stories

### US-1：作為 V2 開發者，我希望 main branch black formatting 一致，以便 backend-ci.yml + ci.yml 的 Black step 通過
- **驗收**：`cd backend && black --check src tests` exit 0；CI 兩個 workflow Black step 全綠
- **影響檔案**：違反 black format 的 src / tests 檔（Day 0 reproduce 後列出）；不修 black version
- **GitHub Issue**：#21（Day 0 建立）

### US-2：作為 11+1 範疇紀律守護者，我希望 lint.yml 的 Lint 2（cross-category imports）通過，以便範疇邊界不再被私有 import 穿透
- **驗收**：`python scripts/lint/check_cross_category_import.py --root backend/src/agent_harness` exit 0；違反者改走 `agent_harness._contracts/` 公開介面或 add 到 allowlist（如真有合理跨範疇）
- **影響檔案**：違反 import 的 .py（Day 0 reproduce 後列出）；可能 `_contracts/` 加 re-export
- **GitHub Issue**：#22

### US-3：作為 E2E 測試 owner，我希望 e2e-tests.yml 的 Playwright + E2E + Check results 三步全綠，以便前端主流量驗收 reactivate
- **驗收**：workflow 全 green；Playwright 啟動 + 既有 E2E spec 全 pass；如有 stale / broken spec，明確 skip（不 silent ignore）
- **影響檔案**：`.github/workflows/e2e-tests.yml`（add `npx playwright install --with-deps`）；`frontend/tests/e2e/**/*.spec.ts`（修或 skip stale）
- **GitHub Issue**：#23

### US-4：作為 Sprint 52.2 carryover owner，我希望 AP-8 PromptBuilder usage lint 加入 lint.yml workflow，以便 V2 Lint 步驟覆蓋全部 6 條規則（避免 AP-4 Potemkin）
- **驗收**：`lint.yml` step 6 = `python scripts/check_promptbuilder_usage.py --root backend/src`；CI 跑此規則綠（main 已通過此檢查 per 52.2 Day 4 verify）
- **影響檔案**：`.github/workflows/lint.yml`（加 step）；可能 move `scripts/check_promptbuilder_usage.py` → `scripts/lint/check_promptbuilder_usage.py` 對齊命名
- **GitHub Issue**：#24

### US-5：作為平台維護者，我希望 main branch protection rule 生效（必須 4 workflow green 才可 merge），以便消除 admin-merge norm 並守護 53.x sprint
- **驗收**：GitHub repo settings → Branches → main：require status checks（V2 Lint / Backend CI / CI Pipeline / E2E Tests + 必要時 Frontend CI）+ require branches to be up-to-date + restrict who can dismiss
- **影響檔案**：GitHub UI 設定；docs `docs/03-implementation/agent-harness-planning/13-deployment-and-devops.md` 加 §Branch Protection 章節說明 + screenshot
- **GitHub Issue**：#25

### US-6：作為 CI 維護者，我希望解除 `test_verify_audit_chain.py` collection error，以便 `ci.yml`「Run tests with coverage」step 進入測試執行階段（Option C scope expansion 2026-05-02）
- **驗收**：`python -m pytest tests/unit/scripts/test_verify_audit_chain.py --collect-only` exit 0 + 9 tests collected；全 baseline pytest 不再有 collection error
- **影響檔案**：`backend/scripts/__init__.py`（新建，52.5 plan 列在 File Change List 但實作未交付）；`backend/pyproject.toml`（加 `pythonpath = ["."]`）
- **GitHub Issue**：#26
- **源頭**：52.5 P0 #13 oversight（Day 0 progress §New Finding 發現）

### US-7：作為 CI 維護者，我希望 14 個 pre-existing test failures 加 `@pytest.mark.xfail(strict=True)` 標記 + umbrella reactivate ticket，以便 `ci.yml`「Run tests with coverage」step exit 0 + bug 不被遺漏（Option C scope expansion 2026-05-02）
- **驗收**：6 個 test file × 14 tests 全加 xfail decorator + reason + reactivate ticket 引用；pytest exit 0；GitHub issue #27 列 6 categories + 53.1 reactivate plan
- **影響檔案**：7 個 test files（per Day 0 progress §New Finding 表）
- **GitHub Issue**：#27（umbrella，53.1 reactivate）
- **源頭**：Day 0.4 baseline 發現 main HEAD 14 failures（遠超 52.2 retrospective 「2 pre-existing CARRY-035」）

---

## Technical Specifications

### US-1 — Black formatting fix

**現況**（Day 0 reproduce on main HEAD `0ec64c77`）：
- `backend-ci.yml` Step "Black (code formatting)" exit 1
- `ci.yml` Step "Run Black (formatting)" exit 1
- 兩 workflow 都跑 `black --check src tests`（path scope 視 workflow 而定，Day 0 確認）

**設計**：
1. Day 0 跑 `cd backend && black --check src tests 2>&1 | head -50` 取得 violation list
2. 跑 `cd backend && black src tests` 修復
3. 確認 mypy strict 仍 200 src clean（black 純格式化不影響 type check）
4. 確認既有 pytest baseline 不變（per 52.2 retrospective: 493 PASS / 1 skipped / 2 pre-existing CARRY-035）

**驗證**：
- `cd backend && black --check src tests` exit 0
- backend-ci.yml + ci.yml Black step 綠
- diff stat 預期僅格式化（無 logic 改動）

**Effort**: 0.5 day（含 reproduce + format + commit + push 確認 CI 綠）

### US-2 — Lint 2 cross-category imports fix

**現況**（Day 0 reproduce）：
- `lint.yml` Step "Lint 2 — no private cross-category imports" exit 1
- 規則 source: `scripts/lint/check_cross_category_import.py`（49.4 Day 4 落地，per `category-boundaries.md`）

**設計**：
1. Day 0 reproduce locally：`python scripts/lint/check_cross_category_import.py --root backend/src/agent_harness 2>&1 | head -30`
2. 分類違反：
   - **Type A — 真違反**：直接 `from agent_harness.<other>.<private>` import 私有模組 → 改走 `agent_harness._contracts/` 公開介面
   - **Type B — 合理跨範疇**：例如範疇 1 → 範疇 6 OutputParser ABC 是 17.md §2.1 核可的 → 加 owner allowlist（如 lint script 支援）或將 ABC 移 `_contracts/`
3. 修完後 `python scripts/lint/check_cross_category_import.py --root backend/src/agent_harness` exit 0
4. **不**降低 lint 嚴格度（不加 `# noqa: cross-category` 逃逸閥）

**驗證**：
- Local lint exit 0
- lint.yml CI 步驟綠
- Grep `from agent_harness\.` in `agent_harness/**`（除 `_contracts/` 自身）counts 不增

**Effort**: 1-1.5 day（取決於違反數量；歷史經驗 5-10 行修補）

### US-3 — E2E Playwright runner restoration

**現況**（Day 0 reproduce）：
- `e2e-tests.yml` 3 個 step fail（Playwright / E2E / Check results）
- Frontend CI（基本 build）SUCCESS — 表示 frontend code 編 OK

**設計**：
1. Day 0 跑 `gh run view <e2e-id> --log-failed | head -200` 取真實 error
2. 常見 root cause + 對應修補：
   - **Missing browser binaries**：workflow 加 `- run: cd frontend && npx playwright install --with-deps chromium`（最小依賴）
   - **Stale spec**：spec 用了已刪 component selector → Day 1 跑 `cd frontend && npm run test:e2e` 確認 + 修 selector or `test.skip`
   - **Workflow ENV missing**：缺 `BACKEND_URL` / `BASE_URL` env var → 加
3. 如修補 > 1 day，**降規模**：保留 1 個 smoke E2E spec（chat-v2 page render），其他 stale spec `test.skip` 並開 issue 排到 53.x

**驗證**：
- Local：`cd frontend && npm run test:e2e` exit 0（或全 pass + skip 列出原因）
- e2e-tests.yml 3 step 綠
- Skipped spec 列入 retrospective Audit Debt（不靜默 skip）

**Effort**: 1-1.5 day

### US-4 — AP-8 lint integration into lint.yml

**現況**：
- `scripts/check_promptbuilder_usage.py` 存在（52.2 Day 4 落地）
- `lint.yml` 只有 Lint 1-5（49.4 + 50.1 落地，AP-1-5）
- AP-8 規則寫了 + 本地單元測試 PASS + 52.2 main 驗證 0 violation；**但 CI 不跑** = AP-4 Potemkin

**設計**：
1. **路徑對齊**：`git mv scripts/check_promptbuilder_usage.py scripts/lint/check_promptbuilder_usage.py`（與 Lint 1-5 一致）
2. 對應改 `backend/tests/unit/scripts/lint/test_promptbuilder_usage_lint.py` import path（or 已在 `tests/unit/scripts/`，重指向）
3. 改 `lint.yml` 加 step：
   ```yaml
   - name: Lint 6 — AP-8 PromptBuilder usage (no bare messages list)
     run: python scripts/lint/check_promptbuilder_usage.py --root backend/src
   ```
4. 驗證 CI：push 後 V2 Lint workflow 跑 6 個 step，全綠

**驗證**：
- `python scripts/lint/check_promptbuilder_usage.py --root backend/src` exit 0
- lint.yml 步驟數 = 6（Lint 1-5 + Lint 6 + unit test）
- AP-8 unit test 仍綠

**Effort**: 0.5 day

### US-6 — Test verify_audit_chain collection fix

**現況**（Day 0.4 reproduce）：
```
ModuleNotFoundError: No module named 'scripts.verify_audit_chain'
```
- `backend/scripts/__init__.py` 不存在（52.5 plan 列在 File Change List 但未提交 — 52.5 retrospective 未發現）
- 即便加 `__init__.py`，仍失敗 — 真因是 **namespace 衝突**：pytest 默認模式下，`tests/unit/scripts/__init__.py` 把 `scripts` 註冊為 `tests.unit.scripts` package，與 `backend/scripts/` 衝突
- Manual `python -c "import sys; sys.path.insert(0, '.'); from scripts.verify_audit_chain import _normalise_db_url"` works（手動加路徑時）

**設計**（fix order，最小改動優先）：
1. **Option I — Pyproject pythonpath**（最低改動，首選）：
   - 加 `[tool.pytest.ini_options] pythonpath = ["."]` to `backend/pyproject.toml`
   - 加 `backend/scripts/__init__.py`（52.5 plan 已要求；空檔）
   - 不改 test file；不 rename
2. **Option II — Test file 用 importlib.util.spec_from_file_location**（fallback）
3. **Option III — Rename `tests/unit/scripts/` → `tests/unit/cli_scripts/`**（最重，最後選項）

**驗證**：
- `python -m pytest tests/unit/scripts/test_verify_audit_chain.py --collect-only` exit 0 + 9 tests collected
- 全 baseline pytest 不再有 collection error
- 既有 539 PASS 不退步

**Effort**: 0.5 day（Day 1 與 US-1 並行）

### US-7 — xfail triage for 14 pre-existing test failures

**現況**（Day 0.4 baseline）：
14 個 failing tests across 6 files / 6 categories

**設計**：
1. 每 failing test 加 `@pytest.mark.xfail(reason="...", strict=True)` decorator
2. Reason 內容：簡述失敗來源 + reactivate ticket reference（GitHub issue #27 / 53.1 sprint）
3. `strict=True` 確保**真意外修好**會自動轉 PASS（防止後續 sprint regression）
4. **不**改 test logic / source code — 純標記
5. 創 GitHub issue #27 umbrella ticket：列 6 categories + 53.1 reactivate plan

**Categories + reason 模板**：

| Test file | xfail count | Reason 模板 |
|-----------|-------------|-------------|
| `e2e/test_lead_then_verify_workflow.py` | 2 | Sprint 51.2 demo affected by 52.x changes; reactivate per #27 in 53.1 |
| `integration/agent_harness/tools/test_builtin_tools.py` | 2 | CARRY-035 (52.2 retrospective AI-11); reactivate per #27 in 53.1 |
| `integration/memory/test_memory_tools_integration.py` | 6 | 52.5 P0 #18 ExecutionContext refactor mismatch; reactivate per #27 in 53.1 |
| `integration/memory/test_tenant_isolation.py` | 2 | 52.5 P0 #11/#18 multi-tenant + ExecutionContext; reactivate per #27 in 53.1 |
| `integration/orchestrator_loop/test_cancellation_safety.py` | 1 | 52.5 orchestrator drift; reactivate per #27 in 53.1 |
| `unit/api/v1/chat/test_router.py::TestMultiTenantIsolation` | 1 | 52.5 P0 #11 multi-tenant; reactivate per #27 in 53.1 |

**驗證**：
- `python -m pytest --tb=no -q` exit 0（with xfailed listed）
- 539 PASS / 14 xfail / 4 skipped / 0 failed
- ci.yml「Run tests with coverage」step 綠（exit 0）

**Effort**: 0.5-1 day（Day 3 與 US-3 並行）

### US-5 — Branch protection rule + admin-merge precedent 截斷

**現況**：
- `gh api repos/laitim2001/ai-semantic-kernel-framework-project/branches/main/protection` 預期 404 / 無設置
- Sprint 52.2 PR #20 + Sprint 52.5 PR #19 都 admin-merge
- Sprint 52.5 retrospective §AD-2 + 52.2 §AI-15 都 flagged

**設計**：
1. **設定 branch protection rule on `main`**：
   - Require status checks to pass before merging：✅
     - V2 Lint
     - Backend CI
     - CI Pipeline
     - E2E Tests
     - Frontend CI（已 pass，加進來鎖住不退步）
   - Require branches to be up to date before merging：✅
   - Require pull request reviews before merging：✅（min 1 approval）
   - Restrict who can push to matching branches：✅（只 admin）
   - Allow force pushes：❌
   - Allow deletions：❌
   - **Allow administrators to bypass**：❌（**關鍵**：杜絕 admin-merge）
2. 文件 `13-deployment-and-devops.md` 加 §Branch Protection（含 GitHub UI 設定 screenshot 或 `gh api` 等價命令）
3. **驗證 lockdown**：故意起一個 dummy PR with red CI → 確認無法 admin-merge
4. **過渡期**：本 sprint 自身的 PR 用正常路徑 merge（4 workflow 都綠）— 不能再 admin-merge bypass

**驗證**：
- `gh api repos/laitim2001/ai-semantic-kernel-framework-project/branches/main/protection` 回傳 protection 配置
- Dummy PR 測試 admin 無法 bypass red CI（screenshot in retrospective）
- Sprint 52.6 PR 自身用正常 merge（不 admin-merge）

**Effort**: 0.5 day

---

## File Change List

### US-1 (Black)
- ✏️ Backend src / tests 中 black violator 檔（Day 0 list；預期 < 20 個）
- 不改 `backend/requirements.txt` 的 `black` version

### US-2 (Lint 2)
- ✏️ `backend/src/agent_harness/<violator>.py`（Day 0 list；預期 < 5 個）
- 可能 ➕ re-export 至 `backend/src/agent_harness/_contracts/__init__.py`

### US-3 (Playwright)
- ✏️ `.github/workflows/e2e-tests.yml`（加 `npx playwright install --with-deps`）
- 可能 ✏️ `frontend/playwright.config.ts`（baseURL / timeout）
- 可能 ✏️ `frontend/tests/e2e/**/*.spec.ts`（修 stale selector or `test.skip`）

### US-4 (AP-8 wire)
- 🔁 `scripts/check_promptbuilder_usage.py` → `scripts/lint/check_promptbuilder_usage.py`（git mv）
- ✏️ `.github/workflows/lint.yml`（加 Lint 6 step）
- 可能 ✏️ `backend/tests/unit/scripts/lint/test_promptbuilder_usage_lint.py` import path

### US-5 (Branch protection)
- GitHub UI 設定（無 file）
- ✏️ `docs/03-implementation/agent-harness-planning/13-deployment-and-devops.md`（加 §Branch Protection 章節）

### US-6 (collection fix)
- ➕ `backend/scripts/__init__.py`（empty file，從 52.5 plan oversight）
- ✏️ `backend/pyproject.toml`（加 `[tool.pytest.ini_options] pythonpath = ["."]`）

### US-7 (xfail triage)
- ✏️ `backend/tests/e2e/test_lead_then_verify_workflow.py`（加 xfail × 2）
- ✏️ `backend/tests/integration/agent_harness/tools/test_builtin_tools.py`（加 xfail × 2 — CARRY-035）
- ✏️ `backend/tests/integration/memory/test_memory_tools_integration.py`（加 xfail × 6）
- ✏️ `backend/tests/integration/memory/test_tenant_isolation.py`（加 xfail × 2）
- ✏️ `backend/tests/integration/orchestrator_loop/test_cancellation_safety.py`（加 xfail × 1）
- ✏️ `backend/tests/unit/api/v1/chat/test_router.py`（加 xfail × 1）
- 不改 source code；純標記

---

## Acceptance Criteria

### Sprint-level（必過）
- [ ] 7 user stories 全 ✅（US-1 ~ US-7；US-6/US-7 加入 Day 0 Option C scope expansion）
- [ ] 4 GitHub Actions workflow（V2 Lint / Backend CI / CI Pipeline / E2E Tests）on `main` HEAD 連續 ≥ 2 runs 全綠
- [ ] Frontend CI 仍綠（不退步）
- [ ] `cd backend && python -m pytest` exit 0：539 PASS / 14 xfail / 4 skipped / **0 failed** / **0 collection error**
- [ ] `cd backend && mypy --strict src` 200 files clean（不退步）
- [ ] `python scripts/lint/check_llm_sdk_leak.py --root backend/src` LLM SDK leak = 0
- [ ] 7 GitHub issues #21-27 全 close（#27 umbrella reactivate ticket 開 + assigned to 53.1）

### 跨切面紀律
- [ ] **No admin-merge**：本 sprint 自身 PR 走正常路徑（4 + 1 workflow 全綠 + 1 review approval）
- [ ] **No silent skip**：E2E spec 若 skip，retrospective 列原因 + 排程 sprint
- [ ] **No new Potemkin**：US-4 修的就是 AP-4 case，不再引入新的 lint-not-wired

### 主流量整合驗收（per mini-W4-pre Process Fix #6）
- [ ] **Black** 在 main 真的執行嗎？`gh run view <latest-main> --json jobs -q '.jobs[].steps[] | select(.name | contains("Black"))'` 顯示 success
- [ ] **Lint 2** 在 main 真的執行嗎？同上
- [ ] **AP-8 (Lint 6)** 在 main 真的執行嗎？同上 — 證明不是 Potemkin
- [ ] **E2E** 在 main 真的執行嗎？同上
- [ ] **Branch protection** 真的生效嗎？故意 push red PR 試圖 admin-merge → 應該被 block

---

## Deliverables（見 checklist 詳細）

| Day | 工作 |
|-----|------|
| 0 | Setup: branch + plan + checklist + GitHub issues #21-27 + reproduce 4 workflow failure locally + 14+1 test failures discovery + Option C scope expansion approved |
| 1 | **US-1 Black formatting fix + US-6 collection fix** + commit + push 驗 backend-ci.yml + ci.yml Black step 綠 + collection 通過 |
| 2 | US-2 Lint 2 cross-category fix + US-4 AP-8 wire to lint.yml + push 驗 V2 Lint 6 step 全綠 |
| 3 | **US-3 Playwright + E2E restoration + US-7 xfail triage** + push 驗 e2e-tests.yml 綠 + ci.yml「Run tests with coverage」step 綠（539 PASS / 14 xfail / 0 failed） |
| 4 | US-5 Branch protection rule setup + 13.md doc + retrospective + Sprint Closeout + PR open（normal merge，**not admin-merge**）|

Day 0 完成 2026-05-02；Day 1-4 預計 6 days（5+1）。

---

## Dependencies & Risks

### 依賴
- `gh` CLI authenticated（已 — Sprint 52.2/52.5 用過）
- GitHub repo admin 權限（用戶持有）
- Local Playwright 可裝（`npx playwright install`）
- 6 個 lint script 在 `scripts/lint/` 健全（49.4 + 50.1 + 52.2 落地）

### 風險

| Risk | Mitigation |
|------|------------|
| **Lint 2 違反深度太大** — 修起來是 architectural refactor 而非 lint compliance | Day 0 reproduce 時 categorize violator；如 type B「合理跨範疇」> 5 處，先加 lint allowlist（with TODO comment）並 retrospective flag 為 53.x scope；不在 52.6 內做 architectural refactor |
| **E2E spec 大量 stale** — frontend pages 演進後 selector / route 全變 | Day 3 出現此情況立刻降規模：保 1 smoke spec + 其他 explicit `test.skip` + retrospective Audit Debt 記錄 + 53.x frontend sprint 重 build |
| **Black 修補過大產生 mass-rename 衝突** | `cd backend && black src tests` 一次 commit；如 > 50 file，分 src / tests 兩 commit；不 amend；不混 logic 改動 |
| **Branch protection 設錯導致用戶被自己鎖外** | Day 4 設定後 immediately 跑 dummy PR 驗證；保留 `Allow administrators to bypass` 選項只在 emergency override（**but 本 sprint 後永久關閉**）|
| **AP-8 lint script path move 影響 52.2 unit test** | git mv 同 commit 內 update import path + run pytest 確認綠 |
| **Sprint 52.6 自身 PR 也跑紅** | DoD 是 4 workflow 全綠才 merge；如某 step 仍紅，不 admin-merge bypass — fix it 或承認 sprint 未完成 |
| **US-6 Option I (pyproject pythonpath) 不解** | Fallback Option II（test file importlib.util）→ Option III（rename test dir）；最差 case 加 1 day |
| **US-7 xfail strict=True triggered**（53.x 修好但忘移除 xfail）| 53.1 reactivate ticket 強制要求移除 xfail 後 commit，pytest fail = 自動 catch |
| **US-7 標記後 cancellation_safety 1 個是 race condition flaky**（不是真 bug）| Day 3 reproduce 3 次；如 3/3 fail 則 xfail；如 1/3 pass 則改 `pytest.mark.flaky` 或 `xfail(strict=False)` + Audit Debt |

---

## Audit Carryover Section（per W3 process fix #1）

本 sprint 處理 §AD-5（Sprint 52.5 retrospective 新發現）+ 52.2 §AI-15（branch protection TODO）+ 52.2 §AP-8 wire（Sprint 52.2 Day 4 落地但 CI 未跑）。

**不在 52.6 scope**（明確排除）：
- CARRY-035（test_builtin_tools.py 2 pre-existing failures）→ 53.1 per 52.2 §AI-11
- CARRY-033（Redis-backed PromptCacheManager）→ Phase 53.x per 52.2 §AI-12
- CARRY-034（Sub-agent delegation）→ Phase 54.2
- W3-2 SLO carryover（child span / metric emit count）→ Phase 53.x per 52.2 §AI-12
- 5×3 matrix real PG fixture → Phase 53.x per 52.2 §AI-13

### 後續 audit 預期

W4 audit（Sprint 52.6 完成後）：驗證
- 4 workflow on main 真綠（連續 5 runs）
- Branch protection 真生效（admin-merge 被擋）
- AP-8 Lint 6 在 CI 跑（非 Potemkin）
- E2E 真執行（非全 skip）

---

## §10 Process 修補落地檢核

per 52.5 §10：

- [x] Plan template 加 Audit Carryover 段落（本 plan §Audit Carryover Section）
- [ ] Retrospective 加 Audit Debt 段落（Day 4 retrospective.md）
- [ ] GitHub issue per US（#21-25 Day 0 建立）
- [ ] **per mini-W4-pre Process Fix #6**：Sprint Retrospective「主流量整合驗收」必答題（Day 4）
- [x] **52.5 §AD-2 落地**：本 sprint **不**用 admin-merge，正常走 4 workflow green + review approval

---

## Retrospective 必答（per W3-2 + mini-W4-pre 教訓）

Sprint 結束時，retrospective 必須回答以下 6 條：

1. **每個 US 真清了嗎？** 列每 US 對應 commit + verification 結果（含 4 workflow 在 main HEAD 的 run id + status）
2. **跨切面紀律守住了嗎？**：admin-merge count（本 sprint 應 = 0）/ silent skip count（E2E）/ new Potemkin lint count
3. **有任何砍 scope 嗎？** 若有，明確列出 + 理由 + 後續排程
4. **GitHub issues #21-25 全 close 了嗎？** 列每個 issue url + close 時 commit hash
5. **Audit Debt 有累積嗎？** 本 sprint 期間發現的新 audit-worthy 問題列出
6. **主流量整合驗收**：4 workflow 在 main 真執行？branch protection 真擋住 admin override？AP-8 Lint 6 真跑？E2E 真跑？

---

## Sprint Closeout

- [ ] Day 4 retrospective.md 寫好（含必答 6 條）
- [ ] All 7 GitHub issues #21-27 closed（#27 umbrella reactivate moved to 53.1 — close 52.6 reference, but keep tracking issue OPEN for 53.1）
- [ ] PR 開到 main，title: `feat(ci-restoration, sprint-52-6): CI infra restoration — AD-5 (4 workflow + branch protection + collection unblock + xfail triage)`
- [ ] PR body 含每 US verification 證據 + workflow run id + branch protection screenshot/api response
- [ ] **PR 用正常 merge**（NOT admin-merge）— 4 workflow + 1 frontend + 1 review approval
- [ ] V2 milestone 更新：12/22 sprints

---

**權威排序**：`agent-harness-planning/` 19 docs > 本 plan > V1 文件 / 既有代碼。本 plan 對齊 V2-AUDIT-OPEN-ISSUES-20260501.md §AD-5 + Sprint 52.5 retrospective §AD-2 + Sprint 52.2 retrospective §AI-15 真相。
