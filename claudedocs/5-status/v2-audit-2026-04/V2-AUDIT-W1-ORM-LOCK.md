# V2 Audit W1-4 — ORM TenantScopedMixin + StateVersion 鎖

**Audit 日期**: 2026-04-29
**Auditor**: Verification Agent
**Sprint 範圍**: 49.2 + 49.3 (commits 6573033 / 6671615 / 2566b97 / 234cca0 / 3084394)
**結論**: ✅ **Passed** — 阻塞 Phase 50：**否**

---

## 摘要（TL;DR）

| 檢查項 | 結果 |
|---|---|
| TenantScopedMixin 覆蓋（business + session-scoped tables） | ✅ 13/13 預期繼承 |
| Mixin 強制 tenant_id NOT NULL + FK CASCADE + index | ✅ 真實落地（`base.py` L71-80） |
| 例外排除（global / junction / chain-via-FK） | ✅ 9 表合理排除 |
| StateVersion 鎖機制 | ✅ **真雙因子**（content hash + DB unique） |
| 100-併發 race test（自寫） | ✅ **1 success / 99 conflicts**（精確預期） |
| Migration vs ORM 一致性 | ✅ 全部 NOT_NULL 已套到實 schema |
| Append-only trigger | ✅ 已 fire（cleanup 時被擋） |

**阻塞 Phase 50**：❌ 否。可繼續推進。

---

## Phase A — TenantScopedMixin 覆蓋

### A.1 Mixin 定義（`backend/src/infrastructure/db/base.py:53-80`）

```python
class TenantScopedMixin:
    @declared_attr
    @classmethod
    def tenant_id(cls) -> Mapped[PyUUID]:
        return mapped_column(
            PgUUID(as_uuid=True),
            ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            ...
        )
```

**驗收**：
- ✅ `nullable=False`（鐵律 1）
- ✅ FK to `tenants.id` ON DELETE CASCADE
- ✅ 自動 index on tenant_id
- ✅ `declared_attr` 確保每子類有獨立 Column

### A.2 ORM Models 實際清單（DB 反射 31 tables，含 partition）

**繼承 TenantScopedMixin（13）— 全部 NOT_NULL=True**：
- `users` / `roles` (identity)
- `sessions` / `messages` / `message_events` (sessions)
- `tool_calls` (tools)
- `state_snapshots` / `loop_states` (state)
- `audit_log` (Sprint 49.3)
- `api_keys` / `rate_limits` (Sprint 49.3)
- `memory_tenant` / `memory_user` (Sprint 49.3)

### A.3 例外排除（9 表）— 全部合理

| Table | 理由 | 對齊 09.md |
|---|---|---|
| `tenants` | 多租戶層級的根 | ✅ |
| `tools_registry` | 全局工具 metadata（cross-tenant） | ✅ L25 explicit |
| `user_roles` / `role_permissions` | Junction；tenant 經 FK chain 推得 | ✅ |
| `tool_results` | tenant 經 tool_call FK chain | ✅ 09.md L25 |
| `memory_system` | Layer 1 全局策略 | ✅ |
| `memory_role` | Junction via role_id → roles.tenant_id | ✅ |
| `memory_session_summary` | Junction via session_id → sessions.tenant_id | ✅ |
| `approvals` / `risk_assessments` / `guardrail_events` | tenant via session chain；governance.py 註解明示與 09.md 對齐 | ✅ |

**RLS 補強**：governance 3 表雖無 tenant_id，但 0009 RLS policies 透過 session JOIN 強制（已於 W1-2 驗）。

### A.4 旁路檢查
- ❌ 沒有 model 重新 override `tenant_id` Column（grep `tenant_id\s*=\s*Column`）
- ❌ 沒有 model 跳過 mixin 又自定 tenant_id

---

## Phase B — StateVersion 雙因子鎖設計

### B.1 鎖機制（`state.py:147-214`）

**雙因子 = content + structure**：

| Factor | 機制 | 位置 |
|---|---|---|
| **F1: Content hash 驗證** | `expected_parent_hash` 比對 parent.state_hash（SHA-256 canonical JSON） | L181-196 |
| **F2: DB UNIQUE constraint** | `UNIQUE(session_id, version)` → IntegrityError | model.py:105 + L211-212 |

```python
new_hash = compute_state_hash(state_data)  # SHA-256(canonical_json)
if parent.state_hash != expected_parent_hash:
    raise StateConflictError("parent_hash mismatch")
session.add(snapshot)
try: await session.flush()
except IntegrityError as e:
    raise StateConflictError("concurrent insert: version=N already taken")
```

### B.2 Append-only enforcement
- ✅ 0005 migration 加 trigger 阻擋 UPDATE/DELETE（cleanup 試 DELETE 時被觸發回擋）
- ✅ `compute_state_hash` 用 `sort_keys=True, separators=(",",":")` 確保跨 process stable

### B.3 Conflict 處理
- ✅ `StateConflictError` 自定 exception，caller 可 catch 重試
- ⚠️ 注意：retry policy 在 `append_snapshot` 上層（caller 責任）；本身不做 retry

---

## Phase C — Runtime Race Test

### C.1 既有測試（`backend/tests/unit/infrastructure/db/test_state_race.py`）

- 測試強度：`asyncio.gather(worker(0), worker(1))` × `parametrize range(5)` = **僅 2 workers / 5 iterations**
- **建議補強**：增加 N=20-50 worker pytest case 至 CI（目前覆蓋偏弱）

### C.2 自寫 100-並發 race test（W1-4 補強）

**Setup**：tenant + user + session + parent snapshot v=1
**Race**：100 個 asyncpg connection 同時 INSERT v=2，jitter 0-3.5ms

```
Successes: 1, Conflicts: 99, HashMismatch: 0
Expected: 1 success, 99 conflicts
PASS
```

✅ **DB UNIQUE(session_id, version) 在 100-concurrent 下精確擋住 race**
✅ Append-only trigger 在 cleanup 階段同樣 fire（無法 DELETE without DISABLE TRIGGER）

---

## Phase D — 跨範疇

### D.1 旁路 / Override
- ❌ 無 model override tenant_id Column
- ❌ 無 nullable=True 漏網

### D.2 Migration vs ORM 一致性
- DB 反射 31 tables（含 messages/message_events 月份 partition）
- 所有有 tenant_id 的 21 tables 一致 `NOT NULL=True`
- 與 ORM models 預期 100% 對齐

---

## 結論

| 檢查項 | 評級 |
|---|---|
| TenantScopedMixin 覆蓋（A） | ✅ Pass |
| StateVersion 雙因子（B） | ✅ Pass |
| Runtime race（C，自寫 100-併發） | ✅ Pass |
| Migration 一致（D） | ✅ Pass |

---

## 修補建議（非阻塞，建議 Sprint 49.4 處理）

1. **既有 race test 強度偏低**：`test_state_race.py` 只 2 workers × 5 iter。建議增 N=20+ worker case 進 CI 防退化。
2. **Caller retry policy 文件化**：`append_snapshot` 上層 retry 策略目前在 docstring 隱含，建議明確寫到 17-cross-category-interfaces.md Contract for State Mgmt。
3. **`tools_registry` 全局表**：Sprint 49.4 多租戶工具上架時需確認是否要拆 `tools_registry_global` + `tools_registry_tenant`。

---

## 阻塞 Phase 50？

**❌ 否**。Sprint 49.2 + 49.3 ORM tenant 隔離 + State Version 雙因子鎖在 100-併發下行為符合 09-db-schema-design.md 與 multi-tenant-data.md 鐵律。可推進 Phase 50.1 (Orchestrator Loop)。
