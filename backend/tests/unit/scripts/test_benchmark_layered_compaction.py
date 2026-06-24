"""
File: backend/tests/unit/scripts/test_benchmark_layered_compaction.py
Purpose: CI-safe coverage of the layered-compaction harness (load / build_transcript /
         measure_case L0/L1/L2 / build_report) — NO Azure.
Category: Tests / Unit / 範疇 4
Scope: Sprint 57.139

The real-Azure semantic (L3) run lives in scripts/benchmark_layered_compaction.py :: main()
(RUN_AZURE_INTEGRATION). This file pins the pure logic + the LLM-free layers against a REAL
TiktokenCounter + the corpus, WITHOUT Azure.

Related:
    - backend/scripts/benchmark_layered_compaction.py
    - backend/tests/fixtures/context_mgmt/layered_compaction_cases.yaml
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from agent_harness.context_mgmt.token_counter.tiktoken_counter import TiktokenCounter

# Load backend/scripts/benchmark_layered_compaction.py via importlib — the plain
# `from scripts.benchmark_layered_compaction import ...` is shadowed by the
# `tests.unit.scripts` package (same idiom as test_benchmark_sandbox_escape.py).
_ROOT = Path(__file__).resolve().parents[3]
_BENCH_PATH = _ROOT / "scripts" / "benchmark_layered_compaction.py"
_spec = importlib.util.spec_from_file_location(
    "_benchmark_layered_compaction_under_test", _BENCH_PATH
)
assert _spec is not None and _spec.loader is not None
_bench = importlib.util.module_from_spec(_spec)
sys.modules["_benchmark_layered_compaction_under_test"] = _bench
_spec.loader.exec_module(_bench)

CompactionCase = _bench.CompactionCase
LayerResult = _bench.LayerResult
load_cases = _bench.load_cases
build_transcript = _bench.build_transcript
measure_case = _bench.measure_case
build_report = _bench.build_report
ACON_BAND = _bench.ACON_BAND
DEFER_THRESHOLD = _bench.DEFER_THRESHOLD

_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "context_mgmt"
    / "layered_compaction_cases.yaml"
)


def _counter() -> TiktokenCounter:
    return TiktokenCounter(model="gpt-4o")


# === load_cases ============================================================


def test_load_cases_parses_fixture() -> None:
    cases = load_cases(_FIXTURE)
    assert len(cases) == 6
    assert all(isinstance(c, CompactionCase) for c in cases)
    assert all(c.id and c.n_user_turns >= 1 and c.tool_result_chars > 0 for c in cases)
    # the single-turn NO-OP demo case must be present
    assert any(c.n_user_turns == 1 for c in cases)


def test_load_cases_rejects_missing_required_key(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text(
        "cases:\n  - id: x\n    n_user_turns: 3\n", encoding="utf-8"
    )  # no tool_result_chars
    with pytest.raises(ValueError):
        load_cases(p)


def test_load_cases_rejects_duplicate_id(tmp_path: Path) -> None:
    p = tmp_path / "dup.yaml"
    p.write_text(
        "cases:\n"
        "  - {id: a, n_user_turns: 3, tool_result_chars: 100}\n"
        "  - {id: a, n_user_turns: 4, tool_result_chars: 200}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_cases(p)


def test_load_cases_rejects_empty(tmp_path: Path) -> None:
    p = tmp_path / "empty.yaml"
    p.write_text("cases: []\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_cases(p)


# === build_transcript ======================================================


def test_build_transcript_structure() -> None:
    case = CompactionCase(
        id="t",
        n_user_turns=4,
        tool_result_chars=500,
        user_text_chars=40,
        assistant_text_chars=10,
        keep_recent=5,
        note="",
    )
    msgs = build_transcript(case)
    assert len(msgs) == 12  # 3 per turn
    assert [m.role for m in msgs[:3]] == ["user", "assistant", "tool"]
    tool_msgs = [m for m in msgs if m.role == "tool"]
    assert len(tool_msgs) == 4
    assert all(isinstance(m.content, str) and len(m.content) == 500 for m in tool_msgs)
    assert all(m.tool_calls for m in msgs if m.role == "assistant")


# === measure_case (LLM-free; hybrid_factory=None) ==========================


@pytest.mark.asyncio
async def test_measure_case_llm_free_has_no_l3() -> None:
    """No hybrid_factory → the Azure L3 arm never runs (l3 None, semantic_reduction None)."""
    case = load_cases(_FIXTURE)[0]  # tool-heavy-long
    result = await measure_case(case, _counter(), hybrid_factory=None)
    assert result.l3_semantic is None
    assert result.semantic_reduction is None
    assert 0.0 <= result.tool_clear_reduction <= 1.0


@pytest.mark.asyncio
async def test_measure_case_multi_turn_reduces() -> None:
    """A deep tool-heavy transcript → tool-clear reclaims a positive fraction."""
    case = CompactionCase(
        id="deep",
        n_user_turns=12,
        tool_result_chars=2000,
        user_text_chars=40,
        assistant_text_chars=0,
        keep_recent=5,
        note="",
    )
    result = await measure_case(case, _counter(), hybrid_factory=None)
    assert result.l1_tool_clear < result.l0_tokens
    assert result.tool_clear_reduction > 0.0


@pytest.mark.asyncio
async def test_tool_clear_equals_structural_on_non_redundant_corpus() -> None:
    """The synthetic corpus has unique tool args (no retries) → structural's dedup drops
    nothing, so structural reduction == tool-clear reduction (masking IS structural's value)."""
    case = CompactionCase(
        id="deep",
        n_user_turns=10,
        tool_result_chars=1500,
        user_text_chars=40,
        assistant_text_chars=0,
        keep_recent=5,
        note="",
    )
    result = await measure_case(case, _counter(), hybrid_factory=None)
    assert result.l1_tool_clear == result.l2_structural


@pytest.mark.asyncio
async def test_single_turn_is_noop_zero_reduction() -> None:
    """KEY (user-anchored limitation): one user turn → masker NO-OPs → 0 reduction."""
    case = CompactionCase(
        id="one",
        n_user_turns=1,
        tool_result_chars=8000,
        user_text_chars=40,
        assistant_text_chars=0,
        keep_recent=5,
        note="",
    )
    result = await measure_case(case, _counter(), hybrid_factory=None)
    assert result.tool_clear_reduction == 0.0
    assert result.l1_tool_clear == result.l0_tokens
    assert result.semantic_deferred is False


# === build_report ==========================================================


def _layer(rid: str, tc_reduction: float) -> LayerResult:
    return LayerResult(
        id=rid,
        l0_tokens=1000,
        l1_tool_clear=int(1000 * (1 - tc_reduction)),
        l2_structural=int(1000 * (1 - tc_reduction)),
        l3_semantic=None,
        tool_clear_reduction=tc_reduction,
        structural_reduction=tc_reduction,
        semantic_reduction=None,
        semantic_deferred=tc_reduction >= DEFER_THRESHOLD,
    )


def test_build_report_band_and_deferral() -> None:
    """mean in [0.26, 0.54] → in_acon_band; deferral counts cases >= DEFER_THRESHOLD."""
    results = [_layer("a", 0.30), _layer("b", 0.40)]  # mean 0.35 in band
    report = build_report(results)
    assert report.mean_tool_clear_reduction == pytest.approx(0.35)
    assert report.in_acon_band is True
    assert report.semantic_deferred_rate == pytest.approx(0.5)  # 0.40>=.333 yes, 0.30 no
    assert report.preclear_recommended is True  # in band AND deferred_rate >= 0.5


def test_build_report_out_of_band_not_recommended() -> None:
    """A prose-dominated set (low tool-clear) → out of band → not recommended."""
    results = [_layer("a", 0.05), _layer("b", 0.10)]  # mean 0.075 below band
    report = build_report(results)
    assert report.in_acon_band is False
    assert report.preclear_recommended is False


def test_build_report_semantic_none_without_azure() -> None:
    report = build_report([_layer("a", 0.30), _layer("b", 0.40)])
    assert report.semantic_ran is False
    assert report.mean_semantic_reduction is None


def test_acon_band_constant() -> None:
    assert ACON_BAND == (0.26, 0.54)
