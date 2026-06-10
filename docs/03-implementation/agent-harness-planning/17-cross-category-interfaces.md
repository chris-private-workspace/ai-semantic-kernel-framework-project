# 17 — 跨範疇接口附錄（Single-Source Registry）

**建立日期**：2026-04-28
**版本**：V2.0
**狀態**：Authoritative reference — 任何 V2 規劃文件都必須遵守

> **本文件是 V2 的「介面權威表」**。當兩份規劃文件對同一介面（dataclass / ABC / tool / event）有不同定義時，**本文件勝出**。所有重複定義必須改為 import / 引用，不可複製。

---

## 為什麼需要這份附錄

V2 review 發現 7 條跨範疇 / 跨文件重複定義：

| 議題 | 衝突點 |
|------|--------|
| `ToolSpec` | 範疇 2 與原則 2 都定義 |
| `ChatClient` ABC | 範疇 6 引用、原則 2 定義 |
| `memory_search` 工具 | 範疇 2 與範疇 3 重複 |
| `task_spawn` 工具 | 範疇 2 與範疇 11 重複 |
| `Tripwire` 概念 | 範疇 8 / 9 邊界模糊 |
| `Subagent delegation` 接口 | 範疇 4 / 11 跨範疇呼叫未明 |
| `HITL` 機制 | 散落在範疇 2 / 7 / 8 / 9 |

如果這些介面在 Sprint 中各自實作，會導致：
- 同一概念兩個實作（Anti-Pattern 6 — Hybrid 橋接層債務）
- 修改一處遺漏另一處（V1 教訓 #1）
- 範疇間整合時 type mismatch 大量浮現

**規則**：每個跨範疇介面**只能定義一次**。其他文件**只能引用**，不能重新定義。

---

## 第 1 部分：核心資料結構（dataclass / TypedDict）

### 1.1 single-source 表

| 介面名稱 | Owner 文件 | Owner 範疇 / 章節 | 說明 |
|---------|----------|------------------|------|
| `ChatRequest` | `10-server-side-philosophy.md` | 原則 2 §`ChatClient` ABC | LLM 呼叫請求；中性化欄位 |
| `ChatResponse` | `10-server-side-philosophy.md` | 原則 2 §`ChatClient` ABC | LLM 呼叫回應；含 `stop_reason` enum |
| `Message` | `10-server-side-philosophy.md` | 原則 2 §`ChatClient` ABC | role / content / tool_calls / **metadata**（**52.1 Day 2 擴充**：`metadata: dict[str, Any] = {}` 用於 Cat 4 Compactor 標記 `hitl=True` / `compacted_summary=True` 等 non-LLM-facing flag；adapter MUST NOT serialise into provider requests） |
| `ContentBlock` | `10-server-side-philosophy.md` | 原則 2 §`ChatClient` ABC | text / image / tool_use / tool_result |
| `ToolSpec` | `01-eleven-categories-spec.md` | 範疇 2 | 工具定義（含 annotations / concurrency_policy / **hitl_policy / risk_level (51.1)** / version） |
| `ToolCall` | `01-eleven-categories-spec.md` | 範疇 2 | 單次工具呼叫 |
| `ToolResult` | `01-eleven-categories-spec.md` | 範疇 2 | 工具回傳（含 `result_content_types`） |
| `ToolAnnotations` | `01-eleven-categories-spec.md` | 範疇 2 | MCP 4 hints（readOnly / destructive / idempotent / openWorld） |
| `ToolHITLPolicy` | `01-eleven-categories-spec.md` | 範疇 2 | Per-tool HITL behavior enum（`AUTO` / `ASK_ONCE` / `ALWAYS_ASK`）— **新增 51.1**；distinct from per-tenant `HITLPolicy` (in `_contracts.hitl`) |
| `ExecutionContext` | `01-eleven-categories-spec.md` | 範疇 2 | Per-call invocation context dataclass（`tenant_id` / `session_id` / `explicit_approval`）— **新增 51.1**（owned by `_contracts/tools.py` so `ToolExecutor` ABC can reference without import cycle）；consumed by `PermissionChecker.check()` |
| `ConcurrencyPolicy` | `01-eleven-categories-spec.md` | 範疇 2 | sequential / read_only_parallel / all_parallel |
| `LoopState` | `01-eleven-categories-spec.md` | 範疇 7 | 中央 state；拆 transient/durable |
| `TransientState` | `01-eleven-categories-spec.md` | 範疇 7 | in-memory 短期 state |
| `DurableState` | `01-eleven-categories-spec.md` | 範疇 7 | DB 持久 state |
| `LoopEvent` | `01-eleven-categories-spec.md` | 範疇 1 | Loop 事件流（`AgentLoop.events()` yield） |
| `StopReason` | `10-server-side-philosophy.md` | 原則 2 enum 中性化表 | 替代 per-provider 字串 |
| `MemoryHint` | `01-eleven-categories-spec.md` | 範疇 3 | 「線索→驗證」資料結構（**51.2 Day 1** 擴 5 欄位：`time_scale` / `confidence` / `last_verified_at` / `verify_before_use` / `source_tool_call_id`） |
| `PromptArtifact` | `01-eleven-categories-spec.md` | 範疇 5 | PromptBuilder 產出（messages / cache_breakpoints / estimated_input_tokens / **layer_metadata** keys per 52.2 Day 1.6：`memory_layers_used: list[str]` / `position_strategy: str` / `cache_sections: list[str]` / `trace_id: str`（W3-2 carryover；前端 SSE event 串連日誌用））|
| `PromptSections` | `01-eleven-categories-spec.md` | 範疇 5 | DefaultPromptBuilder 內部 dataclass；5 欄位（`system: Message` / `tools: list[ToolSpec]` / `memory_layers: dict[str, list[MemoryHint]]` / `conversation: list[Message]` / `user_message: Message \| None`）— **52.2 Day 1.3 新增**；caller 預先按 time_scale priority 排序 memory_layers 後傳入 PositionStrategy.arrange() |
| `CacheBreakpoint` | `01-eleven-categories-spec.md` | 範疇 5（物理）+ 範疇 4（logical metadata） | Provider cache_control 標記。**51.1**：物理欄位 `position` / `ttl_seconds` / `breakpoint_type`（Cat 5 own）。**52.1 Day 1 擴充**：logical metadata 欄位 `section_id` / `content_hash` / `cache_control`（Cat 4 own，全 default=None 維持 51.1 callers 兼容）|
| `CompactionStrategy` | `01-eleven-categories-spec.md` | 範疇 4 | Compactor 策略 enum（STRUCTURAL / SEMANTIC / HYBRID）— **52.1 Day 1 新增** |
| `CompactionResult` | `01-eleven-categories-spec.md` | 範疇 4 | `Compactor.compact_if_needed()` 回傳；7 欄位（triggered / strategy_used / tokens_before / tokens_after / messages_compacted / duration_ms / compacted_state）— **52.1 Day 1 新增** |
| `CachePolicy` | `01-eleven-categories-spec.md` | 範疇 4 | `PromptCacheManager.get_cache_breakpoints()` 輸入；5 個 cache_* boolean + ttl_seconds + invalidate_on triggers — **52.1 Day 1 新增** |
| `VerificationResult` | `01-eleven-categories-spec.md` | 範疇 10 | Verifier 回傳（**Sprint 57.82** 加 judge token 欄位 `input_tokens` / `output_tokens` / `model`，default 0/None；僅 LLMJudgeVerifier 填，供 **in-loop Cat 10 gate（Sprint 57.98，前為 correction-loop wrapper）** 冒泡至 LoopCompleted 入帳 cost-ledger/quota）|
| `SubagentBudget` | `01-eleven-categories-spec.md` | 範疇 11 | token / duration / concurrency cap |
| `SubagentResult` | `01-eleven-categories-spec.md` | 範疇 11 | Subagent 回傳（含強制 ≤ N token 摘要） |
| `TraceContext` | `01-eleven-categories-spec.md` | **範疇 12 (Observability)** | trace_id / span_id / baggage |
| `MetricEvent` | `01-eleven-categories-spec.md` | 範疇 12 | latency / token / cost 三軸 metric |
| `ApprovalRequest` | `01-eleven-categories-spec.md` | §HITL 中央化 | HITL 統一請求結構 |
| `ApprovalDecision` | `01-eleven-categories-spec.md` | §HITL 中央化 | approve / reject / escalate |

### 1.2 引用方式（範例）

```python
# ✅ 正確：範疇 6 (output_parser) 引用 ChatResponse
from agent_harness._contracts import ChatResponse  # 由原則 2 single-source

class OutputParser(ABC):
    @abstractmethod
    def parse(self, response: ChatResponse) -> ParsedOutput: ...
```

```python
# ❌ 錯誤：範疇 6 重新定義 ChatResponse
@dataclass
class ChatResponse:  # ← 違反 single-source rule
    ...
```

### 1.3 實作位置（程式碼層）

V2 backend 中：

```
backend/src/agent_harness/_contracts/
├── __init__.py            ← 統一 re-export
├── chat.py                ← ChatRequest/Response/Message/ContentBlock/StopReason/CacheBreakpoint（51.1 物理 + 52.1 logical）
├── tools.py               ← ToolSpec/ToolCall/ToolResult/ToolAnnotations
├── state.py               ← LoopState/TransientState/DurableState
├── events.py              ← LoopEvent
├── memory.py              ← MemoryHint
├── prompt.py              ← PromptArtifact（CacheBreakpoint re-export from chat.py）/ PromptSections re-export from prompt_builder.strategies._abc（**52.2 Day 1.7**）
├── compaction.py          ← CompactionStrategy/CompactionResult（**52.1 Day 1**）
├── cache.py               ← CachePolicy（**52.1 Day 1**）
├── verification.py        ← VerificationResult
├── subagent.py            ← SubagentBudget/SubagentResult
├── observability.py       ← TraceContext/MetricEvent
└── hitl.py                ← ApprovalRequest/ApprovalDecision
```

`_contracts/` 是**11 範疇 + 範疇 12 共用的型別包**。任何 `agent_harness/` 子目錄都從這裡 import，**不在自己內部 redefine**。

---

## 第 2 部分：核心 ABC（介面）

### 2.1 single-source 表

| ABC 名稱 | Owner 文件 | Owner 章節 | 主要方法 |
|---------|----------|----------|---------|
| `ChatClient` | `10-server-side-philosophy.md` | 原則 2 | `chat()` / `stream()` / `count_tokens()` / `get_pricing()` / `supports_feature()` / `model_info()` |
| `ModelProfile` | `24-multi-model-profile-design.md` | adapters/_base | `@dataclass(frozen=True) {action: ChatClient, cheap: ChatClient}` — Sprint 57.97. A provider-neutral **value object** (NOT an ABC) pairing pre-built `ChatClient`s by role so phases run on different tiers (the ABC fixes model at construction — no per-call `model=`). **WRAPS `ChatClient`; does NOT modify it.** Built at `build_real_llm_handler` (`adapters/azure_openai/profile.py:build_azure_model_profile`); this sprint routes only the verification (Cat 10 llm_judge) → `cheap`, loop/compaction → `action`. Unset cheap env → `cheap is action` (byte-identical). See `CHANGE-064`. |
| `AgentLoop` | `01-eleven-categories-spec.md` | 範疇 1 | `run() -> AsyncIterator[LoopEvent]` |
| `ToolRegistry` | `01-eleven-categories-spec.md` | 範疇 2 | `register()` / `get()` / `list()` |
| `ToolExecutor` | `01-eleven-categories-spec.md` | 範疇 2 | `execute()` / `execute_batch()` |
| `MemoryLayer` | `01-eleven-categories-spec.md` | 範疇 3 | `read()` / `write()` / `evict()` / `resolve()`（**51.2 Day 1** 簽名變更：`write(ttl=...)` → `write(time_scale=..., confidence=...)`；`read()` 加 `time_scales` 軸；新增 `MemoryTimeScale` enum helper） |
| `Compactor` | `01-eleven-categories-spec.md` | 範疇 4 | `should_compact(state) -> bool` / `compact_if_needed(state) -> CompactionResult`（async）— **52.1 Day 1 簽名升級**（49.1 stub `compact() -> LoopState` 已淘汰） |
| `ObservationMasker` | `01-eleven-categories-spec.md` | 範疇 4 | `mask_old_results(messages, *, keep_recent=5) -> list[Message]` — **52.1 Day 1 新增** |
| `JITRetrieval` | `01-eleven-categories-spec.md` | 範疇 4 | `resolve(pointer, *, tenant_id) -> str`（async）— **52.1 Day 1 新增**（multi-tenant safety: tenant_id 強制） |
| `TokenCounter` | `01-eleven-categories-spec.md` | 範疇 4 | `count(messages, tools) -> int` / `accuracy() -> Literal["exact", "approximate"]`（**52.1 Day 1** 加 accuracy method） |
| `PromptCacheManager` | `01-eleven-categories-spec.md` | 範疇 4 | `get_cache_breakpoints(*, tenant_id, policy, trace_context=None) -> list[CacheBreakpoint]`（async） / `invalidate(*, tenant_id, reason, trace_context=None) -> None`（async）— **52.1 Day 1 簽名升級**（49.1 stub `plan_breakpoints(messages, provider_supports_caching)` 已淘汰；multi-tenant safety: tenant_id 強制隔離）+ **52.2 Day 2.3 W3-2 audit carryover**：加 `trace_context: TraceContext \| None = None` default kwarg（cross-cutting trace propagation；既有 51.1/52.1 callers default-arg 兼容） |
| `PromptBuilder` | `01-eleven-categories-spec.md` | 範疇 5 | `build(*, state, tenant_id, user_id, tools, cache_policy, position_strategy, trace_context) -> PromptArtifact`（async）— **52.2 Day 1.2 簽名升級**（49.1 stub 4 參數 → 7 參數；加 `tools: list[ToolSpec] \| None`（Loop 從 tool registry passthrough）+ `cache_policy: CachePolicy \| None`（None 用 builder default）+ `position_strategy: PositionStrategy \| None`（None 用 builder default = LostInMiddleStrategy）+ tenant_id 強制必傳 per multi-tenant tri-rule + trace_context propagation per W3-2 audit carryover）|
| `PositionStrategy` | `01-eleven-categories-spec.md` | 範疇 5 | `arrange(sections: PromptSections) -> list[Message]` — pure stateless rearrangement，no IO；3 concrete impls per 52.2 Day 1.4：`NaiveStrategy`（[system, memory, conv, user]）/ `LostInMiddleStrategy`（**default**；user message 同時錨點首尾）/ `ToolsAtEndStrategy`（messages + tools_position_hint marker；adapter 層 detach）— **52.2 Day 1.3 新增** |
| `OutputParser` | `01-eleven-categories-spec.md` | 範疇 6 | `parse(response) -> ParsedOutput` |
| `Checkpointer` | `01-eleven-categories-spec.md` | 範疇 7 | `save()` / `load()` / `time_travel()` |
| `Reducer` | `01-eleven-categories-spec.md` | 範疇 7 | `merge(state, update) -> state` |
| `ErrorPolicy` | `01-eleven-categories-spec.md` | 範疇 8 | `should_retry()` / `classify()` |
| `CircuitBreaker` | `01-eleven-categories-spec.md` | 範疇 8 | `record()` / `is_open()` |
| `Guardrail` | `01-eleven-categories-spec.md` | 範疇 9 | `check()` |
| `Tripwire` | `01-eleven-categories-spec.md` | 範疇 9（**non-範疇 8**）| `register()` / `trigger()` |
| `Verifier` | `01-eleven-categories-spec.md` | 範疇 10 | `verify() -> VerificationResult` |
| `SubagentDispatcher` | `01-eleven-categories-spec.md` | 範疇 11 | `spawn()` / `handoff()` |
| `ChildLoopFactory` | `_contracts/subagent.py` | 範疇 11 | `Callable[[SubagentBudget], AgentLoop]` — Sprint 57.94 FORK real child loop. **Composition detail, NOT a `SubagentDispatcher` ABC method** (ABC unchanged); built at `build_real_llm_handler`, injected → `ForkExecutor`. Cat 11→Cat 1 ref is TYPE_CHECKING-only. See `20-subagent-child-loop-design.md`. |
| `SubagentEventEmitter` | `subagent/dispatcher.py` | 範疇 11 → 範疇 12 | `Callable[[LoopEvent], Awaitable[None]]` — Sprint 57.12 dispatcher slot; **Sprint 57.95 wired on the chat path** (`make_chat_subagent_dispatcher` ← a router-owned buffer drained by `_stream_loop_events`) so `SubagentSpawned`/`SubagentCompleted` reach the SSE stream (node-level relay; Inspector Tree). **Sprint 57.96 (Scope B)**: the same emitter (passed to `ForkExecutor` as `_emit_safely`) also forwards the child loop's TAO subset wrapped in `SubagentChildEvent` → the Tree node expands to the child's per-turn loop. Composition detail, ABC + type unchanged. See `CHANGE-062` / `CHANGE-063`. |
| `Tracer` | `01-eleven-categories-spec.md` | **範疇 12** | `start_span()` / `record_metric()` |
| `HITLManager` | `01-eleven-categories-spec.md` | §HITL 中央化 | `request_approval()` / `wait()` / `decide()` |

### 2.2 ABC 程式碼位置

```
backend/src/agent_harness/{範疇}/_abc.py
```

每個範疇的 `_abc.py` 只 own 該範疇的 ABC。**禁止**在某範疇 `_abc.py` 定義跨範疇 ABC。

---

## 第 3 部分：跨範疇工具註冊表

> 這些工具是 LLM 可呼叫的 tool，**Owner 範疇**負責提供實作，**Caller 範疇**只透過 Registry 呼叫。

### 3.1 工具註冊權威表

| 工具名稱 | Owner 範疇 | 描述 | concurrency / hitl / risk | 可被誰呼叫 |
|---------|----------|------|--------------------------|----------|
| `memory_search` | **範疇 3 (Memory)** | 跨 5 層搜尋記憶 + 多軸 `time_scales`（short_term / long_term / semantic）；**51.2 Day 4** ships real handler 經 `make_memory_search_handler(retrieval)` 注入；51.1 placeholder fallback 保留為 dev-mode safety net | RO_PARALLEL / AUTO / LOW | LLM via 範疇 2 Registry |
| `memory_write` | **範疇 3 (Memory)** | 寫入指定 scope + `time_scale` + `confidence`；scope=system 拒絕（read-only at runtime）；**51.2 Day 4** ships real handler 經 `make_memory_write_handler(layers)` 注入 | SEQUENTIAL / AUTO / LOW | LLM via 範疇 2 Registry |
| `memory_extract` | **範疇 3 (Memory)** | 內部 worker（`MemoryExtractor.extract_session_to_user`）；**51.2 Day 3** ships 手動觸發版（非 ToolSpec exposed）；自動觸發 Celery / Redis queue → CARRY-027（Phase 53.1） | N/A（internal）| MemoryExtractor caller |
| `task_spawn` | **範疇 11 (Subagent)** | Fork / Teammate subagent（54.2+；**57.64 Day 2** wired on chat path 經 `make_task_spawn_tool(dispatcher, parent_session_id)`；`SubagentResult` 由 handler 內部 merge — **無獨立 `SubagentResultReducer`**） | SEQUENTIAL / AUTO / MEDIUM | LLM via 範疇 2 Registry |
| `handoff` | **範疇 11 (Subagent)** | Handoff 控制權（54.2+） | TBD | LLM via 範疇 2 Registry |
| `request_approval` | **§HITL 中央化** | 觸發人工審批（**51.1 Day 4 ships placeholder**：handler 返回 `pending_approval_id` JSON；ApprovalManager wires 53.3） | SEQUENTIAL / **ALWAYS_ASK** / MEDIUM | LLM via 範疇 2 Registry |
| `verify` | **範疇 10 (Verification)** | 觸發 verifier 檢查當前 output（54.1+） | TBD | LLM via 範疇 2 Registry |
| `web_search` | **範疇 2 (Tools)** | 內建工具：Bing Search v7 via httpx（**51.1 Day 4**；CARRY-024 real-key smoke） | RO_PARALLEL / AUTO / LOW | LLM |
| `python_sandbox` | **範疇 2 (Tools)** | 內建工具：subprocess + tempdir cwd + POSIX rlimit（**51.1 Day 3**；Docker backend 留 CARRY-022） | RO_PARALLEL / AUTO / MEDIUM | LLM |
| `echo_tool` | **範疇 2 (Tools)** | 50.1 bring-up built-in（仍 active in 51.1；可能在 52.x deprecate） | RO_PARALLEL / AUTO / LOW | LLM |

#### 業務領域工具（Sprint 51.0 mock 階段；Phase 55 替換為真實 enterprise integration）

> Sprint 51.0 命名約定：所有業務 stub 加 `mock_` prefix；Phase 55 真實 integration 上線時統一 mass rename 移除 prefix。
> ~~hitl_policy 與 risk_level 為 Sprint 51.0 暫編碼於 `ToolSpec.tags`~~（CARRY-021 已於 **Sprint 51.1 Day 1** 處理：`ToolSpec` 加入 first-class `hitl_policy: ToolHITLPolicy` + `risk_level: RiskLevel` field；Day 5 移除 18 業務 stub 的 tags-encoded workaround）。

| 工具名稱 | Owner | 描述 | concurrency / hitl / risk |
|---------|------|------|--------------------------|
| `mock_patrol_check_servers` | **`business_domain/patrol/`** (08b §Domain 1) | 對 server scope 跑健康檢查 | parallel / auto / low |
| `mock_patrol_get_results` | 同上 | 取單一 PatrolResult | parallel / auto / low |
| `mock_patrol_schedule` | 同上 | Cron + scope 排程定期巡檢 | sequential / ask_once / medium |
| `mock_patrol_cancel` | 同上 | 取消已排程巡檢 | sequential / ask_once / medium |
| `mock_correlation_analyze` | **`business_domain/correlation/`** (08b §Domain 2) | 解析 alert 關聯鏈（同 server ±5min） | parallel / auto / low |
| `mock_correlation_find_root_cause` | 同上 | Incident → 排序 RCA candidates | sequential / auto / low |
| `mock_correlation_get_related` | 同上 | Alert → 關聯 alert（depth 1-3） | parallel / auto / low |
| `mock_rootcause_diagnose` | **`business_domain/rootcause/`** (08b §Domain 3) | 取 incident 最高信心 RCA finding | sequential / auto / low |
| `mock_rootcause_suggest_fix` | 同上 | 生成 mock fix proposal | sequential / auto / low |
| `mock_rootcause_apply_fix` | 同上 | **HIGH RISK**：套用 fix（dry_run default true） | sequential / **always_ask** / **high** |
| `mock_audit_query_logs` | **`business_domain/audit_domain/`** (08b §Domain 4) | 過濾查 audit logs | parallel / auto / low |
| `mock_audit_generate_report` | 同上 | Template + params → 報表 URL placeholder | sequential / auto / medium |
| `mock_audit_flag_anomaly` | 同上 | 標記 audit record 為異常 | sequential / ask_once / medium |
| `mock_incident_create` | **`business_domain/incident/`** (08b §Domain 5) | 建立 incident（title/severity/alert_ids） | sequential / ask_once / medium |
| `mock_incident_update_status` | 同上 | 更新 incident.status | sequential / ask_once / medium |
| `mock_incident_close` | 同上 | **HIGH RISK**：關閉 incident（resolution） | sequential / **always_ask** / **high** |
| `mock_incident_get` | 同上 | 取單一 incident | parallel / auto / low |
| `mock_incident_list` | 同上 | 過濾列出 incidents | parallel / auto / low |

### 3.2 規則

- **Owner 範疇** 是工具的實作來源；**Caller 範疇** 只能 import owner 提供的 `register_*()` helper，**不可重新實作同名工具**
- 範疇 2（Tools）只 own **內建通用工具**（search / sandbox / file ops 等），不 own 跨範疇工具
- 業務領域工具（patrol / correlation / rootcause / audit / incident）見 **`08b-business-tools-spec.md`**（V2 將此拆出 spec，避免混入通用 spec）

### 3.3 工具註冊範例

```python
# 範疇 3 註冊 memory_search 到 Registry（範疇 2 own）
# backend/src/agent_harness/memory/tools.py
from agent_harness._contracts import ToolSpec, ToolAnnotations, ConcurrencyPolicy
from agent_harness.tools import ToolRegistry  # 範疇 2 ABC

def register_memory_tools(registry: ToolRegistry) -> None:
    registry.register(ToolSpec(
        name="memory_search",
        annotations=ToolAnnotations(read_only=True, idempotent=True),
        concurrency_policy=ConcurrencyPolicy.READ_ONLY_PARALLEL,
        version="1.0",
        ...
    ))
```

---

## 第 4 部分：跨範疇 Events

### 4.1 LoopEvent 統一型別表

`LoopEvent` 由**範疇 1（Orchestrator Loop）**從 `_contracts/events.py` 定義；其他範疇**只 emit 子類**，不重新定義 base class。

| Event 子類 | Emit 範疇 | 觸發時機 |
|-----------|----------|---------|
| `LoopStarted` | 範疇 1 | Loop run 開始 |
| `TurnStarted` | 範疇 1 | Loop 每個 TAO 迭代開頭（Sprint 50.2 加） |
| `LLMRequested` | 範疇 1 | LLM call 發出前（含 model 名 + best-effort tokens_in；Sprint 50.2 加） |
| `LLMResponded` | 範疇 1 | LLM 回應收到（canonical SSE `llm_response` 載體：content + tool_calls + thinking；Sprint 50.2 加。Sprint 57.2 加 `provider` / `model` / `input_tokens` / `output_tokens` per-call metadata；**Sprint 57.65 A-2 Tier2 加 `cached_input_tokens`**（neutral `TokenUsage.cached_input_tokens` 來源，prompt-cache observability，LoopMetricsAccumulator 逐 event 累加）） |
| `Thinking` | 範疇 1 | 模型 thinking text（50.1 backward-compat；50.2+ SSE 不發） |
| `ToolCallRequested` | 範疇 6 | output parser 解析出 tool_calls |
| `ToolCallExecuted` | 範疇 2 | Tool executor 完成 |
| `ToolCallFailed` | 範疇 2 | Tool 拋錯 |
| `MemoryAccessed` | 範疇 3 | memory layer read/write（**51.2 Day 4** payload 擴：`scope` / `time_scale` / `confidence` / `verify_before_use` / `tenant_id`） |
| `ContextCompacted` | 範疇 4 | Compactor 觸發（**52.1 Day 2.7** Loop integration 接通；payload：`tokens_before` / `tokens_after` / `compaction_strategy` / `messages_compacted` / `duration_ms`） |
| `PromptBuilt` | 範疇 5 | PromptBuilder 完成（**52.2 Day 3.1** Loop integration 接通；payload：`messages_count` / `estimated_input_tokens` / `cache_breakpoints_count` / `memory_layers_used: tuple[str, ...]` / `position_strategy_used` / `duration_ms`） |
| `StateCheckpointed` | 範疇 7 | Checkpointer save |
| `ErrorRetried` | 範疇 8 | Retry 觸發 |
| `GuardrailTriggered` | 範疇 9 | input/output/tool guardrail block |
| `TripwireTriggered` | 範疇 9 | Tripwire 觸發即停 |
| `VerificationPassed` | 範疇 10 | Verifier OK |
| `VerificationFailed` | 範疇 10 | Verifier 拒絕 |
| `SubagentSpawned` | 範疇 11 | Subagent 啟動 |
| `SubagentCompleted` | 範疇 11 | Subagent 結束 |
| `SubagentChildEvent` | 範疇 11 → 範疇 12 | Subagent 子 loop 的 per-turn TAO 事件 wrapper（Sprint 57.96 Scope B；`subagent_id` + `inner: LoopEvent`）。`ForkExecutor` drain 時把 TAO 子集（`TurnStarted`/`LLMResponded`/`ToolCall*`）包進此 wrapper（tagged with the spawn `subagent_id`）→ 經 dispatcher `_emit_safely` → 既有 57.95 router buffer-drain relay（wrapper IS a `LoopEvent` → 免 router 改）。`sse.py` wire type `subagent_child` = `{subagent_id, inner_type, inner}`（inner 經自身 serializer 攤平）。`LoopEvent` base UNCHANGED（wrapper 非 base field）。前端 `SubagentNode.childEvents` + `chatStore` `subagent_child` routing → Inspector Tree 節點展開成 child per-turn rows。AS_TOOL 共用 `ForkExecutor` → 免費繼承。見 `CHANGE-063`。 |
| `AgentHandoff` | 範疇 11 | HANDOFF 控制轉移：父 agent 退出 + target 子 session 啟動（Sprint 57.68 A-3b；loop 終止 stop_reason="handoff"，platform `HandoffService` boot 子 session 後 router emit `agent_handoff` 含 `new_session_id`） |
| `ApprovalRequested` | §HITL 中央化 | HITL 觸發等待 |
| `ApprovalReceived` | §HITL 中央化 | HITL 結果回到 loop |
| `LoopCompleted` | 範疇 1 | Loop 終止（Sprint 57.2 加 accumulator-sourced `total_tokens` / `input_tokens` / `output_tokens` / `provider` / `model`；**Sprint 57.65 A-2 Tier2 加 `cached_input_tokens` + 衍生 `cache_hit_rate`**（= cached / input，div-by-0 → 0.0；Cat 12 prompt-cache-hit-rate metric，無 Tracer/MetricsRegistry，metric 隨 event 欄位下游消費）；**Sprint 57.82 B-8 leg-1 加 `verification_input_tokens` / `verification_output_tokens` / `verification_model`** — Cat 10 **in-loop verify gate（Sprint 57.98 起；前為 correction-loop wrapper）** 跨 verifier+attempt 累加的 judge LLM token（`_run_turns` 內 `verif_*` local 累加並 stamp terminal LoopCompleted），chat router billing observer 消費為獨立 `_verification` cost-ledger sub_type + 計入 quota actual；server-side only，不上 SSE wire（與 loop input/output_tokens 一致）；**Sprint 57.88 地基 A 加 terminal `stop_reason="awaiting_approval"`**（`TerminationReason.AWAITING_APPROVAL`，parallel to 57.68 `handoff`）— chat-path tool ESCALATE 在 `hitl_deferred` 模式下 checkpoint loop（`pending_approval` + `resume_messages` 進 `state_snapshots` JSONB，免 migration）+ emit `ApprovalRequested` + 終止以**釋放 SSE 連線**；human approve（hours/days 後）→ `POST /chat/{id}/resume` 驅動 NEW `AgentLoopImpl.resume()` 續到 `end_turn`；見 `19-pause-resume-design.md`；**Sprint 57.91 Slice 3 leg 1（CHANGE-058）同一 terminal 新增 origin**：input-guardrail ESCALATE 也經 generalized `_emit_deferred_pause` primitive 觸發 `awaiting_approval`（`pending_approval.kind="input"`，無 tool_call；resume 續到第一個 LLM turn，不執行 tool）；**Sprint 57.92 Slice 3 leg 2（CHANGE-059）同一 terminal 第三 origin**：between-turns guardrail ESCALATE 在 `_run_turns` loop 頂端（≥1 turn 後、下一 LLM call 前）觸發 `awaiting_approval`（`pending_approval.kind="between_turns"`，無 tool_call；resume 經 `skip_between_turns_once` 續到下一 turn 的 LLM，不重新 escalate）；新增 `GuardrailType.BETWEEN_TURNS` enum value（single-source `guardrails/_abc.py`；無新 LoopEvent contract）；**Sprint 57.93 Slice 3 output-guardrail leg（CHANGE-060）同一 terminal 第四 origin**：output-guardrail ESCALATE 在 FINAL answer 上於 `_run_turns` parse 後、`LLMResponded` **之前**（pre-delivery gate，gated on `is_final_answer` + full deferred-HITL wiring）觸發 `awaiting_approval`（`pending_approval.kind="output"`，無 tool_call，carries held-answer `response_snapshot`）；reuse 既有 `GuardrailType.OUTPUT` + `check_output`（無新 enum value）；resume output kind 為 TERMINAL（不 drive `_run_turns`）— APPROVED re-emit held `LLMResponded`+`END_TURN`（無 LLM re-call），REJECTED → `GUARDRAIL_BLOCKED`；無新 LoopEvent contract；**Sprint 57.98 A1（CHANGE-065）新增 terminal `stop_reason="verification_failed"`**：in-loop Cat 10 gate 在 self-correction budget（`max_correction_attempts`，default 2）耗盡時終止（raw string，無新 `TerminationReason` enum，無 consumer switch）；verifier registry 由 `build_handler` 注入 `AgentLoopImpl` ctor（前為 `run_with_verification` wrapper 包覆 `loop.run()`，已退役刪除）；`resume()` 經共用 `_run_turns` 自動驗證 resumed 答案（關閉 pre-57.98 漏洞）；durable `verification_attempts` 騎 checkpoint `metadata`（無新 DurableState 欄位）；`VerificationPassed/Failed` contract 不變；**Sprint 57.99 A2（CHANGE-066）同一 `verification_failed` terminal 加條件性人類 ESCALATE 替代**：`chat_verification_escalate_on_max` toggle（default OFF = A1 byte-identical）ON 且 full deferred-HITL wiring 在場時，FAIL==max swap-point 改 `_cat10_verification_escalate_pause()` 觸發 `awaiting_approval` **第五 origin**（`pending_approval.kind="verification"`，carries held failed-answer `response_snapshot` + durable `verification_escalated` flag 騎 `metadata`，無 migration）而非直接 terminal；`resume()` 新增 `kind="verification"`：APPROVE → `_replay_approved_output` 交付 held 答案（人類覆蓋 verifier，TERMINAL，不 re-verify）/ REJECT-with-note → 註記回注成 `user` correction + 恰一個 human-coached turn（`verification_attempts`=max + durable `verification_escalated` → 2nd fail 綁回 A1 terminal，無第二次 pause）；無新 LoopEvent / event-schema（reuse `ApprovalRequested`/`ApprovalReceived`） |
| `SpanStarted` | **範疇 12** | OTel span 開始 |
| `SpanEnded` | **範疇 12** | OTel span 結束 |
| `MetricRecorded` | **範疇 12** | latency / token / cost 三軸 metric |

### 4.2 事件序列規範

`AgentLoop.run()` 必須 yield `AsyncIterator[LoopEvent]`（**non-sync callback**），由消費者（API / SSE handler）決定怎麼 forward 給用戶。

```python
# ✅ 正確：async iterator
async for event in loop.run(...):
    await sse_emit(event)

# ❌ 錯誤：sync callback（已從 V2 移除，違反原則 1 / 4 Async-First）
def on_event(event: LoopEvent) -> None: ...  # 不再接受
```

---

## 第 5 部分：HITL 中央化

> **問題**：HITL 機制散落在範疇 2（`request_approval` tool）/ 範疇 7（`pending_approvals` in state）/ 範疇 8（HITL recoverable error）/ 範疇 9（HITL guardrail action），缺中央定義。

> **解法**：在 `01-eleven-categories-spec.md` 末尾建立 **§HITL Centralization** 章節，作為 single-source。各範疇只引用、不重新定義。

### 5.1 HITL 統一架構

```
                ┌──────────────────────────────────┐
                │        HITLManager               │
                │  (single-source ABC)             │
                └──────────────┬───────────────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
       ▼                       ▼                       ▼
┌──────────────┐      ┌──────────────────┐    ┌──────────────────┐
│ 範疇 2       │      │ 範疇 9           │    │ 範疇 7           │
│ Tools:       │      │ Guardrail:       │    │ State:           │
│ request_     │      │ HIGH risk →      │    │ pending_         │
│ approval     │      │ require approval │    │ approvals[]      │
│ (caller)     │      │ (caller)         │    │ (storage)        │
└──────────────┘      └──────────────────┘    └──────────────────┘
       │                       │                       │
       └───────────────────────▼───────────────────────┘
                       Approval queue
                  (DB-backed, durable across sessions)
```

### 5.2 HITL 介面（owner: HITL Centralization 章節）

```python
@dataclass
class ApprovalRequest:
    request_id: UUID
    tenant_id: UUID
    session_id: UUID                # source session
    requester: str                  # category name e.g. "tools" / "guardrails"
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    payload: dict
    sla_deadline: datetime
    context_snapshot: dict          # for human reviewer

@dataclass
class ApprovalDecision:
    request_id: UUID
    decision: Literal["APPROVED", "REJECTED", "ESCALATED"]
    reviewer: str
    reason: Optional[str]
    decided_at: datetime

class HITLManager(ABC):
    @abstractmethod
    async def request_approval(self, req: ApprovalRequest) -> UUID: ...
    @abstractmethod
    async def wait_for_decision(self, request_id: UUID, timeout_s: int) -> ApprovalDecision: ...
    @abstractmethod
    async def get_pending(self, tenant_id: UUID) -> list[ApprovalRequest]: ...
    @abstractmethod
    async def get_decision(self, request_id: UUID) -> ApprovalDecision | None: ...  # Sprint 57.88 — non-blocking read (None if still PENDING)
```

> **Sprint 57.88 加 `get_decision`**：deferred pause-resume 需要一個**非阻塞**的決策讀取（`resume()` 在 RUN-2 讀已記錄的 `ApprovalDecision`，不能 block）。`wait_for_decision` 已 refactor 到共用 `_read_decision_if_decided`（0 行為變更）。實作 `DefaultHITLManager`（`platform_layer/governance/hitl/manager.py`）。

### 5.3 跨範疇 HITL 互動規則

- 範疇 2 / 9 **是 caller**，呼叫 `HITLManager.request_approval()`
- 範疇 7 **是 storage**，把 `pending_approval_ids: list[UUID]` 放進 DurableState
- 範疇 8 **不直接 own HITL**，只把 HITL pending 視為 「LLM-recoverable resumable wait」
- HITL 結果回流時，**Reducer** 負責把 `ApprovalDecision` merge 回 `LoopState` 並 resume
- **Deferred mode（Sprint 57.88 地基 A）**：chat path 在 `hitl_deferred=True` 時，範疇 9 的 ESCALATE branch **不** call `wait_for_decision`（阻塞），改 checkpoint loop（`pending_approval` + `resume_messages` 進 `state_snapshots` JSONB）+ emit `ApprovalRequested` + 終止以釋放 SSE 連線；human approve 後 `POST /chat/{id}/resume` → `AgentLoopImpl.resume()` 讀 `HITLManager.get_decision()`（非阻塞）→ APPROVED exec pending tool 續到 end_turn / REJECTED block。阻塞 `wait_for_decision` 路徑 retained（additive，給同步 caller）。權威設計：`19-pause-resume-design.md`

---

## 第 6 部分：Tripwire 邊界（範疇 8 vs 9）

> **問題**：範疇 8（Error）與範疇 9（Guardrail）都提 tripwire 概念，邊界模糊。

> **裁定**：**Tripwire 屬於範疇 9（Guardrail）**。範疇 8 不再用 tripwire 一詞，改用 `error_terminator` 區分。

| 概念 | Owner 範疇 | 觸發方式 | 處置 |
|------|----------|---------|------|
| `Tripwire` | **範疇 9 (Guardrail)** | 偵測到嚴重 policy violation（PII leak / jailbreak / data exfil 嫌疑） | **立即終止 loop**，不 retry |
| `ErrorTerminator` | **範疇 8 (Error)** | Error budget 超支 / circuit breaker open / fatal exception | **立即終止 loop**，不 retry |
| `Guardrail.check()` 失敗 | **範疇 9** | 一般 input/output/tool guardrail | 看 `OutputGuardrailAction`：reroll / sanitize / abort / escalate |
| `ErrorPolicy.should_retry()` 為 false | **範疇 8** | 一般非 transient error | 視 type 決定 retry / 回注 LLM / 回傳給 user |

---

## 第 7 部分：跨範疇呼叫順序圖（節錄）

完整順序圖見 `12-category-contracts.md`。本附錄只列**易混淆的跨範疇呼叫**：

### 7.1 範疇 4（Context）→ 範疇 11（Subagent）

```
Loop turn N: context_used > 75%
  ↓
範疇 4 Compactor.compact() 被呼叫
  ↓
若 compaction 不足 + 任務可拆分
  ↓
範疇 4 emit hint: "consider subagent delegation"
  ↓
範疇 1 Loop 把 hint 注入 next prompt
  ↓
LLM 自己決定是否呼叫 task_spawn tool（範疇 11 own）
  ↓
範疇 4 不直接呼叫範疇 11 — 僅透過 LLM decision
```

**規則**：範疇 4 與 範疇 11 之間**沒有直接 ABC 呼叫**，僅透過「prompt hint + LLM 決策」聯繫。Spec 必須明示這點。

### 7.2 範疇 12（Observability）滲透所有範疇

```
所有範疇的 ABC 都接受 trace_context: TraceContext 參數
  ↓
範疇 12 Tracer.start_span() 在每個 ABC 入口呼叫
  ↓
所有 LoopEvent 都附 trace_id / span_id
  ↓
SSE / OTel collector 端 reconstruction 完整 trace tree
```

**規則**：範疇 12 是 **cross-cutting concern**，所有 ABC 都吃 `TraceContext`，但**不在每個範疇 spec 重複描述**。範疇 12 spec 一次定義 + 跨範疇規範通用即可。

---

## 第 8 部分：禁止重複定義 Lint 規則

V2 在 Phase 49.4 起會加 pre-commit hook 強制執行：

### 8.1 Lint 規則 1：禁止重複 dataclass

```bash
# Pseudo-code
$ duplicate-dataclass-check backend/src/
ERROR: ToolSpec defined in 2 places:
  - backend/src/agent_harness/tools/_abc.py:23
  - backend/src/adapters/_base/chat_client.py:45
Fix: Remove the duplicate, import from agent_harness._contracts instead.
```

### 8.2 Lint 規則 2：禁止跨範疇直接 import

```python
# ❌ 禁止：範疇 4 直接 import 範疇 11
from agent_harness.subagent.dispatcher import SubagentDispatcher

# ✅ 允許：範疇 4 import 範疇 11 的 contract type
from agent_harness._contracts.subagent import SubagentBudget
```

例外：經 `12-category-contracts.md` 顯式核准的 ABC 直接呼叫（如範疇 1 → 範疇 6）。

### 8.3 Lint 規則 3：禁止 sync callback 在 async loop

```python
# ❌ 禁止
def on_event(event: LoopEvent) -> None: ...

# ✅ 允許
async def on_event(event: LoopEvent) -> None: ...
# 或
events: AsyncIterator[LoopEvent]
```

---

## 第 9 部分：使用流程

### 9.1 開發新範疇 / 修現有範疇 spec 時

1. 先看本附錄 §1-3，**確認介面是否已被某文件 own**
2. 若已被 own → spec 文件**只引用 + 加一行 `→ see 17.md §X`**
3. 若未被 own → 在所屬 spec 文件定義 + **回 PR 一併更新本附錄**
4. 不可在新文件平行定義同名介面

### 9.2 Code review 時必檢

- [ ] 修改的 dataclass 是否在本附錄登記？
- [ ] 修改的 ABC 是否在本附錄登記？
- [ ] 新增工具是否在本附錄登記？
- [ ] LoopEvent 子類是否在本附錄登記？
- [ ] 是否違反「禁止重複定義」lint 規則？

### 9.3 維護責任

本附錄與 `12-category-contracts.md`、`01-eleven-categories-spec.md`、`10-server-side-philosophy.md` 共生。任一改動都要回頭更新本附錄。

---

## 第 10 部分：附錄演進路徑

| Phase | 預計增補 |
|-------|---------|
| Phase 49.1 | 11 範疇 + 範疇 12 ABC 全部 stub |
| Phase 49.4 | Lint 規則上線（duplicate-dataclass-check） |
| Phase 50.x | LoopEvent 子類補完（隨 loop 實作） |
| Phase 53.4 | HITL 中央化完整接入 |
| Phase 54.x | Subagent + Verification contracts 補完 |
| Phase 56+ | 第 13 範疇 Cost Tracking 接入後再擴充 |

---

## 參考連結

- [01-eleven-categories-spec.md](./01-eleven-categories-spec.md) — 11 範疇 + 範疇 12 規格
- [02-architecture-design.md](./02-architecture-design.md) — 5 層架構
- [04-anti-patterns.md](./04-anti-patterns.md) — Anti-Pattern 6 (Hybrid 橋接層債務)
- [10-server-side-philosophy.md](./10-server-side-philosophy.md) — 原則 2 ChatClient ABC
- [12-category-contracts.md](./12-category-contracts.md) — 範疇間契約（順序圖 + 失敗模式）

---

**最後更新**：2026-04-28
**下次 review**：Phase 49.4（Lint 規則上線時）
