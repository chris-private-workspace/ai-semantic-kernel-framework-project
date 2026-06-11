# V2 Audit W1-2 — RLS + tenant_id 0-leak

**Audit 日期**: 2026-04-29
**Audit 範圍**: Sprint 49.3 RLS policies + tenant_context middleware + 紅隊測試
**結論**: ✅ **Passed** — 多租戶隔離真實有效；不阻塞 Phase 50 啟動

---

## 摘要

| 指標 | 結果 | 預期 | 評估 |
|---|---|---|---|
| RLS-enabled tables | **13** | 13 | ✅ 完全對齊 |
| RLS policies (USING+CHECK) | **26** | 13×2=26 | ✅ 完全對齊 |
| FORCE ROW LEVEL SECURITY | **13/13** | 全強制 | ✅ owner 也擋 |
| `rls_app_role` 存在 | ✅ | 必須存在 | ✅ 由 test fixture lazy 建立 |
| `ipa_v2.rolbypassrls` | **true** | — | ⚠️ 預期（dev role）；測試走 `SET LOCAL ROLE rls_app_role` 規避 |
| Append-only triggers | **3/3** | audit_no_upd_del + audit_no_trunc + state_no_trunc | ✅ |
| Pytest 紅隊測試 | **13 pass / 0 fail / 0 skip** | 7+ pass | ✅ 全綠 |
| 手動跨租戶 0-leak (5 vectors) | **5/5 守住** | 5/5 | ✅ |
| **阻塞 Phase 50** | ❌ 否 | — | 可推進 |

---

## Phase A 靜態分析

### A.1 RLS Migration（0009_rls_policies.py）

**13 表清單**（與 09-db-schema-design.md 完全對齊）：
users, roles, sessions, messages, message_events, tool_calls, state_snapshots, loop_states, api_keys, rate_limits, audit_log, memory_tenant, memory_user

**Policy 模式**（每表 2 policies）：
- `tenant_isolation_<t>` — `USING (tenant_id = current_setting('app.tenant_id', true)::uuid)` 適用 SELECT/UPDATE/DELETE
- `tenant_insert_<t>` — `WITH CHECK (...)` 適用 INSERT

**關鍵設計細節**：
- `current_setting(..., true)` 第二參 `true` → 未設時返 NULL（不 raise），`NULL = NULL → NULL → 無 row` 為 fail-safe 預設 ✓
- `ENABLE` + `FORCE` 雙重套用 → 連 owner 也被擋 ✓
- INSERT 用 `WITH CHECK` 防 cross-tenant insert ✓

**junction-style 表**（user_roles / role_permissions / tool_results / approvals 等 8 張）刻意不設 RLS，靠 FK upstream 表 RLS + app-layer JOIN filter — migration docstring 明示，**權衡合理但需 W1-4 驗證 ORM 真的 JOIN 過濾**。

### A.2 tenant_context Middleware（platform_layer/middleware/tenant_context.py）

兩部分：
1. **TenantContextMiddleware** — 從 `X-Tenant-Id` header 讀取 + UUID validate；missing → 401，invalid → 400（fail-close）✓
2. **get_db_session_with_tenant** — async dep，開 AsyncSession + `SELECT set_config('app.tenant_id', :tid, true)`（parameterised，無 SQL injection）✓

**驗證點**：
- ✅ JWT 路徑為 Sprint 49.4+ 後續工作（commit 註明）；Sprint 49.3 用 header（dev 階段可接受，但 prod 必換 JWT）
- ✅ exempt 清單只含 `/api/v1/health`（k8s probe），且註明添加路徑需 code review
- ✅ defensive raise 防止 middleware 漏裝
- ✅ commit/rollback 完整封裝

**舊檔 backend/src/middleware/tenant.py**（Sprint 49.1 stub）— 仍 raise 501，未被 api/main.py 使用；建議 Sprint 50.1 刪除避免混淆。

### A.3 紅隊測試誠實性（test_red_team_isolation.py + test_rls_enforcement.py）

| Test | Real PG | Role | Assertion 強度 | 真偽 |
|---|---|---|---|---|
| AV-1 forged tenant_id | ✅ asyncpg via SQLAlchemy | rls_app_role (NOLOGIN) | content compare + filter | ✅ 真 |
| AV-2 missing SET LOCAL | ✅ | rls_app_role | `result == []` | ✅ 真（無 set 時 USING NULL 過濾） |
| AV-3 SQL injection | ✅ | rls_app_role | `pytest.raises(DBAPIError)` | ✅ 真（::uuid cast 阻止） |
| AV-4 UPDATE audit | ✅ | (default) | `pytest.raises + 'append-only' in str` | ✅ 真 |
| AV-5a TRUNCATE audit | ✅ | (default) | 同上 | ✅ 真 |
| AV-5b TRUNCATE state_snapshots | ✅ | (default) | 同上 | ✅ 真 |
| AV-6 Qdrant namespace | unit (純 string) | — | namespace+filter inequality | ⚠️ 邏輯測試（無真 Qdrant）但合理 |

**關鍵亮點**：
- 測試**主動切到 NOLOGIN rls_app_role**（無 BYPASSRLS），不用 superuser → 排除「ipa_v2 BYPASSRLS 自動跳過」自欺
- Savepoint 包裹注入測試 → 不污染外層 fixture
- `_ensure_rls_app_role` 用 `DO $$ ... EXCEPTION WHEN duplicate_object`，idempotent ✓

### A.4 Append-only Triggers（0005_audit_log_append_only.py）

3 個 trigger 確認：
- `audit_log_no_update_delete` — ROW BEFORE UPDATE OR DELETE → RAISE
- `audit_log_no_truncate` — STATEMENT BEFORE TRUNCATE → RAISE
- `state_snapshots_no_truncate` — STATEMENT BEFORE TRUNCATE（49.2 carryover補裝）→ RAISE

均用 `BEFORE` → 真擋；訊息 `'audit_log is append-only'` 清楚 ✓

---

## Phase B Runtime 驗證

### B.1 DB 實況（pg_policies / pg_class）

```
SELECT count(*) FROM pg_tables WHERE rowsecurity=true AND schemaname='public';  -> 13 ✓
SELECT count(*) FROM pg_policies WHERE schemaname='public';                     -> 26 ✓
SELECT count(*) FROM pg_class WHERE relrowsecurity=true AND relforcerowsecurity=false; -> 0 ✓ (全 force)
SELECT count(*) FROM pg_trigger WHERE tgname IN (...);                          -> 3 ✓
SELECT rolname,rolbypassrls FROM pg_roles WHERE rolname='ipa_v2';               -> ipa_v2|t (預期，測試規避)
```

實際 = migration 聲稱，**無 drift**。

### B.2 Pytest 紅隊測試（real PG asyncpg）

```
13 passed in 0.58s
- AV-1 ~ AV-6: 7 pass
- test_rls_enforcement.py: 6 pass (SELECT/INSERT/UPDATE/DELETE/audit blocked)
0 failed, 0 skipped
```

### B.3 手動跨租戶試讀（asyncpg 直連，rls_app_role）

```
[T1 superuser BYPASSRLS] sees 2 rows: ['SECRET_A', 'SECRET_B']  (基線)
[T2 as tenant A]  sees 1 rows: ['SECRET_A']                     ✓ 隔離
[T3 as tenant B]  sees 1 rows: ['SECRET_B']                     ✓ 隔離
[T4 NO SET LOCAL — current_setting=None] sees 0 rows            ✓ fail-safe
[T5 cross-tenant INSERT] BLOCKED: InsufficientPrivilegeError    ✓ WITH CHECK
[T6 bogus uuid cast] BLOCKED: InvalidTextRepresentationError    ✓ injection 拒
```

T1=2 / T2=1 / T3=1 / 重疊=0 → **絕對 0 leak**。

### B.4 Audit Trigger 試驗

- T7a UPDATE audit_log → BLOCKED `audit_log is append-only` ✓
- T7b DELETE audit_log → BLOCKED ✓
- T7c TRUNCATE audit_log → BLOCKED ✓

---

## 各項評分

| 項目 | 評分 |
|---|---|
| RLS Policy 完整性（13 表 × 2 policies × FORCE） | ✅ |
| Middleware 真實性（真執行 set_config + parameterised） | ✅ |
| 紅隊測試誠實性（用 NOLOGIN role + real PG） | ✅ |
| 跨租戶 0-leak（手動 5 vectors + pytest 13 tests 全綠） | ✅ |
| Append-only 三 op 全擋 | ✅ |

---

## 修補建議（非阻塞，建議 Sprint 49.4-50.1 處理）

1. **P2 — 廢棄舊 stub** `backend/src/middleware/tenant.py`（Sprint 49.1 stub raise 501）：與 `platform_layer/middleware/tenant_context.py` 並存有混淆風險；Sprint 50.1 刪掉並 grep 確認無 import。
2. **P1 — JWT 路徑落地**：當前 middleware 從 `X-Tenant-Id` header 讀取，dev 環境可接受但 **prod 必須換 JWT extraction**。Sprint 49.4+ 待辦。
3. **P2 — Junction 表（W1-4 驗證）**：8 張無直接 RLS 的表（approvals / risk_assessments / guardrail_events 等）依賴 ORM JOIN 過濾。W1-4 ORM 審計需驗證 TenantScopedMixin / `select(Approval).join(Session)` 真的帶 tenant_id 過濾。
4. **P3 — Qdrant AV-6 真連測試**：當前僅 namespace string 邏輯測試；Sprint 51.2 Memory 範疇實作後加入 real Qdrant 整合測試。
5. **P3 — pg_partman 49.2 carryover**：image 切換 `postgres:16` 全版（已標記 carryover → 49.4），不擋 RLS 審計。

---

## 阻塞 Phase 50？

**❌ 否，可推進。**

理由：
- 13 表 RLS 全裝、26 policies 全套、FORCE 全開、append-only triggers 全擋
- 紅隊測試**真打 PostgreSQL**（不是 mock / SQLite）、用 **NOLOGIN rls_app_role**（不靠 BYPASSRLS 自欺）
- 手動 6 個攻擊向量驗證跨租戶 0-leak（包含 fail-safe 與 injection）
- middleware 設計 fail-close（missing tenant → 401），用 parameterised set_config（防 SQL injection）

W1-2 是 Week 1 五項中**安全核心最重的審計**（多租戶 = 合規生死線），Sprint 49.3 真實守住。沒有發現「自欺測試」、「pipeline 偽裝 loop」、「Potemkin feature」等 V1 反模式。

---

**下一步**：
- W1-3：審計 Audit hash chain 完整性（hash 計算正確性 + chain 防 tamper）
- W1-4：審計 ORM TenantScopedMixin（junction 表的 JOIN 過濾真實性）+ StateVersion 樂觀鎖
- W1-5：Week 1 審計總結
