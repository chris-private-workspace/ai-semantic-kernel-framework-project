# Agent Harness 深化方案 — Verification 入 Loop / Subagent 完備化 / Model 策略與 Config 分層

**Purpose**: 把「5 點深化討論」收斂出的三個方向（① verification 入 loop、② TEAMMATE/HANDOFF 完備化、③ ModelProfile 擴展 + tenant config 分層）做成**完整終態設計 + 全路徑切片分解**。不是 MVP 清單——每個工作流都定義「達到目標」的終態，再分解為可執行的 sprint 切片；執行時仍遵守 thin-spike → retrospective → design-note-extract 紀律（本文是路線圖與設計依據，不是預寫的正式規劃文件）。
**Category / Scope**: Planning / Architecture deepening proposal（cross-cutting：Cat 1 / 9 / 10 / 11 + adapters + platform_layer + core/config）
**Created**: 2026-06-10
**Last Modified**: 2026-06-10
**Status**: Active (proposal；基於 git HEAD Sprint 57.97)
**Method**: 3 個 Explore agent 平行深挖（verification wrapper 控制流 / subagent 四模式 + mailbox + session 模型 / ModelProfile 消費點 + config 先例）+ 直接 grep 驗證關鍵矛盾（HandoffService 存在性）+ next-phase-candidates.md carryover 對齊。行號為探查所得錨點（近似）。

> **上游文件鏈**：[`agent-harness-cc-parity-20260607.md`](../5-status/agent-harness-cc-parity-20260607.md)（部件對照 + C 類缺口）→ [`cc-source-blueprint-pause-resume-phases-20260608.md`](../5-status/cc-source-blueprint-pause-resume-phases-20260608.md)（CC 證偽：非 6-phase、無 durable resume）→ 本文（三工作流完整方案）。
> **權威提醒**：執行時每個切片仍須按 `.claude/rules/sprint-workflow.md` 走 plan → checklist → Day-0 三-prong → code；本文的 file:line 在各切片 Day 0 須重新 grep 驗證（repo 會繼續演進）。

---

## 0. 總綱

### 0.1 三個工作流與兩個收斂洞察

| 工作流 | 解決的深化點 | 一句話終態 |
|--------|-------------|-----------|
| **A. Verification 入 Loop** | 第 1 點（verify/retry 在外圍）+ 第 5 點（無 self-critique phase） | 品質驗證成為主 loop 的 pre-delivery 齒輪：失敗→feedback 回注→同一 loop 繼續跑→重驗；máx 修正後可升級為人類介入（與 pause-resume 組合） |
| **B. Subagent 完備化** | 第 3 點（subagent 未完成）+ C 類 live message injection | 四模式全真實：TEAMMATE 變成可中途溝通的長壽協作 child；injection primitive 同時服務 chat UX 與 TEAMMATE |
| **C. Model 策略 + Config 分層** | 第 4 點（模型策略單一）+ cc-parity §7.3 config 分層 | 模型/驗證/HITL/guardrail policy 全部 tenant 可治理；cheap tier 擴到 compaction；risky-action detector 落地 |

**收斂洞察 1（A）**：你要的「self-critique phase」效果，不需要 6-phase 重構——CC 源碼已證偽 6-phase（`cc-source-blueprint` 發現①）。把 verification 從外圍 wrapper 搬進 57.93 已建好的 in-loop pre-delivery 接縫，修正以 message 回注、同一 loop 多跑一 turn，**就是** critique loop 的真實形狀，且全程可觀測（correction = 正常 TAO turn，Inspector 自然顯示）。

**收斂洞察 2（B）**：TEAMMATE 多輪化需要的「parent 中途給 child 訊息」與 C 類缺口「使用者中途給 agent 補指令（live message injection）」是**同一個 loop primitive**：在 between-turns 接縫（57.92 已開）drain 一個 message inbox。建一次 primitive，拿兩個 payoff。

### 0.2 現況更正（重要）

**HANDOFF 的 platform 層接管其實已經完成**（先前對話與 57.94-96 carryover 文字均過時）。直接 grep 證實：

- `platform_layer/handoff/` 存在：`service.py`（`boot_handoff`）+ `context_carry.py` + `persona_registry.py`
- `router.py:639` 偵測 `stop_reason == "handoff"` → `HandoffService().boot_handoff(...)` → 建 child session + audit + `AgentHandoff` SSE
- Git 證據：`2a872210`（57.68 HANDOFF control-transfer + platform session-boot）、`3090e8b7`（57.69 context carry + FE session-pivot）、`f2b74be9`（57.70 per-tenant agent-spec catalog）
- DB：`sessions.py:98-100` `handoff_parent_id` FK（migration 0022）；`handoff/service.py:159-162` carried_context 序列化進 `meta_data`；child 繼承 parent `tenant_id`（service.py:167 多租戶鐵律註釋）

→ 工作流 B 的 HANDOFF 部分從「從零建 platform service」縮為「收尾 + 治理」（§3.4）。`next-phase-candidates.md` 的 carryover 是歷史紀錄不回改，本文為 forward 修正。

### 0.3 終態檢核表（「達到目標」的可驗收定義）

完成本方案三工作流後，對照理想 harness 圖 + 5 點 + cc-parity C 類：

| 檢核項 | 現況 | 本方案後 |
|--------|------|---------|
| 每圈 6 齒輪穿過主 loop | ✅（cc-parity §1） | ✅ 不變 |
| 交付前品質閉環（verify→correct→re-verify）在 loop 內 | ❌ wrapper 外圍 | ✅ A1 |
| 機器驗證失敗 → 人類介入（HITL 接管 verification） | ❌ | ✅ A2 |
| Resume 路徑也有 verification | ❌（結構性漏洞，見 §2.1） | ✅ A1 |
| 使用者中途注入指令（live message injection） | ❌ | ✅ B1 |
| TEAMMATE 真多輪協作 | ❌ 單發+mailbox | ✅ B2 |
| HANDOFF 真控制權轉移 | ✅（57.68-70，本文更正） | ✅ B3 收尾治理 |
| Child 也受 Cat 9/10 治理 | ❌ lean child | ✅ B4 |
| Verification 跑 cheap tier | ✅（57.97） | ✅ 不變 |
| Compaction 跑 cheap tier | ❌ | ✅ C2 |
| Per-tenant model policy | ❌ 單層 Settings | ✅ C1 |
| Per-tenant verification/HITL/guardrail policy | ❌ hardcoded | ✅ C3 |
| Risky-action（dangerous command 等價物）detector | ❌ | ✅ C3 |
| Skills system（lazy load） | ❌ | ⏭️ 本方案外（§7） |

---

## 1. 工作流 A — Verification 入 Loop（合併第 1 + 5 點）

### 1.1 現況證據（Explore 探查 + 既有 sprint 事實）

**Wrapper 架構**（`verification/correction_loop.py`）：
- `run_with_verification()`（:83-91）是 `AgentLoop.run()` 的外層 wrapper；`max_correction_attempts=2`（3 次總運行）
- 攔截 `LoopCompleted` 不立即 yield（:145），跑 registry 內全部 verifier，失敗則 `_build_correction_input()` 把修正指示拼成新 `user_input` **重新呼叫 `agent_loop.run()`**（:242-243 獨立 while loop）
- 超限 → emit `LoopCompleted(stop_reason="verification_failed")`（:229-239）
- 接線：`handler.py:488-494` `make_chat_verifier_registry(profile.cheap, ...)`（57.97 cheap tier）；router 在 chat POST 路徑套 wrapper；echo path 不啟用
- 既有資產：`VerificationPassed/Failed` 事件已 wire-ready（`_contracts/events.py:319-343`，含 `correction_attempt` 欄位）；judge tokens → cost ledger `_verification` sub_type（57.82）；verification 預設 ON for real_llm（57.83）

**In-loop pre-delivery 接縫**（57.93，`loop.py`）：
- :2014-2058：final answer parse 之後、yield `LLMResponded` 之前，output-guardrail 檢查；ESCALATE → `_cat9_output_escalate_pause`（:1371-1390）→ `_emit_deferred_pause(kind="output")`（:1412-1509）
- resume() 的 output 分支（:2643-2685）：APPROVED → `_replay_approved_output`（:2805-2856）re-emit 不 re-call LLM

**Wrapper 架構的四個結構性弱點**：
1. **修正 = 重開一局**：每次 correction 重新進入 `run()`，重付完整 prompt 組裝 + 重開 LOOP span + turn counter 歸零；in-loop 修正只是同一 loop 的下一 turn（prefix 不變 → Cat 4 prompt cache 直接命中，token 成本更低）
2. **Resume 路徑零 verification**（✅ 已查證屬實，2026-06-10 直接讀碼確認，不再是推測）：wrapper 只能包 `run()`。主 chat 路徑在 `router.py:432` 套 `run_with_verification`，但 `POST /{session_id}/resume`（`router.py:878`）→ `_stream_resume_events`（`router.py:827`）**直接** `async for event in loop.resume(...)`，**無** `run_with_verification` 包裹 → 任何「HITL pause → resume」的對話，其恢復後產生的最終答案**完全不經 verification**。In-loop gate 天然覆蓋兩個入口（resume 驅動共享 `_run_turns`），一次補上兩條路徑——這是 A1 從「優化」升級為「修結構洞」的關鍵論據
3. **事件流被動手術**：`LoopCompleted` 被捕獲抑制；correction 重跑時前端收到多組 loop 事件，語義混濁
4. **Verifier 看不到 loop 內部**：只能驗最終字串，無法做 trace-aware critique（A3 擴展的前提）

### 1.2 終態設計：pre-delivery 雙 gate

每個 candidate final answer 在交付前依序穿過兩個 gate（**guardrail 先、verification 後**——安全檢查便宜且 ESCALATE 本來就交人眼；被擋的內容不浪費 judge tokens；修正後的新 candidate 重新進同一接縫 → 兩個 gate 自動重跑）：

```
candidate = parse(LLM final answer)
├─ Gate 1: Cat 9 output guardrail（既有 57.93）
│   ├─ BLOCK → 既有 block 路徑
│   ├─ ESCALATE → _emit_deferred_pause(kind="output")（既有）
│   └─ PASS ↓
├─ Gate 2: Cat 10 verification（★ 新，in-loop）
│   ├─ PASS → yield VerificationPassed → 交付（LLMResponded → LoopCompleted end_turn）
│   ├─ FAIL 且 attempts < max:
│   │     yield VerificationFailed(correction_attempt=n)
│   │     append 修正 feedback Message 到 state.messages
│   │     state.verification_attempts += 1（durable）
│   │     continue   # 同一 while loop 的下一 turn —— 這就是 critique loop
│   └─ FAIL 且 attempts == max → 終態策略（可配置，C3 接 per-tenant）:
│         a) stop_reason="verification_failed"（保留現語義，預設）
│         b) deliver-with-flag（交付但標記）
│         c) ESCALATE → _emit_deferred_pause(kind="verification")（A2）
```

**關鍵語義決策**：
- **attempt counter 必須 durable**（進 checkpoint）：修正途中可能撞上 guardrail ESCALATE pause，resume 後計數必須延續
- **Replay 不重驗**：人類 APPROVED 的輸出走 `_replay_approved_output` 直接交付——人類權威高於機器 judge，重驗是浪費也是邏輯倒置
- **A2 的 reject-with-note**：人類拒絕時附 note → note 作為 correction feedback 回注 → loop 再跑一輪（human-coached correction）。機器修正 2 次 → 人類教練 1 次，這是企業級閉環的完整形狀，CC 沒有此能力（CC 核心 loop 無 self-critique，cc-blueprint §1.3）

### 1.3 Touch points（A1 範圍）

| 檔案 | 變更 |
|------|------|
| `loop.py` | 注入 `verifier_registry`（與 `guardrail_engine` 同列）；新 `_cat10_verify_gate()` helper（命名鏡像 `_cat9_*` 家族）；correction feedback 模板自 `correction_loop.py` 遷入；judge token 累積改由 loop 直接填 `LoopCompleted.verification_*_tokens`（router/cost-ledger 介面不變） |
| `_contracts/state.py` | `LoopState` 加 durable `verification_attempts: int = 0` |
| `handler.py` | registry 直接給 loop ctor（不再回傳給 router 套 wrapper） |
| `router.py` | 移除 `run_with_verification` 包裹 |
| `correction_loop.py` | 確認 chat 為唯一消費者（Day-0 grep）後**移除**（AP-11 不留雙路徑；wrapper 留在 git history 供回滾） |
| 測試 | `test_correction_loop.py`（unit）轉換為 in-loop 等價測試（Never-Delete → convert，57.94 precedent）；`test_chat_verification_smoke.py` / `test_verification.py` / `test_sse_verification_serialization.py` 應大致續綠（wire 事件不變） |
| 事件 | `VerificationPassed/Failed` 不變 → **無 wire schema/codegen 變更** |

### 1.4 切片分解

| 切片 | 內容 | 規模感 |
|------|------|--------|
| **A1** | in-loop verify gate + 修正回注 + durable counter + wrapper 退役 + resume 路徑覆蓋驗證 | 1 sprint（觸 loop.py 的 new-domain spike，類比 57.94 的 0.60 class） |
| **A2** | `kind="verification"` deferred pause + 人類 approve/reject-with-note 流 + replay 不重驗 + FE approval card 復用 | 1 sprint（複用 57.91-93 pause 全套基建，偏小） |
| **A3**（後置可選） | trace-aware critique verifier（輸入含近期 turns/tool errors）+ cheap-judge accuracy 正式 benchmark（design note 24 carryover） | 1 sprint |

### 1.5 風險與回滾

- **loop.py 複雜度增長**：以 `_cat10_*` helper 家族隔離；57.91-93 的 `_cat9_*` 模式已驗證此手法可控
- **行為變化**：correction 在 Inspector 變成可見的額外 turn——這是 feature 不是 regression（取代 wrapper 時代的多組 loop 事件混流）
- **延遲/成本**：judge 呼叫本來就在主路徑（57.83 起預設 ON）；位置遷移不增延遲，prompt cache 命中反而降 correction 成本
- **回滾**：沿用 `chat_verification_mode` env gate；極端情況 revert commit 恢復 wrapper（git history 在）
- **Monitor**（57.83 carryover 延續）：verification_failed rate / correction rate / FP creep 經 `verification_log` + `_verification` ledger 觀測

### 1.6 DoD（drive-through 硬約束）

真 UI + 真後端 + 真 Azure：構造一個必然 fail-then-pass 的 prompt（或暫調 judge 閾值），觀測 Inspector 顯示 `VerificationFailed(attempt=1)` → 修正 turn → `VerificationPassed` → 答案渲染；cost_ledger 顯示 judge tokens 在 cheap tier；resume 一個 paused session 確認恢復後的回答也經過 verification。

---

## 2. 工作流 B — Subagent 完備化（第 3 點 + C 類 live injection）

### 2.1 現況（探查證據）

| 部件 | 現況 | 錨點 |
|------|------|------|
| FORK | ✅ 真 child loop（多輪+工具，depth 限制） | `fork.py:108-194`；`ChildLoopFactory`（`_contracts/subagent.py:95-101`） |
| AS_TOOL | ✅ 委派 FORK | `as_tool.py:70-114` |
| TEAMMATE | 🟡 單發 chat() + mailbox 單向投遞；**parent 沒有收取代碼** | `teammate.py:56-156`（D15 simplification 註明 Phase 55+ 多輪化） |
| HANDOFF | ✅ platform 層已完成（§0.2 更正）；dispatcher 模式仍是 UUID stub | `handoff.py:37-62`（stub）vs `router.py:639` + `handoff/service.py`（真路徑） |
| Mailbox | per-request in-memory `dict[UUID, dict[str, asyncio.Queue]]`，無上限/TTL/持久化 | `mailbox.py:46-100` |
| Child 可觀測性 | ✅ node-level（57.95）+ per-turn TAO 展開（57.96） | `SubagentChildEvent` |
| Child transcript | ❌ ephemeral（無 DB row、無 checkpoint） | `fork.py:138`（uuid4 local scope） |
| Child governance | ❌ lean child（無 Cat 9/10） | design note 20 deferred 清單 |

### 2.2 B1 — Between-turns message injection primitive（一個 primitive，兩個 payoff）

**設計**：
- Cat 1 新增 provider-neutral 小 contract：`MessageInbox`（或 `Callable[[], list[Message]]`），可選注入 loop
- Drain 位置：`_run_turns` 頂部 between-turns 接縫（57.92 guardrail check 所在）；**先 drain inbox、後跑 between-turns guardrail** → 注入內容自動受 Cat 9 檢查（免費的安全組合）
- 注入語義誠實化：loop 在 LLM call / tool exec 期間阻塞時，注入落在**下一個 turn 邊界**（與 CC FlushGate 的 drain-at-flush-point 同語義，cc-blueprint §2.1）
- API：`POST /chat/{session_id}/inject`（auth + tenant check + session active 檢查）；新 SSE 事件 `MessageInjected`（走 57.96 已熟的 4-file codegen chain + 2 parity tests）
- 後端 channel：router/app-state 持有 active session_id → queue 註冊表（注意 Risk Class C：測試需 reset fixture）
- FE：chat composer 在 run 中保持可用 → 改送 inject；timeline 渲染注入訊息
- **TEAMMATE 複用**：child loop 的 inbox = parent 可寫的 mailbox 視圖——同一接縫、同一 drain 邏輯

### 2.3 B2 — TEAMMATE 真多輪協作

- `TeammateExecutor` 改為 `factory(budget)` 建 child loop（FORK 已驗證的路），初始 `user_input=task`
- **Parent→child**：child 的 `MessageInbox` 接 mailbox channel（B1 primitive）
- **Child→parent**：child 工具集含 `send_to_parent`（mailbox 工具已有雛形 `tools.py:107-125`）；child turn-stream 經 57.96 relay 免費可見
- Parent 等待語義 v1：await-completion（同 FORK）；detached 長壽 teammate（需生命週期管理）後置
- `SubagentBudget` frozen dataclass 不需改（duration 預設可放寬）
- 與 FORK 的差異定義清晰化：FORK = 隔離一次性任務；TEAMMATE = 可中途雙向溝通的協作 child

### 2.4 B3 — HANDOFF 收尾 + transcript 鏈

範圍已縮小（§0.2），剩四件：
1. **Dispatcher stub 對齊**（AP-2/AP-11 衛生）：`HandoffExecutor` UUID stub 與真路徑（handoff tool → stop_reason → HandoffService）二選一收斂——建議讓 dispatcher 模式委派真路徑或明確刪除 stub 模式
2. **治理**：`target_agent` allowlist + tenant boundary 政策（`handoff.py:17` deferred 註釋）→ 掛到 C3 的 per-tenant policy
3. **Parent-chain 遍歷**：sessions API 暴露 handoff lineage（`handoff_parent_id` 已在 DB）+ FE session 列表顯示鏈
4. **`AD-Subagent-Transcript-Isolation`**：FORK/TEAMMATE child transcript 持久化（借 CC `parentUuid / logicalParentUuid` 鏈 + `agentId / isSidechain` 欄位設計，cc-blueprint §2.4——CC 少數值得借的序列化設計）

### 2.5 B4 — Child governance + failure policies（+ depth>1 後置）

- **Child 必須受 Cat 9 治理**（企業鐵律：child 不能成為 guardrail 旁路）：`ChildLoopFactory` 閉包注入 guardrail_engine（可選 verifier）——目前 lean child 是已知 deferred（design note 20）
- Failure policies：FAIL_FAST / SOFT / PARTIAL（多 spawn 場景的失敗語義）
- Recursion depth > 1：child-of-child 的 `subagent_id` 二級路由 + nested 渲染——等真實需求出現再做（YAGNI）

### 2.6 DoD

- B1：真 UI mid-run 注入「補充指令」，下一 turn LLM 確認收到並改變行為；注入內容觸發 between-turns guardrail 的 case 也驗
- B2：parent spawn teammate → 中途 parent 注入更新 → child 調整 → child send_to_parent → parent 整合回答；Inspector Tree 全程可見
- B3：handoff lineage 在 sessions UI 可追；非 allowlist target 被拒且 audit 留痕

---

## 3. 工作流 C — Model 策略 + Config 分層（第 4 點 + cc-parity §7.3）

### 3.1 現況（探查證據）

- `ModelProfile{action, cheap}` frozen dataclass（`adapters/_base/model_profile.py:46-58`）；`build_azure_model_profile`（`profile.py:54-82`，`AZURE_OPENAI_CHEAP_*` env，unset → `cheap is action`）
- ChatClient 消費點地圖：main loop（action）/ semantic compactor（action，**cheap 候選**，`handler.py:374` + `semantic.py:67-82`）/ memory extraction（action，cheap 候選但精度敏感，`extraction.py:62-80`）/ verification（✅ cheap，`handler.py:492-493`）/ child loop（action）
- 構建時機：`build_real_llm_handler` 每 request 呼叫、`AzureOpenAIAdapter` 構建輕量 → per-tenant profile 可行
- Config 單層：`core/config/__init__.py:28-162` 單一 `Settings`（lru_cache）；`chat_verification_mode` 全局；HITL escalate 工具清單 hardcoded（`handler.py:150` frozenset + 註釋指向 deferred 的 capability_matrix.yaml）
- Per-tenant override 三先例：`feature_flags.tenant_overrides`（registry-table JSONB）/ `tenant.meta_data`（JSONB，曾承載 rate_limits 後畢業到專表 0019-0021）/ quota_overrides
- design note 24 open invariants：compaction cheap tier / thread profile into loop / per-tenant policy / judge benchmark / non-Azure builders
- `llm_pricing.yml` keys：gpt-4o-mini / gpt-5.2 / gpt-5.4 / gpt-5.4-mini / gpt-5.4-nano / claude-3.7-sonnet

### 3.2 儲存決策矩陣（tenant policy 放哪）

| 選項 | 先例 | 優點 | 缺點 | 判斷 |
|------|------|------|------|------|
| `tenant.meta_data["model_policy"]` JSONB | rate_limits（57.48）/ quota_overrides（57.56） | 零 migration、append_audit 既有、spike 最便宜 | schema-less；rate_limits 史證明成熟後要畢業 | ✅ **C1 起步** |
| 專表 `tenant_policies` | `rate_limit_configs`（0019） | typed + RLS + 索引 + 版本化 | migration + 面積大 | C3 政策面擴寬時畢業 |
| registry-table JSONB | feature_flags | 適合「per-key 跨租戶」 | model policy 是 per-tenant 不是 per-key | ❌ 形狀不合 |

**Policy shape v1**（C1 只做 model 欄位）：`{"action_deployment", "action_model", "cheap_deployment", "cheap_model"}`；寫入時**對 `llm_pricing.yml` 驗證**（不認識的 model 拒收）→ 保證 cost ledger 永遠不會遇到無價 model（治理不變量）。

### 3.3 解析鏈設計

```
system defaults（Settings / env） → tenant override（DB，TTL cache ~60s + PUT 即失效）
  → build_real_llm_handler(tenant_id) 內 resolve → build_azure_model_profile(overrides) → profile
```
- Cache 注意 Risk Class C（module-level singleton 跨 test event loop）：附 autouse reset fixture
- 治理面：`PUT /api/v1/admin/tenants/{id}/model-policy`（admin RBAC）+ `append_audit`（直接 ORM UPDATE + 手動 audit，57.56/57.57 無 canonical service 的既定 pattern）
- **明確不做**「thread ModelProfile into loop」：construction-time DI 已覆蓋所有真實需求；「中間 turn 用 cheap、final 用 strong」是品質投機，無具體用例前不做（AP-6 / YAGNI；design note 24 該項降級為 deferred-indefinitely）

### 3.4 切片分解

| 切片 | 內容 | 備註 |
|------|------|------|
| **C1** | config 分層 spike：meta_data["model_policy"] + resolver + TTL cache + admin PUT + audit + pricing 驗證 | 走 Phase-58 write-side 既定 pattern（57.55-57.57 calibration class 可借）；drive-through：兩租戶各自 model，cost_ledger sub_type 分流可證 |
| **C2** | compaction cheap tier（`semantic.py` summarize → profile.cheap）+ 30+ turn 長對話品質 gate（AP-7 測試既有要求）；memory extraction 維持 strong（無 benchmark 前不降） | design note 24 第一 carryover |
| **C3** | policy 面擴寬：per-tenant verification mode/template、HITL escalate 工具清單（capability_matrix.yaml → tenant override）、guardrail keyword 政策；**+ risky-action detector**（CC bashSecurity 的 server-side 等價物：python_sandbox 代碼模式 / 業務工具破壞性操作 detector，掛進既有 guardrail chain、政策 per-tenant）；policy 畢業到專表評估 | 一次關掉 C 類 dangerous-command + cc-parity §7.5 兩項 |
| **C4**（後置） | non-Azure profile builders（Anthropic → 順帶解鎖 native thinking 路徑 A 的 UI 思考 block；OpenAI） | 30-min provider swap 驗收已是 V2 約束 |

> **⚠️ C1 軟前置 — RBAC-JWT wiring**（2026-06-10 加入）：C1 的 `PUT /api/v1/admin/tenants/{id}/model-policy` 以 admin RBAC gate。但 `AD-RBAC-DB-To-JWT-Wiring-Phase58`（`next-phase-candidates.md`，仍開放）顯示 seeded admin 的 `UserRole` 是 DB-real 但**不 authz-effective**——gating 讀 JWT `roles` claim，OIDC callback 卻寫死 `roles=["user"]`（`auth.py:302`）。若不先接通，C1 的 admin 端點會 gate 在一個永遠是 user 的 JWT 上 → **AP-4 Potemkin（死控件）**，正是 drive-through 鐵律要防的。**C1 Day-0 必須決定**：RBAC-JWT wiring 獨立一個 slice 先做，或折進 C1 scope（建議獨立，因它也解鎖其他 admin 端點）。A1/A2/B1/B2 不依賴此前置，可安全先行。

### 3.5 DoD

- C1：tenant A 設 policy 用 gpt-5.4 / tenant B 不設（default gpt-5.2）→ 同 prompt 各跑一次 → cost_ledger 兩租戶 model sub_type 不同；非法 model 寫入被 422 + audit
- C2：30+ turn 長對話 compaction 走 cheap tier，壓縮品質測試續綠，ledger 顯示 compaction tokens 降級
- C3：tenant 級 escalate 清單生效（A 租戶某工具 ESCALATE、B 租戶直通）；risky-action detector 攔截示例 payload 且可 per-tenant 關閉

---

## 4. 整體排序、依賴與工作量提示

### 4.1 依賴圖

```
A1 (loop.py) ──→ A2 (pause 復用) ──────────→ A3 (可選)
B1 (loop.py) ──→ B2 (TEAMMATE)
                 B3 (HANDOFF 收尾) ──┐
C1 (不觸 loop) ─→ C2          C3 ←──┘ (B3 治理掛 C3 policy)
```
- **loop.py 衝突管理**：A1 與 B1 都動 loop.py → 必須序列化（solo dev 本來就 sequential，但 branch 不要並行開）
- C1 完全不觸 loop.py（handler/adapters/DB），可作為 A/B 之間的節奏調劑

### 4.2 建議 sprint 順序（依你同意的 ①→②→③ 優先序）

| # | 切片 | 關閉什麼 |
|---|------|---------|
| 1 | **A1** in-loop verification gate | 第 1 點核心 + 第 5 點 critique 效果 + resume 驗證漏洞 |
| 2 | **A2** verification-ESCALATE + human-coached correction | 機器→人類完整閉環 |
| 3 | **B1** injection primitive + inject API + FE | C 類 live message injection + TEAMMATE 軌道 |
| 4 | **B2** TEAMMATE 真多輪 | 第 3 點最後一個簡化模式 |
| 5 | **C1** config 分層 + per-tenant model policy | 第 4 點治理面 + cc-parity §7.3 |
| 6 | **B3** HANDOFF 收尾 + transcript 鏈 | Cat 11 衛生 + lineage |
| 7 | **C3** policy 面擴寬 + risky-action detector | C 類 dangerous-command + per-tenant 治理完備 |
| 8 | **C2** compaction cheap tier | 成本第二刀 |
| 9 | **B4** child governance + failure policies | child 治理鐵律 |
| 10 | **A3** trace-critique + judge benchmark（可選） | 品質打磨 |

每切片 = 1 個標準 5-day sprint（Day 0 三-prong 必跑——本文 file:line 屆時重驗）；calibration class 提示：A1/B1 類比 `subagent-child-loop-spike` 0.60（new-domain loop 觸碰）、A2/B2/B3 類比 0.55 系（composition wiring）、C1/C3 類比 Phase-58 write-side 0.65（`-design-decisions`）。

### 4.3 與剩餘 C 類 / cc-parity 演進項的對賬

| cc-parity 項 | 歸宿 |
|--------------|------|
| 多模型 profile（C 類 #1） | ✅ 57.97 已開 + C1/C2 完成 |
| Dangerous command detection（C 類 #2） | C3（server-side 等價物） |
| Live message injection（C 類 #3） | B1 |
| Self-Critique（C 類 #4） | A1/A2（+ A3 深化） |
| Skills System（C 類 #5） | ⏭️ 本方案外，獨立 epic（§5） |
| Config 分層（§7.5 #1） | C1/C3 |
| Tool Pre/Post hook 擴展點（§7.5 #2） | 部分被 guardrail chain 涵蓋；待真實插件需求再評（YAGNI） |
| Prompt stable/dynamic 分層（§7.5 #3） | 既有 3 cache breakpoints 已涵蓋主收益；deferred |

### 4.4 Harness 程式 ↔ UX 軌的 sprint-stream 分配

§6 把 frontend mockup 重建系列列為「正交、照既有 epic 平行推進」，但 solo-dev **一次只能跑一個 sprint**，不存在真平行——本方案 10 個 harness 切片與 UX 重建 epic **共用同一條 sprint 流**。若 10 個 harness 切片連續排，代表未來 ~10-15 個 sprint 幾乎無新使用者面向功能上線，而 cc-parity §6 明言「最後一哩 UX 是更靠前的使用者價值」。故 stream 分配是一個須拍板的決策（本文不替使用者決定，列出選項）：

| 模式 | 描述 | 適用 |
|------|------|------|
| **純序列 harness** | 10 切片連跑完再回 UX | 近期無使用者壓力、優先把引擎做深 |
| **穿插（建議預設）** | 每 2-3 個 harness 切片穿插 1 個 UX 切片 | 引擎深化與使用者價值並進；避免做出沒人能開的引擎 |
| **UX 優先窗口** | 先清一批 UX（死控件 / RBAC wiring / mockup 重建）再進 harness | 近期要 demo / 客戶可用性 milestone |

**C1 浮動觸發**（呼應 §4.1「C1 不觸 loop.py、可作節奏調劑」）：預設 C1 在 #5；若近期目標是**企業治理 milestone**（per-tenant model/policy 是 SaaS 定義性功能），C1 可提前到 **#2**（它無 loop.py 序列化約束，唯一前置是它自己解鎖的 ④b/C3）。反之若優先**認知閉環先成形**，維持 #5。

> 註：本節僅定義「兩軌如何共用 sprint 流」的決策框架；UX epic 的內部排序仍歸其既有 epic（§6），不在本方案切片表內。

---

## 5. 明確不做清單（AP-6 防護，證據鏈見上游兩文件）

| 不做 | 理由 |
|------|------|
| 6-phase 顯式狀態機重構 | CC 源碼證偽（真 CC 是 turn loop）；A1 已交付 critique 效果；除非未來要 phase-boundary checkpoint 才重評 |
| 21-section prompt / 5-stage compaction | dev-CLI 長 session 特化；本項目短對話 + 75% threshold 已夠 |
| MCP 工具層橋接 | 無業務需求前不接（cc-parity §8 已澄清現況）；需求出現時建 McpToolHandler 接 ToolRegistry |
| git-undo / /stuck / TUI / Provider TTL cache | 形態正交（cc-parity §4-A） |
| thread ModelProfile into loop（per-phase 選模） | construction-time DI 已覆蓋全部真實需求；投機彈性 |
| Detached 長壽 teammate / depth>1 | 等真實用例（YAGNI） |

---

## 6. 本方案外的剩餘地圖（指向 next-phase-candidates.md）

- **Skills System（lazy load）**：C 類最後一項，獨立 epic（工具註冊機制延伸 + per-tenant skill 治理）
- **Memory scoring（recency/effectiveness）**：B 類增強
- **IAM Block B/C、SOC 2 + SBOM、Tier 1 IaC**：enterprise 軌（已登記）
- **Frontend mockup 重建系列**：與本方案正交，照既有 epic 推進
- **Non-Azure adapters（C4）+ native thinking UI**：provider 中性已鋪路，需求驅動

---

## Modification History (newest-first)
- 2026-06-10: Add §3.4 C1 軟前置 note — RBAC-JWT wiring (`AD-RBAC-DB-To-JWT-Wiring-Phase58`) must be authz-effective BEFORE C1's admin PUT, else AP-4 Potemkin dead-control; C1 Day-0 decision (separate slice vs fold into C1). A1/A2/B1/B2 unaffected.
- 2026-06-10: Add §4.4 (harness↔UX sprint-stream allocation decision framework + C1 float-to-#2 trigger) + mark §1.1 weakness #2 resume-skips-verification as VERIFIED (router.py:432 wraps run() but :827/:878 resume bypasses run_with_verification — confirmed by direct read, no longer speculative).
- 2026-06-10: Initial creation — 三工作流完整方案（A verification 入 loop / B subagent 完備化 / C model 策略+config 分層）；2 收斂洞察（critique=in-loop verify；injection primitive 雙 payoff）+ 1 現況更正（HANDOFF platform 層 57.68-70 已完成，carryover 文字過時）；10 切片排序 + 終態檢核表 + 不做清單；基於 3 Explore agent 深挖 + HandoffService 直接 grep 驗證。
