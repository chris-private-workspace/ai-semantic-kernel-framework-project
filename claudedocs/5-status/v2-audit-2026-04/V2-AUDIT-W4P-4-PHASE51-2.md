# V2 Audit W4P-4 — Phase 51.2 Memory Level 3

**Audit 日期**: 2026-04-29
**Auditor**: Research Agent (W4-pre series)
**結論**: ⚠️ **Concerns — Multi-tenant 正確設計但未進主流量；W3-2 鏡像反模式存在於 tools handler；Tests 大量 mock 依賴 (AP-10)**

---

## TL;DR（先看這個）

| 維度 | 評級 | 說明 |
|------|------|------|
| Plan/Checklist 對齐 | ✅ | 5 day deliverables 全部對應 commits |
| Retrospective 誠實度 | ✅ | 主動披露 5 個 Improve + 5 個 Lesson + CARRY-026~030 |
| 5 層真分離（Schema） | ✅ | 5 個獨立 ORM tables（migration 0007）；非 enum 假分層 |
| 3 time-scale 機制 | ⚠️ | metadata JSONB 存 time_scale + expires_at 24h；semantic 整列 stub（CARRY-026）|
| **Multi-tenant Layer 層** | ✅ | UserLayer / TenantLayer 均強制 tenant_id；缺 → return [] 或 raise |
| **Multi-tenant Tools handler** | ❌ | tenant_id 從 ToolCall.arguments 讀（LLM-controlled 通道）— **W3-2 鏡像反模式**（CARRY-030 自承）|
| **chat router 整合** | ❌ | `src/api/v1/chat/router.py` 0 命中 memory_search/memory_write — **未進主流量**（51.2 沒做這層 wiring）|
| Cache process-wide dict | ✅ | 0 命中（無 W3-2 SessionRegistry 鏡像反模式）|
| Extraction 真 LLM | ✅ | extraction.py 用 ChatClient ABC（neutrality 守住）|
| Conflict_resolver | ✅ | 4 條規則真實作（confidence/freshness/layer-priority/HITL fallback stub）|
| Lead-then-verify demo | ✅ | 2 e2e tests pass（mock CRM；機制可驗證）|
| **Tests 強度（最大紅旗）** | ❌ | unit tests 全用 MagicMock session；integration tenant_isolation 用 `_StubUserLayer`（測試專用 stub）— **AP-10 mock-only path**；0 real PG 測試 |
| LLM Provider Neutrality | ✅ | grep 0 SDK leak in memory/ |
| 17.md 對齐 | ✅ | §1.1 / §2.1 / §3.1 / §4.1 同步 |
| 阻塞 52.2 啟動 | ⚠️ | **不阻塞但需先補 P1 wiring + real PG tests**；52.2 PromptBuilder 整合前必須跑通 chat router → memory tools 鏈路 |

---

## Phase A — Plan/Checklist 對齐 + 誠實度

### A.1 Deliverables → Commits 對應

| Day | Plan deliverable | Commit | 狀態 |
|-----|------------------|--------|------|
| 1 | MemoryHint 擴 5 欄位 + ABC ttl→time_scale | 4ab5ef8e | ✅ |
| 2 | 5 layer concrete impl + 31 unit tests | f7d06141 | ✅ |
| 3 | retrieval + conflict_resolver + extraction + 20 tests | 948fcd5f | ✅ |
| 4 | memory_tools real handler + register_builtin_tools wiring + 8 integration tests | 2ad3fa20 | ✅ |
| 5 | tenant isolation + lead-then-verify + Cat 3 → Level 3 | 73967edd | ✅ |

**全部 5 day 對應到 5 commits，無「靜默砍 scope」。**

### A.3 Retrospective 誠實度

✅ 主動披露：
- Day 5 才補 tenant isolation tests（plan 也是 Day 5 — 非事後補救，但**該紅旗依然存在**：tenant 隔離保險 Day 1 就應守住設計，不是 Day 5 補測試）
- 5 個 Improve（security hook 誤判 / `__init__.py` 衝突 / wire 點寫錯 / ABC 簽名不一致 / Day 5 估時偏高）
- 5 個 CARRY items（026-030）獨立追蹤
- DoD §3 / §4 標 "Day 5 closeout commit pre-checks pending" — 不過度承諾

⚠️ 透明披露但需注意：
- Action Item AI-3 "tests `__init__.py` convention" + AI-4 "security hook trigger pattern" 推 52.x — 為 52.x backlog 增量
- Maturity table Cat 12 仍 Level 2（MemoryAccessed event payload 擴但 retrieval span 推 53.x）— 與 W4P-1 49.4 OTel 結論一致

---

## Phase B — 5 層 × 3 時間軸真實性

### B.1 Schema 結構（真分離 vs 假分層）

✅ **真 5 表分離**（per `infrastructure/db/models/memory.py` + migration 0007）：
- memory_system（global，no tenant_id）
- memory_tenant（TenantScopedMixin）
- memory_role（junction → roles.tenant_id）
- memory_user（TenantScopedMixin + user_id，**核心**）
- memory_session（junction → sessions.tenant_id）

不是 1 table + layer enum 的 AP-3 假分層。

### B.2 5 store 對齐 17.md ABC

✅ 5 layer 全實作 MemoryLayer ABC（_abc.py），signatures 統一 `read()` / `write()` / `evict()` / `resolve()` 帶 `tenant_id` / `user_id` / `time_scale` / `trace_context`。

### B.3 3 time-scale TTL

⚠️ 部分實作：
- short_term：UserLayer write 設 expires_at = now + 24h ✅
- long_term：expires_at = NULL ✅
- semantic：整列 return [] / stub（CARRY-026 Qdrant Phase 53.x）⚠️

**TTL cleanup job：未見 cron / Celery 真清過期**（Day 5 closeout 沒提；推 53.1 範疇 7 State Mgmt CARRY-027）。

---

## Phase C — Multi-tenant 隔離真實性（最關鍵）

### C.1 Memory Layer 內部 tenant filter

✅ **所有 query 強制 tenant_id**：
- UserLayer.read：`tenant_id is None → return []`；query `WHERE tenant_id = $1 AND user_id = $2 ...`
- UserLayer.write：`tenant_id is None → raise ValueError`
- UserLayer.evict：`tenant_id is None → return`；query `WHERE id = $1 AND tenant_id = $2`
- TenantLayer.read/write/evict：同樣強制（grep 確認）
- SessionLayer：composite key (tenant_id, session_id)
- SystemLayer：read-only global（合理無 tenant_id）

64 處 tenant_id occurrences across 8 memory files — 設計層紀律守住。

### C.2 Tools Handler tenant context（**最大紅旗 — W3-2 鏡像**）

❌ **memory_tools.py L177-185 / L236-241**：
```python
tenant_id = _parse_uuid(args.get("tenant_id"))   # ← 從 ToolCall.arguments 讀
user_id = _parse_uuid(args.get("user_id"))
session_id = _parse_uuid(args.get("session_id"))
```

**這就是 W3-2 chat router multi-tenant 鐵律違反的鏡像**：
- W3-2: tenant_id 從 query string 讀
- W4P-4: tenant_id 從 LLM-generated tool call args 讀

**自承為 CARRY-030**（plan §file-header L17-18 + retrospective）：
> "The agent loop is expected to inject these from the authenticated execution context before invoking the executor. LLMs do NOT control these fields directly (loop injection happens after the LLM produces the tool call). Phase 53.3 will replace this with proper ExecutionContext threading."

**問題**：
- "expected to inject" 不是 "enforced to inject" — 設計依賴 caller 自律
- agent loop injection point **未實作**（沒搜到 tenant injection middleware in agent_harness/orchestrator_loop/）
- 中間如有缺漏，LLM 可生成偽 tool_call 帶 attacker-controlled tenant_id 嘗試跨租戶讀取
- Layer 層雖有第二防線（強制 tenant_id），但**只擋 None，不擋 attacker-supplied valid tenant_id_x**

**等級**：與 W3-2 SessionRegistry 同級 — 設計斷層在中間層；尚未阻塞 demo 因為 demo 不過 chat router；但 52.2 PromptBuilder 整合前必須先補。

### C.3 Chat Router Integration（**第二大紅旗**）

❌ `src/api/v1/chat/router.py` grep `memory_search|memory_write|MemoryRetrieval|UserLayer|memory_tools` = **0 命中**

51.2 完成「memory tools 真實 handler + register_builtin_tools 注入點」，但**從未在 API 層真調用 register_builtin_tools(memory_retrieval=..., memory_layers=...)**。

→ 主流量（POST /chat → agent loop → tool execution）目前**走 placeholder fallback**（memory_placeholder_handler L145 — return error JSON）。

**這違反 V2 約束 2「主流量驗證原則」** — 51.2 plan §1 Story 5 寫 "範疇 3 是穩定的、可被 PromptBuilder（Cat 5）注入的" 但**整合鏈路缺最後一哩**。

### C.4 Process-wide Cache（W3-2 SessionRegistry 鏡像）

✅ grep `_cache|memo_cache|memory_cache|MemoryCache|_lru_cache|_session_cache` in memory/ + memory_tools.py = **0 命中**

無 process-wide dict。`UserLayer.__init__` 收 `session_factory` 注入 — 每次 query 從 factory 開新 session（per-request scoped）。

**唯一 cache 提及**：`agent_harness/_contracts/cache.py:50 cache_memory_layers: bool = True` — 這是 **Anthropic prompt caching breakpoint 標記**（Cat 4 Context Mgmt 的 ephemeral cache hint），非 process-wide store。✅ 不算違規。

---

## Phase D — Retrieval / Conflict / Extraction 真實性

### D.1 Retrieval 演算法

✅ MemoryRetrieval.search 跨 5 layers 並行；non-empty time_scales 過濾；ILIKE substring match（無 vector — semantic stub）；ranked by `relevance_score * confidence`。
- 4 處 tenant_id propagation（tenant_id 真傳 down）
- semantic-only request → empty list（CARRY-026 stub 自承）

非「永遠 return all rows」的 ranking 裝飾。

### D.2 Conflict_resolver 4 條規則

✅ 真實作（unit test test_conflict_resolver.py 8 tests pass）：
1. confidence ≥ 0.8 直勝
2. last_verified_at < 7d 取最新
3. layer specificity（user > role > tenant > system）
4. HITL fallback（51.2 stub，trigger 推 53.3）

非 last-write-wins 假邏輯。

### D.3 Extraction（LLM-driven）

✅ extraction.py 用 ChatClient ABC（neutrality 守住）；4 unit tests + 3 integration tests。
- AP-10 風險：unit test 用 `MockChatClient`（49.4 ABC-conformant，retrospective §3 自承）
- 真 LLM 行為驗證需 53.x 在環境跑（Action Item AI-5）

非 regex 假裝 NLP。

### D.4 Lead-then-verify Demo

✅ 2 e2e tests in test_lead_then_verify_workflow.py pass：
- stale hint → mock CRM 驗證 → 不一致時 memory_write 更新
- consistent path 不重複 rewrite

機制可驗證但**仍走 stub layer**（per integration tests 模式）。

---

## Phase E — Tests 強度（重大 AP-10）

### E.1 pytest 結果

✅ **69/69 PASS in 0.36s**：
- unit/agent_harness/memory: 41 tests
- integration/memory: 16 tests
- e2e/test_lead_then_verify_workflow.py: 2 tests

retrospective 報 142 active passed = wider sanity (含其他 sprint tests)。51.2 sprint 自身 net delta +69 — 對齐。

### E.2 抽樣強度（**0.36s 是紅旗**）

❌ **AP-10 Mock vs Real Divergence 風險高**：

| Test | Backend | 真 PG? |
|------|---------|--------|
| test_user_layer.py | `MagicMock` session + `AsyncMock` execute | ❌ |
| test_tenant_layer.py | `MagicMock` session | ❌ |
| test_role_layer.py | `MagicMock` session | ❌ |
| test_system_layer.py | `MagicMock` session | ❌ |
| test_extraction.py | `AsyncMock` ChatClient + `MagicMock` session | ❌ |
| test_memory_tools_integration.py | `_StubUserLayer` (test-only stub) | ❌ |
| test_tenant_isolation.py | `_StubUserLayer` (test-only stub L43) | ❌ |
| test_lead_then_verify_workflow.py | mock CRM + stub layer | ❌ |

**等同：51.2 整個 testing 體系是 mock-only**。

ORM column types（`Numeric(3,2)` for confidence）/ JSON metadata serialization / RLS policy / 索引使用是否正確 — **完全未驗證**。

### E.3 RLS 紅隊

❌ test_tenant_isolation.py L43 `class _StubUserLayer` 是「Test-only layer that enforces tenant_id filter at read/write」— **驗證的是 stub 自己，不是真 UserLayer 對 PostgreSQL 的隔離行為**。

**這是測試 framework 自證，不是真 RLS 紅隊**。

49.3 Day 4 RLS 13 tables 雖建立，但 51.2 5 個 tenant isolation tests **完全沒接 asyncpg + rls_app_role**。49.3 RLS 工作的真實壓力測試 **還沒來**。

### E.4 手動 Cross-tenant 試讀

未執行（需 PG running + asyncpg + rls_app_role config）。建議納入 W4-final 重點。

---

## Phase F — 跨範疇 + 17.md 對齐

### F.1 17.md 對齐

✅ retrospective 自報 4 sections updated（§1.1 MemoryHint 5 fields / §2.1 ABC ttl→time_scale / §3.1 placeholder 移除 / §4.1 MemoryAccessed event）。

✅ 0 cross-category type 重複定義（grep MemoryHint 唯一 owner = `_contracts/memory.py`）。

### F.2 ABC 邊界

✅ MemoryLayer ABC（_abc.py）signatures 含 `trace_context: TraceContext | None`；retrieval / extraction / layers 全用 ABC，不重定義型別。

### F.3 52.2 PromptBuilder Readiness

⚠️ **半就緒**：
- ✅ MemoryHint dataclass 完整（5 新欄位）；retrieval API 設計可被 PromptBuilder 直接用
- ❌ chat router → register_builtin_tools(memory_retrieval=..., memory_layers=...) wiring **未建**
- ❌ 主流量 memory tool call 仍走 placeholder（return error）
- ⚠️ ExecutionContext threading 未實作 — 52.2 PromptBuilder 從哪拿 tenant_id?
  - 選項 A：等 53.3 ExecutionContext（推 1 個 phase = ~1 個月）
  - 選項 B：52.2 啟動前先補 P0 wiring（建議）

---

## 結論

| 維度 | 評級 | 注解 |
|------|------|------|
| Plan/Checklist 對齐 | ✅ | 5 day 全對應 |
| 5 層真分離 | ✅ | 5 ORM tables，非 enum 假 |
| 3 time-scale | ⚠️ | short/long_term 真；semantic stub |
| **Multi-tenant Layer 層** | ✅ | 強制 tenant_id；無 None 漏網 |
| **Multi-tenant Tools handler** | ❌ | W3-2 鏡像（CARRY-030 自承）|
| **Chat router 整合** | ❌ | 0 命中；主流量仍走 placeholder |
| W3-2 SessionRegistry 鏡像反模式 | ✅ | 0 process-wide cache |
| Retrieval / Conflict_resolver | ✅ | 真演算法非裝飾 |
| Extraction LLM | ✅ | ChatClient ABC（neutrality 守住）|
| **Tests 強度** | ❌ | 全 MagicMock + StubUserLayer（AP-10）|
| 17.md 對齊 | ✅ | 4 sections sync |
| **52.2 啟動** | ⚠️ | 不阻塞但需先補 P1 |

---

## 修補建議

### P0（建議納入 52.0 cleanup or 52.1 Day 0）

1. **建立至少 1 個 real PG integration test**（per layer = 5 tests）
   - 驗 ORM Numeric(3,2) confidence 不丟精度
   - 驗 metadata JSONB 真 round-trip
   - 驗 cross-tenant 真 RLS 阻擋（asyncpg + rls_app_role）
   - **這是 49.3 RLS 工作的第一個真壓力測試**
   - 估時：4-6h

### P1（52.2 Day 1 前必補）

2. **chat router → register_builtin_tools(memory_retrieval=..., memory_layers=...) wiring**
   - 否則 52.2 PromptBuilder 整合會發現 chat 主流量 memory tools 是 placeholder
   - 估時：2-3h

3. **ExecutionContext threading 提前**（部分先做）
   - W3-2 揭露 chat router multi-tenant 缺 → 補 dependency injection 同時補 tenant_id propagation 到 tool call sandbox
   - W4P-4 揭露 tools handler tenant 來源不可信 → 同問題同補
   - **這兩個 W 系列發現可一次性修補**
   - 估時：6-8h

### P2（推 53.x）

4. CARRY-026 Qdrant semantic axis（Phase 53.x）
5. CARRY-027 Extraction worker auto-trigger（Phase 53.1）
6. CARRY-028 OWASP LLM Top 10 prompt-injection sweep（Phase 53.3 + 53.4）
7. CARRY-030 ExecutionContext threading（Phase 53.3，與 RBAC CARRY-023 並進）

---

## 對 52.2 PromptBuilder 影響

**不阻塞 52.2 Day 1 啟動**（PromptBuilder 設計可獨立進行 dataclass 階層組裝），但：

- 若 52.2 計畫整合 memory layers 進 prompt：**P1 wiring 必須先補**，否則 PromptBuilder 從 chat router 拿不到真實 memory tools（會直接踩 placeholder fallback）
- 若 52.2 計畫獨立先建組裝層後續再 wire：可繼續，但 52.x cleanup 必須處理 P0+P1

**建議**：52.2 Day 0 必含 P0+P1 修補（10-15h），確保整合鏈路通過 real PG。

---

## 不正常開發 / 偏離 findings

### 1. **Plan §2.5 wire 點寫錯（retrospective §3 自承）**
   Plan 寫 `business_domain/_register_all.py` wire memory_handlers，實際是 `agent_harness/tools/__init__.py register_builtin_tools`。Day 4 中途修正。
   **Lesson**: 寫 plan wire 點前先 grep 既有 wire 結構（已 自承為 future plan rule）

### 2. **W3-2 鏡像反模式（CRITICAL）**
   tools handler tenant_id 從 ToolCall.arguments（LLM-controlled 通道）。雖 self-aware（CARRY-030），但與 W3-2 chat router 從 query string 讀 tenant_id 同性質：**信任不可信通道**。
   Layer 第二防線只擋 None，不擋 attacker-controlled valid UUID。

### 3. **49.3 RLS 工作首次壓力測試延後（CRITICAL）**
   51.2 是首個有條件真壓 49.3 RLS 13 tables 的 sprint，但 5 tenant_isolation tests 全用 stub。49.3 的 RLS policy 從未在 51.2 真實驗證 — 等同**RLS 是無用功直到 W4-final or 52.2**。

### 4. **Tests 全 mock 偏離 V2 testing.md**
   `.claude/rules/testing.md` 規定範疇 3 ≥ 80% coverage + 真 PG 整合測試。51.2 全 mock 違反該規則（隱形偏離）。retrospective Action Item AI-3 提及「tests `__init__.py` convention」但**沒提 AP-10 mock 違規問題**。

### 5. **主流量驗證原則違反（V2 約束 2）**
   chat router 0 命中 memory_search/memory_write — 51.2 實作完整但**主流量入口未串**。Story 1 / Story 2 驗收文字「工具呼叫實際路由到 MemoryRetrieval.search()」實際只在 mock-only test 環境驗證，主流量未過。

---

## 阻塞判定

- 52.2 Day 1 啟動: ⚠️ **不阻塞但需先補 P1**（建議 52.2 Day 0 整合 P0+P1）
- Phase 53.1 啟動: ⚠️ **不阻塞但 P0+P1 必須在 52.x cleanup 結束前完成**
- 52.x cleanup sprint scope: **P0+P1 進入；CARRY-030 也提前到 52.x（不等 53.3）**
- W4-final 範圍：手動 cross-tenant memory query（asyncpg + rls_app_role）+ 49.3 RLS 真壓力 + chat router → memory tools end-to-end smoke

---

**Maintainer**: Research Agent
**Created**: 2026-04-29 (W4-pre series, 4/5 audit)
**Next**: W4P-5 mini-W4-pre 總結
