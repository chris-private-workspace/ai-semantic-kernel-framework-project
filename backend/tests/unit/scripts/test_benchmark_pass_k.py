"""
File: backend/tests/unit/scripts/test_benchmark_pass_k.py
Purpose: CI-safe unit tests for scripts/benchmark_pass_k.py (Sprint 57.141 research #2).
Category: Tests
Scope: Phase 57 / Sprint 57.141

Description:
    Covers the harness's pure + offline logic WITHOUT real Azure:
      - load_cases schema validation
      - evaluate() hybrid oracle (rules contains/exact + judge via a spy client)
      - _FaultInjectingChatClient raises at fault_rate (seeded rng → deterministic)
      - build_report 4-axis metric computation on synthetic CaseRuns
      - run_case drives a real AgentLoopImpl with a spy ChatClient (no Azure)
    The real-Azure run is exercised on demand via @pytest.mark.benchmark (RUN_AZURE_INTEGRATION).

Created: 2026-06-24 (Sprint 57.141)

Modification History:
    - 2026-06-24: Initial creation (Sprint 57.141) — load/evaluate/fault/build_report/run_case
"""

from __future__ import annotations

import importlib.util
import random
import sys
from pathlib import Path
from typing import Any, AsyncIterator, Literal
from unittest.mock import MagicMock

import pytest

from adapters._base.chat_client import ChatClient
from adapters._base.pricing import PricingInfo
from adapters._base.types import ModelInfo, StopReason, StreamEvent
from agent_harness._contracts import (
    CacheBreakpoint,
    ChatRequest,
    ChatResponse,
    Message,
    TokenUsage,
    ToolSpec,
    TraceContext,
)
from agent_harness.tools import ToolExecutorImpl, ToolRegistryImpl

# Load the script by file path (the importlib idiom from test_benchmark_judge.py): avoids the
# scripts.* package shadow; register in sys.modules BEFORE exec so dataclass __module__ resolves.
_BENCH_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent / "scripts" / "benchmark_pass_k.py"
)
_spec = importlib.util.spec_from_file_location("_benchmark_pass_k_under_test", _BENCH_PATH)
assert _spec is not None and _spec.loader is not None
_bench = importlib.util.module_from_spec(_spec)
sys.modules["_benchmark_pass_k_under_test"] = _bench
_spec.loader.exec_module(_bench)


# === Spy ChatClient (mirrors _FlakyChatClient; no Azure) ====================


class _SpyChatClient(ChatClient):
    """Returns a fixed end_turn answer. Counts calls; can be forced to inject content."""

    def __init__(self, content: str = "The answer is 391.") -> None:
        self._content = content
        self.calls = 0

    async def chat(
        self,
        request: ChatRequest,
        *,
        cache_breakpoints: list[CacheBreakpoint] | None = None,
        trace_context: TraceContext | None = None,
    ) -> ChatResponse:
        self.calls += 1
        return ChatResponse(
            model="spy-model",
            content=self._content,
            tool_calls=None,
            stop_reason=StopReason.END_TURN,
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5),
        )

    def stream(
        self,
        request: ChatRequest,
        *,
        cache_breakpoints: list[CacheBreakpoint] | None = None,
        trace_context: TraceContext | None = None,
    ) -> AsyncIterator[StreamEvent]:
        return self._empty()

    async def _empty(self) -> AsyncIterator[StreamEvent]:
        if False:
            yield  # type: ignore[unreachable]

    async def count_tokens(
        self, *, messages: list[Message], tools: list[ToolSpec] | None = None
    ) -> int:
        return 1

    def get_pricing(self) -> PricingInfo:
        return MagicMock(spec=PricingInfo)

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
        return False

    def model_info(self) -> ModelInfo:
        return ModelInfo(
            model_name="spy-model",
            model_family="spy",
            provider="spy",
            context_window=8192,
            max_output_tokens=4096,
        )


def _outcome(passed: bool, answer: str = "x", tool_seq: tuple[str, ...] = ()) -> Any:
    return _bench.RunOutcome(
        passed=passed, answer=answer, tool_seq=tool_seq, tokens=15, stop_reason="end_turn"
    )


def _case_runs(
    case_id: str,
    category: str,
    outcomes: list[Any],
    *,
    arm: str = "baseline",
    variant: str = "orig",
) -> Any:
    return _bench.CaseRuns(
        case_id=case_id, category=category, arm=arm, variant=variant, outcomes=outcomes
    )


# === load_cases =============================================================


def test_load_cases_parses_real_corpus() -> None:
    corpus = (
        Path(__file__).resolve().parent.parent.parent
        / "fixtures"
        / "observability"
        / "pass_k_cases.yaml"
    )
    cases = _bench.load_cases(corpus)
    assert len(cases) >= 10
    ids = {c.id for c in cases}
    assert "mult-17-23" in ids
    # the multistep + judge gradient is present
    assert any(c.category == "multistep" for c in cases)
    assert any(c.oracle_type == "judge" for c in cases)
    # at least one ε case carries perturbations
    assert any(c.perturbations for c in cases)


def test_load_cases_rejects_duplicate_id(tmp_path: Path) -> None:
    p = tmp_path / "dup.yaml"
    p.write_text(
        "cases:\n"
        "  - {id: a, input: x, oracle_type: rules, expected: ['1'], category: easy}\n"
        "  - {id: a, input: y, oracle_type: rules, expected: ['2'], category: easy}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate"):
        _bench.load_cases(p)


def test_load_cases_rejects_bad_category(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text(
        "cases:\n  - {id: a, input: x, oracle_type: rules, expected: ['1'], category: nope}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="category"):
        _bench.load_cases(p)


def test_load_cases_rejects_bad_oracle(tmp_path: Path) -> None:
    p = tmp_path / "bad2.yaml"
    p.write_text(
        "cases:\n  - {id: a, input: x, oracle_type: vibes, expected: ['1'], category: easy}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="oracle_type"):
        _bench.load_cases(p)


# === evaluate (hybrid oracle) ===============================================


@pytest.mark.asyncio
async def test_evaluate_rules_contains_passes() -> None:
    case = _bench.PassKCase(
        id="c", input="i", oracle_type="rules", expected=["391"], category="easy"
    )
    assert await _bench.evaluate(case, "The product is 391, of course.", _SpyChatClient()) is True


@pytest.mark.asyncio
async def test_evaluate_rules_missing_value_fails() -> None:
    case = _bench.PassKCase(
        id="c", input="i", oracle_type="rules", expected=["391"], category="easy"
    )
    assert await _bench.evaluate(case, "I think it is 392.", _SpyChatClient()) is False


@pytest.mark.asyncio
async def test_evaluate_empty_answer_fails() -> None:
    case = _bench.PassKCase(
        id="c", input="i", oracle_type="rules", expected=["391"], category="easy"
    )
    assert await _bench.evaluate(case, "   ", _SpyChatClient()) is False


@pytest.mark.asyncio
async def test_evaluate_judge_reads_passed_json() -> None:
    case = _bench.PassKCase(
        id="c", input="i", oracle_type="judge", expected=["criterion"], category="easy"
    )
    judge_client = _SpyChatClient(content='{"passed": true, "reason": "ok"}')
    assert await _bench.evaluate(case, "some answer", judge_client) is True
    judge_client_fail = _SpyChatClient(content='{"passed": false, "reason": "no"}')
    assert await _bench.evaluate(case, "some answer", judge_client_fail) is False


# === _FaultInjectingChatClient (λ) ==========================================


@pytest.mark.asyncio
async def test_fault_client_raises_at_high_rate() -> None:
    inner = _SpyChatClient()
    # rng forced to always return 0.0 < fault_rate → always raises
    rng = MagicMock()
    rng.random.return_value = 0.0
    client = _bench._FaultInjectingChatClient(inner, fault_rate=1.0, rng=rng)
    with pytest.raises(_bench.InjectedFault):
        await client.chat(ChatRequest(messages=[Message(role="user", content="hi")]))
    assert inner.calls == 0  # never reached the inner client


@pytest.mark.asyncio
async def test_fault_client_passes_through_at_zero_rate() -> None:
    inner = _SpyChatClient()
    client = _bench._FaultInjectingChatClient(inner, fault_rate=0.0, rng=random.Random(7))
    resp = await client.chat(ChatRequest(messages=[Message(role="user", content="hi")]))
    assert resp.content == "The answer is 391."
    assert inner.calls == 1


def test_fault_client_seeded_rng_is_deterministic() -> None:
    inner = _SpyChatClient()
    client = _bench._FaultInjectingChatClient(inner, fault_rate=0.5, rng=random.Random(42))
    # The same seed → the same fault decision sequence (deterministic for CI).
    decisions = [client._rng.random() < client._fault_rate for _ in range(10)]
    ref = random.Random(42)  # one generator (NOT re-seeded each iteration)
    expected = [ref.random() < 0.5 for _ in range(10)]
    assert decisions == expected


# === build_report (4 axes) ==================================================


def test_build_report_pass_k_and_divergence() -> None:
    cases = [
        _bench.PassKCase(id="a", input="i", oracle_type="rules", expected=["1"], category="easy"),
        _bench.PassKCase(
            id="b", input="i", oracle_type="rules", expected=["1"], category="multistep"
        ),
    ]
    # case a: all 3 pass → pass@1=1.0, pass^k=1.0
    # case b: 2/3 pass → pass@1=0.667, pass^k=0.0
    baseline = [
        _case_runs("a", "easy", [_outcome(True), _outcome(True), _outcome(True)]),
        _case_runs("b", "multistep", [_outcome(True), _outcome(False), _outcome(True)]),
    ]
    report = _bench.build_report(cases, baseline, k=3)
    assert report.total_cases == 2
    assert report.pass_at_1 == pytest.approx((1.0 + 2 / 3) / 2)
    assert report.pass_k == pytest.approx(0.5)  # a all-pass (1), b not (0)
    assert report.divergence == pytest.approx(report.pass_at_1 - report.pass_k)
    assert report.per_category["easy"]["pass_k"] == pytest.approx(1.0)
    assert report.per_category["multistep"]["pass_k"] == pytest.approx(0.0)
    assert report.total_runs == 6


def test_build_report_behavioral_consistency() -> None:
    cases = [
        _bench.PassKCase(id="a", input="i", oracle_type="rules", expected=["1"], category="easy")
    ]
    # identical answers + identical tool seqs → consistent
    baseline = [
        _case_runs(
            "a",
            "easy",
            [
                _outcome(True, answer="42", tool_seq=("t",)),
                _outcome(True, answer="42", tool_seq=("t",)),
            ],
        )
    ]
    report = _bench.build_report(cases, baseline, k=2)
    assert report.answer_consistency == pytest.approx(1.0)
    assert report.tool_seq_consistency == pytest.approx(1.0)

    # divergent answers → answer inconsistent
    baseline2 = [
        _case_runs("a", "easy", [_outcome(True, answer="42"), _outcome(True, answer="forty-two")])
    ]
    report2 = _bench.build_report(cases, baseline2, k=2)
    assert report2.answer_consistency == pytest.approx(0.0)


def test_build_report_lambda_degradation() -> None:
    cases = [
        _bench.PassKCase(id="a", input="i", oracle_type="rules", expected=["1"], category="easy")
    ]
    baseline = [_case_runs("a", "easy", [_outcome(True), _outcome(True)])]  # pass^k = 1.0
    fault = [
        _case_runs("a", "easy", [_outcome(True), _outcome(False)], arm="fault")
    ]  # pass^k = 0.0
    report = _bench.build_report(cases, baseline, k=2, fault=fault, fault_rate=0.3)
    assert report.lambda_fault_rate == pytest.approx(0.3)
    assert report.lambda_degradation == pytest.approx(1.0)  # 1.0 − 0.0


def test_build_report_epsilon_instability() -> None:
    cases = [
        _bench.PassKCase(
            id="a",
            input="i",
            oracle_type="rules",
            expected=["1"],
            category="easy",
            perturbations=["p1"],
        )
    ]
    # orig variant pass^k = 1.0, paraphrase variant pass^k = 0.0 → spread 1.0
    epsilon = {
        "a": [
            _case_runs(
                "a", "easy", [_outcome(True), _outcome(True)], arm="epsilon", variant="orig"
            ),
            _case_runs(
                "a", "easy", [_outcome(False), _outcome(True)], arm="epsilon", variant="perturb-0"
            ),
        ]
    }
    baseline = [_case_runs("a", "easy", [_outcome(True), _outcome(True)])]
    report = _bench.build_report(cases, baseline, k=2, epsilon=epsilon)
    assert report.epsilon_cases == 1
    assert report.epsilon_instability == pytest.approx(1.0)


def test_report_to_markdown_renders() -> None:
    cases = [
        _bench.PassKCase(id="a", input="i", oracle_type="rules", expected=["1"], category="easy")
    ]
    baseline = [_case_runs("a", "easy", [_outcome(True)])]
    report = _bench.build_report(cases, baseline, k=1)
    md = _bench.report_to_markdown(report, stamp="2026-06-24T00:00:00")
    assert "pass^k Reliability Benchmark" in md
    assert "pass@1" in md
    assert "Per category" in md


# === run_case (drives a real AgentLoopImpl with the spy client; no Azure) ===


@pytest.mark.asyncio
async def test_run_case_drives_loop_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    # Patch the harness's executor factory so no business backend / DB is touched
    # (the spy returns end_turn with no tool calls → tools are never executed anyway).
    def _fake_executor(**kwargs: Any) -> tuple[Any, Any]:
        reg = ToolRegistryImpl()
        return reg, ToolExecutorImpl(registry=reg, handlers={})

    monkeypatch.setattr(_bench, "make_default_executor", _fake_executor)

    case = _bench.PassKCase(
        id="mult", input="What is 17 * 23?", oracle_type="rules", expected=["391"], category="easy"
    )
    spy = _SpyChatClient(content="The answer is 391.")
    runs = await _bench.run_case(
        case,
        k=3,
        action_client=spy,
        judge_client=spy,
        arm="baseline",
        variant="orig",
        user_input=case.input,
        fault_rate=0.0,
        rng=random.Random(1),
    )
    assert len(runs.outcomes) == 3
    assert all(o.passed for o in runs.outcomes)  # "391" is in the answer
    assert runs.pass_k == pytest.approx(1.0)
    assert spy.calls == 3  # one chat call per run (single end_turn turn)
