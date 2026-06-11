# V2 Audit W4P-1 — Phase 49.4 Day 3-5 (OTel + pg_partman + Lint)

**結論**: ⚠️ Concerns — 基礎設施落地大致完成，但 **OTel 5 處必埋點覆蓋率僅 2/5 (40%)**，Adapter 與 State Mgmt 層完全無 instrumentation；OTel SDK 版本鎖定不符合 rule；pg_partman extension 安裝但未啟用 create_parent。

**Audit Date**: 2026-04-29
**Auditor**: Research Agent (W4P-1)
**Scope**: Sprint 49.4 Day 3-5 (commits `1f2a6fb2` / `cc6f9291` / `3d385bc9`)
**Time Budget**: 60 min

---

## 摘要（速答）

| 項目 | 結果 | 細節 |
|------|------|------|
| OTel SDK 鎖版本 | ❌ Failed | `>=1.27,<2.0` 浮動範圍，違反 `observability-instrumentation.md` 的 `==1.22.0` 要求 |
| Tracer ABC 實作 | ✅ Passed | `Tracer` ABC + `NoOpTracer` + `OTelTracer`；TraceContext propagation 設計正確 |
| 5 處必埋點實際覆蓋 | ❌ **2/5 (40%)** | Loop ✅ / Tools ✅ / **Adapter ❌** / **State ❌** / Verification (預留) |
| TraceContext propagation | ⚠️ 設計到位、未使用 | adapter 簽名收 `trace_context` 8 處，但**無 start_span 呼叫**；API 層 0 個 `create_root()` |
| pg_partman 真升級 | ⚠️ 部分 | Dockerfile.postgres 升 `postgres:16` ✅；`CREATE EXTENSION` ✅；**`create_parent()` 推遲到「ops runbook」** ❌ |
| 4 Lint rules 真強制 | ✅ Passed (4+1) | 5 個 lint script + lint.yml CI workflow + 單元測試（PASS + FAIL fixtures） |
| W3-2 TraceContext gap 來源 | ⚠️ 49.4 Day 3 部分責任 | ABC + Tracer 給了，但 **未在主流量呼叫**（adapter 無 span / API 無 root），50.2 開發者可繼承「沒有上游能 import」假象 |
| 阻塞 52.2 判定 | ⚠️ Conditional | 不阻塞 52.2 編寫，但**強烈建議** Sprint 50.x 補 adapter + state 埋點，否則 chat 主流量永遠無 trace 可看 |

---

## Phase A — Plan/Checklist 對齐（10 min）

讀取 `sprint-49-4-plan.md` Day 3-5 預期 deliverables，對 commits 比對：

| Day | Plan Deliverable | Commit Evidence | 結果 |
|-----|------------------|-----------------|------|
| 3 | OTel SDK 鎖版本（==1.22.0 / 0.43b0） | `requirements.txt` 用 `>=1.27,<2.0` | ❌ |
| 3 | Tracer ABC 實作（OTelTracer 具體類） | `tracer.py` `OTelTracer` + `NoOpTracer` | ✅ |
| 3 | 7 必埋 metric 註冊 | `metrics.py` (未驗證細節) | 🟡 |
| 3 | JaegerExporter + PrometheusExporter | `exporter.py` 存在，**OTLP 取代 Jaeger native** | 🟡 偏離但合理 |
| 3 | `docker-compose.dev.yml` 加 jaeger + prometheus | dirty 但未驗服務啟動 | 🟡 |
| 3 | 6 unit tests | (未列出細節) | 🟡 |
| 4 | 4 lint scripts | 5 個（多 1 個 AP-1） | ✅+ |
| 4 | `.pre-commit-config.yaml` + `lint.yml` | `lint.yml` CI 強制 5 條 + unit tests | ✅ |
| 4 | `Dockerfile.postgres` (`postgres:16` + partman) | `docker/Dockerfile.postgres` `FROM postgres:16` | ✅ |
| 4 | `0010_pg_partman.py` + create_parent for 3 tables | 只 CREATE EXTENSION，**create_parent 推遲到 ops runbook** | ❌ |
| 4 | `tool_calls.message_id` FK 決策 | (未驗證) | 🟡 |
| 5 | FastAPI + /health + middleware | (未驗證) | 🟡 |
| 5 | Phase 49 README 4/4 | commit msg 確認 | ✅ |

**對齐評分**：7/13 ✅，4/13 🟡（未驗證或部分），2/13 ❌（OTel 鎖版本 + create_parent）

---

## Phase B — OTel 整合真實性（15 min）

### B.1 OTel SDK 鎖版本 ❌

`backend/requirements.txt` L32-38:
```
opentelemetry-api>=1.27,<2.0
opentelemetry-sdk>=1.27,<2.0
opentelemetry-exporter-otlp>=1.27,<2.0
opentelemetry-exporter-prometheus>=0.48b0,<1.0
opentelemetry-instrumentation-fastapi>=0.48b0,<1.0
opentelemetry-instrumentation-sqlalchemy>=0.48b0,<1.0
opentelemetry-instrumentation-redis>=0.48b0,<1.0
```

- **`observability-instrumentation.md`** 要求**鎖具體版本**：`opentelemetry-api==1.22.0`，避免 breaking change
- 實際使用 `>=1.27,<2.0` 浮動範圍
- **理由**：commit/註解推測是因 Jaeger native exporter 在 1.27+ 棄用、改用 OTLP。但這不是放棄鎖版本的理由 — 應改為 `==1.27.0` 等
- **風險**：CI 不可重現；某個 minor bump 即可導致 `metrics.py` 行為變化

### B.2 Tracer ABC 實作 ✅

`agent_harness/observability/_abc.py`:
- `Tracer` ABC 完整：`start_span()` / `record_metric()` / `get_current_context()` 全 `@abstractmethod`
- 簽名收 `trace_context: TraceContext | None` ✅
- `start_span` 回傳 `AbstractAsyncContextManager[TraceContext]` ✅

`agent_harness/observability/tracer.py`:
- `NoOpTracer`（測試 / dev）+ `OTelTracer`（生產）兩實作
- TraceContext propagation 邏輯正確（parent / child trace_id / span_id 串接）
- Tenant baggage 透過 attributes 注入

對齐 `17-cross-category-interfaces.md` §Contract 12 ✅

### B.3 5 處必埋點實際覆蓋 ❌（2/5 = 40%）

對 5 處必埋點 grep `tracer\.|start_span|record_metric`：

| 必埋點 | 範疇 | 實際 | 結果 |
|--------|------|------|------|
| 1. Loop 每 Turn | 範疇 1 | `orchestrator_loop/loop.py` 1 處 | ✅ |
| 2. Tool 執行 | 範疇 2 | `tools/executor.py` 1 處 | ✅ |
| 3. **LLM 呼叫** | **Adapter** | `adapters/azure_openai/` **0 處** | ❌ |
| 4. Verification | 範疇 10 | Phase 54.1 才上 | N/A (預留) |
| 5. **State Checkpoint** | **範疇 7** | `agent_harness/state_mgmt/` **0 處** | ❌ |

**最嚴重發現**：
- Adapter 層完全無 instrumentation。**Azure OpenAI API 呼叫的延遲、token 使用、錯誤都無 trace**
- State_mgmt 層完全無 instrumentation。Checkpoint write/read 不可觀測
- 這跟 `metrics.py` 設計的 `llm_chat_duration_seconds` / `llm_tokens_total` metric 完全脫節 — metric 註冊了但**沒人 emit**（AP-4 Potemkin Feature 風險）

### B.4 TraceContext propagation 真實性 ⚠️

- `adapters/azure_openai/adapter.py`: `trace_context` 出現 8 次（簽名與 attribute 設定），但**無 `tracer.start_span()` 呼叫** → 簽名是「裝飾」非「行為」
- `backend/src/api/`: `create_root|TraceContext` **0 個**結果 → API 入口從不創建 root context
- 結合 W3-2 finding（50.2 chat handler 0 個 TraceContext）：

**W3-2 root cause 結論**：
> 49.4 Day 3 交付了 ABC + Tracer 兩層，但**主流量呼叫鏈完全沒接上**。50.2 chat handler 開發者打開 adapter 看到 `trace_context` 參數但無前置範例（Loop 與 ToolExecutor 是內部呼叫，API 層沒有 root context creation 範例），自然偷砍。**這是上游 49.4 Day 3 的「未完成的下半段」**，不單是 50.2 開發者偷砍。

---

## Phase C — pg_partman 升級（5 min）

### C.1 docker-compose / Dockerfile ✅
- `docker/Dockerfile.postgres` `FROM postgres:16`（full 鏡像，非 alpine）✅
- `docker-compose.dev.yml` 已標記 dirty（修改）

### C.2 Migration 0010 ⚠️ 部分

`backend/src/infrastructure/db/migrations/versions/0010_pg_partman.py`:
- ✅ `CREATE EXTENSION IF NOT EXISTS pg_partman`
- ❌ **`create_parent()` 沒有執行** — 移到「OPS RUNBOOK」註解內，等待手動執行
- 註解的理由：「現有 partition 是手動建的，跑 create_parent 要先遷移到 partman 命名」

**評估**：理由合理（避免 prod 數據風險），但**plan 承諾偷砍**。Sprint 49.4 plan Story 49.4-6 明文寫「create_parent for messages / message_events / audit_log（p_premake=6）」— 實際變成「extension 裝起來 + 文檔」。
**影響**：Phase 50+ 仍會在 partition NOW() 邊界撞牆（自動 partition rolling 沒啟動）。

---

## Phase D — 4 Lint Rules 真實性 ✅

### D.1 Lint scripts 存在
`scripts/lint/`:
1. `check_duplicate_dataclass.py` ✅
2. `check_cross_category_import.py` ✅
3. `check_sync_callback.py` ✅
4. `check_llm_sdk_leak.py` ✅
5. `check_ap1_pipeline_disguise.py` ✅ (bonus from W3-1)

### D.2 CI workflow ✅
`.github/workflows/lint.yml`:
- 5 條 lint rules 全在 PR / push to main 觸發
- 每條 step `run: python scripts/lint/check_*.py` → exit 1 真 fail
- 額外 step：`pytest tests/unit/scripts/lint -v`（fixtures 驗證 PASS+FAIL 雙向）

### D.3 LLM SDK leak 細節 ✅
`check_llm_sdk_leak.py`：regex-based + 允許清單（azure_openai 內可 import openai）。設計正確；不是 fake green。

**Lint rules 是 49.4 Day 4-5 最完整的交付**。

---

## Phase E — 跨範疇 + 整合驗證

### E.1 W3-2 TraceContext gap root cause 解構

| 層級 | 49.4 Day 3 交付 | 50.x 主流量 | gap |
|------|-----------------|-------------|------|
| ABC 簽名 | `Tracer.start_span(trace_context=...)` ✅ | adapter signature 收 trace_context | ✅ |
| 具體實作 | `OTelTracer` + `NoOpTracer` | (no instance bound to handler) | ❌ |
| API 入口 root context | (未交付，plan 也沒明文要求) | `create_root()` 0 處 | ❌ 兩層都缺 |
| Adapter LLM call span | (未交付) | adapter 無 `tracer.start_span` | ❌ |
| State checkpoint span | (未交付) | state_mgmt 無 tracer | ❌ |

**結論**：W3-2 chat handler 0 個 TraceContext **不是 50.2 偷砍**，而是 **49.4 Day 3 ABC + Tracer 落地後未補主流量埋點**的下游症狀。此次 audit 應將此責任歸於 49.4，而非單獨怪罪 50.2。

### E.2 5 處必埋點 vs 實際代碼

跟 W4P-3（51.1 Tool Layer Level 3）對比：
- 51.1 ToolExecutor 真有 `tracer.start_span` ✅（W4P-3 已驗證為「整合紀律好」）
- 51.2 Memory store **無**（state_mgmt 旁路；W4P-4 也未提到 memory 有 instrumentation）
- 49.4 自身範圍埋點（Loop + Tools）✅
- **越往下游、越接近 LLM 與 DB 寫入**，埋點越缺

---

## 結論評分

| 維度 | 分數 | 備註 |
|------|------|------|
| Plan 對齐 | 6/10 | OTel 鎖版本 + create_parent 偷砍 |
| 18 文件對齐 | 6/10 | observability-instrumentation.md 5 處 → 實際 2 處 |
| 不正常開發 | ⚠️ | Pattern: 「給 ABC + 元件、不接主流量」（同 W3-2/W4P-4 Potemkin pattern） |
| 阻塞 52.2 | ❌ 不阻塞 | 但會被列入 50.x carryover 必修項 |

---

## 修補建議（按優先序）

### 🔴 P0（Sprint 50.x 必補）
1. **Adapter LLM span**：`adapters/azure_openai/adapter.py` 在 `chat()` 真實呼叫 `tracer.start_span(name="llm_chat", category=SpanCategory.ADAPTER, ...)` + emit `llm_chat_duration_seconds` + `llm_tokens_total` metric
2. **API 入口 root context**：`backend/src/api/` chat handler 必須 `TraceContext.create_root()` 並 propagate 到 Loop / Adapter
3. **State checkpoint span**：`state_mgmt/checkpointer.py` 補 `state_checkpoint_save` span

### 🟡 P1（Sprint 51.x）
4. OTel SDK 改回 `==1.27.x` 等具體版本（非 `>=`）
5. `0010_pg_partman.py` 補 `create_parent()` migration（dev DB recreate-from-scratch 無數據風險）
6. Memory store + Memory Retrieval 補 tracer

### 🟢 P2（Phase 53+）
7. Verification span（範疇 10 上線時）
8. Subagent dispatch span
9. Compaction span

---

## 不正常開發 / 偏離 findings

| Finding | 嚴重性 | 對應規則 |
|---------|--------|---------|
| OTel SDK 浮動版本 | 🟡 中 | `observability-instrumentation.md` §SDK 版本鎖定 |
| Adapter 0 instrumentation（plan 沒明文要求但 rule 要求） | 🔴 高 | `observability-instrumentation.md` §5 處必埋點 #3 |
| State_mgmt 0 instrumentation | 🔴 高 | 同上 #5 |
| `create_parent()` 由 plan 承諾轉為 ops runbook | 🟡 中 | Plan Story 49.4-6 |
| `trace_context` 簽名裝飾不行為（adapter） | 🔴 高 | AP-4 Potemkin 變體 |
| API 層無 `create_root()` 範例 / 入口 | 🔴 高 | 上游缺失導致 W3-2 偷砍 |

---

## 阻塞 52.2 判定

**不阻塞**（lint + Tracer ABC + Loop/Tool 埋點足夠 52.2 編寫 prompt builder + memory 整合）

但 **52.2 必須在文件中明文標記**：
- 「Tracer instance 從何處 inject」必須有範例
- 若 52.2 有任何 LLM 呼叫流程，必須 propagate `trace_context`，否則加深 W3-2 模式

**強烈建議**：將 P0 三項（adapter span / API root context / state span）排入 Sprint 50.2 或 50.3 的 plan checklist，**不要再延後**，否則 chat 主流量正式上線時所有 LLM call 都是 trace 黑洞。

---

**Audit 完成**：2026-04-29
**下次 audit 建議**：W4P-5（mini-W4-pre 總結）整合 W3-1/2、W4P-1/2/3/4 五份 audit 結論，給用戶綜合 Phase 49-51 健康度評分。
