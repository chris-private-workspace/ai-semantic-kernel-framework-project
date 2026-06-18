# Thin-Spike 評估：顯式 Task Primitive（類 CC TodoWrite）

**Purpose**: 評估「在 chat agent loop 加一個顯式 task primitive（類 Claude Code `TodoWrite`）」的可行性、最小可行形狀、冗餘風險與成本。**這是評估，不是實作 sprint**；產出供決策，不預寫 sprint plan（rolling discipline）。
**Category / Scope**: 範疇 1/2/5/7/12 交界；chat-v2 主流量
**Created**: 2026-06-18
**Last Modified**: 2026-06-18
**Status**: Active（評估快照；非 sprint）
**Grounding**: 3 個 read-only Explore agent 對 `backend/src` + `frontend/src` 的 file:line 勘查（2026-06-18）

> **Modification History**
> - 2026-06-18: Initial — thin-spike 評估（缺口來自 chat-v2 agent-loop 能力 drive-through §3）

---

## 0. 缺口背景（一句話）

chat agent loop 會 plan，但 plan 是**自然語言自由文字**（emergent，無系統提示強制、無結構、無 durable 狀態）。CC 的 `TodoWrite` 提供的是**結構化 + durable + 可更新 + 可視**的待辦狀態：agent 邊做邊把 item 標 `pending → in_progress → completed`，並作為「長 run 中途的再聚焦錨點」與「使用者進度可視窗」。本評估問：在現有架構下加這個 primitive **值不值得、最小形狀為何、會不會撞既有機制**。

來源：`chat-v2-agent-loop-capability-drivethrough-20260618.md` §3「能像 CC 長時間運行嗎」三缺口之一。

---

## 1. 現況（code-grounded，file:line）

### 1.1 既有「規劃 / 任務」相關機制（皆**非** todo-list）

| 機制 | file:line | 做什麼 | 與 TodoWrite 的關係 |
|------|-----------|--------|---------------------|
| 系統提示 | `api/v1/chat/handler.py:147-167`（DEMO_SYSTEM_PROMPT / CHILD_SUBAGENT_SYSTEM_PROMPT）| 純工具使用指示，**無**「先做 plan / 逐步追蹤」指令 | plan 是 emergent 自由文字，無結構 |
| `task_spawn`（Cat 11）| `agent_harness/subagent/tools.py:60-151` + `subagent/dispatcher.py:173-316` | async fork/join 派子代、回單一 `SubagentResult` | **正交**：是 dispatch，不是 list 追蹤；「task」一詞衝突需避名 |
| MessageInbox / `/inject`（Cat 1）| `api/v1/chat/injection_registry.py:69-133` + `orchestrator_loop/loop.py:2115-2131` | between-turns 注入訊息 steer running agent | **相鄰**：可作「中途更新 plan」的入口，但本身非 task manager |
| `DBMessageStore`（Cat 3, 57.127）| `state_mgmt/message_store.py` + `_category_factories.py make_chat_message_store` | run 起始 `load()` 舊訊息、clean end `append()` 新訊息 → 跨 send rehydration | **正交但是關鍵範本**（見 §2）|
| `max_turns=8` | `api/v1/chat/handler.py:710` | 單次 send turn 上限 | 長運行靠多 send + rehydration，非單次無界 |

**確認不存在**（3 個 agent grep 一致）：無 `LoopState.plan` / 無 `metadata["plan"]` 使用 / 無 `tasks:[{id,status}]` / 無 checklist / 無 step tracker / 無跨 turn 任務完成度。→ **非冗餘**（無 AP-6 既有實作衝突），唯一共用點是 `DurableState.metadata` 這個擴展 dict。

### 1.2 狀態持久化的關鍵細節（決定儲存方案）

- `DurableState.metadata: dict[str,Any]`（`_contracts/state.py:65-75`）是現成擴展點，Pattern A 已被 `verification_attempts` / `verification_escalated` / `pending_approval` / `resume_messages` 使用，checkpointer JSONB **逐字 round-trip**（`state_mgmt/checkpointer.py:217-281`）。
- **但 `metadata` 只在 `_emit_state_checkpoint()`（pause 時）寫入**（`orchestrator_loop/loop.py:3587-3685`）。正常多 send 長運行是 clean `end_turn`，**不觸發 pause checkpoint** → Pattern A metadata **對多 send 長運行不足**。
- 跨 send 存活的既有正解是 `DBMessageStore`（57.127）：run 起始 `load()`、clean end `append()`。**task list 要跨 send 必須走同一形狀**。

---

## 2. 核心洞察：為何這裡比「邊際功能」更有價值，以及最大風險

**價值更高（而非邊際）**：CC 單次無界 run 把 plan 留在 context 內即可；本平台長任務**橫跨多次 8-turn send**，free-text plan 只是被當對話 rehydrate 回來，**沒有結構化、durable、可更新的任務狀態**讓 agent 在「新 send / compaction 之後」知道「還剩什麼、哪些已完成」。因此顯式 task primitive 在本架構是**多 send 長運行缺的那根「durable 任務脊椎」**，不是裝飾性 nice-to-have。

**最大風險 = load-bearing 與否（AP-4 Potemkin）**：CC 的 TodoWrite 之所以有效，是模型被訓練/提示去「consult + update」它。本平台得靠 (a) 系統提示指示維護、(b) 每次 run 起始把 list re-inject 當聚焦錨點。若 agent 不可靠地更新 → 退化成死控件（與 verification-ESCALATE 的 real-LLM 非確定性同類）。**這正是 thin spike 的 drive-through 要證的唯一關鍵命題**。

---

## 3. 設計選項矩陣

### 3.1 儲存（task list 存哪）

| 選項 | 機制 | 跨 send 存活？ | 成本 | 評估 |
|------|------|--------------|------|------|
| **A. metadata Pattern A** | `DurableState.metadata["task_list"]` | ❌ 僅 pause checkpoint 時持久化 | 最低（0 migration）| **不足** —— 正常 clean end 多 send 不持久 |
| **B. typed DurableState 欄位** | `DurableState.task_list` + serializer + reducer + deserializer + migration | ⚠️ 同 A，仍 pause-scoped | 高（migration + 4 處）| 型別安全但同樣 pause-scoped，不解多 send |
| **C. DB-backed store + run-start rehydrate（推薦）** | 專用 `session_tasks`（或復用 memory layer）；tool 寫、run 起始注入 | ✅ 鏡像 57.127 messages 形狀 | 中（1 表/store + rehydrate hook）| **架構一致**：clean end 也持久、跨 send rehydrate、與長運行模型對齊 |

→ **推薦 C**：唯一能在「多次 8-turn send」模型下保持 task 狀態連續的形狀。

### 3.2 更新入口（agent 怎麼改 list）

- **主路徑**：新 builtin tool `write_todos`（暫名，**避 `task` 字以免撞 `task_spawn`**），Cat 2，input = 整份 list `[{id,title,status}]`（**replace-whole-list** 語意，同 CC TodoWrite 每次重寫整份）。handler 經 `ExecutionContext`（`tenant_id/user_id/session_id/db`，precedent `tools/memory_tools.py` 寫側）持久化到 §3.1-C store。
- **可選**：`POST /chat/{id}/update-plan`（鏡像 `/inject`）讓**人**中途改 plan —— 屬延伸，不在最小切片。

### 3.3 可視（chat-v2 怎麼顯示）

- 新 wire event `tasks_updated`（Cat 12），6 檔管線（`_contracts/events.py` → `sse.py` → `event_wire_schema.py` 25→26 → codegen map → 重生 TS → `chatStore.ts` mergeEvent），precedent `MessageInjected`(57.101)/`loop_terminated`(57.130)。
- chat-v2 用 Inspector 新 tab 或 turn block 渲染 todo 面板（pending/in_progress/completed）。

### 3.4 維護驅動（agent 為何會用）

- 擴 DEMO_SYSTEM_PROMPT / persona：「多步任務先用 `write_todos` 列 plan、每完成一步就更新狀態」。
- run 起始把 §3.1-C 的 list 注入 prompt（新 section，precedent：skills 的 `## Active Skill` 注入 57.115 / memory layers 注入）。

---

## 4. 推薦的最小垂直切片（thin spike 可做的形狀）

> 一個 vertical slice，目的是**證明 agent 會 load-bearingly 維護它**，不是做完整功能。

| 元件 | 範疇 | 估計檔數 | precedent |
|------|------|---------|-----------|
| `write_todos` builtin tool（ToolSpec + handler）| 2 | +1 新 + 1 改（`tools/__init__.py`）| `read_skill`(57.113) / memory_tools 寫側 |
| `session_tasks` DB store + run-start rehydrate | 3/7 | 1 store + 1 migration + loop run() 注入 hook | `DBMessageStore`(57.127) |
| prompt 注入 + 系統提示 nudge | 5 | 1-2 改（handler/prompt_builder）| skills `## Active Skill`(57.115) |
| `tasks_updated` wire event + chat-v2 todo 面板 | 12 | 6 檔（5 改 + 1 codegen）| `MessageInjected`(57.101) |
| **Drive-through gate**（見 §6）| — | — | 本評估的關鍵 |

規模對標 `skills-system-spike`(57.113，greenfield 小模組 + tool + 主流量 wiring，calib class 0.60)。

---

## 5. 冗餘 / Anti-Pattern 評估

- **AP-6（冗餘抽象）**：與 `task_spawn`（dispatch）正交；與 MessageInbox（steer）正交。唯一共用點 `DurableState.metadata` 已被 §3.1-C（獨立 store）繞開 → 低風險。**命名**必須避 `task`（用 `todo`/`plan`）以免語意撞 subagent task。
- **AP-4（Potemkin）**：最大風險點；必須 drive-through 證 agent 真的更新（§6）。
- **AP-6（與 free-text plan 並存混淆，agent-3 標 MEDIUM）**：提示須要求 agent **用工具當 plan**，而非「prose plan + 工具 list」兩套並存。

---

## 6. Drive-Through Gate（這個 spike 的成敗判準）

thin spike **不以「tool 存在 + 渲染」算成功**。成功 = 真 UI + 真後端 + 真 LLM 跑一個**跨多次 send 的多步任務**，並觀察：

1. agent **主動** `write_todos` 列出 plan（≥3 item）；
2. 隨進度把 item `pending → in_progress → completed`（非一次性寫死）；
3. **跨 send + compaction 後**，agent 仍能從 rehydrated list 知道「還剩什麼」並接著做（這是 vs free-text plan 的關鍵增益）；
4. chat-v2 todo 面板隨之更新，標籤真實、非 fixture。

若 (2)/(3) 不可靠（agent 不更新或忽略 rehydrated list）→ 與 verification-ESCALATE 同類的 real-LLM 非確定性 → 評估降級為「需更強 prompt engineering 或暫不做」。

---

## 7. 誠實判斷 + 成本 + 邊界

**判斷**：**值得做一個 thin spike**（不是直接全做）。理由：(a) 架構上是多 send 長運行缺的 durable 任務脊椎，價值非邊際；(b) 非冗餘（無既有 todo-state）；(c) 管線全是走過的路（tool + wire event + rehydration 各有近期 precedent）；(d) 唯一真風險（load-bearing）正好是 thin spike 的 drive-through 能一次性證偽/證實的。

**成本（粗估，spike 級）**：對標 skills-system-spike(0.60 class)，約 1 個 vertical slice sprint；但**本文件只是評估，是否開 spike 由你決定**。

**Scope 邊界（這個 primitive 即使做了，也 NOT 做）**：
- ❌ 不改 `max_turns`（仍 8）；
- ❌ 不做「一次 send 自動跨多個 8-turn 爆發跑到完成」的調度器（那是另一個獨立缺口 — 見 §8）；
- ❌ 不做 task 依賴圖 / 自動排程；只做「線性 todo list + 狀態」。

→ 即：task primitive **解「結構化 + durable + 可視的任務狀態」**，**不解**「單次無界自主 run」。後者是 §8 的另一缺口，不要混為一談。

---

## 8. 與另兩個缺口的關係（不要混淆）

chat-v2 能力 doc §3 列的三缺口彼此獨立：

1. **顯式 task primitive**（本評估）—— 結構化任務狀態。**最易、價值明確、本文件推薦先做 spike**。
2. **單次 run turn 上限**（`max_turns=8`）—— 放寬需評估治理/成本/失控風險，與 task primitive 正交。
3. **跨爆發自動續跑調度器** —— 「一個 send 自動跑到完成」；最大、最接近「CC 式長 run」、風險最高。task primitive 是它的**前置**（要自動續跑得先有 durable 任務狀態知道「還剩什麼」），但不是同一件事。

→ 建議順序：**先 1（task primitive spike）→ 視結果再評估 3**。1 的 durable 任務脊椎是 3 的基礎。

---

## 9. 參考

- `claudedocs/5-status/chat-v2-agent-loop-capability-drivethrough-20260618.md` §3 —— 三缺口來源
- `claudedocs/1-planning/harness-deepening-proposal-20260610.md` —— harness-deepening roadmap（本評估屬其精神延伸）
- grounding（3 Explore agent，2026-06-18）：
  - 狀態/Cat 7：`_contracts/state.py:54-84` / `state_mgmt/checkpointer.py:94-281` / `reducer.py:69-166` / `orchestrator_loop/loop.py:3587-3685`
  - 工具/wire：`agent_harness/tools/__init__.py:55-120` / `_register_all.py:201-387` / `handler.py:274-400` / `_contracts/events.py` / `sse.py` / `event_wire_schema.py`（25 events）/ `scripts/codegen/generate_event_schemas.py` / `chatStore.ts` mergeEvent
  - 既有機制：`subagent/tools.py:60-151` / `injection_registry.py:69-133` / `message_store.py`(57.127) / `handler.py:147-167,710`
- `04-anti-patterns.md` —— AP-4 / AP-6
- **本評估不預寫 sprint plan**；若決定開 spike，依 `.claude/rules/sprint-workflow.md` 標準流程（plan → checklist → Day-0 三-prong → code → drive-through）。
