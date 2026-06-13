"""
File: backend/tests/benchmark/test_judge_accuracy.py
Purpose: A3 real-LLM cheap-judge accuracy benchmark wrapper (@pytest.mark.benchmark + skipif).
Category: Tests / Benchmark / 範疇 10
Scope: Sprint 57.111 (A3)
Created: 2026-06-13

This is the ON-DEMAND benchmark. It is deselected from CI two ways: the `benchmark`
marker AND a RUN_AZURE_INTEGRATION skipif (CI has neither set → it SKIPS, never fails).
Run it with real Azure creds:
    RUN_AZURE_INTEGRATION=1 AZURE_OPENAI_*=... pytest -m benchmark
or equivalently `python scripts/benchmark_judge.py`. The CI-safe coverage of the
load/run/score logic lives in tests/unit/scripts/test_benchmark_judge.py.

Related:
    - backend/scripts/benchmark_judge.py
    - backend/tests/fixtures/verification/judge_benchmark.yaml
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

from agent_harness.verification import LLMJudgeVerifier

# Load backend/scripts/benchmark_judge.py via importlib — `from scripts.benchmark_judge`
# is shadowed by the `tests.unit.scripts` package once it is collected in the same session
# (same idiom as test_verify_audit_chain.py). Register in sys.modules BEFORE exec_module.
_ROOT = Path(__file__).resolve().parents[2]
_BENCH_PATH = _ROOT / "scripts" / "benchmark_judge.py"
_spec = importlib.util.spec_from_file_location("_benchmark_judge_under_test", _BENCH_PATH)
assert _spec is not None and _spec.loader is not None
_bench = importlib.util.module_from_spec(_spec)
sys.modules["_benchmark_judge_under_test"] = _bench
_spec.loader.exec_module(_bench)

CHEAP_ACCURACY_FLOOR = _bench.CHEAP_ACCURACY_FLOOR
build_report = _bench.build_report
load_cases = _bench.load_cases
run_judge = _bench.run_judge

_FIXTURE = (
    Path(__file__).resolve().parents[1] / "fixtures" / "verification" / "judge_benchmark.yaml"
)

pytestmark = [
    pytest.mark.benchmark,
    pytest.mark.skipif(
        os.environ.get("RUN_AZURE_INTEGRATION") != "1",
        reason=(
            "Real-LLM cheap-judge accuracy benchmark — set RUN_AZURE_INTEGRATION=1 "
            "and AZURE_OPENAI_* env vars to enable."
        ),
    ),
]


@pytest.mark.asyncio
async def test_cheap_judge_accuracy_benchmark() -> None:
    """Run the cheap + strong judge over the golden fixture; assert the tracked floor.

    The measured numbers (cheap/strong accuracy, agreement, trace_delta) are recorded
    into design note 24's verdict at sprint closeout — this assertion is the automated
    floor; the keep-cheap-vs-move-to-strong decision is the human go/no-go on the numbers.
    """
    from adapters.azure_openai.profile import build_azure_model_profile

    cases = load_cases(_FIXTURE)
    profile = build_azure_model_profile()
    cheap = LLMJudgeVerifier(
        chat_client=profile.cheap, judge_template="output_quality", temperature=0.0
    )
    strong = LLMJudgeVerifier(
        chat_client=profile.action, judge_template="output_quality", temperature=0.0
    )

    cheap_run = await run_judge(cheap, cases, with_trace=True)
    strong_run = await run_judge(strong, cases, with_trace=True)
    cheap_no_trace = await run_judge(cheap, cases, with_trace=False)
    report = build_report(cases, cheap_run, strong_run, cheap_no_trace=cheap_no_trace)

    print(
        f"\n[benchmark] cheap={report.cheap_accuracy:.2%} strong={report.strong_accuracy:.2%} "
        f"agreement={report.cheap_vs_strong_agreement:.2%} trace_delta={report.trace_delta} "
        f"cheap_tokens={report.cheap_tokens} strong_tokens={report.strong_tokens}"
    )

    assert report.cheap_passes_floor, (
        f"cheap judge accuracy on unambiguous cases below the {CHEAP_ACCURACY_FLOOR:.0%} floor "
        f"→ design note 24 verdict = keep the judge on the strong tier"
    )
