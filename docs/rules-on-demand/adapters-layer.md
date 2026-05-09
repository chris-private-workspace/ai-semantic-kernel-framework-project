# Adapter 層設計準則 + LLM Provider 上架 SOP

**Purpose**: 定義 `backend/src/adapters/` 層 ABC 設計、LLM provider 中立性實作、新 provider 上架流程、Azure OpenAI 細節保留。

**Category**: Framework / Architecture
**Created**: 2026-04-28
**Last Modified**: 2026-04-28
**Status**: Active

**Modification History**:
- 2026-04-28: New rule absorbing agent-framework.md (V1 MAF 已淘汰) + azure-openai-api.md（核心邏輯抽出，Azure 細節保留）

---

## 核心概念

**Adapter 層**是 Agent Harness（11 範疇）與具體 LLM 供應商之間的**唯一隔離層**。所有 LLM SDK（openai / anthropic）import 禁止跨出此層（強制規則見 `llm-provider-neutrality.md`）。

```
┌─────────────────────────────┐
│  Agent Harness（1-12 範疇）   │ ← 禁止 import LLM SDK
│  （ChatClient ABC 使用者）    │
└──────────────┬──────────────┘
               ↓ ChatClient ABC 介面
┌──────────────────────────────┐
│       Adapter Layer           │
├──────────────────────────────┤
│ ✓ azure_openai/               │
│ ✓ anthropic/（Phase 50+）     │
│ ✓ openai/（Phase 50+）        │
└──────────────────────────────┘
```

---

## 目錄結構

```
backend/src/adapters/
├── _base/
│   ├── __init__.py
│   ├── chat_client.py         # ChatClient ABC（owner: 原則 2）
│   ├── types.py               # Message / ToolSpec / ChatResponse / StopReason 中性型別
│   ├── pricing.py             # PricingInfo dataclass
│   └── router.py              # ProviderRouter ABC（Phase 50+）
├── azure_openai/
│   ├── __init__.py
│   ├── adapter.py             # AzureOpenAIAdapter 實作
│   ├── config.py              # endpoint / api_version / deployment 配置
│   ├── error_mapper.py        # Provider native error → ProviderError 映射
│   ├── tool_converter.py      # ToolSpec → Azure function calling 轉換
│   └── tests/
│       ├── conftest.py
│       ├── test_contract.py   # Contract test（每個 adapter 必通）
│       ├── test_token_counting.py
│       └── test_pricing.py
├── anthropic/                  # Phase 50+
├── openai/                     # Phase 50+
└── _testing/
    ├── conftest.py
    ├── mock_clients.py
    └── contract_test_base.py
```

---

## ABC 設計 5 大原則

### 1. 純抽象，不實作細節

```python
# ✅ 正確：純抽象方法
class ChatClient(ABC):
    @abstractmethod
    async def chat(self, *, messages, tools, ...) -> ChatResponse:
        """各供應商實作自己的邏輯，不在 ABC 有預設實作。"""
        ...

# ❌ 錯誤：ABC 有預設實作邏輯
class ChatClient(ABC):
    async def chat(self, ...):
        converted_tools = self._convert_tools(tools)  # 違反純抽象
        return await self._do_chat(converted_tools)
```

### 2. 中性型別，不依賴 LLM SDK

所有 dataclass（Message / ToolSpec / ChatResponse / StopReason）定義在 `_base/types.py`，中立於任何供應商格式。

### 3. 異步優先（async/await）

所有 I/O 操作（LLM call / token counting）強制 async。禁止 sync adapter。

### 4. 顯式 cancellation 支援

Adapter 必須支援 `asyncio.CancelledError` 正確釋放資源。

```python
@abstractmethod
async def chat(self, ..., trace_context: TraceContext | None = None) -> ChatResponse:
    try:
        return await self._do_chat_internal(...)
    except asyncio.CancelledError:
        await self._cleanup()  # cancel in-flight request, close stream
        raise
```

### 5. Tracing Context 強制注入

所有 ABC 方法簽名必須接受 `trace_context: TraceContext | None`（範疇 12 cross-cutting）。

---

## 新 Provider 上架 SOP（5 步）

### Step 1：建目錄 + 骨架

```bash
mkdir -p backend/src/adapters/{provider_name}/{tests}
touch backend/src/adapters/{provider_name}/{__init__,adapter,config,error_mapper,tool_converter}.py
```

### Step 2：實作 ChatClient ABC

```python
# backend/src/adapters/{provider}/adapter.py
from agent_harness._contracts import (
    ChatClient, Message, ToolSpec, ChatResponse, TraceContext, StopReason
)

class ProviderAdapter(ChatClient):
    def __init__(self, api_key: str, model: str, **config):
        self.api_key = api_key
        self.model = model
        self.config = config

    async def chat(
        self,
        *,
        messages: list[Message],
        tools: list[ToolSpec],
        trace_context: TraceContext | None = None,
    ) -> ChatResponse:
        # 1. 轉換 Message → provider format
        native_messages = self._convert_messages(messages)
        # 2. 轉換 ToolSpec → provider tool schema
        native_tools = self._convert_tools(tools) if tools else None
        # 3. 呼叫 provider API
        response = await self._call_provider_api(native_messages, native_tools, trace_context)
        # 4. 轉換 response → 中性 ChatResponse
        return self._convert_response(response)

    async def count_tokens(self, *, messages, tools=None) -> int:
        """用 provider 官方 tokenizer（tiktoken / claude-tokenizer）計算。"""
        ...

    def get_pricing(self) -> PricingInfo: ...
    def supports_feature(self, feature: str) -> bool: ...
    def model_info(self) -> ModelInfo: ...
```

### Step 3：寫 Contract Test

```python
# backend/src/adapters/{provider}/tests/test_contract.py
class TestProviderAdapterContract:
    """每個 adapter 必須通過的契約測試。"""

    @pytest.mark.asyncio
    async def test_chat_basic(self, adapter):
        response = await adapter.chat(
            messages=[Message(role="user", content="What is 2+2?")],
            tools=[],
        )
        assert isinstance(response, ChatResponse)
        assert response.stop_reason in [StopReason.END_TURN, StopReason.MAX_TOKENS]

    @pytest.mark.asyncio
    async def test_tool_calling(self, adapter): ...

    @pytest.mark.asyncio
    async def test_count_tokens(self, adapter):
        count = await adapter.count_tokens(messages=[...])
        assert count > 0

    @pytest.mark.asyncio
    async def test_pricing_info(self, adapter):
        info = adapter.get_pricing()
        assert info.input_per_million > 0

    @pytest.mark.asyncio
    async def test_cancellation(self, adapter):
        """Cancellation 必須正確釋放資源。"""
        try:
            await asyncio.wait_for(adapter.chat(messages=[...], tools=[]), timeout=0.001)
        except asyncio.TimeoutError:
            pass
```

### Step 4：註冊到 ProviderRouter config

```yaml
# providers.yaml
providers:
  azure_openai:
    enabled: true
    default: true
    adapter_class: AzureOpenAIAdapter
    config:
      api_key: ${AZURE_OPENAI_API_KEY}
      endpoint: ${AZURE_OPENAI_ENDPOINT}
      api_version: "2024-02-15-preview"
      deployment_name: ${AZURE_OPENAI_DEPLOYMENT}
  anthropic:
    enabled: false  # Phase 50+
    config: ...

routing_rules:
  - intent: cheap
    providers: [openai, azure_openai]
  - intent: quality
    providers: [anthropic, azure_openai]
  - intent: compliance_strict
    providers: [azure_openai]
```

### Step 5：加 CI matrix + 測試

```yaml
# .github/workflows/adapter-test.yml
on: [pull_request]
jobs:
  adapter-contract-tests:
    strategy:
      matrix:
        provider: [azure_openai, anthropic, openai]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pytest backend/src/adapters/${{ matrix.provider }}/tests/test_contract.py
```

---

## Azure OpenAI 特定細節

### Endpoint 與 API Version

```python
# ✅ 正確格式
endpoint = "https://<resource-name>.openai.azure.com/"
api_version = "2024-02-15-preview"  # 或最新穩定版

# ❌ 常見錯誤
endpoint = "https://openai.azure.com/"  # 缺 resource name
api_version = "latest"  # Azure 不支援
```

### Deployment Name vs Model Name

Azure OpenAI 區分**部署名稱**（租戶自定）和**模型名稱**（Microsoft 官方）：

```python
deployment_name = "gpt-5-4-deployment"  # 租戶自定
model_name = "gpt-5.4"                  # Microsoft 官方

# API 呼叫時用 deployment
client.chat.completions.create(
    model=deployment_name,  # ← deployment，非 model
    messages=[...],
)
```

### Tool Calling 格式對應

Azure OpenAI 使用 OpenAI 函式呼叫格式：

```python
# V2 ToolSpec → Azure 格式
azure_tool = {
    "type": "function",
    "function": {
        "name": tool_spec.name,
        "description": tool_spec.description,
        "parameters": tool_spec.input_schema,
    },
}
```

### 限速 / Retry / Timeout 建議值

```python
AZURE_OPENAI_CONFIG = {
    "timeout": 30,                    # 秒
    "max_retries": 2,
    "retry_backoff_factor": 1.5,
    "rate_limit_rpm": 60,
    "rate_limit_tpm": 90_000,
    "circuit_breaker_threshold": 5,
    "circuit_breaker_timeout": 60,
}
```

---

## 錯誤映射表

所有 provider native error 必須映射到統一的 `ProviderError` enum（範疇 8 依賴）：

```python
class ProviderError(Enum):
    """single-source owner: 原則 2。"""
    AUTH_FAILED = "auth_failed"                   # 401 / 403
    RATE_LIMITED = "rate_limited"                 # 429
    QUOTA_EXCEEDED = "quota_exceeded"             # quota 用盡
    MODEL_UNAVAILABLE = "model_unavailable"       # 模型暫停
    CONTEXT_WINDOW_EXCEEDED = "context_too_long"  # input 太長
    INVALID_REQUEST = "invalid_request"           # 參數錯誤
    TIMEOUT = "timeout"                           # 超時
    SERVICE_UNAVAILABLE = "service_unavailable"   # 5xx
    UNKNOWN = "unknown"                           # 其他

class AzureOpenAIErrorMapper:
    @staticmethod
    def map(azure_error: Exception) -> ProviderError:
        if isinstance(azure_error, AuthenticationError):
            return ProviderError.AUTH_FAILED
        elif "quota" in str(azure_error).lower():
            return ProviderError.QUOTA_EXCEEDED
        elif getattr(azure_error, "status_code", None) == 429:
            return ProviderError.RATE_LIMITED
        else:
            return ProviderError.UNKNOWN
```

---

## Adapter 測試策略

### Contract Test（每個 adapter 必通）

驗證 adapter 遵守 ChatClient ABC 契約。見上方 Step 3。

### Mock Provider for Unit Test

```python
# backend/src/adapters/_testing/mock_clients.py
class MockChatClient(ChatClient):
    """完整實作 ChatClient ABC，用於 agent_harness 單元測試。"""

    def __init__(self, responses: dict | None = None):
        self.responses = responses or {}

    async def chat(self, *, messages, tools, **kwargs) -> ChatResponse:
        return ChatResponse(
            content="mock response",
            stop_reason=StopReason.END_TURN,
            ...
        )

    async def count_tokens(self, *, messages, tools=None) -> int:
        return 100  # 硬編值
```

### Real Provider Integration Test (CI optional, manual trigger)

```bash
pytest backend/src/adapters/azure_openai/tests/test_integration.py \
  -m "integration and not slow" \
  --provider-api-key=$AZURE_OPENAI_API_KEY
```

---

## 禁止項

| 禁止行為 | 理由 | 替代 |
|--------|------|------|
| 在 adapter 內做業務邏輯（如 tenant 過濾） | adapter 只負責 LLM 通信 | 業務邏輯在範疇 1-11 |
| 跨 adapter 共用 helper（如 shared token counter） | 增加耦合 | 每個 adapter 獨立實作 |
| 靜默 fallback（A fail → 自動試 B） | 隱瞞失敗 | 失敗 propagate 讓範疇 8 決策 |
| 在 adapter 層快取 LLM 回應 | 違反單一職責 | 快取在範疇 4 |

---

## Config 範例（providers.yaml）

```yaml
# backend/config/providers.yaml
version: "1.0"
default_provider: azure_openai

providers:
  azure_openai:
    enabled: true
    adapter_class: AzureOpenAIAdapter
    config:
      api_key: ${AZURE_OPENAI_API_KEY}
      endpoint: ${AZURE_OPENAI_ENDPOINT}
      api_version: "2024-02-15-preview"
      deployment_name: ${AZURE_OPENAI_DEPLOYMENT}
      model: "gpt-5.4"
      timeout_sec: 30
      max_retries: 2
      supports_vision: true
      supports_caching: true
      supports_thinking: false
      rpm_limit: 60
      tpm_limit: 90_000
      pricing:
        input_per_million: 0.0015
        output_per_million: 0.0075
        cached_input_per_million: 0.00045

  anthropic:
    enabled: false  # Phase 50+
    adapter_class: AnthropicAdapter
    config:
      api_key: ${ANTHROPIC_API_KEY}
      model: "claude-3.7-sonnet-20250219"
      supports_thinking: true
      pricing:
        input_per_million: 0.003
        output_per_million: 0.015
        cached_input_per_million: 0.0009

router:
  intent_mappings:
    cheap: [openai, azure_openai]
    balanced: [azure_openai]
    quality: [anthropic, azure_openai]
    compliance_strict: [azure_openai]
  fallback_chain: [azure_openai]
```

---

## 引用

- **10-server-side-philosophy.md** §原則 2 LLM Provider Neutrality
- **07-tech-stack-decisions.md** — 技術選型
- **17-cross-category-interfaces.md** §2.1 ChatClient ABC
- **01-eleven-categories-spec.md** §範疇 8 Error Handling / §範疇 12 Observability
- **llm-provider-neutrality.md** — 強制規則
- **category-boundaries.md** — adapter 與 agent_harness 分界

---

**所有 adapter 層開發必須遵守本規則。違反時 PR review 拒絕。**
