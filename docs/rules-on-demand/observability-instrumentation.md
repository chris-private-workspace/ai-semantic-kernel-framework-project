# 觀測性埋點規則（範疇 12 Cross-Cutting）

**Purpose**: 範疇 12（Observability）強制埋點規範；TraceContext 傳遞 + 必埋 metric 集合 + OTel SDK 版本鎖定。

**Category**: Framework / Cross-Cutting (範疇 12)
**Created**: 2026-04-28
**Last Modified**: 2026-04-28
**Status**: Active

**Modification History**:
- 2026-04-28: Initial creation from 01-eleven-categories-spec §範疇 12 + 17-cross-category-interfaces §Contract 12 + 11-test-strategy

---

## 核心原則

**範疇 12 是 cross-cutting concern，不是獨立功能。**

所有其他 11 範疇的執行都必須被觀測。沒有埋點 = 盲人摸象。

```
Agent Harness 11 範疇 → 每個都埋點 → OpenTelemetry SDK
                                    → Jaeger (trace) / Prometheus (metrics) / Loki (logs)
                                    → Grafana Dashboard
```

---

## 必埋點位置 5 處

### 1. Loop 每 Turn 開頭 + 結尾（範疇 1）

```python
# agent_harness/orchestrator_loop/loop.py
class AgentLoop:
    async def run(self, *, messages, tools, ..., trace_context: TraceContext | None = None):
        trace_id = trace_context.trace_id if trace_context else str(uuid4())

        async for turn_num in range(max_turns):
            # ✅ 埋點 1：Turn 開始
            span = tracer.start_span(
                name=f"loop_turn_{turn_num}",
                trace_id=trace_id,
                attributes={"turn": turn_num, "tenant_id": ..., "agent": self.__class__.__name__},
            )

            response = await self.chat_client.chat(
                messages=messages,
                tools=tools,
                trace_context=TraceContext(
                    trace_id=trace_id,
                    span_id=span.span_id,
                    parent_span_id=span.parent_span_id,
                ),
            )

            # ✅ 埋點 2：Turn 結束
            span.record_metric(
                "loop_turn_duration_seconds",
                span.duration_seconds,
                attributes={"status": "success", "stop_reason": response.stop_reason.value},
            )
            span.end()
```

### 2. Tool 執行前後 + 失敗（範疇 2）

```python
class ToolExecutor:
    async def execute(self, tool_call: ToolCall, trace_context: TraceContext) -> ToolResult:
        span = tracer.start_span(
            name=f"tool_{tool_call.tool_name}",
            parent_span_id=trace_context.span_id,
            attributes={"tool": tool_call.tool_name, "trace_id": trace_context.trace_id},
        )

        try:
            result = await self._execute_tool_sandbox(tool_call)
            span.record_metric(
                "tool_execution_duration_seconds",
                span.duration_seconds,
                attributes={"status": "success", "tool": tool_call.tool_name},
            )
            return result
        except Exception as e:
            span.record_metric(
                "tool_execution_duration_seconds",
                span.duration_seconds,
                attributes={"status": "error", "error_type": type(e).__name__},
            )
            span.set_attribute("error.message", str(e))
            span.set_status("ERROR")
            raise
        finally:
            span.end()
```

### 3. LLM 呼叫前後 + Token Usage（Adapters 層）

```python
# backend/src/adapters/azure_openai/adapter.py
class AzureOpenAIAdapter(ChatClient):
    async def chat(self, *, messages, tools, trace_context: TraceContext | None = None):
        trace_context = trace_context or TraceContext.create_root()

        span = tracer.start_span(
            name="llm_chat",
            parent_span_id=trace_context.span_id,
            attributes={"model": self.model, "provider": "azure_openai"},
        )

        try:
            response = await self._call_azure_api(...)

            span.record_metric(
                "llm_chat_duration_seconds",
                span.duration_seconds,
                attributes={"model": self.model, "provider": "azure_openai", "stop_reason": response.stop_reason.value},
            )
            tracer.record_metric(
                "llm_tokens_total",
                response.usage.prompt_tokens,
                attributes={"provider": "azure_openai", "model": self.model, "type": "input"},
            )
            tracer.record_metric(
                "llm_tokens_total",
                response.usage.completion_tokens,
                attributes={"provider": "azure_openai", "model": self.model, "type": "output"},
            )
            return response
        finally:
            span.end()
```

### 4. Verification Pass / Fail（範疇 10）

```python
class Verifier(ABC):
    async def verify(self, output: str, state: LoopState, trace_context: TraceContext) -> VerificationResult:
        span = tracer.start_span(
            name=f"verification_{self.__class__.__name__}",
            parent_span_id=trace_context.span_id,
        )
        try:
            result = await self._verify_internal(output, state)
            tracer.record_metric(
                "verification_pass_rate",
                1.0 if result.passed else 0.0,
                attributes={"verifier_type": self.__class__.__name__, "tenant_id": state.tenant_id},
            )
            return result
        finally:
            span.end()
```

### 5. State Checkpoint Write / Read（範疇 7）

```python
class Checkpointer:
    async def save(self, state: LoopState, trace_context: TraceContext) -> StateSnapshot:
        span = tracer.start_span(
            name="state_checkpoint_save",
            parent_span_id=trace_context.span_id,
        )
        try:
            snapshot = await self._persist_state(state)
            span.record_metric(
                "state_checkpoint_bytes",
                len(snapshot.state_data_json),
                attributes={"version": snapshot.version},
            )
            return snapshot
        finally:
            span.end()
```

---

## TraceContext 傳遞（必須沿鏈，不可斷裂）

```python
@dataclass(frozen=True)
class TraceContext:
    """Owner: 17.md §Contract 12。"""
    trace_id: str                      # 全域唯一，從 API 入口到 subagent
    span_id: str                       # 當前 span
    parent_span_id: str | None = None  # 父 span
    tenant_id: UUID | None = None      # 多租戶追蹤
    user_id: UUID | None = None
    session_id: UUID | None = None

    @classmethod
    def create_root(cls) -> "TraceContext":
        return TraceContext(trace_id=str(uuid4()), span_id=str(uuid4()))

# ✅ 正確：trace_context 沿鏈傳遞
async def api_endpoint(request):
    trace_context = TraceContext.create_root()
    result = await loop.run(messages=..., trace_context=trace_context)
    return result

# Loop 內部建立子 span
async def run(self, ..., trace_context: TraceContext):
    async for event in ...:
        child_span_id = str(uuid4())
        child_context = TraceContext(
            trace_id=trace_context.trace_id,
            span_id=child_span_id,
            parent_span_id=trace_context.span_id,
            tenant_id=trace_context.tenant_id,
        )
        await tool_executor.execute(tc, trace_context=child_context)

# ❌ 禁止：trace_context 斷裂
await tool_executor.execute(tc)  # 沒傳 → 無法關聯
```

### SSE 事件必含 trace_id

```python
@app.get("/api/sessions/{id}/events")
async def stream_events(session_id: UUID):
    trace_context = TraceContext.create_root()

    async def event_generator():
        async for event in loop.run(..., trace_context=trace_context):
            yield f"data: {json.dumps({
                'type': event.type,
                'data': event.data,
                'trace_id': trace_context.trace_id,  # ← 前端用此查日誌
            })}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

---

## Metric 必埋集合（最少 7 個）

| Metric | 類型 | Labels |
|--------|------|--------|
| `agent_loop_duration_seconds` | histogram | tenant_id / outcome / turn_count |
| `tool_execution_duration_seconds` | histogram | tool_name / status |
| `llm_chat_duration_seconds` | histogram | provider / model / stop_reason |
| `llm_tokens_total` | counter | provider / model / type=input/output/cached |
| `verification_pass_rate` | gauge | verifier_type / tenant_id |
| `loop_compaction_count` | counter | tenant_id / reason |
| `loop_subagent_dispatch_count` | counter | mode (fork/teammate/handoff/as_tool) |

---

## OTel SDK 版本鎖定

```python
# requirements.txt — 鎖定具體版本，避免 breaking change
opentelemetry-api==1.22.0
opentelemetry-sdk==1.22.0
opentelemetry-exporter-jaeger==1.22.0
opentelemetry-exporter-prometheus==0.43b0
opentelemetry-exporter-otlp==1.22.0
opentelemetry-instrumentation-fastapi==0.43b0
opentelemetry-instrumentation-sqlalchemy==0.43b0
opentelemetry-instrumentation-redis==0.43b0

# ❌ 禁止 latest / flexible version
# opentelemetry-api>=1.20  ← 可能 breaking
```

---

## Log 規範（結構化 JSON）

```python
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger(__name__)
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

# 使用
logger.info(
    "Tool execution completed",
    extra={
        "timestamp": datetime.utcnow().isoformat(),
        "level": "INFO",
        "trace_id": trace_context.trace_id,
        "tenant_id": state.tenant_id,
        "tool_name": "salesforce_query",
        "duration_ms": 1250,
        "status": "success",
    },
)

# ❌ PII 不入 log
logger.info(f"User {user_email} called tool")  # email 是 PII

# ✅ 脫敏
logger.info("User called tool", extra={"user_hash": sha256(user_email), "tool": "query"})
```

---

## Distributed Tracing 範例

跨範疇呼叫的 span hierarchy：

```
root_trace_id = abc123

├─ span[loop_turn_1]
│  ├─ span[compaction_check]
│  ├─ span[prompt_builder]
│  │  └─ span[memory_search]   ← 範疇 5 呼叫範疇 3
│  └─ span[llm_chat]            ← Adapter 層
│     └─ (Azure OpenAI API，外部)
│
├─ span[loop_turn_2]
│  ├─ span[tool_salesforce_query]
│  │  └─ (Salesforce API，外部)
│  ├─ span[verification_llm_judge]
│  │  └─ span[llm_chat]         ← Judge subagent LLM call
│  └─ (loop evaluates verification)
│
└─ span[state_checkpoint_save]
   └─ (DB persist)
```

每個 span 自動帶：`trace_id`（全局）/ `span_id`（此 span）/ `parent_span_id`（父 span）/ `tenant_id` / `user_id` / `session_id`。

---

## CI 強制：埋點覆蓋率測試

```python
# scripts/check_instrumentation_coverage.py
EXPECTED_METRICS = {
    "01_orchestrator": ["agent_loop_duration_seconds", "loop_turn_duration_seconds"],
    "02_tools": ["tool_execution_duration_seconds"],
    "10_verification": ["verification_pass_rate"],
    # ... 12 範疇
}

def check_category_metrics(category: str):
    implemented = get_implemented_metrics(category)
    required = EXPECTED_METRICS[category]
    missing = set(required) - set(implemented)
    if missing:
        print(f"❌ {category} missing: {missing}")
        sys.exit(1)
    print(f"✅ {category} coverage 100%")

# 在 PR CI 跑
for cat in CATEGORIES:
    check_category_metrics(cat)
```

---

## Dashboard 標準（Grafana）

每個範疇至少有一套 panel：

```
Agent Harness V2 Observability Dashboard

├─ 範疇 1 Loop
│  ├─ Loop duration (p50/p99)
│  ├─ Loop outcome distribution
│  ├─ Turn count distribution
│  └─ Stop reason pie chart
│
├─ 範疇 2 Tools
│  ├─ Tool execution duration by tool_name
│  ├─ Tool success rate (%)
│  ├─ Tool error rate by error_type
│  └─ Top slow tools
│
├─ Adapters (LLM)
│  ├─ LLM call duration by provider
│  ├─ Token usage by provider / model
│  ├─ Provider error rate
│  └─ Cost per 1K tokens (by provider)
│
├─ 範疇 10 Verification
│  ├─ Verification pass rate (%)
│  ├─ Verification duration
│  └─ Self-correction attempt count
│
└─ Alert Rules
   ├─ p99 loop duration > 5min
   ├─ Tool error rate > 10%
   ├─ LLM provider error rate > 5%
   ├─ Verification pass rate < 80%
   └─ Compaction trigger rate > 2x/session
```

---

## 引用

- **01-eleven-categories-spec.md** §範疇 12（Observability）
- **17-cross-category-interfaces.md** §Contract 12 Tracer / TraceContext / MetricEvent
- **11-test-strategy.md** §性能基準目標
- **14-security-deep-dive.md** §Audit Log
- **multi-tenant-data.md** — tenant_id 在 trace 中的傳遞

---

**所有範疇實作必須包含本規則的 5 處埋點。沒有埋點 = 無法觀測 = 無法調整。**
