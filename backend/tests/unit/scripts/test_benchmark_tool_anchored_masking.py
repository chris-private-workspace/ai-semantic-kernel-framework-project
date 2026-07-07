"""
File: backend/tests/unit/scripts/test_benchmark_tool_anchored_masking.py
Purpose: CI-safe coverage of the tool-anchored masking A/B harness (load / build_transcript /
         measure_case OFF-vs-ON / retention / build_report) — fully deterministic, NO Azure.
Category: Tests / Unit / 範疇 4
Scope: Sprint 57.160

The harness is LLM-free (masking is a pure transform), so this pins the whole A/B against a
REAL TiktokenCounter + the corpus. Behavioural retention (agent still answers) is validated by
the Sprint 57.160 drive-through, not here.

Related:
    - backend/scripts/benchmark_tool_anchored_masking.py
    - backend/tests/fixtures/context_mgmt/tool_anchored_masking_cases.yaml
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from agent_harness.context_mgmt.token_counter.tiktoken_counter import TiktokenCounter

# Load backend/scripts/benchmark_tool_anchored_masking.py via importlib — the plain
# `from scripts.benchmark_tool_anchored_masking import ...` is shadowed by the
# `tests.unit.scripts` package (same idiom as test_benchmark_layered_compaction.py).
_ROOT = Path(__file__).resolve().parents[3]
_BENCH_PATH = _ROOT / "scripts" / "benchmark_tool_anchored_masking.py"
_spec = importlib.util.spec_from_file_location(
    "_benchmark_tool_anchored_masking_under_test", _BENCH_PATH
)
assert _spec is not None and _spec.loader is not None
_bench = importlib.util.module_from_spec(_spec)
sys.modules["_benchmark_tool_anchored_masking_under_test"] = _bench
_spec.loader.exec_module(_bench)

ToolAnchorCase = _bench.ToolAnchorCase
MaskResult = _bench.MaskResult
load_cases = _bench.load_cases
build_transcript = _bench.build_transcript
measure_case = _bench.measure_case
build_report = _bench.build_report
MATERIALITY_FLOOR = _bench.MATERIALITY_FLOOR
OFF_NOOP_CEIL = _bench.OFF_NOOP_CEIL

_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "context_mgmt"
    / "tool_anchored_masking_cases.yaml"
)


def _counter() -> TiktokenCounter:
    return TiktokenCounter(model="gpt-4o")


def _case(**overrides: object) -> ToolAnchorCase:
    base = dict(
        id="c",
        n_tool_calls=10,
        tool_result_chars=1500,
        tool_anchor_keep=3,
        user_text_chars=40,
        assistant_text_chars=0,
        keep_recent=5,
        note="",
    )
    base.update(overrides)
    return ToolAnchorCase(**base)  # type: ignore[arg-type]


# === load_cases ============================================================


def test_load_cases_parses_fixture() -> None:
    cases = load_cases(_FIXTURE)
    assert len(cases) == 8
    assert all(isinstance(c, ToolAnchorCase) for c in cases)
    assert all(c.id and c.n_tool_calls >= 1 and c.tool_result_chars > 0 for c in cases)
    assert all(c.tool_anchor_keep >= 1 for c in cases)
    # the <= keep boundary case must be present
    assert any(c.n_tool_calls <= c.tool_anchor_keep for c in cases)


def test_load_cases_rejects_missing_required_key(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text("cases:\n  - id: x\n    n_tool_calls: 3\n", encoding="utf-8")  # no chars/keep
    with pytest.raises(ValueError):
        load_cases(p)


def test_load_cases_rejects_duplicate_id(tmp_path: Path) -> None:
    p = tmp_path / "dup.yaml"
    p.write_text(
        "cases:\n"
        "  - {id: a, n_tool_calls: 3, tool_result_chars: 100, tool_anchor_keep: 1}\n"
        "  - {id: a, n_tool_calls: 4, tool_result_chars: 200, tool_anchor_keep: 2}\n",
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


def test_build_transcript_single_user_turn() -> None:
    msgs = build_transcript(_case(n_tool_calls=4, tool_result_chars=500))
    # 1 user + 4 × (assistant, tool)
    assert len(msgs) == 9
    assert msgs[0].role == "user"
    assert [m.role for m in msgs[1:3]] == ["assistant", "tool"]
    assert sum(1 for m in msgs if m.role == "user") == 1  # THE single-user-turn property
    tool_msgs = [m for m in msgs if m.role == "tool"]
    assert len(tool_msgs) == 4
    assert all(isinstance(m.content, str) and len(m.content) == 500 for m in tool_msgs)
    assert all(m.tool_calls for m in msgs if m.role == "assistant")


# === measure_case (deterministic, no LLM) ==================================


def test_measure_case_off_is_noop_on_is_reduction() -> None:
    """THE A/B: OFF (user-anchored) is a no-op on single-user-turn; ON (tool-anchored) reduces."""
    result = measure_case(
        _case(n_tool_calls=12, tool_result_chars=2000, tool_anchor_keep=3), _counter()
    )
    assert result.off_reduction == 0.0  # user-anchored no-op — the gap the fix targets
    assert result.off_tokens == result.l0_tokens
    assert result.on_reduction > 0.10  # tool-anchored materially reduces
    assert result.on_tokens < result.l0_tokens
    assert result.retention_ok is True


def test_measure_case_keep_covers_all_is_passthrough() -> None:
    """n_tool_calls <= tool_anchor_keep → ON passthrough (0 reduction) but retention still ok."""
    result = measure_case(
        _case(n_tool_calls=3, tool_result_chars=2000, tool_anchor_keep=5), _counter()
    )
    assert result.on_reduction == 0.0
    assert result.on_tokens == result.l0_tokens
    assert result.retention_ok is True


def test_measure_case_keep_1_most_aggressive() -> None:
    """tool_anchor_keep=1 keeps only the latest tool result → the largest reduction."""
    keep1 = measure_case(
        _case(n_tool_calls=10, tool_result_chars=1800, tool_anchor_keep=1), _counter()
    )
    keep5 = measure_case(
        _case(n_tool_calls=10, tool_result_chars=1800, tool_anchor_keep=5), _counter()
    )
    assert keep1.on_reduction > keep5.on_reduction
    assert keep1.retention_ok and keep5.retention_ok


def test_fixture_verdict_recommends_default_on() -> None:
    """The real corpus yields off≈0, on materially high, retention 100% → recommend True."""
    counter = _counter()
    results = [measure_case(c, counter) for c in load_cases(_FIXTURE)]
    report = build_report(results)
    assert report.mean_off_reduction <= OFF_NOOP_CEIL
    assert report.mean_on_reduction >= MATERIALITY_FLOOR
    assert report.retention_ok_rate == 1.0
    assert report.recommend_default_on is True


# === build_report ==========================================================


def _mask_result(rid: str, *, off: float, on: float, retention: bool) -> MaskResult:
    return MaskResult(
        id=rid,
        l0_tokens=1000,
        off_tokens=int(1000 * (1 - off)),
        on_tokens=int(1000 * (1 - on)),
        off_reduction=off,
        on_reduction=on,
        retention_ok=retention,
    )


def test_build_report_recommends_when_all_conditions_met() -> None:
    results = [
        _mask_result("a", off=0.0, on=0.50, retention=True),
        _mask_result("b", off=0.0, on=0.40, retention=True),
    ]
    report = build_report(results)
    assert report.mean_off_reduction == pytest.approx(0.0)
    assert report.mean_on_reduction == pytest.approx(0.45)
    assert report.retention_ok_rate == 1.0
    assert report.recommend_default_on is True


def test_build_report_not_recommended_when_retention_fails() -> None:
    results = [
        _mask_result("a", off=0.0, on=0.50, retention=True),
        _mask_result("b", off=0.0, on=0.40, retention=False),  # a retention failure vetoes
    ]
    report = build_report(results)
    assert report.retention_ok_rate == 0.5
    assert report.recommend_default_on is False


def test_build_report_not_recommended_when_off_not_noop() -> None:
    """A non-zero OFF reduction contradicts the single-user-turn premise → not recommended."""
    results = [
        _mask_result("a", off=0.05, on=0.50, retention=True),  # off exceeds the no-op ceiling
        _mask_result("b", off=0.05, on=0.40, retention=True),
    ]
    report = build_report(results)
    assert report.mean_off_reduction > OFF_NOOP_CEIL
    assert report.recommend_default_on is False


def test_build_report_not_recommended_below_materiality() -> None:
    results = [
        _mask_result("a", off=0.0, on=0.05, retention=True),
        _mask_result("b", off=0.0, on=0.08, retention=True),
    ]
    report = build_report(results)
    assert report.mean_on_reduction < MATERIALITY_FLOOR
    assert report.recommend_default_on is False
