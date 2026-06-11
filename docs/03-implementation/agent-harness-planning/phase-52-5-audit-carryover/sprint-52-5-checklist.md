# Sprint 52.5 — Audit Carryover Cleanup Checklist

**Plan**: [sprint-52-5-plan.md](./sprint-52-5-plan.md)
**Branch**: `feature/sprint-52-5-audit-carryover` (off main `989e064d`)
**Duration**: 10-14 days (Day 0-11 standard layout)

---

## Day 0 — Setup (est. 2 hours)

### 0.1 Branch + plan + checklist commit
- [x] **Recover from graphify hook unwanted merge** (cleanup session 起手)
  - `git stash push -u` 處理主 session 的 sprint 52.2 work
  - `git reset --hard bf66461d` 恢復 feature 真實 tip
  - DoD: `git log -1 feature/phase-52-sprint-2-cat5-prompt-builder` shows `bf66461d`
- [x] **Disable graphify hooks (post-checkout + post-commit) for cleanup session**
  - `mv .git/hooks/post-checkout .git/hooks/post-checkout.disabled-by-cleanup-session`
  - `mv .git/hooks/post-commit .git/hooks/post-commit.disabled-by-cleanup-session`
  - DoD: `ls .git/hooks/post-*` 顯示 `.disabled-by-cleanup-session` suffix
  - **Restore 時機**：PR merge 後 **才** rename 回原名
- [x] **Create feature branch from main**
  - `git checkout main && git checkout -b feature/sprint-52-5-audit-carryover`
  - DoD: `git branch --show-current` returns `feature/sprint-52-5-audit-carryover`
- [x] **Create phase + execution folders**
  - `mkdir -p docs/03-implementation/agent-harness-planning/phase-52-5-audit-carryover`
  - `mkdir -p docs/03-implementation/agent-harness-execution/phase-52-5/sprint-52-5-audit-carryover`
- [ ] **Commit Day 0 docs (plan + checklist)**
  - Files: this plan + this checklist
  - Commit message: `docs(audit-carryover, sprint-52-5): Day 0 plan + checklist`
  - DoD: `git log -1` shows Day 0 commit; `git branch --show-current` 仍是 cleanup branch（驗 hook 沒 hijack）

### 0.2 GitHub issues 確認
- [ ] **Verify 8 GitHub issues #11-18 exist + open**
  - `gh issue list -l audit-carryover -s open` returns 8 rows
  - DoD: 8 URLs 列入 progress.md

### 0.3 Verification environment ready
- [ ] **Confirm `ipa_v2_postgres` Docker container healthy**
  - `docker ps --filter "name=ipa_v2_postgres" --format "{{.Status}}"` returns "Up X days (healthy)"
  - DoD: 不要 `docker-compose up/down/restart`（per task instructions）
- [ ] **Smoke test pre-existing tests**
  - `python -m pytest backend/tests/unit/api/v1/chat/ -v` (capture baseline counts)
  - DoD: baseline test counts recorded in progress.md

---

## Day 1 — Quick Wins: P0 #15 + start P0 #14 (est. 6 hours)

### 1.1 P0 #15 — OTel SDK version lock (est. 30 min)
- [ ] **Edit `backend/requirements.txt` 8 個 OTel package 嚴格鎖定**
  - `opentelemetry-api==1.22.0`
  - `opentelemetry-sdk==1.22.0`
  - `opentelemetry-exporter-jaeger==1.22.0`
  - `opentelemetry-exporter-otlp==1.22.0`
  - `opentelemetry-exporter-prometheus==0.43b0`
  - `opentelemetry-instrumentation-fastapi==0.43b0`
  - `opentelemetry-instrumentation-sqlalchemy==0.43b0`
  - `opentelemetry-instrumentation-redis==0.43b0`
  - DoD: `grep "opentelemetry" backend/requirements.txt | grep -v "==1.22.0\|==0.43b0"` returns 0
- [ ] **Verify install no conflict**
  - `pip install -r backend/requirements.txt` (in venv if available)
  - DoD: no error / no version conflict warning
- [ ] **Run existing OTel tests**
  - `python -m pytest backend/tests -k "otel or trace" -v`
  - DoD: all green
- [ ] **Commit P0 #15**
  - Message: `chore(observability, sprint-52-5): P0 #15 lock OTel SDK to ==1.22.0`
  - **Verify branch before commit**: `git branch --show-current` = cleanup branch
- [ ] **Close GitHub issue #15**
  - `gh issue close 15 --comment "Resolved by commit <hash>. Verified: requirements.txt all OTel packages pinned to ==1.22.0/==0.43b0; existing OTel tests green."`

### 1.2 P0 #14 — JWT module 起手 (est. 4 hours)
- [ ] **Add JWT lib to requirements.txt**
  - 加 `python-jose[cryptography]>=3.3.0,<4.0` (或 `pyjwt[crypto]>=2.8,<3.0`)
  - `pip install -r requirements.txt`
- [ ] **Create `backend/src/platform_layer/identity/jwt.py`**
  - `JWTManager` class: `encode(payload) → str` / `decode(token) → dict` / `verify(token) → bool`
  - Payload schema: `{sub: str user_id, tenant_id: str UUID, roles: list[str], iat: int, exp: int}`
  - HS256 (dev) / RS256 (prod) — config-driven
  - DoD: `python -c "from src.platform_layer.identity.jwt import JWTManager; print(JWTManager)"` works
- [ ] **Add JWT settings to `backend/src/core/config.py`**
  - pydantic Settings: `jwt_secret: str` / `jwt_algorithm: str = "HS256"` / `jwt_expiration_min: int = 60`
  - DoD: `Settings()` 能 load
- [ ] **Add JWT vars to `backend/.env.example`**
  - `JWT_SECRET=<dev-secret-change-me>` / `JWT_ALGORITHM=HS256` / `JWT_EXPIRATION_MIN=60`
- [ ] **Unit tests**
  - `backend/tests/unit/platform_layer/identity/test_jwt.py`
  - Cases: encode→decode round-trip, verify valid, reject expired, reject bad signature
  - DoD: ≥ 6 tests green

### 1.3 Day 1 closeout (est. 1 hour)
- [ ] **Day 1 progress.md**
  - Path: `docs/03-implementation/agent-harness-execution/phase-52-5/sprint-52-5-audit-carryover/progress.md`
  - Sections: Today's accomplishments / Remaining for Day 2 / Notes
- [ ] **Commit Day 1 work**
  - Message: `feat(identity, sprint-52-5): Day 1 — JWT module skeleton + P0 #15 OTel lock`
  - **Verify branch before commit**

---

## Day 2-3 — P0 #11 + #12 + #16 (Multi-tenant + 5-place TraceContext) (est. 12-14 hours)

### 2.1 SessionRegistry tenant-scoped (est. 2 hours)
- [ ] **Refactor `backend/src/api/v1/chat/session_registry.py` to tenant-scoped storage**
  - `dict[UUID tenant_id, dict[UUID session_id, ChatSession]]`
  - `register(tenant_id, session)` / `lookup(tenant_id, session_id)` / `delete(tenant_id, session_id)`
  - Cross-tenant lookup returns `None` (caller raises 404)
  - DoD: 舊 single-dict signature deprecated 或 replaced

### 2.2 chat router endpoints + handler 加 multi-tenant + TraceContext root (est. 3 hours)
- [ ] **`router.py` POST /chat 加 `current_tenant: UUID = Depends(get_current_tenant)`**
- [ ] **`router.py` POST /chat/{session_id}/cancel 加 same**
  - 跨 tenant cancel → 404
- [ ] **`router.py` GET /chat/{session_id}/events 加 same**
  - 跨 tenant SSE → 404
- [ ] **`handler.py` chat_handler 創 `TraceContext.create_root(tenant_id, user_id, session_id)`**
  - 傳給 `AgentLoopImpl.run(trace_context=trace_ctx)`
  - DoD: grep `TraceContext.create_root` in `backend/src/api/` ≥ 1
- [ ] **`sse.py` SSE event payload 加 `trace_id` field** (per 17.md §4.1)
  - DoD: 第一個 event 含 `trace_id`

### 2.3 5-place tracer.start_span (est. 4 hours, P0 #16)
- [ ] **`backend/src/adapters/azure_openai/adapter.py`** — wrap `chat()` body in `tracer.start_span("llm_chat")`
  - Attributes: `provider`, `model`, `tenant_id`, parent from `trace_context.span_id`
  - DoD: grep `tracer.start_span` in adapter ≥ 1
- [ ] **`backend/src/agent_harness/state_mgmt/checkpointer.py`** — wrap `save()` in `tracer.start_span("state_checkpoint_save")`
- [ ] **`backend/src/agent_harness/orchestrator_loop/loop.py`** — `tracer.start_span(f"loop_turn_{n}")` per turn
- [ ] **`backend/src/agent_harness/tools/executor.py`** — `tracer.start_span(f"tool_{tool_name}")` per execution
- [ ] **(Already done in 2.2) chat handler API entry span**
- [ ] **Verify**: grep `tracer.start_span` in `backend/src/` ≥ 5

### 2.4 Integration tests (est. 4 hours)
- [ ] **Update `backend/tests/integration/api/test_chat_e2e.py`**
  - Remove `pytest.skip` on line 8 (per W3-2 audit)
  - Adapt to JWT-based auth (use JWTManager to mint test tokens)
- [ ] **Create `backend/tests/integration/api/test_chat_multi_tenant.py`**
  - Use **real PostgreSQL** (`ipa_v2_postgres`), not SQLite
  - Cases (≥ 3 scenarios):
    - tenant A POST /chat → session_id; tenant B GET /chat/{session_id}/events → 404
    - tenant A cancel tenant B's session → 404
    - SessionRegistry not leak across tenants (direct test)
  - DoD: pytest `-m multi_tenant` all green; runtime ≥ 2s（real DB, not 0.36s mock）
- [ ] **Create `backend/tests/integration/observability/test_trace_propagation.py`**
  - Cases: SSE event has trace_id; capture spans via `tracer.start_span` mock; verify ≥ 5 spans for one chat round-trip
  - DoD: spans count ≥ 5; root → child hierarchy correct

### 2.5 Manual e2e test + Day 2-3 closeout (est. 1.5 hours)
- [ ] **Manual cross-tenant probe**
  - Start backend; mint two JWT tokens (tenant A, tenant B); curl tenant A POST /chat → session_id; curl tenant B GET /chat/{session_id}/events → expect 404
  - Save log + screenshot to progress.md
- [ ] **Coverage check**: multi-tenant + observability ≥ 90%
- [ ] **Day 2 + Day 3 progress.md**
- [ ] **Commit**
  - Message: `feat(api-chat+observability, sprint-52-5): Day 2-3 — multi-tenant chat router + 5-place TraceContext (P0 #11+#12+#16)`
  - **Verify branch before commit**
- [ ] **Close GitHub issues #11, #12, #16**
  - `gh issue close 11 --comment "..."`
  - `gh issue close 12 --comment "..."`
  - `gh issue close 16 --comment "..."`

---

## Day 4-5 — P0 #13 verify_audit_chain.py + cron (est. 12-14 hours)

### 4.1 Standalone CLI core logic (est. 4 hours)
- [ ] **Create `backend/scripts/__init__.py`** (if not exists)
- [ ] **Create `backend/scripts/verify_audit_chain.py`**
  - asyncpg + hashlib, no Django/FastAPI dep
  - Connect via `.env` DB config
  - Per-tenant chain walk:
    - Fetch audit_log rows ASC by `created_at`
    - Recompute `curr_hash = SHA256(prev_hash || canonical_json(payload) || tenant_id || ts_ms)`
    - Compare stored vs computed
    - Compare `prev_hash == previous_row.curr_hash`
  - On mismatch: exit 1 + print 篡改起點 row id
  - On all-OK: exit 0 + print `Verified N rows across M tenants`
  - DoD: `python -m scripts.verify_audit_chain --help` works
- [ ] **CLI args**
  - `--tenant <uuid>` (single tenant fast path)
  - `--from-date <YYYY-MM-DD>` (partial verify)
  - `--alert-webhook <url>` (POST on failure)
  - `--ignore-tenant <uuid>` (skip known-test forgery `aaaa...4444`)
  - DoD: `--help` shows all 4 options

### 4.2 Test against current DB (est. 2 hours)
- [ ] **Run verify against existing audit_log (with fake row id=39 in tenant `aaaa...4444`)**
  - Expected: exit 1 + clearly identifies id=39 as 篡改起點
  - DoD: stdout matches expected pattern
- [ ] **Run with `--ignore-tenant aaaa...4444`**
  - Expected: exit 0 + `Verified N rows across M tenants`

### 4.3 Unit tests (est. 3 hours)
- [ ] **Create `backend/tests/unit/scripts/test_verify_audit_chain.py`**
  - Cases: empty chain, single row, valid 5-row chain, tampered hash, broken link, ignore-tenant flag
  - Mock asyncpg conn for fast test
  - DoD: ≥ 8 tests green

### 4.4 docker-compose audit-verifier service (est. 3 hours)
- [ ] **Add `audit-verifier` service to `docker-compose.dev.yml`**
  - Use `mcuadros/ofelia` or `aptible/supercronic` image
  - Schedule: daily 02:00
  - DoD: `docker compose config` shows new service
- [ ] **Optionally create `docker/audit-verifier/Dockerfile`**
  - python:3.11-slim + asyncpg
  - DoD: `docker compose build audit-verifier` succeeds
- [ ] **Manual cron trigger test**
  - `docker compose run --rm audit-verifier python -m scripts.verify_audit_chain --ignore-tenant aaaa...4444`
  - DoD: exit 0 in container

### 4.5 Webhook alert (est. 1 hour)
- [ ] **Implement webhook alert in verify_audit_chain.py**
  - On mismatch + `--alert-webhook` set → POST JSON `{tenant_id, row_id, expected_hash, actual_hash}`
  - DoD: mock webhook server receives payload

### 4.6 Day 4-5 closeout (est. 1.5 hours)
- [ ] **Add §Audit Verification chapter to `docs/03-implementation/agent-harness-planning/13-deployment-and-devops.md`**
- [ ] **Day 4 + Day 5 progress.md**
- [ ] **Commit**
  - Message: `feat(audit-hash, sprint-52-5): Day 4-5 — verify_audit_chain.py + cron + alert (P0 #13)`
  - **Verify branch before commit**
- [ ] **Close GitHub issue #13**

---

## Day 6 — P0 #14 JWT 完成 + P0 #17 sandbox 起手 (est. 8 hours)

### 6.1 JWT middleware + tests (est. 4 hours, completes P0 #14)
- [ ] **Refactor `backend/src/platform_layer/middleware/tenant_context.py`**
  - Read `Authorization: Bearer <jwt>` header
  - Verify via `JWTManager` (signature + expiration)
  - Extract `tenant_id` → `request.state.tenant_id`
  - No token / expired / bad sig → 401
  - **Remove `X-Tenant-Id` fallback** (per audit P0 緊急度)
  - DoD: grep `X-Tenant-Id` in `backend/src/platform_layer/middleware/` = 0
- [ ] **Update `get_current_tenant` dependency to read from `request.state.tenant_id`**
  - Existing API unchanged, internals refactored
- [ ] **Create `backend/tests/integration/api/test_jwt_auth.py`**
  - Cases: no Authorization → 401, expired → 401, bad sig → 401, valid → 200 + correct tenant_id
  - Attack test: forged `X-Tenant-Id` header → ignored (no fallback)
  - DoD: ≥ 5 tests green

### 6.2 P0 #17 sandbox: requirements + Docker image (est. 3 hours)
- [ ] **Add `docker>=7.0,<8.0` to `backend/requirements.txt`**
- [ ] **Create `docker/sandbox/Dockerfile`**
  - `python:3.11-slim` base
  - non-root user `sandbox-runner`
  - Pre-install: `json`, `requests` (if `network_blocked=False` mode)
  - Read-only fs except /tmp
  - DoD: `docker build -t ipa-sandbox docker/sandbox/` succeeds
- [ ] **Smoke test sandbox image**
  - `docker run --rm --memory=128m --cpus=0.5 --network=none ipa-sandbox python -c "import os; print(os.listdir('/'))"`
  - DoD: only sees container fs, NOT host fs

### 6.3 Day 6 closeout (est. 1 hour)
- [ ] **Day 6 progress.md**
- [ ] **Commit JWT P0 #14**
  - Message: `feat(identity, sprint-52-5): Day 6 — JWT replace X-Tenant-Id (P0 #14 complete)`
  - **Verify branch before commit**
- [ ] **Close GitHub issue #14**
- [ ] **Commit sandbox starter**
  - Message: `chore(sandbox, sprint-52-5): Day 6 — Docker image + requirements (P0 #17 progress)`

---

## Day 7-8 — P0 #17 sandbox Docker isolation 完成 (est. 12-14 hours)

### 7.1 Rewrite `backend/src/agent_harness/tools/sandbox.py` (est. 6 hours)
- [ ] **Replace subprocess+resource-based impl with docker SDK**
  - `class DockerSandbox`:
    - `execute(code: str, timeout_sec, memory_limit_mb, cpu_limit, network_blocked: bool) → SandboxResult`
    - Create short-lived container with `--memory`, `--cpus`, `--network none/bridge`, `--read-only`, `--cap-drop=ALL`
    - Stream stdout/stderr; kill on timeout
    - DoD: grep `# noqa: ARG002` in sandbox.py = 0 (no doc-only flag)
- [ ] **Cross-platform behavior**
  - Windows + Linux + Mac via Docker daemon
  - `network_blocked=True` → real `--network none` (not skip)

### 7.2 Tests (est. 4 hours)
- [ ] **Update existing 51.1 sandbox tests to use `DockerSandbox`**
  - DoD: 既有 sandbox tests 100% pass on Windows + Linux
- [ ] **Create `backend/tests/integration/tools/test_sandbox_isolation.py`**
  - **RCE prevention test**: `os.listdir("/")` from sandbox does NOT show host fs (Windows + Linux)
  - **Network blocked test**: `socket.connect("8.8.8.8", 80)` from sandbox FAILS when `network_blocked=True`
  - **Memory limit test**: allocating 200MB inside 128MB sandbox → killed
  - **Timeout test**: `time.sleep(60)` with timeout=2 → killed at 2s
  - DoD: ≥ 4 isolation tests green

### 7.3 Performance check (est. 1 hour)
- [ ] **Measure sandbox startup overhead**
  - `time docker run --rm ipa-sandbox python -c "print('hi')"` (10 runs avg)
  - DoD: avg < 500ms; record in progress.md
  - If > 500ms: consider pre-warmed container pool (defer to future sprint, note as Audit Debt)

### 7.4 Production manifest update (est. 1 hour)
- [ ] **Remove `disabled_in_production: true` from python_sandbox tool registration**
  - (Was added per W4P-3 audit recommendation)
  - Now real isolation → can re-enable for production
  - DoD: tool config no longer flagged

### 7.5 Day 7-8 closeout (est. 1.5 hours)
- [ ] **Day 7 + Day 8 progress.md**
- [ ] **Commit**
  - Message: `feat(sandbox, sprint-52-5): Day 7-8 — Docker container isolation + RCE prevention (P0 #17 complete)`
  - **Verify branch before commit**
- [ ] **Close GitHub issue #17**

---

## Day 9 — P0 #18 memory_tools tenant injection (est. 6 hours)

### 9.1 ExecutionContext dataclass (est. 1 hour)
- [ ] **Create `backend/src/agent_harness/tools/execution_context.py`**
  ```python
  @dataclass(frozen=True)
  class ExecutionContext:
      tenant_id: UUID
      user_id: UUID
      session_id: UUID
      trace_context: TraceContext
  ```
  - DoD: importable from `agent_harness.tools`

### 9.2 Refactor ToolExecutor (est. 2 hours)
- [ ] **Edit `backend/src/agent_harness/tools/executor.py`**
  - `execute(self, tool_call: ToolCall, context: ExecutionContext) → ToolResult`
  - Pass `context` to handler: `await handler(arguments=tool_call.arguments, context=context)`
- [ ] **Update Loop to construct ExecutionContext per execute()**
  - From state.tenant_id / state.user_id / state.session_id / trace_context

### 9.3 Refactor memory_tools handlers (est. 2 hours)
- [ ] **Edit `backend/src/agent_harness/memory/tools.py`**（或同等 path）
  - All memory tool handlers signature: `async def memory_<op>(arguments: dict, context: ExecutionContext) → dict`
  - Use `context.tenant_id`, NOT `arguments["tenant_id"]`
  - If `arguments.get("tenant_id")` exists and ≠ `context.tenant_id` → raise `ToolExecutionError("Tenant mismatch")` + audit log
  - DoD: grep `arguments\[.tenant_id.\]` in memory/tools.py = 0

### 9.4 Tests (est. 1.5 hours)
- [ ] **Create `backend/tests/unit/memory/test_memory_tools_tenant_injection.py`**
  - Cases:
    - Handler receives ExecutionContext (mock ToolExecutor)
    - LLM-forged `arguments.tenant_id ≠ context.tenant_id` → raises + audit log
    - Real-DB integration: tenant A query memory → only sees A's records
  - **Use real PostgreSQL** for integration cases (not all MagicMock)
  - DoD: ≥ 5 tests green; runtime ≥ 2s (real DB)

### 9.5 Day 9 closeout (est. 30 min)
- [ ] **Day 9 progress.md**
- [ ] **Commit**
  - Message: `feat(memory, sprint-52-5): Day 9 — memory_tools handler ExecutionContext-based tenant (P0 #18 complete)`
  - **Verify branch before commit**
- [ ] **Close GitHub issue #18**

---

## Day 10 — P1 hygiene 一次清完 (est. 6 hours)

### 10.1 P1 #6 — requirements.txt Celery cleanup (est. 30 min)
- [ ] **Edit `backend/requirements.txt`**
  - Remove `celery>=5.4,<6.0`
  - Add comment: `# temporalio: planned for Phase 53.1 (TemporalQueueBackend)`
  - DoD: `grep -i celery backend/requirements.txt` 無生產依賴

### 10.2 P1 #7 — Worker dir 統一 (est. 2 hours)
- [ ] **Move `runtime/workers/` → `platform_layer/workers/` via `git mv`**
  - Preserve git history
- [ ] **Update all imports**
  - `grep -rln "from runtime.workers" backend/src/ | xargs sed -i 's/runtime.workers/platform_layer.workers/g'`
  - DoD: `grep "from runtime.workers" backend/src/` returns 0
- [ ] **Keep `runtime/workers/__init__.py` as deprecation shim** (1 week)
  - Re-export from `platform_layer.workers` + log warning

### 10.3 P1 #8 — AgentLoopWorker docstring warning (est. 1 hour)
- [ ] **Edit `backend/src/platform_layer/workers/agent_loop_worker.py`**
  - Add prominent class + module docstring:
    ```
    [STUB] Phase 49.4-53.1 — production worker requires TemporalQueueBackend (Phase 53.1)
    Current implementation is for development/testing only.
    ```
  - DoD: `head -20 backend/src/platform_layer/workers/agent_loop_worker.py` shows `[STUB]` warning

### 10.4 P1 #4 — Azure OpenAI integration test (est. 2 hours)
- [ ] **Create `backend/src/adapters/azure_openai/tests/test_integration.py`**
  - Mark `@pytest.mark.integration`
  - Default skip; env var `RUN_AZURE_INTEGRATION=1` to enable
  - Cases: 1 round-trip, 1 streaming, 1 tool call (real Azure API)
  - DoD: setting env var + valid Azure key → tests pass

### 10.5 Day 10 closeout (est. 30 min)
- [ ] **Day 10 progress.md**
- [ ] **Commit P1 cleanup**
  - Message: `chore(hygiene, sprint-52-5): Day 10 — 4 P1 items (W2-1 #4 / W2-2 #6 #7 #8)`
  - **Verify branch before commit**

---

## Day 11 — Retrospective + W4 Trigger + PR (est. 5 hours)

### 11.1 Final integration tests (est. 2 hours)
- [ ] **Run full test suite**
  - `python -m pytest --cov=src --cov-report=term-missing` (NOT bare pytest)
  - DoD: all green; coverage ≥ baseline
- [ ] **Manual end-to-end e2e**
  - Start backend + frontend
  - Send chat with JWT token (tenant A)
  - Observe SSE event contains `trace_id`
  - Try cross-tenant probe with tenant B → 404
  - Inspect Jaeger UI: see root span + 5 child spans
  - DoD: log/screenshot evidence in progress.md

### 11.2 Cross-cutting lint counts (est. 30 min)
- [ ] **Multi-tenant grep counts**
  - `grep "Depends(get_current_tenant)" backend/src/api/v1/chat/ -r | wc -l` → ≥ 3
  - Record before/after numbers in retrospective.md
- [ ] **TraceContext propagation grep counts**
  - `grep "tracer.start_span" backend/src/adapters/ -r | wc -l` → ≥ 1
  - `grep "tracer.start_span" backend/src/agent_harness/ -r | wc -l` → ≥ 4
  - `grep "TraceContext.create_root" backend/src/api/ -r | wc -l` → ≥ 1
  - Record before/after
- [ ] **LLM Neutrality**
  - `grep -r "from openai\|from anthropic\|import openai\|import anthropic" backend/src/agent_harness/ backend/src/business_domain/` → 0
- [ ] **AP-10 Real DB test runtime**
  - Multi-tenant tests runtime ≥ 2s (real PG, not 0.36s mock)

### 11.3 Retrospective (est. 1 hour)
- [ ] **Create `docs/03-implementation/agent-harness-execution/phase-52-5/sprint-52-5-audit-carryover/retrospective.md`**
- [ ] **Answer mandatory 5+1 questions**:
  1. **每個 P0 真清了嗎？** Commit hash + verification result for each of 8 P0
  2. **跨切面紀律守住了嗎？** Multi-tenant / TraceContext / LLM Neutrality grep counts (before/after)
  3. **有任何砍 scope 嗎？** 透明列出 (no undisclosed cut)
  4. **GitHub issues 全 close 了嗎？** 8 URLs + close commit hash
  5. **Audit Debt 有累積嗎？** New audit-worthy items found during cleanup
  6. **主流量整合驗收**（per mini-W4-pre Process Fix #6）：
     - chat handler 真用 Depends(get_current_tenant)? grep ≥ 3?
     - chat handler 真 emit TraceContext.create_root()? grep ≥ 1?
     - Adapter 真有 tracer.start_span("llm_chat")? grep ≥ 1?
     - memory_tools handler 真用 ExecutionContext? grep ≥ 1?
     - sandbox 真用 Docker container? 非 fake # noqa flag?

### 11.4 W4 Audit Trigger (est. 30 min)
- [ ] **Notify audit session: cleanup sprint complete, W4 ready**
  - Message includes:
    - 8 P0 close URLs
    - 4 P1 fixed evidence
    - retrospective.md link
    - Cross-cutting grep counts (multi-tenant / TraceContext / LLM Neutrality)
    - Tests runtime growth (mock → real DB)
    - Audit Debt list (new items found)

### 11.5 Final closeout + PR (est. 1 hour)
- [ ] **Day 11 progress.md**
- [ ] **Commit retrospective + closeout**
  - Message: `docs(audit-carryover, sprint-52-5): Day 11 — retrospective + W4 trigger`
  - **Verify branch before commit**
- [ ] **Push branch + open PR**
  - `git push origin feature/sprint-52-5-audit-carryover`
  - PR title: `feat(audit-carryover, sprint-52-5): Cleanup sprint — 8 P0 + 4 P1 (V2 W1+W2+W3+mini-W4-pre)`
  - PR body includes: each P0 verification evidence + GitHub issues close URLs + retrospective summary
- [ ] **CI green check**
  - All GitHub Actions pass (incl. mypy strict, real-DB tests)

### 11.6 Hooks restore — POST-MERGE ONLY
- [ ] **(After PR merged to main)** Restore graphify hooks:
  - `mv .git/hooks/post-checkout.disabled-by-cleanup-session .git/hooks/post-checkout`
  - `mv .git/hooks/post-commit.disabled-by-cleanup-session .git/hooks/post-commit`
  - DoD: hooks back, but cleanup session 已結束，無 commits 風險

---

## Anti-Pattern Self-Check (per anti-patterns-checklist.md 11 points)

Before each commit, verify:
- [ ] AP-1 No Pipeline-disguised-as-Loop (no `for step in steps:` linear executions)
- [ ] AP-2 No side-track (all new code traceable from `api/v1/chat/`)
- [ ] AP-3 No cross-directory scattering (each P0 in single owner directory)
- [ ] AP-4 No Potemkin features (each new component verified main-flow integration)
- [ ] AP-5 No undocumented PoC
- [ ] AP-6 No "future-proof" abstractions
- [ ] AP-7 Context rot mitigation N/A (no long conversations in this sprint)
- [ ] AP-8 PromptBuilder N/A (no LLM calls added; only existing wiring)
- [ ] AP-9 Verification N/A (52.5 doesn't add verifiers; uses existing)
- [ ] AP-10 Mock and real share ABC (multi-tenant tests use real PG)
- [ ] AP-11 No version suffix; naming consistent

---

## Discipline Reminders

🔴 **每個 commit 前必跑 `git branch --show-current`** (graphify hook bug 預防)
🔴 **不能像 50.2 那樣隱形砍 scope**（必須在 retrospective 透明聲明）
🔴 **Tests 必須跑 real PostgreSQL**（不是 SQLite，per AP-10 教訓）
🔴 **`python -m pytest`，不是 bare `pytest`**（per testing.md 50-1 retrospective CARRY-001 教訓）
🔴 **每個 P0 完成立即 close GitHub issue**（不堆到最後）
🔴 **不要動 `ipa_v2_postgres` Docker container**（healthy 多日，主 session 在用）
🔴 **不要修主 session 的 sprint 52.2 commits**（feature/phase-52-sprint-2-cat5-prompt-builder branch）

---

**Plan link**: [sprint-52-5-plan.md](./sprint-52-5-plan.md)
**Audit真相 index**: [V2-AUDIT-OPEN-ISSUES-20260501.md](../../../../claudedocs/5-status/v2-audit-2026-04/V2-AUDIT-OPEN-ISSUES-20260501.md)
