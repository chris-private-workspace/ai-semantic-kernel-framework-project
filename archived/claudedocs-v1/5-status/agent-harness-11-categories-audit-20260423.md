# Agent Harness 11 大範疇 × IPA Platform 嚴格寫實審計（**校正版 V2**）

**建立日期**：2026-04-23
**校正原因**：第一版 V1 對齊度 63% 是高估。真實只 ~27%
**驗證方法**：2 個 codebase-researcher 子代理平行嚴格掃描（Level 0-5 評分）+ 主流量驗證
**佐證**：實際代碼路徑、行號、import 鏈、testing 證據

---

## 校正版核心結論

| 版本 | 整體對齊度 | 評語 |
|------|----------|------|
| V1 第一版 | ~63% | 把「代碼存在」誤計為「項目能力」 |
| V1.5 中途校正 | ~47% | 扣除部分 Claude SDK 高估 |
| **V2 真實版** | **~27%** | **只算生產主流量真實運行** |

**真實狀況**：本項目作為 **未完成體**，11 範疇中 **8 個處於 Level 0-2（代碼存在但未真正運行）**，只有 **1 個達 Level 4**（Output Parsing），**0 個達 Level 5**。

---

## 評分標準（5 級嚴格制）

| Level | 範圍 | 含義 |
|-------|------|------|
| 0 | 0% | 完全沒實作 |
| 1 | 10-20% | 代碼存在但**未接入生產主流量**（PoC/僵屍代碼） |
| 2 | 25-40% | 已接入但**未經測試**或不完整 |
| 3 | 45-65% | 接入且基本測試，但尚未完全在主流量運行 |
| 4 | 70-85% | 在主流量運行 + 有測試 + 缺某些業界標準特性 |
| 5 | 90-100% | 完整對齊業界最佳實踐 |

**生產主流量定義**：UnifiedChat / OrchestratorChat → API → Pipeline → Dispatch  
**不算主流量**：PoC endpoints、autonomous executor、Hybrid V1（被 Phase 48 取代）、Claude SDK 內部（除非確實接入）

---

## 11 範疇真實審計

### 範疇 1：Orchestrator Layer (TAO/ReAct loop)
- **Level**: 1
- **真實 %**: **18%**
- **證據**：
  - `pipeline/service.py:173-394` — 8-step **線性順序執行**，**非 agent loop**
  - `team_agent_adapter.py:74` — `for iteration in range(max_iterations)` 是 tool_call loop（合格的 mini ReAct）
  - `subagent.py:107` — `asyncio.gather` 一次性派發，**無「結果回注重新推理」**
  - `direct_answer.py` — 單次 LLM 呼叫
- **生產主流量**：是 step 順序機 + 分支執行 → 結束。**無 stop_reason 驅動的 while-loop**
- **缺失**：① 工具結果不回注主 orchestrator 重新推理 ② 無 stop_reason 驅動退出
- **誠實判斷**：主流量 = pipeline + dispatch 組合，**不是業界標準的 agent loop**。只有 TeamAgentAdapter 內部是真 ReAct
- **V1 → V2 校正**：70% → **18%**

---

### 範疇 2：Tool Layer
- **Level**: 2
- **真實 %**: **32%**
- **證據**：
  - `team_agent_adapter.py:165-187` — `TeamToolRegistry.get_openai_tool_schemas()` + `execute()`
  - `subagent.py:60-66` — 嘗試載入 `OrchestratorToolRegistry` (hybrid 包) 失敗則 fallback
  - Schema 為 OpenAI native function calling 格式 ✅
- **生產主流量**：用 TeamToolRegistry，但**未見 schema 強制驗證**（無 `jsonschema.validate` 呼叫）
  - `core/sandbox/` 存在但 `team_agent_adapter._execute_tool` **直接呼叫 registry，未經 sandbox**
- **缺失**：① 無 sandbox 接入主流量 ② 無權限/role 隔離（hardcoded `role="admin"`）
- **誠實判斷**：工具能跑，**但安全層全繞過**
- **V1 → V2 校正**：75% → **32%**

---

### 範疇 3：Memory（多時間尺度）
- **Level**: 1
- **真實 %**: **15%**
- **證據**：
  - `pipeline/steps/step1_memory.py` 存在
  - `service.py:511-514` 只記錄 `memory_chars / memory_text`
  - **無 mem0 真實接入主流量證據**
  - memory module（`integrations/memory/` 5 檔）存在但**未在 dispatch executors 中被 import**
- **生產主流量**：Step 1 執行了，但**內容如何產出未見證據**顯示為 mem0 / 真實長期記憶
- **缺失**：① 無短期/長期分層 ② 無 CC 式「線索 → 驗證」設計
- **誠實判斷**：**結構槽位有，內容空**
- **V1 → V2 校正**：65% → **15%**

---

### 範疇 4：Context Management（防 context rot）
- **Level**: 0
- **真實 %**: **5%** （**最弱項，幾近於零**）
- **證據**：
  - `team_agent_adapter.py:66-69` — 每個 `agent.run()` 從零組 messages（system+user），**無壓縮 / observation masking**
  - `subagent.py:312-329` — 把 worker 完整 messages 透過 SSE 推送，**無 size 限制**
  - `context_budget.py` 未顯示接入主流量
- **生產主流量**：**10+ turn 對話會無控制累積；subagent 返回亦無摘要化**
- **缺失**：① 無 compaction ② 無 JIT retrieval ③ 無 subagent summary cap
- **誠實判斷**：**context rot 防禦本質上不存在**
- **V1 → V2 校正**：50% → **5%**

---

### 範疇 5：Prompt Construction
- **Level**: 1
- **真實 %**: **20%**
- **證據**：
  - `team_agent_adapter.py:66-69` — 直接組 `[system, user]`，**無 PromptBuilder 抽象**
  - `subagent.py:175-229` — decompose 走 TaskDecomposer，**prompt 散落於各 executor**
- **生產主流量**：**沒有統一 PromptBuilder**。Memory/knowledge 在 PipelineContext 但 dispatch 階段是否真的注入 LLM prompt **未見系統證據**（adapter `context` 參數只接受 task 字串）
- **缺失**：① 無階層組裝器 ② 無 lost-in-middle 位置策略
- **誠實判斷**：**是平鋪的，且 memory/knowledge 可能未真接入 LLM prompt**
- **V1 → V2 校正**：40% → **20%**

---

### 範疇 6：Output Parsing
- **Level**: 4
- **真實 %**: **75%** ⭐ **唯一真正接近業界標準的範疇**
- **證據**：
  - `team_agent_adapter.py:78-85` — 用 `chat_with_tools(tool_choice="auto")`
  - `team_agent_adapter.py:101` — 取 `result["tool_calls"]`
  - `team_agent_adapter.py:117` — 解析 `tc["function"]["arguments"]` JSON
  - **正確 native function calling**
- **生產主流量**：是 native，**無正則 fallback** ✅
- **缺失**：arguments JSON 解析失敗只 fallback `{}`（line 119），缺 schema 重試
- **誠實判斷**：**唯一真正接近業界標準的範疇**
- **V1 → V2 校正**：90% → **75%**（小幅下調）

---

### 範疇 7：State Management
- **Level**: 2
- **真實 %**: **30%**
- **證據**：
  - `pipeline/persistence.py:18-215` — `PipelineExecutionPersistenceService.save()` **只在最終一次性持久化**（無增量快照）
  - `_build_pipeline_steps` 是收集執行完成後的快照
  - `resume/service.py:17` 含 retry 邏輯但**僅 1 處引用**，**無相關測試**
  - HITL checkpoint：`step5_hitl.py:149` 與 `step8_postprocess.py:71` 各有獨立實作（**無 typed state schema**）
- **生產主流量**：末端會寫 persistence，**無多版本 / 無 time-travel / 無增量 step snapshot**
- **缺失**：① 無 multi-version checkpoint ② 無 time-travel debug ③ resume 路徑未驗證
- **誠實判斷**：**是「最終態快照 + HITL pause 棚架」，不是業界 state machine**。給 30% 偏寬
- **V1 → V2 校正**：60% → **30%**

---

### 範疇 8：Error Handling
- **Level**: 1
- **真實 %**: **20%**
- **證據**：
  - `pipeline/exceptions.py` — 僅 3 類：`PipelineError`、`HITLPauseException`、`DialogPauseException`（**無 transient/LLM-recoverable/user-fixable/unexpected 四分類**）
  - 整個 `orchestration/` 只有 6 檔含 retry，**主 pipeline 僅 `persistence.py:1` 出現 1 次**（極可能是註解）
  - 主流量 `pipeline/steps/base.py` 與各 step `_execute` **無 retry decorator**
- **生產主流量**：**沒有任何 LLM retry / tool retry / backoff 機制**。Dialog/HITL pause 是控制流，**不是錯誤恢復**
- **缺失**：① 無錯誤分類 ② 無 retry cap ③ 無 LLM 拒答/超時策略
- **誠實判斷**：業界基準的 ~20%。**Pause exceptions 不是錯誤處理而是工作流控制**
- **V1 → V2 校正**：55% → **20%**

---

### 範疇 9：Guardrails & Safety
- **Level**: 2
- **真實 %**: **30%** （**V1 的「業界領先」是嚴重高估**）
- **證據**：
  - `step3_intent.py` — 主要做 intent 路由，**無 input guardrail / PII / jailbreak 檢測**
  - `step4_risk.py:73 _execute` + `risk_assessor/assessor.py`（657 行）存在
    - `_get_assessor()` 是延遲取得
    - assessor 657 行多為**規則表**，無看到 main pipeline 強制呼叫的測試證據
  - `step5_hitl.py` + `hitl/controller.py`（833 行）存在，**pause exception 機制可信**
    - 但 **Teams 通知路徑未驗證**
  - 4-hook chain（`claude_sdk/hooks/`）**不在主流量**（Claude SDK 是側翼）
  - `step8_postprocess` 僅做 schedule_memory_extraction，**無毒性/PII 檢查**
  - **無 tripwire / 無 tool-level permission gating**
- **生產主流量**：HITL gate 真實接入（HITLPauseException 會中斷 pipeline）；risk step 接入但執行品質未驗；**input/output guardrail 完全缺失**
- **缺失**：① 無 input guardrail ② 無 output guardrail ③ 無 tripwire ④ Claude hooks 未在主流量
- **誠實判斷**：三層 guardrails **只實作 1.2 層**（risk + HITL）
- **V1 → V2 校正**：85% → **30%**（最大幅校正之一）

---

### 範疇 10：Verification Loops
- **Level**: 1
- **真實 %**: **15%**
- **證據**：
  - `step8_postprocess.py:53-126` — 主要動作是 `_save_checkpoint` + `_schedule_memory_extraction`，**無任何驗證邏輯**（無 rules check / 無 LLM-as-judge / 無 schema validate）
  - `claude_sdk/autonomous/verifier.py` — 存在但屬 autonomous executor 路徑，**不在 UnifiedChat 主流量**
  - 主流量**無 self-correction loop**
- **生產主流量**：**無任何輸出驗證**。Postprocess 名稱誤導，**實為 finalize/persist**
- **缺失**：① 無 rules-based check ② 無 LLM-as-judge ③ 無 retry-on-fail loop
- **誠實判斷**：業界 verification loop 在主流量為 0%；給 15% 是因為 risk_assessor 勉強算前置驗證的一個維度
- **V1 → V2 校正**：40% → **15%**

---

### 範疇 11：Subagent Orchestration
- **Level**: 2
- **真實 %**: **35%**
- **證據**：
  - `dispatch/executors/` 僅 **3 個 executor**：`direct_answer.py`、`subagent.py`、`team.py`
  - `team.py:3` 含 retry，引用 MAF GroupChat（透過 `team_agent_adapter.py`）
  - `subagent.py` 為**單個 subagent 路徑**（非 fork/parallel pool）
  - **Handoff/Magentic/Swarm 不在主流量** — 這些 builders 只在 Agent Team PoC 頁面呼叫
  - **無 worktree-style 隔離**（CC pattern）
  - **無 agents-as-tools registry 在主流量**（`team_tool_registry.py` 僅 team 內部）
- **生產主流量**：dispatch 真實接入 3 路；team 路徑接 MAF GroupChat ✅；但**動態 subagent count（5-10 並行）未實作**
- **缺失**：① 無動態並行數 ② 無 handoff/swarm 主流量 ③ 無 agents-as-tools
- **誠實判斷**：三路 dispatch + MAF GroupChat 是真實主流量功能，但**離 CC subagent 模型有距離**
- **V1 → V2 校正**：80% → **35%**

---

## 整體真實對齊度（V2 校正版）

| # | 範疇 | Level | 真實 % | V1 原報告 | 校正幅度 |
|---|------|-------|-------|----------|---------|
| 6 | Output Parsing | 4 | **75%** | 90% | -15% |
| 11 | Subagent Orchestration | 2 | **35%** | 80% | **-45%** |
| 2 | Tool Layer | 2 | **32%** | 75% | **-43%** |
| 7 | State Management | 2 | **30%** | 60% | -30% |
| 9 | Guardrails & Safety | 2 | **30%** | 85% | **-55%** ⚠️ |
| 5 | Prompt Construction | 1 | **20%** | 40% | -20% |
| 8 | Error Handling | 1 | **20%** | 55% | -35% |
| 1 | Orchestrator (TAO/ReAct) | 1 | **18%** | 70% | **-52%** ⚠️ |
| 3 | Memory | 1 | **15%** | 65% | **-50%** ⚠️ |
| 10 | Verification Loops | 1 | **15%** | 40% | -25% |
| 4 | Context Management | 0 | **5%** | 50% | **-45%** ⚠️ |
| **平均** | | **L1.5** | **~27%** | ~63% | **-36%** |

### Level 分佈

| Level | 範疇數 | % | 含義 |
|-------|-------|---|------|
| 0 | 1 | 9% | 完全未實作 |
| 1 | 5 | 45% | 代碼有但未接入主流量 |
| 2 | 4 | 36% | 接入但不完整/未測試 |
| 3 | 0 | 0% | — |
| 4 | 1 | 9% | 主流量運行 + 部分對齊 |
| 5 | 0 | 0% | — |

**90% 的範疇處於 Level 0-2（不可用 ~ 半成品）**

---

## 三大誠實洞察

### 1. 主流量 ≠ 代碼倉
過去報告把「代碼倉中 30+ 檔案的 Claude SDK / autonomous / verifier / 4-hook chain」**誤計為項目能力**。校正後發現：

- **Claude SDK 路徑** 不在主流量
- **autonomous executor** 不在主流量
- **4-hook chain** 不在主流量
- **Hybrid V1** 被 Phase 48 取代，邊緣化

**真實主流量只有**：UnifiedChat → API → Pipeline (8 step) → Dispatch (3 executor) → MAF / Azure OpenAI

### 2. 5 個範疇是「結構槽位但內容空」
最危險的發現是這 5 個：
- **Memory（15%）**：Step 1 跑了但**沒實際讀 mem0**
- **Context Management（5%）**：**完全沒有 context rot 防禦**
- **Prompt Construction（20%）**：**沒有 PromptBuilder**，memory/knowledge 不確定真注入 LLM
- **Verification Loops（15%）**：postprocess 名稱誤導，實際**只是 finalize**
- **Error Handling（20%）**：**沒有任何 retry 機制**

這些都是**運行起來看似有但其實沒效果**的「Potemkin features」。

### 3. Guardrails 是最大認知校正
V1 給 85%「業界領先」是嚴重錯誤。真實：
- ✅ HITL pause/resume 存在且運作
- ✅ Risk assessor 規則表存在
- ❌ **無 input guardrail（PII/jailbreak）**
- ❌ **無 output guardrail（毒性檢查）**
- ❌ **無 tripwire 自動中斷**
- ❌ **無 tool permission gating**

實際只達 **1.2 層 / 3 層業界標準**。

---

## 對 Phase 49+ 戰略決策的影響

### 1. 改造規模重估
| 項目 | V1 估計 | V2 校正 |
|------|--------|--------|
| 起點對齊度 | 63% | **27%** |
| 目標對齊度 | 95% | 80% |
| 需補的 gap | 32% | **53%** |
| Sprint 數 | 9 | **15-18** |
| 時程 | 2.5 月 | **4-5 月** |

### 2. 最該優先補的（按嚴重度）
| 優先 | 範疇 | 校正 % | 理由 |
|------|-----|-------|------|
| **P0** | 範疇 4 Context Mgmt | 5% | **沒有 context rot 防禦，長對話必爆** |
| **P0** | 範疇 1 Orchestrator Loop | 18% | **架構就不是 loop，要從零植入** |
| **P0** | 範疇 5 Prompt Construction | 20% | 沒有 PromptBuilder，memory 可能根本沒進 LLM |
| **P1** | 範疇 3 Memory 真接入 | 15% | mem0 寫了但沒接入主流量，補接線 |
| **P1** | 範疇 9 input/output Guardrails | 30% | 企業合規必需 |
| **P1** | 範疇 10 Verification | 15% | 沒人檢查 agent 輸出對不對 |
| **P2** | 其他 | | |

### 3. 戰略真相
本項目目前是 **「企業治理棚架（Pipeline + HITL + Risk + Audit）」 + 「3 個 dispatch executor」 + 「MAF GroupChat 一個內 ReAct loop」**。

要稱為「企業級 agent 平台」還差 **53% 的 agent 智能機制**。

**這不是失敗，是誠實 baseline**。Phase 49+ 必須以這個 27% 為起點，而不是 63%。

---

## 致決策者的最終判斷

**坦白說**：
1. 本項目目前**不是一個運行中的 agent harness**，而是一個 **「pipeline 框架 + 3 個分派執行器 + 大量未連接的能力代碼」**
2. 大量代碼**寫了沒用**（autonomous / 4-hook / context_budget / verifier / Claude SDK 整合等）
3. 主流量的 agent 智能基礎**僅 ~20%**（範疇 1-5 平均），治理基礎 **~32%**（範疇 7-9 平均），輸出 **75%**（範疇 6）
4. **整體 27% 是真實起點**，未來 Phase 規劃必須據此

**好消息**：
- 範疇 6 Output Parsing 已對齊，奠定 native tool_calls 基礎
- Pipeline + dispatch 棚架健全，**改造空間大且可擴展**
- 大量「寫了沒用」的代碼可以**重新接線**，不必從零寫
- 已有 Phase 48 LLM-native orchestrator 作為改造起點

**現實版 Phase 49 預估**：
- 4-5 個月、15-18 sprint
- 從 **27% → 70-75%**（不是 95%，95% 不切實際）
- 達到 70% 已可稱「企業級 agent 平台 MVP」

---

**最終誠實一句話**：本項目是「**企業治理框架 + agent 棚架**」，**還不是企業級 agent harness**。但有完整的 baseline 和清晰的補強路徑，Phase 49+ 是「**從棚架填血肉**」而非「**架構推翻**」。
