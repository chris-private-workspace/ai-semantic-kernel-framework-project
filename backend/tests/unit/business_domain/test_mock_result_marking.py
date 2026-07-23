"""
File: backend/tests/unit/business_domain/test_mock_result_marking.py
Purpose: Sprint 57.167 (de-Potemkin 1) — mock-sourced business tool results declare
    themselves, and nothing else changes.
Category: tests / business_domain
Scope: Phase 57 / Sprint 57.167 (US-2)

Description:
    `business_domain_mode` defaults to "mock", and before this sprint a fabricated
    business answer was indistinguishable from a real one. `register_all_business_tools`
    now wraps ONLY the 18 tools it registers, ONLY in mock mode, with a marker that
    keeps the payload valid JSON.

    The four things that must hold (and the four ways this could go wrong):
      - T1/T2  the marker lands, and the payload stays parseable + otherwise intact
      - T3     mode="service" wraps NOTHING (production path byte-identical)
      - T4     co-registered builtins (echo etc.) are never swept in by the key-diff
      - T5     the wrapper does not break the executor's 1-arg/2-arg dispatch —
               asserted through the REAL ToolExecutorImpl, not the wrapper alone
      - T6-T10 dict / non-JSON / array shapes: an ARRAY marks every object element
               (the drive-through caught mock_incident_list returning a bare JSON
               array — an object-only branch shipped every *_list tool UNMARKED)

Created: 2026-07-23 (Sprint 57.167)
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from agent_harness._contracts import (
    ConcurrencyPolicy,
    ExecutionContext,
    RiskLevel,
    ToolAnnotations,
    ToolCall,
    ToolHITLPolicy,
    ToolSpec,
)
from agent_harness.tools import ToolExecutorImpl, ToolRegistryImpl
from business_domain._register_all import (
    _MOCK_KEY,
    _MOCK_PREFIX,
    _mark_mock_result,
    register_all_business_tools,
)


def _spec(name: str) -> ToolSpec:
    return ToolSpec(
        name=name,
        description=f"test spec {name}",
        input_schema={"type": "object", "properties": {}},
        annotations=ToolAnnotations(read_only=True, destructive=False),
        concurrency_policy=ConcurrencyPolicy.READ_ONLY_PARALLEL,
        hitl_policy=ToolHITLPolicy.AUTO,
        risk_level=RiskLevel.LOW,
    )


def _call(name: str) -> ToolCall:
    return ToolCall(id="c1", name=name, arguments={})


class _FakeFactory:
    """Stand-in for BusinessServiceFactory — service mode only needs a provider to exist."""

    def __getattr__(self, name: str) -> Any:  # noqa: ANN401 — never called in these tests
        raise NotImplementedError(name)


# === T1/T2 — the marker lands and the payload survives =====================


@pytest.mark.asyncio
async def test_json_object_result_gains_marker_and_stays_valid_json() -> None:
    """T1: the real shape (every domain returns json.dumps(...)) — marked, still parseable."""

    async def handler(call: ToolCall) -> str:
        return json.dumps({"incident_id": "INC-1", "severity": "high", "nested": {"a": 1}})

    out = await _mark_mock_result(handler)(_call("mock_incident_get"))

    assert isinstance(out, str)
    payload = json.loads(out)  # would raise if we had prefixed the string
    assert payload[_MOCK_KEY] is True


@pytest.mark.asyncio
async def test_marking_preserves_every_original_key() -> None:
    """T2: marking is ADDITIVE — no key dropped, no value reshaped."""
    original = {"incident_id": "INC-1", "severity": "high", "nested": {"a": 1}, "list": [1, 2]}

    async def handler(call: ToolCall) -> str:
        return json.dumps(original)

    payload = json.loads(await _mark_mock_result(handler)(_call("mock_incident_get")))

    assert {k: payload[k] for k in original} == original


# === T3/T4 — applied to exactly the right handlers =========================


def test_service_mode_wraps_nothing() -> None:
    """T3: the production pathway is byte-identical to pre-57.167 (no wrapper at all)."""
    registry, handlers = ToolRegistryImpl(), {}
    register_all_business_tools(
        registry, handlers, mode="service", factory_provider=lambda: _FakeFactory()
    )

    assert handlers
    assert all(getattr(h, "__wrapped__", None) is None for h in handlers.values())


def test_key_diff_never_marks_co_registered_builtins() -> None:
    """T4: callers pass a handlers dict already holding echo / sandbox / memory / todos.

    Marking is by key-diff, so those must come back as the very same objects.
    """

    async def echo_like(call: ToolCall) -> str:
        return "plain echo"

    registry, handlers = ToolRegistryImpl(), {"echo_tool": echo_like}
    register_all_business_tools(registry, handlers, mode="mock")

    assert handlers["echo_tool"] is echo_like  # identity — not merely equal
    business = set(handlers) - {"echo_tool"}
    assert len(business) == 18
    assert all(getattr(handlers[n], "__wrapped__", None) is not None for n in business)


# === T5 — the wrapper must not break executor dispatch =====================


@pytest.mark.asyncio
async def test_arity_preserved_through_the_real_executor() -> None:
    """T5: the load-bearing one.

    ToolExecutorImpl picks 1-arg vs 2-arg dispatch from inspect.signature
    (executor.py:320). A naked `async def w(*args)` wrapper would report 0
    positional params, so a context-taking handler would silently lose its
    ExecutionContext. functools.wraps keeps the original signature visible.
    """
    seen: dict[str, Any] = {}

    async def ctx_handler(call: ToolCall, context: ExecutionContext) -> str:
        seen["tenant_id"] = context.tenant_id
        return json.dumps({"ok": True})

    registry = ToolRegistryImpl()
    registry.register(_spec("ctx_tool"))
    executor = ToolExecutorImpl(
        registry=registry, handlers={"ctx_tool": _mark_mock_result(ctx_handler)}
    )

    ctx = ExecutionContext(tenant_id="t-42")
    result = await executor.execute(_call("ctx_tool"), context=ctx)

    assert result.success is True
    assert seen["tenant_id"] == "t-42"  # the context actually arrived
    assert json.loads(result.content)[_MOCK_KEY] is True


@pytest.mark.asyncio
async def test_single_arg_handler_still_dispatches() -> None:
    """T5b: the shape all 18 handlers currently have (1-arg) keeps working."""

    async def plain(call: ToolCall) -> str:
        return json.dumps({"ok": True})

    registry = ToolRegistryImpl()
    registry.register(_spec("plain_tool"))
    executor = ToolExecutorImpl(
        registry=registry, handlers={"plain_tool": _mark_mock_result(plain)}
    )

    result = await executor.execute(_call("plain_tool"))

    assert result.success is True
    assert json.loads(result.content)[_MOCK_KEY] is True


# === T6-T10 — other return shapes ========================================


@pytest.mark.asyncio
async def test_dict_result_gets_additive_marker() -> None:
    """T6: ToolHandler may return a dict — mark additively, reshape nothing."""

    async def handler(call: ToolCall) -> dict[str, Any]:
        return {"a": 1}

    out = await _mark_mock_result(handler)(_call("x"))

    assert out == {"a": 1, _MOCK_KEY: True}


@pytest.mark.asyncio
async def test_non_json_string_falls_back_to_prefix() -> None:
    """T7: a plain-text result has nowhere to put a key — prefix it instead."""

    async def handler(call: ToolCall) -> str:
        return "not json at all"

    out = await _mark_mock_result(handler)(_call("x"))

    assert out == _MOCK_PREFIX + "not json at all"


@pytest.mark.asyncio
async def test_json_array_of_objects_marks_every_element() -> None:
    """T8: the shape the DRIVE-THROUGH caught (2026-07-23).

    `mock_incident_list` returns a bare JSON array — the first implementation
    left arrays untouched, so every `*_list` tool shipped UNMARKED while the unit
    suite was green. Mark each object element; the array shape is preserved so
    callers that json.loads it still get a list.
    """

    async def handler(call: ToolCall) -> str:
        return json.dumps([{"id": "inc_003"}, {"id": "inc_001"}])

    payload = json.loads(await _mark_mock_result(handler)(_call("mock_incident_list")))

    assert isinstance(payload, list) and len(payload) == 2
    assert all(item[_MOCK_KEY] is True for item in payload)
    assert [item["id"] for item in payload] == ["inc_003", "inc_001"]


@pytest.mark.asyncio
async def test_json_array_of_scalars_left_untouched() -> None:
    """T9: no object to carry the key → leave it rather than reshape it."""

    async def handler(call: ToolCall) -> str:
        return json.dumps([1, 2, 3])

    out = await _mark_mock_result(handler)(_call("x"))

    assert json.loads(out) == [1, 2, 3]


@pytest.mark.asyncio
async def test_list_result_marks_every_element() -> None:
    """T10: a handler returning a raw list (not a JSON string) is marked the same way."""

    async def handler(call: ToolCall) -> Any:
        return [{"a": 1}, {"b": 2}]

    out = await _mark_mock_result(handler)(_call("x"))

    assert out == [{"a": 1, _MOCK_KEY: True}, {"b": 2, _MOCK_KEY: True}]
