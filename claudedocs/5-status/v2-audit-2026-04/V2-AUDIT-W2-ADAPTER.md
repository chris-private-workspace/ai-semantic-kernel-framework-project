# V2 Audit W2-1 — Adapter + LLM Neutrality

**Audit 日期**: 2026-04-29
**Auditor**: Research agent (Claude Opus 4.7)
**Sprint 範圍**: Sprint 49.4 Day 1 (commit c342034)
**結論**: ✅ **PASSED** — LLM Neutrality 鐵律守住，ABC 對齊，contract tests 強度真實

---

## 摘要

| 項目 | 結果 |
|------|------|
| LLM Neutrality 鐵律違反（agent_harness/） | **0** ✅ |
| ChatClient ABC `@abstractmethod` 覆蓋 | **6/6** ✅ |
| Azure OpenAI adapter 6 方法實作真實 | **6/6** ✅ |
| Error mapping 覆蓋 ProviderError cases | **9/9** ✅ |
| 41 contract tests pytest 結果 | **41 pass / 0 fail / 0 skip** ✅ |
| Real Azure integration test 檔案存在 | **❌ 缺**（docstring 提及但 `test_integration.py` 未建） |
| 阻塞 Phase 50? | **否** ✅ |

---

## Phase A — LLM Neutrality 鐵律

### A.1 agent_harness/ 違反
- `^(from|import) (openai|anthropic|agent_framework)`：**0 occurrences** ✅

### A.2 / A.3 其他層
- `business_domain/` / `platform_layer/` / `api/` / `_contracts/`：**0 occurrences** ✅

### A.4 Adapter 唯一例外
- `adapters/azure_openai/adapter.py:41`：`from openai import AsyncAzureOpenAI` ✅ 合法
- `adapters/azure_openai/error_mapper.py:29`：`from openai import (...)` ✅ 合法
- `adapters/_base/`：僅 docstring/comment 提及 provider 名稱，**0 SDK imports** ✅
- `adapters/anthropic/`、`adapters/openai/`：尚未建立（Phase 50+ 計畫，不違規）

### A.5 CI Lint Rule（強制性）
- `.github/workflows/backend-ci.yml:103-110`：
  ```yaml
  - name: LLM SDK leak check (LLM-provider-neutrality)
    run: |
      if grep -rE "^(from |import )(openai|anthropic|agent_framework)" \
        src/agent_harness/ src/infrastructure/; then
        echo "ERROR: ..."
        exit 1   # ← 真強制，非 fake green
      fi
  ```
- ✅ exit 1 真強制
- ⚠️ **gap**：只檢 `agent_harness/` + `infrastructure/`；未涵蓋 `business_domain/` / `platform_layer/` / `api/`
- 修補建議：擴充 grep 範圍至 `src/business_domain/ src/platform_layer/ src/api/`

---

## Phase B — ChatClient ABC 對齊

### B.1 位置
- `backend/src/adapters/_base/chat_client.py`

### B.2 6 方法表
| 方法 | @abstractmethod | 簽名對齊 17.md §2.1 | docstring owner |
|------|:-:|:-:|:-:|
| `chat` | ✅ | ✅ ChatRequest + cache_breakpoints + trace_context | ✅ |
| `stream` | ✅ | ✅ AsyncIterator[StreamEvent]（簽名選擇 regular method 而非 async-gen，理由有 docstring 說明） | ✅ |
| `count_tokens` | ✅ | ✅ messages + tools | ✅ |
| `get_pricing` | ✅ | ✅ → PricingInfo | ✅ |
| `supports_feature` | ✅ | ✅ Literal 7 features | ✅ |
| `model_info` | ✅ | ✅ → ModelInfo | ✅ |

Module-level docstring 明確標 `Owner: 10-server-side-philosophy.md §原則 2` 與 `Single-source: 17.md §2.1`。

### B.3 中性型別 import
- 從 `agent_harness._contracts` import: `CacheBreakpoint`, `ChatRequest`, `ChatResponse`, `Message`, `ToolSpec`, `TraceContext` ✅
- 從 `adapters._base.pricing` import `PricingInfo` ✅
- 從 `adapters._base.types` import `ModelInfo`, `StreamEvent` ✅
- **無重複定義**（無 AP-3 scattering）

---

## Phase C — Azure OpenAI Adapter

### C.1 結構
- `adapter.py` (357 行) ✅
- `error_mapper.py` (120 行) ✅
- `tool_converter.py` ✅（被 import：`messages_to_azure`、`tool_specs_to_azure`、`azure_tool_call_to_neutral`）
- `config.py` ✅（pricing / context_window / supports_* 全在 config）

### C.2 6 方法實作完整性
- `count_tokens`：**真用 tiktoken**（`encoding_for_model` + 回退 `o200k_base`），逐 message + tool 累計，含 per-message overhead 4 ✅
- `get_pricing`：從 config 讀 input/output/cached → PricingInfo ✅
- `supports_feature`：dict lookup，每個 feature 真有判斷邏輯（vision/caching/structured_output/parallel_tool_calls 從 config；audio/computer_use 硬編 False；thinking 從 config）✅
- `model_info`：完整返回（含 `provider="azure_openai"`、`context_window`、`max_output_tokens`）✅
- `chat`：真打 SDK 後 `_parse_response` 回傳中性 `ChatResponse`；含 cancellation propagate + error wrapping ✅
- `stream`：真 async iterator，產出 `content_delta` / `tool_call_delta` / `stop` 事件 ✅

### C.3 Error mapping 覆蓋
| ProviderError | 來源觸發 |
|---|---|
| AUTH_FAILED | `AuthenticationError`, `PermissionDeniedError`, status 401/403 ✅ |
| RATE_LIMITED | `RateLimitError`, status 429 ✅ |
| QUOTA_EXCEEDED | `RateLimitError` + msg "quota" ✅ |
| TIMEOUT | `APITimeoutError`, msg "timeout"/"timed out" ✅ |
| SERVICE_UNAVAILABLE | `APIConnectionError`, `InternalServerError`, status 5xx ✅ |
| MODEL_UNAVAILABLE | `NotFoundError`, status 404 ✅ |
| CONTEXT_WINDOW_EXCEEDED | msg "context_length_exceeded"/"maximum context length" ✅ |
| SAFETY_REFUSAL | msg "content_filter"/"safety"/"policy" ✅ |
| INVALID_REQUEST | `BadRequestError`, `UnprocessableEntityError` (generic) ✅ |
| UNKNOWN | fallback ✅ |

**全 9 cases 涵蓋**（規則文件原列 9 + UNKNOWN）。

### C.4 中性型別 leak
- `chat()` 回傳 `ChatResponse`（中性），不漏 `openai.ChatCompletion` ✅
- `_AZURE_FINISH_REASON_MAP` 把 `"stop"`/`"tool_calls"`/`"length"`/`"content_filter"` → `StopReason` enum，**不外漏 OpenAI 字串** ✅
- `tool_calls` 透過 `azure_tool_call_to_neutral` 轉中性 `ToolCall` ✅
- `usage` 包成中性 `TokenUsage`（含 cached_input_tokens 提取自 `prompt_tokens_details.cached_tokens`）✅

---

## Phase D — 41 Contract Tests 誠實性

### D.1 測試檔位置
- `backend/tests/unit/adapters/azure_openai/test_contract.py` (16 tests)
- `backend/tests/unit/adapters/azure_openai/test_error_mapper.py` (18 tests)
- `backend/tests/unit/adapters/azure_openai/test_pricing.py` (4 tests)
- `backend/tests/unit/adapters/azure_openai/test_token_counting.py` (3 tests)
- **總計：41**

### D.2 Pytest 結果
```
41 passed in 0.33s
0 failed, 0 skipped
```
✅ **無 skip / 無 mark.integration 暗藏**。

### D.3 抽樣 5 test 強度（test_contract.py）

| Test 名 | Mock or Real | Assertion 強度 | 場景真實 |
|---|---|---|---|
| `test_adapter_is_chat_client` | n/a | isinstance check | ABC enforcement |
| `test_count_tokens_with_tools` | Real（tiktoken） | n_with_tools > n_no_tools（真比較）| 真實 token 累計 |
| `test_chat_returns_chat_response` | SDK mock + real adapter | content=="The answer is 4." / stop_reason==END_TURN / prompt_tokens==12 | 真 ChatRequest → 真 parse → 具體值 |
| `test_chat_tool_calls_normalize_to_tool_use` | SDK mock + real adapter | tool_calls[0].arguments == {"a":1,"b":2}（dict，非 str）/ stop_reason==TOOL_USE | 含中性化驗證 |
| `test_chat_cancellation_propagates` | sleep(10) + wait_for(0.05) | pytest.raises CancelledError | 真 race condition |
| `test_provider_error_wrapped_in_adapter_exception` | RuntimeError → adapter | `category == ProviderError.UNKNOWN` + `provider == "azure_openai"` | 真 exception wrapping |

**強度評**：✅ 不是 isinstance fluff；assertion 有具體值 + 中性化檢查 + 真 race + exception 鏈路。

### D.4 Real Azure integration test
- ❌ **`test_integration.py` 不存在**（contract.py docstring 第 12-13 行提及「Network-real tests live in test_integration.py — skipped by default; opt-in via @pytest.mark.integration」，但 file 未建）
- 影響：尚無真打 Azure 的測試，鎖死 SDK behaviour 變動風險未防
- **修補建議（D2 或 D5 補）**：建 `test_integration.py` 含 1-2 個 `@pytest.mark.integration`（CI skip default），讓開發者本地可選擇打真 API

### D.5 Cross-provider 抽象
- `adapters/_testing/mock_clients.py` 存在（讓 agent_harness 單元測試用 MockChatClient）✅
- ⚠️ 沒看到 `adapters/_testing/contract_test_base.py`（讓未來 anthropic adapter 套用同 contract suite 的可重用基類）
- **修補建議（49.4 D5 或 Phase 50 加）**：抽 contract test 為 base class，新 provider 直接繼承減少重寫

---

## Phase E — 跨範疇影響

### E.1 ChatClient 使用點
- 4 個檔 import `ChatClient`：
  - `adapters/_base/__init__.py`（re-export）
  - `adapters/_base/chat_client.py`（定義）
  - `adapters/azure_openai/adapter.py`（concrete）
  - `adapters/_testing/mock_clients.py`（mock）
- ⚠️ **agent_harness/orchestrator_loop 等 11 範疇尚未消費 ChatClient**（D1 只交付 ABC + adapter；wiring 在後續 Sprint 50.1 範疇 1 才接）— 這是計畫預期，不是缺陷

### E.2 ProviderRouter
- ❌ 未實作（17.md §2.1 提及，但 49.4 D1 不在範圍）
- 計畫於 Phase 50+ ProviderRouter 引入；config-driven routing
- **不阻塞 Phase 50**（adapter 中性後 router 是純加值層）

---

## 結論

| 項目 | 評 |
|---|:-:|
| LLM Neutrality 鐵律 | ✅ |
| ChatClient ABC 對齊 17.md | ✅ |
| Azure OpenAI adapter 實作完整 | ✅ |
| Contract tests 強度（assertion 真實 + 場景含 cancel/error/tool_use） | ✅ |
| Real Azure integration test | ⚠️ 缺檔 |
| ProviderRouter | ⚠️ 未做（計畫內） |
| **整體** | ✅ **Sprint 49.4 D1 通過審計** |

---

## 修補建議（優先序）

### 🟡 P1（Sprint 49.4 D2-D5 內補）
1. **建 `test_integration.py`**：1-2 個 `@pytest.mark.integration` 真打 Azure，CI default skip。鎖 SDK behaviour 漂移。
2. **CI lint 範圍擴大**：`backend-ci.yml` 第 106 行加 `src/business_domain/ src/platform_layer/ src/api/`，預防後續層偷渡 LLM SDK。

### 🟢 P2（Phase 50 適時加）
3. **抽 `contract_test_base.py`**：讓 anthropic / openai adapter 直接繼承 contract suite。
4. **建 ProviderRouter 雛形**：config-driven intent → provider 選擇（17.md §2.1 提及）。

---

## 阻塞 Phase 50？

✅ **否**

理由：
- LLM Neutrality 鐵律已守住（最高 severity check 全綠）
- ChatClient ABC 6/6 對齊 17.md，未來 anthropic adapter 直接套用
- Adapter 實作真實完整（無 stub / fake green）
- 41 contract tests 真有強度（無 skip、含具體 assertion、cancellation、error chain）
- 缺 integration test 與 ProviderRouter 是**加值缺**，不影響範疇 1-11 在 Phase 50 起跑

承諾「30 分鐘換 provider 不改代碼」目前**結構上守住**；待 Phase 50 anthropic adapter 落地時做完整端到端驗證。
