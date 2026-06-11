# V2 Verification Audit — Week 2 統籌總結

**Audit 區間**: 2026-04-29
**Sprint 範圍**: Phase 49.4 Day 1（Adapters + LLM Neutrality）/ Day 2（Worker Queue 選型 + agent_loop_worker framework）。**Day 3+（OTel / pg_partman / Lint rules）進行中，未列入 Week 2 審計**。
**Auditor**: Verification Audit team（2 個 read-only sub-audits 匯總）
**版本**: 1.0 — 決策性產出

---

## 一句話結論

> **Week 2 審計：2 項目中 1 ✅（Adapter）+ 1 ⚠️（Worker Queue）。Adapter 層三大鐵律完美守住（0 SDK leak / 6/6 ABC / 41 tests 真實），LLM Provider Neutrality「30 分鐘換 provider」承諾結構上守住。Worker queue 是「誠實 stub + A 級決策 doc + 髒依賴狀態」的混合體 — 不是 Potemkin 但 hygiene 待整。不阻塞 Phase 50.1 Day 1-3，但 Day 4-5 LLM wire 時需替換 handler，Phase 53.1 HITL 嚴重阻塞需先建 TemporalQueueBackend。**

---

## 1. 評分總表

| # | 審計項 | 風險等級 | 結果 | 證據強度 | 阻塞 Phase 50？ |
|---|-------|---------|------|---------|----------------|
| W2-1 | Adapter + LLM Neutrality | 5 | ✅ Passed | **極強**（0 SDK leak grep + 41/0/0 + CI lint exit 1 真強制 + Azure 6/6 真實作）| 否 |
| W2-2 | Worker Queue 選型 + agent_loop_worker framework | 4 | ⚠️ Concerns | **強**（A 級決策 doc + retry 邏輯真）但 dependency hygiene 差 | Partial（50.1 Day 4-5 警告 / 53.1 阻塞）|

**整體分**：1.5/2 ✅。Week 2 核心承諾（LLM 中立）達標，但 worker 層暴露施工 hygiene gap（dependency / 目錄 / 命名三處需整）。

---

## 2. 關鍵正面證據（建立信心）

5 點抽自 2 份報告中**最有說服力的證據** — 證明 Phase 49.4 Day 1-2 是真實工程，無 V1 自欺反模式：

1. **`from openai/anthropic/agent_framework` 在 agent_harness 全 0 grep**（W2-1 A.1-A.3）
   最高鐵律守住。`business_domain/` / `platform_layer/` / `api/` / `_contracts/` 全 0 命中。唯一合法 import 在 `adapters/azure_openai/adapter.py:41` + `error_mapper.py:29` — 完全符合 Adapter Layer 設計約束。

2. **Azure adapter `count_tokens()` 用真 tiktoken**（W2-1 C.2）
   `encoding_for_model` + 回退 `o200k_base`，逐 message + tool 累計，含 per-message overhead 4 — **不是 `len(text) // 4` 估算**。`_AZURE_FINISH_REASON_MAP` 把 OpenAI 字串 (`"stop"`/`"tool_calls"`/`"length"`/`"content_filter"`) 全轉中性 `StopReason` enum，**不外漏 SDK 字串**。

3. **41 contract tests 強度真實，0 skip**（W2-1 D.2-D.3）
   `41 passed in 0.33s, 0 failed, 0 skipped` — 無 `@pytest.mark.integration` 暗藏 skip。抽樣顯示 assertion 強：`tool_calls[0].arguments == {"a":1,"b":2}`（dict 中性化驗證）/ `prompt_tokens == 12`（具體值）/ `pytest.raises CancelledError` 真 race（sleep(10) + wait_for(0.05)）/ `category == ProviderError.UNKNOWN` exception chain。

4. **Worker 決策 doc 是示範級**（W2-2 A.2-A.3）
   `worker-queue-decision.md` 204 行：5-axis 評估（Latency / Durable resume / Replay determinism / Python ergonomics / Operational cost）+ 5 alternatives 對比（Celery / Dramatiq / RQ / Airflow / 手刻）+ 加權打分（B- vs A-）+ 4 條 carry-forward triggers（漲價 / HITL 簡化 / 團隊縮編 / SDK 停更）。HITL 為決策核心 40% 權重 axis。

5. **AgentLoopWorker retry/backoff 真有邏輯**（W2-2 C.3）
   5 tests 全非 trivial。`test_worker_retry_then_succeed` 用 nonlocal call_count，前 2 次 raise，第 3 次成功，assert attempts==3 — **真測 retry 計數語義**。`test_worker_retry_exhausted_marks_failed` 真測 max_retries=2 → FAILED + error 訊息。CI lint `backend-ci.yml:103-110` exit 1 真強制（非 fake green）。

---

## 3. ⚠️ Concerns 詳細分析（W2-2）

唯一未通過項，三大 hygiene 問題詳述。

### 3.1 性質：誠實 stub + A 級決策 doc + 髒依賴狀態 三件混合

**設計層完整**：✅ 決策 A 級 + 5-axis 加權矩陣 + carry-forward triggers
**實作層誠實**：⚠️ Header 明示「Phase 49.4 stub」+ 列 not-in-scope（LLM calls / Temporal signals / graceful shutdown）
**Hygiene 層髒**：🚩 三個一致性問題（依賴 / 目錄 / 命名）

### 3.2 問題 1：依賴狀態不一致（紅旗）

- 決策聲明選 Temporal，但 `requirements.txt` 仍是 `celery>=5.4,<6.0`（已獨立驗證仍在）
- `temporalio` 未裝
- **風險**：開發者 onboarding 看 deps 誤以為 Celery 仍是 plan；新 PR 可能繼續用 Celery
- **修補**：刪 Celery（若 49.x 確認不用）+ 標 `temporalio` 「Phase 53.1 加入」於 requirements 註解

### 3.3 問題 2：目錄分歧（AP-3 風險）

- `platform_layer/workers/`（規劃位置，僅 6 行 README placeholder）
- `runtime/workers/`（實際代碼 3 檔 382 行）
- **風險**：Phase 50.1 開發者按規劃文件找會落空，可能重複實作或誤改 placeholder
- **修補**：合併為單一目錄。建議統一到 `platform_layer/workers/` 對齊 V2 規劃；或在 placeholder 加 redirect 註解明示真實位置

### 3.4 問題 3：命名與性質不符（AP-4 風險）

- `AgentLoopWorker` 名稱暗示生產級 worker（含 LLM 呼叫）
- 實際是 stub，靠 MockQueueBackend，`run_once()` 用 `isinstance(backend, MockQueueBackend)` 對 ABC 抽象有破口（NotImplementedError for non-Mock）
- 無 `@workflow.defn` / 無 activities / 無 Temporal client setup
- **風險**：Phase 50.1 Day 4-5 開發者誤以為可直接 wire LLM，實際發現是空殼
- **修補**：rename 為 `AgentLoopWorkerStub`，或於 class docstring + module header 頂部加 prominent「Stub for Phase 49.4-53.1」警告

### 3.5 影響評估（依用途分支）

| Phase 50 工作 | 是否需先修補 |
|--------------|-----------|
| 50.1 Day 1-3（Loop core / Tool layer 整合）| ❌ 可直接進，Mock + ABC 足夠 |
| 50.1 Day 4-5（real LLM call wire-up）| ⚠️ 必須先換 `_default_handler` 為 AgentLoop.run |
| 53.1 HITL pause/resume | ✅ **嚴重阻塞**，必先建 TemporalQueueBackend + WorkflowEnvironment |

---

## 4. 修補項目（按優先序，含 Week 1 carryover）

### P0（必修，阻塞）— 0 項

無。Week 2 也沒有發現必須立即停工的問題。

### P1（高優，須在 Phase 50 啟動前 / 啟動初）— 8 項

| # | Item | 來源 | Sprint | Effort | Owner | 為何 P1 |
|---|------|------|--------|--------|-------|--------|
| 1 | `scripts/verify_audit_chain.py` + daily cron + alert | W1-3 | 49.4 收尾 / 49.5 | 2-3 days | DBA / SRE | governance/HITL「不可否認證據」前提 |
| 2 | JWT 整合替換 `X-Tenant-Id` header | W1-2 P1 carryover | 49.4+ 或 50.1 | 1-2 days | Backend / Identity | prod 必換否則 trivial spoof |
| 3 | 刪除舊 stub `backend/src/middleware/tenant.py` | W1-2 P2 carryover | 50.1 cleanup | < 1 hour | Backend | 與 `platform_layer/middleware/tenant_context.py` 並存混淆 |
| 4 | 撰寫 `adapters/azure_openai/tests/test_integration.py`（@pytest.mark.integration real-API） | W2-1 D.4 | 49.4 D2-D5 | 2-3 hours | Adapter team | 鎖死 SDK behaviour 漂移；contract docstring 已提及但檔未建 |
| 5 | CI lint scope 擴大：加 `business_domain/` / `platform_layer/` / `api/` | W2-1 A.5 | 49.4 D5 | < 1 hour | DevOps | 預防後續層偷渡 LLM SDK |
| 6 | requirements.txt 清理：刪 Celery（若 49.x 不用）或加註解 "Phase 53.1 前 placeholder" | W2-2 §3.2 | 49.4 D5 | 30 min | Backend | 防止 deps 與決策不一致誤導 |
| 7 | 統一 worker 目錄：`platform_layer/workers/` ↔ `runtime/workers/` 二選一 | W2-2 §3.3 | 49.4 D5 / 50.0 | 1-2 hours | Backend | AP-3 cross-directory scattering 預防 |
| 8 | AgentLoopWorker 命名 / docstring 加「Stub for Phase 49.4-53.1」明示 | W2-2 §3.4 | 49.4 D5 | 30 min | Backend | AP-4 Potemkin 命名風險預防 |

### P2（中優，列入 backlog）— 7 項

承襲 Week 1 P2 四項：
- ORM ↔ contract 轉換 helper（W1-1）
- 強化 `test_state_race.py`（≥ 20 workers×50 iter）（W1-4）
- 17.md Contract 補 `append_snapshot` retry policy（W1-4）
- `tools_registry` 全局表多租戶設計評估（W1-4）

Week 2 加：
- ProviderRouter 雛形 + `contract_test_base.py` 抽象基類（W2-1 P2）
- TemporalQueueBackend 實作 + `WorkflowEnvironment` 整合測試（Phase 53.1 範圍但可預備）
- Multi-tenant worker test + trace_context 沿 envelope 傳遞 test（W2-2 P1 內列）

### P3（低，記錄即可）— 2 項（沿用 Week 1）

無 Week 2 新增。

---

## 5. 累計 Phase 50 啟動判定（Week 1 + Week 2）

**結論**：✅ **不阻塞 Phase 50.1 啟動**，但分階段執行：

| Phase 50 階段 | 判定 | 前置條件 |
|--------------|------|---------|
| Phase 50.1 Day 1-3（Loop core / Tool 整合）| ✅ 可進 | 所有依賴就緒（MockQueueBackend + ChatClient ABC + ORM + RLS）|
| Phase 50.1 Day 4-5（LLM wire-up）| ⚠️ 需先修 | W2-2 P1 #8（AgentLoopWorker handler 替換 + docstring 整改）|
| Phase 53.1（HITL pause/resume）| ❌ 阻塞 | 必先建 TemporalQueueBackend + WorkflowEnvironment + signals |

**建議節奏**：
1. 開 **Phase 50.0 cleanup sprint**（或併入 49.5 收尾）做 P1 #1-#8 八項，預估 1 week
2. 並行 49.4 Day 3-5（OTel + pg_partman + Lint rules）正常推進
3. 完成後正式啟 Phase 50.1 Orchestrator Loop
4. Phase 53.1 啟動前 1 sprint 預備 TemporalQueueBackend Spike → Adapter migration plan

---

## 6. Audit 範圍與限制（明示沒做什麼）

### Week 2 沒做

- ❌ 49.4 Day 3 OTel observability（進行中，working tree 有未 commit 檔案：`platform_layer/observability/logger.py` / `setup.py` / `agent_harness/observability/{exporter,metrics,tracer}.py`）→ **Week 3**
- ❌ 49.4 Day 4 pg_partman + Dockerfile.postgres 升級（進行中，`docker/` 未 commit）→ **Week 3**
- ❌ 49.4 Day 5 Lint rules 4 條（cross-category / LLM neutrality / asyncio / type hints）→ **Week 3**
- ❌ 49.5 收尾驗收 → 視 Phase 50.0 是否成立

### Week 1 + Week 2 累計沒做

- ❌ 49.1 Day 4 frontend Vite skeleton（零代碼審計）
- ❌ Docker compose 完整啟動測試（含 Temporal server，與決策 doc 一致延 Phase 53.1）
- ❌ Memory 5 層 schema 細節（49.3 Day 2 有但風險中等，留 Week 3 或併 Phase 51.2 audit）
- ❌ 49.1 Day 5 CI pipeline 真實觸發效果（部分證據已在 W2-1 backend-ci.yml 取得）

---

## 7. 累計 Anti-Pattern 風險評估（過 8 sprint+）

| AP | 違反次數 | 詳情 |
|----|---------|------|
| AP-1 Pipeline 偽裝 Loop | 0 | 49.x 無 LLM 呼叫，無風險 |
| AP-2 Side-Track Code | 0 | 主流量可追蹤；adapter 唯一例外明示 |
| AP-3 Cross-Directory Scattering | 1（W2-2 worker 目錄分歧 `platform_layer/workers/` vs `runtime/workers/`）| 中等，可修 |
| AP-4 Potemkin Features | 1.5（W1-3 audit hash chain verifier 缺 + W2-2 AgentLoopWorker 命名暗示生產級但實為 stub）| 中等，可修 |
| AP-5 PoC Accumulation | 0 | spike code 在 `experimental/` 隔離 |
| AP-6 Hybrid Bridge Debt | 0 | ChatClient ABC 真為當下使用，非「為將來預留」 |
| AP-7 Context Rot | 0 | 49.x 無 LLM，無對話 |
| AP-8 No PromptBuilder | 0 | 49.x 無 LLM 呼叫 |
| AP-9 No Verification | 0 | 49.x 無 agent loop 輸出 |
| AP-10 Mock vs Real Divergence | 0 | RLS 紅隊測試切 NOLOGIN 角色 + asyncpg 真連 PG；adapter contract test 用真 tiktoken |
| AP-11 Naming Suffix Legacy | 0 | 無 `_v1` / `_v2` / `_old` 殘留 |

**總評**：8 sprint 累計 **2.5 個 AP 違反**（W1-3 / W2-2 hygiene），全部可修，**無架構級錯誤**。AP-3 / AP-4 風險集中在 Phase 49.4 Day 2 一個 sprint，且都有明示 stub 標記與 carry-forward 計畫，與 V1「Phase 35-38 散落 6 處 / Potemkin 結構槽位」級錯誤性質完全不同。

---

## 8. 給專案 owner 的建議行動（5 條，可直接列入下次 standup）

1. **派人寫 `scripts/verify_audit_chain.py`** + 排 daily cron + 接 P1 alert（W1-3 P1 #1；2-3 days；DBA / SRE）
2. **CI lint scope 擴大涵蓋全 src**（加 `business_domain/` / `platform_layer/` / `api/`）（W2-1 P1 #5；< 1 小時；DevOps）
3. **requirements.txt 清 Celery + 加 temporalio TODO 註解**（W2-2 P1 #6；30 分鐘；Backend）
4. **Worker 目錄統一決策**（`platform_layer/workers/` 還是 `runtime/workers/`）— Phase 50 啟動前必須拍板（W2-2 P1 #7）
5. **開 Phase 50.0 cleanup sprint**（或併 49.5）完成上述 P1 全部 8 項，1 week 預估。完成前 Phase 50.1 Day 1-3 可並行啟動，Day 4-5 必須等 P1 #8 完成

---

## 9. 最關鍵 1 行決策建議

> **Adapter 層 LLM 中立性無懸念，Phase 50.1 Day 1-3 可立即啟動；Worker hygiene 三項（依賴 / 目錄 / 命名）+ Week 1 三項 P1 必須在 Phase 50.1 Day 4 LLM wire-up 前完成；Phase 53.1 HITL 啟動前必先建 TemporalQueueBackend，建議提前 1 sprint 預備 Spike。**

---

**Auditor 簽核**: Verification Audit team
**完成時間**: 2026-04-29
**下一次審計**: Week 3（49.4 Day 3-5：OTel / pg_partman / Lint rules + 49.5 收尾）
**相關文件**:
- `claudedocs/5-status/V2-AUDIT-WEEK1-SUMMARY.md`
- `claudedocs/5-status/V2-AUDIT-W2-ADAPTER.md`
- `claudedocs/5-status/V2-AUDIT-W2-WORKER.md`
