# Sprint 52.5 — Audit Carryover Cleanup (P0×8 + P1×4)

**Phase**: phase-52-5-audit-carryover
**Sprint**: 52.5
**Duration**: 10-14 days (Day 0-11 standard layout, compressible to Day 0-7 if dependencies parallelize cleanly)
**Status**: TODO → IN PROGRESS → DONE
**Created**: 2026-05-01
**Owner**: User-spawned cleanup session 2026-05-01+
**Branch**: feature/sprint-52-5-audit-carryover (off main `989e064d`)

---

## Sprint Goal

清除 V2 Verification Audit W1+W2+W3+mini-W4-pre 累積的 **8 P0 critical** + **4 P1 high-priority** carryover，**在 Phase 53.1 啟動前**讓 V2 multi-tenant + observability + audit-chain + auth + sandbox isolation + memory tools tenant-injection 六條鐵律全部落地，避免 worker fork 後修補成本翻倍。

---

## Background

V2 Verification Audit（2026-04-29 ~ 2026-05-01 evening）發現累積 8 個 P0 critical：

**Week 3 累積（4 P0）**：
- W1+W2 P1 8 項中 7 項在 Sprint 49.4 ~ 51.2（5 sprint）完全 dropped（0% 進入 sprint planning）
- W3-2 揭露 Phase 50.2 chat router 同時違反 multi-tenant + observability 兩條鐵律
- W3-2 揭露 sprint plan 隱形砍 scope（TraceContext 承諾未實作 + retrospective 未交代）

**mini-W4-pre 新增（4 P0）— 系統性 AP-4 Potemkin pattern**：
- W4P-1：49.4 OTel ABC + Tracer 類別 + 7 個必埋 metrics 完成 ✅，但 Adapter 0 個 `tracer.start_span` / API entry 0 個 `TraceContext.create_root()`
- W4P-3：51.1 SubprocessSandbox 在 Windows 上**裝飾性**，agent 實測 `os.listdir("C:/")` 從「sandbox」內成功列出 host fs（RCE vector）
- W4P-4：51.2 memory_tools handler tenant_id 從 `ToolCall.arguments` 取（W3-2 鏡像漏洞），允許 LLM caller 控制 tenant_id

**根因**：(1) audit findings 缺乏 ticket 機制（已修：GitHub issues #11-18）;（2) sprint plan template 缺 carryover section（已修）;（3) **跨 sprint 主流量整合驗收**這個維度根本沒有 sprint 負責。本 sprint 同時清債 + 落地 process 修補。

詳見：
- `claudedocs/5-status/v2-audit-2026-04/V2-AUDIT-OPEN-ISSUES-20260501.md` — 真相 index
- `claudedocs/5-status/v2-audit-2026-04/V2-AUDIT-WEEK3-SUMMARY.md` — W1+W2+W3 雙層問題決策報告
- `claudedocs/5-status/v2-audit-2026-04/V2-AUDIT-MINI-W4-PRE-SUMMARY.md` — 系統性 AP-4 pattern + 8 P0 + Process fix #6 proposal

---

## User Stories

### US-1：作為平台維護者，我希望 chat router 強制執行多租戶隔離，以便符合 V2 server-side first 鐵律
- **驗收**：`backend/src/api/v1/chat/*.py` 全部 endpoint 使用 `Depends(get_current_tenant)`；`SessionRegistry` 改 tenant-scoped；integration test 不再 skip tenant middleware
- **影響檔案**：`backend/src/api/v1/chat/router.py` / `handler.py` / `session_registry.py` / `sse.py`；test_chat_e2e.py
- **GitHub Issue**：#11 (P0)

### US-2：作為觀測性負責人，我希望 chat handler 落地 TraceContext propagation 並補齊 5 處必埋 span，以便 distributed tracing 全鏈路可串連
- **驗收**：chat endpoint 創建 `TraceContext.create_root()` 沿鏈傳；adapter / state checkpoint / verification / tools / loop 5 處 `tracer.start_span`；SSE event 含 `trace_id`；Jaeger UI 看到完整 hierarchy
- **影響檔案**：`backend/src/api/v1/chat/handler.py`；`backend/src/adapters/azure_openai/adapter.py`；`backend/src/agent_harness/state_mgmt/`；`backend/src/agent_harness/orchestrator_loop/`；`backend/src/agent_harness/tools/executor.py`；`backend/src/agent_harness/observability/tracer.py`
- **GitHub Issues**：#12 (P0), #16 (P0)；#16 supersedes #12 in scope

### US-3：作為合規負責人，我希望 audit_log hash chain 有 daily verifier，以便 governance/HITL 可仰賴 audit log 為「不可否認證據」
- **驗收**：`backend/scripts/verify_audit_chain.py` 存在 + CLI 可獨立執行；daily cron / scheduled job 整合；偵測篡改時 alert；針對 known-test forgery tenant `aaaa...4444` 加 `--ignore-tenant` flag
- **影響檔案**：新建 `backend/scripts/verify_audit_chain.py`；`docker-compose.dev.yml` 加 cron service；`docs/03-implementation/agent-harness-planning/13-deployment-and-devops.md` 加 verifier 章節
- **GitHub Issue**：#13 (P0)

### US-4：作為 identity 負責人，我希望 JWT 取代 X-Tenant-Id header，以便消除 trivial tenant spoofing 漏洞
- **驗收**：tenant_id 從 JWT decode 取得；middleware 不再讀 `X-Tenant-Id` header（過渡期可加 deprecation warning，最後移除）
- **影響檔案**：`backend/src/platform_layer/middleware/tenant_context.py`；JWT 模組（如尚未存在則新建 `backend/src/platform_layer/identity/jwt.py`）
- **GitHub Issue**：#14 (P0)

### US-5：作為觀測性 owner，我希望 OTel SDK 版本鎖定，以便符合 observability-instrumentation.md 規則並避免 breaking change
- **驗收**：`requirements.txt` `opentelemetry-api==1.22.0`（嚴格相等）；其他 OTel 相關套件對齐版本
- **影響檔案**：`backend/requirements.txt`
- **GitHub Issue**：#15 (P0)，30 min effort

### US-6：作為平台安全負責人，我希望 SubprocessSandbox 在 Windows 上真實隔離（Docker container-based），以便 python_sandbox tool 在 production 不成為 RCE vector
- **驗收**：sandbox 重寫為基於 Docker container；`os.listdir("C:/")` 從 sandbox 內失敗；POSIX `resource.setrlimit` 與 Windows Docker `--memory --cpus` 行為等價；`network_blocked=True` 真實生效（不是 doc-only）
- **影響檔案**：`backend/src/agent_harness/tools/sandbox.py`（重寫）；`docker/sandbox/Dockerfile`（新建）；相關測試
- **GitHub Issue**：#17 (P0, CARRY-022 升級)，3-5 days

### US-7：作為 memory layer owner，我希望 memory_tools handler 從 ExecutionContext 注入 tenant_id（不從 LLM 控制的 ToolCall.arguments 取），以便消除 W3-2 鏡像漏洞
- **驗收**：memory_search / memory_write / memory_delete 等所有 memory tools handler 簽名改為接受 `ExecutionContext` 參數；tenant_id 從 context 取；ToolCall.arguments 中的 `tenant_id` field 被 ignore（或 raise on mismatch）
- **影響檔案**：`backend/src/agent_harness/memory/tools.py`（或同等位置）；ToolExecutor 注入 ExecutionContext
- **GitHub Issue**：#18 (P0, CARRY-030)，1 day

### US-8：作為 codebase 維護者，我希望累積的 4 P1 hygiene 項一次清完，以便 codebase metadata 與實際決策一致
- **驗收**：見「Technical Specs §P1」
- **影響檔案**：見「File Change List §P1」
- **追蹤**：W2-1 #4 / W2-2 #6 / W2-2 #7 / W2-2 #8

---

## Technical Specifications

### P0 #11 — chat router multi-tenant 隔離

**現況**（W3-2 verified, audit grep counts）：
- `backend/src/api/v1/chat/router.py` 0 個 `Depends(get_current_tenant)` / 0 個 `tenant_id` filter
- `SessionRegistry` 是 process-wide dict（跨 tenant 共享）
- `test_chat_e2e.py:8` 明文 skip tenant middleware
- `backend/src/api/`：`tenant_id` 1 hit（main.py），chat router **0**

**設計**：
1. 三個 chat endpoint（`POST /chat`, `POST /chat/{session_id}/cancel`, `GET /chat/{session_id}/events`）全部加 `current_tenant: UUID = Depends(get_current_tenant)`
2. `SessionRegistry` 改為 `dict[UUID, dict[UUID, ChatSession]]`（外層 key = tenant_id，內層 key = session_id），所有 register/lookup/delete 都帶 tenant_id 參數
3. 非該 tenant 的 session_id 直接 raise 404（不洩漏「session 存在但跨 tenant」訊息）
4. `test_chat_e2e.py` 移除 skip + 加 multi-tenant 測試（tenant A 看不到 tenant B 的 session）

**驗證**：
- `pytest -m multi_tenant`（如有此 marker）全綠 with **real PostgreSQL**（不是 SQLite，per AP-10 教訓）
- 手動：tenant A 發 POST /chat → 拿到 session_id → 用 tenant B token 試 GET /chat/{session_id}/events → 預期 404
- Grep `Depends(get_current_tenant)` in `backend/src/api/v1/chat/` → ≥ 3（每個 endpoint 一個）

**Effort**: 1-2 days（合併 P0 #12 共做）

### P0 #12 + P0 #16 — TraceContext propagation + 5-place tracer.start_span

**現況**（W3-2 + W4P-1 verified）：
- `backend/src/api/` grep `TraceContext|tracer` = 0 hit
- 50.2 plan §4.1 明文承諾未落地
- adapter 8 hits `trace_context` 變數，**0** hits `tracer.start_span`

**設計**（per `observability-instrumentation.md` 5 處必埋點）：
1. **API entry**：`chat_handler` 開始時 `trace_ctx = TraceContext.create_root(tenant_id=current_tenant, user_id=current_user, session_id=...)`
2. **Adapter LLM call**：`AzureOpenAIAdapter.chat()` 內 `with tracer.start_span("llm_chat", parent=trace_context.span_id)`
3. **State checkpoint**：`Checkpointer.save()` 內 `with tracer.start_span("state_checkpoint_save", ...)`
4. **Tool execution**：`ToolExecutor.execute()` 內 `with tracer.start_span(f"tool_{tool_name}", ...)`
5. **Loop turn**：`AgentLoop.run()` 每 turn 開頭 + 結尾 `with tracer.start_span(f"loop_turn_{n}", ...)`

加上：
6. SSE event payload 加 `trace_id` field（per 17.md §4.1 spec）
7. `chat_handler` 把 `trace_ctx` 傳給 `AgentLoopImpl.run(trace_context=trace_ctx)`
8. Loop 內遞迴傳 trace_context 給 child operations

**驗證**：
- Unit test：mock loop.run，斷言 trace_context 被傳入
- Integration test：發 POST /chat → SSE stream 第一個 event 含 `trace_id`
- 端到端：跑一個 chat → 在 Jaeger UI 看到 root span + 5 child spans 串連
- Grep counts：`backend/src/`：`tracer.start_span` ≥ 5；`TraceContext.create_root` ≥ 1

**Effort**: 2-3 days（5 places）

### P0 #13 — verify_audit_chain.py + cron + alert

**現況**（W1-3 verified）：
- audit_log table 設計完整（SHA-256 / per-tenant chain / prev_hash 在 input / append-only triggers）
- 但無 verify 程式 — audit session 實測：用 superuser INSERT 假 hash row（id=39, curr_hash="f"*64）成功進庫，0 偵測
- 已知 fake row：tenant `aaaa-aaaa-aaaa-aaaa-aaaa-aaaa-aaaa-4444` 中 id 36-39

**設計**：
1. `backend/scripts/verify_audit_chain.py`（asyncpg + hashlib，無 Django/FastAPI 依賴）：
   - 連接 DB（per `.env`）
   - 對每個 tenant：
     - 取所有 audit_log row 按 `created_at` ASC
     - 從 genesis（`prev_hash="0"*64`）開始重算每筆 `curr_hash = SHA256(prev_hash || canonical_json(payload) || tenant_id || ts_ms)`
     - 比對 stored vs computed
     - 比對 `prev_hash == previous_row.curr_hash`
   - 任一不符 → exit 1 + 輸出篡改起點 row id
   - 全 OK → exit 0 + 輸出 `Verified N rows across M tenants`
2. CLI argument：
   - `--tenant <uuid>`（單一 tenant 加速）
   - `--from-date <YYYY-MM-DD>`（部分驗證）
   - `--alert-webhook <url>`（失敗時 POST）
   - `--ignore-tenant <uuid>`（per task instructions：跳過 known-test forgery `aaaa...4444`）
3. `docker-compose.dev.yml` 加 `audit-verifier` service：
   - cron-style（建議 ofelia / supercronic image）
   - 每日 02:00 跑一次（low-traffic time）
   - 失敗時 webhook → Slack/Teams（dev：log 到 stdout 即可）
4. 文件：`docs/03-implementation/agent-harness-planning/13-deployment-and-devops.md` 加 §Audit Verification 章節

**驗證**：
- 跑現有 audit_log（含 W1-3 留下的 fake row id=39）→ 預期 exit 1，明確指出 id=39 為篡改起點
- 加 `--ignore-tenant aaaa...4444` 後再跑 → 預期 exit 0
- Cron 整合：手動 trigger cron job 確認 service 可用

**Effort**: 2-3 days（含 cron 整合）

### P0 #14 — JWT 取代 X-Tenant-Id header

**現況**（W1-2 verified）：
- `tenant_context.py` 從 `X-Tenant-Id` header 讀 tenant_id（trivially spoofable）
- W1+W2 SUMMARY 自承「49.5+ deadline」但 5 sprint 後仍未修

**設計**：
1. JWT 模組（如尚未有）：
   - `backend/src/platform_layer/identity/jwt.py`：產生 + 驗證 JWT
   - Payload schema: `{sub: user_id, tenant_id: UUID, roles: [str], iat, exp}`
   - 簽章：HS256（dev）或 RS256（prod）— config-driven
2. `TenantContextMiddleware`：
   - 從 `Authorization: Bearer <jwt>` header 解析
   - Verify signature + expiration
   - Extract tenant_id → `request.state.tenant_id`
   - 無 token / 過期 / 簽章不符 → 401
3. 過渡期（optional）：保留 `X-Tenant-Id` 作 fallback + deprecation log warning（一週後移除；本 sprint **直接移除**，per audit P0 緊急度）
4. `get_current_tenant` dependency：從 `request.state.tenant_id` 讀（API 介面不變）

**驗證**：
- Unit test：JWT 產生 + verify round-trip
- Integration test：
  - 無 Authorization header → 401
  - 過期 token → 401
  - 簽章不符 → 401
  - 有效 token → 200 + 正確 tenant_id 注入
- 攻擊測試：嘗試假造 `X-Tenant-Id: <other-tenant>` → 應被忽略（fallback 已移除）

**Effort**: 1-2 days

### P0 #15 — OTel SDK version lock to ==1.22.0

**現況**（W4P-1 verified）：
- `requirements.txt` `opentelemetry-api>=1.27,<2.0`（floating range）
- `observability-instrumentation.md` 規範：`opentelemetry-api==1.22.0`（嚴格相等）

**設計**：
1. 修改 `backend/requirements.txt`：
   - `opentelemetry-api==1.22.0`
   - `opentelemetry-sdk==1.22.0`
   - `opentelemetry-exporter-jaeger==1.22.0`
   - `opentelemetry-exporter-prometheus==0.43b0`
   - `opentelemetry-exporter-otlp==1.22.0`
   - `opentelemetry-instrumentation-fastapi==0.43b0`
   - `opentelemetry-instrumentation-sqlalchemy==0.43b0`
   - `opentelemetry-instrumentation-redis==0.43b0`
2. `pip install -r requirements.txt` 確認無衝突

**驗證**：
- `pip show opentelemetry-api` 顯示 1.22.0
- 既有 OTel 測試全綠

**Effort**: 30 min

### P0 #17 — SubprocessSandbox Windows Docker isolation

**現況**（W4P-3 verified, agent 實測證據）：
- 從「sandbox」內成功 `os.listdir("C:/")` 列出 host fs（Windows）
- `network_blocked` 參數是 `# noqa: ARG002 — doc-only knob`（裝飾性 flag）
- POSIX 用 `resource.setrlimit()`，Windows skip（無對應 API）
- python_sandbox tool 在 production Windows 部署 = **RCE vector**

**設計**：
1. **重寫 `backend/src/agent_harness/tools/sandbox.py`** 為基於 Docker container：
   - 不再依賴 `subprocess` + `resource.setrlimit`
   - 創建 short-lived Docker container per execution
   - `--memory <limit>` / `--cpus <limit>` / `--network none`（or `bridge` per `network_blocked`）/ `--read-only` / `--cap-drop=ALL`
   - 用 docker SDK（python-docker package）程式化管理
2. **建 sandbox Docker image**（`docker/sandbox/Dockerfile`）：
   - python:3.11-slim base
   - 預裝必要 lib（json / requests if `network_blocked=False`）
   - non-root user
3. **Cross-platform**：
   - Windows + Mac + Linux 透過 Docker daemon 統一行為
   - `network_blocked=True` 真實生效（`--network none`）
4. **時限與資源**：
   - timeout 透過 container kill
   - memory_limit_mb / cpu_limit 直接傳給 Docker

**驗證**：
- 從 sandbox 內 `os.listdir("/")` 只看到 container 內 fs，**不**洩漏 host
- `network_blocked=True` 時 `socket.connect("8.8.8.8", 80)` 失敗
- 既有 51.1 sandbox tests 全綠（Windows + Linux 均跑）
- Performance：execution overhead < 500ms (Docker startup) — 可接受

**Effort**: 3-5 days（重寫 + Docker image + 跨平台 tests）

### P0 #18 — memory_tools handler tenant from ExecutionContext

**現況**（W4P-4 verified）：
- chat router 0 hit memory_search/memory_write tools — memory tools 寫了沒人用
- 即使將來主流量呼叫，handler 從 `ToolCall.arguments.tenant_id` 取，允許 LLM caller 控制 tenant_id（W3-2 鏡像漏洞）

**設計**：
1. **改 ToolExecutor**：注入 `ExecutionContext` 給 handler
   ```python
   class ExecutionContext:
       tenant_id: UUID
       user_id: UUID
       session_id: UUID
       trace_context: TraceContext

   async def execute(self, tool_call: ToolCall, context: ExecutionContext):
       handler = self.registry.get(tool_call.tool_name)
       return await handler(arguments=tool_call.arguments, context=context)
   ```
2. **改 memory_tools handler 簽名**：
   ```python
   # ❌ 之前
   async def memory_search(arguments: dict) -> dict:
       tenant_id = UUID(arguments["tenant_id"])  # ← LLM 可控

   # ✅ 之後
   async def memory_search(arguments: dict, context: ExecutionContext) -> dict:
       tenant_id = context.tenant_id  # ← server-side authoritative
       # arguments["tenant_id"] 若存在則 raise（不 silent ignore）
   ```
3. 同樣模式應用到所有 memory tools（search / write / delete / list）

**驗證**：
- Unit test：mock ToolExecutor，斷言 handler 收到 ExecutionContext
- 攻擊 test：LLM 假造 ToolCall.arguments.tenant_id = 別 tenant → handler raise + audit log
- Grep：`def memory_*\(arguments` in memory tools = 0（必有 context 參數）

**Effort**: 1 day

---

### P1（hygiene）

#### P1 #4：寫 `adapters/azure_openai/tests/test_integration.py`
- Source: W2-1
- 設計：mark `@pytest.mark.integration`，預設 skip；env var `RUN_AZURE_INTEGRATION=1` 啟用；真打 Azure API 跑 1 個 round-trip + 1 個 streaming + 1 個 tool call
- Effort: 1 day

#### P1 #6：requirements.txt 清 Celery / 加 temporalio TODO
- Source: W2-2
- 設計：刪 `celery>=5.4,<6.0`；加 `# temporalio: planned for Phase 53.1 (TemporalQueueBackend)` comment
- Effort: 30 min

#### P1 #7：統一 worker 目錄
- Source: W2-2
- 設計：合併 `runtime/workers/` → `platform_layer/workers/`（V2 規劃位置）；更新所有 import；保留 `runtime/workers/__init__.py` 作 deprecation shim 一週
- Effort: half day

#### P1 #8：AgentLoopWorker rename / docstring 警告
- Source: W2-2
- 設計：在 class docstring + module docstring 加 prominent `[STUB] Phase 49.4-53.1 — production worker requires TemporalQueueBackend (Phase 53.1)` 警告
- Effort: 1 hour

---

## File Change List

### P0 #11 + P0 #12 + P0 #16（合併修改 chat handler + observability 5 places）
- ✏️ `backend/src/api/v1/chat/router.py` — 加 Depends(get_current_tenant)
- ✏️ `backend/src/api/v1/chat/handler.py` — 接受 tenant + TraceContext.create_root(); propagate
- ✏️ `backend/src/api/v1/chat/session_registry.py` — tenant-scoped storage
- ✏️ `backend/src/api/v1/chat/sse.py` — SSE event 含 trace_id
- ✏️ `backend/src/adapters/azure_openai/adapter.py` — tracer.start_span("llm_chat")
- ✏️ `backend/src/agent_harness/state_mgmt/checkpointer.py` — tracer.start_span("state_checkpoint_save")
- ✏️ `backend/src/agent_harness/orchestrator_loop/loop.py` — tracer.start_span(f"loop_turn_{n}")
- ✏️ `backend/src/agent_harness/tools/executor.py` — tracer.start_span(f"tool_{name}")
- ✏️ `backend/tests/integration/api/test_chat_e2e.py` — 移除 skip，加 multi-tenant test
- ➕ `backend/tests/integration/api/test_chat_multi_tenant.py` — 跨 tenant 隔離測試
- ➕ `backend/tests/integration/observability/test_trace_propagation.py` — 5-place span coverage 驗收

### P0 #13
- ➕ `backend/scripts/verify_audit_chain.py`（核心邏輯）
- ➕ `backend/scripts/__init__.py`（如尚未存在）
- ➕ `backend/tests/unit/scripts/test_verify_audit_chain.py`
- ✏️ `docker-compose.dev.yml` — 加 audit-verifier service
- ➕ `docker/audit-verifier/Dockerfile`（如需自訂 image）
- ✏️ `docs/03-implementation/agent-harness-planning/13-deployment-and-devops.md` — 加 §Audit Verification

### P0 #14
- ➕ `backend/src/platform_layer/identity/jwt.py`（如未存在）
- ✏️ `backend/src/platform_layer/middleware/tenant_context.py` — 改 JWT decode
- ✏️ `backend/.env.example` — 加 `JWT_SECRET` / `JWT_ALGORITHM` / `JWT_EXPIRATION_MIN`
- ✏️ `backend/src/core/config.py` — pydantic Settings 加 JWT 欄位
- ➕ `backend/tests/integration/api/test_jwt_auth.py`
- ✏️ `backend/requirements.txt` — 加 `python-jose[cryptography]` 或 `pyjwt[crypto]`

### P0 #15
- ✏️ `backend/requirements.txt` — OTel 8 個 package 嚴格鎖定 1.22.0/0.43b0

### P0 #17
- 🔁 `backend/src/agent_harness/tools/sandbox.py` — 重寫為 Docker-based
- ➕ `docker/sandbox/Dockerfile`
- ✏️ `backend/requirements.txt` — 加 `docker>=7.0,<8.0`
- ➕ `backend/tests/integration/tools/test_sandbox_isolation.py` — Windows + Linux RCE prevention test
- ✏️ `backend/src/agent_harness/tools/python_sandbox_tool.py`（若有）— 用新 sandbox

### P0 #18
- ➕ `backend/src/agent_harness/tools/execution_context.py` — ExecutionContext dataclass
- ✏️ `backend/src/agent_harness/tools/executor.py` — 注入 ExecutionContext
- ✏️ `backend/src/agent_harness/memory/tools.py`（或同等位置）— handler 簽名改
- ➕ `backend/tests/unit/memory/test_memory_tools_tenant_injection.py`

### P1
- ✏️ `backend/requirements.txt` — 刪 Celery + 加 temporalio comment
- 🔁 `backend/src/runtime/workers/` → `backend/src/platform_layer/workers/` (move with `git mv`)
- ➕ `backend/src/adapters/azure_openai/tests/test_integration.py`
- ✏️ `backend/src/runtime/workers/agent_loop_worker.py` (or new path) — docstring 警告

---

## Acceptance Criteria

### Sprint-level（必過）
- [ ] 8 P0 全部 ✅（驗證見各 P0 「驗證」section）
- [ ] 4 P1 全部 ✅
- [ ] All tests pass: `python -m pytest --cov=src --cov-report=term-missing`（**不是 bare `pytest`** — per testing.md）
- [ ] Coverage 不低於 sprint 啟動前 baseline
- [ ] mypy strict pass
- [ ] CI green on PR
- [ ] 8 GitHub issues #11-18 全部 close（每 P0 完成立即 close，不堆到最後）

### 跨切面紀律（per W3-2 + mini-W4-pre 教訓）
- [ ] **Multi-tenant**：grep `Depends(get_current_tenant)` in `backend/src/api/v1/chat/` ≥ 3
- [ ] **TraceContext propagation**：grep `tracer.start_span` in `backend/src/adapters/` ≥ 1; `backend/src/agent_harness/` ≥ 4
- [ ] **LLM Neutrality**：`grep -r "from openai\|from anthropic\|import openai\|import anthropic" backend/src/agent_harness/ backend/src/business_domain/` 必須 0 hit
- [ ] **AP-10 Mock vs Real**：multi-tenant tests 跑 **real PostgreSQL**（`ipa_v2_postgres` healthy container）；test runtime ≥ 2s（不是 0.36s 全 mock）
- [ ] Sprint scope 任何砍 / 延後在 retrospective 透明列出（**no undisclosed cut**，不重蹈 50.2 plan TraceContext 隱形砍範圍）

### 主流量整合驗收（per mini-W4-pre Process Fix #6 proposal）
- [ ] 本 sprint 交付的元件，主流量是否真的調用？grep 證據
- [ ] 還是只有 ABC + unit test 完成？
- [ ] 若僅後者，整合的 owner sprint 是哪一個？已開 ticket？

---

## Deliverables（見 checklist 詳細）

| Day | 工作 |
|-----|------|
| 0 | Setup: branch + plan + checklist + GitHub issues 確認 |
| 1 | Quick wins: P0 #15 OTel SDK lock + P0 #14 JWT 起手 |
| 2-3 | P0 #11 + P0 #12 + P0 #16 合併（chat handler 多租戶 + 5-place span）|
| 4-5 | P0 #13 verify_audit_chain.py + cron + alert |
| 6 | P0 #14 JWT 完成 + P0 #17 sandbox 起手 |
| 7-8 | P0 #17 sandbox Docker isolation 完成 |
| 9 | P0 #18 memory_tools tenant injection |
| 10 | 4 P1 hygiene 一次清完 |
| 11 | Retrospective + W4 trigger + PR |

可彈性壓縮成 7-8 days（如 P0 #17 提早 + P1 並行）。

---

## Dependencies & Risks

### 依賴
- `ipa_v2_postgres` Docker container running（已有，healthy 多日）
- `_contracts/TraceContext` dataclass（49.4 Day 3 OTel 已建，per W4P-1 確認）
- `Depends(get_current_tenant)` infrastructure（49.3 Day 4.4 已建，但 chat router 沒接）
- JWT 函式庫 `python-jose[cryptography]` 或 `pyjwt[crypto]`（需加進 requirements.txt）
- Docker daemon（for P0 #17 sandbox 重寫）

### 風險

| Risk | Mitigation |
|------|------------|
| **Graphify hook bug**：commit 後自動切 branch | post-checkout / post-commit hook 已停用（cleanup session 期間）；每次 commit 前後 `git branch --show-current` 驗證 |
| JWT migration 影響其他 endpoint（governance / health） | 過渡期保留 X-Tenant-Id fallback 一週（**本 sprint 直接移除以強制更新**） |
| SessionRegistry tenant-scoped 改變影響 frontend chat-v2 | 先讀 chat-v2 source 確認無 hardcoded session lookup；必要時加 frontend 遷移 task |
| verify_audit_chain.py docker cron 整合複雜度 | Day 4-5 預留 buffer；如 cron 整合 > 1 day，cron 推遲到後續 sprint，先交付 standalone CLI |
| Audit session 留下的 fake hash rows（id 36-39 in tenant `aaaa...4444`）影響 verifier 測試 | 該 tenant 是 known-test forgery baseline，verifier 加 `--ignore-tenant <uuid>` flag |
| Sandbox Docker 重寫影響 51.1 既有 tests | 重寫前 baseline test count；重寫後 100% pass；新增 RCE prevention test |
| Memory tools handler 改簽名影響 memory tools registry | 統一 handler signature 為 `(arguments, context)`；registry 統一注入 |
| **「不能砍 scope」紀律**：8 P0 工時超出 plan 範圍時 | retrospective 必答透明列出；不能像 50.2 那樣隱形砍 |

---

## Audit Carryover Section（per W3 process fix #1）

本 sprint **本身就是** W1+W2+W3+mini-W4-pre 的 carryover sprint，無新 audit carryover。

### 後續 audit 預期

W4 audit（Sprint 52.2 + 本 sprint 完成後）：驗證
- 8 P0 是否真清（重做 W1-2 / W1-3 / W3-2 / W4P-1 / W4P-3 / W4P-4 對應檢查）
- 8 GitHub issues 是否 close
- 52.2 PromptBuilder 是否守住跨切面紀律
- **系統性 AP-4 pattern re-check**（per mini-W4-pre §3）：main-flow integration coverage for all categories
- 是否有新的 process drift

---

## §10 Process 修補落地檢核

per W3 process fix #1 + #2 + #3 + #4 + #5 + mini-W4-pre #6：

- [x] Plan template 加 Audit Carryover 段落（本 plan §Audit Carryover Section 即落地）
- [x] Retrospective template 加 Audit Debt 段落（見 checklist Day 11）
- [x] GitHub issue per P0/P1（#11-18 已建立）
- [ ] 每月 Audit Status Review（手動 review）
- [x] Audit re-verify 每 2-3 sprint（W4 已排）
- [ ] **mini-W4-pre Process Fix #6**：Sprint Retrospective「主流量整合驗收」必答題（本 sprint retrospective Day 11 採用）

---

## Retrospective 必答（per W3-2 + mini-W4-pre 教訓）

Sprint 結束時，retrospective 必須回答以下 5 條：

1. **每個 P0 真清了嗎？** 列每個 P0 對應 commit + verification 結果
2. **跨切面紀律守住了嗎？** Multi-tenant / TraceContext / LLM Neutrality grep counts (before/after)
3. **有任何砍 scope 嗎？** 若有，明確列出 + 理由 + 後續排程（不能像 50.2 那樣隱形砍）
4. **GitHub issues 全 close 了嗎？** 列每個 issue url + close 時 commit hash
5. **Audit Debt 有累積嗎？** 本 sprint 期間有沒有發現新的 audit-worthy 問題？列出（不要等 W4 才發現）

加碼（per mini-W4-pre Process Fix #6）：

6. **主流量整合驗收**：本 sprint 交付的元件，**主流量真的調用了嗎？**
   - chat handler 真用 `Depends(get_current_tenant)` 嗎？grep ≥ 3 hits？
   - chat handler 真 emit `TraceContext.create_root()` 嗎？grep ≥ 1 hit？
   - Adapter 真有 `tracer.start_span("llm_chat")` 嗎？grep ≥ 1 hit？
   - memory_tools handler 真用 ExecutionContext 嗎？grep ≥ 1 hit？
   - sandbox 真用 Docker container 嗎？非 fake `# noqa` flag？

---

## Sprint Closeout

- [ ] Day 11 retrospective.md 寫好（含必答 5+1 條）
- [ ] All 8 P0 GitHub issues closed
- [ ] PR 開到 main，title: `feat(audit-carryover, sprint-52-5): Cleanup sprint — 8 P0 + 4 P1 (V2 W1+W2+W3+mini-W4-pre)`
- [ ] PR body 含每 P0 verification 證據 + GitHub issues close URLs
- [ ] 通知 audit session：cleanup sprint 完成，可進 W4
- [ ] Hooks restore：`mv .git/hooks/post-checkout.disabled-by-cleanup-session .git/hooks/post-checkout`（and post-commit）— **僅在 PR merge 後**

---

**權威排序**：`agent-harness-planning/` 18 docs > 本 plan > V1 文件 / 既有代碼。本 plan 對齊 V2-AUDIT-OPEN-ISSUES-20260501.md 真相。
