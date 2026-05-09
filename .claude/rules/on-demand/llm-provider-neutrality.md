# LLM 供應商中性原則

**Purpose**: 確保 `agent_harness/**` 不綁定特定 LLM 供應商，全走 `adapters/_base/` 中性 ABC。

**Category**: Framework / Architecture
**Created**: 2026-04-28
**Last Modified**: 2026-04-28
**Status**: Active

**Modification History**:
- 2026-04-28: Initial creation from 10-server-side-philosophy.md §原則 2

---

## 核心鐵律

**`agent_harness/**` 任何檔案禁止直接 import 任何 LLM 供應商 SDK。**

```python
# ❌ 嚴禁（CI 強制 fail）
from openai import AzureOpenAI
from openai import AsyncAzureOpenAI
from anthropic import Anthropic
import openai
import anthropic
from anthropic import HUMAN_PROMPT, AI_PROMPT

# ✅ 唯一允許方式
from adapters._base.chat_client import ChatClient
from agent_harness._contracts.chat import Message, ToolSpec, ChatResponse
```

---

## 唯一例外：Adapters 層

**只有 `adapters/<provider>/` 目錄內可 import 該供應商 SDK。**

```python
# ✅ 正確：adapters/azure_openai/ 內可 import
# backend/src/adapters/azure_openai/client.py
from openai import AsyncAzureOpenAI

class AzureOpenAIAdapter(ChatClient):
    def __init__(self, endpoint: str, key: str):
        self._client = AsyncAzureOpenAI(api_key=key, azure_endpoint=endpoint)

    async def chat(self, ...) -> ChatResponse: ...
```

---

## 中性介面（from Contract 2 in 17.md）

### ChatClient ABC

所有 LLM 供應商必須實作此 ABC：

```python
class ChatClient(ABC):
    """Owner: 10-server-side-philosophy.md 原則 2; single-source: 17.md §2.1"""

    @abstractmethod
    async def chat(
        self,
        *,
        messages: list[Message],
        tools: list[ToolSpec],
        tool_choice: str = "auto",
        max_tokens: int | None = None,
        temperature: float = 1.0,
        cache_breakpoints: list[CacheBreakpoint] | None = None,
        trace_context: TraceContext | None = None,
        extra_options: dict | None = None,
    ) -> ChatResponse: ...

    @abstractmethod
    async def stream(
        self,
        *,
        messages: list[Message],
        tools: list[ToolSpec],
        **kwargs,
    ) -> AsyncIterator[StreamEvent]: ...

    @abstractmethod
    async def count_tokens(
        self,
        *,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
    ) -> int:
        """per-provider tokenizer（tiktoken / claude-tokenizer / o200k_base）"""
        ...

    @abstractmethod
    def get_pricing(self) -> PricingInfo:
        """USD per 1M tokens（input / output / cached）"""
        ...

    @abstractmethod
    def supports_feature(
        self,
        feature: Literal["thinking", "caching", "vision", "audio", "computer_use", ...],
    ) -> bool: ...

    @abstractmethod
    def model_info(self) -> ModelInfo:
        """model_name / family / provider / context_window / knowledge_cutoff"""
        ...
```

### 中性型別

#### Message

```python
@dataclass
class Message:
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str | list[ContentBlock]
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None
```

#### ToolSpec（工具定義）

```python
@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict  # JSON Schema（中性，非 OpenAI / Anthropic 原生）
    annotations: ToolAnnotations
    concurrency_policy: ConcurrencyPolicy
    version: str
```

#### ChatResponse

```python
@dataclass
class ChatResponse:
    model: str
    content: str | list[ContentBlock]
    tool_calls: list[ToolCall] | None = None
    stop_reason: StopReason
    usage: TokenUsage
```

#### StopReason（統一 enum）

```python
class StopReason(Enum):
    END_TURN = "end_turn"           # 模型自然結束
    TOOL_USE = "tool_use"           # 呼叫工具
    MAX_TOKENS = "max_tokens"       # 達 max_tokens 限制
    STOP_SEQUENCE = "stop_sequence" # 遇到 stop_sequence
    SAFETY_REFUSAL = "safety_refusal"  # 安全政策拒絕
    PROVIDER_ERROR = "provider_error"  # 供應商錯誤
```

**Adapter 負責轉換**：
```python
class AzureOpenAIAdapter(ChatClient):
    def _map_stop_reason(self, openai_reason: str) -> StopReason:
        return {
            "stop": StopReason.END_TURN,
            "tool_calls": StopReason.TOOL_USE,
            "length": StopReason.MAX_TOKENS,
            "content_filter": StopReason.SAFETY_REFUSAL,
        }.get(openai_reason, StopReason.PROVIDER_ERROR)
```

---

## 禁止項清單

### 禁止 1：供應商原生 tool schema

```python
# ❌ 禁止使用 OpenAI function calling 格式
tools = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "...",
            "parameters": {...}
        }
    }
]

# ❌ 禁止使用 Anthropic tools 格式
tools = [
    {
        "name": "search",
        "description": "...",
        "input_schema": {...}
    }
]

# ✅ 正確：使用 V2 中性 ToolSpec
tools = [
    ToolSpec(
        name="search",
        description="...",
        input_schema={...},
        annotations=ToolAnnotations(...),
    )
]
```

### 禁止 2：供應商原生 message format

```python
# ❌ 禁止
messages = [
    {"role": "system", "content": "You are..."},  # OpenAI native
]

# ✅ 正確
from agent_harness._contracts.chat import Message
messages = [
    Message(role="system", content="You are..."),
]
```

### 禁止 3：供應商特定工具呼叫

```python
# ❌ 禁止
if response.tool_calls:
    for tc in response.tool_calls:
        if hasattr(tc, 'function'):  # ← OpenAI 式
            await execute(tc.function.name, tc.function.arguments)

# ✅ 正確
if response.tool_calls:
    for tc in response.tool_calls:
        await execute(tc.name, tc.arguments)
```

### 禁止 4：供應商特定停止條件

```python
# ❌ 禁止
if response.stop_reason == "end_turn":  # Anthropic 字串
    return response

# ✅ 正確
if response.stop_reason == StopReason.END_TURN:  # 中性 enum
    return response
```

---

## 代碼範例對比

### ❌ 反面：直接 import 供應商 SDK

```python
# agent_harness/orchestrator_loop/loop.py
from anthropic import Anthropic

class AgentLoop:
    def __init__(self):
        self.client = Anthropic(api_key="...")

    async def run(self, state: LoopState):
        response = await self.client.messages.create(
            model="claude-3.7-sonnet",
            messages=[{"role": "user", "content": "..."}],
            tools=[{"name": "...", "input_schema": {...}}]
        )
        # 直接用 Anthropic 的 tool_use 物件
        for tc in response.content:
            if tc.type == "tool_use":
                result = await tool_registry.execute(tc.name, tc.input)
```

**問題**：
- 綁定 Anthropic，無法切到 Azure OpenAI
- 工具格式是 Anthropic 原生，換 provider 要改代碼
- 無法支援不同 provider 的 caching 政策

### ✅ 正面：走 ChatClient ABC

```python
# agent_harness/orchestrator_loop/loop.py
from adapters._base.chat_client import ChatClient
from agent_harness._contracts import Message, ToolSpec, ChatResponse, StopReason

class AgentLoop:
    def __init__(self, chat_client: ChatClient):
        self.chat_client = chat_client  # 注入，不綁定特定 provider

    async def run(self, state: LoopState):
        messages = [Message(role="user", content="...")]
        tools = [ToolSpec(name="...", ...)]

        response: ChatResponse = await self.chat_client.chat(
            messages=messages,
            tools=tools,
        )

        if response.stop_reason == StopReason.TOOL_USE:
            for tc in response.tool_calls:
                result = await tool_registry.execute(tc.name, tc.arguments)
                messages.append(Message(role="tool", tool_call_id=tc.id, content=result))
            continue

        return response  # ChatResponse 是中性的
```

**優點**：
- ChatClient 實例由 config / DI 容器注入
- 切換 provider：改 config，不改代碼
- 工具 spec 中性，所有 provider 統一格式

---

## Multi-Provider Routing（進階）

有些場景需要**同時跑多個 provider**，按需求路由：

```python
# adapters/_base/router.py（新增，Phase 50+）
class ProviderRouter(ABC):
    """根據 request 屬性選 provider"""

    @abstractmethod
    async def select(
        self,
        *,
        tenant_id: UUID,
        intent: Literal["cheap", "balanced", "quality", "compliance_strict"],
        required_features: set[str] | None = None,
    ) -> ChatClient: ...

# 使用範例
router = ProviderRouter()

if is_quick_query:
    client = await router.select(tenant_id, intent="cheap")  # → GPT-4o-mini
else:
    client = await router.select(tenant_id, intent="quality")  # → Claude
```

---

## CI Lint 檢查（Phase 49.4+ 強制）

### Lint Rule 1：禁止 LLM SDK 直接 import

```bash
$ grep -r "from openai\|from anthropic\|import openai\|import anthropic" \
  backend/src/agent_harness/ backend/src/business_domain/
# 結果必須為 0（零）

$ grep -r "from openai\|from anthropic" \
  backend/src/adapters/ --include="*.py" \
  | grep -v "adapters/azure_openai\|adapters/anthropic\|adapters/openai"
# 應只出現在指定 provider adapter 目錄
```

### Lint Rule 2：禁止供應商原生 message/tool schema

```bash
$ grep -r '"type".*"function"' backend/src/agent_harness/  # OpenAI schema
# 結果必須為 0

$ grep -r '"name".*"input_schema"' backend/src/agent_harness/ \
  | grep -v "ToolSpec" | grep -v "_contracts"  # Anthropic pattern
# 結果必須為 0
```

### Lint Rule 3：禁止字串比較 stop_reason

```bash
$ grep -r "stop_reason.*==" backend/src/agent_harness/ \
  | grep -E '"end_turn"|"tool_use"|"stop"|"length"'  # 供應商特定字串
# 結果必須為 0；應改用 StopReason enum
```

---

## 驗收標準

### 驗收 1：Provider 切換測試

- [ ] 主流量從 Azure OpenAI 切到 Anthropic（或反向）
- [ ] 只改 config / env var，**不改 `agent_harness/**` 任何代碼**
- [ ] 時間限制：< 2 週完整測試
- [ ] 品質對齊：切換後 1 個月內 verifier pass rate ±5%

### 驗收 2：Dual-Provider 測試

- [ ] 同一 agent loop 在兩家 provider 各跑一遍
- [ ] 結果在**功能上等價**（內容可不同，但邏輯等價）
- [ ] Token count 在 ±10% 內

### 驗收 3：ChatClient ABC 完整性

- [ ] `count_tokens` / `get_pricing` / `supports_feature` / `model_info` 四方法全實作
- [ ] `ModelInfo` / `PricingInfo` / `StopReason` enum 完整
- [ ] 所有 adapter 傳過 contract 驗證測試

### 驗收 4：CI 強制

- [ ] `grep` 檢查 agent_harness 零 SDK import
- [ ] lint rule 1-3 全過
- [ ] PR merge 前必須通過

---

## 為什麼重要

1. **公司現實**：目前只能用 Azure OpenAI，未來可能開放 Claude
2. **議價能力**：不被任一供應商鎖定，可議價
3. **避險**：某供應商出問題（漲價 / 停服 / 政策變動）能無縫切換
4. **對比測試**：同時跑兩家比質量，成本優化
5. **混合路由**：cheap / quality 分流，per-request 動態選 provider，cost-quality 雙贏

---

## 引用

- **10-server-side-philosophy.md** — §原則 2 LLM Provider Neutrality（完整論述）
- **02-architecture-design.md** — §約束 3 Adapter 層強制
- **17-cross-category-interfaces.md** — §2.1 ChatClient ABC / §1.1 Message / ToolSpec / ChatResponse 型別
- **04-anti-patterns.md** — AP-2 Side-Track Code Pollution（禁止 SDK 直接用）
- **CLAUDE.md** — §約束 3 LLM Provider Neutrality

---

**維護責任**：Architect review @ 每個引入新 SDK 的 PR；CI lint 於 Phase 49.4 自動強制。
