# V2 Audit W3-1 — Phase 50.1 Cat 1 Orchestrator + Cat 6 Output Parser + AP-1 Lint

**Audit 日期**: 2026-04-29
**Auditor**: Research Agent (Claude Opus 4.7)
**結論**: ✅ **PASSED — High Confidence. No Anti-Pattern Drift.**

---

## 摘要

| 項目 | 結果 |
|------|------|
| AP-1 反模式（Pipeline 偽裝 Loop） | ✅ **真 `while True` + StopReason driven** |
| AP-8 PromptBuilder 唯一入口 | N/A（52.2 才上）— 但**無偷渡裸組 messages**（grep 0 hits）|
| LoopState reducer pattern | ⚠️ **mutable @dataclass**（非 frozen）— 已標 53.1 補 |
| LoopEvent 發送對齐 17.md | ✅ 7 events emit（LoopStarted / TurnStarted / LLMRequested / LLMResponded / Thinking / ToolCallRequested / ToolCallExecuted / ToolCallFailed / ContextCompacted / LoopCompleted）|
| AP-1 lint 真實性自驗 | ✅ **實測 exit 1**，AST-based 偵測 while-loop 缺失 + tool feedback marker |
| Cat 6 中性化 | ✅ 純 `ChatResponse` 解析，**禁 regex**（明確 docstring 聲明）|
| 50.1 tests pass/fail/skip | **52 PASS / 0 FAIL / 0 SKIP**（0.50s）|
| Real LLM 串接 | ❌ 仍用 MockChatClient — **CARRY-007 已透明標 50.2**|
| 阻塞 Phase 52+? | ❌ **不阻塞** |

---

## Phase A — Plan/Checklist 對齐

### A.1 Plan / Checklist / Retrospective 三檔齊備

- ✅ `phase-50-loop-core/sprint-50-1-plan.md`（475 行；6 user stories；5-day breakdown）
- ✅ `phase-50-loop-core/sprint-50-1-checklist.md`（存在）
- ✅ `agent-harness-execution/phase-50/sprint-50-1/retrospective.md`（含 estimate accuracy / Did well / Improve / 9 CARRY items）

### A.2 Plan 預期交付項 vs 實際 commit

Plan 列 ~12 新建 + ~6 更新檔。實際 commits（git log filtered）:
- `74dd2e4f` plan + checklist + Phase 50 README
- `068d2fdf` Day 1 — OutputParser + classifier + StopReason mapping ✅
- `6f32d9a1` Day 2 — AgentLoop while-true main loop + 4 terminators ✅
- `6962b8d0` Day 3 — events + InMemoryToolRegistry + AP-1 lint ✅
- `7f708456` Day 4 — e2e + tracer coverage + cancellation safety ✅
- `99d8d7ac`/`92c8fd46` Day 4/5 closeout ✅

每個 plan deliverable 對應實際檔案（loop.py / events.py / termination.py / parser.py / classifier.py / types.py / echo_tool.py / check_ap1_pipeline_disguise.py / 4 test files）— **6/6 stories 全交付**。

### A.3 Retrospective 誠實度

- ✅ **CARRY-007 明確標**：「Phase 50.1 e2e demo via real Azure OpenAI（replace MockChatClient）」owner = User，target = Sprint 50.2 Day 4-5
- ✅ **CARRY-009 明確標**：AP-1 lint substring matching is over-approximate；建議 51.x AST refinement
- ✅ Estimate accuracy 透明：actual ~5.4h vs plan 28h = **19%** ratio（與 49.x 13-26% 一致）
- ✅ CARRY-001/002 trivia carryover 已透明列；不藏

**結論**：retrospective **無樂觀 fudge**，真實狀態完整披露。

---

## Phase B — Cat 1 Orchestrator Loop 結構

### B.1 主類位置 + 結構

`backend/src/agent_harness/orchestrator_loop/loop.py:119` — `class AgentLoopImpl(AgentLoop)`

7 collaborator CTOR 注入：`chat_client / output_parser / tool_executor / tool_registry / system_prompt / max_turns / token_budget / tracer / compactor (52.1+)`

### B.2 AP-1 反模式檢查（最關鍵）

| 檢查項 | 結果 | 證據 |
|-------|------|------|
| `while True`（非 `for ... in steps`） | ✅ **真 while** | `loop.py:171` `while True:` |
| 退出條件由 StopReason 驅動 | ✅ 中性 enum | `should_terminate_by_stop_reason(response)` checks `StopReason.END_TURN` |
| Tool result `messages.append(Message(role="tool", ...))` | ✅ **真回注** | `loop.py:357-363` 後 `continue` 回 LLM |
| Max turns 是安全閥還是邏輯主導 | ✅ 安全閥 | 預設 50；只在 `should_terminate_by_turns` 觸發 |
| 有否 hardcoded 步驟列表（plan/classify/execute/verify） | ✅ **無** | 整體無 `steps = [...]` 模式 |

**4 種 termination：** stop_reason / max_turns / token_budget / cancellation —— 全為 pure function 在 `termination.py`。HANDOFF_NOT_IMPLEMENTED 為 Cat 11 stub 占位（50.1 範圍內預期）。

**AP-1 結論：✅ 真 Loop。Zero Pipeline 偽裝。**

### B.3 LoopState reducer pattern

**⚠️ Concern**：`_contracts/state.py:54-85` `TransientState` / `DurableState` / `LoopState` 全是 `@dataclass`（非 `frozen=True`）。
- 當前 50.1 實作中 `messages.append(...)` 直接改變 `messages: list[Message]`（loop.py:311, 357）
- 並非 immutable reducer pattern；無 `apply_event(state, event) -> state'`
- 17.md §1.1 並未明文要求 frozen，但 reducer pattern 是設計意圖

**緩解**：這在 50.1 是預期 — Day 2.2 docstring 寫明「Phase 53.1+ State Mgmt may revisit」。Phase 53.1 Checkpointer 上線時應切換為 reducer。

### B.4 LoopEvent 發送對齐 17.md

emit 序列（讀 loop.py 實際 `yield`）：
- `LoopStarted` (line 169)
- `ContextCompacted` (line 227, 52.1 only)
- `TurnStarted` (line 237)
- `LLMRequested` (line 241)
- `LLMResponded` (line 271, 50.2 canonical)
- `Thinking` (line 277, 50.1 backward compat)
- `ToolCallRequested` (line 320)
- `ToolCallExecuted` / `ToolCallFailed` (line 342/350, 50.2 emit-by-Cat 1 — owner 17.md §4.1 明指 Cat 2)
- `LoopCompleted` (multiple terminators)

**注意**：`ToolCallExecuted`/`ToolCallFailed` 在 17.md §4.1 owner = Cat 2（tools），但 50.2 在 Cat 1 emit。這是 50.2 的 cross-cut 妥協，retrospective.md 未明示但 loop.py docstring `Day 2.4` 註明「Cat 1+2+6 cooperate」。**輕微 owner 漂移**，建議 51.1 範疇 2 完整實作時遷回 Cat 2。

---

## Phase C — Cat 6 Output Parser

### C.1 主類位置

`backend/src/agent_harness/output_parser/parser.py:56` — `class OutputParserImpl(OutputParser)`

### C.2 中性化邏輯

✅ **完美中性**：
- `parse(response: ChatResponse) -> ParsedOutput` 純轉換
- `tool_calls = list(response.tool_calls or [])` —— 直接讀 adapter 已轉換的中性 `ToolCall`
- `_extract_text` 處理 str 或 `list[ContentBlock]`（中性 type）
- **NO regex / 文本解析**（docstring 明確聲明：`Pure transformation: NO regex/free-text parsing`）

### C.3 多 provider 統一

- ChatResponse 已由 adapter 中性化（W2-1 已驗證）
- Parser 不知道 provider，純消費 ChatResponse
- 為 Anthropic / 未來 provider 預留（thinking blocks / streaming partial 留 50.2+）

### C.4 17.md §1.1 對齐

- `ParsedOutput` 在 `agent_harness/output_parser/types.py` — single source ✅
- 不重複定義 ChatResponse / Message / ToolCall（_contracts/ 唯一）
- `OutputType` enum（FINAL / TOOL_USE / HANDOFF）在 types.py

---

## Phase D — AP-1 Lint Script

### D.1 位置 + 邏輯

`scripts/lint/check_ap1_pipeline_disguise.py` (155 行)

### D.2 偵測技術

- **AST-based**（非純 regex）：`ast.parse` → walk `ast.ClassDef` → 找 `*Impl` / `*Loop`（排除 `AgentLoop`/`Loop` ABC）→ 在其 `async def run` 中 `ast.walk` 找 `ast.While`
- 加上 `Message(role="tool"` substring marker 檢查 tool feedback

### D.3 自驗 fake violation：✅ 真能 catch

我寫了 `/tmp/ap1_test/agent_harness/orchestrator_loop/fake_loop.py`（`FakePipelineLoop` 用 `for step in [step1, step2, step3]`，無 tool feedback）：

```
AP-1 lint FAILED: 2 violation(s) in 1 file(s) scanned ...
:4: AP-1 violation: FakePipelineLoop.run() must contain a `while` loop
:3: AP-1 violation: FakePipelineLoop does not feed tool results back as Message(role="tool", ...)
RealExitCode=1
```

**真實 exit 1，CI 會 fail**。AP-1 lint **不是 fake green**。

**已知限制**（retrospective CARRY-009）：substring 匹配 `Message(role="tool"` 在 comment 中可繞過。Production code 中此 marker 必和 call 一起用，故 50.1 能容忍。Phase 51.x 應升級為 AST call detection。

---

## Phase E — 跨範疇 + 主流量 trace

### E.1 _contracts/ import

✅ Loop 完整使用：
```python
from agent_harness._contracts import (
    ChatRequest, ChatResponse, ContentBlock, ContextCompacted, DurableState,
    LLMRequested, LLMResponded, LoopEvent, LoopState, LoopStarted,
    LoopCompleted, Message, SpanCategory, StateVersion, Thinking,
    ToolCallExecuted, ToolCallFailed, ToolCallRequested, TraceContext,
    TransientState, TurnStarted,
)
```

### E.2 ChatClient ABC 注入

✅ **DI 而非 hardcoded**：
```python
def __init__(self, *, chat_client: ChatClient, ...):
```
測試用 MockChatClient；production 將注入 AzureOpenAIAdapter（W2-1 已驗收）。

### E.3 PromptBuilder 唯一入口（AP-8）

50.1 範圍**無 PromptBuilder**（52.2 才上）。但偷渡裸組檢查：
- `grep "messages = [{'role'"` agent_harness/ → **0 hits**
- `messages` 在 loop.py 內以 typed `Message(role=..., content=...)` 構造
- ✅ AP-8 無偷渡

### E.4 Real LLM 串接

❌ **仍用 MockChatClient** — 但這是 50.1 預期：
- Plan 明確：「不接 API（API 整合是 50.2 工作；50.1 純粹 backend agent_harness/ 內單元 + 整合 test）」
- CARRY-007 透明標 Sprint 50.2 Day 4-5 由 user 換真 Azure OpenAI demo

### E.5 從外部可呼叫（AP-2）

- `AgentLoopImpl.run()` async generator 簽名穩定
- 50.2 已被 `runtime/workers/agent_loop_worker.py` + `api/v1/chat/` SSE consume（git log 確認）
- ✅ **無 orphan**：50.1 寫的 loop 50.2 立刻被用

---

## Phase F — Pytest 驗證

### F.1 結果

```
tests/unit/agent_harness/orchestrator_loop/      8 PASS
tests/unit/agent_harness/orchestrator_loop/test_termination.py  10 PASS
tests/unit/agent_harness/output_parser/test_classifier.py        3 PASS
tests/unit/agent_harness/output_parser/test_parser.py            5 PASS
tests/unit/agent_harness/output_parser/test_stop_reason_mapping.py 13 PASS
tests/integration/orchestrator_loop/test_cancellation_safety.py  3 PASS
tests/integration/orchestrator_loop/test_e2e_echo.py             2 PASS
tests/integration/orchestrator_loop/test_observability_coverage.py 3 PASS
tests/integration/orchestrator_loop/test_tool_feedback.py        2 PASS
tests/unit/scripts/lint/test_ap1_pipeline_disguise.py            4 PASS

TOTAL: 52 PASS / 0 FAIL / 0 SKIP / 0.50s
```

retrospective 自報「210 PASS / 0 SKIPPED」全 sprint cumulative — 此 audit 抽 50.1 子集 = **52** 全綠。

### F.2 強度抽樣

- `test_e2e_echo.py` (2 tests) — 真實 inject MockChatClient 2-turn sequence + InMemoryToolRegistry + echo_tool；驗證 event sequence + final message + turn_count；非 trivial smoke
- `test_cancellation_safety.py` — 3 cancel scenarios（slow tool / mid-turn / before first turn）
- `test_observability_coverage.py` — RecordingTracer ABC + emit-point assertion
- `test_tool_feedback.py` — Message(role="tool") append 驗證 + tool_call_id correlation
- `test_ap1_pipeline_disguise.py` — pos/neg/variant 4 case（lint script self-test）

**強度判定：✅ Real, not trivial**。所有測試異步真跑，斷言 sequence/content/role correlation。

---

## 結論

| 維度 | 評級 |
|------|------|
| AP-1 反模式 | ✅ Pass — 真 while-loop，無 Pipeline 偽裝 |
| AP-8 PromptBuilder（如有） | ✅ Pass — 無偷渡裸組（PromptBuilder 留 52.2） |
| LoopState reducer | ⚠️ Concern — mutable，53.1 補 |
| LoopEvent 發送 | ✅ Pass — 10+ events 符合 17.md（小 owner 漂移：ToolCallExecuted） |
| AP-1 lint 真實性 | ✅ Pass — 實測 catch fake violation，AST-based |
| Cat 6 中性化 | ✅ Pass — 0 regex，純 ChatResponse 消費 |
| Tests 強度 | ✅ Pass — 52 PASS / 0 SKIP，e2e + cancellation + observability |
| 主流量可追蹤（AP-2） | ✅ Pass — 50.2 已連 SSE，無 orphan |

---

## 修補建議

### P1（非阻塞，建議 Phase 53.1 處理）
1. **LoopState 切換為 frozen + reducer pattern**（53.1 Checkpointer 上線時連動）
2. **ToolCallExecuted / ToolCallFailed owner 遷回 Cat 2**（51.1 範疇 2 完整實作時）

### P2（建議 Phase 51.x backlog）
3. **AP-1 lint 升級 AST call detection**（CARRY-009 已標）— 替換當前 substring marker 為 `ast.Call(func=Name('Message'), keywords=...)` 精準檢測

### P3（非 50.1 責任）
4. **Real LLM e2e demo**（CARRY-007）—— 50.2 Day 4-5 用戶 owner

---

## 不正常開發 / 偏離 findings

**1 件輕微 owner 漂移**：
- `ToolCallExecuted` / `ToolCallFailed` 在 17.md §4.1 owner = Cat 2，但 50.2 由 Cat 1（loop.py）emit
- 在 50.1 範圍**不算違規**（Cat 2 InMemoryToolRegistry 是 stub），但 retrospective.md 未明示此 owner cross-cut
- 建議：51.1 範疇 2 完整實作時遷回，或在 17.md 明文允許 Cat 1 為臨時 emitter

**無 Potemkin Feature**。所有交付項有實邏輯 + 真測試 + 從 50.2 main flow 可被呼叫。
**無 undisclosed scope change**。所有 carryover 在 retrospective CARRY-001..009 透明列。
**無偷渡 verification**（範疇 10 確實未做；50.1 不在範圍）。

---

## 阻塞 Phase 52+ 啟動?

✅ **不阻塞**。

理由：
1. AP-1 是 V2 最關鍵反模式，已守住 + lint 強制 + 自驗有效
2. Cat 1 + Cat 6 主迴圈跑通，已被 Sprint 50.2 SSE 路徑成功接入（git log 證明）
3. 52.1 Compactor 已部分注入（loop.py compactor 參數已預留）
4. LoopState mutable 是預期 trade-off（reducer 留 53.1）
5. 52 tests 全綠，無 carryover blocker
