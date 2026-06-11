# Sprint 151: Foundation — AnthropicChatClient + Registry + Selector + build() 修復

## Sprint 目標

1. 修復 MagenticBuilderAdapter.build() 正確轉發 manager 配置到官方 API
2. 建立 AnthropicChatClient（BaseChatClient 實作）
3. 建立 ManagerModelRegistry（YAML 載入 + Agent 工廠）
4. 建立 ManagerModelSelector（風險等級 → 模型選擇）
5. 建立 config/manager_models.yaml 配置檔

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 44 — Magentic Orchestrator Agent |
| **Sprint** | 151 |
| **Story Points** | 9 點 |
| **狀態** | 📋 計劃中 |

## User Stories

### S151-1: 修復 MagenticBuilderAdapter.build() 傳遞 manager_agent (2 SP)

**作為** 平台開發者
**我希望** MagenticBuilderAdapter.build() 正確將 manager 配置傳遞給官方 MagenticBuilder API
**以便** 後續注入自定義 Manager Agent 時能被官方 API 正確使用

**技術規格**:

> **PoC 驗證結果**: RC4 安裝版的 `MagenticBuilder` **沒有** `with_standard_manager()` 方法。
> Manager 注入是透過構造函數的 `manager_agent=` 參數。

**改動 1: `backend/src/integrations/agent_framework/builders/magentic.py` — build() 方法修復**

現有問題（第 1286-1293 行）：
```python
# 現有代碼 — manager 配置被忽略
self._builder = MagenticBuilder(participants=participant_agents)
workflow = self._builder.build()  # ← 構造時沒有傳 manager_agent
```

修復後（PoC 驗證的正確方式）：
```python
# 構造 MagenticBuilder 時直接傳入 manager_agent
self._builder = MagenticBuilder(
    participants=participant_agents,
    manager_agent=self._manager,          # ← 構造函數注入
    max_stall_count=self._max_stall_count,
    max_round_count=self._max_round_count,
    enable_plan_review=self._enable_plan_review,
)
workflow = self._builder.build()
```

**驗收標準**:
- `MagenticBuilder(participants=..., manager_agent=...)` 構造成功
- 現有 E2E 測試全部通過（確認修復不破壞已有功能）
- 自定義 manager 透過 `with_manager()` 設定後，build() 時正確傳遞到構造函數

### S151-2: AnthropicChatClient — MAF ChatClient 實作 (3 SP)

**作為** 平台開發者
**我希望** 有一個 AnthropicChatClient 實作 MAF 的 BaseChatClient 介面
**以便** 可以把 Claude 模型注入到 MagenticBuilder 的 Manager Agent

**技術規格**:

**新增: `backend/src/integrations/agent_framework/clients/anthropic_chat_client.py` (~150 LOC)**

核心實作（PoC 實際代碼驗證）：
```python
from agent_framework import (
    BaseChatClient, ChatResponse, ChatResponseUpdate, Content, Message, ResponseStream,
)
from anthropic import AsyncAnthropic

class AnthropicChatClient(BaseChatClient):
    def __init__(self, *, model, api_key=None, thinking_config=None, max_tokens=16000, **kwargs):
        super().__init__(**kwargs)  # MUST call super
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model
        self._thinking_config = thinking_config
        self._max_tokens = max_tokens

    # ONE method, NOT async — stream param decides return type
    def _inner_get_response(self, *, messages, stream, options, **kwargs):
        if stream:
            return self._build_response_stream(self._stream_anthropic(messages, options))
        else:
            return self._call_anthropic(messages, options)

    async def _call_anthropic(self, messages, options) -> ChatResponse:
        # MAF Message → Anthropic format → API call → ChatResponse

    async def _stream_anthropic(self, messages, options):
        # Stream → yield ChatResponseUpdate(contents=[Content(type='text', text=chunk)])
```

> **PoC 驗證的關鍵差異（與初始假設不同）**:
> - **一個** abstract method（不是兩個），用 `stream` 參數分流
> - 是 `def`（不是 `async def`）
> - 參數是 `stream: bool` + `options: Mapping`（不是 `chat_options`）
> - `ChatResponseUpdate` 需要 `Content(type='text', text=...)` 包裝
> - `__init__` 必須呼叫 `super().__init__(**kwargs)`
> - 不支持 function calling — 需額外加 `FUNCTION_INVOKING_CHAT_CLIENT_MARKER`

關鍵轉換：
- `_convert_messages()` — MAF Message[] → Anthropic `{"role", "content"}` format
- `_convert_response()` — Anthropic Response → `ChatResponse(messages=[Message(role='assistant', text=...)])`
- Extended Thinking 支援 — 透過 `thinking` 參數（type: enabled, budget_tokens）

**驗收標準**（PoC 已通過）:
- `isinstance(client, BaseChatClient)` ✅
- 簡單 prompt 測試成功（"Respond with OK"）→ 901ms 返回正確 ✅
- Extended Thinking 測試成功（thinking_config 啟用時有 thinking 內容）
- `Agent(client, name="Manager")` 可以成功創建 ✅

### S151-3: ManagerModelRegistry + ManagerModelSelector + YAML 配置 (4 SP)

**作為** 運維人員
**我希望** 透過修改 YAML 檔案即可切換 Manager Agent 的模型
**以便** 不需要改代碼就能調整不同場景使用的模型

**技術規格**:

**新增 1: `backend/config/manager_models.yaml` (~80 LOC)**
- 定義 6 個模型配置（3 Anthropic + 3 Azure OpenAI）
- 定義 4 個選擇策略（max_reasoning / balanced / cost_efficient / fast_cheap）
- 定義預設值和 fallback

**新增 2: `backend/src/integrations/hybrid/orchestrator/manager_model_registry.py` (~120 LOC)**

```python
class ManagerModelRegistry:
    """統一模型注冊表 — 單例"""
    def __init__(self, config_path="config/manager_models.yaml"):
        # 從 YAML 載入模型配置

    def create_manager_agent(self, model_key: str) -> Agent:
        # anthropic → AnthropicChatClient → Agent(client, name=...) (positional first arg)
        # azure_openai → Agent(AzureOpenAIResponsesClient(...), name=...)

    def list_models(self) -> list[dict]:
        # 列出所有可用模型

    def get_default_model(self) -> str:
    def get_fallback_model(self) -> str:
    def get_model_config(self, key: str) -> ModelConfig:
```

支援類別：
- `ModelConfig` — 單個模型配置（provider, model_id, capabilities, cost_tier 等）
- `CostTier` — premium / standard / economy

**新增 3: `backend/src/integrations/hybrid/orchestrator/manager_model_selector.py` (~60 LOC)**

```python
class ManagerModelSelector:
    def select_model(self, risk_level: RiskLevel, complexity="MEDIUM",
                     user_override=None) -> str:
        # 1. user_override 最高優先
        # 2. CRITICAL → max_reasoning → claude-opus-4-6
        # 3. HIGH → balanced → claude-sonnet-4-6
        # 4. MEDIUM → cost_efficient → gpt-4o
        # 5. LOW → fast_cheap → claude-haiku-4-5
        # 6. _is_available() 檢查 → fallback

    def _is_available(self, model_key: str) -> bool:
        # anthropic: ANTHROPIC_API_KEY 存在？
        # azure: AZURE_OPENAI_ENDPOINT 存在？
```

**Import 路徑注意**:
- RiskLevel: `from src.integrations.orchestration.intent_router.models import RiskLevel`
- Agent: `from agent_framework import Agent`

**驗收標準**:
- YAML 載入成功，6 個模型配置正確解析
- `${AZURE_OPENAI_ENDPOINT}` 環境變數正確解析
- `create_manager_agent("claude-sonnet-4-6")` 返回可用的 Agent
- `select_model(RiskLevel.CRITICAL)` → "claude-opus-4-6"
- `select_model(RiskLevel.LOW)` → "claude-haiku-4-5"
- 無 ANTHROPIC_API_KEY 時自動 fallback 到 gpt-4o
- user_override 最高優先
- 單元測試覆蓋所有策略路徑

## 技術注意事項（PoC 已驗證）

### BaseChatClient 介面（已確認 — PoC 實際代碼驗證）

- **一個** abstract method: `def _inner_get_response(*, messages, stream, options, **kwargs)`
  - `stream=False` → 返回 `Awaitable[ChatResponse]`
  - `stream=True` → 返回 `ResponseStream[ChatResponseUpdate, ChatResponse]`
- **不是** async def，是普通 def
- **不是** `chat_options`，是 `stream: bool` + `options: Mapping[str, Any]`
- `__init__` 必須呼叫 `super().__init__(**kwargs)`
- MAF 用 `Message` 不是 `ChatMessage`
- `ChatResponseUpdate` 需要 `contents=[Content(type='text', text=...)]`（不是 `text=`）
- **不支持 function calling** — 需要額外加 `FUNCTION_INVOKING_CHAT_CLIENT_MARKER`

### MagenticBuilder API（已確認）

- `MagenticBuilder(participants=[...], manager_agent=agent)` — 構造函數注入
- **沒有** `with_standard_manager()` 方法
- 只有 3 個公開方法: `build()`, `with_checkpointing()`, `with_plan_review()`
- 其他配置（max_stall_count, ledger prompts 等）全在構造函數

### Agent 構造方式（已確認）

```python
# CORRECT — positional first arg 'client'
agent = Agent(anthropic_client, name="Manager", instructions="...")

# WRONG — no chat_client= keyword
agent = Agent(chat_client=anthropic_client, ...)  # TypeError
```

## 測試策略

| 類型 | 範圍 | 工具 |
|------|------|------|
| 單元測試 | ModelConfig 解析、Selector 策略、ChatClient 格式轉換 | pytest + mock |
| 整合測試 | Registry 載入 YAML → create_manager_agent → Agent 可用 | pytest |
| API 測試 | AnthropicChatClient → Claude API round-trip | pytest + 真實 API |
| 回歸測試 | build() 修復後現有功能不破壞 | 現有 E2E 測試 |

## 依賴

- `anthropic>=0.84.0`（已安裝）
- `agent-framework>=1.0.0rc4`（已安裝）
- `pyyaml`（已安裝）
- 無新依賴

---

**Sprint 151 前置**: Phase 43 完成（Sprint 148-150）
**Story Points**: 9 pts
**核心交付**: AnthropicChatClient + ManagerModelRegistry + ManagerModelSelector + build() 修復
