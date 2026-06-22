# 2026 Agent 研究 14 Findings × V2 落地對照(✅/⚠️/❌/💡)

**Purpose**: 把 [`ai-agent-harness-market-research-panorama-20260622.md`](ai-agent-harness-market-research-panorama-20260622.md) 的 14 項研究發現,逐一對照本項目 V2 的 11+1 範疇 + server-side governance + `max_turns=8` 有界爆發設計,標出已具備 / 部分 / 缺口 / 機會。
**Category / Scope**: Status / Research-to-implementation mapping (cross-cutting)
**Created**: 2026-06-22
**Last Modified**: 2026-06-22
**Status**: Active (snapshot;基於 git HEAD Sprint 57.135 程式碼 grounding)
**Grounding**: 3 個 read-only Explore agent 對 `backend/src/agent_harness/` 的 file:line 勘查(2026-06-22)+ 本項目 3 份權威文件(`task-primitive-thin-spike-eval-20260618.md` / `cc-long-running-loop-source-analysis-20260619.md` / `agent-harness-cc-parity-20260607.md`)
**驗證層級**:**程式碼 grounding(file:line)**,非 drive-through。標 ✅ 者若要宣稱「使用者真的能用」,以既有 drive-through 紀錄(`chat-v2-agent-loop-capability-drivethrough-20260618.md`)為準。

> **Modification History**
> - 2026-06-22: Add cross-ref to 3rd same-day deep-research (ux-research, 1-planning)
> - 2026-06-22: Initial creation — 14 findings × V2 對照;校正 2 處 Explore agent 偏差(Cat 10 in-loop verify gate 確存於 loop.py:1770/2617-2687;max_turns loop 預設 50 但 chat 主流量 handler.py:710 寫死 8)

> **標記**:✅ 已具備 · ⚠️ 部分 · ❌ 缺口 · 💡 機會
>
> **🔗 第三份同日研究**:[agent-harness-ux-research-20260622.md](../1-planning/agent-harness-ux-research-20260622.md)(8 角度 deep-research)。對本對照表的增量:**Cat 12** 可加「標準化於 OTel GenAI semantic conventions(invoke_agent→chat→execute_tool span、`captureContent` 預設 off 對齊 PII)」;**Cat 4** compaction 可引 ACON 量化目標(削 26–54% peak token 不損準確率,arXiv 2510.00615);**Cat 10** verification 可引 ICLR2024×EMNLP2024 self-correction 分界線。該文盲點:未涵蓋本對照 finding 14 的安全「限制非偵測」6 模式。

---

## 總覽計分卡

| # | 研究發現 | 範疇 | 判定 |
|---|---------|------|------|
| 1 | Agent = while-loop + ground truth 回注 | Cat 1/6 | ✅ |
| 2 | 先用最簡方案、慎用框架 | 架構哲學 | ✅ |
| 3 | Evaluator-optimizer | Cat 10 | ✅ |
| 4 | Orchestrator-worker multi-agent(增益 + 15× token) | Cat 11 | ✅(增益未實測) |
| 5 | Context engineering + context rot + compaction | Cat 4 | ⚠️ 單層 |
| 6 | Handoff = tool call 機制 | Cat 11 | ⚠️ 不同實作 |
| 7 | Durable execution | Cat 7 | ✅(比範例更重) |
| 8 | 任務長度每 7 個月翻倍 | 趨勢 | n/a(外部趨勢) |
| 9 | ⭐ reliability≠capability、pass@1 vs pass@8 | Cat 1 + 哲學 | ⚠️💡 設計對齊但無實測 |
| 10 | ⭐ self-conditioning | Cat 8 retry | ✅⚠️ 教練式重試但有殘留風險 |
| 11 | ⭐ 任務拆解 + 邊界重啟 = 最高槓桿 | Cat 1/3/7 | ⚠️💡 有機械底座、缺顯式任務原語 |
| 12 | Naive episodic memory scratchpad 有害 | Cat 3 | ✅⚠️ 已避開最差形式 |
| 13 | 結構化反思 / self-correction(實證) | Cat 10/8 | ⚠️ 有結構、非 RL-trained |
| 14 | ⭐ 安全「限制非偵測」+ 6 模式 | Cat 9 | ⚠️💡 混合層防線,含偵測成分 |

**一句話**:V2 在**可靠性「機械底座」與「企業治理」上普遍領先研究的範例**(durable pause、多租戶 guardrail、5-scope memory),但在**長程可靠性的「實測驗證」與「結構化任務脊椎」上有明確空缺**——恰好是 2026 研究指出的最高槓桿區。

---

## A. Loop 架構基礎(發現 1, 2, 3)— ✅ 全綠

### 發現 1:while-loop + ground truth 回注 → ✅
- 主迴圈 `while True:` 由 stop_reason 驅動(`loop.py:2074`),非固定步 pipeline → 正面避開「AP-1 Pipeline 偽裝 Loop」
- 工具結果以 `Message(role="tool")` 回注、`turn_count++` 後 `continue`(`loop.py:2791-3110`)= 研究「每步取 ground truth」
- workflow/agent 二分:V2 是 agent 端,用 server-side guardrail 框住 = 有意 hybrid,不衝突

### 發現 2:先用最簡方案、慎用框架 → ✅
- V2 自建 harness 在 provider-neutral `ChatClient` ABC 上,非套 LangGraph/CrewAI = 研究「直接用 LLM API、不被框架抽象遮蔽」。LLM Provider Neutrality(約束 3)比研究更進一步

### 發現 3:Evaluator-optimizer → ✅
- Cat 10 in-loop verify gate(`loop.py:1770` `_cat10_verify_gate()`)+ RulesBasedVerifier(`rules_based.py:37-77`)+ LLMJudgeVerifier(`llm_judge.py:57-121`)= 研究「一 LLM 產生、另一 LLM 評估回饋」,且做成 in-loop 非 post-hoc

---

## B. 編排 / Multi-agent(發現 4, 6)

### 發現 4:Orchestrator-worker → ✅(增益未實測)
- Cat 11 有 **FORK / TEAMMATE / AS_TOOL 真實子 loop**(`fork.py:101-224`、`teammate.py`、`as_tool.py:46-114`),深度結構性限制 1(`fork.py:21`,recursion-safe)= 2026 共識「orchestrator + ephemeral subagent」
- SSE relay 轉發子 agent 事件到前端(`fork.py:90-98`,57.96)
- ⚠️ 研究 90.2% 是 Anthropic 內部不可重現 eval;**V2 也沒對自己 multi-agent 做增益實測** = 共識採用非實證
- 💡 ~15× token 代價提醒:multi-agent 應只用高價值可並行任務 + 成本歸因(已有 cost_ledger 基礎)

### 發現 6:Handoff = tool call → ⚠️ V2 實作不同
- OpenAI SDK 把 handoff 做成 tool call(`transfer_to_xxx`);**V2 的 HANDOFF 是 loop output classifier 攔截 → `stop_reason="handoff"` → 平台層啟動 child session**(非 tool call;cc-parity §3 #7「半」)
- 💡 可評估是否收斂到 tool-call 形狀以統一心智模型(風格選擇,非缺陷)

---

## C. ⭐ 長程可靠性瓶頸(發現 8, 9, 10)— 最值得關注

### 發現 8:任務長度每 7 個月翻倍 → n/a(外部趨勢)
- 戰略含義:`max_turns=8` 有界爆發會隨模型能力面對越來越長的任務;趨勢站在「需要更好長程支撐」這邊

### 發現 9:⭐ reliability ≠ capability → ⚠️💡
- ✅ **哲學高度對齊**:研究「capability benchmark 對長程可靠性盲目」= V2 的 **drive-through > paper metrics 鐵律**(`feedback_drive_through_over_paper_metrics.md`)的工程化
- ⚠️ **但無「可靠性實測」**:V2 驗證「單次 drive-through 跑通」(類 pass@1),**無 pass@k 式重複可靠性測量**。研究示 pass@1=61% 的東西 pass@8 可能剩 25%
- 💡 **機會**:對關鍵主流量(chat-v2 工具執行 / verification / HITL resume)做「重複 N 次可靠性測量」→ 把「能驅動驗證」升級成「可靠地驅動驗證」

### 發現 10:⭐ self-conditioning → ✅⚠️ 有殘留風險
- ✅ **retry 非 naive 重跑**:工具失敗合成帶診斷 ToolResult(`loop.py:2976-2983`:`"Error: ... Please adjust your approach"`),verification 失敗加 coach feedback(`_build_correction_block` `loop.py:295-309`)= 研究「retry 要帶診斷」
- ✅ 完整 error_policy 矩陣(`retry.py:71-82`)+ circuit_breaker + error_budget + terminator;FATAL/HITL_RECOVERABLE 不重試
- ⚠️💡 **殘留風險**:verification 修正迴圈把**失敗答案 + 修正提示一起 append 進 context** 再 continue(`loop.py:2617-2626`)。研究示「context 留著自己的錯誤 → 後續準確率惡化,放大模型救不了」→ 可能反觸發 self-conditioning
- 💡 **機會**:評估 verification 重試是否該**清掉失敗答案**(只留「目標 + 為何上次不對」精煉版),而非整個失敗 trace 留 context(呼應發現 11「邊界重啟」)

---

## D. ⭐ 可靠性介入(發現 11, 12, 13)

### 發現 11:⭐ 任務拆解 + 邊界重啟 = 最高槓桿 → ⚠️💡 有機械底座、缺顯式脊椎(最關鍵一項)
- ✅ **機械底座已存在**:「`max_turns=8` 有界爆發(`handler.py:710`)+ 跨輪 rehydration(`DBMessageStore.load()` `message_store.py:93-113`、`loop.py:1937-1947`)」**本質上就是研究的「在邊界重啟 agent」**——每 send 是有界 burst,跨 send 透過 message ledger 重新水合
- ❌ **缺「decompose 的顯式結構」**:**無 TodoWrite 式顯式任務原語**(`task-primitive-thin-spike-eval` §1.2 確認:無 `LoopState.plan`、無 `tasks:[{id,status}]`、無跨 turn 任務完成度)。plan 是 emergent 自由文字,跨 send rehydrate 只被當對話,**無結構化、durable、可更新的任務狀態**
- 💡 **正是已評估的 thin spike**:該評估判斷「值得做 thin spike」,推薦 DB-backed `session_tasks` store + run-start rehydrate(鏡像 57.127)。**研究發現 11 提供學術背書**——任務拆解是「最高槓桿可靠性介入」非裝飾
- ⚠️ 校準:研究 13-42pp 為「假設子任務獨立」的分析投影非實測 → 做完增益要自己量

### 發現 12:Naive episodic memory 有害 → ✅⚠️ 已避開最差形式
- ✅ **V2 memory 不是有害的 naive scratchpad**:研究批「每輪注入、無限成長的 add_to_memory」。V2 Cat 3 有 **5 scope × 3 time scale(`memory/_abc.py:46-66`)**、summary 上限 200 字元、per-turn 2000-token budget cap(`builder.py:246-257`、`453-520`,低 confidence 先砍)= 研究結尾建議的「重設計記憶(scoped、有 expiration、預算化)」
- ⚠️ **仍付每輪檢索+注入成本**:每 turn 用「最後一條 user message」重新檢索注入(query-time 固定檢索);budget cap 緩解但未消除
- ⚠️ **semantic time scale 是 STUB**:Qdrant 向量索引回空(51.2 stub)→ 「3 time scale」實際只有 2 個(short-term Redis + long-term PG)在運作
- 💡 **機會**:研究「重設計記憶能否在長程帶來淨增益仍是開放問題」。V2 有完整 scoped memory,**適合產出業界還缺的實證**(測開/關 memory 對長程任務完成度淨影響)

### 發現 13:結構化反思 / self-correction → ⚠️ 有結構、非 RL-trained
- ✅ 有 in-loop self-correction:verification 失敗 → coach feedback → 重試(預設 2 次 `loop.py:2617-2687`),到頂可 verification-ESCALATE 給人(57.99)
- ⚠️ **關鍵差異**:研究實證增益(BFCL v3、Repair@5 6.8%→26.4%)來自 **RL 訓練的反思能力**,非純 inference-time prompt 反思。V2 是 prompt-based coach feedback → **可能拿不到論文增益幅度**
- 💡 **機會**:(a) 用更強 model 跑 verification/correction(對應多模型 profile);(b) 優化 coach feedback 結構(診斷 + 可執行下一步,如論文 reflection 形狀)

---

## E. Context 管理(發現 5, 7)

### 發現 5:context engineering + compaction → ⚠️ 單層
- ✅ 有真 compaction:StructuralCompactor(`structural.py:104-207`)+ observation masking(舊工具結果墓碑化 `observation_masker.py`)+ prompt caching(`cache_manager.py:49-127`,tenant-first hash,多租戶安全)
- ⚠️ **單層**:觸發 token>75% **或** turn>30(`compactor/_abc.py:60-74`),chat 還要 ≥3 user turns 才實際壓。研究 + cc-long-running 都指出 CC 是 **5 層階梯**(snip→microcompact→collapse→autocompact,便宜先做、貴最後做)
- 💡 **條件性機會**(cc-long-running 已點明):「若放寬 max_turns,先補的不是數字是壓縮階梯,否則放寬即爆 context」。對短對話單層「可能已夠」;5 層對短 chat 是過度工程 → **只在走「長 autonomous task」時才需要**

### 發現 7:Durable execution → ✅(比範例更重)
- ✅ **比研究 LangGraph 範例更重**:durable checkpoint(`checkpointer.py:94-281`,transient/durable 分離)+ 獨立 `/resume` 端點重建 = **跨行程可治理暫停**。研究 LangGraph + CC「行程內 await Promise、不持久化」都比 V2 輕
- ✅ 冪等性 caveat 用 message ledger rehydration + SAVEPOINT(`message_store.py:115-140`)處理
- = V2 **強過業界範例**的地方,多租戶 SaaS durable HITL pause 是 CC 零藍本純自研區

---

## F. ⭐ 安全護欄(發現 14)→ ⚠️💡 混合層防線,含「偵測」成分
研究核心:**「限制非偵測」**(偵測啟發式「inherently brittle」)。對照:
- ✅ **「限制」部分有**:capability matrix(8 能力 role/scope 檢查 `capability_matrix.py`)、per-tenant HITLPolicy(`hitl.py:82-189`)、高風險工具 → HITL escalate、Docker sandbox 硬化(`--network=none`/`--cap-drop=ALL`/`read-only` `sandbox.py:219-392`)、destructive=True 強制升 HIGH(57.124)= 結構性限制
- ⚠️ **也重度依賴「偵測」**:RiskyActionDetector 是 **13 條 regex pattern match**(`risky_action_detector.py:84-157`)= 研究說「inherently brittle」的偵測式防線
- ⚠️ **架構模式**:V2 ≈ **context-minimization + guardrail gatekeeping + HITL escalation 混合層防線**,**非** 6 模式中任何單一純結構模式(非 plan-then-execute、非 dual-LLM、非 action-selector);無 plan 層(LLM 直接輸出 tool call),無 dual-LLM(privileged + quarantined)分離
- 💡 **最有價值機會**:6 模式 = 結構性升級菜單。對「agent 攝入不可信輸入(RAG/外部資料)後觸發副作用」威脅,V2 目前靠 regex 偵測 + HITL;研究建議改**結構限制**(如 Dual LLM:quarantined LLM 處理不可信資料、結果符號化、privileged LLM 不直接看原文;或 Plan-Then-Execute:執行期 plan 不可被 injection 改)。對應 cc-parity §4 C 類「Dangerous command detection」缺口,但研究指出**方向應從「加更多 detector」轉向「結構性限制」**

---

## G. End-user UX 層 → ⚠️ 領先框架,但同缺實證
- ✅ **可控性/透明度機制比框架豐富**:4 個 HITL escalate 點(input/between-turns/tool/output ESCALATE,`loop.py:634-1620`)、durable resume、chat-v2 Inspector(Turn Block / 思考過程 / 工具串流 / subagent Tree)、SSE 即時事件;verification-ESCALATE / output-ESCALATE(投遞前暫停)比多數框架細緻
- ⚠️ **但同研究一樣無 UX 對照實證**:無數據證明這些介入點/可視化「量化改善了 end-user 信任或介入效率」
- 💡 **藍海 + 方法論契合**:drive-through 文化能產出業界缺的 agent-UX 實證(A/B 測「有/無 Inspector 思考過程」對信任與介入正確率影響)

---

## 🎯 綜合:最值得關注的 5 個機會(按研究背書強度)

| 優先 | 機會 | 研究背書 | 現況 | 已識別? |
|------|------|---------|------|---------|
| **1** | **顯式任務原語(TodoWrite 式 durable 任務脊椎)** | 發現 11 最高槓桿 | 有 restart 底座、缺 decompose 結構 | ✅ 已有 thin-spike eval,待決定 |
| **2** | **長程「可靠性實測」(pass@k 式重複驗證)** | 發現 9 reliability≠capability | drive-through 是 pass@1 式單次 | ❌ 未識別(研究新增視角) |
| **3** | **安全從「偵測」轉「結構限制」(評估 6 模式)** | 發現 14 restrict not detect | RiskyActionDetector 是 regex 偵測 | ⚠️ 列了 detection 但方向是加 detector |
| **4** | **verification 重試清掉失敗 context(防 self-conditioning)** | 發現 10 錯誤留 context 自我放大 | 目前 append 失敗答案再改 | ❌ 未識別(研究新增視角) |
| **5** | **壓縮階梯化(僅走長 autonomous task 時)** | 發現 5 + CC 5 層 | 單層 75%/turn>30 | ✅ cc-long-running 已點明條件性 |

**兩個 V2 強過研究範例、應守住的地方**:
- **durable 可治理 HITL pause**(發現 7)——比 LangGraph/CC 都重,多租戶 SaaS 正確選擇,別為「學 CC 輕量化」而弱化
- **5-scope 記憶隔離**(發現 12)——比 CC 單一 MEMORY.md 嚴謹,別為學 ACE scoring 而弱化隔離

---

## 後設觀察
V2 內部文件(task-primitive eval、cc-long-running、cc-parity)**已獨立得出與外部研究高度重疊的結論**(任務原語缺口、壓縮階梯、self-continuation、multi-model profile)。這份 deep research 的**增量價值**主要在兩個內部文件還沒涵蓋的學術視角:
1. **發現 9/10「reliability≠capability + self-conditioning」實證** → 給「為何要做可靠性實測、為何 verification 重試別把錯誤留 context」的硬數據依據
2. **發現 14「6 種抗注入結構模式」** → 把「dangerous command detection」方向從「加 detector」修正為「結構限制」

---

## 校正紀錄(Explore agent 偏差)
- Agent 3 報「Cat 10 verification loop 內未啟用」**錯誤** → 實際 in-loop verify gate 存於 `loop.py:1770` `_cat10_verify_gate()` + 修正迴圈 `2617-2687`(預設 2 次)+ verification-ESCALATE;CLAUDE.md 57.98/57.99 drive-through 佐證。Agent 3 grep 用錯關鍵字漏掉
- `max_turns`:loop ctor 預設 **50**(`loop.py:323`),但 chat 主流量 handler 寫死 **8**(`handler.py:710`)→ 主流量邊界是 8
