# Testing Rules

**Purpose**: 測試標準與 V2 11+1 範疇驗收規範。

**Category**: Development Process / Quality Assurance
**Created**: 2025
**Last Modified**: 2026-05-05
**Status**: Active

> **Modification History**
> - 2026-05-05: Sprint 55.6 triage cleanup — add §SAVEPOINT pattern (closes AD-Test-DB-Trigger)
> - 2026-05-04: Sprint 53.7 Day 1 — add §Module-level Singleton Reset Pattern (closes AD-Test-1; pattern from 53.6 Day 4 ServiceFactory consolidation event-loop-cache cascade fix)
> - 2026-04-28: Enhance for V2 — 新增範疇層級測試分工、主流量驗證、Contract Test、Multi-tenant Tests、Anti-Pattern Tests、Test Performance、Observability Tests
> - 2025: Initial V1 version (generic test rules)

---

## Test Commands

### ⚠️ Critical: Use `python -m pytest`, NOT bare `pytest`

Bare `pytest` does NOT add cwd to `sys.path`, so imports like `from tests.conftest import ...` fail
silently with `ModuleNotFoundError`. Always invoke pytest as a Python module.

```bash
# Backend — ALWAYS prefix with `python -m`
cd backend
python -m pytest                          # All tests
python -m pytest tests/unit/              # Unit tests only
python -m pytest -v --cov=src             # With coverage
python -m pytest tests/unit/test_file.py::test_function  # Single test

# Frontend
cd frontend
npm run test                    # Run tests
npm run test:coverage           # With coverage
```

> Source: V2 sprint-50-1 retrospective CARRY-001. Day 0.2 lost time to bare `pytest` failure mode.

---

## Test Organization

```
tests/
├── unit/                       # Unit tests (fast, isolated)
│   ├── orchestrator_loop/      # 範疇 1
│   ├── tools/                  # 範疇 2
│   ├── memory/                 # 範疇 3
│   ├── ...                     # 範疇 4-12
│   ├── adapters/               # Adapter contract tests
│   └── platform/               # Governance / identity
├── integration/                # Integration tests
│   ├── api/                    # API endpoint tests
│   └── multi_tenant/           # Multi-tenant isolation
├── e2e/                        # End-to-end (主流量)
└── conftest.py                 # Shared fixtures
```

---

## Test Naming Convention

```python
# Pattern: test_{action}_{scenario}_{expected_result}
def test_create_session_with_valid_data_returns_session():
    ...

def test_create_session_without_tenant_id_raises_unauthorized():
    ...
```

---

## Requirements

### Must Have
- Unit tests for all public functions
- Integration tests for API endpoints
- Edge case coverage
- Error condition testing

### Forbidden
- ❌ Skipping tests to make CI pass
- ❌ Deleting tests to "fix" failures
- ❌ Tests with hardcoded sleep()
- ❌ Tests that depend on execution order

---

## Mocking Guidelines

```python
# Use pytest fixtures for common mocks
@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)

# Use ChatClient mock (NOT openai/anthropic)
@pytest.fixture
def mock_chat_client():
    from adapters._testing.mock_clients import MockChatClient
    return MockChatClient(responses={...})
```

---

## Module-level Singleton Reset Pattern (Sprint 53.7+ — closes AD-Test-1)

**When you need this**: any module that exposes a lazily-initialized **module-level singleton** (e.g. via `_instance: X | None = None` + `def get_x()`). When `TestClient`-based integration tests run, each test fires up its own asyncio event loop. A singleton cached during test A holds references to event-loop-bound resources (DB session factories / asyncio Queues / Redis clients). When test B starts, the cache returns the dead instance → `RuntimeError: Event loop is closed` cascade.

**Source**: Sprint 53.6 Day 4 (US-5 ServiceFactory consolidation). Adding `service_factory.py` with module-level `_factory` cache made 5 governance / audit tests fail under the full suite even though each passed in isolation. Resolved by adding an autouse fixture in `tests/integration/api/conftest.py` calling `reset_service_factory()` before every test.

### When to apply

- ✅ Module exposes `get_x()` / `set_x()` / `reset_x()` triple, or any equivalent lazy-singleton pattern
- ✅ The singleton holds (directly or transitively) event-loop-bound resources: `asyncio.Queue` / async DB session factory / async Redis client / asyncio Lock
- ✅ Suite has 2+ tests that each acquire the singleton

**Don't apply** if the singleton holds only pure CPU values (e.g. cached config dict). Then there is no event-loop coupling and no cascade.

### Required pattern (autouse fixture per integration suite)

```python
# backend/tests/integration/<suite>/conftest.py
"""
Sprint 53.7+ pattern: per-suite autouse fixture resets module-level
singletons that hold event-loop-bound resources, so each test gets a
fresh instance bound to its own loop.

See .claude/rules/testing.md §Module-level Singleton Reset Pattern.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _reset_module_singletons() -> None:
    """Reset all known module-level singletons before each test."""
    # Add new resets here as singletons are introduced; keep this list
    # in sync with the catalog below.
    from platform_layer.governance.service_factory import reset_service_factory

    reset_service_factory()
    # ... future resets ...
```

### Scope rules

- **Per-suite, NOT global**: place the fixture in the integration suite's `conftest.py` (e.g. `tests/integration/api/conftest.py`), not in the top-level `tests/conftest.py`. Unit tests under `tests/unit/` should not pay for resets they don't need.
- **autouse=True**: makes every test in the suite trigger the reset; explicit fixture wiring is too easy to miss for new tests.
- **No yield**: this is a pre-test hook; teardown is unnecessary because the next test's pre-test reset is the teardown.

### Known module-level singletons (catalog)

Update this list when you add a new singleton-style module. Each entry: `module path → reset function → singleton role`.

| Module | Reset function | Singleton role | Introduced |
|--------|----------------|----------------|------------|
| `platform_layer.governance.service_factory` | `reset_service_factory()` | HITLManager + RiskPolicy lazy cache; AuditQuery factory | Sprint 53.6 |
| _add new entries here_ | | | |

### Anti-patterns (do NOT do these instead)

- ❌ **Pytest fixtures rebuilding the singleton** with `monkeypatch.setattr(module, '_instance', None)`: brittle, hides the public reset API
- ❌ **Global fixture in top-level `tests/conftest.py`**: pays the reset cost for every unit test; pollutes test scope
- ❌ **Skipping affected tests with `@pytest.mark.skip("flaky")`**: hides the real bug; would be flagged by `04-anti-patterns.md` AP-9 verification
- ❌ **Refactoring singleton to be DI-only without reset**: removes the singleton but loses lazy-cache benefits; consider whether per-request DI is genuinely cheaper before refactoring

### Long-term direction

The pattern above is a **mitigation**, not a fix. The root-cause fix is to refactor singletons to be **DI-injected per request** (no module-level cache), which eliminates event-loop coupling entirely. ServiceFactory will be considered for this refactor if a 3rd singleton joins the catalog and the reset list becomes burdensome to maintain.

---

## SAVEPOINT Pattern for Post-Error Verification (Sprint 55.4+ — closes AD-Test-DB-Trigger)

**When you need this**: integration test deliberately triggers a DB error (e.g. constraint violation, deadlock-by-design, deliberately-bad row) and then needs to verify that **other state** persisted by the *pre-error* code path is still correct (audit chain row, guardrail event, soft-failure record). The naive `try/except` poisons the outer test transaction → all subsequent queries fail with `sqlalchemy.exc.PendingRollbackError` / `InFailedSqlTransaction`.

**Source**: Sprint 55.4 Day 3 D9 (5 real-DB integration tests for AD-Cat9-6; chain_verifier 100-row sanity test post-error path). Migration 0005 audit-chain triggers fire on the pre-error insert; without SAVEPOINT we couldn't read the chain state to confirm trigger fired before the deliberate error.

### Required pattern: `session.begin_nested()`

```python
import pytest
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError

@pytest.mark.asyncio
async def test_audit_chain_persists_despite_downstream_error(db_session):
    # Pre-error code path — should succeed; trigger fires here
    await db_session.execute(insert(audit_log).values(tenant_id=..., event="X"))

    # Wrap the deliberate-error block in a SAVEPOINT
    async with db_session.begin_nested():  # ← SAVEPOINT (auto-rollback on exception)
        try:
            await db_session.execute(
                insert(some_table).values(violates_constraint=True)
            )
        except IntegrityError:
            pass  # SAVEPOINT auto-rolls back; outer transaction still alive

    # Outer transaction still usable — verify pre-error state survived
    row = (await db_session.execute(select(audit_log))).scalar_one()
    assert row.chain_hash is not None
```

### Anti-patterns

- ❌ `try/except` without SAVEPOINT → poisons outer transaction; all subsequent queries raise `PendingRollbackError`
- ❌ Open a second `db_session` to bypass poisoning → loses tenant_id `SET LOCAL` context (per `multi-tenant-data.md`); RLS policy returns empty rows; test passes for the wrong reason
- ❌ `pytest-asyncio` `event_loop` fixture override to swap session mid-test → re-introduces event-loop cascade (see §Module-level Singleton Reset Pattern)

### When NOT to use

- Pure unit tests with no DB triggers / no audit chain → use `pytest.raises()` with mock
- Test where error propagation **is** the test goal (you want the outer transaction to roll back) → no SAVEPOINT needed

### Cross-reference

- `multi-tenant-data.md` §Audit chain triggers (Migration 0005)
- `04-anti-patterns.md` AP-9 verification (don't skip the failing case to dodge poisoning)

---

## Coverage Requirements（Baseline）

| Category | Minimum |
|----------|---------|
| Overall | 80% |
| Domain Layer (`agent_harness/`) | 90% |
| API Layer | 85% |
| Infrastructure | 70% |

詳細範疇對應見 `code-quality.md`。

---

## V2 新增：11+1 範疇測試分工矩陣

遵循「測試金字塔」（70% 單元 / 25% 整合 / 5% E2E）：

### 各範疇最低測試要求

| 範疇 | 單元測試 | 整合測試 | E2E 測試 | 主流量驗證 |
|------|---------|---------|---------|----------|
| 1. Orchestrator | ✅ 終止條件 × 5 | ✅ Loop + Adapter | ✅ 對話案例 | ✅ UnifiedChat-V2 完整鏈路 |
| 2. Tool Layer | ✅ ToolSpec 驗證 | ✅ 工具呼叫 | — | ✅ 工具執行可用性 |
| 3. Memory | ✅ 5 層順序 | ✅ Memory store | ✅ 跨 session 案例 | ✅ 租戶隔離 |
| 4. Context Mgmt | ✅ Token counter | ✅ 30+ turn compact | — | ✅ 百 turn 不 OOM |
| 5. Prompt Builder | ✅ 階層組裝 | ✅ Memory 真注入 | — | ✅ 無裸組 messages |
| 6. Output Parser | ✅ Tool call 解析 | ✅ 跨 provider 統一 | — | ✅ 實際 LLM 輸出 |
| 7. State Mgmt | ✅ Checkpoint 完整性 | ✅ HITL pause/resume | ✅ 失敗恢復 | ✅ 時間旅行 |
| 8. Error Handling | ✅ 4 類分類 | ✅ Retry + Backoff | ✅ 故障注入 | ✅ 降級行為 |
| 9. Guardrails | ✅ PII / jailbreak | ✅ Tripwire 觸發 | ✅ 三階段審批 | ✅ OWASP LLM Top 10 × 10 |
| 10. Verification | ✅ RulesBasedVerifier | ✅ LLMJudge subagent | ✅ 自動修正 | ✅ 無 verification 被擋 |
| 11. Subagent | ✅ 4 種模式 | ✅ Subagent dispatch | — | ✅ 並行 5 個不衝突 |
| **12. Observability** | ✅ 埋點覆蓋率 | ✅ Tracer 發出 | ✅ Trace 完整 | ✅ 每個範疇都埋點 |

---

## V2 新增：主流量驗證測試

所有端到端測試**必須**走完整鏈路：**API → Agent Loop → 結果返回**。

### ❌ 禁止做法

- 只測 service 層（繞過 API）
- 單獨測 tool（不在 Loop 內）
- 直接 import 內部 class，不走 HTTP

### ✅ 必須做法

從 `POST /api/v1/chat` 入口開始 → 完整流程 → HTTP 回應。

### 5 個關鍵 E2E 案例（最少）

| 案例 | 目標 | 驗收條件 |
|------|------|---------|
| **Session 建立** | 端點創建 + 返回 session_id | `201 Created` + 有效 session_id |
| **主迴圈執行** | 3-5 turn 對話 + 工具呼叫 | 每個 turn 事件流完整 |
| **工具呼叫** | 範疇 2 工具真實執行 | 工具結果回注 messages |
| **驗證失敗重試** | 範疇 10 自動修正 | 偵測 + 重新推理 + 通過 |
| **HITL 阻擋** | 敏感操作中斷 + 人工批准 | Tripwire → 等待批准 → 繼續 |

---

## V2 新增：Contract Test for Adapters

每個新 LLM provider adapter 必通過 contract test suite。

```python
# tests/integration/adapters/test_adapter_contract.py

@pytest.mark.contract
class TestAdapterContract:
    """每個 adapter 必須滿足契約。"""

    @pytest.mark.asyncio
    async def test_chat_returns_chat_response(self, adapter):
        response = await adapter.chat(
            messages=[Message(role="user", content="Hi")],
            tools=[],
        )
        assert isinstance(response, ChatResponse)
        assert response.content is not None

    @pytest.mark.asyncio
    async def test_stream_yields_events(self, adapter):
        events = []
        async for ev in adapter.stream(...):
            events.append(ev)
        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_count_tokens_accuracy(self, adapter):
        msg = Message(role="user", content="Hello " * 100)
        estimated = await adapter.count_tokens(messages=[msg])
        assert estimated > 0

    def test_get_pricing_returns_info(self, adapter):
        info = adapter.get_pricing()
        assert info.input_per_million > 0
        assert info.output_per_million > 0

    def test_supports_feature_returns_bool(self, adapter):
        assert isinstance(adapter.supports_feature("vision"), bool)

    def test_model_info_complete(self, adapter):
        info = adapter.model_info()
        assert info.context_window > 0
        assert info.provider is not None


@pytest.mark.contract
class TestAdapterCrossProvider:
    """跨 provider 功能等價性。"""

    @pytest.mark.asyncio
    async def test_same_prompt_both_providers(self):
        prompt = "What is 2+2?"
        azure_resp = await azure_adapter.chat(
            messages=[Message(role="user", content=prompt)],
            tools=[], temperature=0.0,
        )
        anthropic_resp = await anthropic_adapter.chat(
            messages=[Message(role="user", content=prompt)],
            tools=[], temperature=0.0,
        )
        assert azure_resp.content is not None
        assert anthropic_resp.content is not None
```

---

## V2 新增：Multi-tenant Tests（每個業務 endpoint 必須）

```python
@pytest.mark.multi_tenant
async def test_tenant_a_cannot_read_tenant_b_sessions():
    session_b = await create_session(tenant_id=TENANT_B_ID, ...)
    resp = client.get(
        f"/api/v1/sessions/{session_b.id}",
        headers={"Authorization": f"Bearer {TENANT_A_TOKEN}"},
    )
    assert resp.status_code == 404  # 隱藏存在

@pytest.mark.multi_tenant
async def test_row_level_security_enforced():
    """RLS：同一 DB 連線亦無法跨租戶。"""
    msg_b = await create_message(tenant_id=TENANT_B_ID, ...)
    async with db.session() as session:
        await session.execute(
            text("SET LOCAL app.tenant_id = :tid"),
            {"tid": str(TENANT_A_ID)}
        )
        result = await session.execute(select(Message).where(Message.id == msg_b.id))
        assert result.scalars().first() is None  # 查不到
```

詳見 `multi-tenant-data.md`。

---

## V2 新增：Anti-Pattern Tests

必須測試反模式避免：

```python
@pytest.mark.anti_pattern
async def test_ap7_30_turn_no_degradation():
    """AP-7：30+ turn 對話不劣化（token 增長控制）。"""
    session = await create_session(...)
    baseline_tokens = ...
    for i in range(35):
        resp = await agent_loop.run(
            messages=[Message(role="user", content=f"Question {i}")],
            ...
        )
        assert resp.tokens_used <= baseline_tokens * 1.1

@pytest.mark.anti_pattern
async def test_ap9_no_verification_blocked():
    """AP-9：沒有 verification 的輸出被擋。"""
    loop_without_verifier = AgentLoop(verifier=None)
    with pytest.raises(VerificationSkippedError):
        await loop_without_verifier.run(...)

@pytest.mark.anti_pattern
def test_ap2_no_orphan_code():
    """AP-2：所有 agent_harness 代碼可從 api/ 追蹤到。"""
    reachable = find_reachable_modules(entry_point="src/api")
    all_modules = list_all_agent_harness_modules()
    orphans = set(all_modules) - reachable
    assert not orphans, f"Orphan modules: {orphans}"
```

---

## V2 新增：Test Performance SLO

| 層級 | 目標 | 上限 |
|------|------|------|
| 單元測試套件 | < 30 秒 | 60 秒 |
| 整合測試套件 | < 3 分鐘 | 5 分鐘 |
| E2E（無 real LLM） | < 5 分鐘 | 10 分鐘 |
| E2E（含 real LLM） | < 10 分鐘 | 20 分鐘 |

---

## V2 新增：Observability Tests（範疇 12）

### 埋點覆蓋率測試

```python
@pytest.mark.observability
async def test_all_categories_emit_traces():
    """每個範疇都埋點，無遺漏。"""
    with capture_spans() as collector:
        await agent_loop.run(...)
        spans = collector.spans

    emitted_categories = {s.attributes.get("category_id") for s in spans}
    EXPECTED_CATEGORIES = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}
    assert emitted_categories == EXPECTED_CATEGORIES, \
        f"Missing categories: {EXPECTED_CATEGORIES - emitted_categories}"

@pytest.mark.observability
async def test_tracer_called_in_tools():
    """Tool 執行時都調用 tracer。"""
    with capture_spans() as collector:
        await tool_registry.execute(tool_name="salesforce_query", ...)
        spans = collector.spans

    tool_spans = [s for s in spans if s.name.startswith("tool_")]
    assert len(tool_spans) >= 2  # 至少 requested + executed

@pytest.mark.observability
async def test_trace_context_propagation():
    """trace_id 不斷裂沿鏈傳遞。"""
    root_trace = TraceContext.create_root()
    with capture_spans() as collector:
        await agent_loop.run(..., trace_context=root_trace)

    # 所有 span 共享同一 trace_id
    trace_ids = {s.trace_id for s in collector.spans}
    assert trace_ids == {root_trace.trace_id}
```

詳見 `observability-instrumentation.md`。

---

## 引用

- **11-test-strategy.md** — 測試金字塔 / DoD
- **01-eleven-categories-spec.md** — 範疇定義（含範疇 12）
- **04-anti-patterns.md** — AP-2 / AP-7 / AP-9
- **17-cross-category-interfaces.md** — Contract test 對應 ABC
- **multi-tenant-data.md** — 租戶隔離測試案例
- **observability-instrumentation.md** — 埋點測試
- **adapters-layer.md** — Adapter contract test
- **code-quality.md** — Coverage targets
