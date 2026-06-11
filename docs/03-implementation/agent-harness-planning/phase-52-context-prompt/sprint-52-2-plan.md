# Sprint 52.2 — Plan：範疇 5 PromptBuilder（Level 0 → Level 4）

**Sprint**：52.2 — Cat 5 Prompt Construction（DefaultPromptBuilder + 3 position strategies + memory 5×3 真注入 + CacheBreakpoint 接通 + AP-8 lint rule + Loop integration）
**Phase**：52（Context + Prompt）/ 第 2 / 共 2 sprint（Phase 52 收尾）
**Cumulative**：11/22 V2 sprints（Phase 52 進度 1/2 → 預計 2/2 = 100%）
**Branch**：`feature/phase-52-sprint-2-cat5-prompt-builder`（待開）
**Plan 起草**：2026-05-01
**Status**：🟡 PLANNING — 待用戶 approve 後啟動 Day 1

---

## 0. Sprint 目標（一句話）

把 **49.1 PromptBuilder ABC stub**（`prompt_builder/_abc.py:31` `build() -> PromptArtifact`）完成 concrete impl + 接通主流量 + 強制 lint，交付 **Cat 5 6 大支柱**：DefaultPromptBuilder（6 層階層組裝）+ 3 種 PositionStrategy（naive / lost_in_middle_aware / tools_at_end）+ Memory 5 layer × 3 time scale 真注入 + CacheBreakpoint 接通 LLM call（Anthropic `cache_control` + OpenAI `prompt_cache_key`）+ Loop 整合（替換 ad-hoc messages 組裝）+ AP-8 lint rule（CI 強制），使範疇 5 從 **Level 0 進到 Level 4**，並接通 51.2 retrospective AI-7 + CARRY-031/032。

---

## 1. User Stories

### Story 1：主流量 LLM 呼叫禁止繞過 PromptBuilder（lint rule 強制）

> **作為** V2 主流量呼叫者
> **我希望** 任何 `ChatClient.chat()` / `ChatClient.stream()` 呼叫前必先 `PromptBuilder.build()`，否則 CI lint fail
> **以便** AP-8（No Centralized PromptBuilder）反模式從架構層杜絕，memory layers 必定真注入，cache breakpoints 必定統一處理

**驗收**：
- `agent_harness/orchestrator_loop/loop.py` 替換既有 ad-hoc `messages = [...]` 組裝為 `await prompt_builder.build(state, tenant_id, ...)` → `chat_client.chat(messages=artifact.messages, cache_breakpoints=artifact.cache_breakpoints, ...)`
- `scripts/check_promptbuilder_usage.py` AST lint：grep `agent_harness/**/*.py` 任何 `chat_client.chat(messages=...)` 必先有同 scope 的 `prompt_builder.build()` call
- 例外白名單：`tests/**` / `_testing/mock_clients.py` / `adapters/_testing/**` / 51.1 contract test files
- `agent_harness/**` 主流量檔案 grep `chat_client.chat\|chat_client.stream` 全部前置有 PromptBuilder.build → 0 violation
- 50.x loop 10/10 baseline tests 維持通過（loop integration backward-compat）

### Story 2：3 種 Position Strategy 可切換（Lost-in-middle 預設）

> **作為** Phase 52+ 開發者
> **我希望** PromptBuilder 可選 `naive`（順序組裝）/ `lost_in_middle_aware`（重要置首尾，預設）/ `tools_at_end`（某些模型偏好）三種策略
> **以便** 不同 model 可切策略；lost-in-middle 場景下重要內容（system + user）位置精準度 ≥ 95%

**驗收**：
- `PositionStrategy` ABC + 3 concrete impl：`NaiveStrategy` / `LostInMiddleStrategy`（default）/ `ToolsAtEndStrategy`
- LostInMiddleStrategy：order = `[system, recent_user_message_top, tools, memory_summary, ...mid_history..., recent_assistant, user_message_bottom]`（user message 同時放首尾錨點）
- NaiveStrategy：order = `[system, tools, memory, conversation, user]`（無位置調整）
- ToolsAtEndStrategy：order = `[system, memory, conversation, user, tools]`（工具 schema 放最後）
- Position 精準度測試：建 mock 50-message prompt → assert system 在 idx 0，user 在 last + first（lost-in-middle）/ tools 在 last（tools_at_end）
- DefaultPromptBuilder constructor 注入 `position_strategy: PositionStrategy = LostInMiddleStrategy()`

### Story 3：Memory 5 layer × 3 time scale 真注入

> **作為** PromptBuilder
> **我希望** `build()` 時透過 51.2 `MemoryRetrieval` ABC 取 5 layer（system / tenant / role / user / session）× 3 time scale（permanent / quarterly / daily）的 memory hints，並依 layer 順序 inject 進 prompt
> **以便** 31 turn 對話仍能依賴 user/role memory 給連貫回覆；tenant_a 的 prompt 永遠不會 leak tenant_b 的 memory

**驗收**：
- DefaultPromptBuilder constructor 注入 `memory_retrieval: MemoryRetrieval`
- `_inject_memory_layers(tenant_id, user_id, query)` 呼叫 `memory_retrieval.retrieve()` → 拿 `MemoryHint` list → 依 layer 排序 inject 為 prompt section（標 `layer_metadata["memory_layers_used"]: list[str]`）
- 5 layer × 3 time scale 矩陣全 13 cell e2e 覆蓋（system 永久 / tenant 永久 / tenant 季 / role 永久 / role 季 / user 永久 / user 季 / user 天 / session 天）
- 🛡️ **Tenant 隔離 red-team test 4 cases**：
  - tenant_a memory 寫入 → tenant_b PromptBuilder.build() → assert tenant_a content 不出現
  - cross-user memory：user_a (tenant_a) memory 寫入 → user_b (tenant_a) build → user-scoped memory 不出現
  - cross-session：session_a memory 寫入 → session_b build → session-scoped memory 不出現
  - cross-time-scale：daily memory 過期後 build → 不再注入
- `MemoryRetrieval` 失敗（DB down）→ PromptBuilder 降級為 system + tools + conversation only（emit warning log，不 fail）

### Story 4：CacheBreakpoint 接通 LLM provider（CARRY-031 + CARRY-032）

> **作為** 平台
> **我希望** PromptBuilder.build() 自動呼叫 `PromptCacheManager.get_cache_breakpoints()` 拿 breakpoints 並產出 PromptArtifact.cache_breakpoints；adapter 層在 chat() 時把 breakpoints 轉換為 provider-specific marker（Anthropic `cache_control: {"type": "ephemeral"}` 注入 messages / OpenAI 設 `prompt_cache_key` request 參數）
> **以便** 多租戶場景成本下降 30-90%（穩態 cache hit > 50%）；CARRY-031 + CARRY-032 解除

**驗收**：
- DefaultPromptBuilder constructor 注入 `cache_manager: PromptCacheManager` + `cache_policy: CachePolicy = CachePolicy()`
- `build()` 內部 call `await cache_manager.get_cache_breakpoints(tenant_id=..., policy=cache_policy)` → 回 `list[CacheBreakpoint]` → 寫入 `PromptArtifact.cache_breakpoints`
- `adapters/azure_openai/adapter.py` 在 `chat(cache_breakpoints=...)` 時：取 `cache_breakpoints[i].section_id` 拼成 deterministic `prompt_cache_key` request param（穩態 hit > 50%）
- 新建 `adapters/_mock/anthropic_adapter.py`（test-only mock；不 import anthropic SDK）：在 `chat()` 時 iterate `cache_breakpoints` → 在對應 message 注入 `cache_control: {"type": "ephemeral"}`（驗證 marker 正確 emit）
- 整合測試：5 turn 同 tenant + user 對話 → assert PromptArtifact.cache_breakpoints ≥ 3（system / tools / memory）+ adapter mock 確認 marker 注入
- **52.2 範圍**：`adapters/anthropic/` 真 adapter 不在 scope（Phase 50+ 才做 real Anthropic provider）；52.2 用 mock + contract test 驗 marker correctness

### Story 5：範疇 5 達 Level 4 + Phase 52 收尾

> **作為** Phase 53+ 開發者
> **我希望** 範疇 5 PromptBuilder 為主流量唯一入口、ABC + concrete + lint rule 全 ship、17.md §1.1 / §2.1 / §4.1 完整登記
> **以便** Phase 53 State Mgmt + Error Handling 不需處理 prompt 組裝（已 centralized）；Cat 12 PromptBuilt event tracer span 在 53.x 加；Phase 52 cumulative 達 100%

**驗收**：
- mypy --strict 全 src（baseline 93 → 目標 ~110 files）clean
- pytest 全綠（baseline 434 → 目標 ~480 PASS）
- 17.md §1.1（PromptArtifact / PromptBuilder row 確認/擴 layer_metadata key）+ §2.1（PromptBuilder ABC 簽名升級）+ §4.1（PromptBuilt event payload schema）同步
- Phase 52 README cumulative table 標 Cat 5 Level 0 → **Level 4**；52.2 ✅ DONE；Phase 52 = 2/2 完成；V2 cumulative 10/22 → **11/22 = 50%**
- AP-8 反模式 — 解決 ✅（本 sprint 主旨；CI lint 強制）
- Loop integration 通過 30+ turn e2e（52.1 baseline 維持，PromptBuilder 透明替換）

---

## 2. 技術設計

### 2.1 Cat 5 6 大支柱概覽

| 支柱 | ABC / 類別 | 主要 Impl | 用途 | 觸發者 |
|------|-----------|----------|------|--------|
| 1. 階層組裝 | `PromptBuilder` (49.1 stub) | `DefaultPromptBuilder` | 6 層 prompt 組裝 | Loop 每 turn 開頭 |
| 2. Position Strategy | `PositionStrategy` ABC | NaiveStrategy / LostInMiddleStrategy / ToolsAtEndStrategy | 重要內容置首尾 / 工具放結尾 | DefaultPromptBuilder.build() 內部 |
| 3. Memory Injection | — | DefaultPromptBuilder._inject_memory_layers() | 5 layer × 3 time scale 注入 | DefaultPromptBuilder.build() 內部 |
| 4. Cache Integration | — | DefaultPromptBuilder._build_cache_breakpoints() | 呼叫 PromptCacheManager 產生 breakpoints | DefaultPromptBuilder.build() 內部 |
| 5. Templates | — | `templates.py` | system role / memory section 文字模板 | DefaultPromptBuilder 內部 |
| 6. AP-8 Lint Rule | — | `scripts/check_promptbuilder_usage.py` | CI 強制 0 ad-hoc messages 組裝 | CI（PR 觸發）|

### 2.2 PromptBuilder ABC 簽名升級（49.1 → 52.2）

49.1 stub（既有，per `prompt_builder/_abc.py:31-44`）：

```python
class PromptBuilder(ABC):
    @abstractmethod
    async def build(
        self,
        *,
        state: LoopState,
        tenant_id: UUID,
        user_id: UUID | None = None,
        trace_context: TraceContext | None = None,
    ) -> PromptArtifact: ...
```

52.2 升級簽名（加 cache_policy + position_strategy_override，全 default）：

```python
class PromptBuilder(ABC):
    @abstractmethod
    async def build(
        self,
        *,
        state: LoopState,
        tenant_id: UUID,
        user_id: UUID | None = None,
        cache_policy: CachePolicy | None = None,        # NEW: None → use builder default
        position_strategy: PositionStrategy | None = None,  # NEW: None → use builder default
        trace_context: TraceContext | None = None,
    ) -> PromptArtifact: ...
```

向後兼容：兩新欄位全 default=None；既有 49.1 callers（無；目前無人 call build() 因為是 stub）不破壞。

### 2.3 Position Strategy 3 種

| 策略 | Order（左到右）| 用途 | p95 latency target |
|------|--------------|------|------------------|
| **Naive** | system → tools → memory → conversation → user | 簡單 / 測試 / debug | < 5ms |
| **LostInMiddleAware**（default）| system → user(echo) → tools → memory_summary → ...mid_history... → recent_assistant → user(actual) | 重要 system + user 置首尾錨點 | < 10ms |
| **ToolsAtEnd** | system → memory → conversation → user → tools | 某些 model（如 gpt-4o）偏好 tools 放末尾 | < 5ms |

> **PositionStrategy ABC 簽名**：`def arrange(self, sections: PromptSections) -> list[Message]` — 純 stateless 重排函式，不做 IO。

### 2.4 6 層階層組裝（DefaultPromptBuilder）+ 範疇 12 埋點

> **🔴 跨切面紀律（per W3-2 audit）**：build() 入口必須 start tracer span；trace_context 必須沿鏈傳遞至所有子呼叫（memory_retrieval / cache_manager / token_counter）— **不可斷裂**（per `.claude/rules/observability-instrumentation.md` §TraceContext 傳遞）。

```python
async def build(self, *, state, tenant_id, user_id=None,
                cache_policy=None, position_strategy=None,
                trace_context: TraceContext | None = None) -> PromptArtifact:
    # Step 0: tracer span（範疇 12 cross-cutting）
    span = self._tracer.start_span(
        name="prompt_builder.build",
        parent_span_id=trace_context.span_id if trace_context else None,
        attributes={"tenant_id": str(tenant_id), "agent": self.__class__.__name__},
    )
    child_ctx = TraceContext(
        trace_id=trace_context.trace_id if trace_context else str(uuid4()),
        span_id=span.span_id,
        parent_span_id=trace_context.span_id if trace_context else None,
        tenant_id=tenant_id, user_id=user_id,
    )

    try:
        # Step 1: 取 sections（trace_context 沿鏈傳）
        sections = PromptSections(
            system=self._build_system_section(state, tenant_id),
            tools=self._build_tools_section(state.transient.tools_available),
            memory_layers=await self._inject_memory_layers(
                tenant_id, user_id, state.transient.last_user_message,
                trace_context=child_ctx,  # ← propagate
            ),
            conversation=state.transient.messages,
            user_message=state.transient.last_user_message,
        )

        # Step 2: PositionStrategy 重排（純 stateless，不需 trace）
        strategy = position_strategy or self._default_strategy
        messages = strategy.arrange(sections)

        # Step 3: CacheBreakpoint 產生（trace_context 沿鏈傳）
        cache_breakpoints = await self._build_cache_breakpoints(
            tenant_id, cache_policy or self._default_policy, sections,
            trace_context=child_ctx,  # ← propagate
        )

        # Step 4: Token estimation（52.1 TokenCounter；同步呼叫，不需 trace span，但記 metric）
        estimated_tokens = self._token_counter.count(messages=messages, tools=state.transient.tools_available)

        return PromptArtifact(
            messages=messages,
            cache_breakpoints=cache_breakpoints,
            estimated_input_tokens=estimated_tokens,
            layer_metadata={
                "memory_layers_used": [...],
                "position_strategy": strategy.__class__.__name__,
                "cache_sections": [...],
                "trace_id": child_ctx.trace_id,  # ← for SSE event 串連
            },
        )
    finally:
        span.record_metric("prompt_builder_build_duration_seconds", span.duration_seconds, attributes={"tenant_id": str(tenant_id)})
        span.end()
```

### 2.5 Memory Layer Injection（5 × 3 矩陣）+ 多租戶鐵律

> **🔴 跨切面紀律（per W1-2 audit + multi-tenant-data.md 三鐵律）**：
> - tenant_id NOT NULL（強制傳；ABC 簽名 required positional/keyword arg）
> - tenant_id filter 強制（每個 retrieve call）
> - **禁止 process-wide memory cache fallback**（fallback 必須 tenant-scoped）

走 51.2 `MemoryRetrieval.retrieve()` ABC（不直接讀 store；single-source 維持）：

```python
async def _inject_memory_layers(
    self, tenant_id: UUID, user_id: UUID | None, query: str,
    *, trace_context: TraceContext | None = None,  # ← propagate per W3-2
) -> dict[MemoryLayer, list[MemoryHint]]:
    # 51.2 MemoryRetrieval 強制 tenant_id filter；52.2 不引入任何 process-wide 快取
    hints = await self._memory_retrieval.retrieve(
        tenant_id=tenant_id, user_id=user_id, query=query, top_k=10,
        trace_context=trace_context,  # ← Cat 12 propagation
    )

    # 按 layer 分組：system / tenant / role / user / session
    by_layer = defaultdict(list)
    for h in hints:
        by_layer[h.layer].append(h)

    # 每 layer 內按 time_scale 排序：permanent > quarterly > daily（重要程度）
    for layer in by_layer:
        by_layer[layer].sort(key=lambda h: TIME_SCALE_PRIORITY[h.time_scale])

    return by_layer
```

**Tenant 隔離保證**（三層）：
1. `MemoryRetrieval.retrieve()` 51.2 已強制 tenant_id filter（紅隊 verified）
2. 52.2 PromptBuilder 信任此契約 + 加額外 assertion（debug mode）
3. **❌ 禁止**：在 PromptBuilder 內加任何「跨 tenant 共享」的 in-memory cache（process-wide dict）→ Day 2.2 紅隊測試含 cross-tenant memory leak case

### 2.6 Cache Breakpoint 接通（CARRY-031 + CARRY-032）

```python
async def _build_cache_breakpoints(
    self, tenant_id: UUID, policy: CachePolicy, sections: PromptSections,
    *, trace_context: TraceContext | None = None,  # ← propagate per W3-2
) -> list[CacheBreakpoint]:
    # 52.1 PromptCacheManager 已強制 tenant_id 隔離（4 紅隊 verified）
    breakpoints = await self._cache_manager.get_cache_breakpoints(
        tenant_id=tenant_id, policy=policy,
        trace_context=trace_context,  # ← Cat 12 propagation
    )

    # 對每個 breakpoint 標 logical metadata（52.1 加的欄位）
    for bp in breakpoints:
        if bp.section_id == "system":
            bp = replace(bp, content_hash=sha256(sections.system.content).hexdigest())
        elif bp.section_id == "tools":
            bp = replace(bp, content_hash=sha256(json.dumps(sections.tools)).hexdigest())
        # ...

    return breakpoints
```

**Adapter 層**（52.2 Day 3 接通）：
- **Azure OpenAI**：`adapters/azure_openai/adapter.py:chat()` 收 `cache_breakpoints` → 拼 deterministic `prompt_cache_key = sha256(":".join([bp.section_id for bp in breakpoints]))` → 傳給 OpenAI API
- **Mock Anthropic**（52.2 範圍）：`adapters/_mock/anthropic_adapter.py:chat()` 收 `cache_breakpoints` → iterate → 在對應 `messages[bp.position]` 注入 `cache_control: {"type": "ephemeral"}` 欄位 → 用於 contract test 驗證 marker 正確性

### 2.7 Loop Integration（替換 ad-hoc messages 組裝）

50.x baseline `loop.py`（既有）：
```python
# OLD (50.x baseline)
messages = state.transient.messages.copy()
response = await self._chat_client.chat(messages=messages, tools=tools, ...)
```

52.2 替換為 PromptBuilder.build()：
```python
# NEW (52.2)
artifact = await self._prompt_builder.build(
    state=state, tenant_id=state.metadata.tenant_id, user_id=state.metadata.user_id, ...
)
response = await self._chat_client.chat(
    messages=artifact.messages,
    tools=tools,
    cache_breakpoints=artifact.cache_breakpoints,
    ...
)
emit LoopEvent(type="PromptBuilt", payload={
    "messages_count": len(artifact.messages),
    "estimated_input_tokens": artifact.estimated_input_tokens,
    "cache_breakpoints_count": len(artifact.cache_breakpoints),
    "memory_layers_used": artifact.layer_metadata.get("memory_layers_used", []),
})
```

**Backward-compat**：`AgentLoopImpl.__init__` 加 `prompt_builder: PromptBuilder | None = None`；None 則 fallback 到 50.x baseline 邏輯（測試友好；50.x tests 不破壞）。

### 2.8 AP-8 Lint Rule

```python
# scripts/check_promptbuilder_usage.py
# AST-based check: any chat_client.chat(...) call in agent_harness/** must have
# a prior PromptBuilder.build(...) call in same function scope (or be in allowlist).

ALLOWLIST = {
    "tests/**",
    "**/_testing/**",
    "**/contract_test_*.py",
    "scripts/check_promptbuilder_usage.py",  # self-exempt
}
```

CI 整合：`.github/workflows/lint.yml` 加 step `python scripts/check_promptbuilder_usage.py`；fail → PR block。

### 2.9 17.md 同步點

**§1.1（dataclass / contract 表）— 確認 + 擴 layer_metadata key**：
- `PromptArtifact`（既有 row L57）— 確認簽名；`layer_metadata` keys 在文件中註明（memory_layers_used / position_strategy / cache_sections）
- 新 row：`PromptSections` — Cat 5，DefaultPromptBuilder 內部 dataclass（system / tools / memory_layers / conversation / user_message）
- 新 row：`PositionStrategy` — Cat 5，ABC for prompt section 重排

**§2.1（ABC 表）— 確認 + 升級**：
- `PromptBuilder`（既有 row L129）— 簽名升級 `build(state, tenant_id, user_id, cache_policy, position_strategy, trace_context) -> PromptArtifact`
- 新 row：`PositionStrategy` — Cat 5，方法 `arrange(sections) -> list[Message]`

**§4.1（LoopEvent 表）— 標記 PromptBuilt 為實作完成**：
- `PromptBuilt`（既有 row L241）— 移除「待 Phase 52.2」備註；payload schema：`messages_count / estimated_input_tokens / cache_breakpoints_count / memory_layers_used / position_strategy_used / duration_ms`

**§3.1（工具表）— 無變化**（Cat 5 不註冊 tool）。

---

## 3. File Change List

### 新建（~13 file）

```
agent_harness/prompt_builder/
├── __init__.py                          # 49.1 stub；52.2 補 public re-exports（DefaultPromptBuilder + 3 strategies）
├── _abc.py                              # 49.1 stub；52.2 升級簽名（+cache_policy +position_strategy）
├── builder.py                           # NEW: DefaultPromptBuilder（6 層階層組裝）
├── strategies/
│   ├── __init__.py                      # NEW: package marker + re-export
│   ├── _abc.py                          # NEW: PositionStrategy ABC + PromptSections dataclass
│   ├── naive.py                         # NEW: NaiveStrategy
│   ├── lost_in_middle.py                # NEW: LostInMiddleStrategy（default）
│   └── tools_at_end.py                  # NEW: ToolsAtEndStrategy
└── templates.py                         # NEW: system role / memory section 文字模板

adapters/_mock/
└── anthropic_adapter.py                 # NEW: test-only mock；驗 cache_control marker；不 import anthropic SDK

scripts/
└── check_promptbuilder_usage.py         # NEW: AP-8 AST lint rule

tests/unit/agent_harness/prompt_builder/  # 11 test files / ~50 tests
├── test_strategies_naive.py             (3)
├── test_strategies_lost_in_middle.py    (5)
├── test_strategies_tools_at_end.py      (3)
├── test_builder_basic.py                (4)
├── test_builder_memory_injection.py     (8 incl. 4 red-team)
├── test_builder_cache_integration.py    (5)
├── test_builder_position_strategy.py    (3)
├── test_builder_token_estimation.py     (3)
├── test_templates.py                    (3)
├── test_lint_rule.py                    (5)
└── test_anthropic_mock_adapter.py       (4)

tests/integration/agent_harness/prompt_builder/
├── test_loop_with_prompt_builder.py     # NEW: Loop + PromptBuilder + ChatClient e2e
├── test_cache_hit_steady_state.py       # NEW: 5 turn cache hit > 50%
└── test_memory_5x3_matrix.py            # NEW: 5 layer × 3 time scale 全 cell 覆蓋

tests/e2e/
└── test_main_flow_via_prompt_builder.py # NEW: 100% 主流量 e2e
```

### 修改（~6 file）

- `agent_harness/orchestrator_loop/loop.py` — 加 `prompt_builder: PromptBuilder | None = None` 注入；替換 ad-hoc messages 組裝；emit `PromptBuilt` event
- `agent_harness/_contracts/events.py` — `PromptBuilt` event 加完整 payload schema（messages_count / estimated_input_tokens / cache_breakpoints_count / memory_layers_used / position_strategy_used / duration_ms）
- `agent_harness/_contracts/__init__.py` — re-export `PromptSections` / `PositionStrategy`
- `adapters/azure_openai/adapter.py` — `chat(cache_breakpoints=...)` 收新欄位 → 拼 `prompt_cache_key`
- `adapters/_testing/mock_clients.py` — `MockChatClient.chat()` 接收 `cache_breakpoints` 參數（assertion 用）
- `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` — §1.1 + §2.1 + §4.1 sync
- `docs/03-implementation/agent-harness-planning/phase-52-context-prompt/README.md` — 52.2 ✅ DONE marker + Phase 52 收尾 + V2 11/22

### 刪除

無（52.2 純加新範疇 + 整合 + lint）。

---

## 4. Acceptance Criteria（DoD）

### 結構驗收
- [ ] DefaultPromptBuilder（6 層階層組裝）齊備
- [ ] 3 PositionStrategy concrete impl（Naive / LostInMiddle / ToolsAtEnd）都通過 PositionStrategy ABC contract test
- [ ] PromptBuilder ABC 簽名升級（+cache_policy +position_strategy default=None）
- [ ] DefaultPromptBuilder constructor 接受 `memory_retrieval / cache_manager / token_counter / position_strategy / cache_policy / templates` 6 個 DI
- [ ] Loop integration：每 turn 透過 PromptBuilder.build()；emit PromptBuilt event；compactor 注入無干擾
- [ ] Anthropic mock adapter 接通 `cache_control` marker；Azure OpenAI adapter 接通 `prompt_cache_key`

### SLO 量化驗收
- [ ] PromptBuilder p95 build time < 50ms（含 memory injection；mock memory_retrieval）
- [ ] LostInMiddleStrategy 後 system 在 idx 0 + user 在 last（精準度 100%；50 個 mock prompt 全 pass）
- [ ] Cache hit 率 > 50%（5 turn 同 tenant + user 穩態量測）
- [ ] PromptBuilder 整體 e2e p95 < 100ms（build + chat + parse 全鏈路）

### 多租戶 / 安全驗收
- [ ] 4 tenant memory red-team test 全綠（cross-tenant / cross-user / cross-session / expired-time-scale 0 leak）
- [ ] PromptBuilder build 後 grep tenant_b content in tenant_a artifact = 0
- [ ] `agent_harness/prompt_builder/**/*.py` grep `import openai|import anthropic` = **0**
- [ ] Anthropic mock adapter 在 `_mock/` 子目錄；不 import anthropic SDK
- [ ] **🔴 W3-2 carryover**：PromptBuilder 內無 process-wide memory cache（grep `class.*Builder` AST 無 class-level / module-level mutable dict 跨 tenant）
- [ ] **🔴 W3-2 carryover**：5×3 矩陣 integration test 用 **real PostgreSQL via docker fixture**（per `.claude/rules/testing.md` + multi-tenant-data.md）— 不用 SQLite，不用 mock store

### 範疇 12（Observability）跨切面驗收（W3-2 carryover）
- [ ] `DefaultPromptBuilder.build()` 入口 emit tracer span（name=`prompt_builder.build`，parent=trace_context.span_id）
- [ ] trace_context 沿鏈傳遞至 3 子呼叫：`memory_retrieval.retrieve()` / `cache_manager.get_cache_breakpoints()` / `chat_client.chat()`（不可斷裂）
- [ ] `prompt_builder_build_duration_seconds` metric emit（labels: tenant_id）
- [ ] `PromptArtifact.layer_metadata["trace_id"]` 寫入；SSE `PromptBuilt` event 含 trace_id（前端可串連日誌）

### Lint / AP-8 驗收
- [ ] `scripts/check_promptbuilder_usage.py` 對 `agent_harness/**` 跑 → 0 violation（除白名單外）
- [ ] 50.x loop tests 10/10 PASS（Loop integration backward-compat）
- [ ] 52.1 baseline 維持（adapter 41/41 / Cat 4 36 unit + 5 integration / Cat 1 10）

### 測試 / Quality 驗收
- [ ] mypy --strict pass
- [ ] pytest baseline 434 → 目標 ~480 PASS（50 unit + 3 integration + 1 e2e）
- [ ] 所有新檔有 file header（per `file-header-convention.md`）
- [ ] AP-8 No Centralized PromptBuilder 反模式 — 解決 ✅（本 sprint 主旨）
- [ ] 5 V2 lints 全 pass（mypy strict / flake8 / LLM neutrality / 51.1 adapter regression / 50.x loop regression）
- [ ] 17.md §1.1 + §2.1 + §4.1 同步（PromptArtifact / PromptSections / PositionStrategy / PromptBuilder upgrade / PromptBuilt payload）

### 整合 / Demo 驗收
- [ ] 5 layer × 3 time scale memory 矩陣 e2e 測試（13 cell 全覆蓋）
- [ ] 100% 主流量 e2e（Cat 1 Loop → Cat 5 PromptBuilder → Cat 6 Adapter → Cat 4 TokenCounter）
- [ ] 30+ turn e2e 維持綠（52.1 baseline）+ PromptBuilder 透明替換無 regression
- [ ] Phase 52 README cumulative table 標 Cat 5 Level 0 → Level 4 + 52.2 ✅ DONE + V2 11/22 = 50%

---

## 5. CARRY Items 處理計畫

### 處理（51.x / 52.1 → 52.2 涵蓋）

| 51.x / 52.1 CARRY | 52.2 處理 |
|------------------|----------|
| **CARRY-031**（Anthropic `cache_control` 接通 LLM call）| ✅ Day 3：mock anthropic adapter 在 chat() 注入 `cache_control: {"type": "ephemeral"}` marker；real Anthropic adapter 留 Phase 50+ |
| **CARRY-032**（OpenAI `prompt_cache_key` 自動 cache 接通）| ✅ Day 3：Azure OpenAI adapter 在 chat() 拼 deterministic `prompt_cache_key` 傳 API |
| **51.2 AI-7**（PromptBuilder 接通 Cat 4 TokenCounter）| ✅ Day 1：DefaultPromptBuilder constructor 注入 `token_counter: TokenCounter` |
| **51.2 AI-9**（ClaudeTokenCounter real anthropic tokenizer 接通）| ⏸ 不在 52.2 scope；Phase 50+ Anthropic real adapter ship 時順手 |

### 不互動（52.2 不影響）

| CARRY | 理由 |
|-------|------|
| **CARRY-026**（Qdrant semantic）| Memory layer 走 51.2 InMemoryStore；Qdrant 在 retrieval 層替換不影響 PromptBuilder |
| **CARRY-027**（MemoryExtractor Celery）| Memory write path；52.2 是 read path |
| **CARRY-029**（SessionLayer Redis）| Session memory 透過 MemoryRetrieval ABC；Redis 替換對 PromptBuilder 透明 |
| **CARRY-030**（ExecutionContext threading）| 52.2 透過 build() kwargs 傳 tenant_id；ExecutionContext 接通 53.3 |
| **CARRY-033**（Redis-backed PromptCacheManager）| 52.2 用 InMemoryCacheManager；Redis 替換對 PromptBuilder 透明 |
| **CARRY-034**（Sub-agent delegation prompt hint）| Phase 54.2（Cat 11 own）；52.2 不接通 |
| **CARRY-035**（test_builtin_tools 2 pre-existing failure）| Sprint 53.x 處理（per 52.1 retro AI-8）|

### 延後（記入 52.2 retrospective）

預期延後（Day 4 retro 確認）：
- ⏸ **PromptAudit 政策**（哪些 tenant 開啟 prompt log；合規 vs 隱私平衡，per 01-spec §範疇 5）→ Phase 53.4 Governance Frontend
- ⏸ **Cat 12 Tracer span for PromptBuilt**（per 52.1 AI-10）→ Phase 53.x 統一處理
- ⏸ **Real Anthropic adapter cache_control**（Phase 50+ Anthropic adapter ship 後）

---

## 6. Day 估時 + Theme（rolling 5-day）

| Day | 主題 | 估時 | 主要交付 |
|-----|------|------|---------|
| **Day 0** | Plan + Checklist + README rolling switch | 2h | 本 plan / checklist / Phase 52 README 52.2 PLANNING |
| **Day 1** | DefaultPromptBuilder + 3 PositionStrategy + templates + ABC 升級 + 17.md §1.1/§2.1 sync | 6h | builder.py + 5 strategies file + templates.py + 18 unit tests + 17.md sync |
| **Day 2** | Memory 5×3 真注入（trace propagate）+ CacheBreakpoint 整合（trace propagate）+ 紅隊測試 + **real PG fixture** | 8h | _inject_memory_layers + _build_cache_breakpoints + 13 unit tests（含 4 red-team）+ 1 integration（5×3 矩陣，**real PG via docker**） |
| **Day 3** | Loop integration + Anthropic mock adapter + Azure OpenAI cache_key + adapter edits | 7h | loop.py edit + _mock/anthropic_adapter.py + adapter.py edit + 11 unit tests + 1 integration |
| **Day 4** | AP-8 lint rule + 100% 主流量 e2e + SLO 量測 + retro + closeout + 17.md §4.1 + Phase 52 README | 8h | check_promptbuilder_usage.py + lint tests + e2e + retrospective.md + closeout |

**總估時**：~31h；預期 actual 8-10h（V2 cumulative pattern 24-28%）

> **Day 0 起跑前確認項**：
> - 用戶 approve plan（本檔）
> - 用戶 approve checklist
> - 用戶確認可開 branch `feature/phase-52-sprint-2-cat5-prompt-builder`

---

## 7. Sprint 結構決策（rolling）

### 決策 1：6 大支柱齊出，不分批

**選擇**：DefaultPromptBuilder + 3 PositionStrategy + Memory injection + CacheBreakpoint + Loop integration + AP-8 lint rule 一併進 52.2。

**理由**：6 者高度耦合 — Builder 依賴 Strategy + Memory + Cache；Loop 依賴 Builder；lint rule 依賴 Loop + Builder 完成才能驗證。分批會反覆改 Loop integration 與 lint 範圍。範疇 5 達 Level 4 必須一次到位。

### 決策 2：Anthropic adapter 用 mock，不寫 real adapter

**選擇**：52.2 建 `adapters/_mock/anthropic_adapter.py`（test-only mock）；不建 `adapters/anthropic/` real adapter。

**理由**：real Anthropic adapter 屬 Phase 50+ Provider 擴充範圍，且需要實際 anthropic SDK + API key + integration test infra。52.2 範圍是「PromptBuilder 接通 cache_breakpoints 機制」，mock 足以驗證 marker correctness（contract test）。Real adapter 在 Phase 50+ canary 處理。

### 決策 3：AP-8 lint rule 從 Day 4 開始 enforce（不漸進）

**選擇**：Day 4.1 寫 lint rule + 同 Day 在 CI 直接 enforce（PR fail）；不採「先 warning → 後 error」漸進策略。

**理由**：52.2 Day 3 已完成 Loop integration 替換；agent_harness/** 應該已無 ad-hoc messages 組裝（除白名單外）。漸進 enforce 會給 AP-8 違規空間 → 違反「centralize PromptBuilder」目標。Allowlist 機制提供必要的 escape hatch（tests / mocks）。

### 決策 4：Position Strategy default = LostInMiddleAware

**選擇**：DefaultPromptBuilder 預設 `position_strategy=LostInMiddleStrategy()`；caller 可 override。

**理由**：lost-in-middle 是業界共識（per 01-spec §範疇 5）；20+ turn 對話下重要 system + user 容易被丟到中段被忽略。Naive 策略保留給 debug 用；ToolsAtEnd 給特定 model（如 gpt-4o）需要時 override。

### 決策 5：Cache Policy default = 全 cache enabled（除 recent_turns）

**選擇**：DefaultPromptBuilder 預設 `cache_policy=CachePolicy()`（per 52.1 default：cache_system=True / cache_tools=True / cache_memory=True / cache_recent_turns=False / ttl=300s）。

**理由**：穩態 cache hit > 50% 驗收依賴此 default；recent_turns 變動快不 cache 是業界共識。

---

## 8. 風險與緩解

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|----------|
| AP-8 lint rule 過嚴 → 既有 50.x / 51.1 contract test callers 需大量改 | Medium | High（regression）| Day 4.1 lint rule 先在 dry-run mode 跑全 codebase；white-list `tests/**` + `_testing/**` + `contract_test_*.py`；發現 violation 時逐個 case-by-case decide allowlist 或改寫 |
| 5 layer × 3 time scale 真注入 e2e 需要 51.2 MemoryStore 全跑通 | Medium | High（測試難度高）| Day 2 用 InMemoryStore + 預灌 13 cell fixture；不依賴 real DB；e2e 用 deterministic seed |
| Anthropic `cache_control` 注入無 real provider 驗證 | Medium | Medium | 用 mock anthropic adapter 驗 marker correctness（contract test）；real 驗證留 Phase 56 canary（已記 retrospective） |
| Loop integration 破壞 50.x baseline | Low | Critical | `prompt_builder: PromptBuilder \| None = None` default → fallback 到 50.x ad-hoc 組裝；Day 3.2 強制跑 50.x 10/10 baseline |
| LostInMiddleStrategy 位置精準度不達 95% | Low | Medium | Day 1.2 strategy unit test 用 50 個 mock prompt 跑全；不達 95% 觸發 strategy 邏輯 review |
| Memory retrieval 失敗（DB down）→ PromptBuilder fail-stop 害 Loop | Medium | High | DefaultPromptBuilder._inject_memory_layers 包 try/except；失敗時降級為 system + tools + conversation only + emit warning log |
| Day 4 過載（lint + e2e + retro + closeout 一併做）| Medium | Medium | 容許滑到 Day 5（rolling 紀律允許）；retro 必跑；lint rule 寫得好則 e2e 有現成驗證機制 |

---

## 9. 啟動條件

- [x] Sprint 52.1 closeout 完成（merge 到 main `a45fd2f2`，pushed origin）✅
- [x] 49.1 PromptBuilder ABC stub 存在於 `prompt_builder/_abc.py`（簽名升級基準）✅
- [x] 51.2 MemoryRetrieval ABC + InMemoryStore 已 ship（PromptBuilder memory injection 依賴）✅
- [x] 52.1 PromptCacheManager ABC + InMemoryCacheManager 已 ship（PromptBuilder cache integration 依賴）✅
- [x] 52.1 TokenCounter（3 impl）已 ship（PromptBuilder token estimation 依賴）✅
- [x] V2 規劃文件 17.md §1.1 / §2.1 / §4.1 確認可加 / 升級 row（無已存在衝突）✅
- [x] 52.1 retrospective Action Items 處理狀態確認（AI-6 / AI-7 / AI-9 / AI-10）：
  - AI-6（grep `_contracts/prompt.py` + Cat 5 既有）✅ Day 0 已完成 — 確認 49.1 stub + PromptArtifact 簽名
  - AI-7（PromptBuilder inject TokenCounter）✅ 本 sprint Day 1.6 處理
  - AI-9（ClaudeTokenCounter real anthropic tokenizer）⏸ Phase 50+；不阻 52.2
  - AI-10（Cat 12 Tracer span for ContextCompacted）⏸ Phase 53.x；不阻 52.2
- [ ] 用戶 approve plan（本檔）+ checklist
- [ ] 用戶確認可開 branch `feature/phase-52-sprint-2-cat5-prompt-builder`

---

**Last Updated**：2026-05-01（Day 0 起草完成 + W3 audit 修補：§2.4-§2.6 + §4 加跨切面紀律 + §10 Audit Carryover；待用戶 approve）
**Maintainer**：用戶 + AI 助手共同維護

---

## 10. Audit Carryover

**來源**：`claudedocs/5-status/v2-audit-2026-04/V2-AUDIT-WEEK3-SUMMARY.md`（2026-05-01）+ W3-0-CARRYOVER.md / W3-2-PHASE50-2.md / W1+W2 SUMMARY

> **Process drift 警告**（per W3-0）：W1+W2 P1 8 項中 7 項在後續 5 sprint dropped（0% 進入 sprint planning）。W1-2 #2 JWT carryover 5 sprint dropped 直接導致 W3-2 chat router 重複違反同一 multi-tenant 鐵律。為避免重蹈，本 plan 加 §10 Audit Carryover 必填段落（per audit prompt §6 template）。

### 10.1 Cleanup Sprint P0 排程（52.2 不耦合；獨立 session 並行執行）

> **詳細 sprint plan template**：[`claudedocs/5-status/v2-audit-2026-04/V2-AUDIT-CLEANUP-SPRINT-TEMPLATE.md`](../../../../claudedocs/5-status/v2-audit-2026-04/V2-AUDIT-CLEANUP-SPRINT-TEMPLATE.md)（593 行；Part 1 plan + Part 2 7-day checklist + Part 3 客製檢查清單）

Cleanup 由獨立 session 採用此 template 執行（user 安排 cleanup session）。本 sprint（52.2）**不阻塞於 cleanup 進度**，但：
- 52.2 retrospective **必答**「P0 進度」段落（per process fix #2 / plan §10.3）
- Phase **53.1 啟動前 cleanup 必須 done**（worker fork 後修補成本翻倍 — per W3 §8）
- W4 audit 將**同時驗證** 52.2 + cleanup 結果

| # | P0 Item | Cleanup Owner | Effort | 詳見 |
|---|---------|--------------|--------|------|
| 1 | 🔴 chat router multi-tenant 隔離（Depends + SessionRegistry tenant-scoped + integration test 開）| user 開新 session（建議併 #2 為 `cleanup-multi-tenant`）| 1-2 days | template Part 1 §User Story 1 + Part 2 Day 1-2 |
| 2 | 🔴 chat handler TraceContext.create_root() propagate | 同上（合併 session）| half day | template Part 1 §User Story 2 + Part 2 Day 2 |
| 3 | 🔴 `scripts/verify_audit_chain.py` + cron + alert（5 sprint dropped）| user 開新 session（`cleanup-audit-hash`）| 2-3 days | template Part 1 §User Story 3 + Part 2 Day 3-5 |
| 4 | 🔴 JWT 替換 X-Tenant-Id header（5 sprint dropped）| user 開新 session（`cleanup-jwt`）| 1-2 days | template Part 1 §User Story 4 + Part 2 Day 5-6 |

**建議分拆**（per audit session prompt §「轉達 user」）：
- 一個 session 處理 P0 #1+#2（chat router 合併修改，2 day）
- 一個 session 處理 P0 #3（verify_audit_chain，2-3 day）
- 一個 session 處理 P0 #4（JWT replace，1-2 day）
- 或單一 session 跑完整 7 day sprint

**52.2 與 P0 的耦合分析**：
- PromptBuilder 是 Cat 5 純內部組件，**不耦合** chat router / SessionRegistry / JWT middleware
- 52.2 內部守住「memory 查詢必傳 tenant_id」+「trace_context 沿鏈傳」即可（已在 §2.5 / §2.6 / §4 落地）
- 52.2 完成後 PromptBuilder 在 cleanup sprint 修 chat router 時自動受惠（chat router 接 Loop with PromptBuilder）

**Cleanup session onboarding prompt**：見本 sprint workflow handoff（user 開 cleanup session 時轉達；包含必讀 5 文件 + Step 1-5 執行流程 + 4 紀律 + 環境說明 + 完成回報 5 項）

### 10.2 本 sprint 設計時 mindful 的跨切面紀律

| 紀律 | 落地位置 | 驗收 |
|------|---------|------|
| ✅ PromptBuilder 簽名含 `trace_context: TraceContext \| None = None` | plan §2.2 ABC 簽名 + §2.4 build() 範例 | DoD §4「範疇 12 跨切面驗收」第 1 條 |
| ✅ Memory 查詢強制 `tenant_id` 必傳 | plan §2.5 `retrieve(tenant_id=...)` | Day 2.2 4 紅隊測試 |
| ✅ trace_context 沿鏈傳遞至 memory_retrieval / cache_manager（不可斷裂）| plan §2.4 / §2.5 / §2.6 全 propagate | DoD §4「範疇 12 跨切面驗收」第 2 條 |
| ✅ `build()` emit tracer span + duration metric | plan §2.4 `tracer.start_span("prompt_builder.build")` | DoD §4「範疇 12 跨切面驗收」第 3 條 |
| ✅ 測試用 real PostgreSQL（5×3 矩陣 integration）| plan §6 Day 2 標 real PG via docker；Day 2.6 task | DoD §4「多租戶 / 安全驗收」第 6 條 |
| ✅ 禁止 process-wide memory cache fallback | plan §2.5 三鐵律明文 | DoD §4「多租戶 / 安全驗收」第 5 條 |
| ✅ LLM Provider Neutrality（無 openai/anthropic import）| plan §4 / Day 4.7 | grep 0 leak |
| ✅ Single-source 型別（從 `_contracts/` import）| plan §2 全段 | mypy strict + 17.md sync |

### 10.3 本 sprint retrospective 必須回答（Day 4.9 落地）

retrospective.md 必填段落「Audit Debt」：

1. **是否守住 §10.2 跨切面紀律？** 任何砍 scope（如 trace_context 未傳 / process-wide cache 出現 / real PG 改 mock）必須在 retrospective 透明列出（不可隱形砍如 50.2 TraceContext 案例）
2. **§10.1 4 P0 在 cleanup sprint 進度如何？** 列 GitHub issue / cleanup sprint plan 連結
3. **新增 audit findings？** 本 sprint implementation 過程若發現 W4+ audit 應抓的 issue，主動列出（避免 self-audit blind spot）
4. **Process 修補進度**：
   - sprint plan template 加 Audit Carryover 段落？
   - retrospective template 加 Audit Debt 段落？
   - GitHub issue per P0/P1 建立？

### 10.4 W3 P1 累計（52.2 不處理；標 owner + sprint）

| # | P1 Item | 來源 | Effort | Sprint |
|---|---------|------|--------|--------|
| 5 | W1-2 #3 刪舊 stub `backend/src/middleware/tenant.py` | W1-2 | < 1h | Cleanup sprint |
| 6 | W2-1 #4 寫 `adapters/azure_openai/tests/test_integration.py` | W2-1 | 1 day | Cleanup sprint |
| 7 | W2-1 #5 CI lint scope 擴大（加 `business_domain/` / `platform_layer/` / `api/`）| W2-1 | < 1h | Cleanup sprint |
| 8 | W2-2 #6 requirements.txt 清 Celery / 加 temporalio TODO | W2-2 | 30 min | Cleanup sprint |
| 9 | W2-2 #7 統一 worker 目錄（`platform_layer/workers/` ↔ `runtime/workers/` 二選一）| W2-2 | half day | Cleanup sprint 或 Phase 53.1 |

### 10.5 P2 backlog（不阻 52.2，列 reference）

- W2-2 #8 AgentLoopWorker rename / docstring 警告 → 53.1
- W3-1 LoopState frozen + reducer pattern → 53.1（CARRY-007/009）
- W3-1 ToolCallExecuted/Failed events owner 遷移 Cat 1 → Cat 2 → 51.1 已標
- W3-2 worker factory consumer wire → 51.x（解 AP-2 邊緣）
- ProviderRouter 雛形 + `contract_test_base.py` → W2-1 P2

### 10.6 決策（per audit prompt §7）

**選定 Option B**：52.2 + 並行 cleanup sprint
- **理由**：(a) 52.2 PromptBuilder 不耦合 chat router 等 P0 範圍；(b) Phase 51.x / 52.x 可推進（W3 §8 判定）；(c) cleanup sprint 由其他 session 並行；(d) 53.1 啟動前必清完
- **風險**：cleanup 又被 drop（重蹈 W3-0 carryover）→ 緩解：本 plan §10.3 retrospective 必答 P0 進度 + §8 process 修補（sprint template + retro template + GitHub issue）

### 10.7 Process 修補同意項（per audit prompt §8）

- ✅ 同意 sprint plan template 加 Audit Carryover 必填段落（本 plan §10 即落地範本）
- ✅ 同意 retrospective template 加 Audit Debt 必填段落（Day 4.9 落地）
- ⏸ GitHub issue per P0/P1 — 待用戶決定（需 GitHub repo 設定 + issue label workflow）
- ✅ 同意每月 Audit Status Review（process 機制留 cleanup sprint plan 落地）
- ✅ 同意 audit 自身定期 re-verify（每 2-3 sprint 跑一次；下次 Week 4 已排）
