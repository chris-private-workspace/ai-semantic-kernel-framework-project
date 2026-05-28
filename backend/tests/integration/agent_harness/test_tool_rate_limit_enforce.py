"""
File: backend/tests/integration/agent_harness/test_tool_rate_limit_enforce.py
Purpose: Integration tests — Cat 2 tool-layer rate-limit enforcement (Sprint 57.58 Track B).
Category: Tests / Integration / 範疇 2 (Tool Layer)
Scope: Sprint 57.58 Day 1 Track B

Description:
    Verifies the ToolExecutorImpl pre-call rate-limit gate + the
    RedisToolRateLimitGate adapter (fakeredis-backed):
    - tool_allowed: under-budget tool call executes normally
    - tool_blocked: over-budget call returns a terminal ToolResult whose
      error_class classifies FATAL via DefaultErrorPolicy (no LLM retry)
    - per_tool_isolation: exhausting tool A's budget does NOT block tool B
    - no_tenant_skip: a call with no tenant_id in context bypasses the gate

    The gate's DB read (tenant.meta_data["rate_limits"]) is patched so the
    tests are DB-free; the Redis sliding-window path is real (fakeredis).

Created: 2026-05-28 (Sprint 57.58 Day 1)

Modification History (newest-first):
    - 2026-05-28: Initial creation (Sprint 57.58 Track B — tool-call rate enforcement)
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from fakeredis.aioredis import FakeRedis

from agent_harness._contracts import ExecutionContext, ToolCall, ToolSpec
from agent_harness._contracts.errors import RateLimitExceededError
from agent_harness._contracts.tools import ToolAnnotations
from agent_harness.error_handling import DefaultErrorPolicy, ErrorClass
from agent_harness.tools import ToolExecutorImpl, ToolRegistryImpl
from platform_layer.tenant.rate_limit_counter import RedisRateLimitCounter
from platform_layer.tenant.tool_rate_limit_gate import RedisToolRateLimitGate

pytestmark = pytest.mark.asyncio


def _spec(name: str) -> ToolSpec:
    return ToolSpec(
        name=name,
        description=f"test spec {name}",
        input_schema={
            "type": "object",
            "properties": {"q": {"type": "string"}},
            "required": ["q"],
        },
        annotations=ToolAnnotations(read_only=True, destructive=False),
    )


def _call(name: str, call_id: str = "c1") -> ToolCall:
    return ToolCall(id=call_id, name=name, arguments={"q": "hi"})


async def _ok_handler(call: ToolCall) -> str:
    return f"echoed:{call.arguments.get('q')}"


def _registry(*names: str) -> ToolRegistryImpl:
    reg = ToolRegistryImpl()
    for n in names:
        reg.register(_spec(n))
    return reg


@pytest.fixture
def fake_redis() -> FakeRedis:
    return FakeRedis(decode_responses=False)


def _gate_with_limits(
    fake_redis: FakeRedis,
    limits: dict[str, tuple[int, int]],
) -> RedisToolRateLimitGate:
    """RedisToolRateLimitGate whose DB read is patched to fixed limits."""
    gate = RedisToolRateLimitGate(RedisRateLimitCounter(fake_redis))

    async def _fake_load(_tenant_id: Any) -> dict[str, tuple[int, int]]:
        return dict(limits)

    gate._load_tool_limits = _fake_load  # type: ignore[method-assign]
    return gate


async def test_tool_allowed_under_budget(fake_redis: FakeRedis) -> None:
    """Under the tool_calls budget → the tool executes normally."""
    gate = _gate_with_limits(fake_redis, {"tool_calls": (5, 60)})
    reg = _registry("search")
    exe = ToolExecutorImpl(registry=reg, handlers={"search": _ok_handler}, rate_limit_gate=gate)
    ctx = ExecutionContext(tenant_id=uuid4())
    result = await exe.execute(_call("search"), context=ctx)
    assert result.success is True
    assert result.content == "echoed:hi"


async def test_tool_blocked_over_budget_is_terminal(fake_redis: FakeRedis) -> None:
    """Over budget → terminal ToolResult that Cat 8 classifies FATAL (no retry)."""
    gate = _gate_with_limits(fake_redis, {"tool_calls": (1, 60)})
    reg = _registry("search")
    exe = ToolExecutorImpl(registry=reg, handlers={"search": _ok_handler}, rate_limit_gate=gate)
    ctx = ExecutionContext(tenant_id=uuid4())

    first = await exe.execute(_call("search", "c1"), context=ctx)
    assert first.success is True

    blocked = await exe.execute(_call("search", "c2"), context=ctx)
    assert blocked.success is False
    assert blocked.error_class == ("agent_harness._contracts.errors.RateLimitExceededError")
    assert "rate limit exceeded" in (blocked.error or "")

    # Cat 8 must classify this as FATAL so the loop does NOT retry the call.
    policy = DefaultErrorPolicy()
    assert policy.classify_by_string(blocked.error_class) is ErrorClass.FATAL
    assert (
        policy.classify(RateLimitExceededError(resource="tool_calls", limit=1, retry_after=60))
        is ErrorClass.FATAL
    )
    assert (
        policy.should_retry(
            RateLimitExceededError(resource="tool_calls", limit=1, retry_after=60),
            attempt=1,
        )
        is False
    )


async def test_per_tool_isolation(fake_redis: FakeRedis) -> None:
    """Exhausting tool A's per-tool budget does NOT block tool B."""
    gate = _gate_with_limits(
        fake_redis,
        {"tool_calls.alpha": (1, 60), "tool_calls.beta": (1, 60)},
    )
    reg = _registry("alpha", "beta")
    exe = ToolExecutorImpl(
        registry=reg,
        handlers={"alpha": _ok_handler, "beta": _ok_handler},
        rate_limit_gate=gate,
    )
    ctx = ExecutionContext(tenant_id=uuid4())

    # Exhaust alpha's budget (limit 1).
    assert (await exe.execute(_call("alpha", "a1"), context=ctx)).success is True
    blocked_alpha = await exe.execute(_call("alpha", "a2"), context=ctx)
    assert blocked_alpha.success is False

    # beta is a separate per-tool key → still allowed.
    assert (await exe.execute(_call("beta", "b1"), context=ctx)).success is True


async def test_no_tenant_skip(fake_redis: FakeRedis) -> None:
    """A call without tenant_id in context bypasses the gate entirely."""
    gate = _gate_with_limits(fake_redis, {"tool_calls": (1, 60)})
    reg = _registry("search")
    exe = ToolExecutorImpl(registry=reg, handlers={"search": _ok_handler}, rate_limit_gate=gate)
    # No ExecutionContext → ctx.tenant_id is None → gate not consulted.
    for i in range(5):
        result = await exe.execute(_call("search", f"c{i}"))
        assert result.success is True
