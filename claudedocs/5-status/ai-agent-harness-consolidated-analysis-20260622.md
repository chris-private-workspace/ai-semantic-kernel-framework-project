# AI Agent Harness — 使用體驗與工程可靠性綜合分析(2024–2026)

**Purpose**: 把同日 3 份 deep-research 產出整合成**單一完整、全面的主分析文件**:中立市場/學術全景(實證方向)+ V2 11+1 範疇落地對照(✅/⚠️/❌/💡 + file:line)+ 跨維度主題 + 優先機會 + 證據品質。讀這一份 = 讀完三份的綜合。
**Category / Scope**: Status / Consolidated research + V2 mapping (cross-cutting)
**Created**: 2026-06-22
**Last Modified**: 2026-06-22
**Status**: Active (snapshot)
**Grounding**: (1) claim 級對抗驗證 deep-research(28 claim / 14 findings)+(2) 8 角度輕驗證 deep-research(41 來源 / 66 findings)+(3) 3 個 Explore agent 對 `backend/src/agent_harness/` 的 file:line 勘查 + 本項目權威文件(task-primitive eval / cc-long-running / cc-parity)。

> **Modification History**
> - 2026-06-22: Initial creation — 整合 panorama + mapping + ux-research 三份為單一主文件;調和 self-conditioning×thinking 矛盾;統一信度系統

> **本文整合的 3 份來源(均保留,作為細節/grounding 後備)**
> - [`ai-agent-harness-market-research-panorama-20260622.md`](ai-agent-harness-market-research-panorama-20260622.md) — 中立全景,**28 條 claim 級對抗驗證**(信度最嚴)
> - [`ai-agent-harness-research-vs-v2-mapping-20260622.md`](ai-agent-harness-research-vs-v2-mapping-20260622.md) — 14 findings × V2,**file:line grounding**(落地最強)
> - [`../1-planning/agent-harness-ux-research-20260622.md`](../1-planning/agent-harness-ux-research-20260622.md) — 8 角度 / 41 來源,**per-Cat 可操作 pattern + 證據品質審查最細**

---

## 0. 怎麼讀(統一信度系統)

兩次 research 用了不同分級,本文統一為:

| 標記 | 意義 | 證據門檻 |
|------|------|---------|
| 🟢 **實證** | arXiv 受控實驗 / 大規模數據,且已 spot-check 或 claim 級對抗驗證通過 | 高 |
| 🟡 **共識/自報** | 廠商 blog / 單篇 preprint self-report / 觀點性最佳實踐 | 中(方向可信,數字 hedge) |
| 🔴 **開放/爭議** | 缺對照實驗、citation 未核實,或對抗驗證否決 | 低(當假設,勿當結論) |

落地對照標記:✅ 已具備 · ⚠️ 部分 · ❌ 缺口 · 💡 機會。

> ⚠️ **全文通則**:多數「可靠性數字」(90.2% / 15× / 93% / 40% / 22.7% / 17.2x)來自 Anthropic 自家 eval 或單篇 preprint self-report,是 **directional / order-of-magnitude,非外部可重現 benchmark**。引用前先讀 §6 證據品質。

---

## 1. 執行摘要

截至 2026 年,改善 agent 系統「使用體驗」與「工程可靠性」的主戰場,已從「**能不能做**」轉向「**能不能可靠地長時間做**」。九條最高價值且有(不同強度)實證支持的方向:

1. **Bounded single TAO/ReAct loop 是有實證背書的預設架構**;multi-agent 的優勢主要來自 aggregate compute(token usage 單獨解釋 ~80% 變異)而非 orchestration 魔法,subagent 應 **gate 在 task coupling + token budget 之後**,而非反射式提升準確率。🟢
2. **長程任務失敗主要是 EXECUTION 而非 PLANNING 問題**——即使給對的 plan + knowledge,單步近乎完美的模型仍在 ~15 turns 內掉到 50% 以下;更好的 planner 救不了多輪退化,**harness 必須外部化狀態 + 在每個 bounded burst 重新 ground**。🟢
3. **Reliability ≠ Capability,且兩者隨任務時長系統性發散**;`pass^k`(k 次重複一致性)應成為平台主要 eval 指標,而非單次 `pass@1` / drive-through-once(τ-bench:GPT-4o ~61% pass@1 但 pass^8 <25%)。🟢
4. **Self-correction 必須由 EXTERNAL verifiable signal 驅動**(tool error / test pass-fail / key-condition check / 獨立 judge);裸 re-prompt 不只中性、會把對的答案改錯。ICLR2024「Cannot」× EMNLP2024「Can with Key-Condition」是可引用的分界線。🟢
5. **Self-conditioning(自己的錯誤留在 context 招致更多錯誤)不被 model scale 修好**——retry / verification 重試**不能把失敗 trace 留在 context**。🟢(但「thinking 完全消除 self-conditioning」是 overclaim,見 §7)
6. **Context rot 是 length-driven**(非只 relevance-driven);compaction 應**分層、依風險排序、有量化目標帶**:tool-result clearing → deterministic eviction → 才 LLM summarization(ACON:削 26–54% peak token 不損準確率)。🟢
7. **安全要「限制(restrict)而非僅偵測(detect)」**——agent 攝入不可信輸入後,須在**結構上**使其無法觸發有副作用動作(6 種抗注入設計模式);偵測式 guardrail(regex / LLM judge)「inherently brittle」,LLM judge 不能是唯一 gate。🟢
8. **Approval fatigue 是已量測的一階風險**:使用者批准 ~93% permission prompt → HITL gate 只在高 blast-radius(tier-3)動作觸發,配 **deny-first** guardrail 而非逐動作確認。🟡(單一 vendor 統計但 load-bearing)
9. **Cat 12 tracing 應標準化在 OpenTelemetry GenAI semantic conventions**(invoke_agent → chat → execute_tool;content capture 預設 off),天然對齊 provider-neutrality + multi-tenant PII/GDPR。🟢

**對 V2 的一句話**:V2 在**可靠性「機械底座」與「企業治理」上普遍領先研究的範例**(durable HITL pause、多租戶 guardrail、5-scope memory、drive-through 文化),但在**長程可靠性的「實測驗證(pass^k)」、「結構化任務脊椎(task primitive)」、「安全結構限制」、「壓縮階梯化」、「OTel 標準化」上有明確空缺**——恰好都是研究指出的高槓桿區。

---

## 2. 研究全景(8 維度,中立)

### 2.1 Agent loop 架構與控制模式 🟢
- 相同 thinking-token budget 下,single-agent 在 multi-hop reasoning **持平或略勝** sequential MAS(FRAMES 0.680 vs 0.670;MuSiQue 4-hop 0.407 vs 0.320)——margin 小,正確描述是「match or modestly beats」🟢
- Agent = **LLM 在環境回饋下於 `while`-loop 用工具**;每步取 **ground truth**(工具結果/程式執行)評估進度。Anthropic 二分:**workflow**(預定義 code path)vs **agent**(LLM 動態自主)🟢
- 架構由 task 決定:**「the task picks the architecture」**——isolated subagent 適合 independent/parallel,shared-state/dependency-heavy 任務會 break 🟢
- 強模型上 plan-then-act 持平或略勝 interleaved ReAct;goal-state reflection(ReflAct)勝 baseline ~33.1% → 建議每 turn 錨定 goal/state 而非冗長 CoT 🟡
- End-to-end behavioral verification 是獨立必要的 loop step(agent 常改完 code 卻沒注意 feature 沒 work)→ 獨立佐證 drive-through 約束 🟡

### 2.2 Intent / Planning / Task decomposition 🟢
- **長程退化即使給對 plan + knowledge 仍發生**(Qwen3-32B H₀.₅ ~15 turns;frontier without thinking 多在 ~4 步失敗)🟢
- **Self-conditioning**:注入更多 prior error 單調惡化 turn-100 準確率,200B+ 仍易受 🟢
- **Thinking/CoT 是執行長度的最大單一槓桿**:GPT-5(thinking)維持 2,176 sequential steps、Claude-4 Sonnet 432 steps,without thinking「a few steps」🟢 → 支持 provider-neutral thinking-budget toggle 作一級旋鈕。**但「CoT 完全消除 self-conditioning」是 overclaim(見 §7,降為 🔴 開放)**
- **Explicit externalized task primitive 是 load-bearing 的反 early-stop 機制**:Anthropic harness 用 initializer 寫 200+ feature JSON(全預標 failing 作完成準則)+ progress 檔 + one-feature-at-a-time + 結構性拒絕 early termination 🟡;Claude Code「Tasks」以 **DAG(含 explicit blocking)** 建模,比 flat list 更具表達力 🟡
- Receding-horizon replanning(只 commit 下一個 action、每 transition 後 replan)在 noisy 評估下勝 brittle 長期 commitment 🟡(原理強、特定 paper 未核實)

### 2.3 Multi-agent orchestration 與 delegation 🟢🟡
- Orchestrator-worker(Opus 4 lead + Sonnet 4 subagents)勝 single Opus 4 達 **90.2%**,但 **token usage 解釋 ~80% 變異**🟡(內部不可重現 eval)
- 成本:multi-agent **~15× chat token**、single ~4×;只建議 outcome value 超過 token cost 時用 🟢
- 不適合 tightly-coupled work(多 inter-agent dependency / 需共享 context);Anthropic 點名 **coding 為弱契合** 🟢
- 拓樸:decentralized/swarm 放大錯誤 ~17.2x,centralized orchestrator 收斂到 ~4.4x 🟡(單篇 2026 preprint,數字未核實);per-step verification 勝 final-only 🟡
- **MAST**(1,600+ trace、7 框架、14 failure mode、3 類:spec/design、inter-agent misalignment、verification/termination):**多數失敗是 orchestration/spec bug 而非 base-model 弱** 🟢(NeurIPS 2025,Kappa 0.88)
- τ-bench:0–1 distractor 時 single-agent 勝 supervisor/swarm,2+ distractor 才反轉;supervisor 損失來自 translation overhead + handoff message 汙染 worker context → **strip routing/handoff metadata 出 worker context** 🟡
- **Handoff = tool call 機制**:OpenAI Agents SDK 把委派做成 `transfer_to_xxx` tool call,重用一般 tool-use 機制 🟢
- 用模型改寫 flawed tool description → 後續任務完成時間 **~40% 下降** 🟡(單一 Anthropic 數據點,量級當 anecdotal)

### 2.4 Tool execution + verification / self-correction 🟢
- **Intrinsic self-correction(無 external signal)一致失敗、常退化準確率**,會把對的答案改錯(ICLR 2024)🟢
- **分界線 = key-condition verification 的存在**:有則 LLM 可 self-correct,無則不能(EMNLP 2024)→ verifier 應檢查 task 的 **key constraint**(schema / required field / tool-arg constraint),而非「這答案好嗎」🟢
- Evaluator-optimizer 僅在三條件成立時建議:有明確準則 / 迭代有可量測價值 / evaluator 能給有用回饋 🟡(Anthropic guidance)
- 對 tool error 的 **structured reflection**(先診斷具體錯誤再 retry;taxonomy:invocation / parameter / wrong-tool / failed-API)可量測強化可靠性(BFCL v3:Qwen3-4B 16.25%→20.75%;Repair@5 6.8%→26.4%)🟢——**但增益部分來自 RL training,scope 限 trained-reflection regime**
- Tool-use eval 已成熟到 mirror-real-API 規模(StableToolBench / MirrorAPI ~7,000+ API)→ 支持 golden-fixture + `@pytest.mark.benchmark` regression 🟡

### 2.5 Long-running:memory + context / compaction 🟢
- **Context rot**:window token 數增加 → recall 準確率下降(歸因 n² attention + 多在較短序列訓練);Anthropic 稱 context engineering 為 agent engineer「#1 job」🟢
- 三 named pattern:(1) **compaction**(摘要近滿後 reinitiate,保留架構決策/未解 bug/實作細節)、(2) **structured note-taking**(外部 memory)、(3) **sub-agent isolation**(只回 1,000–2,000 token 摘要)🟢
- **Tool-result clearing 是最安全、最低風險的 compaction**(已是 Claude Developer Platform 一級 feature)🟢
- **ACON**(arXiv 2510.00615,Microsoft,已驗證):15+ step agent 削 **26–54% peak token** 且 success 持平或改善;distilled compressor 保留 **>95%** 效能、**~99%** API 成本下降 → 支持 per-tenant/turn 跑便宜 distilled model 的 compactor 🟢
- **Lost-in-the-middle**:U-shape positional bias(primacy + recency over middle),可 calibrate → 把最相關 memory + 當前 task 放 context 邊緣 🟢
- **Just-in-time retrieval**(保留 lightweight identifier、runtime 用 tool hydrate)是建議的 memory pattern 🟡
- Naive episodic memory scratchpad(每輪注入、無限成長)**從不改善長程,還傷害 10 模型中 6 個** 🟢——⚠️ 限「naive episodic」+「長程」,**不否定** scoped / 有 expiration / 階層摘要的重設計記憶
- Structured/typed eviction(typed dependency graph + deterministic graduated eviction)被提議優於 summarization 🔴(citation 2606.11213 未核實,原理可信)

### 2.6 HITL / permissions / guardrails / 企業治理 🟢🟡
- **Approval fatigue**:使用者批准 **~93%** permission prompt → interrupt 只在 real-downside 動作觸發 🟡(單一 vendor 內部統計,load-bearing)
- 兩段式 classifier:full pipeline ~0.4% FP 但 **~17% FN**(「the honest number」)→ **classifier 是 defense-in-depth 一層,永不替代 sandbox** 🟢
- **Tiered permission**:(1) safe-tool allowlist auto-run、(2) in-project file ops(version-control 可審)、(3) transcript-classifier-gated shell/external-API → **只有 tier-3 到 gate** 🟡
- **Defense-in-depth 雙向**:input-side prompt-injection probe(screen tool OUTPUTS 進 context)+ output-side classifier(screen tool CALLS before execution),sandbox 作 containment 🟡
- **安全核心原則:「限制非偵測」**——agent 攝入不可信輸入後,須在結構上使其無法觸發有副作用動作。**6 種抗注入設計模式**(各以 agent 通用性換安全保證):Action-Selector / Plan-Then-Execute / LLM Map-Reduce / **Dual LLM**(privileged + quarantined 分離、結果符號化)/ Code-Then-Execute / Context-Minimization 🟢(arXiv 2506.08837,AgentDojo/Microsoft)
- **LLM judge 不能是唯一 gate**(R-Judge:8 LLM risk-awareness「遠非完美」)→ rules-based + LLM-judge + 確定性 human escalation 🟢
- HITL pause/resume **本質是 checkpointing**;四種 decision type:approve / reject / **review-and-edit-state** / review-tool-call(「edit before proceeding」超越二元)🟢
- Runtime monitoring 必要:post-hoc sandbox benchmark(AgentHarm/ToolEmu/R-Judge)在 action 後評估、無法 production 阻止 harm → guardrail 必須 **in-loop pre-execution 攔截** 🟡

### 2.7 Observability / tracing / evaluation 🟢
- **pass^k 為主要指標**:τ-bench GPT-4o ~61% pass@1 retail 但 **pass^8 <25%** 🟢
- Reliability 隨複雜度 **super-linear 退化、對 pass@1 不可見**;建議 eval harness 加 perturbation(ε)+ infra-fault(λ)軸 🟡(citation 有 conflate,技術結論成立)
- **OTel GenAI semantic conventions**(CNCF SIG since 2024-04):標準 span 階層 invoke_agent → chat → execute_tool;`gen_ai.*` attribute;**`finish_reasons`=`tool_calls` vs `stop` 與 while-true loop stop_reason 1:1**;**content capture 預設 off**(`captureContent` opt-in)對齊 PII/GDPR 🟢
- **MAST 14 failure mode** 作 negative-test catalog;附 validated LLM-as-a-Judge pipeline 可自動分類 trace 🟢
- Behavioral consistency 是獨立可量測軸(agent 會「跟自己不同意」),應與 task success 分開追蹤 🟡

### 2.8 Agent UX:trust / transparency / controllability 🟢🔴
- **Auto-approve rate 從 <50 session 的 ~20% 升到 750 session 的 >40%**;整體 ~93% 批准 → per-action confirmation 作唯一 safety 機制「behaviorally unreliable」🟢(arXiv 2604.14228 已逐字核實)
- **Graduated trust spectrum**(plan / default / acceptEdits / auto / dontAsk / bypassPermissions)+ **deny-first**:deny rule 無條件勝 allow rule,未識別動作 escalate 而非靜默執行(fail-closed)🟢
- **Denial 是 routing signal 不是 hard stop**:把 denial reason 餵回 loop 讓下一輪 re-plan(對應 verification-ESCALATE coach-retry)🟢
- File-based append-only transparency(可讀/可編/可版本控制 config + JSONL transcript)以表達力換 auditability + user control → 對 DB-backed memory 是張力:**用 inspector UI 暴露 agent 的 effective context**(注入的 memory layer、compaction summary)🟢
- 串流 discrete progress state(done/running/blocked/next)讓使用者及早抓問題 🟡(部分特定引述 weak/mis-sourced,streaming-state 半段靠 arXiv 2604.14228 存活)
- Capability amplification 有 comprehension cost:~27% Claude-Code-assisted task 是沒工具不會嘗試的工作,但 AI-assisted developer comprehension test 低 17% → **UX 要 build operator understanding,不只 throughput** 🟢(兩數字已逐字核實,但勿單一過度倚賴)
- Binary confidence indicator / 「going silent erodes trust」🔴(agentic-design.ai 來源 specifics 未在頁面找到,方向合理但勿引此來源)

---

## 3. V2 落地對照(11+1 範疇,✅/⚠️/❌/💡 + file:line)

> 驗證層級:**程式碼 grounding(file:line)**,非 drive-through。標 ✅ 者若要宣稱「使用者真的能用」,以 `chat-v2-agent-loop-capability-drivethrough-20260618.md` 為準。

### 計分卡

| 範疇 | 判定 | 一句話 |
|------|------|--------|
| Cat 1 Orchestrator Loop | ✅ + 💡 | while-true + ground truth 回注齊;缺 task primitive |
| Cat 2 Tool Layer | ✅ + 💡 | JSON-schema ToolSpec + Docker sandbox 硬化;可加 structured-error reflection + tool-desc lint |
| Cat 3 Memory | ✅⚠️ | 5-scope × 3-timescale(semantic STUB);避開 naive scratchpad,但每輪檢索有 overhead |
| Cat 4 Context Mgmt | ⚠️ + 💡 | 單層 compaction + masking + prompt cache;缺分層階梯 + 量化目標 |
| Cat 5 Prompt Construction | ✅ + 💡 | 單一 PromptBuilder 入口;可加 positional ordering |
| Cat 6 Output Parsing | ✅ | native tool calls;可標準化 finish_reasons |
| Cat 7 State Mgmt | ✅ | transient/durable 分離 + checkpointer;可補 edit-before-proceed |
| Cat 8 Error Handling | ✅⚠️ | retry matrix + circuit breaker + budget;教練式重試但 self-conditioning 殘留風險 |
| Cat 9 Guardrails & Safety | ⚠️ + 💡 | 混合層防線(含 regex 偵測);可往「結構限制」6 模式升級 |
| Cat 10 Verification | ✅ + 💡 | in-loop verify gate + self-correction;可改 key-condition verifier + pass^k |
| Cat 11 Subagent | ✅ + 💡 | FORK/TEAMMATE/AS_TOOL 真子 loop,深度=1;可加 coupling-based 路由 + clean context |
| Cat 12 Observability | ✅ + 💡 | TraceContext + OTel wrapper;可標準化在 GenAI semantic conventions |

### Cat 1 — Orchestrator Loop ✅ + 💡
- ✅ 主迴圈 `while True:` 由 stop_reason 驅動(`loop.py:2074`),非固定步 pipeline → 避開 AP-1;工具結果 `Message(role="tool")` 回注 + `turn_count++` continue(`loop.py:2791-3110`)= 每步 ground truth
- ✅ 機械底座 = 研究的「邊界重啟」:`max_turns=8` 有界爆發(`handler.py:710`;loop ctor 預設 50 `loop.py:323`)+ 跨輪 rehydration(`DBMessageStore.load()` `message_store.py:93-113`、`loop.py:1937-1947`)
- ❌💡 **缺 explicit task primitive**(`task-primitive-eval` §1.2:無 `LoopState.plan` / `tasks:[{id,status}]`)→ 研究發現 2.2 指其為 load-bearing 反 early-stop;若做,**DAG(含 explicit blocking)優於 flat list**,契合 fork/handoff + HITL gating;走 thin spike(DB-backed store + run-start rehydrate)
- 💡 可採納:每 turn 錨定 goal/state(ReflAct)而非冗長 CoT;denial-as-routing-signal(HITL REJECT/guardrail block 把 denial reason append 成 observation 讓下輪 re-plan);sibling abort controller(同批 tool 一個 error 殺掉同批 in-flight)

### Cat 2 — Tool Layer ✅ + 💡
- ✅ ToolSpec = JSON Schema Draft 2020-12 register-time 驗證(`registry.py`);DockerSandbox 硬化(`--network=none`/`--cap-drop=ALL`/`read-only`/uid=65534/pids-limit `sandbox.py:219-392`);risk level + ToolHITLPolicy(`hitl.py`)
- 💡 可採納:**tool error structured reflection**——on error 把 STRUCTURED error(invocation/parameter/wrong-tool/failed-API taxonomy)餵回 loop 作 observation(這正是 self-correction provably helps 的 regime);**tool-description lint/review step**(~40% 提速數據點,質性強);golden-fixture + `@pytest.mark.benchmark` 鏡像 StableToolBench

### Cat 3 — Memory ✅⚠️
- ✅ 5 scope(system/tenant/role/user/session)× 3 time scale(`memory/_abc.py:46-66`);**非有害 naive scratchpad**:summary 上限 200 字元 + per-turn 2000-token budget cap(低 confidence 先砍 `builder.py:246-257`、`453-520`)= 研究建議的「scoped + expiration + 預算化」重設計
- ⚠️ 仍付每輪檢索+注入成本(query-time 固定檢索);**semantic time scale 是 STUB**(Qdrant 回空,51.2)→ 實際只有 2 個 time scale 運作
- 💡 可採納:**just-in-time / reference-based retrieval**(存 identifier,runtime 用 tool hydrate);固定 subagent return 契約為 1,000–2,000 token condensed summary

### Cat 4 — Context Mgmt ⚠️ + 💡(高優先)
- ✅ StructuralCompactor(`structural.py:104-207`)+ observation masking(舊工具結果墓碑化 `observation_masker.py`)+ prompt caching(`cache_manager.py:49-127`,tenant-first hash)
- ⚠️ **單層**:token>75% **或** turn>30(`compactor/_abc.py:60-74`),chat 還要 ≥3 user turns 才實際壓。研究 + cc-long-running 都指出 CC 是 **5 層階梯**
- 💡 **分層、依風險排序**(研究強共識):(1) tool-result clearing 最先(最低損、無同步 LLM 呼叫)→(2) deterministic/typed eviction(審計友善)→(3) 才 lossy LLM summarization;**量化目標帶 ACON 削 ~25–55% peak token 不損準確率**;compaction 跑 cheap distilled model(對應 multi-model profile)
- 💡 條件性:5 層對短 chat 是過度工程,**只在走長 autonomous task 時才需要**(cc-long-running 已點明「放寬 max_turns 前先補壓縮階梯」)

### Cat 5 — Prompt Construction ✅ + 💡
- ✅ 單一 PromptBuilder 入口(`builder.py:169-351`,AP-8),memory layers 注入有測試
- 💡 可採納:**positional ordering**——decision-relevant 內容放 primacy/recency(lost-in-the-middle);goal-state anchoring 入 system/turn prompt

### Cat 6 — Output Parsing ✅
- ✅ native tool calls、無 regex(`parser.py:56-98`)
- 💡 以 `finish_reasons`(`stop` vs `tool_calls`)作 stop_reason 來源並標準化命名(OTel),使 telemetry 可流入任何 APM

### Cat 7 — State Mgmt ✅
- ✅ DefaultReducer sole-mutator(`reducer.py:69-166`)+ DBCheckpointer transient/durable 分離(`checkpointer.py:94-281`);HITL pause/resume = checkpointing 本質
- 💡 補上四種 HITL decision type 的 **review-and-edit-state**(「edit before proceeding」超越二元 approve/reject)作 resume API 契約

### Cat 8 — Error Handling ✅⚠️
- ✅ retry matrix(`retry.py:71-82`:TRANSIENT max3 / LLM_RECOVERABLE max2 / HITL/FATAL max0)+ circuit_breaker(3 態)+ tenant error budget + terminator(優先序);工具失敗合成帶診斷 ToolResult(`loop.py:2976-2983`)= 研究「retry 要帶診斷」
- ⚠️💡 **self-conditioning 殘留風險**:verification 修正迴圈把失敗答案 + 修正提示一起 append 進 context 再 continue(`loop.py:2617-2626`);研究示「context 留著自己的錯誤 → 後續惡化,放大模型救不了」→ 💡 評估重試時**清掉失敗答案**(只留「目標 + 為何上次不對」精煉版)
- 💡 模組級 failure attribution(memory/reflection/planning/action)餵 structured replanning 而非 blind retry

### Cat 9 — Guardrails & Safety ⚠️ + 💡(高優先)
- ✅「限制」部分:capability matrix(8 能力 role/scope `capability_matrix.py`)+ per-tenant HITLPolicy(`hitl.py:82-189`)+ 高風險 → HITL escalate + Docker sandbox + destructive→HIGH(57.124);4 個 escalate 點(input/between-turns/tool/output `loop.py:634-1620`)
- ⚠️ **重度依賴「偵測」**:RiskyActionDetector = 13 條 regex(`risky_action_detector.py:84-157`)= 研究說「inherently brittle」;架構 ≈ context-minimization + guardrail gatekeeping + HITL escalation 混合層,**非** 6 模式任何單一純結構模式(無 plan 層、無 dual-LLM)
- 💡 **最有價值升級**:對「不可信輸入(RAG/外部資料)觸發副作用」威脅,從「加 detector」轉「結構限制」(Dual LLM:quarantined 處理不可信、結果符號化、privileged 不直接看原文;或 Plan-Then-Execute:執行期 plan 不可被 injection 改);雙向 screening(probe tool OUTPUTS + classifier tool CALLS);LLM judge 要 strip agent 自己 reasoning 防 self-justification;deny rule 無條件勝 allow + unknown tool fail-closed

### Cat 10 — Verification Loops ✅ + 💡
- ✅ in-loop verify gate(`loop.py:1770` `_cat10_verify_gate()`)+ RulesBasedVerifier(`rules_based.py:37-77`)+ LLMJudgeVerifier(`llm_judge.py:57-121`)+ self-correction 重試(預設 2 次 `loop.py:2617-2687`)+ verification-ESCALATE(57.99)。verification-ESCALATE 要求真實 judge 失敗(非 self-reflection)= 研究 ICLR2024×EMNLP2024 分界線直接驗證
- ⚠️ self-correction 是 prompt-based coach feedback,非 RL-trained → 可能拿不到論文增益幅度
- 💡 可採納:verifier 圍繞 **checkable condition**(schema/required field/tool-arg constraint),優先 RulesBased + constraint-check、LLMJudge 用準則明確處;per-step verification(subagent return → lead synthesis 間插);基於 Sprint 57.111 judge benchmark harness 建 offline MAST-14-mode failure classifier

### Cat 11 — Subagent Orchestration ✅ + 💡
- ✅ FORK/TEAMMATE/AS_TOOL 真子 loop(`fork.py:101-224`、`teammate.py`、`as_tool.py:46-114`),深度結構性限制 1(`fork.py:21`);SSE relay(`fork.py:90-98`,57.96);HANDOFF = loop output classifier 攔截 → `stop_reason="handoff"`(⚠️ 與 OpenAI「handoff=tool call」不同實作)
- ⚠️ V2 未對自己 multi-agent 做增益實測(共識採用非實證)
- 💡 可採納:**依 coupling 路由**(independent→fork;dependency-heavy/shared-state→single loop);**strip orchestrator routing/handoff metadata 出 worker context**(避免 self-conditioning);subagent-spawn 當 value-gated + token-budgeted,surface 15× multiplier 進 audit/billing(已有 cost_ledger)

### Cat 12 — Observability ✅ + 💡(高優先)
- ✅ TraceContext propagation + OTelTracer wrapper(`tracer.py:57-149`)+ 5 must-have spans 線上
- 💡 **標準化在 OTel GenAI semantic conventions**(invoke_agent → chat → execute_tool;`gen_ai.*` attribute)→ 滿足約束 3 + CNCF-backed + 避免 bespoke schema;`captureContent` 預設 off 對齊 PII/GDPR;**pass^k 作主要 metric** + fault(λ)/perturbation(ε)軸 + behavioral consistency check(重複同 send N 次 diff trace)+ MAST 3 類/14 mode 作 negative-test catalog

---

## 4. 跨維度主題(6 條反覆出現的共識/張力)

1. **Multi-agent 的價值是 compute,不是 orchestration 魔法**——token usage 解釋 ~80% 變異、~15× 成本、coupling-heavy 任務 single-agent 勝、swarm 放大錯誤。路由規則:**依 coupling 而非 capability 路由**。
2. **Self-correction 的限制有清晰可引用的分界 = external verifiable signal**——intrinsic self-reflection 退化,但 key-condition / tool error / denial-as-routing 讓 correction 可靠。張力:verification agent 自己也不可靠 → **defense-in-depth**(rules-based 優先、LLM judge 次之、human escalation 兜底)。
3. **Context rot 真實且 length-driven**——應對是分層、可審計、依風險排序的 compaction(tool-result clearing → deterministic eviction → LLM summarization);self-conditioning 給了「為何要 prune failed branch」的實證。
4. **approval fatigue 與 transparency 的雙向張力**——「太多 prompt」與「太少可見性」都侵蝕信任。綜合:**deny-first guardrail(少 prompt、高保護)+ glanceable progress streaming(多可見性)+ 暴露 effective context 的 inspector**。
5. **long-horizon 失敗是 execution 問題**——externalized state + bounded burst + rehydration 是跨維度共識,直接驗證 V2 設計;附帶:explicit task primitive 是 load-bearing 反 early-stop 機制(V2 真實 gap)。
6. **empirical eval 必須超越 pass@1 / drive-through-once**——drive-through 證一次能用,**pass^k 證跨重複 run 可靠**;配 behavioral consistency + fault/perturbation 軸 + MAST catalog 形成完整 reliability science。

---

## 5. 優先機會(綜合排序)

| 優先 | 機會 | 範疇 | 研究背書 | V2 現況 | 已識別? |
|------|------|------|---------|---------|---------|
| **1** | **顯式任務原語(DAG-based,非 flat list)** | Cat 1/3/7 | 發現 2.2 load-bearing 反 early-stop | 有 restart 底座、缺 decompose 結構 | ✅ task-primitive thin-spike eval |
| **2** | **pass^k 可靠性實測入 eval harness** | Cat 12 | 發現 2.7 reliability≠capability | drive-through 是 pass@1 式單次 | ❌ 研究新增視角 |
| **3** | **安全從「偵測」轉「結構限制」(評估 6 模式)** | Cat 9 | 發現 2.6 restrict not detect | RiskyActionDetector 是 regex 偵測 | ⚠️ 方向需修正 |
| **4** | **分層 compaction(tool-result clearing 先行)+ ACON 目標帶** | Cat 4 | 發現 2.5 + ACON 26–54% | 單層 75%/turn>30 | ✅ cc-long-running 條件性 |
| **5** | **Cat 12 標準化在 OTel GenAI conventions** | Cat 12 | 發現 2.7 CNCF-backed | 自有 wrapper,非標準 schema | ❌ ux-research 新增 |
| **6** | **verification 重試清掉失敗 context(防 self-conditioning)** | Cat 8/10 | 發現 2.2 self-conditioning | append 失敗答案再改 | ❌ 研究新增視角 |
| **7** | **tool-description lint + structured-error reflection** | Cat 2 | 發現 2.3/2.4 | 無 desc lint | ❌ ux-research 新增 |
| **8** | **key-condition verifier(取代「這答案好嗎」)** | Cat 10 | 發現 2.4 EMNLP2024 分界 | LLMJudge 偏整體判斷 | ⚠️ 可精緻化 |

**兩個 V2 強過研究範例、應守住的地方**:
- **durable 可治理 HITL pause**(比 LangGraph/CC 都重,多租戶 SaaS 正確選擇)
- **5-scope 記憶隔離**(比 CC 單一 MEMORY.md 嚴謹;別為學 ACE scoring 弱化隔離)

---

## 6. 證據品質與保留意見(引用前必讀)

**已獨立驗證 / 高信心(可放心引用)🟢**
- arXiv 2604.14228(Dive into Claude Code):20%→40% / 93% / 七 permission mode / deny-first / 27% / 17% 已逐字核實
- arXiv 2510.00615(ACON):Microsoft,有官方實作,26–54% / >95% / ~99% 多源佐證
- arXiv 2503.13657(MAST):NeurIPS 2025,1,600+ trace / 14 mode / Kappa 0.88
- arXiv 2406.12045(τ-bench)、2310.01798(Cannot Self-Correct ICLR2024)、2024.emnlp-main.714(Key-Condition EMNLP2024)、2406.16008(Lost/Found in the Middle)、ToolEmu / R-Judge、OTel GenAI conventions、2509.09677(Long Horizon Execution)、2604.02460(Single vs Multi-Agent)、2509.18847(Structured Reflection):landmark / 已 spot-check

**Vendor / practitioner 自報(方向可信,數字 hedge)🟡**
- Anthropic engineering posts(multi-agent 90.2% / 15× / 4×、tool-desc ~40%、auto-mode 93% / 17% FN、context engineering、tool-result clearing):first-party,多為內部 eval / 單一 improvement cycle self-report,非外部可重現 benchmark
- LangChain(multi-agent benchmark、interrupt HITL):單一 vendor benchmark,有 framing incentive

**Unverified / mis-attributed / weak(引用前必須再核)🔴**
- Nicolas Bustamante blog(agent-controlled compaction 22.7%):**最弱**,無 published methodology,數字當 hypothesis
- arXiv 2606.11213(CWL/structured eviction)、2512.05470(file-system-as-memory 學術半段)、2601.22311(receding-horizon)、2512.03560(RP-ReAct)、2602.11619(behavioral consistency):未獨立核實,原理可信、empirical 倚賴單篇 self-report
- observability ε/λ reliability:兩篇 2026 paper conflate,「23,392 episodes」與所引 URL(2603.29231)似 mis-attributed(ε 數字應屬 ReliabilityBench 2601.06112)——**技術結論成立,citation precision 不成立**
- self-correction critical survey(2410.20513 vs 通常引用的 Pan et al. 2308.03188):citation conflated
- agentic-design.ai(binary confidence / 「going silent erodes trust」):specifics 未在頁面找到,**勿引此來源**,方向建議靠 arXiv 2604.14228 獨立存活
- multi-agent 17.2x / 4.4x / 96.4%:單篇 2026 preprint,引方向、hedge 數字

**研究盲點**
- 多數可靠性數字缺第三方獨立重現
- enterprise multi-tenant 場景下的 pass^k / fault-injection 實證稀少——**V2 的 trace persistence 反而是少數能廉價產生這類數據的位置**(= 機會 2 的價值)
- **UX 層幾乎無對照硬實證**(透明度/HITL/可視化對 end-user 信任的量化影響)——研究藍海

---

## 7. 已調和的矛盾:thinking/CoT × self-conditioning

兩次 research 在此衝突,本文調和如下(**以 claim 級對抗驗證為準**):

| 子主張 | 信度 | 說明 |
|--------|------|------|
| Self-conditioning 存在,且**不被 model scale 修好** | 🟢 | 兩份一致 + claim 級驗證通過 |
| Thinking/CoT **大幅延長單輪執行長度**(GPT-5 thinking 2,176 steps vs without 「a few」) | 🟢 | 同篇 2509.09677,方向強 |
| Thinking/CoT **完全消除 self-conditioning** | 🔴 開放 | ux-research §2.2 標 [強],但 **panorama claim 級對抗驗證否決此 overclaim(vote 0-1)**;降為開放問題 |

**正確讀法**:thinking 是執行長度的最強單一槓桿(值得做 provider-neutral thinking-budget toggle),但**「完全消除 self-conditioning」未被確立**——所以**仍要在架構上防 self-conditioning**(retry/verification 別把失敗 trace 留 context),不能依賴「開 thinking 就沒事」。

---

## 8. 開放問題

1. **UX 硬實證缺口**:無對照實驗證明特定透明度/HITL/可視化如何量化改善 end-user 信任與介入效率
2. **Reasoning/thinking 能否真正解決長程可靠性與 self-conditioning?**(§7 爭議)
3. **任務拆解的「實測」增益?**(13–42pp 為理論投影,未計 overhead)
4. **記憶系統正確設計**:重設計記憶(階層摘要/scoped/expiration)能否在長程帶來淨增益?(論文明列未來工作)
5. **異步 multi-agent 編排**(AutoGen v0.4 / Google ADK A2A)能否突破「實時協調是開放問題」+ 克服 ~15× token 代價?
6. **DAG vs flat-list task primitive 在多租戶 server 形態的最小可行形狀?**(task-primitive eval 推薦先 thin spike 量測 load-bearing)

---

## 9. 來源清單(去重)

**Primary / 已驗證**
- Anthropic: [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) · [Multi-Agent Research System](https://www.anthropic.com/engineering/multi-agent-research-system) · [Effective Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) · [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) · [Claude Code Auto Mode](https://www.anthropic.com/engineering/claude-code-auto-mode) · [Measuring Agent Autonomy](https://www.anthropic.com/research/measuring-agent-autonomy) · [Claude Code Sandboxing](https://anthropic.com/engineering/claude-code-sandboxing) · [Context Engineering Cookbook](https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools)
- OpenAI: [Agents SDK – Handoffs](https://openai.github.io/openai-agents-python/handoffs/)
- LangChain: [LangGraph Durable Execution](https://docs.langchain.com/oss/python/langgraph/durable-execution) · [Benchmarking Multi-Agent Architectures](https://www.langchain.com/blog/benchmarking-multi-agent-architectures) · [HITL with interrupt](https://www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt)
- arXiv(已驗證/landmark): [2604.14228 Dive into Claude Code](https://arxiv.org/html/2604.14228v1) · [2510.00615 ACON](https://arxiv.org/html/2510.00615) · [2503.13657 MAST](https://arxiv.org/abs/2503.13657) · [2406.12045 τ-bench](https://arxiv.org/abs/2406.12045) · [2310.01798 Cannot Self-Correct](https://arxiv.org/abs/2310.01798) · [2024.emnlp-main.714 Key-Condition](https://aclanthology.org/2024.emnlp-main.714/) · [2406.16008 Found in the Middle](https://arxiv.org/abs/2406.16008) · [2509.09677 Long Horizon Execution](https://arxiv.org/html/2509.09677v3) · [2604.02460 Single vs Multi-Agent](https://arxiv.org/html/2604.02460v1) · [2509.18847 Structured Reflection](https://arxiv.org/pdf/2509.18847) · [2603.29231 Beyond pass@1](https://arxiv.org/pdf/2603.29231) · [2506.08837 Securing LLM Agents](https://arxiv.org/abs/2506.08837) · [2401.10019 R-Judge](https://arxiv.org/html/2401.10019v3) · [ToolEmu](https://openreview.net/forum?id=GEcwtMk1uA) · [2503.14499 METR](https://arxiv.org/abs/2503.14499)
- Microsoft: [Magentic-UI Report](https://www.microsoft.com/en-us/research/wp-content/uploads/2025/07/magentic-ui-report.pdf)
- OTel: [GenAI Observability with OpenTelemetry](https://opentelemetry.io/blog/2026/genai-observability/)
- Sierra: [tau-bench](https://sierra.ai/blog/tau-bench-shaping-development-evaluation-agents)

**未核實 / weak(🔴,引用前再核)**:Cognition「Don't Build Multi-Agents」、Nicolas Bustamante blog、arXiv 2606.11213 / 2512.05470 / 2601.22311 / 2512.03560 / 2602.11619 / 2603.04474、agentic-design.ai、Visible Language 59.2、VentureBeat Claude Code Tasks、各 aggregator/blog 綜述

---

## 10. 統計
- 整合 3 份來源:claim 級驗證 28 claim / 14 findings + 8 角度 41 來源 / 66 findings + 3 Explore agent file:line 勘查
- 兩次 deep-research 合計:~83 agent · ~1,000 萬+ token · 71 來源(去重後 ~50 真實 URL)
