# V2 Verification Audit W3-2 — Phase 50.2（POST /chat SSE 主流量）

**Date**: 2026-04-29
**Auditor**: Claude (W3-2 audit cycle)
**Sprint**: 50.2（feature/phase-50-sprint-2-api-frontend, 13 commits ahead of 50.1）
**Authority Source**: 18 文件（02-architecture-design / 16-frontend-design / 17-cross-category-interfaces / 10-server-side-philosophy / multi-tenant-data.md / observability-instrumentation.md）
**Status**: 🟡 **PASS WITH SIGNIFICANT CAVEATS**（質量門檻 ✅；架構紀律有 3 個 critical gap）

---

## 摘要表

| Phase | 結果 | 摘要 |
|-------|------|------|
| **A. Plan/Checklist 對齊** | 🟢 PASS | 100% deliverables ✅ / 17% actual time / retro 誠實列 9 carryover |
| **B. POST /chat 端點 + SSE events** | 🟡 PARTIAL | 8 events ✅ 是 native LoopEvent dataclass / **但無 tenant_id / 無 TraceContext** |
| **C. chat-v2 Frontend** | 🟢 PASS | 真整合 backend（8 檔 + fetch+ReadableStream + Zustand）非 stub |
| **D. Worker Factory** | 🟡 PARTIAL | 工廠存在但 router **完全 bypass**（inline await）；W2-2 carryover 未動 |
| **E. Pytest + Quality** | 🟢 PASS | 46/46 chat tests / 259 全 tests / mypy strict / 5 lints |
| **F. 跨範疇集成（50.2 ↔ 50.1）** | 🟢 PASS | router → AgentLoopImpl → LoopEvent → SSE → frontend 完整鏈路 |

**綜合結論**：50.2 在「**echo demo + real LLM 主流量打通**」這個 sprint goal 上完成度 100%。但作為 V2 第一條 backbone，它**繞過了多租戶與觀測性兩個跨切面的鐵律**，違反 V2 五大核心約束之 #1（Server-Side First）與範疇 12（Observability Cross-Cutting）。**不會阻塞 Phase 51-52** 但 **必須在 Phase 53.1-53.2 補完否則阻塞 SaaS-ready**。

---

## Phase A — Plan/Checklist 對齊

### A.1 Plan 13 deliverables → 實際交付對應

| # | Plan 項 | 實作 | Commit | 狀態 |
|---|--------|------|--------|------|
| 1 | POST /api/v1/chat/ + SSE | `api/v1/chat/router.py` | 8e615dda | ✅ |
| 2 | GET /sessions/{id} | router.py | 8e615dda | ✅ |
| 3 | POST /sessions/{id}/cancel | router.py | 8e615dda | ✅ |
| 4 | sse.py serializer (7 events) | `api/v1/chat/sse.py`（8 events 實作 — bonus +1）| 8e615dda + 4e04ae77 | ✅+ |
| 5 | session_registry.py | `api/v1/chat/session_registry.py` | 8e615dda | ✅ |
| 6 | handler.py (echo + real_llm) | `api/v1/chat/handler.py` | 8e615dda | ✅ |
| 7 | 4 個新 LoopEvent | 加 3 個（TurnStarted/LLMRequested/LLMResponded）+ 擴 ToolCallExecuted | 4e04ae77 | 🟡（合理替代）|
| 8 | agent_loop_worker.py 真實 handler | `build_agent_loop_handler` factory + `execute_loop_with_sse` | 4e04ae77 | ✅ |
| 9 | frontend/features/chat_v2/ 8 檔 | 全到位 | 8782a49e + 4805aa6f | ✅ |
| 10 | pages/chat-v2/index.tsx | 取代 placeholder | 4805aa6f | ✅ |
| 11 | unit tests ~30 | 43 unit + 3 integration = **46** | 多 commits | ✅+ |
| 12 | CARRY-001（python -m pytest rule）+ CARRY-002（datetime UTC）| testing.md + events.py | 80338f04 | ✅ |
| 13 | progress.md + retrospective.md + Phase 50 README | 全到位 | cf076e64 | ✅ |

**Plan 對齊度**：100%（13/13），1 項合理替代（#7），2 項 bonus（#4 多 1 event、#11 多 16 tests）。

### A.2 Retrospective 誠實度

✅ retro 明列 **9 carryover (CARRY-010..018)** + **5/9 50.1 retro carry-over closed**。明確標 🚧 + reason 的項：
- CARRY-006（streaming partial-token → 51.2/52.1）
- CARRY-010（vitest 沒裝 → 51+）
- 3.1（dev server curl test 跳過 → TestClient 替代）
- 4.5（瀏覽器 e2e 留下 session）
- 5.1（real_llm 真互動留下 session）

✅ 結構對齊 50.1（estimate accuracy 19.7% / 3 lessons / cumulative state）。**未發現過度樂觀**。

### A.3 Checklist Sacred Rule 自檢

✅ 沒刪未勾選項（搜尋 checklist 1.1 中的 `[ ] 建 schemas.py` 仍保留為 🚧 形式）
✅ 所有變動只 `[ ]` → `[x]` 或 🚧+reason（共 **15 個 🚧 reason 紀錄**）

**Phase A 結論**：🟢 100% 對齊，retro 透明，plan 紀律執行典範。

---

## Phase B — POST /chat 端點 + 8 SSE events

### B.1 8 SSE events 真實性對 17.md §4.1

實作的 8 個 SSE event types（router → sse.py）：

| SSE event 字串 | LoopEvent dataclass | 17.md owner | 中性？ |
|----------|---------|---------|------|
| `loop_start` | `LoopStarted` | Cat 1 | ✅ |
| `turn_start` | `TurnStarted` (Day 2 新增) | Cat 1（17.md 同步擴條目）| ✅ |
| `llm_request` | `LLMRequested` (Day 2 新增) | Cat 1 | ✅ |
| `llm_response` | `LLMResponded` (Day 2 新增) | Cat 1 | ✅ |
| `tool_call_request` | `ToolCallRequested` | Cat 6 | ✅ |
| `tool_call_result` (success) | `ToolCallExecuted` (擴 result_content) | Cat 2 | ✅ |
| `tool_call_result` (error) | `ToolCallFailed` | Cat 2 | ✅ |
| `loop_end` | `LoopCompleted` | Cat 1 | ✅ |

✅ **全部 8 個 events 都是 17.md Contract 中性 LoopEvent dataclass**（不是 ad-hoc dict）
✅ 17.md §4.1 表確實同步擴 3 entries（checklist 2.6 紀錄）
✅ 序列化路徑：`LoopEvent → serialize_loop_event() → format_sse_message()` — pure transformation
✅ `Thinking` event 智慧處理：序列化返回 `None` → router skip（避免與 LLMResponded 重複）— Day 2 design decision，紀錄於 sse.py docstring
✅ 14 deferred events raise `NotImplementedError` 帶 sprint pointer（無 Potemkin / 無偽裝）

### B.2 多租戶隔離 ⚠️ **CRITICAL GAP**

**搜尋結果**：
```
backend/src/api/v1/chat/ 下：tenant / current_tenant / TenantContext / get_current_tenant  → 0 matches
```

**對照 .claude/rules/multi-tenant-data.md §規則 3**：
> 規則 3：所有 API Endpoint 必接 current_tenant Dependency

**實際**：
- `POST /api/v1/chat/` 無 `Depends(get_current_tenant)` — **違反**
- `GET /api/v1/chat/sessions/{id}` 無 tenant 過濾 — **任何 session_id 全局可讀**（隱私洩漏風險）
- `POST /sessions/{id}/cancel` 無 tenant 過濾 — **任何人可 cancel 任何 session**
- `SessionRegistry` 是 in-memory dict 全 process 共享，無 tenant key — **跨租戶 session_id 衝撞風險**
- integration test 註明「Boots a FastAPI app with the chat router only (skip OTel + tenant middleware)」 — **明文 skip multi-tenant test**

**注意**：49.3 已部署 `TenantContextMiddleware` 設置 `request.state.tenant_id`，但 50.2 router **未消費**該值。

**影響等級**：對 single-tenant 開發環境**不阻塞**；對 multi-tenant production / SaaS-ready **必修**。

**修補建議（Phase 53.1）**：
1. router 加 `current_tenant: UUID = Depends(get_current_tenant)` 三個 endpoint
2. SessionRegistry 改 key = `(tenant_id, session_id)` tuple
3. integration test 加 cross-tenant denial 案例
4. checklist 2.6 「router 不主動呼叫 worker handler」decision **不影響此修補**

### B.3 TraceContext 注入 ⚠️ **CRITICAL GAP**

**搜尋**：
```
backend/src/api/v1/chat/ 下：tracer / TraceContext / setup_opentelemetry / trace_context  → 0 matches
```

**對照 .claude/rules/observability-instrumentation.md §1（Loop 每 turn 開頭+結尾）**：
> 所有 ABC 方法簽名必須接受 trace_context: TraceContext | None（範疇 12 cross-cutting）

**對照 sprint-50-2-plan.md §4.1**：
> Tracer / Tenant：經 TenantContextMiddleware（49.3 已配）+ setup_opentelemetry（49.4 已配）；endpoint 創建 TraceContext.create_root() 傳入 AgentLoopImpl.run()。

**實際**：
- router._stream_loop_events() 呼叫 `loop.run(session_id=..., user_input=...)` — **無 trace_context 參數**
- AgentLoopImpl 內 LLM call、tool execution、checkpoint 全部丟失 trace 鏈
- SSE event 不帶 `trace_id`（observability-instrumentation.md §「SSE 事件必含 trace_id」）— **違反**
- 49.4 setup_opentelemetry 安裝了 instrumentation，但 chat router 是個**觀測黑洞**

**影響等級**：開發 / debug 仍可（pytest 涵蓋）；production trouble-shooting **將很困難**；違反範疇 12 cross-cutting concern。

**修補建議（Phase 49.4 carry / Phase 53.2）**：
1. router 加 `trace_context = TraceContext.create_root()` 並傳入 `loop.run()`
2. AgentLoopImpl 接 trace_context（範疇 1 簽名擴）
3. SSE frame 加 `trace_id` 給 frontend（debug 入口）

### B.4 sprint-50-2-plan §4.5 LLM-Provider Neutrality 自查

✅ `agent_harness/**` 下無 `import openai/anthropic`（confirmed by Lint #1）
✅ handler.py 用 `MockChatClient`（49.4）做 echo_demo
✅ real_llm 用 `AzureOpenAIAdapter`（49.4）— 經 ChatClient ABC，**真整合非 mock**

**Phase B 結論**：🟡 SSE event 結構正確（8 events 全 Contract）；但 multi-tenant + observability 兩跨切面 missing — 不偽裝 / 不亂寫，是**明確的「scope 外」決策**，但 plan §4.1 明文承諾的 TraceContext 注入未做。

---

## Phase C — chat-v2 Frontend

### C.1 8 檔結構

```
frontend/src/features/chat_v2/
├── components/
│   ├── ChatLayout.tsx        ✅
│   ├── InputBar.tsx          ✅
│   ├── MessageList.tsx       ✅
│   └── ToolCallCard.tsx      ✅
├── hooks/useLoopEventStream.ts  ✅
├── services/chatService.ts      ✅
├── store/chatStore.ts           ✅（Zustand 7-case mergeEvent）
└── types.ts                     ✅（7-arm discriminated union）
```

### C.2 SSE 消費實作

✅ chatService.ts 用 `fetch + response.body.getReader()` + TextDecoder（**不用 EventSource**，因 EventSource 不支援 POST body）
✅ `parseSSEFrame` 用 `KNOWN_LOOP_EVENT_TYPES` Set gate 過濾 unknown event → null（forward-compat）
✅ AbortController 支援 cancellation（Stop button → backend session cancelled）
✅ 7 個 event 都在 chatStore mergeEvent 處理（loop_start / turn_start / llm_request / llm_response / tool_call_request / tool_call_result / loop_end）+ exhaustive check
✅ Auto scroll-to-bottom / 3-status badge / mode toggle / Enter vs Shift+Enter

### C.3 與 backend 整合

✅ `fetch("/api/v1/chat/", { method: "POST", body: JSON.stringify({...}) })` — 對齊 backend
❌ **無 X-Tenant-Id header**（因 backend 不要求；但如修 B.2，frontend 也須補）
🚧 vitest 沒裝 → 0 frontend test（CARRY-010 明標 51+）— **不算 Potemkin，是 deferred 紀錄**

**Phase C 結論**：🟢 真整合非 stub；Sprint 50.2 frontend 是 V2 第一個有完整 SSE 流的頁面。

---

## Phase D — Worker Factory（W2-2 carryover）

### D.1 build_agent_loop_handler 是否真做？

✅ `runtime/workers/agent_loop_worker.py` 加：
- `execute_loop_with_sse(...)` — common driver
- `build_agent_loop_handler(...)` — TaskHandler factory
- 保留 `_default_handler` stub（DEPRECATED-IN: 53.1）
- 3 unit tests PASS

### D.2 Router 是否真用？

❌ **NO**。從 router.py 直接證據：
```python
async def _stream_loop_events(loop, session_id, registry, *, user_input):
    async for event in loop.run(session_id=session_id, user_input=user_input):
        # ... inline await，完全不經 worker queue
```

checklist 2.6 明文紀錄 decision：「router 不主動呼叫 worker handler — 會引入 in-process queue bridge 複雜度；保留 direct iteration；helpers 作為 53.1 forward-compat」。

### D.3 W2-2 carryover 4 項狀態

| 項目 | W3-0 audit | 50.2 是否動 |
|------|-----------|-----------|
| MockQueueBackend 仍 only backend | ❌ | ❌ 未動 |
| Celery 仍在 requirements | ❌ | ❌ 未動 |
| temporalio 缺席 | ❌ | ❌ 未動 |
| AgentLoopWorker rename | ❌ | ❌ 未動 |

**評估**：50.2 plan **未承諾**修這些，因此非「scope 違規」；但 V2 第一條 backbone 跑在 inline await **完全 bypass worker queue** — 系統架構上的缺口，預期 Phase 53.1（State Mgmt + worker fork）解決。

**Phase D 結論**：🟡 工廠存在但無人用（forward-compat），不算 Potemkin（明確 DEPRECATED-IN tag）；W2-2 carryover 全延後到 53.1。

---

## Phase E — Pytest + Quality Gates

### E.1 50.2 chat tests 跑況

```
tests/integration/api/ + tests/unit/api/v1/chat/  →  46 PASSED, 0 FAILED, 0 SKIPPED, 0.49s
```

3 integration（test_chat_e2e.py）：
- e2e_echo_demo_full_loop_event_sequence — 真驗 8-event 順序
- e2e_session_id_in_response_header — X-Session-Id flips to "completed"
- e2e_cancellation_marks_session_cancelled — POST cancel → 204 / status reflects

43 unit：handler 5 / router 9 / schemas 7 / session_registry 7 / sse 15

### E.2 5 test 強度抽樣

✅ test_echo_demo_streams_loop_events — 用 FastAPI TestClient 真打 endpoint，assert SSE 字節序列
✅ test_e2e_echo_demo_full_loop_event_sequence — 完整 8-event ordering + result_content + total_turns
✅ test_real_llm_without_env_returns_503 — handler 真試 build AzureOpenAIAdapter（env 缺則 raise）
✅ test_thinking_returns_none_skipped_in_day_2 — Day 2 design decision 有測試
✅ test_unsupported_event_raises_with_sprint_pointer — deferred events 真 raise

❌ **0 個 multi-tenant test**（test_chat_e2e 第 8 行明文 skip tenant middleware）
❌ **0 個 trace_id propagation test**

### E.3 Quality gates

✅ 259 全 PASS（210 from 50.1 + ~46 new + 3 modified）
✅ mypy strict 通過（136 source files）
✅ 5 V2 lints OK（LLM SDK leak / AP-1 / cross-cat / dup-dataclass [54 classes] / sync-callback）
✅ frontend lint 0 warnings + build 47 modules / 524ms

**Phase E 結論**：🟢 全綠 / TestClient 真打 endpoint 非 trivial 模擬；缺多租戶 + observability test。

---

## Phase F — 跨範疇集成

### F.1 50.2 ↔ 50.1 集成

✅ handler.py import `from agent_harness.orchestrator_loop import AgentLoopImpl`
✅ 注入 ChatClient (W2-1) + ToolExecutor + ToolRegistry + OutputParser
✅ ToolCallExecuted 擴 `result_content` field — 50.1 dataclass 反向兼容

### F.2 LoopEvent 從 Loop → SSE → frontend 流轉

```
[backend]
  AgentLoopImpl.run()
    yield LoopStarted / TurnStarted / LLMRequested / LLMResponded /
          ToolCallRequested / ToolCallExecuted / LoopCompleted
        ↓ (router._stream_loop_events 直接 async for)
    serialize_loop_event(event)  →  {type, data} | None
    format_sse_message()  →  bytes
        ↓ StreamingResponse(text/event-stream)

[frontend]
  fetch + ReadableStream.getReader()
    parseSSEFrame  →  KNOWN_LOOP_EVENT_TYPES gate
        ↓ chatStore.mergeEvent (7-case switch)
        ↓ Zustand re-render
    MessageList / ToolCallCard / 自動 scroll
```

✅ 每 turn 即時 flush（generator 模式 + StreamingResponse）— UX 良好
✅ 範疇 1 (Loop) → 範疇 6 (Output Parser) → API → frontend 完整鏈路 — V2 第一條 backbone 主流量打通

**Phase F 結論**：🟢 端到端集成清晰；範疇成熟度 Cat 1 → Level 3、Cat 6 → Level 4 自評可信。

---

## 結論評分

| 維度 | 評分 |
|------|------|
| Plan 紀律執行 | 🟢 10/10 |
| 17.md Contract 對齊（LoopEvent / SSE shape）| 🟢 10/10 |
| 主流量打通（Cat 1 → frontend）| 🟢 10/10 |
| 多租戶（multi-tenant-data.md 規則 1-3）| 🔴 0/10（完全 missing） |
| 觀測性（observability-instrumentation.md TraceContext）| 🔴 0/10（完全 missing） |
| Worker queue（W2-2 carryover）| 🟡 4/10（factory 寫了，無人用） |
| Test 真實性 | 🟢 9/10（缺 tenant test）|
| Frontend 真整合 | 🟢 10/10 |
| Retro 誠實度 | 🟢 10/10 |

**綜合**：🟡 **PASS WITH SIGNIFICANT CAVEATS**（Sprint goal 100% / V2 跨切面紀律有 2 個 critical gap）

---

## 不正常開發 / 偏離 findings

### Finding 1（CRITICAL）：Multi-tenant 鐵律 #1+#2+#3 全違反
- 違反 .claude/rules/multi-tenant-data.md §核心鐵律 3 條
- 三個 chat endpoints 全部沒有 `tenant_id` filter / Depends
- SessionRegistry in-memory dict 跨 tenant 共享 session_id 空間
- integration test **明文 skip** tenant middleware（test_chat_e2e.py L8）
- **未在 retro / plan / checklist 中聲明此 scope omission**（plan §4.1 反而承諾用 TenantContextMiddleware）

### Finding 2（CRITICAL）：TraceContext 注入承諾未兌現
- plan §4.1 明文：「endpoint 創建 TraceContext.create_root() 傳入 AgentLoopImpl.run()」
- 實作：router 完全沒有 TraceContext / tracer / 任何 OTel 引用
- 違反 .claude/rules/observability-instrumentation.md §埋點 5 處 + §TraceContext 沿鏈傳遞
- SSE event 不帶 trace_id（即使 frontend 收到也無法關聯後端日誌）
- **這是 undisclosed scope cut**（plan 承諾，實作沒做，retro 沒聲明）

### Finding 3（中度）：Worker queue 主流量繞過
- `build_agent_loop_handler` 工廠寫了 + 3 個 test PASS，但**沒有任何呼叫者**
- 50.2 主流量是 `inline await loop.run()`（router → loop 同 process）
- W2-2 audit 已知 MockQueueBackend 仍 only backend / temporalio 不在 / Celery 沒清
- 這是 retro 明列的 53.1 carryover，**不算違規但屬「forward-compat code without consumer」**（接近 AP-2 邊緣）

### Finding 4（輕度）：Plan §4.1 4 個新 LoopEvent → 實作 3 個
- plan 寫加 4 個（TurnStarted / LLMRequested / LLMResponded / ToolCallCompleted）
- 實作加 3 個 + 擴 ToolCallExecuted 加 result_content（避免與 ToolCallExecuted/Failed 重疊）
- ✅ checklist 2.1 明列 decision、17.md 同步擴條目 — **合理替代且透明**

---

## 阻塞 Phase 52+ 評估

| Phase | 阻塞？ | 原因 |
|-------|-------|------|
| Phase 51.1 (Tools) | ❌ 不阻塞 | echo_executor 已是 ABC，51.1 加新工具自然繼承 |
| Phase 51.2 (Memory) | ❌ 不阻塞 | Memory ABC 在 17.md，與 SSE 解耦 |
| Phase 52.1 (Context Mgmt) | ❌ 不阻塞 | 但若加 trace_context 此時補上更便宜 |
| Phase 53.1 (State Mgmt) | 🟡 **強烈建議先補 multi-tenant** | 53.1 引入 worker fork，沒 tenant_id 會更難加 |
| Phase 53.2 (Error Handling) | 🟡 **強烈建議先補 trace_context** | retry / circuit-breaker 沒 trace 無法 debug |
| Phase 53.3+ (Guardrails / HITL) | ⚠️ **必須先補 multi-tenant** | HITL 必須 per-tenant 隔離否則授權混亂 |
| SaaS Stage 1 (Phase 56-58) | 🔴 **強制阻塞** | 多租戶 + observability 是 SaaS 基本盤 |

---

## 修補建議（優先級）

### P0（Phase 53.1 之前必修）— Multi-tenant 三 endpoints
1. router.py 三 endpoints 加 `current_tenant: UUID = Depends(get_current_tenant)`
2. SessionRegistry key 改 `(tenant_id, session_id)`
3. integration test 加 2 個 cross-tenant denial test（依 multi-tenant-data.md 範本）

### P0（Phase 53.2 之前必修）— TraceContext 沿鏈
1. router 在 _stream_loop_events 入口建 `trace_context = TraceContext.create_root(tenant_id=..., session_id=...)`
2. 傳給 `loop.run(trace_context=...)`（範疇 1 簽名擴 — 屬 50.1 latent）
3. SSE frame 加 `trace_id` 到第一個 loop_start data

### P1（Phase 53.1 解決）— Worker queue 真用 build_agent_loop_handler
- 53.1 引入 Temporal/SQS 時，router 改成 dispatch task → worker（current `inline await` 廢除）
- 50.2 已準備好的 factory 屆時 plug-in

### P2（Phase 51.x backlog）— vitest 安裝 + frontend test 補回
- 紀錄為 CARRY-010

---

## 與 W3-0 / W3-1 audit 對照

- **W3-0 carryover**：W2-2 P1 #4-7（worker dir / Celery / temporalio / AgentLoopWorker rename）50.2 仍 ❌
- **W3-1 (50.1 Cat 1)**：50.2 真實消費 50.1 AgentLoopImpl + LoopEvent — Cat 1 從 Level 2 → Level 3 自評可信
- **W3-3 總結預覽**：50.2 是 V2 第一個整合 sprint，本身執行紀律高分；但暴露兩個 cross-cutting 紀律斷層需 Phase 53.1-53.2 強制收回

---

**Audit version**：W3-2 v1.0（2026-04-29）
**Status**：🟡 PASS WITH SIGNIFICANT CAVEATS
**Next action**：W3-3 總結 / Phase 53.1 plan 必須含 multi-tenant 三 endpoints 修補項
