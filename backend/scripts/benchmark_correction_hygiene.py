"""
File: backend/scripts/benchmark_correction_hygiene.py
Purpose: A/B benchmark of the in-loop correction-context strategy (keep vs summarize) —
         measures verification-retry self-conditioning (Sprint 57.136).
Category: 範疇 10 (Verification Loops) — eval tooling
Scope: Phase 57 / Sprint 57.136

Description:
    Settles #6 ("the just-failed answer stays in context on the retry turn →
    self-conditioning") with real numbers + a human go/no-go verdict (keep cheap-context
    vs flip the default to summarize).

    It REPRODUCES the loop's two correction-context constructions (loop.py 2620 branch)
    WITHOUT running the full loop, so the ONLY variable is whether the just-failed answer
    is re-shown to the model on the retry turn:
      - keep:      [user(prompt), assistant(failed_answer), user(correction_block)]
      - summarize: [user(prompt),                            user(correction_block)]
    (Both use the SAME `_build_correction_block` the loop uses — the correction feedback
    is identical across arms; only the failed-answer assistant turn differs.) For each
    arm + case it calls the real model to produce the retry answer, then computes:
      - retry_pass_rate   — the retry answer judged by the real output_quality judge
      - repeat_error_rate — token-Jaccard(retry, failed_answer): HIGH = self-conditioning
      - mean_prompt_tokens — the context-size cost of carrying the failed answer (keep)
    A materially better summarize (lower repeat AND/OR higher pass) → the human verdict is
    to flip the default; else keep stays default + a negative result is recorded (the #6
    concern is settled as low-risk for the 2-turn correction case).

    The reusable logic lives here (importable as `scripts.benchmark_correction_hygiene`):
      - load_cases(path)                          — parse + schema-validate the golden YAML
      - build_correction_messages(case, strategy) — the two message constructions
      - token_jaccard(a, b)                        — pure self-conditioning similarity
      - run_arm(strategy, cases, ...)             — produce retries + judge them (real LLM)
      - build_report(keep, summarize)             — pure A/B metric computation
      - main()                                    — CLI: build Azure profile, run both arms
    CI-safe unit coverage lives in tests/unit/scripts/test_benchmark_correction_hygiene.py
    (MockChatClient + spy judge, NO Azure). Real run on demand:
      RUN_AZURE_INTEGRATION=1 AZURE_OPENAI_*=... python scripts/benchmark_correction_hygiene.py

LLM Provider Neutrality: the core (load / build / run / score) operates on the ChatClient
+ Verifier ABCs; only main() builds the concrete Azure ModelProfile (mirrors
benchmark_judge.py — the on-demand entry, like the real-Azure integration test).

Created: 2026-06-23 (Sprint 57.136)

Modification History (newest-first):
    - 2026-06-23: Initial creation (Sprint 57.136) — keep-vs-summarize self-conditioning A/B

Related:
    - backend/tests/fixtures/verification/correction_hygiene_cases.yaml (the golden dataset)
    - backend/src/agent_harness/orchestrator_loop/loop.py (2620 branch + _build_correction_block)
    - backend/scripts/benchmark_judge.py (the mirrored scaffold)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

import yaml

from agent_harness._contracts import VerificationResult
from agent_harness._contracts.chat import ChatRequest, Message
from agent_harness.orchestrator_loop.loop import _build_correction_block
from agent_harness.verification import LLMJudgeVerifier, Verifier

# A materially better arm must move a metric by at least this much (5 percentage points)
# for the human verdict to flip the default. Below it, the difference is noise → keep
# stays the default (the #6 concern is settled low-risk for the 2-turn correction case).
SELF_CONDITIONING_DELTA = 0.05

_VALID_STRATEGIES = ("keep", "summarize")
_TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class HygieneCase:
    """One fail-prone benchmark case: a prompt + a deliberately flawed answer + feedback."""

    id: str
    prompt: str
    failed_answer: str
    reason: str
    suggested_correction: str


@dataclass(frozen=True)
class ArmRun:
    """Aggregated result of running one strategy arm over the cases."""

    strategy: str
    n: int
    retry_passes: int
    retry_pass_rate: float
    repeat_error_rate: float
    mean_prompt_tokens: float


@dataclass(frozen=True)
class HygieneReport:
    """Computed A/B metrics + the human go/no-go verdict."""

    total: int
    keep: ArmRun
    summarize: ArmRun
    repeat_delta: float  # summarize − keep; NEGATIVE = summarize breaks self-conditioning
    pass_delta: float  # summarize − keep; POSITIVE = summarize corrects better
    token_delta: float  # summarize − keep; NEGATIVE = summarize is cheaper
    summarize_recommended: bool


def load_cases(path: str | Path) -> list[HygieneCase]:
    """Parse + schema-validate the golden YAML fixture into HygieneCase objects."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "cases" not in data:
        raise ValueError("hygiene fixture must be a mapping with a top-level 'cases' list")
    raw_cases = data["cases"]
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("'cases' must be a non-empty list")

    cases: list[HygieneCase] = []
    seen_ids: set[str] = set()
    for i, rc in enumerate(raw_cases):
        if not isinstance(rc, dict):
            raise ValueError(f"case #{i} is not a mapping")
        for key in ("id", "prompt", "failed_answer", "reason", "suggested_correction"):
            if key not in rc:
                raise ValueError(f"case #{i} missing required key '{key}'")
        cid = str(rc["id"])
        if cid in seen_ids:
            raise ValueError(f"duplicate case id '{cid}'")
        seen_ids.add(cid)
        cases.append(
            HygieneCase(
                id=cid,
                prompt=str(rc["prompt"]),
                failed_answer=str(rc["failed_answer"]),
                reason=str(rc["reason"]),
                suggested_correction=str(rc["suggested_correction"]),
            )
        )
    return cases


def build_correction_messages(case: HygieneCase, strategy: str) -> list[Message]:
    """Reproduce the loop's 2620 correction-context construction for one strategy.

    Both arms append the SAME correction feedback (the loop's `_build_correction_block`);
    `keep` additionally re-appends the just-failed answer as an assistant turn, `summarize`
    drops it. This isolates self-conditioning as the only variable.
    """
    if strategy not in _VALID_STRATEGIES:
        strategy = "keep"
    failures = [
        VerificationResult(
            passed=False,
            verifier_name="benchmark",
            verifier_type="rules_based",
            score=0.0,
            reason=case.reason,
            suggested_correction=case.suggested_correction,
        )
    ]
    correction_block = _build_correction_block(failures)
    messages: list[Message] = [Message(role="user", content=case.prompt)]
    if strategy != "summarize":
        messages.append(Message(role="assistant", content=case.failed_answer))
    messages.append(Message(role="user", content=correction_block))
    return messages


def token_jaccard(a: str, b: str) -> float:
    """Self-conditioning similarity: |tokens(a) ∩ tokens(b)| / |tokens(a) ∪ tokens(b)|.

    1.0 = the retry repeats the failed answer's vocabulary verbatim; 0.0 = disjoint.
    """
    sa = set(_TOKEN_RE.findall(a.lower()))
    sb = set(_TOKEN_RE.findall(b.lower()))
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _content_text(content: Any) -> str:
    """Extract plain text from a ChatResponse.content (str or list[ContentBlock])."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join((getattr(b, "text", "") or "") for b in content)
    return str(content)


async def run_arm(
    strategy: str,
    cases: list[HygieneCase],
    *,
    chat_client: Any,
    judge: Verifier,
    max_tokens: int = 512,
) -> ArmRun:
    """Produce + judge the retry answer for every case under `strategy` (real LLM calls)."""
    passes = 0
    repeats: list[float] = []
    prompt_toks: list[int] = []
    for case in cases:
        messages = build_correction_messages(case, strategy)
        resp = await chat_client.chat(
            ChatRequest(messages=messages, temperature=0.0, max_tokens=max_tokens)
        )
        retry = _content_text(resp.content)
        verdict = await judge.verify(output=retry, state=None)
        if verdict.passed:
            passes += 1
        repeats.append(token_jaccard(retry, case.failed_answer))
        if resp.usage is not None:
            prompt_toks.append(resp.usage.prompt_tokens)
    n = len(cases)
    return ArmRun(
        strategy=strategy,
        n=n,
        retry_passes=passes,
        retry_pass_rate=(passes / n) if n else 0.0,
        repeat_error_rate=mean(repeats) if repeats else 0.0,
        mean_prompt_tokens=mean(prompt_toks) if prompt_toks else 0.0,
    )


def build_report(keep: ArmRun, summarize: ArmRun) -> HygieneReport:
    """Pure A/B metric computation + the human go/no-go verdict."""
    repeat_delta = summarize.repeat_error_rate - keep.repeat_error_rate
    pass_delta = summarize.retry_pass_rate - keep.retry_pass_rate
    token_delta = summarize.mean_prompt_tokens - keep.mean_prompt_tokens
    # Flip the default only if summarize MATERIALLY breaks self-conditioning (repeat down)
    # OR corrects better (pass up). Token savings alone do NOT justify a behavior change.
    summarize_recommended = (
        repeat_delta <= -SELF_CONDITIONING_DELTA or pass_delta >= SELF_CONDITIONING_DELTA
    )
    return HygieneReport(
        total=keep.n,
        keep=keep,
        summarize=summarize,
        repeat_delta=repeat_delta,
        pass_delta=pass_delta,
        token_delta=token_delta,
        summarize_recommended=summarize_recommended,
    )


def report_to_markdown(report: HygieneReport, *, stamp: str) -> str:
    """Render a human-readable A/B report (for the design-note verdict)."""
    verdict = "FLIP default → summarize" if report.summarize_recommended else "KEEP default (keep)"
    lines = [
        f"# Correction-Context Hygiene A/B — {stamp}",
        "",
        f"- cases: **{report.total}**",
        "",
        "| metric | keep | summarize | delta (summ−keep) |",
        "|--------|------|-----------|-------------------|",
        f"| retry_pass_rate | {report.keep.retry_pass_rate:.2%} | "
        f"{report.summarize.retry_pass_rate:.2%} | {report.pass_delta:+.2%} |",
        f"| repeat_error_rate | {report.keep.repeat_error_rate:.3f} | "
        f"{report.summarize.repeat_error_rate:.3f} | {report.repeat_delta:+.3f} |",
        f"| mean_prompt_tokens | {report.keep.mean_prompt_tokens:.1f} | "
        f"{report.summarize.mean_prompt_tokens:.1f} | {report.token_delta:+.1f} |",
        "",
        f"- self-conditioning delta threshold: **{SELF_CONDITIONING_DELTA:.0%}**",
        f"- **verdict: {verdict}**",
        "",
        "> repeat_error_rate = token-Jaccard(retry, failed_answer); LOWER = less "
        "self-conditioning. A NEGATIVE repeat_delta or a POSITIVE pass_delta beyond the "
        "threshold flips the default.",
    ]
    return "\n".join(lines) + "\n"


async def _amain(fixture: Path, out_dir: Path, judge_template: str) -> int:
    # Imported lazily so a CI-safe import of this module's pure helpers does not require
    # the Azure adapter env (mirrors benchmark_judge.py).
    from adapters.azure_openai.profile import build_azure_model_profile

    cases = load_cases(fixture)
    profile = build_azure_model_profile()
    # The retry answer is produced by the action-tier model (the production main answerer);
    # the verdict is rendered by the cheap-tier output_quality judge (production verifier).
    judge = LLMJudgeVerifier(
        chat_client=profile.cheap, judge_template=judge_template, temperature=0.0
    )
    keep = await run_arm("keep", cases, chat_client=profile.action, judge=judge)
    summarize = await run_arm("summarize", cases, chat_client=profile.action, judge=judge)
    report = build_report(keep, summarize)

    out_dir.mkdir(parents=True, exist_ok=True)
    md = report_to_markdown(report, stamp=datetime.now().isoformat(timespec="seconds"))
    (out_dir / "correction_hygiene_report.md").write_text(md, encoding="utf-8")
    (out_dir / "correction_hygiene_report.json").write_text(
        json.dumps(
            {
                "total": report.total,
                "keep": report.keep.__dict__,
                "summarize": report.summarize.__dict__,
                "repeat_delta": report.repeat_delta,
                "pass_delta": report.pass_delta,
                "token_delta": report.token_delta,
                "summarize_recommended": report.summarize_recommended,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(md)
    return 0


def main() -> int:
    # The report markdown carries non-ASCII typography (− · → —); a Windows cp950 console
    # can't encode it. Force the stdout text layer to UTF-8 so the print never crashes.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:  # noqa: BLE001 — best-effort; redirected/odd streams keep their codec
        pass
    parser = argparse.ArgumentParser(description="Correction-context hygiene A/B (Sprint 57.136).")
    parser.add_argument(
        "--fixture",
        default=str(
            Path(__file__).resolve().parent.parent
            / "tests"
            / "fixtures"
            / "verification"
            / "correction_hygiene_cases.yaml"
        ),
    )
    parser.add_argument(
        "--out", default=str(Path(__file__).resolve().parent.parent / "benchmark_reports")
    )
    parser.add_argument("--template", default="output_quality")
    args = parser.parse_args()
    return asyncio.run(_amain(Path(args.fixture), Path(args.out), args.template))


if __name__ == "__main__":
    sys.exit(main())
