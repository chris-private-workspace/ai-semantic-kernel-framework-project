"""
File: backend/scripts/benchmark_tool_anchored_masking.py
Purpose: Tool-anchored masking A/B harness — OFF-vs-ON token reduction + mechanical retention
         over single-user-turn tool-heavy transcripts (the compaction single-user-turn no-op fix).
Category: 範疇 4 (Context Management) — eval tooling
Scope: Phase 57 / Sprint 57.160

Description:
    Quantifies the Sprint 57.160 tool-result-recency masking mode against the
    default user-message-count mode, on the shape the chat main flow actually
    produces: ONE user turn that fans out into many assistant->tool round-trips.

    Over a corpus of single-user-turn tool-heavy transcript SPECS
    (tool_anchored_masking_cases.yaml, built into real Message lists), measure
    with a REAL TiktokenCounter:
      - L0            = raw token count
      - OFF (default) = DefaultObservationMasker() user-anchored  -> expected NO-OP (1 user turn)
      - ON            = DefaultObservationMasker(tool_anchor_keep=N) tool-anchored
    Report:
      - off_reduction = (L0 - OFF)/L0 — per-case + mean; ~0 (confirms the no-op the fix targets)
      - on_reduction  = (L0 - ON)/L0  — per-case + mean; the fix's yield
      - retention_ok  = mechanical retention per case: the last N role="tool" results survive
                        byte-intact, every assistant tool_calls provenance survives, and no
                        system/user/assistant content is touched (only OLD tool bodies tombstoned)
      - recommend_default_on = mean_on_reduction >= MATERIALITY_FLOOR AND mean_off_reduction <=
                        OFF_NOOP_CEIL AND retention_ok_rate == 1.0

    Deterministic by design: masking is a pure, LLM-free transform, so BOTH the
    reduction and the mechanical retention are measured without any model call —
    the whole harness is CI-safe. BEHAVIOURAL retention (does the agent still
    answer correctly after old tool blobs are tombstoned) is validated by the
    Sprint 57.160 DRIVE-THROUGH on the real chat-v2 path (real UI + backend +
    LLM) — a stronger, non-synthetic signal than a fabricated Azure probe would
    give, so no RUN_AZURE_INTEGRATION arm is included here (Day-2 scope decision).

    The reusable logic lives here (importable as `scripts.benchmark_tool_anchored_masking`):
      - load_cases(path)        — parse + schema-validate the corpus specs
      - build_transcript(case)  — spec -> real single-user-turn Message list
      - measure_case(...)       — run OFF + ON masking, count tokens, check retention
      - build_report(results)   — pure metric computation (means / retention rate / recommend)
      - main()                  — CLI: writes markdown + json report
    CI-safe unit coverage lives in tests/unit/scripts/test_benchmark_tool_anchored_masking.py
    (real TiktokenCounter + fixture, NO Azure). Real run on demand:
      python scripts/benchmark_tool_anchored_masking.py

LLM Provider Neutrality: the whole harness is pure (TiktokenCounter is a tokenizer, no provider
SDK); no openai / anthropic import anywhere.

Created: 2026-07-07 (Sprint 57.160)

Modification History (newest-first):
    - 2026-07-07: Initial creation (Sprint 57.160) — tool-anchored masking OFF-vs-ON A/B harness

Related:
    - backend/tests/fixtures/context_mgmt/tool_anchored_masking_cases.yaml (the corpus specs)
    - backend/src/agent_harness/context_mgmt/observation_masker.py (the masker under test)
    - backend/scripts/benchmark_layered_compaction.py (the mirrored scaffold, Sprint 57.139)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

from agent_harness._contracts import Message, ToolCall
from agent_harness.context_mgmt.observation_masker import DefaultObservationMasker
from agent_harness.context_mgmt.token_counter._abc import TokenCounter
from agent_harness.context_mgmt.token_counter.tiktoken_counter import TiktokenCounter

# The ON mode must reclaim at least this fraction for the flip-to-default recommendation.
MATERIALITY_FLOOR: float = 0.10
# The OFF (user-anchored) mode must stay this close to a no-op on single-user-turn transcripts
# (it is the very gap the fix targets — a non-zero OFF reduction would contradict the premise).
OFF_NOOP_CEIL: float = 0.01


@dataclass(frozen=True)
class ToolAnchorCase:
    """A single-user-turn tool-heavy transcript SPEC (built by build_transcript)."""

    id: str
    n_tool_calls: int
    tool_result_chars: int
    tool_anchor_keep: int
    user_text_chars: int
    assistant_text_chars: int
    keep_recent: int
    note: str


@dataclass(frozen=True)
class MaskResult:
    """Per-case OFF/ON token counts + derived reductions + retention verdict."""

    id: str
    l0_tokens: int
    off_tokens: int
    on_tokens: int
    off_reduction: float
    on_reduction: float
    retention_ok: bool


@dataclass(frozen=True)
class ToolAnchorReport:
    """Aggregate A/B report (the design-note verdict source)."""

    total: int
    mean_off_reduction: float
    mean_on_reduction: float
    retention_ok_rate: float
    recommend_default_on: bool
    results: list[MaskResult] = field(default_factory=list)


def load_cases(path: str | Path) -> list[ToolAnchorCase]:
    """Parse + schema-validate the corpus specs into ToolAnchorCase objects."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "cases" not in data:
        raise ValueError("corpus must be a mapping with a top-level 'cases' list")
    raw_cases = data["cases"]
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("'cases' must be a non-empty list")

    cases: list[ToolAnchorCase] = []
    seen_ids: set[str] = set()
    for i, rc in enumerate(raw_cases):
        if not isinstance(rc, dict):
            raise ValueError(f"case #{i} is not a mapping")
        for key in ("id", "n_tool_calls", "tool_result_chars", "tool_anchor_keep"):
            if key not in rc:
                raise ValueError(f"case #{i} missing required key '{key}'")
        cid = str(rc["id"])
        if cid in seen_ids:
            raise ValueError(f"duplicate case id '{cid}'")
        seen_ids.add(cid)
        cases.append(
            ToolAnchorCase(
                id=cid,
                n_tool_calls=int(rc["n_tool_calls"]),
                tool_result_chars=int(rc["tool_result_chars"]),
                tool_anchor_keep=int(rc["tool_anchor_keep"]),
                user_text_chars=int(rc.get("user_text_chars", 40)),
                assistant_text_chars=int(rc.get("assistant_text_chars", 0)),
                keep_recent=int(rc.get("keep_recent", 5)),
                note=str(rc.get("note", "")),
            )
        )
    return cases


def build_transcript(case: ToolAnchorCase) -> list[Message]:
    """Spec -> ONE user turn + n_tool_calls × (assistant tool_call, tool result).

    Models the chat main flow: a single send that fans out into many tool
    round-trips. System messages are omitted — the compactor strips system/HITL
    before calling the masker, so the masker sees exactly this shape.
    """
    msgs: list[Message] = [
        Message(role="user", content="u" + ("x" * max(case.user_text_chars - 1, 0)))
    ]
    for i in range(case.n_tool_calls):
        msgs.append(
            Message(
                role="assistant",
                content="a" * case.assistant_text_chars,
                tool_calls=[ToolCall(id=f"c{i}", name="search", arguments={"i": i})],
            )
        )
        msgs.append(
            Message(
                role="tool",
                content="R" * case.tool_result_chars,
                tool_call_id=f"c{i}",
                name="search",
            )
        )
    return msgs


def _mechanical_retention_ok(
    original: list[Message], masked: list[Message], tool_anchor_keep: int
) -> bool:
    """The last N role="tool" results are byte-intact; provenance + non-tool content untouched.

    Masking preserves list length (in-place tombstoning), so original/masked map 1:1.
    """
    if len(original) != len(masked):
        return False
    tool_positions = [i for i, m in enumerate(original) if m.role == "tool"]
    keep_positions = set(tool_positions[-tool_anchor_keep:]) if tool_anchor_keep >= 1 else set()

    for i, (orig, new) in enumerate(zip(original, masked)):
        if orig.role != "tool":
            # system / user / assistant content + tool_calls provenance must be untouched
            if orig.content != new.content or orig.tool_calls != new.tool_calls:
                return False
            continue
        if i in keep_positions:
            # a retained recent tool result must survive byte-for-byte
            if orig.content != new.content:
                return False
        else:
            # an old tool result must be tombstoned
            if not (isinstance(new.content, str) and new.content.startswith("[REDACTED")):
                return False
    return True


def measure_case(case: ToolAnchorCase, counter: TokenCounter) -> MaskResult:
    """Run OFF (user-anchored) + ON (tool-anchored) masking; count tokens; check retention."""
    messages = build_transcript(case)
    l0 = counter.count(messages=messages)

    off = DefaultObservationMasker().mask_old_results(messages, keep_recent=case.keep_recent)
    on = DefaultObservationMasker(tool_anchor_keep=case.tool_anchor_keep).mask_old_results(messages)

    off_tokens = counter.count(messages=off)
    on_tokens = counter.count(messages=on)
    off_reduction = (l0 - off_tokens) / l0 if l0 else 0.0
    on_reduction = (l0 - on_tokens) / l0 if l0 else 0.0
    retention_ok = _mechanical_retention_ok(messages, on, case.tool_anchor_keep)
    return MaskResult(
        id=case.id,
        l0_tokens=l0,
        off_tokens=off_tokens,
        on_tokens=on_tokens,
        off_reduction=off_reduction,
        on_reduction=on_reduction,
        retention_ok=retention_ok,
    )


def build_report(results: list[MaskResult]) -> ToolAnchorReport:
    """Pure metric computation: means + retention rate + flip-to-default recommendation."""
    total = len(results)
    if total == 0:
        raise ValueError("no results to report")
    mean_off = sum(r.off_reduction for r in results) / total
    mean_on = sum(r.on_reduction for r in results) / total
    retention_rate = sum(1 for r in results if r.retention_ok) / total
    recommend = mean_on >= MATERIALITY_FLOOR and mean_off <= OFF_NOOP_CEIL and retention_rate == 1.0
    return ToolAnchorReport(
        total=total,
        mean_off_reduction=mean_off,
        mean_on_reduction=mean_on,
        retention_ok_rate=retention_rate,
        recommend_default_on=recommend,
        results=results,
    )


def report_to_markdown(report: ToolAnchorReport, *, stamp: str) -> str:
    """Render a human-readable OFF-vs-ON A/B report (for the design-note verdict)."""
    lines = [
        f"# Tool-Anchored Masking A/B — {stamp}",
        "",
        f"- cases: **{report.total}** (single-user-turn tool-heavy transcripts)",
        f"- materiality floor: {MATERIALITY_FLOOR:.0%} · off no-op ceiling: {OFF_NOOP_CEIL:.0%}",
        "",
        "| metric | value |",
        "|--------|-------|",
        f"| mean off_reduction (user-anchored) | **{report.mean_off_reduction:.2%}** |",
        f"| mean on_reduction (tool-anchored) | **{report.mean_on_reduction:.2%}** |",
        f"| retention_ok_rate | **{report.retention_ok_rate:.2%}** |",
        f"| **recommend_default_on** | **{report.recommend_default_on}** |",
        "",
        "| case | L0 | OFF | ON | off% | on% | retention |",
        "|------|----|----:|---:|-----:|----:|:---------:|",
    ]
    for r in report.results:
        lines.append(
            f"| {r.id} | {r.l0_tokens} | {r.off_tokens} | {r.on_tokens} | "
            f"{r.off_reduction:.2%} | {r.on_reduction:.2%} | "
            f"{'ok' if r.retention_ok else 'FAIL'} |"
        )
    lines += [
        "",
        "> off_reduction ~0 confirms the user-anchored no-op the fix targets (one user turn "
        "per send). on_reduction is the tool-anchored yield WITHIN that single user turn. "
        "retention_ok = the last N tool results + all tool_calls provenance + non-tool content "
        "survive intact. Behavioural retention → Sprint 57.160 drive-through.",
    ]
    return "\n".join(lines) + "\n"


def _run(corpus: Path, out_dir: Path) -> int:
    counter = TiktokenCounter(model="gpt-4o")
    cases = load_cases(corpus)
    results = [measure_case(case, counter) for case in cases]
    report = build_report(results)

    out_dir.mkdir(parents=True, exist_ok=True)
    md = report_to_markdown(report, stamp=datetime(2026, 1, 1).isoformat(timespec="seconds"))
    (out_dir / "tool_anchored_masking_report.md").write_text(md, encoding="utf-8")
    (out_dir / "tool_anchored_masking_report.json").write_text(
        json.dumps(
            {
                "total": report.total,
                "mean_off_reduction": report.mean_off_reduction,
                "mean_on_reduction": report.mean_on_reduction,
                "retention_ok_rate": report.retention_ok_rate,
                "recommend_default_on": report.recommend_default_on,
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
    parser = argparse.ArgumentParser(description="Tool-anchored masking A/B (Sprint 57.160).")
    parser.add_argument(
        "--corpus",
        default=str(
            Path(__file__).resolve().parent.parent
            / "tests"
            / "fixtures"
            / "context_mgmt"
            / "tool_anchored_masking_cases.yaml"
        ),
    )
    parser.add_argument(
        "--out", default=str(Path(__file__).resolve().parent.parent / "benchmark_reports")
    )
    args = parser.parse_args()
    return _run(Path(args.corpus), Path(args.out))


if __name__ == "__main__":
    sys.exit(main())
