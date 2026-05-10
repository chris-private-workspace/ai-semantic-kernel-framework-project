---
File: docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-14-checklist.md
Purpose: Sprint 57.14 execution checklist — AD-Frontend-E2E-Sweep (e2e suite green + visual baseline CI mechanism; ~4 USs / Day 0-3).
Category: Frontend / e2e / DevOps (CI)
Scope: Phase 57 / Sprint 57.14

Created: 2026-05-10 (drafted post-plan approval)
Last Modified: 2026-05-10
Status: Draft

Modification History (newest-first):
    - 2026-05-10: Initial creation (Sprint 57.14 — mirrors 57.13 day-structure, condensed to Day 0-3 for focused maintenance scope)

Related:
    - sprint-57-14-plan.md (sibling plan — authority for this checklist)
    - sprint-57-13-checklist.md (structural template per sprint-workflow.md §Step 2 — most recent completed sprint)
---

# Sprint 57.14 — Checklist (Day 0-3)

> Branch: `feature/sprint-57-14-frontend-e2e-sweep`
> Calibration: `frontend-e2e-sweep` HYBRID 0.50 (1st application)
> Bottom-up ~8-13 hr → committed ~4-6.5 hr
> Focused maintenance sprint (smaller than normal 5-day; Day 0-3). Closes Sprint 57.13 carryover `AD-Frontend-E2E-Sweep` + lands the `AD-Visual-Baseline-Generation` mechanism.

---

## Day 0 — Setup + Branch + Pre-flight + 三-prong + Calibration

### 0.1 Branch creation
- [x] **Branch `feature/sprint-57-14-frontend-e2e-sweep` from main `2766dc90`** ✅
  - Verify: `git branch --show-current` → `feature/sprint-57-14-frontend-e2e-sweep`; `git rev-parse main` → `2766dc90...`

### 0.2 Pre-flight baseline capture (post Sprint 57.13)
- [x] pytest baseline = **1676 pass + 4 skip** (1680 collected) — not touched this sprint, sanity only
- [x] mypy --strict baseline = **0 / 306 files** — not touched, sanity only
- [x] 9 V2 lints baseline = **9/9 green** — not touched, sanity only
- [x] Vitest baseline = **236 / 57 files** — not touched (unless real-bug fix)
- [x] Playwright baseline = **18 spec files** (incl. 2 opt-in skips: connectivity / visual-regression) — **never run green** (this sprint's target)
- [x] Vite build main bundle baseline = **297.89 kB (gzip 95.27)** — not touched, sanity only
- [x] LLM SDK leak baseline = **0** — not touched, sanity only
- [x] Chromium browser binary installed — `chromium-1217` ↔ Playwright 1.59.1 ✅ (no install needed)

### 0.3 Day 0 三-prong verify (per AD-Plan-1+3+4 promoted rules) — DONE 2026-05-10; 4 D-PRE catalogued in progress.md (1🟢 / 3🟡); 0 abort
- [x] **Prong 1 Path Verify** — 18 e2e spec files + `auth-fixtures.ts` + `playwright.config.ts` + `playwright-e2e.yml` + `package.json` + `CONVENTION.md` + `16-frontend-design.md` + `sprint-workflow.md` exist; `tests/e2e/visual/visual-regression.spec.ts-snapshots/` does NOT exist (NEW, expected). DoD: D-PRE table in progress.md ✅
- [x] **Prong 2 Content Verify** — `playwright.config.ts` webServer (local `npm run dev` :5173 `reuseExistingServer:true` / CI `npm run preview`); `playwright-e2e.yml` `on:` = push+pull_request (NO `workflow_dispatch` → D-PRE-1); `auth-fixtures.ts` already authStore-based, `seedAuthJwt` stable, `**/` JSDoc bug + 5-spec beforeEach already fixed in PR #130 (D-PRE-2 — reduces US-A2 scope); `visual-regression.spec.ts` current `test.skip(!RUN_VISUAL)` + 6 toHaveScreenshot; chromium-1217 present. DoD: drift findings catalogued ✅
- [x] **Prong 3 Schema Verify** — **N/A** (0 DB / migration / ORM model / API endpoint touched this sprint). Noted in progress.md ✅

### 0.4 Calibration baseline confirmation
- [x] **Documented in progress.md Day 0** — Class `frontend-e2e-sweep` HYBRID 0.50 (1st app, 1-data-point opens); bottom-up ~8-13 hr → committed ~4-6.5 hr; Day 0-3; Day 3 retro Q2 verify ratio

### 0.5 Day 0 smoke probe (de-risk US-A1/A2 — per plan §Risk matrix)
- [x] **`npx playwright install chromium`** — already installed (no-op; `chromium-1217`) ✅
- [x] **`npm run e2e -- smoke.spec.ts`** → **2 passed (5.5s)** — pipeline works in this dev session (webServer auto-start `npm run dev` :5173 + chromium launch) ✅ → US-A1/A2 proceed on the real-run path (D-PRE-4)

### 0.6 Day 0 commit
- [ ] **Commit Day 0 baseline + plan + checklist + progress Day 0**
  - Files: `sprint-57-14-{plan,checklist}.md` + `agent-harness-execution/phase-57/sprint-57-14/progress.md`
  - Message: `chore(sprint-57-14, Day 0): plan + checklist + 三-prong baseline`
  - DoD: 1 commit on feature branch

---

## Day 1 — US-A1 (run suite + triage) + US-A2 (fix) — DONE 2026-05-10 (commit pending)

### 1.1 US-A1: run full e2e suite + triage
- [x] **`npm run e2e`** → **39 passed / 1 failed / 7 skipped** (47 tests / 18 spec files; 7 skipped = 1 connectivity + 6 visual-regression opt-in skips)
- [x] **Triage table in progress.md Day 1** — only 1 failing test: `a11y/a11y-scan.spec.ts:70` "gated pages …" — classification (d-ish) **hermeticity bug, not stale assertion**: mocked `/auth/me` but not data endpoints; a real backend on :8000 returned 401 on the data fetches → `handleAuthExpired` → redirect to `/auth/login` → shell never rendered. (PR #130 CI-round fixes had already synced auth-fixtures + tenant-page specs + cost/sla error-path — the carryover note over-estimated the regression.)

### 1.2 US-A2: fix
- [x] **`tests/e2e/a11y/a11y-scan.spec.ts`** — root-cause fix: NEW `mockApi(page, authMe)` registers catch-all `**/api/v1/**` → 503 FIRST + `**/api/v1/auth/me` → 200/401 SECOND (more-specific last-registered wins for `/auth/me`; catch-all 503 for all other API → page renders `<ErrorRetry>` which axe still scans, never a 401 → no redirect → hermetic regardless of a running backend) + `await page.waitForLoadState("networkidle")` after each `goto` before `scan(...)` (settle client redirects + mocked fetches before axe injects/evaluates). File-header MHist + Description updated.
- [x] **`tests/e2e/fixtures/auth-fixtures.ts`** — NOT touched (D-PRE-2: already synced by PR #130; stale header NOTE left — Trivial-tier, untouched file)
- [x] No `src/` change; no implementation change; no new unit test (the bug was in the *test's* hermeticity, not the app)
  - Verify: ✅ `npx playwright test a11y/a11y-scan.spec.ts` → 2 passed (12.8s); `npx playwright test` (full) → **40 passed / 7 skipped / 0 failed** ×3 runs (no flake); `git diff` only `tests/e2e/a11y/a11y-scan.spec.ts`
- [x] **Day 1 progress entry** + drift catalog (D-DAY1-1 scope-reducing / D-DAY1-2 backend on :8000)
- [ ] **Day 1 commit**: `fix(sprint-57-14, Day 1): US-A1 e2e triage + US-A2 a11y-scan hermeticity (mock all /api/v1/**)`

### Day 2.1 — US-A2 remaining specs (verification / memory / chat-v2 / a11y / i18n / admin-tenants / smoke) — DONE 2026-05-10 (all already green)
> Collapsed into Day 1: the triage (1.1) showed the *only* failure was a11y-scan; every other spec already passes. The PR #130 CI-round fixes had synced the rest.
- [x] **`tests/e2e/verification/*.spec.ts`** — 4 tests pass (verification tabs i18n already aligned)
- [x] **`tests/e2e/memory/memory-page.spec.ts`** — 1 test pass (design-system swap already aligned)
- [x] **`tests/e2e/chat/*.spec.ts`** (approval-card ×4 / chat-v2-ship ×2 / chat-v2-loop-inline / chat-v2-subagent-inline) — all pass (chat-v2 untouched this sprint; toast/queryClient changes didn't break ApprovalCard)
- [x] **`tests/e2e/a11y/a11y-scan.spec.ts`** — fixed in 1.2 (hermeticity); color-contrast still disabled at baseline (chat-v2 inline styles — separate `AD-Inline-Style-Cleanup-Sweep`)
- [x] **`tests/e2e/i18n/locale-switch.spec.ts`** — passes (locale switcher selectors fine)
- [x] **`tests/e2e/admin_tenants/admin_tenants_list.spec.ts`** — 4 tests pass (`seedAuthJwt` + RequireAuth gate fine)
- [x] **`tests/e2e/smoke.spec.ts` + `loop-debug/loop-debug-standalone.spec.ts`** — pass
- [x] **`npm run e2e`** (full, excl. 2 opt-in skips) → 0 fail; re-run ×2 → no flake
  - Verify: ✅ `git diff` only `tests/e2e/a11y/a11y-scan.spec.ts`; no `src/` change; no stray `test.skip`/`test.only`/`test.fixme`

---

## Day 2 — US-B1 visual CI mechanism + US-C1 closeout

### 2.2 US-B1: visual-regression CI mechanism + skip-guard rewrite — DONE 2026-05-10 (commit pending)
- [x] **`.github/workflows/playwright-e2e.yml`** — `on:` += `workflow_dispatch`; `e2e` job += `if: github.event_name != 'workflow_dispatch'`; NEW `visual-baseline` job (`if: workflow_dispatch`; ubuntu-latest; `permissions: contents: write`; checkout `ref: github.ref` + `token: GITHUB_TOKEN`; setup-node 20 + `npm ci`; cache + `npx playwright install --with-deps chromium`; `npm run build`; `RUN_VISUAL=1 npx playwright test visual --update-snapshots`; `git add tests/e2e/visual/**/*-snapshots/` + commit `chore(e2e): regenerate visual-regression baselines [skip ci]` + `git push origin HEAD:${{ github.ref_name }}` if changed; upload `visual-baselines` artifact always)
- [x] **`frontend/package.json`** — NEW script `"e2e:visual:update": "RUN_VISUAL=1 playwright test visual --update-snapshots"` (Linux/WSL only)
- [x] **`tests/e2e/visual/visual-regression.spec.ts`** — skip-guard rewrite: `import {existsSync}'node:fs'` + `dirname/join`'node:path' + `fileURLToPath`'node:url'; `SNAPSHOTS_DIR = join(dirname(fileURLToPath(import.meta.url)), "visual-regression.spec.ts-snapshots")`; `RUN_VISUAL = existsSync(SNAPSHOTS_DIR) || Boolean(process.env.RUN_VISUAL)` → auto-un-skips once the `-snapshots/` dir is committed; skip message points to the `visual-baseline` workflow + CONVENTION.md §e2e. File-header Description + MHist updated.
- [x] **`frontend/CONVENTION.md`** — §8: NEW "### Hermetic API mocking (mock the catch-all, not just one route)" + NEW "### Visual regression baselines (Sprint 57.14)" sub-sections; MHist += 57.14 entry (+ backfill 57.13 §10-13 entry); `Last Modified` → 2026-05-10
  - Verify: ✅ YAML valid (`yaml.safe_load` → jobs `[e2e, visual-baseline]`, on `[push, pull_request, workflow_dispatch]`); `npx playwright test visual --list` → 6 tests listed; `npx playwright test visual` → 6 skipped (guard works — no `-snapshots/` dir); `npx playwright test` (full) → 40 passed / 7 skipped / 0 failed (visual changes safe)
  - Note: actual baseline PNG commit NOT done in this dev session (Windows → cross-OS mismatch). The `visual-baseline` workflow produces them; one-shot trigger documented in progress.md Day 2 → `AD-Visual-Baseline-Generation` converges from "carryover" to "run the workflow once post-merge".
- [x] **Day 2 progress entry** + verify notes
- [ ] **Day 2 commit**: `feat(sprint-57-14, Day 2): US-B1 visual-regression CI baseline mechanism + auto-un-skip guard`

---

## Day 3 — US-C1: validation sweep + retrospective + memory + doc syncs + PR

### 3.1 US-C1: full validation sweep
- [ ] **Frontend**: `cd frontend && npm run lint`(silent) + `npm run build`(main 297.89 kB) + `npm run test`(vitest 236 pass) + `npm run e2e`(green, excl. 2 opt-in skips; re-run ×2)
- [ ] **Backend sanity (untouched — confirm baseline)**: `cd backend && pytest -q`(1676 pass + 4 skip) + `python scripts/lint/run_all.py`(9/9) + `mypy src`(0/306) + `python scripts/lint/check_llm_sdk_leak.py`(OK)
  - DoD: all green; any deviation investigated (not skipped)

### 3.2 US-C1: routes / docs cross-check
- [ ] `routes.config.ts` — no change expected (no routing change this sprint); confirm
- [ ] 17.md — no change (0 NEW agent-harness contract/ABC/LoopEvent/migration/API); confirm

### 3.3 US-C1: retrospective.md (Q1-Q7)
- [ ] **NEW `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-14/retrospective.md`**
  - Q1 what shipped / Q2 estimate ratio (actual ÷ committed; verify `frontend-e2e-sweep` 0.50) / Q3 surprises (incl. bundle/build deltas — expected none) / Q4 carryover ADs (`AD-Visual-Baseline-Generation` converged version; any new `test.fixme` specs; `AD-Inline-Style-Cleanup-Sweep` still open separately) / Q5 next-phase candidates (names only — rolling) / Q6 calibration verdict (KEEP / adjust `frontend-e2e-sweep` 0.50) / Q7 design-note extract (N/A — not a spike sprint)
  - 8-point sprint-workflow self-check: plan→checklist→三-prong→code→update→progress→retro→PR all ✅

### 3.4 US-C1: memory snapshot
- [ ] **NEW `~/.claude/projects/C--Users-Chris-Downloads-ai-semantic-kernel-framework-project/memory/project_phase57_14_frontend_e2e_sweep.md`** + **`MEMORY.md` index +1 row** (Recent Sprints section, top)

### 3.5 US-C1: doc syncs (in-sprint)
- [ ] `16-frontend-design.md` — V2 Ship Timeline +1 entry (e2e suite green + visual CI mechanism)
- [ ] `.claude/rules/sprint-workflow.md` — calibration matrix +1 row (`frontend-e2e-sweep` 0.50 1-data-point ratio <result> KEEP) + MHist
- [ ] `frontend/CONVENTION.md` — §e2e visual baseline note (already done in US-B1; confirm)
- [ ] checklist [x] + plan/checklist header MHist closeout (Status: Draft → Closed)
- [ ] **Deferred post-merge** (not in this PR): `CLAUDE.md` (main HEAD + Latest Sprint row + Next Phase 候選 — remove `AD-Frontend-E2E-Sweep`, update `AD-Visual-Baseline-Generation` to converged version) + `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md` §第八部分

### 3.6 US-C1: PR open + closeout sync
- [ ] **`git push -u origin feature/sprint-57-14-frontend-e2e-sweep`**
- [ ] **`gh pr create`** — title `Sprint 57.14 — AD-Frontend-E2E-Sweep (e2e suite green + visual baseline CI mechanism)`; body: summary + test plan + V2 紀律 9 項 self-check + carryover note + post-merge doc-sync TODO + one-shot visual-baseline trigger note
- [ ] **Verify 5 active CI checks green** — incl. `playwright-e2e` (this sprint's target — should now be green)
- [ ] **Squash merge** — 🚧 NOT done in-session: per executing-actions-with-care, squash-merge to `main` is surfaced to the user for confirmation (PR open + CI green → user decides)

### 3.7 Day 3 progress entry + commit
- [ ] **Day 3 progress entry** (validation sweep results + closeout)
- [ ] **Day 3 commit**: `chore(sprint-57-14, Day 3): retrospective + memory + doc syncs + closeout`

---

## 重要備註

### Rolling planning 紀律自檢（每 day 結束 + Day 3 closeout 必檢）
- ☑ 沒預寫 57.15 sprint plan（Phase 57.15+ candidates 只列候選名於 retrospective Q5）
- ☑ 沒跳過 plan/checklist 直接 code（Day 0 plan + checklist 完整；Day 1 起 code）
- ☑ 沒刪除未勾選 [ ] 項（用 [x] 完成 / 🚧 阻塞 + reason / `test.fixme` + reason + carryover AD → 不 silent delete spec）
- ☑ 沒在 retrospective 寫具體未來 sprint task（Q5 只列候選）

### Scope 控管（focused 維護 sprint）
- 若 US-A2 失敗太多一天修不完 → Day 1-2 都給；仍超 → 修高價值（auth / governance / cost / sla / verification），剩餘低風險（chat-v2 / memory / smoke）標 🚧 + reason → carryover AD `AD-Frontend-E2E-Sweep-Round2`（**不刪 spec / 不 disable**）
- 若 dev session 完全跑不了 Playwright（最壞，Day 0 smoke probe 失敗）→ US-A1/A2 退化為「靜態 spec audit vs component 找 stale assertion 並修 + `npm run e2e --list` parse-verify」，實際綠-verify 列 carryover（🚧 + reason；靠 PR CI run 驗）——但先試真跑（Day 0 0.5）
- visual baseline PNG 本身**不在本 dev session 產**（Windows 產的 cross-OS mismatch）；本 sprint 落機制 + script + skip-guard + 文件；baseline commit = retrospective Q4 carryover「跑一次已存在的 `visual-baseline` workflow」（`AD-Visual-Baseline-Generation` 從碩大 carryover 收斂成小步驟）

### V2 紀律 9 項自檢（每 commit + 每 PR — per plan §Acceptance Criteria）
1. ✅ Server-Side First — N/A（不動 backend）；前端 e2e 維護
2. ✅ LLM Provider Neutrality — N/A（不碰 agent_harness）；Playwright / @axe-core 非 LLM SDK
3. ✅ CC Reference 不照搬 — N/A
4. ✅ 17.md Single-source — N/A（0 NEW agent-harness contract/ABC/LoopEvent/migration/API）
5. ✅ 11+1 範疇 — N/A（純前端 e2e + CI workflow；無範疇雜湊）
6. ✅ AP-2/4/6 — no orphan（visual workflow 有觸發路徑 + 文件）/ no Potemkin（un-skip 後真跑 diff）/ YAGNI（不順手 inline-style cleanup / 不加多瀏覽器 project）
7. ✅ Sprint workflow — plan→checklist→三-prong→code→progress→retro，無跳步
8. ✅ File header MHist — plan/checklist/progress/retrospective header + e2e spec 改動更新 MHist（若 Behavioral）— 1-line max
9. ✅ Multi-tenant — N/A（不動 backend / DB / API）

### Sprint 57.x cascade lessons 強制執行
- ✅ Day-0 三-prong（path + content；schema N/A）必跑
- ✅ Day-0 smoke probe（`npm run e2e -- smoke.spec.ts`）de-risk 跑不跑得了 Playwright
- ✅ 修 spec 不修 implementation（除非真 bug — 那要附 unit test + FIX-XXX；per RULES failure-investigation）
- ✅ 不 disable / skip / `test.only` 來「跑綠」（per CLAUDE.md sacred rule）
- ✅ 每修一組跑該 spec ×3（flake check）；最後全套跑 ×2
- ✅ Playwright auto-waiting（`getByRole` / `toBeVisible`）不用 `waitForTimeout`（避免引入 flake）
- ✅ `[skip ci]` 在 visual-baseline auto-commit message（避免無限觸發）

### Open Items / Carry-forward（填入 retrospective Q4）
- AD-Visual-Baseline-Generation（**收斂版**）— merge 後跑一次 `visual-baseline` workflow_dispatch job 產 + commit Linux baselines；之後 `visual-regression.spec.ts` 每次 CI e2e run 跑 diff
- AD-Frontend-E2E-Sweep-Round2（若 US-A2 scope overrun）— 剩餘低風險 spec 的 stale assertion 修正
- AD-Inline-Style-Cleanup-Sweep（**仍獨立 open**，非本 sprint）— ~15 檔 `style={{}}` → Tailwind（順帶解 chat-v2 color-contrast → 重開 a11y scan color-contrast rule）
- AD-Lighthouse-Visual-Hard-Gate — 從 continue-on-error / 新加的 visual 從 baseline 轉 required CI check（待 baseline 穩定後）
- AD-WorkOS-Prod-Redirect-Flow / AD-i18n-Feature-Namespaces / AD-Frontend-RUM-SessionReplay / AD-Bundle-Size(optional) — 57.13 carryover，未動
