"""
File: backend/tests/unit/scripts/test_benchmark_sandbox_escape.py
Purpose: CI-safe coverage of the sandbox escape harness (load / regex_screen / docker_contain /
         report) — NO real Docker.
Category: Tests / Unit / 範疇 9
Scope: Sprint 57.137

The real-Docker containment run lives in scripts/benchmark_sandbox_escape.py :: main()
(RUN_DOCKER_INTEGRATION / auto-detect via is_structurally_isolated). This file pins the pure
logic against the REAL DEFAULT_SANDBOX_PATTERNS + a fake backend so the harness — and the
corpus's should_match claims — are validated WITHOUT Docker.

Related:
    - backend/scripts/benchmark_sandbox_escape.py
    - backend/tests/fixtures/guardrails/sandbox_escape_cases.yaml
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from agent_harness.tools.sandbox import SandboxResult

# Load backend/scripts/benchmark_sandbox_escape.py via importlib — the plain
# `from scripts.benchmark_sandbox_escape import ...` is shadowed by the
# `tests.unit.scripts` package (same idiom as test_benchmark_correction_hygiene.py).
_ROOT = Path(__file__).resolve().parents[3]
_BENCH_PATH = _ROOT / "scripts" / "benchmark_sandbox_escape.py"
_spec = importlib.util.spec_from_file_location("_benchmark_sandbox_escape_under_test", _BENCH_PATH)
assert _spec is not None and _spec.loader is not None
_bench = importlib.util.module_from_spec(_spec)
sys.modules["_benchmark_sandbox_escape_under_test"] = _bench
_spec.loader.exec_module(_bench)

EscapeCase = _bench.EscapeCase
CaseResult = _bench.CaseResult
load_cases = _bench.load_cases
regex_screen = _bench.regex_screen
docker_contain = _bench.docker_contain
build_report = _bench.build_report
ESCAPE_SENTINEL = _bench.ESCAPE_SENTINEL

_FIXTURE = (
    Path(__file__).resolve().parents[2] / "fixtures" / "guardrails" / "sandbox_escape_cases.yaml"
)


# === load_cases ============================================================


def test_load_cases_parses_fixture() -> None:
    cases = load_cases(_FIXTURE)
    assert len(cases) == 10
    assert all(isinstance(c, EscapeCase) for c in cases)
    assert all(c.id and c.primitive and c.code for c in cases)


def test_load_cases_missing_key_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "cases:\n  - id: x\n    code: 'pass'\n", encoding="utf-8"
    )  # no primitive/should_match
    with pytest.raises(ValueError, match="missing required key"):
        load_cases(bad)


def test_load_cases_duplicate_id_raises(tmp_path: Path) -> None:
    bad = tmp_path / "dup.yaml"
    bad.write_text(
        "cases:\n"
        "  - {id: a, primitive: p, code: 'pass', should_match: false}\n"
        "  - {id: a, primitive: p, code: 'pass', should_match: false}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate case id"):
        load_cases(bad)


def test_load_cases_not_a_mapping_raises(tmp_path: Path) -> None:
    bad = tmp_path / "nolist.yaml"
    bad.write_text("cases: 42\n", encoding="utf-8")
    with pytest.raises(ValueError, match="non-empty list"):
        load_cases(bad)


# === regex_screen (the DETECT axis — against the REAL deny-list) ============


def test_regex_screen_matches_corpus_should_match() -> None:
    """Key invariant: every corpus case's should_match reflects the REAL deny-list behavior.

    This is what keeps the corpus honest — if a deny-list pattern changes, a corpus row's
    should_match claim must change with it (this test fails loudly otherwise).
    """
    cases = load_cases(_FIXTURE)
    for c in cases:
        assert (
            regex_screen(c.code) is c.should_match
        ), f"case {c.id!r}: regex_screen={regex_screen(c.code)} but should_match={c.should_match}"


def test_corpus_demonstrates_a_real_gap() -> None:
    """The corpus must contain BOTH caught and missed cases — else there's no gap to show."""
    cases = load_cases(_FIXTURE)
    caught = [c for c in cases if c.should_match]
    missed = [c for c in cases if not c.should_match]
    assert caught, "corpus has no deny-list-caught cases"
    assert missed, "corpus has no deny-list-MISSED cases (no escape gap demonstrated)"


def test_regex_screen_catches_known_primitive() -> None:
    assert regex_screen("import os; os.system('x')") is True
    assert regex_screen("import socket; socket.socket()") is True


def test_regex_screen_misses_unlisted_primitive() -> None:
    # urllib / http.client are real egress primitives the deny-list does not enumerate.
    assert regex_screen("import urllib.request; urllib.request.urlopen('http://x')") is False
    assert regex_screen("import ftplib; ftplib.FTP('x')") is False


# === docker_contain (the RESTRICT axis — fake backend, NO real Docker) =====


class _FakeBackend:
    """Stand-in SandboxBackend: returns a canned stdout (with/without the escape sentinel)."""

    def __init__(self, *, stdout: str) -> None:
        self._stdout = stdout

    async def execute(self, code: str, **kwargs: object) -> SandboxResult:
        return SandboxResult(
            stdout=self._stdout,
            stderr="",
            exit_code=0,
            duration_seconds=0.0,
            killed_by_timeout=False,
        )


@pytest.mark.asyncio
async def test_docker_contain_true_when_no_sentinel() -> None:
    backend = _FakeBackend(stdout="")  # egress blocked → no __ESCAPED__
    assert await docker_contain("anything", backend=backend) is True


@pytest.mark.asyncio
async def test_docker_contain_false_when_sentinel_present() -> None:
    backend = _FakeBackend(stdout=f"some output\n{ESCAPE_SENTINEL}\n")  # egress reached out
    assert await docker_contain("anything", backend=backend) is False


# === build_report (pure) ===================================================


def _r(cid: str, *, caught: bool, contained: bool | None) -> CaseResult:
    return CaseResult(
        id=cid, primitive="p", should_match=caught, regex_caught=caught, docker_contained=contained
    )


def test_build_report_escape_rate() -> None:
    results = [
        _r("a", caught=True, contained=True),
        _r("b", caught=False, contained=True),  # regex MISS
        _r("c", caught=False, contained=True),  # regex MISS
        _r("d", caught=True, contained=True),
    ]
    report = build_report(results, docker_ran=True)
    assert report.total == 4
    assert report.regex_caught == 2
    assert report.regex_missed == 2
    assert report.regex_escape_rate == 0.5
    assert report.docker_contained == 4
    assert report.docker_containment_rate == 1.0


def test_build_report_containment_gap_surfaces() -> None:
    results = [
        _r("a", caught=False, contained=True),
        _r("b", caught=False, contained=False),  # NOT contained — a real escape
    ]
    report = build_report(results, docker_ran=True)
    assert report.regex_escape_rate == 1.0  # both missed by regex
    assert report.docker_containment_rate == 0.5  # one escaped containment


def test_build_report_docker_skipped_containment_none() -> None:
    results = [_r("a", caught=True, contained=None)]
    report = build_report(results, docker_ran=False)
    assert report.docker_ran is False
    assert report.docker_containment_rate is None
    assert report.regex_escape_rate == 0.0  # the one case was caught
