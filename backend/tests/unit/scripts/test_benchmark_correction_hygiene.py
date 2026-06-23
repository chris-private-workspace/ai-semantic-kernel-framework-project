"""
File: backend/tests/unit/scripts/test_benchmark_correction_hygiene.py
Purpose: CI-safe coverage of the correction-hygiene A/B logic (load / build / jaccard / run /
         report) — NO real LLM.
Category: Tests / Unit / 範疇 10
Scope: Sprint 57.136
Created: 2026-06-23

The real-LLM A/B run lives in scripts/benchmark_correction_hygiene.py :: main()
(RUN_AZURE_INTEGRATION). This file pins the pure logic with a MockChatClient + spy judge so
the harness is validated WITHOUT Azure credentials.

Related:
    - backend/scripts/benchmark_correction_hygiene.py
    - backend/tests/fixtures/verification/correction_hygiene_cases.yaml
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

from agent_harness._contracts import VerificationResult
from agent_harness._contracts.chat import ChatResponse, TokenUsage
from agent_harness.verification import Verifier

# Load backend/scripts/benchmark_correction_hygiene.py via importlib — the plain
# `from scripts.benchmark_correction_hygiene import ...` is shadowed by the
# `tests.unit.scripts` package (same idiom as test_benchmark_judge.py). Register in
# sys.modules BEFORE exec_module (Python 3.12 dataclass type-resolution accesses
# sys.modules[__module__]).
_ROOT = Path(__file__).resolve().parents[3]
_BENCH_PATH = _ROOT / "scripts" / "benchmark_correction_hygiene.py"
_spec = importlib.util.spec_from_file_location(
    "_benchmark_correction_hygiene_under_test", _BENCH_PATH
)
assert _spec is not None and _spec.loader is not None
_bench = importlib.util.module_from_spec(_spec)
sys.modules["_benchmark_correction_hygiene_under_test"] = _bench
_spec.loader.exec_module(_bench)

HygieneCase = _bench.HygieneCase
ArmRun = _bench.ArmRun
load_cases = _bench.load_cases
build_correction_messages = _bench.build_correction_messages
token_jaccard = _bench.token_jaccard
run_arm = _bench.run_arm
build_report = _bench.build_report

_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "verification"
    / "correction_hygiene_cases.yaml"
)


# === Fakes =================================================================


class _MockChat:
    """Returns canned retry texts per chat() call; records the requests it received."""

    def __init__(self, texts: list[str], *, prompt_tokens: int = 100) -> None:
        self._texts = texts
        self._idx = 0
        self.requests: list[Any] = []
        self._pt = prompt_tokens

    async def chat(self, request: Any, **kwargs: Any) -> ChatResponse:
        self.requests.append(request)
        text = self._texts[self._idx % len(self._texts)]
        self._idx += 1
        return ChatResponse(
            model="mock",
            content=text,
            usage=TokenUsage(prompt_tokens=self._pt, completion_tokens=5),
        )


class _SpyJudge(Verifier):
    """Returns cycled verdicts; records the outputs it judged."""

    def __init__(self, verdicts: list[bool]) -> None:
        self._verdicts = verdicts
        self._idx = 0
        self.outputs: list[str] = []

    async def verify(
        self, *, output: str, state: object = None, trace_context: object = None
    ) -> VerificationResult:
        self.outputs.append(output)
        v = self._verdicts[self._idx % len(self._verdicts)]
        self._idx += 1
        return VerificationResult(passed=v, verifier_name="spy", verifier_type="llm_judge")


def _case(cid: str = "c1") -> HygieneCase:
    return HygieneCase(
        id=cid,
        prompt="List the additive primaries.",
        failed_answer="red blue yellow",
        reason="lists subtractive primaries",
        suggested_correction="give red green blue",
    )


# === load_cases ============================================================


def test_load_real_fixture_schema() -> None:
    cases = load_cases(_FIXTURE)
    assert len(cases) == 10
    assert len({c.id for c in cases}) == len(cases)  # unique ids
    assert all(c.prompt and c.failed_answer and c.reason and c.suggested_correction for c in cases)


def test_load_rejects_missing_key(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text("cases:\n  - id: x\n    prompt: hi\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required key"):
        load_cases(p)


def test_load_rejects_duplicate_id(tmp_path: Path) -> None:
    p = tmp_path / "dup.yaml"
    p.write_text(
        "cases:\n"
        "  - id: x\n    prompt: a\n    failed_answer: a\n"
        "    reason: r\n    suggested_correction: s\n"
        "  - id: x\n    prompt: b\n    failed_answer: b\n"
        "    reason: r\n    suggested_correction: s\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate case id"):
        load_cases(p)


# === build_correction_messages =============================================


def test_build_messages_keep_includes_failed_answer() -> None:
    msgs = build_correction_messages(_case(), "keep")
    assert any(m.role == "assistant" and m.content == "red blue yellow" for m in msgs)
    user_texts = [m.content for m in msgs if m.role == "user"]
    assert user_texts[0] == "List the additive primaries."  # the prompt
    assert any("failed verification" in (t or "") for t in user_texts)  # correction block
    assert any("give red green blue" in (t or "") for t in user_texts)  # suggested_correction


def test_build_messages_summarize_drops_failed_answer() -> None:
    msgs = build_correction_messages(_case(), "summarize")
    # No assistant turn carrying the failed answer.
    assert not any(m.role == "assistant" for m in msgs)
    # Two user turns: the prompt + the SAME correction feedback as keep.
    user_texts = [m.content for m in msgs if m.role == "user"]
    assert len(user_texts) == 2
    assert any("failed verification" in (t or "") for t in user_texts)
    assert any("give red green blue" in (t or "") for t in user_texts)


def test_build_messages_unknown_strategy_falls_back_to_keep() -> None:
    msgs = build_correction_messages(_case(), "banana")
    assert any(m.role == "assistant" and m.content == "red blue yellow" for m in msgs)


# === token_jaccard =========================================================


def test_token_jaccard_identical_is_one() -> None:
    assert token_jaccard("red green blue", "red green blue") == 1.0


def test_token_jaccard_disjoint_is_zero() -> None:
    assert token_jaccard("red green blue", "alpha beta gamma") == 0.0


def test_token_jaccard_partial() -> None:
    # {a,b,c} vs {b,c,d} → |∩|=2 (b,c), |∪|=4 (a,b,c,d) → 0.5
    assert token_jaccard("a b c", "b c d") == 0.5


def test_token_jaccard_empty_is_zero() -> None:
    assert token_jaccard("", "anything") == 0.0


# === run_arm ===============================================================


@pytest.mark.asyncio
async def test_run_arm_aggregates_and_builds_keep_messages() -> None:
    cases = [_case("c1"), _case("c2")]
    chat = _MockChat(texts=["red green blue", "red blue yellow"])  # 2nd repeats failed answer
    judge = _SpyJudge(verdicts=[True, False])
    arm = await run_arm("keep", cases, chat_client=chat, judge=judge)

    assert arm.strategy == "keep"
    assert arm.n == 2
    assert arm.retry_passes == 1
    assert arm.retry_pass_rate == 0.5
    assert arm.mean_prompt_tokens == 100.0
    # keep arm re-shows the failed answer in the request the model saw.
    assert any(m.role == "assistant" for m in chat.requests[0].messages)
    # repeat_error_rate is the mean Jaccard(retry, failed_answer): case1 retry "red green
    # blue" vs "red blue yellow" = {red,blue}/{red,green,blue,yellow}=0.5; case2 verbatim=1.0
    assert arm.repeat_error_rate == pytest.approx((0.5 + 1.0) / 2)


@pytest.mark.asyncio
async def test_run_arm_summarize_drops_assistant_turn() -> None:
    cases = [_case("c1")]
    chat = _MockChat(texts=["red green blue"])
    judge = _SpyJudge(verdicts=[True])
    await run_arm("summarize", cases, chat_client=chat, judge=judge)
    assert not any(m.role == "assistant" for m in chat.requests[0].messages)


# === build_report ==========================================================


def _arm(strategy: str, *, pass_rate: float, repeat: float, tokens: float) -> ArmRun:
    return ArmRun(
        strategy=strategy,
        n=10,
        retry_passes=int(pass_rate * 10),
        retry_pass_rate=pass_rate,
        repeat_error_rate=repeat,
        mean_prompt_tokens=tokens,
    )


def test_build_report_flips_when_repeat_drops_materially() -> None:
    keep = _arm("keep", pass_rate=0.6, repeat=0.50, tokens=120.0)
    summarize = _arm("summarize", pass_rate=0.6, repeat=0.40, tokens=80.0)  # repeat −0.10
    rep = build_report(keep, summarize)
    assert rep.repeat_delta == pytest.approx(-0.10)
    assert rep.token_delta == pytest.approx(-40.0)
    assert rep.summarize_recommended is True


def test_build_report_flips_when_pass_rises_materially() -> None:
    keep = _arm("keep", pass_rate=0.50, repeat=0.40, tokens=120.0)
    summarize = _arm("summarize", pass_rate=0.60, repeat=0.40, tokens=80.0)  # pass +0.10
    rep = build_report(keep, summarize)
    assert rep.pass_delta == pytest.approx(0.10)
    assert rep.summarize_recommended is True


def test_build_report_keeps_default_when_difference_is_noise() -> None:
    keep = _arm("keep", pass_rate=0.60, repeat=0.40, tokens=120.0)
    summarize = _arm("summarize", pass_rate=0.62, repeat=0.39, tokens=80.0)  # both < 0.05
    rep = build_report(keep, summarize)
    assert rep.summarize_recommended is False  # token savings alone do NOT flip
