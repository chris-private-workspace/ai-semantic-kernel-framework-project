"""
File: backend/tests/unit/scripts/test_benchmark_combined_formation_quality.py
Purpose: CI-safe coverage of the combined formation quality A/B logic (load / score_facts
         / score_summary / run_arm / build_report) — NO real LLM.
Category: Tests / Unit / 範疇 3
Scope: Sprint 57.154 (AD-Memory-Combined-Formation-AB-Quality)
Created: 2026-07-01

The real-LLM A/B run lives in scripts/benchmark_combined_formation_quality.py :: main()
(RUN_AZURE_INTEGRATION). This file pins the pure + offline logic with spy ChatClients (formation +
judge) + capturing sinks so the harness is validated WITHOUT Azure credentials. In particular
run_arm drives the REAL MemoryFormationWorker.form() offline, asserting the efficiency invariant
(combined = 1 chat() / separate = 2 chat() per case).

Related:
    - backend/scripts/benchmark_combined_formation_quality.py
    - backend/tests/fixtures/memory/memory_formation_quality_cases.yaml
"""

from __future__ import annotations

import importlib.util
import json
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

# Load backend/scripts/benchmark_combined_formation_quality.py via importlib — the plain
# `from scripts.… import` is shadowed by the `tests.unit.scripts` package (same idiom as
# test_benchmark_memory_grounded_judge.py). Register in sys.modules BEFORE exec_module (Python 3.12
# dataclass type-resolution accesses sys.modules).
_ROOT = Path(__file__).resolve().parents[3]
_BENCH_PATH = _ROOT / "scripts" / "benchmark_combined_formation_quality.py"
_spec = importlib.util.spec_from_file_location(
    "_benchmark_combined_formation_quality_under_test", _BENCH_PATH
)
assert _spec is not None and _spec.loader is not None
_bench = importlib.util.module_from_spec(_spec)
sys.modules["_benchmark_combined_formation_quality_under_test"] = _bench
_spec.loader.exec_module(_bench)

FormationCase = _bench.FormationCase
ArmScore = _bench.ArmScore
load_cases = _bench.load_cases
score_facts = _bench.score_facts
score_summary = _bench.score_summary
run_arm = _bench.run_arm
build_report = _bench.build_report
_parse_score = _bench._parse_score

_FIXTURE = _ROOT / "tests" / "fixtures" / "memory" / "memory_formation_quality_cases.yaml"


# === Spy ChatClients (no Azure) =============================================


class _BaseSpyClient(ChatClient):
    """Shared ABC stubs; subclasses override chat(). Counts calls."""

    def __init__(self) -> None:
        self.calls = 0

    def _resp(self, content: str) -> ChatResponse:
        return ChatResponse(
            model="spy-model",
            content=content,
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
        return MagicMock(spec=ModelInfo)


_COMBINED_REPLY = json.dumps(
    {
        "facts": [{"content": "User name is Marcus", "confidence": 0.9}],
        "summary": "Talked about a Redis to DynamoDB migration.",
        "key_decisions": ["move to DynamoDB"],
        "unresolved_issues": [],
    }
)
_EXTRACT_REPLY = json.dumps([{"content": "User name is Marcus", "confidence": 0.9}])
_SUMMARY_REPLY = json.dumps(
    {
        "summary": "Talked about a Redis to DynamoDB migration.",
        "key_decisions": ["move to DynamoDB"],
        "unresolved_issues": [],
    }
)


class _FormationSpy(_BaseSpyClient):
    """Scripted formation client: returns combined / extraction / summary JSON by prompt marker."""

    async def chat(
        self,
        request: ChatRequest,
        *,
        cache_breakpoints: list[CacheBreakpoint] | None = None,
        trace_context: TraceContext | None = None,
    ) -> ChatResponse:
        self.calls += 1
        raw = request.messages[0].content if request.messages else ""
        text = raw if isinstance(raw, str) else ""
        if "memory formation assistant" in text:
            return self._resp(_COMBINED_REPLY)
        if "memory extraction assistant" in text:
            return self._resp(_EXTRACT_REPLY)
        if "session memory assistant" in text:
            return self._resp(_SUMMARY_REPLY)
        return self._resp("{}")


class _JudgeSpy(_BaseSpyClient):
    """Judge client: returns a fixed {"score": x}."""

    def __init__(self, score: float = 0.8) -> None:
        super().__init__()
        self._score = score

    async def chat(
        self,
        request: ChatRequest,
        *,
        cache_breakpoints: list[CacheBreakpoint] | None = None,
        trace_context: TraceContext | None = None,
    ) -> ChatResponse:
        self.calls += 1
        return self._resp(json.dumps({"score": self._score}))


def _mk_case(cid: str = "c1") -> Any:
    return FormationCase(
        id=cid,
        conversation=[{"role": "user", "content": "Hi, I'm Marcus, migrating Redis to DynamoDB."}],
        expected_facts=[["marcus"], ["redis", "dynamodb"]],
        expected_summary_points=["migration"],
        expects_facts=True,
    )


def _write(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "cases.yaml"
    p.write_text(body, encoding="utf-8")
    return p


# === load_cases ============================================================


def test_load_cases_happy() -> None:
    cases = load_cases(_FIXTURE)
    assert len(cases) >= 10
    ids = {c.id for c in cases}
    assert "db_migration_clear" in ids
    zero_fact = [c for c in cases if not c.expects_facts]
    assert zero_fact and all(c.expected_facts == [] for c in zero_fact)
    first = next(c for c in cases if c.id == "db_migration_clear")
    assert ["marcus"] in first.expected_facts
    assert first.conversation[0]["role"] == "user"


def test_load_cases_top_level_not_mapping(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        load_cases(_write(tmp_path, "- just a list\n"))


def test_load_cases_missing_key(tmp_path: Path) -> None:
    body = "cases:\n  - id: a\n    conversation:\n      - {role: user, content: hi}\n"
    with pytest.raises(ValueError):  # missing expected_facts / expected_summary_points
        load_cases(_write(tmp_path, body))


def test_load_cases_duplicate_id(tmp_path: Path) -> None:
    turn = "    conversation:\n      - {role: user, content: hi}\n"
    tail = "    expected_facts: []\n    expected_summary_points: []\n"
    body = f"cases:\n  - id: dup\n{turn}{tail}  - id: dup\n{turn}{tail}"
    with pytest.raises(ValueError):
        load_cases(_write(tmp_path, body))


def test_load_cases_bad_conversation_turn(tmp_path: Path) -> None:
    body = (
        "cases:\n  - id: a\n    conversation:\n      - {role: user}\n"
        "    expected_facts: []\n    expected_summary_points: []\n"
    )
    with pytest.raises(ValueError):  # turn missing 'content'
        load_cases(_write(tmp_path, body))


# === score_facts (deterministic) ===========================================


def test_score_facts_full_coverage() -> None:
    coverage, spurious = score_facts(
        ["User name is Marcus", "Migrating from Redis to DynamoDB"],
        [["marcus"], ["redis", "dynamodb"]],
    )
    assert coverage == 1.0
    assert spurious == 0


def test_score_facts_partial_coverage() -> None:
    coverage, spurious = score_facts(["User name is Marcus"], [["marcus"], ["redis", "dynamodb"]])
    assert coverage == 0.5
    assert spurious == 0


def test_score_facts_spurious_on_empty_expected() -> None:
    coverage, spurious = score_facts(["User likes pineapple pizza"], [])
    assert coverage == 1.0  # vacuous
    assert spurious == 1


def test_score_facts_spurious_count() -> None:
    coverage, spurious = score_facts(["User name is Marcus", "User enjoys hiking"], [["marcus"]])
    assert coverage == 1.0
    assert spurious == 1  # the hiking fact matches no expected group


# === _parse_score ==========================================================


def test_parse_score_json() -> None:
    assert _parse_score('{"score": 0.7}') == 0.7


def test_parse_score_prose_wrapped() -> None:
    assert _parse_score('Sure, here it is: {"score": 0.9}. Done.') == 0.9


def test_parse_score_clamps() -> None:
    assert _parse_score('{"score": 1.5}') == 1.0
    assert _parse_score('{"score": -0.2}') == 0.0


def test_parse_score_bare_float() -> None:
    assert _parse_score("0.6") == 0.6


def test_parse_score_unparseable() -> None:
    assert _parse_score("") == 0.0
    assert _parse_score("no digits here") == 0.0


# === score_summary (LLM judge — spy) =======================================


async def test_score_summary_none_short_circuits() -> None:
    judge = _JudgeSpy(score=0.8)
    result = await score_summary(judge, conversation="x", summary_obj=None, expected_points=[])
    assert result == 0.0
    assert judge.calls == 0  # no summary → no judge call


async def test_score_summary_spy_score() -> None:
    judge = _JudgeSpy(score=0.8)
    summary_obj = {"summary": "A migration chat.", "key_decisions": [], "unresolved_issues": []}
    result = await score_summary(
        judge, conversation="[user] hi", summary_obj=summary_obj, expected_points=["migration"]
    )
    assert result == 0.8
    assert judge.calls == 1


# === run_arm drives the REAL worker (efficiency invariant) =================


async def test_run_arm_combined_one_call_per_case() -> None:
    formation, judge = _FormationSpy(), _JudgeSpy()
    cases = [_mk_case("a"), _mk_case("b")]
    score = await run_arm("combined", cases, chat_client=formation, judge=judge)
    assert formation.calls == 2  # ONE combined chat() per case
    assert judge.calls == 2  # one summary judge per case
    assert score.arm == "combined"
    assert score.n_cases == 2


async def test_run_arm_separate_two_calls_per_case() -> None:
    formation, judge = _FormationSpy(), _JudgeSpy()
    cases = [_mk_case("a"), _mk_case("b")]
    await run_arm("separate", cases, chat_client=formation, judge=judge)
    assert formation.calls == 4  # extract + summarize = TWO chat() per case
    assert judge.calls == 2


async def test_run_arm_scores_captured_facts() -> None:
    formation, judge = _FormationSpy(), _JudgeSpy(score=0.9)
    # the combined spy emits a "User name is Marcus" fact → covers the ["marcus"] group
    case = FormationCase(
        id="m",
        conversation=[{"role": "user", "content": "I'm Marcus."}],
        expected_facts=[["marcus"]],
        expected_summary_points=["migration"],
        expects_facts=True,
    )
    score = await run_arm("combined", [case], chat_client=formation, judge=judge)
    assert score.facts_coverage == 1.0
    assert score.summary_score == 0.9


# === build_report (two-sided verdict) ======================================


def _arm(name: str, *, cov: float = 0.90, spur: float = 0.2, summ: float = 0.85) -> Any:
    return ArmScore(
        arm=name, n_cases=10, facts_coverage=cov, facts_spurious_mean=spur, summary_score=summ
    )


def test_build_report_keep_on_tie() -> None:
    report = build_report(_arm("combined"), _arm("separate"))
    assert report.combined_recommended is True


def test_build_report_keep_within_materiality() -> None:
    # combined 3pp lower on both axes = within the 5pp band → still KEEP
    report = build_report(_arm("combined", cov=0.87, summ=0.82), _arm("separate"))
    assert report.combined_recommended is True


def test_build_report_flip_on_facts_regression() -> None:
    report = build_report(_arm("combined", cov=0.70), _arm("separate", cov=0.90))
    assert report.combined_recommended is False
    assert report.facts_coverage_delta < 0


def test_build_report_flip_on_summary_regression() -> None:
    report = build_report(_arm("combined", summ=0.60), _arm("separate", summ=0.85))
    assert report.combined_recommended is False


def test_build_report_flip_on_spurious_inflation() -> None:
    report = build_report(_arm("combined", spur=2.0), _arm("separate", spur=0.2))
    assert report.combined_recommended is False
    assert report.spurious_delta > 1.0
