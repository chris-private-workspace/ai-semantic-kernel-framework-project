"""
File: backend/scripts/benchmark_otel_conformance.py
Purpose: Permanent OTel GenAI semantic-conventions conformance harness (Sprint 57.142, research #5).
Category: 範疇 12 (Observability / Evaluation) — eval tooling
Scope: Phase 57 / Sprint 57.142 (research #5 — AD-Observability-OTel-GenAI-Schema)

Description:
    Drives spans through the REAL OpenTelemetry SDK (a TracerProvider with an
    InMemorySpanExporter) and asserts the EXPORTED spans conform to the CNCF GenAI
    semantic conventions (`gen_ai.*`). This is the drive-through for a pure-infra
    telemetry-schema change: "CATCH = the harness" (mirrors Sprint 57.135/137/138 —
    the real-SDK run IS the verification, there is no UI).

    Two modes:
      - synthetic (default, CI-safe, NO Azure): emits chat / execute_tool / invoke_agent
        spans with the SAME bespoke attrs + post-response mutation the loop emits, so the
        token-loss fix (close-time set_attributes) + finish_reasons are exercised.
      - --real (Azure-gated): direct-constructs the DB-less AgentLoopImpl with the capturing
        OTelTracer injected, runs ONE real turn, and inspects the actual production-path span.

    The capturing tracer is built by injecting a provider-backed OTel tracer into an
    OTelTracer instance (NO global set_tracer_provider → isolated, CI-safe alongside other
    tests). The reusable logic (build_capturing_tracer / run_synthetic / evaluate_spans /
    build_report) is importable for tests/unit/agent_harness/observability/test_genai_semconv.py.

    Run on demand:
      python scripts/benchmark_otel_conformance.py                 # synthetic
      RUN_AZURE_INTEGRATION=1 AZURE_OPENAI_*=... \
        python scripts/benchmark_otel_conformance.py --real        # real loop

LLM Provider Neutrality: the core drives the OTelTracer + the _genai_semconv pure mapping
(NO openai/anthropic import); only the --real path's _amain builds the Azure ModelProfile.

Created: 2026-06-25 (Sprint 57.142 research #5)

Modification History (newest-first):
    - 2026-06-25: Initial creation (Sprint 57.142) — OTel GenAI conformance harness

Related:
    - backend/src/agent_harness/observability/_genai_semconv.py (the mapping under test)
    - backend/src/agent_harness/observability/tracer.py (OTelTracer._span_cm applies it)
    - backend/scripts/benchmark_pass_k.py (the harness pattern this mirrors, Sprint 57.141)
    - claudedocs/5-status/otel-genai-schema-thin-spike-eval-20260625.md (the eval rationale)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from agent_harness._contracts import SpanCategory, TraceContext
from agent_harness.observability._genai_semconv import (
    GEN_AI_OPERATION_NAME,
    GEN_AI_RESPONSE_FINISH_REASONS,
    GEN_AI_USAGE_INPUT_TOKENS,
    OP_CHAT,
    assert_genai_conformant,
)
from agent_harness.observability.tracer import OTelTracer

_SYSTEM_PROMPT = (
    "You are a precise, helpful assistant. Give a concise final answer. "
    "When asked for a number, state it plainly."
)
_MAX_TURNS = 8


# =============================================================================
# Dataclasses
# =============================================================================


@dataclass(frozen=True)
class SpanConformance:
    """Conformance verdict for one exported span."""

    span_name: str
    operation: str | None
    is_genai: bool
    violations: list[str]
    has_usage_tokens: bool
    has_finish_reasons: bool


@dataclass(frozen=True)
class ConformanceReport:
    """Aggregate conformance over the exported spans."""

    mode: str  # "synthetic" | "real"
    total_spans: int
    genai_spans: int
    conformant_spans: int
    conformance_ratio: float
    chat_has_usage_tokens: bool  # the latent-token-loss-fix evidence
    chat_has_finish_reasons: bool
    spans: list[SpanConformance] = field(default_factory=list)


# =============================================================================
# Capturing tracer (real OTel SDK, isolated — no global set_tracer_provider)
# =============================================================================


def build_capturing_tracer() -> tuple[OTelTracer, InMemorySpanExporter]:
    """An OTelTracer whose spans flow to an InMemorySpanExporter we can read back.

    Injects a provider-backed tracer into OTelTracer's lazy cache so we capture spans
    WITHOUT touching the process-global TracerProvider (CI-safe alongside other tests).
    """
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = OTelTracer()
    tracer._otel_tracer = provider.get_tracer("otel-conformance")  # inject (bypass global)
    return tracer, exporter


# =============================================================================
# Synthetic span emission (CI-safe; mirrors the loop's bespoke emission)
# =============================================================================


async def run_synthetic(tracer: OTelTracer) -> None:
    """Emit chat / execute_tool / invoke_agent spans like the loop does (bespoke attrs).

    The chat span mutates its attrs dict AFTER span start (mirrors loop.py post-response
    token write) to exercise the close-time set_attributes fix.
    """
    loop_attrs: dict[str, Any] = {"span_type": "LOOP"}
    async with tracer.start_span(
        name="agent_loop.run", category=SpanCategory.ORCHESTRATOR, attributes=loop_attrs
    ):
        llm_attrs: dict[str, Any] = {"span_type": "LLM_CALL", "model": "gpt-5.2"}
        async with tracer.start_span(
            name="agent_loop.llm_call",
            category=SpanCategory.ORCHESTRATOR,
            attributes=llm_attrs,
        ):
            # post-response mutation (mirrors loop.py:2470-2477) — the close-time re-read
            # must pick these up (the latent-loss fix).
            llm_attrs["prompt_tokens"] = 100
            llm_attrs["completion_tokens"] = 20
            llm_attrs["cached_input_tokens"] = 0
            llm_attrs["total_tokens"] = 120
            llm_attrs["finish_reason"] = "end_turn"

        tool_attrs: dict[str, Any] = {"span_type": "TOOL_EXEC", "tool": "python_sandbox"}
        async with tracer.start_span(
            name="agent_loop.tool.python_sandbox",
            category=SpanCategory.TOOLS,
            attributes=tool_attrs,
        ):
            pass


# =============================================================================
# Conformance evaluation (pure)
# =============================================================================


def evaluate_spans(spans: Any) -> list[SpanConformance]:
    """Run the conformance checker over a sequence of exported ReadableSpans."""
    results: list[SpanConformance] = []
    for span in spans:
        attrs = dict(span.attributes or {})
        operation = attrs.get(GEN_AI_OPERATION_NAME)
        results.append(
            SpanConformance(
                span_name=span.name,
                operation=operation,
                is_genai=operation is not None,
                violations=assert_genai_conformant(span.name, attrs),
                has_usage_tokens=GEN_AI_USAGE_INPUT_TOKENS in attrs,
                has_finish_reasons=GEN_AI_RESPONSE_FINISH_REASONS in attrs,
            )
        )
    return results


def build_report(results: list[SpanConformance], *, mode: str) -> ConformanceReport:
    """Aggregate per-span verdicts into the conformance report."""
    genai = [r for r in results if r.is_genai]
    conformant = [r for r in genai if not r.violations]
    chat = [r for r in genai if r.operation == OP_CHAT]
    return ConformanceReport(
        mode=mode,
        total_spans=len(results),
        genai_spans=len(genai),
        conformant_spans=len(conformant),
        conformance_ratio=(len(conformant) / len(genai)) if genai else 0.0,
        chat_has_usage_tokens=any(r.has_usage_tokens for r in chat),
        chat_has_finish_reasons=any(r.has_finish_reasons for r in chat),
        spans=results,
    )


def report_to_markdown(report: ConformanceReport, *, stamp: str) -> str:
    """Render a human-readable conformance verdict."""
    lines = [
        f"# OTel GenAI Conformance — {stamp}",
        "",
        f"- mode: **{report.mode}**",
        f"- spans: **{report.total_spans}** · GenAI spans: **{report.genai_spans}** · "
        f"conformant: **{report.conformant_spans}**",
        f"- **conformance ratio: {report.conformance_ratio:.2%}**",
        f"- chat span carries usage tokens (latent bug FIXED): "
        f"**{'YES' if report.chat_has_usage_tokens else 'NO'}**",
        f"- chat span carries gen_ai.response.finish_reasons: "
        f"**{'YES' if report.chat_has_finish_reasons else 'NO'}**",
        "",
        "## Per span",
        "",
        "| span name | operation | conformant | usage | finish_reasons |",
        "|-----------|-----------|------------|-------|----------------|",
    ]
    for r in report.spans:
        ok = "✅" if (r.is_genai and not r.violations) else ("—" if not r.is_genai else "❌")
        lines.append(
            f"| `{r.span_name}` | {r.operation or '—'} | {ok} | "
            f"{'✅' if r.has_usage_tokens else '—'} | "
            f"{'✅' if r.has_finish_reasons else '—'} |"
        )
    violations = [(r.span_name, r.violations) for r in report.spans if r.violations]
    if violations:
        lines.append("")
        lines.append("## Violations")
        lines.append("")
        for name, vs in violations:
            for v in vs:
                lines.append(f"- `{name}`: {v}")
    return "\n".join(lines) + "\n"


def _report_to_dict(report: ConformanceReport) -> dict[str, Any]:
    return {
        "mode": report.mode,
        "total_spans": report.total_spans,
        "genai_spans": report.genai_spans,
        "conformant_spans": report.conformant_spans,
        "conformance_ratio": report.conformance_ratio,
        "chat_has_usage_tokens": report.chat_has_usage_tokens,
        "chat_has_finish_reasons": report.chat_has_finish_reasons,
        "spans": [
            {
                "span_name": r.span_name,
                "operation": r.operation,
                "is_genai": r.is_genai,
                "violations": r.violations,
                "has_usage_tokens": r.has_usage_tokens,
                "has_finish_reasons": r.has_finish_reasons,
            }
            for r in report.spans
        ],
    }


# =============================================================================
# CLI entry
# =============================================================================


async def _run_real(tracer: OTelTracer) -> None:
    """Drive ONE real turn through the DB-less loop with the capturing tracer injected."""
    from adapters.azure_openai.profile import build_azure_model_profile
    from agent_harness.orchestrator_loop.loop import AgentLoopImpl
    from agent_harness.output_parser import OutputParserImpl
    from business_domain._register_all import make_default_executor

    profile = build_azure_model_profile()
    registry, executor = make_default_executor()
    loop = AgentLoopImpl(
        chat_client=profile.action,
        output_parser=OutputParserImpl(),
        tool_executor=executor,
        tool_registry=registry,
        system_prompt=_SYSTEM_PROMPT,
        max_turns=_MAX_TURNS,
        tracer=tracer,
    )
    async for _ev in loop.run(
        session_id=uuid4(),
        user_input="What is 2 + 2? Answer with just the number.",
        trace_context=TraceContext.create_root(),
    ):
        pass


async def _amain(out_dir: Path, *, real: bool) -> int:
    tracer, exporter = build_capturing_tracer()
    if real:
        await _run_real(tracer)
    else:
        await run_synthetic(tracer)

    results = evaluate_spans(exporter.get_finished_spans())
    report = build_report(results, mode="real" if real else "synthetic")

    out_dir.mkdir(parents=True, exist_ok=True)
    md = report_to_markdown(report, stamp=datetime.now().isoformat(timespec="seconds"))
    (out_dir / "otel_conformance_report.md").write_text(md, encoding="utf-8")
    (out_dir / "otel_conformance_report.json").write_text(
        json.dumps(_report_to_dict(report), indent=2), encoding="utf-8"
    )
    print(md)
    # Exit non-zero if any GenAI span is non-conformant OR the chat span lost its tokens —
    # this harness IS a conformance gate (unlike pass^k which is descriptive).
    ok = report.genai_spans > 0 and report.conformant_spans == report.genai_spans
    if real:
        ok = ok and report.chat_has_usage_tokens and report.chat_has_finish_reasons
    return 0 if ok else 1


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:  # noqa: BLE001 — best-effort; redirected/odd streams keep their codec
        pass
    parser = argparse.ArgumentParser(description="OTel GenAI conformance harness (research #5).")
    parser.add_argument(
        "--out", default=str(Path(__file__).resolve().parent.parent / "benchmark_reports")
    )
    parser.add_argument(
        "--real", action="store_true", help="drive a real Azure loop (RUN_AZURE_INTEGRATION)"
    )
    args = parser.parse_args()
    return asyncio.run(_amain(Path(args.out), real=args.real))


if __name__ == "__main__":
    sys.exit(main())
