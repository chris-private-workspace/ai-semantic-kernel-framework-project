# V2 Verification Audit — Week 1 統籌總結

**Audit 區間**: 2026-04-29
**Sprint 範圍**: Phase 49.1 / 49.2 / 49.3（49.4 Day 1-2 已 done，Day 3+ 進行中，**未列入 Week 1 審計**）
**Auditor**: Verification Audit team（5 個 read-only sub-audits 匯總）
**版本**: 1.0 — 決策性產出

---

## 一句話結論

> **Week 1 審計：4 項目中 3 ✅ + 1 ⚠️。V2 Phase 49.1-49.3 多租戶安全與 single-source 鐵律真實守住，無 V1 自欺反模式。唯一 concern 是 audit hash chain 缺 verify 程式（典型 AP-4 Potemkin），需在 Phase 50 之前補。不阻塞 Phase 50 啟動，但需排程修補 P1 三項。**

---

## 1. 評分總表

| # | 審計項 | 風險等級 | 結果 | 證據強度 | 阻塞 Phase 50？ |
|---|-------|---------|------|---------|----------------|
| W1-1 | `_contracts/` 跨 sprint 一致性 | 5 | ✅ Passed | **強**（39 imports 跨 25 檔；24/24 + 22/22 對齐 17.md）| 否 |
| W1-2 | RLS + tenant_id 0-leak | 5 | ✅ Passed | **極強**（live PG + asyncpg cross-tenant 試讀重疊 0 rows + pytest 13/0/0）| 否 |
| W1-3 | Audit hash chain 完整性 | 5 | ⚠️ Concerns | **部分**（chain 設計強且重算 3/3 match，但 verify 程式缺）| Soft block（依用途）|
| W1-4 | ORM TenantScopedMixin + StateVersion | 5 | ✅ Passed | **強**（13/13 mixin + 真雙因子鎖 + 100 並行 race 1/99 完美）| 否 |

**整體分**：3.5/4 ✅。Week 1 是「安全與架構基石」最重審計區段，主流量沒有發現 V1 級反模式。

---

## 2. 關鍵正面證據（建立信心）

5 點抽自 4 份報告中**最有說服力的證據** — 證明 Phase 49 是真實實作，反 V1 自欺反模式：

1. **紅隊測試主動切到 NOLOGIN `rls_app_role`（無 BYPASSRLS）執行**（W1-2）
   業界正確做法 — 不是用 `ipa_v2` superuser 自欺通過。Owner 角色（即使 BYPASSRLS=true）無法繞過 `FORCE ROW LEVEL SECURITY`。

2. **手動 asyncpg 跨 tenant 試讀，重疊 0 rows**（W1-2 B.3）
   `tenant_a sees 1` / `tenant_b sees 1` / `重疊=0`；fail-safe（無 SET LOCAL → 0 rows）；WITH CHECK 擋偽造 INSERT；UUID cast 擋 SQL injection。**6 個攻擊向量全擋**。

3. **StateVersion 真雙因子鎖（content hash + DB UNIQUE）+ 100 並行精確 1 succeed / 99 conflicts**（W1-4 C.2）
   非 advisory lock / 非 row-level lock — 是 schema constraint + content addressable。即使 100 個 asyncpg conn 同時打，DB 物理層擋住。

4. **`_contracts/` 0 NotImplementedError / 0 TODO / 0 FIXME；24+22 全對齐 17.md**（W1-1 §5）
   single-source 鐵律真實守住；`TraceContext` 滲透 13 處 `_abc.py` 證實範疇 12 cross-cutting 規範被遵守；4 個 ORM 同名屬合理 namespace separation（不算違規）。

5. **Append-only triggers 連 superuser 都擋**（W1-2 + W1-3 重證）
   `audit_log` UPDATE/DELETE/TRUNCATE 三 op 全 BEFORE-trigger RAISE；`state_snapshots` TRUNCATE 同擋。Trigger function 無條件 RAISE，不檢查 role — **最強防護層**。

---

## 3. ⚠️ Concerns 詳細分析（W1-3）

唯一未通過項，必須詳述。

### 3.1 性質：典型 AP-4 Potemkin Feature

**設計層完整**（✅ 全套）：
- SHA-256 真 chain：公式 `SHA256(prev_hash ‖ canonical_json(payload) ‖ tenant_id ‖ ts_ms)`，prev_hash **在 input** 才算真 chain
- Per-tenant 隔離：`SELECT current_log_hash WHERE tenant_id ORDER BY id DESC LIMIT 1` 抓 chain head
- Genesis sentinel：`"0"*64`（CHAR 64 NOT NULL，不允許 NULL 鑽洞）
- Append-only trigger：UPDATE / DELETE / TRUNCATE 三層擋
- 獨立 SHA-256 重算 stored 一致：W1-3 Phase B 用 stdlib hashlib 在 ad-hoc script 重算 3 row，**3/3 完全對上**

**執行層空殼**（❌ 缺）：
- **無 verify job 在跑** — codebase 全 grep `verify.*chain | validate.*hash | recompute.*hash`，**0 命中**
- 無 CLI script / FastAPI endpoint / cron / batch — 寫了沒人驗
- W1-3 agent **實證可寫假 hash row**（id=39, `curr_hash="f"*64`）合法 INSERT 入庫，**無任何 alarm**

### 3.2 影響評估（依用途分支）

| Audit log 用途 | Phase 50 啟動是否需先修 |
|--------------|----------------------|
| 僅 debug / observability | ❌ 可放行（建議 Phase 50 結束前補）|
| Governance / HITL「不可否認證據」（spec 預期） | ✅ **必須先補**才能上 prod |

### 3.3 自承延後但未排程

ORM model 第 23 行 docstring 寫 "Daily / batch verification (DBA process; **not in this sprint**) walks the chain"。
即 Sprint 49.3 規劃就**已知缺**，但**未排入 49.4 也未排 50.x checklist**。

→ **這是規劃漏洞，不是技術錯誤**。設計圖完整，但施工未閉環就提前驗收。

---

## 4. 修補項目（按優先序）

### P0（必修，阻塞）— 0 項

無。Week 1 沒有發現必須立即停工的問題。

### P1（高優，須在 Phase 50 啟動前 / 啟動初）— 3 項

| # | Item | 來源 | Sprint | Effort | Owner | 為何 P1 |
|---|------|------|--------|--------|-------|--------|
| 1 | `scripts/verify_audit_chain.py` + daily cron + alert | W1-3 | 49.4 收尾 / 新增 49.5 | 2-3 days（agent 已驗 PoC 邏輯可行）| DBA / SRE | governance/HITL「不可否認證據」前提；不補則 audit log 等於 Schrödinger |
| 2 | JWT 整合替換 `X-Tenant-Id` header | W1-2 P1 carryover | 49.4+ 或 50.1 | 1-2 days | Backend / Identity | dev 可接受；prod 必換否則 trivial spoof |
| 3 | 刪除舊 stub `backend/src/middleware/tenant.py` | W1-2 P2 carryover | 50.1 cleanup | < 1 hour | Backend | 與 `platform_layer/middleware/tenant_context.py` 並存有混淆風險 |

### P2（中優，列入 backlog）— 4 項

| # | Item | 來源 | Sprint | 為何 P2 |
|---|------|------|--------|--------|
| 4 | ORM ↔ contract 轉換 helper（`to_contract` / `from_contract`）| W1-1 | 50.1 Day 1 | 各範疇自寫必撞 drift bug；範疇 7 Reducer/Checkpointer 直接受影響 |
| 5 | 強化 `test_state_race.py`（2 workers×5 iter → ≥ 20 workers×50 iter）| W1-4 | 49.4 Day 4 末 / 50.1 | 當前測試強度偏弱（手動 100 並行已過，但 CI 未含）|
| 6 | 17.md Contract 補 `append_snapshot` retry policy | W1-4 | 49.4 docs 收尾 | 文件 gap；retry 隱含於 docstring 應顯式 |
| 7 | `tools_registry` 全局表多租戶設計評估（split global/tenant？）| W1-4 | 51.1 Tool Layer | 49.4 多租戶工具上架時可能衝突 |

### P3（低，記錄即可）— 2 項

- W1-3 Test 殘留：`audit_log` 留 4 row（id 36-39，tenant `aaaa...4444`），含 1 forged。append-only 設計**故意無法 DELETE**。當 verify 程式上線時作 known baseline 用，不強制清。
- W1-2 Qdrant AV-6 為純邏輯測試（無 real Qdrant），Sprint 51.2 Memory 範疇實作後加真連測試。

---

## 5. Test 資料殘留處理決策

W1-3 audit 過程留下：
- Table: `audit_log`
- Tenant: `aaaaaaaa-1111-2222-3333-444444444444`
- Rows: id 36-39（含 1 個 `current_log_hash="f"*64` forged row）
- 移除狀態：**故意保留**（append-only 設計，連 DELETE 都被 trigger 擋）

**決策**：
- 不強制清（破壞 append-only 等於繞過設計初衷）
- P1 #1 verifier 上線後，第一次 run 應**預期**報「1 mismatch in tenant aaaa...4444」並標記 row 39 為 known-test-forgery baseline
- 替代清法：drop `tenants` row CASCADE（需 superuser），但連帶刪 audit_log 違反原則，**不建議**

---

## 6. Phase 50 啟動判定

**結論**：✅ **不阻塞**。但需在 Phase 50.0 / 50.1 啟動初追蹤完成 P1 三項。

**論據**：
- W1-1 / W1-2 / W1-4 三項 ✅，Phase 49 核心架構承諾真實守住（single-source / 多租戶隔離 / 鎖機制）
- W1-3 ⚠️ 是「設計完整但執行未閉環」，不是基礎錯誤；可在 Phase 50.x 並行修補
- 無 V1 級自欺反模式（pipeline 偽裝 loop / Potemkin feature 結構 / cross-directory 散落 / mock-only 測試），都通過反模式檢查

**建議節奏**：
1. 49.4 Day 3-5 期間 **同步**啟動 P1 #1（write `verify_audit_chain.py` + cron）
2. 開新 sprint 49.5（或併 50.0）做 P1 三項收尾，預估 1 week
3. 然後正式啟 Phase 50.1 Orchestrator Loop

---

## 7. Audit 範圍與限制

**已審**（Phase 49.1 / 49.2 / 49.3 完整 + 49.4 Day 1-2 部分）：
- ✅ `_contracts/` 33 型別 / 22 LoopEvent
- ✅ 13 ORM models + TenantScopedMixin + StateVersion
- ✅ 13 表 RLS policies + tenant_context middleware + append-only triggers
- ✅ Audit hash chain 結構與重算

**明示未審**（後續 Week 排程）：
- ❌ 49.4 Day 1 adapters/azure_openai 完整 contract test → **Week 2**
- ❌ 49.4 Day 2 worker queue spike + Temporal 決策報告 → **Week 2**
- ❌ 49.4 Day 3 OTel / Tracer ABC / 7 metric 集合 → **Week 2**
- ❌ 49.4 Day 4 pg_partman + Dockerfile + tool_calls.message_id FK 決策 → **Week 3**
- ❌ 49.4 4 lint rules（cross-category / LLM neutrality / asyncio / type hints）→ **Week 3**
- ❌ 49.1 Day 4 frontend Vite skeleton → **後續**
- ❌ 49.1 Day 5 CI pipeline 真實觸發效果 → **後續**

---

## 8. 給專案 owner 的建議行動（可直接列入下次 standup）

1. **派人寫 `scripts/verify_audit_chain.py`** + 排 daily cron + 接 P1 alert（W1-3 P1 #1；2-3 days；DBA / SRE owner）
2. **開 49.5 收尾 sprint**（或併 50.0）做 P1 三項清掃；不開則 Phase 50 仍可啟，但 P1 #1 必跟到 50.1 結束前
3. **JWT extraction 路徑**從 `X-Tenant-Id` header 替換（W1-2 P1）；prod deploy 前 hard requirement
4. **Phase 50.1 Day 1 開工首日**加上 ORM↔contract conversion helper（W1-1 P2 #4）— 否則範疇 7 Reducer 直接撞 drift
5. **W2 audit 排程確認**：49.4 Day 1-4（Adapters / Worker Queue / OTel / Lint）四大區塊一週內審完，給出 Phase 50 啟動最終放行

---

## 9. 最關鍵 1 行決策建議

> **Phase 50 可啟，但 P1 #1（audit chain verifier）必須 Phase 50 結束前上線；governance / HITL 範疇若先到，須阻塞至此 verifier 完成。**

---

**Auditor 簽核**: Verification Audit team
**完成時間**: 2026-04-29
**下一次審計**: Week 2（49.4 Day 1-3：Adapters / Worker Queue / OTel）
**相關文件**:
- `claudedocs/5-status/V2-AUDIT-BASELINE-20260429.md`
- `claudedocs/5-status/V2-AUDIT-W1-CONTRACTS.md`
- `claudedocs/5-status/V2-AUDIT-W1-RLS.md`
- `claudedocs/5-status/V2-AUDIT-W1-AUDIT-HASH.md`
- `claudedocs/5-status/V2-AUDIT-W1-ORM-LOCK.md`
