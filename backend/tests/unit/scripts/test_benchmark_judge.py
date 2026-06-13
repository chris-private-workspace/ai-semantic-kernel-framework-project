"""
File: backend/tests/unit/scripts/test_benchmark_judge.py
Purpose: CI-safe coverage of the cheap-judge benchmark logic (load / run / score) — NO real LLM.
Category: Tests / Unit / 範疇 10
Scope: Sprint 57.111 (A3)
Created: 2026-06-13

The real-LLM run lives in tests/benchmark/test_judge_accuracy.py (@pytest.mark.benchmark,
skipped in CI). This file pins the pure logic with a spy Verifier + synthetic JudgeRuns so
the harness is validated WITHOUT Azure credentials.

Related:
    - backend/scripts/benchmark_judge.py
    - backend/tests/fixtures/verification/judge_benchmark.yaml
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from agent_harness._contracts import VerificationResult
from agent_harness._contracts.chat import Message
from agent_harness.verification import Verifier

# Load backend/scripts/benchmark_judge.py via importlib — the plain
# `from scripts.benchmark_judge import ...` is shadowed by the `tests.unit.scripts`
# package (same idiom as test_verify_audit_chain.py). Register in sys.modules BEFORE
# exec_module (Python 3.12 dataclass type-resolution accesses sys.modules[__module__]).
_ROOT = Path(__file__).resolve().parents[3]
_BENCH_PATH = _ROOT / "scripts" / "benchmark_judge.py"
_spec = importlib.util.spec_from_file_location("_benchmark_judge_under_test", _BENCH_PATH)
assert _spec is not None and _spec.loader is not None
_bench = importlib.util.module_from_spec(_spec)
sys.modules["_benchmark_judge_under_test"] = _bench
_spec.loader.exec_module(_bench)

BenchCase = _bench.BenchCase
JudgeRun = _bench.JudgeRun
build_report = _bench.build_report
load_cases = _bench.load_cases
run_judge = _bench.run_judge

_FIXTURE = (
    Path(__file__).resolve().parents[2] / "fixtures" / "verification" / "judge_benchmark.yaml"
)


# === load_cases ============================================================


def test_load_real_fixture_schema() -> None:
    cases = load_cases(_FIXTURE)
    assert 24 <= len(cases) <= 32  # the plan's curated range
    assert {c.category for c in cases} == {
        "clear_pass",
        "clear_fail",
        "trace_dependent",
        "borderline",
    }
    # trace_dependent cases carry a trace; clear_pass cases do not.
    td = [c for c in cases if c.category == "trace_dependent"]
    assert any(c.trace for c in td)
    assert all(not c.trace for c in cases if c.category == "clear_pass")
    assert len({c.id for c in cases}) == len(cases)  # unique ids


def test_load_rejects_missing_key(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text("cases:\n  - id: x\n    output: hi\n    category: clear_pass\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required key"):
        load_cases(p)


def test_load_rejects_bad_category(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text(
        "cases:\n  - id: x\n    output: hi\n    category: nonsense\n    expected_passed: true\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="invalid category"):
        load_cases(p)


def test_load_rejects_duplicate_id(tmp_path: Path) -> None:
    p = tmp_path / "dup.yaml"
    p.write_text(
        "cases:\n"
        "  - id: x\n    output: a\n    category: clear_pass\n    expected_passed: true\n"
        "  - id: x\n    output: b\n    category: clear_fail\n    expected_passed: false\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate case id"):
        load_cases(p)


# === run_judge =============================================================


class _SpyJudge(Verifier):
    """Records the state it received; returns a fixed verdict + fixed token usage."""

    def __init__(self, passed: bool = True) -> None:
        self._passed = passed
        self.states: list[object] = []

    async def verify(
        self, *, output: str, state: object = None, trace_context: object = None
    ) -> VerificationResult:
        self.states.append(state)
        return VerificationResult(
            passed=self._passed,
            verifier_name="spy",
            verifier_type="llm_judge",
            input_tokens=10,
            output_tokens=2,
        )


@pytest.mark.asyncio
async def test_run_judge_builds_state_and_accumulates_tokens() -> None:
    cases = [
        BenchCase(id="a", output="x", expected_passed=True, category="clear_pass"),
        BenchCase(
            id="b",
            output="y",
            expected_passed=False,
            category="trace_dependent",
            trace=[Message(role="tool", content="ERR: boom")],
        ),
    ]
    spy = _SpyJudge(passed=True)
    run = await run_judge(spy, cases, with_trace=True)  # type: ignore[arg-type]

    assert run.verdicts == [True, True]
    assert run.input_tokens == 20 and run.output_tokens == 4
    assert spy.states[0] is None  # no trace → state=None
    assert spy.states[1] is not None  # trace_dependent → minimal LoopState built
    assert spy.states[1].transient.messages[0].content == "ERR: boom"  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_run_judge_no_trace_passes_none() -> None:
    cases = [
        BenchCase(
            id="b",
            output="y",
            expected_passed=False,
            category="trace_dependent",
            trace=[Message(role="tool", content="ERR")],
        ),
    ]
    spy = _SpyJudge()
    await run_judge(spy, cases, with_trace=False)  # type: ignore[arg-type]
    assert spy.states == [None]  # with_trace=False → never builds state


# === build_report ==========================================================


def test_build_report_perfect_cheap_passes_floor() -> None:
    cases = [
        BenchCase(id="a", output="x", expected_passed=True, category="clear_pass"),
        BenchCase(id="b", output="y", expected_passed=False, category="clear_fail"),
    ]
    cheap = JudgeRun(verdicts=[True, False], input_tokens=10, output_tokens=2)  # == labels
    strong = JudgeRun(verdicts=[True, False], input_tokens=20, output_tokens=4)
    rep = build_report(cases, cheap, strong)

    assert rep.cheap_accuracy == 1.0
    assert rep.cheap_passes_floor is True
    assert rep.cheap_vs_strong_agreement == 1.0
    assert rep.cheap_tokens == 12 and rep.strong_tokens == 24


def test_build_report_trace_delta_positive() -> None:
    """The trace-dependent cases prove trace-awareness: WITH trace the cheap judge is
    right, WITHOUT trace it misses → a positive delta."""
    cases = [
        BenchCase(
            id="t1",
            output="claims success",
            expected_passed=False,
            category="trace_dependent",
            trace=[Message(role="tool", content="ERR")],
        ),
        BenchCase(
            id="t2",
            output="claims success",
            expected_passed=False,
            category="trace_dependent",
            trace=[Message(role="tool", content="ERR")],
        ),
    ]
    cheap_with = JudgeRun(verdicts=[False, False], input_tokens=10, output_tokens=2)  # caught both
    strong = JudgeRun(verdicts=[False, False], input_tokens=20, output_tokens=4)
    cheap_without = JudgeRun(verdicts=[True, True], input_tokens=10, output_tokens=2)  # missed both
    rep = build_report(cases, cheap_with, strong, cheap_no_trace=cheap_without)

    assert rep.trace_delta == 1.0  # with=1.0 acc, without=0.0 acc


def test_build_report_floor_excludes_borderline() -> None:
    cases = [
        BenchCase(id="a", output="x", expected_passed=True, category="clear_pass"),
        BenchCase(id="z", output="amb", expected_passed=True, category="borderline"),
    ]
    cheap = JudgeRun(verdicts=[True, False], input_tokens=10, output_tokens=2)  # wrong ONLY on bd
    strong = JudgeRun(verdicts=[True, True], input_tokens=20, output_tokens=4)
    rep = build_report(cases, cheap, strong)

    # unambiguous accuracy (clear_pass only) = 1.0 → floor passes despite the borderline miss
    assert rep.cheap_passes_floor is True
    assert rep.cheap_accuracy == 0.5  # overall includes the borderline miss
