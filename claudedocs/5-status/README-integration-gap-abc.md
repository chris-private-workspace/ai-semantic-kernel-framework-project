# A+B+C 整合缺口分析 — README Index

**Purpose**: 索引 2026-05-31~06-01 完成的「整合缺口盤點」16 份核心分析（A 接線缺口 6 + B 優化 4 + C 研究 5 + 1 份 A+B+C 總 capstone），附每項當前狀態（A 區更新至 Sprint 57.73；B/C 截至 57.70）。
**Category / Scope**: Status / Integration-gap inventory (Area A/B/C)
**Created**: 2026-06-02
**Last Modified**: 2026-06-03
**Status**: Active

> **Modification History**
> - 2026-06-03: Area A status synced to Sprint 57.73 (A-4 / A-5 / A-6 rows + 剩餘 line + §當前對齊摘要 addendum) — A 區主 slice 全 ship，僅 4 個 Phase-2/deferred AD 餘留；C-11 real-LLM cost-ledger row-count leg now green (process-state resolved, PR #238)
> - 2026-06-02: Initial creation — index 16 core + 2 supporting docs；status snapshot post-Sprint 57.70

---

## 這批盤點在做什麼

把專案在「主流量接線之外」的所有已知缺口，一次盤成 **15 項**（A 6 + B 4 + C 5），每項一份分析報告，再用一份總 capstone 串起來 → 共 **16 份核心文件**。全部存放於本目錄 `claudedocs/5-status/`（無子資料夾，靠檔名前綴區分）。

**核心洞察（capstone）**：多數缺口是「**已建好沒接通**」或「**有意 interim debt**」，真正從零做的極少。15 項收斂成 **兩條鑰匙鏈**：

- **鑰匙鏈 ①｜real-LLM 上線束** — 鑰匙 = **C-11**（A 區所有 wiring 的真實驗收前提）
- **鑰匙鏈 ②｜billing 正確性束** — **B-7 + B-8 + C-15**（cost_ledger 雙扣 / budget 失效）

---

## Area A — Loop 接線缺口（6 份）

> 「功能蓋好了，但沒接上 agent loop 主流量」。進度最快，已近收尾。

| ID | 主題 | 檔案 | 狀態（至 57.70） | Sprint |
|----|------|------|------------------|--------|
| A-1 | Cat 3 Memory loop 注入 | `cat3-memory-loop-injection-analysis-20260531.md` | ✅ T1/T2 shipped | 57.64 / 57.65 |
| A-2 | Cat 5 PromptBuilder（拱心石） | `cat5-promptbuilder-loop-injection-analysis-20260531.md` | ✅ T1/T2 shipped | 57.64 / 57.65 |
| A-3 | Cat 11 Subagent / HANDOFF | `cat11-handoff-loop-injection-analysis-20260531.md` | ✅ A-3a + A-3b shipped | 57.64 / 57.68-70 |
| A-4 | Cat 12 Loop Tracer | `cat12-loop-tracer-analysis-20260531.md` | ✅ Tier 0+1 shipped（Tier 2 Jaeger 匯出 → Area-C/DevOps）| 57.71 |
| A-5 | Events → SSE | `cat-events-to-sse-analysis-20260531.md` | ✅ A-5a/b/c shipped（Inspector **Tree** tab；Trace/Memory tabs → Phase-2 AD）| 57.66 / 57.67 / 57.72 |
| A-6 | 前端真資料 wiring | `frontend-real-data-wiring-analysis-20260531.md` | 🟡 A-6a/b shipped（partial；stats + memory ops-history deferred）| 57.73 |

**A 區剩餘**（截至 57.73；主 slice 已全 ship，以下皆 Phase-2/deferred AD）：A-5c 的 **Trace/Memory tab**（`AD-ChatV2-Inspector-Trace-Phase2` / `AD-ChatV2-Inspector-Memory-Phase2`，依賴 span / `memory_accessed` 走 SSE）、A-6a 的 **stats 聚合端點**（`AD-AdminTenants-Stats-Aggregate-Endpoint`）、A-6b 的 **memory ops-history backend**（`AD-Memory-OpsHistory-Backend`）；A-4 Tier 2 真 Jaeger 匯出歸 Area-C/DevOps。

---

## Area B — 優化 / 移除冗餘（4 份）

> 釐清「已建好沒接通 / 有意 debt / 已過時前提」。目前只動了 B-10。

| ID | 主題 | 檔案 | 狀態（至 57.70） |
|----|------|------|------------------|
| B-7 | Cat 8 ErrorBudget Redis wiring | `cat8-errorbudget-redis-wiring-analysis-20260531.md` | ❌ 未排程（另揪出 `handler.py:218` 每請求 new `InMemoryBudgetStore` → budget 連單實例都失效）|
| B-8 | Verification 預設開啟 | `cat10-verification-default-enable-analysis-20260601.md` | ⏸️ 有意 deferred（3 個 launch-blocker；維持 `AD-Cat10-Wire-1-Production`）|
| B-9 | Mockup re-point 真實狀態 | `b9-mockup-repoint-status-analysis-20260601.md` | ✅ 大部分完成（22/22 PARITY）· 剩 4 條二階債未排程 |
| B-10 | verifier_factory 去留 | `cat10-verifier-factory-disposition-analysis-20260531.md` | ✅ 已刪除（REFACTOR-006）|

---

## Area C — 研究 / 分析（5 份）

> 需研究釐清真實狀態，或需外部輸入才能動工。全為純研究，尚無實作。

| ID | 主題 | 檔案 | 狀態（至 57.70） |
|----|------|------|------------------|
| C-11 | real-LLM e2e 驗證 | `c11-real-llm-e2e-analysis-20260601.md` | ⭐ gate 早建好（57.6）· 缺 3 個 Azure Secrets · **零 code、capstone 最高優先** |
| C-12 | IAM Block B/C（invites/註冊/MFA） | `c12-iam-block-bc-analysis-20260601.md` | 前端已 ship · 後端有意缺（Phase 58）|
| C-13 | 缺核心頁 agents / workflows | `c13-agents-workflows-pages-analysis-20260601.md` | `agents` 改名 + 57.70 補 catalog 後端 · `workflows` 仍全缺 |
| C-14 | 企業合規軸（SOC2/PDPA/CRA/AI Act） | `c14-compliance-axis-analysis-20260601.md` | 程式 0% · 地基齊（WORM audit + hash chain + RLS + PIIRedactor）|
| C-15 | DevOps IaC/DR + Data platform | `c15-devops-data-platform-analysis-20260601.md` | Bicep IaC 已有 · DR/Outbox/analytics 缺（**cost_ledger 雙扣風險**）|

---

## 總 Capstone（第 16 份）

| 檔案 | 角色 |
|------|------|
| `integration-gap-capstone-abc-20260601.md` | 串起 A+B+C 15 項 → 兩條鑰匙鏈 + 整體優先序 + 最短交接 |

### Capstone 建議優先序

1. **⭐1 C-11** 啟用 real-LLM（零 code，只缺 Azure secrets）
2. **拱心石 bundle**：A-2 T1 + A-1 T1 + A-3a
3. **billing 正確性 spike**：B-7 + B-8 + C-15（cost_ledger）
4. schema codegen + 視覺 CI（A-5b）
5. tracer（A-4）/ admin-tenants 重掛（A-6a）
6. C-12 invites / C-13 agents 後端
7. 後排（待外部輸入）：C-14 合規 / workflows / DR

---

## 支援文件（不計入 16，但同批產出）

| 檔案 | 角色 |
|------|------|
| `area-a-integration-sequencing-capstone-20260531.md` | Area-A 專屬排序 capstone（早一天，A 區先啟動）|
| `integration-progress-20260531.md` | 15 項整體盤點 / 進度底稿（B-9 + DevOps 措辭已於 commit 64f29259 校正）|

---

## 當前對齊摘要（截至 Sprint 57.70）

**主線未偏離** — 57.64→57.70 正在執行 capstone 優先序 #2「拱心石 bundle」及其延伸（A-3b HANDOFF、A-5a/b schema codegen、57.70 觸及 C-13 agents 後端）。

**兩個 strategic gap（capstone 點名的高優先鑰匙鏈，至今未啟動）**：
1. **鑰匙鏈 ① C-11（⭐1）尚未做** — A 區 wiring 全程以 mock 驗證，real-LLM live leg 一路 🚧 deferred（缺 Azure secrets，需用戶提供）。
2. **鑰匙鏈 ② billing 正確性束（B-7+B-8+C-15）完全未動** — 含 per-request budget 失效 bug + cost_ledger 雙扣 / Outbox 缺失，風險高於剩餘的 A-4/A-6 便宜項。

**次要偏離**：A-6a（最便宜 ½ 天贏面）與 A-4 被跳過，優先做了較貴的 A-3b（3 個 sprint）；非錯誤，但低成本項在積壓。

**2026-06-03 更新（post-57.73）**：A 區主 slice 已全部 ship（A-4 tracer 57.71、A-5c Inspector Tree 57.72、A-6a/b 57.73），上述積壓的低成本項已清。**C-11 real-LLM 鑰匙鏈部分達成** —— 閉環 LIVE + 已驗證，`cost_ledger` row-count leg 經重啟驗證轉綠（process-state，非 code bug；PR #238），剩 $ 值=0（pricing-key）屬 billing 束。A 區剩餘僅 4 個 Phase-2/deferred AD（見上表「A 區剩餘」）。
