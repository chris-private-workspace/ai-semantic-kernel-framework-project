# 前後端整合進度盤點 — 2026-05-31

**Purpose**: 以「規劃文件定義的目標狀態」對比「實際代碼 / runtime 狀態」，量化「整個前後端功能連接起來並跑起來」達成多少，並列出待改善 / 優化 / 研究的功能項目。每條結論附 `file:line` 證據。
**Category / Scope**: Status Report / V2 Phase 49-58 + Phase 57+ Frontend（截至 Sprint 57.63 進行中）
**Created**: 2026-05-31
**Last Modified**: 2026-05-31
**Status**: Active
**Author**: AI 助手盤點（4 並行唯讀調查 agent 蒐證 + 主 session 針對性 file:line 驗證）

> **Modification History**
> - 2026-06-01: Correct 2 stale phrasings per A+B+C capstone — §B-9「~13 頁待重建」→ 22/22 PARITY 已達（CI gate 親跑綠）；§15「無 Terraform」→ 有 Bicep IaC（誤導措辭）。strikethrough 保留原文 + 指向 b9/c15 分析。
> - 2026-05-31: Restore comprehensive ZH version after accidental EN overwrite; ground-truth re-verified `.env.example` exists (root + backend, git-tracked) + dev port 3007 @ `vite.config.ts:18`
> - 2026-05-31: Initial creation — integration progress snapshot at Sprint 57.63 in-progress

> **Related**: `cat3-memory-loop-injection-analysis-20260531.md`（A 區項 1 深度分析）

---

## 方法

- 4 個並行唯讀調查 agent 各自蒐證（前後端整合、agent harness runtime、roadmap、待辦），互相交叉驗證。
- 主 session 對高價值可驗證 claim 做針對性 `file:line` 驗證（`handler.py` / `_category_factories.py` / `loop.py` / `sse.py` / `config` / `vite.config.ts` / `.env*`）。
- 百分比為依證據判斷的估值，標明依據；非憑感覺。

---

## 一句話結論

**「主流量脊椎」確實接通且能跑**：chat UI → API → loop → SSE → 渲染，echo_demo 模式全離線可端到端跑通。但「全 12 範疇在 loop 裡活著 + 全頁接真實資料 + 真 LLM 端到端實證」**約 60-70%**。

⚠️ **關鍵注意**：Sprint 57.63 新激活的 **Cat 4 / 7 / 8 / 10 只在 `real_llm` 路徑注入**，而該路徑因缺 `AZURE_OPENAI_*` key 在此環境**從未端到端跑過**——目前僅由 mock 整合測試證明「注入正確」，非「實跑證明」。

---

## 分層達成度

| 層 | 問題 | 達成 | 依據 |
|----|------|------|------|
| **L1 接縫本身** | UI→API→loop→SSE→UI 跑得通嗎? | **~95%** | echo_demo 用 `MockChatClient` 全離線跑通（`handler.py:140`）；router 回 `StreamingResponse(text/event-stream)`；前端真 POST + 手解 SSE frame |
| **L2 後端 harness 深度** | 12 範疇是否都在主流量活著? | **~67-81%**（曾 ~40%）| 見 §L2 逐項表，8/12 全活、~9.75/12 含半分 |
| **L3 前端覆蓋** | 畫面都在且接真資料嗎? | **~40-50%** | 31 路由中 ~13 active；~12 ComingSoon stub；多頁吃 fixture |
| **L4 真 LLM 端到端實證** | 真 Azure 跑一輪證明全鏈? | **0%（此環境）** | `handler.py:178-185` 缺 `AZURE_OPENAI_*` 即 `RuntimeError`；code 已備但未證 |

> 「整個前後端連起來跑起來」：**接縫（脊椎）≈ 95%**，但**完整意義（全範疇活 + 全頁接真資料 + 真 LLM 證）≈ 60-70%**。

---

## L1 — 核心 chat 主流量（✅ 實際能跑）

- `POST /api/v1/chat/` → `StreamingResponse(media_type="text/event-stream")`；前端 `chatService.ts` 真的 POST 並逐行手解 SSE frame。
- **echo_demo 模式全離線跑通**：`handler.py:96-152` `build_echo_demo_handler` 用 `MockChatClient` 2-step 腳本（turn 1 call `echo_tool`、turn 2 `END_TURN`）→ 證明整條 UI→API→loop→SSE→render 鏈是活的，無 env 依賴。
- **14 個 SSE 事件前後端 byte 對齊**：`sse.py` 發的事件名 == 前端 `KNOWN_LOOP_EVENT_TYPES`，`chatStore.mergeEvent` switch 有窮舉 `default: never` 保證無漏接。
- 測試：8 個後端整合測試（e2e / quota / sla / cost / feature-flag / category-wiring / hitl / verification）+ 6 個前端 Playwright e2e。

⚠️ 唯一未證：`real_llm` 模式（真 Azure）在此環境因缺 key 無法跑。

---

## L2 — 12 範疇 loop 注入狀態（Sprint 57.63 後，逐項 file:line 驗證）

> 注入發生於 `build_real_llm_handler`（`handler.py:155-249`）。echo_demo 路徑僅注入 Cat 1/2/6/9，不含 Cat 4/7/8/10。

| # | 範疇 | 狀態 | 證據 |
|---|------|------|------|
| 1 Orchestrator | ✅ 活 | `handler.py:220` `AgentLoopImpl(...)` |
| 2 Tool | ✅ 活 | `handler.py:194` `make_default_executor` → registry + executor |
| 3 Memory | ❌ **Potemkin** | `build_real_llm_handler` 全無 memory provider 注入；loop 不在 turn 內讀記憶（只有 REST 層 `/api/v1/memory`）；`make_default_executor` 也未註冊 `memory_search`/`memory_write` 工具 |
| 4 Context Mgmt | ✅ 活（57.63）| `handler.py:207,230` `make_chat_compactor(chat_client)` → `HybridCompactor`（`_category_factories.py:71-84`）|
| 5 Prompt Construction | ❌ **Potemkin** | `loop.py:196` optional ctor `prompt_builder | None=None`、`loop.py:881` 守衛 `if self._prompt_builder is not None`；但 handler **不傳** → 恆 None，退回裸 message list |
| 6 Output Parsing | ✅ 活 | `handler.py:195` `OutputParserImpl()` |
| 7 State | ✅ 活（57.63）| `handler.py:208,231-232` `make_chat_state_deps`；**all-three-or-nothing**：缺 db/session_id/tenant_id 則回 `(None,None)`（`_category_factories.py:98`）|
| 8 Error Handling | ✅ 活（57.63）| `handler.py:212-238` 注入 5 deps；**惟 budget 是 `InMemoryBudgetStore`**（`_category_factories.py:126`，docstring 明說 `RedisBudgetStore` 跨實例版 deferred）|
| 9 Guardrails | ✅ 活（57.2）| `handler.py:229` `build_default_guardrail_engine()`（PII + Jailbreak input；Toxicity + SensitiveInfo output）|
| 10 Verification | ⚠️ 接了但**預設關** | `handler.py:245` gated on `settings.chat_verification_mode == "enabled"`；`config/__init__.py:112` 預設 **`"disabled"`** |
| 11 Subagent | ⚠️ **HANDOFF stub** | `loop.py:1051-1054` HANDOFF 回 `TerminationReason.HANDOFF_NOT_IMPLEMENTED`（git log 顯示 57.63 含「Cat 11 HANDOFF scope analysis」）；FORK / AS_TOOL 模式經 tool 路徑可活 |
| 12 Observability | ✅ router 層活 / ⚠️ loop 內 tracer 缺 | trace / SLA / cost / audit 在 router 層；loop 每輪內部無 span（`AD-Cat12-LoopTracer`）|

**小計**：8/12 全活（Cat 1,2,4,6,7,8,9 + Cat 12 router 層）、~9.75/12 含半分 ≈ **67-81%**（曾 ~40%）。

### ⚠️ 額外觀測缺口（驗證）

`sse.py` 內**完全沒有** checkpoint / compaction 事件序列化（grep `state_checkpointed|context_compacted|checkpoint|compact` → **No matches**）。即使後端已注入 Cat 4 / Cat 7，前端使用者也**看不到它們在動**——觀測層尚未把這兩個範疇曝露到 SSE 串流。

---

## L3 — 前端頁面 + 真實資料接線

**接真後端（可用）**：
`chat-v2`（真 SSE）、`tenant-settings` 5 tab（Quotas / RateLimits / FeatureFlags / HITLPolicies / Members，多數 READ+WRITE）、`governance`、`verification`、`memory`、`subagents`、`loops`、`state-inspector`、auth（真 JWT）。

**接 fixture / 假資料（畫面在但資料假）**：
`overview`（KPI hardcode）、`admin-tenants`（hook 被卸，吃 `_fixtures.ts`）、`orchestrator`、`cost` / `sla`（summary 真但子圖表吃 fixture）、側欄 session list。

**完全沒建（ComingSoon stub / DRAFT，~12+ 個）**：
`compaction`、`jit-retrieval`、`subagent-tree`、`incidents`、`cache-manager`、`sse`、`devui`、`models`、`tools`、`rbac`、`pricing`、`tenant-onboarding` + 規劃核心頁 `agents` / `workflows`（路由不存在）。

**Mockup 還原度**：1 頁真 parity（overview）、~10 頁 code-level parity（未 Playwright 驗）、~13 頁眼湊 HSL drift 待 re-point、~17 頁未建。

---

## L4 — 真 LLM 端到端實證（此環境 0%）

`build_real_llm_handler`（`handler.py:178-185`）在缺 `AZURE_OPENAI_ENDPOINT` / `AZURE_OPENAI_API_KEY` / `AZURE_OPENAI_DEPLOYMENT_NAME` 任一時即 `raise RuntimeError`。code 已完整備好 AzureOpenAIAdapter 路徑，但缺 key → Cat 4/7/8/10 在真 LLM 串流路徑上的端到端行為（`StateCheckpointed` / `ContextCompacted` / `VerificationPassed` 是否真的發生）尚未實證，僅有 mock 整合測試證明注入正確。

---

## 待改善 / 優化 / 研究分析清單

### A. 接線缺口（功能在但沒接通 — 最高優先）

1. **Cat 3 Memory 注入 loop** — agent 目前在 loop 裡不會用記憶（只有 REST 讀）。**注**：分兩 tier，Tier 2（per-turn auto-inject + verify_before_use）依賴 A-2（Cat 5）；詳見 `cat3-memory-loop-injection-analysis-20260531.md`。
2. **Cat 5 PromptBuilder 啟用** — `loop.py:881` 守衛恆 None，loop 退回裸 message list，無 prompt 快取 / 分層注入。
3. **Cat 11 HANDOFF 真實落地** — 現為 `loop.py:1054` stub。
4. **Cat 12 loop 內部 tracer** — 觀測只在 router 層，loop 每輪無 span。
5. **checkpoint / compaction 事件加入 SSE** — 讓前端看得到 Cat 4/7 在動。
6. **前端真資料接線** — overview KPI、admin-tenants（hook 重掛）、session list 後端化、audit-log 頁路由。

> A 區真實相依：**A-2 →（A-1 Tier 2）**；A-1 Tier 1 / A-3 / A-4 / A-5 / A-6 相對獨立。

### B. 優化（已能跑但需強化）

7. **Cat 8 ErrorBudget 換 RedisBudgetStore** — 現 `InMemoryBudgetStore`（per-process，非跨實例）。
8. **Cat 10 Verification 預設開啟前的驗證** — 現 `disabled`，需先驗證成本 / 品質。
9. **Mockup re-point** — ~~~13 頁待重建；眼湊 HSL → 逐字複製 mockup class；目前僅 overview 過~~ **【2026-06-01 校正：此前提過時】** 實況：**22/22 active 頁 PARITY 已達**（5 個 CATASTROPHIC 於 Sprint 57.40-57.45 逐一重建），CI gate `check-mockup-fidelity.mjs` 親跑綠（byte-identical CSS + 48/48 baseline）。剩餘非「重建 drift 頁」而是 14 PROP stub promote（feature sprint，非 re-point）+ 4 條二階債（baseline 未下修 / shell 層未比對 / 無 per-page 視覺 CI / 5 頁無專屬 mockup）。詳見 `b9-mockup-repoint-status-analysis-20260601.md`。
10. **`_verifier_factory.py` 去留** — 57.63 approach A 後 production 無人用，只剩 4 個測試引用（`AD-Cat10-VerifierFactory-Disposition`）。

### C. 研究 / 分析（需設計決策）

11. **真 LLM e2e 實證** — 需 Azure key，證 Cat 4/7/8/10 真的在串流路徑發生（`AD-Cat4-7-8-10-RealLLM-E2E`）。
12. **IAM Block B/C**（Phase 58+）— `invites` / `mfa` / `tenants/register` 端點前端已呼叫但後端不存在（回 501 / gap banner）。
13. **未建核心頁 `agents` / `workflows`** 的設計與 sprint 排程。
14. **企業合規軸** — SOC 2（0% 規劃，enterprise sales blocker）、APAC PDPA（台灣個資法 / 香港 PDPO，目標市場強制，0%）、EU CRA / AI Act（2026-08/09 硬截止，0%）。
15. **DevOps IaC / multi-region** — ~~~30%，無 Terraform~~ **【2026-06-01 校正：措辭誤導】** 實況：`infra/` **有完整 Bicep IaC**（main.bicep + deploy.sh + 5 模組 + parameters，未驗證部署過）；正確說法是「有 Bicep、無 Terraform/Helm，deploy pipeline disabled」。真缺口：DR 自動化 / multi-region / WAL = 0、DR drill 從未執行。**Data platform / Outbox pattern**（**Outbox 0 實作**只有 schema 設計 → billing 雙扣/漏扣風險、analytics 0%）。詳見 `c15-devops-data-platform-analysis-20260601.md`。

---

## 文件 vs 現實校正

| 項目 | CLAUDE.md / 文件寫 | 現實 | 證據 |
|------|------|------|------|
| 前端 dev port | 3005 | **3007** | `vite.config.ts:18` `port: 3007`（line-6 註解：避開封存 V1 的 3005）|
| `.env.example` | 「複製 `.env.example` 到 `.env`」 | **存在** ✅ | 根目錄 `.env.example`（git-tracked，4620 bytes）+ `backend/.env.example`；先前另一盤點誤報缺失，實際只是未查根目錄 dotfile |

> 真正要修的文件落差**只有** **port 3005 → 3007**（CLAUDE.md §Service Ports 表 + Development Commands）；`.env.example` 指示正確、無需改。

---

## 整體比例

- **規劃**：100%（21 份 agent-harness-planning 規劃文件 + Phase 57+ frontend sprint）。
- **V2 核心（11+1 範疇 code）**：~95% 實作（非 stub）。
- **chat 主流量 runtime 啟用**：~40% → **~67-81%**（Sprint 57.63 激活 Cat 4/7/8/10 後）。
- **前後端整合（完整意義）**：**~60-70%**。
- **企業級 SaaS 外圍能力**（Auth 完整度 / 合規 / SRE ops / DevOps 生產化 / Public API / Data platform）：約業界 baseline 的 **30-40%**，數項有 2026 法規硬截止。

---

## 後續可選動作

1. 針對 A 區任一缺口（如 Cat 5 PromptBuilder 激活、或 checkpoint/compaction SSE 曝露）做單點深入 + 排下一個 sprint。
2. 修 CLAUDE.md §Service Ports 的 port 3005 → 3007。
3. 啟動企業合規軸 spike（SOC 2 / APAC PDPA / EU CRA），多項 2026 截止。

---

## 方法註記

本盤點為 main `526be549`（Sprint 57.63 merged）時點快照。所有百分比為依證據判斷之估值，非量測指標。`.env.example` 與 port 兩項校正已於本 session 用 `git ls-files` + `ls` + `grep vite.config.ts` ground-truth 複驗。
