"""
File: backend/scripts/benchmark_tool_error_reflection.py
Purpose: A/B benchmark of tool-error structured reflection (plain error vs typed diagnosis)
         — does a structured tool-error observation help the model recover? (Sprint 57.144).
Category: 範疇 2 (Tool Layer) — eval tooling
Scope: Phase 57 / Sprint 57.144 (research #7 AD-Tool-Description-Lint-Reflection, Half B)

Description:
    Settles research #7 Half B ("structured-error reflection improves the model's next-turn
    tool recovery") with real numbers + a human go/no-go verdict on the
    CHAT_TOOL_ERROR_REFLECTION lever default.

    For each fail-prone case it builds the SAME 3-message conversation and varies ONLY the
    tool-failure observation the model sees:
      - plain:      the raw error string (a naive no-reflection baseline)
      - reflection: render_reflection(classify_tool_error(...)) — the typed diagnosis +
                    actionable guidance shipped this sprint
    (The arm uses the EXACT production classify_tool_error / render_reflection — so the
    measurement reflects what the live lever-ON path feeds the LLM.) It then asks the real
    model for its next step and judges (real cheap-tier LLM) whether the recovery satisfies
    the case's success criterion. It computes:
      - fix_rate            — fraction of cases the model recovered correctly
      - mean_completion_tokens — the cost of the retry turn
    A materially higher reflection fix_rate (>= MATERIALITY) → the human verdict is to flip
    the lever default to ON; else keep OFF + record the negative result.

    The reusable logic lives here (importable as `scripts.benchmark_tool_error_reflection`):
      - load_cases(path)                 — parse + schema-validate the golden YAML
      - observation_for(case, arm)       — the plain vs reflection tool-failure text
      - build_messages(case, arm)        — the 3-message construction
      - run_arm(arm, cases, ...)         — produce + judge recoveries (real LLM)
      - build_report(plain, reflection)  — pure A/B metric computation + verdict
    CI-safe unit coverage lives in tests/unit/scripts/test_benchmark_tool_error_reflection.py
    (fake ChatClients, NO Azure). Real run on demand:
      RUN_AZURE_INTEGRATION=1 AZURE_OPENAI_*=... python scripts/benchmark_tool_error_reflection.py

LLM Provider Neutrality: the core (load / build / run / score) operates on the ChatClient
ABC; only main() builds the concrete Azure ModelProfile (mirrors benchmark_correction_hygiene.py).

Created: 2026-06-25 (Sprint 57.144)

Modification History (newest-first):
    - 2026-06-25: Initial creation (Sprint 57.144) — plain-vs-reflection tool-recovery A/B

Related:
    - backend/tests/fixtures/tools/tool_error_reflection_cases.yaml (the golden dataset)
    - backend/src/agent_harness/tools/_error_taxonomy.py (classify_tool_error / render_reflection)
    - backend/scripts/benchmark_correction_hygiene.py (the mirrored scaffold)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

import yaml

from agent_harness._contracts.chat import ChatRequest, Message
from agent_harness.tools import classify_tool_error, render_reflection

# A reflection arm must lift fix_rate by at least this much (5 percentage points) for the
# human verdict to flip the lever default to ON. Below it, the difference is noise → keep OFF.
MATERIALITY = 0.05

_VALID_ARMS = ("plain", "reflection")


@dataclass(frozen=True)
class ReflectionCase:
    """One fail-prone case: a user goal + a tool that failed + the raw error + success rule."""

    id: str
    user_prompt: str
    tool_name: str
    bad_call: str  # JSON string of the failing arguments (may be empty)
    error_class: str  # FQ exception class (empty for non-exception failures)
    is_schema_error: bool
    is_unknown_tool: bool
    raw_error: str
    success_criterion: str


@dataclass(frozen=True)
class ArmRun:
    """Aggregated result of running one observation arm over the cases."""

    arm: str
    n: int
    fixes: int
    fix_rate: float
    mean_completion_tokens: float


@dataclass(frozen=True)
class ReflectionReport:
    """Computed A/B metrics + the human go/no-go verdict."""

    total: int
    plain: ArmRun
    reflection: ArmRun
    fix_delta: float  # reflection − plain; POSITIVE = reflection recovers better
    token_delta: float  # reflection − plain; cost of the richer observation
    reflection_recommended: bool


def load_cases(path: str | Path) -> list[ReflectionCase]:
    """Parse + schema-validate the golden YAML fixture into ReflectionCase objects."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "cases" not in data:
        raise ValueError("reflection fixture must be a mapping with a top-level 'cases' list")
    raw_cases = data["cases"]
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("'cases' must be a non-empty list")

    cases: list[ReflectionCase] = []
    seen_ids: set[str] = set()
    for i, rc in enumerate(raw_cases):
        if not isinstance(rc, dict):
            raise ValueError(f"case #{i} is not a mapping")
        for key in ("id", "user_prompt", "tool_name", "raw_error", "success_criterion"):
            if key not in rc:
                raise ValueError(f"case #{i} missing required key '{key}'")
        cid = str(rc["id"])
        if cid in seen_ids:
            raise ValueError(f"duplicate case id '{cid}'")
        seen_ids.add(cid)
        cases.append(
            ReflectionCase(
                id=cid,
                user_prompt=str(rc["user_prompt"]),
                tool_name=str(rc["tool_name"]),
                bad_call=str(rc.get("bad_call", "")),
                error_class=str(rc.get("error_class", "")),
                is_schema_error=bool(rc.get("is_schema_error", False)),
                is_unknown_tool=bool(rc.get("is_unknown_tool", False)),
                raw_error=str(rc["raw_error"]),
                success_criterion=str(rc["success_criterion"]),
            )
        )
    return cases


def observation_for(case: ReflectionCase, arm: str) -> str:
    """The tool-failure observation text for one arm.

    plain → the raw error; reflection → the PRODUCTION render_reflection(classify_tool_error)
    so the A/B measures exactly what the live lever-ON path feeds the LLM.
    """
    if arm == "reflection":
        taxonomy = classify_tool_error(
            error_class=case.error_class or None,
            error_msg=case.raw_error,
            is_schema_error=case.is_schema_error,
            is_unknown_tool=case.is_unknown_tool,
        )
        return render_reflection(taxonomy, case.raw_error)
    return case.raw_error


def build_messages(case: ReflectionCase, arm: str) -> list[Message]:
    """The 3-message conversation; only the tool-failure observation differs by arm.

    Provider-neutral plain user/assistant text (mirrors benchmark_correction_hygiene.py) —
    isolates the observation as the sole variable without coupling to a provider's tool-call
    wire format.
    """
    if arm not in _VALID_ARMS:
        arm = "plain"
    observation = observation_for(case, arm)
    args_clause = f" with arguments {case.bad_call}" if case.bad_call else ""
    return [
        Message(role="user", content=case.user_prompt),
        Message(role="assistant", content=f"I will use the `{case.tool_name}` tool{args_clause}."),
        Message(
            role="user",
            content=(
                f"The `{case.tool_name}` tool failed:\n{observation}\n\n"
                "What is your next step? Be specific about how you will proceed."
            ),
        ),
    ]


def _content_text(content: Any) -> str:
    """Extract plain text from a ChatResponse.content (str or list[ContentBlock])."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join((getattr(b, "text", "") or "") for b in content)
    return str(content)


async def judge_recovery(judge: Any, criterion: str, response: str, *, max_tokens: int = 8) -> bool:
    """Real cheap-tier LLM judge: does `response` satisfy the recovery `criterion`? PASS/FAIL."""
    prompt = (
        "You are evaluating an AI agent's recovery from a tool failure.\n"
        f"Success criterion: {criterion}\n\n"
        f"The agent's next-step response:\n{response}\n\n"
        "Does the response satisfy the success criterion? "
        "Answer with EXACTLY one word: PASS or FAIL."
    )
    resp = await judge.chat(
        ChatRequest(
            messages=[Message(role="user", content=prompt)],
            temperature=0.0,
            max_tokens=max_tokens,
        )
    )
    return _content_text(resp.content).strip().upper().startswith("PASS")


async def run_arm(
    arm: str,
    cases: list[ReflectionCase],
    *,
    answerer: Any,
    judge: Any,
    max_tokens: int = 256,
) -> ArmRun:
    """Produce + judge the recovery for every case under `arm` (real LLM calls)."""
    fixes = 0
    completion_toks: list[int] = []
    for case in cases:
        messages = build_messages(case, arm)
        resp = await answerer.chat(
            ChatRequest(messages=messages, temperature=0.0, max_tokens=max_tokens)
        )
        recovery = _content_text(resp.content)
        if await judge_recovery(judge, case.success_criterion, recovery):
            fixes += 1
        if resp.usage is not None:
            completion_toks.append(resp.usage.completion_tokens)
    n = len(cases)
    return ArmRun(
        arm=arm,
        n=n,
        fixes=fixes,
        fix_rate=(fixes / n) if n else 0.0,
        mean_completion_tokens=mean(completion_toks) if completion_toks else 0.0,
    )


def build_report(plain: ArmRun, reflection: ArmRun) -> ReflectionReport:
    """Pure A/B metric computation + the human go/no-go verdict."""
    fix_delta = reflection.fix_rate - plain.fix_rate
    token_delta = reflection.mean_completion_tokens - plain.mean_completion_tokens
    reflection_recommended = fix_delta >= MATERIALITY
    return ReflectionReport(
        total=plain.n,
        plain=plain,
        reflection=reflection,
        fix_delta=fix_delta,
        token_delta=token_delta,
        reflection_recommended=reflection_recommended,
    )


def report_to_markdown(report: ReflectionReport, *, stamp: str) -> str:
    """Render a human-readable A/B report (for the design-note verdict)."""
    verdict = (
        "FLIP lever default → ON (reflection)"
        if report.reflection_recommended
        else "KEEP lever default OFF (plain)"
    )
    lines = [
        f"# Tool-Error Reflection A/B — {stamp}",
        "",
        f"- cases: **{report.total}**",
        "",
        "| metric | plain | reflection | delta (refl−plain) |",
        "|--------|-------|------------|--------------------|",
        f"| fix_rate | {report.plain.fix_rate:.2%} | "
        f"{report.reflection.fix_rate:.2%} | {report.fix_delta:+.2%} |",
        f"| mean_completion_tokens | {report.plain.mean_completion_tokens:.1f} | "
        f"{report.reflection.mean_completion_tokens:.1f} | {report.token_delta:+.1f} |",
        "",
        f"- materiality threshold: **{MATERIALITY:.0%}** fix_rate lift",
        f"- **verdict: {verdict}**",
        "",
        "> fix_rate = real cheap-tier judge PASS rate on the model's recovery. A fix_delta "
        "at/above the threshold flips the CHAT_TOOL_ERROR_REFLECTION default to ON.",
    ]
    return "\n".join(lines) + "\n"


async def _amain(fixture: Path, out_dir: Path) -> int:
    # Imported lazily so a CI-safe import of this module's pure helpers does not require
    # the Azure adapter env (mirrors benchmark_correction_hygiene.py).
    from adapters.azure_openai.profile import build_azure_model_profile

    cases = load_cases(fixture)
    profile = build_azure_model_profile()
    # The recovery is produced by the action-tier model (the production main answerer);
    # the verdict is rendered by the cheap-tier model (the production judge tier).
    plain = await run_arm("plain", cases, answerer=profile.action, judge=profile.cheap)
    reflection = await run_arm("reflection", cases, answerer=profile.action, judge=profile.cheap)
    report = build_report(plain, reflection)

    out_dir.mkdir(parents=True, exist_ok=True)
    md = report_to_markdown(report, stamp=datetime.now().isoformat(timespec="seconds"))
    (out_dir / "tool_error_reflection_report.md").write_text(md, encoding="utf-8")
    (out_dir / "tool_error_reflection_report.json").write_text(
        json.dumps(
            {
                "total": report.total,
                "plain": report.plain.__dict__,
                "reflection": report.reflection.__dict__,
                "fix_delta": report.fix_delta,
                "token_delta": report.token_delta,
                "reflection_recommended": report.reflection_recommended,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(md)
    return 0


def main() -> int:
    # The report markdown carries non-ASCII typography (− → —); a Windows cp950 console
    # can't encode it. Force the stdout text layer to UTF-8 so the print never crashes.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:  # noqa: BLE001 — best-effort; redirected/odd streams keep their codec
        pass
    parser = argparse.ArgumentParser(description="Tool-error reflection A/B (Sprint 57.144).")
    parser.add_argument(
        "--fixture",
        default=str(
            Path(__file__).resolve().parent.parent
            / "tests"
            / "fixtures"
            / "tools"
            / "tool_error_reflection_cases.yaml"
        ),
    )
    parser.add_argument(
        "--out", default=str(Path(__file__).resolve().parent.parent / "benchmark_reports")
    )
    args = parser.parse_args()
    return asyncio.run(_amain(Path(args.fixture), Path(args.out)))


if __name__ == "__main__":
    sys.exit(main())
