# V2 Audit W2-2 — Worker Queue 選型 + agent_loop_worker framework

**Audit 日期**: 2026-04-29
**Sprint 範圍**: 49.4 Day 2 (commit 86946c4)
**結論**: ⚠️ **Passed with Concerns** — 決策真實且高品質；framework 是合理 stub；tests 強度中上；但聲稱 commit message「Temporal」與實際代碼狀態（無 Temporal 依賴 / 無 adapter / Mock-only）有落差，**用戶需確認此「先決策、後實作」是否符合預期**。

---

## 摘要

| 項目 | 結果 |
|------|------|
| 決策明確選 Temporal | ✅ 明確 |
| 對比 alternatives 數 | 5 個（Celery / Dramatiq / RQ / Airflow / 手刻 asyncio） |
| 5-Axis 評估 | ✅ Latency / Durability / Determinism / Ergonomics / Ops |
| Decision matrix 加權打分 | ✅ B- (Celery) vs A- (Temporal) |
| Trade-off 與 carry-forward 條件 | ✅ 明列 4 個重新評估觸發點 |
| agent_loop_worker.py 是 stub | ⚠️ **明示自稱 stub**（headers 標 "Phase 49.4 stub"），有真 retry/cancel 邏輯，但無 LLM 呼叫 |
| TemporalQueueBackend 存在 | ❌ **不存在**（規劃延到 Phase 53.1） |
| temporalio 在 requirements.txt | ❌ **未安裝** |
| Celery 在 requirements.txt | ⚠️ **仍存在** (`celery>=5.4,<6.0`)（V1 殘留？） |
| Spike code 兩邊都建 | ✅ `experimental/sprint-49-4-spike/{celery,temporal}_spike/` |
| 5 tests pass/fail/skip | ✅ **5 pass / 0 fail / 0 skip**（0.11 秒） |
| Tests 強度 | 🟡 **Medium**（測 retry/cancel/exhausted 真行為，但純 Mock，無 Temporal env） |
| 阻塞 Phase 50? | ⚠️ **部分阻塞** — Mock + ABC 足以撐 Phase 50.1 loop 整合，但 Phase 53.1 HITL 仍需建 TemporalQueueBackend |

---

## Phase A — 決策報告真實性

### A.1 文件位置

`docs/03-implementation/agent-harness-execution/phase-49/sprint-49-4/worker-queue-decision.md`（204 行）

### A.2 決策內容（4 點全通過）

1. **明確選擇**: ✅ "Recommendation: Temporal" — 無「待後續」字眼
2. **Alternatives 對比**: ✅ 5 個（Celery / Dramatiq / RQ / Airflow / 手刻 asyncio + DB）
3. **評估維度**: ✅ 5 axes — Latency / Durable resume / Replay determinism / Python ergonomics / Operational cost
4. **Trade-off 認知**: ✅ 4 條 carry-forward triggers（Temporal Cloud 漲價 / HITL 簡化 / 團隊縮編 / SDK 停更）

### A.3 11+1 範疇對齊

| 範疇 | 是否考慮 |
|------|----------|
| 範疇 1 Loop long-running | ✅ Axis 1 / Phase 50+ 引用 |
| 範疇 7 State checkpoint | ✅ "Cat 7 integration cheaper" 第 3 justification |
| 範疇 8 Error retry | ✅ 已實作於 worker (max_retries + backoff) |
| §HITL pause/resume | ✅ **決策核心**（40% 權重 axis） |
| 範疇 11 Subagent dispatch | ⚠️ 未明示討論（max_inflight=1 留待 Phase 50.2） |

**評**：決策報告**質量極高**（5-axis 矩陣 + 加權打分 + 拒絕清單 + 觸發點）。理由排序明確（HITL > async-first > Cat 7 整合）。

---

## Phase B — Framework 實作

### B.1 結構

```
backend/src/runtime/workers/
├── __init__.py            (4 lines, re-export)
├── queue_backend.py       (211 lines, ABC + MockQueueBackend)
└── agent_loop_worker.py   (167 lines, AgentLoopWorker)
```

注意：**code 在 `runtime/workers/`，非 plan 期望的 `platform_layer/workers/`**。`platform_layer/workers/__init__.py` 仍存在但只 6 行 placeholder。可能是執行期 vs 規劃命名分歧；不影響功能但造成兩處目錄混淆。

### B.2 主類審計

**QueueBackend ABC** (`queue_backend.py`)：
- ✅ 4 個 @abstractmethod (`submit / poll / cancel / list_pending`)
- ✅ `TaskEnvelope` frozen dataclass + `tenant_id`(必填) + `trace_id`(必填) — 對齊多租戶 + Cat 12
- ✅ `TaskStatus` enum (PENDING/RUNNING/COMPLETED/FAILED/CANCELLED)
- ✅ `MockQueueBackend` 完整實作（asyncio.Lock / pending list / results dict / cancelled set）

**AgentLoopWorker** (`agent_loop_worker.py`)：
- ⚠️ `run_once()` 用 `isinstance(self.backend, MockQueueBackend)` 判斷分支，**對 ABC 抽象有破口**（NotImplementedError for non-Mock）
- ✅ `_execute_with_retry` 真有實作：retry count / exponential backoff / cancellation 檢查 / asyncio.CancelledError 重新 raise
- ✅ `_default_handler` 標明「Phase 50.1 replaces with AgentLoop.run()」
- ❌ **無 @workflow.defn**（不是真 Temporal workflow，只是 class — 與決策的 Temporal 選擇有距離）
- ❌ **無 activities** (@activity.defn)
- ❌ **無 Temporal client connection setup / Worker startup script**

**評**：是個誠實的 stub — header 明示 "Phase 49.4 stub" + 列「NOT in scope this sprint」(LLM calls / Temporal signals / graceful shutdown)。**不是 Potemkin**（AP-4），但也**還不是 Temporal 實作**。

### B.3 依賴註冊

```
requirements.txt:
- celery>=5.4,<6.0          ← 仍存在（V1 殘留？應否清除？）
- redis>=5.0,<6.0           ← 仍存在
- temporalio                ← 不存在
```

🚩 **紅旗**：聲稱選 Temporal，但 (1) Temporal SDK 未裝；(2) Celery 仍在 deps。Spike 階段保留 Celery 可理解，但決策已 lock，應在後續 sprint 清理 Celery 或改為「Phase 53.1 才裝 temporalio」明示在 README。

### B.4 Worker bootstrap

❌ **無 start_worker.py / Worker entrypoint** — 符合 stub 意圖，但 Phase 50.1 啟動 loop 時必須補。

---

## Phase C — 5 Tests 強度

### C.1 位置

`backend/tests/unit/runtime/workers/test_agent_loop_worker.py`（141 行）

### C.2 pytest 結果

```
collected 5 items
test_worker_init_default                              PASSED [ 20%]
test_worker_poll_and_execute_returns_result           PASSED [ 40%]
test_worker_cancel_returns_cancelled_status           PASSED [ 60%]
test_worker_retry_then_succeed                        PASSED [ 80%]
test_worker_retry_exhausted_marks_failed              PASSED [100%]
============== 5 passed in 0.11s ==============
```

### C.3 強度抽樣

| Test | 測試行為 | 強度 |
|------|---------|------|
| `init_default` | ✅ 構造器 + handler 預設 + config 合理 | 🟡 Trivial-medium |
| `poll_and_execute` | ✅ 真 submit → run_once → assert TaskStatus.COMPLETED + result.result == echoed payload | 🟢 Medium |
| `cancel` | ✅ submit → cancel → run_once 返回 None + 直接 poll 確認 CANCELLED | 🟢 Medium |
| `retry_then_succeed` | ✅ 自訂 flaky_handler nonlocal call_count，前 2 次 raise，第 3 次成功，assert attempts==3 | 🟢 **Strong**（測 retry 真語義） |
| `retry_exhausted_marks_failed` | ✅ always_fails → max_retries=2 → 確認 FAILED + error 訊息 | 🟢 Medium |

**評**：**5 個都不是 trivial assertion**（沒有「assert isinstance」的偽測試）。最強的兩個（retry_then_succeed / retry_exhausted）真的測到 retry 計數 + backoff 邏輯。**但**：
- ❌ 全 Mock，無 `WorkflowEnvironment` 真跑 Temporal
- ❌ 無 contract test 驗證 ABC 契約對其他 backend 是否成立
- ❌ 無 trace_context 對齊測試（Cat 12）
- ❌ 無 multi-tenant 隔離測試（雖 TaskEnvelope 有 tenant_id 欄位）

整體強度：**Medium**（不是 trivial，但離 production-ready 還差 contract test + trace + tenant test）。

---

## Phase D — Temporal Server (跳過)

`docker-compose.dev.yml` 無 `temporal` service — 與決策 doc 「Phase 53.1 才加」一致。**未啟動 Temporal server**，僅靜態驗證。

---

## Phase E — 跨範疇影響

### E.1 上層使用點

`grep -r "AgentLoopWorker" backend/src/` 結果（隱含）：除 worker 自家外，**主流量無人 import**。符合 Phase 49.4 stub 階段（API 層 Phase 50+ 才 wire）。

### E.2 與範疇 7 State Mgmt 對齊

- ✅ `TaskEnvelope` 含 trace_id + tenant_id，可對應 49.3 RLS / 49.2 state_snapshots
- ❌ 無 checkpoint write 接口（Phase 50.1+53.1 補）

---

## 結論評分

| 評項 | 結果 |
|------|------|
| 決策報告真實 | ✅ **A 級**（5-axis + 加權 + carry-forward） |
| Framework 完整 | ⚠️ **誠實 stub**（不是 Temporal 實作；ABC + Mock OK） |
| Tests 強度 | 🟢 **Medium-strong**（retry 邏輯真測；但無 Temporal env / contract / tenant） |
| 跨範疇對齊 | ✅ Cat 12 trace + multi-tenant 字段就位；Cat 7 待 Phase 53.1 |
| Anti-Pattern 風險 | ⚠️ **AP-4 風險低但需監控**（命名是 "AgentLoopWorker" 但只是 stub；Phase 50.1 必須真實 wire） |

---

## 修補建議

### P0（merge Phase 50.1 前必修）

1. **澄清「選了但沒裝」狀態**：決策 doc 末尾或 worktree README 明示「Phase 49.4 ship Mock + ABC；temporalio 安裝延到 Phase 53.1」防止未來 audit 誤判
2. **Celery 殘留**：requirements.txt 的 `celery>=5.4` + redis 評估是否該標 deprecated 或刪除（可能是 V1 archived 代碼還用？確認後處理）
3. **目錄混淆**：`platform_layer/workers/` (6 行 placeholder) vs `runtime/workers/` (實作) — 統一到一處或在 placeholder 加 redirect 註解

### P1（Phase 50.1 必補）

4. **Contract test**：新增 `tests/contract/test_queue_backend_contract.py`，定義 TemporalQueueBackend 將要通過的測試集
5. **Multi-tenant test**：tenant A submit → tenant B list_pending 不可見
6. **Trace context test**：trace_id 沿 envelope 傳遞 + emit Cat 12 span

### P2（Phase 53.1 補）

7. **TemporalQueueBackend** 真實作 + @workflow.defn + activities
8. **Worker startup script** + docker-compose.dev.yml 加 `temporal` service
9. **HITL signal 整合**（Cat 9 + Cat 7）

---

## 阻塞 Phase 50？

**⚠️ 部分阻塞**

- ✅ **不阻塞 Phase 50.1 Day 1-3**（Loop 框架、Tool layer 整合可用 MockQueueBackend）
- ❌ **阻塞 Phase 50.1 Day 4-5**（real LLM call wire-up 時 `_default_handler` 必須換成 AgentLoop.run）
- ❌ **嚴重阻塞 Phase 53.1**（HITL 需 Temporal `wait_condition` + signals — 屆時必須建 TemporalQueueBackend；提前準備 Spike → Adapter migration plan 為佳）

**結論**：作為 Phase 49.4 Day 2 deliverable，**質量達標但不是「完整 Temporal 實作」**。決策報告是**示範級**；實作部分是**合理的 staged stub**。建議用戶在 Phase 50.1 開工前明示三層期望（Mock-OK / 部分 Temporal / 完整 HITL），避免後續 sprint 對「完成度」標準分歧。

---

**Audit 完成時間**: 2026-04-29
**下一步**: W2-3 Week 2 審計總結
