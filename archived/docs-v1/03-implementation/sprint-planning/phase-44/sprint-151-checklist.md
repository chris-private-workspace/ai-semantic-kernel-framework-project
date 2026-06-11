# Sprint 151 Checklist: Foundation — AnthropicChatClient + Registry + Selector + build() 修復

**Sprint**: 151 | **Phase**: 44 | **Story Points**: 9
**Plan**: [sprint-151-plan.md](./sprint-151-plan.md)

---

## S151-1: 修復 MagenticBuilderAdapter.build() 傳遞 manager_agent (2 SP)

> PoC 驗證：RC4 的 MagenticBuilder **沒有** `with_standard_manager()`，
> Manager 注入是構造函數的 `manager_agent=` 參數。

### build() 修復
- [ ] 修改 `build()` 中 `MagenticBuilder()` 構造，加入 `manager_agent=self._manager`
- [ ] 傳遞 `max_stall_count` 到構造函數
- [ ] 傳遞 `max_round_count` 到構造函數
- [ ] 傳遞 `enable_plan_review` 到構造函數
- [ ] 保留現有 fallback 邏輯（官方 API 失敗時降級到內部實現）
- [ ] 記錄現有 E2E 測試結果作為回歸基線

### 回歸驗證
- [ ] 現有 E2E 測試通過（build() 修復前後行為一致）
- [ ] `with_manager()` 設定的自定義 manager 在 build() 時正確傳遞到構造函數
- [ ] 不設 manager 時預設行為不變

---

## S151-2: AnthropicChatClient — MAF ChatClient 實作 (3 SP)

### BaseChatClient 介面（PoC 實際代碼驗證）
- [x] **一個** abstract method: `def _inner_get_response(*, messages, stream, options, **kwargs)`
- [x] `stream=False` → `Awaitable[ChatResponse]`，`stream=True` → `ResponseStream`
- [x] 是普通 `def`（不是 `async def`）
- [x] 參數是 `stream: bool` + `options: Mapping`（不是 `chat_options`）
- [x] `__init__` 必須呼叫 `super().__init__(**kwargs)`
- [x] MAF 用 `Message` 不是 `ChatMessage`
- [x] `ChatResponseUpdate` 需要 `contents=[Content(type='text', text=...)]`

### AnthropicChatClient 實作
- [ ] 建立 `backend/src/integrations/agent_framework/clients/` 目錄
- [ ] 建立 `anthropic_chat_client.py`（PoC worktree 版本可直接複製）
- [ ] 實作 `__init__(*, model, api_key, thinking_config, max_tokens, **kwargs)` + `super().__init__(**kwargs)`
- [ ] 實作 `_inner_get_response(*, messages, stream, options)` — 根據 stream 分流
- [ ] 實作 `_call_anthropic()` — non-streaming path
- [ ] 實作 `_stream_anthropic()` — streaming path，用 `_build_response_stream()` 包裝
- [ ] 加入 function calling 支持（`FUNCTION_INVOKING_CHAT_CLIENT_MARKER` + tools 轉換）

### 格式轉換
- [ ] `_convert_messages()` — MAF Message[] → Anthropic format
- [ ] 處理 role 映射（system/user/assistant）
- [ ] 處理多模態 content（文字/圖片，如有需要）
- [ ] `_convert_response()` — Anthropic Response → MAF ChatResponse
- [ ] 提取 text content blocks
- [ ] 映射 usage（input_tokens, output_tokens）
- [ ] `_build_chat_response()` — 構建 MAF 標準回應物件

### Extended Thinking 支援
- [ ] `thinking_config` 參數傳遞到 Anthropic API
- [ ] thinking blocks 正確提取和處理
- [ ] budget_tokens 可配置

### 測試
- [ ] isinstance(client, BaseChatClient) 通過
- [ ] 簡單 prompt 測試（"Respond with OK"）
- [ ] Extended Thinking 測試（thinking_config 啟用）
- [ ] 格式轉換 round-trip 測試
- [ ] API key 缺失時的錯誤處理

---

## S151-3: ManagerModelRegistry + ManagerModelSelector + YAML 配置 (4 SP)

### YAML 配置
- [ ] 建立 `backend/config/manager_models.yaml`
- [ ] 定義 claude-opus-4-6 配置（provider, model_id, capabilities, cost_tier, thinking）
- [ ] 定義 claude-sonnet-4-6 配置
- [ ] 定義 claude-haiku-4-5 配置
- [ ] 定義 gpt-5.2 配置
- [ ] 定義 gpt-4o 配置
- [ ] 定義 o3-mini 配置
- [ ] 定義 selection_strategies（max_reasoning, balanced, cost_efficient, fast_cheap）
- [ ] 定義 defaults（manager_model, fallback_model, max_cost_per_task）
- [ ] `${AZURE_OPENAI_ENDPOINT}` 環境變數引用正確

### ManagerModelRegistry
- [ ] 建立 `backend/src/integrations/hybrid/orchestrator/manager_model_registry.py`
- [ ] `ModelConfig` 資料類別（provider, model_id, capabilities, cost_tier 等）
- [ ] `CostTier` enum（premium, standard, economy）
- [ ] `_resolve_env()` 靜態方法（解析 `${}` 環境變數）
- [ ] `_load_config()` 從 YAML 載入配置
- [ ] `create_manager_agent()` — anthropic: `Agent(AnthropicChatClient(...), name=...)` (positional)
- [ ] `create_manager_agent()` — azure_openai: `Agent(AzureOpenAIResponsesClient(...), name=...)` (positional)
- [ ] `_get_manager_instructions()` — Manager prompt
- [ ] `list_models()` — 列出所有模型
- [ ] `get_default_model()` / `get_fallback_model()`
- [ ] `get_model_config()` — 取得單個模型配置
- [ ] 單例模式 `get_instance()`

### ManagerModelSelector
- [ ] 建立 `backend/src/integrations/hybrid/orchestrator/manager_model_selector.py`
- [ ] `select_model(risk_level, complexity, user_override)` 主方法
- [ ] user_override 最高優先邏輯
- [ ] CRITICAL → max_reasoning 策略
- [ ] HIGH → balanced 策略
- [ ] MEDIUM → cost_efficient 策略
- [ ] LOW → fast_cheap 策略
- [ ] `_resolve()` — 從策略名找模型 key
- [ ] `_is_available()` — 檢查 API key / endpoint 是否存在
- [ ] Fallback 邏輯（不可用時降級到 fallback_model）
- [ ] Import 路徑正確：`from src.integrations.orchestration.intent_router.models import RiskLevel`

### 單元測試
- [ ] YAML 載入測試（6 模型正確解析）
- [ ] 環境變數解析測試
- [ ] Selector 策略測試（所有 risk_level 覆蓋）
- [ ] user_override 優先級測試
- [ ] Fallback 測試（無 API key 時降級）
- [ ] Registry 單例測試

---

## 驗收測試

- [ ] `AnthropicChatClient` 通過 `BaseChatClient` isinstance 檢查
- [ ] `AnthropicChatClient` 可成功呼叫 Claude API（需 ANTHROPIC_API_KEY）
- [ ] `ManagerModelRegistry` 從 YAML 載入 6 個模型配置
- [ ] `ManagerModelSelector.select_model(CRITICAL)` → "claude-opus-4-6"
- [ ] `ManagerModelSelector.select_model(LOW)` → "claude-haiku-4-5"
- [ ] 無 ANTHROPIC_API_KEY 時自動 fallback 到 gpt-4o
- [ ] `MagenticBuilderAdapter.build()` 正確傳入 `manager_agent=` 到 `MagenticBuilder()` 構造函數
- [ ] 現有 E2E 測試不受 build() 修復影響
- [ ] TypeScript 零錯誤（前端無改動，確認不受影響）
- [ ] Python 型別檢查通過（mypy）
