# 11 範疇完整規格（Agent Harness Specification）

**建立日期**：2026-04-23
**版本**：V2.0
**目的**：作為 V2 開發的權威範疇定義文件

> **本文件原始定義來自業界研究**，每個範疇後附「業界原文」+ 「V2 規格」+「驗收標準」。

---

## 範疇 1：Orchestrator Layer (TAO/ReAct Loop)

### 業界原文（核心定義）
> Orchestrator layer is the heartbeat. It implements the thought-action-observation (TAO) cycle, also called the ReAct loop. The loop runs: assemble prompt, call LLM, parse output, execute any tool calls, feed results back, repeat until done.

### 完整流程
1. **接收輸入**：用戶 prompt + 系統 prompt + 工具定義 + 對話歷史
2. **模型推理**：分析上下文，生成回應（回應 = 文本 + 工具調用請求（可選））
3. **判斷有無工具可調用**：
   - **有** → 執行工具（harness 執行工具，收集結果：權限檢查 → 執行 → 返回結果）
     - 結果回注（工具結果追加到對話歷史，回到模型推理階段，繼續推理）
   - **無** → 返回最終結果

### V2 規格

#### 核心 API（async-first，**禁止 sync callback**）

> **架構決定（2026-04-28 review 修訂）**：原 `on_event: Callable[[LoopEvent], None]` 是 sync callback，違反原則 1（Server-Side First → async-first），於 async event loop 上會阻塞 SSE 推送。改為 `AsyncIterator[LoopEvent]`。

```python
# agent_harness/orchestrator_loop/_abc.py
from abc import ABC, abstractmethod
from typing import AsyncIterator
from agent_harness._contracts import (
    Message, LoopEvent, TraceContext,
)
from agent_harness._contracts.tools import ToolSpec, ConcurrencyPolicy

class AgentLoop(ABC):
    """TAO loop。事件以 AsyncIterator 流式 yield，由消費者決定 SSE / WebSocket / OTel emit。"""

    @abstractmethod
    async def run(
        self,
        *,
        messages: list[Message],
        tools: list[ToolSpec],
        system_prompt: str,
        max_turns: int = 50,
        token_budget: int = 100_000,
        parallel_tool_policy: ConcurrencyPolicy = ConcurrencyPolicy.READ_ONLY_PARALLEL,
        trace_context: TraceContext | None = None,
    ) -> AsyncIterator[LoopEvent]:
        """
        TAO loop 主循環。

        終止條件（任一）：
          - stop_reason == "end_turn"（範疇 6 中性化 enum，見 17.md §1.1）
          - turn_count >= max_turns
          - tokens_used >= token_budget
          - GuardrailTriggered（範疇 9 tripwire）
          - ErrorTerminator（範疇 8 budget / circuit breaker）
          - asyncio.CancelledError（用戶中斷）

        參數說明：
          - parallel_tool_policy: 由範疇 2 ToolSpec.concurrency_policy 與此 loop-level
            policy 取嚴格交集；read_only_parallel 是業界共識（CC / Codex / LangGraph）。
          - trace_context: 由範疇 12（Observability）注入；所有 event 自動帶 trace_id /
            span_id；None 時 loop 自建 root span。
        """
        ...
```

#### Streaming-first 設計

業界共識（Anthropic / OpenAI / Azure OpenAI 全已 streaming-default）：

- **Tool call 累積**：partial tool_call delta 在 loop 內累積成完整 `ToolCall`，**不在 partial 階段執行**
- **增量 token emit**：每個 token 即時 yield 為 `Thinking` event 子類，由 SSE 立即 forward
- **Cancellation**：用戶取消時透過 `asyncio.CancelledError` 傳播，loop 必須在當前 turn 結束前釋放所有 in-flight resources（含 in-flight tool calls）

#### 必須事件（完整列表見 17.md §4.1）

最小必須集：
- `LoopStarted` / `LoopCompleted`
- `Thinking`（含 partial token emit）
- `ToolCallRequested` / `ToolCallExecuted` / `ToolCallFailed`
- `ContextCompacted`（範疇 4）
- `GuardrailTriggered`（範疇 9）
- `VerificationPassed` / `VerificationFailed`（範疇 10）
- `SpanStarted` / `SpanEnded`（**範疇 12**）

### 驗收標準

#### 結構驗收（binary）
- [ ] Loop 真正使用 `while` 結構（非 `for` 固定迴數）
- [ ] `StopReason` enum 驅動退出（中性化，見 17.md §1.1）
- [ ] 工具結果以 `user message` 形式回注 messages
- [ ] 支援 max_turns / token_budget / tripwire / error_terminator 四類終止
- [ ] 整個 loop 可被取消（asyncio.CancelledError），in-flight tool calls 正確釋放
- [ ] 有完整事件流（`AsyncIterator[LoopEvent]`，**禁止 sync callback**）
- [ ] `parallel_tool_policy` 與 `ToolSpec.concurrency_policy` 取嚴格交集執行
- [ ] 所有 event 自動 propagate `trace_context`（範疇 12 cross-cutting）

#### SLO 量化驗收（Phase 50.2 起強制）
- [ ] **p95 loop latency**：簡單問題（≤ 3 turn） < 5s；中等任務（4-10 turn） < 30s
- [ ] **Token efficiency**：summarize 之後 / 原始 token 比例 < 0.3
- [ ] **Tracing coverage**：100% turn 有對應 OTel span
- [ ] **Anti-Pattern 1（Pipeline 偽裝 Loop）零違反**（lint rule 強制）

---

## 範疇 2：Tool Layer

### 業界原文
> Tools are the agent's hands. They're defined as schemas (name, description, parameter types) injected into the LLM's context so the model knows what's available. The tool layer handles registration, schema validation, argument extraction, sandboxed execution, result capture, and formatting results back into LLM-readable observation.

### ⚠️ 關鍵理解：CC 工具與 V2 工具完全不同

**CC（本地工具）** vs **V2（企業 server-side）** 的根本差異：

| CC 假設 | V2 現實 |
|--------|--------|
| 用戶坐在終端前 | 用戶在遠端瀏覽器 |
| 完整 host filesystem 存取 | server 上**沒有用戶的 filesystem** |
| Bash 任意 shell 執行 | 只能執行**沙盒化** + **白名單命令** |
| 「Read user file」有意義 | **無意義** — server 沒有「用戶檔案」 |
| 單用戶 trust model | multi-tenant zero-trust |

**結論**：**V2 工具不是 CC 工具的「升級版」，而是「完全不同類型的工具」**。

### CC 6 大類（僅作架構參考，非實作模板）

CC 提供 6 大類工具：
1. 文件操作（Read / Write / Edit）— **V2 不對應**
2. 搜索（Grep / Glob）— **V2 不對應本地，改為 KB Search**
3. 執行（Bash）— **V2 改為沙盒**
4. 網頁訪問（WebFetch / WebSearch）— **V2 加企業治理**
5. 代碼智能分析（LSP-based）— **V2 不對應**
6. 子代理生成（Task）— **V2 對應，但跨 process**

### V2 規格（**通用** server-side 6 大類 + 業務領域獨立 + HITL 中央化）

> **架構決定（2026-04-28 review 修訂）**：原 8 大類把 IPA 業務領域工具（patrol / correlation / rootcause / audit / incident）混入**通用** harness spec，違反「11 範疇是通用 harness」的 framing，會把 V1 業務鎖進 harness 規格。**拆分**：
> 1. 第 7 類「業務領域工具」→ 獨立至 [`08b-business-tools-spec.md`](./08b-business-tools-spec.md)
> 2. 第 8 類「HITL / Governance 工具」→ 由 §HITL 中央化（本檔末尾）統一定義
> 3. 本範疇只保留**通用** 6 大類

#### 1. **企業資料查詢工具**（核心）
- `salesforce_query` / `d365_query` / `sap_query`
- `crm_search_customer` / `erp_pull_orders`
- `kb_search` / `sharepoint_search` / `confluence_search`
- 特性：**read-only、tenant-scoped、RBAC enforced**

#### 2. **企業資料變更工具**（高 HITL）
- `salesforce_update` / `servicenow_create_ticket`
- `email_send` / `teams_post_message`
- `erp_modify_order`
- 特性：**mutating、必經 HITL approval、完整 audit**

#### 3. **沙盒執行工具**（受控）
- `python_sandbox`（容器內執行，無 host fs）
- `sql_query`（限定 query account，唯讀）
- `shell_sandbox`（白名單命令，如 grep / curl）
- 特性：**容器隔離、CPU/memory 限制、超時保護**

#### 4. **網絡工具**（治理代理）
- `web_search`（透過企業代理）
- `web_fetch`（白名單 domain）
- `api_call`（已註冊的外部 API）
- 特性：**經企業 proxy、egress 監控、log 完整 URL**

#### 5. **記憶工具**（範疇 3 對接）
- `memory_search(query, layers=["user", "session"], top_k=5)`
- `memory_write(content, layer="user", category=...)`
- `memory_list(layer, category)`
- 特性：**tenant-scoped、agent 可隨時呼叫**

#### 6. **子代理工具**（範疇 11 對接）
- `task_spawn(role, task, mode="fork")` — 衍生子 agent
- `handoff_to(agent_role, context)` — 完全交棒
- `subagent_query(agent_id, message)` — Teammate 通信
- 特性：**返回強制 ≤ 2K token 摘要**

#### 7. **業務領域工具** → 拆出獨立 spec
> 詳見 [`08b-business-tools-spec.md`](./08b-business-tools-spec.md)。本範疇**不**列舉 IPA 業務工具，避免通用 harness 鎖入特定業務。

#### 8. **HITL / Governance 工具** → §HITL 中央化
> 詳見本檔末尾 §HITL 中央化（single-source）。範疇 2 / 9 為 caller，範疇 7 為 storage。

---

### 重要：V2 工具定義使用中性 ToolSpec

**禁止**直接使用 OpenAI 或 Anthropic 的 tool schema 格式：

```python
# ❌ 禁止
tools = [{"type": "function", "function": {...}}]  # OpenAI 原生
tools = [{"name": "...", "input_schema": {...}}]    # Anthropic 原生

# ✅ 正確：V2 中性 ToolSpec
from src.agent_harness.tools.spec import ToolSpec

spec = ToolSpec(
    name="salesforce_query",
    description="Query Salesforce records",
    input_schema={...},     # JSON Schema 中性
    output_schema={...},
    handler=...,
    permissions=...,
    hitl_policy=...,
    sandbox_level=...,
    is_mutating=False,
)
```

Adapter 層負責轉換為各供應商格式（見 `10-server-side-philosophy.md` 原則 2）。

#### ToolSpec 統一規格（**2026-04-28 review 修訂**：對齊 MCP 4 hints + concurrency policy + version）

```python
@dataclass
class ToolAnnotations:
    """MCP-standard hints。LLM 用這 4 個 hint 做決策（非 spec 用於執行控制）。"""
    read_only: bool = False        # readOnlyHint
    destructive: bool = False      # destructiveHint
    idempotent: bool = False       # idempotentHint
    open_world: bool = False       # openWorldHint（如 web_search 結果隨時間變化）


class ConcurrencyPolicy(Enum):
    SEQUENTIAL = "sequential"
    READ_ONLY_PARALLEL = "read_only_parallel"
    ALL_PARALLEL = "all_parallel"


@dataclass
class ToolSpec:
    """Owner: 範疇 2；single-source 在 17.md §1.1。"""
    name: str
    description: str
    input_schema: dict             # JSON Schema 中性
    output_schema: dict
    result_content_types: list[Literal["text","json","image","audio"]] = field(default_factory=lambda: ["text"])

    # MCP-standard annotations（LLM 決策依據）
    annotations: ToolAnnotations = field(default_factory=ToolAnnotations)

    # 並行政策（loop-level policy 與此取嚴格交集）
    concurrency_policy: ConcurrencyPolicy = ConcurrencyPolicy.SEQUENTIAL

    # Versioning（rolling deploy v1 / v2 共存）
    version: str = "1.0"
    deprecated: bool = False

    # 執行
    handler: Callable[[dict, TraceContext], Awaitable[ToolResult]]

    # 權限
    permissions: PermissionSpec    # role × tenant

    # HITL
    hitl_policy: HITLPolicy        # auto / ask_once / always_ask（見 §HITL 中央化）

    # 安全
    is_mutating: bool              # 與 annotations.destructive 應一致
    sandbox_level: SandboxLevel    # none / process / container

    # 審計
    audit: AuditSpec               # log_request / log_response / sensitive_fields
```

#### Schema validation failure 路徑（與範疇 8 對接）

LLM 產生的 tool_call args JSON 驗證失敗時：

```python
# 範疇 6 (output_parser) → 範疇 2 (executor) → 範疇 8 (error)
# 失敗為 LLM_RECOVERABLE，不 raise，回注 error message 讓 LLM 自我修正
ToolResult(
    tool_call_id=tc.id,
    is_error=True,
    content="Schema validation failed: ... Please correct your tool call args.",
    error_category=ErrorCategory.LLM_RECOVERABLE,
)
```

### 驗收標準

#### 結構驗收
- [ ] 所有工具透過統一 `ToolRegistry` 註冊
- [ ] 強制 JSONSchema 驗證輸入
- [ ] **ToolAnnotations 4 hints 完整**（read_only / destructive / idempotent / open_world）
- [ ] **`concurrency_policy` 必填**，與 loop-level policy 取嚴格交集
- [ ] **Tool versioning 機制**（v1 / v2 共存，deprecated 警告）
- [ ] Read-only 工具可並行，mutating 工具序列執行
- [ ] 每個工具都有權限檢查
- [ ] 危險工具經過 sandbox
- [ ] 工具結果格式化為 LLM-readable（支援 `result_content_types` 中性化）
- [ ] Schema validation failure 走 LLM_RECOVERABLE 路徑（不 raise）

#### Multi-tenant / 安全驗收
- [ ] Tenant A 無法呼叫到 tenant B 的工具實例
- [ ] Tool args 中 PII 自動 redact 入 audit log
- [ ] 危險工具（is_mutating=True）強制經 HITL approval

#### SLO 量化驗收
- [ ] Read-only tool p95 latency < 1s
- [ ] Mutating tool p95 latency < 3s（含 HITL wait 不計）
- [ ] Schema validation < 10ms

---

## 範疇 3：Memory（多時間尺度）

### 業界原文
> Memory operates at multiple timescales. Short-term memory is conversation history within a single session. Long-term memory persists across sessions. Anthropic uses local claude.md project files and auto-generated memory.md files; LangGraph uses namespace-organized JSON stores; OpenAI supports Sessions backed by SQLite or Redis.

### Claude Code 3 層架構（參考）
1. **輕量級索引**（每條約 150 字符，**始終處於加載狀態**）
2. **按需載入的詳細主題文件**
3. **只通過搜索才能訪問的原始文件記錄**

> **核心設計原則**：智能體將自身的記憶視為「線索」，**在採取行動前會與實際狀態進行比對**。

### V2 規格（企業雙軸架構：Scope × Time Scale）

> **架構決定（2026-04-28 review 修訂）**：原 5 層只有 **scope 軸**（system → tenant → role → user → session），缺**第二軸 time scale**（業界基準是 short-term / long-term / semantic）。修訂為**雙軸矩陣**，5 個 scope × 3 個 time scale = 15 個 cell（部分 cell 不適用，標 N/A）。

#### 雙軸矩陣

|  | **Short-term**<br/>(working memory<br/>per-session) | **Long-term**<br/>(durable<br/>cross-session) | **Semantic**<br/>(embedded<br/>vector search) |
|---|---|---|---|
| **L1 System** | N/A | 系統規則 / 安全政策<br/>（DB const） | 規則嵌入<br/>（startup index） |
| **L2 Tenant** | 當前 session 注入的<br/>tenant overrides | tenant playbook /<br/>SOP / FAQ（DB） | tenant 知識庫<br/>（Qdrant） |
| **L3 Role** | 當前對話的角色臨時<br/>規則修飾 | per-role policy /<br/>workflow（DB） | 角色行為模板<br/>嵌入 |
| **L4 User** | 當前 session 的<br/>user context（in-mem） | per-user 偏好 /<br/>習慣（DB，TTL: ∞） | user 歷史對話<br/>嵌入索引 |
| **L5 Session** | messages[] in Redis<br/>(TTL 24h) | session summary →<br/>L4 User extraction | session 內容<br/>臨時嵌入 |

#### 存儲後端對應

| Cell | Storage | 寫入觸發 | 讀取模式 | 失效策略 |
|------|---------|---------|---------|---------|
| L1 long-term | PostgreSQL `system_policies` | manual / migration | startup load | DB DELETE |
| L1 semantic | Qdrant `system_index` | startup re-embed | similarity search | rebuild |
| L2 long-term | PostgreSQL `tenant_memory` | admin UI / extraction worker | startup + per-tenant cache | event-driven invalidation |
| L2 semantic | Qdrant `tenant_{id}_kb` | doc upload | similarity search top_k | rebuild on doc update |
| L3 long-term | PostgreSQL `role_policies` | admin UI | per-role cache | event-driven |
| L4 long-term | PostgreSQL `user_memory` | extraction worker | per-user cache | manual / size cap (FIFO) |
| L4 semantic | Qdrant `user_{id}_history` | extraction worker | similarity search | TTL 90d |
| L5 short-term | Redis `session:{id}:messages` | per turn | full load | TTL 24h |
| L5 → L4 | extraction worker | session end | N/A | one-shot |

> 完整 schema 見 `09-db-schema-design.md`。

#### Memory as Tool（CC 模式 + 雙軸支援）

```python
# Owner: 範疇 3，註冊到範疇 2 ToolRegistry（見 17.md §3.1）

await memory_search(
    query="payment refund policy",
    layers=["L2_tenant", "L4_user"],
    time_scales=["long_term", "semantic"],   # ← 新增第二軸
    top_k=5,
)

await memory_write(
    content="user prefers detailed financial breakdowns",
    layer="L4_user",
    time_scale="long_term",
    category="preference",
    verify_before_use=True,                   # ← MemoryHint 新欄位
)
```

#### MemoryHint —「線索→驗證」資料結構

> **架構決定**：原 spec 只寫概念，沒落到 API。現定義 dataclass + `verify_before_use: bool` 強制檢查。

```python
@dataclass
class MemoryHint:
    """記憶條目，agent 必須當作「線索」而非「事實」。"""
    content: str
    layer: Literal["L1_system","L2_tenant","L3_role","L4_user","L5_session"]
    time_scale: Literal["short_term","long_term","semantic"]
    confidence: float                # 0.0-1.0
    last_verified_at: datetime | None
    verify_before_use: bool          # True → agent 必須先用 tool 驗證
    source_tool_call_id: str | None  # 「線索」原始來源
```

Agent 行為規範（由範疇 5 PromptBuilder 注入 system prompt）：
1. 取得 `MemoryHint`（may be 過時）
2. 若 `verify_before_use=True`，**必須** 先呼叫驗證工具
3. 不一致時呼叫 `memory_write` 更新

#### 衝突解決規則

兩條記憶衝突時：

| 規則 | 優先 |
|------|------|
| 1. confidence 高者優先 | confidence ≥ 0.8 直接勝出 |
| 2. last_verified_at 新者優先 | 未過 7 日的最新值 |
| 3. layer 越具體越優先 | L4 user > L3 role > L2 tenant > L1 system |
| 4. 都不確定時 → 觸發 HITL | request_clarification |

### 驗收標準

#### 結構驗收
- [ ] **5 scope × 3 time scale 雙軸矩陣完整**
- [ ] 每個 cell 明確 storage backend + 寫入 / 讀取 / 失效規則
- [ ] `MemoryHint` dataclass 與 `verify_before_use` 機制
- [ ] Memory extraction worker（async background，session end 觸發）
- [ ] 衝突解決規則 4 條落地

#### 工具驗收
- [ ] `memory_search` / `memory_write` / `memory_list` 接 `time_scales` 參數
- [ ] 工具註冊在範疇 2 Registry（見 17.md §3.1）
- [ ] 每輪 loop 自動注入 L1-L4 摘要（< 2K token）
- [ ] 「線索→驗證」工作流範例案例通過

#### 多租戶 / 安全驗收
- [ ] **Red-team test：跨 tenant prompt injection 0 leak**
- [ ] Tenant A 透過 memory_search 看不到 Tenant B 的任何 record
- [ ] Audit log 記錄所有 memory write（含 trace_context）

#### SLO 量化驗收
- [ ] memory_search p95 < 200ms（top_k=5，semantic）
- [ ] memory_write p95 < 100ms
- [ ] Extraction worker SLA：session end 後 60s 內完成
- [ ] L4 user memory 累計 cap：1000 entries，FIFO eviction

---

## 範疇 4：Context Management（防 Context Rot）

### 業界原文
> This is where agents fail silently. The core problem is context rot: model performance degrades 30%+ when key content falls in mid-window positions (Chroma research, corroborated by Stanford's "Lost in the Middle" finding). Even million-token windows suffer from instruction-following degradation as context grows.

### 4 大機制
1. **Compaction**（壓縮）：summarizing conversation history when approaching limits（CC 保架構決策 + 未解 bug，丟冗餘工具輸出）
2. **Observation Masking**（遮蔽）：JetBrains Junie 隱藏舊工具輸出但保留工具呼叫
3. **Just-in-Time Retrieval**（即時檢索）：維持輕量識別碼，動態載入資料（CC 用 grep/glob/head/tail 而非全載）
4. **Sub-agent Delegation**（子代理委派）：每子代理探索後返回 1000-2000 token 摘要

### V2 規格

#### Compaction 觸發
```python
class ContextCompactor:
    def should_compact(self, ctx: LoopContext) -> bool:
        return (
            ctx.token_count > ctx.window_size * 0.75
            or ctx.turn_count > 30
        )
    
    async def compact(self, messages: list[Message]) -> list[Message]:
        """
        策略：
        - 保留：system prompt, 最近 N turn, HITL decisions, 重要 tool results
        - 摘要：早期工具輸出, 重複內容
        - 丟棄：失敗 retry, 已被覆蓋的訊息
        """
```

#### Observation Masking
```python
class ObservationMasker:
    def mask_old_results(self, messages: list[Message], keep_recent: int = 5):
        """
        保留：所有 tool_call requests
        遮蔽：超過 keep_recent 輪的 tool_results（替換為 [REDACTED: tool X result]）
        """
```

#### JIT Retrieval
```python
# 不要：把整個 5000 行文件塞入 context
# 要：只塞 file path + outline，agent 用工具按需 read
```

#### Prompt Caching（**2026-04-28 review 新增**）

> **新增理由**：Anthropic / Azure OpenAI / OpenAI 都支援 prompt caching；multi-tenant 場景中 system prompt + tool definitions + tenant memory 高度可重用，**忽略 caching 等於放棄 30-90% cost saving**。

```python
@dataclass
class CachePolicy:
    """Per-tenant + per-loop caching 政策。"""
    enabled: bool = True
    cache_system_prompt: bool = True      # System prompt（穩定）
    cache_tool_definitions: bool = True   # Tool schemas（半穩定）
    cache_memory_layers: bool = True      # Tenant + role + user memory（半穩定）
    cache_recent_turns: bool = False      # Conversation（變動快，不 cache）
    ttl_seconds: int = 300                # Anthropic default 5 min
    invalidate_on: list[Literal[
        "tenant_memory_update",
        "tool_schema_change",
        "role_policy_change",
    ]] = field(default_factory=list)


class PromptCacheManager(ABC):
    """由範疇 4 own，由範疇 5 PromptBuilder 在 build() 時調用。"""

    @abstractmethod
    async def get_cache_breakpoints(
        self,
        *,
        tenant_id: UUID,
        policy: CachePolicy,
    ) -> list[CacheBreakpoint]:
        """產生 Anthropic-style cache_control breakpoints。"""

    @abstractmethod
    async def invalidate(self, tenant_id: UUID, reason: str) -> None:
        """主動失效（tenant memory 更新時呼叫）。"""
```

**Cache key 設計**（tenant 隔離 + provider 中性）：

```
cache_key = sha256(
    tenant_id || section_id || content_hash || provider_signature
)
```

**Provider 對應**：
- Anthropic：`messages` 中加 `cache_control: {"type": "ephemeral"}` 標記（範疇 5 PromptBuilder 處理）
- Azure OpenAI / OpenAI：用 `prompt_cache_key`（自動 cache）
- 失效統一由 `PromptCacheManager.invalidate()` 觸發

### 驗收標準

#### 結構驗收
- [ ] Compaction 自動觸發於 75% window 使用率
- [ ] 30+ turn 對話不會 OOM
- [ ] Observation masking 保留 tool_calls 但遮蔽舊 results
- [ ] Subagent 返回摘要由 caller-defined cap（範疇 11 SubagentBudget）
- [ ] Context rot 防禦測試案例通過
- [ ] **Compaction 策略可選**（`Literal["structural", "semantic", "hybrid"]`）
- [ ] **TokenCounter ABC** per-provider 實作（tiktoken / claude-tokenizer / o200k_base）

#### Caching 驗收
- [ ] **`PromptCacheManager` 與 `CachePolicy` 實作**
- [ ] Tenant 隔離測試（tenant A cache 不被 tenant B hit）
- [ ] Cache invalidation 在 memory update / role change 時自動觸發
- [ ] **Cache hit 率 > 50%**（穩態 multi-turn 對話量測）

#### SLO 量化驗收
- [ ] `context_used / window <= 75%` 在 95% session 中保持
- [ ] Compaction p95 latency < 2s
- [ ] Token counter 誤差 < 2%（與 provider 實際 billing 比對）

---

## 範疇 5：Prompt Construction（階層組裝）

### 業界原文
> This assembles what the model actually sees at each step. It's hierarchical: system prompt, tool definitions, memory files, conversation history and the current user message.

### 階層順序（業界共識）
```
1. System prompt（角色定義）
2. Tool definitions（工具 schemas）
3. Memory files（CLAUDE.md / 長期記憶摘要）
4. Conversation history（含過去 tool_calls + results）
5. Current user message
```

> **重要內容應位於開頭和結尾**（the "Lost in the Middle" finding）

### V2 規格

#### PromptBuilder 統一抽象
```python
class PromptBuilder:
    def build(
        self,
        system_role: str,
        tools: list[ToolSpec],
        memory_layers: list[MemoryLayer],
        conversation: list[Message],
        user_message: str,
        position_strategy: PositionStrategy = "lost_in_middle_aware",
    ) -> AssembledPrompt:
        """
        position_strategy:
        - "naive": 順序組裝
        - "lost_in_middle_aware": 重要內容置首尾
        - "tools_at_end": 工具放結尾（某些模型偏好）
        """
```

#### Lost-in-Middle 策略
```
順序：
[System][Tools][Memory Summary][...mid context...][Recent Conversation][User Message]
                                                                              ↑ 重要
[System]                                                                     ↑ 重要
```

### 驗收標準

#### 結構驗收
- [ ] 統一 PromptBuilder 為唯一入口
- [ ] 主流量 LLM 呼叫**禁止繞過 PromptBuilder**（lint rule 強制）
- [ ] Lost-in-middle 策略可配置
- [ ] Memory layers 確認真正注入（測試覆蓋 5 layer × 3 time scale）
- [ ] Token 計算精確（為範疇 4 服務）
- [ ] **`CacheBreakpoint` 標記 API**（Anthropic-style cache_control，配合範疇 4 caching）
- [ ] **PromptAudit 政策**（哪些 tenant 開啟 prompt log；合規 vs 隱私平衡）

#### SLO 量化驗收
- [ ] PromptBuilder p95 build time < 50ms（含 memory injection）
- [ ] Lost-in-middle 後位置精準度 95%+
- [ ] Cache hit 率 > 50%（穩態 multi-turn）

---

## 範疇 6：Output Parsing（Native Tool Calling）

### 業界原文
> Modern harnesses rely on native tool calling, where the model returns structured tool_calls objects rather than free-text that must be parsed. The harness checks: are there tool calls? Execute them and loop. No tool calls? That's the final answer.

### V2 規格

#### Native Tool Calling 強制
```python
# Adapter 層
class ChatClientBase(ABC):
    @abstractmethod
    async def chat_with_tools(
        self,
        messages: list[Message],
        tools: list[ToolSpec],
        tool_choice: ToolChoice = "auto",
    ) -> ChatResponse:
        """
        必須使用 native function calling，禁止文本解析。
        Response.tool_calls 是 List[ToolCall] 物件。
        """
```

#### 解析邏輯
```python
def classify_output(response: ChatResponse) -> OutputType:
    if response.tool_calls:
        return OutputType.TOOL_USE  # → 執行工具
    elif response.handoff_request:
        return OutputType.HANDOFF  # → 切換 agent
    else:
        return OutputType.FINAL  # → 結束 loop
```

### 驗收標準

#### 結構驗收
- [ ] 所有 LLM 呼叫透過 native function calling
- [ ] **禁止任何正則解析**作為主路徑
- [ ] Tool args JSON 解析失敗時觸發 schema retry（非靜默 fallback）
- [ ] **`StopReason` enum 中性化**（替代 per-provider 字串，見 17.md §1.1）
- [ ] **Streaming partial parsing**：tool_call 累積成完整 ToolCall 才執行
- [ ] **Handoff first-class**（見範疇 11 spec），釐清 vs tool_use 區分

#### SLO 量化驗收
- [ ] OutputParser p95 < 5ms（不含 streaming 等待）
- [ ] StopReason mapping 100% 精確（per-provider unit test）
- [ ] Schema validation failure rate < 2%（穩態運行）

---

## 範疇 7：State Management

### 業界原文
> LangGraph models state as typed dictionaries flowing through graph nodes, with reducers merging updates. Checkpointing happens at super-step boundaries, enabling resume after interruptions and time-travel debugging. OpenAI offers four mutually exclusive strategies: application memory, SDK sessions, server-side conversations API, or lightweight previous_response_id chaining. Claude Code takes a different approach: git commits as checkpoints and progress files as structured scratchpads.

### V2 規格

> **架構決定（2026-04-28 review 修訂）**：
> 1. 原 LoopState 把 transient（in-memory）與 durable（DB-persisted）混在一起，HITL 跨 session（人 4 小時後才回應）會破壞語意。**拆 `TransientState` + `DurableState`**。
> 2. LangGraph 核心是 typed state + **Reducer merge**，原 spec 只有 dataclass，HITL pause/resume / subagent return 都需要 reducer。**新增 `Reducer` ABC**。
> 3. `version` 來源未指定。**改為 `StateVersion` 明確 = monotonic counter ⊕ content hash**。

#### Typed State（拆 transient / durable）

```python
@dataclass
class TransientState:
    """In-memory 狀態，loop 結束即丟。用於當前 turn 推理。"""
    # Identity
    request_id: str
    session_id: str
    user_id: str
    tenant_id: str

    # Loop state（per-turn）
    turn_count: int
    tokens_used: int

    # In-flight
    pending_tool_calls: list[ToolCall]
    in_flight_subagents: list[SubagentHandle]

    # Verification
    verification_attempts: int

    # Trace
    trace_context: TraceContext


@dataclass
class DurableState:
    """DB-persisted 狀態，跨 session 存活。用於 HITL pause/resume / time-travel。"""
    session_id: str
    tenant_id: str

    # Conversation（DB-backed messages 表，見 09.md）
    messages: list[Message]

    # Tool history
    completed_tool_results: list[ToolResult]

    # HITL（cross-session）
    pending_approval_ids: list[UUID]   # 引用 approvals 表，不直接放 ApprovalRequest

    # Memory pointers（不複製內容，僅 reference）
    memory_layer_versions: dict[str, int]

    # Versioning
    version: StateVersion              # see below
    last_checkpoint_at: datetime


@dataclass(frozen=True)
class StateVersion:
    """版本由 monotonic counter + content hash 雙因子組成，避免 race / 偽造。"""
    counter: int                       # monotonic per session
    content_hash: str                  # sha256(canonical_json(state))
```

```python
@dataclass
class LoopState:
    """Compose transient + durable。Loop runtime 操作此 facade。"""
    transient: TransientState
    durable: DurableState
```

#### Reducer（merge 策略）

```python
from typing import Protocol, TypeVar
T = TypeVar("T")

class Reducer(Protocol[T]):
    """Merge state update。LangGraph-style，HITL resume / subagent return 必經此路徑。"""
    def merge(self, current: T, update: T) -> T: ...


# 預設 reducer 集合
class AppendReducer(Reducer[list]):
    """append-only（messages / tool_results / events）"""
    def merge(self, current: list, update: list) -> list:
        return current + update

class LastWriteWinsReducer(Reducer[Any]):
    """直接覆蓋（turn_count / tokens_used）"""
    def merge(self, current, update):
        return update

class HITLDecisionReducer(Reducer[DurableState]):
    """HITL approve/reject 回流時，把 ApprovalDecision 轉成 messages 並清 pending"""
    def merge(self, current: DurableState, decision: ApprovalDecision) -> DurableState:
        ...

class SubagentResultReducer(Reducer[DurableState]):
    """Subagent 完成時，把 SubagentResult.summary 注入 messages 為 user message"""
    def merge(self, current: DurableState, result: SubagentResult) -> DurableState:
        ...
```

#### Checkpoint 策略

```python
class Checkpointer(ABC):
    """3 種 backend 必須可切換（Phase 53.1 驗收）：PostgreSQL / Redis / S3-compatible"""

    @abstractmethod
    async def snapshot(self, state: DurableState) -> StateVersion:
        """每個 super-step 快照（每輪 loop 完成後）"""

    @abstractmethod
    async def resume(self, session_id: str, version: StateVersion | None = None) -> DurableState:
        """從快照恢復；version=None 取最新"""

    @abstractmethod
    async def time_travel(self, session_id: str, version: StateVersion) -> DurableState:
        """回到指定版本（time-travel debug）"""

    @abstractmethod
    async def list_versions(self, session_id: str) -> list[StateVersion]:
        """列出所有版本（給 DevUI / debug 用）"""
```

#### State Schema Migration（production 必備）

server-side 滾動升級時，舊 state schema 要能讀。Phase 53.1 起：

- 每個 `DurableState` 帶 `schema_version: int`
- 提供 `migrators: list[StateMigrator]`，由低版本逐級 upgrade
- Migration 必須 idempotent + 可 rollback

### 驗收標準

#### 結構驗收
- [ ] LoopState 拆 `TransientState` + `DurableState`，type annotations 完整
- [ ] `StateVersion` 雙因子（counter + hash）；race condition 測試通過
- [ ] **Reducer ABC 完成 + 4 個預設 reducer 實作**
- [ ] HITL pause/resume 必經 `HITLDecisionReducer`（單元測試證明）
- [ ] Subagent return 必經 `SubagentResultReducer`
- [ ] 每輪 loop 完成自動 checkpoint
- [ ] 支援 time-travel（至少同 session 內 10 個 version）

#### Checkpointer 驗收
- [ ] **3 種 backend 可切換**（PostgreSQL / Redis / S3-compatible），單元測試覆蓋全 3 種
- [ ] DurableState schema migration 框架就緒（schema_version + migrators）
- [ ] Audit：每個 checkpoint 操作有 trace span（範疇 12）

#### SLO 量化驗收
- [ ] Checkpoint p95 latency < 100ms（PostgreSQL backend）
- [ ] Resume p95 latency < 300ms
- [ ] Migration 1 個 schema 跳級 < 1s

---

## 範疇 8：Error Handling

### 業界原文
> Here's why this matters: a 10-step process with 99% per-step success still has only ~90.4% end-to-end success. Errors compound fast.
> 
> LangGraph distinguishes four error types: transient (retry with backoff), LLM-recoverable (return error as ToolMessage so the model can adjust), user-fixable (interrupt for human input), and unexpected (bubble up for debugging). Anthropic catches failures within tool handlers and returns them as error results to keep the loop running. Stripe's production harness caps retry attempts at two.

### V2 規格

#### 4 類錯誤
```python
class ErrorCategory(Enum):
    TRANSIENT = "transient"          # 網路、超時 → retry + backoff
    LLM_RECOVERABLE = "llm_recoverable"  # tool 失敗 → 回注給 LLM
    USER_FIXABLE = "user_fixable"    # 缺資料 → 觸發 HITL
    UNEXPECTED = "unexpected"         # bug → bubble up + 警報
```

#### Retry 策略
```python
class RetryPolicy:
    max_attempts: int = 2  # Stripe 標準
    backoff_base: float = 1.0
    backoff_max: float = 30.0
    jitter: bool = True
```

#### LLM-recoverable 範例
```python
# Tool 執行失敗
try:
    result = await tool.execute(args)
except ToolExecutionError as e:
    # 不要 raise，回注為 ToolResult
    return ToolResult(
        tool_call_id=tc.id,
        is_error=True,
        content=f"Error: {e.message}. Please adjust your approach."
    )
# Loop 繼續，LLM 看到錯誤可自我修正
```

### 驗收標準

> **2026-04-28 review 修訂**：
> - 原 `RetryPolicy.max_attempts=2` 寫死 → 改 per-tool / per-error-type 矩陣
> - 新增 `CircuitBreaker` per-provider failure threshold
> - 新增 `ErrorBudget` per-tenant per-day/month
> - **與範疇 9 邊界**：`Tripwire` 屬範疇 9，本範疇用 `ErrorTerminator`（見 17.md §6）

#### 結構驗收
- [ ] 4 類錯誤明確分類
- [ ] **`RetryPolicy` per-tool / per-error-type 矩陣**（不再寫死 2）
- [ ] LLM-recoverable 錯誤回注 messages 而非 raise
- [ ] User-fixable 觸發 HITL（透過 §HITL 中央化）
- [ ] Unexpected 觸發 alert + 完整 stack trace
- [ ] **`CircuitBreaker` per-provider**（threshold 後切備援，配合原則 2 multi-provider）
- [ ] **`ErrorBudget` per-tenant**（月度錯誤預算，超支拒絕新請求防 runaway）
- [ ] **`ErrorTerminator`（非 Tripwire）**：error budget 超支 / circuit open / fatal 觸發

#### SLO 量化驗收
- [ ] Retry overhead < 100ms per attempt
- [ ] Circuit breaker 偵測時間 < 5s
- [ ] Error budget 計算 p95 < 50ms
- [ ] 錯誤統計（per-tool / per-tenant / per-error-type）emit 範疇 12 metric

---

## 範疇 9：Guardrails & Safety

### 業界原文
> OpenAI's SDK implements three levels: input guardrails (run on first agent), output guardrails (run on final output), and tool guardrails (run on every tool invocation). A "tripwire" mechanism halts the agent immediately when triggered. Anthropic separates permission enforcement from model reasoning architecturally. The model decides what to attempt; the tool system decides what's allowed. Claude Code gates ~40 discrete tool capabilities independently, with three stages: trust establishment at project load, permission check before each tool call, and explicit user confirmation for high-risk operations.

### V2 規格

#### 3 層 Guardrails
```python
class GuardrailEngine:
    async def check_input(self, input: UserInput) -> GuardrailResult:
        """跑於 loop 開始前。檢查 PII / jailbreak / 違規請求。"""
    
    async def check_output(self, output: FinalResponse) -> GuardrailResult:
        """跑於 loop 結束前。檢查毒性 / 敏感資訊 / 合規。"""
    
    async def check_tool_call(self, tc: ToolCall, ctx: LoopContext) -> GuardrailResult:
        """跑於每個工具呼叫前。檢查權限 / 風險。"""
```

#### Tripwire
```python
class Tripwire:
    """觸發時立即中斷 agent loop"""
    
    triggers = [
        "pii_leak_detected",
        "prompt_injection_detected",
        "unauthorized_tool_access",
        "rate_limit_exceeded",
        "budget_exceeded",
        "unsafe_output_detected",
    ]
```

#### 權限與推理分離（Anthropic 模式）
```
Agent 決定「想做什麼」 → LLM 推理層
Tool system 決定「能不能做」 → Permission layer

兩者架構分離，互不干擾。
```

#### 三階段審批（CC 模式）
1. **Trust establishment**：session 開始時，建立信任 baseline（用戶角色、tenant policy）
2. **Permission check**：每個 tool call 前自動檢查
3. **Explicit confirmation**：高風險操作明確要用戶確認（透過 Teams / UI）

### 驗收標準

> **2026-04-28 review 修訂**：
> - `Tripwire` 改 ABC + plug-in registry（原 string list 不夠彈性）
> - 新增 `OutputGuardrailAction` enum（reroll / sanitize / abort / escalate）
> - 新增 `CapabilityMatrix`（CC ~40 capability 獨立 gating 對應）
> - **Audit append-only WORM + hash chain**（原「不可篡改」過弱）

#### 結構驗收
- [ ] 3 層 guardrails 全部實作
- [ ] **`Tripwire` ABC + plug-in registry**（`register(name, fn)`）
- [ ] **`OutputGuardrailAction: Literal["reroll","sanitize","abort","escalate"]`**
- [ ] **`CapabilityMatrix`**（capability → tool list 對應）
- [ ] Tripwire 觸發時 loop 立即中斷
- [ ] PII / jailbreak 檢測整合（**Defense in depth：detect + LLM-as-judge second-pass**）
- [ ] 工具能力獨立 gating（每個 tool 有自己的 permission rule）
- [ ] 三階段審批機制可運作
- [ ] **Audit log append-only WORM storage + hash chain**（不可篡改強驗證）

#### SLO 量化驗收
- [ ] Input guardrail p95 < 100ms
- [ ] Tool guardrail p95 < 50ms（per call）
- [ ] Output guardrail p95 < 200ms（含 LLM-as-judge）
- [ ] Tripwire 偵測 < 50ms
- [ ] PII / jailbreak detection accuracy > 95%（red-team test set）

---

## 範疇 10：Verification Loops

### 業界原文
> This is what separates toy demos from production agents. Anthropic recommends three approaches: rules-based feedback (tests, linters, type checkers), visual feedback (screenshots via Playwright for UI tasks), and LLM-as-judge (a separate subagent evaluates output).

### V2 規格

#### 3 種驗證
```python
class Verifier(ABC):
    @abstractmethod
    async def verify(self, output: Any, context: LoopContext) -> VerificationResult: ...

class RulesBasedVerifier(Verifier):
    """Schema validation, business rules, type checking"""

class LLMJudgeVerifier(Verifier):
    """獨立 LLM 評估輸出"""

class VisualVerifier(Verifier):
    """Playwright 截圖（企業場景較少用，保留接口）"""
```

#### Self-Correction Loop
```python
async def run_with_verification(
    loop: AgentLoop,
    verifier: Verifier,
    max_correction_attempts: int = 2,
):
    for attempt in range(max_correction_attempts + 1):
        result = await loop.run(...)
        verification = await verifier.verify(result.output, result.context)
        
        if verification.passed:
            return result
        
        # 失敗：把驗證回饋作為 user message 回注，再跑一輪
        loop.messages.append(Message(
            role="user",
            content=f"Verification failed: {verification.reason}. Please correct."
        ))
    
    # 仍失敗
    return result.with_warning("verification_failed_after_retries")
```

### 驗收標準

> **2026-04-28 review 修訂**：
> - LLM-Judge prompt 設計補 spec（原 spec 跳過此）
> - 補 verifier 自身錯誤處理（fail open vs fail closed）
> - 釐清 `at least 2` 是哪 2 種：**rules + judge 為主流量必跑**

#### 結構驗收
- [ ] 3 種 verifier 至少 2 種實作（**rules-based + LLM-judge 為主流量必跑**；visual 保留接口）
- [ ] LLM-as-judge 用獨立 subagent
- [ ] **Judge prompt template library**（`agent_harness/verification/templates/`）
- [ ] Self-correction 最多 2 次（避免無限迴圈）
- [ ] 驗證失敗有明確 audit log
- [ ] 主流量啟用 verification（非可選）
- [ ] **Verifier 自身錯誤處理**（fail-closed 預設：verifier 出錯視為驗證失敗）

#### SLO 量化驗收
- [ ] Rules-based verifier p95 < 200ms
- [ ] LLM-judge p95 < 5s（含 LLM call）
- [ ] False positive rate < 5%
- [ ] False negative rate < 10%

---

## 範疇 11：Subagent Orchestration

### 業界原文
> Claude Code supports three execution models: Fork (byte-identical copy of parent context), Teammate (separate terminal pane with file-based mailbox communication), and Worktree (own git worktree, isolated branch per agent). OpenAI's SDK supports agents-as-tools (specialist handles bounded subtask) and handoffs (specialist takes full control). LangGraph implements subagents as nested state graphs.

### ⚠️ Worktree 模式 → V2 顯式不對應

> **架構決定（2026-04-28 review 修訂）**：CC 原本的 **Worktree** 模式（per-agent 獨立 git worktree）**V2 不實作**。理由：
>
> 1. **server-side 沒有用戶 git context** — V2 server 上不存在用戶倉庫 working copy
> 2. **multi-tenant 隔離已由 RLS + tenant_id 提供** — 不需要檔案系統層級 isolation
> 3. **企業合規要求 audit log 集中** — worktree 分散 history 違反此原則
> 4. **與 10-server-side-philosophy.md 原則 3 轉化映射表一致**（CC worktree → V2 不對應）
>
> 對應 `04-anti-patterns.md` AP-2（Claude SDK 側翼陷阱）：避免引入 V2 server-side 不適用的 CC 機制。

### V2 規格

#### 4 種模式（企業版適配，**不含 Worktree**）

```python
class SubagentMode(Enum):
    FORK = "fork"            # 複製父 context，子任務探索
    TEAMMATE = "teammate"    # 獨立 context，via shared mailbox 通信
    HANDOFF = "handoff"      # 完全交棒，父 agent 退出
    AS_TOOL = "as_tool"      # 工具化，作為 callable tool
    # WORKTREE — 不對應，理由見上方架構決定
```

#### SubagentBudget（必須，避免 fork 燒爆）

```python
@dataclass
class SubagentBudget:
    """Subagent 資源 cap，由父 agent 強制傳入。"""
    max_tokens: int = 50_000           # subagent 總 token 上限
    max_duration_s: int = 300          # 牆上時鐘上限（5 min）
    max_concurrent_subagents: int = 5  # 同層同時 fork 上限
    summary_token_cap: int = 2000      # 強制摘要長度（**caller-defined**）
```

> **review 修訂**：原 spec 寫死「強制 ≤ 2K token 摘要」，但複雜任務 subagent 可能需要 4-8K。改為 **caller-defined**，由父 agent 在 spawn 時傳 `summary_token_cap`，預設 2K。

#### SubagentResult（中性化）

```python
@dataclass
class SubagentResult:
    """Subagent 回傳。Owner: 範疇 11；single-source 在 17.md §1.1。"""
    subagent_id: UUID
    mode: SubagentMode
    status: Literal["completed", "failed", "budget_exceeded", "cancelled"]
    summary: str                       # 強制 ≤ summary_token_cap
    raw_output: Optional[str]          # 完整輸出，僅 audit / debug 用
    tokens_used: int
    duration_s: float
    error: Optional[str]
```

#### SubagentDispatcher

```python
class SubagentDispatcher(ABC):
    @abstractmethod
    async def fork(
        self,
        *,
        parent_ctx: LoopContext,
        subtask: str,
        budget: SubagentBudget,
        trace_context: TraceContext,
    ) -> SubagentResult:
        """Fork 模式：子 agent 拿到父 context 副本"""

    @abstractmethod
    async def spawn_teammate(
        self,
        *,
        role: str,
        mailbox: Mailbox,
        budget: SubagentBudget,
        trace_context: TraceContext,
    ) -> SubagentHandle:
        """Teammate 模式：獨立 agent 透過 mailbox 通信"""

    @abstractmethod
    async def handoff_to(
        self,
        *,
        target_agent: AgentSpec,
        full_context: LoopContext,
        trace_context: TraceContext,
    ) -> HandoffResult:
        """Handoff 模式：完全交棒（父 agent 退出）"""

    @abstractmethod
    async def as_tool(self, agent_spec: AgentSpec) -> ToolSpec:
        """包裝為 tool（OpenAI agents-as-tools 模式）"""
```

#### Subagent 失敗傳播策略

| 策略 | 父 agent 行為 | 何時用 |
|------|-------------|------|
| `FAIL_FAST` | 任一 subagent 失敗 → 父 agent 立即終止 | 強依賴 subagent 結果的任務 |
| `FAIL_SOFT` | Subagent 失敗 → 把 error 當 SubagentResult 回傳給父；父透過 LLM 決策下一步 | **預設**，企業場景大多適用 |
| `PARTIAL_RESULT` | 多 subagent 並行，部分失敗仍接受可用結果 | Map-reduce 風格任務 |

由 `SubagentBudget.failure_policy: Literal["fail_fast","fail_soft","partial_result"]` 控制。

#### MAF 5 模式整合（保留 adapter）

V1 的 MAF Workflow Builders（GroupChat / Concurrent / Magentic / Handoff / Sequential）由 `adapters/maf/` 模組封裝為 tool，**Phase 54.2 接入**。**對應表**：

| MAF Builder | V2 SubagentMode 對應 | 接入方式 |
|------------|---------------------|---------|
| GroupChat | TEAMMATE（多人 mailbox） | `spawn_group_chat` tool（範疇 11 own） |
| Concurrent | FORK + PARTIAL_RESULT | `spawn_parallel_subagents` tool |
| Magentic | TEAMMATE + 中央 manager | `spawn_magentic` tool |
| Handoff | HANDOFF（直接對應） | `handoff_to` tool |
| Sequential | TEAMMATE 串接 | 由 caller orchestrate，不額外封裝 |

### 驗收標準

#### 結構驗收
- [ ] **顯式刪除 worktree 模式**（spec 與程式碼皆無 `WORKTREE` enum）
- [ ] Fork / Teammate / Handoff / AsTool 4 模式實作
- [ ] **`SubagentBudget` dataclass 必須**（token / duration / concurrency / summary_cap）
- [ ] Subagent 返回 `SubagentResult` 含 status enum
- [ ] Summary token cap **caller-defined**（不寫死）
- [ ] Subagent 失敗 3 種策略可選（fail_fast / fail_soft / partial_result）
- [ ] Subagent 失敗不會 crash 父 agent（fail_soft 預設）
- [ ] MAF 5 builders 透過 tool 介面可觸發（adapters/maf/，Phase 54.2）

#### 整合驗收（範疇 7 / 範疇 12）
- [ ] Subagent return 必經 `SubagentResultReducer`（範疇 7）
- [ ] Subagent 全程帶 `trace_context`，OTel span 與父 agent 連接（範疇 12）

#### SLO 量化驗收
- [ ] Subagent spawn p95 latency < 500ms
- [ ] Concurrent subagents 至少 5 個無資源競爭
- [ ] Budget exceeded 偵測 < 1s 內中斷

---

## 範疇 12：Observability / Tracing（**2026-04-28 review 新增**）

> **新增理由**：原 11 範疇來自業界 educational framing，但 enterprise server-side production 必須有完整 observability。OpenAI Agents SDK 內建 trace、LangGraph + LangSmith 是業界標配、企業 SLA 必須 OTel。原 spec 中「事件流」只是雛形未獨立成範疇。

> **實作狀態 (Sprint 57.71, A-4 loop tracer — Tier 0 + Tier 1)**：loop-internal span tree 已上線——`build_real_llm_handler` 注入真 `OTelTracer`（Tier 0），`loop.py` 開出 reconstructable `LOOP → TURN → {LLM_CALL, TOOL_EXEC, PROMPT_BUILD, COMPACTION}` span tree（root span bound `as child` 修好 nesting）。span-type 以 span name + `attributes["span_type"]` 表達，`SpanCategory` enum 不動（見 `02.md §Naming Drift Note`）。**Deferred**：(a) **Tier 2** — real OTLP→Jaeger export（需 collector + `OTEL_*` env）→ Area-C / DevOps；(b) `SpanStarted`/`SpanEnded`→SSE（§4.1 LoopEvent 子類）→ **A-5**；(c) **VERIFICATION / MEMORY_OP** loop-level span — 無乾淨 call site（verification 是 loop 外層 wrapper `correction_loop.py` 且 verifier 自有 span；memory 在 PromptBuilder 內 / 經 tool）→ 待「nest 既有內部 span」DRY refactor。

### 業界原文（綜合 OpenAI Agents SDK / LangSmith / OpenTelemetry semantic conventions）
> Observability for agent systems must capture three axes simultaneously: latency (per turn / per tool / per LLM call), tokens (input / output / cached), and cost (USD per request, per tenant). Every event must propagate trace_context (W3C TraceContext or OTel SpanContext) to enable distributed reconstruction. Span boundaries cover: per loop, per turn, per LLM call, per tool execution, per subagent, per HITL wait. Metrics complement traces with aggregable counters and histograms.

### V2 規格

#### 三軸 Observability

| 軸 | 對象 | 工具 | 落地 |
|---|------|------|------|
| **Tracing** | 因果追蹤、跨範疇 reconstruction | OpenTelemetry SDK + Jaeger / Tempo | 每個 ABC 接 `trace_context` |
| **Metrics** | latency / tokens / cost 量化 | Prometheus / OTel Metrics | `MetricEvent` emit |
| **Logging** | 結構化事件、debug | structlog + correlation_id | log 自動帶 trace_id |

#### Span 切點（強制）

```python
class SpanCategory(Enum):
    """每個 span 必有 category，OTel attribute 'agent_harness.span.category'"""
    LOOP = "loop"              # 整個 AgentLoop.run()
    TURN = "turn"              # 單一 TAO turn
    LLM_CALL = "llm_call"      # ChatClient.chat() / stream()
    TOOL_EXEC = "tool_exec"    # ToolExecutor.execute()
    MEMORY_OP = "memory_op"    # MemoryLayer read/write
    COMPACTION = "compaction"  # Compactor.compact()
    PROMPT_BUILD = "prompt_build"
    GUARDRAIL = "guardrail"    # Guardrail.check()
    VERIFICATION = "verification"
    SUBAGENT = "subagent"      # SubagentDispatcher 全 mode
    HITL_WAIT = "hitl_wait"    # HITL pause 等待時段
    CHECKPOINT = "checkpoint"  # Checkpointer.snapshot()
```

#### Tracer ABC

```python
# agent_harness/observability/_abc.py
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from agent_harness._contracts import TraceContext, MetricEvent, SpanCategory

class Tracer(ABC):
    """Cross-cutting tracer。所有範疇 ABC 接受 trace_context 並透過 Tracer 開 span。"""

    @abstractmethod
    @asynccontextmanager
    async def start_span(
        self,
        *,
        name: str,
        category: SpanCategory,
        parent: TraceContext | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> AsyncIterator[TraceContext]:
        """
        開啟 span。yield 子 trace_context；退出 context manager 自動 close span。
        attributes 自動 propagate：tenant_id / session_id / user_id / loop_turn。
        """
        ...

    @abstractmethod
    async def record_metric(self, event: MetricEvent) -> None:
        """記錄 metric event。三軸：latency_ms / tokens / cost_usd。"""
        ...

    @abstractmethod
    def get_current_context(self) -> TraceContext:
        """取得當前 trace context（給跨 worker / SSE 透傳用）。"""
        ...
```

#### TraceContext（single-source 在 17.md §1.1）

```python
@dataclass(frozen=True)
class TraceContext:
    """W3C TraceContext-compatible。可與 OTel SpanContext 互轉。"""
    trace_id: str           # 16 bytes hex
    span_id: str            # 8 bytes hex
    parent_span_id: str | None
    flags: int = 0          # sampled / debug
    baggage: dict[str, str] = field(default_factory=dict)  # cross-cutting attrs
```

#### MetricEvent

```python
@dataclass
class MetricEvent:
    """三軸 metric。emit 至 OTel Meter，可 aggregate 為 Prometheus。"""
    name: str                            # e.g. "agent.loop.duration_ms"
    metric_type: Literal["counter", "histogram", "gauge"]
    value: float
    attributes: dict[str, str]           # tenant_id / category / model_name / ...
    timestamp: datetime
```

#### 標準 metric 集（Phase 49.4 起 emit）

| Metric 名稱 | 類型 | 對象 | 用途 |
|------------|------|------|------|
| `agent.loop.duration_ms` | histogram | per loop | p95 SLO |
| `agent.loop.turns` | histogram | per loop | 平均 turn 數 |
| `agent.tokens.input` | counter | per LLM call | cost 累積 |
| `agent.tokens.output` | counter | per LLM call | cost 累積 |
| `agent.tokens.cached` | counter | per LLM call | cache hit 率 |
| `agent.tool.duration_ms` | histogram | per tool | tool p95 |
| `agent.tool.errors` | counter | per tool | 錯誤率 |
| `agent.cost.usd` | counter | per LLM call | tenant 計費 |
| `agent.guardrail.triggered` | counter | per guardrail | 安全事件 |
| `agent.hitl.pending` | gauge | tenant | 等待中審批 |
| `agent.subagent.spawned` | counter | per loop | subagent 使用率 |
| `agent.checkpoint.duration_ms` | histogram | per checkpoint | 持久化效能 |

#### Cross-Cutting 滲透規則

範疇 12 是**橫切關注點（cross-cutting concern）**，不寫進 5 層架構的單一層；它**滲透所有範疇**：

```
所有範疇的 ABC 都接受 trace_context: TraceContext 參數
  ↓
範疇 12 Tracer.start_span() 在每個 ABC 入口呼叫
  ↓
所有 LoopEvent 都附 trace_id / span_id（範疇 1 規範）
  ↓
SSE / OTel collector 端 reconstruction 完整 trace tree
```

> **重要**：範疇 12 spec 只定義 Tracer ABC + MetricEvent 格式 + 標準 metric 集。**不在每個範疇 spec 重複描述如何 emit**。各範疇只需確保：
> 1. ABC 接 `trace_context`
> 2. 進入 / 離開 ABC 用 `tracer.start_span()`
> 3. 關鍵事件呼叫 `tracer.record_metric()`

#### Adapter 整合

| 後端 | Owner |
|------|-------|
| OTel SDK + Jaeger | `adapters/observability/otel/` |
| LangSmith | `adapters/observability/langsmith/`（可選） |
| Datadog APM | `adapters/observability/datadog/`（可選） |

**Phase 49.4 必裝 OTel + Jaeger**；其他可選。

### 驗收標準

#### 結構驗收
- [ ] `Tracer` ABC 在 `agent_harness/observability/_abc.py`
- [ ] `TraceContext` / `MetricEvent` 在 `agent_harness/_contracts/observability.py`
- [ ] 11 個 SpanCategory 全部覆蓋
- [ ] OTel adapter（`adapters/observability/otel/`）通過整合測試

#### Coverage 驗收（Phase 50.2 起強制）
- [ ] **100% turn 有對應 OTel span**（自動驗證 lint）
- [ ] **100% LLM call 有 token + cost metric**
- [ ] **100% tool execution 有 latency + error metric**
- [ ] HITL pause/resume span 連續（沒有 gap）
- [ ] Subagent span 與父 loop span 透過 parent_span_id 連接

#### SLO 量化驗收
- [ ] Tracer overhead < 5% latency（與 disable tracer 對比）
- [ ] Metric emit p95 < 1ms
- [ ] Trace context propagation 跨 worker queue 正確（測試案例：父 agent → Celery worker → subagent）

#### 範疇間整合驗收
- [ ] 12 個範疇（11 + 12）的 ABC 都接 `trace_context: TraceContext` 參數
- [ ] LoopEvent 自動帶 `trace_id`（範疇 1 規範）
- [ ] HITL ApprovalRequest 帶 trace_context（人工審批可查 trace）

---

## §HITL 中央化（Cross-Range Centralization）

> **新增理由（2026-04-28 review）**：HITL 機制原本散落在範疇 2（`request_approval` tool）/ 範疇 7（`pending_approvals` in state）/ 範疇 8（HITL recoverable error）/ 範疇 9（HITL guardrail action），缺中央定義。本章節為 **single-source**，各範疇只引用、不重新定義。

### 統一架構

```
                ┌──────────────────────────────────┐
                │        HITLManager (ABC)         │
                │  Owner: 本章節 (single-source)   │
                └──────────────┬───────────────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
       ▼                       ▼                       ▼
┌──────────────┐      ┌──────────────────┐    ┌──────────────────┐
│ 範疇 2       │      │ 範疇 9           │    │ 範疇 7           │
│ Tools:       │      │ Guardrail:       │    │ State:           │
│ request_     │      │ HIGH risk →      │    │ pending_         │
│ approval     │      │ require approval │    │ approval_ids[]   │
│ (caller)     │      │ (caller)         │    │ (storage)        │
└──────────────┘      └──────────────────┘    └──────────────────┘
       │                       │                       │
       └───────────────────────▼───────────────────────┘
            DurableState.pending_approval_ids
              ↓
            DB-backed approvals 表（cross-session）
              ↓
            HITLDecisionReducer 把 ApprovalDecision merge 回 LoopState
```

### Dataclass（Owner: 本章節 / single-source 在 17.md §1.1）

```python
@dataclass
class ApprovalRequest:
    request_id: UUID
    tenant_id: UUID
    session_id: UUID                    # 觸發審批的 session
    requester: Literal["tools","guardrails","verification","subagent"]
    risk_level: Literal["LOW","MEDIUM","HIGH","CRITICAL"]
    payload: dict                       # 審批內容（含工具 args / 待傳訊息等）
    sla_deadline: datetime              # SLA：超時自動 escalate
    context_snapshot: dict              # 給 reviewer 的上下文（messages 摘要 / tools used 等）
    trace_context: TraceContext         # 範疇 12 propagation
    created_at: datetime


@dataclass
class ApprovalDecision:
    request_id: UUID
    decision: Literal["APPROVED","REJECTED","ESCALATED"]
    reviewer: str                       # user_id 或 service principal
    reason: Optional[str]
    decided_at: datetime
    expires_at: Optional[datetime]      # one-shot 還是 ask_once 後可重用


@dataclass
class HITLPolicy:
    """ToolSpec / Guardrail 配置 HITL 行為。"""
    mode: Literal["auto","ask_once","always_ask"]
    risk_threshold: Literal["LOW","MEDIUM","HIGH","CRITICAL"] = "MEDIUM"
    sla_seconds: int = 14_400           # 預設 4h
    fallback_on_timeout: Literal["reject","escalate","approve_with_audit"] = "escalate"
```

### HITLManager ABC

```python
class HITLManager(ABC):
    """中央 HITL 入口。範疇 2 / 9 為 caller，範疇 7 為 storage，範疇 8 不直接 own。"""

    @abstractmethod
    async def request_approval(
        self,
        req: ApprovalRequest,
    ) -> UUID:
        """提交審批 → 寫入 DB approvals 表 → emit ApprovalRequested event → 通知 reviewer（Teams / UI）。
        回傳 request_id；caller 透過 wait_for_decision 阻塞或加入 LoopState pending list。"""

    @abstractmethod
    async def wait_for_decision(
        self,
        request_id: UUID,
        timeout_s: int,
    ) -> ApprovalDecision:
        """阻塞等待決策；超過 timeout 觸發 fallback_on_timeout 政策。"""

    @abstractmethod
    async def get_pending(self, tenant_id: UUID) -> list[ApprovalRequest]:
        """列出 tenant 待處理審批（給 governance frontend）。"""

    @abstractmethod
    async def decide(
        self,
        request_id: UUID,
        decision: ApprovalDecision,
    ) -> None:
        """reviewer 透過 governance frontend 提交決策；觸發 HITLDecisionReducer 回流到 LoopState。"""
```

### 跨範疇互動規則

| 範疇 | 角色 | 關鍵互動 |
|------|------|---------|
| 範疇 2 (Tools) | **Caller** | 工具 `is_mutating=True` 或 `hitl_policy.mode != "auto"` 時呼叫 `request_approval()` |
| 範疇 9 (Guardrails) | **Caller** | Guardrail check 結果為 `escalate` 時呼叫 `request_approval()` |
| 範疇 7 (State) | **Storage** | `DurableState.pending_approval_ids: list[UUID]` 引用 approvals 表 |
| 範疇 8 (Error) | **不直接 own** | 只把 HITL pending 視為「LLM-recoverable resumable wait」 |
| 範疇 1 (Loop) | **Pause / Resume** | HITL 觸發時 yield `ApprovalRequested` event；外部 worker 看到 ApprovalDecision 後 trigger resume |
| 範疇 12 (Observability) | **Propagation** | ApprovalRequest / Decision 帶 `trace_context`，整段 HITL 等待是一個 OTel span |

### Resume 機制（與範疇 7 Reducer 對接）

```
HITL 觸發
  ↓
ApprovalRequest 寫入 DB → DurableState.pending_approval_ids 加入新 UUID
  ↓
Loop 退出當前 turn，emit ApprovalRequested event
  ↓
Worker 收到 SSE / Teams 通知 → reviewer 在 governance frontend 決策
  ↓
HITLManager.decide() → ApprovalDecision 寫入 DB
  ↓
背景 watcher 偵測到 decision → 觸發 Loop resume worker
  ↓
HITLDecisionReducer.merge() 把 decision 轉成 user message 注入 messages
  ↓
從 last checkpoint 用 Reducer 重組 LoopState → Loop 繼續執行
```

### Frontend 整合

| Frontend 頁面 | 對應 API | 範疇 |
|------------|---------|------|
| `pages/governance/approvals/` | `GET /api/v1/governance/approvals` | HITLManager.get_pending |
| Approval detail modal | `POST /api/v1/governance/approvals/{id}/decide` | HITLManager.decide |
| Inline chat approval card | SSE `ApprovalRequested` event | 範疇 1 emit |

### 驗收標準

#### 結構驗收
- [ ] `HITLManager` ABC 在 `agent_harness/_contracts/hitl.py` 與 `agent_harness/hitl/_abc.py`
- [ ] `ApprovalRequest` / `ApprovalDecision` / `HITLPolicy` dataclass 完整
- [ ] **散落 4 個範疇的 HITL 引用全部改為 `HITLManager` 統一入口**
- [ ] `HITLDecisionReducer` 與範疇 7 整合
- [ ] DB approvals 表（schema 見 09.md）

#### Cross-session 驗收
- [ ] HITL pause 4 小時後仍可 resume（不依賴 in-memory state）
- [ ] Multi-instance 部署時，任一 worker 都能 pickup pending approval
- [ ] timeout fallback 3 種政策正確（reject / escalate / approve_with_audit）

#### 多租戶 / 安全驗收
- [ ] Tenant A reviewer 看不到 tenant B 的 pending
- [ ] 高風險審批（HIGH / CRITICAL）強制 multi-reviewer

#### SLO 量化驗收
- [ ] Approval submit p95 < 200ms
- [ ] Resume p95 < 3s（含 reducer + checkpoint load）
- [ ] HITL throughput：1000 pending / tenant 不影響 list API

---

## 範疇間依賴關係圖

```
                    ┌──────────────────────────────────┐
                    │ Range 1: Orchestrator Loop (TAO) │ ← 中樞
                    └─┬────┬────┬────┬────┬────┬──────┘
                      │    │    │    │    │    │
        ┌─────────────┘    │    │    │    │    └───────────┐
        ↓                  ↓    ↓    ↓    ↓                ↓
   [5: Prompt]      [6: Output]  │ [7: State]      [11: Subagent]
   Construction     Parsing       │  Mgmt
                                  │
                    ┌─────────────┼─────────────┐
                    ↓             ↓             ↓
              [2: Tools]    [3: Memory]   [4: Context Mgmt]
                    │             │             │
                    └─────────────┼─────────────┘
                                  │
                         ┌────────┼────────┐
                         ↓        ↓        ↓
                    [8: Error] [9: Guardrails] [10: Verification]
                         全程跨切面
                                  │
                                  ↓
                  ╔════════════════════════════════════╗
                  ║ [12: Observability]                ║
                  ║ Cross-cutting — 滲透所有 11 範疇    ║
                  ║ TraceContext + MetricEvent + Span  ║
                  ╚════════════════════════════════════╝
```

### 依賴前置順序
1. 先做：範疇 1（Loop） + 範疇 6（Output Parsing） — **基礎**
2. 再做：範疇 2（Tools） + 範疇 5（Prompt Construction） — **入口**
3. 再做：範疇 3（Memory） + 範疇 4（Context Mgmt） — **能力**
4. 再做：範疇 7（State） + 範疇 8（Error） — **健壯**
5. 再做：範疇 9（Guardrails） + 範疇 10（Verification） — **安全**
6. 最後：範疇 11（Subagent） — **進階**
7. **横切**：範疇 12（Observability） — Phase 49.4 起**所有範疇 ABC 必接 trace_context**，不單獨 phase

---

## 範疇成熟度評分系統

每個範疇用 5 級評分追蹤：

| Level | 真實 % | 含義 |
|-------|-------|------|
| 0 | 0% | 完全沒實作 |
| 1 | 10-20% | 代碼存在但未接入主流量 |
| 2 | 25-40% | 已接入但未測試 |
| 3 | 45-65% | 接入且基本測試 |
| 4 | 70-85% | 主流量運行 + 測試 + 缺部分業界特性 |
| 5 | 90-100% | 完整對齊業界最佳實踐 |

V2 目標：**所有範疇至少達 Level 4（70%+）**。

---

## 下一步

確認 11 範疇規格後，下一步：
- `02-architecture-design.md`：將 11 範疇映射到具體目錄結構與 API
- `06-phase-roadmap.md`：規劃 Phase 49-55 各 Sprint 對應哪些範疇
