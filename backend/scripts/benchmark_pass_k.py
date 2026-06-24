"""
File: backend/scripts/benchmark_pass_k.py
Purpose: Permanent, re-runnable pass^k reliability eval harness (Sprint 57.141, research #2).
Category: 範疇 12 (Observability / Evaluation) — eval tooling
Scope: Phase 57 / Sprint 57.141 (research #2 — AD-Eval-PassK-Reliability-Harness)

Description:
    Measures RELIABILITY (not capability): runs the SAME corpus input through V2's own
    agent loop k times and computes 4 axes the single-run drive-through / pass@1 view is
    blind to (τ-bench: GPT-4o pass@1 ~61% but pass^8 <25%):
      1. pass^k vs pass@1 (+ divergence)  — the headline: how often ALL k repeats pass
      2. behavioral consistency           — answer / tool-sequence agreement across runs
      3. fault injection (λ)              — pass^k degradation under injected LLM faults
      4. perturbation (ε)                 — pass^k stability across input paraphrases
    Oracle is HYBRID: rules-based normalized exact/contains for closed-form cases (zero
    judge noise), an LLM judge (cheap tier) for open-ended cases.

    The reusable logic lives here (importable for the CI-safe unit tests):
      - load_cases(path)        — parse + schema-validate the corpus YAML
      - run_case(...)           — drive AgentLoopImpl.run() k times; oracle-judge each
      - build_report(...)       — pure metric computation (the 4 axes + per-category)
      - main()                  — CLI: build the Azure profile, run the axes, write a report
    The pytest wrapper drives a real Azure run behind @pytest.mark.benchmark
    (RUN_AZURE_INTEGRATION); tests/unit/scripts/test_benchmark_pass_k.py covers load/run/build
    CI-safe (a spy ChatClient, no Azure, a seeded rng for the fault axis).

    Run on demand:
      RUN_AZURE_INTEGRATION=1 AZURE_OPENAI_*=... \
        python scripts/benchmark_pass_k.py --k 5 --fault-rate 0.2 --epsilon

LLM Provider Neutrality: the core (load/run/score) drives the AgentLoopImpl + Verifier ABCs;
_FaultInjectingChatClient subclasses the adapters._base ChatClient ABC (NO openai/anthropic
import); only _amain builds the Azure ModelProfile (the concrete on-demand entry, like
benchmark_judge.py).

Created: 2026-06-24 (Sprint 57.141 research #2)

Modification History (newest-first):
    - 2026-06-24: Initial creation (Sprint 57.141) — 4-axis pass^k reliability harness

Related:
    - backend/tests/fixtures/observability/pass_k_cases.yaml (the corpus)
    - backend/scripts/benchmark_judge.py (the harness pattern this mirrors, Sprint 57.111)
    - backend/src/agent_harness/orchestrator_loop/loop.py (the loop under test)
    - claudedocs/5-status/passk-reliability-thin-spike-eval-20260624.md (the eval rationale)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, AsyncIterator, Literal
from uuid import uuid4

import yaml

from adapters._base.chat_client import ChatClient
from adapters._base.pricing import PricingInfo
from adapters._base.types import ModelInfo, StreamEvent
from agent_harness._contracts import (
    CacheBreakpoint,
    ChatRequest,
    ChatResponse,
    LLMResponded,
    LoopCompleted,
    LoopEvent,
    LoopTerminated,
    Message,
    ToolSpec,
    TraceContext,
)
from agent_harness.orchestrator_loop.loop import AgentLoopImpl
from agent_harness.output_parser import OutputParserImpl
from agent_harness.verification import LLMJudgeVerifier
from business_domain._register_all import make_default_executor

# A neutral system prompt — kept local (NOT imported from the chat handler) so the harness
# carries no chat-API wiring. Concise-answer framing keeps the rules oracle robust.
_SYSTEM_PROMPT = (
    "You are a precise, helpful assistant. Think step by step when needed, "
    "but give a concise final answer. When asked for a number or a specific value, "
    "state it plainly in the answer."
)

# The loop's per-send turn cap (mirrors the chat path handler.py:710).
_MAX_TURNS = 8

# Divergence above this is flagged "notable" in the report (descriptive, NOT a pass/fail gate —
# pass^k is a measurement, not a threshold check; the verdict is the number itself).
_NOTABLE_DIVERGENCE = 0.15

_VALID_CATEGORIES = ("easy", "multistep", "tool_use")
_VALID_ORACLES = ("rules", "judge")


# =============================================================================
# Dataclasses
# =============================================================================


@dataclass(frozen=True)
class PassKCase:
    """One reliability corpus case."""

    id: str
    input: str
    oracle_type: str  # "rules" | "judge"
    expected: list[str]  # rules: acceptable answer substrings; judge: [criterion]
    category: str  # "easy" | "multistep" | "tool_use"
    perturbations: list[str] = field(default_factory=list)  # ε paraphrases of `input`


@dataclass(frozen=True)
class RunOutcome:
    """The result of one single run of one case."""

    passed: bool
    answer: str
    tool_seq: tuple[str, ...]
    tokens: int
    stop_reason: str


@dataclass(frozen=True)
class CaseRuns:
    """k runs of one (case, arm, variant)."""

    case_id: str
    category: str
    arm: str  # "baseline" | "fault" | "epsilon"
    variant: str  # "orig" | "perturb-0" | ...
    outcomes: list[RunOutcome]

    @property
    def pass_at_1(self) -> float:
        if not self.outcomes:
            return 0.0
        return mean(1.0 if o.passed else 0.0 for o in self.outcomes)

    @property
    def pass_k(self) -> float:
        return 1.0 if self.outcomes and all(o.passed for o in self.outcomes) else 0.0

    @property
    def answer_consistent(self) -> bool:
        norms = {_norm(o.answer) for o in self.outcomes}
        return len(norms) <= 1

    @property
    def tool_seq_consistent(self) -> bool:
        return len({o.tool_seq for o in self.outcomes}) <= 1


@dataclass(frozen=True)
class PassKReport:
    """Computed reliability metrics (the 4 axes + per-category + cost)."""

    total_cases: int
    k: int
    pass_at_1: float
    pass_k: float
    divergence: float  # pass@1 − pass^k
    divergence_notable: bool
    answer_consistency: float
    tool_seq_consistency: float
    lambda_fault_rate: float | None
    lambda_degradation: float | None  # pass^k(baseline) − pass^k(fault)
    epsilon_cases: int
    epsilon_instability: float | None  # mean per-case (max−min pass^k across paraphrases)
    per_category: dict[str, dict[str, float]]
    total_runs: int
    total_tokens: int


# =============================================================================
# Corpus loading
# =============================================================================


def load_cases(path: str | Path) -> list[PassKCase]:
    """Parse + schema-validate the corpus YAML into PassKCase objects."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "cases" not in data:
        raise ValueError("corpus must be a mapping with a top-level 'cases' list")
    raw_cases = data["cases"]
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("'cases' must be a non-empty list")

    cases: list[PassKCase] = []
    seen_ids: set[str] = set()
    for i, rc in enumerate(raw_cases):
        if not isinstance(rc, dict):
            raise ValueError(f"case #{i} is not a mapping")
        for key in ("id", "input", "oracle_type", "expected", "category"):
            if key not in rc:
                raise ValueError(f"case #{i} missing required key '{key}'")
        cid = str(rc["id"])
        if cid in seen_ids:
            raise ValueError(f"duplicate case id '{cid}'")
        seen_ids.add(cid)
        category = str(rc["category"])
        if category not in _VALID_CATEGORIES:
            raise ValueError(f"case '{cid}' invalid category '{category}'")
        oracle_type = str(rc["oracle_type"])
        if oracle_type not in _VALID_ORACLES:
            raise ValueError(f"case '{cid}' invalid oracle_type '{oracle_type}'")
        raw_expected = rc["expected"]
        expected = (
            [str(raw_expected)] if isinstance(raw_expected, str) else [str(e) for e in raw_expected]
        )
        if not expected:
            raise ValueError(f"case '{cid}' 'expected' must be non-empty")
        perturbations = [str(p) for p in (rc.get("perturbations") or [])]
        cases.append(
            PassKCase(
                id=cid,
                input=str(rc["input"]),
                oracle_type=oracle_type,
                expected=expected,
                category=category,
                perturbations=perturbations,
            )
        )
    return cases


# =============================================================================
# Fault injection (λ axis) — wraps the real ChatClient ABC (LLM-neutral)
# =============================================================================


class InjectedFault(Exception):
    """A transient infra fault injected by the pass^k λ axis (NOT a real failure)."""


class _FaultInjectingChatClient(ChatClient):
    """Wrap an inner ChatClient; raise InjectedFault on `chat` at `fault_rate`.

    Every other ABC method delegates verbatim. `rng` is injectable so the unit tests
    are deterministic; the real run uses an unseeded random.Random().
    """

    def __init__(self, inner: ChatClient, *, fault_rate: float, rng: random.Random) -> None:
        self._inner = inner
        self._fault_rate = fault_rate
        self._rng = rng

    async def chat(
        self,
        request: ChatRequest,
        *,
        cache_breakpoints: list[CacheBreakpoint] | None = None,
        trace_context: TraceContext | None = None,
    ) -> ChatResponse:
        if self._rng.random() < self._fault_rate:
            raise InjectedFault("injected transient LLM fault (pass^k λ axis)")
        return await self._inner.chat(
            request, cache_breakpoints=cache_breakpoints, trace_context=trace_context
        )

    def stream(
        self,
        request: ChatRequest,
        *,
        cache_breakpoints: list[CacheBreakpoint] | None = None,
        trace_context: TraceContext | None = None,
    ) -> AsyncIterator[StreamEvent]:
        return self._inner.stream(
            request, cache_breakpoints=cache_breakpoints, trace_context=trace_context
        )

    async def count_tokens(
        self, *, messages: list[Message], tools: list[ToolSpec] | None = None
    ) -> int:
        return await self._inner.count_tokens(messages=messages, tools=tools)

    def get_pricing(self) -> PricingInfo:
        return self._inner.get_pricing()

    def supports_feature(
        self,
        feature: Literal[
            "thinking",
            "caching",
            "vision",
            "audio",
            "computer_use",
            "structured_output",
            "parallel_tool_calls",
        ],
    ) -> bool:
        return self._inner.supports_feature(feature)

    def model_info(self) -> ModelInfo:
        return self._inner.model_info()


# =============================================================================
# Oracle (hybrid: rules-based exact/contains | LLM judge)
# =============================================================================


def _norm(s: str) -> str:
    """Lowercase + collapse whitespace for robust comparison."""
    return " ".join(s.lower().split())


def _judge_template(criterion: str) -> str:
    """A raw LLMJudgeVerifier template embedding a per-case correctness criterion.

    Must contain `{output}` (the verifier substitutes it) and instruct a JSON
    `{"passed": ...}` response (what LLMJudgeVerifier._parse_response reads).
    """
    return (
        "You are a strict grader. Decide whether the OUTPUT satisfies the CRITERION.\n"
        f"CRITERION: {criterion}\n\n"
        'Respond with ONLY a JSON object: {"passed": true or false, "reason": "<short>"}\n\n'
        "OUTPUT:\n{output}"
    )


async def evaluate(case: PassKCase, answer: str, judge_client: ChatClient) -> bool:
    """Return whether `answer` passes `case` via the hybrid oracle."""
    if not answer.strip():
        return False
    if case.oracle_type == "rules":
        norm_answer = _norm(answer)
        return any(_norm(e) in norm_answer for e in case.expected)
    # judge: cheap-tier LLM judge with a per-case correctness criterion
    criterion = case.expected[0]
    judge = LLMJudgeVerifier(
        chat_client=judge_client, judge_template=_judge_template(criterion), temperature=0.0
    )
    result = await judge.verify(output=answer)
    return result.passed


# =============================================================================
# Run driving
# =============================================================================


def _extract(events: list[LoopEvent]) -> tuple[str, tuple[str, ...], int, str, bool]:
    """Pull (answer, tool_seq, tokens, stop_reason, terminated) from a run's events."""
    answer = ""
    tool_seq: list[str] = []
    tokens = 0
    stop_reason = "unknown"
    terminated = False
    for ev in events:
        if isinstance(ev, LLMResponded):
            if getattr(ev, "content", ""):
                answer = ev.content
            for tc in getattr(ev, "tool_calls", None) or []:
                tool_seq.append(str(getattr(tc, "name", tc)))
        elif isinstance(ev, LoopCompleted):
            stop_reason = ev.stop_reason
            tokens = getattr(ev, "total_tokens", 0) or (
                getattr(ev, "input_tokens", 0) + getattr(ev, "output_tokens", 0)
            )
        elif isinstance(ev, LoopTerminated):
            terminated = True
            stop_reason = "terminated"
    return answer, tuple(tool_seq), tokens, stop_reason, terminated


def _build_loop(chat_client: ChatClient) -> AgentLoopImpl:
    """Direct-construct a minimal AgentLoopImpl driving the same loop as the chat path.

    DB-less (no message_store/checkpointer) per Day-0 D-loop-run-noDB; the executor
    registers echo + mock business tools (unused by reasoning cases)."""
    registry, executor = make_default_executor()
    return AgentLoopImpl(
        chat_client=chat_client,
        output_parser=OutputParserImpl(),
        tool_executor=executor,
        tool_registry=registry,
        system_prompt=_SYSTEM_PROMPT,
        max_turns=_MAX_TURNS,
    )


async def run_case(
    case: PassKCase,
    *,
    k: int,
    action_client: ChatClient,
    judge_client: ChatClient,
    arm: str,
    variant: str,
    user_input: str,
    fault_rate: float,
    rng: random.Random,
) -> CaseRuns:
    """Drive the loop k times for one (case, arm, variant); oracle-judge each run."""
    outcomes: list[RunOutcome] = []
    for _ in range(k):
        client = action_client
        if fault_rate > 0:
            client = _FaultInjectingChatClient(action_client, fault_rate=fault_rate, rng=rng)
        loop = _build_loop(client)
        events: list[LoopEvent] = []
        try:
            async for ev in loop.run(
                session_id=uuid4(),
                user_input=user_input,
                trace_context=TraceContext.create_root(),
            ):
                events.append(ev)
        except Exception:  # noqa: BLE001 — an injected (or real) fault that escapes = a failed run
            outcomes.append(
                RunOutcome(passed=False, answer="", tool_seq=(), tokens=0, stop_reason="error")
            )
            continue
        answer, tool_seq, tokens, stop_reason, terminated = _extract(events)
        passed = False if terminated else await evaluate(case, answer, judge_client)
        outcomes.append(
            RunOutcome(
                passed=passed,
                answer=answer,
                tool_seq=tool_seq,
                tokens=tokens,
                stop_reason=stop_reason,
            )
        )
    return CaseRuns(
        case_id=case.id, category=case.category, arm=arm, variant=variant, outcomes=outcomes
    )


# =============================================================================
# Report (pure metric computation)
# =============================================================================


def build_report(
    cases: list[PassKCase],
    baseline: list[CaseRuns],
    *,
    k: int,
    fault: list[CaseRuns] | None = None,
    fault_rate: float | None = None,
    epsilon: dict[str, list[CaseRuns]] | None = None,
) -> PassKReport:
    """Pure computation of the 4 axes + per-category from the run collections.

    baseline: one CaseRuns per case (arm="baseline", variant="orig").
    fault:    one CaseRuns per case run with fault_rate (arm="fault"); None → λ skipped.
    epsilon:  case_id → [CaseRuns over orig + each paraphrase]; None → ε skipped.
    """
    n = len(baseline)
    pass_at_1 = mean(cr.pass_at_1 for cr in baseline) if baseline else 0.0
    pass_k = mean(cr.pass_k for cr in baseline) if baseline else 0.0
    divergence = pass_at_1 - pass_k
    answer_consistency = (
        mean(1.0 if cr.answer_consistent else 0.0 for cr in baseline) if baseline else 0.0
    )
    tool_seq_consistency = (
        mean(1.0 if cr.tool_seq_consistent else 0.0 for cr in baseline) if baseline else 0.0
    )

    lambda_degradation: float | None = None
    if fault:
        fault_pass_k = mean(cr.pass_k for cr in fault) if fault else 0.0
        lambda_degradation = pass_k - fault_pass_k

    epsilon_instability: float | None = None
    epsilon_cases = 0
    if epsilon:
        spreads: list[float] = []
        for _cid, variants in epsilon.items():
            if not variants:
                continue
            pks = [cr.pass_k for cr in variants]
            spreads.append(max(pks) - min(pks))
        epsilon_cases = len(spreads)
        if spreads:
            epsilon_instability = mean(spreads)

    per_category: dict[str, dict[str, float]] = {}
    for cat in _VALID_CATEGORIES:
        sub = [cr for cr in baseline if cr.category == cat]
        if not sub:
            continue
        per_category[cat] = {
            "n": float(len(sub)),
            "pass_at_1": mean(cr.pass_at_1 for cr in sub),
            "pass_k": mean(cr.pass_k for cr in sub),
        }

    all_runs = list(baseline) + list(fault or [])
    for variants in (epsilon or {}).values():
        all_runs.extend(variants)
    total_runs = sum(len(cr.outcomes) for cr in all_runs)
    total_tokens = sum(o.tokens for cr in all_runs for o in cr.outcomes)

    return PassKReport(
        total_cases=n,
        k=k,
        pass_at_1=pass_at_1,
        pass_k=pass_k,
        divergence=divergence,
        divergence_notable=divergence >= _NOTABLE_DIVERGENCE,
        answer_consistency=answer_consistency,
        tool_seq_consistency=tool_seq_consistency,
        lambda_fault_rate=fault_rate if fault else None,
        lambda_degradation=lambda_degradation,
        epsilon_cases=epsilon_cases,
        epsilon_instability=epsilon_instability,
        per_category=per_category,
        total_runs=total_runs,
        total_tokens=total_tokens,
    )


def report_to_markdown(report: PassKReport, *, stamp: str) -> str:
    """Render a human-readable verdict report."""

    def _pct(x: float | None) -> str:
        return "n/a" if x is None else f"{x:.2%}"

    lines = [
        f"# pass^k Reliability Benchmark — {stamp}",
        "",
        f"- cases: **{report.total_cases}** · k: **{report.k}** · "
        f"total runs: **{report.total_runs}**",
        f"- **pass@1: {report.pass_at_1:.2%}**  ·  **pass^k: {report.pass_k:.2%}**",
        f"- **divergence (pass@1 − pass^k): {report.divergence:+.2%}** "
        f"→ {'NOTABLE' if report.divergence_notable else 'small'}",
        f"- answer consistency: {report.answer_consistency:.2%} · "
        f"tool-seq consistency: {report.tool_seq_consistency:.2%}",
        f"- λ fault-rate: {_pct(report.lambda_fault_rate)} · "
        f"λ degradation (pass^k drop): {_pct(report.lambda_degradation)}",
        f"- ε cases: {report.epsilon_cases} · ε instability (pass^k spread): "
        f"{_pct(report.epsilon_instability)}",
        f"- total tokens: {report.total_tokens}",
        "",
        "## Per category",
        "",
        "| category | n | pass@1 | pass^k |",
        "|----------|---|--------|--------|",
    ]
    for cat, m in report.per_category.items():
        lines.append(f"| {cat} | {int(m['n'])} | {m['pass_at_1']:.2%} | {m['pass_k']:.2%} |")
    return "\n".join(lines) + "\n"


def _report_to_dict(report: PassKReport) -> dict[str, Any]:
    return {
        "total_cases": report.total_cases,
        "k": report.k,
        "pass_at_1": report.pass_at_1,
        "pass_k": report.pass_k,
        "divergence": report.divergence,
        "divergence_notable": report.divergence_notable,
        "answer_consistency": report.answer_consistency,
        "tool_seq_consistency": report.tool_seq_consistency,
        "lambda_fault_rate": report.lambda_fault_rate,
        "lambda_degradation": report.lambda_degradation,
        "epsilon_cases": report.epsilon_cases,
        "epsilon_instability": report.epsilon_instability,
        "per_category": report.per_category,
        "total_runs": report.total_runs,
        "total_tokens": report.total_tokens,
    }


# =============================================================================
# CLI entry (the only Azure-touching code)
# =============================================================================


async def _amain(
    fixture: Path, out_dir: Path, *, k: int, fault_rate: float, run_epsilon: bool
) -> int:
    # Lazy import so a CI-safe import of this module's pure helpers needs no Azure env.
    from adapters.azure_openai.profile import build_azure_model_profile

    cases = load_cases(fixture)
    profile = build_azure_model_profile()
    action = profile.action
    cheap = profile.cheap
    rng = random.Random()

    baseline: list[CaseRuns] = []
    for case in cases:
        baseline.append(
            await run_case(
                case,
                k=k,
                action_client=action,
                judge_client=cheap,
                arm="baseline",
                variant="orig",
                user_input=case.input,
                fault_rate=0.0,
                rng=rng,
            )
        )

    fault: list[CaseRuns] | None = None
    if fault_rate > 0:
        fault = []
        for case in cases:
            fault.append(
                await run_case(
                    case,
                    k=k,
                    action_client=action,
                    judge_client=cheap,
                    arm="fault",
                    variant="orig",
                    user_input=case.input,
                    fault_rate=fault_rate,
                    rng=rng,
                )
            )

    epsilon: dict[str, list[CaseRuns]] | None = None
    if run_epsilon:
        epsilon = {}
        for case in cases:
            if not case.perturbations:
                continue
            variants: list[CaseRuns] = []
            for vi, text in enumerate([case.input, *case.perturbations]):
                variants.append(
                    await run_case(
                        case,
                        k=k,
                        action_client=action,
                        judge_client=cheap,
                        arm="epsilon",
                        variant="orig" if vi == 0 else f"perturb-{vi - 1}",
                        user_input=text,
                        fault_rate=0.0,
                        rng=rng,
                    )
                )
            epsilon[case.id] = variants

    report = build_report(
        cases, baseline, k=k, fault=fault, fault_rate=fault_rate if fault else None, epsilon=epsilon
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    md = report_to_markdown(report, stamp=datetime.now().isoformat(timespec="seconds"))
    (out_dir / "pass_k_report.md").write_text(md, encoding="utf-8")
    (out_dir / "pass_k_report.json").write_text(
        json.dumps(_report_to_dict(report), indent=2), encoding="utf-8"
    )
    print(md)
    # Exit 0 always — pass^k is descriptive; the verdict is the number, not a gate.
    return 0


def main() -> int:
    # The report markdown carries non-ASCII typography (− · → ε λ); a Windows cp950 console
    # can't encode it. Force the stdout text layer to UTF-8 so the print never crashes.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:  # noqa: BLE001 — best-effort; redirected/odd streams keep their codec
        pass
    parser = argparse.ArgumentParser(description="pass^k reliability benchmark (research #2).")
    parser.add_argument(
        "--fixture",
        default=str(
            Path(__file__).resolve().parent.parent
            / "tests"
            / "fixtures"
            / "observability"
            / "pass_k_cases.yaml"
        ),
    )
    parser.add_argument(
        "--out", default=str(Path(__file__).resolve().parent.parent / "benchmark_reports")
    )
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--fault-rate", type=float, default=0.0)
    parser.add_argument("--epsilon", action="store_true")
    args = parser.parse_args()
    return asyncio.run(
        _amain(
            Path(args.fixture),
            Path(args.out),
            k=args.k,
            fault_rate=args.fault_rate,
            run_epsilon=args.epsilon,
        )
    )


if __name__ == "__main__":
    sys.exit(main())
