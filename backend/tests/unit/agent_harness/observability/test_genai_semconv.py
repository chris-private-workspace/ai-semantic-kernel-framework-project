"""
File: backend/tests/unit/agent_harness/observability/test_genai_semconv.py
Purpose: CI-safe tests for the OTel GenAI semconv mapping + real-SDK conformance (Sprint 57.142).
Category: Tests
Scope: Phase 57 / Sprint 57.142 (research #5)

Description:
    Three layers, all CI-safe (NO Azure):
      1. pure mapping (_genai_semconv): to_genai_span renames / pass-through /
         finish_reasons / assert_genai_conformant + full StopReason enum coverage
      2. real-OTel-SDK integration: drive synthetic spans through OTelTracer →
         InMemorySpanExporter (via the harness's build_capturing_tracer/run_synthetic),
         assert the EXPORTED spans carry gen_ai.* + the latent token-loss fix
      3. corpus-driven: the pinned conformance spec (otel_conformance_cases.yaml) is
         satisfied by the exported spans

Created: 2026-06-25 (Sprint 57.142)

Modification History:
    - 2026-06-25: Initial creation (Sprint 57.142) — mapping + real-SDK conformance + corpus
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

from agent_harness._contracts.chat import StopReason
from agent_harness.observability._genai_semconv import (
    GEN_AI_OPERATION_NAME,
    GEN_AI_REQUEST_MODEL,
    GEN_AI_RESPONSE_FINISH_REASONS,
    GEN_AI_TOOL_NAME,
    GEN_AI_USAGE_INPUT_TOKENS,
    GEN_AI_USAGE_OUTPUT_TOKENS,
    STOP_REASON_TO_FINISH_REASON,
    assert_genai_conformant,
    to_genai_span,
)

# Load the harness by file path (importlib idiom from test_benchmark_pass_k.py): scripts/
# is not a package; register in sys.modules before exec so dataclass __module__ resolves.
_BENCH_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "scripts"
    / "benchmark_otel_conformance.py"
)
_spec = importlib.util.spec_from_file_location(
    "_benchmark_otel_conformance_under_test", _BENCH_PATH
)
assert _spec is not None and _spec.loader is not None
_bench = importlib.util.module_from_spec(_spec)
sys.modules["_benchmark_otel_conformance_under_test"] = _bench
_spec.loader.exec_module(_bench)

_CORPUS = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "fixtures"
    / "observability"
    / "otel_conformance_cases.yaml"
)


# =============================================================================
# Layer 1 — pure mapping
# =============================================================================


def test_to_genai_span_chat_renames_attrs_and_name() -> None:
    name, attrs = to_genai_span(
        "agent_loop.llm_call",
        {
            "span_type": "LLM_CALL",
            "model": "gpt-5.2",
            "prompt_tokens": 100,
            "completion_tokens": 20,
        },
    )
    assert name == "chat gpt-5.2"
    assert attrs[GEN_AI_OPERATION_NAME] == "chat"
    assert attrs[GEN_AI_REQUEST_MODEL] == "gpt-5.2"
    assert attrs[GEN_AI_USAGE_INPUT_TOKENS] == 100
    assert attrs[GEN_AI_USAGE_OUTPUT_TOKENS] == 20
    # bespoke keys are renamed away
    assert "model" not in attrs
    assert "prompt_tokens" not in attrs


def test_to_genai_span_tool() -> None:
    name, attrs = to_genai_span(
        "agent_loop.tool.python_sandbox", {"span_type": "TOOL_EXEC", "tool": "python_sandbox"}
    )
    assert name == "execute_tool python_sandbox"
    assert attrs[GEN_AI_OPERATION_NAME] == "execute_tool"
    assert attrs[GEN_AI_TOOL_NAME] == "python_sandbox"
    assert "tool" not in attrs


def test_to_genai_span_loop_invoke_agent() -> None:
    name, attrs = to_genai_span("agent_loop.run", {"span_type": "LOOP"})
    assert name == "invoke_agent"
    assert attrs[GEN_AI_OPERATION_NAME] == "invoke_agent"


def test_to_genai_span_non_genai_passthrough() -> None:
    # TURN / PROMPT_BUILD / COMPACTION have no CNCF operation → pass through bespoke.
    name, attrs = to_genai_span("agent_loop.turn", {"span_type": "TURN", "turn": 3})
    assert name == "agent_loop.turn"
    assert attrs == {"span_type": "TURN", "turn": 3}
    assert GEN_AI_OPERATION_NAME not in attrs


def test_to_genai_span_preserves_enterprise_attrs() -> None:
    _name, attrs = to_genai_span(
        "agent_loop.llm_call",
        {"span_type": "LLM_CALL", "model": "m", "category": "orchestrator_loop", "tenant_id": "t1"},
    )
    assert attrs["category"] == "orchestrator_loop"
    assert attrs["tenant_id"] == "t1"
    assert attrs["span_type"] == "LLM_CALL"  # diagnostic key kept


def test_finish_reason_maps_to_finish_reasons_list() -> None:
    _name, attrs = to_genai_span(
        "agent_loop.llm_call", {"span_type": "LLM_CALL", "model": "m", "finish_reason": "tool_use"}
    )
    assert attrs[GEN_AI_RESPONSE_FINISH_REASONS] == ["tool_calls"]
    assert "finish_reason" not in attrs


def test_to_genai_span_does_not_mutate_input() -> None:
    src = {"span_type": "LLM_CALL", "model": "m"}
    to_genai_span("agent_loop.llm_call", src)
    assert src == {"span_type": "LLM_CALL", "model": "m"}


def test_stop_reason_map_covers_all_enum() -> None:
    # Every provider-neutral StopReason the loop can write must have a finish_reason mapping.
    for sr in StopReason:
        assert sr.value in STOP_REASON_TO_FINISH_REASON, f"unmapped StopReason {sr.value}"


def test_assert_conformant_clean_chat() -> None:
    _name, attrs = to_genai_span("agent_loop.llm_call", {"span_type": "LLM_CALL", "model": "m"})
    assert assert_genai_conformant("chat m", attrs) == []


def test_assert_conformant_non_genai_exempt() -> None:
    assert assert_genai_conformant("agent_loop.turn", {"span_type": "TURN"}) == []


def test_assert_conformant_detects_bespoke_leak() -> None:
    # A GenAI span that still carries a bespoke key = mapping bug.
    bad = {GEN_AI_OPERATION_NAME: "chat", GEN_AI_REQUEST_MODEL: "m", "model": "m"}
    violations = assert_genai_conformant("chat m", bad)
    assert any("model" in v for v in violations)


def test_assert_conformant_detects_missing_required() -> None:
    bad = {GEN_AI_OPERATION_NAME: "chat"}  # missing gen_ai.request.model
    violations = assert_genai_conformant("chat m", bad)
    assert any(GEN_AI_REQUEST_MODEL in v for v in violations)


def test_assert_conformant_detects_name_prefix_mismatch() -> None:
    attrs = {GEN_AI_OPERATION_NAME: "chat", GEN_AI_REQUEST_MODEL: "m"}
    violations = assert_genai_conformant("agent_loop.llm_call", attrs)
    assert any("not prefixed" in v for v in violations)


# =============================================================================
# Layer 2 — real OTel SDK integration (synthetic spans, NO Azure)
# =============================================================================


@pytest.mark.asyncio
async def test_synthetic_spans_export_conformant() -> None:
    tracer, exporter = _bench.build_capturing_tracer()
    await _bench.run_synthetic(tracer)
    results = _bench.evaluate_spans(exporter.get_finished_spans())
    report = _bench.build_report(results, mode="synthetic")
    assert report.genai_spans >= 3  # chat + execute_tool + invoke_agent
    assert report.conformant_spans == report.genai_spans
    assert report.conformance_ratio == 1.0


@pytest.mark.asyncio
async def test_chat_span_carries_usage_tokens_post_response() -> None:
    # THE latent-bug-fix proof: tokens written AFTER span start reach the exported span
    # (the start snapshot missed them; close-time set_attributes recovers them).
    tracer, exporter = _bench.build_capturing_tracer()
    await _bench.run_synthetic(tracer)
    report = _bench.build_report(
        _bench.evaluate_spans(exporter.get_finished_spans()), mode="synthetic"
    )
    assert report.chat_has_usage_tokens is True
    assert report.chat_has_finish_reasons is True


@pytest.mark.asyncio
async def test_exported_chat_span_attribute_values() -> None:
    tracer, exporter = _bench.build_capturing_tracer()
    await _bench.run_synthetic(tracer)
    spans = {s.name: dict(s.attributes or {}) for s in exporter.get_finished_spans()}
    chat = spans["chat gpt-5.2"]
    assert chat[GEN_AI_OPERATION_NAME] == "chat"
    assert chat[GEN_AI_REQUEST_MODEL] == "gpt-5.2"
    assert chat[GEN_AI_USAGE_INPUT_TOKENS] == 100
    assert chat[GEN_AI_USAGE_OUTPUT_TOKENS] == 20
    assert chat[GEN_AI_RESPONSE_FINISH_REASONS] == (
        "stop",
    )  # end_turn → stop (OTel coerces list→tuple)
    assert "model" not in chat and "prompt_tokens" not in chat


# =============================================================================
# Layer 3 — corpus-driven conformance
# =============================================================================


@pytest.mark.asyncio
async def test_corpus_required_keys_satisfied() -> None:
    spec = yaml.safe_load(_CORPUS.read_text(encoding="utf-8"))
    tracer, exporter = _bench.build_capturing_tracer()
    await _bench.run_synthetic(tracer)
    spans = list(exporter.get_finished_spans())
    by_op: dict[str, dict[str, Any]] = {}
    for s in spans:
        attrs = dict(s.attributes or {})
        op = attrs.get(GEN_AI_OPERATION_NAME)
        if op is not None:
            by_op[str(op)] = {"name": s.name, "attrs": attrs}

    for op, rule in spec["operations"].items():
        assert op in by_op, f"no exported span for operation '{op}'"
        entry = by_op[op]
        assert str(entry["name"]).startswith(rule["span_name_prefix"])
        for key in rule.get("required", []):
            assert key in entry["attrs"], f"op '{op}' missing required '{key}'"
        for key in rule.get("expected_on_completed", []):
            assert key in entry["attrs"], f"op '{op}' missing completed-key '{key}'"

    # No bespoke key may leak on ANY GenAI span.
    forbidden = spec["forbidden_on_genai_span"]
    for op, entry in by_op.items():
        for key in forbidden:
            assert key not in entry["attrs"], f"op '{op}' leaked bespoke '{key}'"


def test_corpus_loads() -> None:
    spec = yaml.safe_load(_CORPUS.read_text(encoding="utf-8"))
    assert set(spec["operations"]) == {"chat", "execute_tool", "invoke_agent"}
    assert "forbidden_on_genai_span" in spec
