"""Unit tests for agent_harness.tools._error_taxonomy (Sprint 57.144, research #7 Half B)."""

from __future__ import annotations

import pytest

from agent_harness.tools._error_taxonomy import (
    ErrorTaxonomy,
    classify_tool_error,
    render_reflection,
)


def test_schema_error_is_parameter() -> None:
    assert (
        classify_tool_error(is_schema_error=True, error_msg="q: 'q' is a required property")
        is ErrorTaxonomy.PARAMETER
    )


def test_unknown_tool_is_wrong_tool() -> None:
    assert classify_tool_error(is_unknown_tool=True) is ErrorTaxonomy.WRONG_TOOL


@pytest.mark.parametrize(
    "error_class",
    [
        "asyncio.TimeoutError",
        "aiohttp.ClientConnectionError",
        "httpx.ConnectError",
        "builtins.ConnectionError",
        "ssl.SSLError",
    ],
)
def test_external_exception_class_is_failed_api(error_class: str) -> None:
    assert (
        classify_tool_error(error_class=error_class, error_msg="boom") is ErrorTaxonomy.FAILED_API
    )


def test_generic_exception_class_is_invocation() -> None:
    assert (
        classify_tool_error(error_class="builtins.ValueError", error_msg="bad value")
        is ErrorTaxonomy.INVOCATION
    )


def test_no_signal_is_unknown() -> None:
    assert classify_tool_error() is ErrorTaxonomy.UNKNOWN


def test_message_heuristic_parameter() -> None:
    # No explicit flag, but the message looks like a schema validation failure.
    assert (
        classify_tool_error(error_msg="'query' is a required property") is ErrorTaxonomy.PARAMETER
    )


def test_message_heuristic_failed_api() -> None:
    assert (
        classify_tool_error(error_msg="connection refused by upstream") is ErrorTaxonomy.FAILED_API
    )


def test_schema_flag_takes_precedence_over_exception_class() -> None:
    # is_schema_error wins even if an exception class is also present.
    assert (
        classify_tool_error(is_schema_error=True, error_class="asyncio.TimeoutError", error_msg="x")
        is ErrorTaxonomy.PARAMETER
    )


@pytest.mark.parametrize("taxonomy", list(ErrorTaxonomy))
def test_render_reflection_contains_label_raw_and_guidance(taxonomy: ErrorTaxonomy) -> None:
    out = render_reflection(taxonomy, "missing field 'q'")
    assert "missing field 'q'" in out  # raw error preserved
    assert out.endswith(".")  # guidance sentence
    assert len(out) > len("missing field 'q'")  # label + guidance added


def test_render_reflection_empty_message_falls_back() -> None:
    out = render_reflection(ErrorTaxonomy.PARAMETER, "")
    assert "(no detail)" in out


def test_taxonomy_value_is_stable_str() -> None:
    # ToolResult.error_taxonomy stores the .value (str), not the enum object.
    assert ErrorTaxonomy.PARAMETER.value == "parameter"
    assert ErrorTaxonomy.WRONG_TOOL.value == "wrong_tool"
    assert ErrorTaxonomy.FAILED_API.value == "failed_api"
