# V2 Audit Carryover Cleanup — Session Onboarding Prompt

**用法**：開新 Claude Code session 後，把以下整段（從 `# 你的任務` 開始到檔案結束）貼給新 session。或者直接告訴它：「讀 `claudedocs/5-status/V2-AUDIT-CLEANUP-SESSION-ONBOARDING-PROMPT.md` 並按指示執行」。

**版本**: 2.0（2026-05-01 evening；P0 從 4 → 8 升級版）
**取代**: 嵌在主 session prompt §「Cleanup session onboarding prompt」段內的 1.0 版（過時，不要用）

---

# 你的任務

執行 V2 Verification Audit 累積的 **8 個 P0 critical** + **6 個 P1 high-priority** cleanup work。

**強制完成期限**：Phase 53.1 (worker fork 引入) 啟動之前。Phase 53.1 之後修補成本翻倍。

**本 session 不做開發 / 不做新功能**，只做 cleanup（修補 audit 發現的偏離）。

---

## 環境注意事項

⚠️ **本專案有 graphify post-commit / post-checkout hook bug**：commit 後會自動切換 branch（不是 dev 紀律問題，是 hook 副作用）。處理方式：
- 每個 git push 前先 `git branch --show-current` 驗證
- 推 main 永遠用 `git push origin main`（推 local main 不管 current branch）
- 如果 commit 後 branch 不對，用 `git checkout main && git cherry-pick <commit>` 修正
- 已知此 bug 影響主 session + audit session，cleanup session 也會遇到

⚠️ **Docker 服務不要停**：
- `ipa_v2_postgres`（healthy 多日）— 直接用，不要 docker-compose up/down/restart
- 干擾其他 session

⚠️ **不要修任何已 commit 的源碼**直到讀完必讀文件 + 寫 plan + checklist。

---

## 必讀文件（按序）

讀完才能開始實作。**完整讀過勿略**。

1. **`claudedocs/5-status/V2-AUDIT-OVERVIEW-ONEPAGE.md`**（5 min）
   — V2 audit 總圖；先讀掌握全局

2. **`claudedocs/5-status/V2-AUDIT-OPEN-ISSUES-20260501.md`**（5 min）
   — 8 P0 + 6 P1 + 6 process fixes 真相來源

3. **`claudedocs/5-status/V2-AUDIT-WEEK3-SUMMARY.md`**（10 min）
   — 雙層問題：50.2 偏離 + W3-0 process drift；4 P0 #11-14 來源

4. **`claudedocs/5-status/V2-AUDIT-MINI-W4-PRE-SUMMARY.md`**（10 min）
   — **最重要的單一文件**；揭露系統性 AP-4 pattern；4 新 P0 #15-18 來源

5. **`claudedocs/5-status/V2-AUDIT-CLEANUP-SPRINT-TEMPLATE.md`**（15 min）
   — 你的 plan + checklist 範本（Part 1 + Part 2，共 593 行）

6. **每個 P0 對應的詳細 audit 報告**（依需要查）：
   - P0 #11+#12 → `V2-AUDIT-W3-2-PHASE50-2.md`
   - P0 #13 → `V2-AUDIT-W1-AUDIT-HASH.md`
   - P0 #14 → `V2-AUDIT-W1-RLS.md`
   - P0 #15+#16 → `V2-AUDIT-W4P-1-PHASE49-4-D3-5.md`
   - P0 #17 → `V2-AUDIT-W4P-3-PHASE51-1.md`
   - P0 #18 → `V2-AUDIT-W4P-4-PHASE51-2.md`

7. **GitHub issues #11-18**（用 `gh issue view <N>` 讀）— 含 verification criteria + acceptance steps

---

## 8 P0 Cleanup 項目（全部必修）

| # | Issue | Effort | 主要影響檔案 |
|---|-------|--------|-------------|
| #11 | chat router multi-tenant 隔離 | 1-2d | `backend/src/api/v1/chat/{router,handler,session_registry,sse}.py` + tests |
| #12 | TraceContext propagation at chat handler | half day | `backend/src/api/v1/chat/handler.py`（與 #11 合併） |
| #13 | audit_log hash chain verifier | 2-3d | `backend/scripts/verify_audit_chain.py`（新建）+ docker-compose |
| #14 | JWT replace X-Tenant-Id header | 1-2d | `backend/src/platform_layer/{identity,middleware}/` |
| #15 | OTel SDK version lock to ==1.22.0 | 30 min | `backend/requirements.txt`（單行修改）|
| #16 | OTel main-flow tracer span coverage 5 places | 2-3d | `backend/src/adapters/azure_openai/adapter.py` + state_mgmt + chat handler |
| #17 | SubprocessSandbox Windows Docker isolation | 3-5d | `backend/src/agent_harness/tools/sandbox.py` 重寫 |
| #18 | memory_tools handler tenant from ExecutionContext | 1d | `backend/src/agent_harness/memory/tools.py`（或類似）|

**總工時**: 12-17 days → 安排 **10-14 day sprint**

---

## 6 P1（cleanup sprint Day 6 一次清完）

| # | 項目 | Effort |
|---|------|--------|
| W2-1 #4 | `adapters/azure_openai/tests/test_integration.py` 新建 | 1d |
| W2-2 #6 | `requirements.txt` 清 Celery + 加 temporalio TODO | 30 min |
| W2-2 #7 | 統一 worker 目錄（`runtime/workers/` ↔ `platform_layer/workers/`）| half day |
| W2-2 #8 | AgentLoopWorker docstring stub warning | 1 hour |
| W3-1 | mutable LoopState → frozen + reducer | 等 53.1 一起做 |
| W3-1 | ToolCallExecuted/Failed event owner drift | 等 51.x 處理 |

P1 後兩項建議 defer（不在本 sprint 範圍）。

---

## 執行流程（per cleanup template + 紀律強化）

### Step 1：Setup（Day 0，2 hours）

```bash
# 1.1 建 phase folder
mkdir -p docs/03-implementation/agent-harness-planning/phase-52-5-audit-carryover
mkdir -p docs/03-implementation/agent-harness-execution/phase-52-5/sprint-52-5-audit-carryover

# 1.2 從 main 開 feature branch
git checkout main
git pull origin main
git branch --show-current  # 必驗
git checkout -b feature/sprint-52-5-audit-carryover
git branch --show-current  # 再驗
```

### Step 2：客製 cleanup template（Day 0，2 hours）

從 `V2-AUDIT-CLEANUP-SPRINT-TEMPLATE.md` Part 1 + Part 2 複製到：
- `docs/03-implementation/agent-harness-planning/phase-52-5-audit-carryover/sprint-52-5-plan.md`
- `docs/03-implementation/agent-harness-planning/phase-52-5-audit-carryover/sprint-52-5-checklist.md`

客製 5 處 TBD：
- Sprint number → `52.5`
- Phase folder → `phase-52-5-audit-carryover`
- Duration → 10-14 days（升級因 P0 從 4 → 8）
- Branch → `feature/sprint-52-5-audit-carryover`
- Owner → `User-spawned cleanup session 2026-05-01+`

**重要**：upgrade plan 加 P0 #15-18 內容（template 原本只有 P0 #11-14；自行擴充參考 mini-W4-pre summary §3）

### Step 3：執行 P0（Day 1-7+）

按 effort 與 dependency 排序：

**Day 1（quick wins，建立信心）**
- P0 #15 OTel SDK lock（30 min）
- P0 #14 JWT replace（half day 起手 — 建 jwt 模組 + middleware 改)

**Day 2-3（chat handler 合併修改）**
- P0 #11 + P0 #12（合併 chat router multi-tenant + TraceContext.create_root，共 chat handler）
- P0 #16（同時加 tracer.start_span 在 5 處）

**Day 4-5（hash verifier）**
- P0 #13 verify_audit_chain.py + cron + alert

**Day 6（sandbox 重寫）**
- P0 #17 SubprocessSandbox Docker isolation（3-5d 是這條最長）

**Day 7（tools handler tenant）**
- P0 #18 memory_tools handler ExecutionContext

**Day 8-9（P1 hygiene）**
- 4 P1 items
- Tests + lint

**Day 10-11（retrospective + W4 trigger）**
- 跑全 test suite
- 寫 retrospective.md（必答 5 條，per template）
- 通知 audit session

可彈性壓縮成 7 days 或拉長至 14 days，視實際依賴複雜度。

### Step 4：每個 P0 close GitHub issue

```bash
gh issue close <N> --comment "Resolved by commit <hash> on feature/sprint-52-5-audit-carryover. Verification: <evidence>"
```

每個 P0 完成立即 close，不要堆到最後。

### Step 5：Day 10+ retrospective

per cleanup template §Retrospective 必答（5 條）：

1. 每個 P0 真清了嗎？列 commit hash + verification 結果
2. 跨切面紀律守住了嗎？multi-tenant / TraceContext / LLM Neutrality grep counts
3. 有任何砍 scope 嗎？若有，明確列出 + 後續排程（**不能像 50.2 那樣隱形砍**）
4. GitHub issues 全 close 了嗎？列每 issue url + close 時 commit
5. Audit Debt 有累積嗎？本 sprint 期間有沒有發現新的 audit-worthy 問題？

### Step 6：W4 Audit Trigger

完成後通知 audit session：「cleanup sprint 52.5 完成，可進 W4」。提供：
- 8 P0 全 close URLs
- 6 P1 中 4 個 fixed 證據
- retrospective.md 連結
- 跨切面 grep counts（multi-tenant / TraceContext / LLM Neutrality）

---

## 紀律（不可違反）

per V2 鐵律 + W3+W4P 教訓：

### 1. 不偷砍 scope（W3-2 教訓）
- Plan 承諾的 deliverable 全做完
- 無法做的在 retrospective 透明列出
- **不能像 Sprint 50.2 那樣 plan 寫了 TraceContext.create_root() 結果默默不做 + retrospective 不交代**

### 2. 跨切面 lint 全綠
- multi-tenant grep counts 不下降
- TraceContext propagation 完整
- LLM Neutrality 0 violation
- 每個 commit 跑 `python -m pytest`（**不是 bare `pytest`** — per testing.md AP-10 教訓）

### 3. 主流量整合驗收（mini-W4-pre 揭露的系統性 pattern）
- 不只交付 ABC + unit test
- 必須有 **integration test** 確認 main flow 真調用本次交付
- 例如 P0 #16 不只在 adapter 加 tracer.start_span，必須有 e2e test 跑完 chat 在 Jaeger 看到 5 spans

### 4. AP-10 Mock vs Real Divergence
- Tests 必須跑 real PostgreSQL（不是 SQLite）
- 不可寫 0.36s-runtime 的 100% mock test suite
- multi-tenant test 用 asyncpg + rls_app_role + 真試 cross-tenant query

### 5. 每個 git commit 前驗 branch
- 因 graphify hook bug，每次 commit 前必跑 `git branch --show-current`
- 確認在 `feature/sprint-52-5-audit-carryover` 才 commit
- 如不在，先 `git checkout` 過去

### 6. GitHub issues 即時 close
- 不堆到 sprint 結束才 close
- 每個 P0 完成立即 `gh issue close`

### 7. Audit session 留下的 fake hash row 不要清除
- audit_log table 中 id 36-39 in tenant `aaaa-...-4444` 是 known-test forgery baseline
- P0 #13 verify_audit_chain.py 加 `--ignore-tenant aaaa...4444` flag 跳過

---

## 環境依賴

✅ `ipa_v2_postgres` Docker container 已運行（healthy 多日）
✅ `_contracts/TraceContext` dataclass（49.4 Day 3 已建，per W4P-1 確認）
✅ `Depends(get_current_tenant)` infrastructure（49.3 Day 4.4 已建，但 chat router 沒接 — 你要修）
✅ JWT 函式庫 `python-jose` 或 `pyjwt`（如 requirements.txt 沒有，加進去）
✅ Docker（for P0 #17 sandbox 重寫）

---

## 你不需要做的事（已完成 / 不在範圍）

- ❌ 不審其他 sprint（audit session 的工作）
- ❌ 不開發新功能（dev session 的工作）
- ❌ 不修 graphify hook bug（user 會單獨評估）
- ❌ 不動主 session 的 52.2 Day 1-3 commits（feature/phase-52-sprint-2-cat5-prompt-builder）
- ❌ 不 push 到別的 branch（只 push 到 feature/sprint-52-5-audit-carryover + 最後 PR merge 進 main）

---

## 完成標準

✅ Sprint plan + checklist 寫好並 commit
✅ 8 P0 issues #11-18 全 closed（GitHub issue tracker 證明）
✅ 4 P1 中 4 個 fixed（W2-1 #4 / W2-2 #6/#7/#8）
✅ Retrospective 必答 5 條完整
✅ All `python -m pytest` green
✅ mypy strict pass
✅ CI green on PR
✅ Audit session 收到 W4 trigger 通知
✅ PR merged to main

---

## 完成回報（給 user）

包含以下：

1. **產出**：sprint plan + checklist 路徑 + retrospective 路徑 + PR URL
2. **每個 P0 verification 證據**（grep counts / test output / Jaeger screenshot）
3. **GitHub issues close URLs**（#11-18）
4. **Multi-tenant grep counts**（before/after — 證明 chat router Depends 數從 0 → 3+）
5. **TraceContext grep counts**（before/after — adapter tracer.start_span 從 0 → 3+）
6. **Tests runtime 增長**（W4P-4 51.2 的 0.36s 是紅旗 — cleanup 後 multi-tenant tests 應 ≥ 2s 因為跑 real PG）
7. **Audit Debt list**（cleanup 期間發現的新 audit-worthy 問題）
8. **觸發 W4 audit 的 ready 確認**

---

**注意**：本 prompt 完整自包含。新 cleanup session 不需問 user 「是什麼專案」、「audit 是什麼」、「P0 是什麼」 — 全部已在文件中。

如有疑問先讀必讀文件 1-7。仍不清楚再問。
