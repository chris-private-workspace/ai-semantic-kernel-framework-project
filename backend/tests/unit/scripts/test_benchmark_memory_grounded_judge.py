"""
File: backend/tests/unit/scripts/test_benchmark_memory_grounded_judge.py
Purpose: CI-safe coverage of the memory-grounded-judge A/B logic (load / build_judge_state / run_arm
         / build_report) — NO real LLM.
Category: Tests / Unit / 範疇 10
Scope: Sprint 57.153 (AD-Verification-Judge-Memory-Inject-Blind)
Created: 2026-07-01

The real-LLM A/B run lives in scripts/benchmark_memory_grounded_judge.py :: main()
(RUN_AZURE_INTEGRATION). This file pins the pure logic with a spy judge so the harness is validated
WITHOUT Azure credentials.

Related:
    - backend/scripts/benchmark_memory_grounded_judge.py
    - backend/tests/fixtures/verification/memory_grounded_judge_cases.yaml
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from agent_harness._contracts import VerificationResult
from agent_harness._contracts.state import LoopState
from agent_harness.verification import Verifier

# Load backend/scripts/benchmark_memory_grounded_judge.py via importlib — the plain
# `from scripts.benchmark_memory_grounded_judge import ...` is shadowed by the
# `tests.unit.scripts` package (same idiom as test_benchmark_correction_hygiene.py). Register in
# sys.modules BEFORE exec_module (Python 3.12 dataclass type-resolution accesses sys.modules).
_ROOT = Path(__file__).resolve().parents[3]
_BENCH_PATH = _ROOT / "scripts" / "benchmark_memory_grounded_judge.py"
_spec = importlib.util.spec_from_file_location(
    "_benchmark_memory_grounded_judge_under_test", _BENCH_PATH
)
assert _spec is not None and _spec.loader is not None
_bench = importlib.util.module_from_spec(_spec)
sys.modules["_benchmark_memory_grounded_judge_under_test"] = _bench
_spec.loader.exec_module(_bench)

GroundingCase = _bench.GroundingCase
ArmRun = _bench.ArmRun
load_cases = _bench.load_cases
build_judge_state = _bench.build_judge_state
run_arm = _bench.run_arm
build_report = _bench.build_report

_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "verification"
    / "memory_grounded_judge_cases.yaml"
)


# === Fakes =================================================================


class _SpyJudge(Verifier):
    """Returns cycled verdicts; records the state.injected_memory it was handed per call."""

    def __init__(self, verdicts: list[bool]) -> None:
        self._verdicts = verdicts
        self._idx = 0
        self.seen_memory: list[str | None] = []

    async def verify(
        self, *, output: str, state: LoopState | None = None, trace_context: object = None
    ) -> VerificationResult:
        self.seen_memory.append(state.transient.injected_memory if state else None)
        v = self._verdicts[self._idx % len(self._verdicts)]
        self._idx += 1
        return VerificationResult(passed=v, verifier_name="spy", verifier_type="llm_judge")


def _gcase(cid: str, expected: str) -> GroundingCase:
    return GroundingCase(
        id=cid,
        injected_memory=["User name is Chris."],
        user_question="你知道我是誰?",
        candidate_answer="你是 Chris。",
        expected=expected,
    )


# === load_cases ============================================================


def test_load_real_fixture_schema() -> None:
    cases = load_cases(_FIXTURE)
    assert len(cases) == 10
    assert len({c.id for c in cases}) == len(cases)  # unique ids
    grounded = [c for c in cases if c.expected == "grounded_recall"]
    fabrication = [c for c in cases if c.expected == "genuine_fabrication"]
    assert len(grounded) == 5
    assert len(fabrication) == 5
    assert all(c.injected_memory and c.user_question and c.candidate_answer for c in cases)


def test_load_rejects_missing_key(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text("cases:\n  - id: x\n    injected_memory: []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required key"):
        load_cases(p)


def test_load_rejects_invalid_expected(tmp_path: Path) -> None:
    p = tmp_path / "bad_expected.yaml"
    p.write_text(
        "cases:\n"
        "  - id: x\n    injected_memory: [a]\n    user_question: q\n"
        "    candidate_answer: a\n    expected: maybe\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="expected must be one of"):
        load_cases(p)


def test_load_rejects_duplicate_id(tmp_path: Path) -> None:
    p = tmp_path / "dup.yaml"
    one = (
        "  - id: x\n    injected_memory: [a]\n    user_question: q\n"
        "    candidate_answer: a\n    expected: grounded_recall\n"
    )
    p.write_text("cases:\n" + one + one, encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate case id"):
        load_cases(p)


# === build_judge_state =====================================================


def test_build_judge_state_memory_aware_carries_block() -> None:
    state = build_judge_state(_gcase("c1", "grounded_recall"), grounded=True)
    assert state.transient.injected_memory is not None
    assert "[memory:user] User name is Chris." in state.transient.injected_memory
    # the user question is the {trace}
    assert any(m.role == "user" and m.content == "你知道我是誰?" for m in state.transient.messages)


def test_build_judge_state_bare_has_no_memory() -> None:
    state = build_judge_state(_gcase("c1", "grounded_recall"), grounded=False)
    assert state.transient.injected_memory is None
    # the bare arm still carries the trace (only the grounding differs)
    assert any(m.role == "user" and m.content == "你知道我是誰?" for m in state.transient.messages)


# === run_arm ===============================================================


@pytest.mark.asyncio
async def test_run_arm_classifies_grounded_and_fabrication() -> None:
    cases = [
        _gcase("g1", "grounded_recall"),
        _gcase("g2", "grounded_recall"),
        _gcase("f1", "genuine_fabrication"),
        _gcase("f2", "genuine_fabrication"),
    ]
    # g1 PASS (ok) · g2 REJECT (false positive) · f1 REJECT (caught) · f2 PASS (missed)
    judge = _SpyJudge(verdicts=[True, False, False, True])
    arm = await run_arm("memory_aware", cases, judge=judge)

    assert arm.arm == "memory_aware"
    assert arm.n_grounded == 2
    assert arm.grounded_false_rejects == 1
    assert arm.grounded_recall_false_reject_rate == pytest.approx(0.5)
    assert arm.n_fabrication == 2
    assert arm.fabrication_catches == 1
    assert arm.fabrication_catch_rate == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_run_arm_memory_aware_passes_state_with_memory() -> None:
    cases = [_gcase("g1", "grounded_recall"), _gcase("f1", "genuine_fabrication")]
    judge = _SpyJudge(verdicts=[True])
    await run_arm("memory_aware", cases, judge=judge)
    assert all(m is not None and "[memory:user]" in m for m in judge.seen_memory)


@pytest.mark.asyncio
async def test_run_arm_bare_passes_state_without_memory() -> None:
    cases = [_gcase("g1", "grounded_recall"), _gcase("f1", "genuine_fabrication")]
    judge = _SpyJudge(verdicts=[True])
    await run_arm("bare", cases, judge=judge)
    assert all(m is None for m in judge.seen_memory)


# === build_report ==========================================================


def _arm(arm: str, *, false_reject: float, catch: float) -> ArmRun:
    return ArmRun(
        arm=arm,
        n_grounded=5,
        grounded_false_rejects=int(false_reject * 5),
        grounded_recall_false_reject_rate=false_reject,
        n_fabrication=5,
        fabrication_catches=int(catch * 5),
        fabrication_catch_rate=catch,
    )


def test_build_report_recommends_when_false_reject_drops_and_catch_holds() -> None:
    bare = _arm("bare", false_reject=0.60, catch=1.0)
    memory = _arm("memory_aware", false_reject=0.20, catch=1.0)  # false-reject −0.40, catch held
    rep = build_report(bare, memory)
    assert rep.false_reject_delta == pytest.approx(-0.40)
    assert rep.catch_delta == pytest.approx(0.0)
    assert rep.memory_grounding_recommended is True


def test_build_report_recommends_when_catch_improves_and_false_reject_held() -> None:
    # The real-data scenario (Sprint 57.153 A/B): a lenient bare judge already passes grounded
    # recalls (false-reject 0% both arms) but is BLIND to contradictions (catch 0%); memory_aware
    # catches them (catch +1.0). The catch axis alone justifies default ON.
    bare = _arm("bare", false_reject=0.0, catch=0.0)
    memory = _arm("memory_aware", false_reject=0.0, catch=1.0)  # catch +1.0, false-reject held
    rep = build_report(bare, memory)
    assert rep.false_reject_delta == pytest.approx(0.0)
    assert rep.catch_delta == pytest.approx(1.0)
    assert rep.memory_grounding_recommended is True


def test_build_report_rejects_when_catch_regresses() -> None:
    bare = _arm("bare", false_reject=0.60, catch=1.0)
    memory = _arm("memory_aware", false_reject=0.20, catch=0.80)  # catch −0.20 (too lenient)
    rep = build_report(bare, memory)
    assert rep.catch_delta == pytest.approx(-0.20)
    assert rep.memory_grounding_recommended is False  # the guard rejects a lenient judge


def test_build_report_keeps_off_when_false_reject_unchanged() -> None:
    bare = _arm("bare", false_reject=0.20, catch=1.0)
    memory = _arm("memory_aware", false_reject=0.18, catch=1.0)  # −0.02 < threshold = noise
    rep = build_report(bare, memory)
    assert rep.memory_grounding_recommended is False  # no material improvement → no ship signal
