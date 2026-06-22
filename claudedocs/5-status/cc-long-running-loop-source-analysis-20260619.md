# CC v2.1.88 源碼剖析 — agent loop 為何能「長時間運行數十小時」

**Purpose**: 用 Claude Code `@anthropic-ai/claude-code` v2.1.88 提取源碼,逐行回答一個具體問題:「用戶發一次 input 後,CC 的 agent loop 憑什麼能自己一直跑(號稱數十小時),又在什麼條件下停下來把控制權交回用戶?」核心結論:**CC 沒有「長時間執行」的特殊機制 —— 它只有一個無轉數上限的 `while(true)` ReAct loop,唯一退出信號是「模型這一輪不再呼叫工具」;所謂「數十小時」= 模型自己持續發 tool_use + 多層壓縮讓 context 永不溢出 + 多層 `continue` 讓錯誤永不致命。**
**Category / Scope**: Status / External-benchmark source study(參考,**非 V2 設計權威**)
**Created**: 2026-06-19
**Last Modified**: 2026-06-19
**Status**: Active(snapshot;基於 CC `@anthropic-ai/claude-code` v2.1.88 提取源碼,2026-03-31 擷取)
**Analysis env / Method**: 親讀 `query.ts` 主迴圈骨架(L219-1729)逐段核實 + 3 個 Explore agent 平行深挖周邊子系統(compaction / 停止條件 / 長運行 enabler)後,**關鍵主張(退出邏輯 / token-budget continuation / retry 常數 / autocompact 門檻)由助手親自讀源碼逐一核對**,非僅採信 agent 回報。所有 `file:line` 與常數均已對源碼驗證。
**權威聲明**:本文是「研究外部 benchmark CC」的筆記,**不是 V2 設計文件**。V2 的長運行設計(`max_turns=8` 有界爆發 + 跨輪 rehydration)以 sprint 57.127 + `chat-v2-agent-loop-capability-drivethrough-20260618.md` §3 為準。

> **源碼位置**:本次分析用的是**已複製進 repo 的工作副本** `reference/claude-code-source-cdoe/src/`(git **untracked**,未 vendored 入版本控制 —— 維持「CC 是外部唯讀標竿」立場,與既有鏈一致)。等同前兩份文件引用的 `C:\Users\Chris\Downloads\CC-Source\`,版本同鎖 v2.1.88。所有行號以此副本為準。

> **既有 CC 分析鏈**:本文承接 [`agent-harness-cc-parity-20260607.md`](agent-harness-cc-parity-20260607.md)(部件級對照)+ [`cc-source-blueprint-pause-resume-phases-20260608.md`](cc-source-blueprint-pause-resume-phases-20260608.md)(phase / pause-resume 證偽)。前兩份回答「CC 有哪些齒輪 / CC 是不是 phase 狀態機 / CC 有沒有 durable resume」;**本文回答它們未深挖的力學:「同一個 `while(true)` loop 憑什麼能跑很久」**。三份互補,行號互相交叉驗證(皆據 `query.ts`,L241-307 主迴圈一致)。

---

## 0. 一句話 + executive

> **核心真相**:CC 的「數十小時」不是一個 feature,是三件事的乘積 ——
> **(1) 結構**:互動式 REPL 的 loop **無轉數上限**,唯一自然停止點是模型 end_turn(本輪無 tool_use);
> **(2) context 不爆**:每次呼叫模型前跑 **5 層由輕到重的壓縮管線**,讓上萬輪對話的 token 永遠落在 window 內;
> **(3) 錯誤不致命**:迴圈內 **7 個 `continue` 自癒站點** + fallback model + 持久重試(6hr cap + 30s 心跳)讓 413 / 過載 / token 撞頂全部變成「恢復後重跑」而非 throw 退出。
> 模型只要持續決定「再呼叫一個工具」,這三件事就讓它能無限跑下去。「停」反而是少數明確事件(end_turn / maxTurns / 中斷 / 不可恢復錯誤)。

主迴圈一覽(`query.ts`,行號已核實):

```
query()  L219  → queryLoop()  L241  → while(true)  L307 … L1728
  每圈:
    L365-467  context 管理管線(5 層,§3)           ← 為何 context 不爆
    L659      callModel() 串流呼叫 LLM
    L557      toolUseBlocks ← 串流中收集 tool_use   ← 唯一退出信號
    L1062     if (!needsFollowUp):  本輪無工具
                …413/media/max-token 恢復(§4)…
                L1267 stop hooks  ·  L1308 token budget continuation(§6)
                L1357 return {reason:'completed'}    ← 唯一「正常結束」
    L1485     工具執行後若被中斷 → return aborted_tools
    L1570     queued commands 注入下一輪(§6)
    L1705     if (maxTurns && nextTurnCount>maxTurns) return max_turns  ← 互動模式不設 maxTurns
    L1714     next.messages=[...舊,...assistant,...toolResults]
    L1727     state=next → 迴圈續跑                  ← ReAct 續跑本體
```

---

## 1. 迴圈骨架:退出由「有沒有 tool_use」單一決定

`queryLoop` 是 async generator,`while(true)` 無條件迴圈(`query.ts:307`)。退出信號**只有一個**,源碼註解(`query.ts:554-556`)寫得很直白:

> `// Set during streaming whenever a tool_use block arrives — the sole loop-exit signal. If false after streaming, we're done (modulo stop-hook retry).`

- `toolUseBlocks: ToolUseBlock[]`(`L557`)在串流中每遇一個 tool_use 就 push。
- `needsFollowUp`(`L558` 初始 false)在 `toolUseBlocks.length > 0` 時轉 true。
- `L1062 if (!needsFollowUp)`:本輪沒有工具 → 進「收尾」分支 → 最終 `L1357 return {reason:'completed'}`。
- 否則(有工具結果)→ `L1714-1727` 把 `[...messagesForQuery, ...assistantMessages, ...toolResults]` 組成下一輪 state → 迴圈。

**意義**:這是純 ReAct。迴圈對「該跑多久」沒有任何意見 —— 是**模型靠持續發 tool_use 來驅動自己**。工具結果回注成下一輪輸入,模型再推理,如此循環。

---

## 2. 為何能「長」:互動模式下沒有轉數上限(結構性根因)

```
L1705:  if (maxTurns && nextTurnCount > maxTurns)   return {reason:'max_turns', turnCount}
L1508:  (中斷路徑同樣檢查)  if (maxTurns && nextTurnCountOnAbort > maxTurns) …
```

`maxTurns` 是**可選參數**(`QueryParams.maxTurns?: number`)。判斷式 `if (maxTurns && ...)` —— **互動式 REPL 根本不傳 `maxTurns`**;它只在 SDK / headless / subagent 場景被設定(cc-parity §3 #1 記 SDK default 200)。

⇒ **互動 session 的 loop 無轉數天花板,唯一自然停止 = 模型選擇 end_turn**。這就是「數十小時」最根本的結構原因:不是它「被設計成能跑久」,是「沒有任何計數器叫它停」。

> **對照 V2**:`handler.py:710` 寫死 `max_turns=8`。這正是你 task-primitive-eval 標示的「有界爆發」邊界。CC 互動模式把這個上限**整個拿掉** —— 差異不是技術能力,是**互動 CLI 信任模型自停 vs 多租戶 server 要可治理上限**的形態選擇。

---

## 3. 長運行的真正 enabler:context 永不溢出(每輪呼叫前 5 層壓縮)

模型能跑上萬輪而不爆 context,靠 `query.ts:365-467` 在**每次 callModel 之前**依序跑的壓縮管線(由輕到重;多數 feature-gated,代表是逐步推出的優化):

| 層 | 實作 / gate | 做什麼 | 觸發 | 行號 |
|---|---|---|---|---|
| 1. tool-result budget | `utils/toolResultStorage.ts` `applyToolResultBudget` | 超大工具結果落盤,訊息裡只留 reference + 預覽 | 工具宣告 `maxResultSizeChars` 超標 | `query.ts:379` |
| 2. snip(`HISTORY_SNIP`) | `snipModule.snipCompactIfNeeded` | 移除舊訊息,**不呼叫 LLM**;回報 `tokensFreed` 去校正 autocompact 門檻 | feature-gated | `query.ts:401-409` |
| 3. microcompact(`CACHED_MICROCOMPACT`) | `services/compact/microCompact.ts` | **純按 `tool_use_id`** 清空最舊工具結果內容(從不看內容,所以與層 1 的內容替換正交) | 時間 / cache-edit | `query.ts:414` |
| 4. context collapse(`CONTEXT_COLLAPSE`) | collapse store + `projectView()` 每輪重放 commit log | 分層折疊,保粒度;若折疊後已低於門檻,則 autocompact 變 no-op(保留 granular context 而非單一摘要) | 跑在 autocompact **之前** | `query.ts:440-447` |
| 5. **autocompact** | `services/compact/autoCompact.ts` | 呼叫 LLM 產生摘要 + 保留最近 K 條,`buildPostCompactMessages` 重建並標 compact boundary | **context 用到 ~93.5%** | `query.ts:454` |

核實過的關鍵常數(`services/compact/autoCompact.ts`):

| 常數 | 值 | 行號 | 意義 |
|---|---|---|---|
| `AUTOCOMPACT_BUFFER_TOKENS` | `13_000` | L62 | 觸發門檻 = `effectiveContextWindow − 13k` |
| `getAutoCompactThreshold(model)` | `window − 13k` | L72-76 | 200k window ⇒ **~187k / 93.5% 觸發** |
| `MAX_OUTPUT_TOKENS_FOR_SUMMARY` | `20_000` | L30 | effective window 還會預扣摘要輸出空間 |
| `MANUAL_COMPACT_BUFFER_TOKENS` | `3_000` | L65 | `/compact` 手動門檻更貼近上限 |
| `MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES` | `3` | L70 | circuit breaker:連 3 次壓縮失敗才放棄,防無限重試燒 API |

> **對照 V2**:你只有**單層** compaction(`CHAT_COMPACTION_TOKEN_BUDGET`,且 ≥3 user turn 才實際壓)。CC 是 **5 層階梯**:輕量層(snip / microcompact,毫秒級、零 LLM)先扛日常,重量層(autocompact,秒級、要 LLM call)最後才上。**這個「便宜的先做、貴的最後做」的階梯,才是 CC 能撐超長對話的工程核心** —— 比「無 maxTurns」更值得學(cc-parity §7.4 已警告:5-stage 對短對話是過度工程,但對 autonomous long task 是剛需)。

---

## 4. 為何不會中途死:錯誤非致命 = 7 個 `continue` 自癒站點 + retry 韌性

迴圈裡每個失敗都不是 `throw` 出迴圈,而是觸發一條特定恢復路徑後 `continue` 回 `while(true)`。`query.ts` 7 個 continue 站點:

| # | 站點 | 觸發 | 恢復動作 |
|---|---|---|---|
| 1 | `L894-951` | 主模型連 3 次 529 過載 → `FallbackTriggeredError` | 切 `fallbackModel`、清過期 assistant、重建 streamingToolExecutor、重試 |
| 2 | `L1089-1116` | prompt too long(413) | 先 drain 已 stage 的 context-collapse |
| 3 | `L1119-1166` | 413 仍在 | reactive compact(完整摘要)後重試 |
| 4 | `L1199-1221` | max_output_tokens 撞頂 | 從 8k escalate 到 64k(`ESCALATED_MAX_TOKENS`)同題重試 |
| 5 | `L1223-1252` | 仍撞頂 | 注入「Resume directly — no apology, no recap」續寫(最多 `MAX_OUTPUT_TOKENS_RECOVERY_LIMIT` 次) |
| 6 | `L1282-1306` | stop hook 回 blockingErrors | 注入錯誤後重跑(`stopHookActive=true`) |
| 7 | `L1316-1340` | token budget 判定續跑 | 注入 nudge 合成訊息(§6) |

⚠️ 多條路徑都有**防死亡螺旋**的明確守衛(源碼註解親述教訓):413 壓不動時**不 fall through 到 stop hooks**(`L1168-1172`:否則 error→hook blocking→retry→error 無限燒 call);stop-hook 重跑時**保留** `hasAttemptedReactiveCompact`(`L1292-1296`:重置會造成 compact→still too long→error→hook→compact 無限迴圈,曾燒掉數千 call)。

底層 API 韌性在 `services/api/withRetry.ts`(常數已核實):

| 常數 | 值 | 行號 |
|---|---|---|
| `DEFAULT_MAX_RETRIES` | `10` | L52 |
| `MAX_529_RETRIES` | `3`(連 3 次 529 → 觸發 fallback) | L54 |
| `PERSISTENT_MAX_BACKOFF_MS` | `5 * 60 * 1000`(5 分鐘) | L96 |
| `PERSISTENT_RESET_CAP_MS` | `6 * 60 * 60 * 1000`(**6 小時**) | L97 |
| `HEARTBEAT_INTERVAL_MS` | `30_000`(30 秒) | L98 |

**Ant-only 無人值守模式**(`CLAUDE_CODE_UNATTENDED_RETRY`,`L101`;非外部 build 預設):rate-limit 持續重試達 **6 小時 reset cap**,每 **30 秒**吐一個 keep-alive 防 orchestrator 判定 session 掉線(`L500`)。**這條就是「掛機跑一整晚不死」的字面實作** —— 但要誠實標明:它是 ant-internal flag,不是公開預設行為。

---

## 5. 何時停下來把控制權交回用戶(4 類 + 1 個特例)

| 停止類型 | 機制 | 行號 | 控制權回到用戶的方式 |
|---|---|---|---|
| **任務完成** | 模型 end_turn(無 tool_use)+ 所有 recovery / stop-hook 都放行 | `L1357` `return {reason:'completed'}` | 正常 return Terminal |
| **轉數上限** | 僅當有設 `maxTurns`(SDK / subagent;互動模式無) | `L1705` `return {reason:'max_turns'}` | return + `max_turns_reached` 附件 |
| **用戶中斷** | Esc → `abortController.signal.aborted` | `L1015`(串流中)/ `L1485`(工具中) | `return {reason:'aborted_streaming'/'aborted_tools'}` |
| **不可恢復錯誤** | 413 壓不動 / 圖太大 / 最後訊息是 API error | `L1175 / L1182 / L1264` | yield 錯誤訊息 + return |
| **危險操作 / 需許可**(特例) | `canUseTool` 在**工具執行層** `await` 一個 Promise | `services/tools/toolExecution.ts:921`、`hooks/useCanUseTool.tsx` | **不是迴圈停**:該工具 `await` 卡住,UI 收集用戶決定後 resolve;迴圈因為在 await 工具批次而被動暫停 |

> **設計洞察(對 V2 最重要,延伸 cc-source-blueprint §2)**:CC **沒有獨立的 pause/resume 狀態機**。「危險操作暫停」只是工具 handler 內 `await` 一個由 UI resolve 的 Promise —— 暫停狀態活在 in-process 的 Promise / AbortController,**不持久化**(這正是 cc-source-blueprint 證偽「CC 無 durable pause-resume」的執行層細節)。`canUseTool` 三種結果:`allow` 直接跑 / `deny` 回 tool_result 錯誤後迴圈續下一輪 / `ask` 彈互動對話阻塞該工具。**注意:permission 不退出迴圈,只阻塞單一工具** —— 迴圈是被動等待。
>
> V2 反而做了更重的東西:HITL ESCALATE → durable checkpoint 暫停 → 獨立 `/resume` 端點重建。CC 是「行程內輕量暫停」,V2 是「跨行程可治理暫停」。差異純粹來自**互動 CLI vs 多租戶 SaaS** 的本質需求,不是誰對誰錯(cc-source-blueprint §2.5 已列「loop phase / 執行中間狀態 CC 根本不存 → V2 自研」)。

---

## 6. 兩個「自主續跑」附加引擎(超越單純 end_turn)

CC 還有兩個機制能在模型「想收手」時把它推回去繼續,**不需用戶再輸入** —— 這是最接近「自動續跑調度器」的真實實作:

### 6.1 Token budget continuation(`query/tokenBudget.ts` 全讀 + `query.ts:1308-1340`)
- **僅在 `feature('TOKEN_BUDGET')` 開且設了 budget 時生效**(`tokenBudget.ts:51-53`:`agentId || budget===null || budget<=0` 直接回 stop)。**預設不啟用** —— 這是 opt-in,不是日常行為。
- 邏輯:本輪用量 `< budget × 0.9`(`COMPLETION_THRESHOLD`)且非報酬遞減 → 注入 `createUserMessage({content: nudgeMessage, isMeta:true})` 再 `continue`(`query.ts:1321-1340`)。
- **報酬遞減守衛**(`tokenBudget.ts:59-62`):`continuationCount≥3 && deltaSinceLastCheck<500 && lastDelta<500`(`DIMINISHING_THRESHOLD=500`)→ 才判定停,避免空轉。
- 本質 = **用合成 `isMeta` user message 自我延續**:模型以為用戶說「繼續」,於是繼續做。`isMeta:true` 讓這訊息在 UI / SDK 層不顯示。

### 6.2 Queued commands 注入(`query.ts:1570-1643`)
- 每輪工具跑完後,把佇列(`utils/messageQueueManager.ts` 的 process-global singleton)裡的 `task-notification`(背景 subagent 完成通知)+ 排隊 `prompt` 轉成 attachment,併入下一輪輸入。
- agent 各自只 drain 屬於自己的(main thread drain `agentId===undefined`,subagent drain 自己的 id;`L1570-1578`)。
- slash command **排除**(`L1573`,要走 turn 結束後的 `processSlashCommand`,不能當文字塞給模型)。
- ⇒ 背景任務完成、排隊指令靠這條**無聲驅動續跑**:不中斷串流、不等用戶回應。`scheduler/cron` 式無人值守自動化即由此鋪路。

> **對照 V2**:你目前**無**自主續跑引擎(每爆發需新 send)。CC 的 6.1 給了一個極輕量範本:**不需要 task primitive,只需「判定該繼續 → 注入一條 nudge synthetic message」**。這直接回應你 task-primitive-eval 的「自動續跑調度器」缺口 —— CC 證明它可以做得很薄(一個 budget 判定 + 一條 isMeta 訊息),不必先建 durable 任務脊椎。

---

## 7. 跨 session 持久化(關掉再開繼續)

`assistant/sessionHistory.ts` + `QueryEngine.ts`(`recordTranscript` / `flushSessionStorage`):每輪訊息 fire-and-forget 落盤 `{projectDir}/{sessionId}.jsonl`(一行一 entry;subagent 用 `agent-{id}.jsonl`)。`/resume` 從 session 檔重載**整個 Message[]** 再進 `query()`。compact 邊界訊息帶 `tailUuid` 指向未壓縮段尾,壓縮後 resume 也不丟接點。

⚠️ 但(承 cc-source-blueprint §2.2):這是「**重載整段對話從頭跑**」,**不是**「從中斷點 mid-loop 恢復」—— tool 執行中間狀態 / active stream / loop phase 全部遺失。CC 的「持久化」對長運行的意義是「斷線後對話不丟」,不是「執行狀態可續」。

---

## 8. 對照 V2 + 三個值得研究的 CC 設計

| 維度 | Claude Code(互動) | V2(chat real_llm) |
|---|---|---|
| 迴圈 | `while(true)` ReAct,**無轉數上限** | `while-true` TAO,**`max_turns=8` 硬上限** |
| 長運行模型 | 單次無界 run,模型自決何時停 | 多次有界爆發 + 跨輪 rehydration(57.127) |
| Context 管理 | **5 層階梯**(budget / snip / microcompact / collapse / autocompact) | 單層 compaction(≥3 turn 觸發) |
| 自主續跑 | token-budget continuation(opt-in)+ queued-command 注入 | 無(每爆發需新 send) |
| 暫停 / HITL | 行程內 `await` Promise,**不持久化** | durable checkpoint + `/resume` 端點(可治理) |
| 韌性 | fallback model + 6hr 持久重試 + 30s 心跳(ant flag) | adapter 層重試 |
| 任務脊椎 | 隱式(全靠 messages + tool_use 鏈) | task-primitive-eval 標示的缺口 |

**最值得研究的三個 CC 設計**(都直接對應 task-primitive-eval 的三缺口分析):

1. **「無界 + 多層壓縮」取代「有界 + rehydration」** —— CC 證明只要壓縮夠強,單次無界 run 在技術上可行;V2 的 `max_turns=8` 是伺服器治理選擇,不是技術必需。若要放寬,**先補的不是 max_turns 數字,是壓縮階梯**(否則放寬即爆 context)。
2. **合成 `isMeta` user message 自我延續(§6.1)** —— 這是「自動續跑調度器」的最小實作:不需 task primitive,只需「判定該繼續 → 注入一條 nudge」。比你評估的 DB-backed task store 輕得多,可作為續跑缺口的 thin-spike 起點。
3. **暫停 = await Promise 而非狀態機(§5)** —— CC 用最輕的方式做 HITL;V2 的 durable pause 更重但能跨行程。差異來自 SaaS 多租戶需求,**不是 V2 過度設計** —— 反而印證 cc-source-blueprint「durable resume 是 CC 零藍本的純自研區」。

---

## 9. 與既有 CC 分析鏈的關係(三份互補,非重複)

| 文件 | 回答的問題 | 與本文的關係 |
|---|---|---|
| `agent-harness-cc-parity-20260607` | V2 有沒有 CC 的 18 個進階齒輪? | 部件**靜態盤點**;本文補「核心 loop 齒輪轉起來的動態力學」 |
| `cc-source-blueprint-pause-resume-phases-20260608` | CC 是 phase 狀態機嗎?有 durable resume 嗎?(答:都沒有) | **證偽** CC 的兩個假設;本文承接「CC 是 turn loop」這個事實,往下挖「這個 turn loop 為何能跑長」 |
| **本文(cc-long-running-loop-source-analysis)** | 同一個 `while(true)` loop 憑什麼跑數十小時 + 何時停? | 補前兩份未深挖的**長運行力學**:退出信號 / 無 maxTurns / 5 層壓縮 / 7 自癒站點 / retry 常數 / 自主續跑引擎 |

三份行號互相交叉驗證(皆據 `query.ts`,主迴圈 L241-307 一致),可合視為「CC v2.1.88 核心 loop 完整逆向」的三個切面:**有哪些齒輪(parity)· 是什麼形狀(blueprint)· 怎麼轉得久(本文)**。

---

## Modification History (newest-first)
- 2026-06-19: Initial creation — CC v2.1.88 `query.ts` 主迴圈逐段親讀 + 3 Explore agent 周邊深挖 + 助手親自核實關鍵主張/常數。答「為何能長運行」:無 maxTurns 上限(互動模式)+ 5 層壓縮管線(snip/microcompact/collapse/autocompact,~93.5% 觸發)+ 7 個 continue 自癒站點 + 6hr 持久重試/30s 心跳(ant flag)+ 2 自主續跑引擎(token-budget continuation opt-in / queued-command 注入)。答「何時停」:end_turn(唯一退出信號 toolUseBlocks=0)/ maxTurns(SDK only)/ 中斷 / 不可恢復錯誤 + permission 特例(工具層 await 非迴圈停)。接上 cc-parity + cc-source-blueprint 成三份互補鏈;接 task-primitive-eval 三缺口。源碼用 repo 內 untracked 工作副本 `reference/claude-code-source-cdoe/`。
