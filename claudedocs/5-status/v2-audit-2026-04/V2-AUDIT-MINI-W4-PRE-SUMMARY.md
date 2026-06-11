# V2 Verification Audit — mini-W4-pre 統籌總結

**Audit 區間**: 2026-05-02
**Sprint 範圍**: Phase 49.4 Day 3-5（OTel/pg_partman/Lint）/ Phase 51.0（Mock 企業工具）/ Phase 51.1（Tool Layer L3）/ Phase 51.2（Memory L3）
**Auditor**: Verification Audit team（4 個 read-only sub-audits 匯總）
**版本**: 1.0 — 決策性產出
**前序文件**: `V2-AUDIT-WEEK3-SUMMARY.md` / `V2-AUDIT-CLEANUP-SPRINT-TEMPLATE.md`

---

## 一句話結論

> **mini-W4-pre 揭露系統性紀律 pattern：3/4 audit 對象（49.4 Day 3-5 / 51.2 / 50.2 鏡像）共享『ABC + 元件交付完整、主流量呼叫鏈空懸』反模式，是 AP-4 Potemkin 變體（不是「結構在但無內容」，而是「結構在 + 內容完整、但 main flow 未連接」）。51.0/51.1 較健康但 51.1 含 critical security 缺陷（Windows 上 SubprocessSandbox 裝飾性，agent 實測 `os.listdir("C:/")` 從「sandbox」內成功列出 host fs）。累計覆蓋率 9/22 完整 audit + 1/22 部分 = 約 41%（從 W3 的 24% 提升）。52.2 PromptBuilder 啟動不阻塞但需 mindful：51.2 memory tools 主流量未接，PromptBuilder 若要查 memory 需自接 store ABC（不走 tools layer 那條路徑）。這是 V1 「audit 寫了沒人看 + 跨 sprint 整合無人 own」災難的早期重演升級版。**

---

## 1. 評分總表

| 審計項 | 風險等級 | 結果 | 證據強度 | 阻塞 52.2？ |
|-------|---------|-----|---------|-----------|
| W4P-1 49.4 Day 3-5 OTel/pg_partman/Lint | 中 | ⚠️ Concerns | **強**（OTel 浮動版本 grep 確認 + 5 處必埋點實際 2/5 + Adapter 0 個 `tracer.start_span` + pg_partman `create_parent()` 從 plan 偷砍為 ops runbook + 4 lint over-delivered） | 否 |
| W4P-2 51.0 Mock 企業工具 | 中 | ✅ Passed | **強**（mock_executor 真 dynamic seed.json + 19 tools 真整合 chat handler + e2e mock_patrol 真 multi-turn subprocess uvicorn + 22/0/0 in 4.25s） | 否 |
| W4P-3 51.1 Tool Layer L3 | 高 | 🟡 PASS WITH CAVEATS | **強**（agent 實測 sandbox bypass + `network_blocked` 是 `# noqa: ARG002 — doc-only knob` + JSONSchema 真強制 + PermissionChecker 3-dim 真攔截 + chat handler 3 hits ToolExecutor + 51 tests in 1.87s） | 否（**但 53.3 阻塞**）|
| W4P-4 51.2 Memory L3 | 高 | ⚠️ Concerns | **強**（5 ORM tables 真分離 + 64 處 tenant_id 強制 + chat router 0 hit memory_search/memory_write + memory_tools handler tenant_id from arguments W3-2 鏡像 + tests 69/69 in 0.36s 全 MagicMock） | 否（**但需 mindful**）|

**整體分**：1 ✅ + 1 🟡 + 2 ⚠️。mini-W4-pre 是「個別範疇實作品質中上、跨 sprint 主流量整合系統性失靈」的決定性證據。

---

## 2. 系統性 Pattern 揭露（最重要 section）

### 2.1 Pattern 名稱：「ABC Potemkin」/「Main Flow Integration Gap」

W4P-1 audit 內 agent 自己揭露此 pattern。3 個案例同形：

| # | Sprint | ABC + 元件 | 主流量呼叫鏈 | grep 證據 |
|---|--------|-----------|-------------|---------|
| 1 | W3-2 50.2 | `Depends(get_current_tenant)` infrastructure ✅ + tenant middleware ✅ | chat router 0 個 `Depends` import / 0 個 `tenant_id` filter | `backend/src/api/`：`tenant_id` 1 hit（main.py），chat router **0** |
| 2 | W4P-1 49.4 Day 3 | OTel ABC ✅ + Tracer 類別 ✅ + 7 個必埋 metrics 定義 ✅ + TraceContext dataclass ✅ | Adapter 0 個 `tracer.start_span` / API entry 0 個 `TraceContext.create_root()` | adapter 8 hits `trace_context` 變數，**0** hits `tracer.start_span` |
| 3 | W4P-4 51.2 | 5 層 Memory ORM tables migration 0007 ✅ + 19 memory tools 註冊 registry ✅ + Layer 級 tenant_id 強制 64 處 ✅ + ChatClient ABC 抽取真用 ✅ | chat router 0 hit memory_search/memory_write tools | chat router 對 memory_tools handler **0** 呼叫，memory tools 寫了沒人用 |

### 2.2 Pattern 形成原因（推測）

1. **每個 sprint 視「整合」為下一 sprint 的事**：49.4 Day 3 交付 OTel ABC ✅ → 50.2 沒接 → 51.x 沒接 → 52.2 也不會接（除非 process fix）
2. **「Sprint Done」定義過於寬鬆**：ABC 完成 + unit test 通過 = sprint done。沒人問「主流量真的用了嗎？」
3. **跨 sprint 整合驗收 gate 缺失**：W3 process fix #1-#5 已涵蓋「audit ticket / Sprint Carryover section / Audit Debt 段落」，但**沒有「主流量整合驗收」獨立 gate**

### 2.3 對 V2 的意義（最危險訊息）

- **比單點偷砍 scope（W3-2 critical 1/2）更嚴重**：是**系統性紀律問題**
- **AP-4 Potemkin 變體升級**：原 AP-4 是「結構在但無內容」；新變體是「結構在 + 內容完整、但 main flow 未連接」更難察覺，因為單看 sprint deliverable 全 ✅
- **V1 災難早期重演升級版**：原 V1 是「audit 寫了沒人看」；本次是「**每 sprint 自驗 ✅，跨 sprint 整合 ❌**」— 成本是把 V1 災難移到更深的層級

---

## 3. 51.1 Critical Security 偏離（次重要）

### 3.1 SubprocessSandbox 在 Windows 上裝飾性

**W4P-3 agent 實測證據**：
- 從「sandbox」內成功 `os.listdir("C:/")` 列出 host fs（Windows）
- `network_blocked` 參數是 `# noqa: ARG002 — doc-only knob`（裝飾性 flag）
- POSIX 用 `resource.setrlimit()`，Windows skip（無對應 API）
- python_sandbox tool 在 production Windows 部署 = **RCE vector**

### 3.2 緊急度判定

| 問題 | 阻塞 52.2？ | 阻塞 53.3 Guardrails？ | 建議 |
|------|-----------|---------------------|------|
| Windows sandbox bypass | 否（範圍不含 sandbox） | **是**（HITL approval 仰賴 sandbox 真隔離；guardrails policy 在偽 sandbox 上失效） | 升 P0 至 cleanup sprint，或開獨立 53.3-pre sprint |
| `network_blocked` doc-only | 否 | 是 | 同上 |

CARRY-022（Docker isolation）已標但**無 sprint 排程**，必須在 53.3 之前落地。

### 3.3 Production 暫禁建議

在 Docker isolation 落地前，python_sandbox tool 應在 production deployment manifest 標 `disabled_in_production: true`，僅 dev/staging 可用。

---

## 4. 累計 audit 覆蓋率

| Phase | Sprint | 已 audit | 來源 |
|-------|--------|---------|------|
| 49 | 49.1 | ✅ 完整 | W1-1 baseline |
| 49 | 49.2 | ✅ 完整 | W1-4 contracts |
| 49 | 49.3 | ✅ 完整 | W1-2 RLS + W1-3 audit hash |
| 49 | 49.4 Day 1-2 | ✅ 完整 | W2-1 adapter + W2-2 worker |
| 49 | 49.4 Day 3-5 | ✅ 完整 | **W4P-1**（本批次新增）|
| 50 | 50.1 | ✅ 完整 | W3-1 |
| 50 | 50.2 | ✅ 完整 | W3-2 |
| 51 | 51.0 | ✅ 完整 | **W4P-2**（本批次新增）|
| 51 | 51.1 | ✅ 完整 | **W4P-3**（本批次新增）|
| 51 | 51.2 | ✅ 完整 | **W4P-4**（本批次新增）|
| 52 | 52.1 | ⏳ 部分 / 進行中 | 未 audit |
| 52 | 52.2 | ❌ 未啟動 | — |
| 53-55 | (TBD) | ❌ 未開始 | — |

**累計**：
- W3 結束時：6/22 完整 = **27%**（修正：原 W3 summary 寫 24%，實為 5/22 = 22.7% 約 24%）
- mini-W4-pre 後：**10/22 完整 = 約 45%**（從 24% 提升 21 個百分點）
- 任務 prompt 預估 41% 較保守；實算 45%（含 49.4 Day 1-2 已在 W2 算過）

---

## 5. 對 52.2 PromptBuilder 啟動的影響

### 5.1 結論

> ✅ **不阻塞 52.2 啟動**，但 52.2 plan 必須 mindful 三條紀律以避免重蹈系統性 pattern。

### 5.2 啟動前必確認

| 項目 | 為何 mindful | 52.2 plan 應補 |
|-----|------------|---------------|
| 51.2 memory_tools handler tenant_id 不可信（從 ToolCall.arguments，W3-2 鏡像）| PromptBuilder 若走 memory_tools 這條路徑會繼承同樣漏洞 | **PromptBuilder 直接呼叫 memory store ABC**（layer 級 tenant_id 強制 ✅），不走 tools layer 中介 |
| 49.4 OTel adapter 主流量 0 個 `tracer.start_span` | 上游沒埋，PromptBuilder 不能假設 trace_context 已 propagate | **PromptBuilder.build() 自己 emit `tracer.start_span`**，獨立 contribute observability span |
| W3-2 chat handler 0 multi-tenant 隔離（cleanup sprint 才修）| PromptBuilder 整合測試若仍走 chat handler 會繼承漏洞 | **52.2 主流量整合 test 必須 expect cleanup sprint 已落地的 tenant context**，否則 fail fast |

### 5.3 51.1 整合健康（PromptBuilder 安全使用）

51.1 ToolExecutor + PermissionChecker + JSONSchema 真實落地，chat handler 真呼叫（3 hits），**PromptBuilder 被 ToolExecutor 呼叫的這條路徑可信**。但 sandbox 不可信（不影響 PromptBuilder，影響 53.3）。

---

## 6. 對 cleanup sprint 4 P0 的補充（升級至 7-8 P0）

### 6.1 原 cleanup template 的 4 P0

1. chat router multi-tenant 隔離（W3-2 critical 1）
2. TraceContext propagation at chat handler（W3-2 critical 2）
3. verify_audit_chain.py + cron + alert（W1-3）
4. JWT 取代 X-Tenant-Id header（W1-2）

### 6.2 mini-W4-pre 升級候選 P0

| # | 來源 | Item | Effort | Owner | 阻塞 |
|---|------|------|--------|-------|------|
| 5 | W4P-1 | **OTel adapter 層補 `tracer.start_span`**（是 P0 #2 真正 root cause；TraceContext 沒人發 span 等於 propagate 也徒勞）| 1 day | Backend / Observability | 53.x distributed tracing |
| 6 | W4P-1 | **OTel SDK 版本鎖定 `==1.22.0`**（per `observability-instrumentation.md`，目前 `>=1.27,<2.0` 違反 rule）| 30 min | Backend | — |
| 7 | W4P-3 | **SubprocessSandbox Windows Docker isolation**（CARRY-022 升 P0）| 3-5 days | Platform / Security | **53.3 強制阻塞** |
| 8 | W4P-4 | **memory_tools handler 改 ExecutionContext-based tenant 注入**（W3-2 鏡像；不能讓 LLM caller 控制 tenant_id）| 1 day | Backend / Memory | 53.3 |

**修正後 cleanup sprint**：4 P0 → **8 P0**，est. 5-7 days → **10-14 days**。

### 6.3 P1 補充（從 mini-W4-pre）

- W4P-1：pg_partman `create_parent()` 從 plan 偷砍為 "ops runbook" → 補回為 migration 自動執行
- W4P-3：tools_registry 多租戶空白（W1-4 P2 carryover NOT addressed）
- W4P-3：2 broken tests（test_memory_placeholder regression after 51.2）
- W4P-4：49.3 RLS 13 tables 紅隊測試 scope 擴至 memory 5 tables（不只 conversations/sessions）
- W4P-4：69/69 tests 全 MagicMock（AP-10 mock vs real）→ 補 real DB integration test

---

## 7. Process Drift 進階判斷

### 7.1 W3 process fix 5 條已不夠

W3-0 揭露 7/8 P1 dropped 是「audit findings 沒進 sprint planning」單點問題。mini-W4-pre 揭露**更深層 pattern**：

> **不是「audit findings 沒進 sprint」，而是「跨 sprint 主流量整合」這個維度根本沒有 sprint 負責。**

具體：
- 49.4 Day 3 OTel ABC 完成 ✅ → 50.2 沒接 ❌ → 51.x 沒接 ❌ → audit 才發現
- 51.2 Memory tools 註冊 ✅ → chat router 沒呼叫 ❌ → audit 才發現
- 每個 sprint retrospective 自己 ✅ 但端到端 ❌（cross-sprint blindspot）

### 7.2 建議新增 process fix #6

> **#6: Sprint Retrospective「主流量整合驗收」必答題**
>
> 每個 sprint 結束 retrospective 必須回答：
> 1. 本 sprint 交付的元件，主流量是否真的調用？（grep 證據）
> 2. 還是只有 ABC + unit test 完成？
> 3. 若僅後者，整合的 owner sprint 是哪一個？已開 ticket 嗎？
>
> 答覆需 commit 進 retrospective.md，跨 sprint review 必查。

### 7.3 W4 audit 啟動條件擴大

除原 cleanup sprint + 52.2 audit，**新增 mandatory audit phase**：

> **「跨 sprint 主流量整合驗收」獨立 audit**（每 5 sprint 一次）
>
> Scope：grep `chat handler / api entry / main flow` 對前 5 sprint 交付元件的 import + 呼叫覆蓋率，產出 integration coverage report。

---

## 8. Anti-Pattern 累計（mini-W4-pre 後）

| AP | W1+W2 | W3 | W4P | 累計 | 變化 |
|----|-------|-----|-----|------|------|
| AP-1 Pipeline 偽裝 Loop | 0 | 0 | 0 | 0 | 持平 |
| AP-2 Side-Track Code | 0 | 1 | 0 | 1 | 持平 |
| AP-3 Cross-Directory Scattering | 1 | 0 | 0 | 1 | 持平 |
| AP-4 Potemkin Features | 1.5 | 0.5 | **3+**（系統性 pattern！）| **5+** | **🔴 翻倍** |
| AP-5 PoC Accumulation | 0 | 0 | 0 | 0 | 持平 |
| AP-6 Hybrid Bridge Debt | 0 | 0 | 0 | 0 | 持平 |
| AP-7 Context Rot | 0 | 0 | 0 | 0 | 持平（52.1 才上）|
| AP-8 No PromptBuilder | 0 | 0 | 0 | 0 | 持平（52.2 才上）|
| AP-9 No Verification | 0 | 0 | 0 | 0 | 持平（54.1 才上）|
| AP-10 Mock vs Real | 0 | 1 | 1（W4P-4 全 MagicMock）| **2** | +1 |
| AP-11 Naming Suffix Legacy | 0 | 0 | 0 | 0 | 持平 |

**累計 9-10 個 AP 違反**（從 W3 後 5.5 個翻倍）。**AP-4 系統性 pattern 是新識別的最危險訊號**。

---

## 9. 給專案 owner 的建議行動（5 條）

1. **🔴 緊急升級 cleanup sprint**：從 4 P0 → **8 P0**（含 OTel adapter span / OTel 版本鎖 / Windows sandbox Docker isolation / memory_tools tenant 注入）；est. 5-7 days → **10-14 days**。**不升級不准進 53.x**。

2. **🔴 新增 process fix #6**：Sprint retrospective「主流量整合驗收」必答題，每 sprint commit 進 retrospective.md。**這是真正的 V1 災難止血**。

3. **🟡 52.2 plan 補三條紀律**：
   - PromptBuilder.build() 自 emit tracer span（不假設上游已埋）
   - PromptBuilder 直接呼叫 memory store ABC（不走 memory_tools handler）
   - 主流量整合 test（chat handler 真呼叫 PromptBuilder）

4. **🟡 W4 audit 啟動條件擴大**：除 cleanup + 52.2，必含「跨 sprint 主流量整合驗收」獨立 audit phase。

5. **🟠 51.1 SubprocessSandbox 即時警示**：production deployment manifest 標 `python_sandbox.disabled_in_production: true`，直至 Docker isolation 落地（53.3 前必須）。

---

## 10. 最關鍵 1 行決策建議

> **mini-W4-pre 揭露的「ABC + 元件交付完整、主流量呼叫鏈空懸」系統性 pattern 比 W3 的單點偷砍更危險，因為單看每 sprint 都 ✅、但端到端 ❌；必須在進 52.2 前同步落地：(a) cleanup sprint 升級至 8 P0 / 10-14 days、(b) process fix #6「主流量整合驗收」必答題、(c) 52.2 PromptBuilder plan 三條 mindful 紀律——否則 V1 災難會以「每 sprint 自驗 ✅、跨 sprint 整合 ❌」的更深層級重演，6 個月後驚覺整個 V2 codebase 都是 ABC Potemkin。**

---

**Auditor 簽核**: Verification Audit team
**完成時間**: 2026-05-02
**下一次審計**: cleanup sprint 落地驗收 + 52.2 完成 audit
**相關文件**:
- `claudedocs/5-status/V2-AUDIT-WEEK3-SUMMARY.md`
- `claudedocs/5-status/V2-AUDIT-CLEANUP-SPRINT-TEMPLATE.md`
- `claudedocs/5-status/V2-AUDIT-W4P-1-PHASE49-4-D3-5.md`
- `claudedocs/5-status/V2-AUDIT-W4P-2-PHASE51-0.md`
- `claudedocs/5-status/V2-AUDIT-W4P-3-PHASE51-1.md`
- `claudedocs/5-status/V2-AUDIT-W4P-4-PHASE51-2.md`
