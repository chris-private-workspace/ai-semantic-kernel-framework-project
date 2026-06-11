# V2 Verification Audit — Week 3 統籌總結

**Audit 區間**: 2026-05-01
**Sprint 範圍**: W3-0 Carryover Process（W1+W2 P1 在後續 5 sprint 處理狀態）/ Phase 50.1 Cat 1 Orchestrator Loop + AP-1 lint / Phase 50.2 主流量端到端
**Auditor**: Verification Audit team（3 個 read-only sub-audits 匯總）
**版本**: 1.0 — 決策性產出

---

## 一句話結論

> **Week 3 揭露雙層問題：(a) Phase 50.1 實作品質高（AP-1 lint AST-based 真實阻擋偽 loop + 52/0/0 + while-true loop 真實），(b) Phase 50.2 實作偏離鐵律（chat router 0 multi-tenant 隔離 + TraceContext 隱形砍範圍），(c) audit findings process drift（W1+W2 8 項 P1 在 5 sprint 0 進入 sprint planning，0% 修復率）。Phase 50.2 主流量端到端可用但**不 production-ready**；多租戶 / 觀測性兩條鐵律破，必須在 Phase 53.x 啟動前修。雙層問題互相加強：W1-2 JWT/tenant carryover 5 sprint dropped → 50.2 chat router 直接重複違反同一鐵律。這是 V1 災難「audit 寫了沒人讀」的早期重演。**

---

## 1. 評分總表

| 審計項 | 風險等級 | 結果 | 證據強度 | 阻塞 Phase 53+？ |
|-------|---------|-----|---------|----------------|
| W3-0 Carryover Process | (process) | ❌ Failure | **強**（7/8 dropped + 5 sprint plan/checklist/retrospective grep 0 hit + 1 acknowledged 但無 rename） | Soft（process 修補必修，但不阻塞 51-52 推進） |
| W3-1 Phase 50.1 Cat 1 + AP-1 lint | 5 | ✅ Passed | **強**（loop.py:171 真 while True + tool result append + AST lint 自寫 fake violation 實測 exit 1 + 52/0/0 + Cat 6 Output Parser 中性化） | 否 |
| W3-2 Phase 50.2 主流量 | 5 | 🟡 PASS WITH CAVEATS | **強**（46/0/0 + mypy strict + 5 V2 lints + 8 SSE events 中性 LoopEvent + frontend chat-v2 真整合）**但 2 critical 偏離經三重驗證確認**（multi-tenant 0 隔離 + TraceContext undisclosed scope cut） | **Phase 53.1 + Phase 53.3 阻塞** + SaaS Stage 1 強制阻塞 |

**整體分**：1 ✅ + 1 🟡 + 1 ❌（process 層）。Week 3 是「實作品質與 process 紀律落差顯著」的轉折點。

---

## 2. 關鍵正面證據（W3-1 建立信心）

抽自 W3-1 最具說服力的 5 點 — 證明 Phase 50.1 是真實工程，不是規劃幻覺：

1. **`loop.py:171` 真 `while True` + tool result append + continue**（W3-1 AP-1）
   不是 `for step in steps:` 偽 loop。Tool result 真以 Message 形式回注 messages list，下一輪 LLM 重新推理。AP-1 反模式（V1 災難第一名）結構性無法復現。

2. **AP-1 lint 是 AST-based 真實有效**（W3-1）
   不是 grep regex 假 lint。Auditor 自寫 fake violation（線性 `for step in [s1,s2,s3]:`）實測 exit 1 + 明確錯誤訊息。lint 真實會擋。

3. **Cat 6 Output Parser 0 regex + 純 ChatResponse 消費**（W3-1）
   LLM 中立性沿 50.1 守住。不是「先解析 OpenAI 字串再轉中性」式偷渡，是直接消費 adapter 輸出的中性 ChatResponse dataclass。

4. **AP-8 PromptBuilder（N/A 至 52.2）已守無偷渡**（W3-1）
   grep 證明 50.1 無裸組 messages list。雖然 PromptBuilder 範疇 5 要 52.2 才上，但 50.1 沒提前犯規預埋。

5. **52 tests pass / 0 fail / 0 skip**（W3-1）
   無 `@pytest.mark.skip` 暗藏。LoopState mutable 屬透明標記為 CARRY-007/009 至 53.1（不算違規，是 known scope）；ToolCallExecuted/Failed events 由 Cat 1 emit 但屬 Cat 2 own — 輕微 owner drift，可在 51.1 補正。

---

## 3. ⚠️ Critical 偏離詳細（W3-2 兩 critical findings）

W3-2 整體通過 (46/0/0 + mypy strict + 5 V2 lints + 8 中性 LoopEvent + frontend chat-v2 完整整合 ReadableStream + Zustand + AbortController)，但**經三重獨立驗證確認**兩個 critical 偏離。

### 3.1 Critical 1 — Multi-tenant 完全 missing（W3-2 + W1-2 carryover 共謀）

**性質**：違反 V2 三大最高指導原則之一（10.md §原則 1 server-side first），**carryover P1 重複違反同一鐵律**。

**具體證據**（auditor 獨立 grep 確認）：
- chat router **0** `Depends(get_current_tenant)` import / **0** `tenant_id` filter
- `SessionRegistry` 是 process-wide dict（**跨 tenant 共享**！dev/test 看不出，prod 立即洩漏）
- integration test `test_chat_e2e.py:8` 明文 skip tenant middleware
- 違反 multi-tenant-data.md 三鐵律（tenant_id NOT NULL + query filter + Depends 強制注入）
- 獨立 grep `backend/src/api/`：`tenant_id` 僅 1 hit（main.py），chat router **0**

**影響**：
- Sprint 49.3 整個 RLS 工作（13 表 + 26 policies + FORCE RLS + 紅隊測試）在 50.2 主流量被繞過 — 「DB 層擋住」不等於「應用層擋住」
- SessionRegistry process-wide dict 是隱形 multi-tenant 漏洞，dev/test 環境不會顯化，prod 立即洩漏

**修補成本**：Medium（chat router 加 `Depends(get_current_tenant)` + SessionRegistry 改 tenant-scoped storage + integration test 不再 skip）— 1-2 days

**緊急度**：Phase 53.1（HITL pause/resume 進 worker queue）之前必修，否則 worker fork 後跨 tenant lock-in 修補成本翻倍。

### 3.2 Critical 2 — TraceContext undisclosed scope cut（W3-2）

**性質**：違反 sprint-workflow.md（scope cut 必須 retrospective 透明聲明）+ 觀測性鐵律（observability-instrumentation.md）。

**具體證據**：
- 50.2 plan §4.1 **明文承諾**：「endpoint 創建 TraceContext.create_root() 傳入 AgentLoopImpl.run()」
- 實作 **0** 個 TraceContext / **0** 個 tracer 引用
- retrospective **未聲明** 此 omission（隱形砍範圍）
- 獨立 grep `backend/src/api/`：`TraceContext|tracer` **0 hit**

**影響**：
- 所有 SSE / loop event 無 trace_id → 多租戶 distributed tracing 無法跨層連結
- observability-instrumentation.md 在 50.2 主流量全失效
- 範疇 12 cross-cutting 鐵律破

**修補成本**：Low（chat handler 加 4-5 行 `TraceContext.create_root()` + propagate）— half day

**緊急度**：與 Critical 1 同 sprint 一起修。

### 3.3 Finding 3（邊緣 AP-2）

`build_agent_loop_handler` 工廠 + 3 tests，但 router 完全 bypass（inline await）— **forward-compat without user**，邊緣違反 AP-2（Side-Track Code Pollution / for-future-use 抽象）。中等優先，Phase 51.x 補 wire 即可。

---

## 4. 雙層問題分析（核心訊息）

### 4.1 Layer 1 — 實作層（W3-1 強 + W3-2 弱）

50.1 vs 50.2 品質落差**顯著**：

- **50.1**：純 backend Cat 1 純內部，獨立可驗 → 紀律高（AP-1 lint AST-based + 52/0/0 + 真 while-loop + 中性 ChatResponse 消費）
- **50.2**：API + frontend + worker 整合，跨層工作 → 紀律破（multi-tenant 0 隔離 + TraceContext 隱形砍）

**推測根因**：跨層整合時，**無人 own「跨層紀律」**（multi-tenant / observability 是 cross-cutting，不屬於任何單一範疇 owner）。

### 4.2 Layer 2 — Process 層（W3-0）

W1+W2 audit findings **完全未進入** sprint planning pipeline。具體現象：

- 沒有「audit ticket」系統（GitHub issues / claudedocs/4-changes 0 hit）
- Sprint plan template 無「Audit Carryover」section（49.4 AC-8 處理的是 49.3 carryover，與 audit 無關）
- Retrospective template 無「Audit Debt」段落
- W1-3 #1 verify_audit_chain.py（合規最高風險）5 sprint 後仍 0 行代碼 + 0 plan reference + 0 retrospective 提及
- W1-2 #2 JWT 自承「49.5+ deadline」**已過但無 escalation**

**結果**：audit deliverable 像專案文件，沒人讀沒人 own。

### 4.3 雙層互相加強（最危險）

W1-2 #2 JWT 替換是 W1+W2 P1 → 5 sprint dropped → 50.2 chat router 開發者直接重複違反 multi-tenant 鐵律。

如果 audit ticket 機制有效，50.2 開發前應收到 W1-2 警告 → 先修 JWT/tenant 才動 chat。結果：50.2 重新犯了**同樣的鐵律違反**。

**這就是 V1 災難的早期重演** — audit/review/retrospective 寫了沒人看 → 同樣錯誤反覆 → 6 個月後驚覺已遍佈 codebase。**現在介入成本最低；Phase 55 介入成本爆炸**。

---

## 5. Anti-Pattern 累計（10 sprint 過後）

| AP | 違反次數 | 詳情 |
|----|---------|------|
| AP-1 Pipeline 偽裝 Loop | 0 | 50.1 真 while-true + AP-1 lint AST-based 真強制 |
| AP-2 Side-Track Code | 1（W3-2 worker factory + 3 tests 無 user）| 邊緣 |
| AP-3 Cross-Directory Scattering | 1（W2-2 worker dir 二元並存 5 sprint 未解 → 已從「萌芽」變「定型」）| 中等 |
| AP-4 Potemkin Features | 2（W1-3 hash chain verify 缺 + W3-2 frontend 完整但 backend tenant 缺，名實不符）| 中等高 |
| AP-5 PoC Accumulation | 0 | — |
| AP-6 Hybrid Bridge Debt | 0 | — |
| AP-7 Context Rot | 0（52.1 才上 Cat 4）| — |
| AP-8 No PromptBuilder | 0（52.2 才上）| — |
| AP-9 No Verification | 0（54.1 才上）| — |
| AP-10 Mock vs Real Divergence | 1（test_chat_e2e.py:8 skip multi-tenant，違反 mock 與 real 同 ABC）| 中等高 |
| AP-11 Naming Suffix Legacy | 0 | — |

**總評**：累計 **5.5 個 AP 違反**（Week 1+2 為 2.5；Week 3 新增 AP-4 + AP-10 各 +1，AP-3 從萌芽變定型）。**仍可修，但增長速度比 Week 1+2 加倍**，需介入。

---

## 6. 累計修補項目（從 W1+W2+W3）

### P0（合規 / 安全鐵律）— 4 項，必修

| # | Item | 來源 | Effort | Owner |
|---|------|------|--------|-------|
| 1 | 🔴 **Critical 1（W3-2）** chat router 加 multi-tenant 隔離（Depends + SessionRegistry tenant-scoped + integration test 開）| W3-2 | 1-2 days | Backend / Identity |
| 2 | 🔴 **Critical 2（W3-2）** chat handler 加 TraceContext.create_root() propagate | W3-2 | half day | Backend / Observability |
| 3 | 🔴 **W1-3 #1**（5 sprint dropped）`scripts/verify_audit_chain.py` + cron + alert | W1-3 | 2-3 days | DBA / SRE |
| 4 | 🔴 **W1-2 #2**（5 sprint dropped）JWT 替換 X-Tenant-Id header | W1-2 | 1-2 days | Backend / Identity |

### P1（高優，須 Phase 53 啟動前）— 5 項

5. W1-2 #3 刪舊 stub `backend/src/middleware/tenant.py` — < 1h（純 cleanup）
6. W2-1 #4 寫 `adapters/azure_openai/tests/test_integration.py` — 1 day
7. W2-1 #5 CI lint scope 擴大（加 `business_domain/` / `platform_layer/` / `api/`）— < 1h
8. W2-2 #6 requirements.txt 清 Celery / 加 temporalio TODO — 30 min
9. W2-2 #7 統一 worker 目錄（`platform_layer/workers/` ↔ `runtime/workers/` 二選一）— half day

### P2（中優，列入 backlog）— ~5 項

10. W2-2 #8 AgentLoopWorker rename / docstring 警告（已部分滿足，rename 配 53.1）
11. W3-1 LoopState 改 frozen dataclass + reducer pattern（53.1 一起做；CARRY-007/009）
12. W3-1 ToolCallExecuted/Failed events owner 遷移（51.1 補正）
13. W3-2 worker factory consumer wire（51.x；解 AP-2 邊緣）
14. ProviderRouter 雛形 + `contract_test_base.py`（W2-1 P2）

---

## 7. Process 修補（最重要 — 沒做這個，下次 audit 又會發現新 carryover dropped）

**避免下次 carryover 又被 drop**：

1. **建 audit ticket 系統**：每個 P1 建 GitHub issue（或 claudedocs/4-changes/AUDIT-XXX），assigned to next sprint，有 due date
2. **Sprint plan template 必填 section**：「Audit Carryover」（從前 1-2 個 audit 抽未修項；本 sprint 接 / 推遲 / 不適用）— 49.4 AC-8 模式推廣
3. **Retrospective template 必填段落**：「Audit Debt」（這 sprint 做了哪些 audit P1 / 推遲哪些 / 為何）
4. **每月 Audit Status Review**：跨 sprint 看 P1 累積，避免雪球
5. **Audit 自身定期 re-verify**：每 2-3 sprint 跑一次（W3-0 即此機制；防止 drift > 6 sprint）

如果不做 process 修補，就算這次 P0 修了，**下次 audit 又會發現新 carryover dropped → 永遠在追尾巴**。

---

## 8. Phase 53+ 啟動判定

**結論**：⚠️ **Phase 51-52 可推進**，但 **Phase 53.x 系列必須先 P0 全清**。

| Phase | 判定 | 前置條件 |
|-------|------|---------|
| **Phase 51.x（Tools + Memory）** | ✅ 可推進 | 無新 cross-cutting concern；可平行 P0/P1 |
| **Phase 52.x（Context + Prompt）** | ✅ 可推進 | 主要 backend；可平行 P0/P1 |
| **Phase 53.1（State Mgmt + worker integration）** | ❌ **阻塞** | 必先修 P0 #1（multi-tenant；worker fork 前）+ P0 #2（TraceContext；distributed tracing across worker）+ P1 #5（stub cleanup）+ P1 #9（worker dir 統一） |
| **Phase 53.3+ HITL** | ❌ **阻塞** | 必先修 P0 #3（verify_audit_chain；HITL approval 仰賴 audit log 不可否認）+ P0 #4（JWT） |
| **SaaS Stage 1** | ❌ **強制阻塞** | 全 P0 必清 + audit ticket process 上線 |

**建議**：開 **Phase 52.5 或 53.0 cleanup sprint**（5-7 days）做 P0 4 項 + P1 5 項；無此 sprint Phase 53 不准啟。

---

## 9. Audit 範圍與限制（明示沒做什麼）

### Week 3 沒做

- ❌ Phase 51.0 / 51.1 / 51.2（Tools + Memory）— 留 Week 4
- ❌ Phase 52.1 進行中 — 等 commit 後 Week 5 審
- ❌ 49.4 Day 3-5 OTel observability 細節 — 50.2 已揭露 TraceContext 違規，OTel 細節是進一步 debug
- ❌ Frontend chat-v2 完整 browser real test — source check 過但無 e2e browser 驗證

### Week 1+2+3 累計沒做

- ❌ 業務領域 mock tools（51.0）真實性
- ❌ Memory 5 層 schema 細節（51.2）
- ❌ DevOps（13.md）— Docker 完整啟動 / production deploy 手測

---

## 10. 給專案 owner 的建議行動（5 條，可直接列入下次 standup）

1. **🔴 緊急開 Phase 52.5 或 53.0 cleanup sprint**：5-7 days 做 P0 4 項 + P1 1-3 項（stub 刪 / lint 擴 / requirements 清）。**不開不准進 Phase 53**。
2. **建 audit ticket 系統**：每個 P0/P1 建 GitHub issue + assigned + due date。**否則下次 audit 又 drop**（這是 process 災難的單點修補）。
3. **修 sprint plan/retrospective template**：必填「Audit Carryover」+「Audit Debt」段落。49.4 AC-8 模式推廣到所有 audit findings。
4. **下個 sprint 開始前先確認**：是否有 audit P0 阻塞？尤其 Phase 53.x 系列。
5. **W3-2 兩 critical 修補不可拖延**：Phase 53.1 worker fork 後加 multi-tenant 成本翻倍，TraceContext 加 worker pool 後 distributed tracing 重設成本飆升。**現在 1.5 days，53.1 後 1 week+**。

---

## 11. 最關鍵 1-2 行決策建議

> **Phase 50.1 實作品質可靠（AP-1 lint 真實阻擋偽 loop）；但 Phase 50.2 跨層整合鐵律破（multi-tenant 0 隔離 + TraceContext 隱形砍）+ W1+W2 audit findings 5 sprint 0% 修復率，這是 V1 「audit 寫了沒人看」災難的早期重演。**

> **必須在 Phase 53 啟動前開 5-7 day cleanup sprint 清 P0 4 項 + 建 audit ticket process；否則 Phase 53.1 worker fork 後 multi-tenant 修補成本翻倍，且下次 audit 又會發現新 carryover dropped — 永遠追尾巴。**

---

**Auditor 簽核**: Verification Audit team
**完成時間**: 2026-05-01
**下一次審計**: Week 4（Phase 51.x Tools + Memory + cleanup sprint 驗收）
**相關文件**:
- `claudedocs/5-status/V2-AUDIT-WEEK1-SUMMARY.md`
- `claudedocs/5-status/V2-AUDIT-WEEK2-SUMMARY.md`
- `claudedocs/5-status/V2-AUDIT-W3-0-CARRYOVER.md`
- `claudedocs/5-status/V2-AUDIT-W3-1-PHASE50-1.md`
- `claudedocs/5-status/V2-AUDIT-W3-2-PHASE50-2.md`
