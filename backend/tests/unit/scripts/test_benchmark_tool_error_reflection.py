"""
File: backend/tests/unit/scripts/test_benchmark_tool_error_reflection.py
Purpose: CI-safe coverage of the tool-error reflection A/B logic (load / observation / build /
         run / judge / report) — NO real LLM.
Category: Tests / Unit / 範疇 2
Scope: Sprint 57.144 (research #7 Half B)

The real-LLM A/B run lives in scripts/benchmark_tool_error_reflection.py :: main()
(RUN_AZURE_INTEGRATION). This file pins the pure logic with fake ChatClients so the harness
is validated WITHOUT Azure credentials.

Related:
    - backend/scripts/benchmark_tool_error_reflection.py
    - backend/tests/fixtures/tools/tool_error_reflection_cases.yaml
"""

from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

from agent_harness._contracts.chat import ChatResponse, TokenUsage

# Load backend/scripts/benchmark_tool_error_reflection.py via importlib — the plain
# `from scripts...` import is shadowed by the `tests.unit.scripts` package (same idiom as
# test_benchmark_correction_hygiene.py). Register in sys.modules BEFORE exec_module.
_ROOT = Path(__file__).resolve().parents[3]
_BENCH_PATH = _ROOT / "scripts" / "benchmark_tool_error_reflection.py"
_spec = importlib.util.spec_from_file_location(
    "_benchmark_tool_error_reflection_under_test", _BENCH_PATH
)
assert _spec is not None and _spec.loader is not None
_bench = importlib.util.module_from_spec(_spec)
sys.modules["_benchmark_tool_error_reflection_under_test"] = _bench
_spec.loader.exec_module(_bench)

ReflectionCase = _bench.ReflectionCase
ArmRun = _bench.ArmRun
load_cases = _bench.load_cases
observation_for = _bench.observation_for
build_messages = _bench.build_messages
run_arm = _bench.run_arm
judge_recovery = _bench.judge_recovery
build_report = _bench.build_report
MATERIALITY = _bench.MATERIALITY

_FIXTURE = (
    Path(__file__).resolve().parents[2] / "fixtures" / "tools" / "tool_error_reflection_cases.yaml"
)


class _MockChat:
    """Returns canned texts per chat() call; records the requests it received."""

    def __init__(self, texts: list[str], *, completion_tokens: int = 7) -> None:
        self._texts = texts
        self._idx = 0
        self.requests: list[Any] = []
        self._ct = completion_tokens

    async def chat(self, request: Any, **kwargs: Any) -> ChatResponse:
        self.requests.append(request)
        text = self._texts[self._idx % len(self._texts)]
        self._idx += 1
        return ChatResponse(
            model="mock",
            content=text,
            usage=TokenUsage(prompt_tokens=50, completion_tokens=self._ct),
        )


def _case(**kw: Any) -> ReflectionCase:
    base = dict(
        id="c",
        user_prompt="do a thing",
        tool_name="some_tool",
        bad_call='{"a": 1}',
        error_class="",
        is_schema_error=False,
        is_unknown_tool=False,
        raw_error="schema mismatch: a: 'q' is a required property",
        success_criterion="adds the missing arg",
    )
    base.update(kw)
    return ReflectionCase(**base)  # type: ignore[arg-type]


# === load_cases ============================================================


def test_load_cases_real_fixture() -> None:
    cases = load_cases(_FIXTURE)
    assert len(cases) >= 6
    ids = [c.id for c in cases]
    assert len(ids) == len(set(ids))  # unique
    # at least one of each taxonomy-driving shape is represented
    assert any(c.is_schema_error for c in cases)
    assert any(c.is_unknown_tool for c in cases)
    assert any(c.error_class for c in cases)


def test_load_cases_rejects_missing_key(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("cases:\n  - id: x\n    user_prompt: p\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_cases(bad)


def test_load_cases_rejects_empty(tmp_path: Path) -> None:
    bad = tmp_path / "empty.yaml"
    bad.write_text("cases: []\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_cases(bad)


# === observation_for / build_messages ======================================


def test_observation_plain_is_raw_error() -> None:
    c = _case(raw_error="boom happened")
    assert observation_for(c, "plain") == "boom happened"


def test_observation_reflection_is_typed() -> None:
    c = _case(is_schema_error=True, raw_error="q: 'q' is a required property")
    obs = observation_for(c, "reflection")
    assert "parameter error" in obs  # the typed label
    assert "q: 'q' is a required property" in obs  # raw preserved
    assert obs != c.raw_error  # enriched


def test_observation_reflection_failed_api() -> None:
    c = _case(error_class="aiohttp.ClientConnectionError", raw_error="connection refused")
    assert "tool execution failed (external/API error)" in observation_for(c, "reflection")


def test_build_messages_three_turns_and_arm_difference() -> None:
    c = _case(is_schema_error=True)
    plain = build_messages(c, "plain")
    refl = build_messages(c, "reflection")
    assert len(plain) == 3 == len(refl)
    assert [m.role for m in plain] == ["user", "assistant", "user"]
    # only the final (observation) user turn differs
    assert plain[0].content == refl[0].content
    assert plain[2].content != refl[2].content


def test_build_messages_unknown_arm_falls_back_to_plain() -> None:
    c = _case()
    assert build_messages(c, "bogus")[2].content == build_messages(c, "plain")[2].content


# === judge_recovery / run_arm / build_report ===============================


def test_judge_recovery_pass_fail() -> None:
    judge_pass = _MockChat(["PASS"])
    judge_fail = _MockChat(["FAIL — does not satisfy"])
    assert asyncio.run(judge_recovery(judge_pass, "crit", "resp")) is True
    assert asyncio.run(judge_recovery(judge_fail, "crit", "resp")) is False


def test_run_arm_all_pass() -> None:
    cases = [_case(id="a"), _case(id="b")]
    answerer = _MockChat(["I'll add the missing argument."])
    judge = _MockChat(["PASS"])
    run = asyncio.run(run_arm("reflection", cases, answerer=answerer, judge=judge))
    assert run.n == 2
    assert run.fixes == 2
    assert run.fix_rate == 1.0
    assert run.mean_completion_tokens == 7.0


def test_run_arm_all_fail() -> None:
    cases = [_case(id="a"), _case(id="b")]
    run = asyncio.run(
        run_arm("plain", cases, answerer=_MockChat(["blah"]), judge=_MockChat(["FAIL"]))
    )
    assert run.fixes == 0
    assert run.fix_rate == 0.0


def test_build_report_recommends_when_material() -> None:
    plain = ArmRun(arm="plain", n=10, fixes=5, fix_rate=0.5, mean_completion_tokens=10.0)
    reflection = ArmRun(arm="reflection", n=10, fixes=7, fix_rate=0.7, mean_completion_tokens=14.0)
    report = build_report(plain, reflection)
    assert report.fix_delta == pytest.approx(0.2)
    assert report.reflection_recommended is True  # 0.2 >= MATERIALITY


def test_build_report_keeps_when_immaterial() -> None:
    plain = ArmRun(arm="plain", n=10, fixes=6, fix_rate=0.6, mean_completion_tokens=10.0)
    reflection = ArmRun(arm="reflection", n=10, fixes=6, fix_rate=0.6, mean_completion_tokens=12.0)
    report = build_report(plain, reflection)
    assert report.fix_delta == pytest.approx(0.0)
    assert report.reflection_recommended is False
    assert report.token_delta == pytest.approx(2.0)
