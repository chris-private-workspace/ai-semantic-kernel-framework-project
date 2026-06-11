# V2 Audit W1-3 — Audit Log Hash Chain 完整性

**Audit 日期**: 2026-04-29
**Auditor**: Research Agent (read-only)
**Scope**: Sprint 49.3 audit_log hash chain (commits 6613642 / 4fec9fc)
**結論**: ⚠️ **CONCERNS** — chain 設計正確且 trigger 防護嚴格，但**無 verify 程式存在** = 篡改後無人偵測 = 部分 Potemkin

---

## 摘要

| 項目 | 結果 |
|------|------|
| Hash 演算法 | **SHA-256** (hashlib，✅ 強) |
| 是否真 chain（prev_hash 在 input） | ✅ **真 chain**（公式：`SHA256(prev_hash ‖ canonical_json(payload) ‖ tenant_id ‖ ts_ms)`） |
| Verify 程式存在 | ❌ **不存在**（codebase 無任何 chain 驗證 script / endpoint / scheduled job） |
| Chain 起始定義 | ✅ 清楚（`SENTINEL_HASH = "0" * 64`，per-tenant） |
| 獨立 SHA-256 重算與 stored 一致 | ✅ **3/3 rows match** |
| Chain link（prev_hash == prior curr_hash） | ✅ **3/3 OK** |
| 篡改偵測（UPDATE/DELETE/TRUNCATE） | ✅ Trigger 全部擋（W1-2 已驗證；本次重證） |
| **偽造偵測（INSERT 假 hash）** | ❌ **未被偵測** — 偽造 row id=39 留在資料庫無人察覺 |

---

## Phase A 靜態分析

### A.1 Schema + 計算邏輯
- **Migration**: `backend/src/infrastructure/db/migrations/versions/0005_audit_log_append_only.py`
- **ORM**: `backend/src/infrastructure/db/models/audit.py`
- **Helper**: `backend/src/infrastructure/db/audit_helper.py`
- 欄位：`previous_log_hash` (CHAR 64) + `current_log_hash` (CHAR 64) + `operation_data` (JSONB) + `tenant_id` (UUID) + `timestamp_ms` (BIGINT)
- 計算位置：**Application 層（Python）**，不是 DB trigger

### A.2 真 chain 判定
**Hash 公式**（從 `audit_helper.py:85-87` 抄出）：
```python
payload_json = json.dumps(operation_data, sort_keys=True, separators=(",", ":"))
base = f"{previous_log_hash}{payload_json}{tenant_id}{timestamp_ms}"
hashlib.sha256(base.encode("utf-8")).hexdigest()
```

判定：✅ **真 chain** — `previous_log_hash` 是 input 的第一個元件，篡改任一 row → 後續 row 全部 prev_hash mismatch。

`append_audit()` (lines 132-139) 透過 `SELECT current_log_hash WHERE tenant_id ORDER BY id DESC LIMIT 1` 抓 per-tenant chain head，正確隔離跨租戶污染。

### A.3 Verify 程式 — ❌ 缺失
- 全 codebase grep `verify.*chain | validate.*hash | verify_audit | check.*integrity | recompute.*hash` 命中：
  - **僅 1 個檔案：`audit_helper.py`**（含字串「prevents silent storage-layer tampering」於 docstring）
  - 沒有 `scripts/`、沒有 CLI、沒有 cron、沒有 endpoint、沒有 batch job
- ORM model docstring 第 23 行甚至明說 "Daily / batch verification (DBA process; **not in this sprint**) walks the chain" — 即 Sprint 49.3 規劃就已知缺，但**沒記入 49.4+ checklist**
- Test file `tests/unit/infrastructure/db/test_audit_append_only.py` 是 trigger test，不是 chain verify

### A.4 Chain 起始
- ✅ 明確：`SENTINEL_HASH = "0" * 64`（audit_helper.py:57）
- 第一筆 row：`previous_log_hash = SENTINEL_HASH`
- Schema 不允許 NULL（`nullable=False`），用 sentinel 固定值是好做法

---

## Phase B 獨立 SHA-256 重算

### B.1 / B.2 結果（3 row 全 match）

| ID | Stored curr_hash (前16) | Re-computed (前16) | Match | Chain link OK |
|----|------------------------|-------------------|-------|---------------|
| 36 | adfdafe709225f00 | adfdafe709225f00 | ✅ | ✅ |
| 37 | 1aa85caa22fc4c95 | 1aa85caa22fc4c95 | ✅ | ✅ |
| 38 | 90d1285381e8fdb7 | 90d1285381e8fdb7 | ✅ | ✅ |

獨立用 stdlib `hashlib.sha256` 在我自己的 ad-hoc script 重算（與 audit_helper.py 同公式但不 import 它），**3/3 完全一致**。公式可獨立重現，無黑魔法。

---

## Phase C 篡改 / 偽造偵測

### C.1 Trigger 物理層（再次驗證 W1-2）
- UPDATE：✅ blocked — `audit_log is append-only`
- DELETE：✅ blocked — 同上
- TRUNCATE：✅ blocked — STATEMENT-level trigger

連 `ipa_v2` superuser 都被擋（function 是無條件 RAISE EXCEPTION，不檢查 role）。**這是最強防護**。

### C.2 偽造 INSERT（**critical gap**）
測試：用合法 INSERT 寫一筆 row，但 `current_log_hash = "f"*64`（故意錯誤）。

- 結果：**INSERT 成功，row id=39 進入 audit_log，無任何 alarm**
- 預期：應該有 verify job 定期掃描 → recompute → flag mismatch
- 實際：**沒有任何程式會發現**

→ 攻擊者若取得 INSERT 權限（normal app role 即可，無需 superuser），可：
1. 偽造任意歷史事件（例如假 approval_granted）
2. 或在合法事件後串入「掩護」row 把調查者引向錯誤方向
3. Chain 自身仍可被外部驗證者抓到，但**沒人在驗** = Schrödinger 的 audit log

---

## 結論（逐項）

| 項 | 評定 |
|----|------|
| 真 chain（A.2） | ✅ 是真 chain（prev_hash 在 input，per-tenant 隔離） |
| Verify 程式（A.3） | ❌ **缺失**（Sprint 49.3 規劃明示 deferred 但未排入 49.4） |
| 重算一致（B.2） | ✅ 3/3 |
| Trigger 篡改防護（C.1） | ✅ UPDATE/DELETE/TRUNCATE 全擋 |
| 偽造 INSERT 偵測（C.2） | ❌ **無偵測**（無 verify job） |

整體：**設計正確，落地不完整**。Chain 結構與演算法是對的，但「chain 的價值在於有人定期重算」這環節被當成 Day-N+ 任務忽略，導致目前狀態：寫入端有完整性保證，但**讀取端 / 監控端沒有**。

---

## 修補建議（按優先序）

1. **🔴 P0：寫 chain verifier 並排入 Sprint 49.4 / 50.1**
   - 提供：(a) CLI script `scripts/verify_audit_chain.py` + (b) FastAPI internal endpoint `/admin/audit/verify` + (c) Daily cron 在 platform_layer
   - 邏輯：per-tenant 從第一筆 row 開始 walk，重算 SHA-256，每筆 row 比 stored curr_hash + prev_hash linkage
   - 失敗時：log critical + alert（不是 silent print）
   - 估時：4-6h（PoC of script 在本次 audit 已寫，可 fork）

2. **🟡 P1：在 ORM `__init__` 或 `before_insert` event 做即時 hash check**
   - 現在 `append_audit()` 是唯一正確路徑；若有 caller 繞過直接 `session.add(AuditLog(...))` 用錯的 hash，沒人擋
   - 加 SQLAlchemy `before_insert` listener：重算 hash 與 row.current_log_hash 比對；不一致 → IntegrityError
   - 這擋的是「program bug」不是「惡意」，但 defense-in-depth

3. **🟢 P2：在 14-security-deep-dive.md / 09.md 補上 verify SLO**
   - 「audit chain 應每 24h 完整 verify 一次；發現 mismatch 必須 P1 alert」
   - 寫進 Phase 49.4 observability 規劃

4. **🟢 P3：cleanup test data**
   - 本次 audit 留下 row id=36-39 在 audit_log（tenant_id=`aaaaaaaa-1111-2222-3333-444444444444`、operation 前綴 `w1_3_`、含 1 筆 forged）
   - **無法 DELETE（append-only 設計）** ← 這正是設計初衷
   - 建議：在 verifier P0 上線後，第一次 run 應預期報「1 個 mismatch」並標記 row 39 為 known-test-forgery
   - 或：drop 整個 test tenant（cascade delete）→ 連 tenants row 也會帶走 audit_log，但需 superuser 直接刪 tenants（FK ON DELETE CASCADE）

---

## 阻塞 Phase 50？

⚠️ **Soft block（不全擋）**

- 若 Phase 50 的 governance/HITL 範疇仰賴 audit log 為「不可否認證據」做合規 / 審計輸出 → **必須先補 verifier 才放行**
- 若 Phase 50 只用 audit log 做 debug / observability → **可放行**，但 Phase 50 結束前 verifier 必須上

---

## Critical findings (top 3)

1. **Hash chain 結構與演算法是真的**（非 fingerprint，per-tenant SHA-256，sentinel 起始） — 這是好消息
2. **完全沒有 verify 程式**（codebase 全 scan 0 命中），Sprint 49.3 規劃明知 deferred 卻未排進 49.4 → **Potemkin 風險**：寫得很安全，但無人查 = 等於沒查
3. **偽造 INSERT 攻擊面開放**：app role 即可寫入假 hash row 而不被當下偵測；唯一防線是「未來某天有人 walk chain」，但目前那天還沒被排程

---

**Audit Status**: ✅ Complete
**Next Audit**: W1-4 (ORM TenantScopedMixin + StateVersion 鎖)
