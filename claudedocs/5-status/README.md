# 5-status — 狀態報告 / 分析快照總索引

**Purpose**: `claudedocs/5-status/` 全部文件的總索引（每檔 1 行主題 + 狀態），解決「靠檔名認不出主題」問題。
**Category / Scope**: Status index (cross-cutting)
**Created**: 2026-06-12
**Last Modified**: 2026-06-22
**Status**: Active

> **Modification History**
> - 2026-06-25: 群組 2 +1 行 — `user-interrupt-resume-context-gap-20260625.md`(user-stop→continue 失憶實證缺口 + CC 藍本 + 根因；候選 `AD-UserStop-Resume-Context`)
> - 2026-06-22: 群組 2 +1 行 — `ai-agent-harness-consolidated-analysis-20260622.md`(三份綜合主文件,標為入口)
> - 2026-06-22: 群組 2 +2 行 — `ai-agent-harness-market-research-panorama-20260622.md`(2026 外部市場/學術研究全景 14 findings)+ `ai-agent-harness-research-vs-v2-mapping-20260622.md`(14 findings × V2 落地對照 + 5 大機會)
> - 2026-06-19: 群組 2 +1 行 — `cc-long-running-loop-source-analysis-20260619.md`(CC v2.1.88 長運行 loop 力學剖析,接 cc-parity + cc-source-blueprint 三份互補鏈）
> - 2026-06-12: Initial creation (docs-reorg REFACTOR-007) — 7 主題群索引 + 命名規則

---

## 使用規則

1. **命名**：新分析檔一律 `<主題前綴>-<內容>-YYYYMMDD.md`（例：`c11-real-llm-e2e-analysis-20260601.md`）。
2. **登記**：新增檔案時在本索引對應群組加 1 行（主題 + 狀態）。
3. **完結批次**：一個審計/調查批次全部完結後，整批移入日期命名子目錄（例：`v2-audit-2026-04/`）。
4. **V1 時期文件**：一律歸檔到 `archived/claudedocs-v1/5-status/`，不留在本目錄。
5. **Sprint 工件**（截圖/DRIFT/REPOINT 報告）**不放這裡**，放 `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-XX/artifacts/`。

---

## 群組 1｜Integration-gap ABC 系列（2026-05-31 ~ 06-04）

> 「主流量接線之外」15 項缺口的系統盤點。Area A 🎉 全閉（57.78）、Area B code 層全閉、Area C 部分進行。入口：`README-integration-gap-abc.md`。

| 檔案 | 主題 | 狀態 |
|------|------|------|
| `README-integration-gap-abc.md` | A+B+C 15 項缺口總索引（16 份核心文件導覽）| ⭐ 入口 |
| `integration-gap-capstone-abc-20260601.md` | Capstone：15 項收斂成兩條鑰匙鏈（real-LLM 束 + billing 正確性束）| ✅ 兩束均閉 |
| `integration-progress-20260531.md` | 15 項整體盤點 / 進度底稿 | 歷史快照 |
| `area-a-integration-sequencing-capstone-20260531.md` | Area-A 專屬排序 capstone（依賴圖）| ✅ |
| `area-a-program-closeout-20260604.md` | Area-A program 收尾報告 | ✅ 57.78 |
| `cat3-memory-loop-injection-analysis-20260531.md` | A-1 Cat 3 Memory loop 注入 | ✅ 57.64/65 |
| `cat5-promptbuilder-loop-injection-analysis-20260531.md` | A-2 Cat 5 PromptBuilder（拱心石）| ✅ 57.64/65 |
| `cat11-handoff-loop-injection-analysis-20260531.md` | A-3 Cat 11 Subagent / HANDOFF | ✅ 57.64/68-70 |
| `cat12-loop-tracer-analysis-20260531.md` | A-4 Cat 12 Loop Tracer | ✅ 57.71（Tier 2 Jaeger → C-15）|
| `cat-events-to-sse-analysis-20260531.md` | A-5 Events → SSE 管道 | ✅ 57.66-75 |
| `frontend-real-data-wiring-analysis-20260531.md` | A-6 前端真資料 wiring | ✅ 57.73-77 |
| `cat8-errorbudget-redis-wiring-analysis-20260531.md` | B-7 ErrorBudget Redis wiring | ✅ 57.81 |
| `cat10-verification-default-enable-analysis-20260601.md` | B-8 verification 預設開啟評估 | ✅ 57.82-83 |
| `b9-mockup-repoint-status-analysis-20260601.md` | B-9 mockup re-point 真實狀態 | ✅ 22/22 PARITY（剩 4 二階債）|
| `cat10-verifier-factory-disposition-analysis-20260531.md` | B-10 verifier_factory 去留 | ✅ 已刪（REFACTOR-006）|
| `c11-real-llm-e2e-analysis-20260601.md` | C-11 real-LLM e2e 驗證 | 🟡 剩 CI 排程（待 Azure secrets）|
| `c12-iam-block-bc-analysis-20260601.md` | C-12 IAM Block B/C | 🟡 invites/password/register ✅；MFA/recovery 待 |
| `c13-agents-workflows-pages-analysis-20260601.md` | C-13 缺核心頁 agents / workflows | 🟡 workflows 全缺 |
| `c14-compliance-axis-analysis-20260601.md` | C-14 企業合規軸（SOC2/PDPA/CRA/AI Act）| ❌ 0% code（外部阻擋）|
| `c15-devops-data-platform-analysis-20260601.md` | C-15 DevOps IaC/DR + Data platform | 🟡 billing leg ✅；DR/IaC 外部阻擋 |

## 群組 2｜Agent Harness 對標 / 進度評估（2026-05-30 ~ 06-08）

> harness-deepening roadmap（`../1-planning/harness-deepening-proposal-20260610.md`）的上游證據鏈。

| 檔案 | 主題 | 狀態 |
|------|------|------|
| `v2-overall-progress-gap-assessment-20260606.md` | 11+1 範疇整體進度 gap 評估 | Active |
| `agent-harness-cc-parity-20260607.md` | CC v2.1.88 部件級對照（核心 loop 達標 + C 類 5 缺口）| Active（local，未 commit）|
| `cc-source-blueprint-pause-resume-phases-20260608.md` | CC 源碼證偽：非 6-phase、無 durable resume | Active（local，未 commit）|
| `user-interrupt-resume-context-gap-20260625.md` | ⚠️ **drive-through 實證缺口**：user 中途 Stop → continue 失憶（中斷那輪 ledger 0 列；turn-0 prompt commit-on-disconnect rollback bug）+ CC 藍本（persist-before-LLM + `[Request interrupted by user]` + transcript replay）+ 根因（為何 cc-parity #2「✅」+ pause-resume §5「ahead of CC」漏掉它）→ 候選 `AD-UserStop-Resume-Context` | Active（候選）|
| `cc-long-running-loop-source-analysis-20260619.md` | CC v2.1.88 `query.ts` 逐段親讀：agent loop 為何能長運行（無 maxTurns + 5 層壓縮管線 + 7 continue 自癒站點 + 6hr 重試/30s 心跳 + 2 自主續跑引擎）+ 何時停（end_turn 唯一退出信號 / maxTurns / 中斷 / 不可恢復錯誤 / permission 特例）| Active |
| `v2-architecture-flow-visualization-20260607.md` | V2 架構 / 流程視覺化 | Active（local，未 commit）|
| `runtime-verification-20260530.md` | V2 runtime 實證驗證（實驗證據）| 快照 |
| `subagent-tree-relay-diagnostic-20260617.md` | `AD-Subagent-Child-Event-SSE-Relay` drive-through 診斷：node-level (57.95) + depth-1 (57.96) 已修；depth>1 = YAGNI-by-design | ✅ AD CLOSED |
| `chat-v2-agent-loop-capability-drivethrough-20260618.md` | chat-v2 主流量 agent loop 子能力多輪 drive-through（工具/subagent/verification/HITL/escalate 暫停/handoff/injection/long-run/compaction）+ CC 長運行誠實評估（§3 三缺口）| Active |
| `task-primitive-thin-spike-eval-20260618.md` | 缺口①評估：顯式 task primitive（類 CC TodoWrite）—— 推薦做 thin spike（DB-backed store + rehydrate + drive-through gate）；非冗餘、非邊際、與 max_turns/調度器缺口正交 | ✅ DONE Sprint 57.140 |
| `passk-reliability-thin-spike-eval-20260624.md` | 研究機會 #2 評估：pass^k 可靠性實測 harness（reliability≠capability，τ-bench pass^8<25%）—— 推薦 thin spike（offline `benchmark_pass_k.py` 鏡像 benchmark_judge + pass^k/behavioral-consistency 兩軸 + multi-step corpus；λ/ε 後置 ∵ 證據弱）；net-new 無 AP-6 | ✅ DONE Sprint 57.141 |
| `otel-genai-schema-thin-spike-eval-20260625.md` | 研究機會 #5 評估：Cat 12 標準化在 OTel GenAI semantic conventions —— **關鍵反轉**：OTel SDK 已真實整合（`opentelemetry-*==1.22.0` + OTLP/Prometheus），gap **只是 span/attr schema bespoke**（非 `gen_ai.*`）；推薦 translation-at-tracer 翻譯層（零 loop.py，順手修 post-response token 遺失 latent bug）+ 真 `InMemorySpanExporter` conformance harness | Active（評估） |
| `ai-agent-harness-consolidated-analysis-20260622.md` | ⭐ **三份綜合主文件（讀這一份 = 讀完三份）**：執行摘要 9 條 + 8 維度全景 + 11+1 範疇落地對照（✅/⚠️/❌/💡 + file:line）+ 6 跨維度主題 + 8 優先機會 + 證據品質 + thinking×self-conditioning 矛盾調和 | ⭐ 入口 |
| `ai-agent-harness-market-research-panorama-20260622.md` | 2026 外部市場/學術研究全景（中立）：14 findings（reliability≠capability、self-conditioning、任務拆解最高槓桿、naive memory 有害、6 種抗注入結構模式…）+ 證據強度分級 + 30 來源 | Active（外部研究·細節後備） |
| `ai-agent-harness-research-vs-v2-mapping-20260622.md` | 上述 14 findings × V2（11+1 範疇 + server-side governance + max_turns=8）落地對照（✅/⚠️/❌/💡）+ 5 大機會（任務原語 / 可靠性實測 / 安全結構限制 / verify 清 context / 壓縮階梯）| Active（對照） |

## 群組 3｜Cat 10 Verification 量測

| 檔案 | 主題 | 狀態 |
|------|------|------|
| `cat10-verification-real-llm-measurement-20260605.md` | real-Azure verification 量測（B-8 flip 的數據依據）| ✅ |

## 群組 4｜V2 起點回顧（2026-04-28 過渡期）

| 檔案 | 主題 |
|------|------|
| `v2-eleven-categories-and-philosophy-review-20260428.md` | 11 範疇 + 哲學 review（V1→V2 過渡）|
| `v2-phase-roadmap-pm-review-20260428.md` | V2 初始 22-sprint 路線圖 PM review |

## 群組 5｜審計批次子目錄

| 子目錄 | 檔數 | 主題 | 狀態 |
|--------|-----|------|------|
| `v2-audit-2026-04/` | 22 | Phase 49-51 分週驗證審計（BASELINE + W1-W4P + WEEK summaries + open issues）| 已完結（歷史）|
| `v2-investigation-20260522/` | 13 | V2 重構狀態 + 前端狀態 + mockup drift 根因（根 CLAUDE.md 引用中）| ⭐ Active 引用 |
| `drift-audit-2026-05-25/` | 48 | 全頁 drift 審計批次 | 已完結 |
| `drive-through-20260606/` | 44 | 35 頁 drive-through audit + deep-audit-15-fullimpl + 截圖 | ⭐ carryover 來源 |

## 歸檔出口

V1 時期文件（MAF 審計、phase-15 AG-UI、sprint-0/3 報告等）→ [`archived/claudedocs-v1/5-status/`](../../archived/claudedocs-v1/5-status/)
