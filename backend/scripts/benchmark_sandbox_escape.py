"""
File: backend/scripts/benchmark_sandbox_escape.py
Purpose: Escape-rate harness — measures the python_sandbox regex deny-list's leak vs
         DockerSandbox structural containment (Sprint 57.137, AD-Guardrail-Detect-To-Restrict).
Category: 範疇 9 (Guardrails & Safety) — eval tooling
Scope: Phase 57 / Sprint 57.137

Description:
    Settles research #3 ("detect → restrict") with real numbers: the RiskyActionDetector
    regex deny-list is a losing cat-and-mouse (57.110 found the os.popen bypass), while
    DockerSandbox structurally contains host-reaching code regardless of the primitive used.

    The corpus (sandbox_escape_cases.yaml) is host-EGRESS attempts via diverse primitives —
    network egress is the cleanest single structural boundary (Docker `network none`; the
    one SubprocessSandbox most clearly fails to enforce). Each case prints an __ESCAPED__
    sentinel ONLY if the egress reached outside the sandbox. Two independent measurements:
      - regex_screen(code)  — does the real DEFAULT_SANDBOX_PATTERNS flag it? (the DETECT axis)
      - docker_contain(code) — run under Docker; contained = no __ESCAPED__ (RESTRICT axis)
    Report:
      - regex_escape_rate      — fraction of host-reaching cases the deny-list MISSES (gap > 0)
      - docker_containment_rate— fraction Docker structurally contains (~100% = restrict wins)
    A high escape_rate + a ~100% containment_rate is the evidence that the regex is redundant
    for CONTAINMENT under Docker and must NOT be the primary boundary — the structural sandbox
    must be mandatory (the SANDBOX_REQUIRE_ISOLATION fail-closed gate this sprint ships).

    The reusable logic lives here (importable as `scripts.benchmark_sandbox_escape`):
      - load_cases(path)        — parse + schema-validate the golden YAML
      - regex_screen(code)      — pure: real DEFAULT_SANDBOX_PATTERNS hit?
      - docker_contain(code, …) — run under a backend; contained = no __ESCAPED__ sentinel
      - build_report(results)   — pure metric computation
      - main()                  — CLI: regex arm always; docker arm iff the resolved backend
                                  is_structurally_isolated (dogfoods the 57.137 property)
    CI-safe unit coverage lives in tests/unit/scripts/test_benchmark_sandbox_escape.py
    (real patterns + fixture, NO Docker). Real run on demand:
      RUN_DOCKER_INTEGRATION=1 python scripts/benchmark_sandbox_escape.py

LLM Provider Neutrality: no LLM at all — this is a Cat 9 structural-guardrail measurement;
the docker arm uses the Cat 2 SandboxBackend ABC (default_sandbox()), nothing provider-specific.

Created: 2026-06-24 (Sprint 57.137)

Modification History (newest-first):
    - 2026-06-24: Initial creation (Sprint 57.137) — regex escape-rate vs Docker containment

Related:
    - backend/tests/fixtures/guardrails/sandbox_escape_cases.yaml (the golden corpus)
    - backend/src/agent_harness/guardrails/tool/risky_action_detector.py (DEFAULT_SANDBOX_PATTERNS)
    - backend/src/agent_harness/tools/sandbox.py (default_sandbox / is_structurally_isolated)
    - backend/scripts/benchmark_correction_hygiene.py (the mirrored scaffold)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from agent_harness.guardrails.tool.risky_action_detector import DEFAULT_SANDBOX_PATTERNS

# The corpus snippets print this sentinel ONLY if the host-reaching action succeeded.
ESCAPE_SENTINEL = "__ESCAPED__"

_COMPILED_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p) for p in DEFAULT_SANDBOX_PATTERNS
)


@dataclass(frozen=True)
class EscapeCase:
    """One host-egress attempt: a code snippet + whether the deny-list is EXPECTED to flag it."""

    id: str
    primitive: str
    code: str
    should_match: bool


@dataclass(frozen=True)
class CaseResult:
    """Per-case outcome of the two measurement axes."""

    id: str
    primitive: str
    should_match: bool
    regex_caught: bool
    docker_contained: bool | None  # None when the docker arm did not run


@dataclass(frozen=True)
class EscapeReport:
    """Computed escape-rate (detect gap) + containment-rate (structural restrict)."""

    total: int
    regex_caught: int
    regex_missed: int
    regex_escape_rate: float  # missed / total — the blocklist gap (HIGH = detect loses)
    docker_ran: bool
    docker_contained: int
    docker_containment_rate: float | None  # contained / total — None when docker arm skipped
    results: list[CaseResult] = field(default_factory=list)


def load_cases(path: str | Path) -> list[EscapeCase]:
    """Parse + schema-validate the golden YAML corpus into EscapeCase objects."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "cases" not in data:
        raise ValueError("escape corpus must be a mapping with a top-level 'cases' list")
    raw_cases = data["cases"]
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("'cases' must be a non-empty list")

    cases: list[EscapeCase] = []
    seen_ids: set[str] = set()
    for i, rc in enumerate(raw_cases):
        if not isinstance(rc, dict):
            raise ValueError(f"case #{i} is not a mapping")
        for key in ("id", "primitive", "code", "should_match"):
            if key not in rc:
                raise ValueError(f"case #{i} missing required key '{key}'")
        cid = str(rc["id"])
        if cid in seen_ids:
            raise ValueError(f"duplicate case id '{cid}'")
        seen_ids.add(cid)
        cases.append(
            EscapeCase(
                id=cid,
                primitive=str(rc["primitive"]),
                code=str(rc["code"]),
                should_match=bool(rc["should_match"]),
            )
        )
    return cases


def regex_screen(code: str) -> bool:
    """The DETECT axis: does the real RiskyActionDetector deny-list flag this code?"""
    return any(p.search(code) for p in _COMPILED_PATTERNS)


async def docker_contain(code: str, *, backend: Any, timeout_seconds: float = 8.0) -> bool:
    """The RESTRICT axis: run `code` under `backend`; contained = the egress did NOT reach out.

    'contained' = the __ESCAPED__ sentinel is absent from stdout (the host-reaching action
    raised / was blocked structurally — e.g. Docker `network none` refuses the connect).
    """
    result = await backend.execute(
        code, timeout_seconds=timeout_seconds, memory_mb=128, network_blocked=True
    )
    return ESCAPE_SENTINEL not in result.stdout


def build_report(results: list[CaseResult], *, docker_ran: bool) -> EscapeReport:
    """Pure metric computation: regex escape-rate (gap) + Docker containment-rate (restrict)."""
    total = len(results)
    regex_caught = sum(1 for r in results if r.regex_caught)
    regex_missed = total - regex_caught
    docker_contained = sum(1 for r in results if r.docker_contained)
    return EscapeReport(
        total=total,
        regex_caught=regex_caught,
        regex_missed=regex_missed,
        regex_escape_rate=(regex_missed / total) if total else 0.0,
        docker_ran=docker_ran,
        docker_contained=docker_contained,
        docker_containment_rate=(
            ((docker_contained / total) if total else 0.0) if docker_ran else None
        ),
        results=results,
    )


def report_to_markdown(report: EscapeReport, *, stamp: str) -> str:
    """Render a human-readable escape/containment report (for the design-note verdict)."""
    cont = (
        f"{report.docker_containment_rate:.2%}"
        if report.docker_containment_rate is not None
        else "n/a (docker arm skipped — no structurally-isolated backend)"
    )
    lines = [
        f"# Sandbox Escape vs Containment — {stamp}",
        "",
        f"- cases: **{report.total}** (host-egress attempts via diverse primitives)",
        "",
        "| axis | result |",
        "|------|--------|",
        f"| regex caught (deny-list hit) | {report.regex_caught}/{report.total} |",
        f"| regex MISSED (blocklist gap) | {report.regex_missed}/{report.total} |",
        f"| **regex_escape_rate** | **{report.regex_escape_rate:.2%}** |",
        f"| docker contained (structural) | {report.docker_contained}/{report.total} |",
        f"| **docker_containment_rate** | **{cont}** |",
        "",
        "| case | primitive | should_match | regex_caught | docker_contained |",
        "|------|-----------|--------------|--------------|------------------|",
    ]
    for r in report.results:
        dc = "—" if r.docker_contained is None else ("yes" if r.docker_contained else "**NO**")
        lines.append(
            f"| {r.id} | {r.primitive} | {r.should_match} | "
            f"{'yes' if r.regex_caught else 'no'} | {dc} |"
        )
    lines += [
        "",
        "> regex_escape_rate = host-reaching cases the deny-list MISSES (cat-and-mouse gap). "
        "docker_containment_rate = host-egress structurally blocked under DockerSandbox "
        "(network none). HIGH escape + ~100% containment = the regex is redundant for "
        "containment → make the structural sandbox mandatory (SANDBOX_REQUIRE_ISOLATION), "
        "keep the regex only as ESCALATE-for-visibility.",
    ]
    return "\n".join(lines) + "\n"


async def _amain(corpus: Path, out_dir: Path) -> int:
    # Imported lazily so a CI-safe import of the pure helpers does not require the Cat 2
    # sandbox module's optional docker dependency (mirrors benchmark_correction_hygiene.py).
    from agent_harness.tools.sandbox import default_sandbox

    cases = load_cases(corpus)
    backend = default_sandbox()
    docker_ran = backend.is_structurally_isolated  # dogfood the 57.137 property
    if not docker_ran:
        print(
            "WARNING: resolved sandbox is NOT structurally isolated "
            "(Docker unreachable) — running the regex arm only; the containment arm is "
            "skipped (gate-only, NOT a containment claim).",
            file=sys.stderr,
        )

    results: list[CaseResult] = []
    for case in cases:
        caught = regex_screen(case.code)
        contained: bool | None = None
        if docker_ran:
            contained = await docker_contain(case.code, backend=backend)
        results.append(
            CaseResult(
                id=case.id,
                primitive=case.primitive,
                should_match=case.should_match,
                regex_caught=caught,
                docker_contained=contained,
            )
        )

    report = build_report(results, docker_ran=docker_ran)
    out_dir.mkdir(parents=True, exist_ok=True)
    md = report_to_markdown(report, stamp=datetime.now().isoformat(timespec="seconds"))
    (out_dir / "sandbox_escape_report.md").write_text(md, encoding="utf-8")
    (out_dir / "sandbox_escape_report.json").write_text(
        json.dumps(
            {
                "total": report.total,
                "regex_caught": report.regex_caught,
                "regex_missed": report.regex_missed,
                "regex_escape_rate": report.regex_escape_rate,
                "docker_ran": report.docker_ran,
                "docker_contained": report.docker_contained,
                "docker_containment_rate": report.docker_containment_rate,
                "results": [r.__dict__ for r in report.results],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(md)
    return 0


def main() -> int:
    # The report markdown carries non-ASCII typography (— · ~); a Windows cp950 console
    # can't encode it. Force the stdout text layer to UTF-8 so the print never crashes.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:  # noqa: BLE001 — best-effort; redirected/odd streams keep their codec
        pass
    parser = argparse.ArgumentParser(description="Sandbox escape vs containment (Sprint 57.137).")
    parser.add_argument(
        "--corpus",
        default=str(
            Path(__file__).resolve().parent.parent
            / "tests"
            / "fixtures"
            / "guardrails"
            / "sandbox_escape_cases.yaml"
        ),
    )
    parser.add_argument(
        "--out", default=str(Path(__file__).resolve().parent.parent / "benchmark_reports")
    )
    args = parser.parse_args()
    return asyncio.run(_amain(Path(args.corpus), Path(args.out)))


if __name__ == "__main__":
    sys.exit(main())
