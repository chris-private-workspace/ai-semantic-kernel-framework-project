---
File: docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-14-plan.md
Purpose: Sprint 57.14 plan — AD-Frontend-E2E-Sweep. Close the Sprint 57.13 carryover: the Playwright e2e suite was never run green after Days 4-8 implementation churn, and the visual-regression spec ships skipped (no Linux baselines). This sprint runs the full e2e suite, fixes stale assertions/selectors, and lands a CI mechanism to generate the visual-regression baselines on a Linux runner. Phase 57+ Frontend SaaS — e2e maintenance / carryover-fix sprint.
Category: Frontend / e2e / DevOps (CI)
Scope: Phase 57 / Sprint 57.14

Description:
    Sprint 57.13 (Frontend Foundation 1/N Completion) shipped ~15 USs over Day 0-9.
    Its Day 9 closeout left three e2e-related items as carryover under the umbrella
    AD `AD-Frontend-E2E-Sweep` (see 57.13 retrospective Q4):

      1. Residual e2e spec regression — Days 4-8 changed implementation (RequireAuth
         gate, design-system component swaps, DecisionModal → Radix Dialog, error-path
         copy "Failed to load data", auth-fixtures, i18n string changes) but the e2e
         spec files were only partially synced (auth-fixtures `**/` JSDoc bug + 5
         tenant-page specs seedAuthJwt + a11y color-contrast disable + cost/sla
         error-path were fixed in the PR #130 CI rounds; the full suite was never
         run green in a dev session — "no dev-server boot available" was the stated
         constraint at the tail of that large sprint).
      2. visual-regression.spec.ts ships `test.skip(!process.env.RUN_VISUAL, …)` —
         baselines must be generated on the CI Linux runner (Windows-generated PNGs
         would all mismatch); the spec code is in place, baselines + un-skip are the gap.
      3. chat-v2 / governance e2e regression after the 57.13 Radix DecisionModal swap
         (= D-DAY5-3) — theoretically non-breaking (preserved role="dialog" + button
         names + ESC/outside-click) but needs a real run.

    This is a focused maintenance sprint, not a feature sprint. Work is grouped:

    A. E2E suite green (US-A1, US-A2) — install Playwright Chromium; run the full
       e2e suite locally (`npx playwright test`, which auto-starts `npm run dev`
       on :5173 per playwright.config.ts webServer); triage every failure; fix stale
       selectors / assertions / route-mock shapes against the current (post-57.13)
       implementation; iterate to green (excluding the two opt-in skips —
       connectivity needs a real backend, visual needs Linux baselines). This subsumes
       carryover items 1 and 3.

    B. Visual-regression enablement (US-B1) — add a Linux CI mechanism that generates
       and commits the `visual-regression.spec.ts` baselines: a `workflow_dispatch`
       job in `.github/workflows/playwright-e2e.yml` (ubuntu-latest) running
       `RUN_VISUAL=1 npm run e2e -- visual --update-snapshots` + auto-committing the
       `*-snapshots/*.png` back to the branch; add a `npm run e2e:visual:update`
       convenience script; update the spec's skip guard so that once baselines exist
       in the repo the spec runs on every CI e2e run. Baseline PNGs themselves are
       produced by that workflow (cannot be generated from a Windows dev session);
       this sprint lands the mechanism + documents the one-shot trigger.

    C. Closeout (US-C1) — full validation sweep (npm lint + build + vitest + playwright
       local-runnable subset; backend untouched — confirm baseline) + retrospective
       Q1-Q7 + memory snapshot + doc syncs (16-frontend-design.md timeline note /
       sprint-workflow.md calibration +1 row / CONVENTION.md §e2e addendum if any /
       SITUATION + CLAUDE.md deferred post-merge) + PR.

    Deferred OUT of this sprint (explicitly): the actual visual baseline PNG commit
    happens via the CI workflow this sprint introduces (not from this dev session);
    `connectivity.spec.ts` stays opt-in (needs a running backend + DB — out of scope
    for a CI lane); the broader `AD-Inline-Style-Cleanup-Sweep` (chat-v2 color-contrast
    fix) is a separate carryover and is NOT this sprint.

Created: 2026-05-10 (Sprint 57.14 drafting; closes Sprint 57.13 carryover AD-Frontend-E2E-Sweep)
Last Modified: 2026-05-10
Status: Closed (Day 3 closeout — 4/4 USs done; e2e suite 40 pass / 7 opt-in skip; visual CI mechanism landed; ratio ~1.05 in band; see retrospective.md)

Modification History (newest-first):
    - 2026-05-10: Day 3 closeout — sprint done; calibration `frontend-e2e-sweep` 0.50 1st app ratio ~1.05 KEEP; carryover in retrospective.md Q4
    - 2026-05-10: Initial creation (Sprint 57.14 — AD-Frontend-E2E-Sweep; ~4 USs / Day 0-3)

Related:
    - sprint-57-13-plan.md (structural template per sprint-workflow.md §Step 1 — most recent completed sprint)
    - docs/03-implementation/agent-harness-execution/phase-57/sprint-57-13/retrospective.md (Q4 — origin of AD-Frontend-E2E-Sweep + AD-Visual-Baseline-Generation)
    - frontend/playwright.config.ts (webServer config: local = `npm run dev` :5173, CI = `npm run preview` :5173)
    - .github/workflows/playwright-e2e.yml (existing e2e CI workflow — this sprint extends it with a workflow_dispatch visual-baseline job)
    - frontend/CONVENTION.md (existing codified conventions — §e2e/test patterns if extended)
    - .claude/rules/frontend-react.md / file-header-convention.md / sprint-workflow.md / anti-patterns-checklist.md / testing.md
    - memory/feedback_e2e_network_mocking_pattern.md (most specs mock at page.route() — no real backend needed; only connectivity + visual are opt-in)
---

# Sprint 57.14 — AD-Frontend-E2E-Sweep（e2e 套件跑綠 + visual baseline CI 機制）

## Sprint Goal

把 Sprint 57.13 留下的 e2e carryover 收口：(1) 在 dev session 實際把整套 Playwright e2e 跑起來（`npx playwright test` 會自動起 `npm run dev` 在 :5173 — 大多數 spec 用 `page.route()` mock 不需要真 backend），逐一 triage 失敗，對齊 57.13 Day 4-8 的 implementation 改動（`<RequireAuth>` gate / 設計系統組件 swap / DecisionModal→Radix Dialog / error-path 文案 "Failed to load data" / auth-fixtures / i18n 字串）修掉所有 stale assertion/selector，跑到綠（排除兩個 opt-in skip：`connectivity` 需真 backend、`visual` 需 Linux baseline）；(2) 為 `visual-regression.spec.ts` 落一個 Linux CI 機制——`playwright-e2e.yml` 加一個 `workflow_dispatch` job（ubuntu-latest）跑 `RUN_VISUAL=1 npm run e2e -- visual --update-snapshots` 並把 `*-snapshots/*.png` auto-commit 回 branch + 加 `npm run e2e:visual:update` script + 改 spec 的 skip guard 讓 baseline 一旦存在就在每次 CI e2e run 跑——baseline PNG 本身由該 workflow 產（Windows dev session 產不出可用的）；(3) chat-v2 / governance e2e 在 57.13 Radix DecisionModal swap 後的 regression（D-DAY5-3）由 (1) 跑全套涵蓋。

---

## Background

### 為什麼這個 sprint 存在（Sprint 57.13 carryover）

Sprint 57.13 是一個 ~15 US / Day 0-9 的大型 Foundation 完整化 sprint。它的 Day 4-8 改了大量前端 implementation（`<RequireAuth>` 共用 gate 取代各頁 inline gate、`components/ui/` 設計系統組件被現有頁面採用、governance `DecisionModal` 換成 Radix `<Dialog>`、cost/sla 的 error path 改用 `<ErrorRetry>` 標題從 "Error:" 變 "Failed to load data"、`auth-fixtures.ts`、login/callback 重寫、i18n 字串），但**對應的 Playwright e2e spec 沒同步更新**——Day 9 closeout 時 dev session 沒有 dev-server boot 能力（大 sprint 尾聲的時間/context 限制），只在 PR #130 兩輪 CI 修復裡補了一部分（auth-fixtures `**/` JSDoc bug → SyntaxError；5 個 tenant-page spec 加 `seedAuthJwt` beforeEach；a11y scan disable `color-contrast`；cost/sla error-path 文案 matcher）。整套 e2e 從沒在 dev session 跑綠過——這是 57.13 retrospective Q4 列的 `AD-Frontend-E2E-Sweep`。

另外 `visual-regression.spec.ts`（57.13 US-B8 NEW）ships `test.skip(!process.env.RUN_VISUAL, …)`：baseline 截圖必須在 CI Linux runner 產（本機 Windows 產的 PNG 因 font-hinting / sub-pixel 渲染差異會全 mismatch），所以 spec 在但沒 baseline、沒 un-skip——57.13 retrospective Q4 列的 `AD-Visual-Baseline-Generation`。

### 為什麼 dev session 跑得了 e2e（修正 57.13 的假設）

57.13 Day 9 closeout 寫「no dev-server/backend boot available」——那是大 sprint 尾聲的實務限制（時間 + context budget），不是技術限制。`frontend/playwright.config.ts` 的 `webServer` 已設好：local 跑 `npm run dev -- --port 5173 --strictPort`（`reuseExistingServer: true`），CI 跑 `npm run preview`。所以 `npx playwright test`（= `npm run e2e`）會自動起 Vite dev server。大多數 spec 用 `page.route()` 在網路層 mock backend（per `memory/feedback_e2e_network_mocking_pattern.md` — 比起真 backend 快 ~5x），所以**不需要起 backend**。只有 `connectivity.spec.ts`（`test.skip(!RUN_CONNECTIVITY)`）需要真 backend，`visual-regression.spec.ts`（`test.skip(!RUN_VISUAL)`）需要 Linux baseline——這兩個 Day 0 三-prong 確認後維持 opt-in。唯一前置：`npx playwright install chromium`（下載 Chromium，~150MB；Day 0 跑）。

### Visual baseline 的「不馬虎」原則

- **不在 Windows 產 baseline commit 進 repo**——那會讓 CI 第一次跑就 mismatch（cross-OS 渲染差異）。
- **落一個 CI 機制讓 baseline 在 Linux 產**：`playwright-e2e.yml` 加一個 `workflow_dispatch`-triggered job（`runs-on: ubuntu-latest`）跑 `RUN_VISUAL=1 npm run e2e -- visual --update-snapshots` → 把新增的 `tests/e2e/visual/*-snapshots/*.png` 用 `git add` + `git commit` + `git push` 回觸發的 branch（用 `GITHUB_TOKEN` + `permissions: contents: write`）。User（或 PR author）在這個 sprint 的 PR merge 後手動觸發一次該 workflow，baseline 就進 repo；之後 `visual-regression.spec.ts` 的 skip guard 改成「baseline dir 存在 → 跑；不存在 → skip 並印提示去觸發 workflow」，於是每次 CI e2e run 都會跑 visual diff。
- **這 sprint 落的是「機制 + 文件 + script + skip-guard 改寫」，不是 baseline PNG 本身**——baseline PNG 屬於那個 Linux workflow 的產物。誠實標：US-B1 的 DoD 是「workflow 存在 + 本機 dry-run 確認 spec list 解析 OK + 文件寫明一次性觸發步驟」；實際 baseline commit 列 retrospective Q4（`AD-Visual-Baseline-Generation` 從「碩大的 carryover」收斂成「跑一次已存在的 workflow」）。

### 17.md / V2 紀律對齊

- `17-cross-category-interfaces.md`：N/A——這 sprint 0 NEW agent-harness contract / ABC / LoopEvent / migration / API endpoint；只動前端 e2e spec + CI workflow。
- Multi-tenant 鐵律：N/A（不動 backend / DB / API）。
- LLM Provider Neutrality：N/A（不碰 `agent_harness/`；Playwright / @axe-core 非 LLM SDK）。
- CC Reference 不照搬：N/A（前端 e2e 維護）。
- 04 anti-patterns：AP-2 no orphan（visual workflow 有實際觸發路徑 + 文件；不是建了放著）；AP-4 no Potemkin（`visual-regression.spec.ts` un-skip 後真的會跑 diff，不是空殼）；AP-6 YAGNI（不順手做 inline-style cleanup / 不為「將來」加 Firefox/WebKit project）。

---

## User Stories

### Group A — E2E 套件跑綠

#### US-A1: 跑整套 Playwright e2e，triage 所有失敗

**作為** 維運者，**我希望** 整套前端 e2e 在 CI（與本機）跑得起來且綠，**以便** 前端 regression CI 真的有護欄（不是有 spec 但從沒跑綠）。

- `npx playwright install chromium`（Day 0；下載 Chromium browser binary）。
- `npm run e2e`（= `npx playwright test`）跑整套——playwright.config.ts 的 `webServer` 自動起 `npm run dev` 在 :5173；workers 預設（並行）。
- 把所有失敗分類：(a) stale selector（component DOM 改了，spec 還找舊 selector）；(b) stale assertion（文案/狀態改了）；(c) stale route-mock shape（API response 形狀改了，spec 的 `page.route()` mock 沒跟）；(d) 真 bug（implementation 壞了——預期 0，但若有則修 implementation 不修 spec，per RULES failure-investigation）；(e) flake（重跑穩定）。
- 在 progress.md Day 1 列每個失敗 spec + 分類 + 修法。
- **不改 implementation 來迎合 spec**（除非 (d) 真 bug）；不 disable / skip spec 來「跑綠」（per CLAUDE.md sacred rule + RULES failure-investigation）。

**驗收**: `npm run e2e`（排除 `connectivity` + `visual` 的 opt-in skip）→ 0 fail, 0 flake（重跑 2 次穩定）。

#### US-A2: 修掉所有 stale assertion / selector / route-mock

**作為** 開發者，**我希望** e2e spec 反映當前 implementation（57.13 Day 4-8 改動後的狀態），**以便** spec 抓得到真 regression 而非一直紅在過時的斷言。

- 逐一修 US-A1 triage 出的失敗：對齊 `<RequireAuth>` gate（`tests/e2e/fixtures/auth-fixtures.ts` 的 `seedAuthJwt` + 各 gated-page spec 的 `beforeEach`）、設計系統組件 swap（`<Skeleton>`/`<EmptyState>`/`<ErrorRetry>` 的 testid / role / 文案）、`DecisionModal` → Radix `<Dialog>`（governance approvals spec — `role="dialog"` 應保留，但 close 行為 / focus trap 可能要調 selector）、cost/sla error-path（"Failed to load data" 已在 PR #130 改，確認其他類似的）、login/callback 重寫（auth-flow / dev-login / four-page-gate spec）、i18n 字串（locale-switch spec + 任何斷言英文字串而該字串現在走 `t()` 的）。
- 每修一組跑該 spec 確認綠；最後跑全套確認。
- 若某 spec 的場景在 57.13 後已不適用（如 spec 測一個被移除的 inline gate）→ 重寫該 spec 測新場景（不刪 spec 檔——重寫；若整個場景消失則在 spec 內 `test.fixme(…, "<reason + carryover AD>")` 並列 retrospective，**不 silent delete**）。

**Tests**: e2e spec 本身就是 test；無新增 unit test（除非修 implementation 真 bug，那要附 unit test）。

**驗收**: `git diff` 顯示改的都是 `tests/e2e/**`（+ 可能 `playwright.config.ts`）；`npm run e2e` 綠；`npm run lint && npm run build && npm run test`（vitest）不受影響（baseline 236 pass）。

### Group B — Visual-regression enablement

#### US-B1: Linux CI baseline-generation 機制 + spec un-skip guard 改寫

**作為** 維運者，**我希望** `visual-regression.spec.ts` 的 baseline 能在 Linux CI 產且 commit 回 repo，之後每次 CI e2e run 自動跑 visual diff，**以便** UI 視覺 regression 有護欄（57.13 已寫 spec，缺 baseline + un-skip）。

- `.github/workflows/playwright-e2e.yml` — 加一個 NEW job `visual-baseline`（`if: github.event_name == 'workflow_dispatch'`；`runs-on: ubuntu-latest`；`permissions: contents: write`）：checkout（`ref: ${{ github.ref }}`）→ setup-node + `npm ci`（在 frontend/）→ `npx playwright install --with-deps chromium` → `RUN_VISUAL=1 npm run e2e -- visual --update-snapshots`（CI=true 下 Playwright 不會用 update mode 除非顯式 `--update-snapshots`，故顯式帶）→ `git add tests/e2e/visual/**/*-snapshots/*.png` → if changed: `git commit -m "chore(e2e): regenerate visual-regression baselines [skip ci]"` + `git push`。
- `frontend/package.json` — NEW script `"e2e:visual:update": "RUN_VISUAL=1 playwright test visual --update-snapshots"`（本機 Linux/WSL 可用；Windows 產的不該 commit——文件註明）。
- `frontend/tests/e2e/visual/visual-regression.spec.ts` — skip guard 改寫：原 `test.skip(!process.env.RUN_VISUAL, …)` → 改成「若 `tests/e2e/visual/visual-regression.spec.ts-snapshots/` 目錄存在（= baseline 已 commit）→ 跑；否則 `RUN_VISUAL` 未設 → skip 並印 `console.warn("[visual] no baselines committed yet — run the `visual-baseline` workflow_dispatch job to generate them on Linux, then this spec runs on every CI e2e run")`」。用 `fs.existsSync(path.join(__dirname, '<spec>-snapshots'))` 判斷（top-level，runner 載 spec 時跑）。
- `frontend/CONVENTION.md` — §e2e（或現有相關 §）補一段「Visual regression baselines: 只在 Linux 產（CI workflow_dispatch `visual-baseline` job 或 WSL `npm run e2e:visual:update`）；不 commit Windows 產的；新增/改 UI 影響截圖時重跑該 job」。
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-14/` — progress.md 記一次性觸發步驟（merge 後 `gh workflow run playwright-e2e.yml -f ...` 或 GitHub UI Actions → Run workflow）。

**驗收**: `playwright-e2e.yml` 有 `visual-baseline` job 且 YAML 合法（`actionlint` 或 `gh workflow view` 不報錯）；本機 `npm run e2e -- visual --list` 列出 6 個 visual test（spec 解析 OK）；`visual-regression.spec.ts` 的新 skip guard：無 baseline dir 時 spec skip 並印提示（本機跑 `npm run e2e -- visual` 觀察）。實際 baseline PNG commit = retrospective Q4 carryover（`AD-Visual-Baseline-Generation` 收斂為「跑一次 workflow」）。

### Group C — Closeout

#### US-C1: 驗證 sweep + retrospective + memory + doc syncs + PR

**作為** AI 助手，**我希望** sprint 收尾完整（驗證 / 文件 / memory / PR），**以便** 下個 session 接得上。

- Full validation sweep: `cd frontend && npm run lint && npm run build && npm run test`（vitest — baseline 236 pass，預期不變）+ `npm run e2e`（綠，排除 2 opt-in skip）；backend untouched — 跑 `cd backend && pytest -q` 確認 baseline（1676 pass + 4 skip）+ `python scripts/lint/run_all.py`（9/9）+ `mypy src`（0/306）作 sanity（這 sprint 不動 backend，預期全綠）。
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-14/progress.md` — Day 0-3 daily entries + D-PRE / D-DAY drift catalog。
- 同目錄 `retrospective.md` — Q1-Q7（Q2 ratio；Q4 carryover AD：`AD-Visual-Baseline-Generation`（收斂版）+ 若有 `test.fixme` 的 spec）；Q6 calibration class verdict。
- memory: `~/.claude/projects/.../memory/project_phase57_14_frontend_e2e_sweep.md` + `MEMORY.md` index +1 row。
- in-sprint doc syncs: `16-frontend-design.md`（V2 Ship Timeline +1 entry — e2e suite green + visual CI mechanism）/ `.claude/rules/sprint-workflow.md`（calibration matrix +1 row — `frontend-e2e-sweep` 0.50 1-data-point）/ `frontend/CONVENTION.md`（§e2e visual baseline note — 已在 US-B1）/ checklist [x] + plan/checklist header MHist closeout。
- post-merge doc syncs: `CLAUDE.md`（main HEAD + Latest Sprint row + Next Phase 候選 — 移除 AD-Frontend-E2E-Sweep，更新 AD-Visual-Baseline-Generation 為收斂版）/ `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md` §第八部分。
- PR: `git push` feature branch → `gh pr create`；solo-dev review_count=0；等 5 active CI checks 綠（**含這次跑綠的 playwright-e2e**）；merge 由 user 決定（surface PR，不自行 merge per executing-actions-with-care）。

**驗收**: PR 開好；5 active CI checks 綠；retrospective.md 8 條 sprint-workflow self-check 全 ✅；memory snapshot 寫好。

---

## Technical Specifications

### E2E triage 流程（US-A1 → US-A2）

```
1. Day 0: npx playwright install chromium  (一次性，~150MB)
2. npm run e2e  (auto webServer: npm run dev :5173)
   → 收集失敗清單。預期失敗來源（57.13 Day 4-8 改動）：
     - tests/e2e/fixtures/auth-fixtures.ts — seedAuthJwt 對應 cookie-only + RequireAuth（Day 1-2 已部分修；確認 9-page gate 全套）
     - tests/e2e/auth/*.spec.ts — auth-flow / dev-login / four-page-gate（login/callback 重寫 → selector）
     - tests/e2e/governance/approvals.spec.ts — DecisionModal → Radix Dialog（role="dialog" 保留；close / focus selector 可能調）
     - tests/e2e/cost-dashboard/*.spec.ts + sla-dashboard/*.spec.ts — ErrorRetry 文案（"Failed to load data" 已修；確認 loading skeleton testid）
     - tests/e2e/verification/*.spec.ts — verification tabs i18n（t("verification.tab.*")）
     - tests/e2e/memory/memory-page.spec.ts — design-system EmptyState/Skeleton swap
     - tests/e2e/chat/*.spec.ts — chat-v2 untouched this sprint（低風險；但 ApprovalCard 可能受 toast/queryClient 改動影響）
     - tests/e2e/i18n/locale-switch.spec.ts — 確認 selector（57.13 US-B5 寫的，可能本來就綠）
     - tests/e2e/a11y/a11y-scan.spec.ts — 9 routes axe scan（color-contrast disabled；確認 RequireAuth-gated 頁的 /auth/me mock 還對）
     - tests/e2e/admin_tenants/admin_tenants_list.spec.ts — seedAuthJwt(no tenantId) platform-level（Day 1-2 已修）
     - tests/e2e/smoke.spec.ts — 基本 / route（低風險）
3. 逐一修（per 分類 a/b/c/d/e）；每修跑該 spec；最後跑全套 + 重跑 2 次驗無 flake
4. git diff 確認只動 tests/e2e/**（+ 可能 playwright.config.ts）
```

### visual-regression.spec.ts skip guard 改寫（US-B1）

```typescript
// 現況（57.13）:
//   test.skip(!process.env.RUN_VISUAL, "set RUN_VISUAL=1 ... (baselines must be generated on Linux CI)");
// 改成:
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
const __dirname = dirname(fileURLToPath(import.meta.url));
const BASELINES_DIR = join(__dirname, "visual-regression.spec.ts-snapshots");
const HAS_BASELINES = existsSync(BASELINES_DIR);
// 跑條件：baseline 已 commit（HAS_BASELINES）OR 顯式 RUN_VISUAL（update mode / 本機 Linux）
test.skip(!HAS_BASELINES && !process.env.RUN_VISUAL,
  "[visual] no baselines committed yet — run the `visual-baseline` workflow_dispatch job " +
  "(.github/workflows/playwright-e2e.yml) to generate them on Linux, then this spec runs on every CI e2e run");
```

### `playwright-e2e.yml` NEW `visual-baseline` job（US-B1）

```yaml
  visual-baseline:
    name: Generate visual-regression baselines (Linux, manual)
    if: github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-latest
    permissions:
      contents: write
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.ref }}
          token: ${{ secrets.GITHUB_TOKEN }}
      - uses: actions/setup-node@v4
        with: { node-version: "20", cache: "npm", cache-dependency-path: frontend/package-lock.json }
      - run: npm ci
      - run: npx playwright install --with-deps chromium
      - run: RUN_VISUAL=1 npm run e2e -- visual --update-snapshots
      - name: Commit baselines if changed
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add tests/e2e/visual/**/*-snapshots/ || true
          if ! git diff --cached --quiet; then
            git commit -m "chore(e2e): regenerate visual-regression baselines [skip ci]"
            git push
          else
            echo "no baseline changes"
          fi
```
（`workflow_dispatch` trigger 需加到 `playwright-e2e.yml` 的 `on:` — Day 0 三-prong 確認現有 `on:` block。）

### Calibration class

NEW class `frontend-e2e-sweep` — HYBRID weighted blend over the 3 USs:
- US-A1+A2 (run suite + fix stale assertions) ≈ `test-maintenance-mechanical × 0.45` weight ~0.65 of sprint
- US-B1 (visual CI workflow + skip-guard + script + doc) ≈ `ci-infra-new × 0.55` weight ~0.20
- US-C1 (closeout) ≈ `closeout × 0.80` weight ~0.15
- Weighted blend ≈ **0.50** mid-band. Pending 2-3 future e2e-sweep sprints to validate (recurring shape — `AD-Frontend-E2E-Sweep` will recur whenever a large feature sprint outpaces its e2e specs).

---

## File Change List

> 完整精確清單在 Day 0 三-prong 後於 checklist 落實；以下為 plan 層級概覽。

### NEW Frontend
- （無 NEW source）— 可能 NEW `frontend/tests/e2e/visual/visual-regression.spec.ts-snapshots/*.png`（由 CI `visual-baseline` job 產 — 不在本 dev session）

### MODIFIED Frontend
- `frontend/tests/e2e/**/*.spec.ts` — stale assertion / selector / route-mock 修正（範圍 Day 1 triage 後確定；預期 ~3-8 檔）
- `frontend/tests/e2e/fixtures/auth-fixtures.ts` — `seedAuthJwt` / mock helper 對齊 cookie-only + RequireAuth（若 Day 1-2 修的還不全）
- `frontend/tests/e2e/visual/visual-regression.spec.ts` — skip guard 改寫（baseline-dir-exists OR RUN_VISUAL）
- `frontend/playwright.config.ts` — 視 triage 需要（如 timeout 調整 / project 設定 — 預期最小或不動）
- `frontend/package.json` — NEW script `e2e:visual:update`
- `frontend/CONVENTION.md` — §e2e visual baseline note（只在 Linux 產 / CI workflow_dispatch / 不 commit Windows 產的）

### MODIFIED CI / DevOps
- `.github/workflows/playwright-e2e.yml` — `on:` 加 `workflow_dispatch` + NEW `visual-baseline` job（ubuntu-latest, contents: write, RUN_VISUAL update + auto-commit）

### Doc syncs
- in-sprint: `docs/03-implementation/agent-harness-planning/.../16-frontend-design.md`（V2 Ship Timeline +1 — e2e suite green + visual CI）/ `.claude/rules/sprint-workflow.md`（calibration matrix +1 row — `frontend-e2e-sweep` 0.50）/ `frontend/CONVENTION.md`（已上）/ checklist [x] + plan/checklist MHist closeout
- post-merge: `CLAUDE.md`（main HEAD / Latest Sprint / Next Phase 候選 — 移除 AD-Frontend-E2E-Sweep，AD-Visual-Baseline-Generation 收斂）/ `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md` §第八部分

---

## Acceptance Criteria

### Functional
- [ ] (A1) `npx playwright install chromium` done；`npm run e2e` 跑得起來（auto webServer）；所有失敗 triage 並分類記在 progress.md Day 1。
- [ ] (A2) `npm run e2e`（排除 `connectivity` + `visual` 的 opt-in skip）→ 0 fail；重跑 2 次無 flake。`git diff` 只動 `tests/e2e/**`（+ 可能 `playwright.config.ts`）；無 implementation 改動（除非真 bug — 那要附 unit test + FIX-XXX）。無 `test.skip`/`test.only` 留在 spec 裡（除既有 2 opt-in skip + 任何新 `test.fixme` 必附 reason + carryover AD）。
- [ ] (B1) `playwright-e2e.yml` 有 `workflow_dispatch` trigger + `visual-baseline` job（ubuntu-latest / contents: write / RUN_VISUAL update + auto-commit）且 YAML 合法。`package.json` 有 `e2e:visual:update` script。`visual-regression.spec.ts` skip guard 改成「baseline dir 存在 OR RUN_VISUAL → 跑；否則 skip + console.warn 指向 workflow」。`CONVENTION.md` §e2e 有 visual baseline 規範。本機 `npm run e2e -- visual --list` 列 6 visual tests。
- [ ] (C1) full validation sweep 綠：`npm run lint`（silent）+ `npm run build`（main bundle ~297.89 kB 不變）+ `npm run test`（vitest 236 pass）+ `npm run e2e`（綠，排除 2 opt-in）；backend untouched sanity：`pytest -q`（1676 pass + 4 skip）+ `python scripts/lint/run_all.py`（9/9）+ `mypy src`（0/306）。

### Non-functional
- pytest baseline 1676 + 4 skip — 不變（不動 backend）；mypy --strict 0/306 — 不變；9 V2 lints 9/9 — 不變；Vitest 236 — 不變（不動 unit test，除非真 bug 修 implementation）；Vite build main bundle 297.89 kB — 不變；ESLint silent；LLM SDK leak 0；新增 0 npm runtime dep（`e2e:visual:update` 只是 script，不裝新 package）。
- Playwright e2e suite — 從「有 spec、從沒跑綠」變「跑綠」（排除 2 opt-in skip）；CI `playwright-e2e` check 綠。

### Sprint workflow discipline
- Phase README（無需，沿用 phase-57-frontend-saas）→ plan（本檔）→ checklist → Day 0 三-prong → code（Day 1-2）→ 每 day update checklist + progress.md → retrospective（Day 3）→ PR。
- 三-prong（Day 0）：Prong 1 path verify（所有 e2e spec 檔 + `playwright-e2e.yml` + `auth-fixtures.ts` 存在；`visual-regression.spec.ts-snapshots/` 不存在）+ Prong 2 content verify（`playwright.config.ts` webServer 設定確認 / `playwright-e2e.yml` 現有 `on:` + jobs / `auth-fixtures.ts` 現況 seedAuthJwt 簽名 / visual-regression.spec.ts 現有 skip guard / 是否裝了 chromium browser）+ Prong 3 schema verify（N/A — 不動 DB / migration）。

### V2 紀律 9 項 self-check（each commit + PR）
1. Server-Side First — N/A（不動 backend）；前端 e2e 維護
2. LLM Provider Neutrality — N/A（不碰 agent_harness）；Playwright / @axe-core 非 LLM SDK
3. CC Reference 不照搬 — N/A
4. 17.md Single-source — N/A（0 NEW agent-harness contract/ABC/LoopEvent/migration/API）
5. 11+1 範疇 — N/A（純前端 e2e + CI workflow；無範疇雜湊）
6. 04 anti-patterns — AP-2 no orphan（visual workflow 有觸發路徑 + 文件）/ AP-4 no Potemkin（un-skip 後真跑 diff）/ AP-6 YAGNI（不順手 inline-style cleanup / 不加多瀏覽器）
7. Sprint workflow — plan→checklist→三-prong→code→progress→retro，無跳步
8. File header convention — plan/checklist/progress/retrospective header + MHist 1-line max；e2e spec 改動更新 MHist（若 Behavioral）
9. Multi-tenant rule — N/A（不動 backend / DB / API）

---

## Deliverables (checklist mapping)

- [ ] US-A1: `npx playwright install chromium` + `npm run e2e` 跑 + triage 全失敗 → progress.md Day 1 分類表
- [ ] US-A2: 修所有 stale assertion/selector/route-mock → `npm run e2e` 綠（排除 2 opt-in）+ 重跑無 flake + git diff 只動 tests/e2e/**
- [ ] US-B1: `playwright-e2e.yml` workflow_dispatch + visual-baseline job + `package.json` e2e:visual:update script + `visual-regression.spec.ts` skip-guard 改寫 + CONVENTION.md §e2e note
- [ ] US-C1: full validation sweep + retrospective Q1-Q7 + memory snapshot + 3 in-sprint doc syncs + PR (+ 2 deferred post-merge)

---

## Dependencies & Risks

### External dependencies
- `npx playwright install chromium` — 下載 Chromium browser binary（~150MB；一次性；不是 npm package，不進 bundle / package.json）。無 license 問題。CI 已 `npx playwright install --with-deps chromium`（現有 `playwright-e2e.yml`）。
- 0 NEW npm package（`e2e:visual:update` 只是 script）。

### Risk matrix

| Risk | 機率 | 影響 | 緩解 |
|------|------|------|------|
| dev session 跑不了 Playwright（webServer `npm run dev` 起不來 / Chromium 裝不上 / sandbox 限制） | 中 | 高（US-A1/A2 核心做不了）| Day 0 三-prong 先試 `npx playwright install chromium` + `npm run e2e -- smoke.spec.ts`（一個輕量 spec）確認管線通；若真跑不了 → US-A1/A2 退化成「靜態審計每個 spec vs 對應 component 找 stale assertion 並修 + spec parse/list 確認 + `npm run e2e --list`」，實際綠-verify 列 carryover（誠實標 🚧 + reason）——但這是退化路徑，先試真跑 |
| 失敗太多（57.13 Day 4-8 改動廣）→ 一天修不完 | 中 | 中 | Day 1 triage 後若估超 → Day 2 也用於修（plan 已留 Day 1-2 給 A 組）；若仍超 → 該批 spec 走 minimal（先修高價值的 auth/governance/cost/sla，剩餘 chat-v2/memory 等低風險的標 🚧 + carryover AD `AD-Frontend-E2E-Sweep-Round2`）——**不刪 spec / 不 disable** |
| Radix DecisionModal 的 focus-trap / portal 讓 governance approvals spec 的 selector 難對 | 中 | 低 | Radix Dialog 把內容 render 到 portal（document.body 末）——spec 若用 `page.locator('.modal …')` 範圍查可能失準；改用 `page.getByRole('dialog')` / `page.getByRole('button', {name})` （Radix 保留 ARIA roles）；57.13 D-DAY5-3 已記「preserved role='dialog' + button names + ESC/outside-click」故理論上 selector 可對 |
| visual-baseline workflow 的 auto-commit 因 branch protection（required checks）push 失敗 | 低 | 低（baseline 是 carryover）| `[skip ci]` 在 commit message 避免無限觸發；push 到 feature branch（非 main）不受 branch protection 的 required-checks 擋（那擋的是 merge 不是 push）；若 main 被 protect 不准 bot push → workflow 改成上傳 baseline 為 artifact + 文件說手動下載 commit（fallback；Day 2 試 push 路徑） |
| 改 e2e spec 引入新 flake（timing-sensitive） | 中 | 中 | 每修跑該 spec 3 次；最後全套跑 2 次；用 Playwright 的 auto-waiting（`getByRole` / `toBeVisible`）不用 `waitForTimeout`；flake spec 加 `test.describe.configure({ retries: 1 })`（不是 disable） |

### Roll-back plan
- 每組修一個 commit；若某組修壞可單獨 revert（feature branch）。
- 整個 branch 在 PR 前都可 reset；merge 後若有問題開 hotfix PR。
- 若 dev session 完全跑不了 Playwright（最壞）→ sprint 退化為「靜態 spec audit + 修 + CI 跑綠驗證（依賴 PR CI run）」+ visual CI 機制（這部分不依賴本機跑）——核心交付（spec 對齊 implementation + visual 機制）仍達成，只是「在 dev session 親手跑綠」變成「靠 CI 跑綠」。

---

## Workload (calibrated)

### Bottom-up estimate by US
| US | 估計 | 備註 |
|----|------|------|
| A1 | 1-2 hr | install chromium + 跑全套 + triage 分類（跑本身慢但人工成本低；triage 寫表） |
| A2 | 4-6 hr | 修所有 stale assertion/selector/route-mock（範圍視 triage；57.13 Day 4-8 改動廣，估 3-8 檔）+ 每修跑驗 + 最後全套跑 2 次 |
| B1 | 2-3 hr | playwright-e2e.yml workflow_dispatch + visual-baseline job + e2e:visual:update script + skip-guard 改寫 + CONVENTION.md note + 本機 dry-run（--list） |
| C1 | 1-2 hr | full validation sweep + retrospective Q1-Q7 + memory + 3 doc syncs + PR |
| **Bottom-up total** | **~8-13 hr** | |

### Calibrated commit
Class `frontend-e2e-sweep` HYBRID 0.50 (1st application) → **8-13 hr × 0.50 ≈ 4-6.5 hr** committed. Day 0-3（4 days；Day 0 setup+三-prong / Day 1-2 Group A+B / Day 3 closeout）。Day 3 retrospective Q2 驗 ratio；若 |delta| > 30% → 記 AD-Sprint-Plan-N。

> **這是 focused 維護 sprint**（~4-6.5 hr，比平常 5-day sprint 小）。不切分（已夠小）。Day 數 4（Day 0-3）而非預設 5——scope 已小，5 天會是 padding；per sprint-workflow.md §Step 2 「scope 差異透過內容調整」，此處透過減少 Day 數反映 scope（仍含完整 Day 0 三-prong + Day N closeout 結構）。
