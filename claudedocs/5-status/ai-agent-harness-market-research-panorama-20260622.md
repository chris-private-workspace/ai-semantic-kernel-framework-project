# AI Agent 系統設計與可靠性 — 2026 市場/研究全景報告(中立)

**Purpose**: 截至 2026 年,AI agent 系統(含 harness 控制/保護框架)在實際設計與開發實作時,如何改善「使用體驗」與「工程可靠性」的最新方向與實證。**中立全景,不對照本項目**(落地對照見姊妹文件)。涵蓋 agent loop 架構、記憶、context compaction、orchestration/multi-agent、retry/self-correction、long-running/durable execution、權限/護欄、可觀測性,以及 end-user UX 層。
**Category / Scope**: Status / External market & academic research panorama (cross-cutting)
**Created**: 2026-06-22
**Last Modified**: 2026-06-22
**Status**: Active (snapshot;基於 deep-research workflow 2026-06-22 跑出的 30 來源 / 148 主張 / 28 對抗驗證)
**Method**: deep-research harness(節流版:6 搜尋角度批次 fan-out + 單票對抗驗證,避 WebSearch 速率限制)→ 26/28 主張通過、2 否決 → 綜合 14 findings。**單票驗證強度弱於預設 3 票**:殺掉的 2 主張可信,通過的 medium 信度主張引用前建議覆核原始來源。
**權威聲明**:本文是外部市場/學術研究筆記,**非 V2 設計權威**。

> **Modification History**
> - 2026-06-22: Add cross-ref to sibling ux-research deep-research run (1-planning)
> - 2026-06-22: Initial creation — deep-research workflow 全景報告(節流版 workflow,WebSearch 速率限制後重跑)

> **姊妹文件**:[`ai-agent-harness-research-vs-v2-mapping-20260622.md`](ai-agent-harness-research-vs-v2-mapping-20260622.md) —— 把本文 14 findings 逐一對照本項目 11+1 範疇 + server-side governance + `max_turns=8` 有界爆發設計(✅/⚠️/❌/💡)。
>
> **🔗 同日第二次 deep-research run（增量補充）**:[agent-harness-ux-research-20260622.md](../1-planning/agent-harness-ux-research-20260622.md)(8 角度版,與本文 ~70% 重疊)。其 net-new(本文未涵蓋):Cat 12 標準化於 OTel GenAI semantic conventions / ACON 量化壓縮目標帶(arXiv 2510.00615) / ICLR2024×EMNLP2024 self-correction 分界線 / MAST + tool-description lint。**矛盾提醒**:該文 §2.2 把「CoT thinking 消除 self-conditioning」誤標 [強],與本文 §被否決 #2(claim 級對抗已否決該 overclaim,vote 0-1)相左——**以本文為準**。

---

## 0. 怎麼讀(證據強度分級)

| 標記 | 意義 |
|------|------|
| 🟢 **實證** | 有 arXiv 受控實驗 / 大規模數據(可重現性較高) |
| 🟡 **共識** | 廠商 blog / 框架設計觀點(primary 但第一方、含立場) |
| 🔴 **開放/爭議** | 被廣泛討論但缺對照實驗,或在驗證中被否決 |

**一句話**:2026 年主戰場已從「agent **能不能做**」轉向「agent **能不能可靠地長時間做**」。**工程可靠性層有最強實證;End-user UX 層幾乎無獨立硬實證**(關鍵負面發現)。

---

## Part A — 工程架構與可靠性層(證據最強)

### A1. Agent 本質定義 🟢🟡
Anthropic「Building Effective Agents」二分(2026 仍最廣引用):
- **Workflow** = LLM/工具透過**預定義 code path** 編排;**Agent** = LLM **動態自主**導引流程與工具,自掌如何完成
- 關鍵:執行每一步都要從環境取得 **"ground truth"**(工具結果/程式執行)評估進度 → ReAct/TAO loop 核心
- 來源:Anthropic – Building Effective Agents(primary,vote 3-0)

### A2. 編排模式 🟡
| 模式 | 適用 | 證據 |
|------|------|------|
| 先用最簡方案、慎用框架 | 多數 | 🟡 直接用 LLM API;框架增抽象層、遮蔽 prompt、增除錯難度、誘使過度複雜。**觀點性建議非實證** |
| Evaluator-Optimizer | 有清楚評估標準、迭代有可衡量價值 | 🟡 一 LLM 產生、另一 LLM 評估回饋迴圈 |
| Orchestrator-Worker | 可並行子任務 | 🟡🟢 見 A2.1 |
| Handoff(委派) | agent 各有領域專長 | 🟢 OpenAI Agents SDK:**handoff 機制上就是 tool call**(委派 Refund Agent = 呼叫 `transfer_to_refund_agent`),agent 間委派重用一般 tool-use 機制 |

**A2.1 Multi-agent 實證與代價 🟡**
- ✅ Anthropic orchestrator-worker(Opus 4 lead + Sonnet 4 subagent)內部研究 eval **比單一 Opus 4 高 90.2%**
- ⚠️ 三大保留:(1) **~15× token 代價**(single-agent ~4×,vs chat);(2) 90.2% 為**內部不可重現** eval,且 ~80% 變異由 token 用量解釋(compute confound);(3) **實時 agent 間協調仍是開放問題**,需共享 context / 高互依領域(如多數 coding)不適用
- 🔴 業界辯論:Cognition「Don't Build Multi-Agents」(2025-06)vs Anthropic「Do — Carefully」→ 2026 趨同共識 = **orchestrator + ephemeral subagent**(主 agent 持完整 context,派短命子 agent 在各自乾淨 window 做隔離子任務)

### A3. ⭐ 長程可靠性瓶頸 — 本報告最強實證群 🟢🟢🟢
**(1) Reliability ≠ Capability,隨任務時長系統性發散**
- 即使**單步準確率近乎完美、知識非限制因素**,執行步數仍會在某點崩潰
- 23,392 episodes、10 模型:mean pass@1 從短任務 **76.3% → 很長任務 52.1%**(掉 24.3pp),且**衰退快於 i.i.d. geometric baseline**(正向 error correlation)
- GPT-4o 在 τ-bench retail:**61% pass@1,但僅 25% pass@8**(連跑 8 次至少失敗一次機率近 75%)
- 💡 含義:**capability benchmark(單次成功率)結構性地對長程可靠性盲目**

**(2) Self-conditioning:"confused agent stays confused"**
- context 含自身**先前錯誤**時,後續準確率**進一步惡化**;**放大模型參數救不了**(Kimi-K2 1026B / DeepSeek-V3 670B / Qwen3-235B 皆易受)
- 💡 含義:**retry 不能只是「重跑」**,錯誤會自我放大

**(3) 任務長度成長趨勢**
- METR:前沿 AI「50% 任務完成時間視野」自 2019 約**每 7 個月翻倍**(2024 後可能加速約 4 個月)
- ⚠️ 透明度:原研究「Claude 3.7 Sonnet ≈ 50 分鐘」具體數字**在對抗驗證中被否決**,只保留翻倍趨勢

- 來源:arXiv:2509.09677(Illusion of Diminishing Returns)、arXiv:2603.29231(Beyond pass@1)、arXiv:2503.14499(METR)

### A4. 可靠性介入手段(哪些有效、哪些有害)
| 手段 | 效果 | 證據 |
|------|------|------|
| **任務拆解 + 邊界重啟 agent** | 該研究稱「最高槓桿」;投影增益 13.1pp(DeepSeek V3)~ 41.5pp(Qwen3 30B) | 🟡 **「假設子任務獨立」的分析投影,非實測**,未計拆解/交接 overhead,屬理想上限 |
| **結構化反思 / self-correction** | 用前步證據診斷工具失敗→提修正後續呼叫。BFCL v3 提升(Qwen3-4B 16.25%→20.75%);Repair@5 6.8%→26.4% | 🟢 有數字、方法嚴謹。**但增益來自 RL 訓練的反思能力,非純 inference-time prompt** |
| **Naive episodic memory(每輪注入的 scratchpad)** | ❌ **從不改善長程,還傷害 10 模型中 6 個**(overhead 吃步數預算 + context 空間) | 🟢 強實證**反對** naive 記憶。⚠️ 限「naive episodic」+「長程」,**不否定**階層摘要/scoped/有 expiration 的重設計記憶 |

> 💡 記憶系統設計警示:**記憶必須精算 per-step overhead 對任務長度的影響**,不能無腦累積。
- 來源:arXiv:2603.29231、arXiv:2509.18847(Failure Makes the Agent Stronger)

### A5. Context Engineering + Compaction 🟢🟡
- **定義**:策展與維護 LLM 推論時「最佳 token 集合」的策略,跨 agent loop 迭代管理 context state
- **動機 context rot**:token 數增加 → 模型從 context 準確召回能力**下降**(根源之一 transformer O(n²) 成對 attention);應把 context 當有限資源 + 有「attention budget」。🟢 有獨立實證(Chroma 2025、Lost-in-the-Middle 2023)
- **Compaction**:摘要接近 window 上限的對話、重啟新 window,**保留架構決策與未解 bug、捨棄冗餘工具輸出** → 使長程執行成為可能
- 來源:Anthropic – Effective Context Engineering

### A6. Durable Execution / 長運行 🟢🟡
- **LangGraph checkpointer**:把 thread graph state 持久化為 checkpoints → 中斷後恢復、失敗復原、跨互動記憶,支援對話連續性、**HITL、time travel、容錯**
- ⚠️ 保留:(1) resume 需配 checkpointer、跨 thread 記憶要另設 store(非自動);(2) resume 時 checkpoint 後 node 會**重跑**(LLM/API 重發)→ 需**冪等**;(3) 🔴 有異議來源(Diagrid)主張弱於 Temporal 等真正 durable-execution 引擎
- 🔴 新興:DBOS、Temporal 等「crashproof agent」durable execution 引擎被熱烈討論
- 來源:LangGraph – Durable Execution、Diagrid(異議)

### A7. 安全護欄 / Harness Control 🟢
核心原則:**「限制(restrict)而非僅偵測(detect)」** —— 一旦 agent 攝入**不可信輸入**,必須在**結構上使該輸入不可能觸發任何有副作用的動作**(偵測/對抗訓練「inherently brittle」)。
**6 種抗 prompt-injection 設計模式**(各以「agent 通用性」換「安全保證」):
1. **Action-Selector**(對 injection 免疫,但失去 LLM 模糊搜尋能力)
2. **Plan-Then-Execute**(control-flow integrity 保護)
3. **LLM Map-Reduce**
4. **Dual LLM**(privileged + quarantined 分離,結果符號化儲存)
5. **Code-Then-Execute**
6. **Context-Minimization**
- 💡 含義:**安全是架構問題,不是過濾器問題**
- 來源:arXiv:2506.08837(Design Patterns for Securing LLM Agents against Prompt Injections;作者群 AgentDojo / Microsoft);輔 OWASP Agentic AI、Claude Code Sandboxing

---

## Part B — End-user UX 層 ⚠️🔴(證據最弱)

**關鍵負面發現**:UX 層**幾乎無獨立硬實證**。透明度、信任建立、進度可視化、錯誤處理 UX、agent 協作介面,只能**間接從框架設計層的能力**推得「被廣泛採用」,**非**有對照實驗證明改善 end-user 體驗。

被廣泛採用的可控性/透明度機制(🟡 共識非實證):
- HITL 介入點設計(LangGraph、Microsoft Magentic-UI)
- Durable resume、Time travel(回溯重新分支)、Handoff 可視化、思考過程/工具呼叫串流呈現
- 來源:Microsoft – Magentic-UI Report、Anthropic – Measuring Agent Autonomy

> 💡 **這是「藍海」**:UX 領域被熱烈討論卻缺對照研究,適合用 drive-through 方法論產出這類證據。

---

## 🔴 被否決 / 有爭議的主張(透明度)

對抗驗證殺掉 2 個流傳說法:
1. ❌ **「前沿模型時間視野 ≈ 50 分鐘」**(具體數字證據不足;只保留「每 7 個月翻倍」趨勢)— source: arXiv:2503.14499,vote 0-1
2. ❌ **「thinking / extended reasoning 完全消除 self-conditioning」**— vote 0-1。結合「self-conditioning 不受模型大小緩解」這個已確認發現,意味 **「延伸推理能否救長程可靠性」仍是有爭議、未確立的開放問題**

---

## 🔭 五大開放問題

1. **UX 硬實證缺口**:幾乎無對照實驗證明特定透明度/HITL/可視化設計如何量化改善 end-user 信任與介入效率
2. **Reasoning/thinking 模型能否真正解決長程可靠性與 self-conditioning?**(有爭議)
3. **任務拆解的「實測」增益?**(13-42pp 為理論投影,未計 overhead)
4. **記憶系統正確設計**:naive scratchpad 在長程有害,但階層摘要/scoped/有 expiration 的重設計能否帶來淨增益?(論文明列為未來工作)
5. **異步 multi-agent 編排**(AutoGen v0.4、Google ADK A2A)能否突破「實時協調是開放問題」並克服 ~15× token 代價?

---

## 14 Findings 一覽(供姊妹文件對照引用)

| # | 發現(摘) | 信度 | 主要來源 |
|---|----------|------|---------|
| 1 | Agent = while-loop + ground truth 回注;workflow/agent 二分 | high | Anthropic BEA |
| 2 | 先用最簡方案、慎用框架 | medium | Anthropic BEA |
| 3 | Evaluator-optimizer 模式 | medium | Anthropic BEA |
| 4 | Orchestrator-worker multi-agent 90.2% / 15× token | medium | Anthropic multi-agent |
| 5 | Context engineering + context rot + compaction | high | Anthropic context-eng |
| 6 | Handoff = tool call 機制 | high | OpenAI Agents SDK |
| 7 | Durable execution(checkpointer)| high | LangGraph docs |
| 8 | 任務長度每 7 個月翻倍 | high | arXiv:2503.14499 |
| 9 | ⭐ reliability≠capability、pass@1 vs pass@8 發散 | high | arXiv:2509.09677 + 2603.29231 |
| 10 | ⭐ self-conditioning(放大模型救不了)| high | arXiv:2509.09677 |
| 11 | ⭐ 任務拆解 + 邊界重啟 = 最高槓桿 | medium | arXiv:2603.29231 |
| 12 | Naive episodic memory scratchpad 有害 | medium | arXiv:2603.29231 |
| 13 | 結構化反思提升可靠性(RL-trained)| high | arXiv:2509.18847 |
| 14 | ⭐ 安全「限制非偵測」+ 6 模式 | high | arXiv:2506.08837 |

---

## 來源清單(30 fetched;依角度 + 品質)

**Primary(高品質)**
- Anthropic: [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) · [Multi-Agent Research System](https://www.anthropic.com/engineering/multi-agent-research-system) · [Effective Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) · [Measuring Agent Autonomy](https://www.anthropic.com/research/measuring-agent-autonomy) · [Claude Code Sandboxing](https://anthropic.com/engineering/claude-code-sandboxing) · [Claude Code Security](https://code.claude.com/docs/en/security)
- OpenAI: [Agents SDK – Handoffs](https://openai.github.io/openai-agents-python/handoffs/)
- LangChain: [LangGraph – Durable Execution](https://docs.langchain.com/oss/python/langgraph/durable-execution)
- arXiv: [2503.14499 METR](https://arxiv.org/abs/2503.14499) · [2509.09677 Illusion of Diminishing Returns](https://arxiv.org/html/2509.09677v3) · [2603.29231 Beyond pass@1](https://arxiv.org/pdf/2603.29231) · [2509.18847 Failure Makes the Agent Stronger](https://arxiv.org/pdf/2509.18847) · [2506.08837 Securing LLM Agents](https://arxiv.org/abs/2506.08837) · [2406.12045](https://arxiv.org/pdf/2406.12045) · [2503.13657](https://arxiv.org/abs/2503.13657)
- Microsoft: [Magentic-UI Report](https://www.microsoft.com/en-us/research/wp-content/uploads/2025/07/magentic-ui-report.pdf)
- Sierra: [tau-bench](https://sierra.ai/blog/tau-bench-shaping-development-evaluation-agents)

**Secondary / Blog(佐證或觀點)**
- [Cognition – Don't Build Multi-Agents](https://cognition.ai/blog/dont-build-multi-agents)、[LangChain – Planning Agents](https://www.langchain.com/blog/planning-agents)、[Palo Alto – OWASP Agentic AI](https://www.paloaltonetworks.com/blog/cloud-security/owasp-agentic-ai-security/)、[Diagrid – Checkpoints ≠ Durable Execution](https://www.diagrid.io/blog/checkpoints-are-not-durable-execution-why-langgraph-crewai-google-adk-and-others-fall-short-for-production-agent-workflows)、[DBOS – Crashproof AI Agents](https://www.dbos.dev/blog/durable-execution-crashproof-ai-agents)、Kili / DigitalApplied / agentmarketcap / machinelearningmastery / datasciencedojo(benchmark/memory/loop 綜述,blog 品質)

---

## 方法限制(誠實標註)

1. **證據不對稱**:工程可靠性層(A)有最強實證(3 篇近期 arXiv);**UX 層(B)幾乎無獨立硬實證**——只能從框架能力間接推得。
2. **單票對抗驗證**(本次因 WebSearch 速率限制把預設 3 票降為 1 票):殺掉的 2 主張可信,通過的 medium 信度主張引用前建議覆核。
3. **廠商 blog 為第一方**(Anthropic/OpenAI/LangChain),部分含觀點性建議,非中立 benchmark。
4. **時效性**:multi-agent 實時協調為開放問題的論斷基於 2025-06 文章;異步編排(AutoGen v0.4、Google ADK A2A)快速演進中。
5. **數字限定**:任務拆解 13-42pp 為「假設子任務獨立」的分析投影非實測;結構化反思增益來自 RL 訓練(非純 prompt);memory scaffold 負面結果限「naive episodic」+「長程」。
6. **benchmark 覆蓋**:已驗證 claim 中僅 τ-bench / BFCL v3 有具體數據;SWE-bench / AgentBench / GAIA 雖被點名但本批未取得數據。

---

## 統計
- 搜尋角度 6 · 抓取來源 30(primary ~16)· 萃取主張 148 · 對抗驗證 28(確認 26 / 否決 2)· 綜合 14 findings
- 投入:66 agent · ~1,030 萬 token · ~34 分鐘(節流版 workflow)
