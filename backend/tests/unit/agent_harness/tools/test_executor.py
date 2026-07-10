"""
File: backend/tests/unit/agent_harness/tools/test_executor.py
Purpose: Unit tests for ToolExecutorImpl — permission gate / JSONSchema / concurrency.
Category: Tests / 範疇 2 (Tool Layer)
Scope: Phase 51 / Sprint 51.1 Day 2.4 + 2.5

Created: 2026-04-30
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import pytest

from agent_harness._contracts import (
    ConcurrencyPolicy,
    RiskLevel,
    ToolAnnotations,
    ToolCall,
    ToolHITLPolicy,
    ToolSpec,
)
from agent_harness.tools import (
    ToolExecutorImpl,
    ToolRegistryImpl,
)

# === Fixtures =============================================================


def _spec(
    name: str,
    *,
    hitl: ToolHITLPolicy = ToolHITLPolicy.AUTO,
    risk: RiskLevel = RiskLevel.LOW,
    destructive: bool = False,
    concurrency: ConcurrencyPolicy = ConcurrencyPolicy.READ_ONLY_PARALLEL,
    schema: dict[str, Any] | None = None,
) -> ToolSpec:
    return ToolSpec(
        name=name,
        description=f"test spec {name}",
        input_schema=schema
        or {
            "type": "object",
            "properties": {"q": {"type": "string"}},
            "required": ["q"],
        },
        annotations=ToolAnnotations(read_only=not destructive, destructive=destructive),
        concurrency_policy=concurrency,
        hitl_policy=hitl,
        risk_level=risk,
    )


def _call(name: str, args: dict[str, Any] | None = None, call_id: str = "c1") -> ToolCall:
    return ToolCall(id=call_id, name=name, arguments=args or {"q": "hi"})


async def _ok_handler(call: ToolCall) -> str:
    return f"echoed:{call.arguments.get('q')}"


async def _slow_handler(call: ToolCall) -> str:
    await asyncio.sleep(0.1)  # 100ms
    return "slow_done"


async def _explode_handler(call: ToolCall) -> str:
    raise RuntimeError("boom")


# === Executor allow path (Sprint 57.124: gating moved to loop _cat9) ======


@pytest.mark.asyncio
async def test_allow_simple_read_only() -> None:
    reg = ToolRegistryImpl()
    spec = _spec("ok_read")
    reg.register(spec)
    exe = ToolExecutorImpl(registry=reg, handlers={"ok_read": _ok_handler})

    result = await exe.execute(_call("ok_read"))
    assert result.success is True
    assert result.content == "echoed:hi"


@pytest.mark.asyncio
async def test_executor_runs_always_ask_tool_no_gate() -> None:
    """Sprint 57.124: the executor no longer gates on hitl_policy — gating moved
    to the loop's _cat9 + per-tenant HITLPolicy. An ALWAYS_ASK tool runs through
    the handler at the executor layer (the loop escalates it upstream)."""
    reg = ToolRegistryImpl()
    reg.register(_spec("sensitive", hitl=ToolHITLPolicy.ALWAYS_ASK))
    exe = ToolExecutorImpl(registry=reg, handlers={"sensitive": _ok_handler})

    result = await exe.execute(_call("sensitive"))
    assert result.success is True
    assert result.content == "echoed:hi"


@pytest.mark.asyncio
async def test_executor_runs_destructive_high_risk_tool_no_gate() -> None:
    """Sprint 57.124: a destructive + HIGH-risk tool is NOT re-blocked by the
    executor (the removed PermissionChecker dim 3 used to hard-DENY it even after a
    human approved it). It runs through the handler; the loop's _cat9 + the
    destructive HIGH-floor own the escalate decision upstream."""
    reg = ToolRegistryImpl()
    reg.register(
        _spec(
            "wipe",
            destructive=True,
            hitl=ToolHITLPolicy.ALWAYS_ASK,
            risk=RiskLevel.HIGH,
            concurrency=ConcurrencyPolicy.SEQUENTIAL,
        )
    )
    exe = ToolExecutorImpl(registry=reg, handlers={"wipe": _ok_handler})

    result = await exe.execute(_call("wipe"))
    assert result.success is True


# === JSONSchema validation tests (Day 2.3) ================================


@pytest.mark.asyncio
async def test_schema_valid_arguments() -> None:
    reg = ToolRegistryImpl()
    reg.register(_spec("schema_ok"))
    exe = ToolExecutorImpl(registry=reg, handlers={"schema_ok": _ok_handler})

    result = await exe.execute(_call("schema_ok", {"q": "valid"}))
    assert result.success is True


@pytest.mark.asyncio
async def test_schema_invalid_missing_required_field() -> None:
    reg = ToolRegistryImpl()
    reg.register(_spec("strict"))
    exe = ToolExecutorImpl(registry=reg, handlers={"strict": _ok_handler})

    # missing required 'q'
    result = await exe.execute(_call("strict", {"wrong_key": "x"}))
    assert result.success is False
    assert "schema mismatch" in (result.error or "")


@pytest.mark.asyncio
async def test_schema_invalid_wrong_type() -> None:
    reg = ToolRegistryImpl()
    reg.register(_spec("strict_type"))
    exe = ToolExecutorImpl(registry=reg, handlers={"strict_type": _ok_handler})

    # q must be string, supplying int
    result = await exe.execute(_call("strict_type", {"q": 42}))
    assert result.success is False
    assert "schema mismatch" in (result.error or "")


@pytest.mark.asyncio
async def test_schema_validator_cached_per_spec() -> None:
    """Validator is built once per spec.name and reused across calls."""
    reg = ToolRegistryImpl()
    reg.register(_spec("cached"))
    exe = ToolExecutorImpl(registry=reg, handlers={"cached": _ok_handler})

    await exe.execute(_call("cached", {"q": "first"}))
    await exe.execute(_call("cached", {"q": "second"}))

    assert "cached" in exe._validator_cache  # noqa: SLF001 — verifying internal cache
    assert len(exe._validator_cache) == 1


# === Concurrency tests (Day 2.5) ==========================================


@pytest.mark.asyncio
async def test_batch_empty_returns_empty() -> None:
    reg = ToolRegistryImpl()
    exe = ToolExecutorImpl(registry=reg, handlers={})
    assert await exe.execute_batch([]) == []


@pytest.mark.asyncio
async def test_batch_read_only_parallel_runs_concurrently() -> None:
    """3 read-only-parallel calls × 100ms slow handler should finish in ~100ms (parallel), not ~300ms."""  # noqa: E501
    reg = ToolRegistryImpl()
    reg.register(_spec("ro_a", concurrency=ConcurrencyPolicy.READ_ONLY_PARALLEL))
    reg.register(_spec("ro_b", concurrency=ConcurrencyPolicy.READ_ONLY_PARALLEL))
    reg.register(_spec("ro_c", concurrency=ConcurrencyPolicy.READ_ONLY_PARALLEL))
    exe = ToolExecutorImpl(
        registry=reg,
        handlers={"ro_a": _slow_handler, "ro_b": _slow_handler, "ro_c": _slow_handler},
    )

    calls = [_call("ro_a", call_id="a"), _call("ro_b", call_id="b"), _call("ro_c", call_id="c")]
    t0 = time.monotonic()
    results = await exe.execute_batch(calls)
    elapsed = time.monotonic() - t0

    assert len(results) == 3
    assert all(r.success for r in results)
    # parallel: ~100ms; sequential would be ~300ms. Threshold 250ms allows OS jitter.
    assert elapsed < 0.25, f"expected parallel (<250ms), got {elapsed:.3f}s"


@pytest.mark.asyncio
async def test_batch_with_sequential_runs_serial() -> None:
    """Any SEQUENTIAL spec in batch forces full-batch sequential execution."""
    reg = ToolRegistryImpl()
    reg.register(_spec("seq_a", concurrency=ConcurrencyPolicy.SEQUENTIAL))
    reg.register(_spec("ro_b", concurrency=ConcurrencyPolicy.READ_ONLY_PARALLEL))
    reg.register(_spec("ro_c", concurrency=ConcurrencyPolicy.READ_ONLY_PARALLEL))
    exe = ToolExecutorImpl(
        registry=reg,
        handlers={"seq_a": _slow_handler, "ro_b": _slow_handler, "ro_c": _slow_handler},
    )

    calls = [_call("seq_a", call_id="a"), _call("ro_b", call_id="b"), _call("ro_c", call_id="c")]
    t0 = time.monotonic()
    results = await exe.execute_batch(calls)
    elapsed = time.monotonic() - t0

    assert len(results) == 3
    # serial: ~300ms; parallel would be ~100ms. Threshold 280ms guards against false-pass parallel.
    assert elapsed > 0.28, f"expected serial (>280ms), got {elapsed:.3f}s"


@pytest.mark.asyncio
async def test_batch_all_parallel_runs_concurrently() -> None:
    reg = ToolRegistryImpl()
    reg.register(_spec("p_a", concurrency=ConcurrencyPolicy.ALL_PARALLEL))
    reg.register(_spec("p_b", concurrency=ConcurrencyPolicy.ALL_PARALLEL))
    exe = ToolExecutorImpl(
        registry=reg,
        handlers={"p_a": _slow_handler, "p_b": _slow_handler},
    )

    t0 = time.monotonic()
    results = await exe.execute_batch([_call("p_a", call_id="a"), _call("p_b", call_id="b")])
    elapsed = time.monotonic() - t0

    assert len(results) == 2
    assert all(r.success for r in results)
    assert elapsed < 0.18, f"expected parallel, got {elapsed:.3f}s"


# === Edge case tests ======================================================


@pytest.mark.asyncio
async def test_unknown_tool_returns_error() -> None:
    reg = ToolRegistryImpl()
    exe = ToolExecutorImpl(registry=reg, handlers={})
    result = await exe.execute(_call("nonexistent"))
    assert result.success is False
    assert "unknown tool" in (result.error or "")


@pytest.mark.asyncio
async def test_handler_exception_propagated_via_result_error() -> None:
    reg = ToolRegistryImpl()
    reg.register(_spec("explodes"))
    exe = ToolExecutorImpl(registry=reg, handlers={"explodes": _explode_handler})

    result = await exe.execute(_call("explodes"))
    assert result.success is False
    assert "boom" in (result.error or "")


@pytest.mark.asyncio
async def test_handler_exception_writes_error_class() -> None:
    """Sprint 53.3 US-9 (AD-Cat8-3): exception path preserves original
    type as fully-qualified class name in ToolResult.error_class so
    DefaultErrorPolicy.classify_by_string() can recover ErrorClass.
    """
    reg = ToolRegistryImpl()
    reg.register(_spec("explodes"))

    # Custom exception with known module + qualname
    class CustomToolFault(RuntimeError):
        pass

    async def _custom_explode(_call_arg: object) -> str:
        raise CustomToolFault("boom-custom")

    exe = ToolExecutorImpl(registry=reg, handlers={"explodes": _custom_explode})

    result = await exe.execute(_call("explodes"))
    assert result.success is False
    assert result.error_class is not None
    # tests are run via pytest; class is defined in the test module so its
    # __module__ is the test file path. We only assert the qualname suffix
    # which is what `register_by_string` would key on.
    assert result.error_class.endswith(".CustomToolFault")


@pytest.mark.asyncio
async def test_non_exception_failure_has_no_error_class() -> None:
    """Sprint 53.3 US-9: error_class is None for non-exception failures
    (unknown tool / schema mismatch) since these paths use `_fail()`
    which doesn't set error_class.
    """
    reg = ToolRegistryImpl()
    exe = ToolExecutorImpl(registry=reg, handlers={})

    result = await exe.execute(_call("nonexistent"))
    assert result.success is False
    assert result.error_class is None  # not an exception


@pytest.mark.asyncio
async def test_no_handler_registered_returns_error() -> None:
    reg = ToolRegistryImpl()
    reg.register(_spec("orphan"))  # spec registered but no handler
    exe = ToolExecutorImpl(registry=reg, handlers={})

    result = await exe.execute(_call("orphan"))
    assert result.success is False
    assert "no handler" in (result.error or "")


# === Sprint 57.144 (research #7 Half B): structured-error reflection ========
# The CHAT_TOOL_ERROR_REFLECTION lever gates whether the failure ToolResult's
# LLM-visible `content` carries the typed reflection. Sprint 57.164 (Option B
# decouple): `error_taxonomy` is now classified ALWAYS (display metadata for the
# chat-v2 ToolBlock) regardless of the lever; only `content` is lever-gated (empty
# when OFF = byte-identical pre-57.144 LLM-visible behavior).


@pytest.mark.asyncio
async def test_reflection_off_handler_exception_content_byte_identical(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CHAT_TOOL_ERROR_REFLECTION", raising=False)
    reg = ToolRegistryImpl()
    reg.register(_spec("boom"))
    exe = ToolExecutorImpl(registry=reg, handlers={"boom": _explode_handler})

    result = await exe.execute(_call("boom"))
    assert result.success is False
    assert result.content == ""  # LLM-visible content byte-identical when OFF
    # Sprint 57.164 (Option B): taxonomy is classified even when the lever is OFF.
    assert result.error_taxonomy == "invocation"  # generic handler exception
    assert result.error_class == "builtins.RuntimeError"  # still set for Cat 8


@pytest.mark.asyncio
async def test_reflection_on_handler_exception_enriched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CHAT_TOOL_ERROR_REFLECTION", "1")
    reg = ToolRegistryImpl()
    reg.register(_spec("boom"))
    exe = ToolExecutorImpl(registry=reg, handlers={"boom": _explode_handler})

    result = await exe.execute(_call("boom"))
    assert result.success is False
    assert result.error_taxonomy == "invocation"  # generic handler exception
    assert "tool invocation error" in result.content
    assert "boom" in result.content  # the raw error is preserved
    assert result.error_class == "builtins.RuntimeError"  # Cat 8 retry signal intact


@pytest.mark.asyncio
async def test_reflection_on_unknown_tool_is_wrong_tool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CHAT_TOOL_ERROR_REFLECTION", "1")
    reg = ToolRegistryImpl()
    exe = ToolExecutorImpl(registry=reg, handlers={})

    result = await exe.execute(_call("nonexistent"))
    assert result.error_taxonomy == "wrong_tool"
    assert "wrong-tool error" in result.content


@pytest.mark.asyncio
async def test_reflection_on_schema_invalid_is_parameter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CHAT_TOOL_ERROR_REFLECTION", "1")
    reg = ToolRegistryImpl()
    reg.register(_spec("strict"))  # default schema requires "q"
    exe = ToolExecutorImpl(registry=reg, handlers={"strict": _ok_handler})

    bad = ToolCall(id="c1", name="strict", arguments={"wrong": 1})  # missing "q"
    result = await exe.execute(bad)
    assert result.error_taxonomy == "parameter"
    assert "parameter error" in result.content


@pytest.mark.asyncio
async def test_reflection_off_unknown_tool_content_byte_identical(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CHAT_TOOL_ERROR_REFLECTION", raising=False)
    reg = ToolRegistryImpl()
    exe = ToolExecutorImpl(registry=reg, handlers={})

    result = await exe.execute(_call("nonexistent"))
    assert result.content == ""  # LLM-visible content byte-identical when OFF
    # Sprint 57.164 (Option B): taxonomy is classified even when the lever is OFF.
    assert result.error_taxonomy == "wrong_tool"
