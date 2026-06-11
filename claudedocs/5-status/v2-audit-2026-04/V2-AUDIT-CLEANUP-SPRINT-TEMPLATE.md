# V2 Audit Carryover Cleanup Sprint — Plan + Checklist Template

> **STATUS**: TEMPLATE（主 session 需 fill in 5 處 TBD 後採用）
> **建立日期**: 2026-05-01
> **建立人**: Audit session（per V2-AUDIT-WEEK3-SUMMARY.md §10 建議）
> **使用方式**: 複製內容到 `docs/03-implementation/agent-harness-planning/phase-52-5-audit-carryover/` 下兩個檔案（`sprint-XX-plan.md` + `sprint-XX-checklist.md`），客製 TBD 欄位後 commit
> **TBD 客製處**：
> 1. Sprint number（建議 `sprint-52-3` 或 `sprint-52-5`，視 phase folder 命名）
> 2. Phase folder（建議 `phase-52-5-audit-carryover/`）
> 3. Owner 指派（每個 P0 至少 owner placeholder）
> 4. 起迄日期（建議 7 天）
> 5. Branch 命名（建議 `feature/sprint-XX-audit-carryover`）

---

# Part 1: Sprint Plan Template

```markdown
# Sprint TBD.TBD — Audit Carryover Cleanup (P0×4 + P1×4)

**Phase**: TBD（建議 phase-52-5-audit-carryover）
**Sprint**: TBD（建議 52.3 / 52.5 / 99）
**Duration**: 7 days
**Status**: TODO → IN PROGRESS → DONE
**Created**: 2026-05-01
**Owner**: TBD（建議：user 開新 session 處理）
**Branch**: feature/sprint-TBD-audit-carryover

---

## Sprint Goal

清除 V2 Verification Audit W1+W2+W3 累積的 4 P0 critical + 4 P1 high-priority carryover，**在 Phase 53.1 啟動前**讓 V2 multi-tenant + observability + audit-chain + auth 四條鐵律全部落地，避免 worker fork 後修補成本翻倍。

---

## Background

V2 Verification Audit（2026-04-29 ~ 2026-05-01）發現：
- W1+W2 P1 8 項中 7 項在 Sprint 49.4 ~ 51.2（5 sprint）完全 dropped（0% 進入 sprint planning）
- W3-2 揭露 Phase 50.2 chat router 同時違反 multi-tenant + observability 兩條鐵律
- W3-2 揭露 sprint plan 隱形砍 scope（TraceContext 承諾未實作 + retrospective 未交代）

**根因**：audit findings 缺乏 ticket 機制 / sprint plan template 缺 carryover section。本 sprint 同時清債 + 落地 process 修補。

詳見 `claudedocs/5-status/V2-AUDIT-WEEK3-SUMMARY.md`。

---

## User Stories

### US-1：作為平台維護者，我希望 chat router 強制執行多租戶隔離，以便符合 V2 server-side first 鐵律
- **驗收**：`backend/src/api/v1/chat/*.py` 全部 endpoint 使用 `Depends(get_current_tenant)`；`SessionRegistry` 改 tenant-scoped；integration test 不再 skip tenant middleware
- **影響檔案**：`backend/src/api/v1/chat/router.py` / `handler.py` / `session_registry.py` / `sse.py`；test_chat_e2e.py

### US-2：作為觀測性負責人，我希望 chat handler 落地 TraceContext propagation，以便 distributed tracing 全鏈路可串連
- **驗收**：chat endpoint 創建 `TraceContext.create_root()` + 沿鏈傳給 `AgentLoopImpl.run()`；SSE event 含 `trace_id`；前端可在 SSE event 看到統一 trace_id
- **影響檔案**：`backend/src/api/v1/chat/router.py` / `handler.py`；`backend/src/agent_harness/observability/tracer.py`（如需擴展）

### US-3：作為合規負責人，我希望 audit_log hash chain 有 daily verifier，以便 governance/HITL 可仰賴 audit log 為「不可否認證據」
- **驗收**：`backend/scripts/verify_audit_chain.py` 存在 + CLI 可獨立執行；daily cron / scheduled job 整合；偵測篡改時 alert
- **影響檔案**：新建 `backend/scripts/verify_audit_chain.py`；`docker-compose.dev.yml` 加 cron service；`docs/13-deployment-and-devops.md` 加 verifier 章節

### US-4：作為 identity 負責人，我希望 JWT 取代 X-Tenant-Id header，以便消除 trivial tenant spoofing 漏洞
- **驗收**：tenant_id 從 JWT decode 取得；middleware 不再讀 `X-Tenant-Id` header（保留向後相容性過渡期可加 deprecation warning）
- **影響檔案**：`backend/src/platform_layer/middleware/tenant_context.py`；JWT 產生 / 驗證模組（如尚未存在則新建 `backend/src/platform_layer/identity/jwt.py`）

### US-5：作為 codebase 維護者，我希望累積的 P1 hygiene 項一次清完，以便 codebase metadata 與實際決策一致
- **驗收**：見「Technical Specs §P1」
- **影響檔案**：見「File Change List §P1」

---

## Technical Specifications

### P0 #1 — chat router multi-tenant 隔離

**現況**（W3-2 verified）：
- `backend/src/api/v1/chat/router.py` 0 個 `Depends(get_current_tenant)` / 0 個 `tenant_id` filter
- `SessionRegistry` 是 process-wide dict（跨 tenant 共享）
- `test_chat_e2e.py:8` 明文 skip tenant middleware

**設計**：
1. 三個 chat endpoint（`POST /chat`, `POST /chat/{session_id}/cancel`, `GET /chat/{session_id}/events`）全部加 `current_tenant: UUID = Depends(get_current_tenant)`
2. `SessionRegistry` 改為 `dict[UUID, dict[UUID, ChatSession]]`（外層 key = tenant_id，內層 key = session_id），所有 register/lookup/delete 都帶 tenant_id 參數
3. 非該 tenant 的 session_id 直接 raise 404（不洩漏「session 存在但跨 tenant」訊息）
4. `test_chat_e2e.py` 移除 skip + 加 multi-tenant 測試（tenant A 看不到 tenant B 的 session）

**驗證**：
- `pytest -m multi_tenant`（如有此 marker）全綠
- 手動：tenant A 發 POST /chat → 拿到 session_id → 用 tenant B token 試 GET /chat/{session_id}/events → 預期 404
- W3-2 audit script 跑 grep `Depends(get_current_tenant)` in api/ → ≥ 3（每個 endpoint 一個）

**Effort**: 1-2 days

### P0 #2 — TraceContext propagation at chat handler

**現況**（W3-2 verified）：
- `backend/src/api/` grep `TraceContext|tracer` = 0 hit
- 50.2 plan §4.1 明文承諾未落地

**設計**：
1. `chat_handler` 開始時：`trace_ctx = TraceContext.create_root(tenant_id=current_tenant, user_id=current_user)`
2. 傳給 `AgentLoopImpl.run(trace_context=trace_ctx)`
3. SSE event payload 加 `trace_id` field（per 17.md §4.1 spec）
4. 前端可在 event 看到 `trace_id`（後續可用於 Jaeger query）

**驗證**：
- Unit test：mock loop.run，斷言 trace_context 被傳入
- Integration test：發 POST /chat → SSE stream 第一個 event 含 `trace_id`
- 端到端：跑一個 chat → 在 Jaeger UI 看到 root span + child span 串連

**Effort**: half day（與 P0 #1 共用 chat handler 修改 → 一起做更高效）

### P0 #3 — verify_audit_chain.py + cron + alert

**現況**（W1-3 verified）：
- audit_log table 設計完整（SHA-256 / per-tenant chain / prev_hash 在 input / append-only triggers）
- 但無 verify 程式 — audit session 實測：用 superuser INSERT 假 hash row（id=39, curr_hash="f"*64）成功進庫，0 偵測

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
2. CLI argument：`--tenant <uuid>`（單一 tenant 加速）/ `--from-date <YYYY-MM-DD>`（部分驗證）/ `--alert-webhook <url>`（失敗時 POST）
3. `docker-compose.dev.yml` 加 `audit-verifier` service：
   - cron-style（建議 ofelia / supercronic image）
   - 每日 02:00 跑一次（low-traffic time）
   - 失敗時 webhook → Slack/Teams（dev：log 到 stdout 即可）
4. 文件：`docs/13-deployment-and-devops.md` 加 §Audit Verification 章節

**驗證**：
- 跑現有 audit_log（含 W1-3 留下的 fake row id=39）→ 預期 exit 1，明確指出 id=39 為篡改起點
- 跑 cleanup 後（DBA 手動 cleanup audit session 留下的 test data，per W1-3 報告）→ 預期 exit 0
- Cron 整合：手動 trigger cron job 確認 service 可用

**Effort**: 2-3 days（含 cron 整合）

### P0 #4 — JWT 取代 X-Tenant-Id header

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
3. 過渡期（optional）：保留 `X-Tenant-Id` 作 fallback + deprecation log warning（一週後移除）
4. `get_current_tenant` dependency：從 `request.state.tenant_id` 讀（API 介面不變）

**驗證**：
- Unit test：JWT 產生 + verify round-trip
- Integration test：
  - 無 Authorization header → 401
  - 過期 token → 401
  - 簽章不符 → 401
  - 有效 token → 200 + 正確 tenant_id 注入
- 攻擊測試：嘗試假造 `X-Tenant-Id: <other-tenant>` → 應被忽略（fallback 移除後）

**Effort**: 1-2 days

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
- 設計：在 class docstring + module docstring 加 prominent `[STUB] Phase 49.4-53.1 — production worker requires TemporalQueueBackend (Phase 53.1)` 警告；考慮 rename 為 `AgentLoopWorkerStub`（影響 import path，需評估）
- Effort: 1 hour

---

## File Change List

### P0 #1 + #2（合併修改 chat router）
- ✏️ `backend/src/api/v1/chat/router.py` — 加 Depends + TraceContext.create_root()
- ✏️ `backend/src/api/v1/chat/handler.py` — 接受 tenant + trace_context，propagate
- ✏️ `backend/src/api/v1/chat/session_registry.py` — tenant-scoped storage
- ✏️ `backend/src/api/v1/chat/sse.py` — SSE event 含 trace_id
- ✏️ `backend/tests/integration/api/test_chat_e2e.py` — 移除 skip，加 multi-tenant test
- ➕ `backend/tests/integration/api/test_chat_multi_tenant.py` — 跨 tenant 隔離測試

### P0 #3
- ➕ `backend/scripts/verify_audit_chain.py`（核心邏輯）
- ➕ `backend/scripts/__init__.py`（如尚未存在）
- ✏️ `docker-compose.dev.yml` — 加 audit-verifier service
- ➕ `docker/audit-verifier/Dockerfile`（如需自訂 image）
- ✏️ `docs/03-implementation/agent-harness-planning/13-deployment-and-devops.md` — 加 §Audit Verification

### P0 #4
- ➕ `backend/src/platform_layer/identity/jwt.py`（如未存在）
- ✏️ `backend/src/platform_layer/middleware/tenant_context.py` — 改 JWT decode
- ✏️ `backend/.env.example` — 加 `JWT_SECRET` / `JWT_ALGORITHM` / `JWT_EXPIRATION_MIN`
- ✏️ `backend/src/core/config.py` — pydantic Settings 加 JWT 欄位
- ➕ `backend/tests/integration/api/test_jwt_auth.py`

### P1
- ✏️ `backend/requirements.txt` — 刪 Celery + 加 temporalio comment
- 🔁 `backend/src/runtime/workers/` → `backend/src/platform_layer/workers/` (move)
- ➕ `backend/src/adapters/azure_openai/tests/test_integration.py`
- ✏️ `backend/src/runtime/workers/agent_loop_worker.py` (or new path) — docstring 警告

---

## Acceptance Criteria

### Sprint-level（必過）
- [ ] 4 P0 全部 ✅（驗證見各 P0 「驗證」section）
- [ ] 4 P1 全部 ✅
- [ ] All tests pass: `python -m pytest --cov=src --cov-report=term-missing`
- [ ] Coverage 不低於 sprint 啟動前 baseline
- [ ] mypy strict pass
- [ ] CI green on PR
- [ ] 4 GitHub issues（W3-3 建立）全部 close

### 跨切面紀律（per W3-2 教訓）
- [ ] No new violations of multi-tenant rule（grep `Depends(get_current_tenant)` count 不減）
- [ ] No new TraceContext leak（observability propagation 完整）
- [ ] No new LLM SDK leak（CI lint 通過 W2-1 擴大後的範圍）
- [ ] Sprint scope 任何砍 / 延後在 retrospective 透明列出（no undisclosed cut）

---

## Deliverables（見 checklist 詳細）

- [ ] Day 0：plan + checklist 寫好 + branch + 4 GitHub issues
- [ ] Day 1-2：P0 #1 + P0 #2（chat router 合併修改）
- [ ] Day 3-4：P0 #3（verify_audit_chain.py + cron）
- [ ] Day 5：P0 #4（JWT replace）
- [ ] Day 6：P1 hygiene
- [ ] Day 7：retrospective + integration test + W4 audit trigger

---

## Dependencies & Risks

### 依賴
- `ipa_v2_postgres` Docker container running（已有）
- `_contracts/TraceContext` dataclass（49.4 Day 3 OTel 已建）
- `Depends(get_current_tenant)` infrastructure（49.3 Day 4.4 已建）

### 風險

| Risk | Mitigation |
|------|------------|
| JWT migration 影響其他 endpoint（governance / health） | 過渡期保留 X-Tenant-Id fallback 一週 |
| SessionRegistry tenant-scoped 改變影響 frontend chat-v2 | 先讀 chat-v2 source 確認無 hardcoded session lookup；必要時加 frontend 遷移 task |
| verify_audit_chain.py docker cron 整合複雜度 | Day 3-4 預留 buffer；如 cron 整合 > 1 day，cron 推遲到後續 sprint，先交付 standalone CLI |
| Audit session 留下的 fake hash rows（id 36-39 in tenant aaaa...4444）影響 verifier 測試 | 該 tenant 是 known-test forgery baseline，verifier 加 `--ignore-tenant <uuid>` flag |

---

## Audit Carryover Section（per W3 process fix）

本 sprint **本身就是** W1+W2+W3 的 carryover sprint，無新 audit carryover。

### 後續 audit 預期

- W4 audit（Sprint 52.2 + 本 sprint 完成後）：驗證
  - 4 P0 是否真清（重做 W1-2 / W1-3 / W3-2 對應檢查）
  - 4 GitHub issues 是否 close
  - 52.2 PromptBuilder 是否守住跨切面紀律
  - 是否有新的 process drift

---

## §10 Process 修補落地檢核

per W3 process fix #1 + #2 + #3 + #4 + #5：

- [x] Plan template 加 Audit Carryover 段落（本 plan §10 即範本）
- [x] Retrospective template 加 Audit Debt 段落（見 checklist Day 7）
- [ ] GitHub issue per P0/P1（user 確認後 audit session 建）
- [ ] 每月 Audit Status Review（手動 review）
- [ ] Audit re-verify 每 2-3 sprint（W4 已排）

---

## Retrospective 必答（per W3-2 教訓）

Sprint 結束時，retrospective 必須回答以下 5 條：

1. **每個 P0 真清了嗎？** 列每個 P0 對應 commit + verification 結果
2. **跨切面紀律守住了嗎？** Multi-tenant / TraceContext / LLM Neutrality grep counts
3. **有任何砍 scope 嗎？** 若有，明確列出 + 理由 + 後續排程（不能像 50.2 那樣隱形砍）
4. **GitHub issues 全 close 了嗎？** 列每個 issue url + close 時 commit
5. **Audit Debt 有累積嗎？** 本 sprint 期間有沒有發現新的 audit-worthy 問題？列出（不要等 W4 才發現）
```

---

# Part 2: Sprint Checklist Template

```markdown
# Sprint TBD.TBD — Audit Carryover Cleanup Checklist

[Link to plan]

---

## Day 0 — Setup（est. 2 hours）

### 0.1 Branch + Plan + Checklist commits
- [ ] **Create feature branch from main**
  - Command: `git checkout main && git pull && git checkout -b feature/sprint-TBD-audit-carryover`
  - DoD: `git branch --show-current` returns expected name

- [ ] **Commit Day 0 docs**
  - Files: this plan + this checklist
  - Commit message: `docs(sprint-TBD-audit-carryover): Day 0 plan + checklist`
  - DoD: `git log -1` shows Day 0 commit

### 0.2 GitHub Issues
- [ ] **Create 4 P0 GitHub issues**
  - Use `gh issue create` per P0
  - Label: `audit-carryover` + `priority/P0`
  - DoD: `gh issue list -l audit-carryover` returns 4 open issues

### 0.3 Carryover review
- [ ] **Read W3 SUMMARY + W3-2 + W1-3 + W1-2**
  - Files: claudedocs/5-status/V2-AUDIT-WEEK3-SUMMARY.md + 3 detailed reports
  - DoD: 能口頭描述 4 P0 各自的「現況 / 設計 / 驗證」

---

## Day 1 — P0 #1 + #2 Phase 1（est. 6 hours）

### 1.1 SessionRegistry tenant-scoped 重構（est. 2 hours）
- [ ] **改 SessionRegistry 為 tenant-scoped storage**
  - File: `backend/src/api/v1/chat/session_registry.py`
  - 設計：`dict[UUID, dict[UUID, ChatSession]]`
  - DoD: register/lookup/delete 全部接受 `tenant_id` 參數；舊簽名移除或加 deprecation warning

- [ ] **更新所有 SessionRegistry caller 傳 tenant_id**
  - Files: handler.py / sse.py / cancel logic
  - DoD: grep `SessionRegistry().register\|lookup\|delete` 0 個 caller 漏 tenant_id

### 1.2 chat router endpoint 加 multi-tenant dependency（est. 2 hours）
- [ ] **POST /chat 加 Depends(get_current_tenant)**
  - File: `backend/src/api/v1/chat/router.py`
  - DoD: handler 簽名含 `current_tenant: UUID`

- [ ] **POST /chat/{session_id}/cancel 加 Depends(get_current_tenant)**
  - DoD: 跨 tenant cancel 應 raise 404

- [ ] **GET /chat/{session_id}/events 加 Depends(get_current_tenant)**
  - DoD: 跨 tenant SSE 應 raise 404

### 1.3 chat handler 加 TraceContext.create_root()（est. 1 hour，P0 #2）
- [ ] **chat_handler 開始時創 root trace context**
  - File: `backend/src/api/v1/chat/handler.py`
  - 設計：`trace_ctx = TraceContext.create_root(tenant_id=tenant, user_id=user)`
  - DoD: AgentLoopImpl.run() 收到 trace_context 參數

- [ ] **SSE event 加 trace_id field**
  - File: sse.py
  - DoD: 第一個 event payload 含 `trace_id`，per 17.md §4.1 schema

### 1.4 Day 1 closeout（est. 1 hour）
- [ ] Day 1 progress.md 寫好
- [ ] Commit Day 1 work
  - Format: `feat(api-chat, sprint-TBD-audit-carryover): Day 1 — multi-tenant + TraceContext (P0 #1+#2 phase 1)`

---

## Day 2 — P0 #1 + #2 Phase 2 + Tests（est. 6 hours）

### 2.1 Integration tests（est. 3 hours）
- [ ] **Update test_chat_e2e.py：移除 skip + 加 tenant test**
  - File: `backend/tests/integration/api/test_chat_e2e.py`
  - DoD: line 8 `skip` removed；新增 `test_tenant_a_cannot_see_tenant_b_session`

- [ ] **新建 test_chat_multi_tenant.py**
  - File: `backend/tests/integration/api/test_chat_multi_tenant.py`
  - 案例：3+ scenarios（read / cancel / SSE 跨 tenant 全擋）
  - DoD: pytest 跑 `-m multi_tenant` 全綠

- [ ] **新建 test_chat_trace_context.py**
  - 案例：root trace_id propagation；SSE event 含 trace_id；child span attached
  - DoD: pytest 跑 `-k "trace"` 全綠

### 2.2 Manual e2e test（est. 1 hour）
- [ ] **手測：跨 tenant 試讀 → 預期 404**
  - 啟動 backend；用 curl 模擬兩個 tenant token
  - DoD: 截圖 / log 證據貼進 progress.md

### 2.3 Day 2 closeout（est. 2 hours）
- [ ] Coverage check（multi-tenant 相關代碼 ≥ 90%）
- [ ] Day 2 progress.md
- [ ] Commit
  - Format: `feat(api-chat, sprint-TBD-audit-carryover): Day 2 — multi-tenant tests + manual e2e (P0 #1+#2 phase 2)`
- [ ] **Close GitHub issues #P0-1 + #P0-2**
  - DoD: `gh issue list -s closed -l audit-carryover` 含 2 個

---

## Day 3 — P0 #3 verify_audit_chain.py（est. 8 hours）

### 3.1 Standalone CLI 核心邏輯（est. 4 hours）
- [ ] **建 backend/scripts/verify_audit_chain.py**
  - 設計：asyncpg + hashlib，無 framework 依賴
  - DoD: 可獨立執行 `python -m scripts.verify_audit_chain`

- [ ] **per-tenant chain walk + 重算對比**
  - DoD: 取 5 row 重算 stored=computed 正確

- [ ] **chain link 驗證**
  - DoD: prev_hash 對齐 prev row curr_hash

- [ ] **CLI args**
  - `--tenant <uuid>` / `--from-date <YYYY-MM-DD>` / `--alert-webhook <url>` / `--ignore-tenant <uuid>`
  - DoD: `--help` 可看見全部選項

### 3.2 試驗 audit session 留下的 fake row（est. 1 hour）
- [ ] **跑 verify_audit_chain.py against 現有 DB（含 fake row id=39）**
  - DoD: exit 1 + 明確指出 id=39 為篡改起點

- [ ] **加 `--ignore-tenant aaaa...4444` 後再跑**
  - DoD: exit 0 + 輸出 `Verified N rows across M tenants`

### 3.3 Day 3 closeout（est. 3 hours）
- [ ] Day 3 progress.md
- [ ] Unit tests for verify_audit_chain.py（mock DB + chain scenarios）
- [ ] Commit

---

## Day 4 — P0 #3 cron + alert（est. 6 hours）

### 4.1 docker-compose audit-verifier service（est. 3 hours）
- [ ] **加 audit-verifier service to docker-compose.dev.yml**
  - 用 ofelia / supercronic image
  - 每日 02:00 trigger

- [ ] **建 docker/audit-verifier/Dockerfile（如需）**
  - DoD: `docker compose up audit-verifier` 成功啟動

### 4.2 Alert webhook（est. 2 hours）
- [ ] **失敗時 POST webhook**
  - dev：log 到 stdout 即可
  - prod-ready：HTTP POST JSON to env var URL

- [ ] **手動觸發失敗測試**
  - 用 fake row → 觸發 alert
  - DoD: webhook 收到 payload

### 4.3 Day 4 closeout（est. 1 hour）
- [ ] Day 4 progress.md
- [ ] Update docs/13-deployment-and-devops.md
- [ ] Commit
- [ ] **Close GitHub issue #P0-3**

---

## Day 5 — P0 #4 JWT 取代 X-Tenant-Id（est. 8 hours）

### 5.1 JWT 模組（est. 2 hours）
- [ ] **建 backend/src/platform_layer/identity/jwt.py（如未存在）**
  - 產生 + 驗證 + payload schema
  - DoD: round-trip test 通過

### 5.2 Middleware 改 JWT decode（est. 2 hours）
- [ ] **改 tenant_context.py 從 Authorization header 解析**
  - 加 fallback 過渡期（`X-Tenant-Id` 仍可用 + deprecation log）
  - DoD: middleware 行為 backward-compatible

### 5.3 Tests（est. 3 hours）
- [ ] **新建 test_jwt_auth.py**
  - 案例：no auth → 401；過期 → 401；簽章錯 → 401；valid → 200
  - DoD: 4+ tests 全綠

- [ ] **攻擊測試**
  - 假造 X-Tenant-Id（fallback 移除後）→ 應被忽略
  - DoD: test 證明 JWT 為單一 tenant_id 來源

### 5.4 Day 5 closeout（est. 1 hour）
- [ ] Day 5 progress.md
- [ ] Commit
- [ ] **Close GitHub issue #P0-4**

---

## Day 6 — P1 Hygiene（est. 6 hours）

### 6.1 requirements.txt 清理（est. 30 min）
- [ ] **刪 celery>=5.4,<6.0**
- [ ] **加 temporalio TODO comment**
- [ ] DoD: `grep -i celery backend/requirements.txt` 無生產依賴

### 6.2 Worker 目錄統一（est. 2 hours）
- [ ] **Move runtime/workers/ → platform_layer/workers/**
  - 用 `git mv` 保留 history
- [ ] **更新所有 import**
  - DoD: `grep "from runtime.workers" backend/src/` 0 hit
- [ ] **保留 runtime/workers/__init__.py 作 deprecation shim**
  - DoD: 一週後可安全刪除

### 6.3 AgentLoopWorker docstring 警告（est. 1 hour）
- [ ] **加 prominent stub warning to class + module docstring**
  - DoD: `head -20 backend/src/platform_layer/workers/agent_loop_worker.py` 顯示 `[STUB]` 警告

### 6.4 azure_openai test_integration.py（est. 2 hours）
- [ ] **建 backend/src/adapters/azure_openai/tests/test_integration.py**
  - mark `@pytest.mark.integration`
  - 預設 skip；env var `RUN_AZURE_INTEGRATION=1` 啟用
  - 案例：1 round-trip + 1 streaming + 1 tool call
  - DoD: 在 dev 環境設 env var 後跑 → 真打 Azure pass

### 6.5 Day 6 closeout（est. 30 min）
- [ ] Day 6 progress.md
- [ ] Commit P1 cleanup（一個 commit 或分多個 logical commit）

---

## Day 7 — Retrospective + W4 Trigger（est. 4 hours）

### 7.1 Final integration tests（est. 2 hours）
- [ ] **跑全 test suite**
  - `python -m pytest --cov=src --cov-report=term-missing`
  - DoD: all green + coverage ≥ baseline

- [ ] **手動端到端 e2e**
  - 啟動 backend + frontend；發 chat；觀察 SSE 含 trace_id；確認跨 tenant 隔離
  - DoD: log/截圖證據

### 7.2 Retrospective（est. 1 hour）
- [ ] **建 retrospective.md**
  - Path: `docs/03-implementation/agent-harness-execution/phase-TBD/sprint-TBD-audit-carryover/retrospective.md`
  - 必答 5 條（plan §Retrospective 必答 section）
  - DoD: 9 sections 全填

### 7.3 W4 Audit Trigger（est. 30 min）
- [ ] **通知 audit session：cleanup sprint 完成，可進 W4**
  - 列出每個 P0 的驗證證據 + commit hash
  - 列出 GitHub issues 全 close 證據

### 7.4 Final closeout（est. 30 min）
- [ ] Day 7 progress.md
- [ ] Commit retrospective + closeout
- [ ] Push branch + 開 PR
- [ ] PR title: `feat(audit-carryover, sprint-TBD): Cleanup sprint — 4 P0 + 4 P1 (V2 W1+W2+W3)`
- [ ] PR body 含：每個 P0 verification 證據 + GitHub issues close URLs
```

---

# Part 3: 主 session 客製檢查清單

主 session 採用此 template 時，請逐項客製：

- [ ] Sprint number（建議 52.3 或 52.5；視 phase folder 命名）
- [ ] Phase folder 建立（建議 `phase-52-5-audit-carryover/`）
- [ ] 起迄日期填入（建議 7 天）
- [ ] Branch 命名確認（建議 `feature/sprint-52-5-audit-carryover`）
- [ ] Owner 填入（建議：明寫「user 開新 cleanup session」而非「TBD」）
- [ ] PR title / commit prefix 對齊 sprint number
- [ ] 4 GitHub issues 建立（audit session 可協助）

---

**完成此 template 後**：

1. 主 session（或 user）建立 cleanup sprint 正式 plan + checklist
2. Audit session（我）建立 4 個 GitHub issues（user 確認用）
3. 52.2 Day 0 commit（含 §10 Audit Carryover 已寫的部分）+ Day 1 啟動
4. cleanup session 在 52.2 並行期間執行此 plan
5. 兩條線完成後，user 通知 audit session 觸發 W4 audit
