# 企業級 AI Agent Harness：使用體驗與可靠性優化研究（2024-2026）

**Purpose**: 市場/學術 deep research — 蒐集對「伺服器端企業 agent 平台」開發有幫助、且有實證支持的最新方向，對應 V2 11+1 範疇。
**Category / Scope**: Research / Reference（informs next-phase direction，非 sprint plan）
**Created**: 2026-06-22
**Last Modified**: 2026-06-22
**Status**: Active
**Method**: deep-research workflow（客製化：8 搜尋角度、分批 3+3+2 節流、後段驗證減量為每角度 1 票輕驗證、1 綜合 agent）；17 agents / 82 tool calls / 66 findings。

> **Modification History**
> - 2026-06-22: Add cross-ref to same-day panorama+mapping + flag self-conditioning overclaim
> - 2026-06-22: Initial creation — deep-research workflow output（rate-limit-aware, light-verify variant）

> **⚠️ 證據品質提醒**：多數可靠性數字來自 Anthropic 自家 eval 或單篇 preprint self-report，是 directional / order-of-magnitude，非外部可重現 benchmark。§五 明確標出哪些 citation 已逐字核實、哪些 unverified / mis-attributed、哪些是 vendor marketing。引用前請先讀 §五。

> **🔗 相關研究（同日 2026-06-22，~70% 重疊，建議一起讀）**
> 本文是當日**第二次** deep-research run。先前已有一組**更完整、且有 file:line 程式碼 grounding** 的姊妹研究（落地對照權威性高於本文）：
> - [ai-agent-harness-market-research-panorama-20260622.md](../5-status/ai-agent-harness-market-research-panorama-20260622.md) — 中立全景，含 **28 條 claim 級**對抗驗證
> - [ai-agent-harness-research-vs-v2-mapping-20260622.md](../5-status/ai-agent-harness-research-vs-v2-mapping-20260622.md) — 14 findings × V2 11+1 對照（可操作性最強，有 `loop.py:行號` grounding）
>
> **本文真正的增量（panorama 未涵蓋）**：§六 來源 37 Cat 12 標準化於 OTel GenAI semantic conventions、來源 25 ACON 量化壓縮目標帶、ICLR2024「Cannot」×EMNLP2024「Key-Condition」self-correction 分界線、MAST failure catalog + tool-description lint。
> **本文盲點（panorama 有、本文漏）**：安全「限制非偵測」+ 6 種抗注入結構模式（arXiv 2506.08837）——Cat 9 方向**以 panorama finding 14 為準**。
> **⚠️ 已知矛盾（以 panorama 為準）**：§2.2「CoT thinking 消除 self-conditioning」標 **[強] 為 overclaim**；panorama §被否決 #2 的 claim 級對抗驗證已否決「thinking 完全消除 self-conditioning」（vote 0-1）。此處應降為 **[中/開放問題]**。

---

## 一、執行摘要 — 最高價值且有實證支持的方向

1. **Bounded single TAO/ReAct loop 是有實證背書的預設架構，subagent fork 應該 GATE 在 task type + token budget 之後，而非反射式提升準確率。[強]**
   在相同 thinking-token budget 下，single-agent 在 multi-hop reasoning 上持平或略勝 multi-agent；Anthropic 自家數據顯示 token usage 單獨解釋 ~80% 的 multi-agent 表現變異、且成本約為一般 chat 的 15x。本專案的 bounded max_turns + per-send budgeting + value-gated subagent-spawn 設計被直接驗證。

2. **長程任務失敗主要是 EXECUTION 問題、不是 planning 問題；更好的 planner 不會修好多輪退化——harness 必須外部化狀態並在每個 bounded burst 重新 ground。[強]**
   即使把正確 plan 與 knowledge 交給模型，single-step 近乎完美的模型仍在 ~15 turns 內掉到 50% 以下（arXiv 2509.09677，已 spot-check）。這是 bounded-burst + cross-turn rehydration + compaction 設計的直接實證依據。

3. **Self-correction loop 必須由 EXTERNAL verifiable signal 驅動（tool error / test pass-fail / key-condition check / 獨立 judge），裸 re-prompt 不只是中性、會讓答案變差。[強]**
   ICLR 2024「Cannot Self-Correct」vs EMNLP 2024「Can with Key-Condition Verification」這一對是可引用的分界線，直接驗證本專案 verification-ESCALATE 要求真實 judge 失敗（而非 self-reflection）的設計。

4. **Approval fatigue 是已量測的一階風險：使用者批准 ~93% 的 permission prompt——HITL gate 應只在高 blast-radius（tier-3）動作觸發，配 deny-first guardrail 而非逐動作確認。[強]**
   Anthropic 自家 classifier 也有 ~17% false-negative，R-Judge 顯示 8 個 LLM 的 risk-awareness「遠非完美」。結論：LLM judge 不能是唯一 gate，需 rules-based + LLM-judge + 確定性 human escalation 的 defense-in-depth。

5. **pass^k（k 次重複的一致性）應成為平台主要 eval 指標，而非單次 pass@1 / drive-through-once。[強]**
   τ-bench：GPT-4o retail ~61% pass@1 但 pass^8 <25%。一個 drive-through 過一次的 feature，跨 tenant 重複跑仍可能不可靠——這正是 bounded-loop + per-tenant-replay 場景。

6. **Cat 12 tracing 應標準化在 OpenTelemetry GenAI semantic conventions（invoke_agent → chat → execute_tool）上，content capture 預設關閉。[強]**
   `finish_reasons` = `tool_calls` vs `stop` 與本專案 while-true loop 的 stop_reason 分支 1:1 對應；`captureContent` opt-in 預設與既有 multi-tenant PII/GDPR + PIIRedactor 規則吻合，同時滿足 provider-neutrality（約束 3）。

7. **Compaction 應採「分層、依風險排序」策略，且有可量化目標帶。[強（ACON 已驗證）/ 中（部分技法）]**
   ACON（arXiv 2510.00615，Microsoft，已驗證）：15+ step agent 可削減 26–54% peak token 而不損準確率；distilled compressor 保留 >95% 效能、~99% API 成本下降。順序建議：(1) tool-result clearing 最先（最便宜、最低損、無同步 LLM 呼叫），(2) deterministic eviction（審計友善），(3) 才用 lossy LLM summarization。

8. **Tool-description 品質與 clean scoped subagent context 是高槓桿、可量測的可靠性槓桿。[中]**
   Anthropic 報告：用模型改寫 flawed tool description 帶來 ~40% 後續任務完成時間下降（單一 vendor 數據點）；strip orchestrator routing/handoff metadata 出 worker context（LangChain）可避免 translation overhead 與 self-conditioning。支持一個 tool-description lint/review step。

---

## 二、各維度發現

### 2.1 Agent loop 架構與控制模式（agent-loop）

核心訊息：bounded single loop 是有實證的預設；multi-agent 的優勢主要來自 aggregate compute 與 parallel context，不是 orchestrator 的「聰明」。長程一致性靠外部化狀態 + rehydration + compaction，不是靠更長的單次 run。

- 相同 thinking-token budget 下，single-agent 在 multi-hop reasoning 持平或略勝 sequential MAS（FRAMES 1000-token：0.680 vs 0.670；MuSiQue 4-hop：0.407 vs 0.320）——margin 小，正確描述是「match or modestly beats」。¹
- Multi-agent 在 Anthropic 內部 research eval 勝 single-agent Opus 4 達 90.2%，但 token usage 單獨解釋 ~80% 變異、成本 ~15x chat。² 這是 compute、不是 orchestration 魔法。
- 架構由 task 決定：isolated subagent 適合 independent-thread/parallel 任務，但在需要共享單一連貫 context 的 shared-state 任務上會 break——「the task picks the architecture」。³
- 強模型上 plan-then-act 持平或略勝 interleaved ReAct（GPT-4o）；goal-state reflection（ReflAct）勝 baseline ~33.1%——建議每個 turn 錨定 goal/state 而非冗長 CoT。⁴ [中]
- RP-ReAct（planner/supervisor over bounded ReAct executor）在 enterprise 任務優於 flat ReAct——對應本專案 hybrid orchestrator，但屬單篇 self-report。⁵ [中]
- Agent-controlled（非 threshold-triggered）compaction：在 safe task boundary 觸發，報告 22.7% token 下降且無準確率損失——但來源為單一 practitioner blog，數字當假設、非目標。⁶ [弱]
- 長程 agent 靠 explicit state-rehydration artifact（progress log + feature list + git）在每個 fresh-context session 開頭讀回；two-role split（initializer vs per-feature coding agent）。⁷
- End-to-end behavioral verification 是獨立且必要的 loop step：agent 可靠地改 code 但常沒注意「feature 其實沒 work」，除非明確被要求用 browser automation 驅動。⁷ 獨立佐證本專案的 Drive-Through Acceptance 約束。

### 2.2 Intent recognition、planning 與 task decomposition（planning-decomposition）

核心訊息：長程失敗是 execution 而非 planning 問題；self-conditioning（自己的錯誤留在 context 會招致更多錯誤）不被 model scale 修好；CoT thinking 是執行長度的最大單一槓桿。explicit externalized task primitive 是 load-bearing 的反 early-stop 機制。

- 長程退化即使給對 plan + knowledge 仍發生：Qwen3-32B H₀.₅ ~15 turns、Qwen3-4B ~6 turns；frontier models without thinking 多在 ~4 step/turn 失敗。⁸
- Self-conditioning：注入更多 prior error 單調惡化 turn-100 準確率，200B+ 仍 susceptible；CoT thinking 消除 self-conditioning 並大幅延長單輪執行長度。⁸ [強]
- Thinking/CoT 是最大槓桿：GPT-5 (thinking) 維持 2,176 sequential steps、Claude-4 Sonnet 432 steps，without thinking「a few steps」。⁸ 支持 provider-neutral thinking-budget toggle 作為一級 harness 旋鈕。
- Plan-then-Execute（分離 Planner/Executor + localized replanning）是 long-horizon web navigation 的可重現 SOTA pattern；hierarchical milestone decomposition 進一步改善——來源為 aggregator，特定 SOTA 主張視為單一聚合源。⁹ [中]
- Anthropic harness：initializer 寫 200+ feature JSON（全預標 failing 作為完成準則）+ progress 檔，one-feature-at-a-time + 結構性拒絕 early termination——具體的 externalized TodoWrite-style primitive。⁷ ¹⁰
- Claude Code「Tasks」以 DAG（含 explicit blocking）建模、跨 session/subagent/context window 協調——比 flat list 更具表達力（單一 secondary 來源）。¹¹ [中]
- Compaction（高保真摘要後 reinitiate 新 window）是 Anthropic 點名的長程一致性「first lever」，配 NOTES.md-style note-taking。¹⁰
- 失敗歸因研究將 long-horizon breakdown 拆成 memory / reflection / planning / action 四模組——支持以模組邊界建 Cat 12 observability（單一來源，具體計數未獨立核實）。¹² [中]
- Receding-horizon replanning（只 commit 下一個 action、每次 transition 後 replan）在 noisy evaluation 下勝過 brittle 的長期 commitment——原理強、特定 paper（arXiv 2601.22311）未核實。¹³ [中]

### 2.3 Multi-agent orchestration 與 delegation（multi-agent）

核心訊息：把 subagent spawning 當成 explicit cost/budget 決策；依 coupling（非 capability）路由；coordination 集中化、verification per-step；tool-description 品質與 clean context 是 first-class artifact。

- Orchestrator-worker（Opus 4 lead + Sonnet 4 subagents）勝 single Opus 4 達 90.2%，但 token usage 解釋 ~80% 變異。² [強]
- 成本：multi-agent ~15x chat token、single ~4x；只建議用在 outcome value 超過 token cost 的場景。² [強]
- Multi-agent 不適合 tightly-coupled work（多 inter-agent dependency / 低真實平行度 / 需共享 context）；Anthropic 點名 coding 為弱契合。³ [強]
- Decentralized/swarm 拓樸放大錯誤 ~17.2x vs single-agent baseline，centralized orchestrator 收斂到 ~4.4x（arXiv 2603.04474，單篇 2026 preprint，確切數字未獨立核實）。¹⁴ [中]
- 在每個 primary agent 後插 verification agent，攔下 96.4% 注入錯誤（為 paper 對其他 2025 ICML 工作的 secondary citation，百分比未核實）——方向（per-step 勝 final-only verification）成立。¹⁴ [中]
- MAST：1,600+ annotated trace、7 框架、14 failure mode、3 類（spec/design、inter-agent misalignment、verification/termination）——大多失敗是 orchestration/spec bug 而非 base-model 弱。¹⁵ [強]
- Self-conditioning + recursive context reuse 造成 cascading amplification——支持 clean scoped subagent context、scrub prior error（term/attribution 應再核）。¹⁵ [中]
- τ-bench (retail)：0-1 distractor domain 時 single-agent 勝 supervisor/swarm，2+ distractor 才反轉；supervisor 損失來自 translation overhead + handoff message 汙染 worker context——可重用修法：strip routing/handoff metadata 出 worker context（單一 vendor benchmark）。¹⁶ [中]
- 用模型改寫 flawed tool description → 後續任務完成時間 ~40% 下降；poor tool description 造成 catastrophic failure（單一 Anthropic 數據點，magnitude 視為 anecdotal）。² [強（質性）/ 弱（量級）]

### 2.4 Tool execution 可靠性 + verification/self-correction loop（tool-verification）

核心訊息：可驗證的分界是「self-correction 需要 EXTERNAL signal」。intrinsic self-reflection（裸 re-prompt）neutral-to-harmful。tool error 是你已有的最高品質 external signal。

- Intrinsic self-correction（無 external signal）一致地失敗、常退化推理準確率，會把對的答案改成錯的（ICLR 2024）。¹⁷ [強]
- Evaluator-optimizer（generator LLM + 獨立 evaluator LLM in loop）僅在「有明確準則 / 迭代有可量測價值 / evaluator 能給有用回饋」三條件成立時建議——Anthropic guidance（非 benchmark）。¹⁸ [強]
- 分離 guardrail model 與 response model（一個答、另一個 screen）勝過單一 call 兼任——Anthropic 報告之 tendency。¹⁸ [中]
- 自主 tool agent 有 compounding error，建議 sandboxed testing + HITL checkpoint before irreversible action + Zero-Trust least-privilege——對應本專案 HITL pause/resume + permission-policy + tool-sandbox triad。¹⁸ [強]
- 對 tool error 的 structured reflection（先診斷具體錯誤再 retry）可量測強化 tool-interaction 可靠性（arXiv 2509.18847，含 Tool-Reflection-Bench）；error taxonomy：invocation / parameter / wrong-tool / failed-API——但增益部分來自 RL training，scope 限 trained-reflection regime。¹⁹ [強（trained regime）]
- 分界線是 verification/key-condition signal 的存在：有 key-condition verification 時 LLM 可 self-correct，無則不能（EMNLP 2024）——告訴 verifier 該檢查 task 的 key constraint（schema / required field / tool-arg constraint），而非「這答案好嗎」。²⁰ [強]
- 社群視 self-correction 為 contested、condition-dependent——支持保守、不行銷「autonomous self-correction」為 blanket capability（其中一個 citation 標籤被 conflate，substance 正確）。²¹ [中]
- Tool-use eval 已成熟到 stable、大規模、mirror-real-API benchmark（StableToolBench / MirrorAPI ~7,000+ API）——支持 golden-fixture / `@pytest.mark.benchmark` regression（確切 API 數視為近似）。²² [中]

### 2.5 Long-running agents：memory + context 管理/compaction（memory-context）

核心訊息：context degradation 是 length-driven（context rot），不只是 relevance-driven。三個 named pattern（compaction / structured note-taking / sub-agent isolation）直接對應 Cat 4 / Cat 3 / Cat 11。

- Context rot：window token 數增加，recall 準確率下降；歸因 n² attention + 多在較短序列訓練；Anthropic 稱 context engineering 為 agent engineer 的「#1 job」。²³ [強]（「context rot」部分是 framing 用語，底層退化已被實證。）
- 三 pattern：(1) compaction（摘要近滿 context 後 reinitiate，保留架構決策/未解 bug/實作細節）、(2) structured note-taking（外部 memory）、(3) sub-agent isolation（只回 1,000–2,000 token 摘要）；compaction 調參順序「先 maximize recall、再 iterate precision」。²³ [強]
- Tool-result clearing 是最安全、最低風險的 compaction 形式，已作為 Claude Developer Platform 一級 feature（Anthropic 自家 framing，機制低爭議）。²⁴ [強]
- ACON：15+ step agent peak token 削 26–54% 且 task success 持平或改善（AppWorld 56.5% vs 56.0%、OfficeBench ~30%、8-Objective QA 54.5% token + 61.5% dependency 削減）。²⁵ [強（已驗證 arXiv 2510.00615 + 官方實作）]
- ACON distilled compressor 保留 >95% teacher 效能、~99% API 成本下降；compression 甚至改善 small-model agent（AppWorld +32.4% relative，透過 context-distraction mitigation）——支持 provider-neutral、per-tenant/turn 跑便宜 distilled model 的 compactor。²⁵ [強]
- Lost-in-the-middle 是 U-shape positional bias（primacy + recency over middle），2024 work 顯示可 calibrate；後續發現 bias 不限於 middle，更 pervasive——支持 prompt construction（Cat 5）把最相關 memory + 當前 task 放 context 邊緣。²⁶ [強]
- 結構化/typed eviction（CWL：typed dependency graph + deterministic graduated eviction）被提議優於 summarization，避免 unpredictable lossiness / structural destruction / blocking cost / compression-induced hallucination——**citation（arXiv 2606.11213）未驗證，原理可信、paper 待核**。²⁷ [弱]
- Just-in-time retrieval（保留 lightweight identifier、runtime 用 tool hydrate）是建議的 memory pattern，接受較慢 runtime exploration 換 cleaner context——Anthropic-sourced 半段強；學術 formalization（arXiv 2512.05470）未驗證。²³ [中]

### 2.6 HITL、permissions、guardrails 與企業治理（governance-permissions）

核心訊息：approval fatigue 是量測的一階風險；tiered permission + deny-first + 雙向 screening 是可重用 blueprint；LLM judge 不能是唯一 gate；guardrail 必須 pre-execution 攔截。

- 使用者批准 ~93% 的 permission prompt，prompt 越多注意力越少——interrupt 只在 real-downside 動作觸發。²⁸ [強]（單一 vendor 內部統計，但 load-bearing。）
- 兩段式 classifier：full pipeline ~0.4% FP 但 ~17% FN（「the honest number」）；classifier strips assistant reasoning/tool result 以防 self-justification——classifier 是 defense-in-depth 一層、永不替代 sandbox。²⁸ [強]
- Tiered permission：(1) safe-tool allowlist auto-run、(2) in-project file ops（version-control 可審）、(3) transcript-classifier-gated shell/external-API/out-of-project——只有 tier-3 到 gate。²⁸ [強]
- Defense-in-depth 雙向：input-side prompt-injection probe（screen tool OUTPUTS 進 context）+ output-side classifier（screen tool CALLS before execution），sandbox 作 containment。²⁸ [強]
- HITL pause/resume 本質是 state-persistence/checkpointing：`interrupt()` 存 state 到 checkpoint、標記 interrupted、後續 `resume`；四種 decision type：approve / reject / review-and-edit-state / review-tool-call——對應 Cat 7 state mgmt + checkpointer，特別是「edit before proceeding」超越二元 approve/reject（LangGraph 單一 authoritative 來源）。²⁹ [強]
- Runtime monitoring 必要：post-hoc sandbox benchmark（AgentHarm / ToolEmu / R-Judge）在 action 後評估、無法在 production 阻止 harm——guardrail/verification 必須 in-loop pre-execution 攔截（AgentMonitor attribution 為 extrapolation，引用前再核）。³⁰ [中]
- R-Judge：8 個 LLM 的 risk-awareness「遠非完美」——LLM-as-guardrail 不能是唯一 control，需 rules-based + LLM-judge + human escalation。³¹ [強]
- ToolEmu（LM-emulated sandbox）：human review 認 68.8% 的 ToolEmu-identified failure 為真實 agent failure——可作 red-team permission policy 的 pre-production pattern（為作者自家 human-eval）。³² [強]

### 2.7 Observability、tracing 與 agent evaluation（observability-eval）

核心訊息：pass^k 為主要指標；tracing 標準化在 OTel GenAI conventions；MAST 14 failure mode 作 negative-test catalog；加 fault/perturbation 軸 + behavioral consistency。

- τ-bench pass^k 揭露 pass@1 隱藏的 reliability gap：GPT-4o ~61% pass@1 retail 但 pass^8 <25%；引入 pass^k 衡量跨 k 次 trial 的一致性。³³ [強]
- Reliability 隨複雜度 super-linear 退化、對 pass@1 不可見；perturbation（ε=0.2：96.9%→88.1%）與 infra-fault（λ）軸造成額外大幅下降——建議 eval harness 加 ε / λ 軸。**注意：finding 把兩篇 2026 paper conflate，'23,392 episodes' 與所引 URL 似乎 mis-attributed；技術結論成立、citation precision 不成立。**³⁴ [中]
- MAST 14 failure mode / 3 類，1,600+ trace、Cohen's Kappa = 0.88、NeurIPS 2025 spotlight——對應 Cat 11 / Cat 10 的 negative-test catalog。³⁵ [強]
- MAST 附 validated LLM-as-a-Judge pipeline，自動分類 trace 到 14 mode——可作 SSE/loop trace 的 offline post-run failure-classifier blueprint（judge 準確率視為 paper-reported）。³⁶ [強]
- OTel GenAI semantic conventions（CNCF / GenAI SIG since 2024-04）定義標準 agent span 階層：invoke_agent → chat → execute_tool；已被 Google Cloud / AWS / Azure / Datadog 採用——保持 provider-neutral、避免 vendor lock-in（conventions 仍部分 experimental）。³⁷ [強]
- 具體 attribute：`gen_ai.request.model`、`gen_ai.usage.input_tokens`/`output_tokens`、`gen_ai.response.finish_reasons`（`stop` vs `tool_calls`），histogram `gen_ai.client.operation.duration` + `gen_ai.client.token.usage`——`finish_reasons`='tool_calls' vs 'stop' 與 while-true loop 的 stop_reason 分支 1:1。³⁷ [強]
- Safe-by-default content capture：convention 預設不捕捉 prompt content / tool argument（可含敏感資料），須明確 opt-in `captureContent`——與 multi-tenant PII/GDPR + PIIRedactor 對齊（span 結構/token/latency/finish_reason always-on，payload 按 per-tenant policy gate、預設 off）。³⁷ [強]
- Behavioral consistency 是獨立可量測軸（agent 會「跟自己不同意」），應與 task success 分開追蹤，配 pass^k——概念成立，特定 paper（arXiv 2602.11619）未獨立核實。³⁸ [中]

### 2.8 Agent UX：trust、transparency、controllability、steerability（agent-ux-trust）

核心訊息：trust 是 trajectory 而非固定狀態；graduated trust spectrum + deny-first 勝二元 autonomy；denial 是 routing signal 不是 hard stop；transparency 要 glanceable + 暴露 effective context。

- Auto-approve rate 從 <50 session 的 ~20% 升到 750 session 的 >40%；整體 ~93% 批准——per-action confirmation 作為唯一 safety 機制「behaviorally unreliable」（已逐字對 arXiv 2604.14228 核實）。³⁹ [強]
- Graduated trust spectrum（plan / default / acceptEdits / auto / dontAsk / bypassPermissions）+ deny-first：deny rule 無條件勝 allow rule，未識別動作 escalate 而非靜默執行，跨七層 parallel safety——deny rule 永遠 win、unknown tool call 預設 fail-closed 到 HITL。³⁹ [強]
- Denial 是 routing signal 不是 hard stop：把 denial reason 餵回 loop 讓下一輪 re-plan（對應 verification-ESCALATE coach-retry）；sibling abort controller 在 Bash error 時殺掉 in-flight 子程序。³⁹ [強]
- File-based append-only transparency（可讀/可編/可版本控制的 config + JSONL transcript）以表達力換 auditability + user control，支持 resume/fork/rewind；subagent 只回 summary text——對 DB-backed memory 是張力：用 inspector UI 暴露 agent 的 effective context（注入的 memory layer、compaction summary）。³⁹ [強]
- 串流 discrete progress state（done/running/blocked/next）讓使用者及早抓問題；token-level streaming 的多 progress state 由 arXiv 2604.14228 獨立佐證——**但「going silent erodes trust」這句的 agentic-design.ai 來源未在 fetch 時找到，視為 weak/mis-sourced，核心想法靠 arXiv 半段存活**。⁴⁰ [弱（特定引述）/ 強（streaming-state 半段）]
- Binary confidence indicator（confident / not sure）讓使用者決策更快、progressive autonomy 減摩擦——**none of the three specifics 在所引 agentic-design.ai 頁面找到，視為 unverified-as-stated；方向建議（coarse confident/uncertain 勝 raw score、earned-trust ramp）合理但勿引此來源**。⁴⁰ [弱]
- Trust mis-calibration 來自未浮現的 LLM uncertainty；granular/contextual/actionable feedback + passage-level uncertainty visualization + multi-agent validation（MAVS）助 calibrate——Visible Language 為真實 peer-reviewed 期刊、單一來源未 corroborate。⁴¹ [中]
- Capability amplification 有 comprehension cost：~27% Claude-Code-assisted task 是沒工具不會嘗試的工作，但 AI-assisted developer comprehension test 低 17%（兩個不同來源拼接：27% 為 Anthropic 內部 132-engineer 自陳、17% 引自獨立研究）——UX 要 build operator understanding、不只 throughput。³⁹ [強（兩數字已逐字核實，但勿當單一量測過度倚賴）]

---

## 三、跨維度主題 — 反覆出現的共識與張力

**主題 1：Multi-agent 的價值是 compute，不是 orchestration 魔法——且何時「有害」可被路由規則明確化。**
agent-loop、multi-agent、observability 三個維度一致：token usage 解釋 ~80% multi-agent 變異（²）、~15x 成本（²）、coupling-heavy 任務 single-agent 勝（³ ¹⁶）、decentralized swarm 放大錯誤 ~17.2x（¹⁴）。共識路由規則：**依 coupling 而非 capability 路由**——independent-thread/breadth-first → fork；shared-state/dependency-heavy → single bounded loop 或 handoff with shared memory。本專案把 subagent 當 explicit cost/budget 決策（surface 15x multiplier 進 audit/billing）有直接背書。

**主題 2：Self-correction 的限制有清晰、可引用的分界——external verifiable signal。**
tool-verification、planning-decomposition、governance、agent-ux 四個維度交會：intrinsic self-reflection 退化（¹⁷ ⁸ self-conditioning），但 key-condition verification（²⁰）、tool error（¹⁹）、denial-as-routing-signal（³⁹）這些 external signal 讓 correction 可靠。張力：verification agent 本身（LLM judge）也不可靠（R-Judge ³¹、17% FN ²⁸）。**解法是 defense-in-depth**：rules-based verifier（檢查 checkable condition）優先、LLM judge 次之、確定性 human escalation 兜底——而非把信心押在單一 model gate。

**主題 3：Context rot 是真實且 length-driven，應對是分層、可審計、依風險排序的 compaction。**
memory-context、planning-decomposition、agent-loop 三維度一致點名 context 管理為一級工程問題（²³ 為「#1 job」）。self-conditioning（⁸ ¹⁵）給了「為何要 prune failed branch」的實證。可量化目標帶來自 ACON（²⁵，已驗證）：~25–55% peak token 削減而不損準確率。張力：lossy LLM summarization 有 compression-induced hallucination（²⁷），對企業 audit 不友善——因此順序應為 **tool-result clearing → deterministic/typed eviction → 才 LLM summarization**。

**主題 4：approval fatigue 與 transparency 的雙向張力——「太多 prompt」與「太少可見性」都侵蝕信任。**
governance（²⁸ 93% 批准）與 agent-ux（³⁹ 同一 93% + auto-approve trajectory）一致：per-action confirmation 不可靠。但「going silent erodes trust」（⁴⁰，來源 weak）與 comprehension cost（³⁹，17% 較低）顯示反面：純黑箱 auto-execution 也有害。**綜合**：deny-first guardrail（少 prompt、高保護）+ glanceable progress streaming（多可見性、少 transcript 滑動）+ 暴露 effective context 的 inspector（build understanding）。

**主題 5：long-horizon 失敗是 execution 問題——externalized state + bounded burst + rehydration 是跨維度共識。**
planning-decomposition（⁸ execution-not-planning）、agent-loop（⁷ rehydration artifact）、memory-context（²³ note-taking）三維度收斂到同一架構結論，直接驗證本專案 bounded max_turns + cross-turn rehydration + compaction。附帶共識：**explicit task primitive（feature list / progress 檔 / DAG）是 load-bearing 的反 early-stop 機制**，本專案缺 CC-style TodoWrite 是真實 gap。

**主題 6：empirical eval 必須超越 pass@1 / drive-through-once。**
observability（³³ pass^k）與本專案既有 Drive-Through Acceptance 文化互補但不重疊：drive-through 證一次能用，pass^k 證跨重複 run 可靠。配 behavioral consistency（³⁸）、fault/perturbation 軸（³⁴）、MAST failure catalog（³⁵）形成完整 reliability science。

---

## 四、對本專案的具體建議（對應 11+1 範疇）

### Cat 1 Orchestrator Loop (TAO/ReAct)
- **吻合**：bounded single while-true loop 被 ¹ ⁸ 直接驗證為有實證的預設架構；receding-horizon（每 turn 從 fresh observation re-derive plan，cheap replanning ¹³）天然契合 stop_reason-driven loop。
- **可採納 pattern**：每個 turn 錨定 goal/state（ReflAct ⁴）而非冗長 CoT；denial-as-routing-signal（³⁹）——HITL REJECT / guardrail block 時把 denial reason append 成 observation message 讓下一輪 re-plan。
- **Thin spike**：sibling abort controller——在一批 tool call 中某個 error 時，殺掉同批 in-flight tool 執行而非讓 doomed batch 跑完（³⁹）。
- **落差/gap**：缺 CC-style explicit task primitive（⁷ ¹⁰ ¹¹）；若新增，採 **DAG/dependency model（含 explicit blocking）優於 flat list**，更契合 fork/teammate/handoff + HITL gating。建議走 thin vertical spike → retrospective → design note。

### Cat 2 Tool Layer
- **可採納 pattern**：tool error structured reflection（¹⁹）——on tool error，把 STRUCTURED error（invocation / parameter / wrong-tool / failed-API taxonomy）餵回 loop 作 observation，而非「try again」；這正是 self-correction provably helps 的 regime（²⁰）。
- **Thin spike**：tool-description lint/review step——精確、測過的 tool description 是 first-class artifact（²，~40% 提速數據點，質性強）。
- **可採納 pattern**：golden-fixture + `@pytest.mark.benchmark` regression，mirror StableToolBench/MirrorAPI 的測試集（²²）量測 provider-neutral adapter 的 tool-call reliability。

### Cat 3 Memory（5 scope × 3 time scale）
- **吻合**：cross-turn rehydration 被 ⁷（progress artifact）+ ²³（structured note-taking）背書。
- **可採納 pattern**：just-in-time / reference-based retrieval（²³）——存 lightweight identifier（path / query / ID），runtime 用 tool hydrate，而非 eager 注入所有 memory layer，減 token 壓力。
- **Thin spike**：把 subagent return 契約固定為 condensed summary（1,000–2,000 token，²³），避免 detailed context 汙染 parent。

### Cat 4 Context Mgmt（含 compaction / prompt caching）
- **吻合**：active per-turn token budgeting + AP-7「Context Rot Ignored」被 ²³ 直接驗證；compaction ≥3-turn 門檻與 Anthropic「first lever」一致（¹⁰）。
- **可採納 pattern（分層、依風險排序）**：(1) tool-result clearing 最先（²⁴，最低損、無同步 LLM 呼叫）→ (2) deterministic/typed eviction 用於需 auditability 處（²⁷，原理可信、citation 待核）→ (3) 才 lossy LLM summarization。
- **可量化目標**：ACON（²⁵）給目標帶——compactor 應能削 ~25–55% peak token 而不損準確率；採「failure-driven guideline refinement」作 compactor 調參 loop；compaction 跑 cheap distilled model（>95% 保留、~99% 成本下降）契合 cost-tiered model policy。
- **Thin spike（弱證據、當假設測量）**：把 compaction 暴露為 agent-invokable tool 在 safe task boundary 觸發（⁶，22.7% 數字僅 blog，當 hypothesis），對照現行 75k/≥3-turn 固定門檻——量測是否避免「切斷一輪 tool sequence」。
- **Prompt construction 連動（Cat 5）**：lost-in-the-middle（²⁶）——把最相關 memory + 當前 task 放 context 邊緣，視 compaction 為縮短 recall 最弱的 middle。

### Cat 5 Prompt Construction
- **可採納 pattern**：positional ordering——decision-relevant 內容放 primacy/recency 位置（²⁶）；goal-state anchoring 入 system/turn prompt（⁴）。
- **吻合**：centralized PromptBuilder（AP-8）與「prompt 組裝唯一入口」原則，配 memory layer 注入有 unit-test 驗證。

### Cat 6 Output Parsing
- **可採納 pattern**：以 `finish_reasons`（`stop` vs `tool_calls`）作 stop_reason 來源並標準化命名（³⁷），使 cost-attribution / compaction telemetry 可流入任何 APM。

### Cat 7 State Mgmt（含 Reducer + transient/durable）
- **吻合**：HITL pause/resume 本質是 checkpointing（²⁹）——pause/resume 需 durable state + checkpointer。
- **可採納 pattern**：四種 HITL decision type（approve / reject / **review-and-edit-state** / review-tool-call，²⁹）作 resume API 契約；特別補上「edit before proceeding」超越二元 approve/reject。

### Cat 8 Error Handling
- **可採納 pattern**：tool error taxonomy（¹⁹）+ retry policy；bounded max_turns 作 compounding-error containment（¹⁸）。
- **可採納 pattern**：模組級 failure attribution（memory/reflection/planning/action，¹²）餵入 structured replanning 而非 blind retry。

### Cat 9 Guardrails & Safety
- **可採納 pattern（first-class 要求）**：雙向 screening（²⁸）——prompt-injection probe on tool OUTPUTS + classifier on tool CALLS before execution，sandbox 作 containment。
- **關鍵實作細節**：任何 LLM judge 要 **strip agent 自己的 reasoning/tool output** 出 judge context 以防 self-justification（²⁸）。
- **保留意見**：LLM judge 不可為唯一 gate（³¹ R-Judge、²⁸ 17% FN）；deny rule 無條件勝 allow rule、unknown tool call fail-closed（³⁹）。
- **Thin spike**：ToolEmu-style LM-emulated sandbox red-team permission policy（³²，~69% real-failure validity 作 calibration baseline）。

### Cat 10 Verification Loops
- **吻合**：verification-ESCALATE 要求真實 judge 失敗（非 self-reflection）被 ¹⁷ + ²⁰ 這對直接驗證——這是最 design-actionable 的 finding。
- **可採納 pattern**：verifier 圍繞 **checkable condition** 建（schema satisfaction / required field / tool-arg constraint，²⁰），優先 RulesBasedVerifier + constraint-check，LLMJudge 用在準則明確處（¹⁸ 三條件）。
- **可採納 pattern**：per-step verification（subagent return → lead synthesis 之間插 verifier，¹⁴），而非僅 final-only。
- **Thin spike**：基於既有 LLMJudgeVerifier + Sprint 57.111 judge benchmark harness，建 offline LLM-as-a-Judge failure classifier，以 MAST 14 mode（³⁵ ³⁶）分類 persisted SSE/loop trace。

### Cat 11 Subagent Orchestration（4 模式，無 worktree）
- **吻合**：fork/teammate/handoff 的 summary-only return（²³）+ centralized orchestrator 拓樸（¹⁴ 收斂錯誤到 ~4.4x）被背書。
- **可採納路由規則**：依 coupling 路由——independent/breadth-first → fork；dependency-heavy/shared-state → single loop（³ ¹⁶）；distractor domain <2 時不 fork（¹⁶ 的 threshold heuristic，視為 indicative）。
- **可採納 pattern**：strip orchestrator routing/handoff metadata 出 worker context（¹⁶），給 forked subagent clean scoped context（避免 self-conditioning ¹⁵）。
- **可採納 pattern**：把 subagent-spawn 當 value-gated + token-budgeted 決策，surface 15x multiplier 進 audit/billing（²）。

### Cat 12 Observability / Tracing（cross-cutting）
- **可採納 pattern（最高優先）**：標準化在 OTel GenAI semantic conventions（invoke_agent → chat → execute_tool span tree；`gen_ai.*` attribute，³⁷）——滿足 provider-neutrality（約束 3）、CNCF-backed、避免 bespoke schema。
- **吻合**：`captureContent` 預設 off（³⁷）與 multi-tenant PII/GDPR + PIIRedactor 對齊——span 結構/token/latency/finish_reason always-on，payload capture 按 per-tenant policy gate。
- **可採納 eval pattern**：pass^k（³³）作主要 metric；加 fault-injection（λ）+ perturbation（ε）軸（³⁴，注意 citation 已 conflate）；behavioral consistency check（重複同一 send N 次、diff loop trace，³⁸）抓 verification-ESCALATE / subagent routing 的 non-determinism——廉價地 leverage 既有 trace persistence。
- **可採納 pattern**：以 MAST 3 類 / 14 mode 為 negative-test catalog instrument failure attribution（memory vs planning vs action，¹²）。

### 與既有設計的整體 alignment 結論
- **強 alignment（外部實證佐證既有方向）**：bounded-burst + rehydration（⁷ ⁸ ²³）、HITL pause/resume as checkpointing（²⁹）、Drive-Through Acceptance（⁷）、verification 需 external signal（¹⁷ ²⁰）、compaction ≥3 turns（¹⁰ ²⁵）、PII content-capture off-by-default（³⁷）。
- **可採納的明確 gap**：(1) explicit task primitive（DAG 優於 flat list）；(2) Cat 12 標準化在 OTel GenAI conventions；(3) pass^k 入 eval harness；(4) 分層 compaction（tool-result clearing 先行）；(5) tool-description lint step。
- **建議當假設測量、勿當目標的弱證據項**：agent-invokable compaction 的 22.7% 數字（⁶）、typed eviction 的 CWL paper（²⁷）、binary confidence UX（⁴⁰）。

---

## 五、證據品質與保留意見

**Vendor / practitioner 來源（非 peer-reviewed 實證，方向可信但數字應 hedge）**
- Anthropic engineering posts（multi-agent research system ²、effective harnesses ⁷ ¹⁰、context engineering ²³、Building Effective Agents ¹⁸、auto-mode ²⁸、tool-result clearing ²⁴）：first-party、廣泛引用、credible，但 90.2% / 15x / 4x / ~40% / 93% / 17% 多為 Anthropic 自家 internal eval 或單一 improvement cycle 的 self-report，是 directional / order-of-magnitude，非外部可重現 benchmark。
- LangChain（multi-agent benchmark ¹⁶、interrupt HITL ²⁹）：credible practitioner / vendor docs，但 ¹⁶ 是單一 self-published vendor benchmark，distractor-domain threshold 視為 indicative，有 framing incentive。
- Nicolas Bustamante blog（agent-controlled compaction ⁶）：**最弱來源**，22.7%-token-reduction-with-no-accuracy-loss 是單一 practitioner 無 published methodology / benchmark 的自陳；質性洞見成立、數字勿當已確立證據。

**Unverified / mis-attributed citations（引用前必須再核）**
- **arXiv 2606.11213（CWL / structured eviction，²⁷）**：ID = 2026-06（本月），fetch 未 corroborate，title / method 未確認——**原理可信，paper citation unconfirmed，勿當 authoritative 引用**。
- **arXiv 2512.05470（file-system-as-memory，²³ 學術半段）**：未獨立核實（ID 為 2025-12 有效日期但 paper 未確認）；Anthropic-sourced 半段強，學術 citation 為弱環節。
- **observability finding 的 ε/λ reliability（³⁴）**：finding 把兩篇 2026 paper conflate，'23,392 episodes' 與所引 URL（arXiv 2603.29231）似 mis-attributed（ε 數字應屬 ReliabilityBench arXiv 2601.06112）——**技術結論（加 ε/λ 軸）成立，citation precision 不成立**。
- **arXiv 2601.22311（receding-horizon，¹³）與 2512.03560（RP-ReAct，⁵）與 2602.11619（behavioral consistency ³⁸）**：很新 / 未來日期 preprint，未獨立核實；底層原理（MPC-style replanning / planner-supervisor / consistency as distinct axis）合理，但 empirical strength 倚賴單篇 self-report。
- **self-correction critical survey citation（²¹）**：URL（arXiv 2410.20513）對應「Self-correction is Not An Innate Capability」而非通常引用的 Pan et al. TACL critical survey（arXiv 2308.03188）；兩者被 conflate，substance 正確、一個 citation mislabeled。
- **R-Judge AgentMonitor attribution（³⁰）**：「AgentMonitor uses an LLM to monitor and halt unsafe actions」讀來像 related-work extrapolation 而非 R-Judge 自身核心結論，引用前再核。
- **self-conditioning term/attribution（multi-agent ¹⁵）**：term 與 attribution（指向 MAST URL）muddled，讀來更像 Spark-to-Fire 的 cascade theme，引用前 double-check。

**特別標示 weak / mis-sourced（agent-ux）**
- **agentic-design.ai 來源（⁴⁰，findings 5 & 6）**：「going silent erodes trust」「binary confidence 讓使用者決策更快」「autonomy without transparency creates friction」三項 specifics 在 fetch 該頁時 **未找到**，讀來 embellished / mis-attributed；**勿引用 binary-confidence「decided faster」為 established result**。方向建議（coarse confident/uncertain 勝 raw score、earned-trust ramp、glanceable progress streaming）仍合理，但 streaming-state 半段靠 arXiv 2604.14228（已逐字核實）獨立存活，非靠這些來源。

**已獨立驗證 / 高信心（可放心引用）**
- arXiv 2604.14228（Dive into Claude Code，³⁹ ⁴⁰）：20%→40% / 93% / 七 permission mode / deny-first / 27% / 17% 等多項已逐字對 paper 核實。
- arXiv 2510.00615（ACON，²⁵）：WebSearch 驗證為真（Microsoft，有官方實作），26–54% peak-token-reduction + >95% retention + ~99% cost 由多個獨立 summary 佐證。
- arXiv 2503.13657（MAST，³⁵ ³⁶）：真實、well-known、NeurIPS 2025；1,600+ trace / 7 框架 / 14 mode / Kappa 0.88 準確。
- arXiv 2406.12045（τ-bench，³³）、arXiv 2310.01798（Cannot Self-Correct，¹⁷）、2024.emnlp-main.714（Key Condition Verification，²⁰）、arXiv 2406.16008（Lost/Found in the Middle，²⁶）、ToolEmu / R-Judge（³¹ ³²）：landmark / widely-replicated。
- OTel GenAI conventions（³⁷）：真實、active CNCF SIG（conventions 仍部分 experimental，但架構建議 sound）。
- arXiv 2509.09677（Long Horizon Execution，⁸）、2604.02460（Single vs Multi-Agent，¹）、2509.18847（Structured Reflection，¹⁹）：已 spot-check / WebSearch 驗證為真。

**研究盲點**
- 多數可靠性數字來自 Anthropic 自家 eval 或單篇 self-report，缺第三方獨立重現。
- 2026 年 preprint（含 multi-agent error-cascade、reliability science、structured eviction）尚未被獨立 replicate，確切百分比（17.2x / 4.4x / 96.4% / 22.7% / 23,392）應引方向、hedge 數字。
- enterprise multi-tenant 場景下的 pass^k / fault-injection 實證仍稀少——本專案的 trace persistence 反而是少數能廉價產生這類數據的位置。

---

## 六、來源清單（去重，僅列實際引用的真實 URL）

1. https://arxiv.org/html/2604.02460v1 — Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets (2026)
2. https://www.anthropic.com/engineering/multi-agent-research-system — How we built our multi-agent research system (Anthropic, 2025)
3. https://theaiengineer.substack.com/p/how-anthropic-built-multi-agent-deep — Anthropic's Multi-Agent Research Architecture Explained (2025)
4. https://arxiv.org/pdf/2505.15182 — ReflAct: World-Grounded Decision Making in LLM Agents via Goal-State Reflection (2025)
5. https://arxiv.org/abs/2512.03560 — Reason-Plan-ReAct: A Reasoner-Planner Supervising a ReAct Executor for Complex Enterprise Tasks (2025) [unverified]
6. https://nicolasbustamante.com/blog/long-running-agent-engineering — Long Running Agent Engineering (Nicolas Bustamante, 2025) [weak — single blog]
7. https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents — Effective harnesses for long-running agents (Anthropic, 2025)
8. https://arxiv.org/html/2509.09677v3 — The Illusion of Diminishing Returns: Measuring Long Horizon Execution in LLMs (2025)
9. https://www.emergentmind.com/topics/plan-then-execute-llm-agents — Plan-then-Execute LLM Agents (survey of Plan-and-Act, EAGLET, HiPlan) (2025) [aggregator]
10. https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents — Effective context engineering for AI agents (Anthropic, 2025)
11. https://venturebeat.com/orchestration/claude-codes-tasks-update-lets-agents-work-longer-and-coordinate-across — Claude Code's 'Tasks' update (VentureBeat, 2026) [single secondary source]
12. https://arxiv.org/pdf/2509.25370 — Where LLM Agents Fail and How They Can Learn from Failures (2025) [counts unverified]
13. https://arxiv.org/html/2601.22311 — Why Reasoning Fails to Plan: A Planning-Centric Analysis of Long-Horizon Decision Making in LLM Agents (2026) [paper unverified]
14. https://arxiv.org/html/2603.04474v1 — From Spark to Fire: Modeling and Mitigating Error Cascades in LLM-Based Multi-Agent Collaboration (2026) [specific figures unverified]
15. https://arxiv.org/html/2503.13657v1 — Why Do Multi-Agent LLM Systems Fail? (MAST) (2025)
16. https://www.langchain.com/blog/benchmarking-multi-agent-architectures — Benchmarking Multi-Agent Architectures (LangChain, 2025) [single vendor benchmark]
17. https://arxiv.org/abs/2310.01798 — Large Language Models Cannot Self-Correct Reasoning Yet (ICLR 2024)
18. https://www.anthropic.com/research/building-effective-agents — Building Effective Agents (Anthropic, 2024)
19. https://arxiv.org/pdf/2509.18847 — Failure Makes the Agent Stronger: Structured Reflection for Reliable Tool Interactions (2025)
20. https://aclanthology.org/2024.emnlp-main.714/ — Large Language Models Can Self-Correct with Key Condition Verification (EMNLP 2024)
21. https://arxiv.org/pdf/2410.20513 — Self-correction is Not An Innate Capability in Language Models (2024) [citation conflated with TACL survey]
22. https://arxiv.org/html/2507.21504v1 — Evaluation and Benchmarking of LLM Agents: A Survey (2025) [API count approximate]
23. https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents — (同 10)
24. https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools — Context engineering: memory, compaction, and tool clearing (Claude Cookbook, 2025)
25. https://arxiv.org/html/2510.00615 — ACON: Optimizing Context Compression for Long-horizon LLM Agents (2025) [verified]
26. https://arxiv.org/abs/2406.16008 — Found in the Middle: Calibrating Positional Attention Bias Improves Long Context Utilization (2024)
27. https://arxiv.org/html/2606.11213 — Beyond Compaction: Structured Context Eviction for Long-Horizon Agents (2026) [paper unverified]
28. https://www.anthropic.com/engineering/claude-code-auto-mode — How we built Claude Code auto mode (Anthropic, 2025)
29. https://www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt — Making it easier to build human-in-the-loop agents with interrupt (LangChain, 2024)
30. https://arxiv.org/html/2401.10019v3 — R-Judge: Benchmarking Safety Risk Awareness for LLM Agents (2024) [AgentMonitor attribution to verify]
31. https://aclanthology.org/anthology-files/anthology-files/pdf/findings/2024.findings-emnlp.79.pdf — R-Judge (EMNLP 2024 Findings)
32. https://openreview.net/forum?id=GEcwtMk1uA — Identifying the Risks of LM Agents with an LM-Emulated Sandbox (ToolEmu) (2024)
33. https://arxiv.org/abs/2406.12045 — τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains (2024)
34. https://arxiv.org/pdf/2603.29231 — Beyond pass@1: A Reliability Science Framework for Long-Horizon LLM Agents (2026) [citation conflated; ε figures likely from ReliabilityBench]
35. https://arxiv.org/abs/2503.13657 — Why Do Multi-Agent LLM Systems Fail? (MAST taxonomy) (2025)
36. https://github.com/multi-agent-systems-failure-taxonomy/MAST — MAST GitHub (2025)
37. https://opentelemetry.io/blog/2026/genai-observability/ — Inside the LLM Call: GenAI Observability with OpenTelemetry (2026)
38. https://arxiv.org/pdf/2602.11619 — When Agents Disagree With Themselves: Measuring Behavioral Consistency in LLM-Based Agents (2026) [paper unverified]
39. https://arxiv.org/html/2604.14228v1 — Dive into Claude Code: The Design Space of Today's and Future AI Agent Systems (2026) [verified verbatim]
40. https://agentic-design.ai/patterns/ui-ux-patterns — UI/UX & Human-AI Interaction — Agentic Design Patterns (2025) [weak — specific quotes not found on page]
41. https://www.visible-language.org/Issue-59-2/addressing-uncertainty-in-llm-outputs-for-trust-calibration-through-visualization-and-user-interface-design.pdf — Addressing Uncertainty in LLM Outputs for Trust Calibration (Visible Language 59.2, 2025) [single source, uncorroborated]
